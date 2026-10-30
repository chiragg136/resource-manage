from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

from services.db import get_db
from models.employee import Employee
from models.sow import SOW
from models.invoice import Invoice
from models.payment import PaymentReceivable

from groq import Groq

router = APIRouter(prefix="/api/chat", tags=["Chatbot"])

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in the .env file")
        _client = Groq(api_key=api_key)
    return _client


class ChatRequest(BaseModel):
    question: str


def build_context(db: Session) -> str:
    """Build a compact context string under ~2500 tokens."""
    employees = db.query(Employee).filter(Employee.is_deleted == False).all()
    sows      = db.query(SOW).filter(SOW.is_deleted == False).all()
    invoices  = db.query(Invoice).filter(Invoice.is_deleted == False).all()
    payments  = db.query(PaymentReceivable).filter(PaymentReceivable.is_deleted == False).all()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_invoiced    = sum(i.inv_amount or 0 for i in invoices)
    total_received    = sum(i.payment_received_amount or 0 for i in invoices)
    total_outstanding = max(total_invoiced - total_received, 0)
    total_paid        = sum(p.amount for p in payments)
    pending_count     = sum(1 for i in invoices if i.payment_status == "Pending")
    overdue_count     = sum(1 for i in invoices if i.invoice_status == "Overdue")

    # ── Compact employee lines ─────────────────────────────────────────────────
    emp_lines = "\n".join(
        f"  {e.emp_no}: {e.first_name} {e.last_name}, joined {e.joining_date}, "
        f"{e.total_exp}y exp, {e.working_location}"
        for e in employees
    )

    # ── Compact SOW lines ──────────────────────────────────────────────────────
    sow_lines = "\n".join(
        f"  {s.sow_no}: {s.customer}, PO={s.po_number}, "
        f"{s.start_date}→{s.end_date}, ₹{s.amount:,.0f}"
        for s in sows
    )

    # ── Compact invoice lines (latest 15) ──────────────────────────────────────
    sorted_inv = sorted(invoices, key=lambda i: (i.year or 0, i.month or 0), reverse=True)[:15]
    inv_lines = "\n".join(
        f"  {i.inv_no}: SOW={i.sow_id}, {i.month}/{i.year}, "
        f"₹{i.inv_amount:,.0f}, inv={i.invoice_status}, pay={i.payment_status}, "
        f"rcvd=₹{i.payment_received_amount or 0:,.0f}"
        for i in sorted_inv
    )

    # ── Compact payment lines (latest 8) ──────────────────────────────────────
    sorted_pay = sorted(payments, key=lambda p: str(p.payment_date or ""), reverse=True)[:8]
    pay_lines = "\n".join(
        f"  {p.payment_date}: ₹{p.amount:,.0f} via {p.payment_mode}, bank={p.from_bank}"
        for p in sorted_pay
    )

    return (
        "You are an enterprise assistant for a Resource Management System. "
        "Answer ONLY from the data below. Be concise. Use ₹ for currency.\n\n"
        f"SUMMARY: {len(employees)} employees | {len(sows)} SOWs | "
        f"{len(invoices)} invoices (pending:{pending_count}, overdue:{overdue_count}) | "
        f"Invoiced:₹{total_invoiced:,.0f} | Received:₹{total_received:,.0f} | "
        f"Outstanding:₹{total_outstanding:,.0f} | "
        f"{len(payments)} payments | TotalPaid:₹{total_paid:,.0f}\n\n"
        f"EMPLOYEES:\n{emp_lines}\n\n"
        f"SOWs:\n{sow_lines}\n\n"
        f"INVOICES (latest 15):\n{inv_lines}\n\n"
        f"PAYMENTS (latest 8):\n{pay_lines}"
    )


@router.post("/")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        context = build_context(db)
        client = get_client()
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": context},
                {"role": "user",   "content": request.question}
            ],
            max_tokens=512,
            temperature=0.3,
        )
        return {"answer": response.choices[0].message.content}
    except Exception as e:
        return {"answer": f"Sorry, I encountered an error: {str(e)}"}
