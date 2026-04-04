"""Testy: scheduler — SerpApi job, pełny pipeline, rejestracja harmonogramu."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import schedule

import scheduler


@pytest.fixture(autouse=True)
def clear_schedule() -> None:
    schedule.clear()
    yield
    schedule.clear()


def test_run_serpapi_only_calls_jobs_then_websites() -> None:
    df = pd.DataFrame({"company_name": ["A"]})
    with patch.object(scheduler, "run_jobs", return_value=df) as rj:
        with patch.object(scheduler, "run_websites") as rw:
            scheduler.run_serpapi_only()

    rj.assert_called_once()
    rw.assert_called_once_with(df)


def test_run_serpapi_only_swallows_inner_exception() -> None:
    with patch.object(scheduler, "run_jobs", side_effect=RuntimeError("boom")):
        scheduler.run_serpapi_only()


def test_run_full_pipeline_job_calls_main_run_full_pipeline() -> None:
    mock_run = MagicMock()
    with patch("main.run_full_pipeline", mock_run):
        scheduler.run_full_pipeline_job()
    mock_run.assert_called_once()


def test_register_jobs_registers_sunday_and_weekdays() -> None:
    scheduler.register_jobs()
    assert len(schedule.jobs) == 7


def test_schedule_tasks_wires_register_and_forever(monkeypatch: pytest.MonkeyPatch) -> None:
    reg = MagicMock()
    forever = MagicMock()
    monkeypatch.setattr(scheduler, "register_jobs", reg)
    monkeypatch.setattr(scheduler, "run_forever", forever)
    scheduler.schedule_tasks()
    reg.assert_called_once()
    forever.assert_called_once()
