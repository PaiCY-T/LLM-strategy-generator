"""
Pytest configuration and fixtures for Finlab Backtesting Optimization System.

This module provides shared fixtures for all tests, including temporary paths,
mock settings, and logger instances.

Fixtures:
    tmp_path: pytest built-in temporary directory
    mock_settings: Mock Settings instance for testing
    test_logger: Test logger instance
"""

import logging
import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_settings() -> Generator[MagicMock, None, None]:
    """
    Provide a mock Settings instance for testing.

    Creates a MagicMock with all required settings attributes pre-configured
    with sensible test defaults. Cleans up environment variables after test.

    Yields:
        MagicMock: Mock Settings instance with test configuration

    Example:
        >>> def test_something(mock_settings):
        >>>     assert mock_settings.log_level == "DEBUG"
        >>>     assert mock_settings.finlab.api_token == "test-token"
    """
    # Save original environment
    original_env = {
        "FINLAB_API_TOKEN": os.getenv("FINLAB_API_TOKEN"),
        "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
        "LOG_LEVEL": os.getenv("LOG_LEVEL"),
    }

    # Set test environment variables
    os.environ["FINLAB_API_TOKEN"] = "test-finlab-token"
    os.environ["CLAUDE_API_KEY"] = "test-claude-key"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Create mock settings
    mock = MagicMock()

    # Finlab config
    mock.finlab.api_token = "test-finlab-token"
    mock.finlab.storage_path = Path("./test_data/finlab_cache")
    mock.finlab.cache_retention_days = 7
    mock.finlab.default_datasets = ["price:收盤價"]

    # Backtest config
    mock.backtest.default_fee_ratio = 0.001425
    mock.backtest.default_tax_ratio = 0.003
    mock.backtest.default_resample = "D"
    mock.backtest.timeout_seconds = 60

    # Analysis config
    mock.analysis.claude_api_key = "test-claude-key"
    mock.analysis.claude_model = "claude-sonnet-4.5"
    mock.analysis.max_suggestions = 5
    mock.analysis.min_suggestions = 3

    # Storage config
    mock.storage.database_path = Path("./test_data/test.db")
    mock.storage.backup_path = Path("./test_data/backups")
    mock.storage.backup_retention_days = 7

    # UI config
    mock.ui.default_language = "zh-TW"
    mock.ui.theme = "light"

    # Logging config
    mock.logging.level = "DEBUG"
    mock.logging.log_dir = Path("./test_logs")
    mock.logging.max_file_size_mb = 5
    mock.logging.backup_count = 3
    mock.logging.format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convenience properties
    mock.finlab_api_token = "test-finlab-token"
    mock.claude_api_key = "test-claude-key"
    mock.data_cache_path = Path("./test_data/finlab_cache")
    mock.database_path = Path("./test_data/test.db")
    mock.log_level = "DEBUG"
    mock.ui_language = "zh-TW"

    yield mock

    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture
def test_logger() -> logging.Logger:
    """
    Provide a test logger instance.

    Creates a logger configured for testing with DEBUG level and
    no file handlers (console only).

    Returns:
        logging.Logger: Configured test logger

    Example:
        >>> def test_logging(test_logger):
        >>>     test_logger.info("Test message")
        >>>     assert True  # Logger works without errors
    """
    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    # Remove any existing handlers
    logger.handlers.clear()

    # Add console handler only (no file I/O in tests)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


