"""Testy: rate_limit — retry, przerwy między wywołaniami, api_safe."""

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest

from rate_limit import api_safe, rate_limit, simple_retry


def test_simple_retry_succeeds_after_transient_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"n": 0}

    @simple_retry()
    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ValueError("temporary")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 2


def test_simple_retry_reraises_after_exhausted_attempts() -> None:
    @simple_retry()
    def always_bad() -> None:
        raise RuntimeError("x")

    with pytest.raises(RuntimeError, match="x"):
        always_bad()


def test_rate_limit_invokes_sleep_when_calls_too_close(monkeypatch: pytest.MonkeyPatch) -> None:
    slept: list[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: slept.append(float(s)))

    seq = iter([100.0, 100.05, 100.07, 200.0])

    def mono() -> float:
        return next(seq)

    monkeypatch.setattr(time, "monotonic", mono)

    @rate_limit(1.0)
    def f(x: int) -> int:
        return x

    assert f(1) == 1
    assert f(2) == 2
    assert slept, "drugie wywołanie powinno poczekać"
    assert slept[0] > 0.9


def test_api_safe_applies_rate_limit_and_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda *a, **k: None)

    calls = {"n": 0}

    @api_safe(0.01)
    def work() -> int:
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("retry me")
        return 42

    assert work() == 42
    assert calls["n"] == 2
