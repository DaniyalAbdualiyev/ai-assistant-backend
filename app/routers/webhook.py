from fastapi import APIRouter, Request, Depends
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

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Verify token (must match what you entered in Meta Developer Console)
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "210107067")

# WhatsApp webhook verification endpoint
@router.get("/whatsapp-webhook")
async def verify_whatsapp_webhook(request: Request):
    # Get the query parameters - Meta uses hub.mode, hub.challenge, hub.verify_token
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    logger.info(f"Webhook verification attempt - mode: {mode}, token: {token}, challenge: {challenge}")
    
    # This is the critical part - Meta sends these exact query parameters
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=challenge)
    
    logger.error(f"Webhook verification failed - token mismatch. Expected '{VERIFY_TOKEN}', got '{token}'")
    return JSONResponse(
        content={"success": False, "message": "Verification failed"}, 
        status_code=403
    )

# WhatsApp webhook for incoming messages
@router.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        logger.info(f"Webhook received: {payload}")
        
        # Check if this is a WhatsApp message notification
        if "object" in payload and payload["object"] == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Check for incoming messages
                    if "messages" in value:
                        for message in value.get("messages", []):
                            if message.get("type") == "text":
                                # Extract message details
                                phone_number = message.get("from")
                                message_body = message.get("text", {}).get("body", "")
                                message_id = message.get("id")
                                
                                logger.info(f"Received message from {phone_number}: {message_body}")
                                
                                # Process the message with AI assistant (in background to prevent timeout)
                                background_tasks = BackgroundTasks()
                                background_tasks.add_task(
                                    process_whatsapp_message,
                                    phone_number=phone_number,
                                    message_body=message_body,
                                    message_id=message_id,
                                    db=db
                                )
        
        # Always return a 200 OK to acknowledge receipt
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error"}, status_code=200)  # Still return 200 to acknowledge

async def process_whatsapp_message(phone_number: str, message_body: str, message_id: str, db: Session):
    """Process WhatsApp message with AI assistant and send response"""
    try:
        # Find a matching business profile/assistant for this WhatsApp number
        # This is a simplified version - you would need to map phone numbers to business profiles
        assistant = db.query(AIAssistant).join(BusinessProfile).first()
        
        if not assistant:
            logger.error(f"No assistant found for WhatsApp message from {phone_number}")
            return
            
        # Using your existing message processing logic
        user = db.query(User).filter(User.id == assistant.user_id).first()
        
        # Create a message record
        db_message = Message(
            user_query=message_body,
            ai_response="Processing WhatsApp request...",
            assistant_id=assistant.id,
            user_id=user.id,
            timestamp=datetime.utcnow()
        )
        db.add(db_message)
        db.commit()
        
        # Get chat history and prepare context
        formatted_messages = prepare_chat_context(assistant.id, message_body, db)
        
        # Get AI response
        ai_response = get_ai_response(formatted_messages, assistant.model)
        
        # Update the message with AI response
        db_message.ai_response = ai_response
        db.commit()
        
        # Send the response back via WhatsApp
        whatsapp_service = WhatsAppService()
        await whatsapp_service.send_message(phone_number, ai_response)
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}") 