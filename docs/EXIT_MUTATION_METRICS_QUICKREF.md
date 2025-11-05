# Exit Mutation Metrics - Quick Reference

**Task**: 3.2 - Exit Mutation Metrics Tracking
**Status**: Production Ready ✅

---

## Quick Usage

### Basic Recording

```python
from src.monitoring.metrics_collector import MetricsCollector

collector = MetricsCollector()

# Record successful mutation
collector.record_exit_mutation(success=True, duration=0.254)

# Record failed mutation
collector.record_exit_mutation(success=False, duration=0.180)
```

### Get Statistics

```python
stats = collector.get_exit_mutation_statistics()

print(f"Total: {stats['total']}")
print(f"Success Rate: {stats['success_percentage']:.1f}%")
print(f"Avg Duration: {stats['avg_duration_seconds']*1000:.2f}ms")
```

### Prometheus Export

```python
metrics = collector.export_prometheus()
print(metrics)  # Ready for Prometheus scraping
```

---

## Available Metrics

| Metric | Type | Description | Unit |
|--------|------|-------------|------|
| `exit_mutations_total` | Counter | Total mutations attempted | count |
| `exit_mutations_success` | Counter | Successful mutations | count |
| `exit_mutation_success_rate` | Gauge | Success rate | 0.0-1.0 |
| `exit_mutation_duration_seconds` | Histogram | Mutation latency | seconds |

---

## Statistics Fields

```python
{
    "total": 50,                          # Total mutations
    "successes": 39,                      # Successful mutations
    "failures": 11,                       # Failed mutations
    "success_rate": 0.78,                 # 0.0-1.0
    "success_percentage": 78.0,           # 0-100
    "avg_duration_seconds": 0.308,        # Average
    "recent_avg_duration_seconds": 0.262, # Last 10
    "duration_statistics": {
        "min": 0.105,
        "max": 0.498,
        "p50": 0.319,  # Median
        "p95": 0.479,
        "p99": 0.495
    },
    "total_duration_samples": 50
}
```

---

## Integration with ExitMutationLogger

```python
from src.mutation.exit_mutation_logger import ExitMutationLogger

# Logger automatically calls collector.record_exit_mutation()
logger = ExitMutationLogger(metrics_collector=collector)

logger.log_mutation(
    parameter="stop_loss_pct",
    old_value=0.10,
    new_value=0.12,
    clamped=False,
    success=True,
    validation_passed=True,
    duration=0.254  # Automatically recorded to metrics
)
```

---

## Monitoring Alerts (Example)

### Prometheus Alert Rules

```yaml
groups:
  - name: exit_mutations
    rules:
      # Alert on low success rate
      - alert: ExitMutationLowSuccessRate
        expr: exit_mutation_success_rate < 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Exit mutation success rate below 50%"

      # Alert on high latency
      - alert: ExitMutationHighLatency
        expr: exit_mutation_duration_seconds > 1.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Exit mutation latency above 1 second"
```

---

## Grafana Dashboard (Example Queries)

```promql
# Success rate over time
exit_mutation_success_rate

# Mutations per minute
rate(exit_mutations_total[1m])

# Success rate percentage
exit_mutation_success_rate * 100

# Average duration in milliseconds
exit_mutation_duration_seconds * 1000

# Success vs Failure
exit_mutations_success / exit_mutations_total
```

---

## Performance

- **Recording overhead**: < 1ms per mutation
- **Memory usage**: Minimal (last 100 values)
- **Thread-safe**: Yes
- **Buffered logging**: Yes (10 entries default)

---

## Files

- **Metrics**: `src/monitoring/metrics_collector.py`
- **Logger**: `src/mutation/exit_mutation_logger.py`
- **Operator**: `src/mutation/unified_mutation_operator.py`
- **Tests**: `tests/monitoring/test_metrics_collector.py`
- **Demo**: `examples/exit_mutation_metrics_demo.py`

---

## Troubleshooting

### Metrics not updating

Check that MetricsCollector is passed to ExitMutationLogger:

```python
# Correct
logger = ExitMutationLogger(metrics_collector=collector)

# Wrong - metrics won't be recorded
logger = ExitMutationLogger()
```

### Duration not tracked

Ensure duration parameter is passed:

```python
# Correct
collector.record_exit_mutation(success=True, duration=0.254)

# Works but no duration stats
collector.record_exit_mutation(success=True)
```

### Statistics showing zero

Ensure mutations have been recorded:

```python
stats = collector.get_exit_mutation_statistics()
if stats['total'] == 0:
    print("No mutations recorded yet")
```

---

## See Also

- [Full Implementation Report](../TASK_3.2_EXIT_MUTATION_METRICS_COMPLETE.md)
- [Exit Mutation Redesign Spec](../.spec-workflow/specs/exit-mutation-redesign/design.md)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/naming/)
