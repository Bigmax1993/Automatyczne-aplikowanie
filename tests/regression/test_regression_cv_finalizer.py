"""
Regresja: cv_finalizer — kontrakt promptu dopasowania (bez wywołania API).
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

if "pdf2image" not in sys.modules:
    sys.modules["pdf2image"] = MagicMock()
if "pytesseract" not in sys.modules:
    sys.modules["pytesseract"] = MagicMock()

import cv_finalizer


@pytest.mark.regression
def test_generate_match_section_prompt_requires_key_skills_block() -> None:
    with patch.object(cv_finalizer, "gpt_call", return_value="ok") as gc:
        cv_finalizer.generate_match_section("cvbody", "jobbody")

    prompt = gc.call_args.kwargs["messages"][0]["content"]
    assert "Key Skills Match" in prompt
    assert "NIE przepisuj" in prompt
    assert "cvbody" in prompt and "jobbody" in prompt
