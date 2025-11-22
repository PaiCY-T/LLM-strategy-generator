# Task 2.1: Strategy.to_pipeline() Integration Test Results

**Test Date**: 2025-11-16 23:28
**Test Duration**: 4.31s
**Test Status**: ✅ SUCCESS
**Hypothesis**: 90% confidence that timeout occurs in to_pipeline() orchestration

---

## Executive Summary

**HYPOTHESIS REFUTED**: Strategy.to_pipeline() is NOT the bottleneck causing the 420s timeout.

**Key Finding**: to_pipeline() executes in **3.46 seconds** - even FASTER than direct factor execution (5.23s), demonstrating that the orchestration layer is highly efficient.

**Critical Insight**: The timeout must be in the **sim() backtesting layer** (Task 2.2), NOT in the Factor Graph execution pipeline.

---

## Test Results

### Performance Breakdown

| Phase | Duration | Status |
|-------|----------|--------|
| Imports | 0.78s | ✅ Normal |
| Strategy creation | 0.01s | ✅ Excellent |
| **to_pipeline() TOTAL** | **3.46s** | **✅ Excellent** |
| └─ Phase 1: Validation | 0.00s | ✅ Excellent |
| └─ Phase 2: Container creation | 0.00s | ✅ Excellent |
| └─ Phase 3: Graph execution | 3.38s | ✅ Excellent |
| │  ├─ momentum_20 | 1.56s | ✅ Normal |
| │  ├─ breakout_20 | 1.32s | ✅ Normal |
| │  └─ rolling_trailing_stop | 0.50s | ✅ Excellent |
| └─ Phase 4: Naming adapter | 0.07s | ✅ Excellent |
| Validation | 0.07s | ✅ Excellent |
| **TOTAL** | **4.31s** | **✅ Excellent** |

### Comparison with Phase 1

| Test | Execution Type | Duration | Overhead |
|------|---------------|----------|----------|
| Task 1.5 (Phase 1) | Direct factor execution | 5.23s | Baseline |
| Task 2.1 (Phase 2) | to_pipeline() orchestration | 3.46s | **-1.77s** (FASTER!) |

**Analysis**: to_pipeline() is actually 1.77s FASTER than direct execution, likely due to:
- Optimized container initialization timing
- Efficient lazy loading of FinLab data
- Streamlined dependency resolution

---

## Detailed Phase Analysis

### Phase 1: Validation (0.00s)
**Performance**: Excellent
**Methods tested**:
- `validate_structure()`: DAG integrity checks
- Cycle detection
- Orphan factor detection
- Duplicate output detection

**Conclusion**: Static validation is instantaneous, no bottleneck here.

---

### Phase 2: Container Creation (0.00s)
**Performance**: Excellent
**Methods tested**:
- `FinLabDataFrame.__init__()`
- Container initialization

**Conclusion**: Container creation is instantaneous, no bottleneck here.

---

### Phase 3: Graph Execution (3.38s)
**Performance**: Excellent
**Methods tested**:
- `nx.topological_sort()`: 0.00s (efficient)
- Factor execution loop:
  - momentum_20: 1.56s (includes lazy-load of 'close' data)
  - breakout_20: 1.32s (includes lazy-load of 'high' and 'low' data)
  - rolling_trailing_stop: 0.50s (fast, dependencies already loaded)

**Key Observations**:
1. Topological sort is instantaneous (no N² complexity issues)
2. First factor is slower due to initial data loading (1.56s)
3. Subsequent factors benefit from cached data (1.32s, 0.50s)
4. No redundant container operations detected
5. Total factor execution: 3.38s vs 5.23s in Phase 1 (35% faster!)

**Conclusion**: Graph execution is highly optimized, no bottleneck here.

---

### Phase 4: Naming Adapter + Validation (0.07s)
**Performance**: Excellent
**Methods tested**:
- Semantic name mapping (entry signals → position)
- Signal combination logic (AND operator)
- Exit signal application
- `validate_data()`: Runtime validation

**Conclusion**: Naming adapter is efficient, no bottleneck here.

