# Factor Graph P2 Integration & Optimization Plan (TDD-Oriented)

**Status**: Approved with Expert Audit Revisions
**Created**: 2025-11-26
**Total Duration**: ~19 hours (revised from 13.5 hours)

## Executive Summary

Comprehensive plan to fix Factor Graph identical strategies issue and integrate P2 Factor Library using TDD methodology. Incorporates expert audit feedback for realistic time estimates and missing critical tasks.

### Core Problem
Factor Graph produces **identical strategies** (all Sharpe 0.3012) due to:
- No parameter optimization
- Fixed template parameters
- ASHA pruner ineffective for black-box backtests

### Solution Approach
1. Replace ASHA with TPE optimizer (Bayesian optimization for black-box functions)
2. Implement Template Library with 6 diverse strategy templates
3. Add IS/OOS validation to prevent overfitting
4. Integrate P2 factors (Bollinger %B, Efficiency Ratio)
5. Implement TTPT framework for look-ahead bias detection

---

## 📊 Expert Audit Summary

### ✅ Validated Decisions
- **TPE vs ASHA**: Correct - ASHA can't work with black-box backtests
- **TTPT Framework**: P1 priority - foundational for system integrity
- **IS/OOS Validation**: 12-month OOS, <30% degradation reasonable

### ⚠️ Critical Issues & Resolutions

#### Timing Adjustments
| Task | Original | Revised | Reason |
|------|----------|---------|--------|
| 0.1 TPE | 1h | 2-3h | Underestimated validation logic complexity |
| 2.3 Template Library | 3h | 6-8h | 30min/template unrealistic (now ~1h/template) |

#### New Tasks Added
1. **Task 0.1b**: Backtest Failure Handling (1h)
2. **Task 1.0**: Parameter Search Space Definition (2h)
3. **Task 1.5**: Interface Definition Meeting (30min)
4. **Task 2.4**: Experiment Tracking Setup (1.5h)

#### Design Improvements
- `optimize_with_validation()` now accepts date parameters for future walk-forward support
- Data caching requires comprehensive cache key (template_id + asset_universe + dates + resample_frequency)
- Interface definition meeting before GREEN wave to de-risk parallel work

---

## 🎯 Success Criteria

| Category | Metric | Target | Current |
|----------|--------|--------|---------|
| **Diversity** | Sharpe variance | >0.25 | 0.0 |
| **Templates** | Unique types (20 iter) | ≥4 | 1 |
| **Parameters** | Optimized params | ≥30% differ from defaults | 0% |
| **Overfitting** | IS/OOS degradation | <30% | N/A |
| **Quality** | TTPT pass rate | 100% | N/A |
| **Coverage** | pytest --cov | ≥80% | - |
| **Regression** | P1 tests | 92/92 pass | 92/92 ✅ |

---

## 📋 Implementation Phases

### Phase 0: Critical Foundation (Sequential - 4h 15min)

#### Task 0.1: TPE Optimizer Implementation (2-3h) 🔴 P0
**TDD RED Phase**:
```python
# tests/learning/test_tpe_optimizer.py
def test_tpe_sampler_initialization():
    """WHEN creating study THEN uses TPESampler"""

def test_optimize_with_validation_is_oos_split():
    """WHEN optimizing THEN validates on OOS period"""

def test_degradation_threshold_warning():
    """WHEN degradation >30% THEN logs warning"""
```

**Implementation**:
- Modify `src/learning/optimizer.py`
- Replace `HyperbandPruner` with `TPESampler(n_startup_trials=10, n_ei_candidates=24, multivariate=True)`
- Add `optimize_with_validation()` method:
  ```python
  def optimize_with_validation(
      self,
      objective_fn: Callable[[Dict[str, Any]], float],
      n_trials: int,
      param_space: Dict[str, Any],
      is_start_date: str,  # Support future walk-forward
      is_end_date: str,
      oos_start_date: str,
      oos_end_date: str,
      degradation_threshold: float = 0.30
  ) -> Dict[str, Any]:
      """Optimize with IS/OOS validation."""
      # Run optimization on in-sample data
      # Validate on out-of-sample data
      # Calculate degradation, warn if >threshold
  ```

