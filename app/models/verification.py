from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, index=True)
    code = Column(String)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)

    business_profile = relationship("BusinessProfile", back_populates="verification_codes")

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired() 