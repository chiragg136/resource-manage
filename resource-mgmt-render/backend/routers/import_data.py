from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import pandas as pd
import io

from models.employee import Employee
from models.sow import SOW
from models.invoice import Invoice
from models.payment import PaymentReceivable as Payment
from services.db import get_db

router = APIRouter(prefix="/import", tags=["import"])

# ── Column Definitions ────────────────────────────────────────────────────────
MODULE_COLS = {
    "employees": ["Employee No", "First Name", "Last Name", "Joining Date",
                  "Total Experience", "Relevant Experience", "Location", "Home Address"],
    "sows":      ["SOW Number", "Customer Name", "Start Date", "End Date",
                  "Amount", "Employee Number", "PO Number"],
    "invoices":  ["Invoice Number", "SOW Number", "Month", "Year", "Invoice Amount",
                  "Invoice Status", "Submission Date", "Payment Status",
                  "Received Date", "Received Amount"],
    "payments":  ["Payment Date", "Amount", "Mode", "Bank", "PO Number",
                  "Invoices Covered", "Remarks"],
}

VALID_INV_STATUS = {"Draft", "Submitted", "Paid", "Overdue"}
VALID_PAY_STATUS = {"Pending", "Received", "Partial"}

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_date(val):
    if pd.isna(val) or str(val).strip() == "":
        return None
    try:
        return pd.to_datetime(val).date()
    except Exception:
        return None

def clean_float(val, default=0.0):
    if pd.isna(val) or str(val).strip() == "":
        return default
    try:
        return float(val)
    except Exception:
        return default

def clean_int(val, default=None):
    if pd.isna(val) or str(val).strip() == "":
        return default
    try:
        return int(float(val))
    except Exception:
        return default

def clean_str(val):
    if pd.isna(val):
        return None
    v = str(val).strip()
    return v if v else None


# ── Template download ─────────────────────────────────────────────────────────
@router.get("/template/{module}")
async def get_template(module: str, format: str = "csv"):
    if module not in MODULE_COLS:
        raise HTTPException(status_code=404, detail="Module not found")

    df = pd.DataFrame(columns=MODULE_COLS[module])

    if format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=template_{module}.xlsx"},
        )
    else:
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        bio = io.BytesIO(buffer.getvalue().encode("utf-8"))
        return StreamingResponse(
            bio,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=template_{module}.csv"},
        )


# ── Shared: load DB lookup sets ───────────────────────────────────────────────
def load_db_lookups(db: Session):
    """
    Return sets/dicts of existing keys for duplicate detection.

    IMPORTANT: unique-key fields (emp_no, sow_no, inv_no) are checked against
    ALL rows — including soft-deleted ones — because the MySQL unique index
    still covers those rows and will raise IntegrityError on insert even if
    is_deleted=True.  Payment duplicates only check active rows (no unique index).
    """
    # Check ALL rows (deleted + active) for unique-indexed fields
    existing_emp_nos  = {e.emp_no: e.id for e in db.query(Employee).all()}
    existing_sow_nos  = {s.sow_no: s.id for s in db.query(SOW).all()}
    existing_inv_nos  = {i.inv_no        for i in db.query(Invoice).all()}

    # Payments have no unique index — only block active duplicates
    existing_pay_keys = {
        (str(p.payment_date), round(p.amount, 2), str(p.po_number or ""))
        for p in db.query(Payment).filter(Payment.is_deleted == False).all()
    }
    return existing_emp_nos, existing_sow_nos, existing_inv_nos, existing_pay_keys


