# Learning System Phase 2 - API Reference

Comprehensive API documentation for Learning System stability and convergence components.

## Table of Contents

1. [VarianceMonitor](#variancemonitor)
2. [PreservationValidator](#preservationvalidator)
3. [AntiChurnManager](#antichurnmanager)
4. [RollbackManager](#rollbackmanager)
5. [Configuration Reference](#configuration-reference)
6. [Integration Patterns](#integration-patterns)

---

## VarianceMonitor

**Module:** `src/monitoring/variance_monitor.py`

Tracks Sharpe ratio variance over time to detect learning convergence or instability patterns.

### Class Definition

```python
class VarianceMonitor:
    """Monitor Sharpe ratio variance to detect convergence and instability.

    Tracks rolling variance with configurable window (default 10 iterations).
    Success criterion: σ < 0.5 after iteration 10 indicates convergence.
    Alert threshold: σ > 0.8 for 5+ consecutive iterations indicates instability.
    """
```

### Constructor

```python
def __init__(self, alert_threshold: float = 0.8)
```

**Parameters:**
- `alert_threshold` (float, default=0.8): Variance threshold for instability alerts. When standard deviation exceeds this value for 5+ consecutive iterations, alerts are triggered.

**Example:**
```python
from src.monitoring.variance_monitor import VarianceMonitor

# Initialize with default threshold
monitor = VarianceMonitor()

# Initialize with custom threshold
monitor = VarianceMonitor(alert_threshold=0.9)
```

### Methods

#### update()

```python
def update(self, iteration_num: int, sharpe: float) -> None
```

Update monitor with new iteration Sharpe ratio.

**Parameters:**
- `iteration_num` (int): Current iteration number (for logging context)
- `sharpe` (float): Sharpe ratio from current iteration

**Returns:** None

**Example:**
```python
monitor = VarianceMonitor()
for i in range(50):
    sharpe = run_iteration(i)
    monitor.update(i, sharpe)
```

#### get_rolling_variance()

```python
def get_rolling_variance(self, window: int = 10) -> float
```

Calculate rolling variance (standard deviation) of recent Sharpe ratios.

**Parameters:**
- `window` (int, default=10): Number of recent iterations to include in calculation

**Returns:**
- `float`: Standard deviation (σ) of Sharpe ratios, or 0.0 if insufficient data (< 2 samples)

**Example:**
```python
variance = monitor.get_rolling_variance(window=10)
print(f"Current variance: {variance:.4f}")

# Custom window
variance_20 = monitor.get_rolling_variance(window=20)
```

#### check_alert_condition()

```python
def check_alert_condition() -> Tuple[bool, str]
```

Check if alert condition is met (high variance for 5+ consecutive iterations).

**Parameters:** None

**Returns:**
- `Tuple[bool, str]`:
  - `bool`: True if alert triggered, False otherwise
  - `str`: Context message explaining alert (empty if no alert)

**Alert Logic:**
- Alerts trigger when σ > `alert_threshold` for 5+ consecutive iterations
- Counter resets to 0 when variance drops below threshold
- Indicates unstable learning that may require intervention

**Example:**
```python
alert_triggered, message = monitor.check_alert_condition()
if alert_triggered:
    print(f"ALERT: {message}")
    # Take corrective action: tighten constraints, reduce exploration, etc.
```

#### generate_convergence_report()

```python
def generate_convergence_report() -> Dict[str, any]
```

Generate comprehensive convergence analysis report.

**Parameters:** None

**Returns:**
- `Dict[str, any]` containing:
  - `variance_trend` (List[Tuple[int, float]]): List of (iteration, variance) tuples over time
  - `convergence_status` (str): "converged", "converging", or "unstable"
  - `convergence_iteration` (Optional[int]): First iteration where σ < 0.5 after iteration 10, or None
  - `current_variance` (float): Latest rolling variance
  - `total_iterations` (int): Total iterations processed
  - `recommendations` (List[str]): Actionable recommendations for system tuning

**Convergence Status Logic:**
- `"converged"`: σ < 0.5 detected after iteration 10
- `"converging"`: System still learning, variance not yet stable
- `"unstable"`: σ > 0.8, system exhibiting instability

**Example:**
```python
report = monitor.generate_convergence_report()

print(f"Status: {report['convergence_status']}")
print(f"Current variance: {report['current_variance']:.4f}")

if report['convergence_iteration']:
    print(f"Converged at iteration {report['convergence_iteration']}")

for recommendation in report['recommendations']:
    print(f"  - {recommendation}")

# Visualize variance trend
import matplotlib.pyplot as plt
iterations, variances = zip(*report['variance_trend'])
plt.plot(iterations, variances)
plt.axhline(y=0.5, color='g', linestyle='--', label='Convergence threshold')
plt.axhline(y=0.8, color='r', linestyle='--', label='Alert threshold')
plt.legend()
plt.show()
```

---

## PreservationValidator

**Module:** `src/validation/preservation_validator.py`

Validates champion preservation with behavioral similarity checks to reduce false positives.

### Class Definition

```python
class PreservationValidator:
    """Validate champion preservation with behavioral similarity checks.

    Enhanced preservation validation that checks both parameter preservation
    and behavioral similarity to reduce false positives and detect meaningful
    preservation violations.
    """
```

### Constructor

```python
def __init__(
    self,
    sharpe_tolerance: float = 0.10,
    turnover_tolerance: float = 0.20,
    concentration_tolerance: float = 0.15
)
```

**Parameters:**
- `sharpe_tolerance` (float, default=0.10): Maximum allowed Sharpe ratio deviation (±10%)
- `turnover_tolerance` (float, default=0.20): Maximum allowed portfolio turnover deviation (±20%)
- `concentration_tolerance` (float, default=0.15): Maximum allowed position concentration change (±15%)

**Example:**
```python
from src.validation.preservation_validator import PreservationValidator

# Initialize with default tolerances
validator = PreservationValidator()

# Initialize with custom tolerances (stricter)
validator = PreservationValidator(
    sharpe_tolerance=0.05,
    turnover_tolerance=0.10,
    concentration_tolerance=0.10
)
```

### Methods

#### validate_preservation()

```python
def validate_preservation(
    self,
    generated_code: str,
    champion: Any,  # ChampionStrategy from autonomous_loop.py
    execution_metrics: Optional[Dict[str, float]] = None
) -> Tuple[bool, PreservationReport]
```

Enhanced preservation validation with behavioral checks.

**Parameters:**
- `generated_code` (str): LLM-generated code to validate
- `champion` (ChampionStrategy): Current champion strategy object
- `execution_metrics` (Optional[Dict[str, float]]): Runtime metrics for behavioral validation

**Returns:**
- `Tuple[bool, PreservationReport]`:
  - `bool`: True if champion is preserved, False otherwise
  - `PreservationReport`: Detailed validation report (see below)

**Validation Checks:**
1. **Parameter Preservation:**
   - ROE type preservation (smoothed vs raw)
   - ROE smoothing window (±20% tolerance)
   - Liquidity threshold (≥80% of champion)

2. **Behavioral Similarity** (if execution_metrics provided):
   - Sharpe ratio within tolerance
   - Portfolio turnover within tolerance
   - Position concentration patterns maintained

3. **False Positive Detection:**
   - Flags mismatches between parameter and behavioral checks
   - High risk when parameters pass but behavior differs significantly

**Example:**
```python
from artifacts.working.modules.autonomous_loop import ChampionStrategy

validator = PreservationValidator()

# Without execution metrics (parameter checks only)
is_preserved, report = validator.validate_preservation(
    generated_code=llm_generated_code,
    champion=current_champion,
    execution_metrics=None
)

print(report.summary())
if not is_preserved:
    for recommendation in report.recommendations:
        print(f"  - {recommendation}")

# With execution metrics (full validation)
execution_metrics = {
    'sharpe_ratio': 2.35,
    'total_return': 0.42,
    'max_drawdown': -0.15
}

is_preserved, report = validator.validate_preservation(
    generated_code=llm_generated_code,
    champion=current_champion,
    execution_metrics=execution_metrics
)

if report.requires_manual_review:
    print("Manual review required!")
    print(f"False positive risk: {report.false_positive_risk:.2%}")
```

#### check_behavioral_similarity()

```python
def check_behavioral_similarity(
    self,
    champion_metrics: Dict[str, float],
    generated_metrics: Dict[str, float],
    champion_positions: Optional[pd.DataFrame] = None,
    generated_positions: Optional[pd.DataFrame] = None
) -> Tuple[bool, Dict[str, str]]
```

Check behavioral similarity beyond just metrics.

**Parameters:**
- `champion_metrics` (Dict[str, float]): Champion strategy metrics
- `generated_metrics` (Dict[str, float]): Generated strategy metrics
- `champion_positions` (Optional[pd.DataFrame]): Champion position DataFrame
- `generated_positions` (Optional[pd.DataFrame]): Generated position DataFrame

**Returns:**
- `Tuple[bool, Dict[str, str]]`:
  - `bool`: True if behaviorally similar, False otherwise
  - `Dict[str, str]`: Deviation details with check statuses

**Behavioral Checks:**
1. **Sharpe Similarity:** Within ±10% (configurable)
2. **Turnover Similarity:** Within ±20% (configurable)
3. **Concentration Patterns:** Within ±15% (configurable)

**Example:**
```python
champion_metrics = {'sharpe_ratio': 2.4, 'total_return': 0.45}
generated_metrics = {'sharpe_ratio': 2.35, 'total_return': 0.43}

is_similar, details = validator.check_behavioral_similarity(
    champion_metrics=champion_metrics,
    generated_metrics=generated_metrics
)

print(f"Behaviorally similar: {is_similar}")
print(f"Sharpe status: {details['sharpe_status']}")
print(f"Sharpe deviation: {details['sharpe_deviation_pct']}")
```

### Data Classes

#### PreservationReport

```python
@dataclass
class PreservationReport:
    """Detailed preservation validation report."""
    is_preserved: bool
    parameter_checks: Dict[str, Tuple[bool, str]]
    critical_params_preserved: List[str]
    missing_params: List[str]
    behavioral_checks: List[BehavioralCheck]
    behavioral_similarity_score: float  # 0.0-1.0
    false_positive_risk: float  # 0.0-1.0
    false_positive_indicators: List[str]
    recommendations: List[str]
    requires_manual_review: bool
    timestamp: str
```

**Methods:**
- `summary() -> str`: Human-readable summary string

**Example:**
```python
print(report.summary())
# Output: "✅ PRESERVED | 3/3 params | similarity 95%"

# Access detailed fields
for param, (passed, reason) in report.parameter_checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {param}: {reason}")
```

#### BehavioralCheck

```python
@dataclass
class BehavioralCheck:
    """Single behavioral similarity check result."""
    check_name: str
    passed: bool
    champion_value: float
    generated_value: float
    threshold: float
    deviation_pct: float
    reason: str
```

---

## AntiChurnManager

**Module:** `src/config/anti_churn_manager.py`

Manages champion update thresholds with probation period to prevent excessive churn.

### Class Definition

```python
class AntiChurnManager:
    """Manage anti-churn configuration and champion update dynamics.

    Provides dynamic thresholds based on probation period and tracks
    champion update frequency to detect churn or stagnation issues.

    Phase 3 Enhancement: Hybrid Threshold System
    ---------------------------------------------
    The manager now supports BOTH relative and absolute improvement thresholds.
    A strategy can replace the champion by satisfying EITHER condition:

    1. Relative threshold: new_sharpe >= old_sharpe * (1 + relative_threshold)
    2. Absolute threshold: new_sharpe >= old_sharpe + additive_threshold
    """
```

### Constructor

```python
def __init__(self, config_path: str = "config/learning_system.yaml")
```

**Parameters:**
- `config_path` (str, default="config/learning_system.yaml"): Path to YAML configuration file

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `yaml.YAMLError`: If config file is malformed

**Example:**
```python
from src.config.anti_churn_manager import AntiChurnManager

# Initialize with default config path
manager = AntiChurnManager()

# Initialize with custom config path
manager = AntiChurnManager(config_path="custom_config.yaml")

# Access loaded configuration
print(f"Probation period: {manager.probation_period} iterations")
print(f"Probation threshold: {manager.probation_threshold}")
print(f"Post-probation threshold: {manager.post_probation_threshold}")
print(f"Additive threshold: {manager.additive_threshold}")
```

### Methods

#### get_required_improvement()

```python
def get_required_improvement(
    self,
    current_iteration: int,
    champion_iteration: int
) -> float
```

Get dynamic improvement threshold based on probation period.

**Parameters:**
- `current_iteration` (int): Current iteration number
- `champion_iteration` (int): Iteration when current champion was crowned

**Returns:**
- `float`: Required relative improvement multiplier (e.g., 0.10 for 10% improvement)

**Threshold Logic:**
- **During probation** (iterations_since_champion ≤ probation_period): Returns `probation_threshold` (default 0.10)
- **After probation** (iterations_since_champion > probation_period): Returns `post_probation_threshold` (default 0.05)

**Example:**
```python
manager = AntiChurnManager()

# Champion crowned at iteration 5, now at iteration 6 (probation)
threshold = manager.get_required_improvement(
    current_iteration=6,
    champion_iteration=5
)
print(f"Required improvement: {threshold*100:.0f}%")  # 10%

# Champion crowned at iteration 5, now at iteration 10 (post-probation)
threshold = manager.get_required_improvement(
    current_iteration=10,
    champion_iteration=5
)
print(f"Required improvement: {threshold*100:.0f}%")  # 5%
```

#### get_additive_threshold()

```python
def get_additive_threshold() -> float
```

Get the absolute improvement threshold (Phase 3 hybrid threshold).

**Parameters:** None

**Returns:**
- `float`: Absolute improvement threshold (e.g., 0.02 for +0.02 Sharpe improvement)

**Hybrid Threshold System:**
A strategy can replace the champion by satisfying EITHER condition:
1. Relative: `new_sharpe >= old_sharpe * (1 + relative_threshold)`
2. Absolute: `new_sharpe >= old_sharpe + additive_threshold`

This prevents stagnation at high Sharpe ratios where percentage improvements become difficult.

**Example:**
```python
manager = AntiChurnManager()
additive_threshold = manager.get_additive_threshold()  # 0.02

# Decision logic example
old_sharpe = 2.4751
new_sharpe = 2.495
relative_threshold = 0.01  # 1%

# Check relative threshold
relative_target = old_sharpe * (1 + relative_threshold)  # 2.500
relative_passes = new_sharpe >= relative_target  # False

# Check absolute threshold
absolute_target = old_sharpe + additive_threshold  # 2.495
absolute_passes = new_sharpe >= absolute_target  # True

# Accept if EITHER passes
should_update = relative_passes or absolute_passes  # True
```

#### track_champion_update()

```python
def track_champion_update(
    self,
    iteration_num: int,
    was_updated: bool,
    old_sharpe: Optional[float] = None,
    new_sharpe: Optional[float] = None,
    threshold_used: Optional[float] = None
) -> None
```

Record a champion update event for frequency analysis.

**Parameters:**
- `iteration_num` (int): Current iteration number
- `was_updated` (bool): Whether champion was updated this iteration
- `old_sharpe` (Optional[float]): Previous champion Sharpe (if updated)
- `new_sharpe` (Optional[float]): New champion Sharpe (if updated)
- `threshold_used` (Optional[float]): Improvement threshold that was applied

**Returns:** None

**Example:**
```python
manager = AntiChurnManager()

# Track champion update
manager.track_champion_update(
    iteration_num=5,
    was_updated=True,
    old_sharpe=1.8,
    new_sharpe=2.2,
    threshold_used=0.10
)

# Track no update
manager.track_champion_update(
    iteration_num=6,
    was_updated=False
)
```

#### analyze_update_frequency()

```python
def analyze_update_frequency(
    self,
    window: int = 50
) -> Tuple[float, List[str]]
```

Analyze champion update frequency and generate recommendations.

**Parameters:**
- `window` (int, default=50): Number of recent iterations to analyze

**Returns:**
- `Tuple[float, List[str]]`:
  - `float`: Update frequency (0.0-1.0)
  - `List[str]`: Actionable recommendations

**Target Ranges:**
- **Healthy:** 10-20% update frequency
- **Excessive churn:** >20% (recommend increasing thresholds)
- **Stagnation:** <10% (recommend decreasing thresholds)

**Example:**
```python
manager = AntiChurnManager()

# Track 50 iterations
for i in range(50):
    was_updated = run_iteration_and_check_update(i)
    manager.track_champion_update(i, was_updated)

# Analyze frequency
freq, recommendations = manager.analyze_update_frequency(window=50)
print(f"Update frequency: {freq*100:.1f}%")

for rec in recommendations:
    print(f"  {rec}")

# Example output:
# Update frequency: 28.0%
#   ⚠️ Excessive champion churn detected (28.0% update rate)
#   Consider increasing probation_threshold from 0.10 to 0.12
#   Consider increasing post_probation_threshold from 0.05 to 0.06
```

#### get_recent_updates_summary()

```python
def get_recent_updates_summary(self, count: int = 10) -> str
```

Get human-readable summary of recent champion updates.

**Parameters:**
- `count` (int, default=10): Number of recent updates to summarize

**Returns:**
- `str`: Formatted string with update history

**Example:**
```python
summary = manager.get_recent_updates_summary(count=10)
print(summary)

# Example output:
# Recent Champion Updates (last 10 iterations):
# ============================================================
# Iter 0: ✅ UPDATED (None → 1.2000, N/A)
# Iter 1: ➖ No update
# Iter 2: ➖ No update
# Iter 3: ✅ UPDATED (1.2000 → 1.3500, +12.5%)
# ...
# ============================================================
# Update frequency: 30.0%
```

### Data Classes

#### ChampionUpdateRecord

```python
@dataclass
class ChampionUpdateRecord:
    """Record of a champion update event."""
    iteration_num: int
    was_updated: bool
    old_sharpe: Optional[float]
    new_sharpe: Optional[float]
    improvement_pct: Optional[float]
    threshold_used: float
    timestamp: str
```

---

## RollbackManager

**Module:** `src/recovery/rollback_manager.py`

Provides rollback functionality for reverting to previous champion strategies.

### Class Definition

```python
class RollbackManager:
    """Manages rollback operations for champion strategies.

    Features:
        - Query historical champions
        - Validate rollback candidates
        - Update current champion
        - Maintain audit trail
    """
```

### Constructor

```python
def __init__(
    self,
    hall_of_fame: HallOfFameRepository,
    rollback_log_file: str = "rollback_history.json"
)
```

**Parameters:**
- `hall_of_fame` (HallOfFameRepository): Repository instance for strategy access
- `rollback_log_file` (str, default="rollback_history.json"): Path to rollback audit trail file

**Example:**
```python
from src.repository.hall_of_fame import HallOfFameRepository
from src.recovery.rollback_manager import RollbackManager

hall_of_fame = HallOfFameRepository()
rollback_mgr = RollbackManager(hall_of_fame)

# Custom audit trail location
rollback_mgr = RollbackManager(
    hall_of_fame=hall_of_fame,
    rollback_log_file="logs/rollback_audit.json"
)
```

### Methods

#### get_champion_history()

```python
def get_champion_history(self, limit: int = 20) -> List[ChampionStrategy]
```

Retrieve historical champion strategies sorted by date.

**Parameters:**
- `limit` (int, default=20): Maximum number of champions to return

**Returns:**
- `List[ChampionStrategy]`: Champions sorted by timestamp (newest first)

**Example:**
```python
rollback_mgr = RollbackManager(hall_of_fame)

# Get last 10 champions
champions = rollback_mgr.get_champion_history(limit=10)

for champ in champions:
    print(f"Iteration {champ.iteration_num}: "
          f"Sharpe {champ.metrics['sharpe_ratio']:.2f} "
          f"({champ.timestamp})")

# Example output:
# Iteration 45: Sharpe 2.48 (2025-01-15T14:32:11)
# Iteration 32: Sharpe 2.35 (2025-01-15T12:18:45)
# Iteration 18: Sharpe 2.20 (2025-01-15T09:45:22)
```

#### rollback_to_iteration()

```python
def rollback_to_iteration(
    self,
    target_iteration: int,
    reason: str,
    operator: str,
    data: Any,
    validate: bool = True
) -> Tuple[bool, str]
```

Rollback to a specific champion iteration.

**Workflow:**
1. Find champion matching target_iteration
2. Validate that champion still works (if validate=True)
3. Update current champion in Hall of Fame
4. Record rollback in audit trail

**Parameters:**
- `target_iteration` (int): Iteration number to rollback to
- `reason` (str): Human-readable explanation for rollback
- `operator` (str): Name/email of person performing rollback
- `data` (Any): Finlab data object for validation
- `validate` (bool, default=True): Whether to validate rollback candidate

**Returns:**
- `Tuple[bool, str]`:
  - `bool`: Success status
  - `str`: Result message

**Example:**
```python
rollback_mgr = RollbackManager(hall_of_fame)

# Rollback with validation
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=32,
    reason="Production issue - reverting to stable version",
    operator="john@example.com",
    data=finlab_data
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ Rollback failed: {message}")

# Rollback without validation (emergency)
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=32,
    reason="Emergency rollback - production down",
    operator="oncall@example.com",
    data=finlab_data,
    validate=False  # Skip validation for speed
)
```

#### validate_rollback_champion()

```python
def validate_rollback_champion(
    self,
    champion: ChampionStrategy,
    data: Any,
    min_sharpe_threshold: float = 0.5
) -> Tuple[bool, Dict]
```

Validate that a rollback champion still works.

**Validation Checks:**
1. Execution succeeds without errors
2. Metrics are reasonable (Sharpe > threshold)

**Parameters:**
- `champion` (ChampionStrategy): Champion to validate
- `data` (Any): Finlab data object for execution
- `min_sharpe_threshold` (float, default=0.5): Minimum acceptable Sharpe ratio

**Returns:**
- `Tuple[bool, Dict]`:
  - `bool`: Validation status
  - `Dict`: Detailed validation report

**Example:**
```python
rollback_mgr = RollbackManager(hall_of_fame)
champions = rollback_mgr.get_champion_history(limit=5)

for champ in champions:
    is_valid, report = rollback_mgr.validate_rollback_champion(
        champion=champ,
        data=finlab_data,
        min_sharpe_threshold=1.0  # Strict threshold
    )

    if is_valid:
        print(f"✅ Iteration {champ.iteration_num}: "
              f"Original Sharpe {report['original_sharpe']:.2f}, "
              f"Current Sharpe {report['current_sharpe']:.2f}")
    else:
        print(f"❌ Iteration {champ.iteration_num}: {report['error']}")
```

#### record_rollback()

```python
def record_rollback(
    self,
    from_iteration: int,
    to_iteration: int,
    reason: str,
    operator: str,
    validation_passed: bool,
    validation_report: Dict
) -> None
```

Record rollback operation in audit trail.

**Parameters:**
- `from_iteration` (int): Iteration we're rolling back from
- `to_iteration` (int): Target iteration we're rolling back to
- `reason` (str): Human-readable explanation
- `operator` (str): Name/email of person performing rollback
- `validation_passed` (bool): Whether validation succeeded
- `validation_report` (Dict): Detailed validation results

**Returns:** None

**Side Effects:**
- Appends to in-memory rollback log
- Appends to persistent JSON file (one record per line)

**Example:**
```python
# Typically called internally by rollback_to_iteration()
# Can be called manually for custom tracking

rollback_mgr.record_rollback(
    from_iteration=45,
    to_iteration=32,
    reason="Production issue - high drawdown detected",
    operator="ops@example.com",
    validation_passed=True,
    validation_report={'sharpe': 2.35, 'status': 'valid'}
)
```

#### get_rollback_history()

```python
def get_rollback_history(self, limit: Optional[int] = None) -> List[RollbackRecord]
```

Get rollback audit trail.

**Parameters:**
- `limit` (Optional[int], default=None): Maximum number of records (None = all)

**Returns:**
- `List[RollbackRecord]`: Rollback records sorted by timestamp (newest first)

**Example:**
```python
rollback_mgr = RollbackManager(hall_of_fame)

# Get all rollback history
history = rollback_mgr.get_rollback_history()

for record in history:
    status = "✅" if record.validation_passed else "❌"
    print(f"{status} {record.timestamp}: "
          f"Iter {record.from_iteration} → {record.to_iteration} "
          f"by {record.operator}")
    print(f"   Reason: {record.reason}")

# Get last 5 rollbacks
recent = rollback_mgr.get_rollback_history(limit=5)
```

### Data Classes

#### ChampionStrategy

```python
@dataclass
class ChampionStrategy:
    """Champion strategy representation for rollback system."""
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str
```

**Methods:**
- `to_dict() -> Dict`: Convert to dictionary for JSON serialization
- `from_dict(data: Dict) -> ChampionStrategy`: Create from dictionary

#### RollbackRecord

```python
@dataclass
class RollbackRecord:
    """Audit record for rollback operations."""
    rollback_id: str  # UUID
    from_iteration: int
    to_iteration: int
    reason: str
    operator: str
    timestamp: str  # ISO format
    validation_passed: bool
    validation_report: Dict
```

**Methods:**
- `to_dict() -> Dict`: Convert to dictionary for JSON serialization
- `from_dict(data: Dict) -> RollbackRecord`: Create from dictionary

---

## Configuration Reference

**File:** `config/learning_system.yaml`

### Anti-Churn Configuration

```yaml
anti_churn:
  # Probation period: Higher threshold for newly crowned champions (iterations)
  probation_period: 2

  # Required improvement during probation (multiplicative factor)
  probation_threshold: 0.10  # 10% improvement required

  # Required improvement after probation (multiplicative factor)
  post_probation_threshold: 0.05  # 5% improvement required

  # Hybrid threshold: Absolute improvement (Phase 3)
  additive_threshold: 0.02  # +0.02 Sharpe improvement

  # Minimum Sharpe ratio required to become champion
  min_sharpe_for_champion: 0.5

  # Target champion update frequency (10-20% of iterations)
  target_update_frequency: 0.15  # 15% target

  # Tuning ranges for adaptive adjustment
  tuning_range:
    probation_period: [1, 3]
    probation_threshold: [0.05, 0.15]
    post_probation_threshold: [0.03, 0.10]

  # Champion staleness mechanism
  staleness:
    staleness_check_interval: 50          # Check every 50 iterations
    staleness_cohort_percentile: 0.10     # Top 10% of recent strategies
    staleness_min_cohort_size: 5          # Minimum 5 strategies for valid cohort
    staleness_enabled: true               # Enable staleness mechanism
```

### Multi-Objective Validation Configuration

```yaml
multi_objective:
  # Enable multi-objective validation (feature flag)
  enabled: true

  # Calmar retention ratio: New champion must maintain ≥90% of old champion's Calmar
  # Formula: new_calmar >= old_calmar * calmar_retention_ratio
  calmar_retention_ratio: 0.90

  # Max drawdown tolerance: New champion can have ≤110% of old champion's drawdown
  # Formula: new_mdd <= old_mdd * max_drawdown_tolerance
  max_drawdown_tolerance: 1.10
```

### Feature Flags

```yaml
features:
  enable_anti_churn: true
  enable_adaptive_tuning: false  # Future feature
```

### Monitoring Configuration

```yaml
monitoring:
  log_champion_updates: true
  alert_on_excessive_churn: true
  alert_on_stagnation: true
```

---

## Integration Patterns

### Pattern 1: Basic Learning Loop Integration

```python
from src.monitoring.variance_monitor import VarianceMonitor
from src.config.anti_churn_manager import AntiChurnManager

# Initialize components
variance_monitor = VarianceMonitor(alert_threshold=0.8)
anti_churn_mgr = AntiChurnManager()

# Learning loop
current_champion = None
champion_iteration = 0

for iteration in range(100):
    # Generate and evaluate strategy
    generated_code = generate_strategy()
    metrics = evaluate_strategy(generated_code, data)

    # Update variance monitor
    variance_monitor.update(iteration, metrics['sharpe_ratio'])

    # Check for alerts
    alert_triggered, alert_msg = variance_monitor.check_alert_condition()
    if alert_triggered:
        logger.warning(f"Iteration {iteration}: {alert_msg}")

    # Champion update logic with anti-churn
    if current_champion is None:
        current_champion = create_champion(generated_code, metrics)
        champion_iteration = iteration
        anti_churn_mgr.track_champion_update(iteration, True, None, metrics['sharpe_ratio'])
    else:
        # Get required improvement
        required_improvement = anti_churn_mgr.get_required_improvement(
            current_iteration=iteration,
            champion_iteration=champion_iteration
        )

        # Hybrid threshold check
        old_sharpe = current_champion.metrics['sharpe_ratio']
        new_sharpe = metrics['sharpe_ratio']

        relative_target = old_sharpe * (1 + required_improvement)
        absolute_target = old_sharpe + anti_churn_mgr.get_additive_threshold()

        should_update = (new_sharpe >= relative_target) or (new_sharpe >= absolute_target)

        if should_update:
            anti_churn_mgr.track_champion_update(
                iteration, True, old_sharpe, new_sharpe, required_improvement
            )
            current_champion = create_champion(generated_code, metrics)
            champion_iteration = iteration
        else:
            anti_churn_mgr.track_champion_update(iteration, False)

    # Periodic frequency analysis
    if iteration % 20 == 0 and iteration > 0:
        freq, recommendations = anti_churn_mgr.analyze_update_frequency(window=20)
        logger.info(f"Update frequency: {freq*100:.1f}%")
        for rec in recommendations:
            logger.info(f"  {rec}")

# Generate final convergence report
report = variance_monitor.generate_convergence_report()
print(f"\nLearning Status: {report['convergence_status']}")
print(f"Convergence Iteration: {report['convergence_iteration']}")
for rec in report['recommendations']:
    print(f"  - {rec}")
```

### Pattern 2: Enhanced Preservation Validation

```python
from src.validation.preservation_validator import PreservationValidator
from src.config.anti_churn_manager import AntiChurnManager

# Initialize components
validator = PreservationValidator(
    sharpe_tolerance=0.10,
    turnover_tolerance=0.20,
    concentration_tolerance=0.15
)
anti_churn_mgr = AntiChurnManager()

# Learning iteration with preservation checks
def learning_iteration(iteration, current_champion):
    # Generate strategy
    generated_code = generate_strategy(champion=current_champion)

    # Execute and evaluate
    success, metrics, error = execute_strategy_safe(generated_code, data)
    if not success:
        return current_champion, False

    # Preservation validation
    is_preserved, preservation_report = validator.validate_preservation(
        generated_code=generated_code,
        champion=current_champion,
        execution_metrics=metrics
    )

    if not is_preserved:
        logger.warning(f"Preservation violation at iteration {iteration}")
        logger.warning(preservation_report.summary())

        for rec in preservation_report.recommendations:
            logger.info(f"  - {rec}")

        if preservation_report.requires_manual_review:
            logger.error("Manual review required!")

        return current_champion, False

    # Anti-churn check
    required_improvement = anti_churn_mgr.get_required_improvement(
        current_iteration=iteration,
        champion_iteration=current_champion.iteration_num
    )

    old_sharpe = current_champion.metrics['sharpe_ratio']
    new_sharpe = metrics['sharpe_ratio']

    # Hybrid threshold
    relative_passes = new_sharpe >= old_sharpe * (1 + required_improvement)
    absolute_passes = new_sharpe >= old_sharpe + anti_churn_mgr.get_additive_threshold()

    should_update = relative_passes or absolute_passes

    if should_update:
        logger.info(f"Champion updated at iteration {iteration}")
        logger.info(f"  Old Sharpe: {old_sharpe:.4f}")
        logger.info(f"  New Sharpe: {new_sharpe:.4f}")
        logger.info(f"  Preservation: {preservation_report.summary()}")

        new_champion = create_champion(generated_code, metrics, iteration)
        anti_churn_mgr.track_champion_update(
            iteration, True, old_sharpe, new_sharpe, required_improvement
        )
        return new_champion, True

    anti_churn_mgr.track_champion_update(iteration, False)
    return current_champion, False
```

### Pattern 3: Rollback Operations

```python
from src.recovery.rollback_manager import RollbackManager
from src.repository.hall_of_fame import HallOfFameRepository

# Initialize components
hall_of_fame = HallOfFameRepository()
rollback_mgr = RollbackManager(hall_of_fame)

# View champion history
champions = rollback_mgr.get_champion_history(limit=10)
print("\nChampion History:")
for i, champ in enumerate(champions):
    sharpe = champ.metrics['sharpe_ratio']
    print(f"{i+1}. Iteration {champ.iteration_num}: Sharpe {sharpe:.2f} ({champ.timestamp})")

# Validate rollback candidates
print("\nValidating rollback candidates...")
for champ in champions[:3]:
    is_valid, report = rollback_mgr.validate_rollback_champion(
        champion=champ,
        data=finlab_data,
        min_sharpe_threshold=1.5
    )

    status = "✅" if is_valid else "❌"
    print(f"{status} Iteration {champ.iteration_num}: "
          f"Original={report['original_sharpe']:.2f}, "
          f"Current={report.get('current_sharpe', 'N/A')}")

# Perform rollback
target_iteration = 32
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=target_iteration,
    reason="Production issue - high drawdown detected in iteration 45",
    operator="ops@example.com",
    data=finlab_data
)

if success:
    print(f"\n✅ {message}")
else:
    print(f"\n❌ Rollback failed: {message}")

# View rollback audit trail
print("\nRollback History:")
history = rollback_mgr.get_rollback_history(limit=5)
for record in history:
    status = "✅" if record.validation_passed else "❌"
    print(f"{status} {record.timestamp}")
    print(f"   {record.from_iteration} → {record.to_iteration} by {record.operator}")
    print(f"   Reason: {record.reason}")
```

### Pattern 4: Comprehensive Monitoring Dashboard

```python
from src.monitoring.variance_monitor import VarianceMonitor
from src.config.anti_churn_manager import AntiChurnManager
from src.validation.preservation_validator import PreservationValidator

def generate_monitoring_dashboard(
    variance_monitor: VarianceMonitor,
    anti_churn_mgr: AntiChurnManager
) -> Dict[str, Any]:
    """Generate comprehensive monitoring dashboard."""

    # Convergence analysis
    convergence_report = variance_monitor.generate_convergence_report()

    # Update frequency analysis
    update_freq, freq_recommendations = anti_churn_mgr.analyze_update_frequency(window=50)

    # Recent updates summary
    updates_summary = anti_churn_mgr.get_recent_updates_summary(count=10)

    dashboard = {
        'convergence': {
            'status': convergence_report['convergence_status'],
            'iteration': convergence_report['convergence_iteration'],
            'current_variance': convergence_report['current_variance'],
            'total_iterations': convergence_report['total_iterations'],
            'recommendations': convergence_report['recommendations']
        },
        'update_frequency': {
            'rate': update_freq,
            'target_range': '10-20%',
            'status': 'healthy' if 0.10 <= update_freq <= 0.20 else 'warning',
            'recommendations': freq_recommendations
        },
        'recent_updates': updates_summary,
        'variance_trend': convergence_report['variance_trend']
    }

    return dashboard

# Usage
dashboard = generate_monitoring_dashboard(variance_monitor, anti_churn_mgr)

print("\n=== Learning System Monitoring Dashboard ===")
print(f"\nConvergence Status: {dashboard['convergence']['status']}")
print(f"Current Variance: {dashboard['convergence']['current_variance']:.4f}")
print(f"Total Iterations: {dashboard['convergence']['total_iterations']}")

print(f"\nUpdate Frequency: {dashboard['update_frequency']['rate']*100:.1f}%")
print(f"Status: {dashboard['update_frequency']['status']}")

print("\nRecommendations:")
for rec in dashboard['convergence']['recommendations']:
    print(f"  - {rec}")
for rec in dashboard['update_frequency']['recommendations']:
    print(f"  - {rec}")

print(f"\n{dashboard['recent_updates']}")
```

---

## Exception Handling

### Common Exceptions

All components handle common exceptions gracefully:

**Configuration Errors:**
```python
try:
    manager = AntiChurnManager(config_path="missing.yaml")
except FileNotFoundError as e:
    logger.error(f"Configuration file not found: {e}")
except yaml.YAMLError as e:
    logger.error(f"Invalid YAML configuration: {e}")
```

**Validation Errors:**
```python
is_preserved, report = validator.validate_preservation(
    generated_code=code,
    champion=champion,
    execution_metrics=None
)

if not is_preserved:
    if 'extraction_error' in report.parameter_checks:
        # Parameter extraction failed
        logger.error("Failed to extract parameters from generated code")
    else:
        # Other validation failures
        for param, (passed, reason) in report.parameter_checks.items():
            if not passed:
                logger.warning(f"Parameter check failed: {param} - {reason}")
```

**Rollback Errors:**
```python
success, message = rollback_mgr.rollback_to_iteration(
    target_iteration=32,
    reason="Emergency rollback",
    operator="oncall@example.com",
    data=data
)

if not success:
    if "No champion found" in message:
        logger.error(f"Target iteration {target_iteration} not in champion history")
    elif "Validation failed" in message:
        logger.error("Rollback candidate failed validation")
    else:
        logger.error(f"Rollback failed: {message}")
```

---

## Performance Considerations

### VarianceMonitor
- Memory: O(n) where n = total iterations (stores all Sharpe ratios)
- Computation: O(1) for updates, O(window) for variance calculation
- Recommend: Clear `all_sharpes` periodically for very long runs (>1000 iterations)

### PreservationValidator
- Memory: O(1) per validation (no state maintained)
- Computation: O(n) where n = code size for parameter extraction
- Recommend: Cache parameter extraction results if validating same code multiple times

### AntiChurnManager
- Memory: O(m) where m = number of champion updates tracked
- Computation: O(1) for threshold calculation, O(window) for frequency analysis
- Recommend: Periodically archive old update records for very long runs

### RollbackManager
- Memory: O(k) where k = number of champions in Hall of Fame
- Computation: O(k) for history queries, O(1) for rollback record
- I/O: Appends to log file (no rewriting)
- Recommend: Rotate rollback log file periodically (use log rotation tools)

---

## Version History

- **Phase 2 (v2.0)**: Initial implementation of all four components
  - VarianceMonitor with convergence detection
  - PreservationValidator with behavioral checks
  - AntiChurnManager with probation periods
  - RollbackManager with audit trail

- **Phase 3 (v2.1)**: Hybrid threshold system
  - Added `additive_threshold` to AntiChurnManager
  - Supports both relative and absolute improvement thresholds
  - Prevents stagnation at high Sharpe ratios

---

## Support and Troubleshooting

### Common Issues

**Issue: High variance persists after 20+ iterations**
- Check: Preservation constraints might be too loose
- Solution: Tighten `sharpe_tolerance`, `turnover_tolerance` in PreservationValidator
- Solution: Increase `probation_threshold` in AntiChurnManager

**Issue: No champion updates for 30+ iterations (stagnation)**
- Check: Thresholds might be too strict
- Solution: Decrease `post_probation_threshold` in AntiChurnManager
- Solution: Verify `additive_threshold` is reasonable for current Sharpe levels

**Issue: Excessive champion churn (>25% update rate)**
- Check: Thresholds might be too lenient
- Solution: Increase `probation_period` in AntiChurnManager
- Solution: Increase both `probation_threshold` and `post_probation_threshold`

**Issue: Rollback validation fails for historical champions**
- Check: Data distribution might have changed
- Solution: Use lower `min_sharpe_threshold` in validation
- Solution: Skip validation for emergency rollbacks (`validate=False`)

### Debug Logging

Enable detailed logging for troubleshooting:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Component loggers
variance_logger = logging.getLogger('src.monitoring.variance_monitor')
validator_logger = logging.getLogger('src.validation.preservation_validator')
anti_churn_logger = logging.getLogger('src.config.anti_churn_manager')
rollback_logger = logging.getLogger('src.recovery.rollback_manager')

# Set specific log levels
variance_logger.setLevel(logging.DEBUG)
validator_logger.setLevel(logging.INFO)
```

---

## References

- Design Document: `.spec-workflow/specs/learning-system-stability-fixes/design.md`
- Requirements: `.spec-workflow/specs/learning-system-stability-fixes/requirements.md`
- Configuration: `config/learning_system.yaml`
- Hall of Fame Repository: `src/repository/hall_of_fame.py`
- Autonomous Loop: `artifacts/working/modules/autonomous_loop.py`
