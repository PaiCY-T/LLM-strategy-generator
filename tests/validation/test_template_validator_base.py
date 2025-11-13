"""
Unit Tests for TemplateValidator Base Class - Tasks 26-29
==========================================================

Tests for the three new validation methods added to TemplateValidator:
    - validate_diversity(): Ensure >= 80% unique strategies (Task 27)
    - validate_performance(): Validate metrics against thresholds (Task 28)
    - validate_params(): Validate parameter types, ranges, required fields (Task 29)

Test Coverage:
    - Diversity validation with Levenshtein distance
    - Performance validation with min_sharpe and metric bounds
    - Parameter validation with schema-based checks
    - Edge cases and error handling
"""

import pytest
from src.validation.template_validator import TemplateValidator


class TestValidateDiversity:
    """Test validate_diversity() method - Task 27."""

    def test_diversity_pass_all_unique(self):
        """Test diversity validation passes when all strategies are unique."""
        validator = TemplateValidator()

        strategy_codes = [
            "close = data.get('price:收盤價')\nbuy = close > close.shift(20)",
            "pe = data.get('price_earning_ratio:本益比')\nbuy = pe < 15",
            "dividend = data.get('price_earning_ratio:殖利率(%)')\nbuy = dividend > 6",
            "revenue = data.get('monthly_revenue:當月營收')\nbuy = revenue > revenue.shift(12)",
        ]

        result = validator.validate_diversity(strategy_codes, min_unique_ratio=0.8)

        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert result['metrics']['total_strategies'] == 4
        assert result['metrics']['unique_ratio'] >= 0.8
        assert result['metrics']['min_distance'] > 0.2

    def test_diversity_fail_too_many_duplicates(self):
        """Test diversity validation fails when too many duplicates."""
        validator = TemplateValidator()

        # Create 10 strategies where 5 are nearly identical (50% duplicates > 20% threshold)
        base_code = "close = data.get('price:收盤價')\nbuy = close > close.shift(20)"
        strategy_codes = [
            base_code,  # Original
            base_code + "\n",  # Nearly identical (just whitespace)
            base_code.replace("20", "21"),  # Minor change
            base_code.replace("shift", "shift"),  # Identical
            base_code + " ",  # Nearly identical (trailing space)
            "pe = data.get('price_earning_ratio:本益比')\nbuy = pe < 15",
            "dividend = data.get('price_earning_ratio:殖利率(%)')\nbuy = dividend > 6",
            "revenue = data.get('monthly_revenue:當月營收')\nbuy = revenue > revenue.shift(12)",
            "volume = data.get('price:成交股數')\nbuy = volume > volume.average(60)",
            "roe = data.get('fundamental_features:ROE')\nbuy = roe > 15",
        ]

        result = validator.validate_diversity(strategy_codes, min_unique_ratio=0.8, distance_threshold=0.2)

        # Should fail because we have too many similar strategies
        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert result['metrics']['unique_ratio'] < 0.8
        assert len(result['metrics']['duplicate_pairs']) > 0

    def test_diversity_exact_threshold(self):
        """Test diversity validation at exact 80% threshold (8/10 unique)."""
        validator = TemplateValidator()

        # Create exactly 8 unique and 2 duplicate strategies
        unique_strategies = [
            f"close = data.get('price:收盤價')\nbuy = close > close.shift({i*10})"
            for i in range(8)
        ]
        duplicate_strategies = [
            unique_strategies[0],  # Duplicate of first strategy
            unique_strategies[0],  # Another duplicate
        ]

        strategy_codes = unique_strategies + duplicate_strategies

        result = validator.validate_diversity(strategy_codes, min_unique_ratio=0.8, distance_threshold=0.1)

        # Should pass at exactly 80% threshold
        assert result['metrics']['total_strategies'] == 10

    def test_diversity_empty_input(self):
        """Test diversity validation with empty input."""
        validator = TemplateValidator()

        result = validator.validate_diversity([], min_unique_ratio=0.8)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert "No strategy codes provided" in result['errors'][0]

    def test_diversity_single_strategy(self):
        """Test diversity validation with single strategy (always unique)."""
        validator = TemplateValidator()

        strategy_codes = ["close = data.get('price:收盤價')\nbuy = close > close.shift(20)"]

        result = validator.validate_diversity(strategy_codes, min_unique_ratio=0.8)

        assert result['is_valid'] is True
        assert result['metrics']['unique_strategies'] == 1
        assert result['metrics']['unique_ratio'] == 1.0

    def test_diversity_custom_threshold(self):
        """Test diversity validation with custom distance threshold."""
        validator = TemplateValidator()

        strategy_codes = [
            "close = data.get('price:收盤價')\nbuy = close > close.shift(20)",
            "close = data.get('price:收盤價')\nbuy = close > close.shift(21)",  # Very similar
        ]

        # Strict threshold (0.1) - should fail
        result_strict = validator.validate_diversity(strategy_codes, distance_threshold=0.1)

        # Lenient threshold (0.01) - should pass
        result_lenient = validator.validate_diversity(strategy_codes, distance_threshold=0.01)

        # The strict threshold should detect more duplicates
        assert len(result_strict['metrics']['duplicate_pairs']) >= len(result_lenient['metrics']['duplicate_pairs'])


