"""Tests for Task 6.1 - Circuit Breaker Error Signature Tracking.

This test suite validates the error signature tracking mechanism that prevents
API waste by detecting repeated identical errors.

**TDD Phase**: RED → GREEN → REFACTOR

Test Coverage:
1. test_error_signature_tracking_exists() - Verify error_signatures dict exists
2. test_error_signature_hashing() - Verify error messages are hashed consistently
3. test_error_signature_frequency_tracking() - Track repeated errors across retries
4. test_circuit_breaker_detects_repeated_errors() - Main requirement test

Requirements:
- AC3.4: Error signature tracking to prevent repeated LLM calls
- AC3.5: Circuit breaker triggers on repeated errors
- NFR-R3: Prevent >10 identical retry attempts
"""

import os
import pytest
from unittest.mock import Mock

from src.validation.gateway import ValidationGateway


class TestCircuitBreakerErrorTracking:
    """Test suite for circuit breaker error signature tracking."""

    def setup_method(self):
        """Reset environment before each test."""
        # Ensure Layer 3 is enabled for circuit breaker tests
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

    def teardown_method(self):
        """Clean up environment after each test."""
        if 'ENABLE_VALIDATION_LAYER3' in os.environ:
            del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_error_signature_tracking_exists(self):
        """
        RED TEST: Verify ValidationGateway has error_signatures tracking.

        Given: A ValidationGateway instance
        When: We inspect the gateway attributes
        Then: Should have error_signatures dict for tracking

        This is the foundational test for Task 6.1.
        """
        gateway = ValidationGateway()

        # ASSERTION: error_signatures dict exists
        assert hasattr(gateway, 'error_signatures'), (
            "ValidationGateway should have error_signatures attribute"
        )
        assert isinstance(gateway.error_signatures, dict), (
            "error_signatures should be a dictionary"
        )
        assert len(gateway.error_signatures) == 0, (
            "error_signatures should start empty"
        )

    def test_error_signature_hashing(self):
        """
        RED TEST: Verify error messages are hashed consistently.

        Given: An error message string
        When: We hash the same error message multiple times
        Then: Should produce the same signature hash

        Consistent hashing is critical for detecting repeated errors.
        """
        gateway = ValidationGateway()

        error_message_1 = "Field 'entry' must be a string"
        error_message_2 = "Field 'exit' must be a string"
        error_message_3 = "Field 'entry' must be a string"  # Same as message 1

        # ASSERTION: Same messages produce same hash
        sig_1 = gateway._hash_error_signature(error_message_1)
        sig_2 = gateway._hash_error_signature(error_message_2)
        sig_3 = gateway._hash_error_signature(error_message_3)

        assert sig_1 == sig_3, "Same error messages should hash to same signature"
        assert sig_1 != sig_2, "Different error messages should hash to different signatures"
        assert isinstance(sig_1, str), "Signature should be a string"
        assert len(sig_1) > 0, "Signature should not be empty"

    def test_error_signature_frequency_tracking(self):
        """
        RED TEST: Verify error signature frequency is tracked across retries.

        Given: Multiple validation attempts with same error
        When: We track the error signature
        Then: Frequency count should increment for each occurrence

        This enables the circuit breaker to detect repeated errors.
        """
        gateway = ValidationGateway()

        error_message = "Field 'type' must be one of: factor_graph, llm_generated, hybrid"

        # Simulate 3 retry attempts with same error
        for i in range(3):
            gateway._track_error_signature(error_message)

        # ASSERTION: Error signature tracked with correct frequency
        sig = gateway._hash_error_signature(error_message)
        assert sig in gateway.error_signatures, "Error signature should be tracked"
        assert gateway.error_signatures[sig] == 3, (
            f"Error signature should have frequency 3, got {gateway.error_signatures[sig]}"
        )

    def test_circuit_breaker_detects_repeated_errors(self):
        """
        RED TEST: Verify circuit breaker detects when same error repeats.

        Given: ValidationGateway with error signature tracking
        When: Same error occurs multiple times (>= threshold)
        Then: Circuit breaker should detect repeated error pattern

        This is the main requirement test for Task 6.1.
        **Requirements**: AC3.4, NFR-R3 (prevent >10 identical retries)
        """
        gateway = ValidationGateway()

        error_message = "Field 'required_fields' must be a list"

        # Simulate repeated error across retry attempts
        # Track error 2 times (will reach threshold of 2 in Task 6.2)
        gateway._track_error_signature(error_message)
        gateway._track_error_signature(error_message)

        # ASSERTION: Can detect if error signature repeats
        sig = gateway._hash_error_signature(error_message)
        is_repeated = gateway._is_error_repeated(error_message, threshold=2)

        assert is_repeated is True, (
            "Circuit breaker should detect repeated error when threshold reached"
        )

        # Verify error signature frequency is correct
        assert gateway.error_signatures[sig] == 2, (
            f"Error signature should have frequency 2, got {gateway.error_signatures[sig]}"
        )

        print(f"✓ Circuit breaker detected repeated error: {sig[:16]}... (frequency: 2)")

    def test_different_errors_tracked_separately(self):
        """
        RED TEST: Verify different errors are tracked with separate signatures.

        Given: Multiple different error messages
        When: We track each error
        Then: Each should have its own signature and frequency count

        This ensures the circuit breaker doesn't conflate different errors.
        """
        gateway = ValidationGateway()

        error_1 = "Field 'name' must be a string"
        error_2 = "Field 'type' is invalid"
        error_3 = "Field 'name' must be a string"  # Same as error_1

        # Track errors
        gateway._track_error_signature(error_1)
        gateway._track_error_signature(error_2)
        gateway._track_error_signature(error_3)

        # ASSERTION: Different errors have separate signatures
        sig_1 = gateway._hash_error_signature(error_1)
        sig_2 = gateway._hash_error_signature(error_2)

        assert len(gateway.error_signatures) == 2, (
            "Should track 2 different error signatures"
        )
        assert gateway.error_signatures[sig_1] == 2, "Error 1 should appear 2 times"
        assert gateway.error_signatures[sig_2] == 1, "Error 2 should appear 1 time"

    def test_error_signature_reset(self):
        """
        RED TEST: Verify error signatures can be reset for new validation cycle.

        Given: ValidationGateway with tracked error signatures
        When: We reset error signatures
        Then: error_signatures dict should be empty

        This allows fresh error tracking for each strategy generation cycle.
        """
        gateway = ValidationGateway()

        # Track some errors
        gateway._track_error_signature("Error 1")
        gateway._track_error_signature("Error 2")
        assert len(gateway.error_signatures) > 0

        # Reset error signatures
        gateway._reset_error_signatures()

        # ASSERTION: Error signatures cleared
        assert len(gateway.error_signatures) == 0, (
            "Error signatures should be empty after reset"
        )


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
