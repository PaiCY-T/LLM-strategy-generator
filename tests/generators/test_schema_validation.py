"""
Unit Tests for YAML Strategy Schema Validation
===============================================

Tests the strategy_schema_v1.json validation against valid and invalid YAML specs.
Ensures schema comprehensively validates all strategy patterns and rejects invalid inputs.

Test Coverage:
--------------
1. Valid strategy specs (momentum, mean_reversion, factor_combination)
2. Invalid specs (missing required fields, invalid values, type mismatches)
3. Edge cases (boundary values, empty arrays, complex expressions)
4. Schema completeness (85% strategy pattern coverage)

Requirements:
-------------
- Requirement 1.1-1.5: Schema structure validation
- Requirement 4.1-4.4: 85% strategy pattern coverage
"""

import json
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Load the schema
SCHEMA_PATH = Path(__file__).parent.parent.parent / "schemas" / "strategy_schema_v1.json"
with open(SCHEMA_PATH, 'r') as f:
    STRATEGY_SCHEMA = json.load(f)


class TestSchemaStructure:
    """Test schema structure and completeness."""

    def test_schema_is_valid_draft7(self):
        """Verify schema itself is valid JSON Schema Draft 7."""
        # This will raise an exception if schema is invalid
        Draft7Validator.check_schema(STRATEGY_SCHEMA)

    def test_schema_has_required_sections(self):
        """Verify schema defines all required sections."""
        assert "properties" in STRATEGY_SCHEMA
        required_sections = {"metadata", "indicators", "entry_conditions"}
        assert set(STRATEGY_SCHEMA["required"]) == required_sections

    def test_schema_has_strategy_types(self):
        """Verify schema defines all three strategy types."""
        strategy_types = STRATEGY_SCHEMA["properties"]["metadata"]["properties"]["strategy_type"]["enum"]
        assert set(strategy_types) == {"momentum", "mean_reversion", "factor_combination"}

    def test_schema_has_technical_indicators(self):
        """Verify schema supports required technical indicators."""
        tech_indicators = STRATEGY_SCHEMA["properties"]["indicators"]["properties"]["technical_indicators"]["items"]["properties"]["type"]["enum"]
        required_indicators = {"RSI", "MACD", "BB", "SMA", "EMA"}
        assert required_indicators.issubset(set(tech_indicators))

    def test_schema_has_fundamental_factors(self):
        """Verify schema supports required fundamental factors."""
        fund_factors = STRATEGY_SCHEMA["properties"]["indicators"]["properties"]["fundamental_factors"]["items"]["properties"]["field"]["enum"]
        required_factors = {"ROE", "PB_ratio", "revenue_growth", "debt_ratio"}
        assert required_factors.issubset(set(fund_factors))


