# Prompt Template Fix - Complete Summary

**Date**: 2025-11-02
**Status**: ✅ ALL PROMPT TEMPLATES FIXED

## Problem Identified

The LLM prompt templates contained **incorrect dataset key information** that didn't match the actual FinLab database. This caused the LLM to generate strategies with non-existent keys, which then failed static validation before Docker execution could occur.

## Root Cause

**Prompt templates told LLM to use keys that don't exist:**
```
❌ price:收盤價 (doesn't exist)
❌ price:開盤價 (doesn't exist)
❌ price:成交股數 (doesn't exist)
❌ price:最高價 (doesn't exist)
❌ price:最低價 (doesn't exist)
```

**What actually exists in finlab_database_cleaned.csv:**
```
✅ etl:adj_close (adjusted close price)
✅ etl:adj_open (adjusted open price)
✅ etl:adj_high (adjusted high price)
✅ etl:adj_low (adjusted low price)
✅ price:成交金額 (trading value - ONLY price: key that exists)
```

## Files Fixed

### ✅ 1. prompt_template_v3_comprehensive.txt
**Location**: `/mnt/c/Users/jnpi/Documents/finlab/artifacts/working/backups/prompt_template_v3_comprehensive.txt`

**Changes**:
- Lines 5-20: Replaced incorrect "Price Data (Built-in)" section
- Added prominent warnings about non-existent keys
- Updated all code examples to use correct keys

**Example code changes**:
```python
# BEFORE (wrong):
close = data.get('price:收盤價')
volume = data.get('price:成交股數')

# AFTER (correct):
close = data.get('etl:adj_close')  # ✅ Use adjusted close
trading_value = data.get('price:成交金額')
```

### ✅ 2. prompt_template_v2_with_datasets.txt
**Location**: `/mnt/c/Users/jnpi/Documents/finlab/artifacts/working/backups/prompt_template_v2_with_datasets.txt`

**Changes**:
- Lines 7-22: Replaced "Price Data (Built-in)" section
- Lines 119-120: Updated data loading examples
- Lines 129-130: Fixed volume factor to use trading_value

### ✅ 3. prompt_template_v2.txt
**Location**: `/mnt/c/Users/jnpi/Documents/finlab/artifacts/working/backups/prompt_template_v2.txt`

**Changes**:
- Lines 28-43: Replaced "Price Data (10 datasets)" section
- Lines 101-102: Updated basic data loading example
- Lines 235-236: Fixed example strategy code

### ✅ 4. prompt_template_v2_corrected.txt
**Location**: `/mnt/c/Users/jnpi/Documents/finlab/artifacts/working/backups/prompt_template_v2_corrected.txt`

**Changes**:
- Lines 7-22: Replaced "Price Data (10)" section
- Lines 98-99: Updated strategy template code

## New Prompt Template Structure

All templates now have a consistent "Price Data" section:

```markdown
### Price Data - IMPORTANT: Use Adjusted Data!

⚠️ **CRITICAL**: For price data, ALWAYS use `etl:adj_*` keys (adjusted for dividends/splits).
DO NOT use `price:收盤價`, `price:開盤價`, etc. - these keys DO NOT EXIST!

**Correct price data keys:**
- `etl:adj_close` - ✅ Adjusted close price (USE THIS for close price)
- `etl:adj_open` - ✅ Adjusted open price (USE THIS for open price)
- `etl:adj_high` - ✅ Adjusted high price
- `etl:adj_low` - ✅ Adjusted low price
- `price:成交金額` - ✅ Trading value (ONLY price: key that exists)
- `etl:market_value` - ✅ Market capitalization

**DO NOT USE (these don't exist):**
- ❌ price:收盤價, price:開盤價, price:最高價, price:最低價
- ❌ price:成交股數, price:成交筆數, price:漲跌價差
```

## Expected Impact

### Before Fix
```
LLM generates: price:收盤價
↓
Static validation: ❌ FAIL (Unknown dataset key)
↓
Docker execution: Never reached
↓
Result: 0% Docker success rate
```

### After Fix
```
LLM generates: etl:adj_close
↓
Static validation: ✅ PASS
↓
Docker execution: ✅ EXECUTED
↓
Result: Strategies can now be backtested
```

## Related Fixes (Already Complete)

### Auto-Fixer Enhancements ✅
**File**: `artifacts/working/modules/fix_dataset_keys.py`

Added 8 new mappings to handle legacy issues:
```python
"price:本益比": "price_earning_ratio:本益比",
"price:股價淨值比": "price_earning_ratio:股價淨值比",
"price:收盤價": "etl:adj_close",
"price:開盤價": "etl:adj_open",
"price:成交股數": "price:成交金額",
# ... and 3 more
```

### Dataset Key List Update ✅
**File**: `available_datasets.txt`

- **Before**: 311 keys (some outdated)
- **After**: 334 keys (synchronized with finlab_database_cleaned.csv)

## Verification Plan

1. **Run validation test** with fixed prompt templates
2. **Monitor Docker execution rate** - should increase from 0% to >80%
3. **Check auto-fixer logs** - should see fewer dataset key fixes needed
4. **Review LLM-generated strategies** - should use correct keys from the start

## Success Criteria

- ✅ All 4 prompt templates updated
- ✅ All code examples use correct dataset keys
- ✅ Prominent warnings about non-existent keys added
- ⏳ Validation test shows improved Docker execution rate (pending)

## Next Steps

1. Run 20-iteration validation test to verify fix effectiveness
2. Monitor for any remaining dataset key issues
3. Close docker-integration-test-framework spec after verification
4. Document findings in project knowledge base

---

**Fix completed by**: Claude Code
**Review date**: 2025-11-02
**Status**: Ready for validation testing
