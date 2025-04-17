from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Optional
import uuid
from datetime import datetime

from app.dependencies import get_db
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.services.ai_service import AIService
from app.schemas.chat import ClientChatRequest, ClientChatResponse, ClientSession

router = APIRouter(tags=["client_chat"])
ai_service = AIService()

# Store client sessions in memory (in production, use Redis or database)
client_sessions = {}

@router.post("/start/{business_unique_id}", response_model=ClientSession)
async def start_client_chat(
    business_unique_id: str,
    db: Session = Depends(get_db)
):
    """
    Start a new chat session with a business AI assistant using the business unique ID.
    This is the endpoint that will be called when a client scans a QR code.
    No authentication required - this is a public endpoint.
    """
    # Get business profile by unique ID
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.unique_id == business_unique_id
    ).first()
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Get the associated AI assistant
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == business_profile.assistant_id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="AI assistant not found")
    
    # Create a new client session
    client_id = str(uuid.uuid4())
    client_sessions[client_id] = {
        "business_id": business_profile.id,
        "business_name": business_profile.business_name,
        "assistant_id": assistant.id,
        "assistant_name": assistant.name,
        "created_at": datetime.utcnow(),
        "chat_history": []
    }
    
    return {
        "client_id": client_id,
        "business_name": business_profile.business_name,
        "assistant_name": assistant.name
    }

@router.post("/message", response_model=ClientChatResponse)
async def client_chat_message(
    chat_request: ClientChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a message to the business AI assistant.
    Requires a client_id from a previous start_client_chat call.
    No authentication required - this is a public endpoint.
    """
    client_id = chat_request.client_id
    
    # Check if client session exists
    if client_id not in client_sessions:
        raise HTTPException(status_code=404, detail="Chat session not found or expired")
    
    session = client_sessions[client_id]
    
    # Get business profile
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == session["business_id"]
    ).first()
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Get assistant
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == session["assistant_id"]
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="AI assistant not found")
    
    # Prepare configuration for AI service
    config = {
        "language": assistant.language,
        "tone": business_profile.tone_preferences or "professional",
        "business_type": business_profile.business_type,
        "knowledge_base": business_profile.knowledge_base if hasattr(business_profile, "knowledge_base") else None
    }
    
    try:
        # Get response from AI service
        response = await ai_service.get_response(
            chat_request.message,
            config,
            assistant.id,
            namespace=f"business_{business_profile.id}"  # Use business profile namespace for knowledge base
        )
        
        # Add to chat history
        session["chat_history"].append({
            "role": "user",
            "content": chat_request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        session["chat_history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return {
            "message": response,
            "business_name": business_profile.business_name,
            "assistant_name": assistant.name
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
