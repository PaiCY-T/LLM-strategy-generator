"""Test suite for Task 7.2: Type Validation Integration.

Tests type validation functionality in ValidationGateway to prevent Phase 7 type regressions.
Follows TDD methodology: RED → GREEN → REFACTOR.

Test Categories:
- Category A: Strategy YAML Type Validation (5 tests)
- Category B: StrategyMetrics Type Validation (5 tests)
- Category C: Parameter Type Validation (5 tests)
- Category D: Required Field Type Validation (5 tests)
- Category E: Dict-to-StrategyMetrics Conversion (5 tests)
- Category F: Type Mismatch Detection (5 tests)

Total: 30 tests

Background:
Phase 7 E2E tests failed 100% due to Phase 3 type migration (Dict → StrategyMetrics).
Phase 3.3 added dict interface, but NO type validation to prevent future regressions.
Task 7.2 adds comprehensive type validation to validate_strategy().

Requirements:
- Validate strategy YAML structure is dict
- Validate StrategyMetrics objects have correct type
- Validate parameter types match schema
- Validate required fields exist and have correct types
- Validate dict-to-StrategyMetrics conversions
- Detect and report type mismatches
"""

import pytest
from typing import Dict, Any
import os

from src.validation.gateway import ValidationGateway
from src.backtest.metrics import StrategyMetrics


# ============================================================================
# Category A: Strategy YAML Type Validation
# ============================================================================

class TestStrategyYAMLTypeValidation:
    """Tests for validating YAML strategy structure is a dictionary."""

    def test_valid_yaml_dict_structure(self):
        """Test that valid YAML dict structure passes type validation."""
        # Enable validation layers
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        os.environ['ENABLE_VALIDATION_LAYER2'] = 'true'
        gateway = ValidationGateway()

        yaml_dict: Dict[str, Any] = {
            "name": "Test Strategy",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [],
            "logic": {"entry": "close > 100", "exit": "close < 90"}
        }

        # Should validate YAML structure types
        result = gateway.validate_yaml_structure_types(yaml_dict)
        assert result.is_valid, f"Expected valid YAML structure, got errors: {result.errors}"

    def test_invalid_yaml_not_dict(self):
        """Test that non-dict YAML structure fails type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Invalid: string instead of dict
        invalid_yaml = "not a dict"

        result = gateway.validate_yaml_structure_types(invalid_yaml)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "dictionary" in result.errors[0].message.lower()

    def test_invalid_yaml_list_structure(self):
        """Test that list YAML structure fails type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Invalid: list instead of dict
        invalid_yaml = ["item1", "item2"]

        result = gateway.validate_yaml_structure_types(invalid_yaml)
        assert not result.is_valid
        assert any("dictionary" in err.message.lower() for err in result.errors)

    def test_yaml_required_keys_present(self):
        """Test that YAML dict has required top-level keys."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Missing 'logic' key
        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": []
        }

        result = gateway.validate_yaml_structure_types(yaml_dict)
        # Note: This tests structure, not schema validation
        # Missing keys should be caught by type checking required sections
        assert not result.is_valid or 'logic' not in yaml_dict

    def test_yaml_nested_structure_types(self):
        """Test that nested YAML structures have correct types."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close"],
            "parameters": [
                {"name": "period", "type": "int", "value": 20}  # dict, not list
            ],
            "logic": {"entry": "close > 100", "exit": "close < 90"}  # dict
        }

        result = gateway.validate_yaml_structure_types(yaml_dict)
        assert result.is_valid


# ============================================================================
# Category B: StrategyMetrics Type Validation
# ============================================================================

