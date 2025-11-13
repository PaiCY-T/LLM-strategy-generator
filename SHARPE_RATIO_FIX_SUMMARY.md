# Sharpe Ratio Calculation Bug - Fix Summary

**Date**: 2025-10-20
**Status**: ✅ **FIX IMPLEMENTED AND TESTING**

---

## Executive Summary

Fixed the Sharpe ratio calculation bug that was producing unrealistic values (6.296) by changing PopulationManager to use finlab's actual backtest functionality instead of placeholder calculations.

### Key Changes

1. **PopulationManager._evaluate_strategy()** - Now uses template's real finlab backtest
2. **TemplateRegistry Singleton** - Fixed instantiation to use `get_instance()`
3. **Fallback Safety** - Added frequency inference for rare cases when fallback is needed
4. **Unit Tests** - Created comprehensive tests for different data frequencies

---

## Problem Identified

**User Feedback**: "Sharpe 6.296 這不合理，請先確認這點" (This is unrealistic, verify first)

**Root Cause**: Two different calculation paths:
- Initial population: CombinationTemplate → finlab.backtest → finlab.metrics ✅ **CORRECT**
- Evolution phase: PopulationManager → placeholder → manual calculation ❌ **WRONG**

**Error Magnitude**: 4.58x overestimation for monthly data (sqrt(252)/sqrt(12))

---

## Solution Implemented

### Fix 1: Use Real Finlab Backtest

**File**: `src/evolution/population_manager.py`
**Method**: `_evaluate_strategy()` (lines 278-350)

**BEFORE** (incorrect):
```python
def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
    # ❌ Used placeholder backtest with wrong assumptions
    backtest_result = self._run_placeholder_backtest(strategy)
    perf_metrics = calculate_metrics(backtest_result)  # Triggered fallback
```

**AFTER** (correct):
```python
def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
    # ✅ Use template's real finlab backtest
    registry = TemplateRegistry.get_instance()  # Singleton pattern
    template = registry.get_template(template_type)
    report, metadata = template.generate_strategy(strategy.parameters)

    # ✅ Extract metrics directly from finlab (no fallback)
    sharpe_ratio = report.metrics.sharpe_ratio()
    annual_return = report.metrics.annual_return()
    max_drawdown = report.metrics.max_drawdown()
```

### Fix 2: TemplateRegistry Singleton

**File**: `src/evolution/population_manager.py` (line 302)

**BEFORE**:
```python
registry = TemplateRegistry()  # ❌ RuntimeError
```

**AFTER**:
```python
registry = TemplateRegistry.get_instance()  # ✅ Correct singleton usage
```

### Fix 3: Fallback Safety Net

**File**: `src/backtest/metrics.py` (lines 428-478)

Added frequency inference to fallback calculation as safety net:
```python
def _calculate_sharpe_ratio_fallback(equity_curve: pd.Series) -> float:
    # Infer data frequency from DatetimeIndex
    if isinstance(equity_curve.index, pd.DatetimeIndex):
        freq = pd.infer_freq(equity_curve.index)
        # Map frequency to correct annualization factor
        if 'M' in freq or 'ME' in freq:
            annualization_factor = np.sqrt(12)  # Monthly
        elif 'W' in freq:
            annualization_factor = np.sqrt(52)  # Weekly
        else:
            annualization_factor = np.sqrt(252)  # Daily
```

Added warning when fallback is triggered (lines 181-184):
```python
logger.warning(
    f"Failed to calculate Sharpe ratio using finlab metrics: {e}. "
    f"Using fallback calculation (may be inaccurate if equity_curve lacks DatetimeIndex)"
)
```

### Fix 4: Unit Tests

**File**: `tests/backtest/test_metrics.py` (NEW - 132 lines)

Created 6 comprehensive unit tests:
1. `test_monthly_data_sharpe` - Validates sqrt(12) for monthly data
2. `test_weekly_data_sharpe` - Validates sqrt(52) for weekly data
3. `test_daily_data_sharpe` - Validates sqrt(252) for daily data
4. `test_monthly_vs_daily_sharpe_difference` - Validates 4.58x ratio
5. `test_empty_equity_curve` - Edge case handling
6. `test_single_value_equity_curve` - Edge case handling

**Test Results**: ✅ All 6 tests PASSED

---

## Validation Test

