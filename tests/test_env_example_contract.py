"""Kontrakt: .env.example zawiera wszystkie klucze z pipeline_validate.ENV_KEYS_DOCUMENTED."""

from __future__ import annotations

from pathlib import Path

from pipeline_validate import ENV_KEYS_DOCUMENTED


def _keys_from_env_example(text: str) -> set[str]:
    out: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        key = s.split("=", 1)[0].strip()
        if key:
            out.add(key)
    return out


def test_env_example_lists_all_documented_keys() -> None:
    root = Path(__file__).resolve().parents[1]
    example = root / ".env.example"
    assert example.is_file(), "Brak .env.example w katalogu projektu"

    documented = set(ENV_KEYS_DOCUMENTED)
    in_file = _keys_from_env_example(example.read_text(encoding="utf-8"))

    missing = documented - in_file
    assert not missing, f"W .env.example brakuje kluczy: {sorted(missing)}"
