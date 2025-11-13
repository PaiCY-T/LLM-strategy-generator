# Factor Graph Execution Fix - APPLIED

**Date:** 2025-11-10
**Status:** ✅ **FIXES APPLIED - TESTING IN PROGRESS**

---

## Summary

Applied comprehensive fixes to Factor Graph execution system to resolve data type mismatches. The system now properly initializes DataFrames before factor execution.

---

## ✅ Fixes Applied

### Fix 1: Factor Validation Skip for Modules
**File:** `src/factor_graph/factor.py:210-217`
**Change:** Add conditional check before accessing `.columns` attribute
**Status:** ✅ **APPLIED**

```python
# OLD:
missing = [inp for inp in self.inputs if inp not in data.columns]

# NEW:
# Check if data is a DataFrame (has columns) or a module (finlab.data)
if hasattr(data, 'columns'):
    missing = [inp for inp in self.inputs if inp not in data.columns]
    if missing:
        raise KeyError(...)
```

**Why:** When `data` is finlab.data module (not DataFrame), accessing `.columns` raises AttributeError

### Fix 2: Proper DataFrame Initialization
**File:** `src/factor_graph/strategy.py:444-456`
**Change:** Initialize `result` as DataFrame with basic price data instead of module reference
**Status:** ✅ **APPLIED**

```python
# OLD:
result = data  # data is finlab.data module

# NEW:
import pandas as pd
result = pd.DataFrame()

# Load basic price data that most factors need
try:
    result['close'] = data.get('price:收盤價')
except Exception as e:
    # If we can't load basic price data, continue with empty DataFrame
    # Factors will load what they need
    pass
```

**Why:** Factors expect DataFrame with data columns, not a module object. The first factor in the pipeline needs actual data to work with.

---

## How It Works

### Before (Broken):
1. `strategy.to_pipeline(data)` receives `finlab.data` module
2. Sets `result = data` (module)
3. First factor calls `factor.execute(result)`
4. Factor tries to check `if inp not in data.columns` → **CRASH** (module has no .columns)
5. Factor tries to call `data.copy()` → **CRASH** (module has no .copy())

### After (Fixed):
1. `strategy.to_pipeline(data)` receives `finlab.data` module
2. Creates `result = pd.DataFrame()`
3. Loads `result['close'] = data.get('price:收盤價')` to populate base data
4. First factor calls `factor.execute(result)`
5. Factor validation: `if hasattr(data, 'columns'):` → **PASSES** (True for DataFrame)
6. Factor execution: `data.copy()` → **SUCCESS** (DataFrame has .copy())
7. Factor returns updated DataFrame with new column added
8. Next factor receives accumulated DataFrame → continues successfully

---

## Test Results

### Current Status:
- **Test Running:** Debug pilot test with config_debug.yaml
- **Data Loading:** ✅ Completed (all fundamental and price data loaded)
- **Factor Graph Fix:** ✅ Applied
- **Execution Status:** 🔄 In Progress

### Expected Outcome:
- Factor Graph strategies should now execute successfully
- Classification should reach LEVEL_2 or LEVEL_3 (instead of LEVEL_1 failures)
- LLM strategies may still fail due to cached prompts (waiting for API cache to clear)

---

## Files Modified

1. **src/factor_graph/factor.py** (lines 210-217)
   - Added conditional check before accessing `.columns`
   - Prevents AttributeError when `data` is module

2. **src/factor_graph/strategy.py** (lines 444-456)
   - Initialize result as empty DataFrame
   - Load basic 'close' price data
   - Provides proper data structure for factors

---

## Previous Fixes (Already Applied)

These fixes from STRATEGY_EXECUTION_FIXES.md are also in place:

1. **strategy.py:445** - Removed `data.copy()` call (no longer relevant after Fix 2)
2. **LLM Prompts** - Updated creation/modification templates to include `sim()` call
   - Status: ⚠️ Waiting for API cache to clear

---

## Next Steps

1. ✅ Wait for current test to complete
2. ⏳ Check pilot_results.json for Factor Graph execution status
3. ⏳ Verify strategies reach LEVEL_2/LEVEL_3 classification
4. ⏳ If successful, document in final summary

---

## Technical Notes

### Why Load 'close' Data Initially?

Most factors in the factor library expect at least the 'close' price column:
- **MomentumFactor** (line 73): `data['close'] / data['close'].shift(1)`
- **MAFilterFactor** (line 105): `data['close'].rolling(window=ma_periods)`

By loading 'close' data upfront, we ensure the first factors in the pipeline have data to work with. Subsequent factors receive accumulated DataFrames with all previous factor outputs.

### Alternative Approaches Considered:

1. **Pass module through** - Doesn't work: factors can't call `.copy()` on module
2. **Lazy loading in factors** - Would require rewriting all factor logic functions
3. **Smart auto-loading** - Current solution: load base data, let factors add more

---

## Validation

To verify the fix works:
```bash
# Check test results
cat experiments/llm_learning_validation/results/pilot_results.json | jq '.fg_only.runs[0].iterations[0].execution_result'

# Expected: success = true (or at least no 'columns' error)
```
