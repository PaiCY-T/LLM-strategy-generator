# LLM策略進化系統：統一改善路線圖
## Three-Expert Synthesis & Solo-Developer Action Plan

**Document Version**: 1.0
**Date**: 2025-11-14
**Status**: Final Synthesis
**Experts Consulted**:
- Senior Quant Expert (Gemini 2.5 Pro - Academic rigor)
- Senior Engineer (Gemini 2.5 Pro - Pragmatic solo-dev)
- Critical Analyst (GPT-5 - Adaptive methods)

---

## Executive Summary

### Consensus Points (All 3 Experts Agree)
1. **P0 Critical**: Fix Phase 7 regression immediately (4-8 hours)
2. **Sample Size**: Current 80 iterations insufficient (10-15% Type II error)
3. **UpdateRate Metric**: Flawed metric, should be replaced
4. **Regime Detection**: Simple volatility-only insufficient for Taiwan market
5. **Paper Trading**: Current mindset wrong - not for statistics, for operations validation

### Key Disagreements & Resolution

| Topic | Expert 1 (Quant) | Expert 2 (Engineer) | Expert 3 (Analyst) | **SYNTHESIS** |
|-------|------------------|---------------------|--------------------|-----------------|
| **Search Method** | Bayesian (TPE/BO), 2-stage | Grid (simple, parallel) | Adaptive (ASHA+TPE/BO) | **ASHA+TPE/BO** (2-4x speedup) |
| **Sample Size** | 200 iterations (3x) | Two-stage (80→40) | Multi-fidelity (adaptive) | **Multi-fidelity with ASHA** |
| **Portfolio Timing** | P1 (immediate) | Early MVP, defer optimization | Minimal skeleton early | **Minimal skeleton (Week 2)** |
| **Multi-objective** | Pareto Front | Weighted score + ImprovementMagnitude | Scalarization + ε-constraint | **Scalarization + ε-constraint** |
| **Regime Detection** | 2-state (vol only) | 2x2 (trend × vol) | 2x2 deterministic | **2x2 (trend × vol)** |
| **Paper Trading** | 3 months statistical | 1-2 months pragmatic | 4-8 weeks plumbing only | **6 weeks (plumbing focus)** |
| **Compute Budget** | 12 days (3x sample) | 7-9 days (two-stage) | 5-7 days (ASHA) | **5-7 days (adaptive)** |

---

## PART 1: Priority Framework (Corrected)

### P0 (Immediate - Week 0-1)
**Critical path items blocking all progress**

#### 1.1 Phase 7 Regression Fix ⏱️ 4-8 hours
**Problem**: 100% error rate, StrategyMetrics dataclass lacks dict interface

**Root Cause**:
```python
# Before (worked)
metrics: Dict[str, float] = {...}
value = metrics["sharpe_ratio"]

# After (broken)
metrics: StrategyMetrics = StrategyMetrics(sharpe_ratio=2.5, ...)
value = metrics["sharpe_ratio"]  # ❌ TypeError
```

**Solution** (Add dict compatibility layer):
```python
@dataclass
class StrategyMetrics:
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    # ... other metrics

    def __getitem__(self, key: str) -> float:
        """Enable dict-style access: metrics['sharpe_ratio']"""
        return getattr(self, key)

    def get(self, key: str, default=None) -> Any:
        """Enable .get() method: metrics.get('sharpe_ratio', 0.0)"""
        return getattr(self, key, default)

    def keys(self) -> list:
        """Enable .keys() iteration"""
        return [f.name for f in fields(self)]

    def values(self) -> list:
        """Enable .values() iteration"""
        return [getattr(self, f.name) for f in fields(self)]

    def items(self) -> list:
        """Enable .items() iteration"""
        return [(f.name, getattr(self, f.name)) for f in fields(self)]
```

**Affected Files** (4-5 locations):
- `src/learning/iteration_executor.py`: Fitness calculation
- `src/learning/champion_tracker.py`: Performance comparison
- `src/backtest/metrics.py`: Metric aggregation
- `tests/integration/test_e2e_validation.py`: Validation checks

**Validation**:
```bash
# Run E2E tests
pytest tests/integration/test_e2e_validation.py -v

# Expected: 0% error rate (down from 100%)
```

**Deliverable**: E2E validation GREEN, Phase 7 unblocked

---

#### 1.2 Adaptive Hyperparameter Search (ASHA + TPE/BO) ⏱️ 12-16 hours
**Why**: 2-4x speedup vs fixed grid, 5-7 days compute vs 12 days

**Expert Consensus**:
- ❌ Fixed grid search: 200 iterations × 12 days = computationally prohibitive
- ❌ Manual two-stage: Requires expert judgment, not reproducible
- ✅ Adaptive search: Automated early stopping + Bayesian optimization