@pytest.fixture(autouse=True)
def reset_logging_cache() -> Generator[None, None, None]:
    """
    Reset logger cache and settings singleton before and after each test.

    This ensures tests don't interfere with each other's logger state
    or settings configuration. Automatically applied to all tests.

    Yields:
        None

    Example:
        # Automatically applied, no need to use explicitly
        >>> def test_something():
        >>>     # Logger cache and settings are clean
        >>>     pass
    """
    # Import here to avoid circular imports
    from src.utils import logger

    # Clear logger cache before test
    if hasattr(logger, "clear_logger_cache"):
        logger.clear_logger_cache()

    # Reset settings singleton before test
    if hasattr(logger, "_reset_settings_for_testing"):
        logger._reset_settings_for_testing()

    yield

    # Clear logger cache after test
    if hasattr(logger, "clear_logger_cache"):
        logger.clear_logger_cache()

    # Reset settings singleton after test
    if hasattr(logger, "_reset_settings_for_testing"):
        logger._reset_settings_for_testing()


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """
    Provide a temporary log file path.

    Creates a temporary log file that's automatically cleaned up after the test.

    Args:
        tmp_path: pytest built-in temporary directory fixture

    Returns:
        Path: Path to temporary log file

    Example:
        >>> def test_logging_to_file(temp_log_file):
        >>>     logger = get_logger(__name__, log_file=str(temp_log_file.name))
        >>>     logger.info("Test")
        >>>     assert temp_log_file.exists()
    """
    log_file = tmp_path / "test.log"
    return log_file


@pytest.fixture
def temp_database(tmp_path: Path) -> Path:
    """
    Provide a temporary database path.

    Creates a temporary database file path that's automatically cleaned up
    after the test.

    Args:
        tmp_path: pytest built-in temporary directory fixture

    Returns:
        Path: Path to temporary database file

    Example:
        >>> def test_database(temp_database):
        >>>     # Use temp_database path for SQLite connection
        >>>     conn = sqlite3.connect(temp_database)
        >>>     # Database is automatically cleaned up
    """
    db_file = tmp_path / "test.db"
    return db_file


# ==============================================================================
# Template System Test Fixtures
# ==============================================================================

# Import required for template fixtures
import pandas as pd
from unittest.mock import Mock
from typing import Dict, Any

# Path to fixture files
FIXTURE_DIR = Path(__file__).parent / 'fixtures'


