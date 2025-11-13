# Phase 2 Factor Graph V2 - Container Initialization Investigation

**Date**: 2025-11-11
**Status**: 🔍 INVESTIGATION COMPLETE - Root cause identified
**Previous**: PHASE2_ARCHITECTURE_MISMATCH_ANALYSIS.md
**Investigation**: Strategy.to_pipeline() and FinLabDataFrame initialization behavior

---

## Executive Summary

✅ **Investigation completed** - Container initialization behavior fully understood
🔴 **Design conflict discovered** - Lazy loading vs. eager validation mismatch
🎯 **Root cause identified** - Empty container conflicts with validation assumptions

---

## Investigation: Strategy.to_pipeline() Analysis

### Code Flow (strategy.py:384-472)

```python
def to_pipeline(self, data_module) -> pd.DataFrame:
    """Execute strategy DAG with FinLabDataFrame container."""
    # Step 1: Validate strategy (lines 440-441)
    self.validate()  # ❌ Assumes OHLCV columns exist

    # Step 2: Create empty container (lines 443-445)
    from src.factor_graph.finlab_dataframe import FinLabDataFrame
    container = FinLabDataFrame(data_module=data_module)
    # ⚠️ Container is EMPTY at this point (no matrices pre-loaded)

    # Step 3: Execute factors in topological order (lines 447-463)
    topo_order = list(nx.topological_sort(self.dag))
    for factor_id in topo_order:
        factor = self.factors[factor_id]
        container = factor.execute(container)  # ✅ Factors use lazy loading

    # Step 4: Extract position matrix (lines 465-472)
    return container.get_matrix('position')
```

**Key Finding**: Container created EMPTY, relies on lazy loading during factor execution.

---

## Investigation: FinLabDataFrame Initialization

### Initialization Behavior (finlab_dataframe.py:86-105)

```python
def __init__(self, data_module: Any = None, base_shape: Optional[Tuple[int, int]] = None):
    """Initialize FinLabDataFrame container."""
    self._matrices: Dict[str, pd.DataFrame] = {}  # ⚠️ EMPTY dict
    self._data_module = data_module  # Store reference only
    self._base_shape = base_shape  # None initially
    self._metadata: Dict[str, Any] = {}

    logger.debug(f"Initialized FinLabDataFrame with base_shape={base_shape}")
    # ❌ NO pre-loading of OHLCV data
```

**Key Finding**: Container does NOT pre-load base OHLCV matrices.

### Lazy Loading Mechanism (finlab_dataframe.py:319-360)

```python
def _lazy_load_matrix(self, name: str) -> Optional[pd.DataFrame]:
    """Attempt to lazy load a matrix from the data module."""
    if self._data_module is None:
        return None

    # Map matrix names to FinLab data keys
    finlab_key_map = {
        'close': 'price:收盤價',
        'open': 'price:開盤價',
        'high': 'price:最高價',
        'low': 'price:最低價',
        'volume': 'price:成交股數',
        'market_cap': 'fundamental_features:市值',
        'revenue': 'fundamental_features:營收',
    }

    if name not in finlab_key_map:
        return None

    try:
        finlab_key = finlab_key_map[name]
        matrix = self._data_module.get(finlab_key)
        logger.info(f"Lazy loaded matrix '{name}' from FinLab key '{finlab_key}'")
        return matrix
    except Exception as e:
        logger.warning(f"Failed to lazy load matrix '{name}': {e}")
        return None
```

**Key Finding**: Lazy loading ONLY triggers when `get_matrix()` called.

### get_matrix() Flow (finlab_dataframe.py:156-193)

```python
def get_matrix(self, name: str, lazy_load: bool = True) -> pd.DataFrame:
    """Get a matrix by name from the container."""
    # Check if matrix exists in cache
    if name in self._matrices:
        return self._matrices[name]

    # Try lazy loading if enabled and data_module available
    if lazy_load and self._data_module is not None:
        try:
            matrix = self._lazy_load_matrix(name)
            if matrix is not None:
                self.add_matrix(name, matrix, validate=True)
                return self._matrices[name]
        except Exception as e:
            logger.warning(f"Lazy load failed for matrix '{name}': {e}")

    # Matrix not found
    raise KeyError(
        f"Matrix '{name}' not found in container. "
        f"Available matrices: {list(self._matrices.keys())}"
    )
```

**Key Finding**: Lazy loading happens on-demand during factor execution, NOT during initialization.

---

## The Design Conflict

### Validation Assumption (strategy.py:534-560)

```python
# Check 2: All factor input dependencies satisfied
# Track available columns as we traverse DAG in topological order
# Start with base OHLCV data columns
available_columns = {"open", "high", "low", "close", "volume"}  # ❌ ASSUMPTION

try:
    topo_order = list(nx.topological_sort(self.dag))
except nx.NetworkXError as e:
    raise ValueError(f"Cannot compute topological sort: {str(e)}") from e

for factor_id in topo_order:
    factor = self.factors[factor_id]

    # Check if all inputs are available
    if not factor.validate_inputs(list(available_columns)):
        missing_inputs = [inp for inp in factor.inputs if inp not in available_columns]
        raise ValueError(
            f"Factor '{factor_id}' requires inputs {missing_inputs} "
            f"which are not available. "
            f"Available columns at this point: {sorted(available_columns)}."
        )

    # Add this factor's outputs to available columns
    available_columns.update(factor.outputs)
```