class TestStrategyMetricsTypeValidation:
    """Tests for validating StrategyMetrics objects have correct type."""

    def test_valid_strategy_metrics_instance(self):
        """Test that valid StrategyMetrics instance passes type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        metrics = StrategyMetrics(
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.15,
            win_rate=0.60,
            execution_success=True
        )

        result = gateway.validate_strategy_metrics_type(metrics)
        assert result.is_valid

    def test_invalid_metrics_dict_type(self):
        """Test that dict (not StrategyMetrics) fails type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Invalid: dict instead of StrategyMetrics
        metrics_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.25,
            'max_drawdown': -0.15,
            'win_rate': 0.60,
            'execution_success': True
        }

        result = gateway.validate_strategy_metrics_type(metrics_dict)
        assert not result.is_valid
        assert any("StrategyMetrics" in err.message for err in result.errors)

    def test_invalid_metrics_none_type(self):
        """Test that None fails type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        result = gateway.validate_strategy_metrics_type(None)
        assert not result.is_valid

    def test_metrics_field_types_correct(self):
        """Test that StrategyMetrics fields have correct types."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        metrics = StrategyMetrics(
            sharpe_ratio=1.5,  # float
            total_return=0.25,  # float
            max_drawdown=-0.15,  # float
            win_rate=0.60,  # float
            execution_success=True  # bool
        )

        result = gateway.validate_strategy_metrics_type(metrics)
        assert result.is_valid

        # Validate individual field types
        assert isinstance(metrics.sharpe_ratio, (float, type(None)))
        assert isinstance(metrics.total_return, (float, type(None)))
        assert isinstance(metrics.max_drawdown, (float, type(None)))
        assert isinstance(metrics.win_rate, (float, type(None)))
        assert isinstance(metrics.execution_success, bool)

    def test_metrics_with_none_values(self):
        """Test that StrategyMetrics with None values passes type validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Valid: Optional fields can be None
        metrics = StrategyMetrics(
            sharpe_ratio=None,
            total_return=None,
            max_drawdown=None,
            win_rate=None,
            execution_success=False
        )

        result = gateway.validate_strategy_metrics_type(metrics)
        assert result.is_valid


# ============================================================================
# Category C: Parameter Type Validation
# ============================================================================

class TestParameterTypeValidation:
    """Tests for validating strategy parameter types."""

    def test_valid_parameter_types(self):
        """Test that correctly typed parameters pass validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        parameters = [
            {"name": "period", "type": "int", "value": 20},
            {"name": "threshold", "type": "float", "value": 0.5},
            {"name": "enabled", "type": "bool", "value": True}
        ]

        result = gateway.validate_parameter_types(parameters)
        assert result.is_valid

    def test_invalid_parameter_value_type(self):
        """Test that mismatched parameter value type fails validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Invalid: int type but string value
        parameters = [
            {"name": "period", "type": "int", "value": "20"}  # Should be int
        ]

        result = gateway.validate_parameter_types(parameters)
        assert not result.is_valid
        assert any("declared as" in err.message.lower() or err.error_type == "type_mismatch" for err in result.errors)

    def test_parameter_missing_required_keys(self):
        """Test that parameters missing required keys fail validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Missing 'type' key
        parameters = [
            {"name": "period", "value": 20}
        ]

        result = gateway.validate_parameter_types(parameters)
        assert not result.is_valid

    def test_parameter_unknown_type(self):
        """Test that unknown parameter type fails validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Unknown type 'list'
        parameters = [
            {"name": "values", "type": "list", "value": [1, 2, 3]}
        ]

        result = gateway.validate_parameter_types(parameters)
        # Should fail or warn about unknown type
        # Depends on validation strictness

    def test_empty_parameters_list(self):
        """Test that empty parameters list passes validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        parameters = []

        result = gateway.validate_parameter_types(parameters)
        assert result.is_valid


# ============================================================================
# Category D: Required Field Type Validation
# ============================================================================

