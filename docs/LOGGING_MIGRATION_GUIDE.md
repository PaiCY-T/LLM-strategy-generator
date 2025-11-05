# Structured Logging Migration Guide

Guide for integrating JSON structured logging into existing components.

## Overview

This guide provides step-by-step instructions for migrating existing components from basic Python logging to structured JSON logging.

## Migration Checklist

- [ ] Import EventLogger
- [ ] Initialize logger in `__init__`
- [ ] Replace key logging calls with structured events
- [ ] Test log output
- [ ] Update component documentation
- [ ] Add log analysis to monitoring

## Component Priority

### High Priority (Core System)

1. **autonomous_loop.py** - Iteration lifecycle tracking
2. **performance_attributor.py** - Metric extraction events
3. **iteration_engine.py** - Execution tracking

### Medium Priority (Validation)

4. **metric_validator.py** - Metric validation events
5. **semantic_validator.py** - Semantic validation events
6. **preservation_validator.py** - Preservation validation events
7. **template_validator.py** - Template validation events
8. **parameter_validator.py** - Parameter validation events

### Low Priority (Supporting)

9. **champion management** - Champion update events
10. **template integration** - Template recommendation/instantiation
11. **feedback system** - Feedback generation events

## Step-by-Step Migration

### Step 1: Import and Initialize

**Before**:
```python
import logging

class AutonomousLoop:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
```

**After**:
```python
import logging
from src.utils.json_logger import get_event_logger

class AutonomousLoop:
    def __init__(self):
        # Keep existing logger for backward compatibility
        self.logger = logging.getLogger(__name__)

        # Add event logger for structured logging
        self.event_logger = get_event_logger(
            logger_name=__name__,
            log_file="autonomous_loop.json.log"
        )
```

### Step 2: Migrate Key Events

#### Example 1: Iteration Start

**Before**:
```python
print(f"\n{'='*60}")
print(f"ITERATION {iteration_num}")
print(f"{'='*60}\n")
logger.info(f"Starting iteration {iteration_num}")
```

**After**:
```python
print(f"\n{'='*60}")
print(f"ITERATION {iteration_num}")
print(f"{'='*60}\n")

# Add structured logging
self.event_logger.log_iteration_start(
    iteration_num=iteration_num,
    model=self.model,
    max_iterations=self.max_iterations,
    has_champion=self.champion is not None
)
```

#### Example 2: Champion Update

**Before**:
```python
logger.info(
    f"Champion updated: Iteration {iteration_num}, "
    f"Sharpe {champion_sharpe:.4f} → {current_sharpe:.4f} "
    f"(+{improvement_pct:.1f}%)"
)
```

**After**:
```python
# Keep existing log for backward compatibility
logger.info(
    f"Champion updated: Iteration {iteration_num}, "
    f"Sharpe {champion_sharpe:.4f} → {current_sharpe:.4f} "
    f"(+{improvement_pct:.1f}%)"
)

# Add structured logging
self.event_logger.log_champion_update(
    iteration_num=iteration_num,
    old_sharpe=champion_sharpe,
    new_sharpe=current_sharpe,
    improvement_pct=improvement_pct,
    threshold_type=threshold_type,
    multi_objective_passed=validation_result['passed']
)
```

#### Example 3: Validation Result

**Before**:
```python
if not is_valid:
    logger.error(f"Validation failed: {', '.join(errors)}")
else:
    logger.info("Validation passed")
```

**After**:
```python
# Keep existing log
if not is_valid:
    logger.error(f"Validation failed: {', '.join(errors)}")
else:
    logger.info("Validation passed")

# Add structured logging
self.event_logger.log_validation_result(
    iteration_num=iteration_num,
    validator_name=self.__class__.__name__,
    passed=is_valid,
    checks_performed=self.checks,
    failures=errors,
    warnings=warnings,
    duration_ms=duration_ms
)
```

### Step 3: Add Performance Timing

**Pattern**:
```python
import time

start_time = time.time()

try:
    # ... operation ...

    duration = time.time() - start_time
    self.event_logger.log_performance_metric(
        operation="metric_extraction",
        duration_ms=duration * 1000,
        details={"method": method_used}
    )

except Exception as e:
    duration = time.time() - start_time
    self.event_logger.log_event(
        logging.ERROR,
        "operation_failure",
        f"Operation failed: {str(e)}",
        operation="metric_extraction",
        duration_ms=duration * 1000,
        error_type=type(e).__name__
    )
    raise
```

### Step 4: Test Integration

#### Create Test Script

```python
# test_structured_logging.py
import sys
import json
from pathlib import Path

def test_component_logging(component_name, log_file):
    """Test that component generates valid structured logs."""
    log_path = Path(f"logs/{log_file}")

    if not log_path.exists():
        print(f"✗ Log file not found: {log_path}")
        return False

    # Read and validate JSON logs
    with open(log_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())

                # Validate required fields
                required = ['timestamp', 'level', 'logger', 'message', 'event_type']
                missing = [field for field in required if field not in entry]

                if missing:
                    print(f"✗ Line {i}: Missing fields: {missing}")
                    return False

            except json.JSONDecodeError as e:
                print(f"✗ Line {i}: Invalid JSON: {e}")
                return False

    print(f"✓ {component_name} logging validated")
    return True

if __name__ == "__main__":
    test_component_logging("AutonomousLoop", "autonomous_loop.json.log")
```

## Component-Specific Migrations

### autonomous_loop.py

**Key Events to Migrate**:

1. **Iteration Start** (line ~183)
   ```python
   self.event_logger.log_iteration_start(
       iteration_num, self.model, self.max_iterations, self.champion is not None
   )
   ```

