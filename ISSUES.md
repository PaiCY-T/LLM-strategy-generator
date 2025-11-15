# LLM Strategy Generator - Issue Tracker

**Last Updated**: 2025-01-15
**Source**: P1.4 Validation Gates & Zen Code Review

---

## Issue Status Legend

- 🔴 **Critical**: Blocks production deployment
- 🟠 **High**: Significant impact on functionality or performance
- 🟡 **Medium**: Important but not blocking
- 🟢 **Low**: Enhancement or technical debt
- ✅ **Resolved**: Fixed and verified
- 🚧 **In Progress**: Currently being worked on
- 📋 **Backlog**: Planned for future milestone
- ⏸️ **On Hold**: Deferred or blocked

---

## Active Issues

### 🟠 High Priority (P2 Milestone)

#### Issue #1: ASHA Pruner Not Used Effectively
- **Priority**: 🟠 High
- **Status**: 📋 Backlog (P2)
- **Type**: Performance Optimization
- **Location**: `src/learning/optimizer.py:184`
- **Milestone**: P2.1 - Hyperparameter Optimization Enhancement

**Description**:
ASHA's early-stopping capability is completely disabled because the objective function reports value only at `max_resource`. This prevents the pruner from stopping underperforming trials early, making it no better than random search.

**Current Implementation**:
```python
# Line 184
trial.report(value, step=self.max_resource)
```

**Impact**:
- No early stopping (0% pruning rate instead of 50-80%)
- No time savings vs. random search
- Wasted computational resources on poor trials

**Recommended Fix**:

**Option A**: Make objective_fn iterative (if possible)
```python
# Modify objective_fn signature to accept trial object
def objective_fn(params: dict, trial: optuna.Trial) -> float:
    for step in range(1, max_resource + 1):
        # Train for one step
        score = train_step(params, step)

        # Report intermediate value
        trial.report(score, step)

        # Check if should prune
        if trial.should_prune():
            raise optuna.TrialPruned()

    return final_score
```

**Option B**: Use MedianPruner for black-box objectives (simpler)
```python
# In ASHAOptimizer._create_study()
from optuna.pruners import MedianPruner

pruner = MedianPruner(
    n_startup_trials=5,
    n_warmup_steps=10
)

# Remove reporting logic from objective_wrapper
def objective_wrapper(trial: optuna.Trial) -> float:
    params = {...}
    return objective_fn(params)  # No intermediate reporting needed
```

**Estimate**: 4-6h (Option B), 8-12h (Option A)

**Acceptance Criteria**:
- [ ] Pruning rate ≥50% on test problems
- [ ] Search time reduced by ≥40% vs. current implementation
- [ ] Best value quality maintained or improved
- [ ] All existing tests still pass

**References**:
- Optuna MedianPruner docs: https://optuna.readthedocs.io/en/stable/reference/generated/optuna.pruners.MedianPruner.html
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #2`

---

### 🟡 Medium Priority (P2 Milestone)

#### Issue #2: early_stop_callback Raises NotImplementedError
- **Priority**: 🟡 Medium
- **Status**: 📋 Backlog (P2)
- **Type**: API Completeness
- **Location**: `src/learning/optimizer.py:212-232`
- **Milestone**: P2.1 - API Cleanup

**Description**:
Public method `early_stop_callback` raises `NotImplementedError`, creating incomplete API that confuses users.

**Current Implementation**:
```python
def early_stop_callback(self, study: optuna.Study, trial: optuna.Trial) -> None:
    """Callback for early stopping logic."""
    # TODO: Implement callback logic
    raise NotImplementedError("P0.2: To be implemented in Week 2-3")
```