# ── Validate a single row and return (errors, payload) ───────────────────────
def validate_row(module, row, existing_emp_nos, existing_sow_nos,
                 existing_inv_nos, existing_pay_keys,
                 seen_in_file: set):
    """
    Validate one spreadsheet row.
    seen_in_file tracks keys already seen *within this upload* to catch
    intra-file duplicates as well.
    Returns (errors: list[str], payload: dict)
    """
    errors = []
    payload = {}

    try:
        if module == "employees":
            emp_no = clean_str(row.get("Employee No"))
            if not emp_no:
                errors.append("Employee No is required")
            elif emp_no in existing_emp_nos:
                errors.append(f"Employee No '{emp_no}' already exists in the database")
            elif emp_no in seen_in_file:
                errors.append(f"Employee No '{emp_no}' is duplicated within this file")
            else:
                seen_in_file.add(emp_no)

            fn = clean_str(row.get("First Name"))
            ln = clean_str(row.get("Last Name"))
            if not fn or not ln:
                errors.append("First Name and Last Name are required")

            j_date = parse_date(row.get("Joining Date"))
            if not j_date:
                errors.append("Invalid or missing Joining Date")

            payload = {
                "emp_no": emp_no,
                "first_name": fn,
                "last_name": ln,
                "joining_date": str(j_date) if j_date else None,
                "total_exp": clean_float(row.get("Total Experience")),
                "relevant_exp": clean_float(row.get("Relevant Experience")),
                "working_location": clean_str(row.get("Location")) or "Unknown",
                "home_address": clean_str(row.get("Home Address")),
            }

        elif module == "sows":
            sow_no = clean_str(row.get("SOW Number"))
            if not sow_no:
                errors.append("SOW Number is required")
            elif sow_no in existing_sow_nos:
                errors.append(f"SOW '{sow_no}' already exists in the database")
            elif sow_no in seen_in_file:
                errors.append(f"SOW '{sow_no}' is duplicated within this file")
            else:
                seen_in_file.add(sow_no)

            cust = clean_str(row.get("Customer Name"))
            if not cust:
                errors.append("Customer Name is required")

            s_date = parse_date(row.get("Start Date"))
            e_date = parse_date(row.get("End Date"))
            if not s_date or not e_date:
                errors.append("Valid Start Date and End Date are required")
            elif e_date < s_date:
                errors.append("End Date cannot be before Start Date")

            emp_no = clean_str(row.get("Employee Number"))
            res_id = existing_emp_nos.get(emp_no)
            if not emp_no:
                errors.append("Employee Number is required")
            elif not res_id:
                errors.append(f"Employee '{emp_no}' not found in the database")

            payload = {
                "sow_no": sow_no,
                "name": f"{cust} Project" if cust else "Imported SOW",
                "customer": cust,
                "start_date": str(s_date) if s_date else None,
                "end_date": str(e_date) if e_date else None,
                "amount": clean_float(row.get("Amount")),
                "po_number": clean_str(row.get("PO Number")),
                "resource_id": res_id,
            }

        elif module == "invoices":
            inv_no = clean_str(row.get("Invoice Number"))
            if not inv_no:
                errors.append("Invoice Number is required")
            elif inv_no in existing_inv_nos:
                errors.append(f"Invoice '{inv_no}' already exists in the database")
            elif inv_no in seen_in_file:
                errors.append(f"Invoice '{inv_no}' is duplicated within this file")
            else:
                seen_in_file.add(inv_no)

            sow_no = clean_str(row.get("SOW Number"))
            sow_id = existing_sow_nos.get(sow_no)
            if not sow_no:
                errors.append("SOW Number is required")
            elif not sow_id:
                errors.append(f"SOW '{sow_no}' not found in the database")

            mo = clean_int(row.get("Month"))
            yr = clean_int(row.get("Year"))
            if not mo or not yr or mo < 1 or mo > 12 or yr < 2000:
                errors.append("Valid Month (1–12) and Year (≥2000) required")

            inv_amt = clean_float(row.get("Invoice Amount"))
            istatus = clean_str(row.get("Invoice Status")) or "Draft"
            if istatus not in VALID_INV_STATUS:
                errors.append(f"Invoice Status must be one of: {', '.join(VALID_INV_STATUS)}")

            pstatus = clean_str(row.get("Payment Status")) or "Pending"
            if pstatus not in VALID_PAY_STATUS:
                errors.append(f"Payment Status must be one of: {', '.join(VALID_PAY_STATUS)}")

            sdate = parse_date(row.get("Submission Date"))
            pdate = parse_date(row.get("Received Date"))
            pamt  = clean_float(row.get("Received Amount"))

            if pamt > inv_amt:
                errors.append("Received Amount cannot exceed Invoice Amount")

            payload = {
                "inv_no": inv_no,
                "sow_id": sow_id,
                "month": mo,
                "year": yr,
                "inv_amount": inv_amt,
                "invoice_status": istatus,
                "submission_date": str(sdate) if sdate else None,
                "payment_status": pstatus,
                "payment_received_date": str(pdate) if pdate else None,
                "payment_received_amount": pamt,
            }

        elif module == "payments":
            pdate = parse_date(row.get("Payment Date"))
            if not pdate:
                errors.append("Payment Date is required")

            amt = clean_float(row.get("Amount"))
            if amt <= 0:
                errors.append("Amount must be greater than 0")

            po_number = clean_str(row.get("PO Number")) or ""
            pay_key   = (str(pdate), round(amt, 2), po_number)

            if pay_key in existing_pay_keys:
                errors.append(
                    f"A payment of ₹{amt:,.2f} on {pdate} for PO '{po_number}' "
                    f"already exists in the database"
                )
            elif pay_key in seen_in_file:
                errors.append(
                    f"Payment ₹{amt:,.2f} on {pdate} for PO '{po_number}' "
                    f"is duplicated within this file"
                )
            else:
                seen_in_file.add(pay_key)

            payload = {
                "payment_date": str(pdate) if pdate else None,
                "amount": amt,
                "payment_mode": clean_str(row.get("Mode")) or "Wire Transfer",
                "from_bank": clean_str(row.get("Bank")),
                "po_number": po_number or None,
                "invoice_list": clean_str(row.get("Invoices Covered")),
                "remittance_remarks": clean_str(row.get("Remarks")),
            }

    except Exception as e:
        errors.append(f"Unexpected error: {str(e)}")

    return errors, payload


