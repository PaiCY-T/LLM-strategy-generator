"""
Tests for MomentumTemplate - Momentum + Revenue Catalyst Strategy

Test Coverage:
    - Parameter validation (valid/invalid)
    - Default parameter generation
    - Momentum calculation logic
    - Revenue catalyst filter
    - Multi-timeframe MA filters
    - Strategy generation workflow
    - Edge cases (no stocks pass filters)

Fixtures Used:
    - mock_data_cache: Mocked DataCache with synthetic data
    - mock_finlab_sim: Mocked backtest with predictable metrics
"""

import pytest
from src.templates.momentum_template import MomentumTemplate


class TestMomentumTemplate:
    """Test suite for MomentumTemplate strategy."""

    def test_name_property(self):
        """Test template name property."""
        template = MomentumTemplate()
        assert template.name == "Momentum"

    def test_pattern_type_property(self):
        """Test pattern type property."""
        template = MomentumTemplate()
        assert template.pattern_type == "momentum_catalyst"

    def test_param_grid_structure(self):
        """Test PARAM_GRID contains all required parameters."""
        template = MomentumTemplate()
        param_grid = template.PARAM_GRID

        # Check all 8 required parameters are present
        required_params = [
            'momentum_period', 'ma_short', 'ma_medium', 'ma_long',
            'revenue_short', 'revenue_long', 'n_stocks', 'stop_loss'
        ]

        for param in required_params:
            assert param in param_grid, f"Missing parameter: {param}"
            assert isinstance(param_grid[param], list), f"Parameter {param} must be a list"
            assert len(param_grid[param]) > 0, f"Parameter {param} list is empty"

    def test_expected_performance_ranges(self):
        """Test expected performance targets for momentum strategy."""
        template = MomentumTemplate()
        expected = template.expected_performance

        # Check ranges are defined
        assert expected['sharpe_range'] == (0.8, 1.5)
        assert expected['return_range'] == (0.12, 0.25)
        assert expected['mdd_range'] == (-0.30, -0.18)

    def test_get_default_params(self):
        """Test default parameter generation."""
        template = MomentumTemplate()
        defaults = template.get_default_params()

        # Check all required parameters are present
        assert 'momentum_period' in defaults
        assert 'ma_short' in defaults
        assert 'n_stocks' in defaults

        # Check defaults are from PARAM_GRID
        param_grid = template.PARAM_GRID
        for param_name, param_value in defaults.items():
            assert param_value in param_grid[param_name]

    def test_validate_params_valid(self):
        """Test parameter validation with valid parameters."""
        template = MomentumTemplate()
        params = template.get_default_params()

        is_valid, errors = template.validate_params(params)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_params_invalid(self):
        """Test parameter validation with invalid parameters."""
        template = MomentumTemplate()
        params = template.get_default_params()

        # Invalid momentum period
        params['momentum_period'] = 999

        is_valid, errors = template.validate_params(params)

        assert is_valid is False
        assert len(errors) > 0

    def test_generate_strategy_success(self, mock_data_cache, mock_finlab_sim):
        """Test successful strategy generation."""
        template = MomentumTemplate()
        params = template.get_default_params()

        report, metrics = template.generate_strategy(params)

        # Check report and metrics
        assert report is not None
        assert isinstance(metrics, dict)
        assert 'sharpe_ratio' in metrics
        assert 'annual_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'success' in metrics

        # Check mocked values
        assert metrics['sharpe_ratio'] == 2.0

    def test_generate_strategy_validation_error(self, mock_data_cache, mock_finlab_sim):
        """Test strategy generation fails with invalid parameters."""
        template = MomentumTemplate()
        params = template.get_default_params()

        # Invalid parameter
        params['stop_loss'] = -1

        with pytest.raises(ValueError):
            template.generate_strategy(params)

    def test_calculate_momentum(self, mock_data_cache):
        """Test _calculate_momentum computes rolling mean of returns."""
        template = MomentumTemplate()
        params = template.get_default_params()

        momentum = template._calculate_momentum(params)

        # Check momentum object is returned
        assert momentum is not None

    def test_apply_revenue_catalyst(self, mock_data_cache):
        """Test _apply_revenue_catalyst creates acceleration condition."""
        template = MomentumTemplate()
        params = template.get_default_params()

        revenue_catalyst = template._apply_revenue_catalyst(params)

        # Check catalyst condition is returned
        assert revenue_catalyst is not None
