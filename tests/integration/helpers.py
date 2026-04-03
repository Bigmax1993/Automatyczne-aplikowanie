"""Pomocnicze sprawdzanie flag ENV dla opcjonalnych testów sieciowych."""

from __future__ import annotations

import os

import config


def env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def openai_key_ok_for_live_api() -> bool:
    """Klucz z .env po normalizacji w config; HTTP Bearer wymaga ASCII."""
    k = config.OPENAI_API_KEY
    if not k or not str(k).strip():
        return False
    return str(k).isascii()


def drive_id_looks_real(raw: str | None) -> bool:
    """Pomija integrację Drive, gdy w .env został przykładowy / zbyt krótki identyfikator."""
    if not raw:
        return False
    s = raw.strip()
    if len(s) < 25:
        return False
    low = s.lower()
    bogus = ("id_folderu", "your_", "example", "placeholder", "xxxx", "changeme", "todo")
    return not any(b in low for b in bogus)
