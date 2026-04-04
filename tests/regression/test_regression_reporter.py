"""
Regresja: reporter — None → pusty DataFrame; spójne nazwy arkuszy (EmailsLog).
"""

from __future__ import annotations

from pathlib import Path

import openpyxl
import pandas as pd
import pytest

import reporter
from reporter import _df, save_full_report


@pytest.mark.regression
def test_df_coerces_none_to_empty_dataframe() -> None:
    out = _df(None)
    assert isinstance(out, pd.DataFrame)
    assert out.empty


@pytest.mark.regression
def test_excel_workbook_has_expected_sheet_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xlsx = tmp_path / "regression_report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    df = pd.DataFrame({"col": [1]})
    assert save_full_report(df, df, df, df, df) is True

    wb = openpyxl.load_workbook(xlsx, read_only=True)
    try:
        names = wb.sheetnames
        assert names == [
            "Jobs",
            "Websites",
            "EmailsFound",
            "EmailsToSend",
            "EmailsLog",
        ]
    finally:
        wb.close()
