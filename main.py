"""
main.py
Główny orchestrator pipeline'u.
Łączy wszystkie moduły i generuje jeden raport Excel.
"""

import sys

import pandas as pd
from loguru import logger

from config import PIPELINE_DRY_RUN
from serp_client import run_jobs, run_websites
from webdriver_apply import run_scraper
from mailer import run_mail_generation, run_mail_sending
from reporter import save_full_report


def run_full_pipeline() -> None:
    logger.info("=== START: PEŁNY PIPELINE ===")

    logger.info("Krok 1/6: oferty pracy")
    df_jobs = run_jobs()

    logger.info("Krok 2/6: strony firm")
    df_websites = run_websites(df_jobs)

    logger.info("Krok 3/6: scraping e-maili")
    df_emails = run_scraper(df_websites)

    if df_emails.empty:
        logger.warning("Brak rekordów e-mail — pomijam generowanie i wysyłkę.")
        df_to_send = pd.DataFrame(
            columns=["company_name", "emails", "mail_text"]
        )
        df_log = pd.DataFrame(columns=["company_name", "email", "status"])
    else:
        logger.info("Krok 4/6: generowanie treści maili")
        df_to_send = run_mail_generation(df_emails)

        logger.info("Krok 5/6: wysyłka maili")
        if PIPELINE_DRY_RUN:
            logger.info("PIPELINE_DRY_RUN=1 — pomijam rzeczywistą wysyłkę SMTP.")
            df_log = pd.DataFrame(columns=["company_name", "email", "status"])
        else:
            df_log = run_mail_sending(df_to_send)

    logger.info("Krok 6/6: zapis raportu Excel")
    save_full_report(
        df_jobs=df_jobs,
        df_websites=df_websites,
        df_emails=df_emails,
        df_to_send=df_to_send,
        df_log=df_log,
    )

    logger.info("=== KONIEC: PEŁNY PIPELINE ===")


if __name__ == "__main__":
    try:
        run_full_pipeline()
    except Exception:
        logger.exception("Pipeline zakończony błędem")
        sys.exit(1)