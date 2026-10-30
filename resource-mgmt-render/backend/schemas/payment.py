from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class PaymentBase(BaseModel):
    amount: float
    payment_date: date
    remittance_remarks: Optional[str] = None
    payment_mode: str
    from_bank: Optional[str] = None
    po_number: Optional[str] = None
    invoice_list: Optional[str] = None

class PaymentCreate(PaymentBase):
    pass

class PaymentUpdate(BaseModel):
    amount: Optional[float] = None
    payment_date: Optional[date] = None
    remittance_remarks: Optional[str] = None
    payment_mode: Optional[str] = None
    from_bank: Optional[str] = None
    po_number: Optional[str] = None
    invoice_list: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: int
    is_deleted: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

