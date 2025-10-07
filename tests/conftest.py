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
