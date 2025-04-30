from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models.assistant import AIAssistant
from app.models.message import Message
from app.models.user import User
from app.schemas.message import MessageCreate, MessageResponse
from app.dependencies import get_current_user, get_db
from dotenv import load_dotenv
from openai import OpenAI
import os
from datetime import datetime
import time
from app.models.business_profile import BusinessProfile
from app.services.vector_store import search_similar_texts
from app.services.analytics_service import AnalyticsService
import logging
from app.services.ai_service import get_business_temperature


load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client.api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

router = APIRouter()
analytics_service = AnalyticsService()

@router.post("/chat", response_model=MessageResponse)
async def chat_with_ai(
    message: MessageCreate,
    temperature: Optional[float] = Query(None, ge=0.0, le=2.0, description="Response creativity (0.0-2.0)"),
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """
    Process a chat message with AI assistant:
    1. Verify the assistant exists and user has access
    2. Save the user's message
    3. Get chat history for context
    4. Get AI response
    5. Save and return the AI response
    """
    
    # Step 1: Verify assistant and user permissions
    assistant = verify_assistant_access(message.assistant_id, current_user.id, db)
    
    # Get business profile for the assistant (if exists)
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.assistant_id == assistant.id
    ).first()
    
    # Generate a client session ID for analytics
    client_session_id = f"user_{current_user.id}_assistant_{assistant.id}_{datetime.utcnow().strftime('%Y%m%d')}"
    
    # Record client session for analytics if it's the first message
    client_ip = request.client.host if request and request.client else None
    client_device = request.headers.get("User-Agent") if request else None
    
    if business_profile:
        await analytics_service.record_client_session(
            db=db,
            client_session_id=client_session_id,
            assistant_id=assistant.id,
            business_profile_id=business_profile.id,
            client_ip=client_ip,
            client_device=client_device
        )
    
    # Step 2: Save user's message and create placeholder for AI response
    db_message = save_initial_message(
        user_query=message.content,
        assistant_id=message.assistant_id,
        user_id=current_user.id,
        db=db
    )
    
    try:
        start_time = time.time()
        
        # Step 3: Get and format chat history
        formatted_messages = prepare_chat_context(assistant.id, message.content, db)
        
        # Step 4: Get AI response
        # Get the business type from assistant profile if available
        business_type = getattr(assistant, 'business_type', 'selling')
        
        # Get AI response with business-type specific temperature
        ai_response = get_ai_response(formatted_messages, assistant.model, business_type)
        
        # Step 5: Save and return AI response
        response = save_and_format_response(db_message, ai_response, db)
        
        # Update analytics if there's a business profile
        if business_profile:
            # Count messages for this session
            message_count = db.query(Message).filter(
                Message.assistant_id == assistant.id,
                Message.user_id == current_user.id
            ).count()
            
            await analytics_service.record_analytics_direct(
                db=db,
                assistant_id=assistant.id,
                business_profile_id=business_profile.id,
                client_session_id=client_session_id,
                message_count=message_count,
                response_time=response_time
            )
        
        return response
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

def verify_assistant_access(assistant_id: int, user_id: int, db: Session) -> AIAssistant:
    """Verify that the assistant exists and the user has access to it."""
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    if assistant.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to use this assistant")
    return assistant

def save_initial_message(user_query: str, assistant_id: int, user_id: int, db: Session) -> Message:
    """Save the initial message with a placeholder AI response."""
    db_message = Message(
        user_query=user_query,
        ai_response="Processing your request...",
        assistant_id=assistant_id,
        user_id=user_id,
        timestamp=datetime.utcnow()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def prepare_chat_context(assistant_id: int, current_message: str, db: Session) -> list:
    """Get chat history and format it for the AI model."""
    try:
        # Get the business profile for this assistant
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.assistant_id == assistant_id
        ).first()
        
        # Initialize context with system message
        formatted_messages = [{
            "role": "system",
            "content": "You are a helpful AI assistant for a business. Use the provided business knowledge to answer questions accurately."
        }]
        
        # If we have a business profile with knowledge base, search for relevant information
        if business_profile and business_profile.knowledge_base:
            # Get the namespace from the business profile
            namespace = business_profile.knowledge_base.get('namespace')
            if not namespace:
                # Fallback to a default namespace format if not stored
                namespace = f"business_{business_profile.id}"
                
            # Search for relevant documents using the business-specific namespace
            relevant_docs = search_similar_texts(current_message, namespace=namespace)
            
            if relevant_docs:
                # Add relevant business knowledge to context
                knowledge_context = "\n".join([
                    f"Business Knowledge: {doc.metadata['text']}"
                    for doc in relevant_docs
                ])
                formatted_messages.append({
                    "role": "system",
                    "content": knowledge_context
                })
        
        # Get recent chat history
        chat_history = db.query(Message).filter(
            Message.assistant_id == assistant_id
        ).order_by(Message.timestamp.desc()).limit(5).all()
        
        # Add chat history
        for msg in reversed(chat_history):
            formatted_messages.extend([
                {"role": "user", "content": msg.user_query},
                {"role": "assistant", "content": msg.ai_response}
            ])
        
        # Add current message
        formatted_messages.append({"role": "user", "content": current_message})
        return formatted_messages
        
    except Exception as e:
        logging.error(f"Error preparing chat context: {str(e)}")
        # Fallback to basic context if there's an error
        return [{"role": "user", "content": current_message}]