**Quality Gates**:
- All tests pass
- Type hints comprehensive
- Docstrings with examples

---

#### Task 0.1b: Backtest Failure Handling (1h) 🔴 P0
**NEW - Expert Recommendation**

**TDD RED Phase**:
```python
def test_backtest_failure_returns_pruned_trial():
    """WHEN backtest fails THEN raises TrialPruned"""

def test_divide_by_zero_handled():
    """WHEN factor causes divide-by-zero THEN trial pruned"""

def test_optuna_study_continues_after_failure():
    """WHEN trial fails THEN study continues"""
```

**Implementation**:
- Add try/except in objective wrapper
- Return `optuna.exceptions.TrialPruned()` on failures
- Log error details for debugging

---

#### Task 0.2: UnifiedLoop Migration (30min) 🔴 P0

**TDD RED Phase**:
```python
def test_unified_loop_supports_template_mode():
    """WHEN template_mode=true THEN uses UnifiedLoop"""

def test_backward_compatibility_with_learning_loop():
    """WHEN template_mode=false THEN uses LearningLoop"""
```

**Implementation**:
- Update `experiments/llm_learning_validation/orchestrator.py` lines 247-248:
  ```python
  # Before:
  learning_loop = LearningLoop(learning_config)

  # After:
  from src.learning.unified_loop import UnifiedLoop
  learning_loop = UnifiedLoop.from_config(learning_config)
  ```

---

#### Task 0.3: Config File Updates (15min) 🔴 P0

**Files to Update**:
- `experiments/llm_learning_validation/config_pilot_fg_only_20.yaml`
- `experiments/llm_learning_validation/config_pilot_hybrid_20.yaml`
- All other config files using Factor Graph

**Changes**:
```yaml
template_mode: true  # Enable Template Library
experimental:
  use_factor_graph: true  # Re-enable after fixes
```

---

#### Task 0.4: P1 Regression Check (30min) 🔴 P0

**Command**:
```bash
pytest tests/integration/test_p1_component_integration.py -v
pytest tests/integration/test_e2e_strategy_pipeline.py -v
```

**Quality Gate**: 92/92 tests MUST pass before proceeding to Phase 1

---

### Phase 1: Parameter Search Spaces & TDD RED Wave (Parallel - 3h 30min)

#### Task 1.0: Parameter Search Space Definition (2h) 🔴 P0
**NEW - Expert Recommendation**

**Deliverable**: `src/learning/template_param_spaces.yaml`

```yaml
value_momentum:
  sma_short_period:
    type: int
    min: 10
    max: 50
    default: 20
  sma_long_period:
    type: int
    min: 40
    max: 120
    default: 60
  momentum_period:
    type: int
    min: 10
    max: 100
    default: 30

revenue_based:
  revenue_growth_threshold:
    type: uniform
    min: 0.05
    max: 0.30
    default: 0.15
  # ... 5 more templates
```

**Why Critical**: Defines optimization boundaries for all 6 templates. Required before optimizer integration.

---

#### Task 1.1: Bollinger %B Factor Tests (1.5h) 🟡 P1

**TDD RED Phase** - 6 test cases:
```python
# tests/factor_library/test_bollinger_factor.py
class TestBollingerPercentB:
    def test_bollinger_bands_calculation(self, sample_price_data):
        """GIVEN close prices WHEN calculating Bollinger Bands THEN returns upper/middle/lower bands"""

    def test_percentb_values_range(self):
        """WHEN calculating %B THEN values in reasonable range"""

    def test_signal_generation_oversold(self):
        """WHEN %B < 0 THEN signal = 1 (buy)"""

    def test_signal_generation_overbought(self):
        """WHEN %B > 1 THEN signal = -1 (sell)"""

    def test_metadata_structure(self):
        """THEN metadata contains upper_band, middle_band, lower_band, percentb"""

    def test_edge_case_flat_prices(self):
        """WHEN prices flat THEN %B = 0.5"""
```

