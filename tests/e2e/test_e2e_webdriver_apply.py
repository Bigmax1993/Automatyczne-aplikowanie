"""
E2E: webdriver_apply — lista stron → HTML → wyciągnięcie e-maili (fetch zamockowany).
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import webdriver_apply
from webdriver_apply import run_scraper


@pytest.mark.e2e
def test_scraper_end_to_end_from_website_list_to_email_column() -> None:
    df_sites = pd.DataFrame(
        {
            "company_name": ["WebCo"],
            "website": ["https://webco.example"],
        }
    )

    html = (
        "<html><body>hello@webco.test and "
        '<a href="mailto:jobs@webco.test">apply</a></body></html>'
    )

    with patch.object(webdriver_apply, "fetch_html", return_value=html):
        out = run_scraper(df_sites)

    assert len(out) == 1
    emails = out.iloc[0]["emails"]
    assert isinstance(emails, str)
    assert "hello@webco.test" in emails
    assert "jobs@webco.test" in emails
