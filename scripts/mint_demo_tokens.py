import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth import mint_token
from app.config import DEMO_USERS

for key, user in DEMO_USERS.items():
    print(f"{key}: {mint_token(user['user_id'], user['name'], user['role'])}")