**Impact**:
- Confusing user experience (public method that doesn't work)
- Incomplete API documentation
- Users may try to use it and get errors

**Recommended Fix**:

**Option A**: Implement the callback
```python
def early_stop_callback(
    self,
    study: optuna.Study,
    trial: optuna.Trial,
    patience: int = 10,
    min_improvement: float = 0.01
) -> None:
    """Early stopping callback based on improvement stagnation.

    Stops optimization if no improvement ≥ min_improvement in last
    patience trials.
    """
    if len(study.trials) < patience:
        return

    recent_trials = study.trials[-patience:]
    recent_values = [t.value for t in recent_trials if t.value is not None]

    if len(recent_values) < patience:
        return

    best_recent = max(recent_values)
    best_overall = study.best_value

    improvement = (best_recent - best_overall) / abs(best_overall)

    if improvement < min_improvement:
        study.stop()
```

**Option B**: Make it private/remove
```python
# Rename to _early_stop_callback to indicate internal use
def _early_stop_callback(self, study, trial) -> None:
    """Internal: Not yet implemented."""
    raise NotImplementedError("Future feature")
```

**Option C**: Remove entirely
```python
# Delete the method if not needed
```

**Estimate**: 2-3h (Option A), 0.5h (Option B/C)

**Acceptance Criteria**:
- [ ] No NotImplementedError in public API
- [ ] Documentation updated
- [ ] Tests added if implemented (Option A)

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #3`

---

#### Issue #3: VaR/CVaR Risk Metrics Not Implemented
- **Priority**: 🟡 Medium
- **Status**: 📋 Backlog (P2)
- **Type**: Feature Completeness
- **Location**: `src/intelligence/multi_objective.py:156-160`
- **Milestone**: P2 - Risk Metric Enhancement (Optional)

**Description**:
`EpsilonConstraintOptimizer.optimize()` accepts `risk_metric` parameter with values `'var'` and `'cvar'` but raises `NotImplementedError` for both.

**Current Implementation**:
```python
def risk_constraint(w: npt.NDArray[np.float64]) -> float:
    if risk_metric == 'volatility':
        risk = np.sqrt(w @ cov_matrix @ w) * np.sqrt(252)
    elif risk_metric == 'var':
        raise NotImplementedError("VaR risk metric not yet implemented")
    elif risk_metric == 'cvar':
        raise NotImplementedError("CVaR risk metric not yet implemented")
```

**Impact**:
- Misleading API (parameters that don't work)
- Users expecting VaR/CVaR will get errors
- Incomplete risk management toolkit

**Recommended Fix**:

**Option A**: Implement VaR and CVaR (if needed)
```python
def risk_constraint(w: npt.NDArray[np.float64]) -> float:
    if risk_metric == 'volatility':
        risk = np.sqrt(w @ cov_matrix @ w) * np.sqrt(252)
    elif risk_metric == 'var':
        # Value at Risk (parametric method)
        portfolio_return = w @ mean_returns * 252
        portfolio_vol = np.sqrt(w @ cov_matrix @ w) * np.sqrt(252)
        # 95% VaR (1.645 std devs)
        risk = -(portfolio_return - 1.645 * portfolio_vol)
    elif risk_metric == 'cvar':
        # Conditional Value at Risk (CVaR/Expected Shortfall)
        # Historical simulation method
        portfolio_returns = returns @ w
        sorted_returns = np.sort(portfolio_returns)
        var_threshold = np.percentile(sorted_returns, 5)
        cvar = -np.mean(sorted_returns[sorted_returns <= var_threshold]) * np.sqrt(252)
        risk = cvar
    return float(epsilon - risk)
```

**Option B**: Make API explicit (simpler, recommended)
```python
# At start of optimize() method
if risk_metric not in ['volatility']:
    raise ValueError(
        f"Unsupported risk_metric: '{risk_metric}'. "
        f"Currently only 'volatility' is supported."
    )

# Update docstring
def optimize(
    self,
    returns: pd.DataFrame,
    epsilon_values: npt.NDArray[np.float64],
    risk_metric: str = 'volatility'  # Only 'volatility' supported
) -> List[PortfolioWeights]:
    """...

    Args:
        risk_metric: Risk measure ('volatility' only - VaR/CVaR planned for P3)
    """
```

**Estimate**: 8-12h (Option A), 0.5h (Option B)

**Acceptance Criteria**:
- [ ] No NotImplementedError for documented features
- [ ] Clear error messages for unsupported options
- [ ] Documentation updated with supported values
- [ ] If implemented (Option A): Tests for VaR/CVaR validation

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #4`

---

### 🟢 Low Priority (P3+ Milestone)

#### Issue #4: Code Duplication in RegimeDetector
- **Priority**: 🟢 Low
- **Status**: 📋 Backlog (P3)
- **Type**: Code Quality / Refactoring
- **Location**: `src/intelligence/regime_detector.py:92-142, 144-209`
- **Milestone**: P3 - Technical Debt Cleanup

**Description**:
`detect_regime()` and `get_regime_stats()` duplicate SMA and volatility calculations, violating DRY principle.

**Current Implementation**:
```python
# In detect_regime() - lines 123-128
sma_50 = prices.rolling(window=50).mean().iloc[-1]
sma_200 = prices.rolling(window=200).mean().iloc[-1]
returns = prices.pct_change().dropna()
volatility = returns.std() * np.sqrt(252)

# In get_regime_stats() - lines 171-176
sma_50 = prices.rolling(window=50).mean().iloc[-1]  # DUPLICATE
sma_200 = prices.rolling(window=200).mean().iloc[-1]  # DUPLICATE
returns = prices.pct_change().dropna()  # DUPLICATE
volatility = returns.std() * np.sqrt(252)  # DUPLICATE
```

**Impact**:
- Maintenance overhead (changes must be applied twice)
- Risk of inconsistency if one method updated but not the other
- Slightly larger codebase

**Recommended Fix**:
```python
def _calculate_regime_components(
    self,
    prices: pd.Series
) -> tuple[float, float, float]:
    """Calculate SMA and volatility components (private helper).

    Returns:
        Tuple of (sma_50, sma_200, annualized_volatility)
    """
    if len(prices) < 200:
        raise ValueError(f"Need ≥200 data points, got {len(prices)}")

    sma_50 = prices.rolling(window=50).mean().iloc[-1]
    sma_200 = prices.rolling(window=200).mean().iloc[-1]
    returns = prices.pct_change().dropna()
    volatility = returns.std() * np.sqrt(252)

    return sma_50, sma_200, volatility

def detect_regime(self, prices: pd.Series) -> MarketRegime:
    sma_50, sma_200, volatility = self._calculate_regime_components(prices)
    # ... rest of logic

def get_regime_stats(self, prices: pd.Series) -> RegimeStats:
    sma_50, sma_200, volatility = self._calculate_regime_components(prices)
    # ... rest of logic
```

**Estimate**: 1-2h

**Acceptance Criteria**:
- [ ] No duplicated calculation logic
- [ ] All tests still pass
- [ ] Performance unchanged (helper should be inlined by Python)

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #5`

---

#### Issue #5: Dict Interface Returns Lists Instead of Views
- **Priority**: 🟢 Low
- **Status**: 📋 Backlog (P3)
- **Type**: Enhancement / API Improvement
- **Location**: `src/backtest/metrics.py:165-216`
- **Milestone**: P3 - API Enhancement

**Description**:
`StrategyMetrics.keys()`, `.values()`, `.items()` return lists instead of dict views, less idiomatic and slightly less efficient.

**Current Implementation**:
```python
def keys(self) -> List[str]:
    return ['sharpe_ratio', 'total_return', 'max_drawdown',
            'win_rate', 'execution_success']

def values(self) -> List[Any]:
    return [self.sharpe_ratio, self.total_return, ...]

def items(self) -> List[Tuple[str, Any]]:
    return [(key, getattr(self, key)) for key in self.keys()]
```

**Impact**:
- Minor: Less memory efficient (creates new list each call)
- Minor: Not exactly dict-like behavior (dict returns views)
- Works fine for current usage

**Recommended Fix**:
```python
from typing import KeysView, ValuesView, ItemsView

def keys(self) -> KeysView[str]:
    """Return dict-like keys view."""
    return self.to_dict().keys()

def values(self) -> ValuesView[Any]:
    """Return dict-like values view."""
    return self.to_dict().values()

def items(self) -> ItemsView[str, Any]:
    """Return dict-like items view."""
    return self.to_dict().items()
```

**Estimate**: 1h

**Acceptance Criteria**:
- [ ] Return proper dict views
- [ ] All tests still pass
- [ ] Type hints updated

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #6`

---

#### Issue #6: Hardcoded Regularization Parameter
- **Priority**: 🟢 Low
- **Status**: 📋 Backlog (P3)
- **Type**: Enhancement / Configurability
- **Location**: `src/intelligence/multi_objective.py:136`
- **Milestone**: P3 - Configuration Enhancement

**Description**:
Regularization term `1e-8` is hardcoded in covariance matrix, not tunable for different datasets.

**Current Implementation**:
```python
# Line 136
cov_matrix += np.eye(n_assets) * 1e-8
```

**Impact**:
- Minor: May not be optimal for all datasets
- Minor: No user control over numerical stability tuning
- Works fine for typical portfolio sizes

**Recommended Fix**:
```python
# In __init__
def __init__(
    self,
    diversity_threshold: float = 0.30,
    max_weight: float = 0.70,
    min_weight: float = 0.0,
    regularization: float = 1e-8
):
    """...

    Args:
        regularization: Ridge regularization for covariance matrix (default: 1e-8)
    """
    # ... validation
    self.regularization = regularization

# In optimize method
cov_matrix += np.eye(n_assets) * self.regularization
```

**Estimate**: 0.5h

**Acceptance Criteria**:
- [ ] Regularization parameter is configurable
- [ ] Default value unchanged (1e-8)
- [ ] All tests still pass

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #7`

---

## Resolved Issues

### ✅ Issue #0: Numerical Instability in ERC Optimizer
- **Priority**: 🔴 Critical
- **Status**: ✅ Resolved (2025-01-15)
- **Type**: Bug Fix / Numerical Stability
- **Location**: `src/intelligence/portfolio_optimizer.py:109-140`
- **Resolved In**: Commit `948d740`

**Description**:
ERC objective function caused scipy RuntimeWarning by dividing by potentially small `target_rc`, leading to test failures.

**Fix Applied**:
Changed normalization from `(target_rc + 1e-10)` to stable `mean_rc` divisor.

**Verification**:
- ✅ All 24 portfolio tests passing (15 unit + 9 integration)
- ✅ No scipy RuntimeWarning
- ✅ ERC error <5% maintained

**References**:
- Code review report: `docs/P1_4_VALIDATION_GATES_AND_CODE_REVIEW.md:Issue #1`
- Git commit: `948d740`

---

## Issue Statistics

**Total Issues**: 7 (6 active + 1 resolved)

**By Priority**:
- 🔴 Critical: 0 active, 1 resolved
- 🟠 High: 1 active
- 🟡 Medium: 2 active
- 🟢 Low: 3 active

**By Milestone**:
- P2: 3 issues
- P3: 3 issues
- Resolved: 1 issue

**By Type**:
- Performance: 1
- API Completeness: 2
- Code Quality: 1
- Enhancement: 2
- Bug Fix: 1 (resolved)

---

## Workflow

### Adding New Issues
1. Use next available issue number
2. Set priority, status, type, location
3. Add clear description and recommended fix
4. Set estimate and acceptance criteria
5. Update statistics section

### Updating Issues
1. Update status when work begins (🚧 In Progress)
2. Move to Resolved section when fixed
3. Add commit reference and verification
4. Update statistics

### Closing Issues
1. Verify all acceptance criteria met
2. Add test results and commit reference
3. Move from Active to Resolved section
4. Update statistics

---

**Maintained by**: LLM Strategy Generator Team
**Review Cycle**: After each phase completion (P1.4, P2, P3)
**Next Review**: P2 Validation Layer Completion
