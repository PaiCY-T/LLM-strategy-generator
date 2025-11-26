"""Tests for ValidationMetadata integration into validate_and_fix method.

Task 7.1: Validation Metadata Integration
This module tests the ValidationMetadata structure and its integration into
the ValidationGateway.validate_and_fix() method.

Test Coverage:
- ValidationMetadata structure validation
- Metadata returned with validation results
- Metadata persisted with strategy records
- Layer-by-layer tracking (latency, errors)
- Integration with existing validation layers

Requirements:
- Metadata structure includes layer info, latency, error counts
- Metadata returned with validation results
- Metadata persisted with strategy records
- 100% test coverage for new functionality
"""

import os
import sys
import pytest
import time
from typing import Dict, Any
from dataclasses import is_dataclass, fields

from src.validation.gateway import ValidationGateway
from src.validation.validation_result import ValidationResult


@pytest.fixture(autouse=True)
def reset_feature_flags():
    """Reset FeatureFlagManager singleton before each test."""
    # Save original environment
    original_env = {}
    for key in ['ENABLE_VALIDATION_LAYER1', 'ENABLE_VALIDATION_LAYER2', 'ENABLE_VALIDATION_LAYER3']:
        original_env[key] = os.environ.get(key)

    # Clear singleton instance before test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None

    yield

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    # Clean up after test
    if 'src.config.feature_flags' in sys.modules:
        from src.config.feature_flags import FeatureFlagManager
        FeatureFlagManager._instance = None


class TestValidationMetadataStructure:
    """Test ValidationMetadata dataclass structure."""

    def test_validation_metadata_exists(self):
        """Test that ValidationMetadata dataclass exists and can be imported.

        Expected:
            ValidationMetadata should be importable from src.validation.validation_result
        """
        # This test will fail until we create ValidationMetadata
        from src.validation.validation_result import ValidationMetadata

        # Check it's a dataclass
        assert is_dataclass(ValidationMetadata), "ValidationMetadata should be a dataclass"

    def test_validation_metadata_has_required_fields(self):
        """Test that ValidationMetadata has all required fields.

        Required fields:
            - layers_executed: List[str]
            - layer_results: Dict[str, bool]
            - layer_latencies: Dict[str, float]
            - total_latency_ms: float
            - error_counts: Dict[str, int]
            - timestamp: str
        """
        from src.validation.validation_result import ValidationMetadata

        # Get dataclass fields
        field_names = {f.name for f in fields(ValidationMetadata)}

        # Check required fields
        required_fields = {
            'layers_executed',
            'layer_results',
            'layer_latencies',
            'total_latency_ms',
            'error_counts',
            'timestamp'
        }

        assert required_fields.issubset(field_names), \
            f"Missing required fields: {required_fields - field_names}"

    def test_validation_metadata_can_be_instantiated(self):
        """Test that ValidationMetadata can be created with valid data."""
        from src.validation.validation_result import ValidationMetadata

        # Create metadata instance
        metadata = ValidationMetadata(
            layers_executed=["Layer1", "Layer2"],
            layer_results={"Layer1": True, "Layer2": False},
            layer_latencies={"Layer1": 0.5, "Layer2": 1.2},
            total_latency_ms=1.7,
            error_counts={"Layer1": 0, "Layer2": 2},
            timestamp="2025-11-19T10:00:00"
        )

        # Verify instance
        assert metadata is not None
        assert metadata.layers_executed == ["Layer1", "Layer2"]
        assert metadata.layer_results["Layer1"] is True
        assert metadata.layer_results["Layer2"] is False
        assert metadata.layer_latencies["Layer1"] == 0.5
        assert metadata.total_latency_ms == 1.7
        assert metadata.error_counts["Layer2"] == 2


class TestValidationResultMetadataIntegration:
    """Test ValidationResult integration with ValidationMetadata."""

    def test_validation_result_has_metadata_field(self):
        """Test that ValidationResult has optional metadata field."""
        from src.validation.validation_result import ValidationResult, ValidationMetadata

        # Create result without metadata (backward compatibility)
        result = ValidationResult()
        assert hasattr(result, 'metadata'), "ValidationResult should have metadata attribute"

        # Create result with metadata
        metadata = ValidationMetadata(
            layers_executed=["Layer1"],
            layer_results={"Layer1": True},
            layer_latencies={"Layer1": 0.3},
            total_latency_ms=0.3,
            error_counts={"Layer1": 0},
            timestamp="2025-11-19T10:00:00"
        )

        result_with_metadata = ValidationResult(metadata=metadata)
        assert result_with_metadata.metadata is not None
        assert result_with_metadata.metadata.total_latency_ms == 0.3

    def test_validation_result_metadata_is_optional(self):
        """Test that metadata field is optional for backward compatibility."""
        from src.validation.validation_result import ValidationResult

        # Create result without metadata
        result = ValidationResult()

        # Should work fine
        assert result.is_valid is True
        assert len(result.errors) == 0

        # metadata should be None by default
        assert result.metadata is None