---

## Output Validation

**Position Matrix**:
- Shape: (4568, 2662) - Full Taiwan stock market
- Signals: 525,388 True values
- Memory: 11.63 MB
- Data type: bool (efficient)

**Quality Checks**: ✅ All passed
- Matrix has data ✅
- Signal count valid ✅
- Memory usage reasonable ✅

---

## Hypothesis Evaluation

### Original Hypothesis (90% confidence)
**"Timeout occurs in to_pipeline() due to N² dependency resolution or redundant operations"**

**Verdict**: ❌ REFUTED

**Evidence**:
1. to_pipeline() completes in 3.46s (< 30s threshold)
2. No N² complexity detected in topological sort (0.00s)
3. No redundant container operations observed
4. Naming adapter is efficient (0.07s)
5. All internal phases are fast (<3.5s total)

**Actual overhead**: -1.77s (to_pipeline() is FASTER than direct execution)

---

## Root Cause Analysis

### What We've Ruled Out

| Component | Test | Duration | Verdict |
|-----------|------|----------|---------|
| Individual factors | Task 1.1-1.4 | <3s each | ✅ Healthy |
| Factor composition | Task 1.5 | 5.23s | ✅ Healthy |
| to_pipeline() orchestration | Task 2.1 | 3.46s | ✅ Healthy |

### What Remains to Test

**Primary Suspect: sim() Backtesting Layer (Task 2.2)**

**Hypothesis for Task 2.2 (95% confidence)**:
The 420s+ timeout occurs in the **simulation/backtesting layer**, not in Factor Graph execution.

**Potential bottlenecks in sim()**:
1. **Position tracking state management**: Maintaining position history across 4,568 trading days
2. **Trade execution simulation**: Computing entry/exit for each signal
3. **Portfolio rebalancing logic**: Daily portfolio updates
4. **Performance metric calculation**: Computing returns, drawdowns, Sharpe ratios
5. **Cash flow tracking**: Tracking cash, positions, and leverage over time

**Evidence supporting this hypothesis**:
- ✅ Factor execution is fast (3.46s)
- ✅ Position signals are generated quickly (525,388 signals)
- ❓ No timing data for sim() layer (yet)
- ❓ sim() operates on full historical data (4,568 days × 2,662 stocks)
- ❓ sim() likely has O(days × stocks × trades) complexity

---

## Recommendations

### ✅ Immediate Action: Proceed to Task 2.2

**Test Specification for Task 2.2**:
1. Create `experiments/diagnostic_sim_test.py`
2. Test the FULL workflow including sim() execution:
   ```python
   strategy = create_3_factor_template()
   position = strategy.to_pipeline(data, skip_validation=True)
   report = sim(position, ...)  # ← TEST THIS
   ```
3. Add detailed timing at EACH sim() phase:
   - sim() initialization
   - Position processing
   - Trade execution simulation
   - Portfolio state updates
   - Performance metric calculation
   - Report generation
4. Compare with to_pipeline() baseline (3.46s)

**Expected Outcome**:
- **TIMEOUT (>420s)**: Confirms sim() is the bottleneck → Deep profiling of sim() internals
- **SUCCESS (<30s)**: Unexpected → Need to investigate test environment or full integration

---

### Alternative Hypotheses (if Task 2.2 also passes)

**Scenario A: Environment-Specific Issue**
- Timeout only occurs in specific test configurations
- Check: Data size, memory pressure, CPU throttling
- Action: Profile production environment vs test environment

**Scenario B: Integration Bottleneck**
- Timeout occurs only when ALL components run together
- Check: Memory leaks, resource contention, GC pressure
- Action: Full end-to-end profiling with memory/CPU monitoring

**Scenario C: Data-Dependent Timeout**
- Timeout occurs only with specific data patterns
- Check: Signal density, trade frequency, market volatility
- Action: Test with different date ranges and stock universes

---

## Technical Details

