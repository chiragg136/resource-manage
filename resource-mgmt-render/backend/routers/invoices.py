from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import asc, desc
from typing import List, Optional
from pydantic import BaseModel

from services.db import get_db
from models.invoice import Invoice
from models.sow import SOW
from schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceResponse

router = APIRouter(prefix="/api/invoices", tags=["Invoices"])

SORT_FIELDS = {
    "sort_order":              Invoice.sort_order,
    "created_at":              Invoice.created_at,
    "inv_no":                  Invoice.inv_no,
    "inv_amount":              Invoice.inv_amount,
    "invoice_status":          Invoice.invoice_status,
    "payment_status":          Invoice.payment_status,
    "payment_received_amount": Invoice.payment_received_amount,
    "submission_date":         Invoice.submission_date,
    "year":                    Invoice.year,
    "month":                   Invoice.month,
}


def _build_response(inv: Invoice) -> InvoiceResponse:
    data = {
        "id": inv.id,
        "inv_no": inv.inv_no,
        "sow_id": inv.sow_id,
        "month": inv.month,
        "year": inv.year,
        "inv_amount": inv.inv_amount,
        "invoice_status": inv.invoice_status,
        "submission_date": inv.submission_date,
        "payment_status": inv.payment_status,
        "payment_received_date": inv.payment_received_date,
        "payment_received_amount": inv.payment_received_amount,
        "is_deleted": inv.is_deleted,
        "sort_order": inv.sort_order,
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "diff_amount": round(inv.inv_amount - inv.payment_received_amount, 2),
        "customer": inv.sow.customer if inv.sow else None,
        "sow_no":   inv.sow.sow_no   if inv.sow else None,
    }
    return InvoiceResponse(**data)


def _get_invoice_or_404(inv_id: int, db: Session) -> Invoice:
    inv = db.query(Invoice).options(joinedload(Invoice.sow)).filter(Invoice.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


def _apply_filters(q, search: str, include_deleted: bool, inv_status: str = None, pay_status: str = None):
    if not include_deleted:
        q = q.filter(Invoice.is_deleted == False)
    if search:
        like = f"%{search}%"
        q = q.filter(
            Invoice.inv_no.ilike(like)
            | Invoice.invoice_status.ilike(like)
            | Invoice.payment_status.ilike(like)
        )
    if inv_status:
        q = q.filter(Invoice.invoice_status == inv_status)
    if pay_status:
        q = q.filter(Invoice.payment_status == pay_status)
    return q


@router.get("/", response_model=List[InvoiceResponse])
def list_invoices(
    search:          Optional[str]  = Query(default=""),
    sort_by:         Optional[str]  = Query(default="sort_order"),
    order:           Optional[str]  = Query(default="asc"),
    include_deleted: Optional[bool] = Query(default=False),
    inv_status:      Optional[str]  = Query(default=None),
    pay_status:      Optional[str]  = Query(default=None),
    db: Session = Depends(get_db),
):
    col = SORT_FIELDS.get(sort_by, Invoice.sort_order)
    direction = desc(col) if order == "desc" else asc(col)
    q = _apply_filters(
        db.query(Invoice).options(joinedload(Invoice.sow)),
        search, include_deleted, inv_status, pay_status
    )
    return [_build_response(inv) for inv in q.order_by(direction).all()]


@router.get("/{inv_id}", response_model=InvoiceResponse)
def get_invoice(inv_id: int, db: Session = Depends(get_db)):
    return _build_response(_get_invoice_or_404(inv_id, db))


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate, db: Session = Depends(get_db)):
    if db.query(Invoice).filter(Invoice.inv_no == payload.inv_no).first():
        raise HTTPException(status_code=409, detail=f"Invoice number '{payload.inv_no}' already exists")
    if not db.query(SOW).filter(SOW.id == payload.sow_id).first():
        raise HTTPException(status_code=404, detail=f"SOW with id {payload.sow_id} not found")

    max_order = db.query(Invoice.sort_order).order_by(desc(Invoice.sort_order)).first()
    next_order = (max_order[0] + 1) if max_order else 1

    inv = Invoice(**payload.model_dump(), sort_order=next_order)
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return _build_response(_get_invoice_or_404(inv.id, db))



class ReorderItem(BaseModel):
    id: int
    sort_order: int

class ReorderPayload(BaseModel):
    items: List[ReorderItem]

@router.put("/reorder", response_model=dict)
def reorder_invoices(payload: ReorderPayload, db: Session = Depends(get_db)):
    for item in payload.items:
        inv = db.query(Invoice).filter(Invoice.id == item.id).first()
        if inv:
            inv.sort_order = item.sort_order
    db.commit()
    return {"message": "Order saved"}


@router.put("/{inv_id}", response_model=InvoiceResponse)
def update_invoice(inv_id: int, payload: InvoiceUpdate, db: Session = Depends(get_db)):
    inv = _get_invoice_or_404(inv_id, db)
    updates = payload.model_dump(exclude_unset=True)

    if "inv_no" in updates and updates["inv_no"] != inv.inv_no:
        if db.query(Invoice).filter(Invoice.inv_no == updates["inv_no"]).first():
            raise HTTPException(status_code=409, detail=f"Invoice number '{updates['inv_no']}' already exists")

    if "sow_id" in updates:
        if not db.query(SOW).filter(SOW.id == updates["sow_id"]).first():
            raise HTTPException(status_code=404, detail=f"SOW with id {updates['sow_id']} not found")

    new_inv_amount = updates.get("inv_amount", inv.inv_amount)
    new_payment    = updates.get("payment_received_amount", inv.payment_received_amount)
    if new_payment > new_inv_amount:
        raise HTTPException(status_code=422, detail="payment_received_amount cannot exceed inv_amount")

    for field, value in updates.items():
        setattr(inv, field, value)

    db.commit()
    return _build_response(_get_invoice_or_404(inv_id, db))


@router.delete("/{inv_id}", status_code=status.HTTP_200_OK)
def delete_invoice(inv_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.is_deleted = True
    db.commit()
    return {"message": "Invoice soft-deleted"}


@router.put("/{inv_id}/restore", response_model=InvoiceResponse)
def restore_invoice(inv_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).filter(Invoice.id == inv_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    inv.is_deleted = False
    db.commit()
    return _build_response(_get_invoice_or_404(inv_id, db))