2. **Iteration End** (line ~538)
   ```python
   self.event_logger.log_iteration_end(
       iteration_num, success, is_valid, execution_success, duration, metrics
   )
   ```

3. **Champion Update** (line ~735)
   ```python
   self.event_logger.log_champion_update(
       iteration_num, champion_sharpe, current_sharpe, improvement_pct,
       threshold_type, validation_result['passed']
   )
   ```

4. **Champion Rejection** (line ~715)
   ```python
   self.event_logger.log_champion_rejected(
       iteration_num, current_sharpe, champion_sharpe,
       f"Failed multi-objective: {', '.join(validation_result['failed_criteria'])}"
   )
   ```

5. **Champion Demotion** (line ~520)
   ```python
   self.event_logger.log_champion_demotion(
       old_champion_iteration, new_champion_iteration,
       old_champion_sharpe, new_champion_sharpe,
       staleness_result['reason']
   )
   ```

### performance_attributor.py

**Key Events to Migrate**:

1. **Metric Extraction** (new function)
   ```python
   def log_metric_extraction(
       self,
       iteration_num: int,
       method: str,
       duration_ms: float,
       metrics: Dict[str, float]
   ):
       self.event_logger.log_metric_extraction(
           iteration_num, method, True, duration_ms, metrics, 0
       )
   ```

### Validators (metric_validator.py, semantic_validator.py, etc.)

**Pattern**:
```python
class MetricValidator:
    def __init__(self):
        self.event_logger = get_event_logger(
            logger_name=__name__,
            log_file="metric_validator.json.log"
        )

    def validate_metrics(self, iteration_num, metrics, report):
        start_time = time.time()

        checks = ["sharpe_cross_validation", "impossible_combinations"]
        errors = []
        warnings = []

        # Perform validation...

        duration_ms = (time.time() - start_time) * 1000
        is_valid = len(errors) == 0

        self.event_logger.log_validation_result(
            iteration_num, "MetricValidator", is_valid,
            checks, errors, warnings, duration_ms
        )

        return is_valid, errors
```

## Backward Compatibility

### Keep Existing Logs

Maintain existing logging calls during migration for backward compatibility:

```python
# Existing logging (keep)
logger.info(f"Champion updated: {iteration_num}")
print("✓ Champion updated")

# New structured logging (add)
self.event_logger.log_champion_update(...)
```

### Gradual Rollout

1. **Phase 1**: Add structured logging alongside existing logs
2. **Phase 2**: Monitor structured logs in production
3. **Phase 3**: Gradually remove redundant print statements
4. **Phase 4**: Deprecate basic logging in favor of structured logging

## Monitoring Integration

### Add to System Monitoring

```python
# monitoring/log_monitor.py
from src.utils.json_logger import EventLogger
import schedule
import time

def check_error_rate():
    """Monitor error rate from structured logs."""
    # Query logs for errors in last hour
    errors = query_logs(
        log_file="logs/autonomous_loop.json.log",
        level="ERROR",
        since=datetime.now() - timedelta(hours=1)
    )

    if len(errors) > 10:
        alert("High error rate detected", errors)

schedule.every(10).minutes.do(check_error_rate)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Testing Checklist

After migration, verify:

- [ ] Log files created in `logs/` directory
- [ ] JSON format is valid (use `python -m json.tool`)
- [ ] All required fields present (timestamp, level, event_type, etc.)
- [ ] Query tools work with new logs
- [ ] Performance analysis generates reports
- [ ] No regressions in existing functionality
- [ ] Log rotation works correctly

## Common Pitfalls

### 1. Missing iteration_num

**Problem**: Events logged without iteration number
```python
# ✗ Bad
self.event_logger.log_validation_result(
    validator_name="MetricValidator",
    passed=True,
    ...
)
```

**Solution**: Always include iteration_num
```python
# ✓ Good
self.event_logger.log_validation_result(
    iteration_num=iteration_num,  # Add this
    validator_name="MetricValidator",
    passed=True,
    ...
)
```

### 2. Timing Without try/finally

**Problem**: Duration not logged on exception
```python
# ✗ Bad
start_time = time.time()
result = operation()
duration = time.time() - start_time
log_event(..., duration_ms=duration)
```

**Solution**: Use try/finally or context manager
```python
# ✓ Good
start_time = time.time()
try:
    result = operation()
finally:
    duration = time.time() - start_time
    log_event(..., duration_ms=duration)
```

### 3. Forgetting Context

**Problem**: Missing important context fields
```python
# ✗ Bad
self.event_logger.log_event(
    logging.ERROR,
    "validation_failure",
    "Validation failed"
)
```

**Solution**: Include context fields
```python
# ✓ Good
self.event_logger.log_event(
    logging.ERROR,
    "validation_failure",
    "Validation failed",
    iteration_num=iteration_num,
    validator_name=self.__class__.__name__,
    failure_count=len(errors)
)
```

## Rollback Plan

If issues arise during migration:

1. **Disable structured logging** while keeping existing logs
   ```python
   # Temporarily comment out event logger calls
   # self.event_logger.log_iteration_start(...)
   ```

2. **Investigate issues** using existing logs

3. **Fix problems** and re-enable structured logging

4. **Verify** log output before full deployment

## Support

- **Documentation**: `docs/LOGGING.md`
- **Quick Reference**: `docs/LOGGING_QUICK_REFERENCE.md`
- **Examples**: `examples/logging_integration_example.py`
- **Implementation**: `src/utils/json_logger.py`

## Completion Criteria

Migration is complete when:

✅ All high-priority components have structured logging
✅ Log files are being created and rotated properly
✅ Query and analysis tools work with production logs
✅ Monitoring dashboards use structured log data
✅ No regressions in system functionality
✅ Team is trained on new logging system
