"""Integracja: simple_retry z prawdziwym backoff (wolne; domyślnie wyłączone)."""

from __future__ import annotations

import time

import pytest

from rate_limit import simple_retry

from tests.integration.helpers import env_truthy


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(
    not env_truthy("RUN_SLOW_INTEGRATION"),
    reason="Ustaw RUN_SLOW_INTEGRATION=1 (ok. 4+ s przerw tenacity).",
)
def test_simple_retry_three_attempts_real_delay() -> None:
    state = {"n": 0}

    @simple_retry()
    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise ConnectionError("fail")
        return "ok"

    t0 = time.perf_counter()
    assert flaky() == "ok"
    elapsed = time.perf_counter() - t0
    assert state["n"] == 3
    assert elapsed >= 3.5
