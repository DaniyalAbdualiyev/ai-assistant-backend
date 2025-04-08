from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict
import logging
from app.dependencies import get_db, get_current_user
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.services.whatsapp_verification import WhatsAppVerificationService
from app.services.whatsapp import WhatsAppService
from app.routers.messages import prepare_chat_context, get_ai_response

router = APIRouter()
logger = logging.getLogger(__name__)
verification_service = WhatsAppVerificationService()
whatsapp_service = WhatsAppService()

@router.post("/verify")
async def verify_phone_number(
    phone_number: str,
    business_profile_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start phone number verification process
    """
    try:
        # Verify business profile ownership
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == business_profile_id,
            BusinessProfile.assistant_id == AIAssistant.id,
            AIAssistant.user_id == current_user.id
        ).join(AIAssistant).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Business profile not found")
            
        # Start verification process
        result = await verification_service.verify_phone_number(phone_number)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result["message"])
            
        return result
        
    except Exception as e:
        logger.error(f"Error in phone verification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/confirm")
async def confirm_verification(
    phone_number: str,
    code: str,
    business_profile_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Confirm phone number verification with code
    """
    try:
        # Verify business profile ownership
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == business_profile_id,
            BusinessProfile.assistant_id == AIAssistant.id,
            AIAssistant.user_id == current_user.id
        ).join(AIAssistant).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="Business profile not found")
            
        # Verify the code
        is_verified = await verification_service.verify_code(phone_number, code)
        
        if not is_verified:
            raise HTTPException(status_code=400, detail="Invalid verification code")
            
        # Register the phone number
        result = await verification_service.register_phone_number(business_profile_id, phone_number)
        
        if result["status"] == "success":
            # Update business profile
            profile.whatsapp_number = phone_number
            profile.whatsapp_verified = True
            db.commit()
            
        return result
        
    except Exception as e:
        logger.error(f"Error in verification confirmation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming WhatsApp webhook events
    """
    try:
        # Verify webhook signature
        signature = request.headers.get("x-hub-signature-256", "")
        body = await request.body()
        
        if not whatsapp_service.verify_signature(signature, body):
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        # Parse webhook payload
        payload = await request.json()
        
        # Handle different types of webhook events
        if payload.get("object") == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        await handle_message(change.get("value", {}), db)
                        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_message(message_data: Dict, db: Session):
    """
    Handle incoming WhatsApp messages
    """
    try:
        # Extract message details
        message = message_data.get("messages", [{}])[0]
        from_number = message.get("from")
        message_text = message.get("text", {}).get("body", "")
        
        if not message_text:
            return
            
        # Find business profile by WhatsApp number
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.whatsapp_number == from_number,
            BusinessProfile.whatsapp_verified == True
        ).first()
        
        if not profile:
            logger.warning(f"No verified business profile found for number: {from_number}")
            return
            
        # Get AI response using the business profile's assistant
        assistant = profile.assistant
        context = prepare_chat_context(assistant.id, message_text, db)
        ai_response = get_ai_response(context, assistant.model)
        
        # Send response back via WhatsApp
        await whatsapp_service.send_message(from_number, ai_response)
        
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        # Optionally send an error message to the user
        await whatsapp_service.send_message(
            from_number,
            "Sorry, I encountered an error processing your message. Please try again later."
        ) 