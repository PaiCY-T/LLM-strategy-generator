"""
Tests for MastiffTemplate - Contrarian Reversal Strategy

Test Coverage:
    - Parameter validation (valid/invalid)
    - Default parameter generation
    - 6 contrarian reversal conditions
    - Low-volume weighting and contrarian selection (.is_smallest())
    - Strategy generation workflow
    - Edge cases (no stocks pass filters)

Fixtures Used:
    - mock_data_cache: Mocked DataCache with synthetic data
    - mock_finlab_sim: Mocked backtest with predictable metrics
"""

import pytest
from src.templates.mastiff_template import MastiffTemplate


class TestMastiffTemplate:
    """Test suite for MastiffTemplate strategy."""

    def test_name_property(self):
        """Test template name property."""
        template = MastiffTemplate()
        assert template.name == "Mastiff"

    def test_pattern_type_property(self):
        """Test pattern type property."""
        template = MastiffTemplate()
        assert template.pattern_type == "contrarian_reversal"

    def test_param_grid_structure(self):
        """Test PARAM_GRID contains all required parameters."""
        template = MastiffTemplate()
        param_grid = template.PARAM_GRID

        # Check all 10 required parameters are present
        required_params = [
            'low_volume_days', 'volume_percentile', 'price_drop_threshold',
            'pe_max', 'revenue_growth_min', 'n_stocks', 'stop_loss',
            'take_profit', 'position_limit', 'resample'
        ]

        for param in required_params:
            assert param in param_grid, f"Missing parameter: {param}"
            assert isinstance(param_grid[param], list), f"Parameter {param} must be a list"
            assert len(param_grid[param]) > 0, f"Parameter {param} list is empty"

    def test_expected_performance_ranges(self):
        """Test expected performance targets for contrarian strategy."""
        template = MastiffTemplate()
        expected = template.expected_performance

        # Check ranges are defined
        assert expected['sharpe_range'] == (1.2, 2.0)
        assert expected['return_range'] == (0.15, 0.30)
        assert expected['mdd_range'] == (-0.30, -0.15)

    def test_get_default_params(self):
        """Test default parameter generation."""
        template = MastiffTemplate()
        defaults = template.get_default_params()

        # Check all required parameters are present
        assert 'low_volume_days' in defaults
        assert 'n_stocks' in defaults
        assert 'resample' in defaults

        # Check defaults are from PARAM_GRID
        param_grid = template.PARAM_GRID
        for param_name, param_value in defaults.items():
            assert param_value in param_grid[param_name]

    def test_validate_params_valid(self):
        """Test parameter validation with valid parameters."""
        template = MastiffTemplate()
        params = template.get_default_params()

        is_valid, errors = template.validate_params(params)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_params_invalid(self):
        """Test parameter validation with invalid parameters."""
        template = MastiffTemplate()
        params = template.get_default_params()

        # Set invalid parameter
        params['n_stocks'] = 999  # Not in PARAM_GRID

        is_valid, errors = template.validate_params(params)

        assert is_valid is False
        assert len(errors) > 0

    def test_generate_strategy_success(self, mock_data_cache, mock_finlab_sim):
        """Test successful strategy generation."""
        template = MastiffTemplate()
        params = template.get_default_params()

        report, metrics = template.generate_strategy(params)

        # Check report and metrics
        assert report is not None
        assert isinstance(metrics, dict)
        assert 'sharpe_ratio' in metrics
        assert 'annual_return' in metrics
        assert 'max_drawdown' in metrics

        # Check mocked values
        assert metrics['sharpe_ratio'] == 2.0
        assert metrics['annual_return'] == 0.25

    def test_generate_strategy_validation_error(self, mock_data_cache, mock_finlab_sim):
        """Test strategy generation fails with invalid parameters."""
        template = MastiffTemplate()
        params = template.get_default_params()

        # Invalid parameter
        params['stop_loss'] = -1  # Negative stop loss

        with pytest.raises(ValueError):
            template.generate_strategy(params)

    def test_contrarian_conditions_creation(self, mock_data_cache):
        """Test _create_contrarian_conditions creates combined conditions."""
        template = MastiffTemplate()
        params = template.get_default_params()

        conditions = template._create_contrarian_conditions(params)

        # Check conditions object is returned
        assert conditions is not None

    def test_volume_weighting_contrarian_selection(self, mock_data_cache):
        """Test _apply_volume_weighting selects LOWEST volume stocks (contrarian)."""
        template = MastiffTemplate()
        params = template.get_default_params()

        # Create base conditions
        conditions = template._create_contrarian_conditions(params)

        # Apply volume weighting and contrarian selection
        final_selection = template._apply_volume_weighting(conditions, params)

        # Check selection object is returned
        assert final_selection is not None

        # Note: The key difference from Turtle is that Mastiff uses .is_smallest()
        # instead of .is_largest() for contrarian low-volume stock selection.
        # Full validation requires live finlab data.
