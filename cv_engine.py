"""
cv_engine.py
Pobieranie CV z Google Drive i zapis lokalny.
"""

from pathlib import Path

import requests
from loguru import logger

from config import CV_DRIVE_ID, CV_LOCAL_PATH

DRIVE_EXPORT_URL = "https://drive.google.com/uc"


def _confirm_token(response: requests.Response) -> str | None:
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            return value
    return None


def _looks_like_html(data: bytes) -> bool:
    head = data[:512].lstrip().lower()
    return head.startswith(b"<!doctype") or head.startswith(b"<html")


def download_cv() -> bool:
    """
    Pobiera CV z Google Drive na podstawie CV_DRIVE_ID.
    Zwraca True/False w zależności od powodzenia operacji.
    """
    if not CV_DRIVE_ID:
        logger.error("Brak CV_DRIVE_ID w .env – nie można pobrać CV.")
        return False

    dest = Path(CV_LOCAL_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    params = {"export": "download", "id": CV_DRIVE_ID}
    logger.info(f"Pobieram CV z Google Drive (id={CV_DRIVE_ID})")

    try:
        response = session.get(
            DRIVE_EXPORT_URL,
            params=params,
            stream=True,
            timeout=30,
        )
        response.raise_for_status()

        token = _confirm_token(response)
        if token:
            response.close()
            response = session.get(
                DRIVE_EXPORT_URL,
                params={**params, "confirm": token},
                stream=True,
                timeout=30,
            )
            response.raise_for_status()

        first_chunk: bytes | None = None
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                if first_chunk is None:
                    first_chunk = chunk
                f.write(chunk)

        if first_chunk is None:
            logger.error("Pusta odpowiedź z Google Drive.")
            return False

        if _looks_like_html(first_chunk):
            logger.error(
                "Zapisana treść wygląda na stronę HTML (np. blokada Drive / brak dostępu), "
                "nie na plik CV. Sprawdź udostępnienie pliku i CV_DRIVE_ID."
            )
            dest.unlink(missing_ok=True)
            return False

        logger.info(f"CV zapisane → {dest}")
        return True

    except requests.RequestException as e:
        logger.error(f"Błąd HTTP przy pobieraniu CV: {e}")
        return False
    except OSError as e:
        logger.error(f"Błąd zapisu CV na dysk: {e}")
        return False
