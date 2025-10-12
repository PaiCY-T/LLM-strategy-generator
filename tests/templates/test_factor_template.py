"""
Tests for FactorTemplate - Single-Factor Ranking Strategy

Test Coverage:
    - Parameter validation (valid/invalid)
    - Default parameter generation
    - Factor score calculation (6 factor types)
    - Cross-sectional ranking (ascending/descending)
    - Quality filters application
    - Strategy generation workflow
    - Edge cases (invalid factor type, ranking direction)

Fixtures Used:
    - mock_data_cache: Mocked DataCache with synthetic data
    - mock_finlab_sim: Mocked backtest with predictable metrics
"""

import pytest
from src.templates.factor_template import FactorTemplate


class TestFactorTemplate:
    """Test suite for FactorTemplate strategy."""

    def test_name_property(self):
        """Test template name property."""
        template = FactorTemplate()
        assert template.name == "Factor"

    def test_pattern_type_property(self):
        """Test pattern type property."""
        template = FactorTemplate()
        assert template.pattern_type == "factor_ranking"

    def test_param_grid_structure(self):
        """Test PARAM_GRID contains all required parameters."""
        template = FactorTemplate()
        param_grid = template.PARAM_GRID

        # Check all 7 required parameters are present
        required_params = [
            'factor_type', 'ranking_direction', 'n_stocks',
            'stop_loss', 'take_profit', 'position_limit', 'resample'
        ]

        for param in required_params:
            assert param in param_grid, f"Missing parameter: {param}"
            assert isinstance(param_grid[param], list), f"Parameter {param} must be a list"
            assert len(param_grid[param]) > 0, f"Parameter {param} list is empty"

        # Check factor_type includes all 6 factors
        assert 'pe_ratio' in param_grid['factor_type']
        assert 'pb_ratio' in param_grid['factor_type']
        assert 'roe' in param_grid['factor_type']
        assert 'roa' in param_grid['factor_type']
        assert 'revenue_growth' in param_grid['factor_type']
        assert 'margin' in param_grid['factor_type']

        # Check ranking_direction includes both options
        assert 'ascending' in param_grid['ranking_direction']
        assert 'descending' in param_grid['ranking_direction']

    def test_expected_performance_ranges(self):
        """Test expected performance targets for factor strategy."""
        template = FactorTemplate()
        expected = template.expected_performance

        # Check ranges are defined
        assert expected['sharpe_range'] == (0.8, 1.3)
        assert expected['return_range'] == (0.10, 0.20)
        assert expected['mdd_range'] == (-0.25, -0.15)

    def test_get_default_params(self):
        """Test default parameter generation."""
        template = FactorTemplate()
        defaults = template.get_default_params()

        # Check all required parameters are present
        assert 'factor_type' in defaults
        assert 'ranking_direction' in defaults
        assert 'n_stocks' in defaults

        # Check defaults are from PARAM_GRID
        param_grid = template.PARAM_GRID
        for param_name, param_value in defaults.items():
            assert param_value in param_grid[param_name]

    def test_validate_params_valid(self):
        """Test parameter validation with valid parameters."""
        template = FactorTemplate()
        params = template.get_default_params()

        is_valid, errors = template.validate_params(params)

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_params_invalid_factor_type(self):
        """Test parameter validation with invalid factor type."""
        template = FactorTemplate()
        params = template.get_default_params()

        # Invalid factor type
        params['factor_type'] = 'invalid_factor'

        is_valid, errors = template.validate_params(params)

        assert is_valid is False
        assert len(errors) > 0

    def test_validate_params_invalid_ranking_direction(self):
        """Test parameter validation with invalid ranking direction."""
        template = FactorTemplate()
        params = template.get_default_params()

        # Invalid ranking direction
        params['ranking_direction'] = 'sideways'

        is_valid, errors = template.validate_params(params)

        assert is_valid is False
        assert len(errors) > 0

    def test_generate_strategy_success(self, mock_data_cache, mock_finlab_sim):
        """Test successful strategy generation."""
        template = FactorTemplate()
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

    def test_generate_strategy_pe_ratio_ascending(self, mock_data_cache, mock_finlab_sim):
        """Test strategy generation with P/E ratio ascending (low P/E = value)."""
        template = FactorTemplate()
        params = {
            'factor_type': 'pe_ratio',
            'ranking_direction': 'ascending',
            'n_stocks': 20,
            'stop_loss': 0.10,
            'take_profit': 0.30,
            'position_limit': 0.10,
            'resample': 'M'
        }

        report, metrics = template.generate_strategy(params)

        assert report is not None
        assert metrics['sharpe_ratio'] > 0

    def test_calculate_factor_score_all_types(self, mock_data_cache):
        """Test _calculate_factor_score for all 6 factor types."""
        template = FactorTemplate()

        factor_types = ['pe_ratio', 'pb_ratio', 'roe', 'roa', 'revenue_growth', 'margin']

        for factor_type in factor_types:
            factor_data = template._calculate_factor_score(factor_type)
            assert factor_data is not None, f"Factor data should not be None for {factor_type}"

    def test_calculate_factor_score_invalid_type(self):
        """Test _calculate_factor_score raises error for invalid factor type."""
        template = FactorTemplate()

        with pytest.raises(ValueError) as exc_info:
            template._calculate_factor_score('invalid_factor')

        assert 'Invalid factor_type' in str(exc_info.value)

    def test_cross_sectional_rank_ascending(self, mock_data_cache):
        """Test _apply_cross_sectional_rank with ascending direction."""
        template = FactorTemplate()

        factor_data = template._calculate_factor_score('pe_ratio')
        ranked_data = template._apply_cross_sectional_rank(factor_data, 'ascending')

        assert ranked_data is not None

    def test_cross_sectional_rank_descending(self, mock_data_cache):
        """Test _apply_cross_sectional_rank with descending direction."""
        template = FactorTemplate()

        factor_data = template._calculate_factor_score('roe')
        ranked_data = template._apply_cross_sectional_rank(factor_data, 'descending')

        assert ranked_data is not None

    def test_cross_sectional_rank_invalid_direction(self, mock_data_cache):
        """Test _apply_cross_sectional_rank raises error for invalid direction."""
        template = FactorTemplate()

        factor_data = template._calculate_factor_score('pe_ratio')

        with pytest.raises(ValueError) as exc_info:
            template._apply_cross_sectional_rank(factor_data, 'invalid_direction')

        assert 'Invalid ranking_direction' in str(exc_info.value)

    def test_quality_filters_application(self, mock_data_cache):
        """Test _apply_quality_filters adds technical and liquidity filters."""
        template = FactorTemplate()
        params = template.get_default_params()

        factor_data = template._calculate_factor_score(params['factor_type'])
        ranked_data = template._apply_cross_sectional_rank(factor_data, params['ranking_direction'])
        filtered_data = template._apply_quality_filters(ranked_data, params)

        assert filtered_data is not None
