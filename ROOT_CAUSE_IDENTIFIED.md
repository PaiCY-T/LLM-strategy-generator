# Root Cause Analysis - Sharpe Ratio Calculation Bug

**Date**: 2025-10-20
**Status**: 🔍 **ROOT CAUSE IDENTIFIED**

---

## Executive Summary

Identified the architectural flaw causing 3-5x Sharpe ratio overestimation during CombinationTemplate evolution. The system incorrectly uses placeholder backtest instead of finlab's real backtest functionality during fitness evaluation.

### Key Finding

**Two Different Code Paths**:
1. **Initial Population** (CORRECT): Template → finlab.backtest → finlab.metrics.sharpe_ratio() → Sharpe 1.068-1.378 ✅
2. **Evolution Phase** (WRONG): PopulationManager → placeholder backtest → fallback calculation → Sharpe 3.943-5.495 ❌

---

## Detailed Analysis

### Call Stack Comparison

#### Initial Population (CORRECT)
```
run_combination_smoke_test.py (line 410-470)
  ↓
CombinationTemplate.generate_strategy() (line 450-513)
  ↓
finlab.backtest.sim() (line 483)  # Real finlab backtest
  ↓
report.metrics.sharpe_ratio() (line 495)  # ✅ Uses finlab's built-in calculation
  ↓
Result: Sharpe 1.068-1.378 ✅ CORRECT
```

#### Evolution Phase (WRONG)
```
run_combination_smoke_test.py (line 488)
  ↓
PopulationManager.evolve_generation() (line 367-501)
  ↓
PopulationManager.evaluate_population() (line 224-276)
  ↓
PopulationManager._evaluate_strategy() (line 278-334)
  ↓
PopulationManager._run_placeholder_backtest() (line 336-365)
  ├── Creates equity_curve = pd.Series([...])  # ❌ NO DatetimeIndex!
  └── Returns BacktestResult with non-datetime index
  ↓
calculate_metrics(backtest_result) (line 301)
  ↓
src/backtest/metrics.py calculate_metrics() (line 133-221)
  ├── Try: finlab.report.metrics.sharpe_ratio()  # ❌ NOT AVAILABLE
  └── Fallback: _calculate_sharpe_ratio_fallback() (line 181-182)
  ↓
_calculate_sharpe_ratio_fallback() (line 428-475)
  ├── Check: equity_curve.index is DatetimeIndex?  # ❌ FALSE
  ├── freq = pd.infer_freq(equity_curve.index)  # ❌ Returns None
  └── Default: annualization_factor = sqrt(252)  # ❌ WRONG (assumes daily)
  ↓
Result: Sharpe 3.943-5.495 ❌ 3-5x OVERESTIMATED
```

### Root Causes

#### 1. Architectural Issue (PRIMARY)
**Location**: `src/evolution/population_manager.py` lines 278-334

**Problem**: PopulationManager doesn't use the template's real backtest functionality
```python
def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
    # Step 1: Run backtest (placeholder - will use autonomous_loop)
    backtest_result = self._run_placeholder_backtest(strategy)  # ❌ WRONG!
    # Should be: template.generate_strategy(strategy.parameters)
```

**Why It's Wrong**:
- Placeholder creates synthetic equity_curve without proper datetime handling
- Bypasses finlab's built-in metrics calculations
- Not using the template's actual backtest logic

#### 2. Missing DatetimeIndex (SECONDARY)
**Location**: `src/evolution/population_manager.py` lines 336-365

**Problem**: Placeholder backtest doesn't create DatetimeIndex
```python
def _run_placeholder_backtest(self, strategy: Strategy) -> BacktestResult:
    days = 100
    daily_returns = np.random.normal(0.001, 0.02, days)
    equity_curve = pd.Series((1 + daily_returns).cumprod(), name='equity')  # ❌ No index!
```

**Should Be**:
```python
dates = pd.date_range('2024-01-01', periods=days, freq='D')
equity_curve = pd.Series((1 + daily_returns).cumprod(), index=dates, name='equity')
```

#### 3. Fallback Triggered Incorrectly (CONSEQUENCE)
**Location**: `src/backtest/metrics.py` lines 175-182

**Problem**: System falls back to manual calculation when finlab should be available
```python
try:
    sharpe_ratio = finlab_metrics.sharpe_ratio(equity_curve)  # ❌ Fails for placeholder
except Exception as e:
    sharpe_ratio = _calculate_sharpe_ratio_fallback(equity_curve)  # ❌ Wrong assumptions
```

**Why It Fails**:
- Placeholder equity_curve doesn't match finlab's expected format
- finlab.report.metrics unavailable for synthetic data
- Should never fall back if using real finlab backtest

---

## Solution

### Option 1: Use Template's Real Backtest (RECOMMENDED) ⭐

**Change**: Make PopulationManager call the actual template's generate_strategy() method

**Implementation**:
```python
# src/evolution/population_manager.py

def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
    try:
        # Step 1: Get template from registry
        from src.utils.template_registry import TemplateRegistry
        registry = TemplateRegistry()
        template = registry.get_template(strategy.template_type)

        # Step 2: Run REAL backtest using template
        report, metadata = template.generate_strategy(strategy.parameters)

        # Step 3: Extract metrics directly from finlab report
        return MultiObjectiveMetrics(
            sharpe_ratio=report.metrics.sharpe_ratio(),  # ✅ Use finlab directly
            calmar_ratio=report.metrics.annual_return() / abs(report.metrics.max_drawdown()) if report.metrics.max_drawdown() != 0 else 0.0,
            max_drawdown=report.metrics.max_drawdown(),
            total_return=(report.equity_curve.iloc[-1] - 1.0) if len(report.equity_curve) > 0 else 0.0,
            win_rate=0.0,  # Calculate from trade_records if needed
            annual_return=report.metrics.annual_return(),
            success=True
        )
```

