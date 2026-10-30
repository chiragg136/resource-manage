# Resource Management System — Render Deployment

This folder (`resource-mgmt-render`) is pre-configured for one-click or manual deployment on **[Render](https://render.com)** using **FastAPI** + **Render PostgreSQL (Free)**.

---

## Architecture Overview

```
resource-mgmt-render/
├── render.yaml          ← Render Blueprint (creates Web Service + PostgreSQL DB together)
├── build.sh             ← Automated build & seed script executed on Render
├── .gitignore           ← Ignores cache, .venv, .env
├── .env.example         ← Template for environment variables
├── backend/
│   ├── main.py          ← FastAPI application entry point (serves API & static frontend)
│   ├── requirements.txt ← Python packages with PostgreSQL driver (psycopg2-binary)
│   ├── seed.py          ← Safe database seeder (initializes sample data if empty)
│   ├── models/          ← Database models (PostgreSQL compatible)
│   ├── routers/         ← API routes (Employees, SOWs, Invoices, Payments, Chat, Import)
│   ├── schemas/         ← Pydantic schemas
│   └── services/
│       └── db.py        ← SQLAlchemy DB engine (auto-maps Render's postgres:// to postgresql://)
└── frontend/
    └── admin/           ← Complete Admin UI
        ├── dashboard.html
        ├── employees.html
        ├── sows.html
        ├── invoices.html
        ├── payments.html
        ├── css/style.css
        └── js/app.js, chatbot.js
```

---

## Deployment Option 1: Render Blueprint (Easiest & Recommended)

With `render.yaml`, Render creates both your **Web Service** and your **PostgreSQL Database** automatically in one step.

### Step 1: Push this folder to a GitHub Repository
1. Initialize git inside this folder or push it to a new GitHub repo:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for Render deployment"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/resource-mgmt.git
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Log in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository.
4. Render will detect `render.yaml` and display:
   - **PostgreSQL Database**: `resource-mgmt-db` (Free plan)
   - **Web Service**: `resource-mgmt` (Free plan)
5. Fill in the requested environment variable:
   - `GROQ_API_KEY`: Paste your Groq API key (for the AI Chatbot).
6. Click **Apply**.
7. Render will automatically:
   - Provision the PostgreSQL database.
   - Run `build.sh` (installs dependencies, creates tables, and seeds sample data).
   - Start the FastAPI web service.

Your application will be live at:
```
https://resource-mgmt-xxxx.onrender.com
```

---

## Deployment Option 2: Manual Setup on Render

If you prefer to configure services manually via the Render UI:

### Step 1: Create PostgreSQL Database on Render
1. In Render Dashboard, click **New +** → **PostgreSQL**.
2. **Name**: `resource-mgmt-db`
3. **Database**: `resource_management_db`
4. **User**: `resadmin`
5. **Plan**: Free
6. Click **Create Database**.
7. Once created, copy the **Internal Database URL** (e.g., `postgres://resadmin:xxx@dpg-xxx:5432/resource_management_db`).

### Step 2: Create Web Service on Render
1. Click **New +** → **Web Service**.
2. Connect your GitHub repository.
3. Configure settings:
   - **Name**: `resource-mgmt`
   - **Language**: `Python`
   - **Branch**: `main`
   - **Region**: Same region as your database
   - **Build Command**: `./build.sh` (or `pip install -r backend/requirements.txt && python backend/seed.py`)
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. In **Environment Variables**, add:
   - `DATABASE_URL`: Paste the Internal Database URL from Step 1.
   - `GROQ_API_KEY`: Paste your Groq API key.
   - `PYTHON_VERSION`: `3.11.9`
5. Click **Create Web Service**.

---

## Features Ready on Render
- ✅ **PostgreSQL integration**: Zero configuration needed, automatically handles Render's `postgres://` connection string.
- ✅ **Auto-table creation**: `main.py` creates all tables automatically on startup.
- ✅ **Auto-seeding**: `seed.py` is idempotent — seeds initial records once and safely skips if data already exists.
- ✅ **Full Admin Interface**: Employees, SOWs, Invoices, Payments, Mass Import (Excel/CSV with duplicate detection), and AI Chatbot.