**Implementation** (Optuna + ASHA):
```python
import optuna
from optuna.pruners import HyperbandPruner
from optuna.samplers import TPESampler

def optimize_innovation_rate(trial):
    """Multi-fidelity optimization with early stopping."""

    # Hyperparameter space
    innovation_rate = trial.suggest_float('innovation_rate', 0.05, 0.40, step=0.05)
    regime = trial.suggest_categorical('regime', ['bull_low', 'bull_high', 'bear_low', 'bear_high'])

    # Multi-fidelity: Start with 20 iterations, extend if promising
    n_iterations_base = 20
    n_iterations_max = 200

    # Run partial backtest
    metrics = run_backtest(
        innovation_rate=innovation_rate,
        regime=regime,
        n_iterations=n_iterations_base
    )

    # Report intermediate result (ASHA decides whether to continue)
    trial.report(metrics['sharpe_ratio'], step=n_iterations_base)

    # ASHA pruning: Stop unpromising trials early
    if trial.should_prune():
        raise optuna.TrialPruned()

    # If promising, extend to full 200 iterations
    metrics_full = run_backtest(
        innovation_rate=innovation_rate,
        regime=regime,
        n_iterations=n_iterations_max
    )

    # Multi-objective: Scalarization with epsilon-constraint
    sharpe = metrics_full['sharpe_ratio']
    diversity = metrics_full['diversity_score']

    # Epsilon-constraint: Require diversity ≥ 30%
    if diversity < 0.30:
        return -999.0  # Heavily penalize

    # Objective: Maximize Sharpe × (1 - avg_correlation)^0.5
    avg_corr = 1 - diversity  # Approximate
    score = sharpe * (avg_corr ** 0.5)

    return score

# Study configuration
study = optuna.create_study(
    direction='maximize',
    sampler=TPESampler(seed=42, multivariate=True),
    pruner=HyperbandPruner(
        min_resource=20,      # Minimum iterations before pruning
        max_resource=200,     # Maximum iterations for promising trials
        reduction_factor=3    # Aggressiveness of pruning
    )
)

# Run optimization (auto-determines # trials)
study.optimize(
    optimize_innovation_rate,
    n_trials=100,           # Upper bound
    timeout=7*24*3600,      # 7 days max
    n_jobs=4                # Parallel backtests
)

# Results
best_params = study.best_params
print(f"Optimal innovation_rate: {best_params['innovation_rate']}")
print(f"Optimal regime: {best_params['regime']}")
print(f"Best score: {study.best_value}")
```

**Performance Gains**:
- Fixed grid (200 iter): 12 days, 100% trials complete
- ASHA + TPE/BO: 5-7 days, ~40% trials complete (60% pruned early)
- **Speedup**: 2-4x, same statistical power

**Validation**:
```python
# Compare ASHA vs Grid on synthetic test
from optuna.study import create_study
from sklearn.metrics import mean_squared_error

# Ground truth: Known optimal innovation_rate = 0.20
true_optimum = 0.20

# Run both methods
asha_result = optimize_with_asha()
grid_result = optimize_with_grid()

# Compare convergence
print(f"ASHA: {asha_result} (error: {abs(asha_result - true_optimum)})")
print(f"Grid: {grid_result} (error: {abs(grid_result - true_optimum)})")
# Expected: ASHA converges faster with similar accuracy
```

**Deliverable**: Optuna-based hyperparameter search replacing fixed grid

---

### P1 (Foundational - Week 2-4)
**Essential capabilities for Stage 2 breakthrough**

#### 2.1 Minimal Portfolio Framework ⏱️ 16-24 hours
**Why**: Optimize strategies in portfolio context, not isolation

**Expert Synthesis**:
- Expert 1: Move to P1, full portfolio optimization immediately
- Expert 2: Build MVP early, use portfolio Sharpe as fitness
- Expert 3: Minimal skeleton, defer full optimization
- **Decision**: Minimal skeleton (Week 2), portfolio fitness (Week 3), full optimization (P2)