@pytest.fixture
def mock_data_cache(monkeypatch):
    """
    Mock DataCache to return fixture parquet files for template tests.

    This fixture replaces DataCache.get_instance().get() with a mock that
    returns pre-generated synthetic data from tests/fixtures/ directory.

    Mocking Strategy:
        - MOCK: DataCache.get_instance().get() → Returns FinlabDataFrame with custom methods
        - REAL: All template logic (filtering, ranking, weighting, code generation)

    Usage:
        def test_template_with_mock_data(mock_data_cache):
            template = TurtleTemplate()
            # template._get_cached_data() will return mock data
            result = template.generate_strategy(params)

    Returns:
        MagicMock: Mocked DataCache instance with .get() method
    """
    # Mapping from dataset keys to fixture filenames
    fixture_map = {
        'price:收盤價': 'price_收盤價.parquet',
        'price:成交股數': 'price_成交股數.parquet',
        'monthly_revenue:當月營收': 'monthly_revenue_當月營收.parquet',
        'monthly_revenue:去年同月增減(%)': 'monthly_revenue_去年同月增減(pct).parquet',
        'monthly_revenue:上月比較增減(%)': 'monthly_revenue_上月比較增減(pct).parquet',
        'fundamental_features:營業利益率': 'fundamental_features_營業利益率.parquet',
        'fundamental_features:ROE綜合損益': 'fundamental_features_ROE綜合損益.parquet',
        'fundamental_features:資產報酬率': 'fundamental_features_資產報酬率.parquet',
        'price_earning_ratio:殖利率(%)': 'price_earning_ratio_殖利率(pct).parquet',
        'price_earning_ratio:本益比': 'price_earning_ratio_本益比.parquet',
        'price_earning_ratio:股價淨值比': 'price_earning_ratio_股價淨值比.parquet',
        'internal_equity_changes:董監持有股數占比': 'internal_equity_changes_董監持有股數占比.parquet',
    }

    class MockRolling:
        """Mock class that mimics pandas Rolling behavior but returns MockFinlabDataFrame."""

        def __init__(self, df, period):
            self._df = df
            self._period = period
            self._rolling = df.rolling(period)

        def mean(self):
            """Return rolling mean as MockFinlabDataFrame."""
            return MockFinlabDataFrame(self._rolling.mean())

        def min(self):
            """Return rolling min as MockFinlabDataFrame."""
            return MockFinlabDataFrame(self._rolling.min())

        def max(self):
            """Return rolling max as MockFinlabDataFrame."""
            return MockFinlabDataFrame(self._rolling.max())

        def sum(self):
            """Return rolling sum as MockFinlabDataFrame."""
            return MockFinlabDataFrame(self._rolling.sum())

        def std(self):
            """Return rolling std as MockFinlabDataFrame."""
            return MockFinlabDataFrame(self._rolling.std())

    class MockFinlabDataFrame:
        """Mock class that mimics finlab DataFrame behavior."""

        def __init__(self, df):
            self._df = df

        def average(self, period):
            """Mock .average() method for moving averages."""
            # Return another MockFinlabDataFrame to support chaining
            return MockFinlabDataFrame(self._df.rolling(period).mean())

        def rolling(self, period):
            """Mock .rolling() method - return MockRolling object."""
            return MockRolling(self._df, period)

        def shift(self, periods=1):
            """Mock .shift() method."""
            return MockFinlabDataFrame(self._df.shift(periods))

        def sustain(self, days, min_days=None):
            """Mock .sustain() method for finlab conditions."""
            # Return a mock boolean condition
            return MockFinlabDataFrame(self._df > 0)

        def rank(self, axis=1, pct=True, ascending=True):
            """Mock .rank() method for cross-sectional ranking."""
            return MockFinlabDataFrame(self._df.rank(axis=axis, pct=pct, ascending=ascending))

        def is_largest(self, n):
            """Mock .is_largest() method for top N selection."""
            return MockFinlabDataFrame(self._df.rank(pct=True, ascending=False) <= (n / len(self._df.columns)))

        def is_smallest(self, n):
            """Mock .is_smallest() method for bottom N selection."""
            return MockFinlabDataFrame(self._df.rank(pct=True, ascending=True) <= (n / len(self._df.columns)))

        def __gt__(self, other):
            """Mock > operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df > other._df)
            return MockFinlabDataFrame(self._df > other)

        def __ge__(self, other):
            """Mock >= operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df >= other._df)
            return MockFinlabDataFrame(self._df >= other)

        def __lt__(self, other):
            """Mock < operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df < other._df)
            return MockFinlabDataFrame(self._df < other)

        def __le__(self, other):
            """Mock <= operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df <= other._df)
            return MockFinlabDataFrame(self._df <= other)

        def __eq__(self, other):
            """Mock == operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df == other._df)
            return MockFinlabDataFrame(self._df == other)

        def __and__(self, other):
            """Mock & operator for boolean conditions."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df & other._df)
            return MockFinlabDataFrame(self._df & other)

        def __or__(self, other):
            """Mock | operator for boolean conditions."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df | other._df)
            return MockFinlabDataFrame(self._df | other)

        def __invert__(self):
            """Mock ~ operator for boolean negation."""
            return MockFinlabDataFrame(~self._df)

        def __mul__(self, other):
            """Mock * operator for weighting."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df * other._df)
            return MockFinlabDataFrame(self._df * other)

        def __truediv__(self, other):
            """Mock / operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df / other._df)
            return MockFinlabDataFrame(self._df / other)

        def __sub__(self, other):
            """Mock - operator."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df - other._df)
            return MockFinlabDataFrame(self._df - other)

        def __getitem__(self, key):
            """Mock [] operator for filtering."""
            if isinstance(key, MockFinlabDataFrame):
                return MockFinlabDataFrame(self._df[key._df])
            return MockFinlabDataFrame(self._df[key])

        def __rtruediv__(self, other):
            """Mock right-hand / operator (for float / MockFinlabDataFrame)."""
            if isinstance(other, MockFinlabDataFrame):
                return MockFinlabDataFrame(other._df / self._df)
            return MockFinlabDataFrame(other / self._df)

        def __repr__(self):
            """String representation for debugging."""
            return f"MockFinlabDataFrame(shape={self._df.shape}, dtype={self._df.dtypes.unique()})"

        def __str__(self):
            """User-friendly string representation."""
            return f"MockFinlabDataFrame with {self._df.shape[0]} rows and {self._df.shape[1]} columns"

        def __bool__(self):
            """Boolean conversion - defer to underlying DataFrame."""
            return bool(self._df.empty == False)

    def mock_get(dataset_key: str, verbose: bool = False):
        """Mock implementation of DataCache.get()."""
        filename = fixture_map.get(dataset_key)
        if filename is None:
            raise ValueError(f"Unknown dataset: {dataset_key}")

        filepath = FIXTURE_DIR / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Fixture file not found: {filepath}")

        df = pd.read_parquet(filepath)
        return MockFinlabDataFrame(df)

    # Create mock DataCache instance
    mock_cache = MagicMock()
    mock_cache.get = mock_get

    # Mock the DataCache.get_instance() class method
    from src.templates import data_cache
    monkeypatch.setattr(data_cache.DataCache, 'get_instance', lambda: mock_cache)

    return mock_cache


