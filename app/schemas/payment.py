from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    amount: float
    status: str
    transaction_id: str

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    user_id: int
    plan_id: int
    created_at: datetime

    class Config:
        orm_mode = True
