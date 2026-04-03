"""
E2E: rate_limit — dekoratory ``api_safe`` na rzeczywistym wywołaniu ``_fetch_jobs`` (mock HTTP).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import serp_client


@pytest.mark.e2e
def test_fetch_jobs_through_api_safe_stack_returns_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(serp_client, "SERPAPI_API_KEY", "e2e-key")

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"jobs_results": []}

    with patch.object(serp_client.requests, "get", return_value=mock_resp):
        data = serp_client._fetch_jobs("q", "loc")

    assert data is not None
    assert "jobs_results" in data
