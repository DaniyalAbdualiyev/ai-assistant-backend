from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict
from app.models.integration import Integration
from app.schemas.integration import IntegrationCreate, IntegrationResponse
from app.dependencies import get_current_user, get_db
from app.services.instagram import InstagramService
from app.services.whatsapp import WhatsAppService
from app.models.assistant import AIAssistant

router = APIRouter()

@router.post("/webhook/{platform}")
async def handle_webhook(
    platform: str,
    payload: Dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        if platform == "instagram":
            # Handle Instagram webhook
            background_tasks.add_task(handle_instagram_message, payload, db)
        elif platform == "whatsapp":
            # Handle WhatsApp webhook
            background_tasks.add_task(handle_whatsapp_message, payload, db)
            
        return {"status": "ok"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def handle_instagram_message(payload: Dict, db: Session):
    # Process Instagram messages
    pass

async def handle_whatsapp_message(payload: Dict, db: Session):
    # Process WhatsApp messages
    pass

@router.post("/add", response_model=IntegrationResponse)
async def add_integration(
    integration: IntegrationCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify assistant ownership
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == integration.assistant_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    # Check if integration already exists for this assistant/platform
    existing = db.query(Integration).filter(
        Integration.assistant_id == integration.assistant_id,
        Integration.platform == integration.platform
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail=f"This assistant already has a {integration.platform} integration")
    
    # Create integration record
    new_integration = Integration(
        user_id=current_user.id,
        assistant_id=integration.assistant_id,
        platform=integration.platform,
        credentials=integration.credentials
    )
    
    try:
        # Attempt to set up the integration with the platform
        if integration.platform == "whatsapp":
            whatsapp_service = WhatsAppService()
            await whatsapp_service.setup_webhook(integration.credentials)
        elif integration.platform == "instagram":
            instagram_service = InstagramService()
            await instagram_service.setup_webhook(integration.credentials)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")
        
        # Save the integration
        db.add(new_integration)
        db.commit()
        db.refresh(new_integration)
        
        return new_integration
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) 