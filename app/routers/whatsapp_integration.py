from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.assistant import AIAssistant
from app.models.business_profile import BusinessProfile
from app.models.whatsapp_integration import WhatsAppIntegration
from app.schemas.whatsapp_integration import (
    WhatsAppIntegrationCreate,
    WhatsAppIntegrationResponse,
    WhatsAppIntegrationUpdate
)
from app.services.whatsapp import WhatsAppService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
whatsapp_service = WhatsAppService()

@router.post("/", response_model=WhatsAppIntegrationResponse)
async def create_whatsapp_integration(
    integration: WhatsAppIntegrationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new WhatsApp integration for an assistant"""
    # Verify assistant exists and user has access
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == integration.assistant_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found or you don't have access")
    
    # Verify business profile exists
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == integration.business_profile_id,
        BusinessProfile.assistant_id == integration.assistant_id
    ).first()
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Check if this phone number is already integrated
    existing = db.query(WhatsAppIntegration).filter(
        WhatsAppIntegration.phone_number_id == integration.phone_number_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="This WhatsApp number is already integrated")
    
    # Create the integration
    db_integration = WhatsAppIntegration(
        phone_number_id=integration.phone_number_id,
        display_phone_number=integration.display_phone_number,
        business_profile_id=integration.business_profile_id,
        assistant_id=integration.assistant_id,
        is_active=integration.is_active
    )
    
    try:
        db.add(db_integration)
        db.commit()
        db.refresh(db_integration)
        return db_integration
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating WhatsApp integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create integration: {str(e)}")

@router.get("/", response_model=List[WhatsAppIntegrationResponse])
async def get_whatsapp_integrations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all WhatsApp integrations for the current user"""
    return db.query(WhatsAppIntegration).join(
        AIAssistant, WhatsAppIntegration.assistant_id == AIAssistant.id
    ).filter(
        AIAssistant.user_id == current_user.id
    ).all()

@router.get("/{integration_id}", response_model=WhatsAppIntegrationResponse)
async def get_whatsapp_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific WhatsApp integration"""
    integration = db.query(WhatsAppIntegration).join(
        AIAssistant, WhatsAppIntegration.assistant_id == AIAssistant.id
    ).filter(
        WhatsAppIntegration.id == integration_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")
    
    return integration

@router.put("/{integration_id}", response_model=WhatsAppIntegrationResponse)
async def update_whatsapp_integration(
    integration_id: int,
    integration_data: WhatsAppIntegrationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a WhatsApp integration"""
    # Get the integration
    integration = db.query(WhatsAppIntegration).join(
        AIAssistant, WhatsAppIntegration.assistant_id == AIAssistant.id
    ).filter(
        WhatsAppIntegration.id == integration_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")
    
    # Update fields if provided
    if integration_data.phone_number_id is not None:
        integration.phone_number_id = integration_data.phone_number_id
    
    if integration_data.display_phone_number is not None:
        integration.display_phone_number = integration_data.display_phone_number
    
    if integration_data.business_profile_id is not None:
        # Verify business profile exists
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == integration_data.business_profile_id
        ).first()
        
        if not business_profile:
            raise HTTPException(status_code=404, detail="Business profile not found")
        
        integration.business_profile_id = integration_data.business_profile_id
    
    if integration_data.assistant_id is not None:
        # Verify assistant exists and user has access
        assistant = db.query(AIAssistant).filter(
            AIAssistant.id == integration_data.assistant_id,
            AIAssistant.user_id == current_user.id
        ).first()
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found or you don't have access")
        
        integration.assistant_id = integration_data.assistant_id
    
    if integration_data.is_active is not None:
        integration.is_active = integration_data.is_active
    
    try:
        db.commit()
        db.refresh(integration)
        return integration
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating WhatsApp integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update integration: {str(e)}")

@router.delete("/{integration_id}")
async def delete_whatsapp_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a WhatsApp integration"""
    integration = db.query(WhatsAppIntegration).join(
        AIAssistant, WhatsAppIntegration.assistant_id == AIAssistant.id
    ).filter(
        WhatsAppIntegration.id == integration_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")
    
    try:
        db.delete(integration)
        db.commit()
        return {"message": "WhatsApp integration deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting WhatsApp integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete integration: {str(e)}")

@router.post("/{integration_id}/verify", response_model=dict)
async def verify_whatsapp_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify a WhatsApp integration by testing the connection"""
    integration = db.query(WhatsAppIntegration).join(
        AIAssistant, WhatsAppIntegration.assistant_id == AIAssistant.id
    ).filter(
        WhatsAppIntegration.id == integration_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="WhatsApp integration not found")
    
    # Create a WhatsApp service instance with the integration's credentials
    service = WhatsAppService(
        phone_number_id=integration.phone_number_id,
        access_token=None  # Using the default from environment variables
    )
    
    try:
        # Verify the connection by getting the business profile
        profile = await service.get_business_profile()
        if profile:
            return {
                "status": "success",
                "message": "WhatsApp integration verified successfully",
                "profile": profile
            }
        else:
            return {
                "status": "error",
                "message": "Failed to verify WhatsApp integration"
            }
    except Exception as e:
        logger.error(f"Error verifying WhatsApp integration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify integration: {str(e)}")