def get_ai_response(formatted_messages: list, model: str, business_type: str = "selling") -> str:
    """Get response from OpenAI API with temperature based on business type."""
    try:
        # Get appropriate temperature for this business type
        temperature = get_business_temperature(business_type)
        
        response = client.chat.completions.create(
            model=model,
            messages=formatted_messages,
            temperature=temperature,  # Use business-type specific temperature
            max_tokens=1000
        )
        return response.choices[0].message.content if response.choices else "AI could not generate a response"
    except Exception as e:
        return "Connection with AI assistant failed. Please try again later."

def save_and_format_response(db_message: Message, ai_response: str, db: Session) -> MessageResponse:
    """Save the AI response and format it for the API response."""
    # Update the message with AI response
    db_message.ai_response = ai_response
    db.commit()
    db.refresh(db_message)
    
    # Format response
    return MessageResponse(
        content=db_message.ai_response,
        role="assistant",
        assistant_id=db_message.assistant_id,
        id=db_message.id,
        timestamp=db_message.timestamp,
        user_id=db_message.user_id
    )

@router.get("/history/{assistant_id}", response_model=List[MessageResponse])
async def get_chat_history(
    assistant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verify assistant exists and belongs to user
        assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        if assistant.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view these messages")

        # Get all messages for this assistant
        messages = db.query(Message).filter(
            Message.assistant_id == assistant_id
        ).order_by(Message.timestamp.asc()).all()

        # Convert Message models to MessageResponse format
        formatted_messages = []
        for msg in messages:
            # Create user message
            formatted_messages.append(MessageResponse(
                content=msg.user_query,
                role="user",
                assistant_id=msg.assistant_id,
                id=msg.id,
                timestamp=msg.timestamp,
                user_id=msg.user_id
            ))
            # Create assistant message
            if msg.ai_response and msg.ai_response != "Processing your request...":
                formatted_messages.append(MessageResponse(
                    content=msg.ai_response,
                    role="assistant",
                    assistant_id=msg.assistant_id,
                    id=msg.id,
                    timestamp=msg.timestamp,
                    user_id=msg.user_id
                ))

        return formatted_messages

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific message by ID."""
    try:
        # Get the message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify user has access to this message
        if message.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this message")
        
        # Return formatted message
        return MessageResponse(
            content=message.user_query if message.user_query else message.ai_response,
            role="user" if message.user_query else "assistant",
            assistant_id=message.assistant_id,
            id=message.id,
            timestamp=message.timestamp,
            user_id=message.user_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
    message_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a specific message."""
    try:
        # Get the message
        db_message = db.query(Message).filter(Message.id == message_id).first()
        if not db_message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify user has access to this message
        if db_message.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to modify this message")
        
        # Update the message
        db_message.user_query = message.content
        
        # Get new AI response for the updated message
        formatted_messages = prepare_chat_context(db_message.assistant_id, message.content, db)
        assistant = db.query(AIAssistant).filter(AIAssistant.id == db_message.assistant_id).first()
        ai_response = get_ai_response(formatted_messages, assistant.model)
        db_message.ai_response = ai_response
        
        db.commit()
        db.refresh(db_message)
        
        # Return formatted response
        return MessageResponse(
            content=db_message.ai_response,
            role="assistant",
            assistant_id=db_message.assistant_id,
            id=db_message.id,
            timestamp=db_message.timestamp,
            user_id=db_message.user_id
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{message_id}", response_model=dict)
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific message."""
    try:
        # Get the message
        message = db.query(Message).filter(Message.id == message_id).first()
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Verify user has access to this message
        if message.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this message")
        
        # Delete the message
        db.delete(message)
        db.commit()
        
        return {"message": "Message successfully deleted"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear/{assistant_id}", response_model=dict)
async def clear_chat_history(
    assistant_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all messages between the user and a specific AI assistant."""
    try:
        # Verify assistant exists and belongs to user
        assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        if assistant.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete these messages")
        
        # Delete all messages between user and assistant
        deleted = db.query(Message).filter(
            Message.assistant_id == assistant_id,
            Message.user_id == current_user.id
        ).delete()
        
        db.commit()
        
        return {
            "message": f"Successfully deleted {deleted} messages",
            "count": deleted
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

def get_business_temperature(business_type: str) -> float:
    """Get appropriate temperature for different business types"""
    temperature_map = {
        "selling": 0.8,        # More creative for sales
        "consulting": 0.6,     # Balanced for consulting
        "tech_support": 0.3,   # More precise for support
        "customer_service": 0.5  # Middle ground
    }
    return temperature_map.get(business_type, 0.7)  # Default to 0.7