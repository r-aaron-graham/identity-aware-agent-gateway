from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "iaag.db"

SECRET_KEY = os.getenv("IAAG_SECRET_KEY", "change-me")
DB_PATH = Path(os.getenv("IAAG_DB_PATH", str(DEFAULT_DB_PATH)))
AUTO_INIT_DB = os.getenv("IAAG_AUTO_INIT_DB", "true").lower() == "true"
TOKEN_TTL_SECONDS = int(os.getenv("IAAG_TOKEN_TTL_SECONDS", "43200"))  # 12 hours

DEMO_USERS = {
    "viewer": {"user_id": "u_viewer_jane", "name": "Jane Viewer", "role": "viewer"},
    "analyst": {"user_id": "u_analyst_aaron", "name": "Aaron Analyst", "role": "analyst"},
    "architect": {"user_id": "u_architect_riley", "name": "Riley Architect", "role": "architect"},
    "reviewer": {"user_id": "u_reviewer_sam", "name": "Sam Reviewer", "role": "reviewer"},
    "admin": {"user_id": "u_admin_ada", "name": "Ada Admin", "role": "admin"},
}
