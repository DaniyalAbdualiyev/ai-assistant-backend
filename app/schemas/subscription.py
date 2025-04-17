from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DurationType(str, Enum):
    monthly = "monthly"
    yearly = "yearly"

class SubscriptionPlanBase(BaseModel):
    name: str
    price: float
    features: str
    duration: DurationType = DurationType.monthly
    duration_months: int = 1

class SubscriptionPlanCreate(SubscriptionPlanBase):
    pass

class SubscriptionPlanResponse(SubscriptionPlanBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionCreate(BaseModel):
    user_id: int
    plan_id: int

class SubscriptionResponse(BaseModel):
    session_id: str
    url: str

class UserSubscriptionBase(BaseModel):
    user_id: int
    plan_id: int
    payment_id: int
    start_date: datetime
    end_date: datetime
    is_active: bool

class UserSubscriptionResponse(UserSubscriptionBase):
    id: int
    
    class Config:
        from_attributes = True
