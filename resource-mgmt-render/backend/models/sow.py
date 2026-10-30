from sqlalchemy import Column, Boolean, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from services.db import Base


class SOW(Base):
    __tablename__ = "sows"

    id = Column(Integer, primary_key=True, index=True)
    sow_no = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    customer = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    resource_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    po_number = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False, default=0.0)
    billing_rate_per_hour = Column(Float, nullable=False, default=0.0)

    is_deleted = Column(Boolean, default=False, server_default=false())
    sort_order = Column(Integer, default=0, server_default='0')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    resource = relationship("Employee", back_populates="sows")
    invoices = relationship("Invoice", back_populates="sow", cascade="all, delete-orphan")
