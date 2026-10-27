ROLE_PERMISSIONS = {
    "viewer": {
        "classifications": ["public"],
        "tools": ["search_docs"],
        "max_sensitivity": "low",
    },
    "analyst": {
        "classifications": ["public", "internal"],
        "tools": ["search_docs", "ticket_lookup"],
        "max_sensitivity": "medium",
    },
    "architect": {
        "classifications": ["public", "internal", "restricted"],
        "tools": ["search_docs", "ticket_lookup", "system_summary"],
        "max_sensitivity": "high",
    },
    "reviewer": {
        "classifications": ["public", "internal", "restricted"],
        "tools": ["search_docs", "system_summary", "review_queue"],
        "max_sensitivity": "high",
    },
    "admin": {
        "classifications": ["public", "internal", "restricted", "confidential"],
        "tools": ["search_docs", "ticket_lookup", "system_summary", "finance_export", "review_queue"],
        "max_sensitivity": "critical",
    },
}

SENSITIVITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


def permissions_for(role: str) -> dict:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])
