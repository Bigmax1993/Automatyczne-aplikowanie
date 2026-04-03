"""Integracja: mailer — OpenAI / SMTP tylko przy jawnej zgodzie (ENV)."""

from __future__ import annotations

import os

import pandas as pd
import pytest

import config
import mailer
from mailer import generate_email, run_mail_generation
from tests.integration.helpers import env_truthy, openai_key_ok_for_live_api


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_OPENAI_INTEGRATION")
    or not (config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"))
    or not openai_key_ok_for_live_api(),
    reason=(
        "OpenAI live: RUN_OPENAI_INTEGRATION=1 + OPENAI_API_KEY tylko ASCII (sk-...). "
        "Sprawdź: python scripts/verify_env.py"
    ),
)
def test_generate_email_live_openai() -> None:
    mailer._client = None
    text = generate_email("TestCompany Integration")
    assert text
    assert len(text) > 20
    assert "TestCompany" in text or "testcompany" in text.lower()


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_OPENAI_INTEGRATION")
    or not (config.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY"))
    or not openai_key_ok_for_live_api(),
    reason=(
        "OpenAI live: RUN_OPENAI_INTEGRATION=1 + OPENAI_API_KEY tylko ASCII (sk-...). "
        "Sprawdź: python scripts/verify_env.py"
    ),
)
def test_run_mail_generation_live_one_row() -> None:
    mailer._client = None
    df = pd.DataFrame(
        {"company_name": ["IntegrationCo"], "emails": ["void@example.com"]}
    )
    out = run_mail_generation(df)
    assert len(out) == 1
    mt = out.iloc[0]["mail_text"]
    assert isinstance(mt, str) and len(mt) > 30


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_SMTP_INTEGRATION")
    or not (config.SMTP_USER and config.SMTP_PASS)
    or not os.getenv("INTEGRATION_SMTP_TO"),
    reason="Ustaw RUN_SMTP_INTEGRATION=1, SMTP_* w .env oraz INTEGRATION_SMTP_TO=test@...",
)
def test_send_single_mail_live(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    import smtplib
    from email.message import EmailMessage

    cv = tmp_path / "cv.pdf"
    cv.write_bytes(b"%PDF-1.4 integration test")

    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)

    to_addr = os.environ["INTEGRATION_SMTP_TO"]
    msg = EmailMessage()
    msg["From"] = config.SMTP_USER
    msg["To"] = to_addr
    msg["Subject"] = "[integration] job-auto-apply"
    msg.set_content("Test integracyjny — możesz usunąć.")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_OPENAI_INTEGRATION"),
    reason="Ustaw RUN_OPENAI_INTEGRATION=1, aby uruchomić diagnostykę klucza.",
)
@pytest.mark.skipif(
    openai_key_ok_for_live_api(),
    reason=(
        "Klucz z .env jest poprawny (ASCII). "
        "Test tylko do jawnej reprodukcji złej konfiguracji."
    ),
)
def test_diagnose_openai_key_rejects_invalid_env_before_live_calls() -> None:
    """
    Integracja włączona, klucz zły: ValueError o OPENAI_API_KEY zamiast ``assert None``.
    """
    mailer._client = None
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        mailer._get_openai_client()