**MVP Implementation**:
```python
class MinimalPortfolioManager:
    """Lightweight portfolio evaluation for hyperparameter search."""

    def __init__(self, max_strategies: int = 5, max_weight: float = 0.30):
        self.max_strategies = max_strategies
        self.max_weight = max_weight

    def evaluate_portfolio_fitness(self, strategies: List[Strategy]) -> float:
        """
        Portfolio-aware fitness (used in ASHA optimization).

        Constraints:
        - max_weight ≤ 30% (prevent concentration)
        - pairwise_correlation < 0.7 (ensure diversity)
        - min_strategies ≥ 3 (sufficient diversification)
        """
        if len(strategies) < 3:
            return -999.0  # Insufficient diversification

        # Equal Risk Contribution (ERC) weights
        weights = self._calculate_erc_weights(strategies)

        # Check concentration constraint
        if max(weights) > self.max_weight:
            return -999.0

        # Check correlation constraint
        corr_matrix = self._calculate_correlation_matrix(strategies)
        if np.max(np.triu(corr_matrix, k=1)) > 0.7:
            return -999.0  # Too correlated

        # Portfolio Sharpe (weighted)
        portfolio_sharpe = self._calculate_portfolio_sharpe(strategies, weights)

        return portfolio_sharpe

    def _calculate_erc_weights(self, strategies: List[Strategy]) -> np.ndarray:
        """Equal Risk Contribution weighting."""
        # Simplified: Inverse volatility weighting
        vols = np.array([s.metrics.volatility for s in strategies])
        inv_vols = 1 / vols
        weights = inv_vols / inv_vols.sum()
        return weights

    def _calculate_portfolio_sharpe(self, strategies: List[Strategy], weights: np.ndarray) -> float:
        """Weighted portfolio Sharpe ratio."""
        returns = np.column_stack([s.returns for s in strategies])
        portfolio_returns = returns @ weights
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252)
        return sharpe
```

**Integration with ASHA**:
```python
def optimize_innovation_rate_with_portfolio(trial):
    """Modified ASHA objective with portfolio context."""

    innovation_rate = trial.suggest_float('innovation_rate', 0.05, 0.40, step=0.05)

    # Generate strategies with innovation_rate
    strategies = learning_loop.run(
        innovation_rate=innovation_rate,
        n_iterations=20  # Start with 20
    )

    # Portfolio fitness (not individual Sharpe)
    portfolio_mgr = MinimalPortfolioManager()
    fitness = portfolio_mgr.evaluate_portfolio_fitness(strategies)

    trial.report(fitness, step=20)
    if trial.should_prune():
        raise optuna.TrialPruned()

    # Extend to 200 iterations if promising
    strategies_full = learning_loop.run(
        innovation_rate=innovation_rate,
        n_iterations=200
    )
    fitness_full = portfolio_mgr.evaluate_portfolio_fitness(strategies_full)

    return fitness_full
```

**Defer to P2**:
- Full portfolio optimization (dynamic rebalancing, transaction costs)
- Multi-period optimization
- Risk parity refinements

**Deliverable**: Portfolio-aware fitness function integrated into ASHA

---

#### 2.2 2x2 Market Regime Detection ⏱️ 8-12 hours
**Why**: Taiwan market (70% retail) has momentum/reversal effects beyond volatility

**Expert Consensus**:
- ❌ Volatility-only (2-state): Too coarse, misses directional effects
- ✅ 2x2 (trend × vol): Captures bull/bear × high/low vol regimes
- ❌ HMM (3-state): Fragile, unstable, overkill for solo dev

**Implementation**:
```python
class RegimeDetector2x2:
    """Deterministic 2x2 regime: Trend × Volatility."""

    def __init__(self, ma_window: int = 200, vol_window: int = 60):
        self.ma_window = ma_window      # Trend: 200-day MA
        self.vol_window = vol_window    # Volatility: 60-day rolling std

    def detect_regime(self, prices: pd.Series) -> str:
        """
        Returns one of 4 regimes:
        - 'bull_low': Stable uptrend (best for momentum)
        - 'bull_high': Greedy/breakout market
        - 'bear_low': Stable downtrend (best for mean-reversion)
        - 'bear_high': Panic/crash market (risk-off)
        """
        # Trend axis: Price vs 200-day MA
        ma_200 = prices.rolling(self.ma_window).mean()
        is_bull = prices.iloc[-1] > ma_200.iloc[-1]

        # Volatility axis: 60-day rolling std vs historical median
        returns = prices.pct_change()
        vol_60 = returns.rolling(self.vol_window).std()
        vol_median = vol_60.median()
        is_high_vol = vol_60.iloc[-1] > vol_median

        # 2x2 regime
        if is_bull and not is_high_vol:
            return 'bull_low'
        elif is_bull and is_high_vol:
            return 'bull_high'
        elif not is_bull and not is_high_vol:
            return 'bear_low'
        else:
            return 'bear_high'

    def get_regime_statistics(self, prices: pd.Series) -> pd.DataFrame:
        """Analyze regime distribution over backtest period."""
        regimes = []
        for i in range(self.ma_window, len(prices)):
            regime = self.detect_regime(prices.iloc[:i])
            regimes.append({
                'date': prices.index[i],
                'regime': regime,
                'price': prices.iloc[i]
            })

        df = pd.DataFrame(regimes)

        # Regime distribution
        dist = df['regime'].value_counts(normalize=True)
        print("Regime Distribution:")
        print(dist)

        return df
```