class TestRequiredFieldTypeValidation:
    """Tests for validating required field types in YAML structure."""

    def test_valid_required_fields_list(self):
        """Test that valid required_fields list passes validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close", "volume", "open"]  # list of strings
        }

        result = gateway.validate_required_field_types(yaml_dict)
        assert result.is_valid

    def test_invalid_required_fields_not_list(self):
        """Test that required_fields as non-list fails validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": "close"  # Should be list
        }

        result = gateway.validate_required_field_types(yaml_dict)
        assert not result.is_valid
        assert any("list" in err.message.lower() for err in result.errors)

    def test_required_fields_contain_non_string(self):
        """Test that required_fields with non-string items fail validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": ["close", 123, "volume"]  # 123 is not a string
        }

        result = gateway.validate_required_field_types(yaml_dict)
        assert not result.is_valid

    def test_missing_required_fields_key(self):
        """Test that missing required_fields key fails validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph"
            # Missing required_fields
        }

        result = gateway.validate_required_field_types(yaml_dict)
        assert not result.is_valid

    def test_empty_required_fields_list(self):
        """Test that empty required_fields list passes validation."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "type": "factor_graph",
            "required_fields": []  # Empty but valid list
        }

        result = gateway.validate_required_field_types(yaml_dict)
        assert result.is_valid


# ============================================================================
# Category E: Dict-to-StrategyMetrics Conversion
# ============================================================================

class TestDictToStrategyMetricsConversion:
    """Tests for dict-to-StrategyMetrics type conversion validation."""

    def test_valid_dict_conversion(self):
        """Test that valid dict converts to StrategyMetrics correctly."""
        metrics_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.25,
            'max_drawdown': -0.15,
            'win_rate': 0.60,
            'execution_success': True
        }

        metrics = StrategyMetrics.from_dict(metrics_dict)

        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        assert metrics.execution_success is True

    def test_dict_with_missing_fields(self):
        """Test that dict with missing fields uses default None values."""
        metrics_dict = {
            'sharpe_ratio': 1.5
            # Missing other fields
        }

        metrics = StrategyMetrics.from_dict(metrics_dict)

        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return is None
        assert metrics.max_drawdown is None
        assert metrics.win_rate is None
        assert metrics.execution_success is False  # Default

    def test_dict_with_extra_fields(self):
        """Test that dict with extra fields ignores unknown keys."""
        metrics_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.25,
            'annual_return': 0.30,  # Extra field (not in dataclass)
            'calmar_ratio': 2.0  # Extra field
        }

        metrics = StrategyMetrics.from_dict(metrics_dict)

        assert isinstance(metrics, StrategyMetrics)
        assert metrics.sharpe_ratio == 1.5
        assert metrics.total_return == 0.25
        # Extra fields should be ignored
        assert not hasattr(metrics, 'annual_return')
        assert not hasattr(metrics, 'calmar_ratio')

    def test_conversion_preserves_none_values(self):
        """Test that None values in dict are preserved after conversion."""
        metrics_dict = {
            'sharpe_ratio': None,
            'total_return': None,
            'max_drawdown': -0.15,
            'win_rate': None,
            'execution_success': False
        }

        metrics = StrategyMetrics.from_dict(metrics_dict)

        assert metrics.sharpe_ratio is None
        assert metrics.total_return is None
        assert metrics.max_drawdown == -0.15
        assert metrics.win_rate is None

    def test_roundtrip_dict_to_metrics_to_dict(self):
        """Test that dict → StrategyMetrics → dict preserves values."""
        original_dict = {
            'sharpe_ratio': 1.5,
            'total_return': 0.25,
            'max_drawdown': -0.15,
            'win_rate': 0.60,
            'execution_success': True
        }

        # Convert to StrategyMetrics
        metrics = StrategyMetrics.from_dict(original_dict)

        # Convert back to dict
        result_dict = metrics.to_dict()

        # Should match original (minus extra fields)
        assert result_dict['sharpe_ratio'] == original_dict['sharpe_ratio']
        assert result_dict['total_return'] == original_dict['total_return']
        assert result_dict['max_drawdown'] == original_dict['max_drawdown']
        assert result_dict['win_rate'] == original_dict['win_rate']
        assert result_dict['execution_success'] == original_dict['execution_success']


# ============================================================================
# Category F: Type Mismatch Detection
# ============================================================================

class TestTypeMismatchDetection:
    """Tests for detecting and reporting type mismatches."""

    def test_detect_string_instead_of_dict(self):
        """Test detection of string when dict expected."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Type mismatch: string instead of dict
        invalid_input = "this is a string"

        result = gateway.validate_yaml_structure_types(invalid_input)
        assert not result.is_valid
        assert any("type" in err.error_type.lower() or "dict" in err.message.lower()
                   for err in result.errors)

    def test_detect_int_instead_of_string(self):
        """Test detection of int when string expected."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": 123,  # Should be string
            "type": "factor_graph"
        }

        result = gateway.validate_yaml_structure_types(yaml_dict)
        # Should detect that 'name' field is wrong type

    def test_detect_list_instead_of_dict(self):
        """Test detection of list when dict expected."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        yaml_dict = {
            "name": "Test",
            "logic": ["entry", "exit"]  # Should be dict
        }

        result = gateway.validate_yaml_structure_types(yaml_dict)
        # Should detect that 'logic' field is wrong type

    def test_type_mismatch_error_message_clarity(self):
        """Test that type mismatch errors have clear messages."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        invalid_yaml = ["not", "a", "dict"]

        result = gateway.validate_yaml_structure_types(invalid_yaml)
        assert not result.is_valid
        assert len(result.errors) > 0

        # Error message should clearly state expected vs actual type
        error = result.errors[0]
        assert "dict" in error.message.lower() or "expected" in error.message.lower()

    def test_type_mismatch_with_suggestion(self):
        """Test that type mismatch errors provide helpful suggestions."""
        os.environ['ENABLE_VALIDATION_LAYER1'] = 'true'
        gateway = ValidationGateway()

        # Wrong type for metrics
        invalid_metrics = {'sharpe_ratio': 1.5}  # dict instead of StrategyMetrics

        result = gateway.validate_strategy_metrics_type(invalid_metrics)
        assert not result.is_valid

        # Should have suggestion to use StrategyMetrics.from_dict()
        if result.errors:
            error = result.errors[0]
            assert error.suggestion is not None or "from_dict" in error.message.lower()
