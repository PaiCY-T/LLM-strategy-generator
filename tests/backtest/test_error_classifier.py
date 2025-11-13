"""
Tests for Error Classification System.

Validates that the ErrorClassifier correctly categorizes execution errors
into appropriate categories based on error type and message patterns.

Test Coverage:
    - Individual error type classification
    - Message pattern matching (English and Chinese)
    - Batch error grouping
    - Error summary statistics
    - Edge cases and unknown errors
"""

import pytest
from src.backtest.error_classifier import ErrorCategory, ErrorClassifier
from src.backtest.executor import ExecutionResult


class TestErrorClassification:
    """Test individual error classification."""

    def setup_method(self) -> None:
        """Initialize classifier for each test."""
        self.classifier = ErrorClassifier()

    # TIMEOUT ERROR TESTS
    def test_timeout_error_basic(self) -> None:
        """Test TimeoutError classification."""
        category = self.classifier.classify_error(
            "TimeoutError",
            "Backtest execution exceeded timeout of 420 seconds"
        )
        assert category == ErrorCategory.TIMEOUT

    def test_timeout_error_variations(self) -> None:
        """Test various timeout error messages."""
        messages = [
            "execution timeout",
            "time limit exceeded",
            "timed out waiting for process",
        ]
        for msg in messages:
            category = self.classifier.classify_error("TimeoutError", msg)
            assert category == ErrorCategory.TIMEOUT, f"Failed for: {msg}"

    # DATA_MISSING ERROR TESTS
    def test_key_error(self) -> None:
        """Test KeyError classification."""
        category = self.classifier.classify_error(
            "KeyError",
            "'price' not found"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_key_error_chinese(self) -> None:
        """Test KeyError with Chinese message."""
        category = self.classifier.classify_error(
            "KeyError",
            "找不到鍵 'price'"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_attribute_error(self) -> None:
        """Test AttributeError classification."""
        category = self.classifier.classify_error(
            "AttributeError",
            "'DataFrame' object has no attribute 'invalid_col'"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_attribute_error_chinese(self) -> None:
        """Test AttributeError with Chinese message."""
        category = self.classifier.classify_error(
            "AttributeError",
            "沒有屬性 'missing_field'"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_index_error(self) -> None:
        """Test IndexError classification."""
        category = self.classifier.classify_error(
            "IndexError",
            "list index out of range"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_index_error_chinese(self) -> None:
        """Test IndexError with Chinese message."""
        category = self.classifier.classify_error(
            "IndexError",
            "索引超出範圍"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_column_not_found(self) -> None:
        """Test column missing classification."""
        category = self.classifier.classify_error(
            "KeyError",
            "Column 'close_price' not found"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_column_not_found_chinese(self) -> None:
        """Test column missing with Chinese message."""
        category = self.classifier.classify_error(
            "ValueError",
            "找不到欄位 'price'"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_data_missing_value_error(self) -> None:
        """Test data missing classification with ValueError."""
        category = self.classifier.classify_error(
            "ValueError",
            "data missing in required field"
        )
        assert category == ErrorCategory.DATA_MISSING

    def test_data_unavailable_chinese(self) -> None:
        """Test data unavailable with Chinese message."""
        category = self.classifier.classify_error(
            "ValueError",
            "資料不可用"
        )
        assert category == ErrorCategory.DATA_MISSING

    # CALCULATION ERROR TESTS
    def test_zero_division_error(self) -> None:
        """Test ZeroDivisionError classification."""
        category = self.classifier.classify_error(
            "ZeroDivisionError",
            "division by zero"
        )
        assert category == ErrorCategory.CALCULATION

    def test_zero_division_chinese(self) -> None:
        """Test ZeroDivisionError with Chinese message."""
        category = self.classifier.classify_error(
            "ZeroDivisionError",
            "除以零"
        )
        assert category == ErrorCategory.CALCULATION

    def test_overflow_error(self) -> None:
        """Test OverflowError classification."""
        category = self.classifier.classify_error(
            "OverflowError",
            "value too large"
        )
        assert category == ErrorCategory.CALCULATION

    def test_overflow_chinese(self) -> None:
        """Test OverflowError with Chinese message."""
        category = self.classifier.classify_error(
            "OverflowError",
            "數值溢出"
        )
        assert category == ErrorCategory.CALCULATION

    def test_type_error_arithmetic(self) -> None:
        """Test TypeError for arithmetic operations."""
        category = self.classifier.classify_error(
            "TypeError",
            "unsupported operand type(s) for +: 'str' and 'int'"
        )
        assert category == ErrorCategory.CALCULATION

    def test_type_error_multiply(self) -> None:
        """Test TypeError for multiplication."""
        category = self.classifier.classify_error(
            "TypeError",
            "cannot multiply sequence by non-int"
        )
        assert category == ErrorCategory.CALCULATION

    def test_type_error_chinese(self) -> None:
        """Test TypeError with Chinese message."""
        category = self.classifier.classify_error(
            "TypeError",
            "不支援該操作"
        )
        assert category == ErrorCategory.CALCULATION

    def test_nan_error(self) -> None:
        """Test NaN/Infinity error classification."""
        category = self.classifier.classify_error(
            "FloatingPointError",
            "invalid value encountered in operation"
        )
        assert category == ErrorCategory.CALCULATION

    # SYNTAX ERROR TESTS
    def test_syntax_error(self) -> None:
        """Test SyntaxError classification."""
        category = self.classifier.classify_error(
            "SyntaxError",
            "invalid syntax at line 5"
        )
        assert category == ErrorCategory.SYNTAX

    def test_syntax_error_chinese(self) -> None:
        """Test SyntaxError with Chinese message."""
        category = self.classifier.classify_error(
            "SyntaxError",
            "語法錯誤"
        )
        assert category == ErrorCategory.SYNTAX

    def test_indentation_error(self) -> None:
        """Test IndentationError classification."""
        category = self.classifier.classify_error(
            "IndentationError",
            "expected an indented block"
        )
        assert category == ErrorCategory.SYNTAX

    def test_indentation_chinese(self) -> None:
        """Test IndentationError with Chinese message."""
        category = self.classifier.classify_error(
            "IndentationError",
            "縮進錯誤"
        )
        assert category == ErrorCategory.SYNTAX

    def test_name_error(self) -> None:
        """Test NameError classification."""
        category = self.classifier.classify_error(
            "NameError",
            "name 'undefined_var' is not defined"
        )
        assert category == ErrorCategory.SYNTAX

    def test_name_error_chinese(self) -> None:
        """Test NameError with Chinese message."""
        category = self.classifier.classify_error(
            "NameError",
            "未定義的名稱"
        )
        assert category == ErrorCategory.SYNTAX

    def test_import_error(self) -> None:
        """Test ImportError classification."""
        category = self.classifier.classify_error(
            "ImportError",
            "cannot import name 'missing_module'"
        )
        assert category == ErrorCategory.SYNTAX

    def test_module_not_found(self) -> None:
        """Test ModuleNotFoundError classification."""
        category = self.classifier.classify_error(
            "ModuleNotFoundError",
            "No module named 'sklearn'"
        )
        assert category == ErrorCategory.SYNTAX

    def test_import_error_chinese(self) -> None:
        """Test ImportError with Chinese message."""
        category = self.classifier.classify_error(
            "ImportError",
            "找不到模組 'pandas'"
        )
        assert category == ErrorCategory.SYNTAX

    # OTHER ERROR TESTS
    def test_unknown_error(self) -> None:
        """Test unknown error classification."""
        category = self.classifier.classify_error(
            "UnknownError",
            "something went wrong"
        )
        assert category == ErrorCategory.OTHER

    def test_custom_exception(self) -> None:
        """Test custom exception classification."""
        category = self.classifier.classify_error(
            "CustomException",
            "custom error message"
        )
        assert category == ErrorCategory.OTHER

    def test_empty_error_message(self) -> None:
        """Test classification with empty error message."""
        category = self.classifier.classify_error("ValueError", "")
        assert category == ErrorCategory.OTHER

    def test_case_insensitive_matching(self) -> None:
        """Test case-insensitive pattern matching."""
        category1 = self.classifier.classify_error(
            "KeyError",
            "KEY NOT FOUND"
        )
        category2 = self.classifier.classify_error(
            "KeyError",
            "key not found"
        )
        assert category1 == category2 == ErrorCategory.DATA_MISSING


class TestErrorGrouping:
    """Test batch error grouping functionality."""

    def setup_method(self) -> None:
        """Initialize classifier and create test results."""
        self.classifier = ErrorClassifier()

    def test_group_errors_empty_list(self) -> None:
        """Test grouping empty result list."""
        grouped = self.classifier.group_errors([])
        assert len(grouped) == 0

    def test_group_errors_only_successful(self) -> None:
        """Test grouping with only successful results."""
        results = [
            ExecutionResult(success=True, execution_time=1.0, sharpe_ratio=0.5),
            ExecutionResult(success=True, execution_time=1.5, sharpe_ratio=0.7),
        ]
        grouped = self.classifier.group_errors(results)
        assert len(grouped) == 0

    def test_group_errors_mixed_results(self) -> None:
        """Test grouping with mixed success/failure results."""
        results = [
            ExecutionResult(success=True, execution_time=1.0),
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="key not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="ZeroDivisionError",
                error_message="division by zero",
                execution_time=0.3
            ),
        ]
        grouped = self.classifier.group_errors(results)
        assert len(grouped) == 2
        assert len(grouped[ErrorCategory.DATA_MISSING]) == 1
        assert len(grouped[ErrorCategory.CALCULATION]) == 1

    def test_group_errors_same_category(self) -> None:
        """Test grouping multiple errors in same category."""
        results = [
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="key 'a' not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="key 'b' not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="AttributeError",
                error_message="has no attribute",
                execution_time=0.5
            ),
        ]
        grouped = self.classifier.group_errors(results)
        assert len(grouped) == 1
        assert len(grouped[ErrorCategory.DATA_MISSING]) == 3

    def test_group_errors_all_categories(self) -> None:
        """Test grouping with errors in all categories."""
        results = [
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="timeout",
                execution_time=420.0
            ),
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="key not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="ZeroDivisionError",
                error_message="division by zero",
                execution_time=0.3
            ),
            ExecutionResult(
                success=False,
                error_type="SyntaxError",
                error_message="invalid syntax",
                execution_time=0.1
            ),
            ExecutionResult(
                success=False,
                error_type="UnknownError",
                error_message="unknown",
                execution_time=0.2
            ),
        ]
        grouped = self.classifier.group_errors(results)
        assert len(grouped) == 5
        assert len(grouped[ErrorCategory.TIMEOUT]) == 1
        assert len(grouped[ErrorCategory.DATA_MISSING]) == 1
        assert len(grouped[ErrorCategory.CALCULATION]) == 1
        assert len(grouped[ErrorCategory.SYNTAX]) == 1
        assert len(grouped[ErrorCategory.OTHER]) == 1


class TestErrorSummary:
    """Test error summary statistics."""

    def setup_method(self) -> None:
        """Initialize classifier."""
        self.classifier = ErrorClassifier()

    def test_error_summary_empty(self) -> None:
        """Test summary for empty result list."""
        summary = self.classifier.get_error_summary([])
        assert all(count == 0 for count in summary.values())

    def test_error_summary_mixed(self) -> None:
        """Test summary with mixed errors."""
        results = [
            ExecutionResult(success=True),
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="KeyError",
                error_message="not found",
                execution_time=0.5
            ),
            ExecutionResult(
                success=False,
                error_type="ZeroDivisionError",
                error_message="division by zero",
                execution_time=0.3
            ),
        ]
        summary = self.classifier.get_error_summary(results)
        assert summary["data_missing"] == 2
        assert summary["calculation"] == 1
        assert summary["timeout"] == 0
        assert summary["syntax"] == 0
        assert summary["other"] == 0

    def test_error_summary_format(self) -> None:
        """Test summary returns correct format."""
        results = [
            ExecutionResult(
                success=False,
                error_type="TimeoutError",
                error_message="timeout",
                execution_time=420.0
            ),
        ]
        summary = self.classifier.get_error_summary(results)
        assert isinstance(summary, dict)
        assert "timeout" in summary
        assert "data_missing" in summary
        assert "calculation" in summary
        assert "syntax" in summary
        assert "other" in summary


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self) -> None:
        """Initialize classifier."""
        self.classifier = ErrorClassifier()

    def test_none_values(self) -> None:
        """Test handling of None values."""
        category = self.classifier.classify_error("", "")
        assert category == ErrorCategory.OTHER

    def test_whitespace_only(self) -> None:
        """Test handling of whitespace-only strings."""
        category = self.classifier.classify_error("   ", "   ")
        assert category == ErrorCategory.OTHER

    def test_multiline_error_message(self) -> None:
        """Test handling of multiline error messages."""
        message = "KeyError:\n  key 'price' not found\n  in DataFrame"
        category = self.classifier.classify_error("KeyError", message)
        assert category == ErrorCategory.DATA_MISSING

    def test_very_long_error_message(self) -> None:
        """Test handling of very long error messages."""
        long_message = "x" * 10000 + "division by zero"
        category = self.classifier.classify_error("ZeroDivisionError", long_message)
        assert category == ErrorCategory.CALCULATION

    def test_special_characters_in_message(self) -> None:
        """Test handling of special characters."""
        message = "key '$#@!' not found"
        category = self.classifier.classify_error("KeyError", message)
        assert category == ErrorCategory.DATA_MISSING

    def test_unicode_characters(self) -> None:
        """Test handling of unicode characters."""
        message = "找不到欄位 'price' 在資料集中"
        category = self.classifier.classify_error("KeyError", message)
        assert category == ErrorCategory.DATA_MISSING


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
