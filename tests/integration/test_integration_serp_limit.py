"""Integracja: Serp_limit — plik + lock + limit."""

from __future__ import annotations

import pytest

import Serp_limit as serp_limit_mod


@pytest.fixture
def usage_file(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "serp_usage.json"
    lock = tmp_path / "serp_usage.lock.json"
    monkeypatch.setattr(serp_limit_mod, "USAGE_FILE", path)
    monkeypatch.setattr(serp_limit_mod, "LOCK_FILE", lock)
    return path


@pytest.mark.integration
def test_acquire_until_hard_limit(usage_file, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(serp_limit_mod, "HARD_LIMIT", 3)

    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 2

    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 3

    assert serp_limit_mod.serp_quota_acquire() is False
    assert serp_limit_mod.serp_quota_get_count() == 3
