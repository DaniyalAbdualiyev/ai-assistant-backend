from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.user_subscription import UserSubscription
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def verify_active_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Middleware to verify that a user has an active subscription.
    This should be used as a dependency in routes that require an active subscription.
    """
    # Admin users bypass subscription check
    if current_user.is_admin:
        return current_user
        
    # Find active subscriptions that haven't expired
    active_subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.is_active == True,
        UserSubscription.end_date >= datetime.utcnow()
    ).first()
    
    if not active_subscription:
        logger.warning(f"User {current_user.id} attempted to access premium feature without active subscription")
        raise HTTPException(
            status_code=403,
            detail="Active subscription required. Please subscribe to access this feature."
        )
    
    return current_user