**Integration with Learning Loop**:
```python
# Regime-conditioned hyperparameter search
def optimize_by_regime():
    """Optimize innovation_rate separately for each regime."""

    detector = RegimeDetector2x2()

    # Split data by regime
    regime_data = {
        'bull_low': [],
        'bull_high': [],
        'bear_low': [],
        'bear_high': []
    }

    for date, price in prices.items():
        regime = detector.detect_regime(prices.loc[:date])
        regime_data[regime].append((date, price))

    # Optimize for each regime
    results = {}
    for regime, data in regime_data.items():
        print(f"\nOptimizing for regime: {regime}")
        study = optuna.create_study(direction='maximize')
        study.optimize(
            lambda trial: optimize_innovation_rate_with_portfolio(trial, regime=regime),
            n_trials=50
        )
        results[regime] = study.best_params

    return results

# Expected output:
# bull_low: innovation_rate=0.15 (lower, momentum works)
# bull_high: innovation_rate=0.25 (higher, need adaptation)
# bear_low: innovation_rate=0.10 (lower, mean-reversion stable)
# bear_high: innovation_rate=0.30 (higher, need defensive)
```

**Validation**:
```python
# Backtest regime-aware vs regime-agnostic
results_aware = backtest_with_regime_awareness()
results_agnostic = backtest_without_regime()

print(f"Regime-aware Sharpe: {results_aware['sharpe']}")
print(f"Regime-agnostic Sharpe: {results_agnostic['sharpe']}")
# Expected: 10-20% improvement in Sharpe
```

**Deliverable**: 2x2 regime detector integrated into hyperparameter search

---

#### 2.3 Epsilon-Constraint Multi-Objective ⏱️ 8-12 hours
**Why**: Balance Sharpe and Diversity without Pareto Front overhead

**Expert Synthesis**:
- Expert 1: Use Pareto Front (multi-objective optimization)
- Expert 2: Weighted score with ImprovementMagnitude
- Expert 3: Scalarization with epsilon-constraint (pragmatic)
- **Decision**: Epsilon-constraint (hard constraint on diversity, optimize Sharpe)

**Implementation**:
```python
def calculate_fitness_with_epsilon(metrics: StrategyMetrics, min_diversity: float = 0.30) -> float:
    """
    Epsilon-constraint approach:
    - Hard constraint: diversity ≥ 30%
    - Objective: Maximize Sharpe × (1 - avg_correlation)^0.5
    """
    sharpe = metrics.sharpe_ratio
    diversity = metrics.diversity_score

    # Epsilon-constraint: Hard threshold
    if diversity < min_diversity:
        return -999.0  # Infeasible solution

    # Scalarization: Sharpe weighted by diversity
    avg_corr = 1 - diversity
    fitness = sharpe * (avg_corr ** 0.5)

    return fitness

def calculate_diversity_score(strategies: List[Strategy]) -> float:
    """
    Diversity = 1 - avg(pairwise_correlation).

    Range: [0, 1]
    - 0: All strategies perfectly correlated
    - 1: All strategies uncorrelated
    """
    if len(strategies) < 2:
        return 0.0

    # Calculate pairwise correlations
    returns_matrix = np.column_stack([s.returns for s in strategies])
    corr_matrix = np.corrcoef(returns_matrix.T)

    # Extract upper triangle (excluding diagonal)
    upper_tri = np.triu(corr_matrix, k=1)
    avg_corr = upper_tri[upper_tri != 0].mean()

    diversity = 1 - avg_corr
    return diversity
```

**Comparison with Alternatives**:
```python
# Alternative 1: Pareto Front (Expert 1)
# Pros: Theoretically optimal, no arbitrary weights
# Cons: Returns set of solutions (which one to choose?), 3-5x slower
# Verdict: Overkill for solo trader

# Alternative 2: Weighted Score (Expert 2)
# Score = Sharpe × Diversity^0.5 × ImprovementMagnitude^0.3
# Pros: Simple, interpretable
# Cons: Arbitrary exponents, no guarantee on minimum diversity
# Verdict: Good, but epsilon-constraint more explicit

# Selected: Epsilon-Constraint (Expert 3)
# fitness = Sharpe × (1 - avg_corr)^0.5, subject to diversity ≥ 30%
# Pros: Explicit minimum diversity, single objective
# Cons: Requires tuning epsilon threshold
# Verdict: Best balance for solo developer
```

**Deliverable**: Epsilon-constraint fitness function with 30% diversity floor

---

### P2 (Scaling - Week 5-8)
**Stage 2 breakthrough enablers**

#### 3.1 Full Portfolio Optimization ⏱️ 24-32 hours
**Why**: Move beyond equal-weight to risk parity

**Components**:
1. **Equal Risk Contribution (ERC)** with optimization
2. **Dynamic rebalancing** (monthly)
3. **Transaction cost modeling** (0.3% per trade)
4. **Turnover constraints** (max 50% monthly)

