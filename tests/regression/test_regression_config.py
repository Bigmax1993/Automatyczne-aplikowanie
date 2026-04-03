"""
Regresja: config — stałe JOB_* i ścieżki projektu spójne z BASE_DIR.
"""

from __future__ import annotations

import pytest

import config


@pytest.mark.regression
def test_job_queries_and_locations_non_empty_strings() -> None:
    assert len(config.JOB_QUERIES) >= 1
    assert len(config.JOB_LOCATIONS) >= 1
    assert all(isinstance(q, str) and q.strip() for q in config.JOB_QUERIES)
    assert all(isinstance(loc, str) and loc.strip() for loc in config.JOB_LOCATIONS)


@pytest.mark.regression
def test_data_and_output_under_base_dir() -> None:
    assert config.DATA_DIR.is_relative_to(config.BASE_DIR)
    assert config.OUTPUT_DIR.is_relative_to(config.BASE_DIR)
    assert config.REPORT_XLSX.is_relative_to(config.OUTPUT_DIR)
