"""
E2E: cv_finalizer — OCR+GPT zamockowane, prawdziwy PDF + merge + sprzątanie match_section.pdf.
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


@pytest.mark.e2e
def test_build_final_cv_produces_merged_pdf_and_removes_temp_match(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from pypdf import PdfReader
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    monkeypatch.chdir(tmp_path)

    orig = tmp_path / "source.pdf"
    c = canvas.Canvas(str(orig), pagesize=A4)
    c.drawString(50, 800, "Original CV page")
    c.save()

    out = tmp_path / "final_e2e.pdf"
    monkeypatch.setattr(cv_finalizer, "ocr_pdf", lambda p: "ocr")
    monkeypatch.setattr(
        cv_finalizer, "generate_match_section", lambda cv, job: "Match\n- one"
    )

    cv_finalizer.build_final_cv(str(orig), "job", str(out))

    assert out.is_file()
    assert len(PdfReader(str(out)).pages) == 2
    assert not (tmp_path / "match_section.pdf").exists()
