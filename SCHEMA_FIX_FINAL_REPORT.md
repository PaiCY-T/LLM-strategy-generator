# YAML Schema Fix - Final Report

**Date**: 2025-10-26
**Total Time Invested**: ~3 hours
**Final Success Rate**: 25% (5/20 iterations)
**Target**: >90% success rate
**Status**: ❌ NOT ACHIEVED

---

## Executive Summary

Attempted to fix YAML schema validation by progressively relaxing constraints. Applied 4 major fixes but success rate remains at 25%, far below the 90% target.

**Root Cause**: Schema and LLM generate fundamentally different structures. Using `oneOf` doesn't solve this - the LLM uses field names, types, and formats that don't match either schema variant.

**Recommendation**: **Stop schema fixes. Switch to prompt engineering + post-processing pipeline.**

---

## Chronological Progress

### Phase 1: Initial State (Before Fixes)
- **Success Rate**: 0% (Gemini API) / 20% (OpenRouter)
- **Main Issue**: `additionalProperties: false` rejected LLM additions

### Phase 2: After Quick Wins (Fixes #1 + #2)
- **Applied**:
  - Fix #1: Allow dots in tags pattern
  - Fix #2: Allow entry_conditions as object OR array
- **Success Rate**: 40% (4/10)
- **Result**: ✅ +20% improvement

### Phase 3: After Exit Conditions Fix (Fix #3)
- **Applied**: Allow exit_conditions as object OR array
- **Success Rate**: 30% (3/10)
- **Result**: ⚠️ -10% regression
- **Reason**: LLM behavior shifted - started generating indicators as arrays

### Phase 4: After Indicators Fix (Fix #4)
- **Applied**: Allow indicators as object OR array
- **Success Rate**: 25% (5/20)
- **Result**: ⚠️ -5% regression
- **Reason**: Array schema doesn't match LLM's actual array format

---

## All Fixes Applied

### Fix #1: Tag Pattern ✅ (Working)
```json
// Line 55
"pattern": "^[a-z0-9._-]+$"  // Was: "^[a-z0-9_-]+$"
```
**Impact**: Fixed 13% of initial errors
**Status**: ✅ Working correctly

---

### Fix #2: entry_conditions oneOf ⚠️ (Partially Working)
```json
// Lines 246-383
"entry_conditions": {
  "oneOf": [
    {"type": "object", ...},  // Structured format
    {"type": "array", ...}    // Simplified list
  ]
}
```
**Impact**: Intended to fix 63% of errors
**Status**: ⚠️ Partially working - but LLM uses formats not in either schema

**Examples of LLM formats NOT matching either schema**:
```yaml
# Format 1: Array of complex condition objects
entry_conditions:
  - condition:
      operator: AND
      operands:
        - operator: '>'
          left: {type: indicator, alias: sma_short}
          right: {type: indicator, alias: sma_long}
```

```yaml
# Format 2: Object with wrong field names
entry_conditions:
  ranking_rules:
    - rule: momentum_score >= 3  # Schema expects 'field', not 'rule'
      description: ...
```

```yaml
# Format 3: Array of plain strings
entry_conditions:
  - 'moving_average_short > moving_average_long'
  - 'rsi > 50'
```

---

### Fix #3: exit_conditions oneOf ✅ (Working)
```json
// Lines 385-500
"exit_conditions": {
  "oneOf": [
    {"type": "object", ...},  // Structured format
    {"type": "array", ...}    // Simplified list
  ]
}
```
**Impact**: Fixed 67% of exit_conditions errors (4/4 errors eliminated)
**Status**: ✅ Working - no more exit_conditions errors!

---

### Fix #4: indicators oneOf ⚠️ (Not Working)
```json
// Lines 71-292
"indicators": {
  "oneOf": [
    {"type": "object", ...},  // Structured with technical_indicators, fundamental_factors
    {"type": "array", ...}    // Flat list
  ]
}
```
**Impact**: Intended to fix 57% of errors
**Status**: ❌ Not working - LLM generates formats not matching either schema

**Examples of LLM formats NOT matching**:

```yaml
# Format 1: Array with 'params' instead of individual fields
indicators:
  - name: SMA_Fast
    type: SMA
    params:
      length: 20  # Schema expects 'period', not 'params.length'
```

```yaml
# Format 2: Array with lowercase types
indicators:
  - name: RSI
    type: rsi  # Schema enum requires 'RSI' (uppercase)
    params:
      period: 14
```

```yaml
# Format 3: Object with invalid type enums
indicators:
  technical_indicators:
    - name: macd_hist
      type: MACD_Histogram  # NOT in enum ['RSI', 'MACD', 'SMA', ...]
      fast_period: 12
```

