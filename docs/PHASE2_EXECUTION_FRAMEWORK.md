# Phase 2 Execution Framework

## Overview

The Phase 2 Execution Framework provides a comprehensive system for executing, analyzing, and reporting on trading strategy backtests. It orchestrates the entire pipeline from strategy execution to performance classification, integrating five core components into a unified workflow.

**Purpose**: Execute multiple trading strategies in isolated processes, extract performance metrics, classify results, categorize errors, and generate comprehensive reports.

**Architecture**: Component-based design with clear separation of concerns, enabling independent testing and reusability.

## Components

### 1. BacktestExecutor

**Location**: `src/backtest/executor.py`

**Purpose**: Execute trading strategy code in isolated processes with timeout protection and comprehensive error handling.

**Key Features**:
- Cross-platform timeout protection using multiprocessing
- Process isolation to prevent resource leaks
- Queue-based inter-process communication
- Restricted execution globals (only finlab context + standard libraries)
- Full stack trace capture for debugging

**Timeout Strategy**:
- Default: 420 seconds (7 minutes) per strategy
- Uses `multiprocessing.Process` with `join(timeout)` for portable timeout handling
- Automatic process termination for runaway executions
- Graceful cleanup with terminate() followed by kill() if needed

**Execution Environment**:
```python
execution_globals = {
    "data": data,                      # finlab.data object
    "sim": sim,                        # finlab.backtest.sim function
    "pd": pd,                          # pandas for data manipulation
    "np": np,                          # numpy for numerical operations
    "start_date": "2018-01-01",        # Backtest start date
    "end_date": "2024-12-31",          # Backtest end date
    "fee_ratio": 0.001425,             # Taiwan broker default
    "tax_ratio": 0.003,                # Taiwan securities tax
}
```

**Metrics Extraction**:
- Automatically extracts metrics from finlab report using `get_stats()` API
- Extracted metrics: `daily_sharpe`, `total_return`, `max_drawdown`
- Returns structured `ExecutionResult` dataclass

### 2. MetricsExtractor

**Location**: `src/backtest/metrics.py`

**Purpose**: Extract and calculate performance metrics from finlab backtest reports.

**Key Features**:
- Unified interface for extracting metrics from various finlab report formats
- Handles missing/NaN values gracefully using `pd.isna()` checks
- Attempts multiple attribute/method names for compatibility
- Fallback calculation methods when finlab metrics unavailable

**Primary Extraction Methods**:
1. `report.get_stats()` - Returns comprehensive statistics dictionary
2. `report.get_metrics()` - Returns structured dict with categories (profitability, risk, ratio, winrate)

**Extracted Metrics**:
- **Sharpe Ratio**: Risk-adjusted return measure (daily_sharpe, sharpe_ratio)
- **Total Return**: Cumulative return percentage (total_return, cumulative_return)
- **Max Drawdown**: Peak-to-trough decline (max_drawdown, mdd)
- **Win Rate**: Percentage of winning trades (win_ratio, win_rate)

**Fallback Calculations**:
- Annualized return with proper day-count adjustments
- Sharpe ratio with automatic frequency detection (daily/weekly/monthly)
- Maximum drawdown using running maximum calculation

### 3. SuccessClassifier

**Location**: `src/backtest/classifier.py`

**Purpose**: Classify backtest results into 4 success levels based on execution status, metrics coverage, and profitability.

**Classification Levels**:

| Level | Name | Criteria | Description |
|-------|------|----------|-------------|
| 0 | FAILED | execution_success = False | Execution failed (timeout, error) |
| 1 | EXECUTED | execution_success = True, coverage < 60% | Executed but insufficient metrics |
| 2 | VALID_METRICS | execution_success = True, coverage >= 60% | Valid metrics extracted |
| 3 | PROFITABLE | Level 2 + Sharpe > 0 | Valid metrics with positive Sharpe |

**Metrics Coverage Calculation**:
- Core metrics: `sharpe_ratio`, `total_return`, `max_drawdown`
- Coverage = (extracted_count / 3) * 100%
- Threshold: 60% (at least 2 out of 3 metrics)

