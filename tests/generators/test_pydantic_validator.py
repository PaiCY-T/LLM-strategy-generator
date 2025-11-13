"""
Unit Tests for PydanticValidator

Tests Pydantic-based YAML validation with detailed error message formatting.

Task 4 of yaml-normalizer-phase2-complete-normalization spec.
Coverage target: >80%
"""

import pytest
from typing import Dict, Any

from src.generators.pydantic_validator import (
    PydanticValidator,
    validate_yaml_with_pydantic
)
from src.models.strategy_models import StrategySpecification


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def validator():
    """Create a PydanticValidator instance."""
    return PydanticValidator()


@pytest.fixture
def valid_minimal_spec():
    """Minimal valid YAML specification."""
    return {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "period": 14}
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi < 30"}
            ]
        }
    }


@pytest.fixture
def valid_complete_spec():
    """Complete valid YAML specification with all sections."""
    return {
        "metadata": {
            "name": "Complete Test Strategy",
            "description": "A complete strategy for testing",
            "strategy_type": "factor_combination",
            "rebalancing_frequency": "W-FRI",
            "version": "1.0.0",
            "author": "Test Author",
            "tags": ["test", "momentum", "value"],
            "risk_level": "medium"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "RSI", "period": 14},
                {"name": "sma_50", "type": "SMA", "period": 50}
            ],
            "fundamental_factors": [
                {"name": "roe", "field": "ROE", "transformation": "zscore"}
            ],
            "custom_calculations": [
                {
                    "name": "custom_score",
                    "expression": "rsi_14 * 0.5 + roe * 0.5",
                    "description": "Custom scoring"
                }
            ],
            "volume_filters": [
                {
                    "name": "liquidity",
                    "metric": "average_volume",
                    "period": 20,
                    "threshold": 1000000
                }
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi_14 < 30"},
                {"condition": "sma_50 > 0"}
            ],
            "ranking_rules": [
                {
                    "field": "custom_score",
                    "method": "top_percent",
                    "value": 20.0,
                    "ascending": False
                }
            ],
            "logical_operator": "AND",
            "min_liquidity": {
                "average_volume_20d": 500000,
                "dollar_volume": 10000000
            }
        },
        "exit_conditions": {
            "stop_loss_pct": 0.10,
            "take_profit_pct": 0.25,
            "trailing_stop": {
                "trail_percent": 0.05,
                "activation_profit": 0.10
            },
            "holding_period_days": 60,
            "conditional_exits": [
                {"condition": "rsi_14 > 70"}
            ],
            "exit_operator": "OR"
        },
        "position_sizing": {
            "method": "factor_weighted",
            "max_positions": 20,
            "max_position_pct": 0.10,
            "min_position_pct": 0.02,
            "weighting_field": "custom_score"
        },
        "risk_management": {
            "max_portfolio_volatility": 0.20,
            "max_sector_exposure": 0.30,
            "max_correlation": 0.70,
            "rebalance_threshold": 0.05,
            "max_drawdown_limit": 0.25,
            "cash_reserve_pct": 0.05
        },
        "backtest_config": {
            "start_date": "2020-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 1000000,
            "transaction_cost": 0.001425,
            "slippage": 0.001
        }
    }


# ============================================================================
# BASIC VALIDATION TESTS
# ============================================================================

def test_validator_initialization(validator):
    """Test PydanticValidator initializes correctly."""
    assert validator is not None
    assert validator.model == StrategySpecification


def test_valid_minimal_spec(validator, valid_minimal_spec):
    """Test validation passes for minimal valid spec."""
    strategy, errors = validator.validate(valid_minimal_spec)

    assert strategy is not None
    assert isinstance(strategy, StrategySpecification)
    assert errors == []
    assert strategy.metadata.name == "Test Strategy"
    assert strategy.metadata.strategy_type == "momentum"


def test_valid_complete_spec(validator, valid_complete_spec):
    """Test validation passes for complete valid spec."""
    strategy, errors = validator.validate(valid_complete_spec)

    assert strategy is not None
    assert isinstance(strategy, StrategySpecification)
    assert errors == []
    assert strategy.metadata.name == "Complete Test Strategy"
    assert len(strategy.indicators.technical_indicators) == 2
    assert len(strategy.indicators.fundamental_factors) == 1


def test_invalid_not_dict(validator):
    """Test validation fails for non-dictionary input."""
    strategy, errors = validator.validate("not a dict")

    assert strategy is None
    assert len(errors) == 1
    assert "must be a dictionary" in errors[0]


def test_empty_dict(validator):
    """Test validation fails for empty dictionary."""
    strategy, errors = validator.validate({})

    assert strategy is None
    assert len(errors) > 0
    # Should have errors about missing required fields


# ============================================================================
# MISSING FIELD TESTS
# ============================================================================

def test_missing_metadata(validator, valid_minimal_spec):
    """Test validation fails when metadata is missing."""
    spec = valid_minimal_spec.copy()
    del spec["metadata"]

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("metadata" in err.lower() for err in errors)


