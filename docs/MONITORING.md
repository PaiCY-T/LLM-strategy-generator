# Monitoring Dashboard Metrics Documentation

**Task 99: Production Monitoring Infrastructure**
**Status**: ✅ COMPLETE
**Last Updated**: 2025-10-16

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Metric Categories](#metric-categories)
4. [Metric Definitions](#metric-definitions)
5. [Integration Examples](#integration-examples)
6. [Grafana Dashboard Setup](#grafana-dashboard-setup)
7. [Prometheus Configuration](#prometheus-configuration)
8. [Alerting Rules](#alerting-rules)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The autonomous learning system includes comprehensive production monitoring through the `MetricsCollector` class. Metrics are collected across four dimensions:

1. **Learning Metrics**: Strategy performance, champion tracking, success rates
2. **Performance Metrics**: Execution timing, resource usage
3. **Quality Metrics**: Validation rates, preservation success
4. **System Metrics**: Error tracking, API usage, alerts

All metrics are compatible with industry-standard monitoring tools:
- **Prometheus**: For time-series storage and alerting
- **Grafana**: For visualization dashboards
- **JSON Export**: For custom integrations

---

## Quick Start

### Basic Usage

```python
from src.monitoring.metrics_collector import MetricsCollector

# Initialize collector
collector = MetricsCollector(history_window=100)

# Record iteration start
collector.record_iteration_start(iteration_num=0)

# Record successful iteration
collector.record_iteration_success(
    sharpe_ratio=2.0,
    duration=120.5
)

# Record champion update
collector.record_champion_update(
    old_sharpe=1.8,
    new_sharpe=2.0,
    iteration_num=5
)

# Export metrics
prometheus_metrics = collector.export_prometheus()
json_metrics = collector.export_json(include_history=True)

# Get summary
summary = collector.get_summary()
print(f"Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
```

### Integration with Autonomous Loop

```python
from src.monitoring.metrics_collector import MetricsCollector
from artifacts.working.modules.autonomous_loop import AutonomousLoop

# Initialize loop with metrics collector
loop = AutonomousLoop(model="google/gemini-2.5-flash", max_iterations=10)
collector = MetricsCollector()

# Add collector to loop (in __init__ or run_iteration)
loop.metrics_collector = collector

# In run_iteration method:
def run_iteration(self, iteration_num: int, data):
    start_time = time.time()

    # Record iteration start
    self.metrics_collector.record_iteration_start(iteration_num)

    # ... iteration logic ...

    if is_valid and execution_success:
        duration = time.time() - start_time
        self.metrics_collector.record_iteration_success(
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            duration=duration
        )

    # Record champion updates
    if champion_updated:
        self.metrics_collector.record_champion_update(
            old_sharpe=old_champion_sharpe,
            new_sharpe=new_champion_sharpe,
            iteration_num=iteration_num
        )
```

---

## Metric Categories

### 1. Learning Metrics (learning_*)

Track strategy learning progress and performance:
- Iteration counts (total, successful)
- Success rates (rolling window)
- Sharpe ratios (current, average, best)
- Champion update frequency
- Champion age (iterations since last update)
- Strategy diversity

**Use Cases**:
- Monitor learning convergence
- Track champion stability
- Detect performance degradation
- Measure strategy diversity

### 2. Performance Metrics (performance_*)

Track system execution speed and efficiency:
- Iteration duration (full cycle)
- Generation time (strategy creation)
- Validation time (AST checks)
- Execution time (backtest)
- Metric extraction time
- Extraction method distribution

**Use Cases**:
- Identify performance bottlenecks
- Optimize critical paths
- Monitor resource usage
- Track extraction method effectiveness

### 3. Quality Metrics (quality_*)

Track validation and preservation success:
- Validation pass/fail counts
- Validation pass rate
- Execution success/failure counts
- Preservation validation results
- Suspicious metric detections

**Use Cases**:
- Monitor system reliability
- Track code quality trends
- Detect preservation issues
- Identify systematic failures

### 4. System Metrics (system_*)

Track system health and errors:
- API call counts
- API error rates
- Retry counts
- System errors (by type)
- Fallback strategy usage
- Variance alert triggers
- System uptime

**Use Cases**:
- Monitor system stability
- Track API reliability
- Alert on high error rates
- Measure system availability

---

## Metric Definitions

### Learning Metrics

#### `learning_iterations_total` (counter)
- **Description**: Total number of iterations executed
- **Type**: Counter (monotonically increasing)
- **Unit**: count
- **Example**: `learning_iterations_total 150`

#### `learning_iterations_successful` (counter)
- **Description**: Number of successful iterations (passed validation and execution)
- **Type**: Counter
- **Unit**: count
- **Example**: `learning_iterations_successful 135`

#### `learning_success_rate` (gauge)
- **Description**: Rolling success rate over recent iterations
- **Type**: Gauge
- **Unit**: percentage (0-100)
- **Calculation**: `(successful_iterations / total_iterations) * 100`
- **Example**: `learning_success_rate 90.0`

#### `learning_sharpe_ratio` (gauge)
- **Description**: Current iteration Sharpe ratio
- **Type**: Gauge
- **Unit**: dimensionless
- **Range**: Typically -2.0 to 5.0 (higher is better)
- **Example**: `learning_sharpe_ratio 2.4751`

#### `learning_sharpe_ratio_avg` (gauge)
- **Description**: Average Sharpe ratio over recent successful iterations (window: 20)
- **Type**: Gauge
- **Unit**: dimensionless
- **Example**: `learning_sharpe_ratio_avg 1.8523`

#### `learning_sharpe_ratio_best` (gauge)
- **Description**: Best Sharpe ratio achieved so far (all-time high)
- **Type**: Gauge
- **Unit**: dimensionless
- **Example**: `learning_sharpe_ratio_best 2.4751`

#### `learning_champion_updates_total` (counter)
- **Description**: Total number of champion strategy updates
- **Type**: Counter
- **Unit**: count
- **Example**: `learning_champion_updates_total 8`

#### `learning_champion_age_iterations` (gauge)
- **Description**: Number of iterations since last champion update
- **Type**: Gauge
- **Unit**: iterations
- **Alert Threshold**: >100 may indicate staleness
- **Example**: `learning_champion_age_iterations 25`

#### `learning_strategy_diversity` (gauge)
- **Description**: Number of unique templates used in recent window
- **Type**: Gauge
- **Unit**: count
- **Range**: 0-N (where N = window size)
- **Example**: `learning_strategy_diversity 8`

---

### Performance Metrics

#### `performance_iteration_duration_seconds` (histogram)
- **Description**: Time taken to complete one full iteration
- **Type**: Histogram
- **Unit**: seconds
- **Typical Range**: 60-300 seconds
- **Example**: `performance_iteration_duration_seconds 145.23`

#### `performance_generation_duration_seconds` (histogram)
- **Description**: Time taken for strategy generation (LLM call)
- **Type**: Histogram
- **Unit**: seconds
- **Typical Range**: 10-60 seconds
- **Example**: `performance_generation_duration_seconds 28.45`

#### `performance_validation_duration_seconds` (histogram)
- **Description**: Time taken for AST validation
- **Type**: Histogram
- **Unit**: seconds
- **Typical Range**: 0.1-2 seconds
- **Example**: `performance_validation_duration_seconds 0.34`

#### `performance_execution_duration_seconds` (histogram)
- **Description**: Time taken for strategy execution (backtest)
- **Type**: Histogram
- **Unit**: seconds
- **Typical Range**: 30-120 seconds
- **Example**: `performance_execution_duration_seconds 85.67`

#### `performance_metric_extraction_duration_seconds` (histogram)
- **Description**: Time taken for metric extraction
- **Type**: Histogram
- **Unit**: seconds
- **Typical Range**: 0.1-60 seconds (depends on method)
- **Example**: `performance_metric_extraction_duration_seconds 0.15`

#### `performance_metric_extraction_method` (counter)
- **Description**: Count of metric extraction methods used
- **Type**: Counter (with labels)
- **Labels**: `method` (DIRECT, SIGNAL, DEFAULT)
- **Example**:
  ```
  performance_metric_extraction_method{method="DIRECT"} 120
  performance_metric_extraction_method{method="SIGNAL"} 25
  performance_metric_extraction_method{method="DEFAULT"} 5
  ```

---

### Quality Metrics

#### `quality_validation_passed_total` (counter)
- **Description**: Number of iterations that passed validation
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_validation_passed_total 142`

#### `quality_validation_failed_total` (counter)
- **Description**: Number of iterations that failed validation
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_validation_failed_total 8`

#### `quality_validation_pass_rate` (gauge)
- **Description**: Rolling validation pass rate
- **Type**: Gauge
- **Unit**: percentage (0-100)
- **Target**: ≥90%
- **Example**: `quality_validation_pass_rate 94.7`

#### `quality_execution_success_total` (counter)
- **Description**: Number of iterations with successful execution
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_execution_success_total 135`

#### `quality_execution_failed_total` (counter)
- **Description**: Number of iterations with failed execution
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_execution_failed_total 7`

#### `quality_preservation_validated_total` (counter)
- **Description**: Number of iterations that passed preservation validation
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_preservation_validated_total 118`

#### `quality_preservation_failed_total` (counter)
- **Description**: Number of iterations that failed preservation validation
- **Type**: Counter
- **Unit**: count
- **Example**: `quality_preservation_failed_total 12`

#### `quality_suspicious_metrics_detected` (counter)
- **Description**: Number of times suspicious metrics were detected
- **Type**: Counter
- **Unit**: count
- **Alert Threshold**: Investigate if >5% of iterations
- **Example**: `quality_suspicious_metrics_detected 3`

---

### System Metrics

#### `system_api_calls_total` (counter)
- **Description**: Total number of API calls made (LLM generation)
- **Type**: Counter
- **Unit**: count
- **Example**: `system_api_calls_total 158`

#### `system_api_errors_total` (counter)
- **Description**: Total number of API errors
- **Type**: Counter
- **Unit**: count
- **Alert Threshold**: >10% of total calls
- **Example**: `system_api_errors_total 5`

#### `system_api_retries_total` (counter)
- **Description**: Total number of API retries
- **Type**: Counter
- **Unit**: count
- **Example**: `system_api_retries_total 12`

#### `system_errors_total` (counter)
- **Description**: Total system errors by type
- **Type**: Counter (with labels)
- **Labels**: `error_type` (validation, execution, api, etc.)
- **Example**:
  ```
  system_errors_total{error_type="validation"} 8
  system_errors_total{error_type="execution"} 7
  system_errors_total{error_type="api"} 5
  ```

#### `system_fallback_used_total` (counter)
- **Description**: Number of times fallback strategy was used
- **Type**: Counter
- **Unit**: count
- **Alert Threshold**: >30% of iterations
- **Example**: `system_fallback_used_total 12`

#### `system_variance_alert_triggered` (counter)
- **Description**: Number of times variance alert was triggered
- **Type**: Counter
- **Unit**: count
- **Alert**: Investigate learning instability
- **Example**: `system_variance_alert_triggered 2`

#### `system_uptime_seconds` (gauge)
- **Description**: System uptime since metrics collector initialization
- **Type**: Gauge
- **Unit**: seconds
- **Example**: `system_uptime_seconds 7200.45`

---

## Integration Examples

### Example 1: Basic Integration in Autonomous Loop

```python
# File: artifacts/working/modules/autonomous_loop.py

from src.monitoring.metrics_collector import MetricsCollector
import time

class AutonomousLoop:
    def __init__(self, model: str, max_iterations: int):
        self.model = model
        self.max_iterations = max_iterations

        # Initialize metrics collector
        self.metrics = MetricsCollector(history_window=100)

    def run_iteration(self, iteration_num: int, data):
        # Start timing
        iteration_start = time.time()

        # Record iteration start
        self.metrics.record_iteration_start(iteration_num)

        # Step 1: Generate strategy
        gen_start = time.time()
        code = generate_strategy(iteration_num, feedback)
        self.metrics.record_generation_time(time.time() - gen_start)

        # Step 2: Validate
        val_start = time.time()
        is_valid, errors = validate_code(code)
        self.metrics.record_validation_time(time.time() - val_start)
        self.metrics.record_validation_result(passed=is_valid)

        if not is_valid:
            self.metrics.record_error("validation")
            return False, "Validation failed"

        # Step 3: Execute
        exec_start = time.time()
        success, metrics_dict, error = execute_strategy_safe(code, data)
        self.metrics.record_execution_time(time.time() - exec_start)
        self.metrics.record_execution_result(success=success)

        if not success:
            self.metrics.record_error("execution")
            return False, f"Execution failed: {error}"

        # Step 4: Record success
        sharpe = metrics_dict.get('sharpe_ratio', 0)
        duration = time.time() - iteration_start
        self.metrics.record_iteration_success(
            sharpe_ratio=sharpe,
            duration=duration
        )

        # Step 5: Champion update
        if self._update_champion(iteration_num, code, metrics_dict):
            self.metrics.record_champion_update(
                old_sharpe=self.champion.metrics['sharpe_ratio'],
                new_sharpe=sharpe,
                iteration_num=iteration_num
            )
        else:
            self.metrics.record_champion_age_increment()

        return True, "Success"
```

### Example 2: Prometheus Export Endpoint

```python
# File: src/monitoring/metrics_server.py

from flask import Flask, Response
from src.monitoring.metrics_collector import MetricsCollector

app = Flask(__name__)
collector = MetricsCollector()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint."""
    prometheus_text = collector.export_prometheus()
    return Response(prometheus_text, mimetype='text/plain')

@app.route('/metrics/json')
def metrics_json():
    """JSON metrics endpoint with full history."""
    json_text = collector.export_json(include_history=True)
    return Response(json_text, mimetype='application/json')

@app.route('/health')
def health():
    """Health check endpoint."""
    summary = collector.get_summary()
    uptime = summary['system']['uptime_seconds']

    if uptime > 0:
        return {'status': 'healthy', 'uptime': uptime}
    else:
        return {'status': 'unhealthy'}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9090)
```

### Example 3: Metric Extraction Time Tracking

```python
# In iteration_engine.py or metrics_extractor.py

from src.monitoring.metrics_collector import MetricsCollector
import time

def validate_and_execute(code: str, iteration: int, collector: MetricsCollector):
    # ... validation logic ...

    # Metric extraction with timing and method tracking
    extraction_start = time.time()
    extraction_method = None

    # Method 1: DIRECT
    if captured_report is not None:
        try:
            metrics = _extract_metrics_from_report(captured_report)
            extraction_method = "DIRECT"
        except Exception:
            pass

    # Method 2: SIGNAL
    if extraction_method is None:
        try:
            metrics = extract_metrics_from_signal(signal)
            extraction_method = "SIGNAL"
        except Exception:
            pass

    # Method 3: DEFAULT
    if extraction_method is None:
        metrics = default_metrics()
        extraction_method = "DEFAULT"

    # Record extraction metrics
    extraction_time = time.time() - extraction_start
    collector.record_metric_extraction_time(extraction_time, extraction_method)

    return metrics
```

---

## Grafana Dashboard Setup

### Prerequisites

1. **Prometheus** (for metric storage)
2. **Grafana** (for visualization)
3. **Python metrics server** (see Example 2 above)

### Installation Steps

#### 1. Start Metrics Server

```bash
# Terminal 1: Start metrics HTTP server
cd /mnt/c/Users/jnpi/documents/finlab
python src/monitoring/metrics_server.py

# Server will listen on http://localhost:9090/metrics
```

#### 2. Configure Prometheus

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 30s
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'autonomous-learning'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'finlab-learning'
          environment: 'production'
```

Start Prometheus:

```bash
# Terminal 2: Start Prometheus
prometheus --config.file=prometheus.yml
```

#### 3. Import Grafana Dashboard

1. Open Grafana: `http://localhost:3000`
2. Login (default: admin/admin)
3. Navigate to: **Dashboards → Import**
4. Upload file: `config/grafana_dashboard.json`
5. Select Prometheus data source
6. Click **Import**

### Dashboard Panels

The included dashboard (`config/grafana_dashboard.json`) provides:

1. **Learning Performance** - Sharpe ratio trends (current, average, best)
2. **Success Rate & Champion Updates** - Success rate, champion update frequency, champion age
3. **Total Iterations** - Counter stat panel
4. **Successful Iterations** - Counter stat panel
5. **Best Sharpe Ratio** - Gauge with color thresholds (red <1.0, yellow 1.0-2.0, green >2.0)
6. **Champion Age** - Gauge with staleness alerts (green <50, yellow 50-100, red >100)
7. **Iteration Duration** - Stacked time series (generation, execution, extraction)
8. **Metric Extraction Methods** - Pie chart showing DIRECT vs SIGNAL vs DEFAULT distribution
9. **Quality Metrics** - Validation pass rate, execution success rate, preservation rate
10. **System Health** - Error rates, fallback usage, API errors
11. **Metrics Summary** - Table view of all key metrics

---

## Prometheus Configuration

### Scrape Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'finlab-learning'
    scrape_interval: 30s
    scrape_timeout: 10s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:9090']
```

### Recording Rules

Create `rules.yml`:

```yaml
groups:
  - name: learning_aggregations
    interval: 1m
    rules:
      # Success rate over 5 minutes
      - record: learning:success_rate:5m
        expr: |
          (rate(learning_iterations_successful[5m]) / rate(learning_iterations_total[5m])) * 100

      # Average iteration duration (5m window)
      - record: performance:iteration_duration_avg:5m
        expr: |
          avg_over_time(performance_iteration_duration_seconds[5m])

      # Error rate per hour
      - record: system:error_rate:1h
        expr: |
          rate(system_errors_total[1h]) * 3600

      # Champion update frequency (updates per 100 iterations)
      - record: learning:champion_update_freq:100iter
        expr: |
          (learning_champion_updates_total / learning_iterations_total) * 100
```

Load rules:

```yaml
# Add to prometheus.yml
rule_files:
  - 'rules.yml'
```

---

## Alerting Rules

### Critical Alerts

Create `alerts.yml`:

```yaml
groups:
  - name: learning_system_alerts
    rules:
      # Alert: High error rate
      - alert: HighErrorRate
        expr: rate(system_errors_total[5m]) * 60 > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High system error rate detected"
          description: "Error rate is {{ $value }} errors/hour (threshold: 5)"

      # Alert: Low success rate
      - alert: LowSuccessRate
        expr: learning_success_rate < 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Learning success rate is low"
          description: "Success rate is {{ $value }}% (threshold: 70%)"

      # Alert: Champion staleness
      - alert: ChampionStale
        expr: learning_champion_age_iterations > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Champion strategy is stale"
          description: "Champion hasn't updated in {{ $value }} iterations"

      # Alert: High variance (instability)
      - alert: LearningInstability
        expr: rate(system_variance_alert_triggered[1h]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Learning system is unstable"
          description: "Variance alerts triggered in last hour"

      # Alert: Excessive fallback usage
      - alert: HighFallbackUsage
        expr: (system_fallback_used_total / learning_iterations_total) > 0.3
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High fallback strategy usage"
          description: "{{ $value | humanizePercentage }} of iterations used fallback (threshold: 30%)"

      # Alert: Poor metric extraction
      - alert: MetricExtractionDegraded
        expr: |
          (sum(performance_metric_extraction_method{method="DEFAULT"}) /
           sum(performance_metric_extraction_method)) > 0.1
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Metric extraction quality degraded"
          description: "{{ $value | humanizePercentage }} of extractions using DEFAULT fallback"
```

Load alerts:

```yaml
# Add to prometheus.yml
rule_files:
  - 'alerts.yml'
```

### Alert Manager Configuration

Create `alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'default'

receivers:
  - name: 'default'
    email_configs:
      - to: 'alerts@example.com'
        from: 'prometheus@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'prometheus'
        auth_password: '<password>'

    webhook_configs:
      - url: 'http://localhost:5001/webhook'  # For Slack/Discord integration
```

---

## Troubleshooting

### Issue 1: Metrics Not Appearing in Prometheus

**Symptoms**:
- Prometheus shows target as DOWN
- No metrics visible in Grafana

**Solutions**:

1. **Check metrics server is running**:
   ```bash
   curl http://localhost:9090/metrics
   # Should return Prometheus-formatted metrics
   ```

2. **Verify Prometheus scrape config**:
   ```bash
   # Check targets
   curl http://localhost:9090/api/v1/targets
   ```

3. **Check firewall/network**:
   ```bash
   # Test connection
   telnet localhost 9090
   ```

4. **Review Prometheus logs**:
   ```bash
   # Look for scrape errors
   grep "scrape" prometheus.log
   ```

### Issue 2: Metrics Not Recording

**Symptoms**:
- Metrics server running but values always 0
- Metrics not updating over time

**Solutions**:

1. **Verify collector is being used**:
   ```python
   # In autonomous_loop.py
   print(f"Collector initialized: {hasattr(self, 'metrics')}")
   print(f"Total iterations: {self.metrics.metrics['learning_iterations_total'].get_latest()}")
   ```

2. **Check metric recording calls**:
   ```python
   # Add debug logging
   logger.info(f"Recording iteration success: sharpe={sharpe}")
   self.metrics.record_iteration_success(sharpe, duration)
   logger.info(f"Recorded. Latest value: {self.metrics.metrics['learning_sharpe_ratio'].get_latest()}")
   ```

3. **Verify metric names match**:
   ```python
   # List all available metrics
   print(list(collector.metrics.keys()))
   ```

### Issue 3: Dashboard Panels Empty

**Symptoms**:
- Grafana dashboard loads but panels show "No data"

**Solutions**:

1. **Check Prometheus data source**:
   - Grafana → Configuration → Data Sources
   - Test connection to Prometheus
   - Verify URL is correct (usually `http://localhost:9090`)

2. **Query Prometheus directly**:
   ```bash
   # Test query
   curl 'http://localhost:9090/api/v1/query?query=learning_sharpe_ratio'
   ```

3. **Check time range**:
   - Ensure dashboard time range includes recent data
   - Try "Last 1 hour" or "Last 6 hours"

4. **Verify metric names in queries**:
   - Edit panel → Check query expression
   - Compare with metric names from `/metrics` endpoint

### Issue 4: High Memory Usage

**Symptoms**:
- Metrics collector consuming excessive memory
- System slowdown over time

**Solutions**:

1. **Reduce history window**:
   ```python
   # Reduce from 100 to 50
   collector = MetricsCollector(history_window=50)
   ```

2. **Implement periodic cleanup**:
   ```python
   # Clear old values periodically
   if iteration_num % 100 == 0:
       for metric in collector.metrics.values():
           # Keep only last N values
           metric.values = metric.values[-50:]
   ```

3. **Export and reset**:
   ```python
   # Save to disk and reset
   if iteration_num % 500 == 0:
       with open(f'metrics_snapshot_{iteration_num}.json', 'w') as f:
           f.write(collector.export_json(include_history=True))
       collector.reset()
   ```

### Issue 5: Incorrect Metric Values

**Symptoms**:
- Metrics show unexpected values
- Counters decreasing (should only increase)
- Gauges out of expected range

**Solutions**:

1. **Verify counter vs gauge usage**:
   - Counters: Always increase (e.g., `learning_iterations_total`)
   - Gauges: Can go up or down (e.g., `learning_sharpe_ratio`)

2. **Check value calculations**:
   ```python
   # Add validation
   def record_iteration_success(self, sharpe_ratio: float, duration: float):
       assert sharpe_ratio >= -5.0 and sharpe_ratio <= 10.0, f"Invalid Sharpe: {sharpe_ratio}"
       assert duration > 0, f"Invalid duration: {duration}"
       # ... record logic ...
   ```

3. **Review aggregation logic**:
   ```python
   # Verify average calculation
   avg = metric.get_average(window=20)
   print(f"Values used: {[v.value for v in metric.values[-20:]]}")
   print(f"Calculated avg: {avg}")
   ```

---

## Best Practices

### 1. Metric Collection

- **Record at appropriate granularity**: Don't record every microsecond event
- **Use labels sparingly**: Too many labels can explode cardinality
- **Prefer counters for totals**: Use counters for cumulative values, gauges for current state
- **Add context to labels**: Include meaningful labels (e.g., `method="DIRECT"`)

### 2. Performance

- **Limit history window**: Keep history_window reasonable (50-100 values)
- **Batch exports**: Don't export metrics on every iteration
- **Use async recording**: Record metrics asynchronously if performance critical
- **Monitor collector overhead**: Metrics collection should add <1% overhead

### 3. Alerting

- **Set reasonable thresholds**: Avoid alert fatigue with too-sensitive alerts
- **Use appropriate durations**: Add `for: 5m` to avoid transient alert spam
- **Test alerts**: Manually trigger alerts to verify notification delivery
- **Document runbooks**: Include resolution steps in alert annotations

### 4. Dashboard Design

- **Group related metrics**: Organize panels by category (learning, performance, etc.)
- **Use appropriate visualizations**: Time series for trends, stats for current values
- **Add thresholds**: Color-code gauges (green/yellow/red) for quick assessment
- **Include context**: Add panel descriptions explaining what metrics mean

---

## Performance Considerations

### Metric Collection Overhead

The `MetricsCollector` is designed for minimal overhead:

- **Memory**: ~1KB per metric (with 100-value history)
- **CPU**: <0.1ms per metric recording
- **Total overhead**: <1% of iteration time

### Optimization Tips

1. **Reduce history window** for long-running loops:
   ```python
   collector = MetricsCollector(history_window=50)  # Instead of 100
   ```

2. **Export less frequently**:
   ```python
   if iteration_num % 10 == 0:  # Export every 10 iterations
       prometheus_text = collector.export_prometheus()
   ```

3. **Use summary statistics** instead of full history export:
   ```python
   summary = collector.get_summary()  # Much faster than export_json()
   ```

---

## Appendix: Complete Integration Example

**File: `examples/monitoring_integration_example.py`**

```python
"""Complete example of monitoring integration with autonomous loop."""

from src.monitoring.metrics_collector import MetricsCollector
from artifacts.working.modules.autonomous_loop import AutonomousLoop
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    # Initialize metrics collector
    collector = MetricsCollector(history_window=100)
    logger.info("MetricsCollector initialized")

    # Initialize autonomous loop
    loop = AutonomousLoop(
        model="google/gemini-2.5-flash",
        max_iterations=10
    )

    # Attach collector to loop
    loop.metrics_collector = collector

    # Run loop with metrics collection
    for iteration in range(10):
        start_time = time.time()

        # Record iteration start
        collector.record_iteration_start(iteration)

        # Run iteration
        success, status = loop.run_iteration(iteration, data=None)

        # Record metrics based on result
        if success:
            duration = time.time() - start_time
            record = loop.history.get_record(iteration)

            if record and record.metrics:
                sharpe = record.metrics.get('sharpe_ratio', 0)
                collector.record_iteration_success(sharpe, duration)

                logger.info(f"Iteration {iteration}: Success (Sharpe={sharpe:.4f}, Duration={duration:.2f}s)")
        else:
            logger.warning(f"Iteration {iteration}: Failed ({status})")
            collector.record_error("iteration_failed")

        # Export metrics every 5 iterations
        if (iteration + 1) % 5 == 0:
            summary = collector.get_summary()
            logger.info(f"\n=== Metrics Summary (Iteration {iteration + 1}) ===")
            logger.info(f"Success Rate: {summary['learning']['success_rate']:.1f}%")
            logger.info(f"Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
            logger.info(f"Avg Duration: {summary['performance']['avg_iteration_duration']:.2f}s")

            # Save metrics to file
            with open(f'metrics_iter{iteration + 1}.json', 'w') as f:
                f.write(collector.export_json(include_history=True))

            logger.info(f"Metrics exported to metrics_iter{iteration + 1}.json")

    # Final export
    logger.info("\n=== Final Metrics Export ===")

    # Prometheus format
    with open('metrics_final.txt', 'w') as f:
        f.write(collector.export_prometheus())
    logger.info("Prometheus metrics: metrics_final.txt")

    # JSON format
    with open('metrics_final.json', 'w') as f:
        f.write(collector.export_json(include_history=True))
    logger.info("JSON metrics: metrics_final.json")

    # Print summary
    summary = collector.get_summary()
    logger.info("\n=== Final Summary ===")
    logger.info(f"Total Iterations: {summary['learning']['total_iterations']}")
    logger.info(f"Success Rate: {summary['learning']['success_rate']:.1f}%")
    logger.info(f"Best Sharpe: {summary['learning']['best_sharpe']:.4f}")
    logger.info(f"Champion Updates: {summary['learning']['champion_updates']}")
    logger.info(f"Uptime: {summary['system']['uptime_seconds']:.1f}s")


if __name__ == '__main__':
    main()
```

---

## Conclusion

The monitoring infrastructure provides comprehensive observability for the autonomous learning system. Use this documentation to:

1. **Integrate metrics collection** into your autonomous loop
2. **Set up Prometheus and Grafana** for visualization
3. **Configure alerts** for critical issues
4. **Troubleshoot problems** using metrics data
5. **Optimize performance** based on metric insights

For questions or issues, refer to the troubleshooting section or file a GitHub issue.

---

**Last Updated**: 2025-10-16
**Task**: 99 - Monitoring Dashboard Metrics
**Status**: ✅ COMPLETE
