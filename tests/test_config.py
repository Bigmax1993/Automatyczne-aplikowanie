"""Smoke test: config ładuje się i eksportuje oczekiwane stałe."""

from __future__ import annotations

from pathlib import Path

import config


def test_paths_are_under_base_dir() -> None:
    assert isinstance(config.BASE_DIR, Path)
    assert config.DATA_DIR.parent == config.BASE_DIR
    assert config.OUTPUT_DIR.parent == config.BASE_DIR
    assert config.REPORT_XLSX.parent == config.OUTPUT_DIR


def test_job_lists_are_non_empty_sequences() -> None:
    assert isinstance(config.JOB_QUERIES, list)
    assert isinstance(config.JOB_LOCATIONS, list)
    assert len(config.JOB_QUERIES) >= 1
    assert len(config.JOB_LOCATIONS) >= 1


def test_strip_env_secret_removes_bom_and_typographic_quotes() -> None:
    assert config._strip_env_secret("\ufeffsk-proj-abc") == "sk-proj-abc"
    assert config._strip_env_secret("\u201csk-x\u201d") == "sk-x"
    assert config._strip_env_secret("  plain  ") == "plain"
