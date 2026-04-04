"""Testy: Serp_limit — twardy limit (atomowy acquire + plik)."""

from __future__ import annotations

import json

import pytest

import Serp_limit as serp_limit_mod


@pytest.fixture
def usage_file(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "serp_usage.json"
    lock = tmp_path / "serp_usage.lock.json"
    monkeypatch.setattr(serp_limit_mod, "USAGE_FILE", path)
    monkeypatch.setattr(serp_limit_mod, "LOCK_FILE", lock)
    return path


def test_get_count_zero_when_no_file(usage_file) -> None:
    assert serp_limit_mod.serp_quota_get_count() == 0


def test_acquire_creates_and_increments(usage_file) -> None:
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 1
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 2


def test_acquire_false_at_hard_limit(usage_file, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(serp_limit_mod, "HARD_LIMIT", 2)
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 2
    assert serp_limit_mod.serp_quota_acquire() is False
    assert serp_limit_mod.serp_quota_get_count() == 2


def test_acquire_respects_existing_count(usage_file) -> None:
    usage_file.write_text(json.dumps({"count": 249}), encoding="utf-8")
    assert serp_limit_mod.serp_quota_acquire() is True
    assert serp_limit_mod.serp_quota_get_count() == 250
    assert serp_limit_mod.serp_quota_acquire() is False
