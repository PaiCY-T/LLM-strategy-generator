# Phase 2 Factor Graph V2 - Architecture Mismatch Analysis

**Date**: 2025-11-10
**Status**: 🔴 CRITICAL - Architecture mismatch between tests and production code
**Previous**: PHASE2_TEST_FAILURE_REPORT.md (Strategy API fixes applied successfully)

---

## Executive Summary

✅ **Strategy API fixes successful** - All 11 `Strategy(name=...)` → `Strategy(id=...)` fixes applied
❌ **Deeper issue discovered** - Tests assume automatic dependency inference, production requires explicit DAG construction
🚨 **Design Decision Required** - Choose between relaxing validation or updating tests

---

## Root Cause Analysis

### The Core Mismatch

**Test Assumption** (Implicit):
```python
# Tests assume: add_factor() auto-infers dependencies from factor.inputs/outputs
strategy.add_factor(simple_factor)  # inputs=['close'], outputs=['momentum']
strategy.add_factor(position_factor)  # inputs=['momentum'], outputs=['position']
# Expected: Auto-connect momentum → position via output/input matching
```

**Production Reality** (Explicit):
```python
# Production code: DAG requires explicit depends_on parameter
strategy.add_factor(simple_factor)  # Creates DISCONNECTED node (no edges)
strategy.add_factor(position_factor)  # Creates ANOTHER disconnected node
# Result: nx.is_weakly_connected(dag) = False → "orphaned factors" error
```

### Evidence from Strategy.py

**add_factor() Method** (strategy.py:122-201):
- Line 176: `depends_on = depends_on or []` - Defaults to empty list (no auto-inference)
- Line 185: `self.dag.add_node(factor.id, factor=factor)` - Just adds node
- Line 187-189: Only adds edges if `depends_on` explicitly provided
- **No automatic edge creation from factor.inputs/outputs**

**validate() Check 4** (strategy.py:578-591):
```python
# Check 4: No orphaned factors (all factors reachable from base data)
if not nx.is_weakly_connected(self.dag):
    # Find isolated components
    components = list(nx.weakly_connected_components(self.dag))
    if len(components) > 1:
        orphaned_factors = [sorted(comp) for comp in components[1:]]
        raise ValueError(f"Found orphaned factors: {orphaned_factors}")
```

This validation **requires** all factors to be connected through edges in the DAG. Without explicit `depends_on`, each factor is a separate connected component.

---

## Test Failure Categories (Updated)

### Category 1: Orphaned Factors (11 failures)

**Error Pattern**:
```
ValueError: Strategy validation failed: Found orphaned factors (not reachable from base data):
[['position_from_momentum']]. All factors must be connected through dependencies.
```

**Affected Tests**:
1. test_single_factor_pipeline - 2 disconnected factors
2. test_multi_factor_pipeline_execution - 3 disconnected factors
3. test_container_creation_from_data_module - 2 disconnected factors
4. test_matrix_flow_through_pipeline - 3 disconnected factors
5. test_position_matrix_extraction - 2 disconnected factors
6. test_invalid_data_module_raises_error - 2 disconnected factors
7. test_parallel_factors_can_execute_any_order - 4 disconnected factors

**Root Cause**: No `depends_on` parameter passed to `add_factor()` → disconnected DAG nodes

### Category 2: Missing Position Signal (1 failure)

**Test**: test_missing_position_matrix_raises_error

**Error**:
```
ValueError: Strategy validation failed: Strategy must have at least one factor producing
position signals (columns: ['position', 'positions', 'signal', 'signals']).
Current outputs: ['close', 'high', 'low', 'momentum', 'open', 'volume'].
```

**Root Cause**: Test expects to test missing position error AFTER execution, but validation catches it BEFORE execution

### Category 3: Missing Base Data Connection (2 failures)

**Tests**:
- test_missing_input_matrix_raises_error
- test_factor_execution_order

**Error**:
```
ValueError: Strategy validation failed: Factor 'bad' requires inputs ['nonexistent'] which
are not available. Available columns at this point: ['close', 'high', 'low', 'open', 'volume'].
```

**Root Cause**: Validation Check 2 (line 534-560) checks ALL factor inputs are available, even for factors meant to test error handling

### Category 4: Empty Container (2 failures)

**Tests**:
- test_factor_validation_error_propagates
- test_factor_with_multiple_outputs

**Error**:
```
RuntimeError: Pipeline execution failed at factor 'multi' (Multi):
"Factor 'multi' requires matrices ['close'], but ['close'] are missing from container. Available: []"
```

**Root Cause**: Container not populated with base OHLCV data before factor execution

### Category 5: Empty Inputs Validation (1 failure)

