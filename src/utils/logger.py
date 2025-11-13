"""
Logging infrastructure for Finlab Backtesting Optimization System.

This module provides a centralized logging configuration with file rotation,
color-coded console output, and UTF-8 encoding support for Chinese characters.

Features:
    - File handler with automatic rotation (10MB max, 5 backups)
    - Console handler with color-coded output by level
    - Configurable log level from settings
    - UTF-8 encoding for international character support
    - Thread-safe logging

Example:
    >>> from src.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("System initialized")
    >>> logger.error("Error occurred", exc_info=True)
"""

import io
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, cast, Any

from config.settings import Settings


# ANSI color codes for console output
class ColorFormatter(logging.Formatter):
    """Custom formatter with color-coded output for different log levels."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with color coding.

        Args:
            record: Log record to format

        Returns:
            Formatted and color-coded log message
        """
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.RESET}"
            )

        # Format the message
        formatted = super().format(record)

        # Reset levelname to original for subsequent handlers
        record.levelname = levelname

        return formatted


# Cache for loggers to prevent duplicate handlers
_logger_cache: dict[str, logging.Logger] = {}
_logger_cache_lock = threading.Lock()

# Singleton settings instance with lazy initialization
_settings_instance: Optional[Settings] = None
_settings_lock = threading.Lock()


def _get_or_create_settings() -> Settings:
    """
    Lazily initialize and return the Settings instance (thread-safe singleton).

    Uses double-checked locking pattern for optimal performance in
    high-concurrency scenarios.

    Returns:
        Settings instance

    Raises:
        ValueError: If required environment variables are missing
    """
    global _settings_instance

    # Fast path: return if already initialized (no lock needed)
    if _settings_instance is not None:
        return _settings_instance

    # Slow path: initialize with lock
    with _settings_lock:
        # Double-check inside lock
        if _settings_instance is None:
            _settings_instance = Settings()
        return _settings_instance


def _reset_settings_for_testing() -> None:
    """
    Reset the Settings singleton instance (TESTING ONLY).

    This function allows tests to reload settings with different environment
    variables. Should NEVER be called in production code.

    Thread-safe operation that clears the cached settings instance.

    Warning:
        This is for testing purposes only. Calling this in production
        code will cause unpredictable behavior.

    Example:
        >>> # In test setup
        >>> _reset_settings_for_testing()
        >>> os.environ["LOG_LEVEL"] = "DEBUG"
        >>> settings = _get_or_create_settings()
        >>> assert settings.log_level == "DEBUG"
    """
    global _settings_instance

    with _settings_lock:
        _settings_instance = None


def get_logger(
    name: str, log_file: Optional[str] = None
) -> logging.Logger:
    """
    Get or create a logger with file and console handlers.

    Creates a logger with the following configuration:
    - File handler with rotation (10MB max size, 5 backup files)
    - Console handler with color-coded output and UTF-8 support
    - Log level from settings.LOG_LEVEL
    - UTF-8 encoding for international characters
    - Path traversal protection for log file names

    The logger is cached to prevent duplicate handlers when called
    multiple times with the same name. Thread-safe for concurrent access.

    Args:
        name: Logger name (typically __name__ from calling module)
        log_file: Optional log file name (filename only, no paths).
                  If None, uses 'application.log'

    Returns:
        Configured logger instance

    Raises:
        ValueError: If log_file contains path separators or parent references

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
        >>> logger.error("Failed to process", exc_info=True)

        >>> # With custom log file
        >>> logger = get_logger(__name__, log_file="backtest.log")
        >>> logger.debug("Backtest iteration 5 completed")
    """
    # Validate log_file to prevent path traversal attacks
    if log_file and ('/' in log_file or '\\' in log_file or '..' in log_file):
        raise ValueError(
            f"Invalid log_file: '{log_file}'. "
            f"Must be a filename only (no path separators or '..')."
        )

    cache_key = f"{name}:{log_file or 'default'}"

    # Fast path: check cache without lock
    if cache_key in _logger_cache:
        return _logger_cache[cache_key]

    # Setup logger outside lock to minimize lock contention
    logger = logging.getLogger(name)

    # Load settings with fallback defaults
    log_level = logging.INFO
    log_dir = Path("./logs")
    max_bytes = 10 * 1024 * 1024
    backup_count = 5
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    try:
        settings = _get_or_create_settings()
        log_level = getattr(logging, settings.log_level)
        log_dir = settings.logging.log_dir
        max_bytes = settings.logging.max_file_size_mb * 1024 * 1024
        backup_count = settings.logging.backup_count
        log_format = settings.logging.format
    except ValueError as e:
        sys.stderr.write(
            f"WARNING: Settings configuration error: {e}. "
            f"Using default logging configuration.\n"
        )
    except Exception as e:
        sys.stderr.write(
            f"WARNING: Unexpected error loading settings: {e}. "
            f"Using default logging configuration.\n"
        )

    logger.setLevel(log_level)

    # Create log directory if it doesn't exist (I/O outside lock)
    log_dir.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    log_file_path = log_dir / (log_file or "application.log")
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(log_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler with UTF-8 encoding support
    # Ensure stdout supports UTF-8 for Chinese characters
    if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
        stdout_stream: Any = io.TextIOWrapper(
            cast(io.BufferedWriter, sys.stdout.buffer),
            encoding='utf-8',
            errors='replace'
        )
        console_handler: Any = logging.StreamHandler(stdout_stream)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = ColorFormatter(log_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    # Thread-safe cache insertion (only lock for cache modification)
    with _logger_cache_lock:
        # Double-check: another thread might have created it
        if cache_key in _logger_cache:
            # Close handlers from our logger and return cached one
            for handler in logger.handlers:
                handler.close()
            return _logger_cache[cache_key]

        _logger_cache[cache_key] = logger
        return logger


def clear_logger_cache() -> None:
    """
    Clear the logger cache and close all handler resources.

    Properly closes all file handlers and clears the cache. This prevents
    resource leaks (open file descriptors) and is essential for testing
    or when reconfiguring loggers with new settings.

    Thread-safe operation with proper resource cleanup.

    Example:
        >>> clear_logger_cache()
        >>> logger = get_logger(__name__)  # Will create fresh logger
    """
    with _logger_cache_lock:
        for logger_instance in _logger_cache.values():
            for handler in logger_instance.handlers:
                handler.close()
            logger_instance.handlers.clear()
        _logger_cache.clear()