**Implementation**:
```python
from scipy.optimize import minimize

class FullPortfolioManager:
    """Complete portfolio optimization with ERC and constraints."""

    def optimize_weights(self, strategies: List[Strategy]) -> np.ndarray:
        """
        Minimize: Sum of squared deviations from equal risk contribution
        Subject to:
        - sum(weights) = 1
        - 0 ≤ weight_i ≤ 0.30
        - pairwise_correlation < 0.7
        """
        n = len(strategies)

        # Covariance matrix
        returns = np.column_stack([s.returns for s in strategies])
        cov_matrix = np.cov(returns.T)

        # Objective: Minimize sum((RC_i - RC_mean)^2)
        def objective(weights):
            portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
            risk_contributions = weights * (cov_matrix @ weights) / portfolio_vol
            rc_mean = risk_contributions.mean()
            return np.sum((risk_contributions - rc_mean) ** 2)

        # Constraints
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1},  # Sum to 1
        ]

        bounds = [(0, 0.30) for _ in range(n)]  # Max 30% per strategy

        # Initial guess: Equal weight
        w0 = np.ones(n) / n

        # Optimize
        result = minimize(
            objective,
            w0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        return result.x

    def backtest_with_rebalancing(self, strategies: List[Strategy], rebalance_freq: str = 'M') -> pd.DataFrame:
        """
        Dynamic rebalancing with transaction costs.

        Args:
            rebalance_freq: 'D' (daily), 'W' (weekly), 'M' (monthly)
        """
        # Monthly rebalancing
        returns = pd.concat([s.returns for s in strategies], axis=1)

        # Initialize
        weights = self.optimize_weights(strategies)
        portfolio_value = 100000  # $100K initial
        transaction_cost_rate = 0.003  # 0.3% per trade

        results = []
        for date in returns.resample(rebalance_freq).last().index:
            # Current portfolio value
            current_returns = returns.loc[:date].iloc[-1]
            current_value = portfolio_value * (1 + weights @ current_returns)

            # Rebalance
            new_weights = self.optimize_weights(strategies)
            turnover = np.abs(new_weights - weights).sum()
            transaction_costs = current_value * turnover * transaction_cost_rate

            # Update
            portfolio_value = current_value - transaction_costs
            weights = new_weights

            results.append({
                'date': date,
                'value': portfolio_value,
                'turnover': turnover,
                'costs': transaction_costs
            })

        return pd.DataFrame(results)
```

**Validation**:
```python
# Compare equal-weight vs ERC
equal_weight_sharpe = backtest_equal_weight()
erc_sharpe = backtest_erc_optimized()

print(f"Equal-weight Sharpe: {equal_weight_sharpe}")
print(f"ERC Sharpe: {erc_sharpe}")
# Expected: 5-15% improvement
```

**Deliverable**: Full portfolio optimization with risk parity

---

#### 3.2 Purged Walk-Forward Cross-Validation ⏱️ 16-24 hours
**Why**: Prevent overfitting, reduce data leakage

**Implementation**:
```python
from sklearn.model_selection import TimeSeriesSplit

class PurgedWalkForwardCV:
    """Combinatorially purged cross-validation for time series."""

    def __init__(self, n_splits: int = 5, purge_gap: int = 21):
        self.n_splits = n_splits
        self.purge_gap = purge_gap  # 21 trading days (~1 month)

    def split(self, X: pd.DataFrame):
        """
        Generate train/test splits with purging.

        Purging: Remove `purge_gap` days between train and test
        to prevent information leakage from overlapping bars.
        """
        tscv = TimeSeriesSplit(n_splits=self.n_splits)

        for train_idx, test_idx in tscv.split(X):
            # Purge: Remove last `purge_gap` days from train
            train_end = train_idx[-1] - self.purge_gap
            train_idx_purged = train_idx[train_idx <= train_end]

            yield train_idx_purged, test_idx

    def backtest_with_cv(self, learning_loop, X: pd.DataFrame) -> List[float]:
        """Run walk-forward validation."""

        cv_sharpes = []

        for train_idx, test_idx in self.split(X):
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]

            # Train on fold
            strategies = learning_loop.run(data=X_train, n_iterations=200)

            # Test on fold
            test_sharpe = evaluate_on_test(strategies, X_test)
            cv_sharpes.append(test_sharpe)

        return cv_sharpes
```

**Validation**:
```python
# Compare standard CV vs purged CV
cv_std = cross_validate_standard()
cv_purged = cross_validate_purged()

print(f"Standard CV Sharpe: {np.mean(cv_std)} ± {np.std(cv_std)}")
print(f"Purged CV Sharpe: {np.mean(cv_purged)} ± {np.std(cv_purged)}")
# Expected: Purged CV ~10-20% lower (more realistic)
```

**Deliverable**: Purged walk-forward CV integrated into validation

---

### P3 (Polish - Week 9-12)
**Production readiness**

