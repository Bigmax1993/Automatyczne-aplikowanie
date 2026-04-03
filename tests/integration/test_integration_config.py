"""Integracja: config — ładowanie projektu i katalogów wyjściowych."""

from __future__ import annotations

import pytest

import config


@pytest.mark.integration
def test_config_directories_exist() -> None:
    assert config.DATA_DIR.is_dir()
    assert config.OUTPUT_DIR.is_dir()


@pytest.mark.integration
def test_config_job_lists_populated() -> None:
    assert all(isinstance(s, str) and s.strip() for s in config.JOB_QUERIES)
    assert all(isinstance(s, str) and s.strip() for s in config.JOB_LOCATIONS)
