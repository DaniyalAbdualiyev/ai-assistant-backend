from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db
import os
import logging

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
        
        # Always return a 200 OK to acknowledge receipt
        return JSONResponse(content={"status": "success"}, status_code=200)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse(content={"status": "error"}, status_code=200)  # Still return 200 to acknowledge 