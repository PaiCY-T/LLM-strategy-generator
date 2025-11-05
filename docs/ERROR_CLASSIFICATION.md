# Error Classification System

## Overview

The Error Classification System provides automated categorization of execution errors from backtest runs. It uses pattern matching on error types and messages to classify errors into standardized categories, enabling better debugging, analysis, and error handling.

## Key Features

- **Automated Classification**: Categorizes errors into 5 standard categories
- **Bilingual Support**: Handles both English and Chinese error messages
- **Pattern-Based Matching**: Robust regex patterns for error detection
- **Batch Processing**: Group and analyze multiple errors at once
- **Error Summary**: Quick statistics on error distribution

## Error Categories

### TIMEOUT
Execution time limit exceeded.

**Triggers:**
- Error type: `TimeoutError`
- Message patterns: timeout, time limit, timed out, exceeded timeout

**Example:**
```python
classifier.classify_error(
    "TimeoutError",
    "Backtest execution exceeded timeout of 420 seconds"
)
# Returns: ErrorCategory.TIMEOUT
```

### DATA_MISSING
Missing or inaccessible data (KeyError, AttributeError, IndexError, missing columns/fields).

**Triggers:**
- Error types: `KeyError`, `AttributeError`, `IndexError`, `ValueError`
- Message patterns:
  - English: "key not found", "column not found", "has no attribute", "index out of range"
  - Chinese: "找不到鍵", "找不到欄位", "沒有屬性", "索引超出範圍"

**Example:**
```python
classifier.classify_error(
    "KeyError",
    "'price' not found"
)
# Returns: ErrorCategory.DATA_MISSING

classifier.classify_error(
    "AttributeError",
    "找不到欄位 'close_price'"
)
# Returns: ErrorCategory.DATA_MISSING
```

### CALCULATION
Mathematical or computation errors.

**Triggers:**
- Error types: `ZeroDivisionError`, `OverflowError`, `FloatingPointError`, `TypeError`
- Message patterns:
  - English: "division by zero", "overflow", "cannot multiply", "unsupported operand"
  - Chinese: "除以零", "數值溢出", "無法相乘", "不支援該操作"

**Example:**
```python
classifier.classify_error(
    "ZeroDivisionError",
    "division by zero"
)
# Returns: ErrorCategory.CALCULATION

classifier.classify_error(
    "TypeError",
    "cannot multiply sequence by non-int"
)
# Returns: ErrorCategory.CALCULATION
```

### SYNTAX
Code syntax or structure errors.

**Triggers:**
- Error types: `SyntaxError`, `IndentationError`, `NameError`, `ImportError`, `ModuleNotFoundError`
- Message patterns:
  - English: "syntax error", "not defined", "cannot import", "invalid syntax"
  - Chinese: "語法錯誤", "未定義", "無法導入", "找不到模組"

**Example:**
```python
classifier.classify_error(
    "SyntaxError",
    "invalid syntax at line 5"
)
# Returns: ErrorCategory.SYNTAX

classifier.classify_error(
    "NameError",
    "name 'undefined_var' is not defined"
)
# Returns: ErrorCategory.SYNTAX
```

### OTHER
Uncategorized or unknown errors.

**Default category** for errors that don't match any other pattern.

**Example:**
```python
classifier.classify_error(
    "CustomException",
    "something unexpected happened"
)
# Returns: ErrorCategory.OTHER
```

## Usage

### Basic Classification

```python
from src.backtest import ErrorClassifier, ErrorCategory

classifier = ErrorClassifier()

# Classify a single error
category = classifier.classify_error(
    error_type="KeyError",
    error_message="'price' column not found"
)

if category == ErrorCategory.DATA_MISSING:
    print("This is a data access error")
```

### Batch Grouping

```python
from src.backtest import ExecutionResult

# Group multiple execution results by error category
grouped = classifier.group_errors(execution_results)

for category, results in grouped.items():
    print(f"{category.value}: {len(results)} errors")
    for result in results:
        print(f"  - {result.error_message}")
```

**Output:**
```
data_missing: 3 errors
  - KeyError: 'price' not found
  - AttributeError: has no attribute 'close'
  - IndexError: list index out of range

calculation: 2 errors
  - ZeroDivisionError: division by zero
  - OverflowError: value too large

syntax: 1 errors
  - SyntaxError: invalid syntax at line 10
```

### Error Summary

```python
# Get quick statistics on error distribution
summary = classifier.get_error_summary(execution_results)
print(summary)
```

**Output:**
```python
{
    'timeout': 0,
    'data_missing': 3,
    'calculation': 2,
    'syntax': 1,
    'other': 0
}
```

## API Reference

### ErrorCategory

Enum with 5 categories:
- `TIMEOUT` = "timeout"
- `DATA_MISSING` = "data_missing"
- `CALCULATION` = "calculation"
- `SYNTAX` = "syntax"
- `OTHER` = "other"

