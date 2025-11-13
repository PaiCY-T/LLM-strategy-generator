# phase3-data-integrity-type-safety - Tasks Document

## Overview

This document provides a TDD-oriented task breakdown for Phase 3 Data Integrity & Type Safety implementation. Each task follows the RED-GREEN-REFACTOR cycle with specific test scenarios, acceptance criteria, and parallel processing opportunities.

**Development Approach**: Test-Driven Development (TDD)
- **RED Phase**: Write failing tests first
- **GREEN Phase**: Implement minimal code to pass tests
- **REFACTOR Phase**: Improve code quality while keeping tests green

**Parallel Processing Strategy**: Tasks marked with `[PARALLEL]` can be developed simultaneously by different developers or in separate branches.

---

## Phase 3.1: Type Consistency (P0 - COMPLETED ✅)

**Status**: All tasks completed in prior iteration
**Evidence**:
- TC-1.1 to TC-1.5: ✅ Verified in code
- `StrategyMetrics.to_dict()` and `from_dict()` implemented
- All consuming components updated
- Backward compatibility maintained

---

## Phase 3.2: Schema Validation (P1 - COMPLETED ✅)

**Status**: All tasks completed using TDD methodology with parallel execution
**Completion Date**: 2025-11-13
**Development Strategy**: Wave-based parallel + sequential execution

**Wave 1 - Parallel Tasks** (5 tasks executed simultaneously):
- ✅ Task 3.2.1: sharpe_ratio field validator (8 tests passing)
- ✅ Task 3.2.2: max_drawdown field validator (7 tests passing)
- ✅ Task 3.2.3: total_return field validator (8 tests passing)
- ✅ Task 3.2.4: Validation error logging (6 tests passing)
- ✅ Task 3.2.7: Comprehensive unit tests (16 tests passing)

**Wave 2 - Sequential Tasks** (3 tasks executed in order):
- ✅ Task 3.2.5: BacktestExecutor integration (7 tests passing)
- ✅ Task 3.2.6: Performance benchmarking (7 tests passing, exceeded requirements by 714-10,000×)
- ✅ Task 3.2.8: E2E integration tests (8 tests passing)

**Evidence**:
- **Total Tests**: 67 passing (45 unit + 13 integration + 8 E2E + 1 skipped)
- **Coverage**: 100% of all validation functions
- **Performance**: Average 0.0014ms (<1ms requirement), p95: 0.002ms, p99: 0.003ms
- **Type Safety**: mypy passes with 0 errors
- **Integration**: BacktestExecutor fully integrated at lines 203-222
- **Documentation**: 4 completion reports in spec directory

**Acceptance Criteria Status**:
- SV-2.1 to SV-2.10: ✅ All satisfied
- Performance: ✅ Exceeded by 714-10,000× margins
- Test Coverage: ✅ 67 tests passing (requirement: 15+)

**Completion Reports**:
- `TASK_3.2.5_COMPLETION_REPORT.md`: BacktestExecutor integration
- `TASK_3.2.6_COMPLETION.md`: Performance benchmarking results
- `TASK_3.2.7_COMPLETION_REPORT.md`: Unit test suite results
- `phase3_validation_performance.md`: Detailed performance analysis

---

### Task 3.2.1: Sharpe Ratio Field Validator `[PARALLEL]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 4 hours | **Owner**: TBD

#### Acceptance Criteria
- [ ] **SV-2.1**: `ExecutionResultSchema` validates sharpe_ratio range [-10, 10]

#### TDD Test Plan

**RED Phase - Write Failing Tests** (1 hour):

```python
# tests/backtest/test_execution_result_validation.py

class TestSharpeRatioValidation:
    """SV-2.1: Sharpe ratio range validation [-10, 10]"""

    def test_sharpe_ratio_none_is_valid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=None
        WHEN validating sharpe_ratio
        THEN validation passes (None is valid for optional field)
        """
        result = ExecutionResult(success=True, sharpe_ratio=None)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_at_lower_boundary(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=-10.0
        WHEN validating sharpe_ratio
        THEN validation passes (boundary value is valid)
        """
        result = ExecutionResult(success=True, sharpe_ratio=-10.0)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_at_upper_boundary(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=10.0
        WHEN validating sharpe_ratio
        THEN validation passes (boundary value is valid)
        """
        result = ExecutionResult(success=True, sharpe_ratio=10.0)
        error = validate_sharpe_ratio(result.sharpe_ratio)
        assert error is None

    def test_sharpe_ratio_within_valid_range(self):
        """
        GIVEN ExecutionResult with sharpe_ratio in [-10, 10]
        WHEN validating sharpe_ratio
        THEN validation passes
        """
        for value in [-5.0, 0.0, 1.5, 5.0]:
            result = ExecutionResult(success=True, sharpe_ratio=value)
            error = validate_sharpe_ratio(result.sharpe_ratio)
            assert error is None, f"Valid value {value} should pass"

    def test_sharpe_ratio_below_range_fails(self):
        """
        GIVEN ExecutionResult with sharpe_ratio < -10
        WHEN validating sharpe_ratio
        THEN validation fails with descriptive error
        """
        result = ExecutionResult(success=True, sharpe_ratio=-10.001)
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "sharpe_ratio" in error.lower()
        assert "-10.001" in error
        assert "[-10" in error or "range" in error.lower()

    def test_sharpe_ratio_above_range_fails(self):
        """
        GIVEN ExecutionResult with sharpe_ratio > 10
        WHEN validating sharpe_ratio
        THEN validation fails with descriptive error
        """
        result = ExecutionResult(success=True, sharpe_ratio=10.001)
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "10.001" in error
        assert "10]" in error or "range" in error.lower()

    def test_sharpe_ratio_nan_is_invalid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=NaN
        WHEN validating sharpe_ratio
        THEN validation fails
        """
        result = ExecutionResult(success=True, sharpe_ratio=float('nan'))
        error = validate_sharpe_ratio(result.sharpe_ratio)

        assert error is not None
        assert "nan" in error.lower() or "invalid" in error.lower()

    def test_sharpe_ratio_infinity_is_invalid(self):
        """
        GIVEN ExecutionResult with sharpe_ratio=Inf or -Inf
        WHEN validating sharpe_ratio
        THEN validation fails
        """
        for value in [float('inf'), float('-inf')]:
            result = ExecutionResult(success=True, sharpe_ratio=value)
            error = validate_sharpe_ratio(result.sharpe_ratio)

            assert error is not None
            assert "inf" in error.lower() or "infinite" in error.lower()
```

