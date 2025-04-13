from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SubscriptionPlanBase(BaseModel):
    name: str
    price: float
    features: str

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
