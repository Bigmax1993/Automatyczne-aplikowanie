"""
Regresja: serp_client — brak podwójnego pobierania ofert przy przekazanym df_jobs.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

import serp_client


@pytest.mark.regression
def test_run_websites_with_df_does_not_invoke_run_jobs() -> None:
    df = pd.DataFrame({"company_name": ["Acme"]})

    with patch.object(serp_client, "run_jobs") as mock_run_jobs:
        with patch.object(serp_client, "_fetch_website", return_value="https://acme.test"):
            serp_client.run_websites(df)

    mock_run_jobs.assert_not_called()


@pytest.mark.regression
def test_run_websites_none_still_fetches_jobs_once() -> None:
    df = pd.DataFrame({"company_name": ["Solo"]})

    with patch.object(serp_client, "run_jobs", return_value=df) as mock_run_jobs:
        with patch.object(serp_client, "_fetch_website", return_value="https://solo.test"):
            out = serp_client.run_websites(None)

    mock_run_jobs.assert_called_once()
    assert len(out) == 1


@pytest.mark.regression
def test_fetch_website_query_includes_official_website_phrase() -> None:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"organic_results": [{"link": "https://x"}]}
    mock_resp.raise_for_status = MagicMock()

    with patch.object(serp_client.requests, "get", return_value=mock_resp) as get:
        serp_client._fetch_website("MyBrand")

    params = get.call_args.kwargs["params"]
    assert "official website" in params["q"]
    assert "MyBrand" in params["q"]
