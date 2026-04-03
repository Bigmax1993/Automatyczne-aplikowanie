"""
Regresja: scheduler — run_serpapi_only przekazuje wynik run_jobs do run_websites.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import scheduler


@pytest.mark.regression
def test_run_serpapi_only_passes_jobs_dataframe_to_run_websites() -> None:
    df = pd.DataFrame({"company_name": ["SchedCo"]})

    with patch.object(scheduler, "run_jobs", return_value=df) as rj:
        with patch.object(scheduler, "run_websites") as rw:
            scheduler.run_serpapi_only()

    rj.assert_called_once()
    rw.assert_called_once_with(df)


@pytest.mark.regression
def test_register_jobs_registers_seven_entries() -> None:
    import schedule

    schedule.clear()
    try:
        scheduler.register_jobs()
        assert len(schedule.jobs) == 7
    finally:
        schedule.clear()
