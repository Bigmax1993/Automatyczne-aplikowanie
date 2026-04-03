"""
E2E: cv_engine — pobranie pliku (mock HTTP) i zapis na dysku jak w produkcji.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import cv_engine
from cv_engine import download_cv


@pytest.mark.e2e
def test_download_cv_end_to_end_writes_binary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dest = tmp_path / "e2e_cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "e2e-file-id")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    pdf = b"%PDF-1.4 e2e binary content marker"

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [pdf]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is True

    assert dest.read_bytes() == pdf
