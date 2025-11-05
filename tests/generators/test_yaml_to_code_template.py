"""
Tests for YAML to Code Template Generator
==========================================

Comprehensive test suite for YAMLToCodeTemplate class covering:
- Basic code generation for all strategy types
- Indicator mapping (technical, fundamental, custom)
- Entry/exit condition generation
- Position sizing methods (all 5 types)
- Syntax validation
- Edge cases and error handling

Coverage Target: >90%
"""

import ast
import pytest
from src.generators.yaml_to_code_template import YAMLToCodeTemplate


class TestYAMLToCodeTemplateBasics:
    """Test basic functionality and initialization."""

    def test_initialization(self):
        """Test that generator initializes correctly."""
        generator = YAMLToCodeTemplate()

        assert generator.jinja_env is not None
        assert generator.strategy_template is not None
        assert 'safe_var' in generator.jinja_env.filters
        assert 'format_condition' in generator.jinja_env.filters
        assert 'format_number' in generator.jinja_env.filters

    def test_minimal_spec_generation(self):
        """Test generation with minimal required fields."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Minimal Test Strategy',
                'description': 'A minimal test strategy',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'rsi_14 > 30'}
                ],
                'logical_operator': 'AND'
            }
        }

        code = generator.generate(spec)

        # Verify code is syntactically correct
        ast.parse(code)

        # Verify key elements are present
        assert 'def strategy(data):' in code
        assert 'rsi_14 = data.get(\'RSI_14\')' in code
        assert 'filter_1 = (rsi_14 > 30)' in code
        assert 'return position' in code

    def test_spec_validation_missing_metadata(self):
        """Test that missing metadata raises ValueError."""
        generator = YAMLToCodeTemplate()

        spec = {
            'indicators': {},
            'entry_conditions': {}
        }

        with pytest.raises(ValueError, match="missing required fields: metadata"):
            generator.generate(spec)

    def test_spec_validation_missing_indicators(self):
        """Test that missing indicators raises ValueError."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Test',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'entry_conditions': {}
        }

        with pytest.raises(ValueError, match="missing required fields: indicators"):
            generator.generate(spec)

    def test_spec_validation_missing_entry_conditions(self):
        """Test that missing entry_conditions raises ValueError."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Test',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {}
        }

        with pytest.raises(ValueError, match="missing required fields: entry_conditions"):
            generator.generate(spec)

    def test_spec_validation_incomplete_metadata(self):
        """Test that incomplete metadata raises ValueError."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Test'
                # Missing strategy_type and rebalancing_frequency
            },
            'indicators': {},
            'entry_conditions': {}
        }

        with pytest.raises(ValueError, match="Metadata missing required fields"):
            generator.generate(spec)


