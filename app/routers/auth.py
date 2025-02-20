from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.token import BlacklistedToken
from app.schemas.user import UserLogin
from app.auth.jwt import verify_password, create_access_token
from app.dependencies import get_db, get_current_user
from fastapi.security import HTTPBearer

router = APIRouter()
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login_user(user: UserLogin,db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


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