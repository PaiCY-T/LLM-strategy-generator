"""
Error Classification System for Backtest Execution Results.

Categorizes execution errors using pattern matching on error types and messages.
Supports both English and Chinese error messages for comprehensive coverage.

Error Categories:
    - TIMEOUT: Execution time limit exceeded
    - DATA_MISSING: Missing or inaccessible data (KeyError, AttributeError)
    - CALCULATION: Mathematical/computation errors (ZeroDivisionError, OverflowError)
    - SYNTAX: Code syntax or structure errors (SyntaxError, IndentationError)
    - OTHER: Uncategorized errors

Key Features:
    - Regex-based pattern matching for robust error detection
    - Support for Chinese and English error messages
    - Hierarchical error classification (type-first, then message patterns)
    - Batch error grouping for analysis and debugging
    - Clear documentation of classification rules
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

if False:  # TYPE_CHECKING
    from .executor import ExecutionResult


class ErrorCategory(Enum):
    """Classification categories for execution errors.

    Attributes:
        TIMEOUT: Execution exceeded time limit
        DATA_MISSING: Data/key not found or inaccessible
        CALCULATION: Mathematical or computation errors
        SYNTAX: Code syntax or structure errors
        OTHER: Uncategorized or unknown errors
    """

    TIMEOUT = "timeout"
    DATA_MISSING = "data_missing"
    CALCULATION = "calculation"
    SYNTAX = "syntax"
    OTHER = "other"


@dataclass
class ErrorPattern:
    """Pattern definition for error classification.

    Attributes:
        name: Human-readable pattern name
        error_types: List of error types to match (e.g., ['KeyError', 'AttributeError'])
        message_patterns: Compiled regex patterns for error message matching
        category: ErrorCategory this pattern maps to
    """

    name: str
    error_types: List[str]
    message_patterns: List[str]
    category: ErrorCategory
    compiled_patterns: List[re.Pattern] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        """Compile regex patterns after initialization."""
        # Compile all message patterns with case-insensitive flag
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.message_patterns
        ]

    def matches_error(self, error_type: str, error_message: str) -> bool:
        """Check if this pattern matches the given error.

        Args:
            error_type: Type of error (e.g., 'KeyError')
            error_message: Error message text (may be in Chinese or English)

        Returns:
            True if error_type matches and any message_pattern matches
        """
        # Type must match one of the specified error types
        if error_type not in self.error_types:
            return False

        # If no message patterns, type match is sufficient
        if not self.compiled_patterns:
            return True

        # Message must match at least one pattern
        return any(
            pattern.search(error_message) for pattern in self.compiled_patterns
        )


class ErrorClassifier:
    """Classify execution errors into standardized categories.

    Uses pattern matching on error types and messages to categorize errors
    for better debugging and analysis. Supports both English and Chinese
    error messages.

    Example:
        classifier = ErrorClassifier()
        category = classifier.classify_error("KeyError", "key 'price' not found")
        # Returns: ErrorCategory.DATA_MISSING

        grouped = classifier.group_errors(execution_results)
        # Returns: {
        #     ErrorCategory.DATA_MISSING: [result1, result2],
        #     ErrorCategory.CALCULATION: [result3],
        #     ...
        # }
    """

    def __init__(self) -> None:
        """Initialize error classifier with predefined patterns."""
        self.patterns = self._create_patterns()

    @staticmethod
    def _create_patterns() -> List[ErrorPattern]:
        """Create and return all error classification patterns.

        Returns:
            List of ErrorPattern objects defining error classification rules

        Pattern Strategy:
            1. TIMEOUT patterns: TimeoutError, execution timeout
            2. DATA_MISSING patterns: KeyError, AttributeError, missing data references
            3. CALCULATION patterns: ZeroDivisionError, OverflowError, math errors
            4. SYNTAX patterns: SyntaxError, IndentationError, code structure
            5. OTHER: Fallback category for unmatched errors
        """
        return [
            # TIMEOUT patterns - high priority (checked first)
            ErrorPattern(
                name="timeout_error",
                error_types=["TimeoutError"],
                message_patterns=[
                    r"timeout",
                    r"exceeded timeout",
                    r"time limit",
                    r"timed out",
                ],
                category=ErrorCategory.TIMEOUT,
            ),
            # DATA_MISSING patterns - data access errors
            ErrorPattern(
                name="key_error",
                error_types=["KeyError"],
                message_patterns=[
                    r"key.*not.*found",
                    r"key.*error",
                    r"missing.*key",
                    r"not.*found",  # Generic not found message
                    r"找不到鍵",  # Chinese: "key not found"
                    r"鍵值",  # Chinese: "key value"
                ],
                category=ErrorCategory.DATA_MISSING,
            ),
            ErrorPattern(
                name="attribute_error",
                error_types=["AttributeError"],
                message_patterns=[
                    r"has no attribute",
                    r"object has no attribute",
                    r"沒有屬性",  # Chinese: "no attribute"
                    r"attribute.*error",
                ],
                category=ErrorCategory.DATA_MISSING,
            ),
            ErrorPattern(
                name="index_error",
                error_types=["IndexError"],
                message_patterns=[
                    r"index.*out.*range",
                    r"out of range",
                    r"索引超出範圍",  # Chinese: "index out of range"
                    r"list index",
                ],
                category=ErrorCategory.DATA_MISSING,
            ),
            ErrorPattern(
                name="column_not_found",
                error_types=["ValueError", "KeyError"],
                message_patterns=[
                    r"column.*not.*found",
                    r"missing.*column",
                    r"找不到欄位",  # Chinese: "column not found"
                    r"欄位.*不存在",  # Chinese: "field does not exist"
                ],
                category=ErrorCategory.DATA_MISSING,
            ),
            ErrorPattern(
                name="data_missing",
                error_types=["ValueError", "TypeError"],
                message_patterns=[
                    r"data.*missing",
                    r"no.*data",
                    r"data.*unavailable",
                    r"資料.*遺失",  # Chinese: "data missing"
                    r"資料不可用",  # Chinese: "data unavailable"
                    r"數據.*缺失",  # Chinese: "data missing (alternate)"
                ],
                category=ErrorCategory.DATA_MISSING,
            ),
            # CALCULATION patterns - mathematical/computation errors
            ErrorPattern(
                name="zero_division",
                error_types=["ZeroDivisionError"],
                message_patterns=[
                    r"division by zero",
                    r"divide by zero",
                    r"zero.*division",
                    r"除以零",  # Chinese: "divide by zero"
                ],
                category=ErrorCategory.CALCULATION,
            ),
            ErrorPattern(
                name="overflow_error",
                error_types=["OverflowError"],
                message_patterns=[
                    r"overflow",
                    r"value.*too.*large",
                    r"數值溢出",  # Chinese: "value overflow"
                ],
                category=ErrorCategory.CALCULATION,
            ),
            ErrorPattern(
                name="type_error_calc",
                error_types=["TypeError"],
                message_patterns=[
                    r"cannot.*multiply",
                    r"cannot.*add",
                    r"cannot.*divide",
                    r"unsupported.*operand",
                    r"無法.*相乘",  # Chinese: "cannot multiply"
                    r"不支援.*操作",  # Chinese: "unsupported operation"
                ],
                category=ErrorCategory.CALCULATION,
            ),
            ErrorPattern(
                name="nan_error",
                error_types=["ValueError", "FloatingPointError"],
                message_patterns=[
                    r"invalid value",
                    r"nan",
                    r"infinity",
                    r"inf",
                    r"無效.*值",  # Chinese: "invalid value"
                ],
                category=ErrorCategory.CALCULATION,
            ),
            # SYNTAX patterns - code syntax and structure errors
            ErrorPattern(
                name="syntax_error",
                error_types=["SyntaxError"],
                message_patterns=[
                    r"syntax error",
                    r"invalid syntax",
                    r"unexpected",
                    r"語法錯誤",  # Chinese: "syntax error"
                ],
                category=ErrorCategory.SYNTAX,
            ),
            ErrorPattern(
                name="indent_error",
                error_types=["IndentationError"],
                message_patterns=[
                    r"indentation",
                    r"indent",
                    r"縮進",  # Chinese: "indentation"
                ],
                category=ErrorCategory.SYNTAX,
            ),
            ErrorPattern(
                name="name_error",
                error_types=["NameError"],
                message_patterns=[
                    r"not defined",
                    r"undefined",
                    r"name.*error",
                    r"未定義",  # Chinese: "not defined"
                    r"未知的名稱",  # Chinese: "unknown name"
                ],
                category=ErrorCategory.SYNTAX,
            ),
            ErrorPattern(
                name="import_error",
                error_types=["ImportError", "ModuleNotFoundError"],
                message_patterns=[
                    r"cannot import",
                    r"no module",
                    r"import.*error",
                    r"無法導入",  # Chinese: "cannot import"
                    r"找不到模組",  # Chinese: "module not found"
                ],
                category=ErrorCategory.SYNTAX,
            ),
        ]

    def classify_error(
        self,
        error_type: str,
        error_message: str = "",
    ) -> ErrorCategory:
        """Classify a single error into a category.

        Classification algorithm:
            1. Check patterns in order (order matters for priority)
            2. First matching pattern determines category
            3. Fall back to OTHER if no patterns match

        Args:
            error_type: Type of error (e.g., 'KeyError', 'TimeoutError')
            error_message: Error message text (may be empty, English or Chinese)

        Returns:
            ErrorCategory matching the error

        Example:
            >>> classifier = ErrorClassifier()
            >>> classifier.classify_error("KeyError", "key 'price' not found")
            <ErrorCategory.DATA_MISSING: 'data_missing'>

            >>> classifier.classify_error("ZeroDivisionError", "division by zero")
            <ErrorCategory.CALCULATION: 'calculation'>

            >>> classifier.classify_error("UnknownError", "some weird issue")
            <ErrorCategory.OTHER: 'other'>
        """
        # Normalize error type for case-insensitive matching
        error_type_normalized = error_type.strip()
        error_message_normalized = error_message.strip()

        # Check each pattern in order
        for pattern in self.patterns:
            if pattern.matches_error(error_type_normalized, error_message_normalized):
                return pattern.category

        # No pattern matched - return OTHER
        return ErrorCategory.OTHER

    def group_errors(
        self,
        execution_results: List["ExecutionResult"],
    ) -> Dict[ErrorCategory, List["ExecutionResult"]]:
        """Group execution results by error category.

        Groups all failed results into categories based on their error types
        and messages. Successful results are ignored.

        Args:
            execution_results: List of ExecutionResult objects to categorize

        Returns:
            Dictionary mapping ErrorCategory to list of ExecutionResult objects
            Only categories with at least one error are included

        Example:
            >>> classifier = ErrorClassifier()
            >>> grouped = classifier.group_errors(results)
            >>> print(f"Data errors: {len(grouped.get(ErrorCategory.DATA_MISSING, []))}")
            Data errors: 3
            >>> print(f"Calculation errors: {len(grouped.get(ErrorCategory.CALCULATION, []))}")
            Calculation errors: 1
        """
        # Initialize category buckets
        grouped: Dict[ErrorCategory, List["ExecutionResult"]] = {
            category: [] for category in ErrorCategory
        }

        # Group results by category
        for result in execution_results:
            # Skip successful results
            if result.success:
                continue

            # Classify error and add to appropriate bucket
            category = self.classify_error(
                error_type=result.error_type or "",
                error_message=result.error_message or "",
            )
            grouped[category].append(result)

        # Remove empty categories for cleaner output
        return {
            category: results
            for category, results in grouped.items()
            if results
        }

    def get_error_summary(
        self,
        execution_results: List["ExecutionResult"],
    ) -> Dict[str, int]:
        """Get summary of error counts by category.

        Useful for quick statistics on error distribution.

        Args:
            execution_results: List of ExecutionResult objects

        Returns:
            Dictionary mapping category names (strings) to error counts
            Includes all categories even if count is 0

        Example:
            >>> classifier = ErrorClassifier()
            >>> summary = classifier.get_error_summary(results)
            >>> print(summary)
            {
                'data_missing': 5,
                'calculation': 2,
                'syntax': 1,
                'timeout': 0,
                'other': 1
            }
        """
        grouped = self.group_errors(execution_results)
        # Return all categories with their counts
        return {
            category.value: len(grouped.get(category, []))
            for category in ErrorCategory
        }


__all__ = [
    "ErrorCategory",
    "ErrorClassifier",
    "ErrorPattern",
]
