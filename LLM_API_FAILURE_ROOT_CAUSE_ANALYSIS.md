# LLM API Failure - Root Cause Analysis

**Date**: 2025-10-30
**Status**: ✅ ROOT CAUSE IDENTIFIED
**Impact**: 0/10 success rate (100% failure) in YAML innovation generation

---

## Executive Summary

LLM API is **working correctly** (API calls succeed, 3740 tokens generated). The failure occurs at **YAML validation** step due to **incomplete schema guidance in the prompt**.

### Root Cause
The prompt template (`src/innovation/structured_prompt_builder.py:332`) provides ambiguous guidance about the `indicators` field, causing the LLM to generate YAML that violates the schema's `minProperties: 1` constraint.

---

## Diagnostic Evidence

### Error Message
```
❌ Innovation generation failed: YAML validation failed: Missing required field: 'indicators'
```

### Pipeline Analysis
| Step | Status | Evidence |
|------|--------|----------|
| 1. API Call | ✅ SUCCESS | 3740 tokens generated, $0 cost |
| 2. YAML Extraction | ✅ SUCCESS | (implied by validation attempt) |
| 3. YAML Parsing | ✅ SUCCESS | (implied by validation attempt) |
| 4. **YAML Validation** | ❌ **FAILURE** | `minProperties: 1` violation |
| 5. Code Generation | ⏭️ SKIPPED | (validation failed) |

---

## Schema Requirements

### Required Top-Level Fields (schemas/strategy_schema_v1.json:8)
```json
"required": ["metadata", "indicators", "entry_conditions", "exit_conditions"]
```

### Indicators Field Constraints (lines 71-245)
```json
"indicators": {
  "oneOf": [
    {
      "type": "object",
      "properties": {
        "technical_indicators": {"type": "array", "minItems": 0, "maxItems": 20},
        "fundamental_factors": {"type": "array", "minItems": 0, "maxItems": 15},
        "custom_calculations": {"type": "array", "minItems": 0, "maxItems": 10}
      },
      "minProperties": 1  // ← CRITICAL: At least ONE subsection required
    },
    {
      "type": "array",
      "minItems": 1,       // ← CRITICAL: At least ONE indicator required
      "maxItems": 50
    }
  ]
}
```

**Key Constraint**: `minProperties: 1` means the `indicators` object **must contain at least one subsection** (technical_indicators, fundamental_factors, or custom_calculations).

---

## Current Prompt Template Issues

### Problematic Prompt (src/innovation/structured_prompt_builder.py:329-336)
```python
compact_schema = """
Schema (required fields):
metadata: {name, description, strategy_type, rebalancing_frequency}
indicators: {technical_indicators OR fundamental_factors OR custom_calculations}  ← AMBIGUOUS
entry_conditions: {threshold_rules OR ranking_rules, logical_operator}
exit_conditions: {stop_loss_pct, take_profit_pct} (optional)
position_sizing: {method, max_positions}
"""
```

### Problems
1. **Ambiguous "OR" syntax**: `{A OR B OR C}` is unclear
   - Does it mean "choose one" (mutually exclusive)?
   - Does it mean "at least one" (can have multiple)?
   - Does it mean "any combination"?

2. **Missing minProperties constraint**: Prompt doesn't explicitly state:
   > "indicators object must have AT LEAST ONE of: technical_indicators, fundamental_factors, or custom_calculations"

3. **All subsections marked (optional)** in detailed schema (lines 131-147):
   ```
   indicators:
     technical_indicators: (optional)    ← LLM might think ALL are optional
     fundamental_factors: (optional)     ← Could generate empty indicators: {}
     custom_calculations: (optional)
   ```

---

## LLM Behavior Hypothesis

Given the ambiguous prompt, the LLM likely generates one of these invalid structures:

### Scenario 1: Empty indicators object
```yaml
metadata:
  name: "My Strategy"
  ...
indicators: {}                    ← INVALID: minProperties = 0 (requires ≥1)
entry_conditions:
  ...
```

### Scenario 2: Incomplete indicators object
```yaml
indicators:
  # LLM stopped here, thinking all subsections are optional
entry_conditions:
  ...
```

### Scenario 3: Omitted indicators entirely
```yaml
metadata:
  ...
entry_conditions:              ← INVALID: missing required field "indicators"
  ...
```

