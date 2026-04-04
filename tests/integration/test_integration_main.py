"""Integracja: main — pełny przebieg orchestratora z I/O zastąpionym stubami + prawdziwy Excel."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import main
import reporter


@pytest.mark.integration
def test_run_full_pipeline_stubs_write_excel(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    xlsx = tmp_path / "pipeline_integration.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    df_jobs = pd.DataFrame(
        {
            "job_id": ["1"],
            "title": ["Dev"],
            "company_name": ["Co"],
            "location": ["PL"],
            "via": ["x"],
            "job_google_link": ["https://j"],
            "query": ["q"],
            "location_query": ["loc"],
        }
    )
    df_web = pd.DataFrame({"company_name": ["Co"], "website": ["https://co.example"]})
    df_emails = pd.DataFrame(
        {
            "company_name": ["Co"],
            "website": ["https://co.example"],
            "emails": ["hr@co.example"],
        }
    )
    df_send = pd.DataFrame(
        {
            "company_name": ["Co"],
            "emails": ["hr@co.example"],
            "mail_text": ["Treść testowa."],
        }
    )
    df_log = pd.DataFrame(
        {"company_name": ["Co"], "email": ["hr@co.example"], "status": ["OK"]}
    )

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                with patch.object(main, "run_mail_generation", return_value=df_send):
                    with patch.object(main, "run_mail_sending", return_value=df_log):
                        main.run_full_pipeline()

    assert xlsx.is_file()
    back = pd.read_excel(xlsx, sheet_name="Jobs")
    assert back.iloc[0]["company_name"] == "Co"


@pytest.mark.integration
def test_run_full_pipeline_empty_emails_still_writes_report(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xlsx = tmp_path / "empty_emails.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    df_jobs = pd.DataFrame({"company_name": []})
    df_web = pd.DataFrame()
    df_emails = pd.DataFrame()

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                main.run_full_pipeline()

    assert xlsx.is_file()
    log_sheet = pd.read_excel(xlsx, sheet_name="EmailsLog")
    assert log_sheet.empty
