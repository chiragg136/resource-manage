from pydantic import BaseModel, model_validator
from datetime import date, datetime
from typing import Optional
from schemas.employee import EmployeeResponse


class SOWBase(BaseModel):
    sow_no: str
    name: str
    customer: str
    start_date: date
    end_date: date
    resource_id: int
    po_number: Optional[str] = None
    amount: float = 0.0
    billing_rate_per_hour: float = 0.0

    @model_validator(mode="after")
    def end_after_start(self) -> "SOWBase":
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class SOWCreate(SOWBase):
    pass


class SOWUpdate(BaseModel):
    sow_no: Optional[str] = None
    name: Optional[str] = None
    customer: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    resource_id: Optional[int] = None
    po_number: Optional[str] = None
    amount: Optional[float] = None
    billing_rate_per_hour: Optional[float] = None

    @model_validator(mode="after")
    def end_after_start(self) -> "SOWUpdate":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class SOWResponse(SOWBase):
    id: int
    is_deleted: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime
    resource: Optional[EmployeeResponse] = None

    model_config = {"from_attributes": True}

