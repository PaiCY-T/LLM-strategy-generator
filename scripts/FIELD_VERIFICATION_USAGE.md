# Field Error Rate Verification - Usage Guide

## Quick Start

```bash
# Run verification script
python3 scripts/verify_field_error_rate.py
```

## What It Does

The verification script analyzes test results to measure the **field error rate** in LLM-generated strategies.

### Field Error Rate Formula

```
field_error_rate = (invalid_fields / total_fields) × 100
```

Where:
- **total_fields**: Count of all `data.get('field_name')` calls in generated code
- **invalid_fields**: Count of fields that fail `manifest.validate_field()` check

### Target: 0% Field Error Rate

The goal is to achieve **0% field error rate** by:
1. Using DataFieldManifest for field validation
2. Providing valid field list to LLM
3. Pre-validating code before execution

## Current Results

### Latest Verification (2025-11-18)

```
Total fields analyzed: 359
Invalid fields found: 263
Overall error rate: 73.26%

Status: VERIFICATION FAILED
```

### Test Mode Breakdown

| Mode | Total Fields | Invalid Fields | Error Rate | Status |
|------|--------------|----------------|------------|--------|
| LLM Only (50 iter) | 231 | 172 | 74.46% | FAIL |
| Hybrid (50 iter) | 128 | 91 | 71.09% | FAIL |
| **Overall** | **359** | **263** | **73.26%** | **FAIL** |

## Understanding Results

### PASS Criteria

```
field_error_rate = 0.0%
```

All fields in generated strategies are valid according to DataFieldManifest.

### FAIL Criteria

```
field_error_rate > 0.0%
```

Some fields in generated strategies are invalid. Common issues:
- Using non-existent fields (e.g., `price:成交量`)
- Wrong category prefix (e.g., `price_earning_ratio:` instead of `fundamental_features:`)
- Using aliases instead of canonical names

## Common Invalid Fields

The verification script identifies common mistakes and provides correction suggestions:

### Example Output

```
Invalid fields found:
  - price:成交量 (Did you mean 'price:成交金額'?)
  - pe_ratio (Did you mean 'fundamental_features:本益比'?)
  - pb_ratio (Did you mean 'fundamental_features:股價淨值比'?)
```

### Top Mistakes

1. **`price:成交量`** → Should be `price:成交金額`
   - Most common (trading value confusion)
   - Auto-correction available

2. **`fundamental_features:ROE稅後`** → Should be `fundamental_features:ROE`
   - Chinese suffix causing issues

3. **Category errors** → Wrong field prefix
   - Example: `price_earning_ratio:X` → `fundamental_features:X`

## Verification Process

### Step 1: Load DataFieldManifest

```python
manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
# Loads 14 validated fields from cache
```

### Step 2: Extract Fields from Code

```python
# Parse strategy code using AST
tree = ast.parse(strategy_code)

# Find all data.get('field') calls
extractor = FieldExtractor()
extractor.visit(tree)
fields = extractor.fields
```

### Step 3: Validate Each Field

```python
for field in fields:
    is_valid = manifest.validate_field(field)
    if not is_valid:
        invalid_count += 1
```

### Step 4: Calculate Error Rate

```python
error_rate = (invalid_count / total_count) * 100
```

## Test Directories Analyzed

The script checks the following test result directories:

```
experiments/llm_learning_validation/results/
├── fg_only_50/innovations.jsonl      # Factor Graph (no LLM code)
├── llm_only_50/innovations.jsonl     # LLM Only mode
├── hybrid_50/innovations.jsonl       # Hybrid mode
├── fg_only_20/innovations.jsonl      # 20-iteration runs
├── llm_only_20/innovations.jsonl
└── hybrid_20/innovations.jsonl
```

## Integration Requirements

To achieve 0% field error rate, integrate DataFieldManifest with:

### 1. LLM Prompt (Priority 1)

Add available fields to system prompt:

```python
manifest = DataFieldManifest()
available_fields = manifest.get_all_canonical_names()

prompt = f"""
Available fields: {', '.join(available_fields)}
Use EXACTLY these field names.
"""
```

### 2. Pre-execution Validation (Priority 2)

Validate before running backtest:

```python
from src.validation.field_validator import FieldValidator

validator = FieldValidator(manifest)
is_valid, errors = validator.validate_strategy_code(code)

if not is_valid:
    # Skip execution, provide feedback
    return errors
```

### 3. Error Feedback (Priority 3)

Provide specific corrections:

```python
if field_error:
    is_valid, suggestion = manifest.validate_field_with_suggestion(field)
    feedback = suggestion or "Field not found"
```

## Expected Results After Integration

### Before Integration (Current)

```
Overall error rate: 73.26%
Status: VERIFICATION FAILED

Invalid fields found:
  - price:成交量 (Did you mean 'price:成交金額'?)
  - fundamental_features:ROE稅後
  - price_earning_ratio:股價淨值比
  ... (263 invalid fields)
```

### After Integration (Expected)

```
Overall error rate: 0.0%
Status: VERIFICATION PASSED

All fields validated successfully!
Field error rate = 0.0%

Layer 1 (DataFieldManifest) working as expected.
```

## Troubleshooting

### No Test Data Found

```
WARNING: No fields found to analyze
```

**Solution**: Run tests first to generate innovations.jsonl files:

```bash
python run_pilot_tests_50.py
```

### Field Cache Missing

```
ERROR: Field cache not found at tests/fixtures/finlab_fields.json
```

**Solution**: Generate field cache:

```bash
python scripts/discover_finlab_fields.py
```

### High Error Rate After Integration

If error rate remains high after integration:

1. **Check prompt integration**
   - Verify field list is in system prompt
   - Check LLM is reading the field list

2. **Verify pre-validation**
   - Ensure validator is called before execution
   - Check validation errors are caught

3. **Review field manifest**
   - Verify all required fields are in manifest
   - Check for missing fields in finlab data

## Related Files

- **Verification Script**: `scripts/verify_field_error_rate.py`
- **Verification Report**: `docs/FIELD_ERROR_RATE_VERIFICATION_REPORT.md`
- **DataFieldManifest**: `src/config/data_fields.py`
- **FieldValidator**: `src/validation/field_validator.py`
- **Field Cache**: `tests/fixtures/finlab_fields.json`

## Next Steps

1. **Integrate with LLM prompt** (see Priority 1 above)
2. **Enable pre-execution validation** (see Priority 2 above)
3. **Re-run verification** to confirm 0% error rate
4. **Monitor in production** for regression

---

**Last Updated**: 2025-11-18
**Script Version**: 1.0
**Current Status**: Integration Required (73.26% → 0.0%)
