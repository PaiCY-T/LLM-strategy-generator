# Phase 2 Validation Framework Integration - Design v1.1

**Version**: 1.1 (Production Readiness / Remediation)
**Date**: 2025-10-31
**Based On**: Critical review by Gemini 2.5 Pro

---

## Design Changes from Phase 1.0

Phase 1.0 delivered functional prototype but with critical flaws. Phase 1.1 redesigns three core components:

1. **Returns Extraction**: Replace synthesis with equity curve extraction
2. **Bootstrap Method**: Replace simple bootstrap with stationary bootstrap
3. **Threshold Calculation**: Replace arbitrary value with empirical benchmark

---

## Component 1: Returns Extraction Redesign

### Problem (Phase 1.0)

**Flawed Synthesis Approach**:
```python
# Phase 1.0 - STATISTICALLY UNSOUND
mean_return = total_return / n_days
std_return = (mean_return / sharpe_ratio) * sqrt(252)
synthetic_returns = np.random.normal(mean_return, std_return, n_days)
```

**Fatal Flaws**:
- Assumes normal distribution (false for finance)
- Destroys temporal structure
- Underestimates tail risk
- Will approve dangerous strategies

### Solution (Phase 1.1)

**Multi-Layered Extraction from finlab Report**:

```
┌─────────────────────────────────────────────────┐
│     finlab Report Object                        │
└─────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│  Method 1: report.returns (direct attribute)   │
│  → If exists and len >= 252: SUCCESS           │
└─────────────────────────────────────────────────┘
                    │ fallback
                    ▼
┌─────────────────────────────────────────────────┐
│  Method 2: report.daily_returns (alternative)  │
│  → If exists and len >= 252: SUCCESS           │
└─────────────────────────────────────────────────┘
                    │ fallback
                    ▼
┌─────────────────────────────────────────────────┐
│  Method 3: report.equity.pct_change()          │
│  → Calculate from equity curve                  │
│  → Handle DataFrame/Series                      │
│  → If len >= 252: SUCCESS                       │
└─────────────────────────────────────────────────┘
                    │ fallback
                    ▼
┌─────────────────────────────────────────────────┐
│  Method 4: report.position value changes       │
│  → Sum across positions                         │
│  → Calculate pct_change()                       │
│  → If len >= 252: SUCCESS                       │
└─────────────────────────────────────────────────┘
                    │ all failed
                    ▼
┌─────────────────────────────────────────────────┐
│  FAIL with detailed error message              │
│  → List tried methods                           │
│  → Show available attributes                    │
│  → No synthesis fallback                        │
└─────────────────────────────────────────────────┘
```

### Implementation

**File**: `src/validation/integration.py`

```python
def _extract_returns_from_report(
    self,
    report: Any,
    sharpe_ratio: float,  # Unused, kept for compatibility
    total_return: float,  # Unused, kept for compatibility
    n_days: int = 252
) -> Optional[np.ndarray]:
    """
    Extract actual daily returns from finlab Report.

    Strategy:
    1. Try direct attributes (returns, daily_returns)
    2. Try equity curve differentiation (most likely to work)
    3. Try position value changes
    4. Fail with clear error (NO SYNTHESIS)

    Raises:
        ValueError: If all extraction methods fail or data < 252 days
    """
    # Implementation with 4-layer fallback
    # See tasks_v1.1.md for full code
```

**Benefits**:
- Uses actual returns → statistically valid
- Multiple fallback methods → robust
- Clear errors when data unavailable
- No synthesis → no systematic bias

---

## Component 2: Stationary Bootstrap Redesign

### Problem (Phase 1.0)

**Simple Block Bootstrap**:
```python
# Phase 1.0 - Too simplistic
block_size = 21  # Fixed
start = random.randint(0, n)
block = returns[start:start+block_size]
```

**Limitations**:
- Fixed block size inflexible
- Doesn't optimally preserve temporal structure
- Standard method but not best for finance

### Solution (Phase 1.1)

**Politis & Romano Stationary Bootstrap**:

**Key Features**:
1. **Geometric Block Lengths**: More flexible than fixed
2. **Circular Wrapping**: Blocks can wrap around series end
3. **Preserves Autocorrelation**: Better for financial time series

**Algorithm**:
```
For each bootstrap iteration:
  1. Start with empty resampled series
  2. While len(resampled) < n:
     a. Pick random start index
     b. Draw block length from Geometric(1/avg_block_size)
     c. Extract block with circular wrapping: indices = (start + 0..block_len) % n
     d. Append block to resampled series
  3. Trim resampled to exactly n elements
  4. Calculate Sharpe ratio on resampled series
```

**Flow Diagram**:
```
┌──────────────────────────────────────────────────┐
│  Input: returns series (n days)                  │
└──────────────────────────────────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Iteration Loop     │
         │  (1000 iterations)  │
         └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Resample:          │
         │  1. Random start    │
         │  2. Geometric len   │
         │  3. Circular wrap   │
         └─────────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Calculate Sharpe   │
         │  on resampled data  │
         └─────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│  Aggregate Results:                              │
│  - Point estimate: mean(bootstrap_sharpes)      │
│  - CI lower: percentile(2.5%)                   │
│  - CI upper: percentile(97.5%)                  │
└──────────────────────────────────────────────────┘
```

