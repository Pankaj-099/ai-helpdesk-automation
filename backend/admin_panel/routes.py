from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

from .database import USERS_DB, AVAILABLE_LICENSES, AUDIT_LOG, log_action

# ─── CLEANING ─────────────────────────────────────────

def clean_users_db():
    global USERS_DB
    USERS_DB = {
        k: v for k, v in USERS_DB.items()
        if isinstance(k, str) and isinstance(v, dict)
    }

def clean_audit_log():
    global AUDIT_LOG
    AUDIT_LOG[:] = [log for log in AUDIT_LOG if isinstance(log, dict)]


router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)

# ─── HELPERS ─────────────────────────────────────────

def safe_users():
    return [u for u in USERS_DB.values() if isinstance(u, dict)]

def safe_logs():
    return [log for log in AUDIT_LOG if isinstance(log, dict)]


# ─── DASHBOARD ───────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
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


# ─── USERS ───────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, search: str = ""):
    clean_users_db()

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


# ─── CREATE USER ──────────────────────────────────────

@router.get("/users/create", response_class=HTMLResponse)
async def create_user_form(request: Request):
    return templates.TemplateResponse(
        "create_user.html",
        {"request": request, "licenses": AVAILABLE_LICENSES, "message": None}
    )


@router.post("/users/create", response_class=HTMLResponse)
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    department: str = Form(...),
    password: str = Form(...),
):
    clean_users_db()

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

    log_action("CREATE_USER", f"{email}")

    return templates.TemplateResponse(
        "create_user.html",
        {
            "request": request,
            "licenses": AVAILABLE_LICENSES,
            "message": "✅ User created successfully",
            "message_type": "success",
        },
    )


# ─── RESET PASSWORD ───────────────────────────────────

@router.get("/users/reset-password", response_class=HTMLResponse)
async def reset_password_form(request: Request, email: str = ""):
    user = USERS_DB.get(email)
    return templates.TemplateResponse(
        "reset_password.html",
        {"request": request, "user": user, "prefill_email": email, "message": None}
    )


@router.post("/users/reset-password", response_class=HTMLResponse)
async def reset_password(
    request: Request,
    email: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    clean_users_db()

    if email not in USERS_DB:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "user": None,
                "prefill_email": email,
                "message": "❌ User not found",
                "message_type": "error",
            },
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "user": USERS_DB[email],
                "prefill_email": email,
                "message": "❌ Passwords do not match",
                "message_type": "error",
            },
        )

    USERS_DB[email]["password"] = new_password
    log_action("RESET_PASSWORD", email)

    return templates.TemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "user": USERS_DB[email],
            "prefill_email": email,
            "message": "✅ Password reset successful",
            "message_type": "success",
        },
    )


# ─── LICENSES ─────────────────────────────────────────

@router.get("/users/licenses", response_class=HTMLResponse)
async def licenses_form(request: Request, email: str = ""):
    clean_users_db()

    user = USERS_DB.get(email)

    return templates.TemplateResponse(
        "licenses.html",
        {
            "request": request,
            "user": user,
            "prefill_email": email,
            "all_licenses": AVAILABLE_LICENSES,
            "message": None,
        },
    )


@router.post("/users/licenses", response_class=HTMLResponse)
async def assign_license(
    request: Request,
    email: str = Form(...),
    license_name: str = Form(...),
    action: str = Form(...),
):
    clean_users_db()

    if email not in USERS_DB:
        return HTMLResponse("User not found")

    user = USERS_DB[email]

    if action == "assign":
        if license_name not in user["licenses"]:
            user["licenses"].append(license_name)
            log_action("ASSIGN_LICENSE", f"{license_name} → {email}")
    else:
        if license_name in user["licenses"]:
            user["licenses"].remove(license_name)
            log_action("REVOKE_LICENSE", f"{license_name} → {email}")

    return templates.TemplateResponse(
        "licenses.html",
        {
            "request": request,
            "user": user,
            "prefill_email": email,
            "all_licenses": AVAILABLE_LICENSES,
            "message": "✅ Updated successfully",
            "message_type": "success",
        },
    )


# ─── TOGGLE STATUS ───────────────────────────────────

@router.get("/users/toggle-status", response_class=HTMLResponse)
async def toggle_status_form(request: Request, email: str = ""):
    clean_users_db()

    user = USERS_DB.get(email)

    return templates.TemplateResponse(
        "toggle_status.html",
        {
            "request": request,
            "user": user,
            "prefill_email": email,
            "message": None,
        },
    )


@router.post("/users/toggle-status", response_class=HTMLResponse)
async def toggle_status(
    request: Request,
    email: str = Form(...),
    action: str = Form(...),
):
    clean_users_db()

    if email not in USERS_DB:
        return HTMLResponse("User not found")

    USERS_DB[email]["status"] = "active" if action == "activate" else "inactive"

    log_action("TOGGLE_STATUS", f"{email} → {action}")

    return templates.TemplateResponse(
        "toggle_status.html",
        {
            "request": request,
            "user": USERS_DB[email],
            "prefill_email": email,
            "message": "✅ Status updated",
            "message_type": "success",
        },
    )


# ─── AUDIT LOG ─────────────────────────────────────────

@router.get("/audit-log", response_class=HTMLResponse)
async def audit_log(request: Request):
    clean_audit_log()

    logs = safe_logs()[::-1]

    return templates.TemplateResponse(
        "audit_log.html",
        {"request": request, "logs": logs}
    )