class TestValidateAndFixMethod:
    """Test ValidationGateway.validate_and_fix() method."""

    def test_validate_and_fix_method_exists(self):
        """Test that validate_and_fix method exists in ValidationGateway."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        # Check method exists
        assert hasattr(gateway, 'validate_and_fix'), \
            "ValidationGateway should have validate_and_fix method"
        assert callable(gateway.validate_and_fix), \
            "validate_and_fix should be callable"

    def test_validate_and_fix_returns_validation_result_with_metadata(self):
        """Test that validate_and_fix returns ValidationResult with metadata."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        # Valid YAML dict
        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [{"name": "period", "type": "int", "value": 20}],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        # Call validate_and_fix
        result = gateway.validate_and_fix(yaml_dict)

        # Check return type
        from src.validation.validation_result import ValidationResult
        assert isinstance(result, ValidationResult), \
            "validate_and_fix should return ValidationResult"

        # Check metadata exists
        assert result.metadata is not None, \
            "ValidationResult should have metadata"

        # Check metadata structure
        assert hasattr(result.metadata, 'layers_executed')
        assert hasattr(result.metadata, 'total_latency_ms')

    def test_validate_and_fix_tracks_layer_execution(self):
        """Test that validate_and_fix tracks which layers were executed."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Check layers_executed
        assert len(result.metadata.layers_executed) > 0, \
            "At least one layer should be executed"

        # With Layer 3 enabled, it should execute
        assert "Layer3" in result.metadata.layers_executed, \
            "Layer3 should be in executed layers"

    def test_validate_and_fix_tracks_layer_latency(self):
        """Test that validate_and_fix tracks latency per layer."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        start_time = time.time()
        result = gateway.validate_and_fix(yaml_dict)
        elapsed_ms = (time.time() - start_time) * 1000

        # Check latency tracking
        assert result.metadata.total_latency_ms > 0, \
            "Total latency should be greater than 0"

        # Total latency should be reasonable (< 100ms for simple validation)
        assert result.metadata.total_latency_ms < 100, \
            f"Total latency {result.metadata.total_latency_ms}ms seems too high"

        # Each executed layer should have latency
        for layer in result.metadata.layers_executed:
            assert layer in result.metadata.layer_latencies, \
                f"{layer} should have latency recorded"
            assert result.metadata.layer_latencies[layer] > 0, \
                f"{layer} latency should be > 0"

    def test_validate_and_fix_tracks_error_counts(self):
        """Test that validate_and_fix tracks error counts per layer."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        # Invalid YAML (missing required fields)
        invalid_yaml = {"name": "Incomplete"}

        result = gateway.validate_and_fix(invalid_yaml)

        # Should have errors
        assert not result.is_valid, "Invalid YAML should fail validation"

        # Check error counts
        assert result.metadata.error_counts is not None

        # Layer3 should have errors
        if "Layer3" in result.metadata.error_counts:
            assert result.metadata.error_counts["Layer3"] > 0, \
                "Layer3 should report errors for invalid YAML"

    def test_validate_and_fix_with_layer1_disabled(self):
        """Test validate_and_fix gracefully handles disabled Layer 1."""
        # Disable Layer 1, enable Layer 3
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'false'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Should still return metadata
        assert result.metadata is not None

        # Layer1 should not be in executed layers
        assert "Layer1" not in result.metadata.layers_executed

        # Layer3 should be executed
        assert "Layer3" in result.metadata.layers_executed

    def test_validate_and_fix_timestamp_format(self):
        """Test that validate_and_fix generates ISO format timestamp."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Check timestamp format
        assert result.metadata.timestamp is not None

        # Should be ISO format (YYYY-MM-DDTHH:MM:SS)
        from datetime import datetime
        try:
            datetime.fromisoformat(result.metadata.timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Timestamp {result.metadata.timestamp} is not valid ISO format")


class TestValidateAndFixIntegration:
    """Integration tests for validate_and_fix with real validation layers."""

    def test_validate_and_fix_full_pipeline_valid_yaml(self):
        """Test validate_and_fix with valid YAML through all layers."""
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        # Valid YAML
        yaml_dict = {
            "name": "ROE Momentum Strategy",
            "type": "factor_graph",
            "required_fields": ["close", "volume"],
            "parameters": [
                {"name": "period", "type": "int", "value": 20},
                {"name": "threshold", "type": "float", "value": 0.05}
            ],
            "logic": {
                "entry": "close > close.shift(1) * (1 + threshold)",
                "exit": "close < close.shift(1) * (1 - threshold)"
            }
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Should pass validation
        assert result.is_valid, f"Valid YAML should pass: {result.errors}"

        # Metadata should show all layers executed successfully
        assert result.metadata.layer_results.get("Layer3") is True, \
            "Layer3 should pass for valid YAML"

        # Should have no errors
        assert result.metadata.error_counts.get("Layer3", 0) == 0

    def test_validate_and_fix_performance_requirement(self):
        """Test that validate_and_fix meets <5ms performance requirement per layer.

        NFR-P1: Layer validation completes in <5ms per layer
        """
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Check per-layer latency
        for layer, latency in result.metadata.layer_latencies.items():
            assert latency < 5.0, \
                f"{layer} latency {latency}ms exceeds 5ms requirement (NFR-P1)"

    def test_validate_and_fix_with_code_extraction(self):
        """Test validate_and_fix can also validate extracted strategy code.

        This tests the integration between YAML validation (Layer 3) and
        code validation (Layer 2).
        """
        # Enable all layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER3'] = 'true'

        gateway = ValidationGateway()

        # YAML with embedded code
        yaml_dict = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {
                "entry": "data.get('close') > 100",  # Valid code
                "exit": "data.get('close') < 90"
            }
        }

        result = gateway.validate_and_fix(yaml_dict)

        # Should pass
        assert result.is_valid

        # Metadata should track both YAML and code validation
        # (if code validation is performed)
        assert result.metadata.layers_executed is not None
        assert len(result.metadata.layers_executed) > 0
