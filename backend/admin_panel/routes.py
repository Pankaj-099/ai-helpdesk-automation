from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

from .database import USERS_DB, AVAILABLE_LICENSES, AUDIT_LOG, log_action

# ─── DATA CLEANING FIX ─────────────────────────

def clean_users_db():
    global USERS_DB
    USERS_DB = {
        k: v for k, v in USERS_DB.items()
        if isinstance(k, str) and isinstance(v, dict)
    }


def clean_audit_log():
    global AUDIT_LOG
    AUDIT_LOG[:] = [
        log for log in AUDIT_LOG
        if isinstance(log, dict)
    ]


router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


# ─── SAFE HELPERS ─────────────────────────────────────────

def safe_users():
    return [u for u in USERS_DB.values() if isinstance(u, dict)]


def safe_logs():
    return [log for log in AUDIT_LOG if isinstance(log, dict)]


# ─── Dashboard ────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        # ✅ IMPORTANT FIX (YOU MISSED THIS)
        clean_users_db()
        clean_audit_log()

        users = safe_users()
        logs = safe_logs()

        stats = {
            "total_users": len(users),
            "active_users": sum(1 for u in users if u.get("status") == "active"),
            "inactive_users": sum(1 for u in users if u.get("status") == "inactive"),
            "recent_actions": logs[-5:][::-1],
        }

        return templates.TemplateResponse(
            "dashboard.html",
            {"request": request, "stats": stats}
        )

    except Exception as e:
        return HTMLResponse(f"Dashboard Error: {str(e)}")


# ─── Users List ───────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, search: str = ""):
    try:
        clean_users_db()  # ✅ ADD THIS

        users = safe_users()

        if search:
            users = [
                u for u in users
                if search.lower() in u.get("email", "").lower()
                or search.lower() in u.get("name", "").lower()
            ]

        return templates.TemplateResponse(
            "users.html",
            {"request": request, "users": users, "search": search}
        )

    except Exception as e:
        return HTMLResponse(f"Error: {str(e)}")


# ─── Create User ──────────────────────────────────────────

@router.post("/users/create", response_class=HTMLResponse)
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
    password: str = Form(...),
):
    clean_users_db()  # ✅ ADD THIS

    if email in USERS_DB:
        return templates.TemplateResponse(
            "create_user.html",
            {
                "request": request,
                "licenses": AVAILABLE_LICENSES,
                "message": f"❌ User {email} already exists.",
                "message_type": "error",
            },
        )

    new_id = max((u["id"] for u in safe_users()), default=0) + 1

    USERS_DB[email] = {
        "id": new_id,
        "name": name,
        "email": email,
        "role": role,
        "department": department,
        "status": "active",
        "password": password,
        "licenses": [],
        "created_at": __import__("datetime").date.today().isoformat(),
    }

    log_action("CREATE_USER", f"Created user {name} ({email}), Role: {role}")

    return templates.TemplateResponse(
        "create_user.html",
        {
            "request": request,
            "licenses": AVAILABLE_LICENSES,
            "message": f"✅ User {name} created successfully!",
            "message_type": "success",
        },
    )


# ─── Reset Password ───────────────────────────────────────

@router.post("/users/reset-password", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    clean_users_db()  # ✅ ADD THIS

    if email not in USERS_DB or not isinstance(USERS_DB[email], dict):
        return HTMLResponse("User not found")

    if new_password != confirm_password:
        return HTMLResponse("Passwords do not match")

    USERS_DB[email]["password"] = new_password
    log_action("RESET_PASSWORD", f"Password reset for {email}")

    return HTMLResponse("Password reset successful")


# ─── Audit Log ───────────────────────────────────────────

@router.get("/audit-log", response_class=HTMLResponse)
async def audit_log(request: Request):
    clean_audit_log()  # ✅ ADD THIS

    logs = safe_logs()[::-1]

    return templates.TemplateResponse(
        "audit_log.html",
        {"request": request, "logs": logs}
    )