```yaml
# Format 4: Jinja template values
indicators:
  technical_indicators:
    - name: sma_short
      type: SMA
      period: '{{ parameters.sma_short_period }}'  # String template, not integer
```

---

## Root Cause Analysis

### Why oneOf Doesn't Work

**The Problem**: oneOf validates that data matches ONE of the given schemas. But LLM generates data that matches NEITHER schema.

**LLM Field Name Mismatches**:
- LLM uses: `'params': {'length': 20}`
- Object schema expects: `'period': 20`
- Array schema expects: `'period': 20`

**LLM Type Name Issues**:
- LLM invents types: `'MACD_Histogram'`, `'MACD_Signal'`
- Schema enum only has: `['RSI', 'MACD', 'BB', 'SMA', ...]`

**LLM Case Sensitivity**:
- LLM uses: `'type': 'sma'`, `'type': 'rsi'`, `'type': 'macd'`
- Schema requires: `'type': 'SMA'`, `'type': 'RSI'`, `'type': 'MACD'`

**LLM Template Values**:
- LLM uses: `'period': '{{ parameters.sma_period }}'`
- Schema requires: `'period': 50` (integer, not string template)

---

## Detailed Error Breakdown (20 iterations)

| Error Category | Count | % | Examples |
|----------------|-------|---|----------|
| **indicators validation fails** | 8 | 40% | Wrong field names ('params' vs 'period'), invalid types ('MACD_Histogram'), lowercase types ('sma'), Jinja templates |
| **entry_conditions validation fails** | 4 | 20% | Wrong field names ('rule' vs 'field'), complex nested conditions, array of strings |
| **Missing required fields** | 2 | 10% | Missing 'indicators', missing 'entry_conditions' |
| **Code generation errors** | 1 | 5% | `'list' object has no attribute 'get'` |
| **API timeout** | 1 | 5% | OpenRouter request timeout |
| **YAML parsing errors** | 1 | 5% | Syntax errors in generated YAML |
| **Successes** | 5 | 25% | ✅ Validated successfully |

---

## Why Success Rate Went Down

### Paradoxical Effect: More Flexibility = More Variation

**Before Fix #4** (30% success):
- LLM mostly generated `indicators` as object
- Some generated as array → rejected
- Only object format validated

**After Fix #4** (25% success):
- LLM now generates indicators as array MORE often (because oneOf allows it)
- But array format doesn't match schema
- Both object AND array formats have validation issues

**Key Insight**: oneOf signals to LLM "both formats are valid" → LLM explores more variations → more validation failures

---

## The Fundamental Problem

### Schema Design Philosophy Mismatch

**Current Schema**: Prescriptive, strict structure
- Defines exact field names: `'field'`, `'method'`, `'period'`
- Defines exact enums: `['RSI', 'MACD', 'SMA', ...]`
- Enforces specific nesting: `indicators.technical_indicators[]`

**LLM Generation Style**: Exploratory, creative
- Invents field names: `'rule'`, `'order'`, `'params'`, `'length'`
- Invents type names: `'MACD_Histogram'`, `'MACD_Signal'`, `'rsi'` (lowercase)
- Uses flat structures: `indicators[]` instead of `indicators.technical_indicators[]`
- Adds Jinja templates: `'period': '{{ parameters.sma_period }}'`

**Result**: Irreconcilable without major architectural changes

---

## What Worked vs What Didn't

### ✅ What Worked

1. **Relaxing additionalProperties** (20% → 40%)
   - Allowed LLM to add comments, descriptions, extra fields
   - This was the single biggest improvement

2. **exit_conditions oneOf** (40% → 30% → later recovered)
   - Actually fixed ALL exit_conditions errors
   - No more `exit_conditions: Expected type 'object', got list` errors

3. **Tag pattern fix**
   - Allows dots in tags like `'sharpe-1.50'`
   - No more pattern validation errors

### ❌ What Didn't Work

1. **entry_conditions oneOf**
   - LLM generates formats not in either schema variant
   - Still failing with validation errors

2. **indicators oneOf**
   - LLM uses completely different field structure
   - 'params.length' vs 'period'
   - Lowercase vs uppercase types
   - Made things worse by encouraging array format

---

## Recommended Path Forward

### Option A: Prompt Engineering (2-4 hours) ⭐ RECOMMENDED

**Approach**: Guide LLM to generate correct format through examples and constraints

**Implementation**:

1. **Add 3 Complete Valid YAML Examples to Prompt**:
   ```yaml
   # Example 1: Momentum Strategy
   metadata:
     name: "High Momentum Strategy"
     strategy_type: momentum
     rebalancing_frequency: M
     tags: ["momentum", "growth"]

   indicators:
     technical_indicators:
       - name: rsi_14
         type: RSI
         period: 14
         source: "data.get('RSI_14')"
       - name: sma_50
         type: SMA
         period: 50
         source: "data.get('MA_50')"

   entry_conditions:
     threshold_rules:
       - condition: "rsi_14 > 30"
         description: "RSI above 30"
     ranking_rules:
       - field: momentum_score
         method: top_percent
         value: 20
   ```

2. **Add Explicit Field Name Constraints**:
   ```
   CRITICAL REQUIREMENTS:
   - indicators MUST be an object with 'technical_indicators' array
   - Use 'period' field (NOT 'params', 'length', or nested objects)
   - Use uppercase types: 'RSI', 'SMA', 'MACD' (NOT 'rsi', 'sma', 'macd')
   - entry_conditions.ranking_rules MUST use 'field' and 'method' (NOT 'rule', 'order')
   - Use integer values for periods (NOT Jinja templates like '{{ parameters.period }}')
   ```

3. **Add Error Feedback Loop**:
   - Include previous validation errors in next retry prompt
   - Ask LLM to specifically fix those issues

**Expected Impact**: 25% → **70-80%** success rate

**Pros**:
- No code changes to YAML generator
- Fast to implement
- Reversible

**Cons**:
- LLM might still deviate
- Requires careful prompt tuning

---

### Option B: Post-Processing Pipeline (3-5 hours)

**Approach**: Accept any reasonable LLM output, then transform it to match schema

**Implementation**:

Create `src/generators/yaml_normalizer.py`:

```python
def normalize_yaml(yaml_dict):
    """Transform LLM-generated YAML to match schema."""

    # Fix indicators
    if isinstance(yaml_dict.get('indicators'), list):
        yaml_dict['indicators'] = {
            'technical_indicators': [
                normalize_indicator(ind) for ind in yaml_dict['indicators']
            ]
        }

    # Fix entry_conditions
    if isinstance(yaml_dict.get('entry_conditions'), list):
        yaml_dict['entry_conditions'] = {
            'threshold_rules': [
                {'condition': cond} if isinstance(cond, str) else cond
                for cond in yaml_dict['entry_conditions']
            ]
        }

    return yaml_dict

def normalize_indicator(ind):
    """Normalize indicator field names."""
    normalized = {
        'name': ind['name'],
        'type': ind.get('type', '').upper(),  # Force uppercase
    }

    # Map 'params.length' → 'period'
    if 'params' in ind:
        if 'length' in ind['params']:
            normalized['period'] = int(ind['params']['length'])
        elif 'period' in ind['params']:
            normalized['period'] = int(ind['params']['period'])
    elif 'period' in ind:
        normalized['period'] = int(ind['period'])

    return normalized
```

**Expected Impact**: 25% → **90-95%** success rate

**Pros**:
- Handles ALL LLM variations
- More robust long-term
- Enables flexible LLM generation

**Cons**:
- Requires code changes
- Maintenance overhead
- More complex debugging

---

### Option C: Radical Schema Simplification (2-3 hours)

**Approach**: Make schema extremely permissive, validate semantics at runtime

**Implementation**:

```json
{
  "indicators": {
    "type": ["object", "array"],
    "additionalProperties": true,
    "items": {
      "type": "object",
      "additionalProperties": true
    }
  },
  "entry_conditions": {
    "type": ["object", "array", "string"],
    "additionalProperties": true
  }
}
```

**Move validation to Python runtime**:
- Accept any YAML structure
- Validate semantics when generating Python code
- Provide clear error messages during code generation

**Expected Impact**: **95-100%** YAML validation success, but errors move to code generation phase

**Pros**:
- Maximum LLM flexibility
- Schema becomes documentation, not enforcement
- Easier to evolve

**Cons**:
- Lose schema validation benefits
- Errors detected later in pipeline
- Requires robust runtime validation

---

## Cost Analysis

### Current Test Costs (OpenRouter)

| Test | Iterations | Successes | Cost | Avg Time |
|------|-----------|-----------|------|----------|
| Initial | 10 | 2 (20%) | $0.00 | 10.10s |
| Quick Wins | 10 | 4 (40%) | $0.00 | 8.97s |
| All Fixes | 10 | 3 (30%) | $0.00 | 8.26s |
| Final | 20 | 5 (25%) | $0.00 | 12.08s |
| **Total** | **50** | **14 (28%)** | **$0.00** | **9.85s** |

**Note**: google/gemini-2.5-flash-lite appears free on OpenRouter currently

### Projected Costs for Recommended Approaches