#### 4.1 Paper Trading (6 weeks) ⏱️ Continuous
**Purpose**: Validate implementation, not statistics

**Expert Consensus**:
- Paper trading is for **plumbing validation**, not statistical validation
- 6 weeks (compromise between 1-2 months and 3 months)
- Focus: Order execution, slippage, API reliability

**Checklist**:
- [ ] Order execution latency < 100ms
- [ ] Slippage < 0.1% (TWII market)
- [ ] Position reconciliation 100% accurate
- [ ] API error handling robust (retry logic, failover)
- [ ] Real-time P&L tracking accurate

**Not Goals**:
- ❌ Statistical validation (use walk-forward CV instead)
- ❌ Strategy tuning (already done in P1-P2)

**Deliverable**: 6-week paper trading with operations validation

---

#### 4.2 Monitoring & Alerting ⏱️ 12-16 hours
**Why**: Detect regime shifts, performance degradation

**Implementation**:
```python
class PerformanceMonitor:
    """Real-time performance monitoring with alerts."""

    def __init__(self, baseline_sharpe: float = 2.0, alert_threshold: float = 0.5):
        self.baseline_sharpe = baseline_sharpe
        self.alert_threshold = alert_threshold

    def check_performance_degradation(self, current_sharpe: float) -> bool:
        """Alert if Sharpe drops > 50% from baseline."""
        if current_sharpe < self.baseline_sharpe * (1 - self.alert_threshold):
            self.send_alert(f"Performance degradation: {current_sharpe} < {self.baseline_sharpe}")
            return True
        return False

    def check_regime_shift(self, detector: RegimeDetector2x2) -> bool:
        """Alert if regime changes."""
        current_regime = detector.detect_regime(prices)
        if current_regime != self.last_regime:
            self.send_alert(f"Regime shift: {self.last_regime} → {current_regime}")
            self.last_regime = current_regime
            return True
        return False

    def send_alert(self, message: str):
        """Send email/SMS alert."""
        # Implementation: SMTP, Twilio, etc.
        print(f"ALERT: {message}")
```

**Deliverable**: Monitoring dashboard with email alerts

---

## PART 2: Implementation Timeline

### Week-by-Week Plan (12 weeks to Stage 2)

#### Week 0-1: Critical Path (P0)
- **Day 1-2**: Fix Phase 7 regression (dict compatibility)
- **Day 3-7**: Implement Optuna + ASHA hyperparameter search
- **Validation**: E2E tests GREEN, ASHA converges 2x faster than grid

#### Week 2: Foundation (P1 - Part 1)
- **Day 8-10**: Implement 2x2 regime detection (trend × vol)
- **Day 11-14**: Build minimal portfolio framework (ERC weights)
- **Validation**: Regime-aware search shows 10-20% Sharpe improvement

#### Week 3-4: Multi-Objective (P1 - Part 2)
- **Day 15-17**: Implement epsilon-constraint fitness (diversity ≥ 30%)
- **Day 18-28**: Run comprehensive hyperparameter search (5-7 days compute)
- **Validation**: Achieve Stage 2 targets (80% success, 2.5+ Sharpe, 40%+ diversity)

#### Week 5-6: Portfolio Optimization (P2)
- **Day 29-42**: Full ERC portfolio optimization with rebalancing
- **Validation**: ERC outperforms equal-weight by 5-15%

#### Week 7-8: Statistical Rigor (P2)
- **Day 43-56**: Implement purged walk-forward CV
- **Validation**: Out-of-sample Sharpe within 20% of in-sample

#### Week 9-14: Paper Trading (P3)
- **Day 57-99**: 6 weeks paper trading (operations validation)
- **Validation**: Execution latency < 100ms, slippage < 0.1%

#### Week 15-16: Production (P3)
- **Day 100-112**: Monitoring, alerting, final polish
- **Go-Live**: Deploy to live trading

---

## PART 3: Technical Debt & Risks

### Known Risks

#### 1. ASHA Pruning Too Aggressive
**Risk**: Prune promising trials too early (false negatives)
**Mitigation**:
- Start with conservative `reduction_factor=3` (vs aggressive 5)
- Use `min_resource=20` (sufficient for initial signal)
- Monitor pruned trials: If >80% pruned, relax pruning

#### 2. Epsilon Threshold Too Strict
**Risk**: 30% diversity floor infeasible (all trials infeasible)
**Mitigation**:
- Start with 25% threshold, increase gradually
- Monitor feasible ratio: If <50%, lower threshold
- Use adaptive epsilon based on empirical distribution

#### 3. Regime Detection Instability
**Risk**: Regime switches too frequently (overfitting)
**Mitigation**:
- Add hysteresis: Require 5-day confirmation before regime switch
- Use exponential smoothing on MA and volatility
- Backtest regime stability: Aim for 10-20 regime switches/year (not 100+)

