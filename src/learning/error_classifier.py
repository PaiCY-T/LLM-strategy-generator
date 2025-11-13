"""
Error Classifier for Learning Module - TDD GREEN Phase.

Implements IErrorClassifier Protocol to categorize execution errors into
standardized categories for debugging, analysis, and feedback generation.

This implementation adapts the existing backtest.error_classifier patterns
to satisfy the learning module's Protocol interface requirements.

Key Differences from Backtest Classifier:
    - Takes Dict[str, Any] instead of separate error_type/error_message params
    - Returns Dict[str, Any] instead of ErrorCategory enum
    - Supports additional classification levels and metadata

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Phase 5B.4: Implement IErrorClassifier Protocol
"""

from typing import Dict, Any, Optional
from src.backtest.error_classifier import ErrorCategory, ErrorClassifier as BacktestClassifier


class ErrorClassifier:
    """Classify execution errors implementing IErrorClassifier Protocol.

    Behavioral Contracts (from IErrorClassifier):
        - MUST be deterministic: same input produces same category
        - MUST return valid classification for any input (never raises)
        - MUST support both English and Chinese error messages
        - MUST handle missing keys gracefully (default to UNKNOWN)

    Example Usage:
        >>> classifier = ErrorClassifier()
        >>> result = classifier.classify_error({
        ...     'error_type': 'SyntaxError',
        ...     'error_msg': 'invalid syntax'
        ... })
        >>> print(result['category'])  # ErrorCategory.SYNTAX
        >>> print(result['classification_level'])  # 'LEVEL_1'
    """

    def __init__(self) -> None:
        """Initialize error classifier with backtest classifier engine."""
        # Delegate to existing backtest classifier for classification logic
        self._backtest_classifier = BacktestClassifier()

    def classify_error(self, strategy_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Classify execution error into standardized category.

        Behavioral Contract:
            - MUST be deterministic: same input produces same category
            - MUST return valid classification for any input (never raises)
            - MUST support both English and Chinese error messages
            - MUST handle missing keys gracefully (default to UNKNOWN)

        Pre-conditions:
            - strategy_metrics MUST be a dictionary (may be empty)
            - Keys 'error_type' and 'error_msg' are optional

        Post-conditions:
            - Returns dict with 'category' key (ErrorCategory enum value)
            - Returns dict with 'classification_level' key (str: LEVEL_X)
            - If input contains no error info, returns UNKNOWN category

        Args:
            strategy_metrics: Execution result containing error information
                Expected keys (all optional):
                - error_type: Exception class name (str)
                - error_msg: Exception message (str)
                - traceback: Full error traceback (str)

        Returns:
            Dictionary with classification result:
            - category: ErrorCategory enum value
            - classification_level: Severity level (str: LEVEL_X)
            - confidence: Classification confidence 0.0-1.0 (optional)
            - details: Additional metadata (optional)

        Example:
            >>> classifier = ErrorClassifier()
            >>> result = classifier.classify_error({
            ...     'error_type': 'KeyError',
            ...     'error_msg': "key 'price' not found"
            ... })
            >>> result['category']
            <ErrorCategory.DATA_MISSING: 'data_missing'>
            >>> result['classification_level']
            'LEVEL_2'
        """
        # Extract error info from metrics (with safe defaults)
        error_type = self._safe_get_string(strategy_metrics, 'error_type')
        error_msg = self._safe_get_string(strategy_metrics, 'error_msg')

        # Use backtest classifier for category classification
        category = self._backtest_classifier.classify_error(
            error_type=error_type,
            error_message=error_msg
        )

        # Map category to classification level
        classification_level = self._map_category_to_level(category)

        # Build return dictionary
        result: Dict[str, Any] = {
            'category': category,
            'classification_level': classification_level,
        }

        # Add optional confidence score (based on error type presence)
        if error_type:
            result['confidence'] = 1.0 if error_msg else 0.7
        else:
            result['confidence'] = 0.3  # Low confidence for missing error_type

        return result

    def _safe_get_string(
        self,
        metrics: Dict[str, Any],
        key: str,
        default: str = ""
    ) -> str:
        """Safely extract string value from metrics dict.

        Behavioral Contract:
            - MUST handle None values gracefully (return default)
            - MUST handle missing keys gracefully (return default)
            - MUST normalize whitespace (strip leading/trailing)
            - MUST be deterministic (same input → same output)

        Pre-conditions:
            - metrics MUST be a dictionary (may be empty)
            - key MUST be a string
            - default MUST be a string

        Post-conditions:
            - Returns non-None string (never None)
            - Whitespace is stripped from result
            - Empty/None values → default value

        Args:
            metrics: Dictionary to extract from
            key: Key to extract
            default: Default value if key missing or None

        Returns:
            Normalized string value or default

        Example:
            >>> classifier = ErrorClassifier()
            >>> classifier._safe_get_string({'error_type': 'ValueError'}, 'error_type')
            'ValueError'
            >>> classifier._safe_get_string({'error_type': None}, 'error_type', 'UNKNOWN')
            'UNKNOWN'
            >>> classifier._safe_get_string({}, 'missing_key', 'DEFAULT')
            'DEFAULT'
        """
        value = metrics.get(key, default)

        # Handle None explicitly
        if value is None:
            return default

        # Convert to string and normalize whitespace
        return str(value).strip()

    def _map_category_to_level(self, category: ErrorCategory) -> str:
        """Map ErrorCategory to classification level string.

        Behavioral Contract:
            - MUST be deterministic (same category → same level)
            - MUST return valid level string (LEVEL_1 to LEVEL_5)
            - MUST handle unknown categories (default to LEVEL_5)

        Classification Levels (severity ranking):
            - LEVEL_1: SYNTAX errors (most severe, prevents execution)
            - LEVEL_2: DATA_MISSING errors (data issues)
            - LEVEL_3: CALCULATION errors (runtime math issues)
            - LEVEL_4: TIMEOUT errors (resource limits)
            - LEVEL_5: OTHER errors (unknown/uncategorized)

        Pre-conditions:
            - category MUST be an ErrorCategory enum value

        Post-conditions:
            - Returns string in format "LEVEL_N" where N ∈ {1,2,3,4,5}
            - Mapping is 1-to-1 (each category → exactly one level)

        Args:
            category: ErrorCategory enum value

        Returns:
            Classification level string (LEVEL_1 to LEVEL_5)

        Example:
            >>> classifier = ErrorClassifier()
            >>> classifier._map_category_to_level(ErrorCategory.SYNTAX)
            'LEVEL_1'
            >>> classifier._map_category_to_level(ErrorCategory.DATA_MISSING)
            'LEVEL_2'
            >>> classifier._map_category_to_level(ErrorCategory.OTHER)
            'LEVEL_5'
        """
        # Map categories to severity levels
        level_mapping = {
            ErrorCategory.SYNTAX: 'LEVEL_1',      # Most severe
            ErrorCategory.DATA_MISSING: 'LEVEL_2',
            ErrorCategory.CALCULATION: 'LEVEL_3',
            ErrorCategory.TIMEOUT: 'LEVEL_4',
            ErrorCategory.OTHER: 'LEVEL_5',       # Least severe
        }

        return level_mapping.get(category, 'LEVEL_5')


__all__ = ['ErrorClassifier']