**Test Input Examples**:
- Valid: None, -10.0, -5.0, 0.0, 1.5, 10.0
- Invalid: -10.001, 10.001, NaN, Inf, -Inf

**GREEN Phase - Implement Validator** (2 hours):

```python
# src/backtest/validation.py

import math
from typing import Optional

def validate_sharpe_ratio(value: Optional[float]) -> Optional[str]:
    """
    Validate sharpe_ratio field is within acceptable range [-10, 10].

    Args:
        value: Sharpe ratio value to validate (None is valid)

    Returns:
        Error message if invalid, None if valid
    """
    # None is valid (optional field)
    if value is None:
        return None

    # Check for NaN
    if math.isnan(value):
        return f"sharpe_ratio must be a valid number, got NaN"

    # Check for infinity
    if math.isinf(value):
        return f"sharpe_ratio must be finite, got {value}"

    # Check range
    if value < -10.0 or value > 10.0:
        return (
            f"sharpe_ratio {value} is out of valid range [-10, 10]. "
            f"Expected: -10 <= sharpe_ratio <= 10. "
            f"Suggestion: Check data quality and backtest configuration."
        )

    return None
```

**REFACTOR Phase** (1 hour):
- Extract common validation logic (NaN, Inf checks)
- Add type hints and docstrings
- Optimize for performance (<1ms)

#### Dependencies
- None (can start immediately)

#### Verification Steps
1. Run tests: `pytest tests/backtest/test_execution_result_validation.py::TestSharpeRatioValidation -v`
2. Verify all 8 tests pass
3. Run mypy: `mypy src/backtest/validation.py`
4. Benchmark: `pytest tests/backtest/test_execution_result_validation.py::TestSharpeRatioValidation --benchmark`

---

### Task 3.2.2: Max Drawdown Field Validator `[PARALLEL]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 4 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.2**: `ExecutionResultSchema` validates max_drawdown <= 0

#### TDD Test Plan

**RED Phase - Write Failing Tests** (1 hour):

```python
class TestMaxDrawdownValidation:
    """SV-2.2: Max drawdown must be <= 0 (negative or zero)"""

    def test_max_drawdown_none_is_valid(self):
        """
        GIVEN ExecutionResult with max_drawdown=None
        WHEN validating max_drawdown
        THEN validation passes
        """
        error = validate_max_drawdown(None)
        assert error is None

    def test_max_drawdown_zero_is_valid(self):
        """
        GIVEN ExecutionResult with max_drawdown=0.0 or -0.0
        WHEN validating max_drawdown
        THEN validation passes (no drawdown scenario)
        """
        assert validate_max_drawdown(0.0) is None
        assert validate_max_drawdown(-0.0) is None

    def test_max_drawdown_negative_is_valid(self):
        """
        GIVEN ExecutionResult with max_drawdown < 0
        WHEN validating max_drawdown
        THEN validation passes
        """
        for value in [-0.001, -0.15, -0.5, -0.999]:
            error = validate_max_drawdown(value)
            assert error is None, f"Valid drawdown {value} should pass"

    def test_max_drawdown_positive_fails(self):
        """
        GIVEN ExecutionResult with max_drawdown > 0
        WHEN validating max_drawdown
        THEN validation fails (positive drawdown is logically impossible)
        """
        for value in [0.001, 0.15, 0.5, 1.0]:
            error = validate_max_drawdown(value)

            assert error is not None
            assert "max_drawdown" in error.lower()
            assert str(value) in error
            assert ("<= 0" in error or "negative" in error.lower() or
                    "non-positive" in error.lower())

    def test_max_drawdown_nan_is_invalid(self):
        """
        GIVEN ExecutionResult with max_drawdown=NaN
        WHEN validating max_drawdown
        THEN validation fails
        """
        error = validate_max_drawdown(float('nan'))
        assert error is not None
        assert "nan" in error.lower() or "invalid" in error.lower()

    def test_max_drawdown_infinity_is_invalid(self):
        """
        GIVEN ExecutionResult with max_drawdown=Inf or -Inf
        WHEN validating max_drawdown
        THEN validation fails
        """
        for value in [float('inf'), float('-inf')]:
            error = validate_max_drawdown(value)
            assert error is not None
            assert "inf" in error.lower() or "infinite" in error.lower()
```

