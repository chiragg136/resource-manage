from pydantic import BaseModel, model_validator, field_validator
from datetime import date, datetime
from typing import Optional


VALID_INVOICE_STATUSES = {"Draft", "Submitted", "Paid", "Overdue"}
VALID_PAYMENT_STATUSES = {"Pending", "Received", "Partial"}


class InvoiceBase(BaseModel):
    inv_no: str
    sow_id: int
    month: int
    year: int
    inv_amount: float = 0.0
    invoice_status: str = "Draft"
    submission_date: Optional[date] = None
    payment_status: str = "Pending"
    payment_received_date: Optional[date] = None
    payment_received_amount: float = 0.0

    @field_validator("month")
    @classmethod
    def month_in_range(cls, v: int) -> int:
        if not 1 <= v <= 12:
            raise ValueError("month must be between 1 and 12")
        return v

    @field_validator("invoice_status")
    @classmethod
    def valid_invoice_status(cls, v: str) -> str:
        if v not in VALID_INVOICE_STATUSES:
            raise ValueError(f"invoice_status must be one of {VALID_INVOICE_STATUSES}")
        return v

    @field_validator("payment_status")
    @classmethod
    def valid_payment_status(cls, v: str) -> str:
        if v not in VALID_PAYMENT_STATUSES:
            raise ValueError(f"payment_status must be one of {VALID_PAYMENT_STATUSES}")
        return v

    @model_validator(mode="after")
    def payment_not_exceeds_invoice(self) -> "InvoiceBase":
        if self.payment_received_amount > self.inv_amount:
            raise ValueError("payment_received_amount cannot exceed inv_amount")
        return self


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    inv_no: Optional[str] = None
    sow_id: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    inv_amount: Optional[float] = None
    invoice_status: Optional[str] = None
    submission_date: Optional[date] = None
    payment_status: Optional[str] = None
    payment_received_date: Optional[date] = None
    payment_received_amount: Optional[float] = None

    @field_validator("month")
    @classmethod
    def month_in_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 1 <= v <= 12:
            raise ValueError("month must be between 1 and 12")
        return v

    @field_validator("invoice_status")
    @classmethod
    def valid_invoice_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_INVOICE_STATUSES:
            raise ValueError(f"invoice_status must be one of {VALID_INVOICE_STATUSES}")
        return v

    @field_validator("payment_status")
    @classmethod
    def valid_payment_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PAYMENT_STATUSES:
            raise ValueError(f"payment_status must be one of {VALID_PAYMENT_STATUSES}")
        return v


class InvoiceResponse(InvoiceBase):
    id: int
    is_deleted: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
    # Derived from SOW relationship
    customer: Optional[str] = None
    sow_no: Optional[str] = None
    # Computed field — NOT stored in DB
    diff_amount: float = 0.0

    model_config = {"from_attributes": True}