def test_missing_metadata_name(validator, valid_minimal_spec):
    """Test validation fails when metadata.name is missing."""
    spec = valid_minimal_spec.copy()
    del spec["metadata"]["name"]

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("name" in err.lower() for err in errors)


def test_missing_indicators(validator, valid_minimal_spec):
    """Test validation fails when indicators section is missing."""
    spec = valid_minimal_spec.copy()
    del spec["indicators"]

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("indicators" in err.lower() for err in errors)


def test_missing_entry_conditions(validator, valid_minimal_spec):
    """Test validation fails when entry_conditions is missing."""
    spec = valid_minimal_spec.copy()
    del spec["entry_conditions"]

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("entry_conditions" in err.lower() for err in errors)


# ============================================================================
# TYPE VALIDATION TESTS
# ============================================================================

def test_invalid_strategy_type(validator, valid_minimal_spec):
    """Test validation fails for invalid strategy_type."""
    spec = valid_minimal_spec.copy()
    spec["metadata"]["strategy_type"] = "invalid_type"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("strategy_type" in err.lower() for err in errors)


def test_invalid_rebalancing_frequency(validator, valid_minimal_spec):
    """Test validation fails for invalid rebalancing_frequency."""
    spec = valid_minimal_spec.copy()
    spec["metadata"]["rebalancing_frequency"] = "INVALID"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("rebalancing_frequency" in err.lower() for err in errors)


def test_invalid_indicator_type(validator, valid_minimal_spec):
    """Test validation fails for invalid indicator type."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["type"] = "INVALID_INDICATOR"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("type" in err.lower() for err in errors)


# ============================================================================
# PATTERN VALIDATION TESTS
# ============================================================================

def test_invalid_indicator_name_pattern(validator, valid_minimal_spec):
    """Test validation fails for indicator name not matching pattern."""
    spec = valid_minimal_spec.copy()
    # Indicator names must match ^[a-z_][a-z0-9_]*$
    spec["indicators"]["technical_indicators"][0]["name"] = "Invalid-Name"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("name" in err.lower() and "pattern" in err.lower() for err in errors)


def test_invalid_indicator_name_starts_with_digit(validator, valid_minimal_spec):
    """Test validation fails for indicator name starting with digit."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["name"] = "14_day_rsi"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0


def test_valid_indicator_name_patterns(validator, valid_minimal_spec):
    """Test validation passes for valid indicator name patterns."""
    valid_names = ["rsi", "rsi_14", "ma_fast", "_internal", "score_1"]

    for name in valid_names:
        spec = valid_minimal_spec.copy()
        spec["indicators"]["technical_indicators"][0]["name"] = name

        strategy, errors = validator.validate(spec)

        assert strategy is not None, f"Failed for name: {name}, errors: {errors}"
        assert errors == []


# ============================================================================
# NUMERIC CONSTRAINT TESTS
# ============================================================================

def test_period_too_small(validator, valid_minimal_spec):
    """Test validation fails for period < 1."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["period"] = 0

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("period" in err.lower() for err in errors)


def test_period_too_large(validator, valid_minimal_spec):
    """Test validation fails for period > 250."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["period"] = 500

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("period" in err.lower() for err in errors)


def test_valid_period_range(validator, valid_minimal_spec):
    """Test validation passes for valid period values."""
    valid_periods = [1, 14, 50, 200, 250]

    for period in valid_periods:
        spec = valid_minimal_spec.copy()
        spec["indicators"]["technical_indicators"][0]["period"] = period

        strategy, errors = validator.validate(spec)

        assert strategy is not None, f"Failed for period: {period}, errors: {errors}"
        assert errors == []


# ============================================================================
# CROSS-FIELD VALIDATION TESTS
# ============================================================================

def test_ranking_field_not_in_indicators(validator, valid_minimal_spec):
    """Test validation fails when ranking field references undefined indicator."""
    spec = valid_minimal_spec.copy()
    spec["entry_conditions"]["ranking_rules"] = [
        {
            "field": "undefined_field",
            "method": "top_percent",
            "value": 20.0
        }
    ]

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("undefined_field" in err for err in errors)


def test_ranking_field_references_valid_indicator(validator, valid_minimal_spec):
    """Test validation passes when ranking field references defined indicator."""
    spec = valid_minimal_spec.copy()
    spec["entry_conditions"]["ranking_rules"] = [
        {
            "field": "rsi",  # Defined in indicators
            "method": "top_percent",
            "value": 20.0
        }
    ]

    strategy, errors = validator.validate(spec)

    assert strategy is not None
    assert errors == []


def test_weighting_field_not_in_indicators(validator, valid_complete_spec):
    """Test validation fails when position_sizing weighting_field is undefined."""
    spec = valid_complete_spec.copy()
    spec["position_sizing"]["weighting_field"] = "undefined_weight"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("undefined_weight" in err for err in errors)


def test_weighting_field_references_valid_indicator(validator, valid_complete_spec):
    """Test validation passes when weighting_field references defined indicator."""
    # valid_complete_spec already has this correctly configured
    strategy, errors = validator.validate(valid_complete_spec)

    assert strategy is not None
    assert errors == []


