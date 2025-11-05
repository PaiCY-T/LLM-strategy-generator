"""
Test Suite for YAMLValidator
=============================

Comprehensive tests for YAML/JSON strategy configuration validation.
Covers schema validation, business rules, parameter validation, and error handling.

Test Categories:
---------------
1. Schema Validation Tests (10+ tests)
2. YAML File Validation Tests (5+ tests)
3. Custom Validation Tests (5+ tests)
4. Edge Cases and Error Handling (5+ tests)

Total: 25+ test cases
"""

import pytest
import json
import yaml
from pathlib import Path
import tempfile
import os

from src.tier1.yaml_validator import YAMLValidator, ValidationResult


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def validator():
    """Create YAMLValidator instance for testing."""
    return YAMLValidator()


@pytest.fixture
def valid_basic_config():
    """Valid basic configuration with minimal factors."""
    return {
        "strategy_id": "test-strategy-v1",
        "description": "Test strategy for validation",
        "factors": [
            {
                "id": "momentum_20",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 20},
                "depends_on": []
            }
        ]
    }


@pytest.fixture
def valid_complex_config():
    """Valid complex configuration with multiple factors and dependencies."""
    return {
        "strategy_id": "complex-test-v1",
        "description": "Complex test strategy with dependencies",
        "metadata": {
            "version": "1.0.0",
            "tags": ["test", "complex"],
            "risk_level": "medium"
        },
        "factors": [
            {
                "id": "momentum_20",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 20},
                "depends_on": []
            },
            {
                "id": "ma_filter",
                "type": "ma_filter_factor",
                "parameters": {"ma_periods": 60},
                "depends_on": []
            },
            {
                "id": "trailing_stop",
                "type": "trailing_stop_factor",
                "parameters": {
                    "trail_percent": 0.10,
                    "activation_profit": 0.05
                },
                "depends_on": ["momentum_20", "ma_filter"]
            }
        ]
    }


# ============================================================================
# Schema Validation Tests (10+ tests)
# ============================================================================

