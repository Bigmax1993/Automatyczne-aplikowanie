"""Integracja: serp_client — prawdziwe zapytanie SerpApi (opcjonalnie, płatne)."""

from __future__ import annotations

import os

import pandas as pd
import pytest

import serp_client
from tests.integration.helpers import env_truthy


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_SERP_INTEGRATION") or not os.getenv("SERPAPI_API_KEY"),
    reason="Ustaw RUN_SERP_INTEGRATION=1 i SERPAPI_API_KEY (płatne API).",
)
def test_run_jobs_live_returns_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(serp_client, "JOB_QUERIES", ["Python developer"])
    monkeypatch.setattr(serp_client, "JOB_LOCATIONS", ["Warsaw, Poland"])

    df = serp_client.run_jobs()

    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "company_name" in df.columns
        assert "job_id" in df.columns


@pytest.mark.integration
@pytest.mark.skipif(
    not env_truthy("RUN_SERP_INTEGRATION") or not os.getenv("SERPAPI_API_KEY"),
    reason="Ustaw RUN_SERP_INTEGRATION=1 i SERPAPI_API_KEY (płatne API).",
)
def test_run_websites_live_from_sample_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    df_jobs = pd.DataFrame({"company_name": ["Google", "Microsoft"]})
    df = serp_client.run_websites(df_jobs)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "website" in df.columns
