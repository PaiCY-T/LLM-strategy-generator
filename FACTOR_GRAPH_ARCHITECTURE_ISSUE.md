# Factor Graph Architecture Issue - ROOT CAUSE IDENTIFIED

**Date:** 2025-11-10
**Status:** 🔍 **ARCHITECTURAL MISMATCH DISCOVERED**

---

## Root Cause

The Factor Graph system has an architectural mismatch between how it's being called and how the factors are implemented:

### The Problem:
1. **BacktestExecutor** calls `strategy.to_pipeline(data)` where `data = finlab.data` (the module)
2. **Strategy.to_pipeline()** passes this module to factors: `result = factor.execute(result)`
3. **Momentum factors** expect a DataFrame with a 'close' column: `data['close']`
4. **Module doesn't have 'close' column** → ❌ FAILS

### Code Evidence:

**momentum_factors.py:73**
```python
def _momentum_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    daily_returns = data['close'] / data['close'].shift(1) - 1  # ❌ Expects 'close' column
```

**backtest/executor.py:469**
```python
positions_df = strategy.to_pipeline(data)  # data is finlab.data module
```

---

## The Architectural Mismatch

### Design Assumption (Factors):
- Factors expect `data` to be a DataFrame with columns like 'close', 'volume', etc.
- Factors process this DataFrame and add new columns (e.g., 'momentum', 'ma_filter')
- Sequential processing: Each factor receives accumulated DataFrame from previous factors

### Actual Usage (System):
- System passes `finlab.data` **module** to factors
- Module has `.get()` method to retrieve data: `data.get('price:收盤價')`
- Module is NOT a DataFrame and doesn't have columns

---

## Attempted Fixes

### Fix Attempt 1: Load Data in strategy.py
```python
result = data.get('price:收盤價')
result = pd.DataFrame({'close': result})
```
**Result:** Failed - `data.get()` returns FinlabDataFrame (4563×2661 matrix), not a column

### Fix Attempt 2: Use FinlabDataFrame Directly
```python
result = data.get('price:收盤價')  # Use as-is
```
**Result:** Failed - FinlabDataFrame has symbol columns (0015, 0050, ...), not 'close' column

### Fix Attempt 3: Skip Validation for Modules
```python
if hasattr(data, 'columns'):  # Only validate DataFrames
    check columns...
```
**Result:** Partial - Validation passes but factor logic still fails at `data['close']`

---

## Why This Happened

The Factor Graph system was likely developed and tested with **pre-loaded DataFrames**, not with direct module passing. The integration with `BacktestExecutor` assumed factors could handle modules, but they can't.

---

## Solution Options

### Option A: Modify Factor Logic (Recommended for Long-term)
Rewrite factor logic functions to accept modules and call `.get()`:
```python
def _momentum_logic(data, parameters):
    if hasattr(data, 'get'):  # Module
        close = data.get('price:收盤價')
    else:  # DataFrame
        close = data['close']
    # Rest of logic...
```

**Pros:** Flexible, works with both modules and DataFrames
**Cons:** Requires rewriting all factor logic functions
**Effort:** High (affects multiple files)

### Option B: Pre-load Data in strategy.py (Quick Fix)
Load all required data upfront and create proper DataFrame:
```python
def to_pipeline(self, data):
    # Load all price data factors need
    close = data.get('price:收盤價')
    result = pd.DataFrame()

    # Create DataFrame with columns that match factor expectations
    # This requires knowing what each factor needs
    for symbol in close.columns:
        # Process per-symbol...
```

**Pros:** Factors work unchanged
**Cons:** Complex data reshaping, performance overhead
**Effort:** Medium

### Option C: Disable Factor Graph Temporarily
Focus on LLM strategy validation first, fix Factor Graph later:
```python
if generation_method == "factor_graph":
    skip  # Temporarily disabled
```

**Pros:** Unblocks LLM validation testing
**Cons:** Can't test Factor Graph vs LLM comparison
**Effort:** Low

---

## Current Status - FUNDAMENTAL ARCHITECTURAL INCOMPATIBILITY

**CRITICAL FINDING:**

The Factor Graph system has a fundamental data structure incompatibility with FinLab:

### FinLab Data Structure:
- Returns **Dates×Symbols matrices** (4563 dates × 2661 symbols)
- Each cell = value for (date, symbol) pair
- Example: `close['2024-01-01']['2330']` = stock 2330's close price on 2024-01-01

### Factor Graph Expectation:
- Expects **Observations×Features DataFrames**
- Each row = one observation (e.g., one stock)
- Each column = one feature (e.g., 'close', 'volume', 'momentum')
- Example: `df.loc['2330']['close']` = stock 2330's close price

### The Incompatibility:
1. Cannot assign 2D matrix to DataFrame column: `df['momentum'] = matrix(4563×2661)` → **ValueError**
2. Cannot chain factors with matrices: Each factor returns 4563×2661 matrix, but next factor expects accumulated columns
3. Factor inputs/outputs assume column-based features, not matrix-based time series

### Why All Fixes Failed:
1. **Module assignment**: Modules don't support `data['column'] = value`
2. **DataCache with DataFrame**: Cannot assign FinlabDataFrame (2D) to DataFrame column (1D)
3. **Return matrix directly**: Breaks factor chaining (next factor needs previous outputs as columns)

**CONCLUSION:** Factor Graph system requires complete redesign to work with FinLab's matrix format, OR data needs reshaping (expensive operation).

**RECOMMENDATION:** Disable Factor Graph strategies temporarily (Option C), focus on LLM validation, redesign Factor Graph in Phase 2.

---

## Files Affected

1. **src/factor_graph/strategy.py** - Entry point, receives module
2. **src/factor_graph/factor.py** - Executes individual factors
3. **src/factor_library/momentum_factors.py** - Logic expects DataFrame columns
4. **src/backtest/executor.py** - Calls to_pipeline with module

---

## Test Results

All 6 iterations reach LEVEL_1 (execution attempted) but fail with:
- **Factor Graph**: Various DataFrame/Module mismatch errors
- **LLM**: Missing `sim()` call (separate issue, prompt cache related)

---

## Next Steps

1. **Immediate:** Decide on solution option (A, B, or C)
2. **Short-term:** Implement chosen solution
3. **Long-term:** Design proper data flow architecture

**Time Estimate:** 15 minutes (Option C) to 6 hours (Option A)
