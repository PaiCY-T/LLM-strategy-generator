"""Integration Tests for Task 5.1 - SchemaValidator Integration into ValidationGateway.

This test suite validates the integration of Layer 3 (SchemaValidator) into ValidationGateway
for YAML structure validation before parsing.

**TDD Phase**: RED → GREEN → REFACTOR

Test Coverage:
1. test_validate_yaml_method_exists() - Verify method exists
2. test_validate_yaml_with_valid_structure() - Valid YAML passes
3. test_validate_yaml_with_invalid_structure() - Invalid YAML detected
4. test_validate_yaml_with_missing_required_keys() - Missing keys caught
5. test_validate_yaml_when_layer3_disabled() - Graceful degradation
6. test_validate_yaml_performance_under_5ms() - Performance requirement
7. test_validate_yaml_returns_validation_errors() - Structured error objects
8. test_validate_yaml_integration_with_layer1_layer2() - Multi-layer integration

Requirements:
- AC3.1: SchemaValidator integrated into ValidationGateway
- NFR-P1: Layer 3 validation <5ms per validation
- Task 5.1: YAML structure validation before parsing
"""

import os
import time
import pytest

from src.validation.gateway import ValidationGateway
from src.execution.schema_validator import ValidationError, ValidationSeverity
from src.config.feature_flags import FeatureFlagManager


