# Mock in-memory database for IT Admin Panel
from datetime import datetime

# ─── USERS DATABASE ──────────────────────────────────────

USERS_DB = {
    "john@company.com": {
        "id": 1,
        "name": "John Smith",
        "email": "john@company.com",
        "role": "Developer",
        "department": "Engineering",
        "status": "active",
        "password": "password123",
        "licenses": ["Microsoft 365", "GitHub"],
        "created_at": "2024-01-15",
    },
    "sarah@company.com": {
        "id": 2,
        "name": "Sarah Johnson",
        "email": "sarah@company.com",
        "role": "Product Manager",
        "department": "Product",
        "status": "active",
        "password": "password456",
        "licenses": ["Microsoft 365", "Jira", "Figma"],
        "created_at": "2024-02-20",
    },
    "mike@company.com": {
        "id": 3,
        "name": "Mike Davis",
        "email": "mike@company.com",
        "role": "Designer",
        "department": "Design",
        "status": "inactive",
        "password": "password789",
        "licenses": ["Figma"],
        "created_at": "2024-03-10",
    },
}


# ─── LICENSES ───────────────────────────────────────────

AVAILABLE_LICENSES = [
    "Microsoft 365",
    "GitHub",
    "Jira",
    "Figma",
    "Slack",
    "Zoom",
    "Salesforce",
    "AWS Console",
]


# ─── AUDIT LOG ──────────────────────────────────────────

AUDIT_LOG = []

# ✅ Clean any corrupted data at startup
AUDIT_LOG = [log for log in AUDIT_LOG if isinstance(log, dict)]


# ─── SAFE LOG FUNCTION (FINAL FIX) ──────────────────────

def log_action(action: str, details: str, performed_by: str = "AI Agent"):
    """
    Safe logging function that prevents tuple/dict corruption.
    """

    try:
        # ✅ Force safe types
        action = str(action)
        details = str(details)
        performed_by = str(performed_by)

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "performed_by": performed_by,
        }

        # ✅ Only append valid dict
        if isinstance(entry, dict):
            AUDIT_LOG.append(entry)

    except Exception:
        # fallback safe log
        AUDIT_LOG.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": "ERROR",
            "details": "Invalid log entry prevented",
            "performed_by": "SYSTEM",
        })