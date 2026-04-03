"""Integracja: schedule — rejestracja zadań bez uruchamiania pętli."""

from __future__ import annotations

import pytest
import schedule

import scheduler


@pytest.mark.integration
def test_register_jobs_populates_schedule() -> None:
    schedule.clear()
    try:
        scheduler.register_jobs()
        assert len(schedule.jobs) == 7
    finally:
        schedule.clear()
