from pydantic import BaseModel
from datetime import datetime

class AssistantBase(BaseModel):
    name: str
    model: str
    language: str = "en"

class AssistantCreate(AssistantBase):
    pass

class AssistantResponse(AssistantBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AssistantQuery(BaseModel):
    text: str
    tone: str = "normal"  # Can be "normal", "expert", or "simple"
    business_type: str = "selling"
    