"""Infrastructure validation tests for E2E test framework.

P2.2.1: Verify E2E test infrastructure is properly configured
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from tests.e2e.conftest import N_DAYS, N_STOCKS


@pytest.mark.e2e
class TestE2EInfrastructure:
    """Validate E2E test infrastructure setup."""

    def test_market_data_fixture_structure(self, market_data):
        """
        GIVEN market_data fixture
        WHEN accessing the data
        THEN it should have the expected structure and properties
        """
        # Verify it's a DataFrame
        assert isinstance(market_data, pd.DataFrame), "market_data should be a DataFrame"

        # Verify index is DatetimeIndex
        assert isinstance(market_data.index, pd.DatetimeIndex), \
            "Index should be DatetimeIndex"

        # Verify we have ~3 years of data (N_DAYS trading days)
        assert len(market_data) == N_DAYS, f"Expected {N_DAYS} rows, got {len(market_data)}"

        # Verify we have multiple stocks (N_STOCKS × 3 columns each)
        # (price, volume, returns for each stock)
        expected_cols = N_STOCKS * 3
        assert len(market_data.columns) == expected_cols, \
            f"Expected {expected_cols} columns, got {len(market_data.columns)}"

        # Verify column naming pattern
        sample_stock = "stock_000"
        assert f"{sample_stock}_price" in market_data.columns
        assert f"{sample_stock}_volume" in market_data.columns
        assert f"{sample_stock}_returns" in market_data.columns

    def test_market_data_statistical_properties(self, market_data):
        """
        GIVEN market_data fixture
        WHEN analyzing statistical properties
        THEN data should have realistic market characteristics
        """
        # Extract returns for first stock
        returns = market_data['stock_000_returns']

        # Verify no NaN values
        assert not returns.isna().any(), "Returns should not contain NaN"

        # Verify realistic return distribution
        mean_daily_return = returns.mean()
        std_daily_return = returns.std()

        # Annualized metrics
        annual_return = mean_daily_return * 252
        annual_vol = std_daily_return * np.sqrt(252)

        # Check realistic ranges
        assert -0.2 < annual_return < 0.5, \
            f"Annual return {annual_return:.2%} seems unrealistic"
        assert 0.05 < annual_vol < 0.50, \
            f"Annual volatility {annual_vol:.2%} seems unrealistic"

        # Verify prices are positive
        prices = market_data['stock_000_price']
        assert (prices > 0).all(), "All prices should be positive"

        # Verify volumes are positive integers
        volumes = market_data['stock_000_volume']
        assert (volumes > 0).all(), "All volumes should be positive"

    def test_test_environment_fixture(self, test_environment):
        """
        GIVEN test_environment fixture
        WHEN accessing configuration
        THEN it should contain all required settings
        """
        # Verify it's a dictionary
        assert isinstance(test_environment, dict)

        # Verify required keys exist
        required_keys = [
            'mock_llm',
            'mock_backtest',
            'timeout_seconds',
            'memory_limit_mb',
            'parallel_jobs',
            'temp_strategy_dir',
            'temp_results_dir'
        ]

        for key in required_keys:
            assert key in test_environment, f"Missing required key: {key}"

        # Verify types and reasonable values
        assert isinstance(test_environment['mock_llm'], bool)
        assert isinstance(test_environment['timeout_seconds'], (int, float))
        assert test_environment['timeout_seconds'] > 0
        assert test_environment['memory_limit_mb'] > 0

        # Verify paths
        assert isinstance(test_environment['temp_strategy_dir'], Path)
        assert isinstance(test_environment['temp_results_dir'], Path)

    def test_validation_thresholds_fixture(self, validation_thresholds):
        """
        GIVEN validation_thresholds fixture
        WHEN accessing thresholds
        THEN it should contain all required metrics
        """
        # Verify it's a dictionary
        assert isinstance(validation_thresholds, dict)

        # Verify required thresholds
        required_thresholds = [
            'min_sharpe_ratio',
            'min_total_return',
            'max_drawdown',
            'min_win_rate',
            'max_execution_time',
            'max_error_rate',
            'oos_tolerance'
        ]

        for threshold in required_thresholds:
            assert threshold in validation_thresholds, \
                f"Missing required threshold: {threshold}"

        # Verify threshold values are reasonable
        assert 0 < validation_thresholds['min_sharpe_ratio'] < 5, \
            "Sharpe ratio threshold should be reasonable"
        assert -1 < validation_thresholds['max_drawdown'] < 0, \
            "Max drawdown should be negative"
        assert 0 < validation_thresholds['min_win_rate'] < 1, \
            "Win rate should be between 0 and 1"
        assert validation_thresholds['max_execution_time'] > 0
        assert 0 < validation_thresholds['oos_tolerance'] < 1, \
            "OOS tolerance should be a percentage"

    def test_sample_strategy_code_fixture(self, sample_strategy_code):
        """
        GIVEN sample_strategy_code fixture
        WHEN accessing the code
        THEN it should be valid Python code
        """
        # Verify it's a string
        assert isinstance(sample_strategy_code, str)

        # Verify it's not empty
        assert len(sample_strategy_code) > 0

        # Verify it contains expected patterns
        assert "def strategy" in sample_strategy_code, \
            "Should contain strategy function definition"
        assert "import" in sample_strategy_code, \
            "Should contain import statements"
        assert "return" in sample_strategy_code, \
            "Should contain return statement"

        # Verify it compiles
        try:
            compile(sample_strategy_code, '<string>', 'exec')
        except SyntaxError as e:
            pytest.fail(f"Sample strategy code has syntax error: {e}")

    def test_fixtures_directory_exists(self, test_fixtures_dir):
        """
        GIVEN test_fixtures_dir fixture
        WHEN checking the directory
        THEN it should exist and contain test data
        """
        # Verify directory exists
        assert test_fixtures_dir.exists(), \
            f"Fixtures directory should exist: {test_fixtures_dir}"

        assert test_fixtures_dir.is_dir(), \
            f"Fixtures path should be a directory: {test_fixtures_dir}"

        # Verify it contains some test data files
        files = list(test_fixtures_dir.glob("*.parquet"))
        assert len(files) > 0, \
            "Fixtures directory should contain .parquet test data files"

    def test_e2e_marker_is_registered(self):
        """
        GIVEN pytest configuration
        WHEN checking registered markers
        THEN 'e2e' marker should be available
        """
        # This test itself is marked with @pytest.mark.e2e
        # If the marker weren't registered, pytest would warn/error
        # with --strict-markers flag (which is in pytest.ini)

        # If we get here, the marker is properly registered
        assert True, "E2E marker is registered in pytest.ini"

    def test_temporary_directories_created(self, test_environment):
        """
        GIVEN E2E test setup
        WHEN test begins execution
        THEN temporary directories should be created
        """
        # autouse fixture e2e_test_setup_teardown should create these
        temp_strategy_dir = test_environment['temp_strategy_dir']
        temp_results_dir = test_environment['temp_results_dir']

        assert temp_strategy_dir.exists(), \
            f"Temp strategy dir should be created: {temp_strategy_dir}"
        assert temp_results_dir.exists(), \
            f"Temp results dir should be created: {temp_results_dir}"

    @pytest.mark.slow
    def test_market_data_performance(self, market_data):
        """
        GIVEN market_data fixture
        WHEN measuring generation time
        THEN fixture should be fast enough for testing

        Note: This is marked as @pytest.mark.slow since it measures performance
        """
        import time

        # Measure fixture access time
        start = time.time()
        data = market_data  # Already generated, just access it
        elapsed = time.time() - start

        # Should be very fast (< 100ms) since fixture is already generated
        assert elapsed < 0.1, \
            f"Market data access too slow: {elapsed:.3f}s"

        # Measure basic operations
        start = time.time()
        _ = data['stock_000_price'].mean()
        _ = data['stock_000_returns'].std()
        elapsed = time.time() - start

        # Basic operations should be fast
        assert elapsed < 0.01, \
            f"Basic operations too slow: {elapsed:.3f}s"
