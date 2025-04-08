import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.verification_code import VerificationCode
from app.models.business_profile import BusinessProfile

class VerificationService:
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """Generate a random verification code."""
        return ''.join(random.choices(string.digits, k=length))

    @staticmethod
    def create_verification_code(
        db: Session,
        phone_number: str,
        business_profile_id: int,
        expires_in_minutes: int = 5
    ) -> VerificationCode:
        """Create a new verification code for a phone number."""
        # Invalidate any existing codes for this phone number
        db.query(VerificationCode).filter(
            VerificationCode.phone_number == phone_number,
            VerificationCode.used == False
        ).update({"used": True})
        
        # Generate new code
        code = VerificationService.generate_verification_code()
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)
        
        verification_code = VerificationCode(
            phone_number=phone_number,
            code=code,
            expires_at=expires_at,
            business_profile_id=business_profile_id
        )
        
        db.add(verification_code)
        db.commit()
        db.refresh(verification_code)
        
        return verification_code

    @staticmethod
    def verify_code(
        db: Session,
        phone_number: str,
        code: str
    ) -> bool:
        """Verify a code for a phone number."""
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.phone_number == phone_number,
            VerificationCode.code == code,
            VerificationCode.used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        if not verification_code:
            return False
            
        # Mark code as used
        verification_code.used = True
        db.commit()
        
        # Update business profile verification status
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.id == verification_code.business_profile_id
        ).first()
        
        if business_profile:
            business_profile.verified = True
            business_profile.verified_at = datetime.utcnow()
            db.commit()
            
        return True

    @staticmethod
    def get_active_code(
        db: Session,
        phone_number: str
    ) -> VerificationCode:
        """Get the active verification code for a phone number."""
        return db.query(VerificationCode).filter(
            VerificationCode.phone_number == phone_number,
            VerificationCode.used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first() 