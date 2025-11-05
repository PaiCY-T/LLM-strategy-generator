# Troubleshooting Guide

**Last Updated**: 2025-10-16
**Version**: 1.0

This guide documents common issues, their root causes, diagnostic procedures, and solutions for the Finlab Autonomous Trading Strategy Learning System.

---

## Table of Contents

1. [Quick Diagnostic Checklist](#quick-diagnostic-checklist)
2. [Template Integration Issues](#template-integration-issues)
3. [Metric Extraction Errors](#metric-extraction-errors)
4. [Validation Component Failures](#validation-component-failures)
5. [Data Quality Issues](#data-quality-issues)
6. [API Failures](#api-failures)
7. [Performance Problems](#performance-problems)
8. [Configuration Errors](#configuration-errors)
9. [Recovery Procedures](#recovery-procedures)
10. [Monitoring and Logging](#monitoring-and-logging)

---

## Quick Diagnostic Checklist

When encountering system failures, run through this checklist first:

```bash
# 1. Check system logs
tail -n 100 logs/system.log

# 2. Verify API connectivity
python -c "import finlab; print('Finlab OK')"
python -c "import anthropic; print('Anthropic OK')"

# 3. Check configuration files
ls -la config/
cat config/learning_system.yaml

# 4. Verify data freshness
python -c "from src.data.freshness import DataFreshnessChecker; checker = DataFreshnessChecker(); print(checker.check_all())"

# 5. Check iteration history integrity
python -c "from artifacts.working.modules.history import IterationHistory; h = IterationHistory(); print(f'Records: {len(h.get_all_records())}')"

# 6. Verify champion state
cat champion_strategy.json 2>/dev/null || echo "No champion found"

# 7. Check database connectivity
python -c "from src.storage.manager import StorageManager; s = StorageManager(); print('DB OK')"
```

**Common Quick Fixes:**
- **Issue**: Missing dependencies → Run `pip install -r requirements.txt`
- **Issue**: Outdated data → Run data refresh: `python scripts/refresh_data.py`
- **Issue**: Corrupted history → Restore from backup: `cp iteration_history.json.bak iteration_history.json`

---

## Template Integration Issues

### Issue 1.1: Template Not Found

**Symptom:**
```
ERROR: Template 'momentum_breakout' not found in template registry
```

**Root Cause:** Template file missing or not registered in system.

**Diagnosis:**
```bash
# Check template directory
ls -la src/templates/

# Verify template registration
python -c "from src.templates.registry import TemplateRegistry; r = TemplateRegistry(); print(r.list_templates())"
```

**Solution:**
1. Verify template file exists: `src/templates/momentum_breakout.py`
2. Ensure template has `@register_template` decorator
3. Reload template registry: `python -c "from src.templates.registry import TemplateRegistry; TemplateRegistry().refresh()"`

**Prevention:** Add template validation to CI/CD pipeline.

---

### Issue 1.2: Template Parameter Mismatch

**Symptom:**
```
ValidationError: Required parameter 'lookback_period' not found in template parameters
```

**Root Cause:** Template interface changed but existing strategies still use old parameters.

**Diagnosis:**
```python
from src.validation.preservation_validator import PreservationValidator
validator = PreservationValidator()

# Check parameter compatibility
is_valid, report = validator.validate_preservation(
    generated_code="...",
    champion=champion_strategy
)
print(report.missing_params)
```

**Solution:**
1. Update template to include missing parameters with defaults
2. Migrate existing strategies: `python scripts/migrate_strategies.py --add-defaults`
3. Update parameter extraction logic in `performance_attributor.py`

**Error Message Reference:**
- `Parameter 'X' missing` → Add parameter to template
- `Parameter 'X' has wrong type` → Fix type annotation in template
- `Parameter 'X' out of range` → Update validation bounds

---

### Issue 1.3: Template Generation Timeout

**Symptom:**
```
RuntimeError: Template generation timed out after 120 seconds
```

**Root Cause:** LLM taking too long to generate strategy code, likely due to complex prompt or API throttling.

**Diagnosis:**
```bash
# Check Claude API circuit breaker state
python -c "from src.analysis.claude_client import ClaudeClient; client = ClaudeClient(api_key='...'); print(client.get_circuit_state())"

# Review prompt size
python -c "from artifacts.working.modules.prompt_builder import PromptBuilder; pb = PromptBuilder(); prompt = pb.build_prompt(0, None, None, None); print(f'Prompt size: {len(prompt)} chars')"
```

**Solution:**
1. Increase timeout: Edit `autonomous_loop.py`, change `timeout=120` to `timeout=180`
2. Reduce prompt complexity: Remove verbose feedback history
3. Check API rate limits: Wait 60 seconds and retry
4. Switch to faster model: Use `gemini-2.5-flash` instead of `o3`

**Recovery:** Reset circuit breaker: `python -c "from src.analysis.claude_client import ClaudeClient; client.reset_circuit()"`

---

## Metric Extraction Errors

### Issue 2.1: Impossible Metric Combination

**Symptom:**
```
MetricValidationError: Impossible combination: negative return (-15.8%) with positive Sharpe (0.89)
```

**Root Cause:** Bug in metric calculation or data integrity issue (Zen Challenge finding).

**Diagnosis:**
```python
from src.validation.metric_validator import MetricValidator

validator = MetricValidator()
metrics = {'total_return': -0.158, 'sharpe_ratio': 0.89, 'volatility': 0.15}
is_valid, errors = validator.validate_metrics(metrics)

print("Validation errors:", errors)

# Generate audit trail
audit_trail = validator.generate_audit_trail(finlab_report)
print("Calculation steps:", audit_trail['sharpe_calculation_steps'])
```

**Solution:**
1. **Immediate**: Reject iteration and log for manual review
2. **Investigation**: Check backtest report for data corruption
3. **Fix**: Recalculate metrics using `src.backtest.metrics.calculate_metrics()`
4. **Prevention**: Enable metric validation in iteration loop (already integrated)

**Manual Recalculation:**
```python
from src.backtest.metrics import calculate_metrics

# Recalculate from backtest result
correct_metrics = calculate_metrics(backtest_result)
print(f"Corrected Sharpe: {correct_metrics.sharpe_ratio}")
```

---

### Issue 2.2: Missing Required Metrics

**Symptom:**
```
KeyError: 'calmar_ratio' not found in metrics dictionary
```

**Root Cause:** Backtest execution didn't generate all required metrics (introduced in Phase 3).

**Diagnosis:**
```python
# Check which metrics are present
metrics = execution_result['metrics']
required = ['sharpe_ratio', 'calmar_ratio', 'max_drawdown', 'annual_return']
missing = [m for m in required if m not in metrics]
print(f"Missing metrics: {missing}")
```

**Solution:**
1. **Calculate missing metric manually:**
```python
from src.backtest.metrics import calculate_calmar_ratio

annual_return = metrics['annual_return']
max_drawdown = metrics['max_drawdown']
calmar = calculate_calmar_ratio(annual_return, max_drawdown)
metrics['calmar_ratio'] = calmar
```

2. **Update extraction logic** in `sandbox_simple.py`:
   - Ensure all metrics are extracted from finlab report
   - Add fallback calculations for missing metrics

3. **Configure multi-objective validation** to handle missing metrics gracefully (see `autonomous_loop.py` lines 996-1005)

---

### Issue 2.3: Sharpe Ratio Cross-Validation Failure

**Symptom:**
```
ValidationError: Sharpe ratio mismatch: calculated=1.23, reported=2.45, difference=1.22
```

**Root Cause:** Incorrect Sharpe calculation formula or annualization factor.

**Diagnosis:**
```python
from src.validation.metric_validator import MetricValidator

validator = MetricValidator()
is_valid, error = validator.cross_validate_sharpe(
    total_return=0.52,
    volatility=0.15,
    sharpe=2.45
)
print(f"Valid: {is_valid}, Error: {error}")
```

**Solution:**
1. **Verify annualization**: Check if returns and volatility are both annualized
2. **Check risk-free rate**: Default is 1%, verify if correct for your market
3. **Adjust tolerance**: Increase `sharpe_tolerance` from 0.1 to 0.2 if calculation methods differ
4. **Fix extraction**: Ensure `sandbox_simple.py` uses same formula as validator

**Correct Formula:**
```python
sharpe = (annualized_return - risk_free_rate) / annualized_volatility
```

---

## Validation Component Failures

### Issue 3.1: Semantic Validation False Positive

**Symptom:**
```
SemanticValidationError: Strategy contains no trading logic (no position generation)
```

**Root Cause:** Overly strict pattern matching in semantic validator.

**Diagnosis:**
```python
from src.validation.semantic_validator import SemanticValidator

validator = SemanticValidator()
code = "..."  # Your generated strategy code
is_valid, errors = validator.validate_strategy(code)

# Check which patterns failed
for error in errors:
    print(f"Failed check: {error}")
```

**Solution:**
1. **Review generated code**: Verify if trading logic actually exists
2. **Update patterns**: Adjust regex patterns in `semantic_validator.py` to be less strict
3. **Add alternative patterns**: Support different coding styles (e.g., `positions = ...` vs `position = ...`)
4. **Disable check temporarily**: Set `semantic_validation_enabled: false` in config

**Known False Positives:**
- Code uses `data.get('close')` instead of `data['close']`
- Position generation is in a function call rather than inline
- Uses alternative finlab APIs (e.g., `fast_get` instead of `get`)

---

### Issue 3.2: Preservation Validation Failure

**Symptom:**
```
PreservationValidationError: Critical parameter 'lookback_period' missing from generated code
```

**Root Cause:** LLM failed to preserve champion strategy patterns during generation.

**Diagnosis:**
```python
from src.validation.preservation_validator import PreservationValidator

validator = PreservationValidator()
is_preserved, report = validator.validate_preservation(
    generated_code="...",
    champion=champion_strategy,
    execution_metrics=None
)

print(f"Preserved: {is_preserved}")
print(f"Missing params: {report.missing_params}")
print(f"Recommendations: {report.recommendations}")
```

**Solution:**
1. **Immediate**: Retry generation with stronger preservation prompt (already implemented in `autonomous_loop.py` lines 276-310)
2. **Investigation**: Check if parameter was genuinely removed or just renamed
3. **Prompt tuning**: Strengthen evolutionary constraints in prompt
4. **Manual recovery**: Manually add missing parameter to generated code

**Retry with Stronger Constraints:**
```python
# System automatically retries twice with force_preservation=True
# See autonomous_loop.py line 289
```

---

### Issue 3.3: Data Pipeline Integrity Check Failed

**Symptom:**
```
DataIntegrityError: Dataset checksum changed between iterations (expected: abc123, got: def456)
```

**Root Cause:** Finlab data was updated mid-experiment, invalidating reproducibility.

**Diagnosis:**
```bash
# Check data provenance log
python -c "
from src.data.pipeline_integrity import DataPipelineIntegrity
integrity = DataPipelineIntegrity()
provenance = integrity.record_data_provenance(data, iteration_num)
print('Finlab version:', provenance['finlab_version'])
print('Data timestamp:', provenance['data_pull_timestamp'])
print('Checksum:', provenance['dataset_checksum'])
"
```

**Solution:**
1. **Warning**: Log warning but continue iteration (data drift is expected)
2. **Investigation**: Compare checksums to identify which dataset changed
3. **Mitigation**: Lock data version for experiment duration using data caching
4. **Documentation**: Record data version change in experiment notes

**Lock Data Version:**
```python
# Enable data caching to prevent mid-experiment updates
from src.data.cache import DataCache
cache = DataCache()
cache.enable_strict_mode()  # Use cached data only
```

---

## Data Quality Issues

### Issue 4.1: Missing Price Data

**Symptom:**
```
DataError: Missing required column '收盤價' in dataset
KeyError: 'close'
```

**Root Cause:** Finlab API didn't return expected price data column.

**Diagnosis:**
```python
import finlab

# Check available columns
data = finlab.data.get('price:收盤價')
print(f"Columns: {data.columns.tolist()}")
print(f"Shape: {data.shape}")
print(f"Date range: {data.index[0]} to {data.index[-1]}")
```

**Solution:**
1. **Check API key**: Ensure Finlab API key is valid and has data access
2. **Verify subscription**: Confirm your plan includes historical price data
3. **Try alternative key**: Use `price:close` or `price:close_price`
4. **Manual download**: Download CSV from Finlab portal and import manually

**Fallback Data Loading:**
```python
# Use cached data if API fails
from src.data.cache import DataCache
cache = DataCache()
data = cache.get_or_fetch('price:收盤價', fallback_to_cache=True)
```

---

### Issue 4.2: Stale Data Cache

**Symptom:**
```
DataFreshnessWarning: Data is 7 days old (last updated: 2025-10-09)
```

**Root Cause:** Data cache hasn't been refreshed recently.

**Diagnosis:**
```python
from src.data.freshness import DataFreshnessChecker

checker = DataFreshnessChecker()
report = checker.check_all()

for dataset, status in report.items():
    print(f"{dataset}: {status['age_days']} days old, fresh={status['is_fresh']}")
```

**Solution:**
1. **Refresh data**: Run `python scripts/refresh_data.py`
2. **Check update schedule**: Verify cron job is running: `crontab -l`
3. **Manual refresh**: Delete cache and re-fetch: `rm -rf cache/data/ && python scripts/refresh_data.py`

**Configure Freshness Thresholds:**
```yaml
# config/data_freshness.yaml
freshness_thresholds:
  price_data: 1  # days
  fundamental_data: 7  # days
  market_data: 1  # days
```

---

### Issue 4.3: Data Quality Validation Failed

**Symptom:**
```
DataQualityError: Dataset contains 1247 NaN values (12.3% of data)
```

**Root Cause:** Raw Finlab data has missing values that need imputation.

**Diagnosis:**
```python
import pandas as pd

# Analyze missing data
data = finlab.data.get('price:收盤價')
missing_stats = {
    'total_values': data.size,
    'missing_values': data.isna().sum().sum(),
    'missing_pct': (data.isna().sum().sum() / data.size) * 100,
    'missing_by_column': data.isna().sum().to_dict()
}
print(missing_stats)
```

**Solution:**
1. **Forward fill**: Use `data.fillna(method='ffill')` for price data
2. **Drop incomplete**: Remove stocks with >50% missing data
3. **Imputation**: Use industry-specific imputation strategies
4. **Report to Finlab**: If data quality issue is systemic

**Data Cleaning Pipeline:**
```python
# Apply in strategy code
data = finlab.data.get('price:收盤價')

# 1. Forward fill recent missing data (up to 5 days)
data = data.fillna(method='ffill', limit=5)

# 2. Drop stocks with >50% missing data
data = data.loc[:, data.isna().sum() / len(data) < 0.5]

# 3. Drop rows where >20% of stocks are missing
data = data.loc[data.isna().sum(axis=1) / len(data.columns) < 0.2]
```

---

## API Failures

### Issue 5.1: Finlab API Timeout

**Symptom:**
```
TimeoutError: Finlab API request timed out after 30 seconds
```

**Root Cause:** Finlab API is slow or unreachable.

**Diagnosis:**
```bash
# Test API connectivity
curl -I https://api.finlab.tw/v1/health

# Check API status
python -c "import finlab; print(finlab.data.get('price:收盤價').head())"

# Monitor request timing
time python -c "import finlab; finlab.data.get('price:收盤價')"
```

**Solution:**
1. **Increase timeout**: Set `FINLAB_TIMEOUT=60` in environment
2. **Retry with backoff**: Implemented in `src.data.downloader`
3. **Use cache**: Fallback to cached data during API outage
4. **Contact support**: If persistent, report to Finlab support

**Retry Configuration:**
```python
# In src/data/downloader.py
RETRY_CONFIG = {
    'max_retries': 5,
    'initial_delay': 2.0,  # seconds
    'backoff_factor': 2.0,
    'max_delay': 60.0
}
```

---

### Issue 5.2: OpenRouter / Gemini API Rate Limit

**Symptom:**
```
RateLimitError: Rate limit exceeded (429). Retry after 60 seconds.
```

**Root Cause:** Too many API requests in short time period.

**Diagnosis:**
```python
from src.analysis.claude_client import ClaudeClient

# Check circuit breaker state
client = ClaudeClient(api_key='...')
state = client.get_circuit_state()
print(f"Circuit breaker: {state.value}")

# Check request history
# (requires implementing request tracking)
```

**Solution:**
1. **Wait and retry**: System automatically waits (see `claude_client.py` lines 253-263)
2. **Reduce request rate**: Add delay between iterations
3. **Switch provider**: Use alternative LLM provider (Anthropic Claude direct)
4. **Increase quota**: Purchase higher API tier

**Circuit Breaker Recovery:**
```python
# Circuit breaker automatically recovers after timeout
# Manual reset if needed:
from src.analysis.claude_client import ClaudeClient
client = ClaudeClient(api_key='...')
client.reset_circuit()
```

---

### Issue 5.3: Claude API Circuit Breaker Open

**Symptom:**
```
RuntimeError: Circuit breaker is OPEN - Claude API requests are blocked. State: open
```

**Root Cause:** Too many consecutive API failures triggered circuit breaker.

**Diagnosis:**
```python
from src.analysis.claude_client import ClaudeClient

client = ClaudeClient(api_key='...')
state = client.get_circuit_state()
print(f"Current state: {state.value}")

# Check failure count (requires adding logging)
# See circuit breaker implementation in claude_client.py lines 47-131
```

**Solution:**
1. **Wait for auto-recovery**: Circuit breaker will try half-open after 60 seconds
2. **Manual reset**: `client.reset_circuit()` (use cautiously)
3. **Fix root cause**: Check API key validity, network connectivity
4. **Adjust thresholds**: Modify circuit breaker config:

```python
from src.analysis.claude_client import CircuitBreakerConfig

config = CircuitBreakerConfig(
    failure_threshold=10,  # Increase from 5
    timeout_seconds=30,    # Decrease from 60
    success_threshold=2
)
client = ClaudeClient(api_key='...', circuit_breaker_config=config)
```

---

## Performance Problems

### Issue 6.1: Slow Iteration Speed

**Symptom:**
```
Performance Warning: Iteration took 342 seconds (target: <120s)
```

**Root Cause:** Multiple bottlenecks (LLM generation, backtest execution, data loading).

**Diagnosis:**
```bash
# Profile iteration timing
python -m cProfile -o profile.stats scripts/run_mvp.py

# Analyze bottlenecks
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"

# Check component timing from logs
grep "took.*seconds" logs/system.log | tail -20
```

**Solution:**
1. **Optimize LLM calls**: Use faster model (`gemini-2.5-flash` instead of `o3`)
2. **Cache data**: Enable aggressive data caching
3. **Reduce validation**: Disable non-critical validators temporarily
4. **Parallel execution**: Run multiple experiments in parallel (separate processes)

**Performance Tuning:**
```python
# In autonomous_loop.py
PERFORMANCE_CONFIG = {
    'model': 'gemini-2.5-flash',  # Fast model
    'timeout': 60,                # Reduced timeout
    'skip_semantic_validation': True,  # Disable if not critical
    'use_data_cache': True
}
```

---

### Issue 6.2: Memory Leak

**Symptom:**
```
MemoryError: Cannot allocate memory for array
RuntimeWarning: Memory usage exceeded 8GB
```

**Root Cause:** Iteration history growing too large or data not being released.

**Diagnosis:**
```bash
# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.0f} MB')
"

# Check history file size
du -h iteration_history.json

# Profile memory usage
python -m memory_profiler scripts/run_mvp.py
```

**Solution:**
1. **Compact history**: Remove old iteration data: `python scripts/compact_history.py --keep-last=100`
2. **Release data**: Add explicit `del` statements after processing large DataFrames
3. **Increase swap**: Add more swap space (temporary)
4. **Reduce data scope**: Use smaller date range for backtests

**Memory Management:**
```python
# In iteration loop
import gc

# After each iteration
del backtest_result
del metrics
gc.collect()

# Compact history periodically
if iteration_num % 50 == 0:
    history.compact(keep_last=100)
```

---

### Issue 6.3: Database Lock Contention

**Symptom:**
```
StorageError: Database is locked (sqlite3.OperationalError)
```

**Root Cause:** Multiple processes trying to write to SQLite database simultaneously.

**Diagnosis:**
```bash
# Check for multiple processes
ps aux | grep "python.*run_mvp"

# Check database lock
lsof iteration_history.db 2>/dev/null || echo "No locks"

# Check WAL mode
sqlite3 iteration_history.db "PRAGMA journal_mode;"
```

**Solution:**
1. **Enable WAL mode**: `sqlite3 iteration_history.db "PRAGMA journal_mode=WAL;"`
2. **Increase timeout**: Set `timeout=30` in database connection
3. **Retry logic**: Already implemented in `src.storage.manager`
4. **Kill zombie processes**: `pkill -f "python.*run_mvp"`

**Database Configuration:**
```python
# In src/storage/manager.py
import sqlite3

conn = sqlite3.connect(
    'iteration_history.db',
    timeout=30,           # Increased from 5
    check_same_thread=False,
    isolation_level='DEFERRED'  # Reduce lock contention
)
conn.execute('PRAGMA journal_mode=WAL')
```

---

## Configuration Errors

### Issue 7.1: Invalid YAML Syntax

**Symptom:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Root Cause:** Syntax error in `config/learning_system.yaml`.

**Diagnosis:**
```bash
# Validate YAML syntax
python -c "
import yaml
with open('config/learning_system.yaml') as f:
    config = yaml.safe_load(f)
    print('Config valid:', config is not None)
"

# Use online YAML validator if needed
```

**Solution:**
1. **Fix syntax**: Common issues are incorrect indentation or missing colons
2. **Restore default**: Copy from template: `cp config/learning_system.yaml.template config/learning_system.yaml`
3. **Validate before commit**: Add YAML linting to pre-commit hook

**Common YAML Mistakes:**
```yaml
# WRONG: Missing colon
anti_churn
  probation_period: 2

# CORRECT:
anti_churn:
  probation_period: 2

# WRONG: Inconsistent indentation (mixing tabs and spaces)
anti_churn:
  probation_period: 2
    post_probation_threshold: 0.05

# CORRECT: Use 2 spaces consistently
anti_churn:
  probation_period: 2
  post_probation_threshold: 0.05
```

---

### Issue 7.2: Configuration Value Out of Range

**Symptom:**
```
ValidationError: calmar_retention_ratio must be between 0 and 1, got: 1.5
```

**Root Cause:** Invalid configuration value in YAML file.

**Diagnosis:**
```python
import yaml

with open('config/learning_system.yaml') as f:
    config = yaml.safe_load(f)

# Check bounds
mo_config = config['multi_objective']
print(f"calmar_retention_ratio: {mo_config['calmar_retention_ratio']}")
print(f"max_drawdown_tolerance: {mo_config['max_drawdown_tolerance']}")

# Validate ranges
assert 0 <= mo_config['calmar_retention_ratio'] <= 1.0
assert 0 <= mo_config['max_drawdown_tolerance'] <= 5.0
```

**Solution:**
1. **Fix value**: Edit YAML file with valid range
2. **Check documentation**: See inline comments in `config/learning_system.yaml` for valid ranges
3. **Restore defaults**: Copy from template if unsure

**Valid Ranges:**
```yaml
multi_objective:
  calmar_retention_ratio: 0.90    # Range: [0.0, 1.0], recommended: 0.85-0.95
  max_drawdown_tolerance: 1.10    # Range: [1.0, 5.0], recommended: 1.05-1.20

anti_churn:
  probation_period: 2             # Range: [1, 10], recommended: 2-5
  probation_threshold: 0.10       # Range: [0.0, 0.5], recommended: 0.05-0.15
  post_probation_threshold: 0.05  # Range: [0.0, 0.3], recommended: 0.01-0.10
```

---

### Issue 7.3: Missing Configuration File

**Symptom:**
```
FileNotFoundError: config/learning_system.yaml not found
```

**Root Cause:** Configuration file was deleted or project structure changed.

**Diagnosis:**
```bash
# Check if file exists
ls -la config/learning_system.yaml

# Check current directory
pwd

# Search for config file
find . -name "learning_system.yaml"
```

**Solution:**
1. **Create from template**: `cp config/learning_system.yaml.template config/learning_system.yaml`
2. **Restore from git**: `git checkout config/learning_system.yaml`
3. **Check working directory**: Ensure running from project root

**Default Configuration:**
```bash
# Create default config if missing
cat > config/learning_system.yaml << 'EOF'
anti_churn:
  probation_period: 2
  probation_threshold: 0.10
  post_probation_threshold: 0.05
  post_probation_relative_threshold: 0.01
  additive_threshold: 0.02
  min_sharpe_for_champion: 0.5

multi_objective:
  enabled: true
  calmar_retention_ratio: 0.90
  max_drawdown_tolerance: 1.10

features:
  enable_anti_churn: true
  enable_adaptive_tuning: false
EOF
```

---

## Recovery Procedures

### 9.1: Full System Reset

When to use: Corrupted state, unknown error, need fresh start.

```bash
# 1. Backup current state
mkdir -p backups/$(date +%Y%m%d_%H%M%S)
cp -r iteration_history.json champion_strategy.json experiment_configs.json backups/$(date +%Y%m%d_%H%M%S)/

# 2. Clear caches
rm -rf cache/data/
rm -rf __pycache__/
find . -name "*.pyc" -delete

# 3. Reset databases
sqlite3 iteration_history.db "DELETE FROM iterations WHERE iteration_num > 0;"

# 4. Clear generated strategies
rm -f generated_strategy_loop_iter*.py

# 5. Reset configuration
cp config/learning_system.yaml.template config/learning_system.yaml

# 6. Verify system health
python -c "from artifacts.working.modules.autonomous_loop import AutonomousLoop; loop = AutonomousLoop(); print('System OK')"

# 7. Start fresh experiment
python scripts/run_mvp.py --max-iterations 5
```

---

### 9.2: Champion Recovery

When to use: Champion corrupted or accidentally deleted.

```bash
# Option 1: Restore from Hall of Fame
python << 'EOF'
from src.repository.hall_of_fame import HallOfFameRepository
hof = HallOfFameRepository()

# Get best strategy from Hall of Fame
genomes = hof.get_tier_strategies('legendary')
if genomes:
    best = genomes[0]
    print(f"Restored champion from Hall of Fame: Sharpe {best.metrics.get('sharpe_ratio', 0):.4f}")
else:
    print("No legendary strategies in Hall of Fame")
EOF

# Option 2: Restore from backup
ls -t backups/*/champion_strategy.json | head -1 | xargs cp -t .

# Option 3: Rebuild from iteration history
python scripts/rebuild_champion.py --from-history
```

---

### 9.3: Data Corruption Recovery

When to use: Iteration history corrupted, database inconsistent.

```bash
# 1. Validate current state
python << 'EOF'
from artifacts.working.modules.history import IterationHistory
try:
    history = IterationHistory()
    records = history.get_all_records()
    print(f"History valid: {len(records)} records")
except Exception as e:
    print(f"History corrupted: {e}")
EOF

# 2. If corrupted, restore from backup
cp iteration_history.json.bak iteration_history.json

# 3. If no backup, rebuild from database
python scripts/rebuild_history.py --from-database

# 4. Verify integrity
python scripts/validate_history.py

# 5. Create fresh backup
cp iteration_history.json iteration_history.json.bak
```

---

### 9.4: Experiment Resume After Crash

When to use: System crashed mid-experiment, need to resume.

```bash
# 1. Check last successful iteration
python -c "
from artifacts.working.modules.history import IterationHistory
h = IterationHistory()
records = h.get_all_records()
if records:
    last = records[-1]
    print(f'Last iteration: {last.iteration_num}')
    print(f'Success: {last.execution_success}')
else:
    print('No records found')
"

# 2. Check for partial data
ls -lh generated_strategy_loop_iter*.py | tail -5

# 3. Resume from last successful iteration
python scripts/run_mvp.py --resume --start-iteration <last_iteration + 1>

# 4. Or start fresh from last champion
python scripts/run_mvp.py --from-champion --max-iterations 50
```

---

## Monitoring and Logging

### 10.1: Log File Locations

```bash
# System logs
logs/system.log              # Main system log
logs/autonomous_loop.log     # Iteration loop log
logs/validation.log          # Validation subsystem log
logs/api.log                 # API interaction log

# View recent logs
tail -f logs/system.log

# Search for errors
grep -i "error\|exception\|failed" logs/system.log

# Count warnings
grep -c "WARNING" logs/system.log

# View logs for specific iteration
grep "Iteration 42" logs/autonomous_loop.log
```

---

### 10.2: Key Metrics to Monitor

```python
# Monitor these metrics in real-time
from src.monitoring.variance_monitor import VarianceMonitor

monitor = VarianceMonitor()

# 1. Champion staleness
last_champion_update = monitor.get_last_champion_update_iteration()
print(f"Iterations since champion update: {current_iteration - last_champion_update}")

# 2. Success rate (target: >80%)
success_rate = monitor.get_success_rate()
print(f"Success rate: {success_rate:.1%}")

# 3. Convergence indicator
variance = monitor.get_recent_variance()
print(f"Recent variance: {variance:.4f} (target: <0.1)")

# 4. Validation failure rate (target: <10%)
validation_failures = monitor.get_validation_failure_rate()
print(f"Validation failures: {validation_failures:.1%}")

# 5. API circuit breaker state
from src.analysis.claude_client import ClaudeClient
client = ClaudeClient(api_key='...')
print(f"Circuit breaker: {client.get_circuit_state().value}")
```

---

### 10.3: Health Check Script

Create `scripts/health_check.py`:

```python
#!/usr/bin/env python3
"""System health check script."""

import sys
from datetime import datetime, timedelta

def check_health():
    """Run comprehensive health check."""
    issues = []

    # 1. Check API connectivity
    try:
        import finlab
        finlab.data.get('price:收盤價').head()
    except Exception as e:
        issues.append(f"Finlab API: {e}")

    # 2. Check iteration history
    try:
        from artifacts.working.modules.history import IterationHistory
        h = IterationHistory()
        records = h.get_all_records()
        if len(records) == 0:
            issues.append("Iteration history: Empty")
    except Exception as e:
        issues.append(f"Iteration history: {e}")

    # 3. Check champion
    try:
        from artifacts.working.modules.autonomous_loop import AutonomousLoop
        loop = AutonomousLoop()
        if loop.champion is None:
            issues.append("Champion: Not found")
    except Exception as e:
        issues.append(f"Champion: {e}")

    # 4. Check data freshness
    try:
        from src.data.freshness import DataFreshnessChecker
        checker = DataFreshnessChecker()
        report = checker.check_all()
        stale = [k for k, v in report.items() if not v['is_fresh']]
        if stale:
            issues.append(f"Stale data: {', '.join(stale)}")
    except Exception as e:
        issues.append(f"Data freshness: {e}")

    # 5. Check database
    try:
        from src.storage.manager import StorageManager
        s = StorageManager()
        s.health_check()
    except Exception as e:
        issues.append(f"Database: {e}")

    # Print report
    print("="*60)
    print("SYSTEM HEALTH CHECK")
    print("="*60)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  ❌ {issue}")
        print()
        print(f"Health: DEGRADED ({len(issues)} issues)")
        return 1
    else:
        print("✅ All checks passed")
        print()
        print("Health: HEALTHY")
        return 0

if __name__ == '__main__':
    sys.exit(check_health())
```

Run health check:
```bash
python scripts/health_check.py
```

---

### 10.4: Alert Configuration

Configure alerts in `config/monitoring.yaml`:

```yaml
alerts:
  # Email alerts
  email:
    enabled: true
    recipients:
      - admin@example.com
    smtp_host: smtp.gmail.com
    smtp_port: 587

  # Slack alerts
  slack:
    enabled: false
    webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL

  # Alert conditions
  conditions:
    # Champion staleness
    - type: champion_staleness
      threshold: 100  # iterations
      severity: warning

    # Success rate drop
    - type: success_rate
      threshold: 0.5  # 50%
      window: 20      # iterations
      severity: critical

    # API circuit breaker open
    - type: circuit_breaker_open
      severity: critical

    # Data freshness
    - type: data_stale
      threshold: 7  # days
      severity: warning

    # Memory usage
    - type: memory_usage
      threshold: 0.9  # 90%
      severity: warning
```

---

## Additional Resources

### Documentation
- **Architecture**: `docs/architecture/SYSTEM_DESIGN.md`
- **Configuration Reference**: `config/learning_system.yaml` (inline comments)
- **API Reference**: `docs/API_REFERENCE.md`
- **Migration Guide**: `docs/MIGRATION_GUIDE.md`

### Scripts
- **Health Check**: `scripts/health_check.py`
- **Data Refresh**: `scripts/refresh_data.py`
- **History Compact**: `scripts/compact_history.py`
- **Champion Rebuild**: `scripts/rebuild_champion.py`

### Support
- **GitHub Issues**: https://github.com/your-repo/issues
- **Finlab Support**: support@finlab.tw
- **Claude API Status**: https://status.anthropic.com

---

## Appendix: Error Message Reference

### Error Code Mapping

| Error Code | Component | Severity | Description |
|------------|-----------|----------|-------------|
| E1001 | Template | High | Template not found in registry |
| E1002 | Template | Medium | Template parameter mismatch |
| E1003 | Template | High | Template generation timeout |
| E2001 | Metrics | High | Impossible metric combination detected |
| E2002 | Metrics | Medium | Missing required metrics |
| E2003 | Metrics | Medium | Sharpe cross-validation failure |
| E3001 | Validation | Medium | Semantic validation false positive |
| E3002 | Validation | High | Preservation validation failure |
| E3003 | Validation | Low | Data pipeline integrity check failed |
| E4001 | Data | High | Missing price data |
| E4002 | Data | Low | Stale data cache |
| E4003 | Data | Medium | Data quality validation failed |
| E5001 | API | Medium | Finlab API timeout |
| E5002 | API | High | OpenRouter/Gemini rate limit |
| E5003 | API | Critical | Claude circuit breaker open |
| E6001 | Performance | Low | Slow iteration speed |
| E6002 | Performance | High | Memory leak detected |
| E6003 | Performance | Medium | Database lock contention |
| E7001 | Config | High | Invalid YAML syntax |
| E7002 | Config | High | Configuration value out of range |
| E7003 | Config | Critical | Missing configuration file |

---

**Version History:**
- v1.0 (2025-10-16): Initial release
- Next update: Add automated diagnostic tools and self-healing procedures

**Contributors:** Claude Code System, Finlab Development Team
