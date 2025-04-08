import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from app.database import SessionLocal
from app.models.payment import Payment
from app.models.subscription_plans import SubscriptionPlan
from app.schemas.payment import PaymentResponse
from app.schemas.subscription import (
    SubscriptionCreate, 
    SubscriptionResponse, 
    SubscriptionPlanResponse,
    SubscriptionPlanCreate
)
from sqlalchemy.orm import Session
import os
from dotenv import load_dotenv
from typing import List
from app.dependencies import get_db, get_current_user
from app.models.user import User
import logging
import time

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
    db: Session = Depends(get_db)
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
        logger.info(f"Saved payment record for session {checkout_session.id}")

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
            payment.status = "completed"
            db.commit()
            
    elif event["type"] == "payment_intent.payment_failed":
        session = event["data"]["object"]
        payment_id = session.get("id")
        
        payment = db.query(Payment).filter(Payment.transaction_id == payment_id).first()
        if payment:
            payment.status = "failed"
            db.commit()
            
    return {"status": "success"}

@router.get("/subscriptions/{user_id}", response_model=List[PaymentResponse])
async def get_user_subscriptions(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Users can only view their own subscriptions, admins can view all"""
    if user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You can only view your own subscriptions")
    
    payments = db.query(Payment).filter(
        Payment.user_id == user_id,
        Payment.status == "completed"
    ).all()
    
    if not payments:
        raise HTTPException(status_code=404, detail="No subscriptions found")
        
    return payments

@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_plan(
    plan: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Only admin users should be able to create plans"""
    logger.info("Starting create_plan endpoint")
    start_time = time.time()

    # Check admin status
    logger.info(f"Checking admin status for user {current_user.email}")
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin users can create plans")
    
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