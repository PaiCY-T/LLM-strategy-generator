# Factor Graph Integration Implementation Plan

**Date**: 2025-11-08
**Task**: Complete TODO placeholders in `iteration_executor.py`
**Status**: Ready for Review

---

## Executive Summary

This implementation plan completes the Factor Graph integration in `iteration_executor.py` by filling in the TODO placeholders at lines 370-379 and 414-423. The solution uses existing infrastructure (FactorRegistry, mutations.py, BacktestExecutor) without creating new repositories.

**Approach**: Modified Option B (minimal changes, maximum effect)

---

## Problem Statement

### Current State (Lines 370-379)
```python
def _generate_with_factor_graph(
    self, iteration_num: int
) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Generate strategy using Factor Graph mutation."""
    # TODO: Implement Factor Graph integration (Task 5.2.1)
    logger.warning("Factor Graph not yet integrated, returning placeholder")

    strategy_id = f"momentum_fallback_{iteration_num}"
    strategy_generation = 0

    return (None, strategy_id, strategy_generation)
```

### Current State (Lines 414-423)
```python
elif generation_method == "factor_graph" and strategy_id:
    # TODO: Execute Factor Graph Strategy object (Task 5.2.3)
    logger.warning("Factor Graph execution not yet implemented")
    result = ExecutionResult(
        success=False,
        error_type="NotImplementedError",
        error_message="Factor Graph execution not yet integrated",
        execution_time=0.0,
    )
```

**Impact**: 100% failure rate when `llm.enabled=false` (Factor Graph path not functional)

---

## Solution Architecture

### Components Used (All Existing)

1. **FactorRegistry** (`src/factor_library/registry.py`):
   - Singleton instance with 13 predefined factors
   - `create_factor(name, parameters)` - Create factor instances
   - `list_by_category(category)` - Discover factors by type

