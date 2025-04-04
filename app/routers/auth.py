from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.token import BlacklistedToken
from app.schemas.user import UserLogin, UserCreate, UserResponse
from app.auth.jwt import verify_password, create_access_token, hash_password
from app.dependencies import get_db, get_current_user
from fastapi.security import HTTPBearer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Log registration attempt
        logger.info(f"Registration attempt for email: {user.email}")
        
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.warning(f"Email already registered: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = hash_password(user.password)
        db_user = User(name=user.name, email=user.email, password_hash=hashed_password)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        logger.info(f"User registered successfully: {user.email}")
        return db_user
    except Exception as e:
        db.rollback()
        # Log the specific error
        logger.error(f"Registration error for {user.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@router.post("/login")
def login_user(user: UserLogin,db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Security(security),
    db: Session = Depends(get_db)
):
    try:
        blacklisted_token = BlacklistedToken(token=token.credentials)
        db.add(blacklisted_token)
        db.commit()
        return {"message": "Successfully logged out"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Logout failed")