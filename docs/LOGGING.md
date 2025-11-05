  # Structured Logging Guide

**Version**: 1.0
**Last Updated**: 2025-10-16
**Status**: Production Ready

## Overview

This document describes the structured logging infrastructure for the Finlab Trading System. All components use JSON-formatted logs for machine-parseable output that integrates with log aggregation tools (ELK, Splunk, CloudWatch, etc.).

## Table of Contents

1. [Quick Start](#quick-start)
2. [Log Event Schemas](#log-event-schemas)
3. [Usage Examples](#usage-examples)
4. [Log Analysis](#log-analysis)
5. [Configuration](#configuration)
6. [Integration Guide](#integration-guide)
7. [Best Practices](#best-practices)

---

## Quick Start

### Basic Usage

```python
from src.utils.json_logger import get_event_logger

# Create event logger
logger = get_event_logger("my_module", log_file="my_module.json.log")

# Log structured events
logger.log_iteration_start(
    iteration_num=1,
    model="google/gemini-2.5-flash",
    max_iterations=100,
    has_champion=False
)
```

### Example Log Output

```json
{
  "timestamp": "2025-10-16T14:30:45.123456",
  "level": "INFO",
  "logger": "autonomous_loop",
  "message": "Starting iteration 1/100",
  "hostname": "trading-server-1",
  "process_id": 12345,
  "thread_id": 67890,
  "thread_name": "MainThread",
  "module": "autonomous_loop",
  "function": "run_iteration",
  "line": 185,
  "event_type": "iteration_start",
  "iteration_num": 1,
  "model": "google/gemini-2.5-flash",
  "max_iterations": 100,
  "has_champion": false
}
```

---

## Log Event Schemas

### 1. Iteration Events

#### `iteration_start`

Logged when an iteration begins.

**Fields**:
- `iteration_num` (int): Current iteration number
- `model` (str): LLM model being used
- `max_iterations` (int): Total iterations planned
- `has_champion` (bool): Whether a champion exists

**Example**:
```python
logger.log_iteration_start(
    iteration_num=42,
    model="google/gemini-2.5-flash",
    max_iterations=100,
    has_champion=True
)
```

#### `iteration_end`

Logged when an iteration completes.

**Fields**:
- `iteration_num` (int): Completed iteration number
- `success` (bool): Overall success (validation AND execution)
- `validation_passed` (bool): Code validation result
- `execution_success` (bool): Strategy execution result
- `duration_seconds` (float): Total iteration time
- `metrics` (dict, optional): Performance metrics

**Example**:
```python
logger.log_iteration_end(
    iteration_num=42,
    success=True,
    validation_passed=True,
    execution_success=True,
    duration_seconds=125.7,
    metrics={"sharpe_ratio": 2.5, "annual_return": 0.35}
)
```

#### `iteration_failure`

Logged when an iteration fails.

**Fields**:
- `iteration_num` (int): Failed iteration number
- `failure_stage` (str): Where failure occurred ("generation", "validation", "execution")
- `error_message` (str): Error description
- `error_type` (str, optional): Error class name

**Example**:
```python
logger.log_iteration_failure(
    iteration_num=42,
    failure_stage="validation",
    error_message="AST validation failed: undefined variable 'close'",
    error_type="ValidationError"
)
```

### 2. Champion Events

#### `champion_update`

Logged when a new champion is established.

**Fields**:
- `iteration_num` (int): Iteration that produced new champion
- `old_sharpe` (float, nullable): Previous champion Sharpe ratio
- `new_sharpe` (float): New champion Sharpe ratio
- `improvement_pct` (float): Percentage improvement
- `threshold_type` (str): "relative", "absolute", or "initial"
- `multi_objective_passed` (bool): Multi-objective validation result

**Example**:
```python
logger.log_champion_update(
    iteration_num=42,
    old_sharpe=2.5,
    new_sharpe=2.8,
    improvement_pct=12.0,
    threshold_type="relative",
    multi_objective_passed=True
)
```

#### `champion_rejected`

Logged when a champion update is rejected.

**Fields**:
- `iteration_num` (int): Iteration number
- `candidate_sharpe` (float): Candidate strategy Sharpe
- `champion_sharpe` (float): Current champion Sharpe
- `rejection_reason` (str): Why update was rejected

**Example**:
```python
logger.log_champion_rejected(
    iteration_num=42,
    candidate_sharpe=2.3,
    champion_sharpe=2.5,
    rejection_reason="Below 3% improvement threshold"
)
```

#### `champion_demotion`

Logged when a champion is demoted due to staleness.

**Fields**:
- `old_iteration` (int): Demoted champion iteration
- `new_iteration` (int): New champion iteration
- `old_sharpe` (float): Demoted champion Sharpe
- `new_sharpe` (float): New champion Sharpe
- `demotion_reason` (str): Reason for demotion

**Example**:
```python
logger.log_champion_demotion(
    old_iteration=6,
    new_iteration=54,
    old_sharpe=2.47,
    new_sharpe=2.15,
    demotion_reason="Champion stale: Sharpe 2.47 < cohort median 2.52"
)
```

### 3. Metric Extraction Events

#### `metric_extraction`

Logged when metrics are extracted from backtest results.

**Fields**:
- `iteration_num` (int): Iteration number
- `method_used` (str): "DIRECT", "SIGNAL", or "DEFAULT"
- `success` (bool): Whether extraction succeeded
- `duration_ms` (float): Extraction time in milliseconds
- `metrics` (dict, optional): Extracted metrics
- `fallback_attempts` (int): Number of fallback attempts

**Example**:
```python
logger.log_metric_extraction(
    iteration_num=42,
    method_used="DIRECT",
    success=True,
    duration_ms=45.3,
    metrics={"sharpe_ratio": 2.5, "annual_return": 0.35},
    fallback_attempts=0
)
```

### 4. Validation Events

#### `validation_result`

Logged when a validation check completes.

**Fields**:
- `iteration_num` (int): Iteration number
- `validator_name` (str): Validator name (e.g., "MetricValidator")
- `passed` (bool): Whether validation passed
- `checks_performed` (list): List of checks executed
- `failures` (list): List of failure messages
- `warnings` (list): List of warning messages
- `duration_ms` (float): Validation time in milliseconds

**Example**:
```python
logger.log_validation_result(
    iteration_num=42,
    validator_name="MetricValidator",
    passed=True,
    checks_performed=["sharpe_cross_validation", "impossible_combinations"],
    failures=[],
    warnings=[],
    duration_ms=12.4
)
```

### 5. Template Integration Events

#### `template_recommendation`

Logged when a template is recommended by the feedback system.

**Fields**:
- `iteration_num` (int): Iteration number
- `template_name` (str): Recommended template
- `exploration_mode` (bool): Whether in exploration mode
- `confidence_score` (float, optional): Recommendation confidence

**Example**:
```python
logger.log_template_recommendation(
    iteration_num=42,
    template_name="momentum_value_hybrid",
    exploration_mode=False,
    confidence_score=0.85
)
```

#### `template_instantiation`

Logged when a template is instantiated.

**Fields**:
- `iteration_num` (int): Iteration number
- `template_name` (str): Template being instantiated
- `success` (bool): Whether instantiation succeeded
- `retry_count` (int): Number of retries attempted
- `error_message` (str, optional): Error if failed

**Example**:
```python
logger.log_template_instantiation(
    iteration_num=42,
    template_name="momentum_value_hybrid",
    success=True,
    retry_count=0
)
```

### 6. Performance Events

#### `performance_metric`

Logged for performance monitoring.

**Fields**:
- `operation` (str): Operation name
- `duration_ms` (float): Duration in milliseconds
- `details` (dict, optional): Additional details

**Example**:
```python
logger.log_performance_metric(
    operation="backtest_execution",
    duration_ms=8523.4,
    details={"strategy_name": "momentum_v5", "data_points": 5040}
)
```

---

## Usage Examples

### Component Integration

#### Autonomous Loop

```python
from src.utils.json_logger import get_event_logger
import time

class AutonomousLoop:
    def __init__(self):
        self.event_logger = get_event_logger(
            "autonomous_loop",
            log_file="iterations.json.log"
        )

    def run_iteration(self, iteration_num: int):
        start_time = time.time()

        # Log iteration start
        self.event_logger.log_iteration_start(
            iteration_num=iteration_num,
            model=self.model,
            max_iterations=self.max_iterations,
            has_champion=self.champion is not None
        )

        try:
            # ... iteration logic ...

            # Log iteration end
            duration = time.time() - start_time
            self.event_logger.log_iteration_end(
                iteration_num=iteration_num,
                success=True,
                validation_passed=True,
                execution_success=True,
                duration_seconds=duration,
                metrics=metrics
            )
        except Exception as e:
            # Log iteration failure
            self.event_logger.log_iteration_failure(
                iteration_num=iteration_num,
                failure_stage="execution",
                error_message=str(e),
                error_type=type(e).__name__
            )
            raise
```

#### Validators

```python
from src.utils.json_logger import get_event_logger
import time

class MetricValidator:
    def __init__(self):
        self.event_logger = get_event_logger(
            "metric_validator",
            log_file="validations.json.log"
        )

    def validate_metrics(self, iteration_num: int, metrics: dict):
        start_time = time.time()

        checks = ["sharpe_cross_validation", "impossible_combinations"]
        failures = []
        warnings = []

        # Perform validation checks
        # ... validation logic ...

        duration_ms = (time.time() - start_time) * 1000
        passed = len(failures) == 0

        # Log validation result
        self.event_logger.log_validation_result(
            iteration_num=iteration_num,
            validator_name="MetricValidator",
            passed=passed,
            checks_performed=checks,
            failures=failures,
            warnings=warnings,
            duration_ms=duration_ms
        )

        return passed, failures
```

---

## Log Analysis

### Command-Line Query Tool

Query logs using the `query_logs.py` script:

```bash
# Query all iteration events
python scripts/log_analysis/query_logs.py \
    --event-type iteration_start \
    --log-file logs/iterations.json.log

# Query champion updates in time range
python scripts/log_analysis/query_logs.py \
    --event-type champion_update \
    --since 2025-10-15 \
    --log-file logs/iterations.json.log

# Query errors for specific iteration
python scripts/log_analysis/query_logs.py \
    --level ERROR \
    --iteration 42 \
    --log-file logs/iterations.json.log

# Query validation failures
python scripts/log_analysis/query_logs.py \
    --event-type validation_result \
    --filter passed=false \
    --log-file logs/iterations.json.log

# Aggregate by event type
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --aggregate-by event_type
```

### Performance Analysis Tool

Analyze system performance using `analyze_performance.py`:

```bash
# Generate summary report
python scripts/log_analysis/analyze_performance.py \
    --log-file logs/iterations.json.log \
    --report summary

# Save detailed report to file
python scripts/log_analysis/analyze_performance.py \
    --log-file logs/iterations.json.log \
    --report detailed \
    --output performance_report.txt
```

### Common Query Patterns

#### Find all failed iterations
```bash
python scripts/log_analysis/query_logs.py \
    --event-type iteration_failure \
    --log-file logs/iterations.json.log \
    --format compact
```

#### Track champion update frequency
```bash
python scripts/log_analysis/query_logs.py \
    --event-type champion_update \
    --log-file logs/iterations.json.log \
    --aggregate-by threshold_type
```

#### Identify slow metric extractions
```bash
python scripts/log_analysis/query_logs.py \
    --event-type metric_extraction \
    --log-file logs/iterations.json.log \
    --format json | jq 'select(.duration_ms > 100)'
```

#### Monitor validation pass rates
```bash
python scripts/log_analysis/query_logs.py \
    --event-type validation_result \
    --log-file logs/iterations.json.log \
    --aggregate-by validator_name
```

---

## Configuration

### Log File Management

Logs are automatically rotated when they reach the configured size:

```python
from src.utils.json_logger import get_event_logger

logger = get_event_logger(
    logger_name="my_component",
    log_file="my_component.json.log",
    log_level=logging.INFO,
    log_dir=Path("./logs"),
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10  # Keep 10 backup files
)
```

### Log Levels

Standard Python logging levels:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

### Custom Fields

Add custom fields to any log event:

```python
logger.log_event(
    logging.INFO,
    "custom_event",
    "Custom message",
    custom_field_1="value1",
    custom_field_2=42,
    custom_dict={"key": "value"}
)
```

---

## Integration Guide

### Step 1: Import the Logger

```python
from src.utils.json_logger import get_event_logger
```

### Step 2: Initialize Logger

```python
class MyComponent:
    def __init__(self):
        self.event_logger = get_event_logger(
            logger_name=__name__,
            log_file="my_component.json.log"
        )
```

### Step 3: Log Events

Use the appropriate event method for your event type:

```python
# Iteration events
self.event_logger.log_iteration_start(...)
self.event_logger.log_iteration_end(...)
self.event_logger.log_iteration_failure(...)

# Champion events
self.event_logger.log_champion_update(...)
self.event_logger.log_champion_rejected(...)

# Metric events
self.event_logger.log_metric_extraction(...)

# Validation events
self.event_logger.log_validation_result(...)

# Custom events
self.event_logger.log_event(level, event_type, message, **kwargs)
```

### Step 4: Query Logs

Use the query tools to analyze logs:

```bash
python scripts/log_analysis/query_logs.py --log-file logs/my_component.json.log
```

---

## Best Practices

### 1. Use Appropriate Event Types

Always use the standard event types when logging common operations:
- Iteration events for loop operations
- Champion events for champion updates
- Metric events for performance measurements
- Validation events for validation checks

### 2. Include Context

Always include relevant context in log events:
- `iteration_num` for tracking iteration progress
- `duration_ms` or `duration_seconds` for performance monitoring
- Error details (`error_message`, `error_type`) for debugging

### 3. Log at Appropriate Levels

- `INFO`: Normal operation events (iteration start, champion update)
- `WARNING`: Degraded performance or recoverable errors
- `ERROR`: Failures that prevent normal operation
- `DEBUG`: Detailed diagnostic information

### 4. Avoid Logging Sensitive Data

Never log sensitive information:
- API keys or credentials
- Personal identifiable information (PII)
- Raw strategy code (use hashes instead)

### 5. Use Structured Fields

Prefer structured fields over embedding data in messages:

**Good**:
```python
logger.log_event(
    logging.INFO,
    "backtest_complete",
    "Backtest completed successfully",
    sharpe_ratio=2.5,
    duration_seconds=125.7
)
```

**Bad**:
```python
logger.log_event(
    logging.INFO,
    "backtest_complete",
    f"Backtest completed: Sharpe={2.5}, Duration={125.7}s"
)
```

### 6. Monitor Log Volume

Monitor log file sizes and adjust rotation settings:
- High-frequency events → Smaller max_bytes, more backups
- Low-frequency events → Larger max_bytes, fewer backups

### 7. Test Log Integration

Always test log integration in development:

```python
def test_logging():
    logger = get_event_logger("test", log_file="test.json.log")
    logger.log_iteration_start(
        iteration_num=1,
        model="test_model",
        max_iterations=1,
        has_champion=False
    )

    # Verify log file exists and contains valid JSON
    log_file = Path("logs/test.json.log")
    assert log_file.exists()

    with open(log_file) as f:
        entry = json.loads(f.readline())
        assert entry["event_type"] == "iteration_start"
```

---

## Troubleshooting

### Log File Not Created

**Symptom**: Log file doesn't appear in logs/ directory

**Solution**: Check directory permissions and verify log_dir exists:
```python
from pathlib import Path
log_dir = Path("./logs")
log_dir.mkdir(parents=True, exist_ok=True)
```

### Invalid JSON in Logs

**Symptom**: Query tools fail with JSON decode errors

**Solution**: Check for exceptions during logging. The JSON formatter handles most edge cases, but ensure custom fields are JSON-serializable.

### High Log Volume

**Symptom**: Log files growing too fast

**Solution**:
1. Increase `max_bytes` for rotation
2. Reduce log level from DEBUG to INFO
3. Use separate log files for high-frequency components

### Missing Events

**Symptom**: Expected events not appearing in logs

**Solution**: Verify logger is initialized and event methods are called with correct parameters. Check log level configuration.

---

## References

- **Implementation**: `src/utils/json_logger.py`
- **Query Tool**: `scripts/log_analysis/query_logs.py`
- **Analysis Tool**: `scripts/log_analysis/analyze_performance.py`
- **Task Specification**: `.spec-workflow/specs/system-fix-validation-enhancement/tasks.md` (Task 98)

---

## Changelog

### v1.0 (2025-10-16)
- Initial implementation
- Standard event schemas for iterations, champions, metrics, validations, templates
- Query and analysis tools
- Documentation and examples
