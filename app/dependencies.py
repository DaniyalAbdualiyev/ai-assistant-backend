from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from app.auth.jwt import SECRET_KEY, ALGORITHM
from app.models.user import User
from app.database import SessionLocal
from sqlalchemy.orm import Session
from app.models.token import BlacklistedToken

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def get_current_user(token: str = Depends(security), db: Session = Depends(get_db)):
    try:
        # Check if token is blacklisted
        blacklisted = db.query(BlacklistedToken).filter(
            BlacklistedToken.token == token.credentials
        ).first()
        if blacklisted:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