#### 4. Portfolio Optimization Overfitting
**Risk**: ERC weights overfit to in-sample data
**Mitigation**:
- Use rolling window optimization (6-month window)
- Regularize: Add penalty for extreme weights
- Out-of-sample validation: Test on held-out period

---

## PART 4: Success Metrics

### Stage 2 Targets (Revised)

| Metric | Stage 1 (Current) | Stage 2 (Target) | Stretch Goal |
|--------|-------------------|------------------|--------------|
| **Success Rate** | 70% | 80% | 85% |
| **Best Sharpe** | 2.48 | 2.5+ | 3.0+ |
| **Avg Sharpe** | 1.15 | 1.5+ | 2.0+ |
| **Diversity** | 10.4% (collapsed) | 40%+ | 50%+ |
| **Max Drawdown** | Unknown | <20% | <15% |
| **Portfolio Sharpe** | N/A (no portfolio) | 2.0+ | 2.5+ |
| **Compute Time** | 12 days (projected) | 5-7 days | 3-5 days |

### Validation Gates

**Gate 1 (Week 1)**: Phase 7 regression fixed, E2E tests GREEN
**Gate 2 (Week 2)**: Regime-aware search outperforms regime-agnostic by 10%+
**Gate 3 (Week 4)**: Achieve 80% success rate, 40%+ diversity, 2.5+ Sharpe
**Gate 4 (Week 6)**: ERC portfolio outperforms equal-weight by 5%+
**Gate 5 (Week 8)**: Out-of-sample Sharpe within 20% of in-sample
**Gate 6 (Week 14)**: Paper trading validation passes (latency, slippage, accuracy)

---

## PART 5: Solo Developer Pragmatism

### Time Management

**Full-Time (40h/week)**:
- P0 (Week 0-1): 40 hours
- P1 (Week 2-4): 120 hours
- P2 (Week 5-8): 160 hours
- P3 (Week 9-16): 320 hours
- **Total**: 640 hours (~4 months)

**Part-Time (20h/week)**:
- **Total**: 8 months

### Simplification Trade-offs

**What We Simplified** (vs Expert 1 academic approach):
- ✅ ASHA + TPE/BO instead of full Bayesian (2-4x speedup)
- ✅ Epsilon-constraint instead of Pareto Front (1/3 complexity)
- ✅ 2x2 deterministic regime instead of HMM (no fragility)
- ✅ Minimal portfolio MVP instead of full optimization (defer to P2)
- ✅ 6 weeks paper trading instead of 3 months (focus on plumbing)

**What We Kept** (non-negotiable):
- ✅ Multi-fidelity search (ASHA) for statistical rigor
- ✅ Portfolio-aware fitness (not single-strategy optimization)
- ✅ Regime-conditioned search (Taiwan market characteristics)
- ✅ Purged walk-forward CV (prevent overfitting)
- ✅ 30% diversity floor (prevent correlation collapse)

---

## PART 6: References & Further Reading

### Optimization Methods
1. **ASHA**: Li et al. (2020) "A System for Massively Parallel Hyperparameter Tuning"
2. **TPE**: Bergstra et al. (2011) "Algorithms for Hyper-Parameter Optimization"
3. **Optuna**: Akiba et al. (2019) "Optuna: A Next-generation Hyperparameter Optimization Framework"

### Portfolio Theory
4. **ERC**: Maillard et al. (2010) "The Properties of Equally Weighted Risk Contribution Portfolios"
5. **Risk Parity**: Qian (2005) "Risk Parity Portfolios"

### Validation
6. **Purged CV**: López de Prado (2018) "Advances in Financial Machine Learning" (Chapter 7)
7. **Deflated Sharpe**: Harvey & Liu (2015) "Backtesting"

### Regime Detection
8. **HMM for Finance**: Hamilton (1989) "A New Approach to the Economic Analysis of Nonstationary Time Series"
9. **Trend-Following**: Hurst et al. (2017) "A Century of Evidence on Trend-Following Investing"

---

## PART 7: Decision Log

### Critical Decisions Made

**Decision 1: ASHA + TPE/BO over Fixed Grid**
- **Rationale**: 2-4x speedup, same statistical power, automated early stopping
- **Trade-off**: Slightly more complex implementation vs 7-day time savings
- **Confidence**: HIGH (all 3 experts agreed fixed grid insufficient)

**Decision 2: Epsilon-Constraint over Pareto Front**
- **Rationale**: Explicit minimum diversity, single objective, 1/3 complexity
- **Trade-off**: Less theoretically optimal vs practical solo-developer efficiency
- **Confidence**: MEDIUM-HIGH (2/3 experts favored pragmatic approach)

**Decision 3: 2x2 Regime over HMM**
- **Rationale**: Deterministic, stable, captures directional effects
- **Trade-off**: Less adaptive vs no fragility, easier to debug
- **Confidence**: HIGH (2/3 experts agreed, HMM too fragile)

