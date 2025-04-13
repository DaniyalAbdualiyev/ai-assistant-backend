from fastapi import APIRouter, Depends, HTTPException, status, Security
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import SessionLocal
from app.models.user import User
from app.models.token import BlacklistedToken
from app.schemas.user import UserLogin, UserCreate, UserResponse
from app.auth.jwt import verify_password, create_access_token, hash_password
from app.dependencies import get_db, get_current_user
from fastapi.security import HTTPBearer
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user.password)
        db_user = User(
            name=user.name, 
            email=user.email, 
            password_hash=hashed_password
            # is_admin is not specified, will use default value
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Registration failed. Please try again later."
        )

@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return an access token"""
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user or not verify_password(user.password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid credentials"
            )

        access_token = create_access_token({"sub": db_user.email})
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Login failed. Please try again later."
        )

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Security(security),
    db: Session = Depends(get_db)
):
    """Log out a user by blacklisting their token"""
    try:
        blacklisted_token = BlacklistedToken(token=token.credentials)
        db.add(blacklisted_token)
        db.commit()
        return {"message": "Successfully logged out"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Logout failed")

@router.get("/check-email")
async def check_email_exists(email: str, db: Session = Depends(get_db)):
    """Check if an email is already registered"""
    try:
        result = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        exists = result.rowcount > 0
        return {"exists": exists}
    except Exception:
        # Return false on error to avoid blocking registration
        return {"exists": False, "error": "Could not check email"}