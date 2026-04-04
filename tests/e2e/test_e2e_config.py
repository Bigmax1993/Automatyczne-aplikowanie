"""
E2E: config — załadowanie środowiska projektu (ścieżki, stałe zadań).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import config


@pytest.mark.e2e
def test_config_paths_exist_and_queries_configured() -> None:
    assert config.BASE_DIR.is_dir()
    assert config.DATA_DIR.is_dir()
    assert config.OUTPUT_DIR.is_dir()
    assert isinstance(config.REPORT_XLSX, Path)
    assert len(config.JOB_QUERIES) >= 1
    assert len(config.JOB_LOCATIONS) >= 1
