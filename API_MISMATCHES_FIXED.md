# API Mismatch Fixes - Complete Report

**Date:** 2025-11-09
**Issue:** Pilot test appeared successful but all 300 iterations used Factor Graph instead of expected LLM/FG distribution

## Root Cause Summary

The original pilot test failure was caused by **multiple cascading API mismatches** that were silently falling back to Factor Graph generation. The innovation_rate logic was working correctly, but LLM generation was crashing due to incorrect method calls.

---

## Issues Found and Fixed

### 1. **Stale Python Bytecode Cache** ✅ FIXED
**Impact:** CRITICAL - Caused crashes during execution
**Symptom:** `AttributeError: 'InnovationEngine' object has no attribute 'generate_strategy'`

**Problem:**
Old `.pyc` cache files contained outdated method names from previous code versions.

**Fix:**
```bash
find LLM-strategy-generator/src -type d -name "__pycache__" -exec rm -rf {} +
```

**Files Affected:**
- All `__pycache__` directories under `LLM-strategy-generator/src/`

---

### 2. **InnovationEngine API Mismatch** ✅ FIXED
**Impact:** CRITICAL - Prevented LLM generation from working
**Symptom:** `TypeError: InnovationEngine.generate_innovation() missing 1 required positional argument: 'champion_metrics'`

**Problem:**
Incorrect method call at `iteration_executor.py:379`
```python
# WRONG:
response = engine.generate_innovation(feedback)

# CORRECT:
response = engine.generate_innovation(
    champion_code=champion_code,
    champion_metrics=champion_metrics,
    failure_history=failure_history,
    target_metric="sharpe_ratio"
)
```

**Fix Applied:**
Added champion retrieval and proper parameter passing in `iteration_executor.py:377-413`

**Files Modified:**
- `LLM-strategy-generator/src/learning/iteration_executor.py` (lines 371-418)

---

### 3. **Configuration Environment Variables Not Substituted** ✅ FIXED
**Impact:** HIGH - Prevented LLM API calls from working
**Symptom:** `ValueError: Timeout value connect was ${LLM_TIMEOUT:60}, but it must be an int, float or None.`

**Problem:**
Environment variable placeholders like `${LLM_TIMEOUT:60}` were not being substituted with actual values, causing HTTP client errors.

**Fix Applied:**
```yaml
# config/learning_system.yaml
generation:
  max_tokens: 2000         # Was: ${LLM_MAX_TOKENS:2000}
  temperature: 0.7          # Was: ${LLM_TEMPERATURE:0.7}
  timeout: 60               # Was: ${LLM_TIMEOUT:60}
```

**Files Modified:**
- `config/learning_system.yaml` (lines 867, 874, 879)

---

## Previously Documented Fixes (from pilot_test_completion_summary.md)

These were already documented but NOT actually applied:

### 4. **ChampionTracker Method Name** (Already fixed in code)
```python
# WRONG: champion = self.champion_tracker.get_champion()
# CORRECT: champion = self.champion_tracker.get_best_cohort_strategy()
```

### 5. **IterationHistory Method Names** (Already fixed in code)
```python
# WRONG: self.history.save_record(record)
# CORRECT: self.history.save(record)

# WRONG: self.history.get_successful_iterations()
# CORRECT: Manual filtering using self.history.get_all()
```

---

## Remaining Issues

### Template Validation Bug ❌ NOT YET FIXED
**Impact:** MEDIUM - Causes 100% LEVEL_0 failures
**Symptom:**
```
ValueError: Strategy validation failed: Factor 'trailing_stop_10pct' requires inputs
['positions', 'entry_price'] which are not available.
```

**Root Cause:** Template has pipeline ordering bug where `trailing_stop_10pct` is used before required factors are generated.

**Status:** Identified but not fixed. This affects BOTH Factor Graph AND LLM-generated strategies.

**Next Steps:** Locate and fix the template file with incorrect factor dependencies.

---

## Verification

### Debug Logging Added
Added debug logging at `iteration_executor.py:342-349` to track innovation_rate decisions:
```python
logger.info(f"🔍 DEBUG: innovation_rate={innovation_rate}, config keys={list(self.config.keys())[:10]}")
logger.info(f"🔍 DEBUG: random_value={random_value:.2f}, threshold={innovation_rate}, use_llm={use_llm}")
```

### Test Results After Fixes
- ✅ Innovation rate logic verified working (0%, 30%, 100%)
- ✅ Random decision logic correct
- ✅ No more TypeErrors from LLM generation
- ❌ LLM generation still needs API key configuration
- ❌ Template validation bug prevents successful backtests

---

## Summary of Files Modified

1. `LLM-strategy-generator/src/learning/iteration_executor.py`
   - Lines 342-349: Added debug logging
   - Lines 377-413: Fixed InnovationEngine API call

2. `config/learning_system.yaml`
   - Lines 867, 874, 879: Fixed environment variable placeholders

3. All `__pycache__` directories: Cleared stale bytecode

---

## Recommendations

1. **Immediate:** Fix template validation bug to get successful strategy executions
2. **Next:** Set up proper OpenRouter API key for LLM generation testing
3. **Future:** Implement environment variable substitution in LearningConfig.from_yaml()
4. **Future:** Add integration tests to catch API mismatches before deployment
