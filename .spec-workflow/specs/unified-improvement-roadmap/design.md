# Unified Improvement Roadmap - TDD Implementation - Design Document

## Overview

This design document outlines the technical architecture for implementing a comprehensive improvement roadmap using Test-Driven Development (TDD) methodology. The system enhances an LLM-based trading strategy evolution platform with four priority tiers (P0-P3) targeting performance, reliability, and intelligence improvements.

**Design Principles**:
- **TDD-First**: All implementations follow Red → Green → Refactor cycle
- **Incremental Value**: Each priority delivers measurable improvements
- **Production-Ready**: 99.9% uptime, <100ms latency, <0.1% error rate
- **Evidence-Based**: All optimizations validated with metrics and benchmarks

**Expected Outcomes**:
- P0 (8-12h): +0% performance, 100% reliability foundation
- P1 (24-32h): +10-20% performance through regime awareness
- P2 (48h): +5-15% through portfolio optimization, production deployment readiness
- P3 (40h): Documentation, monitoring, operational excellence

## Architecture

### System Layers

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ LLM Client │  │ Iteration  │  │ Champion   │            │
│  │            │  │ Executor   │  │ Tracker    │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Intelligence Layer (P0-P2)                    │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ ASHA       │  │ Regime     │  │ Portfolio  │            │
│  │ Optimizer  │  │ Detector   │  │ Optimizer  │            │
│  │ (P0.2)     │  │ (P1.1)     │  │ (P1.2-1.3) │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Validation Layer (P2)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Purged     │  │ E2E Test   │  │ Performance│            │
│  │ Walk-Fwd CV│  │ Framework  │  │ Benchmarks │            │
│  │ (P2.1)     │  │ (P2.2)     │  │ (P2.3)     │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                Foundation Layer (P0.1)                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Backtest   │  │ Strategy   │  │ Metrics    │            │
│  │ Executor   │  │ Metrics    │  │ Calculator │            │
│  │            │  │ (Dict Fix) │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Observability Layer (P3)                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐            │
│  │ Monitoring │  │ Logging    │  │ Tracing    │            │
│  │ Dashboard  │  │ Framework  │  │ System     │            │
│  │ (P3.2)     │  │            │  │            │            │
│  └────────────┘  └────────────┘  └────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### Component Interactions

**P0 Foundation Flow**:
```
IterationExecutor → BacktestExecutor → StrategyMetrics (dict interface)
                                     ↓
                              ASHAOptimizer → Optuna Study → Pruned Trials
```

**P1 Intelligence Flow**:
```
MarketData → RegimeDetector → Regime Classification (Trend × Volatility)
                             ↓
                      StrategySelector → Regime-Aware Strategy
                                       ↓
                                PortfolioOptimizer (ERC/Epsilon-Constraint)
```

**P2 Validation Flow**:
```
Strategy → PurgedWalkForwardCV → Train/Test Splits (21-day purge)
                                ↓
                         E2ETestFramework → Validation Gates
                                          ↓
                                   PerformanceBenchmarks
```

## Components and Interfaces

### P0.1: StrategyMetrics Dict Interface Fix

**Module**: `src/backtest/metrics.py`

**Purpose**: Fix Phase 7 regression by implementing complete dict interface compatibility

**Current State**:
- ✅ Implemented: `__getitem__`, `get()`, `__contains__`, `keys()`
- ❌ Missing: `values()`, `items()`, `__len__()`

**Interface Specification**:
```python
@dataclass
class StrategyMetrics:
    """Strategy performance metrics with full dict interface."""

    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success: bool = False

    # Existing methods (already implemented)
    def __getitem__(self, key: str) -> Any:
        """Dict-like bracket access with KeyError on missing keys."""

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get() with special None handling."""

    def __contains__(self, key: str) -> bool:
        """Dict-like 'in' operator."""

    def keys(self) -> KeysView:
        """Dict-like keys() iterator."""

    # New methods (to be implemented)
    def values(self) -> ValuesView:
        """Return iterator of metric values.

        Returns:
            ValuesView: Iterator of all metric values

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5, total_return=0.25)
            >>> list(metrics.values())
            [1.5, 0.25, None, None, False]
        """

    def items(self) -> ItemsView:
        """Return iterator of (key, value) tuples.

        Returns:
            ItemsView: Iterator of (field_name, value) tuples

        Examples:
            >>> metrics = StrategyMetrics(sharpe_ratio=1.5)
            >>> list(metrics.items())
            [('sharpe_ratio', 1.5), ('total_return', None), ...]
        """

    def __len__(self) -> int:
        """Return number of metric fields.

        Returns:
            int: Count of dataclass fields (always 5)

        Examples:
            >>> metrics = StrategyMetrics()
            >>> len(metrics)
            5
        """
```

**Edge Cases**:
- NaN values converted to None in `__post_init__`
- `get()` returns default when value is None (special behavior)
- `__getitem__` returns None directly (different from `get()`)
- `values()` and `items()` must respect None values

**Dependencies**: None (stdlib only)

