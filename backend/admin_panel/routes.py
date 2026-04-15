from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

from .database import USERS_DB, AVAILABLE_LICENSES, AUDIT_LOG, log_action

router = APIRouter()
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


# ─── Dashboard ───────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    stats = {
        "total_users": len(USERS_DB),
        "active_users": sum(1 for u in USERS_DB.values() if u["status"] == "active"),
        "inactive_users": sum(1 for u in USERS_DB.values() if u["status"] == "inactive"),
        "recent_actions": AUDIT_LOG[-5:][::-1],
    }
    return templates.TemplateResponse("dashboard.html", {"request": request, "stats": stats})


# ─── Users List ──────────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, search: str = ""):
    users = list(USERS_DB.values())
    if search:
        users = [
            u for u in users
            if search.lower() in u["email"].lower() or search.lower() in u["name"].lower()
        ]
    return templates.TemplateResponse(
        "users.html", {"request": request, "users": users, "search": search}
    )


# ─── Create User ─────────────────────────────────────────────────────────────

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

    new_id = max((u["id"] for u in USERS_DB.values()), default=0) + 1
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
            "message": f"✅ User {name} ({email}) created successfully!",
            "message_type": "success",
        },
    )


# ─── Reset Password ───────────────────────────────────────────────────────────

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
    if email not in USERS_DB:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "user": None,
                "prefill_email": email,
                "message": f"❌ User {email} not found.",
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
                "message": "❌ Passwords do not match.",
                "message_type": "error",
            },
        )
    if len(new_password) < 6:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "user": USERS_DB[email],
                "prefill_email": email,
                "message": "❌ Password must be at least 6 characters.",
                "message_type": "error",
            },
        )

    USERS_DB[email]["password"] = new_password
    log_action("RESET_PASSWORD", f"Password reset for {email}")
    return templates.TemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "user": USERS_DB[email],
            "prefill_email": email,
            "message": f"✅ Password for {email} has been reset successfully!",
            "message_type": "success",
        },
    )


# ─── Assign / Revoke License ─────────────────────────────────────────────────

@router.get("/users/licenses", response_class=HTMLResponse)
async def licenses_form(request: Request, email: str = ""):
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
    action: str = Form(...),  # "assign" or "revoke"
):
    if email not in USERS_DB:
        return templates.TemplateResponse(
            "licenses.html",
            {
                "request": request,
                "user": None,
                "prefill_email": email,
                "all_licenses": AVAILABLE_LICENSES,
                "message": f"❌ User {email} not found.",
                "message_type": "error",
            },
        )

    user = USERS_DB[email]
    if action == "assign":
        if license_name in user["licenses"]:
            msg = f"⚠️ {license_name} is already assigned to {email}."
            msg_type = "warning"
        else:
            user["licenses"].append(license_name)
            log_action("ASSIGN_LICENSE", f"Assigned {license_name} to {email}")
            msg = f"✅ {license_name} assigned to {email} successfully!"
            msg_type = "success"
    else:
        if license_name not in user["licenses"]:
            msg = f"⚠️ {license_name} was not assigned to {email}."
            msg_type = "warning"
        else:
            user["licenses"].remove(license_name)
            log_action("REVOKE_LICENSE", f"Revoked {license_name} from {email}")
            msg = f"✅ {license_name} revoked from {email} successfully!"
            msg_type = "success"

    return templates.TemplateResponse(
        "licenses.html",
        {
            "request": request,
            "user": USERS_DB[email],
            "prefill_email": email,
            "all_licenses": AVAILABLE_LICENSES,
            "message": msg,
            "message_type": msg_type,
        },
    )


# ─── Toggle User Status ───────────────────────────────────────────────────────

@router.get("/users/toggle-status", response_class=HTMLResponse)
async def toggle_status_form(request: Request, email: str = ""):
    user = USERS_DB.get(email)
    return templates.TemplateResponse(
        "toggle_status.html",
        {"request": request, "user": user, "prefill_email": email, "message": None}
    )


@router.post("/users/toggle-status", response_class=HTMLResponse)
async def toggle_status(
    request: Request,
    email: str = Form(...),
    action: str = Form(...),  # "activate" or "deactivate"
):
    if email not in USERS_DB:
        return templates.TemplateResponse(
            "toggle_status.html",
            {
                "request": request,
                "user": None,
                "prefill_email": email,
                "message": f"❌ User {email} not found.",
                "message_type": "error",
            },
        )

    user = USERS_DB[email]
    new_status = "active" if action == "activate" else "inactive"
    user["status"] = new_status
    log_action("TOGGLE_STATUS", f"User {email} set to {new_status}")
    return templates.TemplateResponse(
        "toggle_status.html",
        {
            "request": request,
            "user": user,
            "prefill_email": email,
            "message": f"✅ User {email} is now {new_status}.",
            "message_type": "success",
        },
    )


# ─── Audit Log ────────────────────────────────────────────────────────────────

@router.get("/audit-log", response_class=HTMLResponse)
async def audit_log(request: Request):
    return templates.TemplateResponse(
        "audit_log.html",
        {"request": request, "logs": AUDIT_LOG[::-1]}
    )
