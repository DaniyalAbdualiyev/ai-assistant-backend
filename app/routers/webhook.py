from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db
import os
import logging
from fastapi import BackgroundTasks
from datetime import datetime
from app.services.whatsapp import WhatsAppService
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.models.user import User
from app.models.message import Message
from app.routers.messages import prepare_chat_context, get_ai_response
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
whatsapp_service = WhatsAppService()

# WhatsApp webhook verification endpoint
@router.get("/whatsapp-webhook")
async def verify_whatsapp_webhook(request: Request):
    # Get the query parameters - Meta uses hub.mode, hub.challenge, hub.verify_token
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    logger.info(f"Webhook verification attempt - mode: {mode}, token: {token}, challenge: {challenge}")
    
    # Verify token from environment variable
    if mode == "subscribe" and token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=challenge)
    
    logger.error(f"Webhook verification failed - token mismatch")
    return JSONResponse(
        content={"success": False, "message": "Verification failed"}, 
        status_code=403
    )

# WhatsApp webhook for incoming messages
@router.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # Verify webhook signature
        signature = request.headers.get("x-hub-signature-256", "")
        body = await request.body()
        
        if not whatsapp_service.verify_signature(signature, body):
            raise HTTPException(status_code=401, detail="Invalid signature")
            
        payload = await request.json()
        logger.info(f"Webhook received: {payload}")
        
        # Check if this is a WhatsApp message notification
        if "object" in payload and payload["object"] == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Handle different types of changes
                    if change.get("field") == "messages":
                        await handle_messages(value, background_tasks, db)
                    elif change.get("field") == "status":
                        await handle_status_updates(value, db)
        
        return JSONResponse(content={"status": "success"}, status_code=200)
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

async def handle_messages(value: dict, background_tasks: BackgroundTasks, db: Session):
    """Handle incoming WhatsApp messages"""
    for message in value.get("messages", []):
        if message.get("type") == "text":
            phone_number = message.get("from")
            message_body = message.get("text", {}).get("body", "")
            message_id = message.get("id")
            
            logger.info(f"Received message from {phone_number}: {message_body}")
            
            # Process the message with AI assistant in background
            background_tasks.add_task(
                process_whatsapp_message,
                phone_number=phone_number,
                message_body=message_body,
                message_id=message_id,
                db=db
            )

async def handle_status_updates(value: dict, db: Session):
    """Handle WhatsApp message status updates"""
    for status in value.get("statuses", []):
        message_id = status.get("id")
        status = status.get("status")
        timestamp = status.get("timestamp")
        
        logger.info(f"Message {message_id} status updated to {status} at {timestamp}")
        
        # Update message status in database if needed
        message = db.query(Message).filter(Message.message_id == message_id).first()
        if message:
            message.status = status
            message.updated_at = datetime.utcnow()
            db.commit()

async def process_whatsapp_message(phone_number: str, message_body: str, message_id: str, db: Session):
    """Process WhatsApp message with AI assistant and send response"""
    try:
        # Find business profile by WhatsApp number
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.whatsapp_number == phone_number,
            BusinessProfile.whatsapp_verified == True
        ).first()
        
        if not profile:
            logger.warning(f"No verified business profile found for number: {phone_number}")
            return
            
        # Get the assistant
        assistant = profile.assistant
        user = db.query(User).filter(User.id == assistant.user_id).first()
        
        # Create message record
        db_message = Message(
            user_query=message_body,
            ai_response="Processing WhatsApp request...",
            assistant_id=assistant.id,
            user_id=user.id,
            message_id=message_id,
            timestamp=datetime.utcnow()
        )
        db.add(db_message)
        db.commit()
        
        # Get chat history and prepare context
        formatted_messages = prepare_chat_context(assistant.id, message_body, db)
        
        # Get AI response
        ai_response = get_ai_response(formatted_messages, assistant.model)
        
        # Update message with AI response
        db_message.ai_response = ai_response
        db.commit()
        
        # Send response back via WhatsApp
        await whatsapp_service.send_message(phone_number, ai_response)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}")
        # Send error message to user
        await whatsapp_service.send_message(
            phone_number,
            "Sorry, I encountered an error processing your message. Please try again later."
        ) 