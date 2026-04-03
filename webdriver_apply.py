"""
webdriver_apply.py
Lekki scraper stron firm — pobiera e‑maile z HTML.
Zwraca DataFrame: company_name, website, emails
"""

import re
from urllib.parse import unquote

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import RetryError

from rate_limit import rate_limit, simple_retry
from serp_client import run_websites

EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

_JUNK_SUFFIX = re.compile(
    r"\.(png|jpe?g|gif|webp|svg|ico|css|js|woff2?|ttf|eot|pdf|zip)(\s|$)",
    re.IGNORECASE,
)


# ---------------------------------------------------------
# 1. Pobieranie HTML z retry
# ---------------------------------------------------------
@simple_retry()
def _fetch_html_raise(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    ctype = (response.headers.get("Content-Type") or "").lower()
    if "text/html" not in ctype and "application/xhtml" not in ctype:
        logger.warning(f"Pomijam nie-HTML ({ctype}) → {url}")
        return ""
    return response.text


@rate_limit(0.4)
def fetch_html(url: str) -> str | None:
    """
    Pobiera HTML strony (z retry i limitem częstotliwości).
    Zwraca tekst HTML, pusty string jeśli typ nie jest HTML, None po wyczerpaniu prób.
    """
    try:
        return _fetch_html_raise(url)
    except RetryError as e:
        cause = e.last_attempt.exception() if e.last_attempt else e
        logger.error(f"Błąd pobierania HTML ({url}) po ponowieniach: {cause}")
        return None
    except requests.RequestException as e:
        logger.error(f"Błąd pobierania HTML ({url}): {e}")
        return None


# ---------------------------------------------------------
# 2. Ekstrakcja e‑maili z HTML
# ---------------------------------------------------------
def _mailto_from_soup(html: str) -> set[str]:
    out: set[str] = set()
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.select('a[href^="mailto:"]'):
        href = a.get("href") or ""
        raw = href[7:].split("?", 1)[0]
        raw = unquote(raw).strip()
        if not raw:
            continue
        m = EMAIL_REGEX.search(raw)
        if m:
            out.add(m.group(0).lower())
    return out


def _filter_email(addr: str) -> bool:
    a = addr.lower()
    if _JUNK_SUFFIX.search(a):
        return False
    if a.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return False
    return True


def extract_emails(html: str) -> list[str]:
    """Wyciąga e‑maile z HTML (regex + linki mailto:)."""
    if not html:
        return []

    found = set(m.group(0).lower() for m in EMAIL_REGEX.finditer(html))
    found |= _mailto_from_soup(html)
    found = {e for e in found if _filter_email(e)}
    return sorted(found)


# ---------------------------------------------------------
# 3. Główna funkcja scraper'a
# ---------------------------------------------------------
def run_scraper(df_websites: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Scraper stron firm.

    df_websites:
        Opcjonalnie wynik run_websites(df_jobs). Jeśli None — wywołuje run_websites().

    Zwraca DataFrame:
    - company_name
    - website
    - emails
    """
    logger.info("=== SCRAPER: Start ===")

    if df_websites is None:
        df_websites = run_websites()

    if df_websites.empty:
        logger.warning("SCRAPER: Pusta lista stron — brak pracy.")
        return pd.DataFrame(columns=["company_name", "website", "emails"])

    rows = []

    for _, row in df_websites.iterrows():
        company = row.get("company_name")
        url = row.get("website")

        if pd.isna(url) or not isinstance(url, str) or not url.strip():
            logger.warning(f"SCRAPER: Brak URL dla firmy: {company}")
            rows.append({"company_name": company, "website": url, "emails": None})
            continue

        url = url.strip()
        if not url.lower().startswith(("http://", "https://")):
            logger.warning(f"SCRAPER: Nieprawidłowy URL dla {company}: {url}")
            rows.append({"company_name": company, "website": url, "emails": None})
            continue

        logger.info(f"SCRAPER: Pobieram e‑maile → {company} ({url})")

        html = fetch_html(url)
        emails = extract_emails(html or "")

        rows.append({
            "company_name": company,
            "website": url,
            "emails": ", ".join(emails) if emails else None,
        })

    df = pd.DataFrame(rows)

    logger.info(f"SCRAPER: Zakończono. Firm: {len(df)}")
    logger.info("=== SCRAPER: Koniec ===")

    return df