**Test Coverage**: 10 unit tests (see TDD_IMPLEMENTATION_ROADMAP.md)

---

### P0.2: ASHA Hyperparameter Optimizer

**Module**: `src/learning/optimizer.py`

**Purpose**: Implement Asynchronous Successive Halving Algorithm for 50-70% faster hyperparameter search

**Architecture**:
```python
class ASHAOptimizer:
    """ASHA-based hyperparameter optimizer using Optuna backend."""

    # Configuration
    n_iterations: int = 100        # Maximum iterations per trial
    min_resource: int = 3          # Minimum backtest iterations before pruning
    reduction_factor: int = 3      # Successive halving reduction factor
    grace_period: int = 5          # Iterations before pruning starts

    # State
    study: Optional[optuna.Study] = None
    _search_stats: Dict[str, Any] = {}
```

**Interface Specification**:

1. **Initialization**:
```python
def __init__(
    self,
    n_iterations: int = 100,
    min_resource: int = 3,
    reduction_factor: int = 3,
    grace_period: int = 5
) -> None:
    """Initialize ASHA optimizer with Optuna backend.

    Args:
        n_iterations: Maximum iterations per trial
        min_resource: Minimum backtest iterations before pruning
        reduction_factor: Factor for successive halving (must be >= 2)
        grace_period: Number of iterations before pruning starts

    Raises:
        ValueError: If reduction_factor < 2 or min_resource < 1
    """
```

2. **Study Creation**:
```python
def create_study(self) -> optuna.Study:
    """Create Optuna study with ASHA pruner.

    Returns:
        optuna.Study: Configured study with SuccessiveHalvingPruner

    Implementation:
        - Direction: maximize (Sharpe ratio)
        - Pruner: SuccessiveHalvingPruner with min_resource, reduction_factor
        - min_early_stopping_rate: 0 (aggressive pruning)
    """
```

3. **Optimization Loop** (to be implemented):
```python
def optimize(
    self,
    objective_fn: Callable[[Dict[str, Any]], float],
    param_space: Dict[str, Any],
    n_trials: int = 50
) -> Dict[str, Any]:
    """Run ASHA optimization and return best parameters.

    Args:
        objective_fn: Function that takes parameters dict and returns score
        param_space: Parameter search space definition
            Format: {
                'param_name': ('type', min, max),
                # Types: 'uniform', 'int', 'categorical', 'log_uniform'
            }
        n_trials: Number of trials to run

    Returns:
        Dict[str, Any]: Best parameters found

    Raises:
        ValueError: If n_trials < 1

    Implementation Steps:
        1. Create study if not exists
        2. Define objective wrapper that:
           - Accepts Optuna trial object
           - Samples parameters from trial
           - Calls objective_fn with sampled parameters
           - Reports intermediate values via trial.report(value, step)
           - Checks trial.should_prune() at each step
        3. Run study.optimize() with n_trials
        4. Collect search statistics
        5. Return best_params

    Note: Optuna's SuccessiveHalvingPruner handles early stopping automatically
          based on intermediate values reported via trial.report()
    """
```

4. **Statistics Collection** (to be implemented):
```python
def get_search_stats(self) -> Dict[str, Any]:
    """Return optimization statistics.

    Returns:
        Dict containing:
            - n_trials: Total trials run
            - n_pruned: Number of pruned trials
            - pruning_rate: Percentage of trials pruned
            - best_value: Best score achieved
            - best_params: Best parameters found
            - search_time: Total search time in seconds

    Raises:
        RuntimeError: If optimize() has not been called yet
    """
```

**Dependencies**:
- `optuna>=3.0.0` (REQUIRED - must add to requirements.txt)
- `typing` (stdlib)

**Performance Targets**:
- 50-70% reduction in search time vs. grid search
- Pruning rate: 40-60% of trials
- Convergence: Within 50-100 trials for typical parameter spaces

**Test Coverage**: 18 unit tests (pruning callback removed, handled by Optuna)

---

### P1.1: Market Regime Detection

**Module**: `src/intelligence/regime_detector.py` (new)

**Purpose**: Classify market conditions using 2×2 matrix (Trend × Volatility) for regime-aware strategy selection

**Architecture**:
```python
class RegimeDetector:
    """Market regime classifier using trend and volatility analysis."""

    # Configuration
    trend_lookback: int = 60       # Days for trend calculation
    vol_lookback: int = 20         # Days for volatility calculation
    trend_threshold: float = 0.05  # Threshold for trend classification
    vol_threshold: float = 0.15    # Threshold for volatility classification
```

**Regime Matrix**:
```
                  Low Volatility    High Volatility
Uptrend          BULL_CALM         BULL_VOLATILE
Downtrend        BEAR_CALM         BEAR_VOLATILE
```

