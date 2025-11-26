"""Tests for Task 6.2 - Circuit Breaker Activation Logic.

This test suite validates the circuit breaker activation that stops retry loops
when the same error repeats multiple times.

**TDD Phase**: RED → GREEN → REFACTOR

Test Coverage:
1. test_circuit_breaker_threshold_default() - Verify default threshold = 2
2. test_circuit_breaker_triggers_on_threshold() - Main requirement test
3. test_circuit_breaker_triggered_flag() - Verify triggered flag is set
4. test_circuit_breaker_configurable_threshold() - ENV variable configuration
5. test_circuit_breaker_prevents_retry_loop() - Integration test

Requirements:
- AC3.5: Circuit breaker triggers on repeated errors (threshold=2)
- NFR-R3: Prevent >10 identical retry attempts
- AC-CC3: Cost monitoring through retry prevention
"""

import os
import pytest

from src.validation.gateway import ValidationGateway


class TestCircuitBreakerActivation:
    """Test suite for circuit breaker activation logic."""

    def setup_method(self):
        """Reset environment before each test."""
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'
        # Clear any circuit breaker threshold override
        if 'CIRCUIT_BREAKER_THRESHOLD' in os.environ:
            del os.environ['CIRCUIT_BREAKER_THRESHOLD']

    def teardown_method(self):
        """Clean up environment after each test."""
        for key in ['ENABLE_VALIDATION_LAYER3', 'CIRCUIT_BREAKER_THRESHOLD']:
            if key in os.environ:
                del os.environ[key]

    def test_circuit_breaker_threshold_default(self):
        """RED TEST: Verify default circuit breaker threshold is 2."""
        gateway = ValidationGateway()

        assert hasattr(gateway, 'circuit_breaker_threshold')
        assert gateway.circuit_breaker_threshold == 2

    def test_circuit_breaker_triggered_flag(self):
        """RED TEST: Verify circuit_breaker_triggered flag exists."""
        gateway = ValidationGateway()

        assert hasattr(gateway, 'circuit_breaker_triggered')
        assert gateway.circuit_breaker_triggered is False  # Initially False

    def test_circuit_breaker_triggers_on_threshold(self):
        """
        RED TEST: Verify circuit breaker triggers when threshold reached.

        This is the main requirement test for Task 6.2.
        **Requirements**: AC3.5, NFR-R3
        """
        gateway = ValidationGateway()

        error_msg = "Field 'type' must be a string"

        # Track error twice (reaching threshold of 2)
        gateway._track_error_signature(error_msg)
        gateway._track_error_signature(error_msg)

        # Check if circuit breaker should trigger
        should_trigger = gateway._should_trigger_circuit_breaker(error_msg)

        assert should_trigger is True

    def test_circuit_breaker_configurable_threshold(self):
        """RED TEST: Verify threshold configurable via environment variable."""
        os.environ['CIRCUIT_BREAKER_THRESHOLD'] = '5'

        gateway = ValidationGateway()

        assert gateway.circuit_breaker_threshold == 5

    def test_circuit_breaker_prevents_retry_loop(self):
        """RED TEST: Integration test - circuit breaker stops retry loop."""
        gateway = ValidationGateway()

        error_msg = "Repeated error"
        retry_count = 0
        max_retries = 10

        # Simulate retry loop
        for i in range(max_retries):
            gateway._track_error_signature(error_msg)

            if gateway._should_trigger_circuit_breaker(error_msg):
                gateway.circuit_breaker_triggered = True
                break

            retry_count += 1

        # Circuit breaker should trigger at threshold (2), preventing full 10 retries
        # Note: retry_count is 1 because:
        # - Iteration 0: Track error (count=1), check threshold (1<2), increment retry_count to 1
        # - Iteration 1: Track error (count=2), check threshold (2>=2), trigger circuit breaker and break
        assert retry_count < max_retries
        assert retry_count == 1  # 1 retry before triggering on 2nd occurrence
        assert gateway.circuit_breaker_triggered is True

    def test_circuit_breaker_reset(self):
        """RED TEST: Verify circuit breaker can be reset."""
        gateway = ValidationGateway()

        # Trigger circuit breaker
        gateway.circuit_breaker_triggered = True

        # Reset
        gateway._reset_circuit_breaker()

        assert gateway.circuit_breaker_triggered is False
        assert len(gateway.error_signatures) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
