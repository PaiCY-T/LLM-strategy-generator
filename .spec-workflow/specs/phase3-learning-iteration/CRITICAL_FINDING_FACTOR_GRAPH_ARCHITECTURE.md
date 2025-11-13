# CRITICAL FINDING: Factor Graph Architecture Mismatch

**Date**: 2025-11-05
**Status**: 🔴 **IMPLEMENTATION PLAN REQUIRES REVISION**
**Impact**: High - Current Phase 5 implementation strategy is based on incorrect assumption

---

## Summary

The `to_python_code()` method **does not exist** in the Factor Graph codebase. The entire Factor Graph system works with **Strategy DAG objects**, not Python code strings.

**Current autonomous_loop.py** works exclusively with **code strings** for LLM-generated strategies, while **Factor Graph mutations** work exclusively with **Strategy objects**. These are **incompatible architectures**.

---

## Verification Results

### Method Search (NEGATIVE)

```bash
# Searched for to_python_code() or similar methods
grep -r "to_python|to_code|generate_code" src/factor_graph/

# Result: NO MATCHES
```

### Strategy Class Analysis

**File**: `src/factor_graph/strategy.py` (616 lines)

**Available Methods**:
- ✅ `add_factor()` - Add factor to DAG
- ✅ `remove_factor()` - Remove factor from DAG
- ✅ `get_factors()` - Get factors in topological order
- ✅ `copy()` - Deep copy strategy
- ✅ `to_pipeline()` - Execute strategy on data
- ✅ `validate()` - Validate DAG integrity
- ❌ `to_python_code()` - **DOES NOT EXIST**

### Mutation Functions Analysis

**File**: `src/factor_graph/mutations.py` (837 lines)

**Available Functions**:
```python
# All work with Strategy objects, not code strings
add_factor(strategy: Strategy, ...) -> Strategy
remove_factor(strategy: Strategy, ...) -> Strategy
replace_factor(strategy: Strategy, ...) -> Strategy
```

