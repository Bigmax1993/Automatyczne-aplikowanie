"""Integracja: reporter + pandas + openpyxl — zapis i odczyt XLSX."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import reporter
from reporter import save_full_report


@pytest.mark.integration
def test_save_full_report_roundtrip_all_sheets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    xlsx = tmp_path / "sub" / "integration_report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    df_jobs = pd.DataFrame({"job_id": ["j1"], "title": ["Dev"]})
    df_web = pd.DataFrame({"company_name": ["Acme"], "website": ["https://a.com"]})
    df_emails = pd.DataFrame(
        {"company_name": ["Acme"], "website": ["https://a.com"], "emails": ["hr@a.com"]}
    )
    df_send = pd.DataFrame(
        {"company_name": ["Acme"], "emails": ["hr@a.com"], "mail_text": ["Hi"]}
    )
    df_log = pd.DataFrame(
        {"company_name": ["Acme"], "email": ["hr@a.com"], "status": ["OK"]}
    )

    assert save_full_report(df_jobs, df_web, df_emails, df_send, df_log) is True
    assert xlsx.is_file()

    jobs_in = pd.read_excel(xlsx, sheet_name="Jobs")
    assert jobs_in.iloc[0]["job_id"] == "j1"

    emails_in = pd.read_excel(xlsx, sheet_name="EmailsFound")
    assert emails_in.iloc[0]["emails"] == "hr@a.com"