**Test Input Examples**:
- Valid: None, 0.0, -0.0, -0.001, -0.15, -0.999
- Invalid: 0.001, 0.15, 1.0, NaN, Inf, -Inf

**GREEN Phase - Implement Validator** (2 hours):

```python
def validate_max_drawdown(value: Optional[float]) -> Optional[str]:
    """
    Validate max_drawdown is non-positive (<= 0).

    Drawdown represents loss from peak, must be negative or zero.
    Positive values indicate data corruption or calculation errors.

    Args:
        value: Maximum drawdown value to validate

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return f"max_drawdown must be a valid number, got NaN"

    if math.isinf(value):
        return f"max_drawdown must be finite, got {value}"

    if value > 0:
        return (
            f"max_drawdown {value} must be <= 0 (drawdown represents loss). "
            f"Positive drawdown indicates data corruption. "
            f"Suggestion: Check equity curve calculation and verify no look-ahead bias."
        )

    return None
```

**REFACTOR Phase** (1 hour):
- Consolidate NaN/Inf checking with sharpe_ratio validator
- Add comprehensive docstrings
- Performance optimization

#### Dependencies
- None (can start immediately)

#### Verification Steps
1. Run tests: `pytest tests/backtest/test_execution_result_validation.py::TestMaxDrawdownValidation -v`
2. Verify all 6 tests pass
3. Check type safety with mypy

---

### Task 3.2.3: Total Return Field Validator `[PARALLEL]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 4 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.3**: `ExecutionResultSchema` validates total_return range [-1, 10]

#### TDD Test Plan

**RED Phase - Write Failing Tests** (1 hour):

```python
class TestTotalReturnValidation:
    """SV-2.3: Total return range validation [-1, 10]"""

    def test_total_return_none_is_valid(self):
        """
        GIVEN ExecutionResult with total_return=None
        WHEN validating total_return
        THEN validation passes
        """
        error = validate_total_return(None)
        assert error is None

    def test_total_return_at_boundaries(self):
        """
        GIVEN ExecutionResult with total_return at boundaries
        WHEN validating total_return
        THEN validation passes
        """
        assert validate_total_return(-1.0) is None  # Total loss
        assert validate_total_return(10.0) is None  # 1000% gain

    def test_total_return_within_range(self):
        """
        GIVEN ExecutionResult with total_return in [-1, 10]
        WHEN validating total_return
        THEN validation passes
        """
        for value in [-0.5, 0.0, 0.25, 0.5, 1.0, 5.0]:
            error = validate_total_return(value)
            assert error is None, f"Valid return {value} should pass"

    def test_total_return_below_range_fails(self):
        """
        GIVEN ExecutionResult with total_return < -1
        WHEN validating total_return
        THEN validation fails (< -100% return impossible)
        """
        error = validate_total_return(-1.001)

        assert error is not None
        assert "total_return" in error.lower()
        assert "-1.001" in error
        assert ("[-1" in error or ">= -1" in error or
                "-100%" in error.lower())

    def test_total_return_above_range_fails(self):
        """
        GIVEN ExecutionResult with total_return > 10
        WHEN validating total_return
        THEN validation fails
        """
        error = validate_total_return(10.001)

        assert error is not None
        assert "10.001" in error
        assert ("<= 10" in error or "10]" in error or
                "1000%" in error.lower())

    def test_total_return_nan_is_invalid(self):
        """
        GIVEN ExecutionResult with total_return=NaN
        WHEN validating total_return
        THEN validation fails
        """
        error = validate_total_return(float('nan'))
        assert error is not None

    def test_total_return_infinity_is_invalid(self):
        """
        GIVEN ExecutionResult with total_return=Inf
        WHEN validating total_return
        THEN validation fails
        """
        for value in [float('inf'), float('-inf')]:
            error = validate_total_return(value)
            assert error is not None
```

**Test Input Examples**:
- Valid: None, -1.0, -0.5, 0.0, 0.25, 1.0, 10.0
- Invalid: -1.001, 10.001, NaN, Inf, -Inf

**GREEN Phase - Implement Validator** (2 hours):

```python
def validate_total_return(value: Optional[float]) -> Optional[str]:
    """
    Validate total_return is within reasonable range [-1, 10].

    Range explanation:
    - Minimum -1.0: Total loss (-100%)
    - Maximum 10.0: Exceptional gain (+1000%)

    Args:
        value: Total return value to validate

    Returns:
        Error message if invalid, None if valid
    """
    if value is None:
        return None

    if math.isnan(value):
        return f"total_return must be a valid number, got NaN"

    if math.isinf(value):
        return f"total_return must be finite, got {value}"

    if value < -1.0 or value > 10.0:
        return (
            f"total_return {value} is out of valid range [-1, 10]. "
            f"Range represents [-100%, +1000%]. "
            f"Values outside this range indicate calculation errors. "
            f"Suggestion: Verify backtest period and position sizing."
        )

    return None
```

