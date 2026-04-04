"""Regresja: Serp_limit — przy count >= HARD_LIMIT acquire zawsze False."""

from __future__ import annotations

import json

import pytest

import Serp_limit as serp_limit_mod


@pytest.mark.regression
def test_acquire_blocked_when_file_at_limit(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "u.json"
    lock = tmp_path / "u.lock.json"
    monkeypatch.setattr(serp_limit_mod, "USAGE_FILE", path)
    monkeypatch.setattr(serp_limit_mod, "LOCK_FILE", lock)
    monkeypatch.setattr(serp_limit_mod, "HARD_LIMIT", 5)

    path.write_text(json.dumps({"count": 5}), encoding="utf-8")

    assert serp_limit_mod.serp_quota_acquire() is False
    assert serp_limit_mod.serp_quota_get_count() == 5
