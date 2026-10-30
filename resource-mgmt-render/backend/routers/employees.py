from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from pydantic import BaseModel

from services.db import get_db
from models.employee import Employee
from schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse

router = APIRouter(prefix="/api/employees", tags=["Employees"])


# ── helpers ──────────────────────────────────────────────────────────────────
SORT_FIELDS = {
    "sort_order": Employee.sort_order,
    "created_at": Employee.created_at,
    "first_name": Employee.first_name,
    "last_name":  Employee.last_name,
    "emp_no":     Employee.emp_no,
    "total_exp":  Employee.total_exp,
    "relevant_exp": Employee.relevant_exp,
    "joining_date": Employee.joining_date,
}


def _apply_filters(q, search: str, include_deleted: bool, location: str = None):
    if not include_deleted:
        q = q.filter(Employee.is_deleted == False)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Employee.emp_no.ilike(like)
            | Employee.first_name.ilike(like)
            | Employee.last_name.ilike(like)
            | Employee.working_location.ilike(like)
        )
    if location:
        q = q.filter(Employee.working_location == location)
    return q


# ── list ─────────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[EmployeeResponse])
def list_employees(
    search:          Optional[str]  = Query(default=""),
    sort_by:         Optional[str]  = Query(default="sort_order"),
    order:           Optional[str]  = Query(default="asc"),
    include_deleted: Optional[bool] = Query(default=False),
    location:        Optional[str]  = Query(default=None),
    db: Session = Depends(get_db),
):
    col = SORT_FIELDS.get(sort_by, Employee.sort_order)
    direction = desc(col) if order == "desc" else asc(col)
    q = _apply_filters(db.query(Employee), search, include_deleted, location)
    return q.order_by(direction).all()


# ── single ───────────────────────────────────────────────────────────────────
@router.get("/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


# ── create ───────────────────────────────────────────────────────────────────
@router.post("/", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_db)):
    existing = db.query(Employee).filter(Employee.emp_no == payload.emp_no).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Employee number '{payload.emp_no}' already exists")

    # Assign sort_order = max + 1
    max_order = db.query(Employee.sort_order).order_by(desc(Employee.sort_order)).first()
    next_order = (max_order[0] + 1) if max_order else 1

    emp = Employee(**payload.model_dump(), sort_order=next_order)
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


# ── reorder ───────────────────────────────────────────────────────────────────
class ReorderItem(BaseModel):
    id: int
    sort_order: int

class ReorderPayload(BaseModel):
    items: List[ReorderItem]

@router.put("/reorder", response_model=dict)
def reorder_employees(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.items:
        emp = db.query(Employee).filter(Employee.id == item.id).first()
        if emp:
            emp.sort_order = item.sort_order
    db.commit()
    return {"message": "Order saved"}


# ── update ───────────────────────────────────────────────────────────────────
@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, payload: EmployeeUpdate, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    updates = payload.model_dump(exclude_unset=True)

    if "emp_no" in updates and updates["emp_no"] != emp.emp_no:
        conflict = db.query(Employee).filter(Employee.emp_no == updates["emp_no"]).first()
        if conflict:
            raise HTTPException(status_code=409, detail=f"Employee number '{updates['emp_no']}' already exists")

    for field, value in updates.items():
        setattr(emp, field, value)

    db.commit()
    db.refresh(emp)
    return emp


# ── soft delete ───────────────────────────────────────────────────────────────
@router.delete("/{emp_id}", status_code=status.HTTP_200_OK)
def delete_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.is_deleted = True
    db.commit()
    return {"message": "Employee soft-deleted"}


# ── restore ───────────────────────────────────────────────────────────────────
@router.put("/{emp_id}/restore", response_model=EmployeeResponse)
def restore_employee(emp_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    emp.is_deleted = False
    db.commit()
    db.refresh(emp)
    return emp