**Interface Specification**:
```python
class MarketRegime(Enum):
    """Market regime classification."""
    BULL_CALM = "bull_calm"           # Uptrend + Low Vol
    BULL_VOLATILE = "bull_volatile"   # Uptrend + High Vol
    BEAR_CALM = "bear_calm"           # Downtrend + Low Vol
    BEAR_VOLATILE = "bear_volatile"   # Downtrend + High Vol

class RegimeDetector:
    def detect_regime(self, prices: pd.Series) -> MarketRegime:
        """Detect current market regime from price series.

        Args:
            prices: Price time series

        Returns:
            MarketRegime: Current regime classification

        Implementation:
            1. Calculate trend using SMA crossover:
               - SMA_short = prices.rolling(50).mean()
               - SMA_long = prices.rolling(200).mean()
               - trend_signal = SMA_short[-1] / SMA_long[-1] - 1.0
               - Uptrend if trend_signal > trend_threshold (default 0.02)
            2. Calculate annualized volatility:
               - returns = prices.pct_change()
               - vol = returns[-vol_lookback:].std() * sqrt(252)
               - High Vol if vol > vol_threshold (default 0.20)
            3. Classify regime from 2×2 matrix:
               - BULL_CALM: Uptrend + Low Vol
               - BULL_VOLATILE: Uptrend + High Vol
               - BEAR_CALM: Downtrend + Low Vol
               - BEAR_VOLATILE: Downtrend + High Vol
        """

    def get_regime_stats(self, prices: pd.Series) -> RegimeStats:
        """Return regime statistics for analysis.

        Returns:
            RegimeStats: Data class containing:
                - trend: SMA(50)/SMA(200) - 1.0
                - volatility: Annualized volatility
                - regime: Current regime classification
                - confidence: Distance from threshold (0-1 scale)

        Implementation:
            confidence = min(
                abs(trend_signal - trend_threshold) / 0.05,
                abs(volatility - vol_threshold) / 0.10
            )
            Capped at 1.0 for strong signals far from threshold
        """
```

**Dependencies**:
- `pandas`, `numpy` (already in requirements.txt)

---

### P1.2: Portfolio Optimization with ERC

**Module**: `src/intelligence/portfolio_optimizer.py` (new)

**Purpose**: Implement Equal Risk Contribution (ERC) portfolio optimization for balanced risk allocation

**Architecture**:
```python
class PortfolioOptimizer:
    """Portfolio optimizer using ERC and Epsilon-Constraint methods."""

    # Configuration
    target_volatility: float = 0.15   # Annual target volatility
    min_weight: float = 0.0           # Minimum asset weight
    max_weight: float = 0.5           # Maximum asset weight
    rebalance_freq: str = "monthly"   # Rebalancing frequency
```

**Interface Specification**:
```python
def optimize_erc(
    self,
    returns: pd.DataFrame,
    covariance: pd.DataFrame
) -> PortfolioWeights:
    """Optimize portfolio using Equal Risk Contribution.

    Args:
        returns: Historical returns DataFrame (assets × time)
        covariance: Covariance matrix of asset returns

    Returns:
        PortfolioWeights: Data class containing:
            - weights: Dict[asset_name, weight]
            - risk_contributions: Dict[asset_name, contribution]
            - total_risk: Portfolio volatility
            - expected_return: Expected portfolio return

    Implementation:
        1. Initialize weights (equal-weighted: w_0 = 1/N for all assets)
        2. Define objective function:
           def objective(w):
               portfolio_vol = sqrt(w^T Σ w)
               risk_contrib = w * (Σw) / portfolio_vol
               target_contrib = portfolio_vol / N
               return sum((risk_contrib - target_contrib)^2)
        3. Define constraints:
           - Equality: sum(w) = 1.0
           - Bounds: min_weight <= w_i <= max_weight (default: 0.0 to 0.3)
        4. Solve using scipy.optimize.minimize:
           result = minimize(objective, w_0, method='SLSQP',
                           constraints=eq_constraint, bounds=weight_bounds)
        5. Calculate final metrics and return PortfolioWeights

    Numerical Solver: scipy.optimize.minimize with SLSQP method
    Convergence Tolerance: 1e-6 for constraint satisfaction
    """
```

**Dependencies**:
- `scipy>=1.7.0` # Constrained optimization (add to requirements.txt)
- `pandas`, `numpy` # Already in requirements.txt

---

### P1.3: Epsilon-Constraint Multi-Objective Optimization

**Module**: `src/intelligence/multi_objective.py` (new)

**Purpose**: Balance return vs. risk trade-offs using epsilon-constraint method

