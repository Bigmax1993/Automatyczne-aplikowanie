"""
serp_client.py
Pobieranie ofert pracy (Google Jobs) i stron firm (Google Search) z SerpApi.
Zwraca DataFrame'y: df_jobs, df_websites.
"""

import pandas as pd
import requests
from loguru import logger

import Serp_limit as serp_quota
from config import JOB_LOCATIONS, JOB_QUERIES, SERPAPI_API_KEY
from rate_limit import api_safe

BASE_URL = "https://serpapi.com/search"


# ---------------------------------------------------------
# 1. Pobieranie ofert pracy z Google Jobs
# ---------------------------------------------------------
@api_safe(1.2)
def _fetch_jobs(query: str, location: str) -> dict | None:
    if not serp_quota.serp_quota_acquire():
        return None

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            logger.warning(
                f"SerpApi 429 (jobs) '{query}' @ '{location}' — ponawiam przez mechanizm retry..."
            )
            raise
        logger.error(f"Błąd HTTP SerpApi (jobs) dla '{query}' @ '{location}': {e}")
        return None
    except requests.RequestException as e:
        logger.error(f"Błąd SerpApi (jobs) dla '{query}' @ '{location}': {e}")
        return None


def run_jobs() -> pd.DataFrame:
    """
    Pobiera oferty pracy dla wszystkich zapytań i lokalizacji.
    Zwraca DataFrame z kolumnami:
    - job_id
    - title
    - company_name
    - location
    - via
    - job_google_link
    - query
    - location_query
    """
    logger.info("=== SERP: Pobieram oferty pracy ===")

    rows = []

    for query in JOB_QUERIES:
        for location in JOB_LOCATIONS:
            logger.info(f"SERP: Jobs → '{query}' @ '{location}'")

            data = _fetch_jobs(query, location)
            if not data or "jobs_results" not in data:
                logger.warning(f"Brak wyników dla '{query}' @ '{location}'")
                continue

            for job in data["jobs_results"]:
                rows.append({
                    "job_id": job.get("job_id"),
                    "title": job.get("title"),
                    "company_name": job.get("company_name"),
                    "location": job.get("location"),
                    "via": job.get("via"),
                    "job_google_link": job.get("job_google_link"),
                    "query": query,
                    "location_query": location,
                })

    df = pd.DataFrame(rows)
    logger.info(f"SERP: Zebrano {len(df)} ofert pracy.")
    return df


# ---------------------------------------------------------
# 2. Pobieranie stron firm z Google Search
# ---------------------------------------------------------
@api_safe(1.2)
def _fetch_website(company: str) -> str | None:
    if not serp_quota.serp_quota_acquire():
        return None

    params = {
        "engine": "google",
        "q": f"{company} official website",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        organic = data.get("organic_results", [])
        if organic:
            return organic[0].get("link")

        return None

    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 429:
            logger.warning(
                f"SerpApi 429 (websites) dla firmy '{company}' — ponawiam przez retry..."
            )
            raise
        logger.error(f"Błąd HTTP SerpApi (websites) dla firmy '{company}': {e}")
        return None
    except requests.RequestException as e:
        logger.error(f"Błąd SerpApi (websites) dla firmy '{company}': {e}")
        return None


def run_websites(df_jobs: pd.DataFrame | None = None) -> pd.DataFrame:
    """
    Pobiera strony firm na podstawie unikalnych nazw firm z ofert pracy.

    df_jobs:
        Jeśli None — wywołuje run_jobs() (drugie wywołanie w pipeline = podwójny koszt Serp).
        Jeśli podasz DataFrame z run_jobs(), użyje go bez ponownego pobierania.

    Zwraca DataFrame:
    - company_name
    - website
    """
    logger.info("=== SERP: Pobieram strony firm ===")

    if df_jobs is None:
        df_jobs = run_jobs()

    if df_jobs.empty or "company_name" not in df_jobs.columns:
        logger.warning("SERP: Brak firm do wyszukania stron.")
        return pd.DataFrame(columns=["company_name", "website"])

    companies = (
        df_jobs["company_name"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .tolist()
    )

    logger.info(f"SERP: Unikalnych firm: {len(companies)}")

    rows = []
    for company in companies:
        logger.info(f"SERP: Szukam strony firmy → {company}")
        website = _fetch_website(company)
        rows.append({"company_name": company, "website": website})

    df = pd.DataFrame(rows)
    logger.info(f"SERP: Zebrano {len(df)} stron firm.")
    return df
