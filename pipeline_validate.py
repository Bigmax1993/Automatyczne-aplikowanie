"""
Walidacja konfiguracji przed krokami pipeline'u (czytelne błędy zamiast późnych wyjątków).
"""

from __future__ import annotations

from config import (
    CV_DRIVE_ID,
    OPENAI_API_KEY,
    SERPAPI_API_KEY,
    SMTP_PASS,
    SMTP_USER,
)

# Klucze opisane w .env.example — test kontraktu używa tej listy
ENV_KEYS_DOCUMENTED = (
    "SERPAPI_API_KEY",
    "OPENAI_API_KEY",
    "SMTP_USER",
    "SMTP_PASS",
    "CV_DRIVE_ID",
    "LOG_LEVEL",
    "PIPELINE_DRY_RUN",
    "PIPELINE_RESUME",
    "CLEAR_CHECKPOINT_ON_SUCCESS",
)


class PipelineConfigError(RuntimeError):
    """Brak wymaganej zmiennej środowiskowej lub niespójna konfiguracja."""


def _require_ascii_api_key(env_name: str, key: str | None) -> None:
    """Klucze w URL/query HTTP muszą być ASCII — placeholdery z ogonkami psują klienta."""
    if key is None or not str(key).strip():
        return
    if not str(key).isascii():
        raise PipelineConfigError(
            f"{env_name} musi zawierać wyłącznie znaki ASCII (nagłówki / parametry HTTP). "
            "Zastąp polski placeholder w .env prawdziwym kluczem API."
        )


def validate_serp_config() -> None:
    if not SERPAPI_API_KEY or not str(SERPAPI_API_KEY).strip():
        raise PipelineConfigError(
            "Brak SERPAPI_API_KEY — ustaw w pliku .env (patrz .env.example)."
        )
    _require_ascii_api_key("SERPAPI_API_KEY", SERPAPI_API_KEY)


def validate_openai_config() -> None:
    if not OPENAI_API_KEY or not str(OPENAI_API_KEY).strip():
        raise PipelineConfigError(
            "Brak OPENAI_API_KEY — potrzebny do generowania treści maili (.env.example)."
        )
    _require_ascii_api_key("OPENAI_API_KEY", OPENAI_API_KEY)


def validate_smtp_and_cv_config() -> None:
    missing: list[str] = []
    if not SMTP_USER or not str(SMTP_USER).strip():
        missing.append("SMTP_USER")
    if not SMTP_PASS or not str(SMTP_PASS).strip():
        missing.append("SMTP_PASS")
    if not CV_DRIVE_ID or not str(CV_DRIVE_ID).strip():
        missing.append("CV_DRIVE_ID")
    if missing:
        raise PipelineConfigError(
            "Brak konfiguracji wysyłki / CV: " + ", ".join(missing) + " — patrz .env.example"
        )
