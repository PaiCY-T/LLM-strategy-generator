# Sharpe Ratio Calculation Bug - Analysis and Fix

**Date**: 2025-10-20
**Status**: 🐛 **BUG IDENTIFIED AND FIXED**
**Severity**: ⚠️ **CRITICAL** - Performance metrics grossly overstated

---

## Executive Summary

Phase 1.5 validation reported **Sharpe 6.296**, which was identified as unrealistic. Root cause analysis revealed that the **Sharpe ratio fallback calculation incorrectly assumed daily data frequency**, leading to **4.58x overestimation** for monthly data.

### Impact

- **Reported Results**: Sharpe 6.296 (❌ INVALID)
- **Corrected Results**: Sharpe ~1.37 (monthly) or ~2.86 (weekly)
- **Decision Gate**: Previously triggered Scenario A (>2.5), may change after correction

---

## Problem Description

### Observed Symptoms

1. **Unrealistically High Sharpe Ratio**: 6.296 far exceeds typical trading strategy performance
2. **Initialization vs Evolution Discrepancy**:
   - Initial population: Sharpe 1.068-1.376 ✅ (reasonable)
   - After evolution: Sharpe 4.929-6.296 ❌ (unreasonable)

### Root Cause

**Two different Sharpe ratio calculation methods**:

#### 1. Initial Population (CORRECT)
**File**: `src/templates/combination_template.py:495`
```python
sharpe_ratio = report.metrics.sharpe_ratio()  # Uses finlab metrics
```
- Uses finlab's built-in metrics
- Correctly accounts for data frequency
- Results: Sharpe 1.068-1.376 ✅

#### 2. Evolution Phase (INCORRECT)
**File**: `src/backtest/metrics.py:448` (before fix)
```python
sharpe = (mean_return / std_return) * np.sqrt(252)  # Assumes daily data
```
- Fallback calculation triggered when `finlab.report.metrics` unavailable
- **Hard-coded `sqrt(252)` assumes daily data**
- Actual data: Monthly ('ME') or Weekly ('W-FRI')
- Results: Sharpe 4.929-6.296 ❌ (4.58x overstated)

### Mathematical Error

**Sharpe Ratio Annualization**:
```
Sharpe = (Mean Return / Std Return) × sqrt(Periods per Year)
```

**Annualization Factors**:
- Daily data: `sqrt(252)` = 15.87
- Weekly data: `sqrt(52)` = 7.21
- Monthly data: `sqrt(12)` = 3.46

**Error Magnitude**:
```
sqrt(252) / sqrt(12) = 4.58x  (daily vs monthly)
sqrt(252) / sqrt(52) = 2.20x  (daily vs weekly)
```

### Example Calculation

**Hypothetical Strategy**:
- Mean monthly return: 1%
- Std monthly return: 5%
- **Correct** Sharpe (monthly): (0.01 / 0.05) × sqrt(12) = **0.69**
- **Incorrect** Sharpe (assuming daily): (0.01 / 0.05) × sqrt(252) = **3.17**

**Error**: 3.17 / 0.69 = 4.59x overstatement

---

## Evidence

### Log Analysis

**Initial Population** (lines 16-35 of `combination_validation.log`):
```
Strategy 1: weights=[0.5, 0.5], sharpe=1.068
Strategy 4: weights=[0.8, 0.2], sharpe=1.245
Strategy 9: weights=[0.8, 0.2], sharpe=1.376
...
```
✅ Values are reasonable

**Generation 1** (lines 44-100):
```
WARNING - finlab.report.metrics not available, using fallback calculations
...
Best Sharpe: 4.892
```
❌ Fallback used, value inflated

**Generation 4+**:
```
Best Sharpe: 6.296
```
❌ Value continues to be inflated

### Validation Reports

**COMBINATION_VALIDATION_PHASE15.md**:
```
Best Sharpe:    6.296
Mean Sharpe:    5.975
Range:          [5.654, 6.296]
```
❌ All values unrealistic

---

## Fix Implementation

### Code Changes

**File**: `src/backtest/metrics.py`
**Function**: `_calculate_sharpe_ratio_fallback()`

**BEFORE** (lines 428-450):
```python
def _calculate_sharpe_ratio_fallback(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2:
        return 0.0

    returns = equity_curve.pct_change().dropna()

    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    # Annualized Sharpe (assuming daily returns)
    mean_return = float(returns.mean())
    std_return = float(returns.std())
    sharpe = (mean_return / std_return) * np.sqrt(252)  # ❌ WRONG

    return float(sharpe)
```

**AFTER** (lines 428-475):
```python
def _calculate_sharpe_ratio_fallback(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2:
        return 0.0

    returns = equity_curve.pct_change().dropna()

    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    # Infer data frequency and use correct annualization factor ✅
    if isinstance(equity_curve.index, pd.DatetimeIndex):
        freq = pd.infer_freq(equity_curve.index)
        if freq is None:
            # Try to infer from first few periods
            if len(equity_curve) >= 2:
                days_diff = (equity_curve.index[1] - equity_curve.index[0]).days
                if days_diff >= 25:  # Monthly (~30 days)
                    annualization_factor = np.sqrt(12)
                elif days_diff >= 5:  # Weekly (~7 days)
                    annualization_factor = np.sqrt(52)
                else:  # Daily
                    annualization_factor = np.sqrt(252)
            else:
                annualization_factor = np.sqrt(252)  # Default
        elif 'M' in freq or 'ME' in freq:  # Monthly
            annualization_factor = np.sqrt(12)
        elif 'W' in freq:  # Weekly
            annualization_factor = np.sqrt(52)
        else:  # Daily or other
            annualization_factor = np.sqrt(252)
    else:
        # Non-datetime index, default to daily
        annualization_factor = np.sqrt(252)

    # Annualized Sharpe ratio ✅
    mean_return = float(returns.mean())
    std_return = float(returns.std())
    sharpe = (mean_return / std_return) * annualization_factor

    return float(sharpe)
```

