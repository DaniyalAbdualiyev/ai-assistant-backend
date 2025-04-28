from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.analytics import ConversationAnalytics
from app.models.business_profile import BusinessProfile
from app.models.assistant import AIAssistant
from app.schemas.analytics import ConversationAnalytics as ConversationAnalyticsSchema
from app.schemas.analytics import AnalyticsSummary, TimeRangeAnalytics
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_service = AnalyticsService()


@router.get("/business/{business_id}/summary", response_model=AnalyticsSummary)
async def get_business_analytics_summary(
    business_id: int,
    days: Optional[int] = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics summary for a business profile.
    Only accessible by the business owner.
    """
    # Check if business profile exists and belongs to the current user
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.id == business_id
    ).first()
    
    if not business_profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    # Check if the business profile's assistant belongs to the current user
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == business_profile.assistant_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=403, detail="Not authorized to access this business profile")
    
    # Get analytics summary
    summary = await analytics_service.get_business_analytics_summary(db, business_id, days)
    return summary


@router.get("/assistant/{assistant_id}/summary", response_model=AnalyticsSummary)
async def get_assistant_analytics_summary(
    assistant_id: int,
    days: Optional[int] = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics summary for a specific assistant.
    Only accessible by the assistant owner.
    """
    # Check if assistant exists and belongs to the current user
    assistant = db.query(AIAssistant).filter(
        AIAssistant.id == assistant_id,
        AIAssistant.user_id == current_user.id
    ).first()
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found or not authorized")
    
    # Get analytics summary
    summary = await analytics_service.get_assistant_analytics_summary(db, assistant_id, days)
    return summary
