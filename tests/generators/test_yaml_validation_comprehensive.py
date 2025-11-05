"""
Comprehensive YAML Validation and Code Generation Unit Tests
=============================================================

Task 9 of structured-innovation-mvp spec.

This comprehensive test suite validates both YAML schema validation and code generation
with >90% coverage target. Tests all validation rules, error handling, edge cases,
and code generation scenarios.

Test Structure:
---------------
- TestValidYAMLSpecs: 15+ valid YAML specification tests
- TestInvalidYAML: Missing fields, wrong types, out of range values
- TestCodeGenerationSuccess: All indicator types and position sizing methods
- TestEdgeCases: Empty specs, maximum complexity, boundary conditions
- TestErrorMessages: Clear and actionable error reporting
- TestCoverage: Integration scenarios and error recovery

Target Metrics:
---------------
- ≥30 comprehensive unit tests
- >90% code coverage
- All tests pass
- Tests complete in <5 seconds

Requirements Coverage:
----------------------
- YAMLSchemaValidator validation logic
- YAMLToCodeGenerator code generation
- All schema validation rules
- All indicator types (RSI, MACD, BB, SMA, EMA, etc.)
- All position sizing methods (equal_weight, factor_weighted, risk_parity, volatility_weighted, custom_formula)
- Error handling and edge cases
"""

import pytest
import ast
import json
import yaml
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def validator():
    """Create YAMLSchemaValidator instance."""
    return YAMLSchemaValidator(use_pydantic=False)


@pytest.fixture
def generator(validator):
    """Create YAMLToCodeGenerator instance."""
    return YAMLToCodeGenerator(validator, validate_semantics=True)


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).resolve().parent.parent.parent


# =============================================================================
# Test Category 1: Valid YAML Specifications (15+ test cases)
# =============================================================================

