"""
rate_limit.py
Uniwersalne dekoratory retry i limitowania zapytań.
"""

import threading
import time
from functools import wraps
from typing import Callable, TypeVar

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

F = TypeVar("F", bound=Callable[..., object])


# ---------------------------------------------------------
# 1. Prosty retry — 3 próby, 2 sekundy przerwy
# ---------------------------------------------------------
def simple_retry() -> Callable[[F], F]:
    """
    Zwraca dekorator retry:
    - 3 próby
    - 2 sekundy przerwy między próbami
    """
    return retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)


# ---------------------------------------------------------
# 2. Limitowanie zapytań — np. SerpApi (1 zapytanie / X sekund)
# ---------------------------------------------------------
def rate_limit(seconds: float) -> Callable[[F], F]:
    """
    Dekorator wymuszający minimalną przerwę między rozpoczęciami kolejnych wywołań.

    Przykład:
        @rate_limit(1.5)
        def fetch():
            ...
    """

    def decorator(func: F) -> F:
        last_start = {"t": 0.0}
        lock = threading.Lock()

        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.monotonic()
                elapsed = now - last_start["t"]
                if elapsed < seconds:
                    wait = seconds - elapsed
                    logger.debug(f"Rate limit: czekam {wait:.2f} s…")
                    time.sleep(wait)
                last_start["t"] = time.monotonic()

            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------
# 3. Retry + rate limit w jednym (dla API)
# ---------------------------------------------------------
def api_safe(seconds: float = 1.0) -> Callable[[F], F]:
    """
    Łączy rate limit (przed każdą próbą) z retry (po błędzie).
    """

    def decorator(func: F) -> F:
        limited = rate_limit(seconds)(func)

        @simple_retry()
        @wraps(func)
        def wrapper(*args, **kwargs):
            return limited(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
