"""
Zbiera pliki raportów do jednego katalogu i przygotowuje paczkę pod zip / Drive.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source-dir",
        default="output",
        help="Katalog źródłowy (np. output lub artifacts/reports)",
    )
    p.add_argument(
        "--out-dir",
        required=True,
        help="Katalog docelowy (np. dist/weekly_bundle)",
    )
    args = p.parse_args()

    src = Path(args.source_dir)
    dst = Path(args.out_dir)
    dst.mkdir(parents=True, exist_ok=True)

    if not src.is_dir():
        (dst / "README.txt").write_text(
            f"Brak katalogu źródłowego: {src.resolve()}\n", encoding="utf-8"
        )
        return

    for pattern in ("*.xlsx", "*.xls", "*.log"):
        for f in sorted(src.glob(pattern)):
            shutil.copy2(f, dst / f.name)

    if not any(dst.iterdir()):
        (dst / "README.txt").write_text(
            "Brak plików .xlsx/.xls/.log w katalogu źródłowym.\n", encoding="utf-8"
        )


if __name__ == "__main__":
    main()
