from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ConversationAnalyticsBase(BaseModel):
    assistant_id: int
    business_profile_id: int
    total_conversations: int
    total_messages: int
    avg_response_time: float
    date: datetime


class ConversationAnalyticsCreate(ConversationAnalyticsBase):
    pass


class ConversationAnalytics(ConversationAnalyticsBase):
    id: int
    last_updated: datetime

    class Config:
        orm_mode = True


class ClientAnalyticsBase(BaseModel):
    client_session_id: str
    assistant_id: int
    business_profile_id: int
    session_start: datetime
    message_count: int
    avg_response_time: Optional[float] = None
    client_ip: Optional[str] = None
    client_device: Optional[str] = None
    client_location: Optional[str] = None


class ClientAnalyticsCreate(ClientAnalyticsBase):
    pass


class ClientAnalyticsUpdate(BaseModel):
    session_end: Optional[datetime] = None
    message_count: Optional[int] = None
    avg_response_time: Optional[float] = None


class ClientAnalytics(ClientAnalyticsBase):
    id: int
    session_end: Optional[datetime] = None

    class Config:
        orm_mode = True


class AnalyticsSummary(BaseModel):
    total_conversations: int
    total_messages: int
    avg_response_time: float
    avg_messages_per_conversation: float
    active_conversations_today: int
    conversations_last_7_days: List[int]
    messages_last_7_days: List[int]
    
    class Config:
        orm_mode = True


class TimeRangeAnalytics(BaseModel):
    start_date: datetime
    end_date: datetime
