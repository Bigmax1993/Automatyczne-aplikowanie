"""
E2E: mailer — DataFrame wejściowy → generowanie → log wysyłki (OpenAI/SMTP zamockowane).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import mailer
from mailer import run_mail_generation, run_mail_sending


@pytest.mark.e2e
def test_mail_generation_then_sending_produces_log_dataframe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cv = tmp_path / "cv.pdf"
    cv.write_bytes(b"%PDF e2e")

    monkeypatch.setattr(mailer, "CV_LOCAL_PATH", cv)

    df_in = pd.DataFrame(
        {"company_name": ["MailCo"], "emails": ["a@mailco.test,b@mailco.test"]}
    )

    with patch.object(mailer, "generate_email", return_value="Szczegóły aplikacji E2E."):
        df_gen = run_mail_generation(df_in)

    assert len(df_gen) == 1
    assert "mail_text" in df_gen.columns

    with patch.object(mailer, "download_cv", return_value=True):
        with patch.object(mailer, "_send_email", return_value=True):
            log = run_mail_sending(df_gen)

    assert len(log) == 2
    assert set(log["email"].tolist()) == {"a@mailco.test", "b@mailco.test"}
    assert (log["status"] == "OK").all()