**Batch Classification**:
- Evaluates multiple strategies collectively
- Calculates average metrics coverage
- Counts profitable strategies (Sharpe > 0)
- Profitability threshold: 40% of strategies must be profitable for Level 3

**Classification Result**:
```python
@dataclass
class ClassificationResult:
    level: int                          # 0-3
    reason: str                         # Human-readable explanation
    metrics_coverage: float             # 0.0-1.0
    profitable_count: Optional[int]     # For batch classification
    total_count: Optional[int]          # For batch classification
```

### 4. ErrorClassifier

**Location**: `src/backtest/error_classifier.py`

**Purpose**: Categorize execution errors using pattern matching on error types and messages.

**Error Categories**:

| Category | Error Types | Description |
|----------|-------------|-------------|
| TIMEOUT | TimeoutError | Execution time limit exceeded |
| DATA_MISSING | KeyError, AttributeError, IndexError | Missing or inaccessible data |
| CALCULATION | ZeroDivisionError, OverflowError, FloatingPointError | Mathematical/computation errors |
| SYNTAX | SyntaxError, IndentationError, NameError, ImportError | Code syntax or structure errors |
| OTHER | All others | Uncategorized errors |

**Pattern Matching Strategy**:
1. Regex-based pattern matching for robust error detection
2. Support for Chinese and English error messages
3. Hierarchical classification (type-first, then message patterns)
4. Case-insensitive matching with DOTALL flag

**Example Patterns**:
```python
# TIMEOUT patterns
error_types=["TimeoutError"]
message_patterns=[r"timeout", r"exceeded timeout", r"time limit"]

# DATA_MISSING patterns
error_types=["KeyError"]
message_patterns=[r"key.*not.*found", r"找不到鍵"]  # English + Chinese
```

**Batch Error Grouping**:
- Groups failed results by error category
- Tracks error frequency for top error identification
- Provides error summary with counts by category

### 5. ResultsReporter

**Location**: `src/backtest/reporter.py`

**Purpose**: Generate comprehensive reports from backtest execution results in JSON and Markdown formats.

**JSON Report Structure**:
```json
{
  "summary": {
    "total": int,
    "successful": int,
    "failed": int,
    "classification_breakdown": {
      "level_0_failed": int,
      "level_1_executed": int,
      "level_2_valid_metrics": int,
      "level_3_profitable": int
    }
  },
  "metrics": {
    "avg_sharpe": float,
    "avg_return": float,
    "avg_drawdown": float,
    "win_rate": float,
    "execution_success_rate": float
  },
  "errors": {
    "by_category": {
      "timeout": int,
      "data_missing": int,
      "calculation": int,
      "syntax": int,
      "other": int
    },
    "top_errors": [
      {"error_type": str, "message": str, "count": int}
    ]
  },
  "execution_stats": {
    "avg_execution_time": float,
    "total_execution_time": float,
    "timeout_count": int
  }
}
```

**Markdown Report Sections**:
1. Executive Summary - Key statistics overview
2. Success/Failure Breakdown - Table with counts and percentages
3. Classification Level Distribution - 4-level breakdown
4. Top Errors - Most frequent errors (up to 10)
5. Performance Metrics Summary - Averaged metrics
6. Execution Statistics - Timing and timeout information

**File Export**:
- JSON: Formatted with 2-space indentation, UTF-8 encoding
- Markdown: Human-readable tables and sections
- Automatic parent directory creation

## Workflow