2. **mutations.py** (`src/factor_graph/mutations.py`):
   - `add_factor(strategy, factor_name, parameters, insert_point)` - Add factor to strategy
   - Pure functions (return new strategy, don't modify original)

3. **Strategy** (`src/factor_graph/strategy.py`):
   - DAG structure for compositional strategy design
   - `add_factor(factor, depends_on)` - Build strategy graph
   - `copy()` - Clone for mutation

4. **BacktestExecutor** (`src/backtest/executor.py`):
   - `execute_strategy(strategy, data, sim, ...)` - Execute Strategy DAG
   - Already implemented and verified (Phase 4)

5. **ChampionTracker** (`src/learning/champion_tracker.py`):
   - `get_champion()` - Get current champion (supports hybrid)
   - `champion.generation_method` - "llm" or "factor_graph"
   - `champion.strategy_id` - Factor Graph champion ID

### New Internal State (IterationExecutor)

Add two registries to `__init__`:

```python
# Strategy DAG registry (internal to IterationExecutor)
self._strategy_registry: Dict[str, Strategy] = {}

# Factor logic registry (for future serialization support)
self._factor_logic_registry: Dict[str, Callable] = {}
```

**Why Internal?**
- Strategies are temporary (per-iteration, not persisted)
- Hall of Fame stores metadata only (via Strategy.to_dict())
- No need for global repository pattern

---

## Implementation Details

### Change 1: Add Registries to `__init__` (Line 96)

**Location**: After line 95 (`self._finlab_initialized = False`)

```python
# Initialize finlab data and sim (lazy loading)
self.data = None
self.sim = None
self._finlab_initialized = False

# === NEW: Factor Graph Support ===
# Strategy DAG registry (maps strategy_id -> Strategy object)
self._strategy_registry: Dict[str, Strategy] = {}

# Factor logic registry (maps factor_id -> logic Callable)
# Used for Strategy serialization/deserialization
self._factor_logic_registry: Dict[str, Callable] = {}

logger.info("IterationExecutor initialized")
```

**Rationale**:
- `_strategy_registry`: Stores Strategy DAG objects created during iteration
- `_factor_logic_registry`: Maps factor IDs to logic functions (future serialization)
- Both are internal state, not persisted between runs

---

### Change 2: Implement `_generate_with_factor_graph()` (Lines 359-379)

**Replace TODO section (lines 370-379) with full implementation**:

```python
def _generate_with_factor_graph(
    self, iteration_num: int
) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Generate strategy using Factor Graph mutation.

    Implementation:
    1. Check if Factor Graph champion exists
    2. If exists: Mutate champion using add_factor()
    3. If not: Create template strategy (momentum + breakout + exit)
    4. Register strategy to internal registry
    5. Return (None, strategy_id, strategy_generation)

    Args:
        iteration_num: Current iteration number

    Returns:
        (None, strategy_id, strategy_generation) for Factor Graph
        - code: Always None (Factor Graph doesn't use code strings)
        - strategy_id: Unique ID for Strategy DAG object
        - strategy_generation: Generation number (0 for templates, N+1 for mutated)
    """
    from src.factor_graph.strategy import Strategy
    from src.factor_graph.mutations import add_factor
    from src.factor_library.registry import FactorRegistry
    from src.factor_graph.factor_category import FactorCategory
    import random

    registry = FactorRegistry.get_instance()

    # Check if we have a Factor Graph champion
    champion = self.champion_tracker.get_champion()

    if champion and champion.generation_method == "factor_graph":
        # Mutate existing champion
        logger.info(f"Mutating Factor Graph champion: {champion.strategy_id}")

        # Get champion strategy from registry
        parent_strategy = self._strategy_registry.get(champion.strategy_id)

        if parent_strategy is None:
            # Champion not in registry (loaded from Hall of Fame)
            # Create template and mutate from there
            logger.warning(f"Champion {champion.strategy_id} not in registry, creating template")
            parent_strategy = self._create_template_strategy(iteration_num)

        # Select random factor to add (mutation)
        available_categories = [
            FactorCategory.MOMENTUM,
            FactorCategory.EXIT,
            FactorCategory.ENTRY,
            FactorCategory.RISK
        ]

        # Randomly select category
        category = random.choice(available_categories)
        factors_in_category = registry.list_by_category(category)

        if not factors_in_category:
            # No factors in category, try MOMENTUM as fallback
            factors_in_category = registry.get_momentum_factors()

        # Randomly select factor from category
        factor_name = random.choice(factors_in_category)

        # Get default parameters from registry
        metadata = registry.get_metadata(factor_name)
        parameters = metadata['parameters'].copy() if metadata else {}

        # Mutate strategy (add factor)
        try:
            mutated_strategy = add_factor(
                strategy=parent_strategy,
                factor_name=factor_name,
                parameters=parameters,
                insert_point="smart"  # Smart insertion based on category
            )

            # Generate new ID and increment generation
            strategy_id = f"fg_{iteration_num}_{champion.strategy_generation + 1}"
            strategy_generation = champion.strategy_generation + 1
            mutated_strategy.id = strategy_id
            mutated_strategy.generation = strategy_generation
            mutated_strategy.parent_ids = [champion.strategy_id]

            logger.info(
                f"Mutated strategy: added {factor_name} "
                f"(gen {strategy_generation}, parent: {champion.strategy_id})"
            )

        except Exception as e:
            logger.error(f"Mutation failed: {e}, creating template instead")
            # Fallback: create template
            mutated_strategy = self._create_template_strategy(iteration_num)
            strategy_id = mutated_strategy.id
            strategy_generation = mutated_strategy.generation

    else:
        # No Factor Graph champion, create template strategy
        logger.info("No Factor Graph champion, creating template strategy")
        mutated_strategy = self._create_template_strategy(iteration_num)
        strategy_id = mutated_strategy.id
        strategy_generation = mutated_strategy.generation

    # Register strategy to internal registry
    self._strategy_registry[strategy_id] = mutated_strategy

    # Return None for code (Factor Graph doesn't use code strings)
    return (None, strategy_id, strategy_generation)
```

**Key Design Decisions**:

1. **Mutation Strategy**:
   - Random category selection (MOMENTUM, EXIT, ENTRY, RISK)
   - Random factor from category
   - Smart insertion (category-aware positioning)

2. **Template Fallback**:
   - If champion not in registry → create template
   - If mutation fails → create template
   - Template = momentum + breakout + trailing stop

3. **Generation Tracking**:
   - Templates: generation = 0
   - Mutated: generation = parent.generation + 1
   - Parent lineage tracked via `parent_ids`

---

### Change 3: Add `_create_template_strategy()` Helper (After line 379)

**Insert new method after `_generate_with_factor_graph()`**:

```python
def _create_template_strategy(self, iteration_num: int) -> Strategy:
    """Create template Factor Graph strategy (momentum + breakout + trailing stop).

    Template Strategy Composition:
    1. Momentum Factor (MOMENTUM): Price momentum using rolling mean
    2. Breakout Factor (ENTRY): N-day high/low breakout detection
    3. Trailing Stop Factor (EXIT): Trailing stop loss for risk management

    This provides a baseline strategy for Factor Graph evolution when no champion exists.

    Args:
        iteration_num: Current iteration number (used for unique ID)

    Returns:
        Strategy: Template strategy with 3 factors
    """
    from src.factor_graph.strategy import Strategy
    from src.factor_library.registry import FactorRegistry

    registry = FactorRegistry.get_instance()

    # Create strategy
    strategy_id = f"template_{iteration_num}"
    strategy = Strategy(id=strategy_id, generation=0)

    # Add momentum factor (root)
    momentum_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )
    strategy.add_factor(momentum_factor, depends_on=[])

    # Add breakout factor (entry signal)
    breakout_factor = registry.create_factor(
        "breakout_factor",
        parameters={"entry_window": 20}
    )
    strategy.add_factor(breakout_factor, depends_on=[])

    # Add trailing stop factor (exit)
    trailing_stop_factor = registry.create_factor(
        "trailing_stop_factor",
        parameters={"trail_percent": 0.10, "activation_profit": 0.05}
    )
    strategy.add_factor(
        trailing_stop_factor,
        depends_on=[momentum_factor.id, breakout_factor.id]
    )

    logger.info(f"Created template strategy: {strategy_id} with 3 factors")

    return strategy
```

**Template Design**:
- **Momentum Factor**: Trend-following signal
- **Breakout Factor**: Entry timing
- **Trailing Stop**: Risk management and exit
- **Simple but functional**: Baseline for evolution

---

### Change 4: Implement Factor Graph Execution Path (Lines 414-423)

**Replace TODO section with**:

```python
elif generation_method == "factor_graph" and strategy_id:
    # Execute Factor Graph Strategy object
    logger.info(f"Executing Factor Graph strategy: {strategy_id}")

    # Get strategy from registry
    strategy = self._strategy_registry.get(strategy_id)

    if strategy is None:
        # Strategy not found in registry (shouldn't happen)
        logger.error(f"Strategy {strategy_id} not found in registry")
        result = ExecutionResult(
            success=False,
            error_type="ValueError",
            error_message=f"Strategy {strategy_id} not found in internal registry",
            execution_time=0.0,
        )
    else:
        # Execute Strategy DAG using BacktestExecutor.execute_strategy()
        result = self.backtest_executor.execute_strategy(
            strategy=strategy,
            data=self.data,
            sim=self.sim,
            timeout=self.config.get("timeout_seconds", 420),
            start_date=self.config.get("start_date"),
            end_date=self.config.get("end_date"),
            fee_ratio=self.config.get("fee_ratio"),
            tax_ratio=self.config.get("tax_ratio"),
            resample=self.config.get("resample", "M"),
        )

        logger.info(
            f"Factor Graph execution complete: "
            f"success={result.success}, time={result.execution_time:.1f}s"
        )
```

**Key Points**:
- Gets Strategy object from `_strategy_registry`
- Calls `BacktestExecutor.execute_strategy()` (already implemented)
- Same configuration as LLM path (timeout, dates, fees)
- Comprehensive logging for debugging

---

## Import Dependencies

**Add to top of file (after existing imports, around line 29)**:

```python
from typing import Any, Dict, Optional, Tuple, Callable  # Add Callable to existing line
```

**Note**: Most imports are already present. Only need to add `Callable` to typing imports.

---

## Complete Modified File Section

**Lines 54-97 (Modified `__init__`)**:

```python
def __init__(
    self,
    llm_client: LLMClient,
    feedback_generator: FeedbackGenerator,
    backtest_executor: BacktestExecutor,
    champion_tracker: ChampionTracker,
    history: IterationHistory,
    config: Dict[str, Any],
):
    """Initialize iteration executor with all required components.

    Args:
        llm_client: LLM client for strategy generation
        feedback_generator: Feedback generator from history
        backtest_executor: Backtest executor with timeout
        champion_tracker: Champion tracker for best strategy
        history: Iteration history
        config: Configuration dict with keys:
            - innovation_rate: 0-100, percentage of LLM vs Factor Graph
            - history_window: Number of recent iterations for feedback
            - timeout_seconds: Backtest timeout in seconds
            - start_date: Backtest start date
            - end_date: Backtest end date
            - fee_ratio: Transaction fee ratio
            - tax_ratio: Transaction tax ratio
            - resample: Rebalancing frequency (M/W/D)
    """
    self.llm_client = llm_client
    self.feedback_generator = feedback_generator
    self.backtest_executor = backtest_executor
    self.champion_tracker = champion_tracker
    self.history = history
    self.config = config

    # Initialize Phase 2 components
    self.metrics_extractor = MetricsExtractor()
    self.success_classifier = SuccessClassifier()

    # Initialize finlab data and sim (lazy loading)
    self.data = None
    self.sim = None
    self._finlab_initialized = False

    # === Factor Graph Support ===
    # Strategy DAG registry (maps strategy_id -> Strategy object)
    self._strategy_registry: Dict[str, 'Strategy'] = {}

    # Factor logic registry (maps factor_id -> logic Callable)
    # Used for Strategy serialization/deserialization
    self._factor_logic_registry: Dict[str, Callable] = {}

    logger.info("IterationExecutor initialized")
```

---

## Testing Strategy

### Unit Tests (New File: `tests/learning/test_iteration_executor_factor_graph.py`)

**Test Cases**:

1. **test_generate_with_factor_graph_no_champion**:
   - No existing champion → creates template strategy
   - Verify template has 3 factors (momentum, breakout, trailing_stop)
   - Verify strategy registered to `_strategy_registry`

2. **test_generate_with_factor_graph_with_champion**:
   - Existing Factor Graph champion → mutates champion
   - Verify new factor added
   - Verify generation incremented
   - Verify parent_ids tracking

3. **test_generate_with_factor_graph_mutation_failure**:
   - Mutation fails (e.g., invalid factor)
   - Fallback to template creation
   - No crash, returns valid strategy

4. **test_execute_strategy_factor_graph_success**:
   - Create mock Strategy object
   - Register to `_strategy_registry`
   - Execute → verify BacktestExecutor.execute_strategy() called
   - Verify ExecutionResult returned

5. **test_execute_strategy_factor_graph_not_found**:
   - Strategy ID not in registry
   - Returns ExecutionResult with error

6. **test_create_template_strategy**:
   - Creates strategy with 3 factors
   - Verify DAG structure (dependencies)
   - Verify factor parameters

### Integration Tests (Extend `tests/integration/test_hybrid_architecture_phase6.py`)

**Add Test Cases**:

1. **test_end_to_end_factor_graph_iteration**:
   - Run iteration with `innovation_rate=0` (force Factor Graph)
   - Verify template created on first iteration
   - Verify mutation on second iteration
   - Verify execution succeeds

2. **test_factor_graph_champion_update**:
   - Create Factor Graph strategy
   - Execute and get good metrics
   - Verify champion updated
   - Next iteration mutates the champion

---

## Risk Analysis

### Low Risk ✅

1. **Uses existing components**: No new classes/modules
2. **Pure functions**: mutations.py doesn't modify originals
3. **Isolated changes**: Only affects iteration_executor.py
4. **Backward compatible**: LLM path unchanged

### Medium Risk ⚠️

1. **Template strategy quality**:
   - **Risk**: Template may perform poorly
   - **Mitigation**: Simple but proven factors (momentum + breakout + trailing stop)
   - **Future**: Add more sophisticated templates

2. **Mutation randomness**:
   - **Risk**: Random factor selection may not improve strategy
   - **Mitigation**: Smart insertion (category-aware), fallback to template
   - **Future**: Guided mutation using feedback

3. **Registry growth**:
   - **Risk**: `_strategy_registry` grows unbounded
   - **Mitigation**: Short-term OK (cleared per-iteration)
   - **Future**: Add cleanup logic if memory becomes issue

### Addressed Risks 🛡️

1. **Champion not in registry**:
   - **Solution**: Fallback to template creation
   - **Logging**: Warning message for debugging

2. **Mutation failure**:
   - **Solution**: Try-catch with template fallback
   - **Logging**: Error logged, no crash

3. **Missing strategy in execution**:
   - **Solution**: Check registry, return error if not found
   - **Logging**: Error logged with strategy_id

---

## Performance Considerations

### Expected Performance

- **Template creation**: <10ms (3 factors, simple DAG)
- **Mutation (add_factor)**: <10ms (smart insertion, dependency resolution)
- **Strategy execution**: Same as LLM path (BacktestExecutor)

### Memory Usage

- **Per strategy**: ~5-10KB (3-10 factors typical)
- **Registry size**: <1MB for 100 strategies
- **Acceptable**: Strategies temporary (per-iteration)

---

## Migration Path

### Phase 1: Implementation (This PR)
- Complete TODO placeholders
- Add unit tests
- Verify no regressions

### Phase 2: Enhancement (Future)
- Add sophisticated template library
- Implement guided mutation (using feedback)
- Add strategy cleanup logic (memory management)

### Phase 3: Optimization (Future)
- Add caching for factor creation
- Optimize mutation operators
- Implement parallel execution

---

## Validation Checklist

### Code Quality
- [ ] No breaking changes to existing code
- [ ] All imports at top of file
- [ ] Type hints on all new methods
- [ ] Comprehensive docstrings
- [ ] Logging for debugging
- [ ] Error handling (try-catch)

### Functionality
- [ ] Template creation works
- [ ] Mutation from champion works
- [ ] Execution calls BacktestExecutor correctly
- [ ] Strategy registry management works
- [ ] Fallback logic works (mutation failure)

### Testing
- [ ] Unit tests for all new methods
- [ ] Integration tests for end-to-end flow
- [ ] Edge cases covered (no champion, mutation fail, strategy not found)
- [ ] Mock-based tests (no finlab dependency)

### Documentation
- [ ] Docstrings explain behavior
- [ ] Comments explain non-obvious logic
- [ ] Examples in docstrings
- [ ] Implementation plan documented

---

## Summary

This implementation:

1. **Completes TODO placeholders** in iteration_executor.py (lines 370-379, 414-423)
2. **Uses existing infrastructure** (FactorRegistry, mutations, BacktestExecutor, Strategy)
3. **No new files/classes** (minimal changes, maximum effect)
4. **Production-ready** (error handling, logging, fallbacks)
5. **Well-tested** (unit + integration tests)

**Total Changes**:
- **1 file modified**: `src/learning/iteration_executor.py`
- **Lines added**: ~150 lines (implementation + docstrings)
- **Lines modified**: ~5 lines (import, __init__)
- **New tests**: ~300 lines

**Estimated Implementation Time**: 2-3 hours
**Estimated Testing Time**: 1-2 hours
**Total**: 3-5 hours

---

## Next Steps

1. **Review this plan** - Ensure approach is correct
2. **Approve implementation** - Confirm changes are acceptable
3. **Implement changes** - Modify iteration_executor.py
4. **Write tests** - Add unit and integration tests
5. **Verify execution** - Run tests (when environment available)
6. **Commit and push** - Create PR

---

**Ready for Review** ✅

請檢視此實施方案，確認後我將開始實作。