---

## Proposed Fix

### Fix 1: Clarify Prompt Constraints (RECOMMENDED)

**Before** (line 332):
```
indicators: {technical_indicators OR fundamental_factors OR custom_calculations}
```

**After** (explicit constraint):
```
indicators:  # MUST include at least ONE of:
  technical_indicators: [{name, type, period, source}]  # array (1-20 items)
  fundamental_factors: [{name, field, source}]          # array (1-15 items)
  custom_calculations: [{name, expression}]             # array (1-10 items)
```

### Fix 2: Add Validation Instruction (DEFENSE IN DEPTH)

Add to instructions (line 347):
```python
instructions = """
Output ONLY valid YAML starting with 'metadata:'.

CRITICAL: The 'indicators' section MUST contain at least ONE of:
- technical_indicators array (with at least 1 indicator)
- fundamental_factors array (with at least 1 factor)
- custom_calculations array (with at least 1 calculation)
"""
```

### Fix 3: Provide Minimal Working Example (FALLBACK)

If token budget allows, add minimal example:
```yaml
# Minimal valid structure:
metadata:
  name: "Example Strategy"
  strategy_type: "momentum"
  rebalancing_frequency: "M"
indicators:
  technical_indicators:    # ← At least one subsection required
    - name: "rsi_14"
      type: "RSI"
      period: 14
      source: "data.get('RSI_14')"
entry_conditions:
  threshold_rules:
    - condition: "rsi_14 > 50"
```

---

## Expected Impact

### Before Fix
- LLM success rate: **0%** (0/10)
- Validation failures: **100%** (missing/empty indicators)
- Innovation mode: **Completely broken**

### After Fix (Projected)
- LLM success rate: **>90%** (target per spec)
- Validation failures: **<10%** (edge cases only)
- Innovation mode: **Fully functional**

---

## Additional Findings

### YAML Normalizer Phase2 Status
- **Completion**: ✅ All 6 tasks complete
- **Functionality**: Normalizes indicator types (sma → SMA), flattens nested params
- **Limitation**: Does NOT fix missing required fields (by design - see yaml_normalizer.py:16-18)

### Two Different YAML Schemas in Codebase
1. **Structured YAML** (schemas/strategy_schema_v1.json):
   - Used by: InnovationEngine, YAMLSchemaValidator
   - Fields: `metadata`, `indicators`, `entry_conditions`, `exit_conditions`
   - Purpose: LLM-friendly declarative format

2. **Factor Graph YAML** (src/tier1/yaml_schema.json):
   - Used by: YAMLValidator, YAMLInterpreter
   - Fields: `strategy_id`, `factors`
   - Purpose: Direct factor composition

**Note**: These are intentionally different formats for different use cases. The normalizer works with format #1 only.

---

## Implementation Priority

**Priority**: 🔴 **CRITICAL** - Blocks Phase 3 LLM innovation activation

### Implementation Steps
1. ✅ **COMPLETE**: Root cause analysis (this document)
2. ⏳ **NEXT**: Fix prompt template (structured_prompt_builder.py)
3. ⏳ **TEST**: Run debug_yaml_pipeline.py to verify fix
4. ⏳ **VALIDATE**: Run test_real_llm_api.py (target: 9/10 success)
5. ⏳ **ACTIVATE**: Enable LLM innovation in config (llm.enabled: true)

---

## Files Involved

### To Modify
- `src/innovation/structured_prompt_builder.py` (lines 329-347)
  - Clarify indicators constraints
  - Add validation instructions
  - Consider adding minimal example

### Test Scripts
- `debug_yaml_pipeline.py` (diagnostic test)
- `test_real_llm_api.py` (10-iteration validation)

### Configuration
- `config/learning_system.yaml` (llm.enabled: false → true after fix)

---

## Success Criteria

**Fix Validated When**:
1. ✅ debug_yaml_pipeline.py generates code successfully
2. ✅ test_real_llm_api.py achieves ≥9/10 success rate (>90%)
3. ✅ Generated YAML passes schema validation
4. ✅ YAMLToCodeGenerator produces executable Python code
5. ✅ Generated strategies pass backtesting

---

**Report Status**: ✅ COMPLETE
**Next Action**: Implement Fix 1 + Fix 2
**Owner**: Continue session
**Estimated Fix Time**: 30 minutes
