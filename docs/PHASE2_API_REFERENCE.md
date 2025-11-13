# Phase 2 API Reference

Complete API documentation for the Phase 2 Backtest Execution Framework components.

## Table of Contents

1. [BacktestExecutor API](#backtestexecutor-api)
2. [MetricsExtractor API](#metricsextractor-api)
3. [SuccessClassifier API](#successclassifier-api)
4. [ErrorClassifier API](#errorclassifier-api)
5. [ResultsReporter API](#resultsreporter-api)
6. [Phase2TestRunner API](#phase2testrunner-api)

---

## BacktestExecutor API

**Module**: `src.backtest.executor`

**Purpose**: Execute trading strategy code in isolated processes with timeout protection.

### Classes

#### ExecutionResult

```python
@dataclass
class ExecutionResult:
    """Result from isolated strategy execution."""
    success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    report: Optional[Any] = field(default=None, repr=False)
    stack_trace: Optional[str] = None
```

**Attributes**:
- `success` (bool): Whether execution completed without errors
- `error_type` (Optional[str]): Type of error if failed (e.g., 'TimeoutError', 'SyntaxError')
- `error_message` (Optional[str]): Human-readable error message
- `execution_time` (float): Total execution time in seconds
- `sharpe_ratio` (Optional[float]): Sharpe ratio from backtest (if successful)
- `total_return` (Optional[float]): Total return percentage (if successful)
- `max_drawdown` (Optional[float]): Maximum drawdown (if successful)
- `report` (Optional[Any]): Finlab backtest report object (not serialized across processes)
- `stack_trace` (Optional[str]): Full stack trace if error occurred

**Example**:
```python
# Successful execution
ExecutionResult(
    success=True,
    execution_time=15.2,
    sharpe_ratio=1.52,
    total_return=2.45,
    max_drawdown=-0.18
)

# Failed execution
ExecutionResult(
    success=False,
    error_type="KeyError",
    error_message="key 'price' not found",
    execution_time=2.1,
    stack_trace="Traceback (most recent call last):\n..."
)
```

#### BacktestExecutor

```python
class BacktestExecutor:
    """Execute trading strategies in isolated processes with timeout protection."""

    def __init__(self, timeout: int = 420):
        """Initialize BacktestExecutor.

        Args:
            timeout: Default timeout in seconds (default: 420 = 7 minutes)
        """

    def execute(
        self,
        strategy_code: str,
        data: Any,
        sim: Any,
        timeout: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
    ) -> ExecutionResult:
        """Execute strategy code in isolated process with timeout protection.

        Args:
            strategy_code: Python code to execute (must call sim() and return report)
            data: finlab.data object for strategy to use
            sim: finlab.backtest.sim function for backtesting
            timeout: Execution timeout in seconds (overrides default)
            start_date: Backtest start date (YYYY-MM-DD, default: 2018-01-01)
            end_date: Backtest end date (YYYY-MM-DD, default: 2024-12-31)
            fee_ratio: Transaction fee ratio (default: 0.001425)
            tax_ratio: Transaction tax ratio (default: 0.003)

        Returns:
            ExecutionResult with execution status, metrics, and any errors
        """
```

**Example**:
```python
from src.backtest.executor import BacktestExecutor
from finlab import data, backtest

executor = BacktestExecutor(timeout=420)

strategy_code = """
close = data.get("price:收盤價")
position = close > close.rolling(20).mean()
position = position.loc[start_date:end_date]
report = sim(
    position,
    fee_ratio=fee_ratio,
    tax_ratio=tax_ratio,
    resample="M",
    position_limit=0.1
)
"""

result = executor.execute(
    strategy_code=strategy_code,
    data=data,
    sim=backtest.sim,
    timeout=300,
    start_date="2020-01-01",
    end_date="2023-12-31",
    fee_ratio=0.0,
    tax_ratio=0.003
)

if result.success:
    print(f"Sharpe: {result.sharpe_ratio:.2f}")
    print(f"Return: {result.total_return:.1%}")
else:
    print(f"Error: {result.error_type} - {result.error_message}")
```

**Timeout Behavior**:
- Process runs until completion or timeout
- At timeout: `terminate()` → wait 5s → `kill()` if needed
- Returns ExecutionResult with error_type="TimeoutError"

**Process Isolation**:
- Each execution runs in separate process
- Restricted globals (data, sim, pd, np only)
- No shared memory with parent
- Automatic cleanup on completion

---

## MetricsExtractor API

**Module**: `src.backtest.metrics`

**Purpose**: Extract performance metrics from finlab backtest reports.

### Classes

#### StrategyMetrics

```python
@dataclass
class StrategyMetrics:
    """Extracted metrics from finlab backtest reports."""
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success: bool = False
```

**Attributes**:
- `sharpe_ratio` (Optional[float]): Sharpe ratio of strategy returns
- `total_return` (Optional[float]): Total return percentage (0.25 = 25%)
- `max_drawdown` (Optional[float]): Maximum drawdown (negative value)
- `win_rate` (Optional[float]): Percentage of winning trades (0.65 = 65%)
- `execution_success` (bool): Whether metrics were successfully extracted

**Post-Init Validation**:
- NaN values automatically converted to None
- Uses `pd.isna()` for validation

**Example**:
```python
StrategyMetrics(
    sharpe_ratio=1.5,
    total_return=0.25,
    max_drawdown=-0.15,
    win_rate=0.55,
    execution_success=True
)
```

#### MetricsExtractor

```python
class MetricsExtractor:
    """Extract metrics from finlab backtest report objects."""

    def extract_metrics(self, report: Any) -> StrategyMetrics:
        """Extract metrics from finlab backtest report.

        Uses finlab API methods (get_stats() and get_metrics()) to extract
        performance metrics. Returns structured StrategyMetrics dataclass.

        Args:
            report: Finlab backtest report object (from finlab.backtest.sim)

        Returns:
            StrategyMetrics with extracted metrics (None if extraction fails)

        Notes:
            - NaN values converted to None
            - Non-numeric values ignored
            - execution_success=True only if at least one metric extracted
        """
```

**Extraction Strategy**:
1. Try `report.get_stats()` first (primary method)
2. Extract from stats dict using multiple key patterns
3. Fall back to `report.get_metrics()` if needed
4. Return StrategyMetrics with available values

**Supported Metric Keys**:
- Sharpe: `daily_sharpe`, `sharpe_ratio`, `sharpe`, `annual_sharpe`
- Return: `total_return`, `cumulative_return`, `cum_return`, `return`
- Drawdown: `max_drawdown`, `maximum_drawdown`, `mdd`, `drawdown`
- Win Rate: `win_ratio`, `win_rate`, `winning_rate`, `winrate`

**Example**:
```python
from src.backtest.metrics import MetricsExtractor

extractor = MetricsExtractor()
metrics = extractor.extract_metrics(report)

if metrics.execution_success:
    print(f"Sharpe: {metrics.sharpe_ratio}")
    print(f"Return: {metrics.total_return:.1%}")
    print(f"Drawdown: {metrics.max_drawdown:.1%}")
else:
    print("Metrics extraction failed")
```

### Functions

#### calculate_max_drawdown

```python
def calculate_max_drawdown(equity_curve: list) -> float:
    """Calculate maximum drawdown from equity curve.

    Args:
        equity_curve: List of equity values over time

    Returns:
        Maximum drawdown as negative decimal (-0.25 for 25% drawdown)

    Notes:
        - Returns 0.0 for empty or single-value lists
        - Uses numpy cumulative maximum for efficiency
        - Always returns non-positive values
    """
```

**Example**:
```python
from src.backtest.metrics import calculate_max_drawdown

equity = [100, 110, 105, 120, 90]
dd = calculate_max_drawdown(equity)
print(f"Max Drawdown: {dd:.1%}")  # -25.0%
```

#### calculate_calmar_ratio

```python
def calculate_calmar_ratio(
    annual_return: float,
    max_drawdown: float
) -> Optional[float]:
    """Calculate Calmar Ratio: annual return / abs(max drawdown).

    Args:
        annual_return: Annualized return as decimal (0.15 for 15%)
        max_drawdown: Maximum drawdown as negative decimal (-0.20)

    Returns:
        Calmar ratio as float, or None if inputs invalid

    Notes:
        - Returns None for zero or near-zero drawdown (< 1e-10)
        - Returns None for NaN inputs
        - Can return negative values if annual_return negative
    """
```

**Example**:
```python
from src.backtest.metrics import calculate_calmar_ratio

calmar = calculate_calmar_ratio(0.15, -0.20)
print(f"Calmar Ratio: {calmar:.2f}")  # 0.75
```

---

## SuccessClassifier API

**Module**: `src.backtest.classifier`

**Purpose**: Classify backtest results into 4 success levels.

### Classes

#### ClassificationResult

```python
@dataclass
class ClassificationResult:
    """Result of strategy backtest classification."""
    level: int
    reason: str
    metrics_coverage: float
    profitable_count: Optional[int] = None
    total_count: Optional[int] = None
```

**Attributes**:
- `level` (int): Classification level (0-3)
  - 0: FAILED - Execution failed
  - 1: EXECUTED - Executed but incomplete metrics
  - 2: VALID_METRICS - Sufficient metrics extracted
  - 3: PROFITABLE - Valid metrics with positive Sharpe
- `reason` (str): Human-readable explanation of classification
- `metrics_coverage` (float): Percentage of metrics extracted (0.0-1.0)
- `profitable_count` (Optional[int]): Number of profitable strategies (batch only)
- `total_count` (Optional[int]): Total strategies evaluated (batch only)

**Example**:
```python
ClassificationResult(
    level=3,
    reason="Valid metrics with profitable performance (Sharpe=1.52)",
    metrics_coverage=1.0,
    profitable_count=None,
    total_count=None
)
```

#### SuccessClassifier

```python
class SuccessClassifier:
    """Classifies backtest results into success levels."""

    # Class attributes
    COVERAGE_METRICS = {'sharpe_ratio', 'total_return', 'max_drawdown'}
    METRICS_COVERAGE_THRESHOLD = 0.60
    PROFITABILITY_THRESHOLD = 0.40

    def classify_single(
        self,
        strategy_metrics: StrategyMetrics
    ) -> ClassificationResult:
        """Classify a single backtest result.

        Args:
            strategy_metrics: StrategyMetrics from metrics extraction

        Returns:
            ClassificationResult with level (0-3), reason, and coverage

        Notes:
            - Level 0: execution_success=False
            - Level 1: execution_success=True AND coverage < 60%
            - Level 2: execution_success=True AND coverage >= 60%
            - Level 3: Level 2 AND sharpe_ratio > 0
        """

    def classify_batch(
        self,
        results: List[StrategyMetrics]
    ) -> ClassificationResult:
        """Classify a batch of backtest results.

        Args:
            results: List of StrategyMetrics objects

        Returns:
            ClassificationResult with aggregate level and profitability stats

        Notes:
            - Level 0: No executed strategies (all failed)
            - Level 1: Average coverage < 60%
            - Level 2: Average coverage >= 60%
            - Level 3: Level 2 AND >= 40% strategies profitable
        """
```

**Example**:
```python
from src.backtest.classifier import SuccessClassifier

classifier = SuccessClassifier()

# Single strategy classification
metrics = StrategyMetrics(
    sharpe_ratio=1.5,
    total_return=0.25,
    max_drawdown=-0.15,
    execution_success=True
)
result = classifier.classify_single(metrics)
print(f"Level {result.level}: {result.reason}")
print(f"Coverage: {result.metrics_coverage:.1%}")

# Batch classification
metrics_list = [metrics1, metrics2, metrics3]
batch_result = classifier.classify_batch(metrics_list)
print(f"Level {batch_result.level}: {batch_result.reason}")
print(f"Profitable: {batch_result.profitable_count}/{batch_result.total_count}")
```

**Coverage Calculation**:
```python
# Core metrics: sharpe_ratio, total_return, max_drawdown
extracted_count = sum([
    metrics.sharpe_ratio is not None,
    metrics.total_return is not None,
    metrics.max_drawdown is not None
])
coverage = extracted_count / 3  # 0.0, 0.33, 0.67, or 1.0
```

---

## ErrorClassifier API

**Module**: `src.backtest.error_classifier`

**Purpose**: Categorize execution errors using pattern matching.

### Enums

#### ErrorCategory

```python
class ErrorCategory(Enum):
    """Classification categories for execution errors."""
    TIMEOUT = "timeout"
    DATA_MISSING = "data_missing"
    CALCULATION = "calculation"
    SYNTAX = "syntax"
    OTHER = "other"
```

**Values**:
- `TIMEOUT`: Execution exceeded time limit
- `DATA_MISSING`: Data/key not found or inaccessible
- `CALCULATION`: Mathematical or computation errors
- `SYNTAX`: Code syntax or structure errors
- `OTHER`: Uncategorized or unknown errors

### Classes

#### ErrorPattern

```python
@dataclass
class ErrorPattern:
    """Pattern definition for error classification."""
    name: str
    error_types: List[str]
    message_patterns: List[str]
    category: ErrorCategory
    compiled_patterns: List[re.Pattern] = field(default_factory=list, init=False)

    def matches_error(self, error_type: str, error_message: str) -> bool:
        """Check if this pattern matches the given error.

        Args:
            error_type: Type of error (e.g., 'KeyError')
            error_message: Error message text

        Returns:
            True if error_type matches and any message_pattern matches
        """
```

**Example**:
```python
ErrorPattern(
    name="key_error",
    error_types=["KeyError"],
    message_patterns=[
        r"key.*not.*found",
        r"找不到鍵"  # Chinese support
    ],
    category=ErrorCategory.DATA_MISSING
)
```

#### ErrorClassifier

```python
class ErrorClassifier:
    """Classify execution errors into standardized categories."""

    def __init__(self) -> None:
        """Initialize error classifier with predefined patterns."""

    def classify_error(
        self,
        error_type: str,
        error_message: str = "",
    ) -> ErrorCategory:
        """Classify a single error into a category.

        Args:
            error_type: Type of error (e.g., 'KeyError', 'TimeoutError')
            error_message: Error message text (may be empty)

        Returns:
            ErrorCategory matching the error

        Notes:
            - Checks patterns in order (priority matters)
            - First matching pattern determines category
            - Falls back to OTHER if no patterns match
        """

    def group_errors(
        self,
        execution_results: List[ExecutionResult],
    ) -> Dict[ErrorCategory, List[ExecutionResult]]:
        """Group execution results by error category.

        Args:
            execution_results: List of ExecutionResult objects

        Returns:
            Dictionary mapping ErrorCategory to list of ExecutionResult
            Only categories with at least one error included
        """

    def get_error_summary(
        self,
        execution_results: List[ExecutionResult],
    ) -> Dict[str, int]:
        """Get summary of error counts by category.

        Args:
            execution_results: List of ExecutionResult objects

        Returns:
            Dictionary mapping category names to error counts
            Includes all categories even if count is 0
        """
```

**Example**:
```python
from src.backtest.error_classifier import ErrorClassifier, ErrorCategory

classifier = ErrorClassifier()

# Classify single error
category = classifier.classify_error(
    error_type="KeyError",
    error_message="key 'price' not found"
)
print(f"Category: {category.value}")  # data_missing

# Group batch errors
grouped = classifier.group_errors(execution_results)
for category, results in grouped.items():
    print(f"{category.value}: {len(results)} errors")

# Get error summary
summary = classifier.get_error_summary(execution_results)
print(summary)
# {'timeout': 0, 'data_missing': 5, 'calculation': 2, ...}
```

**Supported Patterns**:
- Timeout: `timeout`, `exceeded timeout`, `time limit`
- Data Missing: `key.*not.*found`, `has no attribute`, `index.*out.*range`
- Calculation: `division by zero`, `overflow`, `nan`, `infinity`
- Syntax: `syntax error`, `indentation`, `not defined`, `cannot import`

**Chinese Support**: Patterns include Chinese error message matching (e.g., `找不到鍵`, `除以零`, `語法錯誤`)

---

## ResultsReporter API

**Module**: `src.backtest.reporter`

**Purpose**: Generate comprehensive reports in JSON and Markdown formats.

### Classes

#### ReportMetrics

```python
@dataclass
class ReportMetrics:
    """Aggregated metrics statistics for report generation."""
    avg_sharpe: Optional[float] = None
    avg_return: Optional[float] = None
    avg_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success_rate: Optional[float] = None
```

**Attributes**:
- `avg_sharpe` (Optional[float]): Average Sharpe ratio across results
- `avg_return` (Optional[float]): Average total return across results
- `avg_drawdown` (Optional[float]): Average maximum drawdown across results
- `win_rate` (Optional[float]): Percentage with positive Sharpe ratio
- `execution_success_rate` (Optional[float]): Percentage of successful executions

#### ResultsReporter

```python
class ResultsReporter:
    """Generate summary reports from backtest execution results."""

    def __init__(self):
        """Initialize ResultsReporter with helper components."""

    def generate_json_report(
        self,
        results: List[ExecutionResult]
    ) -> Dict[str, Any]:
        """Generate a JSON-serializable report from execution results.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Dictionary with structure:
            {
                "summary": {...},
                "metrics": {...},
                "errors": {...},
                "execution_stats": {...}
            }
        """

    def generate_markdown_report(
        self,
        results: List[ExecutionResult]
    ) -> str:
        """Generate a human-readable Markdown report.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Markdown-formatted string containing the full report
        """

    def save_report(
        self,
        report: Any,
        filename: str,
        format: str = "json",
    ) -> Path:
        """Save report to file in specified format.

        Args:
            report: Report object (dict for JSON, str for Markdown)
            filename: Target file path
            format: Report format ('json' or 'markdown')

        Returns:
            Path object pointing to created file

        Raises:
            ValueError: If format not 'json' or 'markdown'
            IOError: If file cannot be written
        """
```

**JSON Report Structure**:
```json
{
  "summary": {
    "total": 20,
    "successful": 20,
    "failed": 0,
    "classification_breakdown": {
      "level_0_failed": 0,
      "level_1_executed": 0,
      "level_2_valid_metrics": 0,
      "level_3_profitable": 20
    }
  },
  "metrics": {
    "avg_sharpe": 0.7163,
    "avg_return": 4.0099,
    "avg_drawdown": -0.3437,
    "win_rate": 1.0,
    "execution_success_rate": 1.0
  },
  "errors": {
    "by_category": {
      "timeout": 0,
      "data_missing": 0,
      "calculation": 0,
      "syntax": 0,
      "other": 0
    },
    "top_errors": []
  },
  "execution_stats": {
    "avg_execution_time": 15.89,
    "total_execution_time": 317.86,
    "timeout_count": 0
  }
}
```

**Example**:
```python
from src.backtest.reporter import ResultsReporter

reporter = ResultsReporter()

# Generate JSON report
json_report = reporter.generate_json_report(execution_results)
reporter.save_report(json_report, 'report.json', format='json')

# Generate Markdown report
markdown_report = reporter.generate_markdown_report(execution_results)
reporter.save_report(markdown_report, 'report.md', format='markdown')

# Access report data
print(f"Total: {json_report['summary']['total']}")
print(f"Success Rate: {json_report['metrics']['execution_success_rate']:.1%}")
print(f"Avg Sharpe: {json_report['metrics']['avg_sharpe']:.2f}")
```

---

## Phase2TestRunner API

**Module**: `run_phase2_backtest_execution`

**Purpose**: Orchestrate complete execution pipeline for 20 trading strategies.

### Classes

#### Phase2TestRunner

```python
class Phase2TestRunner:
    """Orchestrator for executing 20 trading strategies end-to-end."""

    def __init__(self, timeout: int = 420, limit: Optional[int] = None):
        """Initialize Phase2TestRunner.

        Args:
            timeout: Default timeout per strategy (default: 420 seconds)
            limit: Maximum strategies to execute (None = all)
        """

    def run(
        self,
        timeout: Optional[int] = None,
        verbose: bool = True
    ) -> dict:
        """Execute main orchestration loop for all strategies.

        Args:
            timeout: Override default timeout (in seconds)
            verbose: Whether to print progress messages

        Returns:
            Dictionary with execution summary:
            {
                'success': bool,
                'total_strategies': int,
                'executed': int,
                'failed': int,
                'results': [ExecutionResult, ...],
                'strategy_metrics': [StrategyMetrics, ...],
                'classifications': [ClassificationResult, ...],
                'report': dict,
                'timestamp': str,
                'execution_time': float
            }

        Raises:
            RuntimeError: If finlab session not authenticated
        """
```

**Workflow Steps**:
1. Verify finlab session authentication
2. Discover strategy files (generated_strategy_fixed_iter*.py)
3. Execute each strategy with BacktestExecutor
4. Extract metrics with MetricsExtractor
5. Classify results with SuccessClassifier
6. Categorize errors with ErrorClassifier
7. Generate reports with ResultsReporter

**Example**:
```python
from run_phase2_backtest_execution import Phase2TestRunner

# Initialize runner
runner = Phase2TestRunner(timeout=420, limit=None)

# Execute all strategies
summary = runner.run(timeout=420, verbose=True)

# Access results
print(f"Total: {summary['total_strategies']}")
print(f"Successful: {summary['executed']} ({summary['executed']/summary['total_strategies']*100:.1f}%)")
print(f"Failed: {summary['failed']}")
print(f"Execution Time: {summary['execution_time']:.1f}s")

# Access detailed results
for i, result in enumerate(summary['results']):
    if result.success:
        print(f"Strategy {i}: Sharpe={result.sharpe_ratio:.2f}, Return={result.total_return:.1%}")
    else:
        print(f"Strategy {i}: FAILED - {result.error_type}: {result.error_message}")

# Access classifications
for i, cls in enumerate(summary['classifications']):
    print(f"Strategy {i}: Level {cls.level} - {cls.reason}")
```

**Command-Line Interface**:
```bash
# Execute all strategies (default)
python run_phase2_backtest_execution.py

# Execute limited subset
python run_phase2_backtest_execution.py --limit 5

# Custom timeout
python run_phase2_backtest_execution.py --timeout 300

# Quiet mode
python run_phase2_backtest_execution.py --quiet

# Combined flags
python run_phase2_backtest_execution.py --limit 3 --timeout 300 --quiet
```

**Arguments**:
- `--limit N`: Execute only first N strategies (default: all)
- `--timeout N`: Timeout per strategy in seconds (default: 420)
- `--quiet`: Suppress verbose output and authentication details

**Exit Codes**:
- `0`: Success (all strategies processed)
- `1`: Failure (authentication failed or exception)

---

## Type Hints

All APIs use Python type hints for clarity:

```python
from typing import Any, Dict, List, Optional, Tuple

# Example function signatures
def execute(
    strategy_code: str,
    data: Any,
    sim: Any,
    timeout: Optional[int] = None
) -> ExecutionResult:
    ...

def classify_batch(
    results: List[StrategyMetrics]
) -> ClassificationResult:
    ...

def generate_json_report(
    results: List[ExecutionResult]
) -> Dict[str, Any]:
    ...
```

## Error Handling

All methods handle errors gracefully:

```python
try:
    result = executor.execute(strategy_code, data, sim)
    if result.success:
        # Process successful result
        metrics = extractor.extract_metrics(result.report)
    else:
        # Handle execution failure
        print(f"Error: {result.error_type} - {result.error_message}")
        print(f"Stack trace: {result.stack_trace}")
except Exception as e:
    # Handle unexpected exceptions
    print(f"Unexpected error: {e}")
```

## Thread Safety

- **BacktestExecutor**: Process-safe (uses multiprocessing)
- **MetricsExtractor**: Thread-safe (read-only operations)
- **SuccessClassifier**: Thread-safe (stateless)
- **ErrorClassifier**: Thread-safe (read-only patterns)
- **ResultsReporter**: Thread-safe (stateless)

## Performance Characteristics

| Component | Time Complexity | Memory Usage |
|-----------|----------------|--------------|
| BacktestExecutor.execute() | O(n) where n=strategy complexity | Isolated process |
| MetricsExtractor.extract_metrics() | O(1) | Minimal |
| SuccessClassifier.classify_single() | O(1) | Minimal |
| SuccessClassifier.classify_batch() | O(m) where m=num strategies | O(m) |
| ErrorClassifier.classify_error() | O(p) where p=num patterns | Minimal |
| ErrorClassifier.group_errors() | O(m*p) | O(m) |
| ResultsReporter.generate_json_report() | O(m) | O(m) |
| ResultsReporter.generate_markdown_report() | O(m) | O(m) |

**Typical Performance** (20 strategies):
- Total execution: ~320 seconds (~16s per strategy)
- Metrics extraction: <1 second total
- Classification: <1 second total
- Report generation: <1 second total
- **Bottleneck**: Strategy execution (99% of time)

## Versioning

**Current Version**: Phase 2 (v2.0)

**Compatibility**:
- Python: 3.8+
- finlab: Latest version (tested with finlab API 2023+)
- Dependencies: pandas, numpy, multiprocessing (stdlib)

## Import Paths

```python
# BacktestExecutor
from src.backtest.executor import BacktestExecutor, ExecutionResult

# MetricsExtractor
from src.backtest.metrics import (
    MetricsExtractor,
    StrategyMetrics,
    calculate_max_drawdown,
    calculate_calmar_ratio
)

# SuccessClassifier
from src.backtest.classifier import (
    SuccessClassifier,
    ClassificationResult
)

# ErrorClassifier
from src.backtest.error_classifier import (
    ErrorClassifier,
    ErrorCategory,
    ErrorPattern
)

# ResultsReporter
from src.backtest.reporter import (
    ResultsReporter,
    ReportMetrics
)

# Phase2TestRunner
from run_phase2_backtest_execution import Phase2TestRunner
```

## Related Documentation

- **Execution Framework**: `docs/PHASE2_EXECUTION_FRAMEWORK.md`
- **Code Review**: `docs/PHASE2_CODE_REVIEW.md`
- **Test Results**: `phase2_backtest_results.json`, `phase2_backtest_results.md`
