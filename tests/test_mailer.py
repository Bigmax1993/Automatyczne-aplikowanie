"""Testy: mailer — OpenAI, generowanie, wysyłka SMTP, run_*."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import mailer
from mailer import (
    _get_openai_client,
    _send_email,
    generate_email,
    run_mail_generation,
    run_mail_sending,
)


@pytest.fixture(autouse=True)
def reset_openai_singleton() -> None:
    mailer._client = None
    yield
    mailer._client = None


def test_get_openai_client_creates_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_cls = MagicMock()
    mock_cls.return_value = MagicMock(name="client")
    monkeypatch.setattr(mailer, "OpenAI", mock_cls)
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "sk-test")

    a = _get_openai_client()
    b = _get_openai_client()
    assert a is b
    mock_cls.assert_called_once_with(api_key="sk-test")


def test_get_openai_client_rejects_non_ascii_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "sk-b\u0142\u0105d")
    with pytest.raises(ValueError, match="ASCII-only"):
        _get_openai_client()


def test_generate_email_non_ascii_key_returns_none_and_logs_actionable_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Pełna ścieżka jak przy złym .env: API nie startuje, asercja ``assert text`` w integracji
    daje mało sygnału — tu sprawdzamy None + log z komunikatem o ASCII (jak Bearer + ó).
    """
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "Bearer_tw\xf3j_klucz")
    mailer._client = None
    with patch.object(mailer.logger, "error") as mock_err:
        assert generate_email("TestCompany Integration") is None
    mock_err.assert_called()
    logged = repr(mock_err.call_args)
    assert "ASCII-only" in logged or "OPENAI_API_KEY" in logged


def test_generate_email_success(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="  Witam  "))]
    )
    monkeypatch.setattr(mailer, "_get_openai_client", lambda: mock_client)

    text = generate_email("Acme")
    assert text == "Witam"
    mock_client.chat.completions.create.assert_called_once()


def test_generate_email_empty_content_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="   "))]
    )
    monkeypatch.setattr(mailer, "_get_openai_client", lambda: mock_client)

    assert generate_email("Co") is None


def test_generate_email_api_error_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("api down")
    monkeypatch.setattr(mailer, "_get_openai_client", lambda: mock_client)

    assert generate_email("Co") is None


def test_run_mail_generation_skips_rows_without_emails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mailer, "generate_email", lambda c: f"body-{c}")

    df = pd.DataFrame(
        {
            "company_name": ["A", "B"],
            "emails": ["a@x.pl", float("nan")],
        }
    )
    out = run_mail_generation(df)
    assert len(out) == 1
    assert out.iloc[0]["company_name"] == "A"


def test_send_email_success(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    cv = tmp_path / "cv.pdf"
    cv.write_bytes(b"%PDF")

    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)
    monkeypatch.setattr(mailer, "SMTP_USER", "u@test.com")
    monkeypatch.setattr(mailer, "SMTP_PASS", "p")

    server = MagicMock()
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = server
    smtp_cm.__exit__.return_value = None

    with patch("mailer.smtplib.SMTP", return_value=smtp_cm):
        assert _send_email("to@test.com", "Sub", "Body") is True

    server.starttls.assert_called_once()
    server.login.assert_called_once_with("u@test.com", "p")
    server.send_message.assert_called_once()


def test_send_email_empty_cv_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    cv = tmp_path / "empty.pdf"
    cv.write_bytes(b"")
    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)

    assert _send_email("t@t.com", "S", "B") is False


def test_send_email_missing_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", "/nonexistent/cv.pdf")

    assert _send_email("t@t.com", "S", "B") is False


def test_send_email_smtp_failure(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    cv = tmp_path / "c.pdf"
    cv.write_bytes(b"x")
    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)
    monkeypatch.setattr(mailer, "SMTP_USER", "u")
    monkeypatch.setattr(mailer, "SMTP_PASS", "p")

    server = MagicMock()
    server.send_message.side_effect = smtplib.SMTPException("fail")
    smtp_cm = MagicMock()
    smtp_cm.__enter__.return_value = server
    smtp_cm.__exit__.return_value = None

    with patch("mailer.smtplib.SMTP", return_value=smtp_cm):
        assert _send_email("t@t.com", "S", "B") is False


def test_run_mail_sending_stops_when_download_cv_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mailer, "download_cv", lambda: False)

    df = pd.DataFrame(
        {"company_name": ["A"], "emails": ["a@b.c"], "mail_text": ["Hi"]}
    )
    log = run_mail_sending(df)

    assert log.empty
    assert list(log.columns) == ["company_name", "email", "status"]


def test_run_mail_sending_splits_emails_and_logs_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mailer, "download_cv", lambda: True)
    monkeypatch.setattr(mailer, "_send_email", lambda *a, **k: True)

    df = pd.DataFrame(
        {
            "company_name": ["Co"],
            "emails": [" a@x.pl , b@y.pl "],
            "mail_text": ["Hello"],
        }
    )
    log = run_mail_sending(df)
    assert len(log) == 2
    assert log["status"].tolist() == ["OK", "OK"]


def test_run_mail_sending_skips_empty_body(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mailer, "download_cv", lambda: True)

    df = pd.DataFrame(
        {
            "company_name": ["Co"],
            "emails": ["a@b.c"],
            "mail_text": [""],
        }
    )
    log = run_mail_sending(df)
    assert log.empty
