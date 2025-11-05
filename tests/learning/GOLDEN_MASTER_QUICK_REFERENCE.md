# Golden Master Test Quick Reference

**Purpose**: Validate Week 1 refactoring maintains behavioral equivalence

---

## Quick Commands

### Run All Golden Master Tests
```bash
pytest tests/learning/test_golden_master_deterministic.py -v
```

### Run Main Golden Master Test Only
```bash
pytest tests/learning/test_golden_master_deterministic.py::test_golden_master_deterministic_pipeline -v
```

### Run with Output (Debug)
```bash
pytest tests/learning/test_golden_master_deterministic.py -v -s
```

---

## Current Status

```
✅ test_fixtures_are_available           PASSED
✅ test_golden_master_structure_validation PASSED
⏭️  test_golden_master_deterministic_pipeline SKIPPED
```

**Why main test is skipped**: Baseline is structural only (no actual data yet)

**To activate main test**: Generate baseline with Task H1.1.2

---

## Test Components

### 1. Main Test: `test_golden_master_deterministic_pipeline()`

**What it tests**:
- ConfigManager singleton and config persistence
- IterationHistory JSONL writes and loads
- LLMClient mock integration
- Deterministic mutation generation
- Structure matches baseline

**When it runs**:
- Currently SKIPS (baseline is structural)
- Will run after baseline generation (Task H1.1.2)

### 2. Structure Test: `test_golden_master_structure_validation()`

**What it tests**:
- Baseline has all required fields
- Config structure (seed=42, iterations=5)
- Iteration outcomes structure (5 entries)

**Status**: ✅ PASSING

### 3. Fixture Test: `test_fixtures_are_available()`

**What it tests**:
- All fixtures properly defined
- Mock LLM behavior correct
- Fixed data/config available

**Status**: ✅ PASSING

---

## Fixtures Available

### `fixed_dataset`
- Fixed market data (2020-2024)
- Uses real FinLab data or synthetic fallback
- Deterministic (same data every run)

### `fixed_config`
- Fixed system configuration
- 5 iterations, seed=42
- LLM disabled, sandbox enabled

### `canned_strategy`
- Pre-defined MA20 strategy code
- No LLM randomness
- Simple, deterministic logic

### `mock_llm_client`
- Mocked LLMClient
- Returns fixed canned strategy
- Deterministic mutations

### `golden_master_baseline`
- Loads baseline JSON file
- Contains expected metrics
- Currently structural only

---

## Helper Functions

### `compare_metrics(actual, expected, tolerance, metric_name)`
```python
# Compare two metrics with tolerance
compare_metrics(1.234, 1.235, 0.01, "Sharpe ratio")
# Passes (diff 0.001 < tolerance 0.01)

compare_metrics(1.234, 1.250, 0.01, "Sharpe ratio")
# AssertionError: Sharpe ratio mismatch: expected 1.250, got 1.234, diff 0.016 exceeds tolerance 0.01
```

### `compare_iteration_outcome(actual, expected, iteration_id, tolerance)`
```python
# Compare iteration result with baseline
compare_iteration_outcome(
    actual={'success': True, 'sharpe': 1.23},
    expected={'success': True, 'sharpe': 1.24},
    iteration_id=0,
    tolerance=0.01
)
# Passes (success matches, sharpe within tolerance)
```

---

## Baseline File Structure

**File**: `tests/fixtures/golden_master_baseline.json`

```json
{
  "config": {
    "seed": 42,
    "iterations": 5
  },
  "final_champion": {
    "sharpe_ratio": 0.0,
    "max_drawdown": 0.0,
    "total_return": 0.0
  },
  "iteration_outcomes": [
    {"id": 0, "success": null, "sharpe": null},
    {"id": 1, "success": null, "sharpe": null},
    ...
  ],
  "history_entries": 5,
  "trade_count": 0
}
```

**Current State**: Structural placeholder (nulls)
**After H1.1.2**: Populated with real metrics

---

## Next Steps

### 1. Generate Baseline (Task H1.1.2)

**Option A: From Current Refactored Code**
```bash
# Run autonomous loop with fixed parameters
python scripts/generate_golden_master.py --iterations 5 --seed 42
```

**Option B: From Pre-Refactor Commit** (recommended)
```bash
# Checkout pre-refactor code
git checkout <pre-refactor-commit>

# Generate baseline
python scripts/generate_golden_master.py --iterations 5 --seed 42

# Return to refactored code
git checkout feature/learning-system-enhancement
```

**Output**: `tests/fixtures/golden_master_baseline.json` (with real data)

### 2. Validate Refactoring

After baseline is generated:
```bash
# Run golden master test (will no longer skip)
pytest tests/learning/test_golden_master_deterministic.py -v

# Expected: All 3 tests PASS
# If main test FAILS: Refactoring introduced behavioral changes
```

---

## Troubleshooting

### Main test skips with "structural only"
**Cause**: Baseline not yet generated
**Solution**: Run Task H1.1.2 to generate baseline

### Main test fails with metric mismatch
**Cause**: Refactoring changed behavior
**Options**:
1. Fix refactoring to restore original behavior
2. Update baseline if new behavior is correct
3. Adjust tolerance if difference is acceptable

### Fixture error "Failed to load real market data"
**Cause**: FinLab data not available
**Effect**: Uses synthetic fallback data
**Note**: This is expected and handled gracefully

### ConfigManager singleton error
**Cause**: Singleton not reset between tests
**Solution**: Verify `reset_test_state()` fixture is running

---

## Tolerances

### Default Tolerance: ±0.01

**Applied to**:
- Sharpe ratio
- Max drawdown
- Total return
- Annual return

**Rationale**: Account for floating-point precision differences

**Adjusting Tolerance**:
```python
# In helper function calls
compare_metrics(actual, expected, tolerance=0.05, metric_name="Sharpe")
```

---

## Test Philosophy

### Design Principles

1. **Isolate Determinism**
   - Only test deterministic parts
   - Mock out LLM randomness
   - Use fixed data and config

2. **Pragmatic Scope**
   - Test refactored components individually
   - Defer full integration to Phase 2
   - Focus on Week 1 deliverables

3. **Graceful Degradation**
   - Skip if baseline missing
   - Handle None/NaN values
   - Flexible structure validation

4. **Clear Errors**
   - Show expected vs actual
   - Include tolerance context
   - Identify failing component

---

## File Locations

```
tests/
├── learning/
│   ├── test_golden_master_deterministic.py    [521 lines - test code]
│   ├── GOLDEN_MASTER_BASELINE_GENERATION_REPORT.md
│   ├── TASK_H1.1.3_GOLDEN_MASTER_TEST_IMPLEMENTATION.md
│   └── GOLDEN_MASTER_QUICK_REFERENCE.md       [this file]
└── fixtures/
    └── golden_master_baseline.json            [structural placeholder]
```

---

## References

- **Week 1 Plan**: `.spec-workflow/specs/phase3-learning-iteration/WEEK1_HARDENING_PLAN.md`
- **Implementation Report**: `tests/learning/TASK_H1.1.3_GOLDEN_MASTER_TEST_IMPLEMENTATION.md`
- **Completion Summary**: `TASK_H1.1.3_COMPLETION_SUMMARY.md`

---

**Last Updated**: 2025-11-04
**Test Status**: 2 passed, 1 skipped (expected)
**Ready For**: Baseline generation (Task H1.1.2)
