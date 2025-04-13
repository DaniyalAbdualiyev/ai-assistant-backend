from typing import List
from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    role: str = "user"  # Default role
    assistant_id: int

class MessageCreate(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    timestamp: datetime  # Changed from created_at to timestamp
    user_id: int

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    messages: List[MessageResponse]