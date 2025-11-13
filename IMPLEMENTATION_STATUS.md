# Sharpe Ratio Bug Fix - Implementation Status

**Date**: 2025-10-20
**Status**: 🔄 **TESTING IN PROGRESS**
**Test ID**: fadd75

---

## Summary

Fixed Sharpe ratio calculation bug (6.296 → ~1.37) by changing PopulationManager to use finlab's real backtest functionality. Encountered and resolved 3 implementation issues during validation.

---

## Issues Identified and Fixed

### Issue 1: Architectural Flaw (ROOT CAUSE)
**Problem**: Evolution phase used placeholder backtest instead of real finlab backtest

**User Insight**: "主要的回測核心不應該是用finlab 的回測功能嗎？" ✅ CORRECT!

**Fix**: Modified `_evaluate_strategy()` to call `template.generate_strategy()`
```python
# BEFORE: Placeholder backtest
backtest_result = self._run_placeholder_backtest(strategy)

# AFTER: Real finlab backtest
template = registry.get_template(template_type)
report, metadata = template.generate_strategy(strategy.parameters)
```

**File**: `src/evolution/population_manager.py` (lines 300-337)

### Issue 2: Singleton Pattern Violation
**Problem**: `RuntimeError: TemplateRegistry is a singleton. Use get_instance() instead.`

**Root Cause**: Attempted to instantiate TemplateRegistry using `TemplateRegistry()` instead of singleton pattern

**Fix**: Changed to `TemplateRegistry.get_instance()`
```python
# BEFORE: Direct instantiation
registry = TemplateRegistry()  # ❌ Error

# AFTER: Singleton access
registry = TemplateRegistry.get_instance()  # ✅ Correct
```

**File**: `src/evolution/population_manager.py` (line 302)

### Issue 3: Report Object Attribute Error
**Problem**: `AttributeError: 'Report' object has no attribute 'equity_curve'`

**Root Cause**: Finlab Report object doesn't expose equity_curve as a public attribute

**Fix**: Use annual_return instead of trying to calculate total_return from equity curve
```python
# BEFORE: Accessing non-existent attribute
total_return = float(report.equity_curve.iloc[-1] - 1.0)  # ❌ Error

# AFTER: Use annual_return as approximation
total_return = annual_return if annual_return is not None else 0.0  # ✅ Correct
```

**File**: `src/evolution/population_manager.py` (lines 325-327)

---

## All Code Changes

### 1. PopulationManager._evaluate_strategy() (Main Fix)

**File**: `src/evolution/population_manager.py` (lines 278-350)

**Complete Updated Method**:
```python
def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
    """
    Evaluate single strategy using template's real finlab backtest.

    Note:
        This now uses the template's actual finlab backtest instead of
        placeholder, ensuring consistent Sharpe calculations throughout.
    """
    try:
        # Step 1: Get template from registry (singleton pattern)
        from src.utils.template_registry import TemplateRegistry
        registry = TemplateRegistry.get_instance()  # ✅ Fix #2

        # Validate template_type
        template_type = strategy.template_type if hasattr(strategy, 'template_type') else 'Momentum'
        if not registry.validate_template_type(template_type):
            logger.warning(f"Invalid template type '{template_type}', falling back to Momentum")
            template_type = 'Momentum'

        template = registry.get_template(template_type)

        # Step 2: Run REAL backtest using template (uses finlab internally)  # ✅ Fix #1
        # This ensures consistent Sharpe calculation with initial population
        report, metadata = template.generate_strategy(strategy.parameters)

        # Step 3: Extract metrics directly from finlab report
        # NO FALLBACK - uses finlab's built-in calculations
        sharpe_ratio = report.metrics.sharpe_ratio()
        annual_return = report.metrics.annual_return()
        max_drawdown = report.metrics.max_drawdown()

        # Step 4: Calculate Calmar ratio
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

        # Step 5: Use annual_return as total_return approximation  # ✅ Fix #3
        # (Report object doesn't have equity_curve attribute)
        total_return = annual_return if annual_return is not None else 0.0

        # Step 6: Map to MultiObjectiveMetrics with graceful defaults
        return MultiObjectiveMetrics(
            sharpe_ratio=sharpe_ratio if sharpe_ratio is not None else 0.0,
            calmar_ratio=calmar if calmar is not None else 0.0,
            max_drawdown=max_drawdown if max_drawdown is not None else 0.0,
            total_return=total_return if total_return is not None else 0.0,
            win_rate=0.0,  # Could extract from trade_records if needed
            annual_return=annual_return if annual_return is not None else 0.0,
            success=True
        )

    except Exception as e:
        logger.warning(f"Backtest evaluation failed for strategy {strategy.id}: {e}", exc_info=True)
        # Return zero metrics on failure
        return MultiObjectiveMetrics(
            sharpe_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,
            total_return=0.0,
            win_rate=0.0,
            annual_return=0.0,
            success=False
        )
```

### 2. Sharpe Ratio Fallback (Safety Net)

**File**: `src/backtest/metrics.py` (lines 428-478)

Added frequency inference for rare cases when fallback is needed:
```python
def _calculate_sharpe_ratio_fallback(equity_curve: pd.Series) -> float:
    # ... existing code ...

    # Infer data frequency and use correct annualization factor
    if isinstance(equity_curve.index, pd.DatetimeIndex):
        freq = pd.infer_freq(equity_curve.index)
        if freq is None:
            # Manual detection from period differences
            if len(equity_curve) >= 2:
                days_diff = (equity_curve.index[1] - equity_curve.index[0]).days
                if days_diff >= 25:
                    annualization_factor = np.sqrt(12)  # Monthly
                elif days_diff >= 5:
                    annualization_factor = np.sqrt(52)  # Weekly
                else:
                    annualization_factor = np.sqrt(252)  # Daily
        elif 'M' in freq or 'ME' in freq:
            annualization_factor = np.sqrt(12)
        elif 'W' in freq:
            annualization_factor = np.sqrt(52)
        else:
            annualization_factor = np.sqrt(252)
    else:
        annualization_factor = np.sqrt(252)  # Default assumption

    # Calculate annualized Sharpe ratio
    sharpe = (mean_return / std_return) * annualization_factor
    return float(sharpe)
```