**Benefits**:
- ✅ Uses finlab's battle-tested backtest engine
- ✅ Correct Sharpe calculation (no fallback needed)
- ✅ Consistent with initial population evaluation
- ✅ Supports all template types (Turtle, Mastiff, Momentum, Combination)
- ✅ No hard-coded assumptions

**Risks**:
- ⚠️ Slower than placeholder (real backtest takes longer)
- ⚠️ Requires finlab API token
- ⚠️ Network-dependent

### Option 2: Fix Placeholder DatetimeIndex (NOT RECOMMENDED)

**Change**: Add DatetimeIndex to placeholder backtest

**Implementation**:
```python
def _run_placeholder_backtest(self, strategy: Strategy) -> BacktestResult:
    days = 100
    daily_returns = np.random.normal(0.001, 0.02, days)

    # FIX: Add DatetimeIndex
    dates = pd.date_range('2024-01-01', periods=days, freq='D')
    equity_curve = pd.Series((1 + daily_returns).cumprod(), index=dates, name='equity')
```

**Why NOT Recommended**:
- ❌ Still doesn't use real backtest logic
- ❌ Synthetic data doesn't match production use case
- ❌ User's concern remains: "Should use finlab's backtest functionality"
- ❌ Only fixes symptom, not root cause

---

## User's Concern Validated

**User Question**: "但主要的回測核心不應該是用finlab 的回測功能嗎？"
(Shouldn't the core backtesting use finlab's backtest functionality?)

**Answer**: **YES! You are absolutely correct!**

The system architecture should use finlab's backtest.sim() throughout:
1. Initial population ✅ Already uses finlab
2. Evolution phase ❌ Currently uses placeholder (WRONG)
3. Final validation ✅ Already uses finlab

**Correct Architecture**:
```
All Backtest Operations
  ↓
Template.generate_strategy()
  ↓
finlab.backtest.sim()
  ↓
finlab.report.metrics
  ↓
Consistent, correct results everywhere
```

---

## Impact Assessment

### Performance Metrics Correction

**Before (INVALID)**:
- Best Sharpe: 6.296 → 5.495 (after partial fix)
- Mean Sharpe: 5.975 → 5.440
- Range: [5.654, 6.296] → [5.386, 5.495]

**Expected After Full Fix**:
- Best Sharpe: ~1.3-1.4 (monthly) or ~2.5-2.9 (weekly)
- Mean Sharpe: ~1.2-1.3 (monthly) or ~2.3-2.7 (weekly)
- Range: [1.0-1.4] (monthly) or [2.0-3.0] (weekly)

### Decision Gate Impact

**Current (Invalid)**: Sharpe 6.296 → Scenario A (combination sufficient)

**Corrected (Expected)**:
- If monthly data: Sharpe ~1.37 → **Scenario B** (combination insufficient, proceed to structural mutation)
- If weekly data: Sharpe ~2.86 → **Scenario A** (combination sufficient, optimize further)

**Most Likely**: Monthly data → Scenario B (1.37 < 2.5 threshold)

---

## Next Steps

### Immediate Actions

1. ✅ **Complete Task 1**: Root cause identified
2. 🔄 **Task 2**: Implement Option 1 (use template's real backtest)
3. ⏳ **Task 3**: Add DatetimeIndex fallback (safety net only)
4. ⏳ **Task 4**: Add unit tests for different data frequencies
5. ⏳ **Task 5**: Re-run validation with corrected implementation

### Implementation Plan

**File Changes Required**:
1. **src/evolution/population_manager.py** (_evaluate_strategy method)
   - Remove _run_placeholder_backtest() call
   - Add template.generate_strategy() call
   - Extract metrics directly from finlab report

2. **src/backtest/metrics.py** (_calculate_sharpe_ratio_fallback)
   - Keep DatetimeIndex fix as fallback safety
   - Add warning log when fallback is triggered

3. **tests/backtest/test_metrics.py** (NEW)
   - Test Sharpe calculation with monthly data
   - Test Sharpe calculation with weekly data
   - Test Sharpe calculation with daily data
   - Test fallback with non-datetime index

4. **run_combination_smoke_test.py**
   - No changes needed (uses PopulationManager correctly)

### Validation Criteria

✅ **Fix Complete When**:
1. Initial population Sharpe matches evolution Sharpe (1.0-1.4 range)
2. No "finlab.report.metrics not available" warnings
3. All unit tests pass
4. 20-generation validation shows consistent Sharpe values
5. No sudden jumps between generations

---

## Files Involved

### Analysis Files
- `SHARPE_CALCULATION_BUG_ANALYSIS.md` - Initial bug analysis
- `ROOT_CAUSE_IDENTIFIED.md` - This file (detailed root cause)

### Source Files
- `src/evolution/population_manager.py` - Primary fix location
- `src/backtest/metrics.py` - Fallback safety net
- `src/templates/combination_template.py` - Reference implementation (already correct)

### Test Files
- `run_combination_smoke_test.py` - Integration test harness
- `tests/backtest/test_metrics.py` - Unit tests (TO BE CREATED)

### Results
- `COMBINATION_VALIDATION_PHASE15.md` - Invalid results (Sharpe 6.296)
- `COMBINATION_VALIDATION_PHASE15_CORRECTED.md` - Still invalid (Sharpe 5.495)
- `COMBINATION_VALIDATION_PHASE15_FINAL.md` - Awaiting correct results (~1.3-1.4)

---

**End of Root Cause Analysis**
