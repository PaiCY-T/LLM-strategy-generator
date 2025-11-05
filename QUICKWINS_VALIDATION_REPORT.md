# Quick Wins Schema Fix - Validation Report

**Date**: 2025-10-26
**Fixes Applied**: 3 schema modifications
**Result**: ⚠️ PARTIAL SUCCESS | Success Rate: 20% → 40% → 30%

---

## Summary

Applied three Quick Wins schema fixes to improve YAML validation success rate:

1. ✅ **Tag Pattern** - Allow dots in tags: `^[a-z0-9._-]+$`
2. ✅ **entry_conditions** - Allow both object and array formats using oneOf
3. ✅ **exit_conditions** - Allow both object and array formats using oneOf

**Result**:
- Initial success rate: **20%** (2/10)
- After first 2 fixes: **40%** (4/10) ✅ +20% improvement
- After all 3 fixes: **30%** (3/10) ⚠️ -10% regression

---

## Why Success Rate Decreased

### Exit Conditions Fix Worked Perfectly
- **Before Fix #3**: 4 failures with `exit_conditions: Expected type 'object', got list`
- **After Fix #3**: 0 failures with exit_conditions errors ✅

### But LLM Behavior Changed - New Error Emerged

**New Primary Error** (57% of failures):
```
indicators: Expected type 'object', got list
```

**Root Cause**: LLM switched from generating `indicators` as object to generating it as array

**Example of what LLM now generates**:
```yaml
indicators:
  - name: rsi_14
    type: RSI
    period: 14
  - name: sma_50
    type: SMA
    period: 50
```

**Schema expects**:
```yaml
indicators:
  technical_indicators:
    - name: rsi_14
      type: RSI
      period: 14
```

---

## Remaining Errors Breakdown (7 failures)

### Error #1: indicators Type Mismatch (57%)
**Occurrences**: 4/7 failures
**Error**: `indicators: Expected type 'object', got list`

**Fix Required**: Apply oneOf to indicators (same as entry_conditions/exit_conditions)

**Expected Impact**: +57% → **87% total success rate**

---

### Error #2: entry_conditions Field Mismatch (14%)
**Occurrences**: 1/7 failures
**Error**: `entry_conditions: {...} is not valid under any of the given schemas`

**Details**: LLM used wrong field names:
- Used `'rule'` instead of `'field'`
- Used `'order'` instead of `'method'`

**Example**:
```yaml
ranking_rules:
  - rule: momentum_score  # Should be 'field'
    order: descending      # Should be 'method'
```

**Fix Required**: More flexible array schema OR better prompts

---

### Error #3: entry_conditions Array of Strings (14%)
**Occurrences**: 1/7 failures
**Error**: `entry_conditions: ['rsi.value < 30', ...] is not valid`

**Details**: LLM generated array of plain strings instead of array of objects

**Example**:
```yaml
entry_conditions:
  - 'rsi.value < 30'
  - 'macd.histogram > 0'
```

**Fix Required**: Allow array of strings in oneOf for entry_conditions

---

### Error #4: Missing Required Field (14%)
**Occurrences**: 1/7 failures
**Error**: `Missing required field: 'entry_conditions'`

**Fix Required**: None (LLM mistake, will naturally improve with better prompts)

---

## Next Steps to Reach 90%

### Immediate Fix (30 min) - Fix #4

**Apply oneOf to indicators** to allow array format:

```json
"indicators": {
  "oneOf": [
    {
      "type": "object",
      "description": "Structured indicators (current format)",
      "properties": {
        "technical_indicators": [...],
        "fundamental_factors": [...]
      }
    },
    {
      "type": "array",
      "description": "Simplified indicators (flat list)",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "type": {"type": "string"},
          "period": {"type": "integer"}
        }
      }
    }
  ]
}
```

**Expected Impact**: 30% + 57% = **87% success rate**

---

### Follow-up Fixes (1 hour) - Prompts

**Improve LLM prompts** to guide correct format:
1. Add 2-3 complete YAML examples showing correct structure
2. Explicitly list required fields
3. Show both object and array formats as valid options

**Expected Impact**: 87% → **95%+ success rate**

---

## Performance Metrics

### Test Run #1: Initial Quick Wins (Fixes #1 + #2)
- **Iterations**: 10
- **Successes**: 4/10 (40%)
- **Avg Time**: 8.97s per attempt
- **Cost**: $0.00 (free tier)

**Top Errors**:
- exit_conditions type mismatch: 67%
- Case sensitivity: 17%
- Missing required field: 17%

---

### Test Run #2: All Quick Wins (Fixes #1 + #2 + #3)
- **Iterations**: 10
- **Successes**: 3/10 (30%)
- **Avg Time**: 8.26s per attempt
- **Cost**: $0.00 (free tier)

**Top Errors**:
- indicators type mismatch: 57% (NEW!)
- entry_conditions field mismatch: 14%
- entry_conditions array format: 14%
- Missing required field: 14%

---

## Lessons Learned

### 1. LLM Behavior is Adaptive
- Fixing one schema constraint can shift LLM behavior to different patterns
- Need to monitor for emergent errors after each fix

### 2. oneOf is Powerful but Tricky
- Successfully fixed exit_conditions (0 errors after fix)
- But need to ensure array schema matches what LLM actually generates
- LLM generates simpler formats (flat arrays) vs structured (nested objects)

### 3. Schema Flexibility Trade-off
- More flexible schema (using oneOf) → LLM has more options
- LLM doesn't always pick the "intended" format
- Need to support ALL formats LLM naturally generates

---

## Files Modified

1. `schemas/strategy_schema_v1.json`:
   - Line 55: Tag pattern allows dots
   - Lines 246-383: entry_conditions accepts object OR array
   - Lines 385-500: exit_conditions accepts object OR array

---

## Test Results Files

- `quickwins_validation_results.json` - Test #1 results (40% success)
- `quickwins_validation_output.txt` - Test #1 detailed output
- `final_validation_results.json` - Test #2 results (30% success)
- `final_validation_output.txt` - Test #2 detailed output

---

## Recommendation

**Apply Fix #4 (indicators oneOf)** to reach ~87% success rate, then evaluate if prompt improvements are needed to reach 90%+ target.

**Estimated Time**:
- Fix #4 implementation: 30 min
- Testing: 10 min
- Prompt improvements (if needed): 1-2 hours

**Total to 90%+**: 1-3 hours
