from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional

class TransactionCreate(BaseModel):
    order_id: int
    amount: Decimal
    bank_trans_id: Optional[str] = None
    description: Optional[str] = None
    sender_account: Optional[str] = None
    sender_bank: Optional[str] = None
    status: str = 'pending'

class TransactionOut(BaseModel):
    transaction_id: int
    order_id: int
    amount: Decimal
    bank_trans_id: Optional[str]
    description: Optional[str]
    sender_account: Optional[str]
    sender_bank: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
