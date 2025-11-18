"""Test FieldValidator integration into ValidationGateway.

This test suite verifies Task 3.2 requirements:
- AC2.1: FieldValidator integrated into ValidationGateway
- AC2.2: Call FieldValidator.validate_code() after YAML parsing but before execution
- NFR-P1: Layer 2 performance <5ms per validation
- Return structured FieldError objects with line/column information

Test Strategy:
- Test validation gateway method exists and has correct signature
- Test FieldValidator called when Layer 2 enabled
- Test structured FieldError objects returned
- Test performance meets <5ms budget
- Test graceful degradation when Layer 2 disabled
- Test backward compatibility with existing functionality
"""
import os
import time
import pytest
from src.validation.gateway import ValidationGateway
from src.validation.validation_result import ValidationResult, FieldError
from src.config.feature_flags import FeatureFlagManager


class TestFieldValidatorIntegration:
    """Test suite for FieldValidator integration into ValidationGateway."""

    def test_validate_strategy_method_exists(self):
        """Test that ValidationGateway has validate_strategy() method.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Verify method exists
            assert hasattr(gateway, 'validate_strategy'), \
                "ValidationGateway must have validate_strategy() method"

            # Verify it's callable
            assert callable(gateway.validate_strategy), \
                "validate_strategy must be callable"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_field_validator_detects_invalid_fields(self):
        """Test that FieldValidator detects invalid field usage.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - AC2.1: FieldValidator integrated into ValidationGateway
        - AC2.2: Call FieldValidator.validate_code() after YAML parsing
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Test code with invalid field
            invalid_code = """
def strategy(data):
    price = data.get('price:成交量')  # Invalid field
    return price > 100
"""

            # Call validation
            result = gateway.validate_strategy(invalid_code)

            # Verify validation result
            assert isinstance(result, ValidationResult), \
                "validate_strategy must return ValidationResult"
            assert not result.is_valid, \
                "Invalid field should cause validation to fail"
            assert len(result.errors) > 0, \
                "Invalid field should generate errors"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_field_validator_returns_field_errors(self):
        """Test that FieldValidator returns structured FieldError objects.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - Return structured FieldError objects with line/column information
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Test code with invalid field
            invalid_code = """
def strategy(data):
    volume = data.get('price:成交量')  # Invalid field at line 3
    return volume > 1000
"""

            # Call validation
            result = gateway.validate_strategy(invalid_code)

            # Verify structured errors
            assert len(result.errors) > 0, "Should have at least one error"

            error = result.errors[0]
            assert isinstance(error, FieldError), \
                "Errors must be FieldError objects"
            assert error.line > 0, "Error must have line number"
            assert error.column >= 0, "Error must have column number"
            assert error.field_name == 'price:成交量', \
                "Error must include field name"
            assert error.suggestion is not None, \
                "Error should include suggestion for common mistakes"
            assert 'price:成交金額' in error.suggestion, \
                "Suggestion should point to correct field"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_field_validator_performance_under_5ms(self):
        """Test that Layer 2 validation completes in <5ms.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - NFR-P1: Layer 2 performance <5ms per validation
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Test code with multiple fields
            test_code = """
def strategy(data):
    close = data.get('close')
    volume = data.get('volume')
    pe = data.get('fundamental_features:本益比')
    return close > 100 and volume > 1000
"""

            # Measure validation time
            start_time = time.perf_counter()
            result = gateway.validate_strategy(test_code)
            end_time = time.perf_counter()

            # Calculate elapsed time in milliseconds
            elapsed_ms = (end_time - start_time) * 1000

            # Verify performance
            assert elapsed_ms < 5.0, \
                f"Validation took {elapsed_ms:.2f}ms, must be <5ms (NFR-P1)"

            # Verify validation succeeded
            assert result.is_valid, \
                "Valid code should pass validation"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_field_validator_integration_with_gateway(self):
        """Test that ValidationGateway properly integrates FieldValidator.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - AC2.1: FieldValidator integrated into ValidationGateway
        - Verify proper initialization and usage
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Verify FieldValidator is initialized
            assert gateway.field_validator is not None, \
                "FieldValidator should be initialized when Layer 2 enabled"

            # Test valid code passes validation
            valid_code = """
