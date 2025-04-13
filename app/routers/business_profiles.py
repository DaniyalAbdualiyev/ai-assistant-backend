from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import json
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.schemas.business_profile import BusinessProfileCreate, BusinessProfileResponse
from app.dependencies import get_current_user, get_db
from app.services.file_processor import process_file
from app.services.vector_store import store_embeddings

router = APIRouter()

@router.post("/create", response_model=BusinessProfileResponse)
async def create_business_profile(
    profile: BusinessProfileCreate,
    assistant_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify assistant ownership
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")

    # Create business profile
    new_profile = BusinessProfile(
        assistant_id=assistant_id,
        business_name=profile.business_name,
        business_type=profile.business_type,
        tone_preferences=profile.tone_preferences
    )
    
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile

@router.post("/upload/{profile_id}")
async def upload_business_documents(
    profile_id: int,
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file type
    if not file.filename.endswith(('.pdf', '.docx', '.txt')):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF, DOCX, or TXT files."
        )
    
    # Get business profile
    profile = db.query(BusinessProfile).join(AIAssistant).filter(
        BusinessProfile.id == profile_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    try:
        # Process the uploaded file
        processed_data = await process_file(file)
        if not processed_data:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Store embeddings in vector database
        knowledge_base_id = store_embeddings(processed_data)
        
        # Update business profile with knowledge base reference
        profile.knowledge_base = {"id": knowledge_base_id}
        db.commit()
        
        return {"message": "File processed successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 