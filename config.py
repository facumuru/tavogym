import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"

# Render y Neon entregan postgres:// pero psycopg2 necesita postgresql://
_raw_db_url = os.getenv("DATABASE_URL", "")
if _raw_db_url.startswith("postgres://"):
    _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
DATABASE_URL = _raw_db_url

SECRET_KEY = os.getenv("SECRET_KEY", "tavogym-dev-key-cambiar-en-produccion")

_private = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PRIVATE_KEY = _private.replace("\\n", "\n") if _private else ""
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "mailto:admin@tavogym.com")

MONTHLY_FEE_DEFAULT = int(os.getenv("MONTHLY_FEE_DEFAULT", "25000"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "tavo")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "tavogym2024")
