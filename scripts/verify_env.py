"""
Diagnostyka .env bez ujawniania pełnych sekretów.
Uruchom z katalogu projektu: python scripts/verify_env.py
Kod wyjścia: 0 = OK, 1 = krytyczny problem (np. klucz API z ogonkami).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _report(name: str, val: str | None, *, show_prefix: bool) -> bool:
    """Zwraca True, jeśli wartość jest ustawiona, ale nie-ASCII (dla kluczy API)."""
    if val is None or not str(val).strip():
        print(f"  {name}: (brak / pusty)")
        return False
    s = str(val)
    ascii_ok = s.isascii()
    tip = "OK" if ascii_ok else "BŁĄD: znaki spoza ASCII — HTTP/SMTP się wyłożą"
    extra = ""
    if show_prefix:
        head = s[:12]
        extra = f" | początek (max 12 znaków): {head!r}"
    else:
        extra = " | (treść ukryta — tylko metadane)"
    print(f"  {name}: len={len(s)} ascii={ascii_ok} | {tip}{extra}")
    return not ascii_ok


def main() -> int:
    env_path = ROOT / ".env"
    print(f"Katalog projektu: {ROOT}")
    print(f"Plik .env: {'istnieje' if env_path.is_file() else 'BRAK — skopiuj .env.example'}")
    print("Wczytywanie config (load_dotenv)...")

    import config  # noqa: PLC0415 — po sys.path

    print("\nZmienne (wartości sekretów nie są drukowane w całości):\n")

    bad_api = False
    bad_api |= _report("SERPAPI_API_KEY", config.SERPAPI_API_KEY, show_prefix=True)
    bad_api |= _report("OPENAI_API_KEY", config.OPENAI_API_KEY, show_prefix=True)

    _report("SMTP_USER", config.SMTP_USER, show_prefix=True)
    _report("SMTP_PASS", config.SMTP_PASS, show_prefix=False)
    _report("CV_DRIVE_ID", config.CV_DRIVE_ID, show_prefix=True)
    if config.CV_DRIVE_ID and str(config.CV_DRIVE_ID).strip().lower().startswith("http"):
        print(
            "  UWAGA: CV_DRIVE_ID wygląda na URL — moduł cv_engine używa tylko "
            "identyfikatora pliku (fragment `id=...` z linku Google Drive)."
        )

    print("\nFlagi pipeline:")
    print(f"  PIPELINE_DRY_RUN={config.PIPELINE_DRY_RUN}")
    print(f"  PIPELINE_RESUME={config.PIPELINE_RESUME}")
    print(f"  CLEAR_CHECKPOINT_ON_SUCCESS={config.CLEAR_CHECKPOINT_ON_SUCCESS}")

    if bad_api:
        print(
            "\n>>> Napraw .env: klucze Serp/OpenAI muszą być wyłącznie ASCII "
            "(prawdziwy sk-... / klucz z panelu). "
            "Polski placeholder lub cudzysłowy z Worda psują żądania."
        )
        return 1

    print("\nKlucze API wyglądają poprawnie (ASCII).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