**REFACTOR Phase** (1 hour):
- Create shared `_check_numeric_valid()` helper
- Add percentage display in error messages
- Optimize validation pipeline

#### Dependencies
- None (can start immediately)

#### Verification Steps
1. Run tests: `pytest tests/backtest/test_execution_result_validation.py::TestTotalReturnValidation -v`
2. Verify all 7 tests pass

---

### Task 3.2.4: Validation Logging Setup `[PARALLEL]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 3 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.5**: Validation errors logged with field, value, constraint

#### TDD Test Plan

**RED Phase - Write Failing Tests** (1 hour):

```python
class TestValidationLogging:
    """SV-2.5: Validation error logging with structured information"""

    def test_validation_error_logged_with_details(self, caplog):
        """
        GIVEN validation failure for sharpe_ratio
        WHEN validation occurs
        THEN error is logged with field name, value, and constraint
        """
        import logging
        caplog.set_level(logging.WARNING)

        error = validate_sharpe_ratio(100.0)
        log_validation_error("sharpe_ratio", 100.0, error)

        assert "Metric validation failed" in caplog.text
        assert "sharpe_ratio" in caplog.text
        assert "100" in caplog.text
        assert "[-10, 10]" in caplog.text or "range" in caplog.text

    def test_multiple_validation_errors_all_logged(self, caplog):
        """
        GIVEN multiple validation failures
        WHEN validating ExecutionResult
        THEN all errors are logged
        """
        caplog.set_level(logging.WARNING)

        result = ExecutionResult(
            success=True,
            sharpe_ratio=100.0,
            max_drawdown=0.5,
            total_return=20.0
        )

        errors = validate_execution_result(result)
        for field, error in errors.items():
            log_validation_error(field, getattr(result, field), error)

        # All three errors should be logged
        assert caplog.text.count("Metric validation failed") >= 3
        assert "sharpe_ratio" in caplog.text
        assert "max_drawdown" in caplog.text
        assert "total_return" in caplog.text

    def test_validation_success_not_logged(self, caplog):
        """
        GIVEN valid metrics
        WHEN validation occurs
        THEN no error logs are created
        """
        caplog.set_level(logging.WARNING)

        result = ExecutionResult(
            success=True,
            sharpe_ratio=1.5,
            max_drawdown=-0.15,
            total_return=0.25
        )

        errors = validate_execution_result(result)
        assert len(errors) == 0
        assert "validation failed" not in caplog.text.lower()
```

**GREEN Phase - Implement Logging** (1.5 hours):

```python
import logging

logger = logging.getLogger(__name__)

def log_validation_error(
    field_name: str,
    actual_value: Any,
    error_message: str
) -> None:
    """
    Log validation error with structured information.

    Args:
        field_name: Name of field that failed validation
        actual_value: Actual value that was invalid
        error_message: Validation error message
    """
    logger.warning(
        f"Metric validation failed: field={field_name}, "
        f"value={actual_value}, error={error_message}"
    )
```

**REFACTOR Phase** (0.5 hours):
- Add structured logging with JSON format
- Include context (iteration number, strategy code hash)

#### Dependencies
- None (can start immediately)

#### Verification Steps
1. Run tests with logging: `pytest tests/backtest/test_execution_result_validation.py::TestValidationLogging -v -s`
2. Verify log output format

---

### Task 3.2.5: BacktestExecutor Integration `[DEPENDS ON: 3.2.1, 3.2.2, 3.2.3]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 6 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.4**: `BacktestExecutor.execute()` validates before creating ExecutionResult
- [ ] **SV-2.6**: Invalid data returns ExecutionResult(success=False, error_message=...)

#### TDD Test Plan

**RED Phase - Write Failing Tests** (2 hours):

