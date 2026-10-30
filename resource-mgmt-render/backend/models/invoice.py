from sqlalchemy import Column, Boolean, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from services.db import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    inv_no = Column(String(100), unique=True, index=True, nullable=False)
    sow_id = Column(Integer, ForeignKey("sows.id"), nullable=False)

    month = Column(Integer, nullable=False)           # 1–12 (validated)
    year = Column(Integer, nullable=False)
    inv_amount = Column(Float, nullable=False, default=0.0)
    invoice_status = Column(String(50), nullable=False, default="Draft")
    # Allowed: Draft, Submitted, Paid, Overdue

    submission_date = Column(Date, nullable=True)
    payment_status = Column(String(50), nullable=False, default="Pending")
    # Allowed: Pending, Received, Partial

    payment_received_date = Column(Date, nullable=True)
    payment_received_amount = Column(Float, nullable=False, default=0.0)

    is_deleted = Column(Boolean, default=False, server_default=false())
    sort_order = Column(Integer, default=0, server_default='0')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    sow = relationship("SOW", back_populates="invoices")
