from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional


class EmployeeBase(BaseModel):
    emp_no: str
    first_name: str
    last_name: str
    joining_date: date
    total_exp: float = 0.0
    relevant_exp: float = 0.0
    working_location: str
    home_address: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    emp_no: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    joining_date: Optional[date] = None
    total_exp: Optional[float] = None
    relevant_exp: Optional[float] = None
    working_location: Optional[str] = None
    home_address: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: int
    is_deleted: bool = False
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

