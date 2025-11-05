"""
Test Suite for YAMLSchemaValidator

Tests validation logic, error messages, and edge cases.
Target: >95% validation success on conforming specs.

Task 2 of structured-innovation-mvp spec.
"""

import json
import pytest
from pathlib import Path
import yaml
import tempfile
import os

from src.generators.yaml_schema_validator import YAMLSchemaValidator


# Fixtures
@pytest.fixture
def validator():
    """Create a YAMLSchemaValidator instance."""
    return YAMLSchemaValidator()


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def examples_dir(project_root):
    """Get YAML examples directory."""
    return project_root / "examples" / "yaml_strategies"


@pytest.fixture
def valid_momentum_spec():
    """Valid momentum strategy spec."""
    return {
        "metadata": {
            "name": "Test Momentum Strategy",
            "description": "A simple test momentum strategy for validation",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M",
            "version": "1.0.0"
        },
        "indicators": {
            "technical_indicators": [
                {
                    "name": "rsi_14",
                    "type": "RSI",
                    "period": 14,
                    "source": "data.get('RSI_14')"
                }
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {
                    "condition": "rsi_14 > 30",
                    "description": "RSI not oversold"
                }
            ]
        }
    }


@pytest.fixture
def valid_factor_combo_spec():
    """Valid factor combination strategy spec."""
    return {
        "metadata": {
            "name": "Quality Factor Strategy",
            "description": "Select high ROE stocks with momentum",
            "strategy_type": "factor_combination",
            "rebalancing_frequency": "M",
            "version": "1.0.0",
            "tags": ["quality", "momentum"],
            "risk_level": "medium"
        },
        "indicators": {
            "fundamental_factors": [
                {
                    "name": "roe",
                    "field": "ROE",
                    "source": "data.get('ROE')"
                },
                {
                    "name": "revenue_growth",
                    "field": "revenue_growth",
                    "source": "data.get('revenue_growth')"
                }
            ],
            "custom_calculations": [
                {
                    "name": "quality_score",
                    "expression": "roe * (1 + revenue_growth)",
                    "description": "Combined quality score"
                }
            ]
        },
        "entry_conditions": {
            "ranking_rules": [
                {
                    "field": "quality_score",
                    "method": "top_percent",
                    "value": 20,
                    "ascending": False
                }
            ]
        },
        "position_sizing": {
            "method": "equal_weight",
            "max_positions": 20
        }
    }


# Test Basic Functionality
class TestBasicValidation:
    """Test basic validation functionality."""

    def test_validator_initialization(self, validator):
        """Test validator initializes correctly."""
        assert validator is not None
        assert validator._schema is not None
        assert validator._validator is not None
        assert validator.schema_path.exists()

    def test_schema_loaded(self, validator):
        """Test schema is loaded correctly."""
        schema = validator.schema
        assert schema is not None
        assert "$schema" in schema
        assert "properties" in schema
        assert "metadata" in schema["properties"]
        assert "indicators" in schema["properties"]
        assert "entry_conditions" in schema["properties"]

    def test_schema_version(self, validator):
        """Test schema version is accessible."""
        version = validator.schema_version
        assert version == "1.0.0"

    def test_valid_spec_passes(self, validator, valid_momentum_spec):
        """Test that a valid spec passes validation."""
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_spec_type_fails(self, validator):
        """Test that non-dict spec fails."""
        is_valid, errors = validator.validate("not a dict")
        assert is_valid is False
        assert len(errors) > 0
        assert "must be a dictionary" in errors[0]


