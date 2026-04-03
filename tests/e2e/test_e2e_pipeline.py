"""
E2E: main — pełny pipeline (Serp → strony → scraper → maile → raport Excel).

Obejmuje pośrednio: config, rate_limit (na wywołaniach Serp), wszystkie kroki main.
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import mailer
import main
import reporter
import serp_client
import webdriver_apply


def _serp_response(params: dict) -> MagicMock:
    m = MagicMock()
    m.raise_for_status = MagicMock()
    engine = (params or {}).get("engine")
    if engine == "google_jobs":
        m.json.return_value = {
            "jobs_results": [
                {
                    "job_id": "e2e-job",
                    "title": "Engineer",
                    "company_name": "E2ECorp",
                    "location": "Poland",
                    "via": "E2E",
                    "job_google_link": "https://jobs.example/e2e",
                }
            ]
        }
        return m
    if engine == "google":
        m.json.return_value = {
            "organic_results": [{"link": "https://e2ecorp.example"}]
        }
        return m
    raise AssertionError(f"nieobsługiwany engine: {params}")


def _fake_serp_get(url: str, params=None, timeout=None, **kwargs):
    return _serp_response(params or {})


def _html_for_fetch(url: str) -> str:
    return (
        "<!DOCTYPE html><html><body>"
        '<a href="mailto:hr@e2ecorp.test">HR</a>'
        "</body></html>"
    )


def _e2e_patches(stack: ExitStack) -> None:
    stack.enter_context(patch.object(serp_client.requests, "get", side_effect=_fake_serp_get))
    stack.enter_context(patch.object(webdriver_apply, "fetch_html", side_effect=_html_for_fetch))
    stack.enter_context(
        patch.object(mailer, "generate_email", return_value="Treść aplikacji E2E.")
    )
    stack.enter_context(patch.object(mailer, "download_cv", return_value=True))
    stack.enter_context(patch.object(mailer, "_send_email", return_value=True))


@pytest.mark.e2e
def test_full_pipeline_produces_excel_with_expected_sheets_and_rows(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tmp_path / "e2e_full_report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", report)
    monkeypatch.setattr(serp_client, "JOB_QUERIES", ["e2e-query"])
    monkeypatch.setattr(serp_client, "JOB_LOCATIONS", ["E2E-Location"])

    with ExitStack() as stack:
        _e2e_patches(stack)
        main.run_full_pipeline()

    assert report.is_file()

    xl = pd.ExcelFile(report)
    assert set(xl.sheet_names) == {
        "Jobs",
        "Websites",
        "EmailsFound",
        "EmailsToSend",
        "EmailsLog",
    }

    jobs = pd.read_excel(report, sheet_name="Jobs")
    assert len(jobs) == 1
    assert jobs.iloc[0]["company_name"] == "E2ECorp"
    assert jobs.iloc[0]["job_id"] == "e2e-job"

    sites = pd.read_excel(report, sheet_name="Websites")
    assert len(sites) == 1
    assert sites.iloc[0]["company_name"] == "E2ECorp"
    assert sites.iloc[0]["website"] == "https://e2ecorp.example"

    found = pd.read_excel(report, sheet_name="EmailsFound")
    assert "hr@e2ecorp.test" in str(found.iloc[0]["emails"])

    to_send = pd.read_excel(report, sheet_name="EmailsToSend")
    assert to_send.iloc[0]["mail_text"] == "Treść aplikacji E2E."

    log = pd.read_excel(report, sheet_name="EmailsLog")
    assert len(log) == 1
    assert log.iloc[0]["status"] == "OK"
    assert log.iloc[0]["email"] == "hr@e2ecorp.test"


@pytest.mark.e2e
def test_full_pipeline_dry_run_skips_smtp_but_writes_generation_and_report(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = tmp_path / "e2e_dry_report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", report)
    monkeypatch.setattr(serp_client, "JOB_QUERIES", ["e2e-query"])
    monkeypatch.setattr(serp_client, "JOB_LOCATIONS", ["E2E-Location"])

    mock_smtp_send = MagicMock()

    with ExitStack() as stack:
        _e2e_patches(stack)
        stack.enter_context(patch.object(main, "run_mail_sending", mock_smtp_send))
        main.run_full_pipeline(dry_run=True)

    mock_smtp_send.assert_not_called()
    assert report.is_file()

    to_send = pd.read_excel(report, sheet_name="EmailsToSend")
    assert to_send.iloc[0]["mail_text"] == "Treść aplikacji E2E."

    log = pd.read_excel(report, sheet_name="EmailsLog")
    assert log.empty
