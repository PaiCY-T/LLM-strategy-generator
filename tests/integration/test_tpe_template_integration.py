"""
Integration Tests for TPE Optimizer + Template Library Integration

Tests Task 3.1 integration:
- optimize_with_template() method
- optimize_with_validation() method (IS/OOS)
- Template diversity (6 templates with different Sharpe ratios)
- Data caching functionality

Success Criteria:
- All 6 templates optimize successfully
- Sharpe ratios DIVERGE from 0.3012 (diversity achieved)
- Data caching reduces execution time by 70%
- IS/OOS validation detects degradation
"""

import pytest
import warnings
from typing import Dict
import pandas as pd
import numpy as np
import optuna

# Suppress Optuna experimental warnings for cleaner test output
warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)

from src.learning.optimizer import TPEOptimizer
from src.templates.template_library import TemplateLibrary
from src.templates.template_registry import get_template_names


class TestTPETemplateIntegration:
    """Test TPE Optimizer integration with Template Library."""

    @pytest.fixture
    def asset_universe(self):
        """Test asset universe."""
        return ['2330.TW', '2317.TW', '2303.TW']

    @pytest.fixture
    def date_range(self):
        """Test date range."""
        return {
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }

    @pytest.fixture
    def backtest_objective(self):
        """Mock backtest objective function."""
        def objective(strategy_code: str, cached_data: Dict) -> float:
            """
            Simulate backtest returning Sharpe ratio.

            For testing diversity, we return different Sharpe ratios
            based on strategy code hash to simulate template differences.
            """
            # Extract template name from strategy code
            template_name = None
            if 'Momentum' in strategy_code:
                template_name = 'Momentum'
            elif 'Mean Reversion' in strategy_code:
                template_name = 'MeanReversion'
            elif 'Breakout' in strategy_code:
                template_name = 'BreakoutTrend'
            elif 'Volatility' in strategy_code:
                template_name = 'VolatilityAdaptive'
            elif 'Dual' in strategy_code:
                template_name = 'DualMomentum'
            elif 'Regime' in strategy_code:
                template_name = 'RegimeAdaptive'

            # Base Sharpe ratio with template-specific variation
            # This simulates different templates achieving different performance
            template_sharpes = {
                'Momentum': 0.65,
                'MeanReversion': 0.52,
                'BreakoutTrend': 0.71,
                'VolatilityAdaptive': 0.48,
                'DualMomentum': 0.63,
                'RegimeAdaptive': 0.57
            }

            base_sharpe = template_sharpes.get(template_name, 0.50)

            # Add parameter-based variation (-0.1 to +0.1)
            # This simulates TPE optimization finding better parameters
            code_hash = hash(strategy_code)
            np.random.seed(abs(code_hash) % 10000)
            param_variation = np.random.uniform(-0.1, 0.1)

            final_sharpe = base_sharpe + param_variation

            return final_sharpe

        return objective

    def test_optimize_with_template_single(self, asset_universe, date_range, backtest_objective):
        """Test optimize_with_template() with single template."""
        optimizer = TPEOptimizer()

        result = optimizer.optimize_with_template(
            template_name='Momentum',
            objective_fn=backtest_objective,
            n_trials=10,
            asset_universe=asset_universe,
            start_date=date_range['start_date'],
            end_date=date_range['end_date']
        )

        # Verify result structure
        assert 'best_params' in result
        assert 'best_value' in result
        assert 'template' in result
        assert 'n_trials' in result
        assert 'best_strategy_code' in result

        # Verify optimization worked
        assert result['template'] == 'Momentum'
        assert result['n_trials'] == 10
        assert isinstance(result['best_params'], dict)
        assert len(result['best_params']) > 0

        # Verify Sharpe ratio is reasonable (diversity check)
        assert 0.4 < result['best_value'] < 1.0
        assert result['best_value'] != 0.3012  # NOT the hardcoded value

        # Verify strategy code was generated
        assert 'Momentum Strategy' in result['best_strategy_code']
        assert 'def momentum_strategy' in result['best_strategy_code']

        print(f"✓ Single template optimization: {result['template']} | Sharpe: {result['best_value']:.3f}")

    def test_optimize_all_6_templates(self, asset_universe, date_range, backtest_objective):
        """Test optimization for all 6 templates to verify diversity."""
        templates = get_template_names()
        assert len(templates) == 6, f"Expected 6 templates, got {len(templates)}"

        results = {}
        sharpe_ratios = []

        for template_name in templates:
            optimizer = TPEOptimizer()  # Fresh optimizer per template

            result = optimizer.optimize_with_template(
                template_name=template_name,
                objective_fn=backtest_objective,
                n_trials=10,
                asset_universe=asset_universe,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )

            results[template_name] = result
            sharpe_ratios.append(result['best_value'])

            print(f"  {template_name:20s} | Sharpe: {result['best_value']:.3f}")

        # DIVERSITY CHECK: Sharpe ratios should DIVERGE
        unique_sharpes = set([round(s, 2) for s in sharpe_ratios])
        assert len(unique_sharpes) >= 4, \
            f"Expected at least 4 distinct Sharpe ratios, got {len(unique_sharpes)}"

        # Verify no strategies have hardcoded Sharpe of 0.3012
        for sharpe in sharpe_ratios:
            assert abs(sharpe - 0.3012) > 0.05, \
                f"Found hardcoded Sharpe {sharpe:.3f}, expected diversity"

        # Verify reasonable Sharpe range (0.4 - 0.8)
        assert 0.3 < min(sharpe_ratios) < 0.9
        assert 0.4 < max(sharpe_ratios) < 1.0

        print(f"\n✓ All 6 templates optimized successfully")
        print(f"✓ Diversity achieved: {len(unique_sharpes)} distinct Sharpe values")
        print(f"✓ Sharpe range: {min(sharpe_ratios):.3f} - {max(sharpe_ratios):.3f}")

    def test_data_caching_performance(self, asset_universe, date_range, backtest_objective):
        """Test that data caching improves performance."""
        import time

        # Test WITHOUT caching (disabled)
        library_no_cache = TemplateLibrary(cache_data=False)
        start_no_cache = time.time()

        # Simulate 5 trials (load data each time)
        for _ in range(5):
            data = library_no_cache.cache_market_data(
                template_name='Momentum',
                asset_universe=asset_universe,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )

        time_no_cache = time.time() - start_no_cache

        # Test WITH caching (enabled)
        library_with_cache = TemplateLibrary(cache_data=True)
        start_with_cache = time.time()

        # Simulate 5 trials (load data once, cache hits for remaining)
        for _ in range(5):
            data = library_with_cache.cache_market_data(
                template_name='Momentum',
                asset_universe=asset_universe,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )

        time_with_cache = time.time() - start_with_cache

        # Caching should be AT LEAST 2x faster (target: 70% speedup = 3.3x)
        speedup = time_no_cache / time_with_cache if time_with_cache > 0 else 1.0

        print(f"\n✓ Performance comparison:")
        print(f"  Without caching: {time_no_cache*1000:.1f}ms")
        print(f"  With caching: {time_with_cache*1000:.1f}ms")
        print(f"  Speedup: {speedup:.1f}x")

        assert speedup >= 2.0, \
            f"Expected at least 2x speedup with caching, got {speedup:.1f}x"

    def test_optimize_with_validation(self, asset_universe, backtest_objective):
        """Test IS/OOS validation with degradation detection."""
        optimizer = TPEOptimizer()

        result = optimizer.optimize_with_validation(
            template_name='Momentum',
            objective_fn=backtest_objective,
            n_trials=10,
            is_asset_universe=asset_universe,
            is_start_date='2023-01-01',
            is_end_date='2023-06-30',
            oos_start_date='2023-07-01',
            oos_end_date='2023-12-31',
            degradation_threshold=0.30
        )

        # Verify result structure
        assert 'best_params' in result
        assert 'is_value' in result
        assert 'oos_value' in result
        assert 'degradation' in result
        assert 'overfitting_detected' in result
        assert 'template' in result

        # Verify IS/OOS values are reasonable
        assert 0.3 < result['is_value'] < 1.0
        assert 0.2 < result['oos_value'] < 1.0

        # Verify degradation calculation
        expected_degradation = (result['is_value'] - result['oos_value']) / result['is_value']
        assert abs(result['degradation'] - expected_degradation) < 0.01

        # Verify overfitting flag
        assert isinstance(result['overfitting_detected'], bool)

        print(f"\n✓ IS/OOS validation:")
        print(f"  IS Sharpe: {result['is_value']:.3f}")
        print(f"  OOS Sharpe: {result['oos_value']:.3f}")
        print(f"  Degradation: {result['degradation']:.1%}")
        print(f"  Overfitting: {result['overfitting_detected']}")

    def test_parameter_diversity(self, asset_universe, date_range, backtest_objective):
        """Test that TPE finds different optimal parameters for different templates."""
        templates = ['Momentum', 'MeanReversion', 'BreakoutTrend']
        param_sets = []

        for template_name in templates:
            optimizer = TPEOptimizer()

            result = optimizer.optimize_with_template(
                template_name=template_name,
                objective_fn=backtest_objective,
                n_trials=10,
                asset_universe=asset_universe,
                start_date=date_range['start_date'],
                end_date=date_range['end_date']
            )

            param_sets.append(result['best_params'])

            print(f"  {template_name}: {list(result['best_params'].keys())[:3]}")

        # Verify parameter sets are different (templates have different param spaces)
        # At least one parameter should differ between templates
        all_keys = [set(params.keys()) for params in param_sets]
        assert len(set(frozenset(keys) for keys in all_keys)) >= 2, \
            "Expected different parameter spaces for different templates"

        print(f"\n✓ Parameter diversity verified")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
