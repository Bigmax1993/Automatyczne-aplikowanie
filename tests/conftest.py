"""Wspólne fixture'y: brak rzeczywistego sleep (retry / rate_limit), ścieżka projektu."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_configure(config: pytest.Config) -> None:
    """
    Pytest podmienia stderr/stdout przy capture.
    Bez UTF-8 loguru z polskimi znakami rzuca UnicodeEncodeError.
    """
    for stream in (sys.stdout, sys.stderr):
        if stream is None:
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, TypeError):
                pass


@pytest.fixture(autouse=True)
def _disable_real_sleep(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Przyspiesza tenacity i rate_limit w testach jednostkowych (nie dotyczy @integration)."""
    if request.node.get_closest_marker("integration"):
        return
    monkeypatch.setattr(time, "sleep", lambda *args, **kwargs: None)


@pytest.fixture(autouse=True)
def _job_auto_apply_harness(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """
    Serp limit odblokowany (poza testami Serp_limit).
    main: bez walidacji ENV i bez checkpointów na dysku.
    """
    path = str(getattr(request.node, "path", "") or "").replace("\\", "/")

    serp_limit_only = (
        "test_serp_limit.py",
        "test_regression_serp_limit.py",
        "test_integration_serp_limit.py",
        "test_e2e_serp_limit.py",
    )
    if any(name in path for name in serp_limit_only):
        return

    monkeypatch.setattr("Serp_limit.serp_quota_acquire", lambda: True)

    main_pipeline_tests = (
        "test_main.py",
        "test_integration_main.py",
        "test_e2e_pipeline.py",
        "test_regression_main.py",
    )
    if any(name in path for name in main_pipeline_tests):
        import main as main_mod

        monkeypatch.setattr(main_mod, "validate_serp_config", lambda: None)
        monkeypatch.setattr(main_mod, "validate_openai_config", lambda: None)
        monkeypatch.setattr(main_mod, "validate_smtp_and_cv_config", lambda: None)
        monkeypatch.setattr(main_mod, "_save_checkpoint", lambda *a, **k: None)
        monkeypatch.setattr(main_mod, "_load_checkpoint", lambda *a, **k: None)
        monkeypatch.setattr(main_mod, "_clear_checkpoints", lambda: None)
