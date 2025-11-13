# Debug Test Results - All API Fixes Verified

**Date:** 2025-11-09
**Test Type:** 6-iteration debug test (2 per group)
**Status:** ✅ **ALL API FIXES WORKING**

---

## Test Configuration

- **FG_ONLY**: innovation_rate=0% (baseline, 100% Factor Graph)
- **HYBRID**: innovation_rate=30% (30% LLM, 70% Factor Graph)
- **LLM_ONLY**: innovation_rate=100% (100% LLM)

---

## ✅ Innovation Rate Logic Verification

### FG_ONLY Group (0% innovation_rate)
| Iteration | Random Value | Threshold | Decision | Method Used |
|-----------|--------------|-----------|----------|-------------|
| 0 | 55.44 | 0 | use_llm=False | factor_graph ✅ |
| 1 | 69.58 | 0 | use_llm=False | factor_graph ✅ |

**Result:** 2/2 Factor Graph (100%) ✅ **CORRECT**

### HYBRID Group (30% innovation_rate)
| Iteration | Random Value | Threshold | Decision | Method Used |
|-----------|--------------|-----------|----------|-------------|
| 0 | 77.33 | 30 | use_llm=False | factor_graph ✅ |
| 1 | 18.93 | 30 | use_llm=True | llm ✅ |

**Result:** 1/2 LLM (50%), 1/2 Factor Graph (50%) ✅ **CORRECT**
*Expected ~30% LLM usage - 50% is within statistical variance for small sample*

### LLM_ONLY Group (100% innovation_rate)
| Iteration | Random Value | Threshold | Decision | Method Used |
|-----------|--------------|-----------|----------|-------------|
| 0 | 56.35 | 100 | use_llm=True | llm ✅ |
| 1 | 9.08 | 100 | use_llm=True | llm ✅ |

**Result:** 2/2 LLM (100%) ✅ **CORRECT**

---

## ✅ LLM Generation Working

### HYBRID Group - Iteration 1 (LLM)
```python
def strategy(data):
    # Retrieve fundamental data: ROE, Revenue Growth Rate, P/E Ratio
    roe = data.get('fundamental_features:ROE稅後')
    revenue_growth = data.get('fundamental_features:營收成長率')
    pe_ratio = data.get('fundamental_features:本益比')
    ...
    return position
```
**Status:** ✅ LLM successfully generated 2,839 characters of strategy code

### LLM_ONLY Group - Both Iterations
- **Iteration 0:** Generated 2,493 chars of strategy code ✅
- **Iteration 1:** Generated 1,915 chars of strategy code ✅

**LLM API:** ✅ **WORKING** (OpenRouter + Gemini 2.5 Flash)

---

## ✅ All API Fixes Verified

| Fix | Status | Evidence |
|-----|--------|----------|
| 1. FactorCategory import | ✅ FIXED | No more `NameError: 'FactorCategory' is not defined` |
| 2. strategy_code attribute | ✅ FIXED | No more `'IterationRecord' object has no attribute 'code'` |
| 3. LLM response handling | ✅ FIXED | No more `'str' object has no attribute 'get'` |
| 4. Classification logic | ✅ FIXED | Proper LEVEL_1 classification (was LEVEL_0) |

---

## ⚠️ Strategy Execution Issues (Separate from API fixes)

### Issue 1: Factor Graph Template Error
```
AttributeError: module 'finlab.data' has no attribute 'copy'
Location: src/factor_graph/strategy.py:445
```

**Root Cause:** Template strategy calls `data.copy()` but `data` is a module, not a DataFrame.

**Impact:** All Factor Graph strategies fail at execution (LEVEL_1 classification)

**Note:** This is a **template design issue**, not an API mismatch. The template needs to be updated to properly handle the FinLab data object.

---

### Issue 2: LLM Strategy Missing sim() Call
```
ValueError: Strategy code did not create 'report' variable.
Ensure code calls sim() and assigns result to 'report'.
```

**Root Cause:** LLM generates `strategy()` function that returns positions, but doesn't call `sim()` to create backtest report.

**Impact:** All LLM-generated strategies fail at execution (LEVEL_1 classification)

**Note:** This is a **prompt engineering issue**, not an API mismatch. The LLM prompt needs to instruct the model to call `sim()`.

---

## Summary

### ✅ What's Working
1. **Innovation rate logic** - Correctly controls LLM vs Factor Graph split
2. **LLM API integration** - Successfully generates strategy code
3. **All 4 API fixes** - No more crashes from method signature mismatches
4. **Error classification** - Properly categorizes failures as LEVEL_1

### ⚠️ What Needs Fixing (Next Phase)
1. **Factor Graph template** - Fix `data.copy()` issue in strategy.py
2. **LLM prompt** - Add instruction to call `sim()` in generated code

### 📊 Test Metrics
- **Total Iterations:** 6 (2 per group)
- **API Crashes:** 0 ✅
- **LLM Generations:** 3/3 successful ✅
- **Factor Graph Generations:** 3/3 successful ✅
- **Strategy Executions:** 0/6 successful (template/prompt issues)

---

## Files Modified in This Session

1. **src/learning/iteration_executor.py**
   - Line 27: Added `FactorCategory` import
   - Lines 400, 404: Changed `rec.code` → `rec.strategy_code`
   - Lines 409-422: Fixed LLM response handling (string not dict)
   - Lines 795-826: Rewrote classification logic to use `classify_error()`

2. **Cache:** Cleared multiple times to ensure latest code runs

---

## Next Steps

1. **Fix Factor Graph template** (High Priority)
   - Investigate why `data.copy()` fails
   - Update template to use correct FinLab data API

2. **Fix LLM prompt** (High Priority)
   - Add explicit instruction to call `sim()`
   - Provide example of complete strategy with backtest

3. **Run full pilot test** (After fixes)
   - 300 iterations (100 per group)
   - Verify statistical distribution matches innovation_rate

---

## Conclusion

✅ **ALL API MISMATCHES FIXED**
✅ **INNOVATION RATE LOGIC WORKING**
✅ **LLM GENERATION WORKING**

The experiment infrastructure is now ready. The remaining issues (template execution, LLM prompt) are in the strategy generation layer, not the learning loop infrastructure.

**Status:** Ready for template/prompt fixes, then full pilot test 🚀