### Fix Logic

1. **Check if index is DatetimeIndex**
2. **Infer frequency** using `pd.infer_freq()`
3. **Fallback to manual detection** if inference fails:
   - Days between periods ≥25 → Monthly (sqrt(12))
   - Days between periods ≥5 → Weekly (sqrt(52))
   - Otherwise → Daily (sqrt(252))
4. **Select appropriate annualization factor** based on frequency
5. **Calculate Sharpe** with correct factor

---

## Expected Corrected Results

### Scenario 1: Monthly Data (Most Likely)

**Reported Sharpe**: 6.296
**Correction Factor**: 4.58x
**Corrected Sharpe**: **6.296 / 4.58 ≈ 1.37**

**Analysis**:
- Sharpe 1.37 is reasonable for monthly rebalancing
- Comparable to Turtle baseline (1.5-2.5)
- **Decision Gate**: ❌ FAILS (1.37 < 2.5 threshold)
- **Outcome**: Scenario B (proceed to structural mutation)

### Scenario 2: Weekly Data (Less Likely)

**Reported Sharpe**: 6.296
**Correction Factor**: 2.20x
**Corrected Sharpe**: **6.296 / 2.20 ≈ 2.86**

**Analysis**:
- Sharpe 2.86 is good for weekly rebalancing
- Slightly above Decision Gate threshold
- **Decision Gate**: ✅ PASSES (2.86 > 2.5 threshold)
- **Outcome**: Scenario A (template combination sufficient)

---

## Validation Plan

### Re-run Tests

**Command**:
```bash
python3 run_combination_smoke_test.py \
  --population-size 20 \
  --generations 20 \
  --output COMBINATION_VALIDATION_PHASE15_CORRECTED.md \
  --checkpoint-dir combination_validation_checkpoints
```

**Expected Results**:
- Initial population Sharpe: 1.068-1.376 (unchanged)
- Evolution Sharpe: **1.2-1.6** (monthly) or **2.5-3.5** (weekly)
- Consistent values throughout evolution

### Validation Criteria

✅ **PASS** if:
1. Initial population Sharpe matches previous run (1.068-1.376)
2. Evolution Sharpe stays within same range as initial
3. No sudden 3-4x jumps in Sharpe values
4. Final Sharpe is realistic (<3.0)

❌ **FAIL** if:
1. Sharpe values still >5.0
2. Large discrepancy between initial and evolution
3. Values don't match expected correction

---

## Impact on Phase 1.5 Decision Gate

### Previous (Incorrect) Conclusion

**Sharpe 6.296** → Scenario A: Template combination sufficient

**Actions**:
- ✅ Optimize combinations
- ❌ NO structural mutation needed

### Revised (Pending Correct Results)

**Scenario A** (Sharpe >2.5 after correction):
- Continue with template optimization
- End Phase 1.5

**Scenario B** (Sharpe ≤2.5 after correction):
- **Proceed to structural mutation**
- Document learnings from Phase 1.5
- 6-8 week implementation as originally planned

**Most Likely**: Scenario B (monthly data → Sharpe ~1.37)

---

## Lessons Learned

### What Went Wrong

1. **Fallback Assumptions Not Validated**:
   - Hard-coded sqrt(252) without checking data frequency
   - No unit tests for fallback calculations

2. **Lack of Sanity Checks**:
   - No automated validation that Sharpe values are reasonable
   - No comparison between finlab and fallback results

3. **Insufficient Logging**:
   - Fallback triggered but not clearly flagged as potential issue
   - No logging of annualization factor used

### Improvements Needed

1. **Add Unit Tests**:
   ```python
   def test_sharpe_ratio_fallback_monthly():
       # Test with monthly data
       dates = pd.date_range('2020-01-01', periods=12, freq='ME')
       equity = pd.Series([100, 102, 104, ...], index=dates)
       sharpe = _calculate_sharpe_ratio_fallback(equity)
       assert sharpe < 3.0  # Sanity check
   ```

2. **Add Sanity Check Warnings**:
   ```python
   if sharpe > 5.0:
       logger.warning(f"Unusually high Sharpe ratio: {sharpe:.2f}")
   ```

3. **Log Annualization Factor**:
   ```python
   logger.debug(f"Using annualization factor: {annualization_factor:.2f}")
   ```

4. **Compare finlab vs fallback**:
   - When both available, log discrepancy
   - Alert if difference >20%

---

## Next Steps

1. ✅ **Code fix applied** (`src/backtest/metrics.py`)
2. 🔄 **Re-running validation test** (in progress)
3. ⏳ **Awaiting corrected results**
4. ⏳ **Update Phase 1.5 conclusion** based on correct Sharpe
5. ⏳ **Decide on Scenario A vs B**
6. ⏳ **Update documentation** (STATUS.md, COMPLETION_SUMMARY.md)

---

## References

- **Bug Location**: `src/backtest/metrics.py:428-450` (before fix)
- **Fix Location**: `src/backtest/metrics.py:428-475` (after fix)
- **Test Script**: `run_combination_smoke_test.py`
- **Validation Results**: `COMBINATION_VALIDATION_PHASE15_CORRECTED.md` (pending)
- **Original (Incorrect) Results**: `COMBINATION_VALIDATION_PHASE15.md`

---

**End of Bug Analysis**
