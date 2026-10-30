from sqlalchemy import Column, Boolean, Integer, String, Float, Date, DateTime
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from services.db import Base

class PaymentReceivable(Base):
    __tablename__ = "payments_receivable"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    remittance_remarks = Column(String(255), nullable=True)
    payment_mode = Column(String(50), nullable=False) # Check, Wire
    from_bank = Column(String(100), nullable=True)
    po_number = Column(String(100), nullable=True)
    invoice_list = Column(String(255), nullable=True) # Comma separated list of invoices

    is_deleted = Column(Boolean, default=False, server_default=false())
    sort_order = Column(Integer, default=0, server_default='0')

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
