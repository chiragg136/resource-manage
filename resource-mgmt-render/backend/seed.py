import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db import SessionLocal, Base, engine
from models.employee import Employee
from models.sow import SOW
from models.invoice import Invoice
from models.payment import PaymentReceivable
from datetime import date

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    existing_emp_count = db.query(Employee).count()
    if existing_emp_count > 0:
        print(f"Database already contains {existing_emp_count} employees. Skipping seed.")
        sys.exit(0)

    # ── Employees ──────────────────────────────────────────────
    emps = [
        Employee(emp_no="EMP-001", first_name="Arjun",  last_name="Sharma", joining_date=date(2020,3,15), total_exp=7.5,  relevant_exp=5.0, working_location="Bangalore", home_address="12 MG Road, Bangalore", sort_order=1),
        Employee(emp_no="EMP-002", first_name="Priya",  last_name="Nair",   joining_date=date(2019,7,1),  total_exp=9.0,  relevant_exp=6.5, working_location="Mumbai",    home_address="Andheri West, Mumbai",  sort_order=2),
        Employee(emp_no="EMP-003", first_name="Rahul",  last_name="Verma",  joining_date=date(2021,11,10),total_exp=5.0,  relevant_exp=3.5, working_location="Delhi",     home_address="Sector 18, Noida",      sort_order=3),
        Employee(emp_no="EMP-004", first_name="Sneha",  last_name="Patel",  joining_date=date(2022,1,20), total_exp=4.0,  relevant_exp=2.5, working_location="Pune",      home_address="Hinjewadi, Pune",       sort_order=4),
        Employee(emp_no="EMP-005", first_name="Vikram", last_name="Iyer",   joining_date=date(2018,5,5),  total_exp=12.0, relevant_exp=8.0, working_location="Chennai",   home_address="Anna Nagar, Chennai",   sort_order=5),
        Employee(emp_no="EMP-006", first_name="Deepa",  last_name="Menon",  joining_date=date(2023,4,1),  total_exp=3.0,  relevant_exp=2.0, working_location="Hyderabad", home_address="Gachibowli, Hyderabad", sort_order=6),
    ]
    db.add_all(emps)
    db.flush()

    # ── SOWs ───────────────────────────────────────────────────
    sows = [
        SOW(sow_no="SOW-2024-001", name="TechCorp Alpha",    customer="TechCorp Ltd",  start_date=date(2024,1,1),  end_date=date(2024,12,31), amount=1500000, po_number="PO-TC-001", resource_id=emps[0].id, sort_order=1),
        SOW(sow_no="SOW-2024-002", name="Infra Systems Beta", customer="Infra Systems", start_date=date(2024,3,1),  end_date=date(2025,2,28),  amount=2200000, po_number="PO-IS-002", resource_id=emps[1].id, sort_order=2),
        SOW(sow_no="SOW-2024-003", name="FinServ Analytics",  customer="FinServ Inc",   start_date=date(2024,4,1),  end_date=date(2024,9,30),  amount=800000,  po_number="PO-FS-003", resource_id=emps[2].id, sort_order=3),
        SOW(sow_no="SOW-2024-004", name="RetailMax Platform", customer="RetailMax",     start_date=date(2024,6,1),  end_date=date(2025,5,31),  amount=3000000, po_number="PO-RM-004", resource_id=emps[3].id, sort_order=4),
        SOW(sow_no="SOW-2025-001", name="HealthPlus Digital", customer="HealthPlus",    start_date=date(2025,1,1),  end_date=date(2025,12,31), amount=1800000, po_number="PO-HP-001", resource_id=emps[4].id, sort_order=5),
        SOW(sow_no="SOW-2025-002", name="TechCorp Expansion", customer="TechCorp Ltd",  start_date=date(2025,3,1),  end_date=date(2026,2,28),  amount=2500000, po_number="PO-TC-002", resource_id=emps[5].id, sort_order=6),
    ]
    db.add_all(sows)
    db.flush()

    # ── Invoices ───────────────────────────────────────────────
    invoices = [
        Invoice(inv_no="INV-2024-001", sow_id=sows[0].id, month=1, year=2024, inv_amount=125000, invoice_status="Paid",      submission_date=date(2024,1,31), payment_status="Received", payment_received_date=date(2024,2,15), payment_received_amount=125000, sort_order=1),
        Invoice(inv_no="INV-2024-002", sow_id=sows[0].id, month=2, year=2024, inv_amount=125000, invoice_status="Paid",      submission_date=date(2024,2,29), payment_status="Received", payment_received_date=date(2024,3,14), payment_received_amount=125000, sort_order=2),
        Invoice(inv_no="INV-2024-003", sow_id=sows[1].id, month=3, year=2024, inv_amount=183333, invoice_status="Submitted", submission_date=date(2024,3,31), payment_status="Pending",  payment_received_date=None,            payment_received_amount=0,      sort_order=3),
        Invoice(inv_no="INV-2024-004", sow_id=sows[2].id, month=4, year=2024, inv_amount=133333, invoice_status="Paid",      submission_date=date(2024,4,30), payment_status="Received", payment_received_date=date(2024,5,20), payment_received_amount=133333, sort_order=4),
        Invoice(inv_no="INV-2024-005", sow_id=sows[3].id, month=6, year=2024, inv_amount=250000, invoice_status="Submitted", submission_date=date(2024,6,30), payment_status="Partial",  payment_received_date=date(2024,7,25), payment_received_amount=100000, sort_order=5),
        Invoice(inv_no="INV-2024-006", sow_id=sows[3].id, month=7, year=2024, inv_amount=250000, invoice_status="Overdue",   submission_date=date(2024,7,31), payment_status="Pending",  payment_received_date=None,            payment_received_amount=0,      sort_order=6),
        Invoice(inv_no="INV-2025-001", sow_id=sows[4].id, month=1, year=2025, inv_amount=150000, invoice_status="Submitted", submission_date=date(2025,1,31), payment_status="Pending",  payment_received_date=None,            payment_received_amount=0,      sort_order=7),
        Invoice(inv_no="INV-2025-002", sow_id=sows[5].id, month=3, year=2025, inv_amount=208333, invoice_status="Draft",     submission_date=None,            payment_status="Pending",  payment_received_date=None,            payment_received_amount=0,      sort_order=8),
    ]
    db.add_all(invoices)
    db.flush()

    # ── Payments ───────────────────────────────────────────────
    payments = [
        PaymentReceivable(payment_date=date(2024,2,15), amount=125000, payment_mode="Wire Transfer", from_bank="HDFC Bank",  po_number="PO-TC-001", invoice_list="INV-2024-001", remittance_remarks="Payment for Jan 2024", sort_order=1),
        PaymentReceivable(payment_date=date(2024,3,14), amount=125000, payment_mode="Wire Transfer", from_bank="HDFC Bank",  po_number="PO-TC-001", invoice_list="INV-2024-002", remittance_remarks="Payment for Feb 2024", sort_order=2),
        PaymentReceivable(payment_date=date(2024,5,20), amount=133333, payment_mode="Check",         from_bank="ICICI Bank", po_number="PO-FS-003", invoice_list="INV-2024-004", remittance_remarks="FinServ Q1 payment",   sort_order=3),
        PaymentReceivable(payment_date=date(2024,7,25), amount=100000, payment_mode="Wire Transfer", from_bank="Axis Bank",  po_number="PO-RM-004", invoice_list="INV-2024-005", remittance_remarks="RetailMax partial",    sort_order=4),
    ]
    db.add_all(payments)
    db.commit()

    print(f"Successfully seeded: {len(emps)} employees, {len(sows)} SOWs, {len(invoices)} invoices, {len(payments)} payments")

except Exception as e:
    db.rollback()
    print(f"Error seeding database: {e}")
    raise
finally:
    db.close()
