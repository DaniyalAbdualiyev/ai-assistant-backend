from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import uuid
import json
from datetime import datetime
import time

from app.dependencies import get_db, get_current_user
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.routers.messages import prepare_chat_context, get_ai_response
from app.services.analytics_service import AnalyticsService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Store chat sessions in memory (in production, this would be in a database)
# Key: unique_id + client_id, Value: chat session data
chat_sessions = {}

# Initialize analytics service
analytics_service = AnalyticsService()

@router.post("/start-chat/{business_unique_id}")
async def start_chat_session(
    business_unique_id: str,
    client_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Start a new chat session with a business AI assistant using the business unique ID.
    The client_id is optional and can be used to maintain separate chat histories for different clients.
    """
    # Verify business profile exists
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.unique_id == business_unique_id
    ).first()
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Get the associated AI assistant
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == business_profile.assistant_id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="AI assistant not found")
    
    # Generate a client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Create a session key
    session_key = f"{business_unique_id}_{client_id}"
    
    # Store session information
    chat_sessions[session_key] = {
        "business_profile_id": business_profile.id,
        "assistant_id": assistant.id,
        "created_at": datetime.utcnow(),
        "messages": []
    }
    
    # Return session information
    return {
        "business_name": business_profile.business_name,
        "business_type": business_profile.business_type,
        "client_id": client_id,
        "session_key": session_key
    }

@router.post("/chat/{business_unique_id}")
async def chat_with_business_assistant(
    business_unique_id: str,
    message: MessageCreate,
    client_id: Optional[str] = None,
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Send a message to the business AI assistant and get a response.
    This endpoint is used by the web chat interface accessed via shared link.
    """
    logger.info(f"Web chat message received for business_unique_id={business_unique_id}, client_id={client_id}")
    logger.info(f"User query: {message.content[:100]}...")
    
    # Generate a client ID if not provided
    if not client_id:
        client_id = str(uuid.uuid4())
        logger.info(f"Generated new client_id: {client_id}")
        
    # Create a session key
    session_key = f"{business_unique_id}_{client_id}"
    
    # Check if session exists, if not create it
    if session_key not in chat_sessions:
        logger.info(f"Creating new web chat session for key: {session_key}")
        
        # Get business profile
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.unique_id == business_unique_id
        ).first()
        
        if not business_profile:
            logger.warning(f"Business profile not found: {business_unique_id}")
            raise HTTPException(status_code=404, detail="Business profile not found")
        
        # Get the associated AI assistant
        assistant = db.query(AIAssistant).filter(
            AIAssistant.id == business_profile.assistant_id
        ).first()
        
        if not assistant:
            logger.warning(f"AI assistant not found for business profile: {business_unique_id}")
            raise HTTPException(status_code=404, detail="AI assistant not found")
            
        # Create new session
        chat_sessions[session_key] = {
            "business_profile_id": business_profile.id,
            "assistant_id": assistant.id,
            "created_at": datetime.utcnow(),
            "messages": []
        }
        
        logger.info(f"New web chat session created for business_id={business_profile.id}, assistant_id={assistant.id}")
        
        # Record client session for analytics
        client_ip = request.client.host if request and request.client else None
        client_device = request.headers.get("User-Agent") if request else None
        
        await analytics_service.record_client_session(
            db=db,
            client_session_id=client_id,
            assistant_id=assistant.id,
            business_profile_id=business_profile.id,
            client_ip=client_ip,
            client_device=client_device
        )
    else:
        logger.info(f"Using existing web chat session: {session_key}")
    
    session = chat_sessions[session_key]
    
    # Get business profile and assistant
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == session["business_profile_id"]
    ).first()
    
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == session["assistant_id"]
    ).first()
    
    if not business_profile or not assistant:
        logger.warning(f"Business profile or assistant not found for session: {session_key}")
        raise HTTPException(status_code=404, detail="Business profile or assistant not found")
    
    # Check if knowledge base exists for business profile
    has_knowledge_base = bool(business_profile.knowledge_base)
    if has_knowledge_base:
        namespace = business_profile.knowledge_base.get('namespace')
        logger.info(f"Business has knowledge base with namespace: {namespace}")
    else:
        logger.warning(f"Business profile {business_profile.id} has no knowledge base configured")
    
    # Store user message in session
    session["messages"].append({
        "role": "user",
        "content": message.content,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        start_time = time.time()
        
        # Prepare chat context with business profile knowledge
        logger.info(f"Preparing chat context for web chat with assistant_id={assistant.id}")
        formatted_messages = prepare_chat_context(assistant.id, message.content, db)
        
        # Get AI response
        logger.info(f"Getting AI response for web chat with model={assistant.model}")
        ai_response = get_ai_response(formatted_messages, assistant.model)
        
        # Calculate response time
        response_time = time.time() - start_time
        logger.info(f"Response generated in {response_time:.2f} seconds")
        
        # Store AI response in session
        session["messages"].append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update analytics
        message_count = len(session["messages"])
        logger.info(f"Web chat session now has {message_count} messages")
        
        await analytics_service.record_analytics_direct(
            db=db,
            assistant_id=assistant.id,
            business_profile_id=business_profile.id,
            client_session_id=client_id,
            message_count=message_count,
            response_time=response_time
        )
        
        # Log a preview of the response
        response_preview = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
        logger.info(f"Web chat response: {response_preview}")
        
        # Return the response
        return {
            "content": ai_response,
            "role": "assistant",
            "client_id": client_id,
            "business_unique_id": business_unique_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing web chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.get("/history/{business_unique_id}")
async def get_chat_history(
    business_unique_id: str,
    client_id: str
):
    """
    Get the chat history for a business-client session.
    This endpoint is used by the web chat interface to load previous messages.
    """
    # Create session key
    session_key = f"{business_unique_id}_{client_id}"
    
    # Verify session exists
    if session_key not in chat_sessions:
        # Return empty history if no session exists yet
        return {
            "business_unique_id": business_unique_id,
            "client_id": client_id,
            "messages": []
        }
    
    # Return chat history
    return {
        "business_unique_id": business_unique_id,
        "client_id": client_id,
        "messages": chat_sessions[session_key]["messages"]
    }