**Interface Specification**:
```python
class EpsilonConstraintOptimizer:
    """Multi-objective optimizer using epsilon-constraint method."""

    def optimize(
        self,
        asset_returns: pd.DataFrame,
        asset_covariance: pd.DataFrame,
        epsilon_values: List[float]
    ) -> List[PortfolioWeights]:
        """Solve multi-objective optimization using epsilon-constraint.

        Args:
            asset_returns: Historical returns DataFrame (assets × time)
            asset_covariance: Covariance matrix of asset returns
            epsilon_values: Risk constraint levels to explore (e.g., [0.10, 0.15, 0.20])

        Returns:
            List[PortfolioWeights]: Pareto-optimal portfolio solutions,
                                   one for each epsilon value

        Implementation:
            For each epsilon in epsilon_values:
                1. Define objective: maximize expected_return = w^T * mean_returns
                2. Define constraints:
                   - Equality: sum(w) = 1.0
                   - Risk limit: sqrt(w^T Σ w) <= epsilon
                   - Bounds: min_weight <= w_i <= max_weight
                   - Diversity: sum(w > 0.01) >= 0.3 * N (at least 30% of assets)
                3. Solve using scipy.optimize.minimize:
                   result = minimize(
                       lambda w: -w @ mean_returns,  # Negative for maximization
                       x0=w_0,
                       method='SLSQP',
                       constraints=[eq_constraint, risk_constraint, diversity_constraint],
                       bounds=weight_bounds
                   )
                4. Calculate risk contributions and metrics
                5. Create PortfolioWeights object
            Return list of all Pareto-optimal solutions

        Numerical Solver: scipy.optimize.minimize with SLSQP method
        Convergence Tolerance: 1e-6
        """
```

**Dependencies**:
- `scipy>=1.7.0` # Constrained optimization (add to requirements.txt)
- `pandas`, `numpy` # Already in requirements.txt

---

### P2.1: Purged Walk-Forward Cross-Validation

**Module**: `src/validation/purged_cv.py` (new)

**Purpose**: Implement time-series CV with 21-day purge gap to prevent data leakage

**Architecture**:
```python
class PurgedWalkForwardCV:
    """Walk-forward cross-validation with purge gap."""

    # Configuration
    n_splits: int = 5              # Number of CV splits
    purge_days: int = 21           # Days to purge between train/test
    test_size_ratio: float = 0.2  # Test set size as fraction of total
```

**Interface Specification**:
```python
def split(
    self,
    data: pd.DataFrame,
    dates: pd.DatetimeIndex
) -> Iterator[Tuple[pd.Index, pd.Index]]:
    """Generate train/test splits with purge gap.

    Args:
        data: Full dataset
        dates: Date index for the data

    Yields:
        Tuple[train_idx, test_idx]: Train and test indices for each split

    Implementation:
        For each split i:
            1. Calculate split_point = start + (i+1) * window_size
            2. train_end = split_point - purge_days
            3. test_start = split_point
            4. test_end = test_start + test_size
            5. Yield (train_idx, test_idx)

    Validation:
        - No overlap between train and test (including purge gap)
        - All test sets are in the future relative to train sets
        - Test sets are contiguous in time
    """
```

---

### P2.2: E2E Testing Framework

**Module**: `tests/e2e/` (new directory)

**Purpose**: End-to-end integration tests for complete strategy workflows

**Test Categories**:
1. **Strategy Evolution Tests**: LLM → Feedback → Improvement → Validation
2. **Regime-Aware Tests**: Market data → Regime detection → Strategy selection
3. **Portfolio Tests**: Multi-asset → Optimization → Rebalancing
4. **Performance Tests**: Latency <100ms, Error rate <0.1%

**Framework Architecture**:
```python
class E2ETestFramework:
    """End-to-end testing framework for strategy workflows.

    Uses pytest fixtures for shared test setup and data provisioning.
    """

    # Shared Fixtures (defined in conftest.py)
    @pytest.fixture
    def market_data():
        """Provide realistic market data for testing."""
        # Load from fixtures/market_data.csv

    @pytest.fixture
    def test_environment():
        """Set up isolated test environment with mock LLM."""
        # Configure mock services, temporary directories

    @pytest.fixture
    def validation_thresholds():
        """Define success thresholds for each test category."""
        return {
            'latency_ms': 100,
            'error_rate': 0.001,
            'min_sharpe': 1.5
        }
```

**Test Interface Specification**:
```python
def run_evolution_test(
    self,
    initial_strategy: str,
    target_sharpe: float,
    max_iterations: int = 10,
    test_environment: TestEnvironment
) -> Dict[str, Any]:
    """Test complete strategy evolution workflow.

    Implementation:
        1. Initialize strategy with initial_strategy code
        2. For each iteration (up to max_iterations):
           - Execute backtest on test_environment.market_data
           - Generate feedback from results
           - Call LLM to improve strategy
           - Validate improved strategy compiles
        3. Assert final_sharpe >= target_sharpe
        4. Assert execution_time < 5.0 seconds

    Returns:
        {
            'success': bool,
            'final_sharpe': float,
            'iterations_used': int,
            'execution_time': float
        }
    """

def run_regime_test(
    self,
    market_data: pd.DataFrame,
    expected_regime: MarketRegime,
    regime_detector: RegimeDetector
) -> Dict[str, Any]:
    """Test regime detection and strategy selection.

    Implementation:
        1. Run regime_detector.detect_regime(market_data)
        2. Assert detected regime == expected_regime
        3. Select strategy based on regime
        4. Assert strategy selection logic is correct
        5. Measure confidence level

    Returns:
        {
            'regime_detected': str,
            'regime_correct': bool,
            'strategy_selected': str,
            'confidence': float
        }
    """
```

