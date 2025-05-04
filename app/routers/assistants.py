from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.schemas.assistant import AssistantCreate, AssistantResponse, AssistantQuery, BusinessProfileBase
from app.dependencies import get_current_user, get_db
from app.middleware.subscription_middleware import verify_active_subscription
from app.services.ai_service import AIService
from app.services.file_processor import process_file
from app.services.vector_store import store_embeddings
from PyPDF2 import PdfReader
import io
import os
import logging
from dotenv import load_dotenv
import time

load_dotenv()

# Get the base URL from environment variables or use a default
BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

router = APIRouter()
ai_service = AIService()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/")
def create_assistant(
    assistant: AssistantCreate, 
    db: Session = Depends(get_db),
    user=Depends(verify_active_subscription)  # Require active subscription
):
    # Create new assistant
    new_assistant = AIAssistant(name=assistant.name, model=assistant.model, language=assistant.language, user_id=user.id)
    db.add(new_assistant)
    db.commit()
    db.refresh(new_assistant)
    
    chat_url = None
    business_profile = None
    
    # If business profile data is provided, create a business profile
    if assistant.business_profile:
        business_profile = BusinessProfile(
            business_name=assistant.business_profile.business_name,
            business_type=assistant.business_profile.business_type,
            tone_preferences=assistant.business_profile.tone_preferences,
            assistant_id=new_assistant.id
        )
        db.add(business_profile)
        db.commit()
        db.refresh(business_profile)
        

        
        # Generate chat path and full URL for the business profile
        chat_path = f"/web-chat/{business_profile.unique_id}"
        chat_url = f"{BASE_URL}{chat_path}"
    
    # Prepare response with assistant data and chat link if available
    response = {
        "id": new_assistant.id,
        "name": new_assistant.name,
        "model": new_assistant.model,
        "language": new_assistant.language,
        "user_id": new_assistant.user_id,
        "created_at": new_assistant.created_at
    }
    
    # Add business profile and chat URL if available
    if business_profile:
        # Ensure unique_id is a string
        business_profile.unique_id = str(business_profile.unique_id)
        
        response["business_profile"] = {
            "id": business_profile.id,
            "business_name": business_profile.business_name,
            "business_type": business_profile.business_type,
            "unique_id": business_profile.unique_id
        }
        
    if chat_url:
        response["chat_url"] = chat_url
        response["chat_path"] = chat_path
    
    return response

