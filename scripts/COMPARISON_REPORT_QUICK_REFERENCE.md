# Comparison Report Generator - Quick Reference

## Purpose
Compare validation results before and after the Bonferroni threshold fix to verify correctness.

## Quick Start

```bash
# Basic usage
python3 scripts/generate_comparison_report.py \
  --before phase2_validated_results_20251101_060315.json \
  --after phase2_validated_results_20251101_132244.json \
  --output validation_comparison_report.md

# View help
python3 scripts/generate_comparison_report.py --help

# Run tests
python3 scripts/test_generate_comparison_report.py
```

## Parameters

| Parameter | Required | Description | Default |
|-----------|----------|-------------|---------|
| `--before` | Yes | Path to original (before fix) JSON | - |
| `--after` | Yes | Path to new (after fix) JSON | - |
| `--output` | No | Output Markdown file path | `validation_comparison_report.md` |

## Expected Results

When comparing before/after fix results:

- **Bonferroni Threshold**: 0.8 → 0.5 (FIXED)
- **Dynamic Threshold**: 0.8 → 0.8 (UNCHANGED)
- **Statistically Significant**: 4 → 19 (+15, +375% increase)
- **Validation Passed**: 4 → 4 (no change, requires both tests)
- **Newly Significant**: 15 strategies with Sharpe 0.5-0.8

## Report Sections

1. **Executive Summary**: One-paragraph overview
2. **Threshold Configuration**: Before/after comparison table
3. **Validation Results**: Statistical summary
4. **Strategy-Level Changes**: Per-strategy analysis
5. **Execution Performance**: Timing metrics
6. **Validation**: Automated fix verification
7. **Conclusion**: Final status and recommendations

## Success Indicators

✅ Look for these in the report:

- `✅ FIXED` next to Bonferroni Threshold
- `✅ UNCHANGED` next to Dynamic Threshold
- `✅ **Threshold fix working correctly**`
- `✅ **No regressions**`
- `✅ **FIX VALIDATED - READY FOR PRODUCTION**`

## Common Use Cases

### Compare Latest Results
```bash
# Find latest results
ls -lt phase2_validated_results_*.json | head -2

# Generate report
python3 scripts/generate_comparison_report.py \
  --before <older_file>.json \
  --after <newer_file>.json
```

### Archive Reports
```bash
# Generate timestamped report
python3 scripts/generate_comparison_report.py \
  --before before.json \
  --after after.json \
  --output reports/comparison_$(date +%Y%m%d_%H%M%S).md
```

### Integration Testing
```bash
# Run validation test
python3 run_phase2_with_validation.py

# Generate comparison with previous baseline
python3 scripts/generate_comparison_report.py \
  --before baseline_results.json \
  --after phase2_validated_results_$(date +%Y%m%d_%H%M%S).json
```

## Troubleshooting

### Error: File not found
```
Error: File not found: <filename>
```
**Solution**: Verify file path is correct and file exists

### Error: Invalid JSON
```
Error: Invalid JSON in <filename>: ...
```
**Solution**: Check JSON file is valid and complete

### Unexpected validation failure
```
⚠️ **Threshold fix verification failed**
```
**Solution**: Verify threshold values in input files are as expected

## Testing

Run the test suite to verify functionality:

```bash
python3 scripts/test_generate_comparison_report.py
```

Expected output:
```
============================================================
Testing generate_comparison_report.py
============================================================

Test 1: Data loading and extraction...
✅ Test 1 passed: Data loading and extraction
Test 2: Strategy comparison...
✅ Test 2 passed: Strategy comparison
Test 3: Full report generation...
✅ Test 3 passed: Full report generation
Test 4: Edge cases...
✅ Test 4 passed: Edge cases
Test 5: Actual files (if available)...
✅ Test 5 passed: Actual files

============================================================
✅ All tests passed!
============================================================
```

## Files

| File | Purpose |
|------|---------|
| `scripts/generate_comparison_report.py` | Main report generator |
| `scripts/test_generate_comparison_report.py` | Test suite |
| `validation_comparison_report.md` | Generated report (example) |
| `scripts/COMPARISON_REPORT_QUICK_REFERENCE.md` | This file |

## Related Documentation

- **Task Summary**: See `TASK_4.2_COMPLETION_SUMMARY.md`
- **Specification**: `.claude/specs/validation-framework-critical-fixes/`
- **Validation Results**: `phase2_validated_results_*.json` files

## Contact

For issues or questions about this tool, see:
- Task 4.2 implementation details in `TASK_4.2_COMPLETION_SUMMARY.md`
- Test suite for usage examples
- Generated report for expected output format