class TestValidSpecs:
    """Test validation of valid strategy specifications."""

    def test_valid_momentum_strategy(self):
        """Test validation of basic momentum strategy."""
        spec = {
            "metadata": {
                "name": "Basic Momentum",
                "strategy_type": "momentum",
                "rebalancing_frequency": "W-FRI",
                "version": "1.0.0"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "rsi_14",
                        "type": "RSI",
                        "period": 14,
                        "source": "data.get('RSI_14')"
                    },
                    {
                        "name": "ma_50",
                        "type": "SMA",
                        "period": 50,
                        "source": "data.get('MA_50')"
                    }
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "rsi_14 > 30"},
                    {"condition": "close > ma_50"}
                ],
                "logical_operator": "AND"
            }
        }

        # Should not raise ValidationError
        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_valid_mean_reversion_strategy(self):
        """Test validation of mean reversion strategy."""
        spec = {
            "metadata": {
                "name": "BB Mean Reversion",
                "description": "Bollinger Bands mean reversion with RSI filter",
                "strategy_type": "mean_reversion",
                "rebalancing_frequency": "M",
                "risk_level": "medium"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "bb_lower",
                        "type": "BB",
                        "period": 20,
                        "source": "data.get('BB_LOWER')",
                        "parameters": {
                            "std_dev": 2.0
                        }
                    },
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
                    {"condition": "close < bb_lower"},
                    {"condition": "rsi_14 < 30"}
                ],
                "logical_operator": "AND"
            },
            "exit_conditions": {
                "take_profit_pct": 0.15,
                "stop_loss_pct": 0.08
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_valid_factor_combination_strategy(self):
        """Test validation of factor combination strategy."""
        spec = {
            "metadata": {
                "name": "Quality Growth Value",
                "description": "Multi-factor strategy combining quality, growth, and value",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M",
                "tags": ["factor", "quality", "growth", "value"],
                "risk_level": "low"
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
                    },
                    {
                        "name": "pb_ratio",
                        "field": "PB_ratio",
                        "source": "data.get('PB_ratio')"
                    }
                ],
                "custom_calculations": [
                    {
                        "name": "quality_score",
                        "expression": "roe * (1 + revenue_growth) / pb_ratio",
                        "description": "Combined quality-growth-value score"
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
                "max_positions": 20,
                "max_position_pct": 0.10
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_valid_complex_strategy_with_all_sections(self):
        """Test validation of complex strategy using all schema sections."""
        spec = {
            "metadata": {
                "name": "Advanced Multi-Factor",
                "description": "Comprehensive strategy with all features",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "W-FRI",
                "version": "2.1.0",
                "author": "FinLab System",
                "tags": ["advanced", "multi-factor", "risk-managed"],
                "risk_level": "high"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "rsi_14",
                        "type": "RSI",
                        "period": 14,
                        "source": "data.get('RSI_14')"
                    },
                    {
                        "name": "macd",
                        "type": "MACD",
                        "source": "data.get('MACD')",
                        "parameters": {
                            "fast_period": 12,
                            "slow_period": 26,
                            "signal_period": 9
                        }
                    }
                ],
                "fundamental_factors": [
                    {
                        "name": "roe",
                        "field": "ROE",
                        "source": "data.get('ROE')",
                        "transformation": "winsorize"
                    },
                    {
                        "name": "debt_ratio",
                        "field": "debt_ratio",
                        "source": "data.get('debt_ratio')"
                    }
                ],
                "custom_calculations": [
                    {
                        "name": "composite_score",
                        "expression": "roe * (1 - debt_ratio) * rsi_14 / 100",
                        "description": "Quality-risk-momentum composite"
                    }
                ],
                "volume_filters": [
                    {
                        "name": "avg_volume",
                        "metric": "average_volume",
                        "period": 20,
                        "threshold": 100000000
                    }
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "rsi_14 > 40", "description": "Not oversold"},
                    {"condition": "debt_ratio < 0.6", "description": "Low leverage"}
                ],
                "ranking_rules": [
                    {
                        "field": "composite_score",
                        "method": "top_n",
                        "value": 15,
                        "ascending": False
                    }
                ],
                "logical_operator": "AND",
                "min_liquidity": {
                    "average_volume_20d": 50000000,
                    "dollar_volume": 1000000
                }
            },
            "exit_conditions": {
                "stop_loss_pct": 0.12,
                "take_profit_pct": 0.30,
                "trailing_stop": {
                    "trail_percent": 0.08,
                    "activation_profit": 0.10
                },
                "holding_period_days": 60,
                "conditional_exits": [
                    {"condition": "rsi_14 > 80", "description": "Overbought exit"}
                ],
                "exit_operator": "OR"
            },
            "position_sizing": {
                "method": "factor_weighted",
                "max_positions": 25,
                "max_position_pct": 0.08,
                "min_position_pct": 0.02,
                "weighting_field": "composite_score"
            },
            "risk_management": {
                "max_sector_exposure": 0.25,
                "rebalance_threshold": 0.10,
                "max_drawdown_limit": 0.20,
                "cash_reserve_pct": 0.05
            },
            "backtest_config": {
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 10000000,
                "transaction_cost": 0.001425,
                "slippage": 0.001
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)


class TestInvalidSpecs:
    """Test validation rejection of invalid specifications."""

    def test_missing_required_metadata_fields(self):
        """Test rejection when required metadata fields are missing."""
        spec = {
            "metadata": {
                "name": "Incomplete Strategy"
                # Missing strategy_type and rebalancing_frequency
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "period": 14}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=spec, schema=STRATEGY_SCHEMA)
        assert "'strategy_type' is a required property" in str(exc_info.value)

    def test_invalid_strategy_type(self):
        """Test rejection of invalid strategy type."""
        spec = {
            "metadata": {
                "name": "Invalid Type",
                "strategy_type": "invalid_type",  # Not in enum
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [{"name": "rsi", "type": "RSI", "period": 14}]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=spec, schema=STRATEGY_SCHEMA)
        assert "'invalid_type' is not one of" in str(exc_info.value)

    def test_invalid_rebalancing_frequency(self):
        """Test rejection of invalid rebalancing frequency."""
        spec = {
            "metadata": {
                "name": "Invalid Freq",
                "strategy_type": "momentum",
                "rebalancing_frequency": "DAILY"  # Not in enum
            },
            "indicators": {
                "technical_indicators": [{"name": "rsi", "type": "RSI", "period": 14}]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_missing_indicators_section(self):
        """Test rejection when indicators section is completely missing."""
        spec = {
            "metadata": {
                "name": "No Indicators",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=spec, schema=STRATEGY_SCHEMA)
        assert "'indicators' is a required property" in str(exc_info.value)

    def test_empty_indicators_section(self):
        """Test rejection when indicators section is empty."""
        spec = {
            "metadata": {
                "name": "Empty Indicators",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {},  # Empty - violates minProperties: 1
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_invalid_indicator_name_pattern(self):
        """Test rejection of invalid indicator naming (must be lowercase snake_case)."""
        spec = {
            "metadata": {
                "name": "Invalid Names",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "RSI-14",  # Invalid: contains hyphen, uppercase
                        "type": "RSI",
                        "period": 14
                    }
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "RSI-14 > 30"}]
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_invalid_period_range(self):
        """Test rejection of periods outside valid range."""
        spec = {
            "metadata": {
                "name": "Invalid Period",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {
                        "name": "rsi_invalid",
                        "type": "RSI",
                        "period": 500  # Exceeds maximum of 250
                    }
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi_invalid > 30"}]
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=spec, schema=STRATEGY_SCHEMA)
        assert "500 is greater than the maximum" in str(exc_info.value)

    def test_invalid_stop_loss_range(self):
        """Test rejection of stop loss outside valid range."""
        spec = {
            "metadata": {
                "name": "Invalid Stop Loss",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "period": 14}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            },
            "exit_conditions": {
                "stop_loss_pct": 0.75  # Exceeds maximum of 0.50
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_invalid_ranking_method(self):
        """Test rejection of invalid ranking method."""
        spec = {
            "metadata": {
                "name": "Invalid Ranking",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "fundamental_factors": [
                    {"name": "roe", "field": "ROE"}
                ]
            },
            "entry_conditions": {
                "ranking_rules": [
                    {
                        "field": "roe",
                        "method": "invalid_method",  # Not in enum
                        "value": 20
                    }
                ]
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_missing_entry_conditions(self):
        """Test rejection when entry_conditions is missing."""
        spec = {
            "metadata": {
                "name": "No Entry Conditions",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "period": 14}
                ]
            }
            # Missing entry_conditions
        }

        with pytest.raises(ValidationError) as exc_info:
            validate(instance=spec, schema=STRATEGY_SCHEMA)
        assert "'entry_conditions' is a required property" in str(exc_info.value)

    def test_empty_entry_conditions(self):
        """Test rejection when entry_conditions has no rules."""
        spec = {
            "metadata": {
                "name": "Empty Entry",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "period": 14}
                ]
            },
            "entry_conditions": {}  # Empty - violates minProperties: 1
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)


class TestEdgeCases:
    """Test edge cases and boundary values."""

    def test_minimum_valid_spec(self):
        """Test minimal valid specification with only required fields."""
        spec = {
            "metadata": {
                "name": "Minimal",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI"}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "rsi > 30"}
                ]
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_maximum_indicators(self):
        """Test specification with maximum number of indicators (20 technical)."""
        indicators = [
            {"name": f"indicator_{i}", "type": "RSI", "period": 14}
            for i in range(20)
        ]

        spec = {
            "metadata": {
                "name": "Max Indicators",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": indicators
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "indicator_0 > 30"}]
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_exceeds_maximum_indicators(self):
        """Test rejection when exceeding maximum indicators (21 > 20)."""
        indicators = [
            {"name": f"indicator_{i}", "type": "RSI", "period": 14}
            for i in range(21)
        ]

        spec = {
            "metadata": {
                "name": "Too Many Indicators",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": indicators
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "indicator_0 > 30"}]
            }
        }

        with pytest.raises(ValidationError):
            validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_boundary_values_for_percentages(self):
        """Test boundary values (0.0 and 1.0) for percentage fields."""
        spec = {
            "metadata": {
                "name": "Boundary Values",
                "strategy_type": "momentum",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "rsi", "type": "RSI", "period": 14}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [{"condition": "rsi > 30"}]
            },
            "exit_conditions": {
                "stop_loss_pct": 0.01,  # Minimum
                "take_profit_pct": 2.0   # Maximum
            },
            "position_sizing": {
                "method": "equal_weight",
                "max_position_pct": 1.0   # Maximum
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_complex_custom_expression(self):
        """Test validation of complex custom calculation expression."""
        spec = {
            "metadata": {
                "name": "Complex Expression",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "M"
            },
            "indicators": {
                "fundamental_factors": [
                    {"name": "roe", "field": "ROE"},
                    {"name": "revenue_growth", "field": "revenue_growth"},
                    {"name": "debt_ratio", "field": "debt_ratio"}
                ],
                "custom_calculations": [
                    {
                        "name": "complex_score",
                        "expression": "(roe ** 0.5) * (1 + revenue_growth) / (1 + debt_ratio) * 100",
                        "description": "Multi-factor quality score with power transformation"
                    }
                ]
            },
            "entry_conditions": {
                "ranking_rules": [
                    {
                        "field": "complex_score",
                        "method": "percentile_range",
                        "percentile_min": 80,
                        "percentile_max": 100
                    }
                ]
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_all_position_sizing_methods(self):
        """Test validation of all position sizing methods."""
        methods = [
            ("equal_weight", {}),
            ("factor_weighted", {"weighting_field": "roe"}),
            ("risk_parity", {}),
            ("volatility_weighted", {}),
            ("custom_formula", {"custom_formula": "roe / roe.sum()"})
        ]

        for method, extra_params in methods:
            spec = {
                "metadata": {
                    "name": f"Test {method}",
                    "strategy_type": "momentum",
                    "rebalancing_frequency": "M"
                },
                "indicators": {
                    "fundamental_factors": [
                        {"name": "roe", "field": "ROE"}
                    ]
                },
                "entry_conditions": {
                    "threshold_rules": [{"condition": "roe > 0.10"}]
                },
                "position_sizing": {
                    "method": method,
                    **extra_params
                }
            }

            validate(instance=spec, schema=STRATEGY_SCHEMA)


class TestStrategyCoverage:
    """Test schema coverage of real-world strategy patterns (85% target)."""

    def test_turtle_trading_pattern(self):
        """Test schema can express turtle trading pattern."""
        spec = {
            "metadata": {
                "name": "Turtle Trading",
                "strategy_type": "momentum",
                "rebalancing_frequency": "W-FRI"
            },
            "indicators": {
                "technical_indicators": [
                    {"name": "high_20", "type": "SMA", "period": 20},
                    {"name": "atr_20", "type": "ATR", "period": 20}
                ]
            },
            "entry_conditions": {
                "threshold_rules": [
                    {"condition": "close > high_20"}
                ]
            },
            "exit_conditions": {
                "trailing_stop": {
                    "trail_percent": 0.10,
                    "activation_profit": 0.0
                },
                "holding_period_days": 90
            },
            "position_sizing": {
                "method": "volatility_weighted"
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_value_investing_pattern(self):
        """Test schema can express value investing pattern."""
        spec = {
            "metadata": {
                "name": "Graham Value",
                "strategy_type": "factor_combination",
                "rebalancing_frequency": "Q"
            },
            "indicators": {
                "fundamental_factors": [
                    {"name": "pe_ratio", "field": "PE_ratio"},
                    {"name": "pb_ratio", "field": "PB_ratio"},
                    {"name": "dividend_yield", "field": "dividend_yield"}
                ],
                "custom_calculations": [
                    {
                        "name": "value_score",
                        "expression": "dividend_yield / (pe_ratio * pb_ratio)"
                    }
                ]
            },
            "entry_conditions": {
                "ranking_rules": [
                    {
                        "field": "value_score",
                        "method": "top_percent",
                        "value": 10,
                        "ascending": False
                    }
                ],
                "threshold_rules": [
                    {"condition": "pe_ratio < 15"},
                    {"condition": "pb_ratio < 1.5"}
                ]
            },
            "position_sizing": {
                "method": "equal_weight",
                "max_positions": 30
            }
        }

        validate(instance=spec, schema=STRATEGY_SCHEMA)

    def test_pairs_trading_pattern(self):
        """Test schema limitations - pairs trading requires multiple symbols (out of scope)."""
        # This test documents that pairs trading is NOT covered by current schema
        # which is acceptable as we target 85% coverage, not 100%
        pass

    def test_options_strategy_pattern(self):
        """Test schema limitations - options strategies are out of scope."""
        # This test documents that options strategies are NOT covered
        # Schema focuses on equity long/short strategies only
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
