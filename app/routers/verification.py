from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.verification import VerificationRequest, VerificationResponse
from app.services.verification import VerificationService
from app.database import get_db
from app.models.verification import VerificationCode

router = APIRouter(prefix="/verification", tags=["verification"])

@router.post("/request", response_model=VerificationResponse)
async def request_verification(
    request: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Request a new verification code for a phone number.
    """
    try:
        verification_code = VerificationService.create_verification_code(db, request)
        return VerificationResponse(
            message="Verification code sent successfully",
            expires_in_minutes=15
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/verify", response_model=VerificationResponse)
async def verify_code(
    request: VerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a phone number using the provided code.
    """
    try:
        is_valid = VerificationService.verify_code(db, request)
        if is_valid:
            return VerificationResponse(
                message="Phone number verified successfully",
                expires_in_minutes=0
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid verification code")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 