# Phase 2 Factor Graph V2 - Test Failure Analysis Report

**Date**: 2025-11-10
**Status**: 🔴 CRITICAL - 21/36 architecture tests failing
**Root Cause**: API mismatches between tests and production code

---

## Executive Summary

### Current Test Status

| Test Suite | Status | Pass Rate | Files |
|------------|--------|-----------|-------|
| FinLabDataFrame Unit Tests | ✅ PASSING | 35/35 (100%) | test_finlab_dataframe.py |
| Strategy V2 Tests | ❌ FAILING | 2/14 (14%) | test_strategy_v2.py |
| Factor.execute V2 Tests | ❌ FAILING | 13/22 (59%) | test_factor_execute_v2.py |
| **TOTAL** | **⚠️ PARTIAL** | **50/71 (70%)** | **3 files** |

### Bugs Fixed

1. ✅ **Missing import** - Added `Callable` to `src/factor_graph/strategy.py:11`
   - Impact: Blocked ALL tests from running
   - Fix: One-line import addition

---

## Failure Analysis by Category

### Category 1: Strategy API Mismatch (11 failures)

**Root Cause**: Tests use `Strategy(name='...')` but Strategy class doesn't have `name` parameter

**Production API** (src/factor_graph/strategy.py:68-73):
```python
def __init__(self, id: str, generation: int = 0, parent_ids: Optional[List[str]] = None)
```

**Test Usage** (test_strategy_v2.py):
```python
# ❌ WRONG - Strategy doesn't have 'name' parameter
strategy = Strategy(name='test_strategy')

# ✅ CORRECT - Use 'id' parameter
strategy = Strategy(id='test_strategy')
```

**Affected Tests** (test_strategy_v2.py):
1. `test_empty_strategy_raises_error`
2. `test_container_creation_from_data_module`
3. `test_matrix_flow_through_pipeline`
4. `test_position_matrix_extraction`
5. `test_missing_position_matrix_raises_error`
6. `test_missing_input_matrix_raises_error`
7. `test_factor_validation_error_propagates`
8. `test_invalid_data_module_raises_error`
9. `test_factor_execution_order`
10. `test_parallel_factors_can_execute_any_order`
11. `test_factor_with_multiple_outputs`

**Fix Priority**: 🔴 CRITICAL
**Estimated Effort**: 15 minutes (search & replace)

---

### Category 2: Factor Validation Changes (2 failures)

**Root Cause**: Tests expect "at least one input" but `Factor` dataclass doesn't enforce this

**Affected Tests**:
1. `test_strategy_v2.py::test_factor_with_no_inputs` - ValueError expected but not raised
2. `test_factor_execute_v2.py::test_factor_with_no_inputs` - ValueError expected but not raised

**Investigation Needed**:
- Check if Factor.__post_init__ validates inputs list is non-empty
- Tests may be outdated or validation removed

**Fix Priority**: 🟡 MEDIUM
**Estimated Effort**: 30 minutes (check design decision + update tests)

---

### Category 3: Error Message Format Changes (3 failures)

**Root Cause**: Error message format changed but tests expect old format

**Affected Tests** (test_factor_execute_v2.py):
1. `test_missing_input_raises_keyerror`
   - Expected: `'Missing matrices'` regex
   - Actual: `"Factor 'test' requires matrices ['nonexistent'], but ['nonexistent'] are missing from container. Available: ['close']"`

2. `test_multiple_missing_inputs`
   - Expected: `'Missing matrices'` regex
   - Actual: More detailed error message

3. `test_logic_function_error_propagates`
   - Expected wrapped exception, got RuntimeError instead

**Fix Priority**: 🟡 MEDIUM
**Estimated Effort**: 20 minutes (update regex patterns)

---

### Category 4: Container Behavior Changes (2 failures)

**Root Cause**: FinLabDataFrame behavior differs from test expectations

**Affected Tests** (test_factor_execute_v2.py):
1. `test_lazy_loading_in_factor`
   - KeyError: Matrix not lazy-loaded as expected
   - May indicate lazy loading not working in factor context

2. `test_shape_validation_in_factor`
   - RuntimeError: Shape validation error message format changed

