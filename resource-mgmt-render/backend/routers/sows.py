from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional
from pydantic import BaseModel

from services.db import get_db
from models.sow import SOW
from models.employee import Employee
from schemas.sow import SOWCreate, SOWUpdate, SOWResponse

router = APIRouter(prefix="/api/sows", tags=["SOWs"])

SORT_FIELDS = {
    "sort_order":  SOW.sort_order,
    "created_at":  SOW.created_at,
    "sow_no":      SOW.sow_no,
    "name":        SOW.name,
    "customer":    SOW.customer,
    "amount":      SOW.amount,
    "start_date":  SOW.start_date,
    "end_date":    SOW.end_date,
}


def _get_sow_or_404(sow_id: int, db: Session) -> SOW:
    sow = db.query(SOW).options(joinedload(SOW.resource)).filter(SOW.id == sow_id).first()
    if not sow:
        raise HTTPException(status_code=404, detail="SOW not found")
    return sow


def _apply_filters(q, search: str, include_deleted: bool, customer: str = None):
    if not include_deleted:
        q = q.filter(SOW.is_deleted == False)
    if search:
        like = f"%{search}%"
        q = q.filter(
            SOW.sow_no.ilike(like)
            | SOW.name.ilike(like)
            | SOW.customer.ilike(like)
            | SOW.po_number.ilike(like)
        )
    if customer:
        q = q.filter(SOW.customer == customer)
    return q


@router.get("/", response_model=List[SOWResponse])
def list_sows(
    search:          Optional[str]  = Query(default=""),
    sort_by:         Optional[str]  = Query(default="sort_order"),
    order:           Optional[str]  = Query(default="asc"),
    include_deleted: Optional[bool] = Query(default=False),
    customer:        Optional[str]  = Query(default=None),
    db: Session = Depends(get_db),
):
    col = SORT_FIELDS.get(sort_by, SOW.sort_order)
    direction = desc(col) if order == "desc" else asc(col)
    q = _apply_filters(
        db.query(SOW).options(joinedload(SOW.resource)),
        search, include_deleted, customer
    )
    return q.order_by(direction).all()


@router.get("/{sow_id}", response_model=SOWResponse)
def get_sow(sow_id: int, db: Session = Depends(get_db)):
    return _get_sow_or_404(sow_id, db)


@router.post("/", response_model=SOWResponse, status_code=status.HTTP_201_CREATED)
def create_sow(payload: SOWCreate, db: Session = Depends(get_db)):
    if db.query(SOW).filter(SOW.sow_no == payload.sow_no).first():
        raise HTTPException(status_code=409, detail=f"SOW number '{payload.sow_no}' already exists")
    if not db.query(Employee).filter(Employee.id == payload.resource_id).first():
        raise HTTPException(status_code=404, detail=f"Employee with id {payload.resource_id} not found")

    max_order = db.query(SOW.sort_order).order_by(desc(SOW.sort_order)).first()
    next_order = (max_order[0] + 1) if max_order else 1

    sow = SOW(**payload.model_dump(), sort_order=next_order)
    db.add(sow)
    db.commit()
    db.refresh(sow)
    return _get_sow_or_404(sow.id, db)



class ReorderItem(BaseModel):
    id: int
    sort_order: int

class ReorderPayload(BaseModel):
    items: List[ReorderItem]

@router.put("/reorder", response_model=dict)
def reorder_sows(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.items:
        sow = db.query(SOW).filter(SOW.id == item.id).first()
        if sow:
            sow.sort_order = item.sort_order
    db.commit()
    return {"message": "Order saved"}


@router.put("/{sow_id}", response_model=SOWResponse)
def update_sow(sow_id: int, payload: SOWUpdate, db: Session = Depends(get_db)):
    sow = _get_sow_or_404(sow_id, db)
    updates = payload.model_dump(exclude_unset=True)

    if "sow_no" in updates and updates["sow_no"] != sow.sow_no:
        if db.query(SOW).filter(SOW.sow_no == updates["sow_no"]).first():
            raise HTTPException(status_code=409, detail=f"SOW number '{updates['sow_no']}' already exists")

    if "resource_id" in updates:
        if not db.query(Employee).filter(Employee.id == updates["resource_id"]).first():
            raise HTTPException(status_code=404, detail=f"Employee with id {updates['resource_id']} not found")

    from datetime import date
    start = updates.get("start_date", sow.start_date)
    end   = updates.get("end_date",   sow.end_date)
    if end < start:
        raise HTTPException(status_code=422, detail="end_date cannot be earlier than start_date")

    for field, value in updates.items():
        setattr(sow, field, value)

    db.commit()
    return _get_sow_or_404(sow_id, db)


@router.delete("/{sow_id}", status_code=status.HTTP_200_OK)
def delete_sow(sow_id: int, db: Session = Depends(get_db)):
    sow = db.query(SOW).filter(SOW.id == sow_id).first()
    if not sow:
        raise HTTPException(status_code=404, detail="SOW not found")
    sow.is_deleted = True
    db.commit()
    return {"message": "SOW soft-deleted"}


@router.put("/{sow_id}/restore", response_model=SOWResponse)
def restore_sow(sow_id: int, db: Session = Depends(get_db)):
    sow = db.query(SOW).filter(SOW.id == sow_id).first()
    if not sow:
        raise HTTPException(status_code=404, detail="SOW not found")
    sow.is_deleted = False
    db.commit()
    return _get_sow_or_404(sow_id, db)

