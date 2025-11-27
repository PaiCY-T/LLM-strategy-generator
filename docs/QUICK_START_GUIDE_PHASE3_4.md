# Quick Start Guide: Phase 3 & 4 Features

**Advanced Optimization with TPE, TTPT, and Experiment Tracking**

---

## Installation

```bash
# Install required dependencies
pip install optuna pandas numpy

# Verify installation
python3 -c "import optuna; print(f'Optuna {optuna.__version__} installed')"
```

---

## Basic Usage

### 1. TPE Optimization (Simplest)

```python
from src.learning.optimizer import TPEOptimizer

# Initialize optimizer
optimizer = TPEOptimizer()

# Define your backtest objective
def backtest_objective(params):
    """Your backtest function returning Sharpe ratio."""
    lookback = params['lookback']
    threshold = params['threshold']

    # ... run backtest with parameters ...
    sharpe_ratio = run_backtest(lookback, threshold)

    return sharpe_ratio

# Run optimization
result = optimizer.optimize(
    objective_fn=backtest_objective,
    param_space={
        'lookback': ('int', 10, 50),
        'threshold': ('float', 0.01, 0.1)
    },
    n_trials=20
)

print(f"Best Sharpe: {result['best_value']:.3f}")
print(f"Best Params: {result['best_params']}")
```

---

### 2. Template-Based Optimization

```python
from src.learning.optimizer import TPEOptimizer

optimizer = TPEOptimizer()

# Optimize using built-in template
result = optimizer.optimize_with_template(
    template_name='Momentum',
    objective_fn=backtest_objective,
    n_trials=30,
    asset_universe=['2330.TW', '2317.TW'],
    start_date='2023-01-01',
    end_date='2023-12-31'
)

# Access optimized strategy code
print(result['best_strategy_code'])
```

**Available Templates**:
- `Momentum` - Trend-following strategy
- `MeanReversion` - Mean reversion strategy
- `BreakoutTrend` - Breakout detection
- `VolatilityAdaptive` - Volatility-based
- `DualMomentum` - Dual momentum
- `RegimeAdaptive` - Market regime aware

---

### 3. IS/OOS Validation

```python
# Detect overfitting with IS/OOS split
result = optimizer.optimize_with_validation(
    template_name='Momentum',
    objective_fn=backtest_objective,
    n_trials=30,
    # In-Sample period
    is_asset_universe=['2330.TW'],
    is_start_date='2023-01-01',
    is_end_date='2023-06-30',
    # Out-of-Sample period
    oos_start_date='2023-07-01',
    oos_end_date='2023-12-31',
    # Overfitting threshold (30%)
    degradation_threshold=0.30
)

print(f"IS Sharpe: {result['is_value']:.3f}")
print(f"OOS Sharpe: {result['oos_value']:.3f}")
print(f"Degradation: {result['degradation']:.1%}")
print(f"Overfitting: {result['overfitting_detected']}")
```

---

### 4. Runtime TTPT Monitoring (Recommended)

```python
import pandas as pd
from src.learning.optimizer import TPEOptimizer

# Prepare market data
dates = pd.date_range('2023-01-01', periods=252, freq='D')
data = {
    'close': pd.DataFrame({
        '2330.TW': [...],  # Your price data
        '2317.TW': [...]
    }, index=dates)
}

# Define strategy function for TTPT validation
def momentum_strategy(data_dict, params):
    """Strategy that generates signals."""
    close = data_dict['close']
    lookback = params['lookback']

    # Calculate signals
    ma = close.rolling(window=lookback).mean()
    signals = (close > ma).astype(float)

    return signals

# Run optimization with TTPT monitoring
optimizer = TPEOptimizer()

result = optimizer.optimize_with_runtime_ttpt(
    objective_fn=backtest_objective,
    strategy_fn=momentum_strategy,
    data=data,
    n_trials=50,
    param_space={
        'lookback': ('int', 10, 50),
        'threshold': ('float', 0.01, 0.1)
    },
    checkpoint_interval=5  # Validate every 5 trials
)

# Review TTPT results
print(f"Best Sharpe: {result['best_value']:.3f}")
print(f"\nTTPT Summary:")
print(f"  Total Validations: {result['ttpt_summary']['total_validations']}")
print(f"  Total Violations: {result['ttpt_summary']['total_violations']}")
print(f"  Violation Rate: {result['ttpt_summary']['violation_rate']:.1%}")

if result['ttpt_summary']['violation_rate'] > 0.2:
    print("⚠️  WARNING: High violation rate detected!")
else:
    print("✅ Strategy validated - No significant look-ahead bias")
```

