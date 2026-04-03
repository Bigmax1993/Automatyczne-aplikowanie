"""
Regresja: webdriver_apply — pusty DataFrame; brak http w URL; mailto + tekst.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import webdriver_apply
from webdriver_apply import extract_emails, run_scraper


@pytest.mark.regression
def test_run_scraper_empty_input_returns_typed_columns() -> None:
    df = pd.DataFrame(columns=["company_name", "website"])
    out = run_scraper(df)
    assert list(out.columns) == ["company_name", "website", "emails"]
    assert len(out) == 0


@pytest.mark.regression
def test_run_scraper_rejects_non_http_url_without_fetch() -> None:
    df = pd.DataFrame(
        {"company_name": ["Bad"], "website": ["ftp://x.com"]}
    )
    with patch.object(webdriver_apply, "fetch_html") as fh:
        out = run_scraper(df)

    fh.assert_not_called()
    assert out.iloc[0]["emails"] is None


@pytest.mark.regression
def test_extract_emails_mailto_and_plain_text_deduped() -> None:
    html = (
        '<a href="mailto:Same@EXAMPLE.com">x</a> '
        "contact same@example.com extra"
    )
    got = extract_emails(html)
    assert got == ["same@example.com"]