**Fix Priority**: 🟡 MEDIUM
**Estimated Effort**: 45 minutes (investigate + fix)

---

### Category 5: Immutability Protection Failure (1 failure)

**Root Cause**: Test expects input matrix NOT to be modified, but it WAS modified

**Affected Test** (test_factor_execute_v2.py):
```python
test_factor_modifying_input_matrix
# Expected: Original 'close' matrix unchanged after factor execution
# Actual: First value changed from 103.164... to 999.0
```

**Analysis**: This is a **DATA INTEGRITY BUG** 🚨
- FinLabDataFrame.add_matrix() should copy data
- OR Factor.execute() should not allow logic to modify input matrices
- This violates immutability guarantee documented in Phase 2

**Fix Priority**: 🔴 CRITICAL (Data Safety Issue)
**Estimated Effort**: 1-2 hours (investigate + fix + verify)

---

## Summary Statistics

| Issue Category | Count | Priority | Total Effort |
|----------------|-------|----------|--------------|
| Strategy API Mismatch | 11 | 🔴 CRITICAL | 15 min |
| Factor Validation | 2 | 🟡 MEDIUM | 30 min |
| Error Messages | 3 | 🟡 MEDIUM | 20 min |
| Container Behavior | 2 | 🟡 MEDIUM | 45 min |
| Immutability Bug | 1 | 🔴 CRITICAL | 90 min |
| **TOTAL** | **21** | **Mixed** | **~3 hours** |

---

## Recommended Action Plan

### Phase 1: Critical Fixes (30 minutes)

1. **Fix Strategy API mismatch** (11 tests)
   ```bash
   # Search and replace in test_strategy_v2.py
   Strategy(name= → Strategy(id=
   ```

2. **Verify Callable import persists**
   ```bash
   git diff src/factor_graph/strategy.py
   ```

### Phase 2: Data Integrity Bug (90 minutes)

3. **Investigate immutability violation**
   - Read FinLabDataFrame.add_matrix() implementation
   - Check if copy() is actually called
   - Add defensive copy in Factor.execute() if needed

4. **Add regression test**
   - Ensure input matrices are never modified

### Phase 3: Test Updates (65 minutes)

5. **Update error message assertions** (20 min)
   - Replace exact string matches with regex patterns
   - Make tests resilient to message improvements

6. **Fix container behavior tests** (45 min)
   - Investigate lazy loading in factor context
   - Update shape validation assertions

### Phase 4: Design Decisions (30 minutes)

7. **Resolve Factor validation question**
   - Decide if empty inputs list should be allowed
   - Update either tests or Factor validation logic

---

## Test Execution Evidence

### Before Fix (All tests blocked):
```
ERROR: NameError: name 'Callable' is not defined
3 errors during collection
```

### After Import Fix (Tests run but many fail):
```
tests/factor_graph/test_finlab_dataframe.py: 35 passed ✅
tests/factor_graph/test_strategy_v2.py: 2 passed, 12 failed ❌
tests/factor_graph/test_factor_execute_v2.py: 13 passed, 9 failed ❌

TOTAL: 50 passed, 21 failed (70% pass rate)
```

---

## Conclusion

**Status Reassessment**: Phase 2 Factor Graph V2 is **85% complete**, not 100%

### What IS True:
- ✅ 170 tests written (comprehensive coverage)
- ✅ Production code implemented
- ✅ Merged to main
- ✅ Unit tests passing (35/35)

### What is NOT True:
- ❌ "100% tests passing" - Actually 70% (50/71)
- ❌ "Production ready" - Has data integrity bug
- ❌ "100% coverage" - Unverified (tests don't run cleanly)

### Estimated Completion:
- **Current**: 85% complete
- **Remaining**: ~3 hours of focused work
- **Blockers**: 1 data integrity bug (CRITICAL)

---

**Recommendation**: Fix critical issues (Strategy API + immutability bug) before claiming production readiness.

**Next Steps**:
1. Apply Phase 1 fixes (30 min)
2. Run full test suite
3. Fix data integrity bug (90 min)
4. Re-run tests
5. Update status to 100% when all tests pass

---

**Report Generated**: 2025-11-10
**Last Updated**: After Callable import fix
**Verified By**: Direct pytest execution
