from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from services.db import get_db
from models.employee import Employee
from models.sow import SOW
from models.invoice import Invoice

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()

    total_employees = db.query(func.count(Employee.id)).scalar() or 0
    active_sows = db.query(func.count(SOW.id)).filter(SOW.end_date >= today).scalar() or 0
    pending_invoices = db.query(func.count(Invoice.id)).filter(Invoice.payment_status.in_(["Pending", "Partial"])).scalar() or 0
    revenue_collected = db.query(func.coalesce(func.sum(Invoice.payment_received_amount), 0.0)).scalar() or 0.0

    unpaid = db.query(Invoice).filter(Invoice.payment_status.in_(["Pending", "Partial"])).all()
    outstanding_amount = sum(max(inv.inv_amount - inv.payment_received_amount, 0) for inv in unpaid)

    # Fetch recent SOWs
    recent_sows_orm = db.query(SOW).order_by(SOW.id.desc()).limit(5).all()
    recent_sows = []
    for sow in recent_sows_orm:
        recent_sows.append({
            "sow_no": sow.sow_no,
            "customer": sow.customer,
            "amount": sow.amount,
            "end_date": sow.end_date.isoformat() if sow.end_date else None
        })
    
    # Fetch recent invoices and inject diff_amount
    recent_invoices_orm = db.query(Invoice).order_by(Invoice.id.desc()).limit(10).all()
    recent_invoices = []
    for inv in recent_invoices_orm:
        diff = max(inv.inv_amount - (inv.payment_received_amount or 0), 0)
        inv_dict = {
            "inv_no": inv.inv_no,
            "inv_amount": inv.inv_amount,
            "invoice_status": inv.invoice_status,
            "diff_amount": diff
        }
        recent_invoices.append(inv_dict)

    return {
        "total_employees": total_employees,
        "active_sows": active_sows,
        "pending_invoices": pending_invoices,
        "total_revenue_collected": round(float(revenue_collected), 2),
        "total_outstanding": round(outstanding_amount, 2),
        "recent_sows": recent_sows,
        "recent_invoices": recent_invoices
    }