class TestValidatePerformance:
    """Test validate_performance() method - Task 28."""

    def test_performance_pass_all_metrics(self):
        """Test performance validation passes when all metrics meet thresholds."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 1.8,
            'annual_return': 0.25,
            'max_drawdown': -0.15
        }

        result = validator.validate_performance(
            metrics,
            min_sharpe=1.5,
            sharpe_range=(1.5, 2.5),
            annual_return_range=(0.20, 0.35),
            max_dd_range=(-0.25, -0.10)
        )

        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert result['metrics']['meets_min_sharpe'] is True
        assert result['metrics']['in_sharpe_range'] is True
        assert result['metrics']['in_return_range'] is True
        assert result['metrics']['in_dd_range'] is True

    def test_performance_fail_min_sharpe(self):
        """Test performance validation fails when Sharpe below minimum."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 0.3,
            'annual_return': 0.15,
            'max_drawdown': -0.20
        }

        result = validator.validate_performance(metrics, min_sharpe=0.5)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert result['metrics']['meets_min_sharpe'] is False
        assert "below minimum threshold" in result['errors'][0]

    def test_performance_fail_return_bounds(self):
        """Test performance validation fails when annual return out of bounds."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 1.5,
            'annual_return': 0.05,  # Too low
            'max_drawdown': -0.15
        }

        result = validator.validate_performance(
            metrics,
            min_sharpe=1.0,
            annual_return_range=(0.15, 0.30)
        )

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert result['metrics']['in_return_range'] is False

    def test_performance_fail_drawdown_bounds(self):
        """Test performance validation fails when drawdown exceeds limit."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 1.5,
            'annual_return': 0.20,
            'max_drawdown': -0.35  # Too large drawdown
        }

        result = validator.validate_performance(
            metrics,
            min_sharpe=1.0,
            max_dd_range=(-0.25, -0.10)
        )

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert result['metrics']['in_dd_range'] is False

    def test_performance_warnings_only(self):
        """Test performance validation with warnings but no critical errors."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 1.0,  # Meets min_sharpe but below optimal range
            'annual_return': 0.12,
            'max_drawdown': -0.18
        }

        result = validator.validate_performance(
            metrics,
            min_sharpe=0.8,
            sharpe_range=(1.5, 2.5)  # Outside optimal range
        )

        assert result['is_valid'] is True  # No critical errors
        assert len(result['errors']) == 0
        assert len(result['warnings']) > 0  # Has warnings
        assert result['metrics']['meets_min_sharpe'] is True
        assert result['metrics']['in_sharpe_range'] is False

    def test_performance_missing_sharpe(self):
        """Test performance validation fails when sharpe_ratio missing."""
        validator = TemplateValidator()

        metrics = {
            'annual_return': 0.20,
            'max_drawdown': -0.15
        }

        result = validator.validate_performance(metrics, min_sharpe=1.0)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert "Missing required metric: 'sharpe_ratio'" in result['errors'][0]

    def test_performance_negative_return_warning(self):
        """Test performance validation warns for negative returns."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 0.8,
            'annual_return': -0.05,  # Negative return
            'max_drawdown': -0.20
        }

        result = validator.validate_performance(metrics, min_sharpe=0.5)

        assert result['is_valid'] is True  # Still valid (meets min_sharpe)
        assert len(result['warnings']) > 0
        assert any("negative annual return" in w for w in result['warnings'])

    def test_performance_excessive_drawdown_warning(self):
        """Test performance validation warns for excessive drawdown."""
        validator = TemplateValidator()

        metrics = {
            'sharpe_ratio': 1.5,
            'annual_return': 0.20,
            'max_drawdown': -0.55  # > 50% drawdown
        }

        result = validator.validate_performance(metrics, min_sharpe=1.0)

        assert result['is_valid'] is True  # Still valid (meets min_sharpe)
        assert len(result['warnings']) > 0
        assert any("excessive drawdown" in w for w in result['warnings'])

    def test_performance_turtle_template_ranges(self):
        """Test performance validation with TurtleTemplate expected ranges."""
        validator = TemplateValidator()

        # TurtleTemplate: Sharpe 1.5-2.5, Return 20-35%, MDD -25% to -10%
        metrics = {
            'sharpe_ratio': 2.0,
            'annual_return': 0.28,
            'max_drawdown': -0.18
        }

        result = validator.validate_performance(
            metrics,
            min_sharpe=1.5,
            sharpe_range=(1.5, 2.5),
            annual_return_range=(0.20, 0.35),
            max_dd_range=(-0.25, -0.10)
        )

        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert result['metrics']['meets_min_sharpe'] is True


