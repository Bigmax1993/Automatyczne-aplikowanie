"""
E2E: serp_client — oferty → strony firm (mock SerpApi), bez pojedynczych testów _fetch_*.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import serp_client


def _fake_get(url: str, params=None, timeout=None, **kwargs):
    p = params or {}
    m = MagicMock()
    m.raise_for_status = MagicMock()
    if p.get("engine") == "google_jobs":
        m.json.return_value = {
            "jobs_results": [
                {
                    "job_id": "1",
                    "title": "T",
                    "company_name": "ChainCo",
                    "location": "L",
                    "via": "v",
                    "job_google_link": "https://j",
                }
            ]
        }
        return m
    if p.get("engine") == "google":
        m.json.return_value = {
            "organic_results": [{"link": "https://chainco.example"}]
        }
        return m
    raise AssertionError(p)


@pytest.mark.e2e
def test_run_jobs_then_run_websites_produces_linked_dataframes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(serp_client, "JOB_QUERIES", ["one"])
    monkeypatch.setattr(serp_client, "JOB_LOCATIONS", ["loc"])

    with patch.object(serp_client.requests, "get", side_effect=_fake_get):
        df_jobs = serp_client.run_jobs()
        df_web = serp_client.run_websites(df_jobs)

    assert len(df_jobs) == 1
    assert df_jobs.iloc[0]["company_name"] == "ChainCo"
    assert len(df_web) == 1
    assert df_web.iloc[0]["website"] == "https://chainco.example"
