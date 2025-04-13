from fastapi import APIRouter, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db
import os
import logging
import json
from datetime import datetime
from app.services.whatsapp import WhatsAppService
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.models.user import User
from app.models.message import Message
from app.models.whatsapp_integration import WhatsAppIntegration
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
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Webhook endpoint for WhatsApp messages"""
    try:
        payload = await request.json()
        logger.info(f"Webhook received: {payload}")
        
        # Check if this is a WhatsApp message notification
        if "object" in payload and payload["object"] == "whatsapp_business_account":
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Get the metadata about this WhatsApp phone number
                    metadata = value.get("metadata", {})
                    phone_number_id = metadata.get("phone_number_id")
                    
                    if not phone_number_id:
                        logger.error("Missing phone_number_id in webhook payload")
                        continue
                    
                    # Check for incoming messages
                    if "messages" in value:
                        for message in value.get("messages", []):
                            # Handle different message types
                            if message.get("type") == "text":
                                # Extract message details
                                phone_number = message.get("from")
                                message_body = message.get("text", {}).get("body", "")
                                message_id = message.get("id")
                                
                                logger.info(f"Received text message from {phone_number}: {message_body}")
                                
                                # Process the message with AI assistant (in background to prevent timeout)
                                background_tasks.add_task(
                                    process_whatsapp_message,
                                    phone_number_id=phone_number_id,
                                    phone_number=phone_number,
                                    message_body=message_body,
                                    message_id=message_id,
                                    db=db
                                )
                            elif message.get("type") == "image":
                                # Handle image messages
                                phone_number = message.get("from")
                                image = message.get("image", {})
                                caption = image.get("caption", "")
                                message_id = message.get("id")
                                
                                # For now, just process the caption if available, otherwise use a default message
                                message_body = caption if caption else "[Image received. Please describe what you're looking for.]"                                
                                
                                logger.info(f"Received image message from {phone_number} with caption: {caption}")
                                
                                background_tasks.add_task(
                                    process_whatsapp_message,
                                    phone_number_id=phone_number_id,
                                    phone_number=phone_number,
                                    message_body=message_body,
                                    message_id=message_id,
                                    db=db
                                )
                            else:
                                # Log other message types
                                logger.info(f"Received unsupported message type: {message.get('type')}")
        
        # Always return a 200 OK to acknowledge receipt
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error"}, status_code=200)  # Still return 200 to acknowledge

async def process_whatsapp_message(phone_number_id: str, phone_number: str, message_body: str, message_id: str, db: Session):
    """Process WhatsApp message with AI assistant and send response
    
    Args:
        phone_number_id: The WhatsApp phone number ID that received the message
        phone_number: The sender's phone number
        message_body: The message content
        message_id: The WhatsApp message ID
        db: Database session
    """
    try:
        # Find the WhatsApp integration for this phone number ID
        integration = db.query(WhatsAppIntegration).filter(
            WhatsAppIntegration.phone_number_id == phone_number_id,
            WhatsAppIntegration.is_active == True
        ).first()
        
        if not integration:
            logger.error(f"No active WhatsApp integration found for phone number ID {phone_number_id}")
            # Send a fallback message
            whatsapp_service = WhatsAppService(phone_number_id=phone_number_id)
            await whatsapp_service.send_message(
                phone_number, 
                "Sorry, this WhatsApp number is not connected to an AI assistant. Please contact the business directly."
            )
            return
        
        # Get the associated assistant and business profile
        assistant = db.query(AIAssistant).filter(AIAssistant.id == integration.assistant_id).first()
        business_profile = db.query(BusinessProfile).filter(BusinessProfile.id == integration.business_profile_id).first()
        
        if not assistant or not business_profile:
            logger.error(f"Assistant or business profile not found for WhatsApp integration {integration.id}")
            return
            
        # Get the user who owns this assistant
        user = db.query(User).filter(User.id == assistant.user_id).first()
        if not user:
            logger.error(f"User not found for assistant {assistant.id}")
            return
        
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
        
        # Get chat history and prepare context with business profile context
        formatted_messages = prepare_chat_context(assistant.id, message_body, db)
        
        # Add business profile type to system message
        if business_profile.business_type:
            # Find the system message (first message)
            for msg in formatted_messages:
                if msg.get("role") == "system":
                    # Enhance the system message with the business profile type
                    business_type = business_profile.business_type.lower()
                    assistant_type = ""
                    
                    if "sell" in business_type:
                        assistant_type = "a sales assistant. Your goal is to help sell products or services."
                    elif "consult" in business_type:
                        assistant_type = "a consultant. Your goal is to provide expert advice and guidance."
                    elif "support" in business_type:
                        assistant_type = "a support assistant. Your goal is to help solve problems and provide assistance."
                    else:
                        assistant_type = f"an assistant for a {business_type} business."
                    
                    msg["content"] += f" You are {assistant_type}"
                    break
        
        # Get AI response
        ai_response = get_ai_response(formatted_messages, assistant.model)
        
        # Update the message with AI response
        db_message.ai_response = ai_response
        db.commit()
        
        # Send the response back via WhatsApp
        whatsapp_service = WhatsAppService(phone_number_id=phone_number_id)
        await whatsapp_service.send_message(phone_number, ai_response)
        
        logger.info(f"Successfully processed WhatsApp message from {phone_number} with assistant {assistant.name}")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {str(e)}") 