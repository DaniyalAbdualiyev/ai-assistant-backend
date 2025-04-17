from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class ClientChatRequest(BaseModel):
    client_id: str
    message: str

class ClientChatResponse(BaseModel):
    message: str
    business_name: str
    assistant_name: str

class ClientSession(BaseModel):
    client_id: str
    business_name: str
    assistant_name: str
    
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

class ChatHistory(BaseModel):
    messages: List[ChatMessage]
