from sqlalchemy import Column, Boolean, Integer, String, Float, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import false
from services.db import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    emp_no = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    joining_date = Column(Date, nullable=False)
    total_exp = Column(Float, nullable=False, default=0.0)       # years
    relevant_exp = Column(Float, nullable=False, default=0.0)    # years
    working_location = Column(String(100), nullable=False)
    home_address = Column(String(255), nullable=True)

    is_deleted = Column(Boolean, default=False, server_default=false())
    sort_order = Column(Integer, default=0, server_default='0')

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    sows = relationship("SOW", back_populates="resource", cascade="all, delete-orphan")
