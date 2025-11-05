# Structured Logging Quick Reference

One-page guide for using JSON structured logging in the trading system.

## Setup

```python
from src.utils.json_logger import get_event_logger

# Initialize logger (once per component)
event_logger = get_event_logger(
    logger_name=__name__,
    log_file="my_component.json.log"
)
```

## Common Events

### Iteration Events

```python
# Start
event_logger.log_iteration_start(
    iteration_num=42,
    model="google/gemini-2.5-flash",
    max_iterations=100,
    has_champion=True
)

# End
event_logger.log_iteration_end(
    iteration_num=42,
    success=True,
    validation_passed=True,
    execution_success=True,
    duration_seconds=125.7,
    metrics={"sharpe_ratio": 2.5}
)

# Failure
event_logger.log_iteration_failure(
    iteration_num=42,
    failure_stage="validation",  # "generation", "validation", "execution"
    error_message="Validation failed",
    error_type="ValidationError"
)
```

### Champion Events

```python
# Update
event_logger.log_champion_update(
    iteration_num=42,
    old_sharpe=2.5,
    new_sharpe=2.8,
    improvement_pct=12.0,
    threshold_type="relative",  # "relative", "absolute", "initial"
    multi_objective_passed=True
)

# Rejection
event_logger.log_champion_rejected(
    iteration_num=42,
    candidate_sharpe=2.3,
    champion_sharpe=2.5,
    rejection_reason="Below 3% threshold"
)

# Demotion
event_logger.log_champion_demotion(
    old_iteration=6,
    new_iteration=54,
    old_sharpe=2.47,
    new_sharpe=2.15,
    demotion_reason="Champion stale"
)
```

### Metric Events

```python
event_logger.log_metric_extraction(
    iteration_num=42,
    method_used="DIRECT",  # "DIRECT", "SIGNAL", "DEFAULT"
    success=True,
    duration_ms=45.3,
    metrics={"sharpe_ratio": 2.5},
    fallback_attempts=0
)
```

### Validation Events

```python
event_logger.log_validation_result(
    iteration_num=42,
    validator_name="MetricValidator",
    passed=True,
    checks_performed=["sharpe_cross_validation", "impossible_combinations"],
    failures=[],
    warnings=[],
    duration_ms=12.4
)
```

### Template Events

```python
# Recommendation
event_logger.log_template_recommendation(
    iteration_num=42,
    template_name="momentum_value_hybrid",
    exploration_mode=False,
    confidence_score=0.85
)

# Instantiation
event_logger.log_template_instantiation(
    iteration_num=42,
    template_name="momentum_value_hybrid",
    success=True,
    retry_count=0
)
```

### Custom Events

```python
event_logger.log_event(
    logging.INFO,
    "custom_event_type",
    "Human-readable message",
    custom_field_1="value1",
    custom_field_2=42
)
```

## Query Logs

```bash
# Basic queries
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --event-type iteration_start

# Filter by iteration
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --iteration 42

# Time range
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --since 2025-10-15

# Custom filters
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --filter passed=false

# Aggregate
python scripts/log_analysis/query_logs.py \
    --log-file logs/iterations.json.log \
    --aggregate-by event_type
```

## Analyze Performance

```bash
python scripts/log_analysis/analyze_performance.py \
    --log-file logs/iterations.json.log \
    --report summary
```

## Log Output Format

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

## Best Practices

### ✅ Do

- Use standard event types for common operations
- Include `iteration_num` in all iteration-related events
- Log timing information (`duration_ms`, `duration_seconds`)
- Include error details (`error_message`, `error_type`)
- Use structured fields instead of embedding data in messages

### ❌ Don't

- Log sensitive data (API keys, credentials, PII)
- Embed structured data in message strings
- Log raw strategy code (use hashes instead)
- Skip error context in failure events

## Common Patterns

### Pattern 1: Iteration Lifecycle

```python
start_time = time.time()

event_logger.log_iteration_start(iteration_num, model, max_iterations, has_champion)

try:
    # ... iteration logic ...

    duration = time.time() - start_time
    event_logger.log_iteration_end(iteration_num, True, True, True, duration, metrics)

except Exception as e:
    event_logger.log_iteration_failure(iteration_num, "execution", str(e), type(e).__name__)
    raise
```

### Pattern 2: Champion Update with Multi-Objective

```python
if should_update_champion(new_sharpe, champion_sharpe):
    validation_result = validate_multi_objective(new_metrics, champion_metrics)

    if validation_result['passed']:
        event_logger.log_champion_update(
            iteration_num, champion_sharpe, new_sharpe, improvement_pct,
            threshold_type, multi_objective_passed=True
        )
        update_champion(new_strategy)
    else:
        event_logger.log_champion_rejected(
            iteration_num, new_sharpe, champion_sharpe,
            f"Multi-objective failed: {validation_result['failed_criteria']}"
        )
```

### Pattern 3: Metric Extraction with Fallback

```python
start_time = time.time()
method = "DIRECT"
fallback_attempts = 0

try:
    metrics = extract_direct(report)
except Exception:
    method = "SIGNAL"
    fallback_attempts = 1
    try:
        metrics = extract_signal(strategy)
    except Exception:
        method = "DEFAULT"
        fallback_attempts = 2
        metrics = get_default_metrics()

duration_ms = (time.time() - start_time) * 1000

event_logger.log_metric_extraction(
    iteration_num, method, True, duration_ms, metrics, fallback_attempts
)
```

### Pattern 4: Validation with Timing

```python
start_time = time.time()
checks = ["check1", "check2", "check3"]
failures = []
warnings = []

# Perform validation checks
for check in checks:
    if not perform_check(check):
        failures.append(f"{check} failed")

duration_ms = (time.time() - start_time) * 1000
passed = len(failures) == 0

event_logger.log_validation_result(
    iteration_num, "MyValidator", passed, checks, failures, warnings, duration_ms
)
```

## See Also

- **Full Documentation**: `docs/LOGGING.md`
- **Analysis Tools**: `scripts/log_analysis/README.md`
- **Integration Example**: `examples/logging_integration_example.py`
- **Implementation**: `src/utils/json_logger.py`
