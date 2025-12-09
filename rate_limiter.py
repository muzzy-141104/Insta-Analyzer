import time
import random
import logging
import re
from typing import Callable, Optional
from functools import wraps
from enum import Enum

logger = logging.getLogger("rate_limiter")


class RateLimitStrategy(Enum):
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts delays based on observed success/failure rates."""
    def __init__(self, strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE):
        self.strategy = strategy
        self.success_count = 0
        self.failure_count = 0
        self.consecutive_failures = 0
        self.last_request_time = 0.0

    def _get_base_delay(self) -> tuple:
        if self.strategy == RateLimitStrategy.CONSERVATIVE:
            return (3.5, 7.0)
        elif self.strategy == RateLimitStrategy.AGGRESSIVE:
            return (1.0, 3.0)
        else:
            return (2.0, 5.0)

    def _calculate_delay(self) -> float:
        base_min, base_max = self._get_base_delay()
        multiplier = 1.0

        if self.strategy == RateLimitStrategy.ADAPTIVE:
            total = self.success_count + self.failure_count
            success_rate = (self.success_count / total) if total > 0 else 1.0

            if success_rate > 0.9:
                multiplier *= 0.8
            elif success_rate > 0.7:
                multiplier *= 1.0
            else:
                multiplier *= 1.5

            # Add penalty for consecutive failures
            if self.consecutive_failures > 0:
                multiplier += min(self.consecutive_failures * 0.5, 6.0)

        delay_min = base_min * multiplier
        delay_max = base_max * multiplier
        delay = random.uniform(delay_min, delay_max)
        return delay

    def wait(self):
        delay = self._calculate_delay()
        logger.debug(f"Rate limiting: waiting {delay:.2f}s (strategy: {self.strategy.value})")
        time.sleep(delay)
        self.last_request_time = time.time()

    def record_success(self):
        self.success_count += 1
        self.consecutive_failures = 0
        logger.debug(f"Recorded success. Total successes: {self.success_count}")

    def record_failure(self):
        self.failure_count += 1
        self.consecutive_failures += 1
        logger.debug(f"Recorded failure. Consecutive failures: {self.consecutive_failures}")

    def get_stats(self) -> dict:
        total = self.success_count + self.failure_count
        success_rate = (self.success_count / total) if total > 0 else 0.0
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "consecutive_failures": self.consecutive_failures,
            "success_rate": success_rate,
        }


def intelligent_retry(max_retries: int = 5, base_delay: float = 2.0, max_delay: float = 60.0):
    """Decorator to wrap network actions with intelligent retry and 429 detection."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    msg = str(e).lower()
                    status_code = getattr(e, "status_code", None) or getattr(getattr(e, "response", None), "status_code", None)
                    # Broad detection of rate-limit / block signals
                    is_rate_limit = False
                    if status_code == 429:
                        is_rate_limit = True
                    if re.search(r"rate limit|too many requests|temporarily blocked|checkpoint_required|challenge_required|login required|blocked", msg):
                        is_rate_limit = True

                    # Exponential backoff with jitter
                    if is_rate_limit:
                        multiplier = 2.0 + attempt * 1.2
                    else:
                        multiplier = 1.0 + (attempt * 0.5)

                    wait = min(max_delay, base_delay * (2 ** (attempt - 1)) * multiplier) + random.random() * 1.5
                    logger.warning(f"[intelligent_retry] Attempt {attempt}/{max_retries} failed: {e}. Rate-limit? {is_rate_limit}. Sleeping {wait:.1f}s")
                    time.sleep(wait)

                    if attempt >= max_retries:
                        logger.exception(f"[intelligent_retry] Final attempt failed for {func.__name__}: {e}")
                        raise
            # unreachable
        return wrapper
    return decorator


class RequestThrottler:
    """Simple token-bucket-like throttler that returns a recommended wait_time; avoids busy loops."""
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self._interval = 60.0 / max(1, requests_per_minute)
        self._last_ts = 0.0

    def can_make_request(self) -> float:
        """Return 0.0 if request can be made now, or seconds to wait otherwise."""
        now = time.time()
        next_allowed = self._last_ts + self._interval
        if now >= next_allowed:
            self._last_ts = now
            return 0.0
        else:
            wait = next_allowed - now
            return wait

    def wait_if_needed(self):
        wait = self.can_make_request()
        if wait > 0:
            logger.debug(f"RequestThrottler: sleeping {wait:.2f}s to respect rate limit")
            time.sleep(wait)

    def get_stats(self):
        return {"requests_per_minute": self.requests_per_minute, "interval_seconds": self._interval}