| Approach | Dev Time | Test Iterations | Expected Success | Est. Cost |
|----------|----------|----------------|------------------|-----------|
| **Option A: Prompts** | 2-4h | 50 | 70-80% | $0.00 |
| **Option B: Post-process** | 3-5h | 50 | 90-95% | $0.00 |
| **Option C: Simplify Schema** | 2-3h | 30 | 95-100% YAML | $0.00 |

**Production (100 iterations/day)**:
- Cost: $0.00/day (free tier)
- If needs paid tier: $0.02/day ($0.60/month)

---

## Lessons Learned

### 1. Schema oneOf is Not a Silver Bullet
- oneOf works when formats are similar with minor variations
- Doesn't work when LLM uses completely different structures
- Can actually make things worse by encouraging more variation

### 2. LLM Behavior is Adaptive and Unpredictable
- Relaxing one constraint changes LLM behavior globally
- LLM explores the solution space creatively
- Cannot rely on LLM to pick the "intended" format

### 3. Prescriptive Schemas Fight LLM Nature
- LLMs want to be creative and exploratory
- Strict schemas create constant friction
- Better to accept LLM output and transform it

### 4. Prompt Engineering > Schema Fixes (for LLM tasks)
- 3 good examples worth more than 10 schema changes
- Explicit constraints in prompts more effective than JSON Schema
- Error feedback loops help LLM self-correct

### 5. Post-Processing is Underrated
- Normalizing LLM output is faster than fighting schema
- Enables flexible LLM generation
- Centralized transformation logic easier to maintain

---

## Decision Matrix

| Criteria | Option A: Prompts | Option B: Post-process | Option C: Simplify |
|----------|-------------------|------------------------|-------------------|
| **Time to Implement** | 2-4h | 3-5h | 2-3h |
| **Expected Success** | 70-80% | 90-95% | 95-100% YAML |
| **Code Changes** | None | Medium | Small |
| **Maintenance** | Low | Medium | Low |
| **Robustness** | Medium | High | Very High |
| **Reversibility** | High | Medium | Low |
| **LLM Flexibility** | Low | High | Very High |

---

## Final Recommendation

### Immediate (TODAY - 3 hours)

**Implement Option B: Post-Processing Pipeline**

**Why**:
1. Highest success rate potential (90-95%)
2. One-time effort, long-term benefit
3. Handles all current AND future LLM variations
4. Enables flexible prompt engineering later

**Action Plan**:
1. Create `src/generators/yaml_normalizer.py` (1 hour)
2. Add normalization to YAML generation pipeline (30 min)
3. Test with 20 iterations (30 min)
4. Fix edge cases (1 hour)

**Expected Outcome**: **90%+ success rate**

---

### Short-term (TOMORROW - 2 hours)

**Add Option A: Prompt Examples**

**Why**:
- Further improves success rate to 95%+
- Complements post-processing
- Makes LLM output more consistent

**Action Plan**:
1. Add 3 complete valid YAML examples to prompt
2. Add explicit field name constraints
3. Test with 20 iterations
4. Measure improvement

**Expected Outcome**: **95%+ success rate**

---

### Long-term (NEXT WEEK - Optional)

**Consider Option C: Schema Simplification**

**Why**:
- Maximum LLM flexibility
- Easier to evolve system
- Reduces schema maintenance

**Trade-off**:
- Move validation to runtime
- Need robust code generation validation

---

## Appendix: All Schema Changes Made

### File: `schemas/strategy_schema_v1.json`

1. **Line 55**: Tag pattern
   - Before: `"pattern": "^[a-z0-9_-]+$"`
   - After: `"pattern": "^[a-z0-9._-]+$"`

2. **Lines 71-292**: indicators oneOf
   - Before: `{"type": "object", ...}`
   - After: `{"oneOf": [{"type": "object", ...}, {"type": "array", ...}]}`

3. **Lines 294-430**: entry_conditions oneOf
   - Before: `{"type": "object", ...}`
   - After: `{"oneOf": [{"type": "object", ...}, {"type": "array", ...}]}`

4. **Lines 432-547**: exit_conditions oneOf
   - Before: `{"type": "object", ...}`
   - After: `{"oneOf": [{"type": "object", ...}, {"type": "array", ...}]}`

---

## Appendix: Test Results Files

- `SCHEMA_FIX_VALIDATION_REPORT.md` - Initial schema fix (0% → 20%)
- `openrouter_schema_fixed_results.json` - First test (20% success)
- `QUICKWINS_VALIDATION_REPORT.md` - Fixes #1-#3 (20% → 40% → 30%)
- `quickwins_validation_results.json` - After fixes #1-#2 (40% success)
- `final_validation_results.json` - After fix #3 (30% success)
- `complete_validation_results.json` - After fix #4 (25% success)
- `SCHEMA_FIX_FINAL_REPORT.md` - This file

---

**End of Report**
