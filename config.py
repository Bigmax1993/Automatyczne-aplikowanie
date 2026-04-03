"""
config.py
Centralna konfiguracja projektu: ścieżki, ENV, logowanie, stałe.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


def _configure_text_streams_utf8() -> None:
    """
    Na Windows stderr/stdout bywa cp1252 lub ascii.
    Logi z polskimi znakami mogą wtedy rzucać UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, TypeError):
                pass


_configure_text_streams_utf8()

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"

DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)

REPORT_XLSX = OUTPUT_DIR / "report.xlsx"
CV_LOCAL_PATH = DATA_DIR / "cv.pdf"


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


# Cudzysłowy z Word/PDF + BOM — potrafią dodać znaki spoza ASCII przy wklejaniu do .env
_ENV_QUOTE_CHARS = frozenset("\"'`\u201c\u201d\u201e\u201f\u00ab\u00bb\u2039\u203a")


def _strip_env_secret(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    while s.startswith("\ufeff"):
        s = s[1:].lstrip()
    changed = True
    while changed and s:
        changed = False
        s = s.strip()
        if len(s) >= 2 and s[0] in _ENV_QUOTE_CHARS and s[-1] in _ENV_QUOTE_CHARS:
            s = s[1:-1]
            changed = True
    return s or None


SERPAPI_API_KEY = _strip_env_secret(os.getenv("SERPAPI_API_KEY"))
OPENAI_API_KEY = _strip_env_secret(os.getenv("OPENAI_API_KEY"))
SMTP_USER = _strip_env_secret(os.getenv("SMTP_USER"))
SMTP_PASS = _strip_env_secret(os.getenv("SMTP_PASS"))
CV_DRIVE_ID = _strip_env_secret(os.getenv("CV_DRIVE_ID"))

PIPELINE_DRY_RUN = _env_bool("PIPELINE_DRY_RUN", False)
PIPELINE_RESUME = _env_bool("PIPELINE_RESUME", False)
CLEAR_CHECKPOINT_ON_SUCCESS = _env_bool("CLEAR_CHECKPOINT_ON_SUCCESS", True)

# Zapytania i lokalizacje Google Jobs (SerpApi) — dostosuj pod siebie
JOB_QUERIES = [
    "Python developer",
    "backend developer",
]
JOB_LOCATIONS = [
    "Poznań, Poland",
    "Wrocław, Poland",
    "Zielona Góra, Poland",
]

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger.add(
    OUTPUT_DIR / "pipeline.log",
    level=_LOG_LEVEL,
    rotation="1 week",
    encoding="utf-8",
    enqueue=True,
    backtrace=True,
    diagnose=False,
)
