import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
CASES_DIR = REPO_ROOT / "data" / "cases"

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
NPC_MODEL = os.environ.get("NPC_MODEL", "claude-haiku-4-5-20251001")
REPORT_MODEL = os.environ.get("REPORT_MODEL", "claude-sonnet-5")

CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]