class TestValidateParams:
    """Test validate_params() method - Task 29."""

    def test_params_pass_all_valid(self):
        """Test parameter validation passes when all parameters are valid."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'required': True,
                'min': 5,
                'max': 50,
                'description': 'Number of stocks'
            },
            'sharpe_threshold': {
                'type': (int, float),
                'required': False,
                'min': 0.0,
                'description': 'Minimum Sharpe'
            }
        }

        params = {
            'n_stocks': 30,
            'sharpe_threshold': 1.5
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is True
        assert len(result['errors']) == 0
        assert result['metrics']['validated_parameters'] == 2
        assert result['metrics']['total_parameters'] == 2

    def test_params_fail_missing_required(self):
        """Test parameter validation fails when required parameter missing."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'required': True,
                'min': 5,
                'max': 50,
                'description': 'Number of stocks'
            }
        }

        params = {}  # Missing n_stocks

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'n_stocks' in result['metrics']['missing_required']
        assert "Missing required parameter" in result['errors'][0]

    def test_params_fail_type_mismatch(self):
        """Test parameter validation fails on type mismatch."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'required': True,
                'description': 'Number of stocks'
            }
        }

        params = {
            'n_stocks': "30"  # String instead of int
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'n_stocks' in result['metrics']['type_errors']
        assert "wrong type" in result['errors'][0]

    def test_params_fail_below_min(self):
        """Test parameter validation fails when value below minimum."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'min': 5,
                'max': 50
            }
        }

        params = {
            'n_stocks': 2  # Below minimum
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'n_stocks' in result['metrics']['range_errors']
        assert "below minimum" in result['errors'][0]

    def test_params_fail_above_max(self):
        """Test parameter validation fails when value above maximum."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'min': 5,
                'max': 50
            }
        }

        params = {
            'n_stocks': 100  # Above maximum
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'n_stocks' in result['metrics']['range_errors']
        assert "exceeds maximum" in result['errors'][0]

    def test_params_fail_invalid_allowed_value(self):
        """Test parameter validation fails when value not in allowed_values."""
        validator = TemplateValidator()

        schema = {
            'resample': {
                'type': str,
                'allowed_values': ['M', 'W-FRI', 'Q']
            }
        }

        params = {
            'resample': 'D'  # Not in allowed values
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is False
        assert len(result['errors']) > 0
        assert 'resample' in result['metrics']['range_errors']
        assert "not in allowed values" in result['errors'][0]

    def test_params_warning_unknown_parameter(self):
        """Test parameter validation warns for unknown parameters."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'min': 5,
                'max': 50
            }
        }

        params = {
            'n_stocks': 30,
            'unknown_param': 123  # Not in schema
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is True  # Still valid
        assert len(result['warnings']) > 0
        assert 'unknown_param' in result['metrics']['unknown_parameters']
        assert "Unknown parameter" in result['warnings'][0]

    def test_params_multiple_type_support(self):
        """Test parameter validation with multiple allowed types."""
        validator = TemplateValidator()

        schema = {
            'threshold': {
                'type': (int, float),  # Both int and float allowed
                'min': 0.0
            }
        }

        # Test with int
        result_int = validator.validate_params({'threshold': 10}, schema)
        assert result_int['is_valid'] is True

        # Test with float
        result_float = validator.validate_params({'threshold': 10.5}, schema)
        assert result_float['is_valid'] is True

        # Test with string (should fail)
        result_str = validator.validate_params({'threshold': "10"}, schema)
        assert result_str['is_valid'] is False

    def test_params_complex_schema(self):
        """Test parameter validation with complex schema (multiple parameters)."""
        validator = TemplateValidator()

        schema = {
            'n_stocks': {
                'type': int,
                'required': True,
                'min': 5,
                'max': 50,
                'description': 'Number of stocks'
            },
            'ma_short': {
                'type': int,
                'required': True,
                'min': 5,
                'max': 60,
                'description': 'Short MA period'
            },
            'ma_long': {
                'type': int,
                'required': True,
                'min': 20,
                'max': 120,
                'description': 'Long MA period'
            },
            'resample': {
                'type': str,
                'required': False,
                'allowed_values': ['M', 'W-FRI', 'Q'],
                'description': 'Resampling frequency'
            }
        }

        params = {
            'n_stocks': 30,
            'ma_short': 20,
            'ma_long': 60,
            'resample': 'M'
        }

        result = validator.validate_params(params, schema)

        assert result['is_valid'] is True
        assert result['metrics']['validated_parameters'] == 4
        assert len(result['errors']) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
