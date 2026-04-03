"""Testy: reporter — _df, save_full_report."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

import reporter
from reporter import _df, save_full_report


def test_df_returns_empty_for_none() -> None:
    out = _df(None)
    assert isinstance(out, pd.DataFrame)
    assert out.empty


def test_df_passes_through_dataframe() -> None:
    df = pd.DataFrame({"a": [1]})
    assert _df(df) is df


def test_save_full_report_writes_excel(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    xlsx = tmp_path / "out" / "report.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    df = pd.DataFrame({"c": [1]})
    ok = save_full_report(df, df, df, df, df)

    assert ok is True
    assert xlsx.is_file()


def test_save_full_report_false_when_mkdir_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(reporter, "REPORT_XLSX", Path("z/report.xlsx"))

    def boom_mkdir(self, *a, **k):
        raise OSError("denied")

    monkeypatch.setattr(Path, "mkdir", boom_mkdir)

    ok = save_full_report(None, None, None, None, None)
    assert ok is False


def test_save_full_report_false_on_writer_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    xlsx = tmp_path / "r.xlsx"
    monkeypatch.setattr(reporter, "REPORT_XLSX", xlsx)

    with patch("reporter.pd.ExcelWriter", side_effect=OSError("write fail")):
        ok = save_full_report(pd.DataFrame(), None, None, None, None)

    assert ok is False