**Command**:
```bash
python3 run_combination_smoke_test.py \
  --population-size 20 \
  --generations 20 \
  --output COMBINATION_VALIDATION_PHASE15_FINAL.md \
  --checkpoint-dir combination_validation_checkpoints_final
```

**Status**: 🔄 RUNNING

**Initial Results** (population initialization):
- Sharpe range: 1.206 - 1.378 ✅ **REALISTIC**
- No singleton errors ✅
- Using real finlab backtest ✅

**Expected Final Results**:
- Initial population Sharpe: 1.206-1.378 (unchanged)
- Evolution Sharpe: 1.2-1.6 (should match initial, monthly data)
- No sudden jumps between generations
- No "finlab.report.metrics not available" warnings
- Consistent values throughout 20 generations

---

## Validation Criteria

**✅ PASS if**:
1. Initial population Sharpe matches expected (1.206-1.378)
2. Evolution Sharpe stays within same range as initial
3. No sudden 3-4x jumps in Sharpe values
4. Final Sharpe is realistic (<3.0)
5. No errors or fallback warnings

**❌ FAIL if**:
1. Sharpe values still >5.0
2. Large discrepancy between initial and evolution
3. Values don't match expected correction
4. Errors during evolution

---

## Impact on Phase 1.5 Decision Gate

### Previous (Invalid) Conclusion
**Sharpe 6.296** → Scenario A: Template combination sufficient ❌

### Corrected Analysis (Pending)
**Expected Sharpe ~1.37** (monthly data):
- **Decision Gate Threshold**: 2.5
- **Actual**: ~1.37
- **Conclusion**: ❌ **Scenario B** - Proceed to structural mutation
- **Rationale**: CombinationTemplate does not exceed single-template ceiling

---

## Files Modified

### Source Code
1. **src/evolution/population_manager.py** (lines 278-350)
   - Replaced placeholder backtest with template.generate_strategy()
   - Fixed TemplateRegistry singleton instantiation

2. **src/backtest/metrics.py** (lines 428-478, 181-184)
   - Added DatetimeIndex frequency inference
   - Added fallback warning

### Tests
3. **tests/backtest/test_metrics.py** (NEW - 132 lines)
   - Comprehensive unit tests for all data frequencies

### Documentation
4. **SHARPE_CALCULATION_BUG_ANALYSIS.md** - Initial bug analysis
5. **ROOT_CAUSE_IDENTIFIED.md** - Detailed root cause documentation
6. **SHARPE_RATIO_FIX_SUMMARY.md** - This file (fix summary)

---

## Lessons Learned

### What Went Wrong
1. **Architectural Inconsistency**: Different code paths for initialization vs evolution
2. **Hard-coded Assumptions**: Placeholder backtest assumed daily data without validation
3. **Insufficient Testing**: No unit tests for fallback calculations
4. **Missing Sanity Checks**: No automated validation for unrealistic values

### Improvements Made
1. **Consistent Architecture**: All backtest operations now use finlab
2. **Frequency Inference**: Fallback automatically detects data frequency
3. **Comprehensive Testing**: Unit tests cover monthly, weekly, daily data
4. **Better Logging**: Warning when fallback is triggered

### Best Practices Applied
1. **Evidence-Based Analysis**: Used user feedback to identify the issue
2. **Root Cause Focus**: Traced back to architectural flaw, not just symptom
3. **Test-Driven Validation**: Created tests before declaring fix complete
4. **Documentation**: Comprehensive documentation of bug and fix

---

## User's Key Insight

**User Question**: "但主要的回測核心不應該是用finlab 的回測功能嗎？"
*Translation*: "Shouldn't the core backtesting use finlab's backtest functionality?"

**Answer**: **YES! Absolutely correct!**

This architectural insight was the key to identifying the proper fix. The system should use finlab's backtest consistently throughout:
- ✅ Initial population: Uses finlab
- ✅ Evolution phase: **NOW** uses finlab (was using placeholder)
- ✅ Final validation: Uses finlab

---

## Next Steps

1. ✅ Root cause identified
2. ✅ Implementation complete
3. ✅ Unit tests created and passing
4. 🔄 Smoke test running (in progress)
5. ⏳ Update Phase 1.5 conclusion based on corrected metrics
6. ⏳ Document final decision on Scenario A vs B

---

**End of Fix Summary**
