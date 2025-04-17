import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from app.database import SessionLocal
from app.models.payment import Payment
from app.models.subscription_plans import SubscriptionPlan
from app.models.user_subscription import UserSubscription
from app.schemas.payment import PaymentResponse
from app.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionResponse, 
    SubscriptionPlanResponse,
    SubscriptionPlanCreate,
    UserSubscriptionResponse
)
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import List
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.middleware.admin_middleware import verify_admin
import logging
import time
from datetime import datetime, timedelta

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
stripe.api_version = "2023-10-16"  # Set specific API version
stripe.max_network_retries = 2     # Limit retries
stripe.default_http_client = stripe.http_client.RequestsClient(timeout=10)  # Set timeout

router = APIRouter(tags=["payments"])

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/subscriptions", response_model=SubscriptionResponse)
async def create_subscription(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    test_mode: bool = True  # Enable test mode by default for development
):
    """Users can only create subscriptions for themselves"""
    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only create subscriptions for yourself")
    
    logger.info("Starting create_subscription endpoint")
    start_time = time.time()

    try:
        logger.info(f"Creating subscription for user {subscription.user_id}")
        plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == subscription.plan_id).first()
        if not plan:
            logger.error(f"Plan {subscription.plan_id} not found")
            raise HTTPException(status_code=404, detail="Subscription plan not found")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": plan.name,
                    },
                    "unit_amount": int(plan.price * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:8000/payments/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/payments/cancel?session_id={CHECKOUT_SESSION_ID}",
        )
        
        logger.info(f"Created Stripe session: {checkout_session.id}")

        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            plan_id=subscription.plan_id,
            amount=plan.price,
            status="pending",
            transaction_id=checkout_session.id
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        logger.info(f"Saved payment record for session {checkout_session.id}")
        
        # For testing/development: Automatically create subscription without waiting for webhook
        if test_mode:
            logger.info(f"Test mode enabled: Automatically creating subscription for user {current_user.id}")
            # Update payment status to completed
            payment.status = "completed"
            
            # Calculate subscription end date based on plan duration
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=30 * plan.duration_months)
            
            # Create user subscription
            subscription = UserSubscription(
                user_id=current_user.id,
                plan_id=plan.id,
                payment_id=payment.id,
                start_date=start_date,
                end_date=end_date,
                is_active=True
            )
            
            db.add(subscription)
            db.commit()
            logger.info(f"Created test subscription for user {current_user.id} valid until {end_date}")

        end_time = time.time()
        logger.info(f"Subscription creation completed in {end_time - start_time:.2f} seconds")
        
        return {"session_id": checkout_session.id, "url": checkout_session.url}  # Return both session ID and URL

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle different types of events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        payment_id = session.get("id")
        
        payment = db.query(Payment).filter(Payment.transaction_id == payment_id).first()
        if payment:
            # Update payment status
            payment.status = "completed"
            
            # Get the subscription plan
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == payment.plan_id).first()
            
            if plan:
                # Calculate end date based on plan duration
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=30 * plan.duration_months)
                
                # Create user subscription
                subscription = UserSubscription(
                    user_id=payment.user_id,
                    plan_id=payment.plan_id,
                    payment_id=payment.id,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=True
                )
                
                db.add(subscription)
            
            db.commit()
            
    elif event["type"] == "payment_intent.payment_failed":
        session = event["data"]["object"]
        payment_id = session.get("id")
        
        payment = db.query(Payment).filter(Payment.transaction_id == payment_id).first()
        if payment:
            payment.status = "failed"
            db.commit()
            
    return {"status": "success"}

@router.get("/subscriptions/{user_id}", response_model=List[UserSubscriptionResponse])
async def get_user_subscriptions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Users can only view their own subscriptions, admins can view all"""
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only view your own subscriptions")
    
    subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.is_active == True
    ).all()
    
    if not subscriptions:
        raise HTTPException(status_code=404, detail="No active subscriptions found")
        
    return subscriptions

@router.get("/subscriptions/{user_id}/active", response_model=bool)
async def check_active_subscription(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if a user has an active subscription"""
    # Only allow users to check their own subscription or admins to check any
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only check your own subscription")
    
    # Find active subscriptions that haven't expired
    active_subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id,
        UserSubscription.is_active == True,
        UserSubscription.end_date >= datetime.utcnow()
    ).first()
    
    return active_subscription is not None

@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_plan(
    plan: SubscriptionPlanCreate,
    current_user: User = Depends(verify_admin),  # Use admin middleware
    db: Session = Depends(get_db)
):
    """Only admin users should be able to create plans"""
    logger.info("Starting create_plan endpoint")
    start_time = time.time()

    # Admin status is already verified by the verify_admin dependency
    logger.info(f"Admin user {current_user.email} creating plan")
    
    try:
        # Create new plan
        logger.info("Creating new subscription plan")
        new_plan = SubscriptionPlan(
            name=plan.name,
            price=plan.price,
            features=plan.features
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        
        end_time = time.time()
        logger.info(f"Plan creation completed in {end_time - start_time:.2f} seconds")
        return new_plan
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating plan: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Anyone can view plans"""
    plans = db.query(SubscriptionPlan).all()
    return plans

# Remove the authentication requirement for success and cancel endpoints
@router.get("/success")
async def payment_success():
    return {"message": "Payment successful! Thank you for your purchase."}

@router.get("/cancel")
async def payment_cancel():
    return {"message": "Payment cancelled. Please try again."}