**Problem**: Validation ASSUMES base OHLCV columns exist, but container is EMPTY.

### Reality: Lazy Loading Design

```python
# What actually happens during execution:
# 1. Container created EMPTY
container = FinLabDataFrame(data_module=data_module)
# container._matrices = {}  # EMPTY!

# 2. Factor tries to get 'close'
close = container.get_matrix('close')
# → Triggers lazy loading from data_module
# → Loads 'price:收盤價' from FinLab
# → Adds to container._matrices['close']
```

**Reality**: OHLCV columns lazy-loaded during factor execution, NOT pre-existing.

---

## Root Cause Summary

### The Mismatch

| Component | Assumption | Reality |
|-----------|------------|---------|
| **Strategy.validate()** | OHLCV columns exist at validation time | Container doesn't exist yet |
| **Strategy.to_pipeline()** | Container empty, relies on lazy loading | Validation already checked inputs |
| **FinLabDataFrame** | Lazy load on first `get_matrix()` call | No pre-loading in `__init__` |
| **Tests** | Factors auto-connect via inputs/outputs | Explicit `depends_on` required |

### Two Separate Issues

**Issue 1: Validation vs. Lazy Loading Conflict**
- **Validation (line 535)**: Assumes `{"open", "high", "low", "close", "volume"}` exist
- **Reality (line 445)**: Container is empty dict `{}`
- **Result**: Validation checks phantom columns, not actual container state

**Issue 2: Test Assumption vs. Production Reality** (from PHASE2_ARCHITECTURE_MISMATCH_ANALYSIS.md)
- **Test Assumption**: `add_factor()` auto-connects via input/output matching
- **Production Reality**: Requires explicit `depends_on` parameter
- **Result**: Tests create disconnected DAG nodes → orphaned factors

---

## All Test Failure Categories (Updated)

### Category 1: Orphaned Factors (11 failures)
**Root Cause**: No `depends_on` parameter → disconnected DAG nodes

**Affected Tests** (test_strategy_v2.py):
1. test_single_factor_pipeline - 2 disconnected factors
2. test_multi_factor_pipeline_execution - 3 disconnected factors
3. test_container_creation_from_data_module - 2 disconnected factors
4. test_matrix_flow_through_pipeline - 3 disconnected factors
5. test_position_matrix_extraction - 2 disconnected factors
6. test_invalid_data_module_raises_error - 2 disconnected factors
7. test_parallel_factors_can_execute_any_order - 4 disconnected factors

**Fix**: Add explicit `depends_on` to all `add_factor()` calls

### Category 2: Missing Position Signal (1 failure)
**Test**: test_missing_position_matrix_raises_error

**Root Cause**: Validation catches error BEFORE execution (line 570-576)

**Fix**: Use `skip_validation` parameter or accept validation error

### Category 3: Missing Base Data Connection (2 failures)
**Tests**:
- test_missing_input_matrix_raises_error
- test_factor_execution_order

**Root Cause**: Validation Check 2 requires ALL inputs exist (even for error-testing factors)

**Fix**: Use `skip_validation` parameter for error-handling tests

### Category 4: Empty Container (2 failures)
**Tests**:
- test_factor_validation_error_propagates
- test_factor_with_multiple_outputs

**Root Cause**: Container not populated with base OHLCV data before factor execution

**Analysis**: This is actually EXPECTED behavior (lazy loading design)

**Fix**: Ensure factors properly trigger lazy loading, or tests use mock data_module

### Category 5: Empty Inputs Validation (1 failure)
**Test**: test_factor_with_no_inputs

**Root Cause**: Factor.__post_init__ enforces non-empty inputs list

**Fix**: Update test or allow empty inputs (design decision needed)

### Category 6: Error Message Format (1 failure)
**Test**: test_empty_strategy_raises_error

**Expected**: `"No factors"`
**Actual**: `"Strategy validation failed: Strategy must contain at least one factor"`

**Fix**: Update regex to match new message format

---

## Design Decisions Required

### Decision 1: Validation Strategy

**Option A: Eager Validation (Current Behavior)**
- Validate before execution (line 441)
- Assumes OHLCV columns exist
- Catches configuration errors early
- **Problem**: Conflicts with lazy loading design

**Option B: Lazy Validation**
- Validate during execution (when container populated)
- Check actual container state
- More accurate validation
- **Problem**: Later error detection

**Option C: Split Validation**
- **Static validation** at `validate()`: DAG structure, cycles, dependencies
- **Runtime validation** at `to_pipeline()`: Actual data availability
- Best of both worlds
- **Implementation**: Separate `validate_structure()` and `validate_data(container)`

**Recommendation**: **Option C** - Split validation
- Early DAG structure validation (cycles, orphans, dependencies)
- Runtime data validation (after lazy loading)
- Backward compatible (current `validate()` becomes `validate_structure()`)

