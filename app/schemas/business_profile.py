from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class BusinessProfileBase(BaseModel):
    business_name: str
    business_type: str
    business_description: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[List[str]] = None
    products_services: Optional[List[str]] = None
    language: str = "en"

class TonePreferences(BaseModel):
    tone: str = Field(..., description="The tone of voice for the AI assistant")
    style: str = Field(..., description="The writing style for the AI assistant")
    personality: Optional[str] = Field(None, description="Specific personality traits for the AI")
    formality: str = Field(..., description="Level of formality (formal, casual, etc.)")

class BusinessProfileCreate(BusinessProfileBase):
    tone_preferences: TonePreferences
    whatsapp_number: Optional[str] = None
    instagram_username: Optional[str] = None

class BusinessProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    industry: Optional[str] = None
    target_audience: Optional[List[str]] = None
    products_services: Optional[List[str]] = None
    tone_preferences: Optional[TonePreferences] = None
    language: Optional[str] = None
    whatsapp_number: Optional[str] = None
    instagram_username: Optional[str] = None

class BusinessProfileResponse(BusinessProfileBase):
    id: int
    tone_preferences: Dict
    knowledge_base: Optional[Dict] = None
    files: Optional[Dict] = None
    whatsapp_number: Optional[str] = None
    whatsapp_verified: bool = False
    instagram_username: Optional[str] = None
    instagram_verified: bool = False
    assistant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str
    size: int
    processed: bool = False

class KnowledgeBaseUpdate(BaseModel):
    content: str
    source: str
    type: str = "text"  # text, file, url, etc. 