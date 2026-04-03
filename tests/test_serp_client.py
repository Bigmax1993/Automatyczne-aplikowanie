"""Testy: serp_client — fetch jobs/websites, run_jobs, run_websites."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import serp_client


@pytest.fixture
def one_query_one_location(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(serp_client, "JOB_QUERIES", ["Python"])
    monkeypatch.setattr(serp_client, "JOB_LOCATIONS", ["Warsaw"])


def test_fetch_jobs_success_returns_json(one_query_one_location: None) -> None:
    payload = {
        "jobs_results": [
            {
                "job_id": "1",
                "title": "Dev",
                "company_name": "Acme",
                "location": "Warsaw",
                "via": "LinkedIn",
                "job_google_link": "https://example.com",
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp) as get:
        out = serp_client._fetch_jobs("Python", "Warsaw")

    assert out == payload
    get.assert_called_once()
    assert get.call_args.kwargs["params"]["engine"] == "google_jobs"


def test_fetch_jobs_returns_none_when_serp_quota_blocks(
    one_query_one_location: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("Serp_limit.serp_quota_acquire", lambda: False)

    with patch.object(serp_client.requests, "get") as get:
        assert serp_client._fetch_jobs("q", "loc") is None
    get.assert_not_called()


def test_fetch_jobs_calls_serp_quota_acquire_before_http(
    one_query_one_location: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    acquire = MagicMock(return_value=True)

    monkeypatch.setattr("Serp_limit.serp_quota_acquire", acquire)

    payload = {"jobs_results": []}
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp):
        serp_client._fetch_jobs("q", "loc")

    acquire.assert_called_once()


def test_fetch_jobs_request_error_returns_none(one_query_one_location: None) -> None:
    import requests as req_lib

    with patch.object(
        serp_client.requests,
        "get",
        side_effect=req_lib.RequestException("network"),
    ):
        assert serp_client._fetch_jobs("q", "loc") is None


def test_run_jobs_builds_dataframe(one_query_one_location: None) -> None:
    payload = {
        "jobs_results": [
            {
                "job_id": "j1",
                "title": "T",
                "company_name": "Co",
                "location": "L",
                "via": "V",
                "job_google_link": "https://x",
            }
        ]
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp):
        df = serp_client.run_jobs()

    assert len(df) == 1
    assert df.iloc[0]["company_name"] == "Co"
    assert df.iloc[0]["query"] == "Python"
    assert df.iloc[0]["location_query"] == "Warsaw"


def test_fetch_website_returns_first_organic_link() -> None:
    payload = {"organic_results": [{"link": "https://acme.com"}]}
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp):
        link = serp_client._fetch_website("Acme Corp")

    assert link == "https://acme.com"


def test_fetch_website_empty_organic_returns_none() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp):
        assert serp_client._fetch_website("X") is None


def test_run_websites_empty_jobs_returns_columns_only() -> None:
    df = pd.DataFrame(columns=["company_name"])
    out = serp_client.run_websites(df)
    assert list(out.columns) == ["company_name", "website"]
    assert len(out) == 0


def test_run_websites_deduplicates_and_calls_fetch() -> None:
    df_jobs = pd.DataFrame(
        {
            "company_name": ["Acme", "Acme", "Beta", None, ""],
        }
    )

    def fake_fetch(company: str) -> str:
        return f"https://{company.lower()}.test"

    with patch.object(serp_client, "_fetch_website", side_effect=fake_fetch):
        out = serp_client.run_websites(df_jobs)

    assert len(out) == 2
    names = set(out["company_name"].tolist())
    assert names == {"Acme", "Beta"}


def test_run_websites_none_triggers_run_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_jobs = pd.DataFrame({"company_name": ["Only"]})

    def fake_run_jobs() -> pd.DataFrame:
        return fake_jobs

    monkeypatch.setattr(serp_client, "run_jobs", fake_run_jobs)

    with patch.object(serp_client, "_fetch_website", return_value="https://u"):
        out = serp_client.run_websites(None)

    assert len(out) == 1
    assert out.iloc[0]["website"] == "https://u"