# Test Required Fields Validation
class TestRequiredFields:
    """Test validation of required fields."""

    def test_missing_metadata(self, validator):
        """Test error when metadata is missing."""
        spec = {
            "indicators": {"technical_indicators": []},
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid is False
        assert any("metadata" in err.lower() for err in errors)

    def test_missing_indicators(self, validator):
        """Test error when indicators is missing."""
        spec = {
            "metadata": {
                "name": "Test",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid is False
        assert any("indicators" in err.lower() for err in errors)

    def test_missing_entry_conditions(self, validator):
        """Test error when entry_conditions is missing."""
        spec = {
            "metadata": {
                "name": "Test",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {"technical_indicators": []}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid is False
        assert any("entry_conditions" in err.lower() for err in errors)

    def test_missing_metadata_name(self, validator, valid_momentum_spec):
        """Test error when metadata.name is missing."""
        del valid_momentum_spec["metadata"]["name"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("name" in err.lower() for err in errors)

    def test_missing_strategy_type(self, validator, valid_momentum_spec):
        """Test error when metadata.strategy_type is missing."""
        del valid_momentum_spec["metadata"]["strategy_type"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("strategy_type" in err.lower() for err in errors)

    def test_missing_rebalancing_frequency(self, validator, valid_momentum_spec):
        """Test error when metadata.rebalancing_frequency is missing."""
        del valid_momentum_spec["metadata"]["rebalancing_frequency"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("rebalancing_frequency" in err.lower() for err in errors)


# Test Field Type Validation
class TestFieldTypes:
    """Test validation of field types."""

    def test_invalid_strategy_type(self, validator, valid_momentum_spec):
        """Test error for invalid strategy_type enum value."""
        valid_momentum_spec["metadata"]["strategy_type"] = "invalid_type"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("strategy_type" in err for err in errors)
        assert any("allowed values" in err.lower() for err in errors)

    def test_invalid_rebalancing_frequency(self, validator, valid_momentum_spec):
        """Test error for invalid rebalancing_frequency."""
        valid_momentum_spec["metadata"]["rebalancing_frequency"] = "DAILY"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("rebalancing_frequency" in err for err in errors)

    def test_invalid_indicator_type(self, validator, valid_momentum_spec):
        """Test error for invalid technical indicator type."""
        valid_momentum_spec["indicators"]["technical_indicators"][0]["type"] = "INVALID"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("type" in err for err in errors)

    def test_invalid_name_pattern(self, validator, valid_momentum_spec):
        """Test error for invalid indicator name pattern."""
        valid_momentum_spec["indicators"]["technical_indicators"][0]["name"] = "invalid-name!"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("pattern" in err.lower() for err in errors)


# Test Indicator Validation
class TestIndicatorValidation:
    """Test validation of indicators section."""

    def test_valid_technical_indicator(self, validator, valid_momentum_spec):
        """Test valid technical indicator passes."""
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True

    def test_technical_indicator_missing_name(self, validator, valid_momentum_spec):
        """Test error when indicator name is missing."""
        del valid_momentum_spec["indicators"]["technical_indicators"][0]["name"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("name" in err.lower() for err in errors)

    def test_technical_indicator_missing_type(self, validator, valid_momentum_spec):
        """Test error when indicator type is missing."""
        del valid_momentum_spec["indicators"]["technical_indicators"][0]["type"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("type" in err.lower() for err in errors)

    def test_period_out_of_range(self, validator, valid_momentum_spec):
        """Test error for period outside valid range."""
        valid_momentum_spec["indicators"]["technical_indicators"][0]["period"] = 500
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("period" in err.lower() for err in errors)

    def test_fundamental_factor_valid(self, validator, valid_factor_combo_spec):
        """Test valid fundamental factor passes."""
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is True

    def test_fundamental_factor_invalid_field(self, validator, valid_factor_combo_spec):
        """Test error for invalid fundamental field type."""
        valid_factor_combo_spec["indicators"]["fundamental_factors"][0]["field"] = "INVALID"
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is False


# Test Entry Conditions Validation
class TestEntryConditionsValidation:
    """Test validation of entry conditions."""

    def test_threshold_rule_valid(self, validator, valid_momentum_spec):
        """Test valid threshold rule passes."""
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True

    def test_ranking_rule_valid(self, validator, valid_factor_combo_spec):
        """Test valid ranking rule passes."""
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is True

    def test_invalid_ranking_method(self, validator, valid_factor_combo_spec):
        """Test error for invalid ranking method."""
        valid_factor_combo_spec["entry_conditions"]["ranking_rules"][0]["method"] = "invalid"
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is False
        assert any("method" in err for err in errors)

    def test_invalid_logical_operator(self, validator, valid_momentum_spec):
        """Test error for invalid logical operator."""
        valid_momentum_spec["entry_conditions"]["logical_operator"] = "XOR"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False


# Test Exit Conditions Validation
class TestExitConditionsValidation:
    """Test validation of exit conditions (optional section)."""

    def test_exit_conditions_optional(self, validator, valid_momentum_spec):
        """Test that exit_conditions is optional."""
        # Remove exit_conditions if present
        if "exit_conditions" in valid_momentum_spec:
            del valid_momentum_spec["exit_conditions"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True

    def test_stop_loss_valid(self, validator, valid_momentum_spec):
        """Test valid stop_loss_pct passes."""
        valid_momentum_spec["exit_conditions"] = {"stop_loss_pct": 0.10}
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True

    def test_stop_loss_out_of_range(self, validator, valid_momentum_spec):
        """Test error for stop_loss_pct out of range."""
        valid_momentum_spec["exit_conditions"] = {"stop_loss_pct": 0.60}
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False


# Test Position Sizing Validation
class TestPositionSizingValidation:
    """Test validation of position sizing (optional section)."""

    def test_position_sizing_optional(self, validator, valid_momentum_spec):
        """Test that position_sizing is optional."""
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is True

    def test_position_sizing_requires_method(self, validator, valid_momentum_spec):
        """Test that position_sizing requires method field."""
        valid_momentum_spec["position_sizing"] = {"max_positions": 20}
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("method" in err.lower() for err in errors)

    def test_valid_position_sizing(self, validator, valid_factor_combo_spec):
        """Test valid position sizing passes."""
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is True

    def test_invalid_position_sizing_method(self, validator, valid_factor_combo_spec):
        """Test error for invalid position sizing method."""
        valid_factor_combo_spec["position_sizing"]["method"] = "invalid"
        is_valid, errors = validator.validate(valid_factor_combo_spec)
        assert is_valid is False


# Test File Loading
class TestFileLoading:
    """Test loading and validating YAML files."""

    def test_load_valid_yaml_file(self, validator, examples_dir):
        """Test loading valid YAML file from examples."""
        yaml_file = examples_dir / "test_valid_momentum.yaml"
        if yaml_file.exists():
            is_valid, errors = validator.load_and_validate(str(yaml_file))
            assert is_valid is True
            assert len(errors) == 0

    def test_load_invalid_yaml_file(self, validator, examples_dir):
        """Test loading invalid YAML file produces errors."""
        yaml_file = examples_dir / "test_invalid_missing_required.yaml"
        if yaml_file.exists():
            is_valid, errors = validator.load_and_validate(str(yaml_file))
            assert is_valid is False
            assert len(errors) > 0

    def test_load_nonexistent_file(self, validator):
        """Test error when file doesn't exist."""
        is_valid, errors = validator.load_and_validate("nonexistent.yaml")
        assert is_valid is False
        assert any("not found" in err.lower() for err in errors)

    def test_load_malformed_yaml(self, validator):
        """Test error for malformed YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: syntax:\n  - bad\n  indentation")
            temp_path = f.name

        try:
            is_valid, errors = validator.load_and_validate(temp_path)
            assert is_valid is False
            assert any("parsing error" in err.lower() for err in errors)
        finally:
            os.unlink(temp_path)


# Test Error Message Format
class TestErrorMessages:
    """Test error message formatting and clarity."""

    def test_error_message_includes_field_path(self, validator, valid_momentum_spec):
        """Test that error messages include field paths."""
        del valid_momentum_spec["metadata"]["name"]
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert len(errors) > 0
        # Should mention 'name' and possibly 'metadata'
        assert any("name" in err.lower() for err in errors)

    def test_error_message_clear_for_enum(self, validator, valid_momentum_spec):
        """Test clear error for invalid enum value."""
        valid_momentum_spec["metadata"]["strategy_type"] = "bad_value"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        # Should mention allowed values
        assert any("allowed values" in err.lower() for err in errors)

    def test_multiple_errors_all_reported(self, validator):
        """Test that multiple errors are all reported."""
        spec = {
            "metadata": {
                "name": "Test"
                # Missing strategy_type and rebalancing_frequency
            },
            "indicators": {"technical_indicators": []},
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid is False
        assert len(errors) >= 2  # At least 2 missing fields

    def test_get_validation_errors_method(self, validator, valid_momentum_spec):
        """Test get_validation_errors convenience method."""
        del valid_momentum_spec["metadata"]["name"]
        errors = validator.get_validation_errors(valid_momentum_spec)
        assert len(errors) > 0
        assert isinstance(errors, list)


# Test Indicator Reference Validation
class TestIndicatorReferences:
    """Test cross-field validation of indicator references."""

    def test_valid_ranking_field_reference(self, validator, valid_factor_combo_spec):
        """Test valid ranking field reference passes."""
        is_valid, errors = validator.validate_indicator_references(valid_factor_combo_spec)
        assert is_valid is True
        assert len(errors) == 0

    def test_invalid_ranking_field_reference(self, validator, valid_factor_combo_spec):
        """Test error for ranking field not in indicators."""
        valid_factor_combo_spec["entry_conditions"]["ranking_rules"][0]["field"] = "nonexistent_field"
        is_valid, errors = validator.validate_indicator_references(valid_factor_combo_spec)
        assert is_valid is False
        assert len(errors) > 0
        assert any("not found in indicators" in err for err in errors)

    def test_valid_weighting_field_reference(self, validator, valid_factor_combo_spec):
        """Test valid position sizing weighting field."""
        valid_factor_combo_spec["position_sizing"]["method"] = "factor_weighted"
        valid_factor_combo_spec["position_sizing"]["weighting_field"] = "quality_score"
        is_valid, errors = validator.validate_indicator_references(valid_factor_combo_spec)
        assert is_valid is True

    def test_invalid_weighting_field_reference(self, validator, valid_factor_combo_spec):
        """Test error for weighting field not in indicators."""
        valid_factor_combo_spec["position_sizing"]["method"] = "factor_weighted"
        valid_factor_combo_spec["position_sizing"]["weighting_field"] = "nonexistent"
        is_valid, errors = validator.validate_indicator_references(valid_factor_combo_spec)
        assert is_valid is False
        assert any("not found in indicators" in err for err in errors)


# Test Example Files
class TestExampleFiles:
    """Test all example YAML files for validation success/failure."""

    def test_all_valid_examples_pass(self, validator, examples_dir):
        """Test that all valid example files pass validation."""
        valid_files = [
            "test_valid_momentum.yaml",
            "test_valid_factor_combo.yaml",
            "test_valid_mean_reversion.yaml"
        ]

        for filename in valid_files:
            yaml_file = examples_dir / filename
            if yaml_file.exists():
                is_valid, errors = validator.load_and_validate(str(yaml_file))
                assert is_valid is True, f"{filename} should be valid but has errors: {errors}"

    def test_all_invalid_examples_fail(self, validator, examples_dir):
        """Test that all invalid example files fail validation."""
        invalid_files = [
            "test_invalid_missing_required.yaml",
            "test_invalid_bad_values.yaml",
            "test_invalid_empty_sections.yaml"
        ]

        for filename in invalid_files:
            yaml_file = examples_dir / filename
            if yaml_file.exists():
                is_valid, errors = validator.load_and_validate(str(yaml_file))
                assert is_valid is False, f"{filename} should be invalid but passed validation"
                assert len(errors) > 0


# Test Edge Cases
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_spec(self, validator):
        """Test empty specification."""
        is_valid, errors = validator.validate({})
        assert is_valid is False
        assert len(errors) > 0

    def test_minimal_valid_spec(self, validator):
        """Test minimal spec that passes validation."""
        spec = {
            "metadata": {
                "name": "Minimal",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "test",
                        "type": "RSI"
                    }
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "test > 50"}
                ]
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid is True

    def test_very_long_name(self, validator, valid_momentum_spec):
        """Test error for name exceeding max length."""
        valid_momentum_spec["metadata"]["name"] = "A" * 101
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False

    def test_very_short_name(self, validator, valid_momentum_spec):
        """Test error for name below min length."""
        valid_momentum_spec["metadata"]["name"] = "ABC"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False

    def test_additional_properties_rejected(self, validator, valid_momentum_spec):
        """Test that additional properties in metadata are rejected."""
        valid_momentum_spec["metadata"]["extra_field"] = "not allowed"
        is_valid, errors = validator.validate(valid_momentum_spec)
        assert is_valid is False
        assert any("additional" in err.lower() for err in errors)


# Test Performance
class TestPerformance:
    """Test validator performance and schema caching."""

    def test_schema_cached(self, validator):
        """Test that schema is loaded once and cached."""
        schema1 = validator.schema
        schema2 = validator.schema
        # Should be the same object
        assert schema1 is schema2

    def test_multiple_validations_use_cached_schema(self, validator, valid_momentum_spec):
        """Test multiple validations don't reload schema."""
        initial_schema = validator._schema

        # Run multiple validations
        for _ in range(5):
            validator.validate(valid_momentum_spec)

        # Schema should still be the same object
        assert validator._schema is initial_schema
