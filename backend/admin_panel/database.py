# Mock in-memory database for IT Admin Panel
from datetime import datetime

# Seed data - simulates a real company directory
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

AUDIT_LOG = []


def log_action(action: str, details: str, performed_by: str = "AI Agent"):
    AUDIT_LOG.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "details": details,
            "performed_by": performed_by,
        }
    )