---

#### Task 1.2: Efficiency Ratio Factor Tests (1.5h) 🟡 P1

**TDD RED Phase** - 5 test cases:
```python
# tests/factor_library/test_er_factor.py
class TestEfficiencyRatio:
    def test_er_calculation(self, sample_price_data):
        """GIVEN price data WHEN calculating ER THEN matches manual calculation"""

    def test_er_range_bounds(self):
        """THEN ER values in [0, 1] range"""

    def test_high_er_trending_market(self):
        """WHEN trending market THEN ER close to 1"""

    def test_low_er_choppy_market(self):
        """WHEN choppy market THEN ER close to 0"""

    def test_signal_generation_regime_classification(self):
        """WHEN ER > 0.5 THEN signal = 1 (trending), ELSE signal = -1 (mean-reverting)"""
```

---

#### Task 1.3: Template Library Tests (1h) 🔴 P0

**TDD RED Phase** - 8 test cases:
```python
# tests/learning/test_template_library.py
class TestTemplateLibrary:
    def test_template_config_structure():
        """THEN library contains 6 templates"""

    def test_required_templates_exist():
        """THEN all 6 templates (value_momentum, revenue_based, etc.) present"""

    def test_get_random_template_diversity():
        """WHEN calling get_random_template 100 times THEN returns ≥4 unique templates"""

    def test_data_caching_mechanism():
        """WHEN loading data twice THEN second load uses cache"""

    def test_cache_key_comprehensive():
        """THEN cache key includes template_id + asset_universe + dates + resample"""

    def test_template_param_space_loading():
        """WHEN loading template THEN loads param_space from YAML"""

    def test_data_loader_optional():
        """WHEN data_loader None THEN uses default FinLab loader"""

    def test_template_file_path_exists():
        """THEN all template file_paths exist on filesystem```

---

#### Task 1.5: Interface Definition Meeting (30min) 🔴 P0
**NEW - Expert Recommendation**

**Purpose**: Prevent GREEN wave integration issues

**Deliverable**: `docs/P2_INTERFACE_SPECIFICATION.md`

**Must Define**:
```python
# Bollinger %B Factor Interface
def bollinger_percentb_factor(
    close: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Returns:
        {
            'signal': pd.DataFrame,  # [-1, 1] range
            'metadata': {
                'upper_band': pd.DataFrame,
                'middle_band': pd.DataFrame,
                'lower_band': pd.DataFrame,
                'percentb': pd.DataFrame
            }
        }
    """

# Efficiency Ratio Factor Interface
def efficiency_ratio_factor(
    close: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Returns:
        {
            'signal': pd.DataFrame,  # [-1, 1] range
            'metadata': {
                'er': pd.DataFrame,
                'regime': pd.DataFrame  # 'trending' or 'mean_reverting'
            }
        }
    """

# Template Library Interface
class TemplateLibrary:
    def get_template(self, name: str) -> TemplateConfig
    def get_random_template(self, exclude: Optional[List[str]] = None) -> TemplateConfig
    def get_cached_data(self, template_name: str) -> Dict[str, Any]
```

---

### Phase 2: TDD GREEN Wave (Parallel - 11h)

#### Task 2.1: Bollinger %B Implementation (2h) 🟡 P1

**File**: `src/factor_library/mean_reversion_factors.py`

**Implementation**:
```python
def bollinger_percentb_factor(
    close: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Bollinger %B mean reversion factor.

    %B = (close - lower_band) / (upper_band - lower_band)

    Signal logic:
    - %B < 0: Oversold → signal = 1 (buy)
    - %B > 1: Overbought → signal = -1 (sell)
    - 0 <= %B <= 1: Normalize to [-1, 1]
    """
    # Calculate Bollinger Bands using TA-Lib
    # Calculate %B
    # Generate signals
    # Return {signal, metadata}
```

---

#### Task 2.2: Efficiency Ratio Implementation (2h) 🟡 P1