class TestIndicatorGeneration:
    """Test indicator section generation."""

    def test_technical_indicators(self):
        """Test generation of technical indicators."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Technical Test',
                'description': 'Test technical indicators',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'W-FRI'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    },
                    {
                        'name': 'ma_50',
                        'type': 'SMA',
                        'period': 50,
                        'source': "data.get('MA_50')"
                    },
                    {
                        'name': 'macd',
                        'type': 'MACD',
                        'source': "data.get('MACD')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "rsi_14 = data.get('RSI_14')  # RSI (period=14)" in code
        assert "ma_50 = data.get('MA_50')  # SMA (period=50)" in code
        assert "macd = data.get('MACD')  # MACD" in code

    def test_fundamental_factors(self):
        """Test generation of fundamental factors."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Fundamental Test',
                'description': 'Test fundamental factors',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')",
                        'transformation': 'none'
                    },
                    {
                        'name': 'revenue_growth',
                        'field': 'revenue_growth',
                        'source': "data.get('revenue_growth')",
                        'transformation': 'winsorize'
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'roe > 0.15'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "roe_raw = data.get('ROE')  # ROE" in code
        assert "roe = roe_raw" in code
        assert "revenue_growth_raw = data.get('revenue_growth')  # revenue_growth" in code
        assert "revenue_growth = revenue_growth_raw.clip" in code

    def test_fundamental_transformations(self):
        """Test all fundamental factor transformations."""
        generator = YAMLToCodeTemplate()

        transformations = ['log', 'sqrt', 'rank', 'zscore', 'winsorize']

        for transform in transformations:
            spec = {
                'metadata': {
                    'name': f'Transform Test {transform}',
                    'description': f'Test {transform} transformation',
                    'strategy_type': 'factor_combination',
                    'rebalancing_frequency': 'M'
                },
                'indicators': {
                    'fundamental_factors': [
                        {
                            'name': 'test_factor',
                            'field': 'ROE',
                            'source': "data.get('ROE')",
                            'transformation': transform
                        }
                    ]
                },
                'entry_conditions': {
                    'threshold_rules': [{'condition': 'test_factor > 0'}]
                }
            }

            code = generator.generate(spec)
            ast.parse(code)  # Verify syntax

            assert "test_factor_raw = data.get('ROE')" in code
            assert "test_factor =" in code

    def test_custom_calculations(self):
        """Test generation of custom calculations."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Custom Calc Test',
                'description': 'Test custom calculations',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    },
                    {
                        'name': 'debt_ratio',
                        'field': 'debt_ratio',
                        'source': "data.get('debt_ratio')"
                    }
                ],
                'custom_calculations': [
                    {
                        'name': 'quality_score',
                        'expression': 'roe * (1 - debt_ratio)',
                        'description': 'Quality score with leverage adjustment'
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'quality_score > 0.10'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "quality_score = roe * (1 - debt_ratio)" in code
        assert "Quality score with leverage adjustment" in code

    def test_volume_filters(self):
        """Test generation of volume filters."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Volume Test',
                'description': 'Test volume filters',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'W-FRI'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ],
                'volume_filters': [
                    {
                        'name': 'avg_volume_20',
                        'metric': 'average_volume',
                        'period': 20,
                        'threshold': 100000000
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "avg_volume_20 = volume.rolling(20).mean()" in code


class TestEntryConditions:
    """Test entry condition generation."""

    def test_threshold_rules_single(self):
        """Test single threshold rule generation."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Threshold Test',
                'description': 'Test threshold rules',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {
                        'condition': 'rsi_14 > 30',
                        'description': 'RSI above oversold'
                    }
                ],
                'logical_operator': 'AND'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "filter_1 = (rsi_14 > 30)  # RSI above oversold" in code
        assert "threshold_mask = filter_1" in code

    def test_threshold_rules_multiple_and(self):
        """Test multiple threshold rules with AND logic."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Multiple AND Test',
                'description': 'Test multiple AND rules',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    },
                    {
                        'name': 'ma_50',
                        'type': 'SMA',
                        'period': 50,
                        'source': "data.get('MA_50')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'rsi_14 > 30'},
                    {'condition': 'close > ma_50'},
                    {'condition': 'rsi_14 < 70'}
                ],
                'logical_operator': 'AND'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "filter_1 = (rsi_14 > 30)" in code
        assert "filter_2 = (close > ma_50)" in code
        assert "filter_3 = (rsi_14 < 70)" in code
        assert "threshold_mask = filter_1 & filter_2 & filter_3" in code

    def test_threshold_rules_multiple_or(self):
        """Test multiple threshold rules with OR logic."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Multiple OR Test',
                'description': 'Test multiple OR rules',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'rsi_14 > 70'},
                    {'condition': 'rsi_14 < 30'}
                ],
                'logical_operator': 'OR'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "filter_1 = (rsi_14 > 70)" in code
        assert "filter_2 = (rsi_14 < 30)" in code
        assert "threshold_mask = filter_1 | filter_2" in code

    def test_ranking_rules_top_percent(self):
        """Test ranking rule with top_percent method."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Ranking Test',
                'description': 'Test ranking rules',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'roe',
                        'method': 'top_percent',
                        'value': 20,
                        'ascending': False
                    }
                ]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "rank_1 = roe.rank(axis=1, ascending=False, pct=True)" in code
        assert "ranking_mask_1 = rank_1 <= 0.2" in code

    def test_ranking_rules_top_n(self):
        """Test ranking rule with top_n method."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Top N Test',
                'description': 'Test top N ranking',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'quality_score',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'quality_score',
                        'method': 'top_n',
                        'value': 30,
                        'ascending': False
                    }
                ]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "ranking_mask_1 = quality_score[threshold_mask].is_largest(30)" in code

    def test_ranking_rules_percentile_range(self):
        """Test ranking rule with percentile_range method."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Percentile Range Test',
                'description': 'Test percentile range ranking',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'momentum',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'momentum',
                        'method': 'percentile_range',
                        'percentile_min': 50,
                        'percentile_max': 80,
                        'ascending': True
                    }
                ]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "rank_1 = momentum.rank(axis=1, ascending=True, pct=True)" in code
        assert "ranking_mask_1 = (rank_1 >= 0.5) & (rank_1 <= 0.8)" in code

    def test_liquidity_filters(self):
        """Test liquidity filter generation."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Liquidity Test',
                'description': 'Test liquidity filters',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'rsi_14 > 30'}
                ],
                'min_liquidity': {
                    'average_volume_20d': 100000000,
                    'dollar_volume': 5000000
                }
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "liquidity_filter_volume = volume.rolling(20).mean() > 100000000" in code
        assert "liquidity_filter_dollar = (close * volume) > 5000000" in code
        assert "threshold_mask = threshold_mask & liquidity_filter_volume" in code
        assert "threshold_mask = threshold_mask & liquidity_filter_dollar" in code


class TestPositionSizing:
    """Test position sizing generation."""

    def test_equal_weight(self):
        """Test equal weight position sizing."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Equal Weight Test',
                'description': 'Test equal weight sizing',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            },
            'position_sizing': {
                'method': 'equal_weight',
                'max_positions': 20
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Equal weight across all positions" in code
        assert "position = entry_mask.astype(float)" in code
        assert "position = position / position.sum(axis=1).values.reshape(-1, 1)" in code

    def test_factor_weighted(self):
        """Test factor weighted position sizing."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Factor Weight Test',
                'description': 'Test factor weighted sizing',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'quality_score',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'quality_score > 0.10'}]
            },
            'position_sizing': {
                'method': 'factor_weighted',
                'weighting_field': 'quality_score',
                'max_positions': 30
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Weight by factor score" in code
        assert "weights = quality_score[entry_mask]" in code
        assert "weights = weights / weights.sum(axis=1).values.reshape(-1, 1)" in code

    def test_risk_parity(self):
        """Test risk parity position sizing."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Risk Parity Test',
                'description': 'Test risk parity sizing',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            },
            'position_sizing': {
                'method': 'risk_parity'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Risk parity (inverse volatility weighting)" in code
        assert "returns = close.pct_change()" in code
        assert "volatility = returns.rolling(60).std()" in code
        assert "inv_vol = 1.0 / volatility" in code

    def test_volatility_weighted(self):
        """Test volatility weighted position sizing."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Vol Weight Test',
                'description': 'Test volatility weighted sizing',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            },
            'position_sizing': {
                'method': 'volatility_weighted'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Volatility-weighted (inverse volatility)" in code
        assert "volatility = returns.rolling(60).std()" in code

    def test_custom_formula(self):
        """Test custom formula position sizing."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Custom Formula Test',
                'description': 'Test custom formula sizing',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    },
                    {
                        'name': 'momentum',
                        'field': 'revenue_growth',
                        'source': "data.get('revenue_growth')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'roe > 0.10'}]
            },
            'position_sizing': {
                'method': 'custom_formula',
                'custom_formula': 'roe * momentum'
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Custom position sizing formula" in code
        assert "custom_weights = roe * momentum" in code

    def test_position_size_limits(self):
        """Test max/min position size limits."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Position Limits Test',
                'description': 'Test position size limits',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            },
            'position_sizing': {
                'method': 'equal_weight',
                'max_position_pct': 0.10,
                'min_position_pct': 0.01
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# Apply maximum position size limit" in code
        assert "position = position.clip(upper=0.1)" in code
        assert "# Filter out positions below minimum size" in code
        assert "position = position.where(position >= 0.01, 0)" in code


class TestCompleteStrategies:
    """Test generation of complete strategy examples."""

    def test_momentum_strategy_complete(self):
        """Test complete momentum strategy from YAML example."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'RSI Momentum Test Strategy',
                'description': 'Basic momentum strategy using RSI indicator',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'W-FRI',
                'version': '1.0.0',
                'risk_level': 'medium'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    },
                    {
                        'name': 'ma_50',
                        'type': 'SMA',
                        'period': 50,
                        'source': "data.get('MA_50')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'rsi_14 > 50', 'description': 'RSI shows upward momentum'},
                    {'condition': 'close > ma_50', 'description': 'Price above 50-day MA'}
                ],
                'logical_operator': 'AND',
                'min_liquidity': {
                    'average_volume_20d': 100000000
                }
            },
            'position_sizing': {
                'method': 'equal_weight',
                'max_positions': 20,
                'max_position_pct': 0.10
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        # Verify all sections are present
        assert 'def strategy(data):' in code
        assert "rsi_14 = data.get('RSI_14')" in code
        assert "ma_50 = data.get('MA_50')" in code
        assert 'filter_1 = (rsi_14 > 50)' in code
        assert 'filter_2 = (close > ma_50)' in code
        assert 'liquidity_filter_volume' in code
        assert 'position = entry_mask.astype(float)' in code
        assert 'return position' in code

    def test_factor_combination_complete(self):
        """Test complete factor combination strategy."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Quality Growth Combo',
                'description': 'Factor combination with quality and growth',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')",
                        'transformation': 'winsorize'
                    },
                    {
                        'name': 'revenue_growth',
                        'field': 'revenue_growth',
                        'source': "data.get('revenue_growth')"
                    }
                ],
                'custom_calculations': [
                    {
                        'name': 'quality_score',
                        'expression': 'roe * (1 + revenue_growth)',
                        'description': 'Combined quality and growth score'
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'quality_score',
                        'method': 'top_percent',
                        'value': 20,
                        'ascending': False
                    }
                ],
                'threshold_rules': [
                    {'condition': 'roe > 0.15'},
                    {'condition': 'revenue_growth > 0.05'}
                ],
                'logical_operator': 'AND'
            },
            'position_sizing': {
                'method': 'factor_weighted',
                'weighting_field': 'quality_score',
                'max_positions': 30,
                'max_position_pct': 0.08
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        # Verify factor combination specific elements
        assert "roe_raw = data.get('ROE')" in code
        assert "roe = roe_raw.clip" in code
        assert "quality_score = roe * (1 + revenue_growth)" in code
        assert "rank_1 = quality_score.rank" in code
        assert "weights = quality_score[entry_mask]" in code


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_indicators_section(self):
        """Test handling of empty indicators section."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'Empty Indicators Test',
                'description': 'Test with no indicators',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {},
            'entry_conditions': {
                'threshold_rules': [{'condition': 'True'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        # Should still generate valid code even with empty indicators
        assert 'def strategy(data):' in code

    def test_no_ranking_rules(self):
        """Test strategy with only threshold rules, no ranking."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'No Ranking Test',
                'description': 'Test without ranking rules',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [{'condition': 'rsi_14 > 30'}]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "# No ranking rules - use threshold mask only" in code
        assert "entry_mask = threshold_mask" in code

    def test_no_threshold_rules(self):
        """Test strategy with only ranking rules, no thresholds."""
        generator = YAMLToCodeTemplate()

        spec = {
            'metadata': {
                'name': 'No Threshold Test',
                'description': 'Test without threshold rules',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'fundamental_factors': [
                    {
                        'name': 'roe',
                        'field': 'ROE',
                        'source': "data.get('ROE')"
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'roe',
                        'method': 'top_n',
                        'value': 20
                    }
                ]
            }
        }

        code = generator.generate(spec)
        ast.parse(code)

        assert "threshold_mask = True" in code
        assert "ranking_mask" in code

    def test_number_formatting(self):
        """Test that numbers are formatted correctly."""
        generator = YAMLToCodeTemplate()

        # Test integer formatting
        assert generator._format_number(20) == "20"

        # Test float formatting
        assert generator._format_number(0.15) == "0.150000"
        assert generator._format_number(100000000.0) == "100000000.000000"

    def test_safe_variable_name_filter(self):
        """Test safe variable name filter."""
        generator = YAMLToCodeTemplate()

        assert generator._safe_variable_name("test_var") == "test_var"
        assert generator._safe_variable_name("Test_Var") == "test_var"
        assert generator._safe_variable_name("test-var") == "test_var"

    def test_format_condition_filter(self):
        """Test condition formatting filter."""
        generator = YAMLToCodeTemplate()

        condition = "rsi_14 > 30"
        assert generator._format_condition(condition) == condition


class TestSyntaxValidation:
    """Test syntax validation functionality."""

    def test_valid_syntax_passes(self):
        """Test that valid Python code passes syntax check."""
        generator = YAMLToCodeTemplate()

        valid_code = """
def strategy(data):
    close = data.get('price:收盤價')
    return close
"""
        # Should not raise
        generator._validate_syntax(valid_code)

    def test_invalid_syntax_raises(self):
        """Test that invalid Python code raises SyntaxError."""
        generator = YAMLToCodeTemplate()

        invalid_code = """
def strategy(data):
    close = data.get('price:收盤價'
    return close
"""
        with pytest.raises(SyntaxError, match="Generated code has syntax errors"):
            generator._validate_syntax(invalid_code)