**Test Runner Configuration**:
- Uses pytest with custom markers: `@pytest.mark.e2e`, `@pytest.mark.slow`
- Shared fixtures defined in `tests/e2e/conftest.py`
- Test data stored in `tests/fixtures/`
- Parallel execution via `pytest-xdist` (optional)

---

### P2.3: Performance Benchmarks

**Module**: `tests/benchmarks/` (new directory)

**Purpose**: Automated performance regression testing

**Benchmark Suites**:
1. **Latency Benchmarks**: Strategy execution <100ms
2. **Throughput Benchmarks**: Iterations per second
3. **Memory Benchmarks**: Peak memory usage
4. **Accuracy Benchmarks**: Sharpe ratio, win rate, max drawdown

**Framework Architecture**:
```python
class PerformanceBenchmark:
    """Performance benchmark suite using pytest-benchmark.

    Configuration:
        - Uses pytest-benchmark plugin for statistical analysis
        - Runs each benchmark 10 times (warmup) + 100 times (measurement)
        - Reports min, max, mean, median, stddev
        - Stores baseline results in .benchmarks/ for regression detection
    """
```

**Interface Specification**:
```python
def benchmark_latency(self, benchmark) -> Dict[str, float]:
    """Measure end-to-end latency for key operations.

    Args:
        benchmark: pytest-benchmark fixture

    Implementation:
        Use benchmark.pedantic() for precise measurement:
        result = benchmark.pedantic(
            target_function,
            args=(arg1, arg2),
            iterations=100,
            rounds=10
        )

    Returns:
        {
            'strategy_execution': float,  # milliseconds
            'backtest_run': float,
            'optimization_step': float,
            'regime_detection': float
        }

    Thresholds (enforced via pytest.raises):
        - strategy_execution < 100ms
        - backtest_run < 500ms
        - optimization_step < 200ms
        - regime_detection < 50ms

    Example:
        def test_benchmark_strategy_execution(benchmark):
            result = benchmark(execute_strategy, sample_strategy)
            assert benchmark.stats.median < 0.100  # 100ms
    """

def benchmark_memory(self) -> Dict[str, float]:
    """Measure peak memory usage using memory_profiler.

    Returns:
        {
            'optimizer_peak_mb': float,
            'backtest_peak_mb': float,
            'regime_detector_peak_mb': float
        }

    Thresholds:
        - optimizer_peak_mb < 500
        - backtest_peak_mb < 1000
        - regime_detector_peak_mb < 100
    """
```

**Dependencies**:
- `pytest-benchmark>=3.4.1` # Statistical benchmarking
- `memory-profiler>=0.60.0` # Memory profiling

---

### P3.1: Documentation System

**Modules**: `docs/` directory

**Purpose**: Comprehensive documentation for system architecture, APIs, and operational guides

**Documentation Structure**:
- `docs/architecture/`: System design and component diagrams
- `docs/api/`: API reference for all modules
- `docs/guides/`: User guides and tutorials
- `docs/operations/`: Deployment and monitoring guides

---

### P3.2: Monitoring Dashboard

**Module**: `src/monitoring/dashboard.py` (new)

**Purpose**: Real-time monitoring of system health and performance

**Metrics**:
- **Performance**: Latency, throughput, error rate
- **Business**: Sharpe ratio, total return, win rate
- **System**: CPU, memory, disk usage
- **Reliability**: Uptime, success rate, failure rate

**Interface Specification**:
```python
class MonitoringDashboard:
    """Real-time monitoring dashboard."""

    def collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics.

        Returns:
            {
                'latency_p50': float,
                'latency_p95': float,
                'latency_p99': float,
                'error_rate': float,
                'uptime': float,
                'sharpe_ratio': float,
                'total_return': float
            }
        """

    def check_health(self) -> Dict[str, str]:
        """Check system health status.

        Returns:
            {
                'overall': 'healthy' | 'degraded' | 'critical',
                'latency': 'healthy' | 'warning' | 'critical',
                'errors': 'healthy' | 'warning' | 'critical',
                'uptime': 'healthy' | 'warning' | 'critical'
            }

        Thresholds:
            - Latency: <100ms healthy, <200ms warning, >=200ms critical
            - Error rate: <0.1% healthy, <1% warning, >=1% critical
            - Uptime: >=99.9% healthy, >=99% warning, <99% critical
        """
```

## Data Models

### Core Data Structures

**StrategyMetrics** (P0.1):
```python
@dataclass
class StrategyMetrics:
    """Strategy performance metrics with dict interface."""
    sharpe_ratio: Optional[float] = None      # Risk-adjusted return
    total_return: Optional[float] = None      # Cumulative return
    max_drawdown: Optional[float] = None      # Maximum peak-to-trough decline
    win_rate: Optional[float] = None          # Percentage of winning trades
    execution_success: bool = False           # Whether execution succeeded
```

**ASHAConfig** (P0.2):
```python
@dataclass
class ASHAConfig:
    """ASHA optimizer configuration."""
    n_iterations: int = 100
    min_resource: int = 3
    reduction_factor: int = 3
    grace_period: int = 5
```