---

### 5. Experiment Tracking

```python
from src.tracking.experiment_tracker import ExperimentTracker

# Initialize tracker
tracker = ExperimentTracker(db_path="experiments.db")

# Create experiment
exp_id = tracker.create_experiment(
    name="Momentum Optimization Run 1",
    template="Momentum",
    mode="tpe_runtime_ttpt",
    config={
        'n_trials': 50,
        'checkpoint_interval': 5,
        'asset_universe': ['2330.TW', '2317.TW']
    }
)

# Run optimization (as above)
result = optimizer.optimize_with_runtime_ttpt(...)

# Log trials automatically
for i, trial in enumerate(result['trials']):
    tracker.log_trial(
        experiment_id=exp_id,
        trial_number=i+1,
        params=trial['params'],
        performance=trial['performance']
    )

# Log TTPT summary
tracker.log_experiment_summary(
    experiment_id=exp_id,
    summary={
        'ttpt_summary': result['ttpt_summary'],
        'best_sharpe': result['best_value'],
        'n_trials_completed': len(result['trials'])
    }
)

print(f"Experiment logged with ID: {exp_id}")
```

---

### 6. Query Experiments

```python
# List all experiments
experiments = tracker.list_experiments()

for exp in experiments:
    print(f"ID: {exp['id']} | Name: {exp['name']} | Template: {exp['template']}")

# Get specific experiment
experiment = tracker.get_experiment(exp_id)

# Get all trials for experiment
trials = tracker.get_trials(exp_id)

# Filter experiments by violation rate
clean_experiments = tracker.filter_experiments(
    max_violation_rate=0.1  # Only experiments with <10% violations
)

# Export to DataFrame for analysis
import pandas as pd
df = tracker.export_to_dataframe(exp_id)

# Analyze performance
best_trial = df.loc[df['sharpe'].idxmax()]
print(f"Best trial: {best_trial['trial_number']}")
print(f"Best params: {best_trial['params']}")
```

---

### 7. Compare Experiments

```python
# Compare multiple experiments
exp_ids = [1, 2, 3]
comparison = tracker.compare_experiments(exp_ids)

for exp in comparison:
    print(f"{exp['name']:30s} | Sharpe: {exp['best_sharpe']:.3f}")

# Get performance improvement
improvement = tracker.get_performance_improvement(exp_id)
print(f"Improvement: {improvement:.1%}")
```

---

## Advanced Usage

### Custom TTPT Configuration

```python
from src.validation.runtime_ttpt_monitor import RuntimeTTPTMonitor

# Custom TTPT settings
monitor = RuntimeTTPTMonitor(
    checkpoint_interval=10,  # Validate every 10 trials
    ttpt_config={
        'shift_days': [1, 3, 5, 7, 10],  # More time shifts
        'tolerance': 0.03,  # Tighter 3% tolerance
        'min_correlation': 0.97  # Higher correlation threshold
    },
    log_dir='ttpt_logs',
    alert_on_violation=True  # Print alerts
)

# Use in optimization
result = optimizer.optimize_with_runtime_ttpt(
    objective_fn=backtest_objective,
    strategy_fn=momentum_strategy,
    data=data,
    n_trials=100,
    param_space={...},
    ttpt_monitor=monitor  # Pass custom monitor
)
```

---

### Parallel Trial Execution (Future)

```python
# Coming soon: Parallel optimization
result = optimizer.optimize_parallel(
    objective_fn=backtest_objective,
    param_space={...},
    n_trials=100,
    n_jobs=4  # Use 4 CPU cores
)
```

---

## Configuration Files

### config/optimization.yaml

```yaml
tpe_optimizer:
  n_trials: 50
  checkpoint_interval: 5

ttpt_config:
  shift_days: [1, 3, 5, 7]
  tolerance: 0.05
  min_correlation: 0.95

experiment_tracking:
  backend: sqlite
  db_path: experiments.db

templates:
  - Momentum
  - MeanReversion
  - BreakoutTrend
  - VolatilityAdaptive
  - DualMomentum
  - RegimeAdaptive
```

