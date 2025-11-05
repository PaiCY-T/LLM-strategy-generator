# Monitoring Quick Start Guide

**5-Minute Integration Guide**

---

## 1. Import and Initialize (30 seconds)

```python
from src.monitoring.metrics_collector import MetricsCollector

# Initialize collector
collector = MetricsCollector(history_window=100)
```

---

## 2. Basic Recording (2 minutes)

### In Your Iteration Loop

```python
# Start of iteration
collector.record_iteration_start(iteration_num)

# After generation
collector.record_generation_time(duration)

# After validation
collector.record_validation_result(passed=is_valid)

# After execution
collector.record_execution_result(success=execution_success)

# After successful iteration
collector.record_iteration_success(
    sharpe_ratio=metrics['sharpe_ratio'],
    duration=total_duration
)

# After champion update
if champion_updated:
    collector.record_champion_update(
        old_sharpe=old_sharpe,
        new_sharpe=new_sharpe,
        iteration_num=iteration_num
    )
else:
    collector.record_champion_age_increment()
```

---

## 3. Export Metrics (1 minute)

### Prometheus Format (for Grafana)

```python
# Every 10 iterations
if iteration_num % 10 == 0:
    prometheus_text = collector.export_prometheus()
    with open('metrics.txt', 'w') as f:
        f.write(prometheus_text)
```

### JSON Format (for logging)

```python
json_text = collector.export_json(include_history=True)
with open('metrics.json', 'w') as f:
    f.write(json_text)
```

### Quick Summary

```python
summary = collector.get_summary()
print(f"Success Rate: {summary['learning']['success_rate']:.1f}%")
print(f"Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
```

---

## 4. Serve Metrics for Prometheus (1 minute)

```python
# Create simple HTTP server
from flask import Flask, Response

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(
        collector.export_prometheus(),
        mimetype='text/plain'
    )

app.run(host='0.0.0.0', port=9090)
```

---

## 5. View in Grafana (30 seconds)

1. Start Prometheus: `prometheus --config.file=prometheus.yml`
2. Import dashboard: `config/grafana_dashboard.json`
3. View metrics at `http://localhost:3000`

---

## Common Patterns

### Pattern 1: Full Iteration Tracking

```python
start = time.time()

collector.record_iteration_start(iteration_num)

# ... generation ...
collector.record_generation_time(time.time() - gen_start)

# ... validation ...
collector.record_validation_result(passed=is_valid)

# ... execution ...
collector.record_execution_result(success=success)

# ... success ...
collector.record_iteration_success(
    sharpe_ratio=sharpe,
    duration=time.time() - start
)
```

### Pattern 2: Error Tracking

```python
try:
    # ... iteration logic ...
    collector.record_iteration_success(sharpe, duration)
except ValidationError:
    collector.record_error("validation")
except ExecutionError:
    collector.record_error("execution")
except APIError:
    collector.record_api_call(success=False, retries=2)
```

### Pattern 3: Metric Extraction Tracking

```python
extraction_start = time.time()

# Try DIRECT method
if captured_report:
    metrics = extract_from_report(captured_report)
    method = "DIRECT"
# Try SIGNAL method
elif signal:
    metrics = extract_from_signal(signal)
    method = "SIGNAL"
# Use DEFAULT
else:
    metrics = default_metrics()
    method = "DEFAULT"

collector.record_metric_extraction_time(
    time.time() - extraction_start,
    method=method
)
```

---

## Key Metrics to Monitor

### Learning Health
- **Success Rate** (target: ≥80%)
- **Best Sharpe** (target: ≥2.0)
- **Champion Age** (alert: >100 iterations)

### System Health
- **Validation Pass Rate** (target: ≥90%)
- **Error Rate** (alert: >5 errors/hour)
- **Fallback Usage** (alert: >30%)

### Performance
- **Iteration Duration** (typical: 60-300s)
- **Extraction Method** (prefer: DIRECT >80%)

---

## Troubleshooting

### Problem: Metrics not updating
**Solution**: Verify collector is recording calls
```python
print(f"Total iterations: {collector.metrics['learning_iterations_total'].get_latest()}")
```

### Problem: Prometheus shows no data
**Solution**: Check metrics server is running
```bash
curl http://localhost:9090/metrics
```

### Problem: Grafana panels empty
**Solution**: Verify time range and data source
- Time range: "Last 6 hours"
- Data source: http://localhost:9090

---

## Next Steps

1. **Basic Integration** (5 min): Add `record_iteration_success()` to your loop
2. **Full Integration** (15 min): Add all recording calls
3. **Dashboard Setup** (10 min): Import Grafana dashboard
4. **Alert Setup** (15 min): Configure Prometheus alerts

**Full Documentation**: See `/docs/MONITORING.md`
**Example Code**: See `/examples/monitoring_integration_example.py`
**Tests**: Run `pytest tests/monitoring/test_metrics_collector.py`

---

**Status**: ✅ Task 99 Complete | Production Ready