**MarketRegime** (P1.1):
```python
class MarketRegime(Enum):
    """Market regime classification."""
    BULL_CALM = "bull_calm"
    BULL_VOLATILE = "bull_volatile"
    BEAR_CALM = "bear_calm"
    BEAR_VOLATILE = "bear_volatile"
```

**RegimeStats** (P1.1):
```python
@dataclass
class RegimeStats:
    """Market regime statistics."""
    trend: float                    # Current trend value (-1 to 1)
    volatility: float               # Current volatility value
    regime: MarketRegime           # Current regime classification
    confidence: float               # Confidence score (0 to 1)
```

**PortfolioWeights** (P1.2):
```python
@dataclass
class PortfolioWeights:
    """Portfolio weight allocation."""
    weights: Dict[str, float]       # Asset weights
    risk_contributions: Dict[str, float]  # Risk contribution per asset
    total_risk: float               # Portfolio total risk
    expected_return: float          # Expected portfolio return
```

**ValidationResult** (P2):
```python
@dataclass
class ValidationResult:
    """Cross-validation result."""
    train_metrics: StrategyMetrics  # Training set metrics
    test_metrics: StrategyMetrics   # Test set metrics
    split_idx: int                  # Split index
    train_dates: Tuple[str, str]    # Train date range
    test_dates: Tuple[str, str]     # Test date range
```

**BenchmarkResult** (P2.3):
```python
@dataclass
class BenchmarkResult:
    """Performance benchmark result."""
    operation: str                  # Operation name
    latency_p50: float             # 50th percentile latency (ms)
    latency_p95: float             # 95th percentile latency (ms)
    latency_p99: float             # 99th percentile latency (ms)
    throughput: float              # Operations per second
    memory_peak: float             # Peak memory usage (MB)
    status: str                    # 'pass' | 'fail'
```

## Error Handling

### Error Categories

**Validation Errors** (P0.1, P0.2):
- `ValueError`: Invalid configuration parameters
- `KeyError`: Missing required metric fields
- `TypeError`: Type mismatch in function arguments

**Optimization Errors** (P0.2):
- `TrialPruned`: Trial pruned by ASHA algorithm (expected)
- `OptimizationTimeout`: Search exceeded time limit
- `ConvergenceError`: Failed to converge within max iterations

**Regime Detection Errors** (P1.1):
- `InsufficientDataError`: Not enough data for regime calculation
- `RegimeAmbiguityError`: Market conditions unclear (near threshold)

**Portfolio Optimization Errors** (P1.2):
- `InfeasibleConstraintError`: No solution satisfying constraints
- `SingularCovarianceError`: Covariance matrix not invertible

**Validation Errors** (P2.1):
- `DataLeakageError`: Detected overlap between train and test sets
- `PurgeSizeError`: Purge gap larger than available data

### Error Handling Strategies

**Defensive Programming**:
```python
def validate_input(data: Any, schema: Dict) -> None:
    """Validate input data against schema."""
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data)}")

    for key, expected_type in schema.items():
        if key not in data:
            raise ValueError(f"Missing required field: {key}")
        if not isinstance(data[key], expected_type):
            raise TypeError(f"Field {key}: expected {expected_type}, got {type(data[key])}")
```

**Graceful Degradation**:
```python
def detect_regime_safe(prices: pd.Series) -> Optional[MarketRegime]:
    """Detect regime with fallback to None on error."""
    try:
        return detect_regime(prices)
    except InsufficientDataError:
        logger.warning("Insufficient data for regime detection")
        return None
    except Exception as e:
        logger.error(f"Regime detection failed: {e}")
        return None
```

**Retry Logic**:
```python
def optimize_with_retry(
    objective_fn: Callable,
    max_retries: int = 3,
    backoff: float = 2.0
) -> Dict[str, Any]:
    """Optimize with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return optimize(objective_fn)
        except OptimizationTimeout:
            if attempt < max_retries - 1:
                time.sleep(backoff ** attempt)
                continue
            raise
```

**Validation Logging**:
```python
def log_validation_result(result: ValidationResult) -> None:
    """Log validation result with full context."""
    logger.info(
        f"Validation split {result.split_idx}: "
        f"train_sharpe={result.train_metrics.sharpe_ratio:.2f}, "
        f"test_sharpe={result.test_metrics.sharpe_ratio:.2f}, "
        f"dates={result.test_dates}"
    )
```

## Testing Strategy

### TDD Red-Green-Refactor Cycle

**Red Phase**:
1. Write failing test for next feature
2. Verify test fails for the right reason
3. Ensure test is specific and minimal

**Green Phase**:
1. Write minimal code to make test pass
2. Verify all tests pass (including new test)
3. No refactoring yet

**Refactor Phase**:
1. Improve code structure without changing behavior
2. Run tests continuously to ensure no regression
3. Commit only when all tests pass

### Test Pyramid

**Unit Tests (70% of tests)**:
- Target: All functions and methods
- Coverage: ≥95% line coverage, ≥90% branch coverage
- Speed: <1ms per test
- Isolation: Mock all external dependencies