**Decision 4: Minimal Portfolio MVP (Week 2) over Full Optimization (P1)**
- **Rationale**: Get portfolio fitness early, defer full optimization
- **Trade-off**: Slightly suboptimal early results vs reduced upfront complexity
- **Confidence**: MEDIUM (synthesized 3 conflicting expert opinions)

**Decision 5: 6 Weeks Paper Trading**
- **Rationale**: Compromise between 1-2 months (too short) and 3 months (overkill)
- **Trade-off**: May miss some edge cases vs faster to production
- **Confidence**: MEDIUM (all experts agreed on plumbing focus, differed on duration)

---

## Appendix A: Code Integration Checklist

### Phase 7 Regression Fix
- [ ] Add `__getitem__()` to StrategyMetrics
- [ ] Add `get()` method
- [ ] Add `keys()`, `values()`, `items()` methods
- [ ] Update 4-5 affected locations
- [ ] Run E2E tests (target: 0% error rate)

### ASHA + TPE/BO Implementation
- [ ] Install Optuna: `pip install optuna`
- [ ] Implement `optimize_innovation_rate()` function
- [ ] Configure HyperbandPruner (reduction_factor=3)
- [ ] Configure TPESampler (multivariate=True)
- [ ] Add intermediate reporting (trial.report())
- [ ] Add pruning logic (trial.should_prune())
- [ ] Set n_jobs for parallelism
- [ ] Validate convergence vs grid search

### 2x2 Regime Detection
- [ ] Implement RegimeDetector2x2 class
- [ ] Add trend detection (200-day MA)
- [ ] Add volatility detection (60-day rolling std)
- [ ] Integrate with hyperparameter search
- [ ] Validate regime distribution (bull_low, bull_high, bear_low, bear_high)

### Minimal Portfolio Framework
- [ ] Implement MinimalPortfolioManager class
- [ ] Add ERC weight calculation
- [ ] Add correlation constraint checking (< 0.7)
- [ ] Add concentration constraint (≤ 30%)
- [ ] Integrate portfolio_fitness into ASHA
- [ ] Validate vs single-strategy optimization

### Epsilon-Constraint Multi-Objective
- [ ] Implement calculate_fitness_with_epsilon()
- [ ] Set diversity threshold (30%)
- [ ] Implement diversity_score calculation (1 - avg_corr)
- [ ] Add scalarization (Sharpe × diversity^0.5)
- [ ] Validate feasible solution ratio (target: >50%)

---

## Appendix B: Expert Opinion Summary

### Expert 1 (Senior Quant - Gemini 2.5 Pro)
**Strengths**: Rigorous statistical approach, academic best practices
**Weaknesses**: Time-intensive (12 days compute), complex (Pareto Front)
**Best Contributions**:
- Identified 3x sample size need (80→200 iterations)
- Highlighted two-stage search benefit
- Emphasized portfolio-first sequencing

### Expert 2 (Senior Engineer - Gemini 2.5 Pro)
**Strengths**: Pragmatic solo-developer focus, simplicity advocacy
**Weaknesses**: May underestimate statistical rigor needs
**Best Contributions**:
- Challenged Pareto Front complexity (weighted score sufficient)
- Advocated 2x2 regime over volatility-only
- Shortened paper trading (1-2 months)

### Expert 3 (Critical Analyst - GPT-5)
**Strengths**: Balanced rigor + pragmatism, adaptive methods expertise
**Weaknesses**: Required clarifying questions (not all answered)
**Best Contributions**:
- ASHA + TPE/BO recommendation (2-4x speedup)
- Multi-fidelity sequential testing
- Scalarization + epsilon-constraint synthesis

### Synthesis Philosophy
**Consensus First**: Where all 3 experts agreed, adopt immediately
**Pragmatic Tiebreaker**: When 2/3 agree on simplicity, favor solo-developer efficiency
**Rigor Floor**: Never compromise on statistical validity (30% diversity, purged CV, ASHA)
**Time Boxed**: 12-week limit forces prioritization (P0→P1→P2→P3)

---

## READY FOR EXECUTION

This roadmap synthesizes:
- ✅ My original thinkdeep analysis (5-step framework)
- ✅ Senior Quant Expert corrections (statistical rigor)
- ✅ Senior Engineer pragmatism (solo-developer focus)
- ✅ Critical Analyst adaptations (ASHA, epsilon-constraint)

**Next Steps**:
1. Review this roadmap
2. Clarify any ambiguities (GPT-5's questions if needed)
3. Begin Week 0-1 implementation (P0 tasks)
4. Track progress against validation gates

**Est. Time to Stage 2**: 12-16 weeks (full-time) or 24-32 weeks (part-time)

---

*Generated: 2025-11-14*
*Version: 1.0 (Final Synthesis)*