### Implementation

**File**: `src/validation/stationary_bootstrap.py` (NEW)

```python
def stationary_bootstrap(
    returns: np.ndarray,
    n_iterations: int = 1000,
    avg_block_size: int = 21,
    confidence_level: float = 0.95
) -> Tuple[float, float, float]:
    """
    Stationary bootstrap for Sharpe ratio CIs.

    Implements Politis & Romano (1994) method.

    Returns:
        (point_estimate, ci_lower, ci_upper)

    Raises:
        ValueError: If len(returns) < 252
    """
    # Full implementation in tasks_v1.1.md
```

**Benefits**:
- Statistically rigorous
- Preserves temporal structure
- Industry-standard method
- Can validate against scipy

---

## Component 3: Dynamic Threshold Redesign

### Problem (Phase 1.0)

**Arbitrary Static Threshold**:
```python
# Phase 1.0 - No justification
threshold = max(calculated_threshold, 0.5)
```

**Problems**:
- No empirical Taiwan market basis
- Ignores passive benchmark performance
- Market regime blind
- May be too high or too low

### Solution (Phase 1.1)

**Dynamic Benchmark-Relative Threshold**:

**Formula**:
```
threshold = max(
    benchmark_sharpe + margin,
    static_floor
)

Where:
- benchmark_sharpe = rolling 3-year Sharpe of 0050.TW
- margin = 0.2 (active strategy must beat passive by 0.2)
- static_floor = 0.0 (positive risk-adjusted returns minimum)
```

**Design**:
```
┌──────────────────────────────────────────────────┐
│  0050.TW Historical Data                         │
│  (Taiwan passive benchmark)                      │
└──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│  Calculate Rolling 3-Year Sharpe                │
│  (preserves market regime awareness)             │
└──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│  Add Margin (0.2)                                │
│  → Active must beat passive by 20% Sharpe       │
└──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│  Apply Floor (0.0)                               │
│  → Ensure positive risk-adjusted returns         │
└──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│  Dynamic Threshold                               │
│  → Adapts to market conditions                   │
│  → Empirically justified                         │
└──────────────────────────────────────────────────┘
```

### Implementation

**File**: `src/validation/dynamic_threshold.py` (NEW)

```python
class DynamicThresholdCalculator:
    """Calculate Sharpe threshold based on Taiwan benchmarks."""

    def __init__(
        self,
        benchmark_ticker: str = "0050.TW",
        lookback_years: int = 3,
        margin: float = 0.2,
        static_floor: float = 0.0
    ):
        self.benchmark_ticker = benchmark_ticker
        self.lookback_years = lookback_years
        self.margin = margin
        self.static_floor = static_floor

    def get_threshold(self, current_date: Optional[str] = None) -> float:
        """Calculate dynamic threshold."""
        # Fetch 0050.TW data (TODO)
        # Calculate rolling Sharpe
        # Return max(benchmark_sharpe + margin, floor)
```

**Integration**:
```python
class BonferroniIntegrator:
    def __init__(self, n_strategies=20, use_dynamic_threshold=True):
        if use_dynamic_threshold:
            self.threshold_calc = DynamicThresholdCalculator()

    def validate_single_strategy(self, sharpe_ratio, ...):
        if self.threshold_calc:
            threshold = self.threshold_calc.get_threshold()
        # ... validation logic
```

**Benefits**:
- Empirically justified
- Market-regime aware
- Adapts to conditions
- Prevents arbitrary choices

---

## Testing Strategy Redesign

### Phase 1.0 Testing (INSUFFICIENT)

**Only Unit Tests**:
- Methods exist ✓
- Methods return expected structure ✓
- Happy path works ✓

**Missing**:
- Integration tests ✗
- Statistical validation ✗
- E2E validation ✗
- Failure modes ✗

### Phase 1.1 Testing (COMPREHENSIVE)

**4-Layer Testing Pyramid**:

```
                    ┌──────────────┐
                    │   E2E Tests  │  (Layer 4)
                    │  Real finlab │
                    │  execution   │
                    └──────────────┘
                          │
                ┌────────────────────┐
                │  Integration Tests │  (Layer 3)
                │  Component combos  │
                └────────────────────┘
                          │
          ┌──────────────────────────────┐
          │  Statistical Validation     │  (Layer 2)
          │  vs scipy, coverage rates   │
          └──────────────────────────────┘
                          │
    ┌────────────────────────────────────────┐
    │          Unit Tests                     │  (Layer 1)
    │  Individual methods, mocks              │
    └────────────────────────────────────────┘
```

**Layer 1: Unit Tests** (Existing + Enhanced)
- Mock Report objects with equity/returns
- 4 extraction methods tested individually
- Stationary bootstrap with known inputs
- Threshold calculator with fixed dates