### Complete Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase2TestRunner                         │
│                  (Orchestration Layer)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 1: Verify Authentication                                │
│   - Check finlab session status                              │
│   - Validate credentials and session                         │
│   - Abort if authentication fails                            │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 2: Discover Strategies                                  │
│   - Scan for generated_strategy_fixed_iter*.py files         │
│   - Sort by iteration number                                 │
│   - Apply --limit flag if specified                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 3: Execute Strategies (Loop)                            │
│   FOR EACH strategy_file:                                    │
│     1. Read strategy code                                    │
│     2. BacktestExecutor.execute()                            │
│        ├─ Create isolated process                            │
│        ├─ Set up restricted globals                          │
│        ├─ exec() strategy code                               │
│        ├─ Extract metrics from report                        │
│        └─ Return ExecutionResult                             │
│     3. Log progress (every 5 strategies)                     │
│     4. Handle failures gracefully (continue to next)         │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 4: Extract Metrics and Classify                         │
│   FOR EACH execution_result:                                 │
│     1. Convert ExecutionResult → StrategyMetrics             │
│     2. SuccessClassifier.classify_single()                   │
│        ├─ Check execution_success                            │
│        ├─ Calculate metrics coverage                         │
│        ├─ Check profitability (Sharpe > 0)                   │
│        └─ Assign level (0-3)                                 │
│     3. Store classification results                          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ Step 5: Generate Reports                                     │
│   1. ResultsReporter.generate_json_report()                  │
│      ├─ Aggregate summary statistics                         │
│      ├─ Calculate average metrics                            │
│      ├─ Categorize errors with ErrorClassifier               │
│      └─ Compile execution statistics                         │
│   2. ResultsReporter.generate_markdown_report()              │
│      ├─ Format executive summary                             │
│      ├─ Create tables for breakdown                          │
│      ├─ Generate metrics summary                             │
│      └─ Add execution statistics                             │
│   3. Save both reports to disk                               │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │  Print Summary │
                   │   & Complete   │
                   └────────────────┘
```

### Detailed Component Interaction

```
Strategy Code (Python file)
         │
         ▼
BacktestExecutor.execute()
         │
         ├─► Multiprocessing.Process (isolated)
         │        │
         │        ├─► exec(strategy_code, restricted_globals)
         │        │
         │        ├─► report = sim(position, ...)
         │        │
         │        ├─► stats = report.get_stats()
         │        │
         │        └─► Queue.put(ExecutionResult)
         │
         ▼
ExecutionResult
  ├─ success: bool
  ├─ sharpe_ratio: float
  ├─ total_return: float
  ├─ max_drawdown: float
  ├─ error_type: str (if failed)
  └─ error_message: str (if failed)
         │
         ▼
MetricsExtractor.extract_metrics()
         │
         ▼
StrategyMetrics
  ├─ sharpe_ratio: float
  ├─ total_return: float
  ├─ max_drawdown: float
  ├─ win_rate: float
  └─ execution_success: bool
         │
         ▼
SuccessClassifier.classify_single()
         │
         ▼
ClassificationResult
  ├─ level: int (0-3)
  ├─ reason: str
  └─ metrics_coverage: float
         │
         ▼
ResultsReporter.generate_json_report()
ResultsReporter.generate_markdown_report()
         │
         ▼
   Report Files
  ├─ phase2_backtest_results.json
  └─ phase2_backtest_results.md
