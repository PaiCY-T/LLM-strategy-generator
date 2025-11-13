"""
Integration Tests for YAMLSchemaValidator with Pydantic Integration

Tests the integration of PydanticValidator into YAMLSchemaValidator when normalize=True.

Task 5 of yaml-normalizer-phase2-complete-normalization spec.
"""

import pytest
from typing import Dict, Any

from src.generators.yaml_schema_validator import YAMLSchemaValidator


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def validator():
    """Create YAMLSchemaValidator with Pydantic enabled."""
    return YAMLSchemaValidator(use_pydantic=True)


@pytest.fixture
def validator_no_pydantic():
    """Create YAMLSchemaValidator with Pydantic disabled."""
    return YAMLSchemaValidator(use_pydantic=False)


@pytest.fixture
def valid_spec():
    """Valid YAML specification."""
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
def spec_needing_normalization():
    """YAML spec that needs normalization (uppercase indicator name)."""
    return {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "RSI_Fast", "type": "RSI", "period": 14}  # Uppercase - needs normalization
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi_fast < 30"}
            ]
        }
    }


@pytest.fixture
def invalid_spec():
    """Invalid YAML specification."""
    return {
        "metadata": {
            "name": "Test",
            "strategy_type": "invalid_type",  # Invalid
            "rebalancing_frequency": "M"
        },
        "indicators": {},
        "entry_conditions": {}
    }


# ============================================================================
# BACKWARD COMPATIBILITY TESTS (normalize=False)
# ============================================================================

def test_backward_compatibility_normalize_false(validator, valid_spec):
    """Test that normalize=False still uses JSON Schema validation."""
    is_valid, errors = validator.validate(valid_spec, normalize=False)

    assert is_valid
    assert errors == []


def test_backward_compatibility_default_normalize_false(validator, valid_spec):
    """Test that default (normalize=False) still uses JSON Schema validation."""
    # Default normalize parameter is False
    is_valid, errors = validator.validate(valid_spec)

    assert is_valid
    assert errors == []


def test_backward_compatibility_invalid_spec_normalize_false(validator, invalid_spec):
    """Test that invalid specs are rejected with normalize=False."""
    is_valid, errors = validator.validate(invalid_spec, normalize=False)

    assert not is_valid
    assert len(errors) > 0


# ============================================================================
# PYDANTIC INTEGRATION TESTS (normalize=True)
# ============================================================================

def test_normalize_true_uses_pydantic(validator, valid_spec):
    """Test that normalize=True triggers Pydantic validation."""
    is_valid, errors = validator.validate(valid_spec, normalize=True)

    assert is_valid
    assert errors == []


def test_normalize_true_with_normalization_needed(validator, spec_needing_normalization):
    """Test that normalize=True normalizes and validates with Pydantic."""
    is_valid, errors = validator.validate(spec_needing_normalization, normalize=True)

    # Should pass after normalization (RSI_Fast -> rsi_fast)
    assert is_valid
    assert errors == []


def test_normalize_true_invalid_spec(validator, invalid_spec):
    """Test that normalize=True rejects invalid specs with Pydantic errors."""
    is_valid, errors = validator.validate(invalid_spec, normalize=True)

    assert not is_valid
    assert len(errors) > 0
    # Pydantic errors should be more detailed
    assert any("strategy_type" in err.lower() for err in errors)


