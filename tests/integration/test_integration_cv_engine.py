"""Integracja: cv_engine — prawdziwe pobranie z Google Drive (opcjonalnie)."""

from __future__ import annotations

import os

import pytest

import config
import cv_engine
from tests.integration.helpers import drive_id_looks_real, env_truthy


def _drive_id() -> str:
    return (config.CV_DRIVE_ID or os.getenv("CV_DRIVE_ID") or "").strip()


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_DRIVE_INTEGRATION")
    or not _drive_id()
    or not drive_id_looks_real(_drive_id()),
    reason=(
        "Ustaw RUN_DRIVE_INTEGRATION=1 i prawdziwy CV_DRIVE_ID z linku do pliku (min. ~25 znaków), "
        "nie placeholder z .env.example."
    ),
)
def test_download_cv_from_google_drive(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "downloaded_cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", _drive_id())

    ok = cv_engine.download_cv()
    assert ok is True, (
        "download_cv() zwróciło False — sprawdź CV_DRIVE_ID, udostępnienie pliku "
        "(np. „Każdy z linkiem”) oraz log: często zamiast PDF przychodzi strona HTML z Drive."
    )
    assert dest.is_file()
    assert dest.stat().st_size > 50