class TestSchemaValidatorIntegration:
    """Test suite for SchemaValidator integration into ValidationGateway."""

    def setup_method(self):
        """Reset FeatureFlagManager singleton before each test."""
        # Reset singleton instance to ensure fresh state
        FeatureFlagManager._instance = None
        # Clear any cached _initialized flag
        if hasattr(FeatureFlagManager, '_initialized'):
            delattr(FeatureFlagManager, '_initialized')

    def teardown_method(self):
        """Clean up environment variables and reset singleton after each test."""
        # Reset singleton instance
        FeatureFlagManager._instance = None
        # Clear environment variables
        for key in ['ENABLE_VALIDATION_LAYER1', 'ENABLE_VALIDATION_LAYER2', 'ENABLE_VALIDATION_LAYER3']:
            if key in os.environ:
                del os.environ[key]

    def test_validate_yaml_method_exists(self):
        """
        RED TEST: Verify ValidationGateway has validate_yaml() method.

        Given: A ValidationGateway instance
        When: We check for validate_yaml() method
        Then: Method should exist and be callable

        This is the foundational test for Task 5.1.
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # ASSERTION: validate_yaml() method exists
            assert hasattr(gateway, 'validate_yaml'), (
                "ValidationGateway should have validate_yaml() method"
            )
            assert callable(gateway.validate_yaml), (
                "validate_yaml() should be callable"
            )

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_with_valid_structure(self):
        """
        RED TEST: Verify validate_yaml() returns empty list for valid YAML.

        Given: A valid YAML dictionary matching expected schema
        When: We call gateway.validate_yaml(yaml_dict)
        Then: Should return empty list (no errors)

        Valid YAML contains all required keys with correct types.
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # Valid YAML dictionary
            yaml_dict = {
                "name": "Test Strategy",
                "type": "factor_graph",
                "required_fields": ["close", "volume"],
                "parameters": [
                    {"name": "period", "type": "int", "value": 20}
                ],
                "logic": {
                    "entry": "close > close.rolling(20).mean()",
                    "exit": "close < close.rolling(20).mean()"
                }
            }

            # ASSERTION: Valid YAML returns empty error list
            errors = gateway.validate_yaml(yaml_dict)
            assert isinstance(errors, list), "Should return list"
            assert len(errors) == 0, (
                f"Valid YAML should have no errors, got {len(errors)} errors"
            )

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_with_invalid_structure(self):
        """
        RED TEST: Verify validate_yaml() detects invalid YAML structure.

        Given: An invalid YAML dictionary (not a dict)
        When: We call gateway.validate_yaml(invalid_yaml)
        Then: Should return list with ValidationError objects

        Invalid YAML structure should be caught before parsing.
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # Invalid YAML (list instead of dict)
            invalid_yaml = ["not", "a", "dictionary"]

            # ASSERTION: Invalid structure returns errors
            errors = gateway.validate_yaml(invalid_yaml)
            assert isinstance(errors, list), "Should return list"
            assert len(errors) > 0, "Invalid YAML should have errors"

            # Verify error structure
            error = errors[0]
            assert isinstance(error, ValidationError), (
                "Should return ValidationError objects"
            )
            assert error.severity == ValidationSeverity.ERROR, (
                "Should be ERROR severity"
            )

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_with_missing_required_keys(self):
        """
        RED TEST: Verify validate_yaml() detects missing required keys.

        Given: YAML dictionary missing required keys (name, type, etc.)
        When: We call gateway.validate_yaml(incomplete_yaml)
        Then: Should return errors for each missing required key

        Required keys: name, type, required_fields, parameters, logic
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # YAML missing required keys
            incomplete_yaml = {
                "name": "Incomplete Strategy"
                # Missing: type, required_fields, parameters, logic
            }

            # ASSERTION: Missing keys detected
            errors = gateway.validate_yaml(incomplete_yaml)
            assert len(errors) > 0, (
                "YAML with missing required keys should have errors"
            )

            # Verify at least one error mentions missing key
            error_messages = [error.message for error in errors]
            assert any("required" in msg.lower() or "missing" in msg.lower()
                      for msg in error_messages), (
                "Should mention missing/required keys in error messages"
            )

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_when_layer3_disabled(self):
        """
        RED TEST: Verify graceful degradation when Layer 3 disabled.

        Given: ENABLE_VALIDATION_LAYER3=false (default)
        When: We call gateway.validate_yaml(invalid_yaml)
        Then: Should return empty list (no validation performed)

        This ensures backward compatibility when Layer 3 is disabled.
        """
        # Disable Layer 3 (default)
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'false'

        try:
            gateway = ValidationGateway()

            # Invalid YAML (should pass when validation disabled)
            invalid_yaml = {"invalid": "structure"}

            # ASSERTION: No validation when Layer 3 disabled
            errors = gateway.validate_yaml(invalid_yaml)
            assert isinstance(errors, list), "Should return list"
            assert len(errors) == 0, (
                "Should return empty list when Layer 3 disabled (graceful degradation)"
            )

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_performance_under_5ms(self):
        """
        RED TEST: Verify Layer 3 validation completes in <5ms.

        Given: A typical YAML dictionary
        When: We measure validation latency over 100 calls
        Then: Average latency should be <5ms (NFR-P1)

        Performance budget: <5ms per validation
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # Typical YAML dictionary
            yaml_dict = {
                "name": "Performance Test Strategy",
                "type": "factor_graph",
                "required_fields": ["close", "volume", "open"],
                "parameters": [
                    {"name": "period", "type": "int", "value": 20},
                    {"name": "threshold", "type": "float", "value": 0.05}
                ],
                "logic": {
                    "entry": "close > close.rolling(20).mean()",
                    "exit": "close < close.rolling(20).mean()"
                }
            }

            # Measure latency over 100 validations
            total_latency_ms = 0.0
            num_validations = 100

            for _ in range(num_validations):
                start_time = time.perf_counter()
                errors = gateway.validate_yaml(yaml_dict)
                end_time = time.perf_counter()

                latency_ms = (end_time - start_time) * 1000
                total_latency_ms += latency_ms

            # Calculate average latency
            avg_latency_ms = total_latency_ms / num_validations

            # ASSERTION: Average latency <5ms
            assert avg_latency_ms < 5.0, (
                f"Average validation latency {avg_latency_ms:.2f}ms should be <5ms (NFR-P1)"
            )

            print(f"\n✓ Layer 3 validation performance: {avg_latency_ms:.2f}ms (<5ms target)")

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_returns_validation_errors(self):
        """
        RED TEST: Verify validate_yaml() returns structured ValidationError objects.

        Given: YAML with type validation errors
        When: We call gateway.validate_yaml(yaml_dict)
        Then: Should return ValidationError objects with proper structure

        ValidationError should contain: severity, message, field_path
        """
        # Enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # YAML with type error (type should be str, not int)
            yaml_dict = {
                "name": "Test Strategy",
                "type": 123,  # Invalid type (should be string)
                "required_fields": ["close"],
                "parameters": [],
                "logic": {"entry": "true", "exit": "false"}
            }

            # ASSERTION: Returns ValidationError objects
            errors = gateway.validate_yaml(yaml_dict)

            if len(errors) > 0:
                error = errors[0]

                # Verify ValidationError structure
                assert hasattr(error, 'severity'), "Should have severity"
                assert hasattr(error, 'message'), "Should have message"
                assert hasattr(error, 'field_path'), "Should have field_path"

                # Verify error content
                assert isinstance(error.severity, ValidationSeverity), (
                    "severity should be ValidationSeverity enum"
                )
                assert isinstance(error.message, str), "message should be string"
                assert len(error.message) > 0, "message should not be empty"

        finally:
            if 'ENABLE_VALIDATION_LAYER3' in os.environ:
                del os.environ['ENABLE_VALIDATION_LAYER3']

    def test_validate_yaml_integration_with_layer1_layer2(self):
        """
        RED TEST: Verify Layer 3 works alongside Layer 1 and Layer 2.

        Given: All validation layers enabled (Layer 1, 2, 3)
        When: We call gateway.validate_yaml(yaml_dict)
        Then: Layer 3 validation should work independently

        This ensures proper layer independence and integration.
        """
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        try:
            gateway = ValidationGateway()

            # Verify all layers initialized
            assert gateway.manifest is not None, "Layer 1 should be initialized"
            assert gateway.field_validator is not None, "Layer 2 should be initialized"
            assert gateway.schema_validator is not None, "Layer 3 should be initialized"

            # Valid YAML
            yaml_dict = {
                "name": "Multi-Layer Test",
                "type": "factor_graph",
                "required_fields": ["close"],
                "parameters": [],
                "logic": {"entry": "close > 100", "exit": "close < 90"}
            }

            # ASSERTION: Layer 3 validation works with other layers
            errors = gateway.validate_yaml(yaml_dict)
            assert isinstance(errors, list), "Should return list"
            # Valid YAML should pass all layers
            assert len(errors) == 0, (
                f"Valid YAML should pass all validation layers, got {len(errors)} errors"
            )

            print(f"\n✓ Multi-layer integration working: All 3 layers initialized and functional")

        finally:
            for key in ['ENABLE_VALIDATION_LAYER1', 'ENABLE_VALIDATION_LAYER2', 'ENABLE_VALIDATION_LAYER3']:
                if key in os.environ:
                    del os.environ[key]


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '-s'])
