from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WhatsAppIntegrationBase(BaseModel):
    phone_number_id: str
    display_phone_number: str
    business_profile_id: int
    assistant_id: int
    is_active: bool = True

class WhatsAppIntegrationCreate(WhatsAppIntegrationBase):
    pass

class WhatsAppIntegrationUpdate(BaseModel):
    phone_number_id: Optional[str] = None
    display_phone_number: Optional[str] = None
    business_profile_id: Optional[int] = None
    assistant_id: Optional[int] = None
    is_active: Optional[bool] = None

class WhatsAppIntegrationResponse(WhatsAppIntegrationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
