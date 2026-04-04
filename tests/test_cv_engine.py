"""Testy: cv_engine — token, wykrywanie HTML, download_cv."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

import cv_engine
from cv_engine import (
    _confirm_token,
    _looks_like_html,
    download_cv,
)


def test_confirm_token_returns_value_from_download_warning_cookie() -> None:
    resp = MagicMock(spec=requests.Response)
    resp.cookies = MagicMock()
    resp.cookies.items.return_value = [("download_warning_xyz", "token123")]
    assert _confirm_token(resp) == "token123"


def test_confirm_token_returns_none_when_no_matching_cookie() -> None:
    resp = MagicMock(spec=requests.Response)
    resp.cookies = MagicMock()
    resp.cookies.items.return_value = [("other", "v")]
    assert _confirm_token(resp) is None


@pytest.mark.parametrize(
    "data,expected",
    [
        (b"<!DOCTYPE html><html>", True),
        (b"  <html>", True),
        (b"%PDF-1.4", False),
        (b"Hello contact@x.com", False),
    ],
)
def test_looks_like_html(data: bytes, expected: bool) -> None:
    assert _looks_like_html(data) is expected


def test_download_cv_returns_false_without_drive_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "")
    assert download_cv() is False


def test_download_cv_success_writes_pdf_bytes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "data" / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "fileid")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    chunk = b"%PDF-1.4 minimal"
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [chunk]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is True

    assert dest.read_bytes() == chunk
    mock_session.get.assert_called()


def test_download_cv_rejects_html_payload(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "id")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    html_chunk = b"<!DOCTYPE html><html></html>"
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.iter_content.return_value = [html_chunk]
    mock_resp.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is False

    assert not dest.exists()


def test_download_cv_uses_confirm_token_on_second_request(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    dest = tmp_path / "cv.pdf"
    monkeypatch.setattr(cv_engine, "CV_DRIVE_ID", "id")
    monkeypatch.setattr(cv_engine, "CV_LOCAL_PATH", dest)

    first = MagicMock()
    first.raise_for_status = MagicMock()
    first.iter_content.return_value = [b"x"]
    first.cookies.items.return_value = [("download_warning_abc", "conf")]

    second = MagicMock()
    second.raise_for_status = MagicMock()
    second.iter_content.return_value = [b"%PDF-ok"]
    second.cookies.items.return_value = []

    mock_session = MagicMock()
    mock_session.get.side_effect = [first, second]

    with patch("cv_engine.requests.Session", return_value=mock_session):
        assert download_cv() is True

    assert mock_session.get.call_count == 2
    second_call = mock_session.get.call_args_list[1]
    assert second_call.kwargs["params"].get("confirm") == "conf"
