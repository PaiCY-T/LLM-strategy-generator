# Validation Infrastructure Monitoring Setup

This document describes the monitoring system for the validation infrastructure, including metrics collection, dashboard setup, and alert configuration.

## Overview

The validation monitoring system tracks key metrics to ensure production-ready performance and reliability:

- **Field Error Rate**: Percentage of strategies with invalid field names
- **LLM Success Rate**: Percentage of LLM-generated strategies that pass validation
- **Validation Latency**: Total and per-layer validation performance
- **Circuit Breaker Triggers**: Frequency of circuit breaker activations
- **Error Signatures**: Diversity of validation errors

## Architecture

```
┌─────────────────────┐
│ ValidationGateway   │
│  (collects metrics) │
└──────────┬──────────┘
           │
           v
┌─────────────────────┐
│ MetricsCollector    │
│  (aggregates data)  │
└──────────┬──────────┘
           │
           ├─────────────────────┐
           │                     │
           v                     v
┌──────────────────┐   ┌─────────────────┐
│ Prometheus       │   │ CloudWatch      │
│ (time-series DB) │   │ (AWS metrics)   │
└─────────┬────────┘   └────────┬────────┘
          │                     │
          v                     v
┌──────────────────────────────────┐
│ Grafana Dashboard                │
│ (visualization & alerting)       │
└──────────────────────────────────┘
```

## Metrics Reference

### Field Error Rate
- **Metric**: `validation_field_error_rate`
- **Type**: Gauge (percentage)
- **Description**: Percentage of strategies with field name errors
- **Alert Thresholds**:
  - Warning: >5%
  - Critical: >10%
- **Expected Value**: 0% (with validation enabled)

### LLM Success Rate
- **Metric**: `validation_llm_success_rate`
- **Type**: Gauge (percentage)
- **Description**: Percentage of LLM generations that pass validation
- **Alert Thresholds**:
  - Warning: <90%
  - Critical: <80%
- **Expected Value**: >95%

### Validation Latency

#### Total Latency
- **Metric**: `validation_total_latency_ms`
- **Type**: Histogram (milliseconds)
- **Description**: Total validation time across all layers
- **Alert Thresholds**:
  - Mean Warning: >1ms
  - Mean Critical: >5ms
  - P99 Warning: >5ms
  - P99 Critical: >8ms
- **Expected Value**: <1ms average, <5ms P99

#### Layer-Specific Latency
- **Layer 1**: `validation_layer1_latency_ms` (DataFieldManifest lookup)
  - Expected: <0.001ms (1μs)
- **Layer 2**: `validation_layer2_latency_ms` (AST code validation)
  - Expected: <5ms
- **Layer 3**: `validation_layer3_latency_ms` (YAML schema validation)
  - Expected: <5ms

### Circuit Breaker Triggers
- **Metric**: `validation_circuit_breaker_triggers`
- **Type**: Counter (total count)
- **Description**: Number of circuit breaker activations
- **Alert Thresholds**:
  - Warning: >10 triggers/min
  - Critical: >20 triggers/min
- **Expected Value**: <1 trigger/min

### Unique Error Signatures
- **Metric**: `validation_error_signatures_unique`
- **Type**: Gauge (count)
- **Description**: Number of distinct error types tracked
- **Expected Value**: Decreasing over time as common errors are fixed

## Setup Instructions

### 1. Metrics Collection

#### Initialize MetricsCollector in Your Application

```python
from src.monitoring.metrics_collector import MetricsCollector
from src.validation.gateway import ValidationGateway

# Create metrics collector
collector = MetricsCollector()

# Attach to validation gateway
gateway = ValidationGateway()
gateway.set_metrics_collector(collector)
```

#### Record Validation Metrics

The ValidationGateway automatically records metrics when a MetricsCollector is attached:

```python
# Validation happens automatically, metrics recorded
result = gateway.validate_strategy(strategy_code)

# Metrics are automatically tracked:
# - Field error rate
# - Validation latency (all layers)
# - Circuit breaker triggers
# - Error signatures
```

### 2. Prometheus Export

#### Export Metrics to Prometheus Format

```python
# Get Prometheus-formatted metrics
prometheus_output = collector.export_prometheus()

# Serve via HTTP endpoint for Prometheus scraping
# Example with Flask:
from flask import Flask, Response

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    return Response(
        collector.export_prometheus(),
        mimetype='text/plain'
    )
```