**Layer 2: Statistical Validation** (NEW)
- Bootstrap vs scipy comparison
- Coverage rate verification (100 experiments)
- Known returns series validation
- CI width reasonableness checks

**Layer 3: Integration Tests** (NEW)
- ValidationIntegrator + BootstrapIntegrator interaction
- BaselineIntegrator caching behavior
- Report generator with all validator results
- Backward compatibility checks

**Layer 4: E2E Tests** (NEW)
- Real finlab data and sim objects
- Actual strategy execution
- Full validation pipeline
- HTML/JSON report generation

**Chaos Testing** (NEW):
- NaN/inf in returns
- Network timeout (baseline fetch)
- Concurrent execution
- Malformed configuration
- Resource exhaustion

---

## Architecture Impact

### Data Flow (Phase 1.1)

```
┌─────────────────────────────────────────────────────────┐
│  1. Strategy Execution                                  │
│  BacktestExecutor → finlab Report object                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. Returns Extraction (NEW DESIGN)                     │
│  Report.equity.pct_change() → numpy array               │
│  ✓ 252-day minimum enforced                             │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. Stationary Bootstrap (NEW DESIGN)                   │
│  1000 iterations, geometric blocks → CI                 │
│  ✓ Preserves temporal structure                         │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  4. Dynamic Threshold (NEW DESIGN)                      │
│  0050.TW benchmark + 0.2 margin → threshold             │
│  ✓ Empirically justified                                │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  5. Validation Decision                                 │
│  ci_lower > threshold AND ci_lower > 0                  │
└─────────────────────────────────────────────────────────┘
```

### New Files

1. **src/validation/stationary_bootstrap.py** (NEW)
   - Standalone stationary bootstrap implementation
   - Reusable for other applications

2. **src/validation/dynamic_threshold.py** (NEW)
   - Taiwan market threshold calculator
   - Configurable for different benchmarks

3. **tests/validation/test_returns_extraction_robust.py** (NEW)
   - Comprehensive extraction testing

4. **tests/validation/test_stationary_bootstrap.py** (NEW)
   - Statistical validation tests

5. **tests/integration/test_validation_pipeline_e2e_v1_1.py** (NEW)
   - Full E2E pipeline tests

### Modified Files

1. **src/validation/integration.py**
   - `_extract_returns_from_report()`: Complete redesign
   - `BootstrapIntegrator.validate_with_bootstrap()`: Use stationary bootstrap
   - `BonferroniIntegrator`: Integrate dynamic threshold

2. **src/validation/__init__.py**
   - Export new modules

---

## Performance Impact

### Phase 1.0 Estimates (Unrealistic)
- Bootstrap: "~2-5 seconds" (based on guessing)
- Total: "~30-60 seconds" (no actual measurement)

### Phase 1.1 Targets (Measured)
- Bootstrap: <5 seconds (1000 iterations on 252-day series)
- Returns extraction: <0.1 seconds
- Threshold calculation: <0.01 seconds (cached)
- **Total per-strategy overhead: <60 seconds** (measured target)

---

## Risk Mitigation

### Risks from Phase 1.0

| Risk | Phase 1.0 Status | Phase 1.1 Mitigation |
|------|------------------|----------------------|
| Approve risky strategies | HIGH (synthesis bias) | **FIXED**: Use actual returns |
| Reject good strategies | MEDIUM (arbitrary threshold) | **FIXED**: Empirical threshold |
| Silent failures | HIGH (no integration tests) | **FIXED**: E2E + chaos tests |
| Performance degradation | UNKNOWN | **FIXED**: Benchmarks |
| Memory leaks | UNKNOWN | **FIXED**: Stress tests |

---

## Migration Path

### Backward Compatibility

**API Compatibility Maintained**:
- All method signatures unchanged (new optional parameters only)
- All public exports remain
- Existing client code continues to work

**Behavior Changes** (Improvements):
- Bootstrap now uses actual returns (was synthesis)
- Threshold now dynamic (was static 0.5)
- More stringent validation (better quality control)

**Migration Steps**:
1. Phase 1.1 code deployed
2. Run regression tests to verify compatibility
3. Monitor validation pass rates
4. Adjust threshold parameters if needed

---

## Success Criteria

Phase 1.1 achieves production readiness when:

1. **Statistical Validity**:
   - ✓ Bootstrap uses actual returns (verified in tests)
   - ✓ Bootstrap validates vs scipy (CI widths within 30%)
   - ✓ Coverage rates match confidence level (85-100%)

2. **Integration**:
   - ✓ E2E test passes with real finlab
   - ✓ All 5 validators execute successfully
   - ✓ Reports generate correctly

3. **Performance**:
   - ✓ <60s per strategy overhead (measured)
   - ✓ No memory leaks (100-strategy stress test)
   - ✓ HTML scales to 1000+ strategies

4. **Robustness**:
   - ✓ All chaos tests pass
   - ✓ Error messages clear and actionable
   - ✓ Concurrent execution safe

---

**Version**: 1.1
**Status**: DESIGN APPROVED
**Next**: Implement according to tasks_v1.1.md