### ErrorClassifier

Main class for error classification.

#### Methods

**`classify_error(error_type: str, error_message: str = "") -> ErrorCategory`**

Classify a single error into a category.

Args:
- `error_type`: Type of error (e.g., 'KeyError', 'TimeoutError')
- `error_message`: Error message text (English or Chinese, optional)

Returns:
- `ErrorCategory` matching the error

**`group_errors(execution_results: List[ExecutionResult]) -> Dict[ErrorCategory, List[ExecutionResult]]`**

Group execution results by error category.

Args:
- `execution_results`: List of ExecutionResult objects to categorize

Returns:
- Dictionary mapping ErrorCategory to list of ExecutionResult objects
- Only includes categories with at least one error

**`get_error_summary(execution_results: List[ExecutionResult]) -> Dict[str, int]`**

Get summary of error counts by category.

Args:
- `execution_results`: List of ExecutionResult objects

Returns:
- Dictionary mapping category names to error counts
- Includes all categories even if count is 0

## Pattern Matching Details

The classifier uses compiled regex patterns with the following flags:
- Case-insensitive matching (`re.IGNORECASE`)
- Multiline mode (`re.DOTALL`)

This allows robust matching of error messages regardless of case or formatting.

### Pattern Priority

Patterns are checked in this order:
1. TIMEOUT patterns (highest priority)
2. DATA_MISSING patterns
3. CALCULATION patterns
4. SYNTAX patterns
5. OTHER (default fallback)

The first matching pattern determines the category.

### Chinese Character Support

All error categories support Chinese error messages:

```python
# Chinese examples
classifier.classify_error("KeyError", "找不到鍵 'price'")         # DATA_MISSING
classifier.classify_error("ZeroDivisionError", "除以零")           # CALCULATION
classifier.classify_error("SyntaxError", "語法錯誤")               # SYNTAX
classifier.classify_error("AttributeError", "沒有屬性 'close'")   # DATA_MISSING
```

## Integration with ExecutionResult

The ErrorClassifier works seamlessly with the `ExecutionResult` dataclass from the backtest executor:

```python
from src.backtest import BacktestExecutor, ExecutionResult

executor = BacktestExecutor(timeout=420)
result = executor.execute(strategy_code, data, sim)

# Classify the error if execution failed
if not result.success:
    category = classifier.classify_error(
        error_type=result.error_type,
        error_message=result.error_message
    )
    print(f"Error category: {category}")
```

## Examples

### Example 1: Simple Classification

```python
from src.backtest import ErrorClassifier, ErrorCategory

classifier = ErrorClassifier()

# Test timeout
category = classifier.classify_error("TimeoutError", "timeout exceeded")
assert category == ErrorCategory.TIMEOUT

# Test data error
category = classifier.classify_error("KeyError", "key not found")
assert category == ErrorCategory.DATA_MISSING

# Test calculation error
category = classifier.classify_error("ZeroDivisionError", "division by zero")
assert category == ErrorCategory.CALCULATION
```

### Example 2: Batch Analysis

```python
from src.backtest import BacktestExecutor, ErrorClassifier

# Run multiple backtests
results = []
for strategy_code in strategies:
    result = executor.execute(strategy_code, data, sim)
    results.append(result)

# Analyze errors
classifier = ErrorClassifier()
grouped = classifier.group_errors(results)

# Report by category
for category in sorted(grouped.keys(), key=lambda c: c.value):
    errors = grouped[category]
    print(f"\n{category.value.upper()}: {len(errors)} errors")
    for result in errors[:3]:  # Show first 3
        print(f"  - {result.error_message}")
```

### Example 3: Error Distribution

```python
# Get summary statistics
summary = classifier.get_error_summary(execution_results)
total_errors = sum(summary.values())

print(f"Total errors: {total_errors}")
for category, count in sorted(summary.items()):
    percentage = 100 * count / total_errors if total_errors > 0 else 0
    print(f"  {category}: {count} ({percentage:.1f}%)")
```

## Testing

Comprehensive test suite with 47 test cases covering:
- Individual error type classification
- Message pattern matching (English and Chinese)
- Batch error grouping
- Error summary statistics
- Edge cases (empty messages, special characters, unicode)
- Case-insensitive matching

Run tests with:
```bash
pytest tests/backtest/test_error_classifier.py -v
```

## Implementation Notes

- **No External Dependencies**: Uses only Python stdlib (re module for regex)
- **Thread-Safe**: ErrorClassifier is stateless and thread-safe
- **Extensible**: New patterns can be added via pattern definitions
- **Performance**: Pattern compilation happens once during initialization
- **Chinese Support**: Native support for Chinese error messages via Unicode

## Future Enhancements

Potential improvements:
- Custom pattern registration for domain-specific errors
- Error severity levels beyond categories
- Automatic remediation suggestions
- Integration with monitoring/alerting systems
- Error message deduplication and clustering
