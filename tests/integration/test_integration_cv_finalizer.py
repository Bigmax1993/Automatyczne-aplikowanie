"""
Integracja: cv_finalizer — zapis PDF dopasowania na dysk (reportlab).
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

if "pdf2image" not in sys.modules:
    sys.modules["pdf2image"] = MagicMock()
if "pytesseract" not in sys.modules:
    sys.modules["pytesseract"] = MagicMock()

import cv_finalizer


@pytest.mark.integration
def test_generate_match_pdf_writes_valid_pdf(tmp_path) -> None:
    path = tmp_path / "match_integration.pdf"
    cv_finalizer.generate_match_pdf("Key Skills Match\n- punkt testowy", str(path))

    assert path.stat().st_size > 500

    from pypdf import PdfReader

    assert len(PdfReader(str(path)).pages) >= 1