```python
class TestBacktestExecutorValidation:
    """SV-2.4 & SV-2.6: Integration with BacktestExecutor"""

    @pytest.fixture
    def executor(self):
        return BacktestExecutor(timeout=420)

    @pytest.fixture
    def mock_data(self):
        """Mock finlab data object"""
        # Create mock data for testing
        return Mock()

    @pytest.fixture
    def mock_sim(self):
        """Mock finlab sim function"""
        return Mock()

    def test_execute_with_valid_metrics_succeeds(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy that returns valid metrics
        WHEN execute() is called
        THEN execution succeeds without validation errors
        """
        strategy_code = """
# Valid strategy with normal metrics
position = data.get("price:收盤價") > data.get("price:收盤價").rolling(20).mean()
report = sim(position.loc[start_date:end_date])
"""

        # Mock report with valid metrics
        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': 1.5,
            'total_return': 0.25,
            'max_drawdown': -0.15
        }
        mock_sim.return_value = mock_report

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is True
        assert result.error_type is None
        assert result.sharpe_ratio == 1.5
        assert result.max_drawdown == -0.15

    def test_execute_with_invalid_sharpe_fails(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy that returns sharpe_ratio > 10
        WHEN execute() is called
        THEN execution fails with ValidationError
        """
        strategy_code = "# Strategy with anomalous sharpe"

        # Mock report with invalid sharpe
        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': 100.0,  # Anomalous value
            'total_return': 0.25,
            'max_drawdown': -0.15
        }
        mock_sim.return_value = mock_report

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is False
        assert result.error_type == "ValidationError"
        assert "sharpe_ratio" in result.error_message.lower()
        assert "100" in result.error_message
        assert "[-10, 10]" in result.error_message or "range" in result.error_message

    def test_execute_with_positive_drawdown_fails(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy that returns positive max_drawdown
        WHEN execute() is called
        THEN execution fails with ValidationError
        """
        strategy_code = "# Strategy with corrupt drawdown"

        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': 1.5,
            'total_return': 0.25,
            'max_drawdown': 0.15  # Positive (invalid)
        }
        mock_sim.return_value = mock_report

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is False
        assert result.error_type == "ValidationError"
        assert "max_drawdown" in result.error_message.lower()
        assert "0.15" in result.error_message

    def test_execute_with_multiple_validation_errors(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy with multiple invalid metrics
        WHEN execute() is called
        THEN all validation errors are reported
        """
        strategy_code = "# Strategy with multiple errors"

        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': 100.0,      # Invalid
            'total_return': 20.0,       # Invalid
            'max_drawdown': 0.5         # Invalid
        }
        mock_sim.return_value = mock_report

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is False
        assert result.error_type == "ValidationError"
        # Should mention all three fields
        error_lower = result.error_message.lower()
        assert "sharpe_ratio" in error_lower or "100" in result.error_message
        assert "max_drawdown" in error_lower or "0.5" in result.error_message
        assert "total_return" in error_lower or "20" in result.error_message

    def test_execute_timeout_skips_validation(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy that times out
        WHEN execute() is called
        THEN timeout error is returned, validation not performed
        """
        strategy_code = "import time; time.sleep(10)"  # Will timeout

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim,
            timeout=1  # Short timeout
        )

        assert result.success is False
        assert result.error_type == "TimeoutError"
        # Validation should not run for timeouts
        assert "validation" not in result.error_message.lower()

    def test_execute_syntax_error_skips_validation(self, executor, mock_data, mock_sim):
        """
        GIVEN strategy with syntax error
        WHEN execute() is called
        THEN syntax error is returned, validation not performed
        """
        strategy_code = "invalid python syntax {"

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is False
        assert "SyntaxError" in result.error_type or "syntax" in result.error_message.lower()
        # Validation should not run for syntax errors
        assert "validation" not in result.error_message.lower()

    def test_execute_preserves_execution_time(self, executor, mock_data, mock_sim):
        """
        GIVEN validation failure
        WHEN execute() fails validation
        THEN execution_time is still recorded
        """
        strategy_code = "# Quick strategy"

        mock_report = Mock()
        mock_report.get_stats.return_value = {
            'daily_sharpe': 100.0  # Invalid
        }
        mock_sim.return_value = mock_report

        result = executor.execute(
            strategy_code=strategy_code,
            data=mock_data,
            sim=mock_sim
        )

        assert result.success is False
        assert result.execution_time > 0  # Should still be recorded
```

**GREEN Phase - Implement Integration** (3 hours):

Modify `src/backtest/executor.py`:

```python
# After line 196 in BacktestExecutor.execute()

def execute(...) -> ExecutionResult:
    # ... existing code ...

    # Process completed - check for result
    try:
        result = result_queue.get(timeout=2)

        # [NEW CODE START]
        # Validate metrics if execution was successful
        if result.success:
            validation_errors = self._validate_metrics(result)
            if validation_errors:
                # Validation failed - return error result
                error_details = "; ".join(validation_errors)
                return ExecutionResult(
                    success=False,
                    error_type="ValidationError",
                    error_message=f"Metric validation failed: {error_details}",
                    execution_time=result.execution_time,
                    stack_trace=result.stack_trace
                )
        # [NEW CODE END]

        # Add final execution time if not already set
        if result.execution_time <= 0:
            result.execution_time = execution_time
        return result

    # ... rest of existing code ...

def _validate_metrics(self, result: ExecutionResult) -> List[str]:
    """
    Validate ExecutionResult metrics.

    Args:
        result: ExecutionResult to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    from .validation import (
        validate_sharpe_ratio,
        validate_max_drawdown,
        validate_total_return,
        log_validation_error
    )

    errors = []

    # Validate sharpe_ratio
    if result.sharpe_ratio is not None:
        error = validate_sharpe_ratio(result.sharpe_ratio)
        if error:
            log_validation_error("sharpe_ratio", result.sharpe_ratio, error)
            errors.append(error)

    # Validate max_drawdown
    if result.max_drawdown is not None:
        error = validate_max_drawdown(result.max_drawdown)
        if error:
            log_validation_error("max_drawdown", result.max_drawdown, error)
            errors.append(error)

    # Validate total_return
    if result.total_return is not None:
        error = validate_total_return(result.total_return)
        if error:
            log_validation_error("total_return", result.total_return, error)
            errors.append(error)

    return errors
```

**REFACTOR Phase** (1 hour):
- Extract validation logic to separate module
- Add configuration for enabling/disabling validation
- Optimize validation path to minimize overhead

#### Dependencies
- Requires: Tasks 3.2.1, 3.2.2, 3.2.3 (field validators)