@router.get("/", response_model=List[AssistantResponse])
def get_assistants(db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistants = db.query(AIAssistant).filter(AIAssistant.user_id == user.id).all()
    
    # Process each assistant to ensure UUID is converted to string
    for assistant in assistants:
        if assistant.business_profile:
            # Ensure unique_id is a string
            assistant.business_profile.unique_id = str(assistant.business_profile.unique_id)
    
    return assistants

@router.get("/{assistant_id}")
def get_assistant(assistant_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    # Prepare response with assistant data
    response = {
        "id": assistant.id,
        "name": assistant.name,
        "model": assistant.model,
        "language": assistant.language,
        "user_id": assistant.user_id,
        "created_at": assistant.created_at
    }
    
    # If there's a business profile, include its details and chat link
    if assistant.business_profile:
        business_profile = assistant.business_profile
        
        # Ensure unique_id is a string
        business_profile.unique_id = str(business_profile.unique_id)
        
        if business_profile:
            response["business_profile"] = {
                "id": business_profile.id,
                "business_name": business_profile.business_name,
                "business_type": business_profile.business_type,
                "unique_id": business_profile.unique_id
            }
            
            # Generate chat URL
            chat_url = f"{BASE_URL}/web-chat/{business_profile.unique_id}"
            response["chat_url"] = chat_url
    
    return response

@router.get("/{assistant_id}/chat-link")
def get_assistant_chat_link(assistant_id: int, db: Session = Depends(get_db), user=Depends(verify_active_subscription)):
    """Get chat link for an assistant's business profile"""
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id, 
        AIAssistant.user_id == user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
        
    # Get business profile
    if not assistant.business_profile:
        raise HTTPException(status_code=404, detail="No business profile found for this assistant")
        
    business_profile = assistant.business_profile
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Generate chat URL
    chat_url = f"{BASE_URL}/web-chat/{business_profile.unique_id}"
    
    return {
        "business_name": business_profile.business_name,
        "unique_id": business_profile.unique_id,
        "chat_url": chat_url
    }

@router.put("/{assistant_id}", response_model=AssistantResponse)
def update_assistant(assistant_id: int, assistant_data: AssistantCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    assistant.name = assistant_data.name
    assistant.model = assistant_data.model
    assistant.language = assistant_data.language
    db.commit()
    db.refresh(assistant)
    return assistant

@router.delete("/{assistant_id}")
def delete_assistant(assistant_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    assistant = db.query(AIAssistant).filter(AIAssistant.id == assistant_id, AIAssistant.user_id == user.id).first()
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
        
    # Delete business profile if it exists
    if hasattr(assistant, 'business_profile') and assistant.business_profile:
        db.delete(assistant.business_profile)

    db.delete(assistant)
    db.commit()
    return {"message": "Assistant deleted successfully"}

@router.post("/{assistant_id}/chat")
async def chat_with_assistant(
    assistant_id: int,
    query: AssistantQuery,
    db: Session = Depends(get_db),
    user=Depends(verify_active_subscription)  # Require active subscription
):
    """Chat with an AI assistant"""
    logger.info(f"[CHAT] Received chat request for assistant_id={assistant_id}, query={query.text[:100]}...")
    
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id, 
        AIAssistant.user_id == user.id
    ).first()
    
    if not assistant:
        logger.warning(f"[CHAT] Assistant not found: assistant_id={assistant_id}, user_id={user.id}")
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Check if this assistant has a business profile with knowledge base
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.assistant_id == assistant.id
    ).first()
    
    if business_profile and business_profile.knowledge_base:
        kb_id = business_profile.knowledge_base.get('id', 'None')
        kb_namespace = business_profile.knowledge_base.get('namespace', 'None')
        logger.info(f"[CHAT] Assistant has knowledge base: id={kb_id}, namespace={kb_namespace}")
    else:
        logger.warning(f"[CHAT] Assistant {assistant_id} has no knowledge base configured")

    # Use query language if provided, otherwise use assistant's default language
    language = query.language if query.language else assistant.language

    config = {
        "language": language,
        "tone": query.tone if hasattr(query, 'tone') and query.tone else "normal",
        "business_type": query.business_type if hasattr(query, 'business_type') else "selling"
    }
    
    logger.info(f"[CHAT] Using config: {config}")

    try:
        logger.info(f"[CHAT] Getting AI response for assistant_id={assistant_id}")
        start_time = time.time()
        
        # Pass the db session to the AI service
        response = await ai_service.get_response(
            query.text,
            config,
            assistant_id,
            user.id,
            db=db  # Pass database session
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"[CHAT] Response generated in {elapsed_time:.2f} seconds")
        
        # Log a preview of the response
        response_preview = response[:200] + "..." if len(response) > 200 else response
        logger.info(f"[CHAT] AI response preview: {response_preview}")
        
        return {"response": response}
    except Exception as e:
        logger.error(f"[CHAT] Error getting AI response: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{assistant_id}/upload-knowledge")
async def upload_knowledge(
    assistant_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(verify_active_subscription)  # Require active subscription
):
    """Upload knowledge base document for an assistant"""
    logger.info(f"Knowledge base upload started for assistant_id={assistant_id}, file={file.filename}")
    
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id, 
        AIAssistant.user_id == user.id
    ).first()
    
    if not assistant:
        logger.warning(f"Assistant not found: assistant_id={assistant_id}, user_id={user.id}")
        raise HTTPException(status_code=404, detail="Assistant not found")
        
    # Get business profile if it exists
    business_profile = None
    if hasattr(assistant, 'business_profile') and assistant.business_profile:
        business_profile = assistant.business_profile
        logger.info(f"Using existing business profile: profile_id={business_profile.id}")
    
    # If no business profile exists, create one
    if not business_profile:
        logger.warning(f"No business profile found for assistant_id={assistant_id}")
        raise HTTPException(status_code=400, detail="Assistant has no business profile. Please create one first.")

    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        logger.warning(f"Invalid file type: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, or TXT files."
        )

    try:
        logger.info(f"Processing file: {file.filename}")
        # Process the uploaded file
        processed_data = await process_file(file)
        if not processed_data:
            logger.error(f"Failed to extract text from file: {file.filename}")
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        logger.info(f"Text extracted from file, length: {len(processed_data)} characters")
        
        # Store embeddings in vector database with business profile namespace
        namespace = f"business_{business_profile.id}"
        logger.info(f"Storing embeddings in namespace: {namespace}")
        
        knowledge_base_id = store_embeddings(processed_data, namespace=namespace)
        logger.info(f"Knowledge base created with ID: {knowledge_base_id}")
        
        # Update business profile with knowledge base reference
        business_profile.knowledge_base = {"id": knowledge_base_id, "namespace": namespace}
        db.commit()
        logger.info(f"Business profile updated with knowledge base reference")
        
        # Generate chat path and full URL for the business profile
        chat_path = f"/web-chat/{business_profile.unique_id}"
        chat_url = f"{BASE_URL}{chat_path}"
        
        # Ensure unique_id is a string
        business_profile.unique_id = str(business_profile.unique_id)
        
        logger.info(f"Knowledge base upload completed successfully for assistant_id={assistant_id}")
        
        return {
            "message": "Knowledge base updated successfully",
            "chat_url": chat_url,
            "chat_path": chat_path,
            "business_profile": {
                "id": business_profile.id,
                "business_name": business_profile.business_name,
                "business_type": business_profile.business_type,
                "unique_id": business_profile.unique_id
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading knowledge base: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))