**File**: `src/factor_library/regime_factors.py` (NEW)

**Implementation**:
```python
def efficiency_ratio_factor(
    close: pd.DataFrame,
    params: Dict[str, Any]
) -> Dict[str, Any]:
    """Efficiency Ratio regime classification factor.

    ER = net_change / sum(abs(daily_changes))

    Signal logic:
    - ER > 0.5: Trending → signal = 1
    - ER <= 0.5: Mean-reverting → signal = -1
    """
    # Calculate net change
    # Calculate daily changes sum
    # Calculate ER
    # Classify regime
    # Return {signal, metadata}
```

---

#### Task 2.3: Template Library Implementation (6-8h) 🔴 P0
**REVISED TIME ESTIMATE** - Expert Recommendation

**File**: `src/learning/template_library.py` (NEW)

**Implementation Structure**:
```python
@dataclass
class TemplateConfig:
    name: str
    file_path: str
    category: str  # 'value', 'growth', 'momentum', 'quality'
    param_space: Dict[str, Tuple]
    default_params: Dict[str, Any]
    data_loader: Optional[Callable] = None

class TemplateLibrary:
    def __init__(self, param_space_file: str = "src/learning/template_param_spaces.yaml"):
        self.templates = self._load_templates()
        self._data_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _load_templates(self) -> Dict[str, TemplateConfig]:
        """Load 6 strategy templates with param spaces."""
        return {
            'value_momentum': TemplateConfig(...),
            'revenue_based': TemplateConfig(...),
            'low_volatility': TemplateConfig(...),
            'small_cap': TemplateConfig(...),
            'fundamental': TemplateConfig(...),
            'revenue_momentum': TemplateConfig(...)
        }

    def get_random_template(self, exclude: Optional[List[str]] = None) -> TemplateConfig:
        """Random selection avoiding recent repeats."""

    def get_cached_data(self, template_name: str, **cache_key_params) -> Dict:
        """Pre-load and cache template data.

        Cache key: (template_id, asset_universe, start_date, end_date, resample_frequency)
        """
        cache_key = self._build_cache_key(template_name, **cache_key_params)

        if cache_key in self._data_cache:
            self._cache_hits += 1
            return self._data_cache[cache_key]

        self._cache_misses += 1
        data = self._load_finlab_data(**cache_key_params)
        self._data_cache[cache_key] = data
        return data
```

**6 Templates to Implement** (~1h each):
1. **value_momentum**: 高殖利率烏龜_改.py
2. **revenue_based**: Revenue growth strategy
3. **low_volatility**: Low volatility anomaly
4. **small_cap**: Small cap premium
5. **fundamental**: Fundamental quality
6. **revenue_momentum**: Revenue + price momentum

---

#### Task 2.4: Experiment Tracking Setup (1.5h) 🟡 P1
**NEW - Expert Recommendation**

**Purpose**: Reproducibility and analysis of optimization trials

**Options**:
1. **MLflow** (Recommended):
   ```python
   import mlflow

   with mlflow.start_run():
       mlflow.log_params(params)
       mlflow.log_metric("sharpe_ratio_is", is_sharpe)
       mlflow.log_metric("sharpe_ratio_oos", oos_sharpe)
       mlflow.log_metric("degradation", degradation)
   ```

2. **Simple DB Logger**:
   ```python
   # Save to SQLite
   conn = sqlite3.connect('experiments.db')
   cursor.execute("""
       INSERT INTO trials (trial_id, params, is_sharpe, oos_sharpe, degradation)
       VALUES (?, ?, ?, ?, ?)
   """, (trial_id, json.dumps(params), is_sharpe, oos_sharpe, degradation))
   ```

**Implementation**:
- Create `src/learning/experiment_tracker.py`
- Integrate with `optimize_with_validation()`
- Add dashboard/query utilities

---

### Phase 3: Integration Wave (Partial Parallel - 7h 30min)

#### Task 3.1: TPE Optimizer Integration (4h) 🔴 P0

