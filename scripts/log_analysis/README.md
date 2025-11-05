# Log Analysis Scripts

Utilities for querying and analyzing JSON structured logs from the Finlab Trading System.

## Overview

These scripts provide command-line tools for:
- **Querying logs** by event type, time range, and custom filters
- **Performance analysis** with statistical summaries
- **Aggregation** of metrics and trends

## Scripts

### 1. query_logs.py

Query and filter JSON log entries.

**Features**:
- Filter by event type, log level, iteration number
- Time range queries (--since, --until)
- Custom field filtering
- Multiple output formats (table, JSON, compact)
- Aggregation by field

**Usage**:

```bash
# Query all iteration events
python query_logs.py --event-type iteration_start --log-file logs/iterations.json.log

# Query champion updates since yesterday
python query_logs.py --event-type champion_update --since 2025-10-15 --log-file logs/iterations.json.log

# Query errors for specific iteration
python query_logs.py --level ERROR --iteration 42 --log-file logs/iterations.json.log

# Query validation failures
python query_logs.py --event-type validation_result --filter passed=false --log-file logs/iterations.json.log

# Aggregate by event type
python query_logs.py --log-file logs/iterations.json.log --aggregate-by event_type

# Compact output for piping
python query_logs.py --event-type iteration_end --log-file logs/iterations.json.log --format compact
```

**Options**:
- `--log-file`: Path to JSON log file (required)
- `--event-type`: Filter by event type
- `--level`: Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--iteration`: Filter by iteration number
- `--since`: Filter by timestamp >= date (ISO format)
- `--until`: Filter by timestamp <= date (ISO format)
- `--filter`: Additional filter (key=value), can be specified multiple times
- `--format`: Output format (table, json, compact)
- `--limit`: Maximum number of results
- `--aggregate-by`: Aggregate results by field

### 2. analyze_performance.py

Analyze system performance metrics from logs.

**Features**:
- Iteration duration statistics
- Champion update frequency analysis
- Metric extraction performance
- Validation pass rates
- Template instantiation success rates
- Statistical summaries (min, max, mean, median, stdev, percentiles)

**Usage**:

```bash
# Generate summary report
python analyze_performance.py --log-file logs/iterations.json.log --report summary

# Save detailed report to file
python analyze_performance.py --log-file logs/iterations.json.log --report detailed --output report.txt
```

**Options**:
- `--log-file`: Path to JSON log file (required)
- `--report`: Report type (summary, detailed)
- `--output`: Output file (default: stdout)

**Metrics Analyzed**:

1. **Iteration Performance**:
   - Total/successful/failed iterations
   - Success/validation/execution rates
   - Duration statistics (min, max, mean, median, stdev)

2. **Champion Updates**:
   - Total updates/rejections/demotions
   - Update frequency
   - Improvement statistics
   - Threshold type distribution
   - Multi-objective pass rate

3. **Metric Extraction**:
   - Success rate
   - Method distribution (DIRECT, SIGNAL, DEFAULT)
   - Duration statistics (min, max, mean, median, P95)
   - Fallback statistics

4. **Validation Performance**:
   - Per-validator statistics
   - Pass rates
   - Duration metrics

5. **Template Integration**:
   - Recommendation frequency
   - Instantiation success rate
   - Template distribution
   - Exploration mode rate
   - Retry statistics

## Common Use Cases

### 1. Monitor System Health

```bash
# Check overall success rates
python analyze_performance.py --log-file logs/iterations.json.log | grep "Success rate"

# Find recent errors
python query_logs.py --level ERROR --since $(date -I) --log-file logs/iterations.json.log
```

### 2. Debug Performance Issues

```bash
# Find slow metric extractions
python query_logs.py --event-type metric_extraction --log-file logs/iterations.json.log --format json | \
  jq 'select(.duration_ms > 100)'

# Analyze iteration durations
python query_logs.py --event-type iteration_end --log-file logs/iterations.json.log --format json | \
  jq '.duration_seconds' | python -c "import sys; nums=[float(x) for x in sys.stdin]; print(f'Mean: {sum(nums)/len(nums):.2f}s')"
```

### 3. Track Champion Evolution

```bash
# List all champion updates
python query_logs.py --event-type champion_update --log-file logs/iterations.json.log --format compact

# Aggregate by threshold type
python query_logs.py --event-type champion_update --log-file logs/iterations.json.log --aggregate-by threshold_type

# Track Sharpe progression
python query_logs.py --event-type champion_update --log-file logs/iterations.json.log --format json | \
  jq -r '[.iteration_num, .new_sharpe] | @tsv'
```

### 4. Validation Analysis

```bash
# Find validation failures
python query_logs.py --event-type validation_result --filter passed=false --log-file logs/iterations.json.log

# Aggregate failures by validator
python query_logs.py --event-type validation_result --filter passed=false --log-file logs/iterations.json.log --aggregate-by validator_name

# Check validation performance
python analyze_performance.py --log-file logs/iterations.json.log | grep -A 5 "VALIDATION PERFORMANCE"
```

### 5. Template Usage Analysis

```bash
# Track template recommendations
python query_logs.py --event-type template_recommendation --log-file logs/iterations.json.log --aggregate-by template_name

# Find template instantiation failures
python query_logs.py --event-type template_instantiation --filter success=false --log-file logs/iterations.json.log

# Check exploration mode frequency
python query_logs.py --event-type template_recommendation --filter exploration_mode=true --log-file logs/iterations.json.log
```

## Output Formats

### Table Format (Default)

Detailed view with all fields:

```
================================================================================
Found 3 matching entries
================================================================================

Entry #1:
--------------------------------------------------------------------------------
  event_type: iteration_start
  hostname: trading-server-1
  iteration_num: 1
  level: INFO
  logger: autonomous_loop
  message: Starting iteration 1/100
  ...
```

### JSON Format

Machine-parseable output:

```json
[
  {
    "timestamp": "2025-10-16T14:30:45.123456",
    "level": "INFO",
    "event_type": "iteration_start",
    "iteration_num": 1,
    ...
  }
]
```

### Compact Format

One line per entry:

```
[2025-10-16 14:30:45,123] INFO     iteration_start      Starting iteration 1/100
[2025-10-16 14:32:10,456] INFO     champion_update      Champion updated: Sharpe 2.50 → 2.80
```

## Integration with Log Aggregation Tools

### ELK Stack

Configure Filebeat to read JSON logs:

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /path/to/logs/*.json.log
  json.keys_under_root: true
  json.add_error_key: true
```

Query in Kibana:
```
event_type:"champion_update" AND new_sharpe:>2.5
```

### Splunk

Configure Splunk to parse JSON logs:

```
[finlab_logs]
sourcetype = _json
INDEXED_EXTRACTIONS = json
TIME_PREFIX = \"timestamp\":\s*\"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%6N
```

Query in Splunk:
```
sourcetype=finlab_logs event_type=iteration_failure | stats count by failure_stage
```

### CloudWatch Logs

Use CloudWatch Insights:

```
fields @timestamp, event_type, iteration_num, message
| filter event_type = "champion_update"
| sort new_sharpe desc
| limit 20
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## See Also

- **Logging Documentation**: `docs/LOGGING.md`
- **JSON Logger Module**: `src/utils/json_logger.py`
- **Integration Example**: `examples/logging_integration_example.py`