```

## Success Levels

### Level 0: FAILED

**Criteria**: `execution_success = False`

**Typical Causes**:
- Timeout (exceeded 420 seconds)
- Syntax errors in generated code
- Data access errors (KeyError, AttributeError)
- Mathematical errors (ZeroDivisionError)
- Import errors or missing dependencies

**Outcome**: No metrics extracted, full error details captured

**Example**:
```
ClassificationResult(
    level=0,
    reason="Execution failed (execution_success=False)",
    metrics_coverage=0.0
)
```

### Level 1: EXECUTED

**Criteria**: `execution_success = True` AND `metrics_coverage < 60%`

**Typical Causes**:
- Report object has unusual structure
- Metrics not available in finlab report
- Extraction methods returned NaN values
- Only 0-1 out of 3 core metrics extracted

**Outcome**: Partial metrics available, needs investigation

**Example**:
```
ClassificationResult(
    level=1,
    reason="Executed but insufficient metrics coverage (1/3, need >= 60%)",
    metrics_coverage=0.33
)
```

### Level 2: VALID_METRICS

**Criteria**: `execution_success = True` AND `metrics_coverage >= 60%`

**Typical Causes**:
- All 3 metrics extracted successfully
- But Sharpe ratio is negative or zero (not profitable)

**Outcome**: Complete metrics available, strategy is not profitable

**Example**:
```
ClassificationResult(
    level=2,
    reason="Valid metrics extracted (3/3) but not profitable (Sharpe=-0.15)",
    metrics_coverage=1.0
)
```

### Level 3: PROFITABLE

**Criteria**: Level 2 + `sharpe_ratio > 0`

**Requirements**:
- Execution successful
- At least 2 out of 3 core metrics extracted (≥60% coverage)
- Sharpe ratio > 0 (positive risk-adjusted return)

**Outcome**: Complete metrics available, strategy shows positive performance

**Example**:
```
ClassificationResult(
    level=3,
    reason="Valid metrics extracted (3/3) with profitable performance (Sharpe=1.52)",
    metrics_coverage=1.0
)
```

**Phase 2 Results**: All 20 strategies achieved Level 3 (100% success rate)

## Usage Examples

### Basic Usage - Execute All Strategies

```bash
python run_phase2_backtest_execution.py
```

**Output**:
- Executes all 20 strategies with default 420s timeout
- Generates `phase2_backtest_results.json`
- Generates `phase2_backtest_results.md`
- Prints summary to console

### Execute Limited Subset

```bash
python run_phase2_backtest_execution.py --limit 5
```

**Use Case**: Quick validation test with first 5 strategies

### Custom Timeout

```bash
python run_phase2_backtest_execution.py --timeout 300
```

**Use Case**: Reduce timeout to 5 minutes for faster iteration

### Quiet Mode

```bash
python run_phase2_backtest_execution.py --quiet
```

**Use Case**: Suppress verbose authentication details and progress messages

### Combined Flags

```bash
python run_phase2_backtest_execution.py --limit 3 --timeout 300 --quiet
```

**Use Case**: Quick test with 3 strategies, 5-minute timeout, minimal output

### Programmatic Usage

```python
from run_phase2_backtest_execution import Phase2TestRunner

# Initialize runner
runner = Phase2TestRunner(timeout=420, limit=None)

# Execute all strategies
summary = runner.run(timeout=420, verbose=True)

# Access results
print(f"Total: {summary['total_strategies']}")
print(f"Successful: {summary['executed']}")
print(f"Failed: {summary['failed']}")
print(f"Execution Time: {summary['execution_time']:.1f}s")

# Access detailed results
for result in summary['results']:
    if result.success:
        print(f"Sharpe: {result.sharpe_ratio:.2f}")
        print(f"Return: {result.total_return:.1%}")
        print(f"Drawdown: {result.max_drawdown:.1%}")
```

### Component-Level Usage

**Execute Single Strategy**:
```python
from src.backtest.executor import BacktestExecutor
from finlab import data, backtest

executor = BacktestExecutor(timeout=420)

strategy_code = """
close = data.get("price:收盤價")
position = close > close.rolling(20).mean()
position = position.loc[start_date:end_date]
report = sim(position, fee_ratio=fee_ratio, tax_ratio=tax_ratio)
"""

result = executor.execute(
    strategy_code=strategy_code,
    data=data,
    sim=backtest.sim,
    timeout=420
)

print(f"Success: {result.success}")
print(f"Sharpe: {result.sharpe_ratio}")
```

**Extract Metrics**:
```python
from src.backtest.metrics import MetricsExtractor

extractor = MetricsExtractor()
metrics = extractor.extract_metrics(report)

print(f"Sharpe: {metrics.sharpe_ratio}")
print(f"Return: {metrics.total_return}")
print(f"Drawdown: {metrics.max_drawdown}")
```

**Classify Result**:
```python
from src.backtest.classifier import SuccessClassifier

classifier = SuccessClassifier()
classification = classifier.classify_single(metrics)

print(f"Level: {classification.level}")
print(f"Reason: {classification.reason}")
print(f"Coverage: {classification.metrics_coverage:.1%}")
```

**Categorize Errors**:
```python
from src.backtest.error_classifier import ErrorClassifier

