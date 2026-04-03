"""
E2E: reporter — pięć arkuszy w jednym pliku jak po całym pipeline.
"""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd
import pytest

import reporter
from reporter import save_full_report


@pytest.mark.e2e
def test_save_full_report_end_to_end_workbook_structure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "e2e" / "report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", path)

    df = pd.DataFrame({"k": [1]})
    ok = save_full_report(df, df, df, df, df)

    assert ok is True
    wb = openpyxl.load_workbook(path, read_only=True)
    try:
        assert wb.sheetnames == [
            "Jobs",
            "Websites",
            "EmailsFound",
            "EmailsToSend",
            "EmailsLog",
        ]
    finally:
        wb.close()