#### Verification Steps
1. Run integration tests: `pytest tests/backtest/test_backtest_executor_validation.py -v`
2. Verify all 8 integration tests pass
3. Test with real backtest execution

---

### Task 3.2.6: Performance Benchmarking `[DEPENDS ON: 3.2.5]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 4 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.7**: Validation overhead <1ms per call (benchmarked)

#### TDD Test Plan

**RED Phase - Write Failing Tests** (1 hour):

```python
class TestValidationPerformance:
    """SV-2.7: Performance requirements < 1ms"""

    def test_single_validation_under_1ms(self, benchmark):
        """
        GIVEN ExecutionResult with all metrics
        WHEN validating metrics
        THEN validation completes in < 1ms
        """
        result = ExecutionResult(
            success=True,
            sharpe_ratio=1.5,
            max_drawdown=-0.15,
            total_return=0.25
        )

        executor = BacktestExecutor()

        # Benchmark the validation method
        def validate():
            return executor._validate_metrics(result)

        result = benchmark(validate)

        # pytest-benchmark will fail if > 1ms (configure in pytest.ini)
        assert result == []  # No errors

    def test_validation_overhead_acceptable(self, benchmark):
        """
        GIVEN 1000 validation calls
        WHEN benchmarking
        THEN average time < 1ms per call
        """
        results = [
            ExecutionResult(
                success=True,
                sharpe_ratio=i / 100.0,
                max_drawdown=-i / 100.0,
                total_return=i / 500.0
            )
            for i in range(1000)
        ]

        executor = BacktestExecutor()

        def validate_all():
            for result in results:
                executor._validate_metrics(result)

        benchmark(validate_all)
        # Average per validation should be << 1ms

    def test_validation_does_not_slow_execution(self):
        """
        GIVEN BacktestExecutor with validation enabled
        WHEN executing strategy
        THEN total overhead < 5% of execution time
        """
        executor = BacktestExecutor()

        # Time without validation (mock)
        start = time.time()
        # Simulate backtest execution
        time.sleep(0.1)  # 100ms simulated execution
        baseline = time.time() - start

        # Time with validation
        start = time.time()
        # Simulate backtest + validation
        time.sleep(0.1)
        result = ExecutionResult(success=True, sharpe_ratio=1.5)
        executor._validate_metrics(result)
        with_validation = time.time() - start

        overhead = with_validation - baseline
        overhead_pct = (overhead / baseline) * 100

        assert overhead_pct < 5, f"Validation overhead {overhead_pct:.1f}% exceeds 5%"
```

**GREEN Phase - Optimize Implementation** (2 hours):
- Profile validation code
- Optimize hot paths
- Cache validation logic if needed
- Use fast math libraries

**REFACTOR Phase** (1 hour):
- Add performance monitoring hooks
- Create performance regression tests

#### Dependencies
- Requires: Task 3.2.5 (BacktestExecutor integration)

#### Verification Steps
1. Run benchmarks: `pytest tests/backtest/test_execution_result_validation.py::TestValidationPerformance --benchmark-only`
2. Verify performance < 1ms target
3. Profile with `py-spy` or `cProfile` if needed

---

### Task 3.2.7: Unit Test Suite `[PARALLEL with all tasks]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 6 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.8**: 15+ schema validation tests pass

#### Test Coverage Goals
- **Target**: 100% line coverage for validation module
- **Minimum**: 95% line coverage
- **Edge Cases**: All boundary conditions tested

#### Test Files
```
tests/backtest/
├── test_execution_result_validation.py (15+ tests)
│   ├── TestSharpeRatioValidation (8 tests)
│   ├── TestMaxDrawdownValidation (6 tests)
│   ├── TestTotalReturnValidation (7 tests)
│   ├── TestValidationLogging (3 tests)
│   └── TestValidationEdgeCases (5 tests)
├── test_backtest_executor_validation.py (8+ tests)
│   └── TestBacktestExecutorValidation
└── test_validation_performance.py (3+ tests)
    └── TestValidationPerformance
```

#### Dependencies
- Can be developed in parallel with implementation

#### Verification Steps
1. Run all tests: `pytest tests/backtest/ -v --cov=src/backtest/validation --cov-report=html`
2. Verify coverage >= 95%
3. Review coverage report: `open htmlcov/index.html`

---

### Task 3.2.8: Integration Testing `[DEPENDS ON: 3.2.5]` ✅ COMPLETED

**Priority**: P1 | **Effort**: 5 hours | **Completed**: 2025-11-13

#### Acceptance Criteria
- [ ] **SV-2.9**: Integration test with schema validation passes
- [ ] **SV-2.10**: No false positives in validation (all valid strategies accepted)

#### TDD Test Plan

**RED Phase - Write Failing Tests** (2 hours):