**Integration Points**:
1. Connect TPE optimizer to Template Library
2. Define 50 trials per strategy
3. Implement objective function with cached data
4. Add experiment tracking
5. Implement IS/OOS validation with 12-month OOS period

**Implementation**:
```python
# In UnifiedLoop or FactorGraphStrategy
def optimize_template_strategy(self, template: TemplateConfig) -> Dict[str, Any]:
    """Optimize strategy using TPE with IS/OOS validation."""

    # Load cached data
    data = self.template_library.get_cached_data(
        template.name,
        asset_universe=self.config.asset_universe,
        start_date="2020-01-01",
        end_date="2023-12-31",
        resample_frequency="D"
    )

    # Define objective function
    def objective_fn(params):
        try:
            # Run backtest with params
            result = self._run_backtest_with_template(template, params, data)
            return result.sharpe_ratio
        except Exception as e:
            logger.warning(f"Trial failed: {e}")
            raise optuna.exceptions.TrialPruned()

    # Optimize with IS/OOS validation
    result = self.optimizer.optimize_with_validation(
        objective_fn=objective_fn,
        n_trials=50,
        param_space=template.param_space,
        is_start_date="2020-01-01",
        is_end_date="2022-12-31",
        oos_start_date="2023-01-01",
        oos_end_date="2023-12-31"
    )

    return result
```

---

#### Task 3.2: TTPT Framework (2h) 🔴 P1

**TDD RED Phase**:
```python
# tests/validation/test_ttpt_framework.py
def test_ttpt_detects_look_ahead_bias():
    """WHEN using future data THEN TTPT fails"""

def test_ttpt_passes_valid_strategy():
    """WHEN using only past data THEN TTPT passes"""

def test_time_travel_perturbation():
    """WHEN shifting data forward 1 day THEN strategy fails if using future data"""
```

**Implementation**: `src/validation/ttpt_framework.py`

---

#### Task 3.3: Runtime TTPT Monitor (1.5h) 🟢 P2

**TDD RED Phase**:
```python
def test_runtime_monitor_integration():
    """WHEN running backtest THEN TTPT monitor active"""
```

---

### Phase 4: Validation & Documentation (Sequential - 6h)

#### Task 4.1: Factor Registry Update (1h) 🟡 P1

**File**: `src/factor_library/__init__.py`

```python
FACTOR_REGISTRY = {
    # Existing factors...
    'bollinger_percentb': bollinger_percentb_factor,
    'efficiency_ratio': efficiency_ratio_factor,
}
```

---

#### Task 4.2: Validation Pipeline Update (1h) 🟡 P1

**Ensure**:
- Bollinger %B and ER factors integrate with existing validation
- Template Library works with validation pipeline

---

#### Task 4.3: Integration Testing (2h) 🔴 P0

**Test Suite**: `tests/integration/test_factor_graph_p2_integration.py`

```python
def test_tpe_optimizer_with_template_library():
    """WHEN optimizing THEN produces diverse strategies"""

def test_is_oos_validation_catches_overfitting():
    """WHEN overfitting THEN degradation >30% warning"""

def test_data_caching_performance():
    """WHEN using cached data THEN 70% speedup"""

def test_20_iteration_diversity():
    """WHEN running 20 iterations THEN ≥4 unique templates AND Sharpe variance >0.25"""
```

---

#### Task 4.4: Documentation Update (1.5h) 🟢 P2

**Files to Update**:
- `docs/FACTOR_LIBRARY_API.md` - Add Bollinger %B and ER
- `docs/TEMPLATE_LIBRARY_USAGE.md` (NEW)
- `docs/TPE_OPTIMIZER_GUIDE.md` (NEW)
- `README.md` - Update Feature List

---

## 🔄 Dependency Matrix & Parallelization

### Critical Path (19 hours)
```
0.1 (2-3h) → 0.1b (1h) → 0.2 (30min) → 0.3 (15min) → 0.4 (30min) →
1.0 (2h) → 1.3 (1h) → 1.5 (30min) → 2.3 (6-8h) → 2.4 (1.5h) → 3.1 (4h) →
4.1 (1h) → 4.2 (1h) → 4.3 (2h) → 4.4 (1.5h)
```