error_classifier = ErrorClassifier()

# Classify single error
category = error_classifier.classify_error(
    error_type="KeyError",
    error_message="key 'price' not found"
)
print(f"Category: {category.value}")

# Group batch errors
grouped = error_classifier.group_errors(execution_results)
for category, results in grouped.items():
    print(f"{category.value}: {len(results)} errors")
```

**Generate Reports**:
```python
from src.backtest.reporter import ResultsReporter

reporter = ResultsReporter()

# Generate JSON report
json_report = reporter.generate_json_report(execution_results)
reporter.save_report(json_report, 'report.json', format='json')

# Generate Markdown report
markdown_report = reporter.generate_markdown_report(execution_results)
reporter.save_report(markdown_report, 'report.md', format='markdown')
```

## Results Interpretation

### Reading JSON Reports

**Key Sections**:

1. **Summary**: High-level statistics
   - `total`: Number of strategies executed
   - `successful`: Strategies with execution_success=True
   - `failed`: Strategies with execution_success=False
   - `classification_breakdown`: Count by level (0-3)

2. **Metrics**: Averaged performance indicators
   - `avg_sharpe`: Average Sharpe ratio (>0.5 good, >1.0 excellent)
   - `avg_return`: Average total return (decimal format, 4.01 = 401%)
   - `avg_drawdown`: Average max drawdown (negative value, -0.34 = -34%)
   - `win_rate`: Percentage of profitable strategies (Sharpe > 0)
   - `execution_success_rate`: Percentage of successful executions

3. **Errors**: Error analysis
   - `by_category`: Count per error category
   - `top_errors`: Most frequent errors with counts

4. **Execution Stats**: Timing information
   - `avg_execution_time`: Average seconds per strategy
   - `total_execution_time`: Total seconds for all strategies
   - `timeout_count`: Number of timeouts

### Phase 2 Results Analysis

**Actual Results** (20 strategies):
```json
{
  "summary": {
    "total": 20,
    "successful": 20,
    "failed": 0,
    "classification_breakdown": {
      "level_3_profitable": 20  // 100% at highest level
    }
  },
  "metrics": {
    "avg_sharpe": 0.7163,        // Good risk-adjusted returns
    "avg_return": 4.0099,        // 401% average return
    "avg_drawdown": -0.3437,     // 34% average drawdown
    "win_rate": 1.0,             // 100% profitable strategies
    "execution_success_rate": 1.0 // 100% execution success
  },
  "execution_stats": {
    "avg_execution_time": 15.89,  // ~16 seconds per strategy
    "total_execution_time": 317.86, // ~5.3 minutes total
    "timeout_count": 0            // No timeouts
  }
}
```

**Interpretation**:
- **Perfect Execution**: 100% success rate with no failures
- **All Profitable**: 100% of strategies achieved Level 3 (Sharpe > 0)
- **Strong Returns**: Average 401% return over backtest period
- **Acceptable Risk**: Average Sharpe 0.72 indicates positive risk-adjusted returns
- **Fast Execution**: Average 16s per strategy, well under 420s timeout
- **No Issues**: Zero timeouts, zero errors - system is stable

### Performance Benchmarks

**Sharpe Ratio Guidelines**:
- `< 0.0`: Losing money, worse than risk-free rate
- `0.0 - 0.5`: Marginal performance, high risk
- `0.5 - 1.0`: Good performance, acceptable risk
- `1.0 - 2.0`: Excellent performance, strong risk-adjusted returns
- `> 2.0`: Outstanding performance (rare in practice)

**Return Guidelines** (7-year backtest, 2018-2024):
- `< 0%`: Net loss
- `0% - 50%`: Modest returns (~7% annualized)
- `50% - 200%`: Good returns (~14-18% annualized)
- `200% - 400%`: Excellent returns (~18-25% annualized)
- `> 400%`: Outstanding returns (>25% annualized)

**Drawdown Guidelines**:
- `0% - 10%`: Excellent capital preservation
- `10% - 20%`: Good, typical for conservative strategies
- `20% - 30%`: Acceptable, typical for balanced strategies
- `30% - 40%`: High, requires strong risk tolerance
- `> 40%`: Very high, suitable only for aggressive portfolios

**Execution Time Guidelines** (per strategy):
- `< 30s`: Fast, efficient backtesting
- `30s - 120s`: Normal, acceptable for production
- `120s - 300s`: Slow, consider optimization
- `300s - 420s`: Very slow, approaching timeout
- `> 420s`: Timeout, indicates performance issue

### Success Rate Benchmarks

**Classification Distribution**:
- **Level 0 (FAILED)**: Target < 5%, indicates execution stability
- **Level 1 (EXECUTED)**: Target < 10%, indicates metrics extraction quality
- **Level 2 (VALID_METRICS)**: Acceptable if < 40%, needs improvement if higher
- **Level 3 (PROFITABLE)**: Target > 40% for viable strategy generation system

**Phase 2 Achievement**: 100% Level 3 (exceptional, exceeds all targets)

## Error Handling

### Timeout Protection

**Process Isolation**:
- Each strategy runs in separate process via `multiprocessing.Process`
- Parent process monitors child with `join(timeout)`
- No shared memory between processes

**Termination Sequence**:
1. Wait for process completion up to `timeout` seconds
2. If still running, call `process.terminate()` (SIGTERM)
3. Wait 5 seconds for graceful cleanup
4. If still running, call `process.kill()` (SIGKILL)
5. Wait 2 seconds for forced termination

**Error Result**:
```python
ExecutionResult(
    success=False,
    error_type="TimeoutError",
    error_message="Backtest execution exceeded timeout of 420 seconds",
    execution_time=420.0,
    stack_trace="Process killed after timeout (420s)"
)
```

### Exception Handling

**Execution Exceptions**:
- `SyntaxError`: Invalid Python syntax with line number
- `TimeoutError`: Explicit timeout raised in process
- `KeyError/AttributeError`: Data access errors
- `ZeroDivisionError`: Mathematical errors
- Generic `Exception`: Catch-all for unexpected errors

**Stack Trace Capture**:
```python
except Exception as e:
    result = ExecutionResult(
        success=False,
        error_type=type(e).__name__,
        error_message=str(e),
        execution_time=time.time() - start_time,
        stack_trace=traceback.format_exc()  # Full traceback
    )