#### Configure Prometheus Scraping

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'validation_monitoring'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:5000']  # Your metrics endpoint
```

### 3. CloudWatch Export

#### Export Metrics to CloudWatch

```python
import boto3
import json

# Get CloudWatch-formatted metrics
cloudwatch_output = collector.export_cloudwatch()
cloudwatch_data = json.loads(cloudwatch_output)

# Push to CloudWatch
cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(**cloudwatch_data)
```

#### Automated CloudWatch Push

```python
import schedule
import time

def push_to_cloudwatch():
    """Push metrics to CloudWatch every 30 seconds."""
    cloudwatch_output = collector.export_cloudwatch()
    cloudwatch_data = json.loads(cloudwatch_output)

    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(**cloudwatch_data)

# Schedule every 30 seconds (NFR-O4 requirement)
schedule.every(30).seconds.do(push_to_cloudwatch)

while True:
    schedule.run_pending()
    time.sleep(1)
```

### 4. Grafana Dashboard Setup

#### Import Dashboard

1. Open Grafana web UI
2. Navigate to **Dashboards** → **Import**
3. Upload `config/monitoring/grafana_dashboard.json`
4. Select your Prometheus data source
5. Click **Import**

#### Dashboard Panels

The dashboard includes 9 panels:

1. **Field Error Rate** - Time series with alert thresholds
2. **LLM Success Rate** - Time series with alert thresholds
3. **Validation Latency (Total)** - P50/P95/P99 percentiles
4. **Validation Latency by Layer** - Layer breakdown
5. **Circuit Breaker Triggers** - Current trigger rate
6. **Unique Error Signatures** - Error diversity tracking
7. **Alert Status** - Active alerts table
8. **Mean Validation Latency** - Gauge with 5-min average
9. **P99 Validation Latency** - Gauge with P99 tracking

### 5. Alert Configuration

#### Prometheus Alert Rules

Create `alerts/validation.rules.yml`:

```yaml
groups:
  - name: validation_alerts
    interval: 30s
    rules:
      # Field Error Rate Alerts
      - alert: HighFieldErrorRate
        expr: validation_field_error_rate > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Field error rate above 5%"
          description: "{{ $value }}% of strategies have field errors"

      - alert: CriticalFieldErrorRate
        expr: validation_field_error_rate > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Field error rate above 10%"
          description: "{{ $value }}% of strategies have field errors"

      # LLM Success Rate Alerts
      - alert: LowLLMSuccessRate
        expr: validation_llm_success_rate < 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LLM success rate below 90%"
          description: "Only {{ $value }}% of LLM generations pass validation"

      - alert: CriticalLLMSuccessRate
        expr: validation_llm_success_rate < 80
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "LLM success rate below 80%"
          description: "Only {{ $value }}% of LLM generations pass validation"

      # Validation Latency Alerts
      - alert: HighMeanLatency
        expr: avg_over_time(validation_total_latency_ms[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Mean validation latency above 1ms"
          description: "Average latency: {{ $value }}ms"

      - alert: CriticalMeanLatency
        expr: avg_over_time(validation_total_latency_ms[5m]) > 5
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Mean validation latency above 5ms"
          description: "Average latency: {{ $value }}ms"

      - alert: HighP99Latency
        expr: histogram_quantile(0.99, validation_total_latency_ms) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "P99 validation latency above 5ms"
          description: "P99 latency: {{ $value }}ms"

      - alert: CriticalP99Latency
        expr: histogram_quantile(0.99, validation_total_latency_ms) > 8
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "P99 validation latency above 8ms"
          description: "P99 latency: {{ $value }}ms"

      # Circuit Breaker Alerts
      - alert: HighCircuitBreakerTriggers
        expr: rate(validation_circuit_breaker_triggers[1m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Circuit breaker triggering frequently"
          description: "{{ $value }} triggers per minute"

      - alert: CriticalCircuitBreakerTriggers
        expr: rate(validation_circuit_breaker_triggers[1m]) > 20
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker triggering excessively"
          description: "{{ $value }} triggers per minute"
```

#### Load Alert Rules in Prometheus

Add to `prometheus.yml`:

```yaml
rule_files:
  - "alerts/validation.rules.yml"
```

#### Configure Alertmanager

Create `alertmanager.yml`:

```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'team-notifications'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

receivers:
  - name: 'team-notifications'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK_URL'
        channel: '#validation-alerts'
        title: 'Validation Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'
```

## Monitoring Best Practices

### 1. Regular Metric Review

- **Daily**: Check field error rate and LLM success rate
- **Weekly**: Review latency trends and alert frequency
- **Monthly**: Analyze error signature diversity and circuit breaker patterns

### 2. Alert Response Procedures

#### Field Error Rate >5% (Warning)
1. Check recent strategy generations for patterns
2. Review field suggestion injection in prompts
3. Verify DataFieldManifest is up to date
4. Monitor for 30 minutes before escalating

#### Field Error Rate >10% (Critical)
1. Immediate investigation required
2. Check for breaking changes in data fields
3. Review LLM prompt quality
4. Consider circuit breaker manual trigger

#### Validation Latency >5ms (Mean Critical)
1. Profile validation layers to identify bottleneck
2. Check system resource utilization
3. Review recent code changes
4. Consider scaling if persistent

#### Circuit Breaker >20 triggers/min (Critical)
1. Review error signatures for repeated patterns
2. Check for systemic issue (data corruption, API failures)
3. Investigate LLM quality degradation
4. Consider temporary rollback

### 3. Metrics Retention

- **Prometheus**: 15 days (default)
- **CloudWatch**: 30 days for detailed metrics, 1 year for aggregated
- **Long-term Storage**: Export to S3 for historical analysis

### 4. Dashboard Customization

The provided dashboard is a starting point. Customize based on your needs:

- Add panels for specific error types
- Create team-specific dashboards
- Integrate with other monitoring systems
- Add business metrics correlation

## Troubleshooting

### Metrics Not Appearing in Prometheus

1. Verify metrics endpoint is accessible: `curl http://localhost:5000/metrics`
2. Check Prometheus scrape targets: `http://prometheus:9090/targets`
3. Verify metric names match exactly (case-sensitive)
4. Check Prometheus logs for scraping errors

### CloudWatch Metrics Missing

1. Verify AWS credentials are configured correctly
2. Check CloudWatch namespace: "StrategyValidation"
3. Verify metrics are being pushed (check application logs)
4. Check IAM permissions for `cloudwatch:PutMetricData`

### Grafana Dashboard Not Loading

1. Verify Prometheus data source is configured
2. Check time range (default: last 6 hours)
3. Verify metrics exist in Prometheus
4. Check Grafana logs for query errors

### High Latency False Positives

1. Verify system clock synchronization
2. Check for GC pauses or resource contention
3. Review metric collection overhead (<0.1ms expected)
4. Consider adjusting alert thresholds if baseline differs

## Performance Impact

The monitoring system is designed for minimal overhead:

- **Metrics Collection**: <0.1ms per validation
- **Prometheus Export**: <10ms per request
- **CloudWatch Push**: ~100ms every 30 seconds (async)
- **Memory Usage**: ~10MB for 100,000 metric samples

Total overhead: **<1% of validation time**

## Example Queries

### Prometheus Queries

```promql
# Average field error rate over last hour
avg_over_time(validation_field_error_rate[1h])

# P95 latency by layer
histogram_quantile(0.95, validation_layer2_latency_ms)

# Circuit breaker trigger rate
rate(validation_circuit_breaker_triggers[5m])

# Latency heatmap
histogram_quantile(0.50, validation_total_latency_ms) by (le)
```

### CloudWatch Insights Queries

```sql
-- Field error rate trend
fields @timestamp, FieldErrorRate
| filter Namespace = "StrategyValidation"
| sort @timestamp desc

-- Latency percentiles
fields @timestamp, TotalLatency
| stats percentile(TotalLatency, 50) as P50,
        percentile(TotalLatency, 95) as P95,
        percentile(TotalLatency, 99) as P99 by bin(5m)
```

## Integration with Existing Monitoring

### APM Integration (New Relic, Datadog, etc.)

```python
# Example: New Relic integration
import newrelic.agent

def record_validation_to_apm(collector):
    """Record validation metrics to APM."""
    summary = collector.get_summary()

    newrelic.agent.record_custom_metric(
        'Custom/Validation/FieldErrorRate',
        summary['validation']['field_error_rate']
    )
    newrelic.agent.record_custom_metric(
        'Custom/Validation/LLMSuccessRate',
        summary['validation']['llm_success_rate']
    )
```

## References

- Task 6.5: Performance Monitoring Dashboard
- NFR-M1: Monitoring and Alerting Requirements
- NFR-O4: 30-Second Update Time Requirement
- Task 6.4: Validation Performance Analysis
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
