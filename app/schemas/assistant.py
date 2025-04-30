from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Optional

class BusinessProfileBase(BaseModel):
    business_name: str
    business_type: str
    tone_preferences: Dict[str, str]

class AssistantBase(BaseModel):
    name: str = "Assistant"
    model: str = "gpt-3.5-turbo"
    language: str = "en"

class AssistantCreate(AssistantBase):
    business_profile: Optional[BusinessProfileBase] = None

class BusinessProfileResponse(BaseModel):
    id: int
    business_name: str
    business_type: str
    unique_id: str

    class Config:
        from_attributes = True

class AssistantResponse(AssistantBase):
    id: int
    user_id: int
    created_at: datetime
    business_profile: Optional[BusinessProfileResponse] = None
    chat_url: Optional[str] = None

    class Config:
        from_attributes = True

class AssistantQuery(BaseModel):
    text: str
    tone: str = "normal"  # Can be "normal", "expert", or "simple"
    business_type: str = "selling"
    language: str = None