Load config:
```python
import yaml

with open('config/optimization.yaml') as f:
    config = yaml.safe_load(f)

optimizer = TPEOptimizer(**config['tpe_optimizer'])
```

---

## Troubleshooting

### TTPT Violation Warnings

**Problem**: High TTPT violation rate (>20%)

**Solutions**:
1. Check for future data leakage in strategy code
2. Review `.shift()` operations (negative shifts are look-ahead)
3. Inspect rolling window calculations
4. Verify data alignment

### Slow Optimization

**Problem**: Optimization taking too long

**Solutions**:
1. Enable data caching: `TemplateLibrary(cache_data=True)`
2. Reduce `n_trials` for initial exploration
3. Use simpler objective function
4. Consider parallel execution (future feature)

### Database Errors

**Problem**: SQLite locked or permission errors

**Solutions**:
1. Check file permissions on `db_path`
2. Use different database path
3. Try JSON backend: `ExperimentTracker(backend='json')`

---

## Best Practices

### 1. Start Simple
```python
# Begin with basic TPE optimization
result = optimizer.optimize(objective_fn, param_space, n_trials=20)
```

### 2. Add Template Support
```python
# Use templates for better initial guesses
result = optimizer.optimize_with_template(
    template_name='Momentum',
    objective_fn=backtest_objective,
    n_trials=30
)
```

### 3. Enable TTPT Monitoring
```python
# Add look-ahead bias detection
result = optimizer.optimize_with_runtime_ttpt(
    objective_fn=backtest_objective,
    strategy_fn=strategy_function,
    data=market_data,
    n_trials=50,
    checkpoint_interval=5
)
```

### 4. Track Everything
```python
# Log all experiments for analysis
tracker = ExperimentTracker()
exp_id = tracker.create_experiment(...)
# ... run optimization ...
tracker.log_trial(...)
```

---

## Common Patterns

### Pattern 1: Quick Exploration

```python
# Fast initial exploration
optimizer = TPEOptimizer()

for template in ['Momentum', 'MeanReversion', 'BreakoutTrend']:
    result = optimizer.optimize_with_template(
        template_name=template,
        objective_fn=backtest_objective,
        n_trials=10  # Quick exploration
    )
    print(f"{template:20s} | Sharpe: {result['best_value']:.3f}")
```

### Pattern 2: Deep Dive

```python
# Thorough optimization with validation
result = optimizer.optimize_with_runtime_ttpt(
    objective_fn=backtest_objective,
    strategy_fn=strategy_function,
    data=market_data,
    n_trials=100,  # Thorough search
    checkpoint_interval=10
)

# Validate with IS/OOS split
validation_result = optimizer.optimize_with_validation(
    template_name='Momentum',
    objective_fn=backtest_objective,
    n_trials=50,
    is_start_date='2023-01-01',
    is_end_date='2023-06-30',
    oos_start_date='2023-07-01',
    oos_end_date='2023-12-31'
)
```

### Pattern 3: Production Workflow

```python
# Complete production workflow
tracker = ExperimentTracker()
optimizer = TPEOptimizer()

# 1. Create experiment
exp_id = tracker.create_experiment(
    name=f"Production Run {datetime.now():%Y%m%d}",
    template="Momentum",
    mode="tpe_runtime_ttpt"
)

# 2. Run optimization
result = optimizer.optimize_with_runtime_ttpt(
    objective_fn=backtest_objective,
    strategy_fn=strategy_function,
    data=market_data,
    n_trials=50,
    checkpoint_interval=5
)

# 3. Log results
for trial in result['trials']:
    tracker.log_trial(exp_id, ...)

# 4. Validate TTPT
if result['ttpt_summary']['violation_rate'] < 0.1:
    print("✅ Strategy approved for production")
else:
    print("❌ Strategy rejected - high violation rate")
```

---

## Next Steps

1. **Read**: [Phase 3 & 4 Completion Summary](PHASE_3_4_COMPLETION_SUMMARY.md)
2. **Explore**: Run examples in `examples/` directory
3. **Experiment**: Try different templates and parameters
4. **Monitor**: Check TTPT violation rates
5. **Analyze**: Use experiment tracker for insights

---

**Questions?** See the full documentation in `docs/` directory.
