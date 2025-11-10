# Factor Graph Matrix-Native Redesign - Development Specification

**Version:** 2.0.0
**Date:** 2025-11-10
**Status:** Ready for Implementation
**Phase:** Phase 2 - Matrix-Native Architecture
**Priority:** High
**Effort Estimate:** 40 hours (1 week full-time)

---

## Executive Summary

This specification defines the Phase 2 redesign of the Factor Graph system to natively support FinLab's Dates×Symbols matrix format. Phase 1 temporarily disabled Factor Graph via configuration flag (completed 2025-11-10). This document provides complete architectural design, implementation roadmap, and comprehensive test strategy for Claude Cloud to implement.

**Problem Statement:** Factor Graph expects Observations×Features DataFrames with 1D columns, but FinLab provides Dates×Symbols matrices (4563×2661 2D arrays), causing execution failure.

**Solution:** Redesign Factor Graph with matrix-native container, eliminating DataFrame column assumptions.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Architecture Design](#architecture-design)
3. [Implementation Roadmap](#implementation-roadmap)
4. [Test Strategy](#test-strategy)
5. [Acceptance Criteria](#acceptance-criteria)
6. [Risk Management](#risk-management)
7. [Deployment Plan](#deployment-plan)

---

## Requirements

### Functional Requirements

**FR-1: Matrix Container**
- Create FinLabDataFrame wrapper for multiple Dates×Symbols matrices
- Support add_matrix(), get_matrix(), has_matrix(), list_matrices() operations
- Validate shape consistency across all matrices
- Store data_module reference for additional data loading

**FR-2: Strategy Pipeline**
- Modify Strategy.to_pipeline() to accept data module instead of DataFrame
- Pass FinLabDataFrame container through factor DAG
- Extract final position matrix for backtest executor
- Maintain topological execution order

**FR-3: Factor Execution**
- Update Factor.execute() to validate matrix existence instead of columns
- Pass container to factor logic functions
- Return updated container with new matrices
- Preserve existing error handling patterns

**FR-4: Factor Logic Migration**
- Refactor 13 factors to work with matrix container:
  - 4 Momentum factors (momentum, RSI, volatility, volume momentum)
  - 4 Turtle factors (ATR, breakout, dual MA, position sizing)
  - 5 Exit factors (trailing stop, profit target, time exit, drawdown exit, combined)
- Remove DataCache workarounds
- Implement vectorized operations where possible

### Non-Functional Requirements

**NFR-1: Performance**
- Execution time ≤ 1.2x template baseline
- Memory usage ≤ 150MB peak (97MB per matrix + overhead)
- Vectorized operations for computational efficiency

**NFR-2: Reliability**
- All 115 tests passing with >90% code coverage
- Graceful error handling with clear messages
- No silent failures or data corruption

**NFR-3: Maintainability**
- Clean API with proper abstractions
- Comprehensive documentation
- Backward compatibility via feature flag

**NFR-4: Testability**
- Test fixtures for common scenarios
- Mock support for external dependencies
- Performance benchmarks for validation

---

## Architecture Design

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│ BacktestExecutor                                            │
│  execute_factor_graph_strategy(strategy, data_module)      │
└──────────────────────┬──────────────────────────────────────┘
                       │ passes data_module
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Strategy                                                    │
│  to_pipeline(data_module) → position_matrix                │
│    1. Create FinLabDataFrame(data_module)                  │
│    2. Execute factors in topological order                 │
│    3. Extract container.get_matrix('position')             │
└──────────────────────┬──────────────────────────────────────┘
                       │ for each factor in DAG
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Factor                                                      │
│  execute(container) → updated_container                    │
│    1. Validate input matrices exist                        │
│    2. Call self.logic(container, parameters)              │
│    3. Return updated container                             │
└──────────────────────┬──────────────────────────────────────┘
                       │ logic function
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ Factor Logic (13 implementations)                          │
│  _momentum_logic(container, params)                        │
│    1. Load matrices: close = container.get_matrix('close')│
│    2. Compute: momentum = close / close.shift(20) - 1     │
│    3. Store: container.add_matrix('momentum', momentum)   │
└─────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. FinLabDataFrame Container

**File:** `src/factor_graph/finlab_dataframe.py` (NEW)

```python
class FinLabDataFrame:
    """Container for multiple Dates×Symbols matrices.

    Attributes:
        _matrices (Dict[str, pd.DataFrame]): Named matrices storage
        _data_module: FinLab data module for additional loading
        _base_shape (Tuple[int, int]): Expected (dates, symbols) shape
    """

    def __init__(self, data_module=None):
        """Initialize empty container.

        Args:
            data_module: FinLab data module (optional)
        """
        self._matrices: Dict[str, pd.DataFrame] = {}
        self._data_module = data_module
        self._base_shape: Optional[Tuple[int, int]] = None

    def add_matrix(self, name: str, matrix: pd.DataFrame) -> None:
        """Add named matrix to container.

        Args:
            name: Matrix identifier
            matrix: Dates×Symbols DataFrame

        Raises:
            ValueError: If matrix shape doesn't match existing matrices
        """
        if not isinstance(matrix, pd.DataFrame):
            raise TypeError(f"Expected DataFrame, got {type(matrix)}")

        if self._base_shape is None:
            self._base_shape = matrix.shape
        elif matrix.shape != self._base_shape:
            raise ValueError(
                f"Shape mismatch: expected {self._base_shape}, got {matrix.shape}"
            )

        self._matrices[name] = matrix

    def get_matrix(self, name: str) -> pd.DataFrame:
        """Retrieve matrix by name.

        Args:
            name: Matrix identifier

        Returns:
            Dates×Symbols DataFrame

        Raises:
            KeyError: If matrix doesn't exist
        """
        if name not in self._matrices:
            raise KeyError(f"Matrix '{name}' not found")
        return self._matrices[name]

    def has_matrix(self, name: str) -> bool:
        """Check if matrix exists.

        Args:
            name: Matrix identifier

        Returns:
            True if matrix exists
        """
        return name in self._matrices

    def list_matrices(self) -> List[str]:
        """List all matrix names.

        Returns:
            List of matrix identifiers
        """
        return list(self._matrices.keys())
```

#### 2. Strategy Pipeline Modification

**File:** `src/factor_graph/strategy.py` (MODIFIED)

**Current Code (LINE 446-470):**
```python
def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
    """Execute strategy DAG."""
    result = pd.DataFrame()  # ❌ BUG: Creates empty DataFrame
    self._data_module = data  # ⚠️ Stored but unused

    for factor_id in nx.topological_sort(self.dag):
        factor = self.factors[factor_id]
        try:
            result = factor.execute(result)
        except Exception as e:
            raise RuntimeError(f"Pipeline execution failed at factor '{factor_id}': {e}")

    return result
```

**New Implementation:**
```python
def to_pipeline(self, data_module) -> pd.DataFrame:
    """Execute strategy DAG with matrix container.

    Args:
        data_module: FinLab data module

    Returns:
        Position DataFrame (final 'position' matrix)

    Raises:
        RuntimeError: If factor execution fails
        KeyError: If final position matrix missing
    """
    from src.factor_graph.finlab_dataframe import FinLabDataFrame

    # Create matrix container with data module
    container = FinLabDataFrame(data_module)

    # Execute factors in topological order
    for factor_id in nx.topological_sort(self.dag):
        factor = self.factors[factor_id]
        try:
            container = factor.execute(container)
        except Exception as e:
            raise RuntimeError(
                f"Pipeline execution failed at factor '{factor_id}': {e}"
            ) from e

    # Extract final position matrix
    if not container.has_matrix('position'):
        raise KeyError("Strategy did not produce 'position' matrix")

    return container.get_matrix('position')
```

#### 3. Factor Execution Modification

**File:** `src/factor_graph/factor.py` (MODIFIED)

**Current Code (LINE 209-232):**
```python
def execute(self, data: pd.DataFrame) -> pd.DataFrame:
    """Execute factor logic."""
    # Validate inputs are available
    if hasattr(data, 'columns'):
        missing = [inp for inp in self.inputs if inp not in data.columns]
        if missing:
            raise KeyError(f"Factor '{self.id}' requires columns {self.inputs}")

    # Execute logic
    result = self.logic(data, self.parameters)

    # Validate outputs were generated
    missing_outputs = [out for out in self.outputs if out not in result.columns]
    if missing_outputs:
        raise RuntimeError(f"Factor '{self.id}' failed to generate outputs {missing_outputs}")

    return result
```

**New Implementation:**
```python
def execute(self, container: 'FinLabDataFrame') -> 'FinLabDataFrame':
    """Execute factor logic with matrix container.

    Args:
        container: Matrix container with inputs

    Returns:
        Updated container with new matrices

    Raises:
        KeyError: If required input matrices missing
        RuntimeError: If logic execution fails
    """
    from src.factor_graph.finlab_dataframe import FinLabDataFrame

    # Validate input matrices exist
    missing = [inp for inp in self.inputs if not container.has_matrix(inp)]
    if missing:
        raise KeyError(
            f"Factor '{self.id}' requires matrices {missing} which are not available"
        )

    # Execute logic (modifies container in-place)
    try:
        self.logic(container, self.parameters)
    except Exception as e:
        raise RuntimeError(
            f"Factor '{self.id}' execution failed: {e}"
        ) from e

    # Validate outputs were generated
    missing_outputs = [out for out in self.outputs if not container.has_matrix(out)]
    if missing_outputs:
        raise RuntimeError(
            f"Factor '{self.id}' failed to generate matrices {missing_outputs}"
        )

    return container
```

#### 4. Factor Logic Migration Examples

**Momentum Factor (BEFORE):**
```python
def _momentum_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """Calculate momentum signal."""
    # ❌ Uses DataCache workaround
    cache = DataCache.get_instance()
    close = cache.get('price:收盤價', verbose=False)

    window = parameters.get('window', 20)
    momentum = (close / close.shift(window)) - 1

    # ❌ Cannot assign 2D matrix to 1D column
    data['momentum'] = momentum
    return data
```

**Momentum Factor (AFTER):**
```python
def _momentum_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """Calculate momentum signal.

    Args:
        container: Matrix container (modified in-place)
        parameters: {'window': int}
    """
    # Load close price matrix from container
    close = container.get_matrix('close')

    # Calculate momentum
    window = parameters.get('window', 20)
    momentum = (close / close.shift(window)) - 1

    # Store result matrix
    container.add_matrix('momentum', momentum)
```

**Exit Factor (BEFORE - Row Iteration):**
```python
def _trailing_stop_logic(data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame:
    """Apply trailing stop exits."""
    # ❌ O(n) row iteration, not vectorized
    for idx in range(len(data)):
        if data['positions'].iloc[idx]:
            # ... complex position tracking logic
            pass
    return data
```

**Exit Factor (AFTER - Vectorized):**
```python
def _trailing_stop_logic(container: FinLabDataFrame, parameters: Dict[str, Any]) -> None:
    """Apply trailing stop exits (vectorized).

    Args:
        container: Matrix container with 'position' and 'close' matrices
        parameters: {'stop_pct': float}
    """
    position = container.get_matrix('position')
    close = container.get_matrix('close')
    stop_pct = parameters.get('stop_pct', 0.05)

    # Vectorized trailing stop calculation
    # Track highest price since entry
    entry_price = close.where(position).ffill()
    trailing_stop = entry_price * (1 - stop_pct)

    # Generate exit signal when close drops below trailing stop
    exit_signal = (close < trailing_stop) & (position > 0)

    container.add_matrix('exit', exit_signal)
```

---

## Implementation Roadmap

### Phase 1: Foundation (8 hours)

**Day 1 Morning (4 hours)**

**Task 1.1: Create FinLabDataFrame Container (2h)**
- File: `src/factor_graph/finlab_dataframe.py`
- Implement: `__init__`, `add_matrix`, `get_matrix`, `has_matrix`, `list_matrices`
- Validation: Shape consistency checking
- Error handling: Clear error messages

**Task 1.2: Unit Tests for Container (1h)**
- File: `tests/factor_graph/test_finlab_dataframe.py`
- Test: Basic operations (add/get/has)
- Test: Shape validation (match/mismatch)
- Test: Error cases (missing matrix, invalid shape)
- Coverage: >95% for container class

**Task 1.3: BacktestExecutor Integration (1h)**
- File: `src/backtest/executor.py`
- Modify: `execute_factor_graph_strategy` (LINE 498)
- Change: Pass `data` module instead of DataFrame
- Extract: Final position matrix from container

**Day 1 Afternoon (4 hours)**

**Task 1.4: Strategy.to_pipeline Refactor (4h)**
- File: `src/factor_graph/strategy.py`
- Modify: `to_pipeline` method (LINE 446-470)
- Create: FinLabDataFrame container initialization
- Update: Factor execution loop
- Extract: Final position matrix
- Test: Integration with container

### Phase 2: Core Architecture (6 hours)

**Day 2 Morning (2 hours)**

**Task 2.1: Factor.execute Refactor (2h)**
- File: `src/factor_graph/factor.py`
- Modify: `execute` method (LINE 209-232)
- Update: Input validation (matrices instead of columns)
- Update: Output validation (matrices instead of columns)
- Preserve: Error handling patterns

**Day 2 Afternoon (4 hours)**

**Task 2.2: Pipeline Integration Tests (4h)**
- File: `tests/factor_graph/test_strategy_pipeline.py`
- Test: DAG execution order
- Test: Matrix passing between factors
- Test: Error propagation
- Test: Final position extraction
- Coverage: >90% for pipeline logic

### Phase 3: Factor Migration (16 hours)

**Day 2-3 (8 hours)**

**Task 3.1: Momentum Factors (4h)**
- File: `src/factor_library/momentum_factors.py`
- Refactor: `_momentum_logic` (remove DataCache)
- Refactor: `_rsi_logic`
- Refactor: `_volatility_logic`
- Refactor: `_volume_momentum_logic`
- Test: Unit tests for each factor

**Task 3.2: Turtle Factors (4h)**
- File: `src/factor_library/turtle_factors.py`
- Refactor: `_atr_logic`
- Refactor: `_breakout_logic`
- Refactor: `_dual_ma_filter_logic`
- Refactor: `_position_sizing_logic`
- Test: Unit tests for each factor

**Day 3-4 (8 hours)**

**Task 3.3: Exit Factors (8h) ← CRITICAL PATH**
- File: `src/factor_library/exit_factors.py`
- Refactor: `_trailing_stop_logic` (vectorize position tracking)
- Refactor: `_profit_target_logic`
- Refactor: `_time_exit_logic`
- Refactor: `_drawdown_exit_logic`
- Refactor: `_combined_exit_logic`
- Test: Comprehensive unit tests (30 tests)
- Focus: Vectorization validation, edge cases

### Phase 4: Testing & Validation (10 hours)

**Day 4 Afternoon (6 hours)**

**Task 4.1: Component Unit Tests (4h)**
- File: `tests/factor_library/test_momentum_factors.py`
- File: `tests/factor_library/test_turtle_factors.py`
- File: `tests/factor_library/test_exit_factors.py`
- Total: 60 tests across all factors
- Coverage: >90% for all factor logic

**Task 4.2: Integration Tests (2h)**
- File: `tests/integration/test_factor_graph_integration.py`
- Test: Multi-factor pipelines
- Test: Real-world scenarios
- Test: Edge cases (empty matrices, single symbol)

**Day 5 Morning (4 hours)**

**Task 4.3: E2E Tests (2h)**
- File: `tests/e2e/test_factor_graph_e2e.py`
- Test: Full backtest execution with real FinLab data
- Test: Multi-strategy scenarios
- Test: Error recovery

**Task 4.4: Performance Benchmarks (2h)**
- File: `tests/performance/test_factor_graph_performance.py`
- Benchmark: vs template baseline (target: ≤1.2x)
- Profile: Memory usage (target: ≤150MB)
- Profile: Execution time by factor type

### Phase 5: Deployment & Documentation (6 hours)

**Day 5 Afternoon (6 hours)**

**Task 5.1: Feature Flag Update (1h)**
- File: `experiments/llm_learning_validation/config.yaml`
- Update: `experimental.use_factor_graph: true`
- Add: `experimental.factor_graph_version: "v2"`
- Document: Rollback procedure

**Task 5.2: Migration & Rollout (2h)**
- Create: Backward compatibility tests
- Move: Old Factor Graph to `deprecated/`
- Validate: No breaking changes to LLM/template systems
- Test: Feature flag toggle

**Task 5.3: Documentation (3h)**
- Create: Architecture Decision Record (ADR)
- Create: API documentation for FinLabDataFrame
- Create: Migration guide for future factor development
- Create: Troubleshooting guide
- Update: README with Phase 2 changes

---

## Test Strategy

### Test Pyramid

```
              E2E (5 tests)
             /              \
        Integration (15)
       /                    \
   Component (30)
  /                          \
Unit Tests (65)
```

**Total: 115 tests**
- Unit: 65 tests (57%) - Basic operations, validation, error handling
- Component: 30 tests (26%) - Factor logic, computations
- Integration: 15 tests (13%) - Multi-factor, real scenarios
- E2E: 5 tests (4%) - Full backtest execution

### Critical Test Areas

#### A. FinLabDataFrame Container (20 tests)

**test_finlab_dataframe.py**

```python
class TestBasicOperations:
    def test_add_matrix_success()
    def test_get_matrix_existing()
    def test_get_matrix_missing()
    def test_has_matrix_true()
    def test_has_matrix_false()
    def test_list_matrices_empty()
    def test_list_matrices_multiple()
    def test_add_matrix_overwrite()

class TestShapeValidation:
    def test_shape_validation_match()
    def test_shape_validation_mismatch_rows()
    def test_shape_validation_mismatch_cols()
    def test_empty_dataframe_allowed()
    def test_single_row_matrix()
    def test_single_col_matrix()

class TestDataModuleIntegration:
    def test_data_module_storage()
    def test_data_module_none()
    def test_data_module_access()
    def test_lazy_loading_from_module()
    def test_cache_integration()
    def test_module_fallback()
```

#### B. Strategy Pipeline (15 tests)

**test_strategy_pipeline.py**

```python
class TestDAGExecution:
    def test_topological_sort_order()
    def test_single_factor_pipeline()
    def test_linear_pipeline()
    def test_branching_pipeline()
    def test_diamond_dependency()
    def test_circular_dependency_detection()

class TestMatrixPassing:
    def test_matrix_passing_between_factors()
    def test_matrix_accumulation()
    def test_intermediate_matrix_availability()
    def test_missing_input_matrix()
    def test_multiple_output_matrices()

class TestErrorHandling:
    def test_factor_execution_failure()
    def test_missing_position_matrix()
    def test_empty_dag()
    def test_final_extraction()
```

#### C. Factor Logic (60 tests)

**test_momentum_factors.py (15 tests)**
```python
class TestMomentumLogic:
    def test_momentum_calculation_basic()
    def test_momentum_edge_case_insufficient_data()
    def test_momentum_nan_handling()
    def test_momentum_zero_prices()
    def test_momentum_negative_returns()

class TestRSILogic:
    def test_rsi_standard_14_period()
    def test_rsi_overbought_oversold()
    def test_rsi_boundary_values()

class TestVolatilityLogic:
    def test_volatility_rolling_std()
    def test_volatility_zero_variance()

class TestVolumeMomentumLogic:
    def test_volume_momentum_calculation()
    def test_volume_momentum_missing_volume()
    def test_volume_momentum_zero_volume()
```

**test_turtle_factors.py (15 tests)**
```python
class TestATRLogic:
    def test_atr_standard_calculation()
    def test_atr_true_range_components()
    def test_atr_missing_data()

class TestBreakoutLogic:
    def test_breakout_high_channel()
    def test_breakout_low_channel()
    def test_breakout_no_breakout()

class TestDualMAFilter:
    def test_dual_ma_crossover()
    def test_dual_ma_golden_cross()
    def test_dual_ma_death_cross()

class TestPositionSizing:
    def test_position_sizing_atr_based()
    def test_position_sizing_max_position()
    def test_position_sizing_zero_atr()
```

**test_exit_factors.py (30 tests) ← CRITICAL**
```python
class TestTrailingStopLogic:
    def test_trailing_stop_basic()
    def test_trailing_stop_vectorized()
    def test_trailing_stop_multiple_entries()
    def test_trailing_stop_no_positions()
    def test_trailing_stop_all_positions()
    def test_trailing_stop_partial_exits()
    def test_trailing_stop_edge_case_single_day()

class TestProfitTargetLogic:
    def test_profit_target_basic()
    def test_profit_target_not_reached()
    def test_profit_target_exceeded()
    def test_profit_target_matrix_operations()

class TestTimeExitLogic:
    def test_time_exit_max_holding()
    def test_time_exit_before_max()
    def test_time_exit_date_based()

class TestDrawdownExitLogic:
    def test_drawdown_exit_from_peak()
    def test_drawdown_exit_rolling_max()
    def test_drawdown_exit_no_drawdown()

class TestCombinedExitLogic:
    def test_combined_any_condition()
    def test_combined_all_conditions()
    def test_combined_priority_ordering()
    def test_combined_complex_scenario()
```

#### D. Integration & E2E (20 tests)

**test_integration.py (15 tests)**
```python
class TestMultiFactorPipeline:
    def test_momentum_to_turtle_pipeline()
    def test_full_entry_exit_pipeline()
    def test_parallel_factor_branches()
    def test_error_propagation()

class TestRealWorldScenarios:
    def test_taiwan_stock_data()
    def test_empty_trading_days()
    def test_delisted_stocks()
    def test_split_adjusted_prices()

class TestPerformanceComparison:
    def test_vs_template_baseline()
    def test_memory_usage()
    def test_execution_time()
```

**test_e2e.py (5 tests)**
```python
def test_e2e_backtest_execution()
def test_e2e_multi_strategy()
def test_e2e_performance_validation()
def test_e2e_error_recovery()
def test_e2e_feature_flag_toggle()
```

### Test Infrastructure

**Fixtures:**
```python
@pytest.fixture
def create_test_matrix():
    """Create test matrix with specified dimensions."""
    def _create(dates=100, symbols=50, value_range=(0, 100)):
        return pd.DataFrame(
            np.random.uniform(*value_range, (dates, symbols)),
            index=pd.date_range('2020-01-01', periods=dates),
            columns=[f'STOCK_{i}' for i in range(symbols)]
        )
    return _create

@pytest.fixture
def create_position_matrix():
    """Create position matrix (0/1 values)."""
    def _create(dates=100, symbols=50, fill_rate=0.3):
        return pd.DataFrame(
            np.random.choice([0, 1], (dates, symbols), p=[1-fill_rate, fill_rate]),
            index=pd.date_range('2020-01-01', periods=dates),
            columns=[f'STOCK_{i}' for i in range(symbols)]
        )
    return _create

@pytest.fixture
def mock_data_module(mocker):
    """Mock FinLab data module."""
    mock = mocker.Mock()
    mock.get = mocker.Mock(return_value=create_test_matrix())
    return mock
```

---

## Acceptance Criteria

### Functional Acceptance

**AC-1: Container Operations**
- [ ] FinLabDataFrame can store multiple matrices
- [ ] Shape validation prevents incompatible matrices
- [ ] get_matrix raises KeyError for missing matrices
- [ ] list_matrices returns all stored matrix names

**AC-2: Pipeline Execution**
- [ ] Strategy.to_pipeline accepts data module (not DataFrame)
- [ ] Factors execute in topological DAG order
- [ ] Matrices pass correctly between factors
- [ ] Final position matrix extracted successfully

**AC-3: Factor Logic**
- [ ] All 13 factors work with matrix container
- [ ] No DataCache workarounds remain
- [ ] Vectorized operations used where possible
- [ ] Error messages are clear and actionable

**AC-4: Integration**
- [ ] BacktestExecutor integration works end-to-end
- [ ] Multi-factor pipelines execute correctly
- [ ] Real FinLab data processes without errors
- [ ] Feature flag toggle works (enable/disable)

### Quality Acceptance

**AC-5: Test Coverage**
- [ ] Overall code coverage >90%
- [ ] All 115 tests passing
- [ ] No flaky or intermittent test failures
- [ ] Performance benchmarks within targets

**AC-6: Performance**
- [ ] Execution time ≤ 1.2x template baseline
- [ ] Memory usage ≤ 150MB peak
- [ ] No memory leaks in extended runs
- [ ] Profiling shows no unexpected bottlenecks

**AC-7: Documentation**
- [ ] Architecture Decision Record complete
- [ ] API documentation for FinLabDataFrame
- [ ] Migration guide for future factors
- [ ] Troubleshooting guide with common issues

**AC-8: Deployment**
- [ ] Feature flag functional (true/false)
- [ ] Rollback procedure tested and documented
- [ ] No breaking changes to existing systems
- [ ] Backward compatibility validated

---

## Risk Management

### Identified Risks

**Risk 1: Exit Factor Vectorization Complexity (HIGH)**
- **Issue:** Vectorizing position tracking is non-trivial
- **Impact:** 8 hours on critical path, could block work
- **Probability:** Medium
- **Mitigation:**
  - Start exit factors early (parallel with momentum/turtle)
  - Prototype vectorization approach first (2h spike)
  - Fallback: Row-by-row with optimization later
- **Contingency:** Accept row-iteration for Phase 2, optimize in Phase 2.5

**Risk 2: Performance Degradation (MEDIUM)**
- **Issue:** Matrix operations might be slower than expected
- **Impact:** User experience, adoption resistance
- **Probability:** Low
- **Mitigation:**
  - Benchmark early (after Phase 1 complete)
  - Profile bottlenecks with cProfile
  - Optimize critical paths (caching, vectorization)
  - Accept 1.2x slowdown as acceptable threshold
- **Contingency:** Profile and optimize hot paths, consider Numba/Cython

**Risk 3: Shape Mismatch Edge Cases (MEDIUM)**
- **Issue:** Different date ranges or symbol lists
- **Impact:** Runtime errors in production
- **Probability:** Medium
- **Mitigation:**
  - Comprehensive shape validation in container
  - Unit tests for all edge cases
  - Clear error messages for debugging
- **Contingency:** Additional validation layer, graceful degradation

**Risk 4: Breaking Changes to Existing Code (LOW)**
- **Issue:** Might affect template or LLM systems
- **Impact:** Regression in working features
- **Probability:** Very Low
- **Mitigation:**
  - Feature flag for gradual rollout
  - Keep old code in deprecated/
  - Regression tests before cutover
- **Contingency:** Immediate rollback via feature flag

### Contingency Plans

**If behind schedule after Phase 2 (10h mark):**
- Reduce factor migration scope (defer exit factors)
- Focus on momentum + turtle first (8h total)
- Exit factors as Phase 2.5 follow-up
- Maintain test coverage for implemented factors

**If performance unacceptable (>1.5x baseline):**
- Profile and identify hot paths
- Optimize critical loops with vectorization
- Consider Numba for exit factor logic
- Accept degradation with optimization roadmap

**If integration issues discovered:**
- Rollback via feature flag (set to false)
- Debug in isolation branch
- Incremental integration by factor type
- Additional integration tests as needed

---

## Deployment Plan

### Pre-Deployment Checklist

**Code Quality:**
- [ ] All 115 tests passing
- [ ] Code coverage >90%
- [ ] No linting errors
- [ ] Code review completed

**Performance:**
- [ ] Benchmarks within targets (≤1.2x)
- [ ] Memory profiling acceptable (≤150MB)
- [ ] No performance regressions identified
- [ ] Load testing completed

**Documentation:**
- [ ] ADR published
- [ ] API documentation complete
- [ ] Migration guide available
- [ ] Troubleshooting guide ready

**Testing:**
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Performance tests passing

### Deployment Steps

**Step 1: Code Merge**
1. Create feature branch: `feature/factor-graph-v2-matrix-native`
2. Implement all changes per specification
3. Pass all tests and code review
4. Merge to main branch

**Step 2: Feature Flag Configuration**
1. Update `config.yaml`:
   ```yaml
   experimental:
     use_factor_graph: true  # Enable v2
     factor_graph_version: "v2"  # Matrix-native
   ```
2. Commit configuration change
3. Deploy to development environment

**Step 3: Validation Testing**
1. Run full test suite in dev environment
2. Execute sample backtests
3. Verify performance metrics
4. Check error logs for issues

**Step 4: Staged Rollout**
1. Enable in development (Day 1)
2. Enable in staging (Day 2)
3. Monitor metrics and logs
4. Enable in production (Day 3) if successful

**Step 5: Monitoring**
1. Track execution time metrics
2. Monitor memory usage
3. Check error rates
4. Review user feedback

### Rollback Procedure

**If issues detected:**
1. Set `use_factor_graph: false` in config.yaml
2. Restart affected services
3. Verify fallback to LLM/template generation
4. Investigate issue in isolation
5. Fix and redeploy when ready

**Rollback triggers:**
- Error rate >5% for Factor Graph strategies
- Performance degradation >2x baseline
- Critical bugs discovered
- Data corruption or incorrect results

---

## Success Metrics

### Technical Metrics

**Code Quality:**
- Test coverage: >90% (Target: 95%)
- Tests passing: 115/115 (100%)
- Code review score: >8/10
- Linting errors: 0

**Performance:**
- Execution time: ≤1.2x template baseline
- Memory peak: ≤150MB
- Vectorization ratio: >80% for exit factors
- Throughput: ≥500 strategies/hour

**Reliability:**
- Error rate: <1%
- Uptime: >99.9%
- Successful backtest rate: >95%
- Rollback incidents: 0

### Business Metrics

**Adoption:**
- Factor Graph usage: >30% after 1 week
- LLM validation study: Unblocked
- User satisfaction: >85%
- Feature flag enabled: Yes

**Value Delivery:**
- Implementation time: ≤40 hours
- Technical debt reduction: High
- System maintainability: Improved
- Future extensibility: Enhanced

---

## References

### Documentation

1. **Phase 1 Completion:** `docs/PHASE1_COMPLETION_SUMMARY.md`
2. **Architecture Analysis:** `docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md` (93KB)
3. **Debug Record:** `docs/DEBUG_RECORD_LLM_AUTO_FIX.md`
4. **Status Document:** `LLM_VALIDATION_STATUS.md`

### Code References

**Current Implementation:**
- Strategy: `src/factor_graph/strategy.py:446-470`
- Factor: `src/factor_graph/factor.py:209-232`
- Momentum Factors: `src/factor_library/momentum_factors.py`
- Exit Factors: `src/factor_library/exit_factors.py`
- Turtle Factors: `src/factor_library/turtle_factors.py`

**Configuration:**
- Experiment Config: `experiments/llm_learning_validation/config.yaml:87-94`
- Executor: `src/backtest/executor.py:498`

### External Dependencies

- **pandas**: DataFrame operations
- **numpy**: Numerical computations
- **NetworkX**: DAG topology
- **pytest**: Testing framework
- **pytest-benchmark**: Performance testing
- **FinLab API**: Data provider

---

## Appendix A: Complete File List

### New Files (1)
- `src/factor_graph/finlab_dataframe.py` (200 lines)

### Modified Files (6)
- `src/factor_graph/strategy.py` (~50 lines modified)
- `src/factor_graph/factor.py` (~30 lines modified)
- `src/factor_library/momentum_factors.py` (~100 lines modified)
- `src/factor_library/turtle_factors.py` (~100 lines modified)
- `src/factor_library/exit_factors.py` (~200 lines modified)
- `src/backtest/executor.py` (~10 lines modified)

### Test Files (8)
- `tests/factor_graph/test_finlab_dataframe.py` (20 tests)
- `tests/factor_graph/test_strategy_pipeline.py` (15 tests)
- `tests/factor_library/test_momentum_factors.py` (15 tests)
- `tests/factor_library/test_turtle_factors.py` (15 tests)
- `tests/factor_library/test_exit_factors.py` (30 tests)
- `tests/integration/test_factor_graph_integration.py` (15 tests)
- `tests/e2e/test_factor_graph_e2e.py` (5 tests)
- `tests/performance/test_factor_graph_performance.py` (3 benchmarks)

### Documentation Files (4)
- `docs/ADR_FACTOR_GRAPH_V2.md` (Architecture Decision Record)
- `docs/API_FINLAB_DATAFRAME.md` (API documentation)
- `docs/MIGRATION_GUIDE_FACTOR_GRAPH.md` (Migration guide)
- `docs/TROUBLESHOOTING_FACTOR_GRAPH.md` (Troubleshooting)

**Total Lines Modified:** ~690 lines across 6 files
**Total Test Lines:** ~2000 lines across 8 files
**Total Documentation:** ~500 lines across 4 files

---

## Appendix B: Expert Analysis Summary

Based on zen testgen expert analysis, additional considerations:

### Critical Bug Identified

**Strategy.to_pipeline LINE 446:**
```python
result = pd.DataFrame()  # ❌ CRITICAL BUG
```

This creates an empty DataFrame, discarding input data. The expert analysis confirms this is the root cause of the architectural issue. **This must be the first fix in Phase 1.**

### Test Priorities from Expert

1. **Strategy validation** - Highest priority, complex logic, many branches
2. **Exit factor vectorization** - Critical for correctness and performance
3. **DAG integrity** - Fundamental to system reliability
4. **Factor.execute contract** - Base functionality, affects all factors

### Additional Test Scenarios

The expert identified these critical test cases:

```python
def test_to_pipeline_fails_on_factor_requiring_base_data_due_to_bug():
    """Explicitly surfaces the LINE 446 bug."""
    # This test should FAIL with current code
    # Will PASS after bug fix

def test_validate_fails_for_orphaned_factors():
    """Ensures all factors in connected component."""

def test_validate_fails_for_duplicate_output_columns():
    """Prevents ambiguity and race conditions."""
```

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-11-10 | Claude Code + Zen MCP | Initial specification |
| 2.0.0 | 2025-11-10 | Claude Code + Zen Planner + Zen Testgen | Complete implementation specification |

---

**Document Status:** Ready for Implementation by Claude Cloud
**Approved By:** Phase 1 Complete, Analysis Complete, Planning Complete, Testing Strategy Complete
**Next Action:** Assign to Claude Cloud for implementation
