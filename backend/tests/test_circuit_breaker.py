"""Tests for the circuit breaker module."""

import asyncio

import pytest

from app.utils.circuit_breaker import (
    CircuitOpenError,
    CircuitState,
    _CircuitBreaker,
    _get_circuit,
    get_circuit_status,
    reset_circuit,
)

# ---------------------------------------------------------------------------
# Helper: controllable async functions
# ---------------------------------------------------------------------------


class ControllableError(Exception):
    """Non-transient error for testing."""

    pass


async def succeed():
    return "ok"


async def fail():
    raise ControllableError("boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_starts_closed():
    """A fresh circuit breaker starts in CLOSED state."""
    cb = _CircuitBreaker(provider="test-closed", failure_threshold=3, recovery_timeout=1.0)
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_opens_after_failures():
    """Circuit opens after reaching the failure threshold."""
    cb = _CircuitBreaker(
        provider="test-opens",
        failure_threshold=3,
        recovery_timeout=60.0,
        max_retries=0,
    )

    for _ in range(3):
        with pytest.raises(ControllableError):
            await cb.call(fail)

    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_rejects_when_open():
    """An open circuit raises CircuitOpenError immediately."""
    cb = _CircuitBreaker(
        provider="test-rejects",
        failure_threshold=2,
        recovery_timeout=60.0,
        max_retries=0,
    )

    # Trip the circuit
    for _ in range(2):
        with pytest.raises(ControllableError):
            await cb.call(fail)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError) as exc_info:
        await cb.call(succeed)
    assert "test-rejects" in str(exc_info.value)


@pytest.mark.asyncio
async def test_circuit_half_open_after_recovery_timeout():
    """Circuit moves to HALF_OPEN after recovery_timeout elapses."""
    cb = _CircuitBreaker(
        provider="test-halfopen",
        failure_threshold=2,
        recovery_timeout=0.1,  # very short for testing
        max_retries=0,
    )

    # Trip the circuit
    for _ in range(2):
        with pytest.raises(ControllableError):
            await cb.call(fail)

    assert cb.state == CircuitState.OPEN

    # Wait for recovery timeout
    await asyncio.sleep(0.15)

    # Next call should go through (circuit transitions to HALF_OPEN)
    result = await cb.call(succeed)
    assert result == "ok"
    # After one success, still HALF_OPEN (need success_threshold=2)
    assert cb.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_circuit_closes_after_successes_in_half_open():
    """Circuit returns to CLOSED after enough successes in HALF_OPEN."""
    cb = _CircuitBreaker(
        provider="test-closes",
        failure_threshold=2,
        recovery_timeout=0.1,
        success_threshold=2,
        max_retries=0,
    )

    # Trip the circuit
    for _ in range(2):
        with pytest.raises(ControllableError):
            await cb.call(fail)

    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.15)

    # Two successes should close it
    await cb.call(succeed)
    assert cb.state == CircuitState.HALF_OPEN

    await cb.call(succeed)
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_transient_errors_are_retried():
    """Transient errors trigger retries before recording failure."""
    from openai import APITimeoutError as OpenAITimeout

    call_count = 0

    async def fail_then_succeed():
        nonlocal call_count
        call_count += 1
        if call_count <= 1:
            raise OpenAITimeout(request=None)
        return "recovered"

    cb = _CircuitBreaker(
        provider="test-retry",
        failure_threshold=5,
        max_retries=2,
        base_backoff=0.01,  # fast backoff for tests
    )

    result = await cb.call(fail_then_succeed)
    assert result == "recovered"
    assert call_count == 2


@pytest.mark.asyncio
async def test_non_transient_errors_not_retried():
    """Non-transient errors are NOT retried — fail immediately."""
    call_count = 0

    async def non_transient_fail():
        nonlocal call_count
        call_count += 1
        raise ControllableError("permanent")

    cb = _CircuitBreaker(
        provider="test-no-retry",
        failure_threshold=5,
        max_retries=2,
    )

    with pytest.raises(ControllableError):
        await cb.call(non_transient_fail)

    # Should have been called only once (no retries)
    assert call_count == 1


@pytest.mark.asyncio
async def test_get_circuit_status():
    """get_circuit_status returns info about registered circuits."""
    # Create a circuit via the global registry
    cb = await _get_circuit("test-status-provider", failure_threshold=5)
    await cb.call(succeed)

    status = get_circuit_status()
    assert "test-status-provider" in status
    info = status["test-status-provider"]
    assert info["state"] == "closed"
    assert info["total_calls"] >= 1


@pytest.mark.asyncio
async def test_reset_circuit():
    """reset_circuit resets a circuit to CLOSED with zeroed metrics."""
    cb = await _get_circuit(
        "test-reset-provider",
        failure_threshold=2,
    )
    # Mutate the circuit's state
    cb._metrics.state = CircuitState.OPEN
    cb._metrics.consecutive_failures = 5

    result = await reset_circuit("test-reset-provider")
    assert result is True
    assert cb.state == CircuitState.CLOSED
    assert cb._metrics.consecutive_failures == 0

    # Resetting non-existent circuit returns False
    result2 = await reset_circuit("nonexistent-provider")
    assert result2 is False
