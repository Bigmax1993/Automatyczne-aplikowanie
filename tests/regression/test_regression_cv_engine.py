"""
Regresja: cv_engine — brak CV_DRIVE_ID; odrzucenie odpowiedzi HTML zamiast PDF.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import cv_engine
from cv_engine import download_cv


@pytest.mark.regression
def test_download_cv_false_when_drive_id_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "")
    assert download_cv() is False


@pytest.mark.regression
def test_download_cv_deletes_file_when_payload_is_html(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "id")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [b"<!DOCTYPE html><html></html>"]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is False

    assert not dest.exists()
