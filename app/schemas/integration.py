from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict

class IntegrationBase(BaseModel):
    platform: str
    credentials: Optional[Dict] = None
    assistant_id: int

class IntegrationCreate(IntegrationBase):
    pass

class IntegrationResponse(IntegrationBase):
    id: int
    user_id: int
    created_at: datetime
    status: str

    class Config:
        from_attributes = True 