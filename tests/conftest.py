import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Point the app at a throwaway database before any app module is imported,
# so tests never touch (or depend on) a developer's local data/iaag.db.
_TMP_DIR = tempfile.mkdtemp(prefix="iaag-tests-")
os.environ.setdefault("IAAG_DB_PATH", str(Path(_TMP_DIR) / "test.db"))
os.environ.setdefault("IAAG_SECRET_KEY", "test-secret-key")
