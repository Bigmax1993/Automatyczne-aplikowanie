"""
Scenariusze OpenAI / SMTP w ``mailer`` odpowiadające pomijanym integracjom (bez API).

Pełna ścieżka ``generate_email`` + ``run_mail_generation`` jak przy live, ale z mockami.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

import mailer
from mailer import generate_email, run_mail_generation


@pytest.fixture(autouse=True)
def _reset_openai_singleton() -> None:
    mailer._client = None
    yield
    mailer._client = None


def test_generate_email_live_like_openai_returns_long_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Odpowiednik ``test_generate_email_live_openai`` — mock zamiast sieci."""
    body = (
        "Szanowni Państwo, TestCompany Integration — "
        "piszę w sprawie aplikacji na stanowisko programisty."
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=body))]
    )
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "sk-test-mock")
    monkeypatch.setattr(mailer, "OpenAI", MagicMock(return_value=mock_client))

    text = generate_email("TestCompany Integration")
    assert text
    assert len(text) > 20
    assert "TestCompany" in text or "testcompany" in text.lower()
    mock_client.chat.completions.create.assert_called_once()


def test_run_mail_generation_live_like_one_row_over_30_chars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Odpowiednik ``test_run_mail_generation_live_one_row`` — mock zamiast sieci."""
    long_body = "A" * 80
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=long_body))]
    )
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "sk-test-mock")
    monkeypatch.setattr(mailer, "OpenAI", MagicMock(return_value=mock_client))

    df = pd.DataFrame(
        {"company_name": ["IntegrationCo"], "emails": ["void@example.com"]}
    )
    out = run_mail_generation(df)
    assert len(out) == 1
    mt = out.iloc[0]["mail_text"]
    assert isinstance(mt, str) and len(mt) > 30


def test_get_openai_client_missing_key_raises_like_before_api_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(mailer, "OPENAI_API_KEY", "")
    mailer._client = None
    with pytest.raises(ValueError, match="missing or empty"):
        mailer._get_openai_client()
