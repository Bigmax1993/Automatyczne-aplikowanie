"""Integracja: rate_limit — prawdziwy sleep między wywołaniami."""

from __future__ import annotations

import time

import pytest

from rate_limit import rate_limit


@pytest.mark.integration
def test_rate_limit_enforces_real_elapsed_gap() -> None:
    @rate_limit(0.12)
    def tick() -> int:
        return 1

    t0 = time.perf_counter()
    tick()
    tick()
    elapsed = time.perf_counter() - t0
    assert elapsed >= 0.10, f"oczekiwano ~≥0.12s przerwy, było {elapsed:.3f}s"