```

### Graceful Degradation

**Strategy-Level Failures**:
- Individual strategy failures do NOT stop execution
- Runner continues to next strategy
- Failed results included in final report
- Error categorization helps identify systematic issues

**Metrics Extraction Failures**:
- Missing metrics → StrategyMetrics with None values
- NaN values converted to None
- Fallback calculations if finlab metrics unavailable
- Classification adjusts based on metrics coverage

**Report Generation Resilience**:
- Empty results list → generates empty report template
- Missing metrics → displays "N/A" in tables
- Zero successful strategies → still produces valid report structure

## Performance Considerations

### Execution Efficiency

**Multiprocessing Overhead**:
- Process creation: ~0.1-0.3s per strategy
- Queue communication: negligible (<10ms)
- Total overhead: ~2-6s for 20 strategies

**Actual Performance** (Phase 2):
- Average execution: 15.89s per strategy
- Total time: 317.86s for 20 strategies
- Overhead ratio: ~2% (very efficient)

### Memory Management

**Process Isolation Benefits**:
- Each strategy has independent memory space
- Failed strategies cannot leak memory to parent
- Automatic cleanup when process terminates
- No cumulative memory growth across strategies

**Data Loading**:
- finlab.data loaded once in parent process
- Passed to child processes via multiprocessing (copy-on-write on Unix)
- Each strategy execution is independent

### Scalability

**Parallel Execution** (not implemented in Phase 2):
- Current: Sequential execution (one strategy at a time)
- Future: Parallel execution using `multiprocessing.Pool`
- Estimated speedup: Linear with CPU cores (8 cores → ~8x faster)
- Trade-off: Higher memory usage (multiple finlab.data copies)

**Batch Size Considerations**:
- 20 strategies: ~5 minutes total (acceptable)
- 100 strategies: ~26 minutes estimated (acceptable)
- 1000 strategies: ~4.4 hours estimated (requires parallelization)

## Security

### Code Execution Safety

**Restricted Globals**:
- Only finlab context (data, sim) and standard libraries (pd, np)
- No access to `os`, `sys`, `subprocess`, `eval`, `open`, etc.
- `__builtins__` included for basic operations only

**Process Sandbox**:
- Separate process per strategy (no shared state)
- Cannot affect parent process except through Queue
- Timeout enforcement prevents infinite loops
- Process termination prevents resource exhaustion

**Input Validation**:
- Strategy code read from trusted files (generated by system)
- No user-supplied code execution in production
- File paths validated before reading

### Resource Protection

**CPU Protection**:
- Timeout enforced at 420 seconds (7 minutes)
- Process termination prevents CPU monopolization
- No strategy can hang the system

**Memory Protection**:
- Each process has independent memory space
- Automatic memory cleanup on process termination
- No memory leaks propagate to parent

**Disk Protection**:
- Strategy code has no file system access (no open() in globals)
- Reports written to controlled output paths
- No arbitrary file writes possible

## Troubleshooting

### Common Issues

**Issue**: "Finlab session authentication failed"
- **Cause**: finlab credentials not set or expired
- **Solution**: Set FINLAB_API_TOKEN environment variable or run `finlab.login()`
- **Verification**: Run `python -c "from finlab import data; print(data.get('price:收盤價').shape)"`

**Issue**: "No strategy files found"
- **Cause**: generated_strategy_fixed_iter*.py files missing
- **Solution**: Ensure strategy files exist in project root
- **Verification**: Run `ls generated_strategy_fixed_iter*.py`

**Issue**: "TimeoutError: execution exceeded timeout"
- **Cause**: Strategy taking too long to execute (>420s)
- **Solution**: Increase timeout with `--timeout 600` or optimize strategy
- **Diagnosis**: Check strategy complexity (number of operations, data size)

**Issue**: "KeyError: 'price:收盤價'"
- **Cause**: Data not available in finlab.data
- **Solution**: Verify finlab data access, check field names
- **Diagnosis**: Run `print(data.list_fields())` to see available fields

**Issue**: "Metrics extraction failed - all None"
- **Cause**: finlab report format incompatible with MetricsExtractor
- **Solution**: Update MetricsExtractor patterns, check finlab version
- **Diagnosis**: Inspect report object: `print(dir(report))`, `print(report.get_stats())`

### Debugging Strategies

**Enable Verbose Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Inspect Execution Results**:
```python
summary = runner.run()
for i, result in enumerate(summary['results']):
    if not result.success:
        print(f"Strategy {i}: {result.error_type} - {result.error_message}")
        print(f"Stack trace: {result.stack_trace}")
```

**Test Single Strategy**:
```bash
python run_phase2_backtest_execution.py --limit 1 --timeout 60
```

**Check Report Structure**:
```python
from finlab import data, backtest
import pandas as pd
import numpy as np

# Minimal working example
close = data.get("price:收盤價")
position = close > close.rolling(20).mean()
report = backtest.sim(position.iloc[:100], resample="D")
print(type(report))
print(dir(report))
print(report.get_stats())
```

## Related Documentation

- **API Reference**: `docs/PHASE2_API_REFERENCE.md` - Detailed API documentation
- **Code Review**: `docs/PHASE2_CODE_REVIEW.md` - Architecture analysis and recommendations
- **Component Documentation**:
  - `src/backtest/executor.py` - BacktestExecutor implementation
  - `src/backtest/metrics.py` - MetricsExtractor implementation
  - `src/backtest/classifier.py` - SuccessClassifier implementation
  - `src/backtest/error_classifier.py` - ErrorClassifier implementation
  - `src/backtest/reporter.py` - ResultsReporter implementation
- **Test Results**:
  - `phase2_backtest_results.json` - Actual execution results (JSON)
  - `phase2_backtest_results.md` - Actual execution results (Markdown)