# ── Preview endpoint ──────────────────────────────────────────────────────────
@router.post("/preview/{module}")
async def preview_import(module: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if module not in MODULE_COLS:
        raise HTTPException(status_code=404, detail="Module not found")

    contents = await file.read()
    if file.filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(contents))
    elif file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="Invalid file format. Use .xlsx or .csv")

    existing_emp_nos, existing_sow_nos, existing_inv_nos, existing_pay_keys = load_db_lookups(db)
    seen_in_file: set = set()
    results = []

    for index, row in df.iterrows():
        errors, payload = validate_row(
            module, row,
            existing_emp_nos, existing_sow_nos,
            existing_inv_nos, existing_pay_keys,
            seen_in_file,
        )
        results.append({
            "row_index": index + 2,
            "is_valid": len(errors) == 0,
            "errors": errors,
            "payload": payload,
            "raw_data": {k: ("" if (isinstance(v, float) and pd.isna(v)) else v)
                         for k, v in row.items()},
        })

    return {"records": results}


# ── Confirm / Insert endpoint ─────────────────────────────────────────────────
@router.post("/confirm/{module}")
async def confirm_import(module: str, records: list[dict], db: Session = Depends(get_db)):
    if module not in MODULE_COLS:
        raise HTTPException(status_code=404, detail="Module not found")

    if not records:
        raise HTTPException(status_code=400, detail="No valid records provided to insert")

    # ── Re-validate against live DB at insert time (prevents race conditions) ──
    existing_emp_nos, existing_sow_nos, existing_inv_nos, existing_pay_keys = load_db_lookups(db)
    seen_in_batch: set = set()

    safe_records = []
    skipped = []

    for rec in records:
        dup_error = None

        if module == "employees":
            key = rec.get("emp_no")
            if key in existing_emp_nos:
                dup_error = f"Employee No '{key}' already exists (detected at insert time)"
            elif key in seen_in_batch:
                dup_error = f"Employee No '{key}' duplicated in batch"
            else:
                seen_in_batch.add(key)

        elif module == "sows":
            key = rec.get("sow_no")
            if key in existing_sow_nos:
                dup_error = f"SOW '{key}' already exists (detected at insert time)"
            elif key in seen_in_batch:
                dup_error = f"SOW '{key}' duplicated in batch"
            else:
                seen_in_batch.add(key)

        elif module == "invoices":
            key = rec.get("inv_no")
            if key in existing_inv_nos:
                dup_error = f"Invoice '{key}' already exists (detected at insert time)"
            elif key in seen_in_batch:
                dup_error = f"Invoice '{key}' duplicated in batch"
            else:
                seen_in_batch.add(key)

        elif module == "payments":
            pdate  = rec.get("payment_date", "")
            amt    = round(float(rec.get("amount", 0)), 2)
            po     = str(rec.get("po_number") or "")
            key    = (str(pdate), amt, po)
            if key in existing_pay_keys:
                dup_error = f"Payment ₹{amt:,.2f} on {pdate} for PO '{po}' already exists"
            elif key in seen_in_batch:
                dup_error = f"Payment ₹{amt:,.2f} on {pdate} for PO '{po}' duplicated in batch"
            else:
                seen_in_batch.add(key)

        if dup_error:
            skipped.append({"record": rec, "reason": dup_error})
        else:
            safe_records.append(rec)

    if not safe_records:
        return {
            "success": False,
            "inserted_count": 0,
            "skipped_count": len(skipped),
            "message": "All records were skipped — they already exist in the database.",
            "skipped": skipped,
        }

    ModelClass = {
        "employees": Employee,
        "sows":      SOW,
        "invoices":  Invoice,
        "payments":  Payment,
    }[module]

    max_obj    = db.query(ModelClass).order_by(ModelClass.sort_order.desc()).first()
    next_order = (max_obj.sort_order + 1) if max_obj else 1
    now        = datetime.utcnow()
    inserted   = 0

    date_fields = ["joining_date", "start_date", "end_date",
                   "submission_date", "payment_received_date", "payment_date"]

    try:
        for rec in safe_records:
            for field in date_fields:
                if rec.get(field):
                    rec[field] = datetime.strptime(rec[field], "%Y-%m-%d").date()

            obj             = ModelClass(**rec)
            obj.sort_order  = next_order
            obj.is_deleted  = False
            obj.created_at  = now
            obj.updated_at  = now

            db.add(obj)
            next_order += 1
            inserted   += 1

        db.commit()

        return {
            "success":        True,
            "inserted_count": inserted,
            "skipped_count":  len(skipped),
            "message":        f"{inserted} record(s) imported successfully."
                              + (f" {len(skipped)} duplicate(s) skipped." if skipped else ""),
            "skipped":        skipped,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failed: {str(e)}")
