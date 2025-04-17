from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

class BusinessProfileCreate(BaseModel):
    business_name: str
    business_type: str
    tone_preferences: Dict[str, str]

class BusinessProfileResponse(BusinessProfileCreate):
    id: int
    unique_id: str
    assistant_id: int
    created_at: datetime
    knowledge_base: Optional[Dict] = None

    class Config:
        from_attributes = True 