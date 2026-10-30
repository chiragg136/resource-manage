import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from services.db import Base, engine
from models import employee, sow, invoice, payment  # ensure all models are registered
from routers import employees, sows, invoices, dashboard, payments, chat, import_data

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Resource Management System",
    description="Manage Employees, SOWs, and Invoices",
    version="1.0.0",
)

# API Routers
app.include_router(employees.router)
app.include_router(sows.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(payments.router)
app.include_router(chat.router)
app.include_router(import_data.router)

# Serve frontend
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_path = os.path.join(base_dir, "frontend", "admin")
os.makedirs(frontend_path, exist_ok=True)

app.mount("/admin", StaticFiles(directory=frontend_path, html=True), name="admin_static")


@app.get("/")
def root():
    return RedirectResponse(url="/admin/index.html")
