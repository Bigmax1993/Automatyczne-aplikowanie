"""
E2E: scheduler — punkt wejścia harmonogramu (bez nieskończonej pętli).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import scheduler


@pytest.mark.e2e
def test_schedule_tasks_registers_and_enters_forever_loop_stub() -> None:
    reg = MagicMock()
    forever = MagicMock()

    with patch.object(scheduler, "register_jobs", reg):
        with patch.object(scheduler, "run_forever", forever):
            scheduler.schedule_tasks()

    reg.assert_called_once()
    forever.assert_called_once()


@pytest.mark.e2e
def test_register_jobs_builds_weekly_schedule() -> None:
    import schedule

    schedule.clear()
    try:
        scheduler.register_jobs()
        assert len(schedule.jobs) == 7
    finally:
        schedule.clear()
