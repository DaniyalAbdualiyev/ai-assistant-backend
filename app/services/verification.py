import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.verification import VerificationCode
from app.models.business_profile import BusinessProfile
from app.schemas.verification import VerificationRequest, VerificationResponse

class VerificationService:
    @staticmethod
    def generate_code(length: int = 6) -> str:
        """Generate a random verification code."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def create_verification_code(db: Session, request: VerificationRequest) -> VerificationCode:
        """
        Create a new verification code for a phone number.
        """
        # Check if there's an existing active code
        existing_code = db.query(VerificationCode).filter(
            VerificationCode.phone_number == request.phone_number,
            VerificationCode.business_profile_id == request.business_profile_id,
            VerificationCode.expires_at > datetime.utcnow(),
            VerificationCode.is_used == False
        ).first()

        if existing_code:
            return existing_code

        # Generate new code
        code = VerificationService.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        verification_code = VerificationCode(
            phone_number=request.phone_number,
            business_profile_id=request.business_profile_id,
            code=code,
            expires_at=expires_at
        )

        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)

        # TODO: Send the code via SMS or other messaging service
        print(f"Verification code for {request.phone_number}: {code}")

        return verification_code

    @staticmethod
    def verify_code(db: Session, request: VerificationRequest) -> bool:
        """
        Verify a code for a phone number.
        """
        if not request.code:
            raise ValueError("Verification code is required")

        verification_code = db.query(VerificationCode).filter(
            VerificationCode.phone_number == request.phone_number,
            VerificationCode.business_profile_id == request.business_profile_id,
            VerificationCode.code == request.code,
            VerificationCode.expires_at > datetime.utcnow(),
            VerificationCode.is_used == False
        ).first()

        if not verification_code:
            return False

        # Mark the code as used
        verification_code.is_used = True
        verification_code.used_at = datetime.utcnow()
        db.commit()

        return True

    @staticmethod
    def verify_code_request(
        db: Session,
        request: VerificationRequest
    ) -> VerificationResponse:
        """Verify a code and return appropriate response."""
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.phone_number == request.phone_number,
            VerificationCode.business_profile_id == request.business_profile_id,
            VerificationCode.code == request.code,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()

        if not verification_code:
            return VerificationResponse(
                message="Invalid or expired verification code"
            )

        verification_code.is_used = True
        verification_code.used_at = datetime.utcnow()
        db.commit()

        return VerificationResponse(
            message="Verification successful",
            expires_at=verification_code.expires_at
        ) 