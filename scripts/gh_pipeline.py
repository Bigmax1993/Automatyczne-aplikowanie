"""
Entry point for GitHub Actions (workflow_dispatch / schedule).

Modes: SerpApi-only (raport Excel), pełny pipeline (main), wysyłka raportu e-mail.
"""

from __future__ import annotations

import argparse
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pandas as pd
from loguru import logger

from reporter import save_full_report
from serp_client import run_jobs, run_websites


def _run_serpapi_and_save_report() -> None:
    logger.info("=== GH: tryb serpapi (oferty + strony firm) ===")
    df_jobs = run_jobs()
    df_websites = run_websites(df_jobs)
    save_full_report(
        df_jobs=df_jobs,
        df_websites=df_websites,
        df_emails=pd.DataFrame(),
        df_to_send=pd.DataFrame(),
        df_log=pd.DataFrame(),
    )


def _run_full() -> None:
    logger.info("=== GH: pełny pipeline (main) ===")
    from main import run_full_pipeline

    run_full_pipeline()


def _run_email_report() -> None:
    logger.info("=== GH: wysyłka raportu Excel na e-mail ===")
    from scripts.send_report_email import send_latest_report

    send_latest_report()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="GitHub Actions pipeline runner")
    p.add_argument(
        "mode",
        choices=("serpapi", "full", "weekly_email_report"),
        help="serpapi | full | weekly_email_report",
    )
    args = p.parse_args(argv)

    if args.mode == "serpapi":
        _run_serpapi_and_save_report()
    elif args.mode == "full":
        _run_full()
    else:
        _run_email_report()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