**Integration Tests (20% of tests)**:
- Target: Component interactions
- Coverage: Key workflows and data flows
- Speed: <100ms per test
- Isolation: Use test databases and mock external APIs

**E2E Tests (10% of tests)**:
- Target: Complete user workflows
- Coverage: Critical business paths
- Speed: <5s per test
- Isolation: Use test environments

### Validation Gates (6 Gates)

**Gate 1: Unit Tests GREEN** (P0 Exit Criteria):
```bash
pytest tests/unit/ --cov=src --cov-report=term
# Expected: 0% error rate, ≥95% coverage, all tests pass
```

**Gate 2: Regime-Aware Performance** (P1 Exit Criteria):
```bash
pytest tests/integration/test_regime_aware.py
# Expected: ≥10% improvement vs. baseline
```

**Gate 3: Stage 2 Breakthrough** (P1 + P2 Target):
```bash
pytest tests/validation/test_stage2_metrics.py
# Expected: 80%+ win rate, 2.5+ Sharpe, 40%+ return
```

**Gate 4: Portfolio Optimization** (P1.2-1.3 Validation):
```bash
pytest tests/integration/test_portfolio.py
# Expected: +5-15% improvement vs. equal-weighted
```

**Gate 5: OOS Validation** (P2.1 Requirement):
```bash
pytest tests/validation/test_oos.py
# Expected: Test sharpe within ±20% of train sharpe
```

**Gate 6: Production Readiness** (P2 + P3 Exit):
```bash
pytest tests/benchmarks/ tests/e2e/ --benchmark
# Expected: <100ms latency, <0.1% error, 99.9%+ uptime
```

### Test Organization

**Directory Structure**:
```
tests/
├── unit/                     # Unit tests (P0-P3)
│   ├── test_metrics.py       # P0.1: StrategyMetrics tests
│   ├── test_optimizer.py     # P0.2: ASHA tests
│   ├── test_regime.py        # P1.1: RegimeDetector tests
│   ├── test_portfolio.py     # P1.2-1.3: Portfolio tests
│   └── test_purged_cv.py     # P2.1: CV tests
├── integration/              # Integration tests
│   ├── test_evolution.py     # Strategy evolution workflow
│   ├── test_regime_aware.py  # Regime-aware strategy selection
│   └── test_portfolio.py     # Portfolio optimization workflow
├── e2e/                      # End-to-end tests (P2.2)
│   ├── test_complete_flow.py
│   └── test_production.py
└── benchmarks/               # Performance benchmarks (P2.3)
    ├── test_latency.py
    └── test_throughput.py
```

### Test Patterns

**Fixture-Based Testing**:
```python
@pytest.fixture
def sample_metrics():
    """Provide sample metrics for testing."""
    return StrategyMetrics(
        sharpe_ratio=1.5,
        total_return=0.25,
        max_drawdown=-0.15,
        win_rate=0.60,
        execution_success=True
    )

def test_metrics_dict_interface(sample_metrics):
    """Test dict interface methods."""
    assert sample_metrics['sharpe_ratio'] == 1.5
    assert 'total_return' in sample_metrics
    assert len(sample_metrics) == 5
```

**Parameterized Testing**:
```python
@pytest.mark.parametrize("reduction_factor,expected", [
    (2, True),   # Valid
    (3, True),   # Valid
    (1, False),  # Invalid (too small)
])
def test_asha_validation(reduction_factor, expected):
    """Test ASHA parameter validation."""
    if expected:
        optimizer = ASHAOptimizer(reduction_factor=reduction_factor)
        assert optimizer.reduction_factor == reduction_factor
    else:
        with pytest.raises(ValueError):
            ASHAOptimizer(reduction_factor=reduction_factor)
```

**Mock-Based Testing**:
```python
@patch('src.learning.optimizer.optuna.create_study')
def test_create_study(mock_create_study):
    """Test study creation with mocked Optuna."""
    mock_study = Mock()
    mock_create_study.return_value = mock_study

    optimizer = ASHAOptimizer()
    study = optimizer.create_study()

    assert study == mock_study
    mock_create_study.assert_called_once()
```

### Continuous Integration

**Pre-Commit Hooks**:
```bash
# Run before each commit
pytest tests/unit/ --fast-only
mypy src/ --strict
black src/ tests/ --check
flake8 src/ tests/
```

**CI Pipeline**:
```yaml
# .github/workflows/ci.yml
- name: Run tests
  run: |
    pytest tests/unit/ --cov=src --cov-report=xml
    pytest tests/integration/ --integration
    pytest tests/e2e/ --e2e --slow

- name: Check coverage
  run: |
    coverage report --fail-under=95  # Unit test coverage

- name: Run benchmarks
  run: |
    pytest tests/benchmarks/ --benchmark-only
```

### Performance Testing

**Latency Benchmarks**:
```python
def test_benchmark_strategy_execution(benchmark):
    """Benchmark strategy execution latency."""
    result = benchmark(execute_strategy, strategy_code)
    assert result.stats.median < 0.1  # <100ms
```

