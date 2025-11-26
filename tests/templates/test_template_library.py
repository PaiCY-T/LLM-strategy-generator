"""
TDD Tests for Template Library (RED Phase)

Tests verify:
1. Template library initialization and configuration
2. Template retrieval and validation
3. Data caching functionality and performance
4. Strategy generation from templates + parameters
5. Integration with TPE optimizer and UnifiedLoop

CRITICAL PROBLEM: Factor Graph produces IDENTICAL strategies (all Sharpe 0.3012)
ROOT CAUSE: `_create_template_strategy()` uses fixed hardcoded parameters
SOLUTION: Template Library with data caching + TPE optimization

Performance Target: Reduce 5 min/strategy → 1-2 min/strategy (70% speedup)
"""

import pytest
import numpy as np
import pandas as pd
import optuna
from typing import Dict, Any, Callable, Optional
from datetime import datetime

# These imports will FAIL initially (RED phase)
from src.templates.template_library import TemplateLibrary


class TestTemplateLibraryInitialization:
    """Test Template Library initialization and configuration."""

    def test_library_loads_all_templates(self):
        """Verify all 6 templates are registered in library."""
        library = TemplateLibrary()

        expected_templates = {
            'Momentum',
            'MeanReversion',
            'BreakoutTrend',
            'VolatilityAdaptive',
            'DualMomentum',
            'RegimeAdaptive'
        }

        available_templates = set(library.templates.keys())

        assert available_templates == expected_templates, \
            f"Expected {expected_templates}, got {available_templates}"

    def test_template_names_match_registry(self):
        """Verify template names match TEMPLATE_SEARCH_SPACES registry."""
        from src.templates.template_registry import TEMPLATE_SEARCH_SPACES

        library = TemplateLibrary()

        # Should have exact same keys as registry
        assert set(library.templates.keys()) == set(TEMPLATE_SEARCH_SPACES.keys()), \
            "Template library should mirror registry exactly"

    def test_cache_enabled_by_default(self):
        """Verify caching is enabled by default for performance."""
        library = TemplateLibrary()

        # Cache should be enabled by default
        assert hasattr(library, 'cache'), "Library should have cache attribute"
        assert isinstance(library.cache, dict), "Cache should be a dictionary"


class TestTemplateRetrieval:
    """Test template retrieval and validation."""

    def test_get_template_returns_callable(self):
        """Get template should return a callable search space function."""
        library = TemplateLibrary()

        template_fn = library.get_template('Momentum')

        assert callable(template_fn), "Template should be a callable function"

    def test_get_template_invalid_name_raises(self):
        """Getting unknown template should raise KeyError."""
        library = TemplateLibrary()

        with pytest.raises(KeyError) as exc_info:
            library.get_template('NonExistentTemplate')

        # Error message should be helpful
        assert 'NonExistentTemplate' in str(exc_info.value), \
            "Error should mention the invalid template name"

    def test_get_template_momentum(self):
        """Verify Momentum template can be retrieved."""
        library = TemplateLibrary()

        momentum_fn = library.get_template('Momentum')

        # Should be the momentum search space function
        assert callable(momentum_fn), "Momentum template should be callable"

        # Test it works with Optuna trial
        study = optuna.create_study(direction='maximize')
        trial = study.ask()
        params = momentum_fn(trial)

        assert isinstance(params, dict), "Should return parameter dictionary"
        assert len(params) > 0, "Should return non-empty parameters"

    def test_get_template_all_six_templates(self):
        """Verify all 6 templates can be retrieved successfully."""
        library = TemplateLibrary()

        template_names = [
            'Momentum',
            'MeanReversion',
            'BreakoutTrend',
            'VolatilityAdaptive',
            'DualMomentum',
            'RegimeAdaptive'
        ]

        for template_name in template_names:
            template_fn = library.get_template(template_name)
            assert callable(template_fn), \
                f"{template_name} should return callable function"


