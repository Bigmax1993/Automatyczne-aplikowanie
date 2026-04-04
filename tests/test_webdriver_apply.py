"""Testy: webdriver_apply — HTML, mailto, ekstrakcja, scraper."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

import webdriver_apply
from webdriver_apply import (
    _fetch_html_raise,
    _filter_email,
    _mailto_from_soup,
    extract_emails,
    fetch_html,
    run_scraper,
)


def test_mailto_from_soup_parses_href() -> None:
    html = '<a href="mailto:HR@Example.COM?subject=Hi">x</a>'
    assert _mailto_from_soup(html) == {"hr@example.com"}


def test_filter_email_rejects_junk_suffix() -> None:
    assert _filter_email("a@b.com") is True
    assert _filter_email("x@y.png") is False
    assert _filter_email("img@2x.png") is False


def test_extract_emails_regex_and_mailto_and_sort() -> None:
    html = 'Contact <a href="mailto:bb@co.pl">b</a> and sales@aa.org'
    assert extract_emails(html) == ["bb@co.pl", "sales@aa.org"]


def test_extract_emails_empty_input() -> None:
    assert extract_emails("") == []


def test_fetch_html_returns_empty_string_for_non_html_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "application/json"}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = "{}"

    with patch.object(webdriver_apply.requests, "get", return_value=mock_resp):
        out = _fetch_html_raise("https://example.com")

    assert out == ""


def test_fetch_html_returns_text_for_html(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_resp = MagicMock()
    mock_resp.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_resp.raise_for_status = MagicMock()
    mock_resp.text = "<html></html>"

    with patch.object(webdriver_apply.requests, "get", return_value=mock_resp):
        out = _fetch_html_raise("https://x.com")

    assert out == "<html></html>"


def test_fetch_html_wrapper_returns_none_on_request_error() -> None:
    with patch.object(
        webdriver_apply,
        "_fetch_html_raise",
        side_effect=requests.RequestException("fail"),
    ):
        assert fetch_html("https://x") is None


def test_run_scraper_empty_df() -> None:
    df = pd.DataFrame(columns=["company_name", "website"])
    out = run_scraper(df)
    assert out.empty
    assert list(out.columns) == ["company_name", "website", "emails"]


def test_run_scraper_skips_bad_url() -> None:
    df = pd.DataFrame(
        {
            "company_name": ["A", "B"],
            "website": [float("nan"), "not-a-url"],
        }
    )
    out = run_scraper(df)
    assert len(out) == 2
    assert out["emails"].isna().all()


def test_run_scraper_uses_fetch_html(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame(
        {
            "company_name": ["Co"],
            "website": ["https://co.example"],
        }
    )
    html = '<a href="mailto:hr@co.example">m</a>'

    with patch.object(webdriver_apply, "fetch_html", return_value=html):
        out = run_scraper(df)

    assert len(out) == 1
    assert out.iloc[0]["emails"] == "hr@co.example"


def test_run_scraper_none_calls_run_websites(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = pd.DataFrame(
        {"company_name": ["X"], "website": ["https://x.com"]}
    )

    monkeypatch.setattr(webdriver_apply, "run_websites", lambda: fake)

    with patch.object(webdriver_apply, "fetch_html", return_value=""):
        out = run_scraper(None)

    assert len(out) == 1