def strategy(data):
    close = data.get('close')
    return close > 100
"""
            result = gateway.validate_strategy(valid_code)
            assert result.is_valid, "Valid code should pass validation"
            assert len(result.errors) == 0, "Valid code should have no errors"

            # Test invalid code fails validation
            invalid_code = """
def strategy(data):
    bad = data.get('invalid_field_xyz')
    return bad > 100
"""
            result = gateway.validate_strategy(invalid_code)
            assert not result.is_valid, "Invalid code should fail validation"
            assert len(result.errors) > 0, "Invalid code should have errors"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_validation_happens_before_execution(self):
        """Test that validation occurs before execution (architectural requirement).

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - AC2.2: Call FieldValidator.validate_code() after YAML parsing but before execution
        - Verify timing and error handling
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Code with invalid field that would fail at execution
            code_with_error = """
def strategy(data):
    # This would fail at execution if not caught
    result = data.get('nonexistent_field')
    return result > 100
"""

            # Validation should catch error before execution
            result = gateway.validate_strategy(code_with_error)

            # Verify error caught during validation phase
            assert not result.is_valid, \
                "Validation should catch errors before execution"
            assert len(result.errors) > 0, \
                "Errors should be reported in validation phase"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)

    def test_graceful_degradation_when_layer2_disabled(self):
        """Test graceful degradation when Layer 2 is disabled.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.

        Requirements:
        - Backward compatibility when ENABLE_VALIDATION_LAYER2=false
        - Graceful degradation without errors
        """
        # Setup: Disable Layer 2 explicitly
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'

        try:
            # Reset singleton to pick up new env vars
            FeatureFlagManager._instance = None

            gateway = ValidationGateway()

            # Verify FieldValidator is None
            assert gateway.field_validator is None, \
                "FieldValidator should be None when Layer 2 disabled"

            # Test that validation still works (returns valid)
            test_code = """
def strategy(data):
    close = data.get('close')
    return close > 100
"""
            result = gateway.validate_strategy(test_code)

            # Should return valid result (no validation performed)
            assert isinstance(result, ValidationResult), \
                "Should still return ValidationResult"
            assert result.is_valid, \
                "Should return valid when Layer 2 disabled (graceful degradation)"
            assert len(result.errors) == 0, \
                "Should have no errors when Layer 2 disabled"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)
            # Reset singleton for next test
            FeatureFlagManager._instance = None

    def test_multiple_field_errors_detected(self):
        """Test that multiple field errors are detected in single validation.

        RED Phase: This test will fail because validate_strategy() doesn't exist yet.
        """
        # Setup: Enable Layer 2
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'

        try:
            gateway = ValidationGateway()

            # Code with multiple invalid fields
            code_with_multiple_errors = """
def strategy(data):
    bad1 = data.get('invalid_field_1')
    bad2 = data.get('invalid_field_2')
    bad3 = data.get('price:成交量')  # Common mistake
    return bad1 + bad2 + bad3 > 100
"""

            # Call validation
            result = gateway.validate_strategy(code_with_multiple_errors)

            # Verify multiple errors detected
            assert not result.is_valid, "Should fail validation"
            assert len(result.errors) >= 3, \
                "Should detect all 3 invalid fields"

            # Verify structured errors
            for error in result.errors:
                assert isinstance(error, FieldError), \
                    "All errors must be FieldError objects"
                assert error.line > 0, "Each error must have line number"

        finally:
            # Cleanup
            os.environ.pop('ENABLE_VALIDATION_LAYER1', None)
            os.environ.pop('ENABLE_VALIDATION_LAYER2', None)