**Memory Profiling**:
```python
@memory_profiler.profile
def test_memory_usage():
    """Profile memory usage during optimization."""
    optimizer = ASHAOptimizer()
    optimizer.optimize(objective_fn, param_space, n_trials=100)
    # Monitor peak memory usage
```

## Implementation Timeline

### P0: Foundation (8-12h)
- **P0.1**: StrategyMetrics dict fix (2-3h)
  - Phase 1 Tests (1h): Unit tests for new methods
  - Phase 1 Implementation (1-2h): values(), items(), __len__()
- **P0.2**: ASHA Optimizer (6-9h)
  - Phase 1 Tests (2h): 8 immediate tests
  - Phase 1 Implementation (2-3h): optimize(), early_stop_callback()
  - Phase 2 Tests (1h): 12 additional tests
  - Phase 2 Implementation (1-4h): get_search_stats(), refinement

### P1: Intelligence (24-32h)
- **P1.1**: Regime Detection (8-10h)
- **P1.2**: Portfolio ERC (8-10h)
- **P1.3**: Epsilon-Constraint (8-12h)

### P2: Validation (48h)
- **P2.1**: Purged CV (12-16h)
- **P2.2**: E2E Framework (20-24h)
- **P2.3**: Benchmarks (16h)

### P3: Operations (40h)
- **P3.1**: Documentation (24h)
- **P3.2**: Monitoring (16h)

**Total**: 132h sequential → 88h parallel (44h savings through parallel execution)

## Dependencies

**Required Additions** (must add to requirements.txt):
- `optuna>=3.0.0` # P0.2: ASHA optimization
- `scipy>=1.7.0` # P1.2-1.3: Portfolio optimization (constrained optimization)
- `pytest-benchmark>=3.4.1` # P2.3: Performance benchmarking
- `memory-profiler>=0.60.0` # P2.3: Memory profiling

**Existing Dependencies** (already in requirements.txt):
- `pandas`, `numpy` # Data manipulation
- `pytest`, `pytest-cov` # Testing
- `finlab` # Trading platform integration

**Development Dependencies**:
- `mypy` # Type checking
- `black` # Code formatting
- `flake8` # Linting
- `pytest-xdist` # Parallel test execution (optional)

## Success Criteria

**P0 Success** (Foundation):
- ✅ All Phase 7 regressions fixed
- ✅ ASHA optimizer 50-70% faster than baseline
- ✅ 100% test coverage for new code
- ✅ Gate 1 passed (E2E tests GREEN)

**P1 Success** (Intelligence):
- ✅ Regime detection accuracy ≥85%
- ✅ Regime-aware strategies +10-20% vs. baseline
- ✅ Portfolio optimization +5-15% vs. equal-weighted
- ✅ Gate 2, 3, 4 passed

**P2 Success** (Validation):
- ✅ OOS metrics within ±20% of in-sample
- ✅ Production latency <100ms
- ✅ Error rate <0.1%
- ✅ Gate 5, 6 passed

**P3 Success** (Operations):
- ✅ Comprehensive documentation complete
- ✅ Monitoring dashboard operational
- ✅ 99.9%+ uptime achieved

## Risk Mitigation

**Technical Risks**:
- **Risk**: Optuna dependency conflicts
  - **Mitigation**: Pin version to >=3.0.0, test in clean venv
- **Risk**: ASHA convergence issues
  - **Mitigation**: Extensive testing with diverse parameter spaces
- **Risk**: Regime detection overfitting
  - **Mitigation**: Validate on out-of-sample data, use simple indicators
- **Risk**: scipy optimization failures (singular matrices, infeasible constraints)
  - **Mitigation**: Add matrix conditioning checks, fallback to equal-weighted portfolios

**Model & Data Risks**:
- **Risk**: 2×2 regime matrix oversimplifies market dynamics
  - **Mitigation**:
    - Backtest across multiple historical periods (2008, 2020, 2022 crises)
    - Implement fallback to regime-agnostic baseline if performance degrades
    - Monitor regime classification stability (avoid rapid switching)
- **Risk**: ERC/Epsilon-Constraint models underperform in practice
  - **Mitigation**:
    - Compare against simpler baselines (equal-weight, 60/40)
    - Validate assumptions (correlation stability, return predictability)
    - Implement ensemble approach if single model fails
- **Risk**: Data quality issues (survivor bias, gaps, errors)
  - **Mitigation**:
    - Implement data cleaning pipeline with anomaly detection
    - Use multiple data sources for cross-validation
    - Test model robustness against simulated noise (±10% price perturbations)
    - Explicitly test with incomplete data scenarios

**Timeline Risks**:
- **Risk**: P2 validation taking longer than 48h
  - **Mitigation**: Prioritize critical tests, defer nice-to-have tests to P3
- **Risk**: Integration issues between P1 components
  - **Mitigation**: Incremental integration with continuous testing

**Quality Risks**:
- **Risk**: Test coverage <95%
  - **Mitigation**: Enforce coverage gates in CI, block merges on coverage drop
- **Risk**: Performance regression
  - **Mitigation**: Continuous benchmarking, automated performance alerts
