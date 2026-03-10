"""
Circuit breaker for LLM API calls (OpenAI and Anthropic).

Prevents cascading failures by short-circuiting requests to providers
that are experiencing outages. Includes retry logic with exponential
backoff for transient errors.
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from anthropic import (
    APIError as AnthropicAPIError,
)
from anthropic import (
    APITimeoutError as AnthropicTimeoutError,
)
from openai import (
    APIError as OpenAIAPIError,
)
from openai import (
    APITimeoutError as OpenAITimeoutError,
)

logger = logging.getLogger(__name__)

# Status codes considered transient (worth retrying)
TRANSIENT_STATUS_CODES = {429, 500, 502, 503}


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    """Raised when a call is attempted against an open circuit."""

    def __init__(self, provider: str, remaining_seconds: float):
        self.provider = provider
        self.remaining_seconds = remaining_seconds
        super().__init__(f"Circuit for '{provider}' is OPEN. Recovery in {remaining_seconds:.1f}s.")


def _is_transient(exc: Exception) -> bool:
    """Check if an exception represents a transient/retryable error."""
    # Timeouts are always transient
    if isinstance(exc, (AnthropicTimeoutError, OpenAITimeoutError)):
        return True

    # API errors with retryable status codes
    if isinstance(exc, (AnthropicAPIError, OpenAIAPIError)):
        status = getattr(exc, "status_code", None)
        if status is None:
            status = getattr(exc, "status", None)
        if status in TRANSIENT_STATUS_CODES:
            return True

    return False


@dataclass
class CircuitMetrics:
    total_calls: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: float | None = None
    state: CircuitState = CircuitState.CLOSED


@dataclass
class _CircuitBreaker:
    """Per-provider circuit breaker state."""

    provider: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    max_retries: int = 2
    base_backoff: float = 1.0

    # Internal state
    _metrics: CircuitMetrics = field(default_factory=CircuitMetrics)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def state(self) -> CircuitState:
        return self._metrics.state

    def _transition(self, new_state: CircuitState) -> None:
        old = self._metrics.state
        if old != new_state:
            self._metrics.state = new_state
            logger.warning("Circuit '%s': %s -> %s", self.provider, old.value, new_state.value)

    def _seconds_until_recovery(self) -> float:
        if self._metrics.last_failure_time is None:
            return 0.0
        elapsed = time.monotonic() - self._metrics.last_failure_time
        return max(0.0, self.recovery_timeout - elapsed)

    async def _pre_call(self) -> None:
        """Check circuit state before allowing a call through."""
        async with self._lock:
            self._metrics.total_calls += 1

            if self._metrics.state == CircuitState.CLOSED:
                return

            if self._metrics.state == CircuitState.OPEN:
                remaining = self._seconds_until_recovery()
                if remaining > 0:
                    raise CircuitOpenError(self.provider, remaining)
                # Recovery timeout elapsed — move to half-open
                self._transition(CircuitState.HALF_OPEN)
                self._metrics.consecutive_successes = 0
                return

            # HALF_OPEN: allow the call through (testing recovery)

    async def _record_success(self) -> None:
        async with self._lock:
            self._metrics.consecutive_failures = 0

            if self._metrics.state == CircuitState.HALF_OPEN:
                self._metrics.consecutive_successes += 1
                if self._metrics.consecutive_successes >= self.success_threshold:
                    self._transition(CircuitState.CLOSED)
                    self._metrics.consecutive_successes = 0
            else:
                self._metrics.consecutive_successes = 0

    async def _record_failure(self) -> None:
        async with self._lock:
            self._metrics.total_failures += 1
            self._metrics.consecutive_failures += 1
            self._metrics.last_failure_time = time.monotonic()

            if self._metrics.state == CircuitState.HALF_OPEN:
                # Any failure in half-open reopens immediately
                self._transition(CircuitState.OPEN)
                self._metrics.consecutive_successes = 0
            elif self._metrics.consecutive_failures >= self.failure_threshold:
                self._transition(CircuitState.OPEN)

    async def call(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Execute a function through the circuit breaker with retry logic."""
        await self._pre_call()

        last_exc: Exception | None = None

        for attempt in range(1 + self.max_retries):
            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except Exception as exc:
                last_exc = exc

                if _is_transient(exc) and attempt < self.max_retries:
                    delay = self.base_backoff * (2**attempt)
                    logger.info(
                        "Circuit '%s': transient error on attempt %d/%d, retrying in %.1fs — %s",
                        self.provider,
                        attempt + 1,
                        1 + self.max_retries,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                    continue

                # Non-transient or retries exhausted
                await self._record_failure()
                raise

        # Should not reach here, but just in case
        if last_exc:
            await self._record_failure()
            raise last_exc

    def get_status(self) -> dict[str, Any]:
        m = self._metrics
        return {
            "provider": self.provider,
            "state": m.state.value,
            "total_calls": m.total_calls,
            "total_failures": m.total_failures,
            "consecutive_failures": m.consecutive_failures,
            "last_failure_time": m.last_failure_time,
            "seconds_until_recovery": (self._seconds_until_recovery() if m.state == CircuitState.OPEN else 0),
        }


# ---------------------------------------------------------------------------
# Global registry
# ---------------------------------------------------------------------------

_circuits: dict[str, _CircuitBreaker] = {}
_registry_lock = asyncio.Lock()


async def _get_circuit(
    provider: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
) -> _CircuitBreaker:
    """Get or create a circuit breaker for the given provider."""
    if provider not in _circuits:
        async with _registry_lock:
            # Double-check after acquiring lock
            if provider not in _circuits:
                _circuits[provider] = _CircuitBreaker(
                    provider=provider,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    success_threshold=success_threshold,
                )
    return _circuits[provider]


def _get_circuit_sync(provider: str) -> _CircuitBreaker | None:
    """Non-async lookup for existing circuits only."""
    return _circuits.get(provider)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def circuit_protected(
    provider: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 2,
) -> Callable:
    """
    Decorator that wraps an async function with circuit breaker protection.

    Usage:
        @circuit_protected(provider="openai")
        async def call_openai(prompt: str) -> str:
            ...

        @circuit_protected(provider="anthropic")
        async def call_anthropic(prompt: str) -> str:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            cb = await _get_circuit(
                provider,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold,
            )
            return await cb.call(func, *args, **kwargs)

        return wrapper

    return decorator


def get_circuit_status() -> dict[str, Any]:
    """
    Return the current status of all registered circuit breakers.
    Suitable for a /health endpoint response.
    """
    return {name: cb.get_status() for name, cb in _circuits.items()}


async def reset_circuit(provider: str) -> bool:
    """
    Manually reset a circuit breaker to CLOSED state.
    Returns True if the circuit existed and was reset.
    """
    cb = _get_circuit_sync(provider)
    if cb is None:
        return False
    async with cb._lock:
        cb._metrics = CircuitMetrics()
    logger.info("Circuit '%s' manually reset to CLOSED.", provider)
    return True
