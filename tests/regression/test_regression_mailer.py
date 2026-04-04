"""
Regresja: mailer — brak wysyłki bez CV; pomijanie pustej treści; rozdzielanie adresów.
"""

from __future__ import annotations

import smtplib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import mailer
from mailer import _send_email, run_mail_sending


@pytest.mark.regression
def test_send_email_false_when_cv_file_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", Path("/nonexistent/cv_missing.pdf"))
    assert _send_email("a@b.c", "S", "B") is False


@pytest.mark.regression
def test_run_mail_sending_aborted_when_download_cv_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mailer, "download_cv", lambda: False)

    df = pd.DataFrame(
        {"company_name": ["X"], "emails": ["a@b.c"], "mail_text": ["Hi"]}
    )
    log = run_mail_sending(df)

    assert log.empty


@pytest.mark.regression
def test_run_mail_sending_splits_multiple_recipients(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cv = tmp_path / "c.pdf"
    cv.write_bytes(b"%PDF")

    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)
    monkeypatch.setattr(mailer, "download_cv", lambda: True)
    monkeypatch.setattr(mailer, "SMTP_USER", "u@t.com")
    monkeypatch.setattr(mailer, "SMTP_PASS", "p")

    sent: list[str] = []

    def capture_send(to: str, subj: str, body: str) -> bool:
        sent.append(to)
        return True

    monkeypatch.setattr(mailer, "_send_email", capture_send)

    df = pd.DataFrame(
        {
            "company_name": ["Co"],
            "emails": [" first@test.pl , second@test.pl "],
            "mail_text": ["Body"],
        }
    )
    log = run_mail_sending(df)

    assert sent == ["first@test.pl", "second@test.pl"]
    assert len(log) == 2


@pytest.mark.regression
def test_send_email_smtp_error_returns_false(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cv = tmp_path / "x.pdf"
    cv.write_bytes(b"data")
    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)
    monkeypatch.setattr(mailer, "SMTP_USER", "u")
    monkeypatch.setattr(mailer, "SMTP_PASS", "p")

    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = MagicMock(
        send_message=MagicMock(side_effect=smtplib.SMTPException("fail"))
    )
    smtp_cm.__exit__.return_value = None

    with patch("mailer.smtplib.SMTP", return_value=smtp_cm):
        assert _send_email("t@t.com", "S", "B") is False
