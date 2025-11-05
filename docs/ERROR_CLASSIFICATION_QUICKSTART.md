# Error Classification - Quick Start Guide

## Installation

Already integrated into the backtest module. Just import:

```python
from src.backtest import ErrorClassifier, ErrorCategory
```

## 5 Minute Overview

### ErrorCategory Enum
```python
class ErrorCategory:
    TIMEOUT      # Execution time exceeded
    DATA_MISSING # Missing/inaccessible data
    CALCULATION  # Mathematical errors
    SYNTAX       # Code/syntax errors
    OTHER        # Unknown errors
```

### Basic Usage

```python
from src.backtest import ErrorClassifier

classifier = ErrorClassifier()

# Single error classification
category = classifier.classify_error(
    error_type="KeyError",
    error_message="'price' not found"
)
print(category)  # ErrorCategory.DATA_MISSING
```

## Common Error Patterns

### Data Missing Errors
```python
# KeyError
classifier.classify_error("KeyError", "key not found")
# ErrorCategory.DATA_MISSING

# AttributeError
classifier.classify_error("AttributeError", "has no attribute")
# ErrorCategory.DATA_MISSING

# Column not found
classifier.classify_error("KeyError", "column 'price' not found")
# ErrorCategory.DATA_MISSING
```

### Calculation Errors
```python
# Division by zero
classifier.classify_error("ZeroDivisionError", "division by zero")
# ErrorCategory.CALCULATION

# Overflow
classifier.classify_error("OverflowError", "value too large")
# ErrorCategory.CALCULATION

# Type error in arithmetic
classifier.classify_error("TypeError", "cannot multiply sequence by non-int")
# ErrorCategory.CALCULATION
```

### Syntax Errors
```python
# Syntax error
classifier.classify_error("SyntaxError", "invalid syntax at line 5")
# ErrorCategory.SYNTAX

# Name not defined
classifier.classify_error("NameError", "name 'x' is not defined")
# ErrorCategory.SYNTAX

# Import error
classifier.classify_error("ImportError", "cannot import module")
# ErrorCategory.SYNTAX
```

### Timeout Errors
```python
# Timeout
classifier.classify_error("TimeoutError", "execution timeout exceeded")
# ErrorCategory.TIMEOUT
```

## Batch Operations

### Group Multiple Errors
```python
# Group results by error category
grouped = classifier.group_errors(execution_results)

for category, results in grouped.items():
    print(f"{category.value}: {len(results)} errors")
    for result in results:
        print(f"  - {result.error_message}")
```

### Error Summary
```python
# Get error counts by category
summary = classifier.get_error_summary(execution_results)
print(summary)
# Output: {'timeout': 0, 'data_missing': 3, 'calculation': 1, 'syntax': 0, 'other': 0}
```

## Chinese Support

All patterns work with Chinese error messages:

```python
# Chinese: key not found
classifier.classify_error("KeyError", "找不到鍵 'price'")
# ErrorCategory.DATA_MISSING

# Chinese: no attribute
classifier.classify_error("AttributeError", "沒有屬性 'close'")
# ErrorCategory.DATA_MISSING

# Chinese: divide by zero
classifier.classify_error("ZeroDivisionError", "除以零")
# ErrorCategory.CALCULATION

# Chinese: syntax error
classifier.classify_error("SyntaxError", "語法錯誤")
# ErrorCategory.SYNTAX
```

## Integration Example

```python
from src.backtest import BacktestExecutor, ErrorClassifier

# Execute strategy
executor = BacktestExecutor(timeout=420)
result = executor.execute(strategy_code, data, sim)

# Classify error if failed
if not result.success:
    classifier = ErrorClassifier()
    category = classifier.classify_error(
        error_type=result.error_type,
        error_message=result.error_message
    )
    print(f"Error type: {category.value}")
```

## API Reference

### ErrorClassifier Methods

**classify_error(error_type, error_message="")**
- Returns: ErrorCategory
- Classifies single error

**group_errors(execution_results)**
- Returns: Dict[ErrorCategory, List[ExecutionResult]]
- Groups multiple results by category

**get_error_summary(execution_results)**
- Returns: Dict[str, int]
- Returns error counts by category

## Performance Notes

- Pattern compilation: One-time cost at initialization
- Classification: O(1) average case, O(n patterns) worst case
- Grouping: O(n results) linear time
- Thread-safe: Classifier is stateless

## Testing

Run all tests:
```bash
pytest tests/backtest/test_error_classifier.py -v
```

Expected output:
```
47 passed in 1.81s
```

## When to Use Each Category

| Category | When | Example |
|----------|------|---------|
| TIMEOUT | Code runs too long | Backtest exceeds 420 seconds |
| DATA_MISSING | Can't find/access data | KeyError on missing column |
| CALCULATION | Math/computation error | Division by zero |
| SYNTAX | Code structure error | Invalid Python syntax |
| OTHER | Anything else | Unknown custom error |

## Common Mistakes

### Mistake 1: Case Sensitivity
```python
# Don't worry about case - matching is case-insensitive
classifier.classify_error("KeyError", "KEY NOT FOUND")
# Still returns ErrorCategory.DATA_MISSING
```

### Mistake 2: Empty Messages
```python
# Empty messages default to error type classification
classifier.classify_error("KeyError", "")
# Still returns ErrorCategory.DATA_MISSING if type matches
```

### Mistake 3: Filtering Out Errors
```python
# group_errors() automatically filters successful results
# No need to pre-filter
grouped = classifier.group_errors(all_results)  # Works fine
```

## Pro Tips

1. **Use for error analysis**: Group errors and find patterns
2. **Use for retry logic**: Timeout errors may warrant retry
3. **Use for alerting**: Different categories can trigger different alerts
4. **Use for reporting**: Summary provides quick error distribution

## Documentation

- Full API documentation: `/mnt/c/Users/jnpi/documents/finlab/docs/ERROR_CLASSIFICATION.md`
- Test examples: `/mnt/c/Users/jnpi/documents/finlab/tests/backtest/test_error_classifier.py`
- Source code: `/mnt/c/Users/jnpi/documents/finlab/src/backtest/error_classifier.py`