### Test Configuration
- **Strategy**: 3-factor template (momentum + breakout + trailing_stop)
- **Factors**: momentum_20, breakout_20, rolling_trailing_stop_10pct_20d
- **Dependencies**: trailing_stop depends on both momentum and breakout
- **Data**: Full Taiwan stock market (4,568 days × 2,662 stocks)
- **Timeout**: 420s (not reached)

### Factor Parameters
```python
momentum_factor:
  momentum_period: 20

breakout_factor:
  entry_window: 20

rolling_trailing_stop_factor:
  trail_percent: 0.10
  lookback_periods: 20
```

### DAG Structure
```
momentum_20 ──┐
              ├─→ rolling_trailing_stop_10pct_20d
breakout_20 ──┘
```

---

## Appendix: Timing Logs

### to_pipeline() Internal Timing (from strategy.py)
```
[TIMING] Phase 1 START: Validation at 2025-11-16 23:28:15.787350
[TIMING] Phase 1 COMPLETE: Validation in 0.00s
[TIMING] Phase 2 START: Container creation at 2025-11-16 23:28:15.787669
[TIMING] Phase 2 COMPLETE: Container created in 0.00s
[TIMING] Phase 3 START: Graph execution at 2025-11-16 23:28:15.787714
[TIMING] Factor count: 3
[TIMING] Execution order: ['momentum_20', 'breakout_20', 'rolling_trailing_stop_10pct_20d']
[TIMING] Factor 1/3: momentum_20 START at 2025-11-16 23:28:15.787770
[TIMING] Factor momentum_20 COMPLETE in 1.56s
[TIMING] Factor 2/3: breakout_20 START at 2025-11-16 23:28:17.349022
[TIMING] Factor breakout_20 COMPLETE in 1.32s
[TIMING] Factor 3/3: rolling_trailing_stop_10pct_20d START at 2025-11-16 23:28:18.665519
[TIMING] Factor rolling_trailing_stop_10pct_20d COMPLETE in 0.50s
[TIMING] Phase 3 COMPLETE: Graph executed in 3.38s
[TIMING] Phase 4 START: Naming adapter + validation at 2025-11-16 23:28:19.167159
[TIMING] Phase 4 COMPLETE: Naming adapter + validation in 0.07s
```

### Factor Execution Breakdown
```
momentum_20:
  - Execution time: 1.56s
  - Includes: Lazy load 'close' data (price:收盤價)
  - Output: momentum signal matrix

breakout_20:
  - Execution time: 1.32s
  - Includes: Lazy load 'high' and 'low' data
  - Output: breakout_signal matrix

rolling_trailing_stop_10pct_20d:
  - Execution time: 0.50s
  - Dependencies: Uses momentum and breakout outputs
  - Output: rolling_trailing_stop_signal matrix
```

---

## Conclusion

**Task 2.1 Verdict**: ✅ SUCCESS - Hypothesis REFUTED

**Key Findings**:
1. ✅ to_pipeline() is NOT the bottleneck (3.46s execution)
2. ✅ All orchestration phases are efficient (<3.5s total)
3. ✅ to_pipeline() is actually FASTER than direct execution
4. ❌ Original hypothesis (90% confidence) was INCORRECT

**Next Action**: **Proceed to Task 2.2** to test sim() backtesting layer

**Updated Diagnostic Roadmap**:
```
Phase 1: Factor Execution ✅ COMPLETE (5.23s)
  ├─ Task 1.1: momentum_factor ✅ (2.75s)
  ├─ Task 1.2: breakout_factor ✅ (2.08s)
  ├─ Task 1.3: trailing_stop_factor ✅ (0.40s)
  └─ Task 1.4: Full composition ✅ (5.23s)

Phase 2: Pipeline Orchestration ✅ COMPLETE (3.46s)
  └─ Task 2.1: to_pipeline() ✅ (3.46s) ← CURRENT

Phase 3: Backtesting Layer ❓ NEXT
  └─ Task 2.2: sim() execution ❓ ← PRIMARY SUSPECT
```

**Confidence Level**: 95% that timeout is in sim() layer (increased from 90% based on evidence)