def test_pydantic_error_messages_are_detailed(validator):
    """Test that Pydantic validation provides detailed error messages with field paths."""
    spec = {
        "metadata": {
            "name": "Test",
            "strategy_type": "momentum",
            # Missing rebalancing_frequency
        },
        "indicators": {
            "technical_indicators": []
        },
        "entry_conditions": {
            "threshold_rules": []
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    assert not is_valid
    assert len(errors) > 0
    # Should have detailed field path
    assert any("rebalancing_frequency" in err.lower() or "metadata" in err.lower() for err in errors)


# ============================================================================
# FALLBACK BEHAVIOR TESTS
# ============================================================================

def test_pydantic_disabled_falls_back_to_json_schema(validator_no_pydantic, valid_spec):
    """Test that when Pydantic is disabled, JSON Schema is used even with normalize=True."""
    is_valid, errors = validator_no_pydantic.validate(valid_spec, normalize=True)

    # Should still validate (using JSON Schema)
    assert is_valid
    assert errors == []


def test_normalization_error_graceful_degradation(validator):
    """Test that normalization errors don't break validation."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "14_invalid", "type": "RSI", "period": 14}  # Invalid name (starts with digit)
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi < 30"}
            ]
        }
    }

    # Even though normalization will fail, validation should continue
    is_valid, errors = validator.validate(spec, normalize=True)

    # Should fail validation (invalid indicator name)
    assert not is_valid
    assert len(errors) > 0


# ============================================================================
# CROSS-FIELD VALIDATION TESTS
# ============================================================================

def test_pydantic_validates_indicator_references(validator):
    """Test that Pydantic validates cross-field references (ranking field)."""
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
        "entry_conditions": {
            "ranking_rules": [
                {
                    "field": "undefined_field",  # Not in indicators
                    "method": "top_percent",
                    "value": 20.0
                }
            ]
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    assert not is_valid
    assert len(errors) > 0
    assert any("undefined_field" in err for err in errors)


def test_pydantic_allows_valid_indicator_references(validator):
    """Test that Pydantic allows valid cross-field references."""
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
        "entry_conditions": {
            "ranking_rules": [
                {
                    "field": "rsi",  # Defined in indicators
                    "method": "top_percent",
                    "value": 20.0
                }
            ]
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    assert is_valid
    assert errors == []


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_empty_spec_with_normalize_true(validator):
    """Test empty spec with normalize=True."""
    is_valid, errors = validator.validate({}, normalize=True)

    assert not is_valid
    assert len(errors) > 0


def test_non_dict_input_with_normalize_true(validator):
    """Test non-dict input with normalize=True."""
    is_valid, errors = validator.validate("not a dict", normalize=True)

    assert not is_valid
    assert len(errors) > 0


def test_complete_spec_with_all_sections(validator):
    """Test complete spec with all optional sections using normalize=True."""
    spec = {
        "metadata": {
            "name": "Complete Strategy",
            "description": "A complete test strategy",
            "strategy_type": "factor_combination",
            "rebalancing_frequency": "W-FRI",
            "version": "1.0.0",
            "risk_level": "medium"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "rsi_14", "type": "RSI", "period": 14}
            ],
            "fundamental_factors": [
                {"name": "roe", "field": "ROE"}
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi_14 < 30"}
            ],
            "ranking_rules": [
                {"field": "roe", "method": "top_percent", "value": 20.0}
            ]
        },
        "exit_conditions": {
            "stop_loss_pct": 0.10,
            "take_profit_pct": 0.25
        },
        "position_sizing": {
            "method": "equal_weight",
            "max_positions": 20
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    assert is_valid
    assert errors == []


# ============================================================================
# NORMALIZATION + VALIDATION INTEGRATION
# ============================================================================

def test_array_format_normalized_and_validated(validator):
    """Test that array format is normalized and then validated by Pydantic."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": [  # Array format - needs normalization
            {"name": "rsi", "type": "RSI", "period": 14}
        ],
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi < 30"}
            ]
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    # Should pass after normalization (array -> object)
    assert is_valid
    assert errors == []


def test_nested_params_normalized_and_validated(validator):
    """Test that nested params are flattened and validated."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {
                    "name": "rsi",
                    "type": "RSI",
                    "params": {  # Nested params - needs normalization
                        "period": 14
                    }
                }
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi < 30"}
            ]
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    # Should pass after normalization (params flattened)
    assert is_valid
    assert errors == []


def test_lowercase_type_normalized_and_validated(validator):
    """Test that lowercase indicator types are normalized and validated."""
    spec = {
        "metadata": {
            "name": "Test Strategy",
            "strategy_type": "momentum",
            "rebalancing_frequency": "M"
        },
        "indicators": {
            "technical_indicators": [
                {"name": "rsi", "type": "rsi", "period": 14}  # lowercase type
            ]
        },
        "entry_conditions": {
            "threshold_rules": [
                {"condition": "rsi < 30"}
            ]
        }
    }

    is_valid, errors = validator.validate(spec, normalize=True)

    # Should pass after normalization (type uppercased)
    assert is_valid
    assert errors == []