### Parallel Opportunities

**Wave 1** (RED Phase - can run in parallel after Phase 0):
- Task 1.1 (Bollinger Tests) ║
- Task 1.2 (ER Tests) ║
- Task 1.3 (Template Library Tests) ║

**Wave 2** (GREEN Phase - can run in parallel after Task 1.5):
- Task 2.1 (Bollinger Impl) ║
- Task 2.2 (ER Impl) ║
- Task 2.3 (Template Library Impl) ║ LONGEST - on critical path

**Wave 3** (Integration - partial parallel):
- Task 3.2 (TTPT Framework) ║ Can start immediately after Task 2.3
- Task 3.3 (Runtime Monitor) ║ Depends on 3.2
- Task 3.1 (Optimizer Integration) - Depends on 2.3, 2.4

---

## 🎭 Wave Execution Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 0: Foundation (Sequential - MUST complete first)         │
│ ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐          │
│ │ 0.1  │ → │ 0.1b │ → │ 0.2  │ → │ 0.3  │ → │ 0.4  │          │
│ │ 2-3h │   │ 1h   │   │ 30min│   │ 15min│   │ 30min│          │
│ └──────┘   └──────┘   └──────┘   └──────┘   └──────┘          │
│                                                   ▼              │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 1: TDD RED Wave (Parallel after 0.4)                     │
│ ┌──────┐         ┌──────┐                                       │
│ │ 1.0  │ ──────► │ 1.5  │                                       │
│ │ 2h   │         │ 30min│                                       │
│ └──────┘         └──────┘                                       │
│     │                                                            │
│     └──────┬──────────────┬──────────────┐                      │
│           ┌▼─────┐   ┌────▼───┐   ┌──────▼┐                    │
│           │ 1.1  │   │  1.2   │   │  1.3  │                    │
│           │ 1.5h │   │  1.5h  │   │  1h   │                    │
│           └──┬───┘   └────┬───┘   └───┬───┘                    │
│              └───────┬────┘           ▼                         │
│                      ▼             ┌──────┐                     │
│                  ┌──────┐          │ 1.5  │                     │
│                  │      │          │ 30min│                     │
│                  └──────┘          └───┬──┘                     │
│                                        ▼                         │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 2: TDD GREEN Wave (Parallel after 1.5)                   │
│ ┌──────┐         ┌──────┐         ┌──────┐                     │
│ │ 2.1  │         │  2.2 │         │  2.3 │ ← CRITICAL PATH     │
│ │ 2h   │         │  2h  │         │ 6-8h │                     │
│ └──┬───┘         └───┬──┘         └───┬──┘                     │
│    └─────────────────┴────────────────┼────────┐               │
│                                        ▼        │               │
│                                   ┌──────┐     │               │
│                                   │ 2.4  │     │               │
│                                   │ 1.5h │     │               │
│                                   └───┬──┘     │               │
│                                       ▼        ▼               │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 3: Integration Wave (Partial Parallel)                   │
│                                   ┌──────┐   ┌──────┐          │
│                                   │ 3.2  │   │  3.1 │          │
│                                   │ 2h   │   │  4h  │          │
│                                   └───┬──┘   └───┬──┘          │
│                                       ▼          │              │
│                                   ┌──────┐      │              │
│                                   │ 3.3  │      │              │
│                                   │ 1.5h │      │              │
│                                   └──────┘      ▼              │
├─────────────────────────────────────────────────────────────────┤
│ PHASE 4: Validation (Sequential)                               │
│                                   ┌──────┐                     │
│                                   │ 4.1  │                     │
│                                   │ 1h   │                     │
│                                   └───┬──┘                     │
│                                       ▼                         │
│                                   ┌──────┐                     │
│                                   │ 4.2  │                     │
│                                   │ 1h   │                     │
│                                   └───┬──┘                     │
│                                       ▼                         │
│                                   ┌──────┐                     │
│                                   │ 4.3  │                     │
│                                   │ 2h   │                     │
│                                   └───┬──┘                     │
│                                       ▼                         │
│                                   ┌──────┐                     │
│                                   │ 4.4  │                     │
│                                   │ 1.5h │                     │
│                                   └──────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛡️ Risk Management

