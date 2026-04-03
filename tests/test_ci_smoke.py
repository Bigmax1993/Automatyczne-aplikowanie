"""
Smoke pod CI: importy punktów wejścia, CLI, brak błędów kolekcji.
Uruchamiane w każdym ``pytest`` (nie wymagają integracji / sieci).
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _stub_ocr_modules() -> None:
    from unittest.mock import MagicMock

    for name in ("pdf2image", "pytesseract"):
        if name not in sys.modules:
            m = MagicMock()
            if name == "pdf2image":
                m.convert_from_path = MagicMock(return_value=[])
            if name == "pytesseract":
                m.image_to_string = MagicMock(return_value="")
            sys.modules[name] = m


def test_import_core_modules() -> None:
    """Wszystkie moduły aplikacji muszą się importować na czystym venv (jak w GA)."""
    importlib.import_module("config")
    importlib.import_module("pipeline_validate")
    importlib.import_module("Serp_limit")
    importlib.import_module("rate_limit")
    importlib.import_module("serp_client")
    importlib.import_module("webdriver_apply")
    importlib.import_module("cv_engine")
    importlib.import_module("reporter")
    importlib.import_module("mailer")
    importlib.import_module("scheduler")
    importlib.import_module("main")

    _stub_ocr_modules()
    importlib.import_module("cv_finalizer")


def test_main_help_exits_zero() -> None:
    r = subprocess.run(
        [sys.executable, str(ROOT / "main.py"), "--help"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stderr
    assert "--dry-run" in r.stdout
    assert "--resume" in r.stdout


def test_scheduler_module_import_no_side_effect_loop() -> None:
    """Scheduler importuje się bez uruchamiania pętli (tylko przy __main__)."""
    import scheduler

    assert callable(scheduler.register_jobs)
    assert callable(scheduler.run_full_pipeline_job)
