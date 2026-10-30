from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from typing import List, Optional
from pydantic import BaseModel

from services.db import get_db
from models.payment import PaymentReceivable
from schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse

router = APIRouter(prefix="/api/payments", tags=["Payments"])

SORT_FIELDS = {
    "sort_order":   PaymentReceivable.sort_order,
    "created_at":   PaymentReceivable.created_at,
    "payment_date": PaymentReceivable.payment_date,
    "amount":       PaymentReceivable.amount,
    "payment_mode": PaymentReceivable.payment_mode,
    "po_number":    PaymentReceivable.po_number,
}


def _apply_filters(q, search: str, include_deleted: bool, mode: str = None):
    if not include_deleted:
        q = q.filter(PaymentReceivable.is_deleted == False)
    if search:
        like = f"%{search}%"
        q = q.filter(
            PaymentReceivable.po_number.ilike(like)
            | PaymentReceivable.from_bank.ilike(like)
            | PaymentReceivable.payment_mode.ilike(like)
            | PaymentReceivable.remittance_remarks.ilike(like)
            | PaymentReceivable.invoice_list.ilike(like)
        )
    if mode:
        q = q.filter(PaymentReceivable.payment_mode == mode)
    return q


@router.get("/", response_model=List[PaymentResponse])
def list_payments(
    search:          Optional[str]  = Query(default=""),
    sort_by:         Optional[str]  = Query(default="sort_order"),
    order:           Optional[str]  = Query(default="asc"),
    include_deleted: Optional[bool] = Query(default=False),
    mode:            Optional[str]  = Query(default=None),
    db: Session = Depends(get_db),
):
    col = SORT_FIELDS.get(sort_by, PaymentReceivable.sort_order)
    direction = desc(col) if order == "desc" else asc(col)
    q = _apply_filters(db.query(PaymentReceivable), search, include_deleted, mode)
    return q.order_by(direction).all()


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(PaymentReceivable).filter(PaymentReceivable.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)):
    max_order = db.query(PaymentReceivable.sort_order).order_by(desc(PaymentReceivable.sort_order)).first()
    next_order = (max_order[0] + 1) if max_order else 1

    payment = PaymentReceivable(**payload.model_dump(), sort_order=next_order)
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment



class ReorderItem(BaseModel):
    id: int
    sort_order: int

class ReorderPayload(BaseModel):
    items: List[ReorderItem]

@router.put("/reorder", response_model=dict)
def reorder_payments(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.items:
        p = db.query(PaymentReceivable).filter(PaymentReceivable.id == item.id).first()
        if p:
            p.sort_order = item.sort_order
    db.commit()
    return {"message": "Order saved"}


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(payment_id: int, payload: PaymentUpdate, db: Session = Depends(get_db)):
    payment = db.query(PaymentReceivable).filter(PaymentReceivable.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_200_OK)
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(PaymentReceivable).filter(PaymentReceivable.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment.is_deleted = True
    db.commit()
    return {"message": "Payment soft-deleted"}


@router.put("/{payment_id}/restore", response_model=PaymentResponse)
def restore_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(PaymentReceivable).filter(PaymentReceivable.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    payment.is_deleted = False
    db.commit()
    db.refresh(payment)
    return payment