**Test**: test_factor_with_no_inputs

**Error**:
```
ValueError: Factor must have at least one input column
```

**Root Cause**: Factor.__post_init__ (factor.py:120-121) enforces non-empty inputs list

### Category 6: Error Message Format (1 failure)

**Test**: test_empty_strategy_raises_error

**Expected**: `"No factors"`
**Actual**: `"Strategy validation failed: Strategy must contain at least one factor"`

**Root Cause**: Minor - error message format changed

---

## Design Decisions Required

### Decision 1: Automatic Dependency Inference

**Option A: Implement Auto-Inference** (Match Test Expectations)
- Modify `Strategy.add_factor()` to auto-connect factors based on input/output matching
- Scan existing factors for outputs matching new factor's inputs
- Add `auto_connect=True` parameter with default True

**Pros**:
- Tests work without modification
- More intuitive API for users (less boilerplate)
- Matches original test design intent

**Cons**:
- Adds complexity to add_factor()
- May create unintended connections
- Less explicit (implicit magic)
- Breaks existing explicit-DAG design

**Option B: Update Tests** (Match Production Reality)
- Add `depends_on` parameter to all test `add_factor()` calls
- Tests explicitly specify factor dependencies
- Keep production code as-is (explicit DAG construction)

**Pros**:
- Maintains explicit, predictable behavior
- Tests document actual usage pattern
- No production code changes needed
- Preserves design philosophy

**Cons**:
- 30+ test call sites need updating
- More verbose test code
- Higher maintenance burden for test writers

**Recommendation**: **Option B** - Update tests to match production reality
- Explicit is better than implicit (Python zen)
- Current design is correct for DAG library
- Tests should document actual API usage

### Decision 2: Validation Strictness

**Current State**: `Strategy.validate()` has 5 strict checks that block many test scenarios

**Option A: Skip Validation in Tests**
- Add `skip_validation=False` parameter to `to_pipeline()`
- Tests can bypass validation for error-handling tests

**Option B: Relax Validation Rules**
- Make orphan detection optional
- Allow factors without position signals (for testing)
- Less strict input availability checking

**Recommendation**: **Option A** - Add optional validation skip
- Keep validation strict for production use
- Allow tests to test specific error conditions
- Minimal production code change

### Decision 3: Empty Container Issue

**Root Cause**: Container not initialized with base OHLCV data matrices

**Options**:
1. Modify `to_pipeline()` to auto-add base matrices from data_module
2. Require tests to explicitly initialize container
3. Add helper method `add_base_matrices(data_module)`

**Investigation Needed**: Read `to_pipeline()` implementation to understand container initialization

---

## Proposed Action Plan (Revised)

### Phase 1: Investigation (30 minutes)

1. **Read Strategy.to_pipeline()** - Understand how container is initialized
2. **Check if base matrices should be auto-added** - Design intent verification
3. **Verify lazy loading behavior** - Should base data be pre-loaded?

### Phase 2: Quick Wins (45 minutes)

1. **Fix error message regex** - Update test_empty_strategy_raises_error (5 min)
2. **Add skip_validation parameter** - Allow tests to bypass validation (20 min)
3. **Document decision** - Record design decisions in DESIGN.md (20 min)

### Phase 3: Test Updates (2-3 hours)

1. **Add depends_on to all test add_factor() calls** - Explicit DAG construction
2. **Add base data factors where needed** - Connect to OHLCV columns
3. **Update error-handling tests** - Use skip_validation parameter
4. **Fix empty inputs test** - Either allow or document restriction

### Phase 4: Validation (30 minutes)

1. **Run full test suite** - Verify all fixes work
2. **Check coverage** - Ensure no regressions
3. **Update progress report** - Final status documentation

---

## Summary

**What We Fixed**:
- ✅ Strategy API mismatch (11 tests) - `Strategy(name=...)` → `Strategy(id=...)`

**What We Discovered**:
- ❌ Architectural mismatch - tests assume auto-inference, production uses explicit DAG
- ❌ Validation too strict for test scenarios (orphan detection, position signals)
- ❌ Container initialization unclear (empty matrices)

**Status**: **75% complete** (down from 85% after discovering architectural issues)

**Estimated Remaining Work**: ~4-5 hours
- Investigation: 30 min
- Quick wins: 45 min
- Test updates: 2-3 hours
- Validation: 30 min

**Blocker**: Design decision needed on automatic dependency inference vs. explicit DAG

---

**Report Generated**: 2025-11-10
**Previous Report**: PHASE2_TEST_FAILURE_REPORT.md
**Next Steps**: Investigate Strategy.to_pipeline() container initialization