class TestValidYAMLSpecs:
    """Test that all valid YAML specifications pass validation."""

    def test_valid_minimal_momentum(self, validator):
        """Test minimal valid momentum strategy."""
        spec = {
            "metadata": {
                "name": "Minimal Momentum",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 50"}]
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Should be valid but got errors: {errors}"
        assert errors == []

    def test_valid_momentum_with_multiple_indicators(self, validator):
        """Test momentum with RSI, MACD, and moving averages."""
        spec = {
            "metadata": {
                "name": "Multi Indicator Momentum",
                "description": "Momentum strategy with multiple technical indicators",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M",
                "version": "1.0.0"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                    {"name": "macd", "type": "MACD", "source": "data.get('MACD')"},
                    {"name": "sma_50", "type": "SMA", "period": 50, "source": "data.get('SMA_50')"},
                    {"name": "ema_20", "type": "EMA", "period": 20, "source": "data.get('EMA_20')"}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "rsi_14 > 30", "description": "RSI not oversold"},
                    {"condition": "macd > 0", "description": "MACD bullish"},
                    {"condition": "sma_50 > ema_20", "description": "Golden cross"}
                ],
                "logical_operator": "AND"
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_mean_reversion(self, validator):
        """Test mean reversion strategy with Bollinger Bands."""
        spec = {
            "metadata": {
                "name": "BB Mean Reversion",
                "description": "Bollinger Band mean reversion strategy",
                "strategy_type": "mean_reversion",
                "rebalancing_frequency": "W-FRI",
                "version": "1.0.0"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "bb_upper", "type": "BB", "period": 20, "source": "data.get('BB_UPPER')"},
                    {"name": "bb_lower", "type": "BB", "period": 20, "source": "data.get('BB_LOWER')"},
                    {"name": "rsi", "type": "RSI", "period": 14, "source": "data.get('RSI')"}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "close < bb_lower", "description": "Price below lower band"},
                    {"condition": "rsi < 30", "description": "RSI oversold"}
                ],
                "logical_operator": "AND"
            },
            "exit_conditions": {
                "stop_loss_pct": 0.10
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_factor_combination(self, validator):
        """Test factor combination strategy with fundamentals."""
        spec = {
            "metadata": {
                "name": "Quality Momentum",
                "description": "Combined fundamental quality and technical momentum",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M",
                "version": "1.0.0",
                "tags": ["quality", "momentum", "fundamental"]
            },
            "indicators": {
                "fundamental_factors": [
                    {"name": "roe", "field": "ROE", "source": "data.get('ROE')"},
                    {"name": "revenue_growth", "field": "revenue_growth", "source": "data.get('revenue_growth')"}
                ],
                "technical_indicators": [
                    {"name": "momentum", "type": "Momentum", "period": 126, "source": "data.get('returns_126')"}
                ],
                "custom_calculations": [
                    {"name": "quality_score", "expression": "roe * (1 + revenue_growth)", "description": "Quality metric"}
                ]
            },
            "entry_conditions": {
                "ranking_rules": [
                    {"field": "quality_score", "method": "top_percent", "value": 20, "ascending": False}
                ]
            },
            "position_sizing": {
                "method": "factor_weighted",
                "weighting_field": "quality_score",
                "max_positions": 30
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_all_indicator_types(self, validator):
        """Test spec with all supported indicator types."""
        indicator_types = ["RSI", "MACD", "BB", "SMA", "EMA", "ATR", "ADX",
                          "Stochastic", "CCI", "Williams_R", "MFI", "OBV"]

        spec = {
            "metadata": {
                "name": "All Indicators Test",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": f"ind_{i}", "type": ind_type, "source": f"data.get('{ind_type}')"}
                    for i, ind_type in enumerate(indicator_types)
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "ind_0 > 50"}]
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_equal_weight_sizing(self, validator):
        """Test equal_weight position sizing."""
        spec = {
            "metadata": {"name": "Equal Weight Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "equal_weight", "max_positions": 20}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_factor_weighted_sizing(self, validator):
        """Test factor_weighted position sizing."""
        spec = {
            "metadata": {"name": "Factor Weight Test", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {
                "fundamental_factors": [{"name": "score", "field": "ROE", "source": "data.get('ROE')"}]
            },
            "entry_conditions": {"ranking_rules": [{"field": "score", "method": "top_n", "value": 10}]},
            "position_sizing": {"method": "factor_weighted", "weighting_field": "score"}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_risk_parity_sizing(self, validator):
        """Test risk_parity position sizing."""
        spec = {
            "metadata": {"name": "Risk Parity Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "risk_parity", "lookback_period": 60}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_volatility_weighted_sizing(self, validator):
        """Test volatility_weighted position sizing."""
        spec = {
            "metadata": {"name": "Vol Weight Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "volatility_weighted", "lookback_period": 30, "target_volatility": 0.15}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_custom_formula_sizing(self, validator):
        """Test custom_formula position sizing."""
        spec = {
            "metadata": {"name": "Custom Formula Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {
                "technical_indicators": [{"name": "score", "type": "RSI", "source": "data.get('RSI')"}]
            },
            "entry_conditions": {"threshold_rules": [{"condition": "score > 50"}]},
            "position_sizing": {"method": "custom_formula", "formula": "score / score.sum()"}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_weekly_rebalancing_variants(self, validator):
        """Test all weekly rebalancing frequency options."""
        frequencies = ["W-MON", "W-TUE", "W-WED", "W-THU", "W-FRI"]

        for freq in frequencies:
            spec = {
                "metadata": {"name": f"Weekly {freq} Test", "strategy_type": "momentum", "rebalancing_frequency": freq},
                "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
                "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
            }
            is_valid, errors = validator.validate(spec)
            assert is_valid, f"Frequency {freq} should be valid but got errors: {errors}"

    def test_valid_quarterly_rebalancing(self, validator):
        """Test quarterly rebalancing frequency."""
        spec = {
            "metadata": {"name": "Quarterly Test", "strategy_type": "momentum", "rebalancing_frequency": "Q"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_volume_filters(self, validator):
        """Test volume filter indicators."""
        spec = {
            "metadata": {"name": "Volume Filter Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {
                "technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}],
                "volume_filters": [
                    {"name": "avg_volume", "metric": "average_volume", "period": 20, "min_value": 1000000}
                ]
            },
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_with_exit_conditions(self, validator):
        """Test strategy with comprehensive exit conditions."""
        spec = {
            "metadata": {"name": "Exit Conditions Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "exit_conditions": {
                "stop_loss_pct": 0.15,
                "take_profit_pct": 0.30,
                "trailing_stop_pct": 0.10,
                "max_holding_period": 90
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_with_risk_management(self, validator):
        """Test strategy with risk management parameters."""
        spec = {
            "metadata": {"name": "Risk Management Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "risk_management": {
                "max_position_size": 0.10,
                "max_sector_exposure": 0.30,
                "max_portfolio_volatility": 0.20
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"

    def test_valid_complex_multi_factor(self, validator):
        """Test complex multi-factor strategy combining all features."""
        spec = {
            "metadata": {
                "name": "Complex Multi Factor",
                "description": "Comprehensive multi-factor strategy with all features",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M",
                "version": "2.1.0",
                "author": "Test Suite",
                "tags": ["multi-factor", "quality", "momentum", "value"],
                "risk_level": "medium"
            },
            "indicators": {
                "fundamental_factors": [
                    {"name": "roe", "field": "ROE", "source": "data.get('ROE')"},
                    {"name": "pb", "field": "PB_ratio", "source": "data.get('PB_ratio')"},
                    {"name": "revenue_growth", "field": "revenue_growth", "source": "data.get('revenue_growth')"}
                ],
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                    {"name": "momentum_126", "type": "Momentum", "period": 126, "source": "data.get('returns_126')"},
                    {"name": "atr_20", "type": "ATR", "period": 20, "source": "data.get('ATR_20')"}
                ],
                "custom_calculations": [
                    {"name": "quality_score", "expression": "roe * (1 + revenue_growth)", "description": "Quality metric"},
                    {"name": "value_score", "expression": "1 / pb", "description": "Value metric"},
                    {"name": "composite_score", "expression": "quality_score * value_score * momentum_126"}
                ],
                "volume_filters": [
                    {"name": "liquidity", "metric": "dollar_volume", "period": 20, "min_value": 5000000}
                ]
            },
            "entry_conditions": {
                "ranking_rules": [
                    {"field": "composite_score", "method": "top_percent", "value": 10, "ascending": False}
                ],
                "threshold_rules": [
                    {"condition": "rsi_14 > 30", "description": "Not oversold"},
                    {"condition": "roe > 0.10", "description": "Profitable"}
                ],
                "logical_operator": "AND"
            },
            "exit_conditions": {
                "stop_loss_pct": 0.20,
                "take_profit_pct": 0.50
            },
            "position_sizing": {
                "method": "factor_weighted",
                "weighting_field": "composite_score",
                "max_positions": 25
            },
            "risk_management": {
                "max_position_size": 0.08,
                "max_sector_exposure": 0.25
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Errors: {errors}"


# =============================================================================
# Test Category 2: Invalid YAML (Missing Fields, Wrong Types, Out of Range)
# =============================================================================

class TestInvalidYAML:
    """Test that invalid YAML specifications are properly rejected."""

    def test_missing_metadata(self, validator):
        """Test error when metadata section is missing."""
        spec = {
            "indicators": {"technical_indicators": []},
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert len(errors) > 0
        assert any("metadata" in err.lower() for err in errors)

    def test_missing_indicators(self, validator):
        """Test error when indicators section is missing."""
        spec = {
            "metadata": {"name": "Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("indicators" in err.lower() for err in errors)

    def test_missing_entry_conditions(self, validator):
        """Test error when entry_conditions is missing."""
        spec = {
            "metadata": {"name": "Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": []}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("entry_conditions" in err.lower() for err in errors)

    def test_missing_strategy_name(self, validator):
        """Test error when metadata.name is missing."""
        spec = {
            "metadata": {"strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("name" in err.lower() for err in errors)

    def test_invalid_strategy_type(self, validator):
        """Test error for invalid strategy_type enum value."""
        spec = {
            "metadata": {"name": "Invalid Type", "strategy_type": "invalid_strategy", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("strategy_type" in err for err in errors)
        assert any("allowed" in err.lower() for err in errors)

    def test_invalid_rebalancing_frequency(self, validator):
        """Test error for invalid rebalancing frequency."""
        spec = {
            "metadata": {"name": "Invalid Freq", "strategy_type": "momentum", "rebalancing_frequency": "DAILY"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("rebalancing_frequency" in err for err in errors)

    def test_name_too_short(self, validator):
        """Test error for strategy name below minimum length."""
        spec = {
            "metadata": {"name": "ABC", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("name" in err.lower() for err in errors)

    def test_name_too_long(self, validator):
        """Test error for strategy name exceeding maximum length."""
        spec = {
            "metadata": {"name": "A" * 101, "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_invalid_indicator_type(self, validator):
        """Test error for invalid technical indicator type."""
        spec = {
            "metadata": {"name": "Invalid Indicator", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "invalid", "type": "INVALID_TYPE", "source": "data.get('X')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "invalid > 0"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("type" in err for err in errors)

    def test_indicator_name_invalid_pattern(self, validator):
        """Test error for indicator name with invalid characters."""
        spec = {
            "metadata": {"name": "Invalid Pattern", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "invalid-name!", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "invalid-name! > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        # Pattern validation errors may be reported differently
        assert len(errors) > 0

    def test_period_out_of_range_low(self, validator):
        """Test error for period value below minimum."""
        spec = {
            "metadata": {"name": "Period Too Low", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "period": 0, "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_period_out_of_range_high(self, validator):
        """Test error for period value above maximum."""
        spec = {
            "metadata": {"name": "Period Too High", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "period": 500, "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_invalid_ranking_method(self, validator):
        """Test error for invalid ranking method."""
        spec = {
            "metadata": {"name": "Invalid Ranking", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {"fundamental_factors": [{"name": "score", "field": "ROE", "source": "data.get('ROE')"}]},
            "entry_conditions": {"ranking_rules": [{"field": "score", "method": "invalid_method", "value": 10}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("method" in err for err in errors)

    def test_invalid_position_sizing_method(self, validator):
        """Test error for invalid position sizing method."""
        spec = {
            "metadata": {"name": "Invalid Sizing", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "invalid_method"}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_stop_loss_out_of_range(self, validator):
        """Test error for stop_loss_pct exceeding valid range."""
        spec = {
            "metadata": {"name": "Invalid Stop Loss", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "exit_conditions": {"stop_loss_pct": 0.60}  # Over 50% limit
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_wrong_type_for_period(self, validator):
        """Test error for period field with wrong type."""
        spec = {
            "metadata": {"name": "Wrong Type", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "period": "fourteen", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid

    def test_undefined_indicator_reference(self, validator):
        """Test semantic validation for undefined indicator reference."""
        spec = {
            "metadata": {"name": "Undefined Ref", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {"fundamental_factors": [{"name": "roe", "field": "ROE", "source": "data.get('ROE')"}]},
            "entry_conditions": {"ranking_rules": [{"field": "undefined_field", "method": "top_n", "value": 10}]}
        }
        is_valid, errors = validator.validate_indicator_references(spec)
        assert not is_valid
        assert any("not found" in err.lower() for err in errors)

    def test_invalid_weighting_field_reference(self, validator):
        """Test error for weighting field not in indicators."""
        spec = {
            "metadata": {"name": "Invalid Weight Field", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {"fundamental_factors": [{"name": "score", "field": "ROE", "source": "data.get('ROE')"}]},
            "entry_conditions": {"ranking_rules": [{"field": "score", "method": "top_n", "value": 10}]},
            "position_sizing": {"method": "factor_weighted", "weighting_field": "nonexistent_field"}
        }
        is_valid, errors = validator.validate_indicator_references(spec)
        assert not is_valid
        assert any("not found" in err.lower() for err in errors)


# =============================================================================
# Test Category 3: Code Generation Success (All Indicator Types & Position Sizing)
# =============================================================================

class TestCodeGenerationSuccess:
    """Test successful code generation for all scenarios."""

    def test_generate_momentum_strategy(self, generator):
        """Test code generation for momentum strategy."""
        spec = {
            "metadata": {"name": "Test Momentum", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                    {"name": "ma_50", "type": "SMA", "period": 50, "source": "data.get('SMA_50')"}
                ]
            },
            "entry_conditions": {"threshold_rules": [{"condition": "rsi_14 > 30"}, {"condition": "ma_50 > 0"}]}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None
        ast.parse(code)  # Verify syntactically correct
        assert "def strategy(data):" in code
        assert "rsi_14" in code

    def test_generate_mean_reversion_strategy(self, generator):
        """Test code generation for mean reversion strategy."""
        spec = {
            "metadata": {"name": "Test Mean Rev", "strategy_type": "mean_reversion", "rebalancing_frequency": "M"},
            "indicators": {
                "technical_indicators": [
                    {"name": "bb_lower", "type": "BB", "period": 20, "source": "data.get('BB_LOWER')"}
                ]
            },
            "entry_conditions": {"threshold_rules": [{"condition": "close < bb_lower"}]}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None
        ast.parse(code)

    def test_generate_factor_combination_strategy(self, generator):
        """Test code generation for factor combination strategy."""
        spec = {
            "metadata": {"name": "Test Factor Combo", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {
                "fundamental_factors": [{"name": "roe", "field": "ROE", "source": "data.get('ROE')"}],
                "custom_calculations": [{"name": "score", "expression": "roe * 2"}]
            },
            "entry_conditions": {"ranking_rules": [{"field": "score", "method": "top_n", "value": 10}]}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None
        ast.parse(code)

    def test_generate_equal_weight_position_sizing(self, generator):
        """Test code generation with equal_weight position sizing."""
        spec = {
            "metadata": {"name": "Equal Weight", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "equal_weight", "max_positions": 20}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert "equal" in code.lower() or "entry_mask.astype(float)" in code

    def test_generate_factor_weighted_position_sizing(self, generator):
        """Test code generation with factor_weighted position sizing."""
        spec = {
            "metadata": {"name": "Factor Weight", "strategy_type": "factor_combination", "rebalancing_frequency": "M"},
            "indicators": {"fundamental_factors": [{"name": "score", "field": "ROE", "source": "data.get('ROE')"}]},
            "entry_conditions": {"ranking_rules": [{"field": "score", "method": "top_n", "value": 10}]},
            "position_sizing": {"method": "factor_weighted", "weighting_field": "score"}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert "weights" in code.lower() or "score" in code

    def test_generate_risk_parity_position_sizing(self, generator):
        """Test code generation with risk_parity position sizing."""
        spec = {
            "metadata": {"name": "Risk Parity", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "risk_parity", "lookback_period": 60}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert "volatility" in code.lower() or "risk" in code.lower()

    def test_generate_volatility_weighted_position_sizing(self, generator):
        """Test code generation with volatility_weighted position sizing."""
        spec = {
            "metadata": {"name": "Vol Weight", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "position_sizing": {"method": "volatility_weighted", "lookback_period": 30}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert "volatility" in code.lower()

    def test_generate_custom_formula_position_sizing(self, generator):
        """Test code generation with custom_formula position sizing."""
        spec = {
            "metadata": {"name": "Custom Formula", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "score", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "score > 50"}]},
            "position_sizing": {"method": "custom_formula", "formula": "score / score.sum()"}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert "custom" in code.lower() or "formula" in code.lower()

    def test_generate_all_technical_indicators(self, generator):
        """Test code generation with all technical indicator types."""
        indicators = ["RSI", "MACD", "BB", "SMA", "EMA", "ATR"]
        spec = {
            "metadata": {"name": "All Tech Indicators", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {
                "technical_indicators": [
                    {"name": f"ind_{i}", "type": ind_type, "source": f"data.get('{ind_type}')"}
                    for i, ind_type in enumerate(indicators)
                ]
            },
            "entry_conditions": {"threshold_rules": [{"condition": "ind_0 > 50"}]}
        }
        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None
        ast.parse(code)


# =============================================================================
# Test Category 4: Edge Cases
# =============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_spec(self, validator):
        """Test validation of completely empty spec."""
        is_valid, errors = validator.validate({})
        assert not is_valid
        assert len(errors) > 0

    def test_none_spec(self, validator):
        """Test validation of None spec."""
        is_valid, errors = validator.validate(None)
        assert not is_valid

    def test_minimal_valid_spec(self, validator):
        """Test absolutely minimal valid spec."""
        spec = {
            "metadata": {"name": "Minimal", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "x", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "x > 0"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid

    def test_maximum_complexity_spec(self, validator):
        """Test spec with maximum complexity (many indicators, rules, etc.)."""
        spec = {
            "metadata": {
                "name": "Maximum Complexity",
                "description": "Testing maximum spec complexity",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M",
                "version": "1.0.0",
                "tags": [f"tag{i}" for i in range(10)]
            },
            "indicators": {
                "technical_indicators": [
                    {"name": f"tech_{i}", "type": "RSI", "source": f"data.get('RSI_{i}')"}
                    for i in range(10)
                ],
                "fundamental_factors": [
                    {"name": f"fund_{i}", "field": "ROE", "source": f"data.get('ROE_{i}')"}
                    for i in range(10)
                ],
                "custom_calculations": [
                    {"name": f"calc_{i}", "expression": f"tech_{i} * fund_{i}"}
                    for i in range(5)
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": f"tech_{i} > 30"} for i in range(10)],
                "ranking_rules": [{"field": "calc_0", "method": "top_n", "value": 10}]
            }
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid, f"Max complexity should be valid but got: {errors}"

    def test_boundary_period_minimum(self, validator):
        """Test period at minimum boundary (1)."""
        spec = {
            "metadata": {"name": "Min Period", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "period": 1, "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid

    def test_boundary_period_maximum(self, validator):
        """Test period at maximum boundary (250)."""
        spec = {
            "metadata": {"name": "Max Period", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "period": 250, "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid

    def test_boundary_stop_loss_minimum(self, validator):
        """Test stop_loss_pct at minimum (0.01)."""
        spec = {
            "metadata": {"name": "Min Stop Loss", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "exit_conditions": {"stop_loss_pct": 0.01}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid

    def test_boundary_stop_loss_maximum(self, validator):
        """Test stop_loss_pct at maximum (0.50)."""
        spec = {
            "metadata": {"name": "Max Stop Loss", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]},
            "exit_conditions": {"stop_loss_pct": 0.50}
        }
        is_valid, errors = validator.validate(spec)
        assert is_valid

    def test_file_loading_nonexistent(self, validator):
        """Test loading nonexistent file."""
        is_valid, errors = validator.load_and_validate("nonexistent_file_xyz.yaml")
        assert not is_valid
        assert any("not found" in err.lower() for err in errors)

    def test_file_loading_malformed_yaml(self, validator):
        """Test loading file with malformed YAML syntax."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [unclosed\n  bad: indentation")
            temp_path = f.name

        try:
            is_valid, errors = validator.load_and_validate(temp_path)
            assert not is_valid
            assert any("parsing" in err.lower() or "yaml" in err.lower() for err in errors)
        finally:
            Path(temp_path).unlink()


# =============================================================================
# Test Category 5: Error Messages Quality
# =============================================================================

class TestErrorMessages:
    """Test that error messages are clear and actionable."""

    def test_error_includes_field_path(self, validator):
        """Test that error messages include field paths."""
        spec = {
            "metadata": {"name": "Test", "rebalancing_frequency": "M"},  # Missing strategy_type
            "indicators": {"technical_indicators": []},
            "entry_conditions": {"threshold_rules": []}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("strategy_type" in err for err in errors)

    def test_error_mentions_allowed_values(self, validator):
        """Test that enum errors mention allowed values."""
        spec = {
            "metadata": {"name": "Test", "strategy_type": "invalid", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert any("allowed" in err.lower() for err in errors)

    def test_multiple_errors_all_reported(self, validator):
        """Test that all validation errors are reported."""
        spec = {
            "metadata": {"name": "X"},  # Missing strategy_type and rebalancing_frequency
            "indicators": {},  # Empty
            "entry_conditions": {}  # Empty
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        assert len(errors) >= 2  # Multiple errors

    def test_error_message_descriptive(self, validator):
        """Test that error messages are sufficiently descriptive."""
        spec = {
            "metadata": {"name": "Test", "strategy_type": "bad", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }
        is_valid, errors = validator.validate(spec)
        assert not is_valid
        for error in errors:
            assert len(error) > 10  # Reasonably descriptive

    def test_generation_error_clear(self, generator):
        """Test that code generation errors are clear."""
        invalid_spec = {"metadata": {"name": "Invalid"}}
        code, errors = generator.generate(invalid_spec)
        assert code is None
        assert len(errors) > 0
        for error in errors:
            assert len(error) > 5  # Not just a code


# =============================================================================
# Test Category 6: Performance and Integration
# =============================================================================

class TestPerformanceAndIntegration:
    """Test performance characteristics and integration scenarios."""

    def test_validation_completes_quickly(self, validator):
        """Test that validation completes in reasonable time."""
        import time
        spec = {
            "metadata": {"name": "Performance Test", "strategy_type": "momentum", "rebalancing_frequency": "M"},
            "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
            "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
        }

        start = time.time()
        for _ in range(100):
            validator.validate(spec)
        elapsed = time.time() - start

        assert elapsed < 2.0  # 100 validations in under 2 seconds

    def test_batch_generation(self, generator):
        """Test batch code generation."""
        specs = [
            {
                "metadata": {"name": f"Batch {i}", "strategy_type": "momentum", "rebalancing_frequency": "M"},
                "indicators": {"technical_indicators": [{"name": "rsi", "type": "RSI", "source": "data.get('RSI')"}]},
                "entry_conditions": {"threshold_rules": [{"condition": "rsi > 50"}]}
            }
            for i in range(5)
        ]

        results = generator.generate_batch(specs)
        assert len(results) == 5
        for code, errors in results:
            assert errors == []
            assert code is not None

    def test_schema_caching(self, validator):
        """Test that schema is loaded once and cached."""
        schema1 = validator.schema
        schema2 = validator.schema
        assert schema1 is schema2  # Same object reference

    def test_end_to_end_pipeline(self, generator):
        """Test complete end-to-end validation and generation."""
        spec = {
            "metadata": {
                "name": "E2E Test Strategy",
                "description": "End-to-end test",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M",
                "version": "1.0.0"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi_14", "type": "RSI", "period": 14, "source": "data.get('RSI_14')"},
                    {"name": "ma_50", "type": "SMA", "period": 50, "source": "data.get('SMA_50')"}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "rsi_14 > 30"},
                    {"condition": "ma_50 > 0"}
                ]
            },
            "position_sizing": {
                "method": "equal_weight",
                "max_positions": 20
            }
        }

        # Validate
        is_valid, val_errors = generator.validate_only(spec)
        assert is_valid
        assert val_errors == []

        # Generate
        code, gen_errors = generator.generate(spec)
        assert gen_errors == []
        assert code is not None

        # Verify syntax
        ast.parse(code)

        # Check content
        assert "def strategy(data):" in code
        assert "rsi_14" in code
        assert "ma_50" in code


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
