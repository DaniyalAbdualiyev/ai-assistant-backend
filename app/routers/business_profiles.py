from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from app.dependencies import get_db, get_current_user
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.schemas.business_profile import (
    BusinessProfileCreate,
    BusinessProfileUpdate,
    BusinessProfileResponse,
    FileUploadResponse,
    KnowledgeBaseUpdate
)
from app.services.file_processor import FileProcessor
from app.services.vector_store import add_to_knowledge_base
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=BusinessProfileResponse)
async def create_business_profile(
    profile: BusinessProfileCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a new business profile with questionnaire answers
    """
    try:
        # Create AI Assistant first
        assistant = AIAssistant(
            name=f"{profile.business_name} Assistant",
            model="gpt-4",  # Default model
            language=profile.language,
            user_id=current_user.id
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)

        # Create Business Profile
        db_profile = BusinessProfile(
            **profile.dict(exclude={'tone_preferences'}),
            tone_preferences=profile.tone_preferences.dict(),
            assistant_id=assistant.id
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)

        return db_profile

    except Exception as e:
        logger.error(f"Error creating business profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{profile_id}/upload", response_model=FileUploadResponse)
async def upload_business_file(
    profile_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Upload a file for business knowledge base
    """
    try:
        # Verify profile ownership
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == profile_id,
            AIAssistant.user_id == current_user.id
        ).join(AIAssistant).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Business profile not found")

        # Process file
        processor = FileProcessor()
        file_content = await file.read()
        processed_content = await processor.process_file(file_content, file.filename)

        # Update knowledge base
        if not profile.knowledge_base:
            profile.knowledge_base = {"files": []}
        
        file_metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "processed": True
        }
        
        profile.knowledge_base["files"].append(file_metadata)
        db.commit()

        # Add to vector store
        add_to_knowledge_base(
            texts=[processed_content],
            metadata=[{"source": file.filename, "type": "file"}],
            namespace=f"business_{profile_id}"
        )

        return FileUploadResponse(
            file_id=str(len(profile.knowledge_base["files"]) - 1),
            **file_metadata
        )

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{profile_id}/knowledge-base", response_model=BusinessProfileResponse)
async def update_knowledge_base(
    profile_id: int,
    update: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Add or update knowledge base content
    """
    try:
        # Verify profile ownership
        profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == profile_id,
            AIAssistant.user_id == current_user.id
        ).join(AIAssistant).first()

        if not profile:
            raise HTTPException(status_code=404, detail="Business profile not found")

        # Update knowledge base
        if not profile.knowledge_base:
            profile.knowledge_base = {"texts": []}
        
        profile.knowledge_base["texts"].append({
            "content": update.content,
            "source": update.source,
            "type": update.type
        })
        
        db.commit()

        # Add to vector store
        add_to_knowledge_base(
            texts=[update.content],
            metadata=[{"source": update.source, "type": update.type}],
            namespace=f"business_{profile_id}"
        )

        return profile

    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{profile_id}", response_model=BusinessProfileResponse)
async def get_business_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get business profile details
    """
    profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == profile_id,
        AIAssistant.user_id == current_user.id
    ).join(AIAssistant).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    return profile

@router.put("/{profile_id}", response_model=BusinessProfileResponse)
async def update_business_profile(
    profile_id: int,
    profile_update: BusinessProfileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update business profile details
    """
    db_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == profile_id,
        AIAssistant.user_id == current_user.id
    ).join(AIAssistant).first()

    if not db_profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    update_data = profile_update.dict(exclude_unset=True)
    if "tone_preferences" in update_data:
        update_data["tone_preferences"] = update_data["tone_preferences"].dict()

    for key, value in update_data.items():
        setattr(db_profile, key, value)

    db.commit()
    db.refresh(db_profile)
    return db_profile 