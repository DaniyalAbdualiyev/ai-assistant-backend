from fastapi import Request, HTTPException, Depends
from app.dependencies import get_current_user
from app.models.user import User
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def admin_required(func):
    """
    Decorator to check if the user is an admin.
    This should be used after the get_current_user dependency.
    """
    @wraps(func)
    async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
        if not current_user.is_admin:
            logger.warning(f"Non-admin user {current_user.id} attempted to access admin endpoint")
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        return await func(*args, current_user=current_user, **kwargs)
    return wrapper

async def verify_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency to verify admin status.
    Use this as a dependency in FastAPI routes.
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.id} attempted to access admin endpoint")
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user
