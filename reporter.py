"""
reporter.py
Tworzenie jednego pliku Excel z wieloma arkuszami.
"""

from pathlib import Path

import pandas as pd
from loguru import logger

from config import REPORT_XLSX


def _df(x: pd.DataFrame | None) -> pd.DataFrame:
    return x if isinstance(x, pd.DataFrame) else pd.DataFrame()


def save_full_report(
    df_jobs: pd.DataFrame | None,
    df_websites: pd.DataFrame | None,
    df_emails: pd.DataFrame | None,
    df_to_send: pd.DataFrame | None,
    df_log: pd.DataFrame | None,
) -> bool:
    """
    Zapisuje wszystkie DataFrame'y do jednego pliku Excel.
    Każdy DataFrame trafia do osobnego arkusza.
    Zwraca True, gdy zapis się powiódł.
    """
    logger.info("=== START: Generowanie raportu Excel ===")

    path = Path(REPORT_XLSX)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logger.error(f"Nie można utworzyć katalogu na raport: {e}")
        logger.info("=== KONIEC: Generowanie raportu Excel ===")
        return False

    sheets = [
        (_df(df_jobs), "Jobs"),
        (_df(df_websites), "Websites"),
        (_df(df_emails), "EmailsFound"),
        (_df(df_to_send), "EmailsToSend"),
        (_df(df_log), "EmailsLog"),
    ]

    try:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for df, name in sheets:
                # Excel: max 31 znaków w nazwie arkusza
                safe_name = name[:31]
                df.to_excel(writer, sheet_name=safe_name, index=False)

        logger.info(f"Raport zapisany → {path.resolve()}")
        logger.info("=== KONIEC: Generowanie raportu Excel ===")
        return True

    except OSError as e:
        logger.error(f"Błąd zapisu pliku raportu: {e}")
    except ImportError as e:
        logger.error(f"Brak zależności do Excela (openpyxl?): {e}")
    except Exception as e:
        logger.error(f"Błąd podczas generowania raportu: {e}")

    logger.info("=== KONIEC: Generowanie raportu Excel ===")
    return False