### Decision 2: Auto-Dependency Inference (from PHASE2_ARCHITECTURE_MISMATCH_ANALYSIS.md)

**Option A: Implement Auto-Inference**
- Scan existing factors for outputs matching new factor's inputs
- Add `auto_connect=True` parameter (default True)
- Tests work without modification

**Option B: Update Tests**
- Add `depends_on` parameter to all test `add_factor()` calls
- Keep explicit DAG construction
- Tests document actual API usage

**Recommendation**: **Option B** - Update tests to match production
- Explicit is better than implicit (Python zen)
- Current design is correct for DAG library
- Tests should document actual usage

### Decision 3: Empty Container Issue

**Root Cause Analysis**: NOT a bug, but design feature

**Current Design**:
```python
# Container starts empty
container = FinLabDataFrame(data_module=data_module)  # _matrices = {}

# Factor execution triggers lazy loading
close = container.get_matrix('close')  # → Loads 'price:收盤價'
```

**Options**:
1. **Keep lazy loading** (recommended) - Efficient, only loads needed data
2. **Pre-load OHLCV** - Wastes memory, simpler for tests
3. **Add helper method** - `container.preload_base_data()` for testing

**Recommendation**: **Option 1** - Keep lazy loading
- Efficient design (only load what's needed)
- Fix tests to properly mock data_module
- Document lazy loading behavior

---

## Proposed Fix Plan (Revised)

### Phase 1: Validation Split (2-3 hours)

**Step 1.1**: Separate validation into two methods (45 min)
```python
class Strategy:
    def validate_structure(self) -> bool:
        """Validate DAG structure (static checks)."""
        # Check 0: At least one factor
        # Check 1: DAG is acyclic
        # Check 4: No orphaned factors
        # Check 5: No duplicate outputs
        return True

    def validate_data(self, container: FinLabDataFrame) -> bool:
        """Validate data availability (runtime checks)."""
        # Check 2: All factor inputs available (check actual container)
        # Check 3: At least one position signal factor
        return True

    def validate(self) -> bool:
        """Backward-compatible: static validation only."""
        return self.validate_structure()
```

**Step 1.2**: Update `to_pipeline()` to use split validation (30 min)
```python
def to_pipeline(self, data_module) -> pd.DataFrame:
    # Static validation (DAG structure)
    self.validate_structure()

    # Create container
    container = FinLabDataFrame(data_module=data_module)

    # Execute factors (lazy loading happens here)
    for factor_id in topo_order:
        container = factor.execute(container)

    # Runtime validation (data availability)
    self.validate_data(container)

    # Extract position
    return container.get_matrix('position')
```

**Step 1.3**: Add tests for split validation (45 min)

**Step 1.4**: Add `skip_validation` parameter (30 min)
```python
def to_pipeline(self, data_module, skip_validation: bool = False) -> pd.DataFrame:
    if not skip_validation:
        self.validate_structure()
    # ... rest of execution
```

### Phase 2: Test Updates (3-4 hours)

**Step 2.1**: Add `depends_on` to all test `add_factor()` calls (2 hours)
- 11 orphaned factor tests
- ~30 call sites need updating

**Step 2.2**: Update error-handling tests (1 hour)
- Use `skip_validation` for tests that need to bypass validation
- Tests: missing_input, factor_execution_order

**Step 2.3**: Fix error message assertions (30 min)
- Update regex patterns to match new messages
- Test: test_empty_strategy_raises_error

**Step 2.4**: Fix container behavior tests (30 min)
- Ensure proper mock data_module setup
- Tests: factor_validation_error_propagates, factor_with_multiple_outputs

### Phase 3: Documentation (30 min)

**Step 3.1**: Update design documentation
- Document lazy loading behavior
- Document split validation approach
- Update API examples

**Step 3.2**: Create PHASE2_FIX_SUMMARY.md
- Summarize all changes
- Document validation logic split
- Provide migration guide for users

---

## Status Summary

**What We Know**:
- ✅ Container initialization behavior fully understood (empty + lazy loading)
- ✅ Validation conflict identified (eager validation vs. lazy loading)
- ✅ Root causes for all 18 test failures identified
- ✅ Design decisions clarified with recommendations

**What Needs Fixing**:
- ❌ Split validation into static + runtime (2-3 hours)
- ❌ Update tests with explicit `depends_on` (2 hours)
- ❌ Fix error-handling tests with `skip_validation` (1 hour)
- ❌ Update error message assertions (30 min)
- ❌ Documentation updates (30 min)

**Estimated Total Work**: ~6-7 hours

**Current Completion**: 75% (investigation complete, implementation pending)

**Blockers**: None - clear path forward with split validation approach

---

**Report Generated**: 2025-11-11
**Investigation Method**: Code reading + analysis
**Files Analyzed**:
- src/factor_graph/strategy.py (834 lines, lines 384-607 critical)
- src/factor_graph/finlab_dataframe.py (369 lines, lines 86-360 critical)
- tests/factor_graph/test_strategy_v2.py (504 lines)

**Next Steps**: Implement Phase 1 (split validation) before test updates
