"""
scheduler.py
Harmonogram automatycznego uruchamiania pipeline'u:
- Niedziela 21:00 → tylko SerpApi (run_jobs + run_websites)
- Poniedziałek–Sobota 06:00 → pełny pipeline

Uwaga: biblioteka `schedule` używa czasu lokalnego systemu (strefa z OS).
"""

import signal
import time

import schedule
from loguru import logger

from serp_client import run_jobs, run_websites


def run_serpapi_only() -> None:
    """
    Uruchamia tylko część SerpApi:
    - run_jobs()
    - run_websites()
    """
    logger.info("=== SCHEDULER: TYLKO SerpApi (niedziela 21:00) ===")

    try:
        df_jobs = run_jobs()
        run_websites(df_jobs)
        logger.info(
            "SCHEDULER: wyniki SerpApi tylko w pamięci; "
            "raport Excel powstaje w main.run_full_pipeline()."
        )
        logger.info("=== SCHEDULER: SerpApi zakończone ===")
    except Exception:
        logger.exception("SCHEDULER: błąd SerpApi")


def run_full_pipeline_job() -> None:
    """Pełny pipeline — import dopiero tu, żeby ograniczyć importy cykliczne."""
    from main import run_full_pipeline

    logger.info("=== SCHEDULER: Pełny pipeline (Pn–Sb 06:00) ===")
    try:
        run_full_pipeline()
        logger.info("=== SCHEDULER: Pełny pipeline zakończony ===")
    except Exception:
        logger.exception("SCHEDULER: błąd pełnego pipeline'u")


def register_jobs() -> None:
    """
    Rejestruje zadania (bez uruchamiania pętli).
    """
    logger.info("=== SCHEDULER: Rejestruję harmonogram ===")

    schedule.every().sunday.at("21:00").do(run_serpapi_only)

    for day in (
        schedule.every().monday,
        schedule.every().tuesday,
        schedule.every().wednesday,
        schedule.every().thursday,
        schedule.every().friday,
        schedule.every().saturday,
    ):
        day.at("06:00").do(run_full_pipeline_job)

    logger.info("=== SCHEDULER: Harmonogram zarejestrowany ===")


def run_forever(poll_seconds: float = 1.0) -> None:
    """
    Pętla scheduler'a. Kończy się po SIGINT/SIGTERM lub KeyboardInterrupt.
    """
    stop = {"flag": False}

    def _stop(*_args: object) -> None:
        stop["flag"] = True
        logger.info("=== SCHEDULER: Sygnał zatrzymania — kończę pętlę ===")

    try:
        signal.signal(signal.SIGINT, _stop)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _stop)
    except ValueError:
        # np. wątek inny niż główny — ignoruj
        pass

    logger.info("=== SCHEDULER: Start pętli (Ctrl+C = stop) ===")
    while not stop["flag"]:
        schedule.run_pending()
        time.sleep(poll_seconds)


def schedule_tasks() -> None:
    """Rejestruje zadania i wchodzi w nieskończoną pętlę (jak dotychczas)."""
    register_jobs()
    run_forever()


if __name__ == "__main__":
    schedule_tasks()
