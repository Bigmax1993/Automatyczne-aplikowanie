"""
Regresja: rate_limit — retry + limit w api_safe nie psują wyniku przy sukcesie.
"""

from __future__ import annotations

import pytest

from rate_limit import api_safe, rate_limit, simple_retry


@pytest.mark.regression
def test_rate_limit_preserves_return_value() -> None:
    @rate_limit(0.001)
    def add_one(x: int) -> int:
        return x + 1

    assert add_one(40) == 41


@pytest.mark.regression
def test_simple_retry_eventually_returns() -> None:
    n = {"c": 0}

    @simple_retry()
    def third_time_lucky() -> str:
        n["c"] += 1
        if n["c"] < 3:
            raise ValueError("not yet")
        return "done"

    assert third_time_lucky() == "done"


@pytest.mark.regression
def test_api_safe_single_successful_call_invokes_inner_once() -> None:
    calls = {"n": 0}

    @api_safe(0.001)
    def ping() -> int:
        calls["n"] += 1
        return 7

    assert ping() == 7
    assert calls["n"] == 1