# ============================================================================
# ERROR MESSAGE FORMAT TESTS
# ============================================================================

def test_error_message_contains_field_path(validator):
    """Test error messages include field paths."""
    spec = {
        "metadata": {
            "name": "Test",
            "strategy_type": "momentum",
            # Missing rebalancing_frequency
        },
        "indicators": {},
        "entry_conditions": {}
    }

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    # Error should mention the field path
    assert any("metadata" in err.lower() or "rebalancing_frequency" in err.lower() for err in errors)


def test_error_message_for_type_mismatch(validator, valid_minimal_spec):
    """Test error messages for type mismatches are clear."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["period"] = "not a number"

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    assert any("period" in err.lower() for err in errors)


def test_error_message_for_enum_violation(validator, valid_minimal_spec):
    """Test error messages for enum violations include allowed values."""
    spec = valid_minimal_spec.copy()
    spec["metadata"]["risk_level"] = "extreme"  # Not in enum

    strategy, errors = validator.validate(spec)

    assert strategy is None
    assert len(errors) > 0
    # Should mention allowed values or be clear about the error
    assert any("risk_level" in err.lower() for err in errors)


# ============================================================================
# ARRAY FORMAT VALIDATION TESTS
# ============================================================================

def test_indicators_as_array(validator):
    """Test validation passes for indicators in array format."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": [
            {"name": "rsi", "type": "RSI", "period": 14}
        ],
        "entry_conditions": {
            "threshold_rules": [{"condition": "rsi < 30"}]
        }
    }

    strategy, errors = validator.validate(spec)

    assert strategy is not None
    assert errors == []


def test_entry_conditions_as_array(validator):
    """Test validation passes for entry_conditions in array format."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "RSI", "period": 14}
            ]
        },
        "entry_conditions": [
            {"condition": "rsi < 30"}
        ]
    }

    strategy, errors = validator.validate(spec)

    assert strategy is not None
    assert errors == []


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

def test_validate_yaml_with_pydantic_valid(valid_minimal_spec):
    """Test convenience function with valid spec."""
    strategy, errors = validate_yaml_with_pydantic(valid_minimal_spec)

    assert strategy is not None
    assert errors == []


def test_validate_yaml_with_pydantic_invalid():
    """Test convenience function with invalid spec."""
    strategy, errors = validate_yaml_with_pydantic({})

    assert strategy is None
    assert len(errors) > 0


def test_get_model_schema(validator):
    """Test getting JSON schema from Pydantic model."""
    schema = validator.get_model_schema()

    assert isinstance(schema, dict)
    assert "title" in schema
    assert "properties" in schema


def test_validate_and_raise_valid(validator, valid_minimal_spec):
    """Test validate_and_raise returns strategy for valid spec."""
    strategy = validator.validate_and_raise(valid_minimal_spec)

    assert isinstance(strategy, StrategySpecification)
    assert strategy.metadata.name == "Test Strategy"


def test_validate_and_raise_invalid(validator):
    """Test validate_and_raise raises exception for invalid spec."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        validator.validate_and_raise({})


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_none_input(validator):
    """Test validation handles None input gracefully."""
    strategy, errors = validator.validate(None)

    assert strategy is None
    assert len(errors) > 0


def test_list_input(validator):
    """Test validation handles list input gracefully."""
    strategy, errors = validator.validate([1, 2, 3])

    assert strategy is None
    assert len(errors) > 0
    assert "dictionary" in errors[0].lower()


def test_string_input(validator):
    """Test validation handles string input gracefully."""
    strategy, errors = validator.validate("string input")

    assert strategy is None
    assert len(errors) > 0


def test_multiple_errors(validator):
    """Test validation returns all errors, not just first one."""
    spec = {
        "metadata": {
            # Missing name
            # Missing strategy_type
            # Missing rebalancing_frequency
        },
        # Missing indicators
        # Missing entry_conditions
    }

    strategy, errors = validator.validate(spec)

    assert strategy is None
    # Should have multiple errors
    assert len(errors) >= 3


# ============================================================================
# REGRESSION TESTS
# ============================================================================

def test_backward_compatibility_with_extra_fields(validator, valid_minimal_spec):
    """Test validation allows extra fields (backward compatibility)."""
    spec = valid_minimal_spec.copy()
    spec["metadata"]["extra_field"] = "should be allowed"
    spec["custom_section"] = {"custom": "data"}

    strategy, errors = validator.validate(spec)

    # Should still validate (extra fields allowed)
    assert strategy is not None
    assert errors == []


def test_type_coercion_uppercase(validator, valid_minimal_spec):
    """Test Pydantic automatically uppercases indicator types."""
    spec = valid_minimal_spec.copy()
    spec["indicators"]["technical_indicators"][0]["type"] = "rsi"  # lowercase

    strategy, errors = validator.validate(spec)

    # Should pass - type is auto-uppercased by field_validator
    assert strategy is not None
    assert errors == []
    assert strategy.indicators.technical_indicators[0].type == "RSI"