class TestDataCaching:
    """Test data caching functionality and performance."""

    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data for testing."""
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        stocks = ['2330.TW', '2317.TW', '2454.TW']

        # Realistic price movements
        close_data = pd.DataFrame({
            '2330.TW': 100 + np.cumsum(np.random.randn(252) * 2),
            '2317.TW': 50 + np.cumsum(np.random.randn(252) * 1),
            '2454.TW': 200 + np.cumsum(np.random.randn(252) * 3)
        }, index=dates)

        volume_data = pd.DataFrame({
            '2330.TW': np.random.randint(1000, 10000, 252),
            '2317.TW': np.random.randint(500, 5000, 252),
            '2454.TW': np.random.randint(2000, 20000, 252)
        }, index=dates)

        high_data = close_data * (1 + np.random.rand(252, 3) * 0.02)
        low_data = close_data * (1 - np.random.rand(252, 3) * 0.02)
        open_data = close_data + np.random.randn(252, 3) * 0.5

        return {
            'close': close_data,
            'volume': volume_data,
            'high': high_data,
            'low': low_data,
            'open': open_data
        }

    def test_cache_market_data_structure(self, sample_market_data):
        """Cached data should have OHLCV structure."""
        library = TemplateLibrary(cache_data=True)

        cached_data = library.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW', '2317.TW', '2454.TW'],
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Should return dictionary with OHLCV keys
        assert isinstance(cached_data, dict), "Should return dictionary"

        expected_keys = {'close', 'volume', 'high', 'low', 'open'}
        assert set(cached_data.keys()) == expected_keys, \
            f"Should have OHLCV keys, got {set(cached_data.keys())}"

        # Each value should be a DataFrame
        for key, df in cached_data.items():
            assert isinstance(df, pd.DataFrame), \
                f"{key} should be a DataFrame"

    def test_cache_key_uniqueness(self):
        """Different parameters should create different cache keys."""
        library = TemplateLibrary(cache_data=True)

        # Cache for different templates
        cache_key_1 = library._make_cache_key(
            'Momentum',
            ['2330.TW'],
            '2023-01-01',
            '2023-12-31',
            'D'
        )

        cache_key_2 = library._make_cache_key(
            'MeanReversion',
            ['2330.TW'],
            '2023-01-01',
            '2023-12-31',
            'D'
        )

        assert cache_key_1 != cache_key_2, \
            "Different templates should have different cache keys"

        # Cache for different date ranges
        cache_key_3 = library._make_cache_key(
            'Momentum',
            ['2330.TW'],
            '2023-01-01',
            '2023-06-30',
            'D'
        )

        assert cache_key_1 != cache_key_3, \
            "Different date ranges should have different cache keys"

    def test_cache_hit_reuses_data(self):
        """Second call with same params should return cached data (fast)."""
        library = TemplateLibrary(cache_data=True)

        params = {
            'template_name': 'Momentum',
            'asset_universe': ['2330.TW', '2317.TW'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }

        # First call - cache miss (slow)
        import time
        start_time = time.time()
        data_1 = library.cache_market_data(**params)
        time_1 = time.time() - start_time

        # Second call - cache hit (fast)
        start_time = time.time()
        data_2 = library.cache_market_data(**params)
        time_2 = time.time() - start_time

        # Cache hit should be significantly faster
        assert time_2 < time_1 * 0.1, \
            f"Cache hit ({time_2:.4f}s) should be <10% of miss time ({time_1:.4f}s)"

        # Should return same data
        assert data_1.keys() == data_2.keys(), \
            "Cached data should have same keys"

    def test_cache_miss_loads_fresh(self):
        """New parameters should trigger fresh data load."""
        library = TemplateLibrary(cache_data=True)

        # First load
        data_1 = library.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW'],
            start_date='2023-01-01',
            end_date='2023-06-30'
        )

        # Different parameters - should load fresh
        data_2 = library.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW'],
            start_date='2023-07-01',
            end_date='2023-12-31'
        )

        # Should have different data (different date ranges)
        assert not data_1['close'].index.equals(data_2['close'].index), \
            "Different date ranges should have different data"

    def test_cache_disabled_always_loads(self):
        """When cache=False, should always reload data."""
        library = TemplateLibrary(cache_data=False)

        params = {
            'template_name': 'Momentum',
            'asset_universe': ['2330.TW'],
            'start_date': '2023-01-01',
            'end_date': '2023-12-31'
        }

        # Both calls should load fresh (no caching)
        data_1 = library.cache_market_data(**params)
        data_2 = library.cache_market_data(**params)

        # Cache should remain empty
        assert len(library.cache) == 0, \
            "Cache should be empty when cache_data=False"


class TestStrategyGeneration:
    """Test strategy generation from templates + parameters."""

    @pytest.fixture
    def sample_params(self):
        """Sample optimized parameters for testing."""
        return {
            'Momentum': {
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30,
                'volume_threshold': 1.5,
                'position_size': 0.1
            },
            'MeanReversion': {
                'rsi_period': 10,
                'rsi_overbought': 80,
                'rsi_oversold': 20,
                'position_size': 0.15
            }
        }

    def test_generate_strategy_returns_dict(self, sample_params):
        """Generate strategy should return dict with code and metadata."""
        library = TemplateLibrary()

        strategy = library.generate_strategy(
            template_name='Momentum',
            params=sample_params['Momentum']
        )

        # Should return dictionary
        assert isinstance(strategy, dict), "Should return dictionary"

        # Should have required keys
        assert 'code' in strategy, "Should have 'code' key"
        assert 'metadata' in strategy, "Should have 'metadata' key"

        # Code should be a string
        assert isinstance(strategy['code'], str), "Code should be string"

        # Metadata should be a dictionary
        assert isinstance(strategy['metadata'], dict), "Metadata should be dict"

    def test_generate_strategy_uses_params(self, sample_params):
        """Generated code should include parameter values."""
        library = TemplateLibrary()

        strategy = library.generate_strategy(
            template_name='Momentum',
            params=sample_params['Momentum']
        )

        code = strategy['code']

        # Code should contain parameter values
        assert '14' in code or 'rsi_period=14' in code, \
            "Code should include rsi_period value"
        assert '70' in code or 'rsi_overbought=70' in code, \
            "Code should include rsi_overbought value"

    def test_generate_strategy_template_specific(self, sample_params):
        """Different templates should generate different code."""
        library = TemplateLibrary()

        momentum_strategy = library.generate_strategy(
            template_name='Momentum',
            params=sample_params['Momentum']
        )

        mean_reversion_strategy = library.generate_strategy(
            template_name='MeanReversion',
            params=sample_params['MeanReversion']
        )

        # Generated code should be different
        assert momentum_strategy['code'] != mean_reversion_strategy['code'], \
            "Different templates should generate different code"

        # Metadata should indicate different templates
        assert momentum_strategy['metadata']['template'] == 'Momentum'
        assert mean_reversion_strategy['metadata']['template'] == 'MeanReversion'

    def test_generate_strategy_with_cached_data(self, sample_params):
        """Should use cached data when provided."""
        library = TemplateLibrary(cache_data=True)

        # Pre-cache data
        cached_data = library.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW', '2317.TW'],
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Generate strategy with cached data
        strategy = library.generate_strategy(
            template_name='Momentum',
            params=sample_params['Momentum'],
            cached_data=cached_data
        )

        # Should return valid strategy
        assert 'code' in strategy
        assert 'metadata' in strategy

        # Metadata should indicate cached data was used
        assert strategy['metadata'].get('used_cache', False) == True, \
            "Metadata should indicate cached data was used"

    def test_generate_strategy_without_cache(self, sample_params):
        """Should work without cached data (loads fresh)."""
        library = TemplateLibrary(cache_data=False)

        # Generate strategy without pre-cached data
        strategy = library.generate_strategy(
            template_name='Momentum',
            params=sample_params['Momentum'],
            cached_data=None
        )

        # Should still return valid strategy
        assert 'code' in strategy
        assert 'metadata' in strategy

        # Metadata should indicate no cache was used
        assert strategy['metadata'].get('used_cache', False) == False, \
            "Metadata should indicate no cache was used"


class TestTemplateLibraryIntegration:
    """Test integration with TPE optimizer and UnifiedLoop."""

    def test_six_templates_generate_unique_strategies(self):
        """Each template should produce distinct strategy code."""
        library = TemplateLibrary()

        # Create Optuna study to get trial params
        study = optuna.create_study(direction='maximize')

        generated_strategies = []

        template_names = [
            'Momentum',
            'MeanReversion',
            'BreakoutTrend',
            'VolatilityAdaptive',
            'DualMomentum',
            'RegimeAdaptive'
        ]

        for template_name in template_names:
            # Get template and generate params
            template_fn = library.get_template(template_name)
            trial = study.ask()
            params = template_fn(trial)

            # Generate strategy
            strategy = library.generate_strategy(
                template_name=template_name,
                params=params
            )

            generated_strategies.append(strategy['code'])

        # All strategies should be unique
        unique_strategies = set(generated_strategies)
        assert len(unique_strategies) == 6, \
            f"Expected 6 unique strategies, got {len(unique_strategies)}"

    def test_caching_improves_performance(self):
        """Cached generation should be faster than uncached."""
        # Library WITH caching
        library_cached = TemplateLibrary(cache_data=True)

        # Library WITHOUT caching
        library_uncached = TemplateLibrary(cache_data=False)

        params = {
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'volume_threshold': 1.5,
            'position_size': 0.1
        }

        # Pre-cache data
        cached_data = library_cached.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW'],
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Time cached generation
        import time

        start_time = time.time()
        for _ in range(5):
            library_cached.generate_strategy(
                template_name='Momentum',
                params=params,
                cached_data=cached_data
            )
        cached_time = time.time() - start_time

        # Time uncached generation
        start_time = time.time()
        for _ in range(5):
            library_uncached.generate_strategy(
                template_name='Momentum',
                params=params,
                cached_data=None
            )
        uncached_time = time.time() - start_time

        # Cached should be at least 2x faster
        assert cached_time < uncached_time * 0.5, \
            f"Cached ({cached_time:.2f}s) should be <50% of uncached ({uncached_time:.2f}s)"

    def test_integration_with_tpe_optimizer(self):
        """Verify Template Library works with TPE optimizer workflow."""
        library = TemplateLibrary(cache_data=True)

        # Simulate TPE optimization workflow
        study = optuna.create_study(direction='maximize')

        # Pre-cache data (done once before optimization)
        cached_data = library.cache_market_data(
            template_name='Momentum',
            asset_universe=['2330.TW', '2317.TW'],
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Simulate multiple optimization trials
        for _ in range(3):
            trial = study.ask()

            # Get template
            template_fn = library.get_template('Momentum')

            # Generate parameters from search space
            params = template_fn(trial)

            # Generate strategy with cached data
            strategy = library.generate_strategy(
                template_name='Momentum',
                params=params,
                cached_data=cached_data
            )

            # Verify strategy is valid
            assert 'code' in strategy
            assert 'metadata' in strategy
            assert isinstance(strategy['code'], str)
            assert len(strategy['code']) > 0

            # Simulate objective function returning Sharpe
            simulated_sharpe = np.random.uniform(0.0, 2.0)
            study.tell(trial, simulated_sharpe)

        # Verify study has results
        assert len(study.trials) == 3, "Should have 3 completed trials"
        assert study.best_value is not None, "Should have best value"
