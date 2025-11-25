"""Pytest configuration and shared fixtures for E2E tests.

This module provides shared fixtures for end-to-end testing including
market data, test environments, and validation thresholds.
"""

import os
from pathlib import Path
from typing import Dict, Any

import pytest
import pandas as pd
import numpy as np


# Test data constants
N_DAYS = 756  # 3 years of trading days (252 trading days/year)
N_STOCKS = 100  # Number of stocks in test market data


def get_test_api_key() -> str:
    """Get API key from environment variable or use mock key for CI.

    Returns:
        API key string - either from TEST_API_KEY env var or mock key

    Note:
        In production tests, set TEST_API_KEY environment variable.
        In CI/CD, the mock key is used for fast, isolated testing.
    """
    return os.environ.get("TEST_API_KEY", "mock-key-for-ci")


def create_test_learning_config(
    tmpdir: str,
    max_iterations: int,
    innovation_rate: int,
) -> Any:
    """Create LearningConfig for E2E tests.

    Centralized config factory to reduce code duplication across test files.

    Args:
        tmpdir: Temporary directory for test artifacts
        max_iterations: Number of iterations to run
        innovation_rate: 0-100, LLM vs Factor Graph ratio

    Returns:
        LearningConfig instance configured for testing

    Note:
        Imports LearningConfig inside function to avoid circular imports
        during pytest collection phase.
    """
    from src.learning.learning_config import LearningConfig
    import yaml

    tmpdir_path = Path(tmpdir)

    # Create required directories
    (tmpdir_path / "artifacts" / "data").mkdir(parents=True, exist_ok=True)
    (tmpdir_path / "logs").mkdir(parents=True, exist_ok=True)

    # Create minimal config file for AntiChurnManager and LLMClient
    config_file = tmpdir_path / "test_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump({
            'anti_churn': {
                'min_improvement_pct': 2.0,
                'probation_iterations': 3,
                'probation_multiplier': 1.5
            },
            'llm': {
                'enabled': True,
                'provider': 'openrouter',
                'model': 'gemini-2.5-flash',
                'api_key': get_test_api_key(),  # Load from environment variable
                'timeout': 30,
                'max_tokens': 2000,
                'temperature': 0.7,
                'innovation_rate': innovation_rate / 100.0  # Convert 0-100 to 0.0-1.0
            }
        }, f)

    return LearningConfig(
        # Loop control
        max_iterations=max_iterations,
        continue_on_error=False,

        # LLM config
        llm_model="gemini-2.5-flash",
        api_key=get_test_api_key(),
        llm_timeout=30,
        llm_temperature=0.7,
        llm_max_tokens=2000,

        # Innovation
        innovation_mode=True,
        innovation_rate=innovation_rate,
        llm_retry_count=1,  # Minimal retries for speed

        # Backtest
        timeout_seconds=60,  # Short timeout for tests
        start_date="2020-01-01",
        end_date="2022-12-31",
        fee_ratio=0.001425,
        tax_ratio=0.003,
        resample="M",

        # Files
        history_file=str(tmpdir_path / "artifacts" / "data" / "innovations.jsonl"),
        history_window=3,
        champion_file=str(tmpdir_path / "artifacts" / "data" / "champion.json"),
        log_dir=str(tmpdir_path / "logs"),
        config_file=str(config_file),

        # Logging
        log_level="ERROR",  # Reduce noise in tests
        log_to_file=False,
        log_to_console=False,
    )


@pytest.fixture
def market_data() -> pd.DataFrame:
    """Provide realistic market data for E2E testing.

    Returns synthetic market data with realistic statistical properties
    suitable for backtesting and strategy evaluation.

    Returns:
        DataFrame with columns:
            - price: Close prices (100 stocks)
            - volume: Trading volume
            - returns: Daily returns
        Index: DatetimeIndex with 756 trading days (~3 years)

    Statistical Properties:
        - Mean daily return: ~0.04% (10% annualized)
        - Daily volatility: ~1.2% (19% annualized)
        - Realistic Sharpe ratio: ~0.5
        - Cross-sectional correlation: ~0.3
    """
    np.random.seed(42)  # Reproducible test data

    # Use module constants for test data dimensions
    n_days = N_DAYS
    n_stocks = N_STOCKS

    # Generate correlated returns using factor model
    # Common market factor (strength: 0.5)
    market_factor = np.random.randn(n_days) * 0.012

    # Generate individual stock returns
    returns_data = {}
    prices_data = {}
    volumes_data = {}

    for i in range(n_stocks):
        stock_id = f"stock_{i:03d}"

        # Stock-specific parameters
        beta = 0.5 + np.random.rand() * 1.5  # Beta: 0.5 - 2.0
        idio_vol = 0.008 + np.random.rand() * 0.015  # Idiosyncratic vol: 0.8% - 2.3%
        drift = 0.0002 + np.random.rand() * 0.0006  # Drift: 0.02% - 0.08%

        # Generate returns: market + idiosyncratic + drift
        idiosyncratic = np.random.randn(n_days) * idio_vol
        returns = beta * market_factor + idiosyncratic + drift

        # Convert to prices (starting at 100)
        prices = 100 * np.exp(np.cumsum(returns))

        # Generate volume (correlated with volatility)
        base_volume = 1_000_000
        volume_noise = np.random.rand(n_days) * 0.5 + 0.75  # 0.75 - 1.25
        volumes = (base_volume * volume_noise).astype(int)

        returns_data[stock_id] = returns
        prices_data[stock_id] = prices
        volumes_data[stock_id] = volumes

    # Create DataFrame with datetime index
    dates = pd.date_range('2020-01-01', periods=n_days, freq='B')

    # Create multi-column DataFrame using pd.concat for performance
    # Build all columns at once to avoid fragmentation
    all_columns = {}
    for stock_id in prices_data:
        all_columns[f"{stock_id}_price"] = prices_data[stock_id]
        all_columns[f"{stock_id}_volume"] = volumes_data[stock_id]
        all_columns[f"{stock_id}_returns"] = returns_data[stock_id]

    data = pd.DataFrame(all_columns, index=dates)

    return data