**Key Architecture Points**:
1. Mutations are **pure functions** (return new Strategy, don't modify original)
2. Work with **Strategy DAG objects**, not code strings
3. All validation happens at DAG level (no code generation)

---

## Architecture Incompatibility

### Current System (autonomous_loop.py)

```python
# Lines 1078-1628: _run_freeform_iteration()
# Works exclusively with CODE STRINGS

# LLM generates code string
code = llm_client.generate_code(prompt)

# Execute code string
result = backtest_executor.execute(code)

# Store code string
champion_strategy = ChampionStrategy(code=code, ...)
```

**Data Flow**: `Prompt → LLM → Code String → Execute → Store Code String`

### Factor Graph System

```python
# Works exclusively with STRATEGY OBJECTS

# Create strategy
strategy = Strategy(id="momentum", generation=0)

# Add factors
strategy.add_factor(rsi_factor)
strategy.add_factor(signal_factor, depends_on=["rsi_14"])

# Mutate strategy
mutated = add_factor(strategy, "trailing_stop_factor", insert_point="leaf")

# Execute strategy
result = mutated.to_pipeline(data)
```

**Data Flow**: `Strategy DAG → Mutations → Strategy DAG → Execute via to_pipeline()`

---

## Impact on Phase 5 Implementation

### Original Plan (INCORRECT)

From `OPTION_B_ANALYSIS_COMPLETE.md`:

```python
class FactorGraphGenerator:
    """Generate strategy variations using Factor Graph mutations."""

    def generate_mutation(self, base_strategy: Strategy) -> Strategy:
        """Apply single random mutation with retry logic."""
        # ... apply mutations ...
        return mutated_strategy

    def to_code(self, strategy: Strategy) -> str:
        """Convert Strategy to Python code."""
        return strategy.to_python_code()  # ❌ DOES NOT EXIST
```

**Problem**: Assumed `to_python_code()` exists to convert Strategy → code string

### Required Revision

**Two possible approaches**:

#### **Option A: Implement `to_python_code()` Method** (HARDER)

Add method to Strategy class to serialize DAG to executable Python code:

```python
def to_python_code(self) -> str:
    """Generate executable Python code from Strategy DAG."""
    # Complex implementation required:
    # - Traverse factors in topological order
    # - Generate imports
    # - Generate factor instantiation code
    # - Generate pipeline execution code
    # - Return as executable string
```

**Complexity**: HIGH (~200-300 lines)
**Risk**: HIGH (brittle code generation, hard to maintain)
**Timeline**: +2-3 days

#### **Option B: Store Strategy Objects Instead of Code** (EASIER, BETTER)

Change champion storage from code strings to Strategy objects:

```python
# Current (code string)
@dataclass
class ChampionStrategy:
    code: str  # ❌ Incompatible with Factor Graph
    metrics: Dict[str, float]
    ...

# Revised (Strategy object)
@dataclass
class ChampionStrategy:
    strategy: Strategy  # ✅ Compatible with Factor Graph
    metrics: Dict[str, float]
    ...
```

**Complexity**: MEDIUM (refactor storage + execution)
**Risk**: MEDIUM (requires changes to multiple files)
**Timeline**: +1 day

---

## Recommended Solution

### ✅ **Adopt Option B: Hybrid Architecture**

Support **both** LLM code strings AND Factor Graph Strategy objects:

```python
@dataclass
class ChampionStrategy:
    """Champion can be either LLM code or Factor Graph Strategy."""
    code: Optional[str] = None         # For LLM-generated strategies
    strategy: Optional[Strategy] = None  # For Factor Graph strategies
    generation_method: str = "unknown"  # "llm" or "factor_graph"
    metrics: Dict[str, float] = field(default_factory=dict)
    ...

    def execute(self, data) -> BacktestResult:
        """Execute champion regardless of generation method."""
        if self.generation_method == "llm":
            return execute_code_string(self.code, data)
        elif self.generation_method == "factor_graph":
            return execute_strategy_dag(self.strategy, data)
        else:
            raise ValueError(f"Unknown generation method: {self.generation_method}")
```

**Benefits**:
- ✅ Supports both LLM and Factor Graph strategies
- ✅ No need to implement complex `to_python_code()` serialization
- ✅ Minimal changes to existing LLM code path
- ✅ Clean separation of concerns
- ✅ Future-proof (can add more generation methods)

**Implementation Changes Required**:
1. Update `ChampionStrategy` dataclass (5 lines changed)
2. Update `ChampionTracker` to handle both types (~20 lines)
3. Update `BacktestExecutor` to handle Strategy objects (~30 lines)
4. Update `IterationHistory` serialization (~15 lines)
5. Add tests for hybrid execution (~40 tests)

**Timeline**: **1 day** (vs. 2-3 days for Option A)

---

## Execution Strategy Comparison

### LLM Code String Execution (Current)

```python
# Execute code string
result = backtest_executor.execute(code_string)

# Internally uses exec() or subprocess
namespace = {}
exec(code_string, namespace)
strategy_func = namespace['strategy']
result = strategy_func(data)
```

### Factor Graph Strategy Execution (New)

```python
# Execute Strategy DAG
result = strategy.to_pipeline(data)

# Internally executes factors in topological order
for factor in strategy.get_factors():
    data = factor.execute(data)
return data
```

**Compatibility**: Both return DataFrame with backtest results ✅

---

## Revised Phase 5 Implementation Plan

### Day 1: Core IterationExecutor (NO CHANGES)

Tasks 5.1.1-5.1.5 remain unchanged - these don't interact with Factor Graph yet.

**Reason**: Extraction focuses on LLM path first (current working code).

### Day 2: Factor Graph Fallback (REVISED)

**OLD PLAN** (based on incorrect assumption):
```python
# Task 5.2.1: Create FactorGraphGenerator with to_python_code()
generator = FactorGraphGenerator()
mutated_strategy = generator.generate_mutation(base_strategy)
code = mutated_strategy.to_python_code()  # ❌ DOESN'T EXIST
```

**NEW PLAN** (hybrid architecture):
```python
# Task 5.2.1: Create FactorGraphGenerator returning Strategy objects
generator = FactorGraphGenerator()
mutated_strategy = generator.generate_mutation(base_strategy)

# Task 5.2.2: Update BacktestExecutor to handle Strategy objects
result = backtest_executor.execute(mutated_strategy)  # ✅ Handles both code & Strategy

# Task 5.2.3: Update ChampionTracker to store Strategy objects
champion_tracker.update(
    strategy=mutated_strategy,  # Store Strategy object, not code
    generation_method="factor_graph"
)
```

**New Subtasks**:
- 5.2.1a: Implement hybrid ChampionStrategy dataclass (30 min)
- 5.2.1b: Update BacktestExecutor to handle Strategy objects (1 hour)
- 5.2.1c: Create FactorGraphGenerator (no to_code needed) (1.5 hours)
- 5.2.2: Integrate fallback logic into IterationExecutor (1 hour)
- 5.2.3: Add hybrid execution tests (2 hours)

**Total Day 2 Time**: 6 hours (same as original, but different tasks)

### Day 3: Testing & Validation (REVISED)

**Additional Tests Required**:
- Hybrid champion storage/retrieval (10 tests)
- Strategy object execution path (5 tests)
- LLM → Factor Graph transition (5 tests)
- Serialization of Strategy objects (5 tests)

**Total New Tests**: +25 tests (85 total instead of 60)

---

## File Changes Required

### 1. ChampionStrategy Dataclass

**File**: `artifacts/working/modules/autonomous_loop.py` (lines 50-92)

```python
@dataclass
class ChampionStrategy:
    """Champion can be either LLM code or Factor Graph Strategy."""

    # HYBRID FIELDS (support both generation methods)
    code: Optional[str] = None         # For LLM-generated strategies
    strategy: Optional[Strategy] = None  # For Factor Graph strategies
    generation_method: str = "unknown"  # "llm" or "factor_graph"

    # Common fields
    metrics: Dict[str, float] = field(default_factory=dict)
    iteration_num: int = 0
    timestamp: str = ""

    def __post_init__(self):
        """Validate exactly one generation method is set."""
        if self.code is None and self.strategy is None:
            raise ValueError("Either code or strategy must be set")
        if self.code is not None and self.strategy is not None:
            raise ValueError("Cannot set both code and strategy")
```

### 2. BacktestExecutor Update

**File**: `src/backtest/executor.py`

**New Method** (~30 lines):
```python
def execute_strategy_dag(
    self,
    strategy: Strategy,
    data: pd.DataFrame,
    timeout: Optional[float] = None
) -> ExecutionResult:
    """Execute Factor Graph Strategy DAG.

    Args:
        strategy: Strategy DAG to execute
        data: Market data
        timeout: Optional timeout

    Returns:
        ExecutionResult with metrics
    """
    try:
        # Execute strategy via to_pipeline()
        result_df = strategy.to_pipeline(data)

        # Extract metrics (same logic as code execution)
        metrics = self._extract_metrics(result_df)

        return ExecutionResult(
            success=True,
            execution_time=execution_time,
            sharpe_ratio=metrics.get('sharpe_ratio'),
            ...
        )
    except Exception as e:
        return ExecutionResult(
            success=False,
            error_type=type(e).__name__,
            error_message=str(e),
            ...
        )
```

### 3. IterationHistory Serialization

**File**: `src/learning/iteration_history.py`

**Challenge**: Strategy objects are not JSON-serializable

**Solution**: Store Strategy as metadata, not in JSONL

```python
# Option 1: Store only strategy ID, load from registry
{
    "iteration_num": 5,
    "generation_method": "factor_graph",
    "strategy_id": "momentum_v5",  # Reference to external storage
    "metrics": {...}
}

# Option 2: Pickle Strategy objects separately
# .spec-workflow/specs/phase3-learning-iteration/strategies/
#   - iteration_5_strategy.pkl
#   - iteration_7_strategy.pkl
```

---

## Decision Points

### Immediate Decision Required

**Question**: Which approach for Phase 5 Factor Graph integration?

**Option A: Implement `to_python_code()` serialization**
- Pros: Keeps code string architecture
- Cons: Complex, brittle, 2-3 days extra work
- Risk: HIGH

**Option B: Hybrid architecture (code + Strategy objects)**
- Pros: Clean, maintainable, supports both methods
- Cons: More extensive changes across codebase
- Risk: MEDIUM
- Timeline: +1 day

### Recommended Decision

✅ **Adopt Option B: Hybrid Architecture**

**Rationale**:
1. Cleaner long-term architecture
2. Supports both LLM and Factor Graph natively
3. Avoids brittle code generation
4. Only +1 day vs. +2-3 days for Option A
5. More maintainable and testable
6. Future-proof for additional generation methods

---

## Updated Timeline

### Phase 5 Revised Timeline

**Day 0 (Today)**: Architecture decision + hybrid ChampionStrategy (3 hours)
- Document decision
- Implement hybrid ChampionStrategy dataclass
- Update BacktestExecutor to handle Strategy objects
- Write basic tests

**Day 1**: Core IterationExecutor (6-8 hours, NO CHANGES)
- Tasks 5.1.1-5.1.5 as originally planned
- Focus on LLM path extraction first

**Day 2**: Factor Graph Fallback + Hybrid Execution (6-8 hours)
- Implement FactorGraphGenerator (no to_code needed)
- Integrate fallback logic
- Add Strategy object execution tests
- Add serialization for Strategy objects

**Day 3**: Testing & Documentation (6-8 hours)
- Complete 85 tests (60 unit + 25 hybrid)
- Integration tests for both paths
- Documentation updates
- Validation

**Total**: **3.5-4 days** (vs. original 3 days + 2-3 days for to_python_code)

---

## Next Steps

### Immediate Actions (Next 30 Minutes)

1. ✅ **Document this finding** (COMPLETE)
2. ⏭️ **Get user approval** for hybrid architecture approach
3. ⏭️ **Update PHASE5_IMPLEMENTATION_ROADMAP.md** with revised tasks
4. ⏭️ **Begin Day 0 implementation** if approved

### Blocked Until Decision

- Cannot start FactorGraphGenerator implementation
- Cannot finalize Day 2 task breakdown
- Cannot write Factor Graph integration tests

---

## Key Learnings

### 1. Verify External Dependencies Early

**Lesson**: The `to_python_code()` method was assumed to exist based on typical DAG serialization patterns, but **verifying it before planning** would have caught this mismatch earlier.

**Prevention**: Always verify external APIs exist before building implementation plans that depend on them.

### 2. Code Generation is Complex

**Lesson**: Serializing DAG structures to executable code is **non-trivial**. The Factor Graph team likely avoided it for good reasons (complexity, brittleness, maintenance burden).

**Alternative**: Work with objects directly when possible, serialize only when absolutely necessary.

### 3. Hybrid Architectures Are Valid

**Lesson**: Supporting multiple generation methods (LLM code strings + Factor Graph DAGs) is a **valid architectural pattern** when integrating different systems.

**Benefit**: Clean separation of concerns, easier testing, future-proof.

---

## Conclusion

**Critical Finding**: The `to_python_code()` method does not exist in the Factor Graph codebase. The original Phase 5 implementation plan assumed this method existed and built the entire Factor Graph fallback mechanism around it.

**Impact**: Implementation plan requires revision to adopt **hybrid architecture** supporting both LLM code strings and Factor Graph Strategy objects.

**Recommendation**: Adopt **Option B (Hybrid Architecture)** for cleaner, more maintainable solution with only +1 day timeline impact.

**Status**: ⏸️ **BLOCKED** - Awaiting user decision on approach before proceeding with Phase 5 Day 1 implementation.

---

**Report Generated**: 2025-11-05
**Verification Time**: 15 minutes
**Blocker Type**: Architecture Mismatch
**Severity**: HIGH (blocks Factor Graph integration)
**Recommended Action**: Approve hybrid architecture approach and proceed with Day 0 implementation
