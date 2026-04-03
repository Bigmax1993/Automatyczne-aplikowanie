"""
Testy jednostkowe: cv_finalizer (OCR/GPT/PDF zamockowane lub lekkie zależności).
Import modułu wymaga podmiany pdf2image/pytesseract zanim załaduje się cv_finalizer.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# cv_finalizer importuje pdf2image / pytesseract — na CI bez Popplera używamy atrap
if "pdf2image" not in sys.modules:
    _m = MagicMock()
    _m.convert_from_path = MagicMock(return_value=[])
    sys.modules["pdf2image"] = _m
if "pytesseract" not in sys.modules:
    _t = MagicMock()
    _t.image_to_string = MagicMock(return_value="cv text line")
    sys.modules["pytesseract"] = _t

import cv_finalizer


@pytest.fixture(autouse=True)
def restore_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cv_finalizer.time, "sleep", lambda *a, **k: None)


def test_ocr_pdf_returns_empty_when_convert_returns_no_pages() -> None:
    cv_finalizer.convert_from_path = MagicMock(return_value=[])
    assert cv_finalizer.ocr_pdf("/fake.pdf") == ""


def test_ocr_pdf_success_concatenates_pages() -> None:
    page = MagicMock()
    cv_finalizer.convert_from_path = MagicMock(return_value=[page, page])
    cv_finalizer.pytesseract.image_to_string = MagicMock(side_effect=["A B", "C D"])

    out = cv_finalizer.ocr_pdf("/x.pdf")
    assert "A B" in out and "C D" in out


def test_gpt_call_returns_message_content() -> None:
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="  OK  "))]

    with patch.object(cv_finalizer.client.chat.completions, "create", return_value=mock_resp):
        assert cv_finalizer.gpt_call([{"role": "user", "content": "hi"}]) == "  OK  "


def test_generate_match_section_delegates_to_gpt_call() -> None:
    with patch.object(cv_finalizer, "gpt_call", return_value="bullets") as gc:
        out = cv_finalizer.generate_match_section("cv", "job")

    assert out == "bullets"
    assert "cv" in gc.call_args.kwargs["messages"][0]["content"]
    assert "job" in gc.call_args.kwargs["messages"][0]["content"]


def test_generate_match_pdf_creates_file(tmp_path) -> None:
    out = tmp_path / "match.pdf"
    cv_finalizer.generate_match_pdf("Line one\nLine two", str(out))
    assert out.is_file() and out.stat().st_size > 0


def test_merge_pdfs_combines_page_counts(tmp_path) -> None:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from pypdf import PdfReader

    a = tmp_path / "a.pdf"
    b = tmp_path / "b.pdf"
    c = tmp_path / "out.pdf"

    for path in (a, b):
        can = canvas.Canvas(str(path), pagesize=A4)
        can.drawString(100, 800, "x")
        can.save()

    cv_finalizer.merge_pdfs(str(a), str(b), str(c))

    r = PdfReader(str(c))
    assert len(r.pages) == 2


def test_build_final_cv_end_to_end_with_stubbed_ocr_and_gpt(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from pypdf import PdfReader

    monkeypatch.chdir(tmp_path)

    orig = tmp_path / "in.pdf"
    can = canvas.Canvas(str(orig), pagesize=A4)
    can.drawString(100, 800, "CV")
    can.save()

    out = tmp_path / "final.pdf"
    monkeypatch.setattr(cv_finalizer, "ocr_pdf", lambda p: "dummy cv text")
    monkeypatch.setattr(
        cv_finalizer, "generate_match_section", lambda c, j: "Key Skills\n- punkt"
    )

    cv_finalizer.build_final_cv(str(orig), "opis stanowiska", str(out))

    assert out.is_file()
    assert len(PdfReader(str(out)).pages) == 2
    assert not (tmp_path / "match_section.pdf").exists()
