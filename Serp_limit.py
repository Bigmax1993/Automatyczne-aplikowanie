"""
Serp_limit.py
Twardy limit 250 zapytań do SerpApi — bez wyjątków i obejść.

- Jeden licznik w pliku JSON + blokada plikowa (wiele procesów).
- Każde udane ``serp_quota_acquire()`` przed HTTP zużywa dokładnie 1 slot.
- Przy count >= HARD_LIMIT kolejne acquire zawsze zwraca False (żadnego wyjścia „poza limit”).
"""

from __future__ import annotations

import json

from filelock import FileLock
from loguru import logger

from config import DATA_DIR

USAGE_FILE = DATA_DIR / "serp_usage.json"
LOCK_FILE = USAGE_FILE.with_suffix(".lock.json")
HARD_LIMIT = 250


def _load_count_unlocked() -> int:
    if not USAGE_FILE.exists():
        return 0
    data = json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    return int(data.get("count", 0))


def _save_count_unlocked(count: int) -> None:
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(
        json.dumps({"count": count}, indent=2),
        encoding="utf-8",
    )


def serp_quota_get_count() -> int:
    """Aktualna liczba zużytych slotów (tylko odczyt, pod lockiem)."""
    with FileLock(str(LOCK_FILE), timeout=120):
        return _load_count_unlocked()


def serp_quota_acquire() -> bool:
    """
    Rezerwuje jeden slot limitu (atomowo). Wywołaj **przed** każdym requestem do SerpApi.

    - Gdy count >= HARD_LIMIT: zwraca False (nic nie zmienia).
    - W przeciwnym razie: count += 1, zapis, zwraca True.
    - Przy błędzie HTTP **nie** cofamy — limit jest twardy w sensie „250 prób zarezerwowanych”.
    """
    with FileLock(str(LOCK_FILE), timeout=120):
        count = _load_count_unlocked()
        if count >= HARD_LIMIT:
            logger.error(
                f"SERP LIMIT: twardy limit {HARD_LIMIT} zapytań — brak wolnych slotów "
                f"(obecnie {count})."
            )
            return False
        count += 1
        _save_count_unlocked(count)
        logger.debug(f"SERP LIMIT: zużyto slot {count}/{HARD_LIMIT}.")
        return True