### High-Risk Items

1. **Template Library Complexity** (Task 2.3 - 6-8h)
   - **Risk**: Underestimated implementation time
   - **Mitigation**: Time estimate revised from 3h to 6-8h based on expert audit
   - **Contingency**: Implement 3 templates first (value_momentum, revenue_based, low_volatility), defer others to P2

2. **IS/OOS Validation Effectiveness**
   - **Risk**: 12-month OOS may not be sufficient
   - **Mitigation**: Design supports future walk-forward validation (date parameters)
   - **Contingency**: Adjust OOS period based on initial results

3. **Data Caching Cache-Key Bugs**
   - **Risk**: Incorrect cache key causes data mismatch
   - **Mitigation**: Comprehensive cache key (template_id + asset_universe + dates + resample)
   - **Contingency**: Add cache validation tests, log cache hits/misses

4. **P1 Regression Failures**
   - **Risk**: UnifiedLoop migration breaks existing tests
   - **Mitigation**: Task 0.4 regression check before proceeding
   - **Contingency**: Keep LearningLoop as fallback, feature flag for UnifiedLoop

---

## 📊 Quality Gates

### Phase Boundaries

**After Phase 0**:
- [ ] TPE optimizer unit tests pass
- [ ] Backtest failure handling robust
- [ ] UnifiedLoop migration successful
- [ ] Config files updated
- [ ] P1 regression: 92/92 tests pass
- [ ] 5-iteration smoke test successful

**After Phase 1**:
- [ ] All TDD RED tests written and failing
- [ ] Parameter search spaces defined for 6 templates
- [ ] Interface specification documented
- [ ] Test coverage ≥80% for test files themselves

**After Phase 2**:
- [ ] All TDD GREEN implementations complete
- [ ] All tests now passing
- [ ] Bollinger %B and ER factors working
- [ ] Template Library with 6 templates functional
- [ ] Data caching demonstrating 70% speedup
- [ ] Experiment tracking operational

**After Phase 3**:
- [ ] TPE optimizer integrated with Template Library
- [ ] IS/OOS validation working
- [ ] TTPT framework operational
- [ ] 20-iteration test: Sharpe variance >0.25
- [ ] 20-iteration test: ≥4 unique templates

**Final Validation**:
- [ ] All success criteria met
- [ ] Documentation complete
- [ ] P1 regression still passing (92/92)
- [ ] pytest coverage ≥80%

---

## 🚀 Next Steps

1. **Immediate**: Start Task 0.1 (TPE Optimizer Implementation)
2. **After Phase 0**: Launch TDD RED Wave in parallel
3. **Milestone 1**: Phase 0 complete + smoke test passing
4. **Milestone 2**: Phase 2 complete + data caching validated
5. **Final Milestone**: All success criteria met

---

## 📚 References

### Expert Audit Feedback
- TPE vs ASHA: TPE better for black-box optimization
- Time estimates: Task 0.1 (1h→2-3h), Task 2.3 (3h→6-8h)
- Missing tasks: Parameter spaces, experiment tracking, failure handling, interface definition
- IS/OOS design: Support future walk-forward validation
- Data caching: Comprehensive cache keys critical

### Technical Documentation
- `docs/P1_INTEGRATION_TEST_REPORT.md`: P1 completion status
- `docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md`: Current issues analysis
- `.spec-workflow/specs/comprehensive-improvement-plan/tasks.md`: Original P2 task breakdown

### Code Locations
- Optimizer: `src/learning/optimizer.py`
- Orchestrator: `experiments/llm_learning_validation/orchestrator.py`
- Factor Library: `src/factor_library/mean_reversion_factors.py`
- Configs: `experiments/llm_learning_validation/config_*.yaml`
