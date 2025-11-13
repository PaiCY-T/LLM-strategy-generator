# Learning System User Guide

**Version**: 1.0
**Last Updated**: 2025-10-16
**Status**: Phase 2 Complete - Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Phase 2 Components](#phase-2-components)
   - [VarianceMonitor](#variancemonitor)
   - [PreservationValidator](#preservationvalidator)
   - [AntiChurnManager](#antichurnmanager)
   - [RollbackManager](#rollbackmanager)
4. [Configuration Guide](#configuration-guide)
5. [Rollback Operations](#rollback-operations)
6. [Monitoring & Diagnostics](#monitoring--diagnostics)
7. [Production Best Practices](#production-best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Topics](#advanced-topics)

---

## Overview

The Learning System is an autonomous trading strategy optimization engine that uses LLM-based learning to iteratively improve strategies through experimentation and feedback. **Phase 2 enhancements** add critical stability features to prevent regression, detect convergence, and enable safe recovery operations.

### Phase 2 Features

- **Convergence Monitoring**: Track Sharpe ratio variance to detect learning convergence (σ < 0.5)
- **Enhanced Preservation**: Behavioral similarity checks to prevent false positive preservation violations
- **Anti-Churn Configuration**: Externalized thresholds to prevent excessive champion updates (target 10-20%)
- **Rollback Mechanism**: Restore previous champion strategies with validation and audit trail

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Autonomous Loop                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Generation → Execution → Validation → Update      │    │
│  └────────────────────────────────────────────────────┘    │
│         ▲              ▲             ▲           ▲          │
│         │              │             │           │          │
│    ┌────┴────┐    ┌───┴────┐   ┌───┴───┐  ┌───┴────┐     │
│    │ History │    │Sandbox │   │Metrics│  │Champion│     │
│    │ Manager │    │        │   │Valida-│  │Manager │     │
│    └─────────┘    └────────┘   │tion   │  └────────┘     │
│                                 └───────┘                   │
└─────────────────────────────────────────────────────────────┘
         │              │             │           │
    ┌────┴────┐    ┌───┴────┐   ┌───┴───┐  ┌───┴────┐
    │Variance │    │Preserv-│   │Anti-  │  │Rollback│
    │Monitor  │    │ation   │   │Churn  │  │Manager │
    │(Phase 2)│    │Validat │   │Manager│  │(Phase 2│
    └─────────┘    │or(Ph2) │   │(Ph2)  │  └────────┘
                   └────────┘   └───────┘
```

---

## Quick Start

### Basic Usage

```bash
# Run 5-iteration test (basic validation)
python run_5iteration_test.py

# Run 50-iteration test with Phase 2 monitoring
python run_50iteration_test.py

# Run 200-iteration production validation
python run_200iteration_test.py
```

### Enable Phase 2 Features

```python
from artifacts.working.modules.autonomous_loop import AutonomousLoop
from src.monitoring.variance_monitor import VarianceMonitor
from src.validation.preservation_validator import PreservationValidator
from src.config.anti_churn_manager import AntiChurnManager

# Initialize autonomous loop with Phase 2 components
loop = AutonomousLoop(
    model="claude-sonnet-4.1",
    prompt_template_path="prompt_template_v3_comprehensive.txt"
)

# Phase 2 components are automatically initialized:
# - loop.variance_monitor (convergence tracking)
# - loop.anti_churn_mgr (dynamic thresholds)
# Preservation validator used in _validate_preservation()

# Run iterations
for i in range(50):
    result = loop.run_iteration(i, data)

    # Check convergence status
    report = loop.variance_monitor.generate_convergence_report()
    print(f"Convergence status: {report['convergence_status']}")
```

### Configuration

```yaml
# config/learning_system.yaml
anti_churn:
  probation_period: 2              # Higher threshold for new champions
  probation_threshold: 0.10        # 10% improvement during probation
  post_probation_threshold: 0.05   # 5% improvement after probation
  additive_threshold: 0.02         # +0.02 Sharpe absolute improvement
  min_sharpe_for_champion: 0.5     # Minimum Sharpe to become champion
  target_update_frequency: 0.15    # Target 15% update rate (10-20% range)
```

---

## Phase 2 Components

### VarianceMonitor

**Purpose**: Track Sharpe ratio variance over time to detect learning convergence or instability.

**Location**: `src/monitoring/variance_monitor.py`

#### Configuration

```python
from src.monitoring.variance_monitor import VarianceMonitor

# Initialize with custom alert threshold
monitor = VarianceMonitor(alert_threshold=0.8)  # Default: 0.8
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `alert_threshold` | float | 0.8 | Variance threshold triggering instability alerts |

#### Usage

```python
# Update with iteration results
monitor.update(iteration_num=5, sharpe=2.3)

# Get rolling variance (default 10-iteration window)
variance = monitor.get_rolling_variance(window=10)
print(f"σ = {variance:.4f}")

# Check alert condition (σ > threshold for 5+ consecutive iterations)
alert_triggered, message = monitor.check_alert_condition()
if alert_triggered:
    print(f"⚠️ Instability detected: {message}")

# Generate convergence report
report = monitor.generate_convergence_report()
print(f"Status: {report['convergence_status']}")
print(f"Convergence iteration: {report['convergence_iteration']}")
print(f"Current σ: {report['current_variance']:.4f}")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

#### Convergence Report Schema

```python
{
    'variance_trend': [(iter, variance), ...],  # Historical variance
    'convergence_status': 'converged',          # converged | converging | unstable
    'convergence_iteration': 15,                # First iter with σ < 0.5 after iter 10
    'current_variance': 0.35,                   # Latest rolling variance
    'total_iterations': 50,                     # Total iterations tracked
    'recommendations': [                        # Actionable recommendations
        "System converged at iteration 15. Monitor for regression..."
    ]
}
```

#### Adjusting Variance Thresholds

Edit `src/monitoring/variance_monitor.py` or pass at initialization:

```python
# More sensitive to instability (lower threshold)
monitor = VarianceMonitor(alert_threshold=0.6)

# Less sensitive (higher threshold)
monitor = VarianceMonitor(alert_threshold=1.0)
```

**Guidelines**:
- **σ < 0.5**: Converged (stable learning)
- **0.5 ≤ σ < 0.8**: Converging (normal learning)
- **σ ≥ 0.8**: Unstable (requires attention)

---

### PreservationValidator

**Purpose**: Validate champion preservation with behavioral similarity checks to reduce false positives.

**Location**: `src/validation/preservation_validator.py`

#### Configuration

```python
from src.validation.preservation_validator import PreservationValidator

# Initialize with tolerance settings
validator = PreservationValidator(
    sharpe_tolerance=0.10,          # ±10% Sharpe deviation allowed
    turnover_tolerance=0.20,        # ±20% turnover deviation allowed
    concentration_tolerance=0.15    # ±15% concentration deviation allowed
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sharpe_tolerance` | float | 0.10 | Maximum allowed Sharpe ratio deviation (±10%) |
| `turnover_tolerance` | float | 0.20 | Maximum allowed portfolio turnover deviation (±20%) |
| `concentration_tolerance` | float | 0.15 | Maximum allowed position concentration deviation (±15%) |

#### Usage

```python
# Validate preservation
is_preserved, report = validator.validate_preservation(
    generated_code=new_strategy_code,
    champion=current_champion,
    execution_metrics=execution_result  # Optional: enables behavioral checks
)

# Check result
if is_preserved:
    print(f"✅ {report.summary()}")
else:
    print(f"❌ {report.summary()}")
    print("Violations:")
    for param, (passed, reason) in report.parameter_checks.items():
        if not passed:
            print(f"  - {param}: {reason}")

    print(f"False positive risk: {report.false_positive_risk:.1%}")

    if report.requires_manual_review:
        print("⚠️ Manual review recommended")
        for rec in report.recommendations:
            print(f"  - {rec}")
```

#### PreservationReport Schema

```python
@dataclass
class PreservationReport:
    is_preserved: bool                           # Overall preservation status

    # Parameter preservation
    parameter_checks: Dict[str, Tuple[bool, str]]  # {param: (passed, reason)}
    critical_params_preserved: List[str]           # Parameters that passed
    missing_params: List[str]                      # Missing critical parameters

    # Behavioral similarity
    behavioral_checks: List[BehavioralCheck]       # Individual behavior checks
    behavioral_similarity_score: float             # 0.0-1.0 (0=different, 1=identical)

    # False positive detection
    false_positive_risk: float                     # 0.0-1.0 risk score
    false_positive_indicators: List[str]           # Reasons for risk

    # Recommendations
    recommendations: List[str]                     # Actionable guidance
    requires_manual_review: bool                   # High-risk flag
    timestamp: str                                 # ISO format
```

#### Adjusting Tolerances

**Example: Stricter Preservation (Production)**
```python
validator = PreservationValidator(
    sharpe_tolerance=0.05,      # ±5% (stricter)
    turnover_tolerance=0.10,    # ±10% (stricter)
    concentration_tolerance=0.10 # ±10% (stricter)
)
```

**Example: Looser Preservation (Experimentation)**
```python
validator = PreservationValidator(
    sharpe_tolerance=0.15,      # ±15% (more lenient)
    turnover_tolerance=0.30,    # ±30% (more lenient)
    concentration_tolerance=0.20 # ±20% (more lenient)
)
```

**Guidelines**:
- **Sharpe tolerance**: 5-15% (production: 5-10%, experimentation: 10-15%)
- **Turnover tolerance**: 10-30% (production: 10-20%, experimentation: 20-30%)
- **Concentration tolerance**: 10-20% (production: 10-15%, experimentation: 15-20%)

---

### AntiChurnManager

**Purpose**: Manage champion update thresholds with probation period to prevent excessive churn.

**Location**: `src/config/anti_churn_manager.py`
**Configuration File**: `config/learning_system.yaml`

#### Configuration

```yaml
# config/learning_system.yaml
anti_churn:
  # === PROBATION SYSTEM ===
  probation_period: 2              # Iterations before relaxing threshold
  probation_threshold: 0.10        # 10% improvement during probation
  post_probation_threshold: 0.05   # 5% improvement after probation

  # === HYBRID THRESHOLD SYSTEM ===
  # Accept EITHER relative OR absolute improvement
  post_probation_relative_threshold: 0.01  # 1% relative improvement
  additive_threshold: 0.02                 # 0.02 absolute Sharpe improvement
  threshold_logging_enabled: true          # Log which threshold was used

  # === CHAMPION STALENESS MECHANISM ===
  staleness:
    staleness_check_interval: 50        # Check every 50 iterations
    staleness_cohort_percentile: 0.10   # Top 10% of recent strategies
    staleness_min_cohort_size: 5        # Minimum 5 strategies for valid cohort
    staleness_enabled: true             # Enable staleness mechanism

  # === MULTI-OBJECTIVE VALIDATION ===
  # Require ALL criteria to pass for champion update
  multi_objective:
    enabled: true                       # Enable multi-objective validation
    calmar_retention_ratio: 0.90        # New Calmar ≥ 90% of old Calmar
    max_drawdown_tolerance: 1.10        # New drawdown ≤ 110% of old drawdown

  # === GENERAL SETTINGS ===
  min_sharpe_for_champion: 0.5     # Minimum Sharpe to become champion
  target_update_frequency: 0.15    # Target 15% update rate (10-20% range)
```

#### Usage

```python
from src.config.anti_churn_manager import AntiChurnManager

# Initialize (loads config/learning_system.yaml)
manager = AntiChurnManager()

# Get dynamic threshold based on probation period
required_improvement = manager.get_required_improvement(
    current_iteration=10,
    champion_iteration=8
)
# Returns: 0.10 (probation) or 0.05 (post-probation)

# Get additive threshold (Phase 3 hybrid threshold)
additive = manager.get_additive_threshold()
# Returns: 0.02 (absolute Sharpe improvement)

# Track champion updates
manager.track_champion_update(
    iteration_num=10,
    was_updated=True,
    old_sharpe=2.0,
    new_sharpe=2.15,
    threshold_used=0.10
)

# Analyze update frequency (check against 10-20% target)
update_freq, recommendations = manager.analyze_update_frequency(window=50)
print(f"Update frequency: {update_freq*100:.1f}%")
for rec in recommendations:
    print(f"  - {rec}")

# Get recent updates summary
print(manager.get_recent_updates_summary(count=10))
```

#### Tuning Anti-Churn Thresholds

**Problem**: Champion update frequency outside target range (10-20%)

**Solution**: Adjust thresholds in `config/learning_system.yaml`

##### Scenario 1: Excessive Churn (>20% update rate)

```yaml
anti_churn:
  probation_period: 3                # Increase from 2 to 3
  probation_threshold: 0.12          # Increase from 0.10 to 0.12
  post_probation_threshold: 0.07     # Increase from 0.05 to 0.07
  additive_threshold: 0.03           # Increase from 0.02 to 0.03
```

**Effect**: Higher barriers → fewer updates → reduced churn

##### Scenario 2: Champion Stagnation (<10% update rate)

```yaml
anti_churn:
  probation_period: 1                # Decrease from 2 to 1
  probation_threshold: 0.08          # Decrease from 0.10 to 0.08
  post_probation_threshold: 0.03     # Decrease from 0.05 to 0.03
  additive_threshold: 0.01           # Decrease from 0.02 to 0.01
```

**Effect**: Lower barriers → more updates → reduced stagnation

##### Tuning Guidelines

| Metric | Target Range | Action if Below | Action if Above |
|--------|--------------|-----------------|-----------------|
| Update frequency | 10-20% | Decrease thresholds by 0.01-0.02 | Increase thresholds by 0.01-0.02 |
| Probation period | 1-3 iterations | Increase by 1 | Decrease by 1 |
| Variance (σ) | <0.5 after iter 20 | Increase thresholds (stabilize) | Decrease thresholds (improve) |

#### Hybrid Threshold System

**Problem**: At high Sharpe ratios (e.g., 2.5), a 5% improvement requires 2.625 (extremely difficult)

**Solution**: Accept EITHER relative OR absolute threshold

```python
# Example: Champion at Sharpe 2.4751
old_sharpe = 2.4751
new_sharpe = 2.50

# Relative threshold (1%): requires 2.4751 * 1.01 = 2.500
relative_required = old_sharpe * (1 + 0.01)  # 2.500

# Absolute threshold (0.02): requires 2.4751 + 0.02 = 2.495
absolute_required = old_sharpe + 0.02  # 2.495

# System accepts 2.50 because it meets BOTH thresholds
# (easier absolute threshold prevents stagnation at high Sharpe)
```

**Configuration**:
```yaml
anti_churn:
  post_probation_relative_threshold: 0.01  # 1% relative
  additive_threshold: 0.02                 # 0.02 absolute
```

#### Champion Staleness Mechanism

**Purpose**: Prevent system from clinging to outdated outlier champions

**How it works**:
1. Every N iterations (`staleness_check_interval`), perform staleness check
2. Build cohort from top X% of recent strategies (`staleness_cohort_percentile`)
3. Calculate median Sharpe ratio of the cohort
4. Compare champion Sharpe vs cohort median
5. If champion < cohort median → DEMOTE champion and promote best cohort strategy

**Example Scenario**:
```
Iteration 6: Champion achieves exceptional Sharpe 2.4751 (outlier)
Iterations 7-56: Champion remains dominant, no better strategies found
Iteration 50: Staleness check triggered
  - Recent cohort (top 10% from iterations 40-50): median Sharpe 1.8
  - Champion Sharpe 2.4751 > cohort median 1.8
  - Result: KEEP champion (still competitive)

Iteration 100: Another staleness check
  - Recent cohort median: 2.6 (system has improved significantly)
  - Champion Sharpe 2.4751 < cohort median 2.6
  - Result: DEMOTE champion, promote best strategy from cohort (Sharpe 2.8)
```

**Configuration Guidelines**:
```yaml
staleness:
  staleness_check_interval: 50        # Lower = more frequent checks
                                      # Higher = allow longer reign
                                      # Typical: 50 (twice per 100 iterations)

  staleness_cohort_percentile: 0.10   # Lower = stricter comparison
                                      # Higher = more lenient
                                      # Typical: 0.10 (top 10%)

  staleness_min_cohort_size: 5        # Minimum strategies for valid comparison
                                      # Typical: 5 (statistical reliability)
```

#### Multi-Objective Validation

**Purpose**: Prevent brittle strategy selection by ensuring balanced risk/return characteristics

**Problem**: A strategy can have high Sharpe but poor risk characteristics (low Calmar, high drawdown)

**Solution**: Require ALL criteria to pass for champion update:
1. **Sharpe**: Pass hybrid threshold (relative OR absolute improvement)
2. **Calmar**: `new_calmar >= old_calmar * calmar_retention_ratio`
3. **Max Drawdown**: `new_mdd <= old_mdd * max_drawdown_tolerance`

**Example Scenarios**:

✅ **ACCEPT**: Sharpe 2.0→2.1 (+5%), Calmar 0.8→0.75 (-6.25%), MDD -15%→-16% (+6.7%)
- Sharpe improves ✓
- Calmar drops <10% ✓
- Drawdown worsens <10% ✓

❌ **REJECT**: Sharpe 2.0→2.1 (+5%), Calmar 0.8→0.65 (-18.75%), MDD -15%→-16% (+6.7%)
- Reason: Calmar drops >10%, fails retention ratio (0.65/0.8 = 81.25% < 90%)

❌ **REJECT**: Sharpe 2.0→2.1 (+5%), Calmar 0.8→0.75 (-6.25%), MDD -15%→-18% (+20%)
- Reason: Drawdown worsens >10%, fails tolerance (18%/15% = 120% > 110%)

**Configuration**:
```yaml
multi_objective:
  enabled: true                       # Feature flag
  calmar_retention_ratio: 0.90        # New Calmar ≥ 90% of old Calmar
  max_drawdown_tolerance: 1.10        # New drawdown ≤ 110% of old drawdown
```

**Tuning Guidelines**:
- **Calmar retention ratio**: 0.85-0.95 (higher = stricter Calmar maintenance)
- **Max drawdown tolerance**: 1.05-1.15 (lower = stricter drawdown control)

---

### RollbackManager

**Purpose**: Restore previous champion strategies with validation and audit trail.

**Location**: `src/recovery/rollback_manager.py`

#### Configuration

```python
from src.repository.hall_of_fame import HallOfFameRepository
from src.recovery.rollback_manager import RollbackManager

# Initialize with Hall of Fame repository
hall_of_fame = HallOfFameRepository()
rollback_mgr = RollbackManager(
    hall_of_fame=hall_of_fame,
    rollback_log_file="rollback_history.json"  # Audit trail file
)
```

#### Usage

##### View Champion History

```python
# Get recent champions
champions = rollback_mgr.get_champion_history(limit=10)

for champ in champions:
    print(f"Iteration {champ.iteration_num}: "
          f"Sharpe {champ.metrics['sharpe_ratio']:.2f} "
          f"({champ.timestamp})")
```

##### Rollback to Specific Iteration

```python
# Rollback with validation
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=5,
    reason="Production issue - reverting to stable version",
    operator="john@example.com",
    data=finlab_data,
    validate=True  # Run validation before rollback
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

##### Validate Rollback Candidate

```python
# Check if champion still works before rollback
is_valid, report = rollback_mgr.validate_rollback_champion(
    champion=target_champion,
    data=finlab_data,
    min_sharpe_threshold=0.5
)

if is_valid:
    print(f"✅ Validation passed: Sharpe {report['current_sharpe']:.2f}")
else:
    print(f"❌ Validation failed: {report['error']}")
```

##### View Rollback History

```python
# Get audit trail
history = rollback_mgr.get_rollback_history(limit=10)

for record in history:
    print(f"{record.timestamp}: "
          f"Iteration {record.from_iteration} → {record.to_iteration}")
    print(f"  Reason: {record.reason}")
    print(f"  Operator: {record.operator}")
    print(f"  Validation: {'✅ PASS' if record.validation_passed else '❌ FAIL'}")
```

#### Command-Line Tool

Use the `rollback_champion.py` CLI tool for interactive rollback:

```bash
# Basic rollback (with validation)
python rollback_champion.py \
    --target-iteration 5 \
    --reason "Production issue - reverting to stable version" \
    --operator "john@example.com"

# Rollback without validation (fast, use cautiously)
python rollback_champion.py \
    --target-iteration 5 \
    --reason "Emergency rollback" \
    --operator "john@example.com" \
    --no-validate
```

#### Rollback Validation

**Validation Checks**:
1. **Execution Success**: Champion code runs without errors
2. **Metrics Availability**: Sharpe ratio and other metrics returned
3. **Minimum Performance**: Sharpe ≥ threshold (default 0.5)
4. **Performance Degradation**: Compare current vs original Sharpe

**Validation Report**:
```python
{
    'iteration_num': 5,
    'original_sharpe': 2.15,
    'current_sharpe': 2.03,
    'sharpe_degradation': 0.12,
    'execution_success': True,
    'execution_error': None,
    'status': 'valid',
    'validation_timestamp': '2025-10-16T10:30:00'
}
```

#### Audit Trail

All rollback operations are logged to `rollback_history.json`:

```json
{
  "rollback_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "from_iteration": 10,
  "to_iteration": 5,
  "reason": "Production issue - reverting to stable version",
  "operator": "john@example.com",
  "timestamp": "2025-10-16T10:30:00",
  "validation_passed": true,
  "validation_report": {
    "iteration_num": 5,
    "current_sharpe": 2.03,
    "status": "valid"
  }
}
```

---

## Configuration Guide

### Configuration Files

| File | Purpose | Components |
|------|---------|------------|
| `config/learning_system.yaml` | Anti-churn configuration | AntiChurnManager, MultiObjective, Staleness |
| `prompt_template_v3_comprehensive.txt` | LLM prompt template | AutonomousLoop |
| `experiment_configs.json` | Experiment snapshots | ExperimentConfigManager |

### Environment Variables

```bash
# Required
export FINLAB_API_TOKEN='your_finlab_token'
export OPENROUTER_API_KEY='your_openrouter_key'
export GOOGLE_API_KEY='your_google_api_key'

# Optional
export VARIANCE_ALERT_THRESHOLD=0.8      # Default: 0.8
export SHARPE_TOLERANCE=0.10             # Default: 0.10
export TURNOVER_TOLERANCE=0.20           # Default: 0.20
export CONCENTRATION_TOLERANCE=0.15      # Default: 0.15
```

### Configuration Priority

1. **Runtime Parameters** (highest priority): Passed to constructors
2. **Environment Variables**: Override config files
3. **Configuration Files**: `config/learning_system.yaml`
4. **Default Values** (lowest priority): Hardcoded in classes

### Example: Custom Configuration

```python
import os
from src.monitoring.variance_monitor import VarianceMonitor
from src.validation.preservation_validator import PreservationValidator
from src.config.anti_churn_manager import AntiChurnManager

# Override defaults via environment
os.environ['VARIANCE_ALERT_THRESHOLD'] = '0.7'

# Or pass directly to constructors
variance_monitor = VarianceMonitor(alert_threshold=0.7)
preservation_validator = PreservationValidator(
    sharpe_tolerance=0.08,
    turnover_tolerance=0.15,
    concentration_tolerance=0.12
)
anti_churn_mgr = AntiChurnManager(config_path="config/custom_learning_system.yaml")
```

---

## Rollback Operations

### When to Use Rollback

**Scenario 1: Production Failure**
- New champion deployed but causes live trading issues
- Immediate rollback to last known good champion

**Scenario 2: Performance Regression**
- Champion metrics degrade significantly
- Rollback to earlier high-performing champion

**Scenario 3: Recovery from Bad Update**
- LLM generated invalid champion that passed validation
- Rollback to stable champion while investigating

### Rollback Workflow

```
1. Identify Problem
   ↓
2. Review Champion History (get_champion_history)
   ↓
3. Select Target Iteration
   ↓
4. Validate Target Champion (validate_rollback_champion)
   ↓ (if valid)
5. Execute Rollback (rollback_to_iteration)
   ↓
6. Verify Recovery
   ↓
7. Update Audit Trail (automatic)
```

### Step-by-Step Example

```python
from src.repository.hall_of_fame import HallOfFameRepository
from src.recovery.rollback_manager import RollbackManager

# Step 1: Initialize manager
hall_of_fame = HallOfFameRepository()
rollback_mgr = RollbackManager(hall_of_fame)

# Step 2: Review champion history
champions = rollback_mgr.get_champion_history(limit=20)
print("Recent Champions:")
for champ in champions:
    print(f"  Iteration {champ.iteration_num}: Sharpe {champ.metrics['sharpe_ratio']:.2f}")

# Step 3: Select target (e.g., iteration 5 had good performance)
target_iteration = 5

# Step 4: Validate target champion
target_champion = next(c for c in champions if c.iteration_num == target_iteration)
is_valid, report = rollback_mgr.validate_rollback_champion(
    champion=target_champion,
    data=finlab_data
)

if not is_valid:
    print(f"❌ Validation failed: {report['error']}")
    exit(1)

print(f"✅ Validation passed: Sharpe {report['current_sharpe']:.2f}")

# Step 5: Execute rollback
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=target_iteration,
    reason="Rollback due to production performance degradation",
    operator="system_admin@example.com",
    data=finlab_data,
    validate=False  # Already validated
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")

# Step 6: Verify recovery
current_champion = hall_of_fame.get_current_champion()
print(f"Current champion: Iteration {current_champion.parameters['__iteration_num__']}")

# Step 7: Review audit trail
history = rollback_mgr.get_rollback_history(limit=5)
print("\nRollback History:")
for record in history:
    print(f"  {record.timestamp}: {record.from_iteration} → {record.to_iteration}")
```

### Rollback Best Practices

1. **Always Validate First**: Use `validate=True` unless emergency
2. **Document Reason**: Provide clear, detailed rollback reason
3. **Record Operator**: Include operator name/email for audit
4. **Verify Recovery**: Confirm champion after rollback
5. **Review Audit Trail**: Check rollback history periodically
6. **Test in Staging**: Practice rollback procedures in non-production

### Emergency Rollback

```bash
# Fast rollback without validation (use cautiously)
python rollback_champion.py \
    --target-iteration 5 \
    --reason "EMERGENCY: Production critical issue" \
    --operator "oncall@example.com" \
    --no-validate
```

---

## Monitoring & Diagnostics

### Real-Time Monitoring

```python
from src.monitoring.variance_monitor import VarianceMonitor

monitor = VarianceMonitor(alert_threshold=0.8)

for i in range(50):
    result = loop.run_iteration(i, data)
    sharpe = result['metrics']['sharpe_ratio']

    # Update monitor
    monitor.update(i, sharpe)

    # Check alert condition every 5 iterations
    if i % 5 == 0:
        alert, msg = monitor.check_alert_condition()
        if alert:
            print(f"⚠️ ALERT (iter {i}): {msg}")

        # Check convergence
        variance = monitor.get_rolling_variance()
        print(f"Iteration {i}: Sharpe {sharpe:.2f}, σ={variance:.4f}")
```

### Convergence Report

```python
# Generate comprehensive convergence analysis
report = monitor.generate_convergence_report()

print(f"Status: {report['convergence_status']}")
print(f"Total iterations: {report['total_iterations']}")
print(f"Current variance: {report['current_variance']:.4f}")

if report['convergence_iteration']:
    print(f"Converged at iteration: {report['convergence_iteration']}")

print("\nVariance Trend:")
for iter_num, variance in report['variance_trend'][-10:]:
    print(f"  Iteration {iter_num}: σ={variance:.4f}")

print("\nRecommendations:")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

### Champion Update Analysis

```python
from src.config.anti_churn_manager import AntiChurnManager

manager = AntiChurnManager()

# Analyze update frequency
update_freq, recommendations = manager.analyze_update_frequency(window=50)

print(f"Champion Update Analysis (last 50 iterations):")
print(f"  Update frequency: {update_freq*100:.1f}%")
print(f"  Target range: 10-20%")
print(f"  Status: {'✅ Within target' if 0.10 <= update_freq <= 0.20 else '⚠️ Outside target'}")

print("\nRecommendations:")
for rec in recommendations:
    print(f"  - {rec}")

# View recent updates
print("\n" + manager.get_recent_updates_summary(count=10))
```

### Logging & Alerts

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('learning_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log key events
logger.info(f"Iteration {i} completed: Sharpe {sharpe:.2f}")
logger.warning(f"Variance alert: σ={variance:.4f} exceeds threshold {threshold}")
logger.error(f"Champion update failed: {error_message}")
```

---

## Production Best Practices

### Pre-Production Checklist

- [ ] Run 200-iteration validation test
- [ ] Verify convergence (σ < 0.5 after iteration 20)
- [ ] Confirm champion update frequency (10-20%)
- [ ] Review preservation false positive rate (<10%)
- [ ] Test rollback procedure
- [ ] Configure monitoring alerts
- [ ] Set up audit trail logging
- [ ] Document runbook procedures

### Operational Guidelines

#### 1. Start Small

```bash
# Week 1: 5-iteration validation
python run_5iteration_test.py

# Week 2: 50-iteration validation
python run_50iteration_test.py

# Week 3: 200-iteration production validation
python run_200iteration_test.py
```

#### 2. Monitor Key Metrics

| Metric | Target | Alert Threshold | Action |
|--------|--------|-----------------|--------|
| Variance (σ) | <0.5 after iter 20 | >0.8 for 5+ iters | Review config, check data |
| Update frequency | 10-20% | <5% or >30% | Adjust thresholds |
| Preservation false positive | <10% | >20% | Adjust tolerances |
| Convergence iteration | <30 | >50 | Review prompt template |

#### 3. Regular Review

**Daily**:
- Check variance trend
- Review champion updates
- Monitor alert logs

**Weekly**:
- Generate convergence report
- Analyze update frequency
- Review preservation reports

**Monthly**:
- Tune configuration parameters
- Review rollback history
- Update runbook procedures

#### 4. Configuration Management

```bash
# Version control configurations
git add config/learning_system.yaml
git commit -m "Update anti-churn thresholds: increase probation to 3 iters"

# Tag stable configurations
git tag -a "config-v1.2" -m "Production stable config (update freq 12%)"
```

#### 5. Disaster Recovery

**Backup Strategy**:
```bash
# Backup champion history
cp iteration_history.json backups/iteration_history_$(date +%Y%m%d).json

# Backup configurations
cp config/learning_system.yaml backups/learning_system_$(date +%Y%m%d).yaml

# Backup rollback logs
cp rollback_history.json backups/rollback_history_$(date +%Y%m%d).json
```

**Recovery Procedure**:
1. Identify failure point (iteration number)
2. Review rollback history
3. Select last known good champion
4. Execute rollback with validation
5. Verify recovery
6. Document incident

### Performance Optimization

#### Reduce Convergence Time

```yaml
anti_churn:
  probation_period: 1                # Faster initial exploration
  probation_threshold: 0.08          # Lower barrier for early updates
  post_probation_threshold: 0.05     # Standard after probation
```

#### Increase Stability

```yaml
anti_churn:
  probation_period: 3                # Longer probation
  probation_threshold: 0.12          # Higher barrier
  post_probation_threshold: 0.07     # Stricter post-probation
```

#### Balance Exploration vs Exploitation

```yaml
anti_churn:
  probation_period: 2                # Moderate probation
  probation_threshold: 0.10          # Balanced barrier
  post_probation_threshold: 0.05     # Gradual relaxation
  additive_threshold: 0.02           # Prevent high-Sharpe stagnation
```

---

## Troubleshooting

### Common Issues

#### 1. High Variance (σ > 0.8)

**Symptoms**:
- Sharpe ratios fluctuate wildly
- No convergence after 30+ iterations
- Frequent champion updates

**Diagnosis**:
```python
report = variance_monitor.generate_convergence_report()
print(f"Status: {report['convergence_status']}")
print(f"Current σ: {report['current_variance']:.4f}")
```

**Solutions**:

A. **Tighten Preservation Constraints**
```python
validator = PreservationValidator(
    sharpe_tolerance=0.05,      # Reduce from 0.10
    turnover_tolerance=0.10,    # Reduce from 0.20
    concentration_tolerance=0.10 # Reduce from 0.15
)
```

B. **Increase Anti-Churn Thresholds**
```yaml
anti_churn:
  probation_threshold: 0.12      # Increase from 0.10
  post_probation_threshold: 0.07 # Increase from 0.05
```

C. **Review Data Consistency**
```python
from src.data.pipeline_integrity import DataPipelineIntegrity

integrity = DataPipelineIntegrity()
checksum = integrity.compute_dataset_checksum(data)
is_valid, msg = integrity.validate_data_consistency(data, prev_checksum)
if not is_valid:
    print(f"⚠️ Data changed: {msg}")
```

#### 2. Champion Stagnation (<10% update rate)

**Symptoms**:
- No champion updates for 20+ iterations
- Update frequency <10%
- System not learning

**Diagnosis**:
```python
update_freq, recs = manager.analyze_update_frequency(window=50)
print(f"Update frequency: {update_freq*100:.1f}%")
```

**Solutions**:

A. **Decrease Anti-Churn Thresholds**
```yaml
anti_churn:
  probation_threshold: 0.08      # Decrease from 0.10
  post_probation_threshold: 0.03 # Decrease from 0.05
  additive_threshold: 0.01       # Decrease from 0.02
```

B. **Review Champion Quality**
```python
champions = rollback_mgr.get_champion_history(limit=5)
for champ in champions:
    print(f"Iteration {champ.iteration_num}: Sharpe {champ.metrics['sharpe_ratio']:.2f}")
# If current champion has exceptionally high Sharpe, may be valid stagnation
```

C. **Enable Champion Staleness Detection**
```yaml
staleness:
  staleness_enabled: true
  staleness_check_interval: 30  # More frequent checks
```

#### 3. Excessive Champion Churn (>20% update rate)

**Symptoms**:
- Champion changes every 2-3 iterations
- Update frequency >20%
- Unstable system

**Diagnosis**:
```python
print(manager.get_recent_updates_summary(count=20))
```

**Solutions**:

A. **Increase Probation Period**
```yaml
anti_churn:
  probation_period: 3            # Increase from 2
```

B. **Increase Thresholds**
```yaml
anti_churn:
  probation_threshold: 0.12      # Increase from 0.10
  post_probation_threshold: 0.07 # Increase from 0.05
```

C. **Enable Multi-Objective Validation**
```yaml
multi_objective:
  enabled: true
  calmar_retention_ratio: 0.95   # Stricter Calmar requirement
  max_drawdown_tolerance: 1.05   # Stricter drawdown requirement
```

#### 4. Preservation False Positives (>10% rate)

**Symptoms**:
- Valid champion preservation rejected
- False positive risk >0.5
- Requires manual review frequently

**Diagnosis**:
```python
is_preserved, report = validator.validate_preservation(code, champion, metrics)
print(f"False positive risk: {report.false_positive_risk:.1%}")
print(f"Behavioral similarity: {report.behavioral_similarity_score:.1%}")
```

**Solutions**:

A. **Loosen Tolerances**
```python
validator = PreservationValidator(
    sharpe_tolerance=0.15,      # Increase from 0.10
    turnover_tolerance=0.25,    # Increase from 0.20
    concentration_tolerance=0.20 # Increase from 0.15
)
```

B. **Review Behavioral Checks**
```python
for check in report.behavioral_checks:
    if not check.passed:
        print(f"{check.check_name}: {check.reason}")
        print(f"  Champion: {check.champion_value:.4f}")
        print(f"  Generated: {check.generated_value:.4f}")
        print(f"  Deviation: {check.deviation_pct:.1f}%")
```

#### 5. Rollback Validation Fails

**Symptoms**:
- Rollback validation returns `is_valid=False`
- Old champion no longer executes successfully

**Diagnosis**:
```python
is_valid, report = rollback_mgr.validate_rollback_champion(champion, data)
print(f"Error: {report.get('error')}")
print(f"Execution success: {report.get('execution_success')}")
```

**Solutions**:

A. **Data Mismatch**
```python
# Champion may have been trained on different data
# Check data provenance
from history import History
history = History()
record = history.get_record(target_iteration)
print(f"Data checksum: {record.data_checksum}")
```

B. **Dependency Changes**
```python
# Check if Python packages have changed
print(f"Original config: {record.config_snapshot}")
# Compare with current environment
```

C. **Select Different Champion**
```python
# Try earlier champion
champions = rollback_mgr.get_champion_history(limit=20)
for champ in champions:
    is_valid, report = rollback_mgr.validate_rollback_champion(champ, data)
    if is_valid:
        print(f"Valid champion found: Iteration {champ.iteration_num}")
        break
```

### Debug Mode

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
loop.run_iteration(i, data, debug=True)
```

### Log Analysis

```bash
# View recent errors
grep "ERROR" learning_system.log | tail -20

# View variance alerts
grep "Variance alert" learning_system.log

# View champion updates
grep "Champion updated" learning_system.log

# View preservation violations
grep "Preservation validation failed" learning_system.log
```

---

## Advanced Topics

### Custom Validation Logic

```python
from src.validation.preservation_validator import PreservationValidator

class CustomPreservationValidator(PreservationValidator):
    def validate_preservation(self, generated_code, champion, execution_metrics):
        # Call parent validation
        is_preserved, report = super().validate_preservation(
            generated_code, champion, execution_metrics
        )

        # Add custom checks
        if execution_metrics:
            win_rate = execution_metrics.get('win_rate', 0)
            champion_win_rate = champion.metrics.get('win_rate', 0)

            if abs(win_rate - champion_win_rate) > 0.15:
                report.false_positive_risk += 0.2
                report.false_positive_indicators.append(
                    f"Win rate deviation: {abs(win_rate - champion_win_rate):.1%}"
                )

        return is_preserved, report
```

### Multi-Model Validation

```python
from artifacts.working.modules.autonomous_loop import AutonomousLoop

# Run multiple models in parallel
models = ['claude-sonnet-4.1', 'gpt-4', 'gemini-pro']

for model in models:
    loop = AutonomousLoop(model=model)

    for i in range(50):
        result = loop.run_iteration(i, data)

    # Compare convergence across models
    report = loop.variance_monitor.generate_convergence_report()
    print(f"{model}: {report['convergence_status']} at iter {report['convergence_iteration']}")
```

### Statistical Analysis

```python
from tests.integration.extended_test_harness import ExtendedTestHarness

# Run extended test with statistical analysis
harness = ExtendedTestHarness(
    model='claude-sonnet-4.1',
    target_iterations=200,
    checkpoint_interval=50
)

results = harness.run_test(data)

# Analyze statistical significance
print(f"Cohen's d: {results['cohens_d']:.2f}")
print(f"P-value: {results['p_value']:.4f}")
print(f"Production ready: {results['production_ready']}")
```

### Integration with External Systems

```python
import requests

# Send alerts to Slack
def send_slack_alert(message):
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    requests.post(webhook_url, json={'text': message})

# Alert on variance threshold
alert, msg = variance_monitor.check_alert_condition()
if alert:
    send_slack_alert(f"⚠️ Learning System Alert: {msg}")

# Alert on champion update
if champion_updated:
    send_slack_alert(
        f"✅ Champion Updated: Iteration {i}, "
        f"Sharpe {new_sharpe:.2f} (was {old_sharpe:.2f})"
    )
```

---

## Appendix

### Configuration Reference

**Complete `config/learning_system.yaml`**:
```yaml
anti_churn:
  probation_period: 2
  probation_threshold: 0.10
  post_probation_threshold: 0.05
  post_probation_relative_threshold: 0.01
  additive_threshold: 0.02
  threshold_logging_enabled: true
  min_sharpe_for_champion: 0.5
  target_update_frequency: 0.15
  tuning_range:
    probation_period: [1, 3]
    probation_threshold: [0.05, 0.15]
    post_probation_threshold: [0.03, 0.10]
  staleness:
    staleness_check_interval: 50
    staleness_cohort_percentile: 0.10
    staleness_min_cohort_size: 5
    staleness_enabled: true

multi_objective:
  enabled: true
  calmar_retention_ratio: 0.90
  max_drawdown_tolerance: 1.10

features:
  enable_anti_churn: true
  enable_adaptive_tuning: false

monitoring:
  log_champion_updates: true
  alert_on_excessive_churn: true
  alert_on_stagnation: true
```

### API Reference

**VarianceMonitor**:
- `__init__(alert_threshold: float = 0.8)`
- `update(iteration_num: int, sharpe: float) -> None`
- `get_rolling_variance(window: int = 10) -> float`
- `check_alert_condition() -> Tuple[bool, str]`
- `generate_convergence_report() -> Dict[str, any]`

**PreservationValidator**:
- `__init__(sharpe_tolerance: float = 0.10, turnover_tolerance: float = 0.20, concentration_tolerance: float = 0.15)`
- `validate_preservation(generated_code: str, champion: Any, execution_metrics: Optional[Dict] = None) -> Tuple[bool, PreservationReport]`
- `check_behavioral_similarity(champion_metrics: Dict, generated_metrics: Dict, champion_positions: Optional[pd.DataFrame] = None, generated_positions: Optional[pd.DataFrame] = None) -> Tuple[bool, Dict]`

**AntiChurnManager**:
- `__init__(config_path: str = "config/learning_system.yaml")`
- `get_required_improvement(current_iteration: int, champion_iteration: int) -> float`
- `get_additive_threshold() -> float`
- `track_champion_update(iteration_num: int, was_updated: bool, old_sharpe: Optional[float] = None, new_sharpe: Optional[float] = None, threshold_used: Optional[float] = None) -> None`
- `analyze_update_frequency(window: int = 50) -> Tuple[float, List[str]]`
- `get_recent_updates_summary(count: int = 10) -> str`

**RollbackManager**:
- `__init__(hall_of_fame: HallOfFameRepository, rollback_log_file: str = "rollback_history.json")`
- `get_champion_history(limit: int = 20) -> List[ChampionStrategy]`
- `rollback_to_iteration(target_iteration: int, reason: str, operator: str, data: Any, validate: bool = True) -> Tuple[bool, str]`
- `validate_rollback_champion(champion: ChampionStrategy, data: Any, min_sharpe_threshold: float = 0.5) -> Tuple[bool, Dict]`
- `record_rollback(from_iteration: int, to_iteration: int, reason: str, operator: str, validation_passed: bool, validation_report: Dict) -> None`
- `get_rollback_history(limit: Optional[int] = None) -> List[RollbackRecord]`

### Glossary

- **Champion**: The current best strategy with highest validated performance
- **Probation Period**: Iterations after champion update with higher replacement threshold
- **Convergence**: Learning system reaches stable state (σ < 0.5)
- **Variance (σ)**: Standard deviation of Sharpe ratios over rolling window
- **False Positive**: Valid preservation incorrectly rejected
- **Hybrid Threshold**: Accept EITHER relative OR absolute improvement criteria
- **Staleness**: Champion becomes outdated relative to recent strategy cohort
- **Multi-Objective**: Validation requiring multiple metrics (Sharpe, Calmar, Drawdown)
- **Rollback**: Restore previous champion strategy
- **Audit Trail**: Complete log of all rollback operations

### Resources

**Documentation**:
- Design Document: `.spec-workflow/specs/learning-system-stability-fixes/design.md`
- Requirements: `.spec-workflow/specs/learning-system-stability-fixes/requirements.md`
- Tasks: `.spec-workflow/specs/learning-system-stability-fixes/tasks.md`
- Project TODO: `PROJECT_TODO.md`

**Test Scripts**:
- `run_5iteration_test.py` - Basic validation
- `run_50iteration_test.py` - Phase 1+2 validation
- `run_200iteration_test.py` - Production validation

**Key Files**:
- `src/monitoring/variance_monitor.py` - Convergence tracking
- `src/validation/preservation_validator.py` - Enhanced preservation
- `src/config/anti_churn_manager.py` - Dynamic thresholds
- `src/recovery/rollback_manager.py` - Rollback operations
- `config/learning_system.yaml` - System configuration

### Support

**Issue Reporting**: GitHub Issues
**Documentation**: `docs/`
**Contact**: See `PROJECT_TODO.md` for project status and updates

---

**End of Learning System User Guide**
