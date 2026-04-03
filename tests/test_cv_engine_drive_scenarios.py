"""
Scenariusze ``cv_engine.download_cv`` odpowiadające integracji Drive (bez sieci).

Uzupełnia ``test_cv_engine.py`` o błędy HTTP, pustą odpowiedź i błąd zapisu.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

import cv_engine
from cv_engine import download_cv


def test_download_cv_returns_false_on_http_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "realistic_drive_id_min_length_ok")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    mock_session = MagicMock()
    mock_session.get.side_effect = requests.HTTPError("404")

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is False


def test_download_cv_returns_false_on_empty_stream(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "realistic_drive_id_min_length_ok")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = []
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is False


def test_download_cv_returns_false_on_os_error_writing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "realistic_drive_id_min_length_ok")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [b"%PDF"]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        with patch("builtins.open", side_effect=OSError("permission")):
            assert download_cv() is False


def test_download_cv_success_large_file_like_integration_min_size(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Jak integracja: plik > 50 B po pobraniu (tu sztuczny chunk, bez Google)."""
    dest = tmp_path / "downloaded_cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "realistic_drive_id_min_length_ok")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    payload = b"%PDF-1.4" + b"x" * 100
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [payload]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is True

    assert dest.is_file()
    assert dest.stat().st_size > 50
