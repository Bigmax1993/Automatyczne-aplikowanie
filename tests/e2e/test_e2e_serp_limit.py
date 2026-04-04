"""E2E: Serp_limit — pełny cykl acquire do kresu limitu."""

from __future__ import annotations

import pytest

import Serp_limit as serp_limit_mod


@pytest.mark.e2e
def test_quota_lifecycle(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "e2e_serp.json"
    lock = tmp_path / "e2e_serp.lock.json"
    monkeypatch.setattr(serp_limit_mod, "USAGE_FILE", path)
    monkeypatch.setattr(serp_limit_mod, "LOCK_FILE", lock)
    monkeypatch.setattr(serp_limit_mod, "HARD_LIMIT", 100)

    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 2

    monkeypatch.setattr(serp_limit_mod, "HARD_LIMIT", 2)
    assert serp_limit_mod.serp_quota_acquire() is False