@pytest.fixture
def mock_finlab_sim(monkeypatch):
    """
    Mock finlab.backtest.sim with predictable metrics for template tests.

    This fixture replaces finlab.backtest.sim() with a mock that returns
    a report object with consistent performance metrics.

    Mock Metrics:
        - sharpe_ratio: 2.0 (good risk-adjusted returns)
        - annual_return: 0.25 (25% annual return)
        - max_drawdown: -0.15 (-15% max drawdown)

    Usage:
        def test_strategy_generation(mock_data_cache, mock_finlab_sim):
            template = TurtleTemplate()
            report, metrics = template.generate_strategy(params)
            assert metrics['sharpe_ratio'] == 2.0

    Returns:
        MagicMock: Mocked backtest report with metrics property
    """
    # Create mock metrics object with callable methods
    mock_metrics = MagicMock()
    mock_metrics.sharpe_ratio = Mock(return_value=2.0)
    mock_metrics.annual_return = Mock(return_value=0.25)
    mock_metrics.max_drawdown = Mock(return_value=-0.15)

    # Create mock report object
    mock_report = MagicMock()
    mock_report.metrics = mock_metrics

    def mock_sim(*args, **kwargs):
        """Mock implementation of finlab.backtest.sim()."""
        return mock_report

    # Mock both finlab.backtest.sim and finlab.backtest module
    try:
        import finlab.backtest
        monkeypatch.setattr(finlab.backtest, 'sim', mock_sim)
    except ImportError:
        # If finlab is not installed, create a mock module
        import sys
        mock_backtest = MagicMock()
        mock_backtest.sim = mock_sim
        mock_finlab = MagicMock()
        mock_finlab.backtest = mock_backtest
        sys.modules['finlab'] = mock_finlab
        sys.modules['finlab.backtest'] = mock_backtest

    return mock_report


@pytest.fixture
def sample_strategy_genome() -> Dict[str, Any]:
    """
    Sample strategy genome for Hall of Fame tests.

    Provides a realistic strategy genome dictionary for testing Hall of Fame
    repository operations (add, retrieve, novelty detection).

    Returns:
        Dict[str, Any]: Strategy genome with standard structure
    """
    return {
        'strategy_id': 'test_strategy_001',
        'template': 'turtle',
        'params': {
            'yield_threshold': 6.0,
            'ma_short': 20,
            'ma_long': 60,
            'rev_short': 3,
            'rev_long': 12,
            'op_margin_threshold': 3,
            'director_threshold': 10,
            'vol_min': 50,
            'vol_max': 10000,
            'n_stocks': 10,
            'stop_loss': 0.06,
            'take_profit': 0.5,
            'position_limit': 0.125,
            'resample': 'M'
        },
        'code': '''def initialize(context):
    pass

def handle_data(context, data):
    pass

def before_trading_start(context, data):
    pass
''',
        'metrics': {
            'sharpe_ratio': 2.5,
            'annual_return': 0.30,
            'max_drawdown': -0.12
        },
        'timestamp': '2025-10-12T10:00:00'
    }


# Pytest configuration for markers
def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: marks tests requiring Finlab API access"
    )