```python
class TestE2EValidation:
    """SV-2.9 & SV-2.10: End-to-end validation integration"""

    def test_full_learning_loop_with_validation(self):
        """
        GIVEN learning loop with validation enabled
        WHEN running single iteration
        THEN validation is transparent, metrics are validated
        """
        # Setup iteration executor
        executor = IterationExecutor(
            innovator=mock_innovator,
            backtest_executor=BacktestExecutor(),
            feedback_generator=mock_feedback_generator,
            champion_tracker=mock_champion_tracker
        )

        # Run iteration
        result = executor.run_iteration(iteration_num=1)

        # Validation should be transparent
        assert result is not None

        if result.execution_result.success:
            # Metrics should be valid
            metrics = result.metrics
            assert metrics.sharpe_ratio is None or -10 <= metrics.sharpe_ratio <= 10
            assert metrics.max_drawdown is None or metrics.max_drawdown <= 0
            assert metrics.total_return is None or -1 <= metrics.total_return <= 10

    def test_no_false_positives_on_valid_strategies(self):
        """
        GIVEN 100 valid strategy executions
        WHEN running backtests
        THEN no validation false positives occur
        """
        executor = BacktestExecutor()

        # Generate 100 valid strategy results
        valid_strategies = [
            generate_valid_strategy(seed=i) for i in range(100)
        ]

        false_positives = 0

        for strategy in valid_strategies:
            result = executor.execute(
                strategy_code=strategy.code,
                data=strategy.data,
                sim=strategy.sim
            )

            # All valid strategies should pass validation
            if not result.success and result.error_type == "ValidationError":
                false_positives += 1
                print(f"False positive: {result.error_message}")

        assert false_positives == 0, f"Found {false_positives} false positives"

    def test_validation_catches_real_anomalies(self):
        """
        GIVEN strategies with known anomalous metrics
        WHEN running backtests
        THEN validation correctly identifies issues
        """
        executor = BacktestExecutor()

        # Test cases with known issues
        anomalous_cases = [
            ("extreme_sharpe", 100.0, None, None),
            ("positive_drawdown", 1.5, 0.15, 0.25),
            ("excessive_return", 1.5, -0.15, 20.0),
        ]

        for name, sharpe, drawdown, total_return in anomalous_cases:
            # Mock result with anomalous metrics
            result = ExecutionResult(
                success=True,
                sharpe_ratio=sharpe,
                max_drawdown=drawdown,
                total_return=total_return
            )

            errors = executor._validate_metrics(result)
            assert len(errors) > 0, f"Failed to detect anomaly in {name}"

    def test_backward_compatibility_with_existing_code(self):
        """
        GIVEN existing code that doesn't expect validation
        WHEN validation is enabled
        THEN no breaking changes occur
        """
        # Existing code pattern
        executor = BacktestExecutor()
        result = executor.execute(
            strategy_code="# Simple strategy",
            data=mock_data,
            sim=mock_sim
        )

        # Should still work as before
        assert hasattr(result, 'success')
        assert hasattr(result, 'error_message')
        assert hasattr(result, 'sharpe_ratio')
```

**GREEN Phase - Implement E2E Tests** (2 hours):
- Create test harness for full learning loop
- Generate realistic test data
- Implement validation assertions

**REFACTOR Phase** (1 hour):
- Extract test utilities
- Add property-based testing with Hypothesis
- Document test scenarios

#### Dependencies
- Requires: Task 3.2.5 (BacktestExecutor integration)

#### Verification Steps
1. Run E2E tests: `pytest tests/integration/test_phase3_validation.py -v`
2. Verify no false positives on 100+ valid strategies
3. Confirm backward compatibility

---

## Phase 3.3: LLM Code Pre-Validation (P2 - CONDITIONAL)

**Decision Gate**: Implement only if Phase 1+2 show LLM error rate >20%

**Status**: Not Started (decision pending)

### Evaluation Task: Measure LLM Error Rate

**Priority**: P2 | **Effort**: 2 hours | **Owner**: TBD

#### Acceptance Criteria
- [ ] Measure LLM syntax error rate over 50+ iterations
- [ ] Measure look-ahead bias occurrence rate
- [ ] Decide: Implement Phase 3.3 if error_rate > 20%

#### Implementation Plan

```python
def measure_llm_error_rate():
    """
    Run 50+ iterations and measure error types.

    Error categories:
    - Syntax errors (Python syntax invalid)
    - Look-ahead bias (.shift(-1) patterns)
    - API misuse (missing axis parameter)
    - Other execution errors
    """
    executor = IterationExecutor(...)

    errors = {
        'syntax': 0,
        'lookahead': 0,
        'api_misuse': 0,
        'other': 0,
        'total': 0
    }

    for i in range(50):
        result = executor.run_iteration(iteration_num=i)

        if not result.execution_result.success:
            errors['total'] += 1
            error_msg = result.execution_result.error_message.lower()

            if 'syntax' in error_msg:
                errors['syntax'] += 1
            elif 'shift(-1)' in result.strategy_code:
                errors['lookahead'] += 1
            elif 'axis' in error_msg and 'rank' in result.strategy_code:
                errors['api_misuse'] += 1
            else:
                errors['other'] += 1

    error_rate = errors['total'] / 50

    print(f"LLM Error Rate: {error_rate:.1%}")
    print(f"Breakdown: {errors}")

    return error_rate
```

**Decision**:
- If `error_rate > 0.20` (20%): Proceed with Phase 3.3 tasks
- If `error_rate <= 0.20`: Skip Phase 3.3, document decision

---

## Parallel Processing Summary

### Wave 1 - Independent Field Validators (Week 1, Days 1-2)
**Can be developed simultaneously by different developers:**

