"""Testy: main — orchestracja pipeline (wszystko zamockowane)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

import main


def test_run_full_pipeline_with_emails_runs_all_steps() -> None:
    df_jobs = pd.DataFrame({"j": [1]})
    df_web = pd.DataFrame({"w": [1]})
    df_emails = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "website": ["https://x"]}
    )
    df_send = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "mail_text": ["Hi"]}
    )
    df_log = pd.DataFrame({"company_name": ["C"], "email": ["a@b.c"], "status": ["OK"]})

    mock_save = MagicMock(return_value=True)

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                with patch.object(main, "run_mail_generation", return_value=df_send):
                    with patch.object(main, "run_mail_sending", return_value=df_log):
                        with patch.object(main, "save_full_report", mock_save):
                            main.run_full_pipeline()

    mock_save.assert_called_once()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["df_jobs"] is df_jobs
    assert kwargs["df_websites"] is df_web
    assert kwargs["df_emails"] is df_emails
    assert kwargs["df_to_send"] is df_send
    assert kwargs["df_log"] is df_log


def test_run_full_pipeline_skips_mail_when_no_emails() -> None:
    df_jobs = pd.DataFrame()
    df_web = pd.DataFrame()
    df_emails = pd.DataFrame()

    mock_save = MagicMock(return_value=True)
    mock_gen = MagicMock()
    mock_send = MagicMock()

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                with patch.object(main, "run_mail_generation", mock_gen):
                    with patch.object(main, "run_mail_sending", mock_send):
                        with patch.object(main, "save_full_report", mock_save):
                            main.run_full_pipeline()

    mock_gen.assert_not_called()
    mock_send.assert_not_called()
    kwargs = mock_save.call_args.kwargs
    assert kwargs["df_to_send"].empty
    assert kwargs["df_log"].empty


def test_run_full_pipeline_clears_checkpoints_only_when_report_saved() -> None:
    df_jobs = pd.DataFrame({"j": [1]})
    df_web = pd.DataFrame({"w": [1]})
    df_emails = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "website": ["https://x"]}
    )
    df_send = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "mail_text": ["Hi"]}
    )
    df_log = pd.DataFrame({"company_name": ["C"], "email": ["a@b.c"], "status": ["OK"]})

    mock_clear = MagicMock()

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                with patch.object(main, "run_mail_generation", return_value=df_send):
                    with patch.object(main, "run_mail_sending", return_value=df_log):
                        with patch.object(main, "save_full_report", return_value=False):
                            with patch.object(main, "_clear_checkpoints", mock_clear):
                                with patch.object(main, "CLEAR_CHECKPOINT_ON_SUCCESS", True):
                                    main.run_full_pipeline()

    mock_clear.assert_not_called()


def test_run_full_pipeline_clears_checkpoints_when_report_ok() -> None:
    df_jobs = pd.DataFrame({"j": [1]})
    df_web = pd.DataFrame({"w": [1]})
    df_emails = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "website": ["https://x"]}
    )
    df_send = pd.DataFrame(
        {"company_name": ["C"], "emails": ["a@b.c"], "mail_text": ["Hi"]}
    )
    df_log = pd.DataFrame({"company_name": ["C"], "email": ["a@b.c"], "status": ["OK"]})

    mock_clear = MagicMock()

    with patch.object(main, "run_jobs", return_value=df_jobs):
        with patch.object(main, "run_websites", return_value=df_web):
            with patch.object(main, "run_scraper", return_value=df_emails):
                with patch.object(main, "run_mail_generation", return_value=df_send):
                    with patch.object(main, "run_mail_sending", return_value=df_log):
                        with patch.object(main, "save_full_report", return_value=True):
                            with patch.object(main, "_clear_checkpoints", mock_clear):
                                with patch.object(main, "CLEAR_CHECKPOINT_ON_SUCCESS", True):
                                    main.run_full_pipeline()

    mock_clear.assert_called_once()
