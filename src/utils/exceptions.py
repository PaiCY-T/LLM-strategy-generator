"""
Custom Exception Hierarchy for Finlab Backtesting Optimization System.

This module defines a hierarchy of custom exceptions for different error scenarios
in the backtesting system. All custom exceptions inherit from FinlabSystemError
to allow catching all system-specific errors.

Exception Hierarchy:
    FinlabSystemError (base)
    ├── DataError
    ├── BacktestError
    ├── ValidationError
    ├── NormalizationError
    ├── AnalysisError
    └── StorageError

Usage:
    >>> from src.utils.exceptions import DataError
    >>> raise DataError("Failed to fetch stock data")

    >>> try:
    >>>     # some operation
    >>> except FinlabSystemError as e:
    >>>     # Catches all system errors
    >>>     logger.error(f"System error: {e}")
"""


class FinlabSystemError(Exception):
    """
    Base exception for all Finlab Backtesting Optimization System errors.

    All custom exceptions in this system inherit from this base class,
    allowing for catch-all error handling when needed.

    Use this class directly only when the error doesn't fit into
    more specific categories.

    Example:
        >>> try:
        >>>     # system operation
        >>> except FinlabSystemError as e:
        >>>     logger.error(f"System error occurred: {e}")
    """

    pass


class DataError(FinlabSystemError):
    """
    Exception raised for data retrieval and validation errors.

    Raised when:
        - Finlab API fails to retrieve market data
        - Network connection issues prevent data access
        - Data validation fails (missing columns, invalid formats)
        - Cache corruption or read/write failures
        - Dataset not available or access denied

    Examples:
        >>> # API failure
        >>> raise DataError("Finlab API returned 500 status code")

        >>> # Data validation
        >>> raise DataError("Missing required column '收盤價' in dataset")

        >>> # Cache error
        >>> raise DataError("Failed to load cached data: file corrupted")
    """

    pass


class BacktestError(FinlabSystemError):
    """
    Exception raised for backtest execution errors.

    Raised when:
        - Backtest execution fails or times out
        - Invalid position DataFrame provided
        - Strategy code contains errors
        - Insufficient data for backtest period
        - Resource constraints prevent execution

    Examples:
        >>> # Execution failure
        >>> raise BacktestError("Backtest execution timed out after 120s")

        >>> # Invalid input
        >>> raise BacktestError("Position DataFrame contains NaN values")

        >>> # Strategy error
        >>> raise BacktestError(
        >>>     "Strategy code raised exception: division by zero"
        >>> )
    """

    pass


class ValidationError(FinlabSystemError):
    """
    Exception raised for input validation errors.

    Raised when:
        - User input fails validation (invalid dates, parameters)
        - Configuration values are out of acceptable range
        - Required fields are missing or empty
        - Data types don't match expected types

    Note: This is different from Python's built-in ValueError.
    Use this for application-level validation errors.

    Examples:
        >>> # Date validation
        >>> raise ValidationError("Start date must be before end date")

        >>> # Parameter validation
        >>> raise ValidationError(
        >>>     "Fee ratio must be between 0 and 1, got: 1.5"
        >>> )

        >>> # Required field
        >>> raise ValidationError("Stock symbol is required")
    """

    pass


class NormalizationError(FinlabSystemError):
    """
    Exception raised for YAML normalization errors.

    Raised when:
        - YAML contains Jinja templates that cannot be normalized
        - Required fields are missing and cannot be inferred
        - Data structure is fundamentally incompatible with schema
        - Transformation would result in data loss or ambiguity

    Examples:
        >>> # Jinja template detected
        >>> raise NormalizationError(
        >>>     "Cannot normalize YAML with Jinja templates: {{ parameters.period }}"
        >>> )

        >>> # Missing required field
        >>> raise NormalizationError("Missing required field: 'indicators'")

        >>> # Ambiguous structure
        >>> raise NormalizationError(
        >>>     "Cannot determine indicator type from provided fields"
        >>> )
    """

    pass


class AnalysisError(FinlabSystemError):
    """
    Exception raised for AI analysis errors.

    Raised when:
        - Claude API fails to respond or times out
        - AI-generated code is invalid or cannot be parsed
        - Strategy improvement suggestions cannot be generated
        - API rate limits exceeded
        - Authentication failures with Claude API

    Examples:
        >>> # API failure
        >>> raise AnalysisError("Claude API timeout after 30s")

        >>> # Invalid response
        >>> raise AnalysisError(
        >>>     "AI-generated code failed syntax validation"
        >>> )

        >>> # Rate limit
        >>> raise AnalysisError("Claude API rate limit exceeded")
    """

    pass


class StorageError(FinlabSystemError):
    """
    Exception raised for database and storage errors.

    Raised when:
        - SQLite database operations fail
        - Database connection cannot be established
        - Query execution errors or constraint violations
        - Backup or restore operations fail
        - Disk space exhausted or permission denied

    Examples:
        >>> # Database connection
        >>> raise StorageError("Failed to connect to database: locked")

        >>> # Query error
        >>> raise StorageError("Unique constraint violation on iteration_id")

        >>> # Backup failure
        >>> raise StorageError("Database backup failed: disk full")
    """

    pass
