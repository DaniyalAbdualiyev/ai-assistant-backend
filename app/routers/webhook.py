from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db
import os

router = APIRouter()

# Verify token (should match what you entered in the Meta Developer Console)
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "21010767")

# WhatsApp webhook verification endpoint
@router.get("/whatsapp-webhook")
async def verify_whatsapp_webhook(hub_mode: str = None, hub_verify_token: str = None, hub_challenge: str = None):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(content=hub_challenge)
    else:
        return JSONResponse(content={"status": "error", "message": "Verification failed"}, status_code=403)

# WhatsApp webhook for incoming messages
@router.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    
    # Log the payload
    print("WhatsApp webhook received:", payload)
    
    # Process the incoming message (implement this later)
    # Handle the WhatsApp message format here
    
    # Always return a 200 OK to acknowledge receipt
    return JSONResponse(content={"status": "success"}, status_code=200) 