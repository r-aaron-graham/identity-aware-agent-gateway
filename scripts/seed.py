import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db import init_db, fetch_one, execute

DOCS = [
    (
        "DOC-PUB-ONBOARD",
        "Onboarding Checklist",
        "public",
        "New team members should complete account setup, security training, and the onboarding checklist before production access is granted.",
    ),
    (
        "DOC-INT-RUNBOOK",
        "Oncall Incident Runbook",
        "internal",
        "The oncall incident runbook covers triage, ticket assignment, customer communication, and escalation timelines for service-impacting incidents.",
    ),
    (
        "DOC-RES-ARCH",
        "Architecture Exception Standard",
        "restricted",
        "Architecture exceptions require documented risk acceptance, reviewer signoff, and a bounded remediation timeline before approval.",
    ),
    (
        "DOC-CONF-FIN",
        "Quarterly Finance Export Procedure",
        "confidential",
        "Quarterly finance exports include margin and payroll-sensitive data and require admin approval before release or external sharing.",
    ),
    (
        "DOC-INT-TICKET",
        "Ticket Triage SOP",
        "internal",
        "Ticket triage uses severity, customer impact, and ownership routing to assign requests to the appropriate queue.",
    ),
]

def main():
    init_db()
    for doc_id, title, classification, content in DOCS:
        exists = fetch_one("SELECT id FROM documents WHERE doc_id = ?", (doc_id,))
        if not exists:
            execute(
                "INSERT INTO documents (doc_id, title, classification, content, updated_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (doc_id, title, classification, content),
            )
    print("Seed complete.")

if __name__ == "__main__":
    main()
