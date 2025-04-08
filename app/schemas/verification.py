from datetime import datetime
from pydantic import BaseModel, constr
from typing import Optional

class VerificationRequest(BaseModel):
    phone_number: constr(regex=r'^\+?[1-9]\d{1,14}$')
    code: Optional[str] = None
    business_profile_id: int

class VerificationResponse(BaseModel):
    message: str
    expires_in_minutes: int 