"""
Regresja: main — przekazywanie df_jobs → run_websites, df_websites → run_scraper.
"""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

import main


@pytest.mark.regression
def test_pipeline_wires_dataframes_between_steps() -> None:
    df_jobs = pd.DataFrame({"company_name": ["J1"], "job_id": ["1"]})
    df_web = pd.DataFrame({"company_name": ["J1"], "website": ["https://j1.com"]})
    df_emails = pd.DataFrame(
        {"company_name": ["J1"], "website": ["https://j1.com"], "emails": ["e@j1.com"]}
    )

    captured: dict[str, object] = {}

    def rw(df):
        captured["websites_arg"] = df
        return df_web

    def rs(df):
        captured["scraper_arg"] = df
        return df_emails

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", side_effect=rw):
            with patch.object(main, "run_scraper", side_effect=rs):
                with patch.object(main, "run_mail_generation", return_value=pd.DataFrame()):
                    with patch.object(main, "run_mail_sending", return_value=pd.DataFrame()):
                        with patch.object(main, "save_full_report"):
                            main.run_full_pipeline()

    assert captured["websites_arg"] is df_jobs
    assert captured["scraper_arg"] is df_web
