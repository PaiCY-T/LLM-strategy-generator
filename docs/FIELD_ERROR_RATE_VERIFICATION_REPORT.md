# Field Error Rate Verification Report

**Date**: 2025-11-18
**Verification Script**: `scripts/verify_field_error_rate.py`
**Test Data**: Recent 50-iteration runs (fg_only_50, llm_only_50, hybrid_50)

---

## Executive Summary

**VERIFICATION FAILED**

The field error rate verification reveals that while Layer 1 (DataFieldManifest), Layer 2 (FieldValidator), and Layer 3 (Config-based architecture) have been implemented, they are **not integrated** with the LLM strategy generation workflow.

### Key Findings

- **Current Field Error Rate**: 73.26%
- **Total Fields Analyzed**: 359
- **Invalid Fields Found**: 263
- **Status**: Integration missing - infrastructure exists but not in use

---

## Detailed Results

### Test Mode Breakdown

| Mode | Total Fields | Invalid Fields | Error Rate | Status |
|------|--------------|----------------|------------|--------|
| Factor Graph (50 iter) | 0 | 0 | N/A | SKIP (no LLM code) |
| LLM Only (50 iter) | 231 | 172 | 74.46% | FAIL |
| Hybrid (50 iter) | 128 | 91 | 71.09% | FAIL |
| **Overall** | **359** | **263** | **73.26%** | **FAIL** |

### Common Invalid Fields

The following invalid fields were found repeatedly in generated strategies:

1. **`price:成交量`** → Should be `price:成交金額`
   - Most common mistake (trading value vs. shares confusion)
   - Correction suggestion available in manifest

2. **`fundamental_features:ROE稅後`** → Invalid field
   - Should use `fundamental_features:ROE` instead
   - Chinese suffix causing issues

3. **`price_earning_ratio:股價淨值比`** → Wrong category
   - Should be `fundamental_features:股價淨值比`
   - Category prefix incorrect

4. **`pe_ratio`, `pb_ratio`** → Alias not canonical
   - Should use full canonical names
   - Suggestions available: `fundamental_features:本益比`, `fundamental_features:股價淨值比`

5. **`etl:market_value`, `price:市值`, `market_cap`** → Field doesn't exist
   - No market cap field in manifest
   - Need to verify if this field should be added

---

## Root Cause Analysis

### Infrastructure Status

✅ **Layer 1 (DataFieldManifest)** - Implemented
- Location: `src/config/data_fields.py`
- O(1) field validation working
- Auto-correction suggestions available
- 14 fields loaded from cache

✅ **Layer 2 (FieldValidator)** - Implemented
- AST-based field extraction
- Pre-execution validation capability

✅ **Layer 3 (Config-based architecture)** - Implemented
- Available fields configuration exists

### Integration Gap

❌ **LLM Prompt Integration** - Missing
- DataFieldManifest not referenced in LLM prompts
- No validation before code execution
- No field list provided to LLM during generation

❌ **Pre-execution Validation** - Not Active
- FieldValidator exists but not called
- Code executes without field validation
- Errors caught at runtime, not before

### Evidence

From `llm_only_50/innovations.jsonl`:
```python
# Iteration 0 - Invalid field usage
volume = data.get('price:成交量')  # ❌ INVALID - should be 'price:成交金額'

# Error message
Exception: **Error: price:成交量 not exists
```

This pattern repeats across all 50 iterations, showing that the LLM never learned the correct field names.

---

## Impact Assessment

### Current System Behavior

1. **LLM generates code with invalid fields** (73% error rate)
2. **Code executes and fails** at runtime
3. **Generic error feedback** provided to LLM
4. **LLM tries again** with same mistakes
5. **Iteration loop** without improvement

### Expected System Behavior (After Integration)

1. **LLM generates code** using valid field list
2. **Pre-execution validation** catches field errors
3. **Specific correction suggestions** provided
4. **LLM fixes issues** before execution
5. **Code executes successfully** with 0% field errors

---

## Required Actions

To achieve 0% field error rate, the following integrations are required:

### Priority 1: LLM Prompt Integration

**Action**: Inject available fields into LLM system prompt

**Location**: Strategy generation prompt template

**Implementation**:
```python
# Load manifest
manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')

# Get all canonical field names
available_fields = manifest.get_all_canonical_names()

# Add to prompt
prompt = f"""
Available data fields (use EXACTLY these names):
{chr(10).join(f'- {field}' for field in available_fields)}

CRITICAL: Only use fields from the list above.
Using invalid field names will cause execution errors.
"""
```

**Expected Impact**: Reduce field errors by 50-70%

### Priority 2: Pre-execution Validation

**Action**: Validate generated code before execution

**Location**: Strategy executor (before backtest)

**Implementation**:
```python
from src.validation.field_validator import FieldValidator

# Before execution
validator = FieldValidator(manifest)
is_valid, errors = validator.validate_strategy_code(strategy_code)

if not is_valid:
    # Provide specific feedback
    feedback = f"Field validation failed: {errors}"
    # Skip execution, request regeneration
```

**Expected Impact**: Catch remaining errors before runtime

### Priority 3: Feedback Enhancement

**Action**: Provide field-specific correction suggestions

**Location**: Error feedback generation

**Implementation**:
```python
# When field error detected
if "not exists" in error_message:
    invalid_field = extract_field_from_error(error_message)
    is_valid, suggestion = manifest.validate_field_with_suggestion(invalid_field)

    if suggestion:
        feedback += f"\n{suggestion}"
```

**Expected Impact**: Enable LLM to self-correct

---

## Verification Methodology

### Data Collection

The verification script analyzes `innovations.jsonl` files from test results:

1. **Load DataFieldManifest** for field validation
2. **Read each iteration** from innovations.jsonl
3. **Extract field references** using AST parsing
4. **Validate each field** using manifest.validate_field()
5. **Calculate error rate** = (invalid / total) × 100

### AST-based Field Extraction

```python
class FieldExtractor(ast.NodeVisitor):
    def visit_Call(self, node):
        # Find data.get('field_name') calls
        if (node.func.attr == 'get' and
            node.func.value.id == 'data'):
            field_name = node.args[0].value
            self.fields.add(field_name)
```

### Validation Logic

```python
for field in extracted_fields:
    is_valid = manifest.validate_field(field)
    if not is_valid:
        invalid_count += 1
```

---

## Next Steps

### Immediate Actions

1. **Integrate DataFieldManifest with LLM prompt**
   - Add available fields list to system prompt
   - Emphasize using exact field names

2. **Enable pre-execution validation**
   - Call FieldValidator before backtest
   - Provide specific field error feedback

3. **Re-run verification**
   - Execute 50-iteration test with integration
   - Verify field_error_rate = 0.0%

### Long-term Improvements

1. **Expand field manifest**
   - Add missing fields (market_cap, etc.)
   - Verify coverage against actual finlab data

2. **Auto-correction in validator**
   - Automatically fix common mistakes
   - Use manifest.COMMON_CORRECTIONS mapping

3. **Continuous monitoring**
   - Track field error rate in production
   - Alert on regression

---

## Conclusion

The infrastructure for achieving 0% field error rate has been successfully implemented:

- ✅ Layer 1 (DataFieldManifest): O(1) validation, auto-correction
- ✅ Layer 2 (FieldValidator): AST-based extraction, pre-execution checks
- ✅ Layer 3 (Config-based): Available fields configuration

However, **integration with the LLM workflow is missing**, resulting in a current field error rate of **73.26%**.

The verification script confirms that the validation infrastructure works correctly and can identify all field errors. Once integrated with the LLM prompt and execution pipeline, we expect to achieve the target **0% field error rate**.

### Verification Command

```bash
python3 scripts/verify_field_error_rate.py
```

### Expected Output After Integration

```
VERIFICATION PASSED

All fields validated successfully!
Field error rate = 0.0%

Layer 1 (DataFieldManifest) working as expected.
```

---

**Report Generated**: 2025-11-18
**Script Version**: 1.0
**Status**: Integration Required