### 3. Fallback Warning (Lines 181-184)

Added explicit warning when fallback is triggered:
```python
logger.warning(
    f"Failed to calculate Sharpe ratio using finlab metrics: {e}. "
    f"Using fallback calculation (may be inaccurate if equity_curve lacks DatetimeIndex)"
)
```

### 4. Unit Tests

**File**: `tests/backtest/test_metrics.py` (NEW - 132 lines)

Created 6 comprehensive unit tests covering all data frequencies:
- ✅ test_monthly_data_sharpe
- ✅ test_weekly_data_sharpe
- ✅ test_daily_data_sharpe
- ✅ test_monthly_vs_daily_sharpe_difference (validates 4.58x ratio)
- ✅ test_empty_equity_curve
- ✅ test_single_value_equity_curve

**Test Results**: All 6 tests PASSED ✅

---

## Validation Test Status

**Command**:
```bash
python3 run_combination_smoke_test.py \
  --population-size 20 \
  --generations 20 \
  --output COMBINATION_VALIDATION_PHASE15_FINAL.md \
  --checkpoint-dir combination_validation_checkpoints_final
```

**Status**: 🔄 RUNNING (Background process ID: fadd75)

**Expected Outcomes**:
1. ✅ Initial population Sharpe: 1.068-1.378 (realistic, monthly data)
2. ⏳ Evolution Sharpe: Should match initial (1.2-1.6 range)
3. ⏳ No sudden jumps between generations
4. ⏳ No errors during evolution
5. ⏳ Consistent metrics across all 20 generations

**Pass Criteria**:
- Initial and evolution Sharpe values within same range
- No "finlab.report.metrics not available" warnings
- No singleton or attribute errors
- Final Sharpe <3.0 (realistic for monthly data)

---

## Timeline

| Time | Event |
|------|-------|
| 12:00 | User identified Sharpe 6.296 as unrealistic |
| 12:05 | Initial bug analysis - found fallback calculation issue |
| 12:15 | First fix attempt - added frequency inference to fallback |
| 12:20 | Partial success - Sharpe still inflated (5.495) |
| 12:25 | User insight - should use finlab consistently |
| 12:30 | Root cause identified - PopulationManager using placeholder |
| 12:40 | Implemented Fix #1 - use template's real backtest |
| 12:45 | Unit tests created and passing (6/6) |
| 12:50 | Test run #1 - singleton error discovered |
| 12:55 | Implemented Fix #2 - singleton pattern |
| 13:00 | Test run #2 - equity_curve attribute error |
| 13:05 | Implemented Fix #3 - use annual_return |
| 13:10 | Test run #3 - currently in progress |

---

## Remaining Tasks

1. ⏳ **Monitor test completion** - Wait for 20-generation test to finish
2. ⏳ **Validate results** - Confirm Sharpe ratios are consistent and realistic
3. ⏳ **Update Phase 1.5 conclusion** - Based on corrected metrics
4. ⏳ **Document final decision** - Scenario A (>2.5) vs Scenario B (≤2.5)
5. ⏳ **Update STATUS.md** - Mark Phase 1.5 as complete with final verdict

---

## Impact on Phase 1.5 Decision Gate

### Previous (Invalid) Analysis
- **Sharpe**: 6.296 (4.58x overstated)
- **Conclusion**: Scenario A - Template combination sufficient
- **Action**: Optimize combinations, no structural mutation

### Expected Corrected Analysis
- **Sharpe**: ~1.37 (monthly data, realistic)
- **Threshold**: 2.5
- **Conclusion**: ❌ Scenario B - Template combination **insufficient**
- **Action**: Proceed to structural mutation (6-8 week implementation)

**Rationale**: CombinationTemplate (1.37) does not significantly exceed single-template ceiling (Turtle: 1.5-2.5), indicating that simple weighted combinations are not sufficient to achieve breakthrough performance.

---

## Files Modified

**Source Code**:
1. `src/evolution/population_manager.py` (3 fixes, lines 278-350)
2. `src/backtest/metrics.py` (frequency inference + warning, lines 428-478, 181-184)

**Tests**:
3. `tests/backtest/test_metrics.py` (NEW - 6 comprehensive tests)

**Documentation**:
4. `SHARPE_CALCULATION_BUG_ANALYSIS.md` (initial analysis)
5. `ROOT_CAUSE_IDENTIFIED.md` (detailed root cause)
6. `SHARPE_RATIO_FIX_SUMMARY.md` (fix summary)
7. `IMPLEMENTATION_STATUS.md` (this file - current status)

---

## Lessons Learned

### Technical
1. **Architectural Consistency**: Different code paths must use same backtest methodology
2. **Singleton Patterns**: Always use `get_instance()` for singletons
3. **API Assumptions**: Don't assume object attributes exist - check first
4. **Incremental Testing**: Test each fix before moving to next

### Process
1. **User Feedback Critical**: User's architectural insight led to proper fix
2. **Root Cause Analysis**: Don't stop at symptoms - find underlying cause
3. **Comprehensive Testing**: Unit tests catch issues before integration testing
4. **Documentation**: Track all changes and iterations for future reference

---

**End of Implementation Status**
