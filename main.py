"""
main.py
Główny orchestrator pipeline'u.
Łączy wszystkie moduły i generuje jeden raport Excel.

CLI: ``python main.py [--dry-run] [--resume]``
Zmienne: ``PIPELINE_DRY_RUN``, ``PIPELINE_RESUME``, ``CLEAR_CHECKPOINT_ON_SUCCESS``
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from loguru import logger

from config import CHECKPOINT_DIR, CLEAR_CHECKPOINT_ON_SUCCESS, PIPELINE_DRY_RUN, PIPELINE_RESUME
from mailer import run_mail_generation, run_mail_sending
from pipeline_validate import (
    PipelineConfigError,
    validate_openai_config,
    validate_serp_config,
    validate_smtp_and_cv_config,
)
from reporter import save_full_report
from serp_client import run_jobs, run_websites
from webdriver_apply import run_scraper


def _checkpoint_path(name: str) -> Path:
    return CHECKPOINT_DIR / f"{name}.parquet"


def _save_checkpoint(name: str, df: pd.DataFrame) -> None:
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(_checkpoint_path(name), index=False)


def _load_checkpoint(name: str) -> pd.DataFrame | None:
    p = _checkpoint_path(name)
    if not p.exists():
        return None
    return pd.read_parquet(p)


def _clear_checkpoints() -> None:
    for p in CHECKPOINT_DIR.glob("*.parquet"):
        try:
            p.unlink()
        except OSError:
            pass


def run_full_pipeline(*, dry_run: bool | None = None, resume: bool | None = None) -> None:
    dry = PIPELINE_DRY_RUN if dry_run is None else dry_run
    res = PIPELINE_RESUME if resume is None else resume

    logger.info("=== START: PEŁNY PIPELINE ===")
    if dry:
        logger.info("Tryb dry-run: generacja treści maili bez wysyłki SMTP.")

    validate_serp_config()

    logger.info("Krok 1/6: oferty pracy")
    if res:
        loaded = _load_checkpoint("jobs")
        if loaded is not None:
            df_jobs = loaded
            logger.info("Resume: wczytano checkpoint jobs")
        else:
            df_jobs = run_jobs()
            _save_checkpoint("jobs", df_jobs)
    else:
        df_jobs = run_jobs()
        _save_checkpoint("jobs", df_jobs)

    logger.info("Krok 2/6: strony firm")
    if res:
        loaded = _load_checkpoint("websites")
        if loaded is not None:
            df_websites = loaded
            logger.info("Resume: wczytano checkpoint websites")
        else:
            df_websites = run_websites(df_jobs)
            _save_checkpoint("websites", df_websites)
    else:
        df_websites = run_websites(df_jobs)
        _save_checkpoint("websites", df_websites)

    logger.info("Krok 3/6: scraping e-maili")
    if res:
        loaded = _load_checkpoint("emails")
        if loaded is not None:
            df_emails = loaded
            logger.info("Resume: wczytano checkpoint emails")
        else:
            df_emails = run_scraper(df_websites)
            _save_checkpoint("emails", df_emails)
    else:
        df_emails = run_scraper(df_websites)
        _save_checkpoint("emails", df_emails)

    if df_emails.empty:
        logger.warning("Brak rekordów e-mail — pomijam generowanie i wysyłkę.")
        df_to_send = pd.DataFrame(
            columns=["company_name", "emails", "mail_text"]
        )
        df_log = pd.DataFrame(columns=["company_name", "email", "status"])
    else:
        validate_openai_config()

        logger.info("Krok 4/6: generowanie treści maili")
        if res:
            loaded = _load_checkpoint("to_send")
            if loaded is not None:
                df_to_send = loaded
                logger.info("Resume: wczytano checkpoint to_send")
            else:
                df_to_send = run_mail_generation(df_emails)
                _save_checkpoint("to_send", df_to_send)
        else:
            df_to_send = run_mail_generation(df_emails)
            _save_checkpoint("to_send", df_to_send)

        if dry:
            logger.warning("Dry-run: pomijam krok wysyłki (SMTP).")
            df_log = pd.DataFrame(columns=["company_name", "email", "status"])
        else:
            validate_smtp_and_cv_config()
            logger.info("Krok 5/6: wysyłka maili")
            df_log = run_mail_sending(df_to_send)

    logger.info("Krok 6/6: zapis raportu Excel")
    report_ok = save_full_report(
        df_jobs=df_jobs,
        df_websites=df_websites,
        df_emails=df_emails,
        df_to_send=df_to_send,
        df_log=df_log,
    )

    if CLEAR_CHECKPOINT_ON_SUCCESS:
        if report_ok:
            _clear_checkpoints()
        else:
            logger.warning(
                "Zapis raportu Excel nie powiódł się — checkpointy pozostają (możesz --resume)."
            )

    logger.info("=== KONIEC: PEŁNY PIPELINE ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline job-auto-apply")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Wygeneruj treści maili i raport, bez wysyłki SMTP",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Wznów z plików Parquet w data/checkpoints/",
    )
    args = parser.parse_args()

    try:
        run_full_pipeline(
            dry_run=args.dry_run if args.dry_run else None,
            resume=args.resume if args.resume else None,
        )
    except PipelineConfigError as e:
        logger.error(str(e))
        sys.exit(2)
    except Exception:
        logger.exception("Pipeline zakończony błędem")
        sys.exit(1)