1. Task 3.2.1: Sharpe Ratio Validator `[DEV 1]`
2. Task 3.2.2: Max Drawdown Validator `[DEV 2]`
3. Task 3.2.3: Total Return Validator `[DEV 3]`
4. Task 3.2.4: Validation Logging `[DEV 4]`
5. Task 3.2.7: Unit Test Suite `[QA TEAM]` - Can be written in parallel with implementation

**Estimated Duration**: 2 days (16 hours) with 4 developers

### Wave 2 - Integration (Week 1, Days 3-4)
**Depends on Wave 1 completion:**

6. Task 3.2.5: BacktestExecutor Integration `[DEV 1 + DEV 2]`

**Estimated Duration**: 1.5 days (12 hours)

### Wave 3 - Testing & Optimization (Week 1, Day 5)
**Depends on Wave 2 completion:**

7. Task 3.2.6: Performance Benchmarking `[DEV 3]`
8. Task 3.2.8: Integration Testing `[QA TEAM]`

**Estimated Duration**: 1 day (8 hours)

### Total Estimated Timeline
- **Sequential Development**: 5 weeks (200 hours)
- **Parallel Development**: 1 week (40 hours with 4-person team)
- **Efficiency Gain**: 80% reduction in calendar time

---

## Quality Metrics

### Test Coverage Targets
- **Unit Tests**: >= 95% line coverage
- **Integration Tests**: >= 90% coverage
- **E2E Tests**: All critical paths covered

### Performance Targets
- **Validation Overhead**: < 1ms per validation
- **Total Impact**: < 5% increase in execution time
- **Memory Overhead**: < 1MB

### Code Quality Targets
- **Mypy**: 0 type errors
- **Pylint**: >= 9.0/10 score
- **Complexity**: Cyclomatic complexity <= 10 per function

---

## Risk Management

### Risk 1: Performance Degradation
**Mitigation**: Benchmark early (Task 3.2.6), optimize hot paths, add performance regression tests

### Risk 2: False Positives
**Mitigation**: Extensive testing with real strategies (Task 3.2.8), conservative validation ranges

### Risk 3: Backward Compatibility Breaks
**Mitigation**: Integration tests with existing code, gradual rollout with feature flag

### Risk 4: Team Dependencies
**Mitigation**: Clear task boundaries, parallel development strategy, daily standups

---

## Success Criteria

Phase 3.2 is considered complete when:

1. ✅ All 10 acceptance criteria (SV-2.1 to SV-2.10) pass
2. ✅ Test coverage >= 95%
3. ✅ Performance benchmarks pass (< 1ms overhead)
4. ✅ No false positives on 100+ valid strategies
5. ✅ Integration tests pass with real learning loop
6. ✅ Mypy reports 0 type errors
7. ✅ Documentation updated with validation examples
8. ✅ Code reviewed and approved by 2+ team members

---

## Appendix A: Test Data Generation

### Generating Valid Test Data

```python
def generate_valid_execution_result(seed: int = 42) -> ExecutionResult:
    """Generate ExecutionResult with valid metrics for testing."""
    import random
    random.seed(seed)

    return ExecutionResult(
        success=True,
        sharpe_ratio=random.uniform(-10, 10),
        max_drawdown=random.uniform(-0.999, 0),
        total_return=random.uniform(-1, 10),
        execution_time=random.uniform(0.1, 5.0)
    )

def generate_invalid_execution_result(
    error_type: str,
    seed: int = 42
) -> ExecutionResult:
    """Generate ExecutionResult with specific validation error."""
    import random
    random.seed(seed)

    if error_type == "sharpe_too_high":
        return ExecutionResult(
            success=True,
            sharpe_ratio=random.uniform(10.1, 100),
            max_drawdown=random.uniform(-0.999, 0),
            total_return=random.uniform(-1, 10)
        )
    elif error_type == "positive_drawdown":
        return ExecutionResult(
            success=True,
            sharpe_ratio=random.uniform(-10, 10),
            max_drawdown=random.uniform(0.001, 1),
            total_return=random.uniform(-1, 10)
        )
    # ... more error types
```

---

## Appendix B: TDD Workflow Checklist

For each task:

- [ ] **RED Phase**
  - [ ] Write test cases covering all acceptance criteria
  - [ ] Write boundary condition tests
  - [ ] Write edge case tests (NaN, Inf, None)
  - [ ] Run tests - verify they fail
  - [ ] Commit failing tests: `git commit -m "test: Add failing tests for [feature]"`

- [ ] **GREEN Phase**
  - [ ] Implement minimal code to pass tests
  - [ ] Run tests - verify they pass
  - [ ] Fix any failing tests
  - [ ] Commit working implementation: `git commit -m "feat: Implement [feature]"`

- [ ] **REFACTOR Phase**
  - [ ] Improve code quality (extract functions, add docstrings)
  - [ ] Optimize performance if needed
  - [ ] Run tests - verify they still pass
  - [ ] Run mypy and pylint
  - [ ] Commit refactored code: `git commit -m "refactor: Improve [feature]"`

- [ ] **Integration**
  - [ ] Create pull request
  - [ ] Request code review
  - [ ] Address review comments
  - [ ] Merge to main branch