@pytest.fixture
def test_environment() -> Dict[str, Any]:
    """Provide test environment configuration.

    Returns environment settings for E2E tests including
    API mocking, timeouts, and resource limits.

    Returns:
        Dictionary with test environment configuration:
            - mock_llm: Whether to mock LLM API calls
            - mock_backtest: Whether to mock backtest execution
            - timeout_seconds: Maximum test execution time
            - memory_limit_mb: Memory limit for tests
            - parallel_jobs: Number of parallel test jobs
    """
    return {
        # API mocking
        'mock_llm': True,  # Mock LLM calls for fast, deterministic tests
        'mock_backtest': False,  # Use real backtest engine for accuracy

        # Resource limits
        'timeout_seconds': 60,  # Max execution time per test
        'memory_limit_mb': 1024,  # Max memory per test

        # Execution settings
        'parallel_jobs': 1,  # Sequential execution for E2E tests
        'retry_attempts': 0,  # No retries for E2E tests

        # Temporary paths
        'temp_strategy_dir': Path('./test_data/e2e_strategies'),
        'temp_results_dir': Path('./test_data/e2e_results'),

        # Cleanup
        'cleanup_on_success': True,
        'cleanup_on_failure': False,  # Keep artifacts for debugging
    }


@pytest.fixture
def validation_thresholds() -> Dict[str, Any]:
    """Provide validation thresholds for E2E test assertions.

    Returns performance and quality thresholds that strategies
    must meet to pass E2E validation.

    Returns:
        Dictionary with validation thresholds:
            - min_sharpe_ratio: Minimum acceptable Sharpe ratio
            - min_total_return: Minimum total return percentage
            - max_drawdown: Maximum acceptable drawdown (negative)
            - min_win_rate: Minimum win rate percentage
            - max_execution_time: Maximum execution time in seconds
            - max_error_rate: Maximum error rate percentage
            - oos_tolerance: Out-of-sample tolerance (±%)
    """
    return {
        # Performance thresholds
        'min_sharpe_ratio': 0.5,  # Minimum Sharpe for passing strategy
        'min_total_return': 0.10,  # 10% minimum return
        'max_drawdown': -0.30,  # -30% maximum drawdown
        'min_win_rate': 0.45,  # 45% minimum win rate

        # Execution thresholds
        'max_execution_time': 5.0,  # 5 seconds max for strategy evolution
        'max_error_rate': 0.001,  # 0.1% maximum error rate
        'max_latency_ms': 100,  # 100ms max latency for operations

        # Validation thresholds
        'oos_tolerance': 0.20,  # ±20% OOS tolerance (Gate 5)
        'improvement_threshold': 0.05,  # 5% minimum improvement vs baseline

        # Quality gates
        'min_code_quality_score': 0.7,  # Minimum code quality (0-1)
        'max_complexity': 15,  # Maximum cyclomatic complexity
        'min_test_coverage': 0.80,  # 80% minimum test coverage
    }


@pytest.fixture
def sample_strategy_code() -> str:
    """Provide sample strategy code for E2E testing.

    Returns a simple but realistic strategy template that can be
    used as a starting point for evolution tests.

    Returns:
        String containing valid Python strategy code
    """
    return """
import pandas as pd

def strategy(data):
    \"\"\"Simple momentum strategy for E2E testing.

    Args:
        data: DataFrame with price and volume data

    Returns:
        DataFrame with position signals
    \"\"\"
    # Calculate 20-day momentum
    close = data['price_收盤價']
    momentum = close.pct_change(20)

    # Generate signals
    positions = pd.DataFrame(index=data.index)

    # Buy when momentum > 5%, sell when < -5%
    positions['signal'] = 0
    positions.loc[momentum > 0.05, 'signal'] = 1
    positions.loc[momentum < -0.05, 'signal'] = -1

    return positions
"""


@pytest.fixture
def test_fixtures_dir() -> Path:
    """Provide path to test fixtures directory.

    Returns:
        Path to tests/fixtures/ containing test data files
    """
    fixtures_dir = Path(__file__).parent.parent / "fixtures"
    assert fixtures_dir.exists(), f"Fixtures directory not found: {fixtures_dir}"
    return fixtures_dir


@pytest.fixture(autouse=True)
def e2e_test_setup_teardown(test_environment: Dict[str, Any]) -> None:
    """Setup and teardown for each E2E test.

    Creates temporary directories before test execution and
    optionally cleans up after completion.

    Args:
        test_environment: Test environment configuration
    """
    # Setup: Create temporary directories
    temp_strategy_dir = test_environment['temp_strategy_dir']
    temp_results_dir = test_environment['temp_results_dir']

    temp_strategy_dir.mkdir(parents=True, exist_ok=True)
    temp_results_dir.mkdir(parents=True, exist_ok=True)

    yield  # Run the test

    # Teardown: Optional cleanup
    # (Cleanup logic can be added here if needed)
