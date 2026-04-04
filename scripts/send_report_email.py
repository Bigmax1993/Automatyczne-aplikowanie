"""
Wysyła najnowszy plik .xlsx z katalogu raportów (domyślnie output/) jako załącznik.
Używane z GitHub Actions (sekrety SMTP_*).
"""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from loguru import logger

from config import OUTPUT_DIR, REPORT_XLSX


def _smtp_config() -> tuple[str, str, str]:
    user = (os.getenv("SMTP_USER") or "").strip()
    password = (os.getenv("SMTP_PASS") or "").strip()
    to_addr = (os.getenv("REPORT_EMAIL_TO") or user).strip()
    if not user or not password:
        raise ValueError("Brak SMTP_USER lub SMTP_PASS — ustaw sekrety repozytorium.")
    if not to_addr:
        raise ValueError("Brak adresu odbiorcy (REPORT_EMAIL_TO lub SMTP_USER).")
    return user, password, to_addr


def _pick_report_path() -> Path:
    explicit = (os.getenv("REPORT_XLSX_PATH") or "").strip()
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p
        raise FileNotFoundError(f"REPORT_XLSX_PATH nie wskazuje na plik: {p}")

    if REPORT_XLSX.is_file():
        return REPORT_XLSX

    out = Path(OUTPUT_DIR)
    if not out.is_dir():
        raise FileNotFoundError(f"Brak katalogu output: {out}")

    candidates = sorted(out.glob("*.xlsx"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"Brak plików .xlsx w {out}")
    return candidates[0]


def send_latest_report() -> None:
    user, password, to_addr = _smtp_config()
    path = _pick_report_path()

    msg = EmailMessage()
    msg["From"] = user
    msg["To"] = to_addr
    msg["Subject"] = f"Raport pipeline — {path.name}"
    msg.set_content(
        "Załącznik: raport Excel z automatycznego pipeline'u.\n"
        f"Plik: {path.name}\n"
    )

    data = path.read_bytes()
    msg.add_attachment(
        data,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=path.name,
    )

    logger.info("Wysyłam raport e-mailem → {} (załącznik: {})", to_addr, path.name)
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
    logger.info("Wysłano raport.")
