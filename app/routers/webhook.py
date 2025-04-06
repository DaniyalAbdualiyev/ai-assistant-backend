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
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "21010767")

# WhatsApp webhook verification endpoint
@router.get("/whatsapp-webhook")
async def verify_whatsapp_webhook(
    hub_mode: str = None, 
    hub_verify_token: str = None, 
    hub_challenge: str = None
):
    logger.info(f"Webhook verification attempt - mode: {hub_mode}, token: {hub_verify_token}, challenge: {hub_challenge}")
    
    # This is the critical part - Meta sends these exact query parameters
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(content=hub_challenge)
    
    logger.error("Webhook verification failed")
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