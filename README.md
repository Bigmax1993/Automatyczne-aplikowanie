# Automatyczne aplikowanie

Pipeline: wyszukiwanie ofert (SerpApi) → strony firm → scraping e-maili → generowanie treści (OpenAI) → wysyłka (SMTP) → raport Excel.

Repozytorium GitHub: **automatyczne-aplikowanie** (katalog roboczy historycznie: `job-auto-apply`).

## Konfiguracja

1. Skopiuj `.env.example` do `.env`.
2. Uzupełnij klucze API i dane SMTP (patrz komentarze w `.env.example`).
3. **Nie commituj** pliku `.env` z prawdziwymi sekretami.

### Sekrety, kodowanie, integracje

- **Klucze API (SerpApi, OpenAI)** muszą być **wyłącznie ASCII** — prawdziwy token z panelu (np. `sk-...` / `sk-proj-...`). Polski placeholder w `.env`, **cudzysłowy typograficzne z Worda** albo **UTF-8 z BOM** potrafią zepsuć nagłówki HTTP; `config.py` obcina BOM i typowe cudzysłowy, ale **nie zamieni** złej treści na prawdziwy klucz.
- Zapisuj `.env` jako **UTF-8** (w Windows Notatniku wybierz „UTF-8”; bez BOM, jeśli edytor pozwala).
- **Szybka diagnostyka** (bez drukowania pełnych sekretów):

```bash
python scripts/verify_env.py
```

Kod wyjścia `1` oznacza m.in. nie-ASCII w kluczu Serp/OpenAI.

- W **GitHub Actions** ustaw prawdziwe wartości jako [encrypted secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions), nie wklejaj ich do repozytorium.
- **Testy integracyjne** z prawdziwym OpenAI / Serp / SMTP uruchamiaj lokalnie z `.env` i flagami `RUN_*` (patrz `tests/integration/__init__.py`); na każdej maszynie bez sekretów część testów zostanie pominięta — to zamierzone.

## Uruchomienie

```bash
pip install -r requirements.txt
python main.py
```

- **Dry-run** (bez wysyłki maili): `python main.py --dry-run` lub `PIPELINE_DRY_RUN=true`.
- **Wznowienie** po błędzie (checkpointy Parquet w `data/checkpoints/`): `python main.py --resume` lub `PIPELINE_RESUME=true`.
- Harmonogram: `python scheduler.py`

## Limity SerpApi

**Twardy limit 250** — bez wyjątków: przed każdym requestem do SerpApi wywoływane jest atomowe `serp_quota_acquire()` (plik `data/serp_usage.json` + blokada `data/serp_usage.lock.json`). Slot jest zajmowany **przed** HTTP; przy błędzie sieci **nie** ma zwrotu slotu. Powyżej 250 nie wykonasz kolejnego zapytania (również przy wielu procesach).

## Testy

```bash
pytest
pytest tests -m "not integration"
pytest tests/integration -m integration
```

Pełna sesja lokalna (wszystkie markery + typowe flagi integracji), **PowerShell**:

```powershell
cd C:\Users\svinc\projects\job-auto-apply
$env:PYTHONUTF8 = "1"
$env:RUN_SLOW_INTEGRATION = "1"
$env:RUN_SERP_INTEGRATION = "1"
$env:RUN_OPENAI_INTEGRATION = "1"
$env:RUN_DRIVE_INTEGRATION = "1"
$env:RUN_SMTP_INTEGRATION = "1"
python -m pytest tests/ -v --tb=short
```

Najpierw warto `python scripts/verify_env.py`, jeśli integracje z API mają sensownie przejść.

## OCR / `cv_finalizer`

Moduł `cv_finalizer.py` wymaga dodatkowo `requirements-ocr.txt`, Poppler i Tesseract — patrz komentarz w tym pliku.
