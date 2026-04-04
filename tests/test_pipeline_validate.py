"""Testy: pipeline_validate — komunikaty przy braku ENV."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import pipeline_validate
from pipeline_validate import (
    PipelineConfigError,
    validate_openai_config,
    validate_serp_config,
    validate_smtp_and_cv_config,
)


def test_validate_serp_raises_without_key() -> None:
    with patch.object(pipeline_validate, "SERPAPI_API_KEY", ""):
        with pytest.raises(PipelineConfigError, match="SERPAPI_API_KEY"):
            validate_serp_config()


def test_validate_serp_raises_on_non_ascii_key() -> None:
    with patch.object(pipeline_validate, "SERPAPI_API_KEY", "klucz_z_\u00f3"):
        with pytest.raises(PipelineConfigError, match="ASCII"):
            validate_serp_config()


def test_validate_openai_raises_without_key() -> None:
    with patch.object(pipeline_validate, "OPENAI_API_KEY", None):
        with pytest.raises(PipelineConfigError, match="OPENAI_API_KEY"):
            validate_openai_config()


def test_validate_openai_raises_on_non_ascii_key() -> None:
    with patch.object(pipeline_validate, "OPENAI_API_KEY", "tw\u00f3j_klucz"):
        with pytest.raises(PipelineConfigError, match="ASCII"):
            validate_openai_config()


def test_validate_smtp_raises_without_credentials() -> None:
    with (
        patch.object(pipeline_validate, "SMTP_USER", ""),
        patch.object(pipeline_validate, "SMTP_PASS", ""),
        patch.object(pipeline_validate, "CV_DRIVE_ID", "x"),
    ):
        with pytest.raises(PipelineConfigError, match="SMTP"):
            validate_smtp_and_cv_config()