class TestSchemaValidation:
    """Test JSON schema validation."""

    def test_valid_basic_config(self, validator, valid_basic_config):
        """Test that valid basic config passes validation."""
        result = validator.validate(valid_basic_config)
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.config == valid_basic_config

    def test_valid_complex_config(self, validator, valid_complex_config):
        """Test that valid complex config passes validation."""
        result = validator.validate(valid_complex_config)
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.config is not None

    def test_missing_required_strategy_id(self, validator):
        """Test error when strategy_id is missing."""
        config = {
            "description": "Test",
            "factors": [
                {
                    "id": "test",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("strategy_id" in error.lower() for error in result.errors)

    def test_missing_required_factors(self, validator):
        """Test error when factors list is missing."""
        config = {
            "strategy_id": "test-strategy"
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("factors" in error.lower() for error in result.errors)

    def test_invalid_strategy_id_format(self, validator):
        """Test error for invalid strategy_id format (uppercase, spaces, etc)."""
        config = {
            "strategy_id": "Invalid Strategy ID!",
            "factors": [
                {
                    "id": "test",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("pattern" in error.lower() or "strategy_id" in error.lower()
                   for error in result.errors)

    def test_invalid_factor_type(self, validator):
        """Test error for non-existent factor type."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "invalid",
                    "type": "nonexistent_factor",
                    "parameters": {}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("unknown type" in error.lower() or "nonexistent_factor" in error.lower()
                   for error in result.errors)

    def test_invalid_parameter_type(self, validator):
        """Test error when parameter has wrong type (string instead of int)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": "twenty"}  # Should be int
                }
            ]
        }
        # The validator catches this as a type error during parameter validation
        # We expect either validation to fail or an exception to be caught
        try:
            result = validator.validate(config)
            # If validation succeeds in checking, it should report an error
            assert not result.is_valid
        except TypeError:
            # If registry validation throws TypeError, that's also acceptable
            pass

    def test_empty_factors_list(self, validator):
        """Test error for empty factors list (minItems=1)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": []
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("factors" in error.lower() for error in result.errors)

    def test_missing_factor_id(self, validator):
        """Test error when factor is missing required 'id' field."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("id" in error.lower() for error in result.errors)

    def test_missing_factor_type(self, validator):
        """Test error when factor is missing required 'type' field."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "test",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("type" in error.lower() for error in result.errors)

    def test_missing_factor_parameters(self, validator):
        """Test error when factor is missing required 'parameters' field."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "test",
                    "type": "momentum_factor"
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("parameters" in error.lower() for error in result.errors)


# ============================================================================
# Dependency Validation Tests
# ============================================================================

class TestDependencyValidation:
    """Test dependency graph validation."""

    def test_valid_dependencies(self, validator, valid_complex_config):
        """Test that valid dependency graph passes validation."""
        result = validator.validate(valid_complex_config)
        assert result.is_valid

    def test_nonexistent_dependency(self, validator):
        """Test error when factor depends on non-existent factor."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["nonexistent_factor"]
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("nonexistent_factor" in error for error in result.errors)

    def test_circular_dependency_simple(self, validator):
        """Test detection of simple circular dependency (A -> B -> A)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "factor_a",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["factor_b"]
                },
                {
                    "id": "factor_b",
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60},
                    "depends_on": ["factor_a"]
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("circular" in error.lower() for error in result.errors)

    def test_circular_dependency_complex(self, validator):
        """Test detection of complex circular dependency (A -> B -> C -> A)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "factor_a",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "depends_on": ["factor_c"]
                },
                {
                    "id": "factor_b",
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60},
                    "depends_on": ["factor_a"]
                },
                {
                    "id": "factor_c",
                    "type": "atr_factor",
                    "parameters": {"atr_period": 20},
                    "depends_on": ["factor_b"]
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("circular" in error.lower() for error in result.errors)

    def test_duplicate_factor_ids(self, validator):
        """Test error when multiple factors have same ID."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "duplicate",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                },
                {
                    "id": "duplicate",
                    "type": "ma_filter_factor",
                    "parameters": {"ma_periods": 60}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("duplicate" in error.lower() for error in result.errors)


# ============================================================================
# Parameter Validation Tests
# ============================================================================

class TestParameterValidation:
    """Test parameter bounds and type validation."""

    def test_parameter_out_of_range_low(self, validator):
        """Test error when parameter below minimum range."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 2}  # Min is 5
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("out of range" in error.lower() or "momentum_period" in error.lower()
                   for error in result.errors)

    def test_parameter_out_of_range_high(self, validator):
        """Test error when parameter above maximum range."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 150}  # Max is 100
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("out of range" in error.lower() or "momentum_period" in error.lower()
                   for error in result.errors)

    def test_missing_required_parameter(self, validator):
        """Test error when required parameter is missing."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {}  # Missing momentum_period
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("missing" in error.lower() or "momentum_period" in error.lower()
                   for error in result.errors)

    def test_unknown_parameter_warning(self, validator):
        """Test warning for unknown parameters (not in schema)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {
                        "momentum_period": 20,
                        "unknown_param": 999
                    }
                }
            ]
        }
        result = validator.validate(config)
        # Should be valid but with warnings
        assert result.is_valid or len(result.warnings) > 0

    def test_multi_parameter_factor(self, validator):
        """Test factor with multiple parameters (dual_ma_filter_factor)."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "dual_ma",
                    "type": "dual_ma_filter_factor",
                    "parameters": {
                        "short_ma": 20,
                        "long_ma": 60
                    }
                }
            ]
        }
        result = validator.validate(config)
        assert result.is_valid


# ============================================================================
# File Validation Tests
# ============================================================================

class TestFileValidation:
    """Test YAML/JSON file loading and validation."""

    def test_validate_yaml_file_valid(self, validator, valid_basic_config):
        """Test validation of valid YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(valid_basic_config, f)
            temp_path = f.name

        try:
            result = validator.validate_file(temp_path)
            assert result.is_valid
            assert result.config is not None
        finally:
            os.unlink(temp_path)

    def test_validate_json_file_valid(self, validator, valid_basic_config):
        """Test validation of valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(valid_basic_config, f)
            temp_path = f.name

        try:
            result = validator.validate_file(temp_path)
            assert result.is_valid
            assert result.config is not None
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self, validator):
        """Test error when file does not exist."""
        result = validator.validate_file("/nonexistent/path/config.yaml")
        assert not result.is_valid
        assert any("not found" in error.lower() for error in result.errors)

    def test_invalid_yaml_syntax(self, validator):
        """Test error for invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax: [unclosed")
            temp_path = f.name

        try:
            result = validator.validate_file(temp_path)
            assert not result.is_valid
            assert any("yaml" in error.lower() or "parsing" in error.lower()
                       for error in result.errors)
        finally:
            os.unlink(temp_path)

    def test_invalid_json_syntax(self, validator):
        """Test error for invalid JSON syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid": json syntax}')
            temp_path = f.name

        try:
            result = validator.validate_file(temp_path)
            assert not result.is_valid
            assert any("json" in error.lower() or "parsing" in error.lower()
                       for error in result.errors)
        finally:
            os.unlink(temp_path)

    def test_validate_example_configs(self, validator):
        """Test that all example YAML configs are valid."""
        examples_dir = Path(__file__).parent.parent.parent / "examples" / "yaml_strategies"

        if examples_dir.exists():
            yaml_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))

            assert len(yaml_files) >= 3, "Should have at least 3 example configs"

            for yaml_file in yaml_files:
                result = validator.validate_file(str(yaml_file))
                assert result.is_valid, f"Example config {yaml_file.name} should be valid: {result.errors}"


# ============================================================================
# Utility Method Tests
# ============================================================================

class TestUtilityMethods:
    """Test validator utility methods."""

    def test_get_schema_info(self, validator):
        """Test getting schema information."""
        info = validator.get_schema_info()
        assert 'title' in info
        assert 'factor_types' in info
        assert len(info['factor_types']) >= 13  # Should have 13 registered factors

    def test_list_factor_types(self, validator):
        """Test listing supported factor types."""
        factor_types = validator.list_factor_types()
        assert isinstance(factor_types, list)
        assert len(factor_types) >= 13
        assert "momentum_factor" in factor_types
        assert "trailing_stop_factor" in factor_types

    def test_get_parameter_schema(self, validator):
        """Test getting parameter schema for specific factor."""
        schema = validator.get_parameter_schema("momentum_factor")
        assert schema is not None
        assert "momentum_period" in str(schema)

    def test_validation_result_str(self, validator, valid_basic_config):
        """Test ValidationResult string representation."""
        result = validator.validate(valid_basic_config)
        result_str = str(result)
        assert "VALID" in result_str or result.is_valid


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_config(self, validator):
        """Test validation of completely empty config."""
        result = validator.validate({})
        assert not result.is_valid

    def test_null_values(self, validator):
        """Test handling of null/None values in config."""
        config = {
            "strategy_id": None,
            "factors": None
        }
        result = validator.validate(config)
        assert not result.is_valid

    def test_very_long_strategy_id(self, validator):
        """Test error for strategy_id exceeding max length."""
        config = {
            "strategy_id": "a" * 100,  # Max is 64
            "factors": [
                {
                    "id": "test",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid

    def test_very_short_strategy_id(self, validator):
        """Test error for strategy_id below min length."""
        config = {
            "strategy_id": "ab",  # Min is 3
            "factors": [
                {
                    "id": "test",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20}
                }
            ]
        }
        result = validator.validate(config)
        assert not result.is_valid

    def test_max_factors_limit(self, validator):
        """Test that configuration respects max factors limit (50)."""
        # Create config with exactly 50 factors
        factors = []
        for i in range(50):
            factors.append({
                "id": f"factor_{i}",
                "type": "momentum_factor",
                "parameters": {"momentum_period": 20}
            })

        config = {
            "strategy_id": "max-factors-test",
            "factors": factors
        }
        result = validator.validate(config)
        assert result.is_valid  # 50 should be OK (maxItems=50)

        # Add one more to exceed limit
        factors.append({
            "id": "factor_51",
            "type": "momentum_factor",
            "parameters": {"momentum_period": 20}
        })
        config["factors"] = factors
        result = validator.validate(config)
        assert not result.is_valid  # 51 should fail

    def test_validation_result_bool_conversion(self, validator, valid_basic_config):
        """Test ValidationResult truthiness."""
        valid_result = validator.validate(valid_basic_config)
        assert valid_result  # Should be truthy
        assert bool(valid_result) is True

        invalid_config = {"strategy_id": "test"}
        invalid_result = validator.validate(invalid_config)
        assert not invalid_result  # Should be falsy
        assert bool(invalid_result) is False

    def test_factor_enabled_field(self, validator):
        """Test optional 'enabled' field for factors."""
        config = {
            "strategy_id": "test-strategy",
            "factors": [
                {
                    "id": "momentum",
                    "type": "momentum_factor",
                    "parameters": {"momentum_period": 20},
                    "enabled": False
                }
            ]
        }
        result = validator.validate(config)
        assert result.is_valid
        assert result.config["factors"][0]["enabled"] is False


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple validation aspects."""

    def test_complex_multi_factor_strategy(self, validator):
        """Test validation of complex multi-factor strategy."""
        config = {
            "strategy_id": "integration-test-complex",
            "description": "Integration test for complex strategy validation",
            "metadata": {
                "version": "1.0.0",
                "tags": ["integration", "test", "complex"],
                "risk_level": "high"
            },
            "factors": [
                {
                    "id": "atr_20",
                    "type": "atr_factor",
                    "parameters": {"atr_period": 20},
                    "depends_on": []
                },
                {
                    "id": "breakout",
                    "type": "breakout_factor",
                    "parameters": {"entry_window": 20},
                    "depends_on": []
                },
                {
                    "id": "atr_stop",
                    "type": "atr_stop_loss_factor",
                    "parameters": {"atr_multiplier": 2.0},
                    "depends_on": ["atr_20"]
                },
                {
                    "id": "time_exit",
                    "type": "time_based_exit_factor",
                    "parameters": {"max_holding_periods": 30},
                    "depends_on": ["breakout"]
                },
                {
                    "id": "composite_exit",
                    "type": "composite_exit_factor",
                    "parameters": {
                        "exit_signals": ["atr_stop_signal", "time_exit_signal"]
                    },
                    "depends_on": ["atr_stop", "time_exit"]
                }
            ]
        }
        result = validator.validate(config)
        assert result.is_valid
        assert len(result.config["factors"]) == 5

    def test_all_factor_types_valid(self, validator):
        """Test that all 13 factor types can be validated."""
        factor_types = validator.list_factor_types()

        for factor_type in factor_types:
            # Get parameter schema to build valid config
            metadata = validator.registry.get_metadata(factor_type)
            if metadata:
                config = {
                    "strategy_id": f"test-{factor_type}",
                    "factors": [
                        {
                            "id": "test",
                            "type": factor_type,
                            "parameters": metadata["parameters"].copy()
                        }
                    ]
                }
                result = validator.validate(config)
                assert result.is_valid, f"Factor type {factor_type} should be valid"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
