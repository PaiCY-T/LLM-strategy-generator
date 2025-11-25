# unified-strategy-interface-refactor - Design Document

## Overview

This design document specifies the technical implementation for unifying three strategy generation modes (Template, LLM, Factor Graph) under a common `IStrategy` Protocol interface, while maintaining the existing Repository Pattern architecture. The refactor focuses on:

1. **Domain Interface Unification**: Define `IStrategy` Protocol with domain-only methods (no persistence)
2. **Factor Graph Serialization**: Extend persistence layer to support Factor Graph DAG structures
3. **Bug Fixes**: Resolve Champion update inconsistencies across all three modes
4. **Architecture Preservation**: Maintain clean separation between Domain, Persistence, and Interface layers

**Design Philosophy**: Repository Pattern with explicit separation of concerns - serialization (data transformation) is distinct from persistence (storage mechanism).

## Architecture

### Layer Architecture (Preserved from Current Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                    Interface Layer                          │
│  - IStrategy Protocol (domain contract ONLY)                │
│  - IChampionTracker Protocol                                │
│  - No persistence methods (save/load)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  - ChampionTracker (business logic)                         │
│  - Strategy classes (Template, LLM, Factor Graph)          │
│  - Zero persistence code                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Model Layer                              │
│  - Strategy, ChampionStrategy dataclasses                   │
│  - Serialization helpers: to_dict(), from_dict()           │
│  - NO file I/O (pure data transformation)                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Persistence Layer                          │
│  - HallOfFameRepository (file I/O)                         │
│  - Uses serialization helpers internally                    │
│  - Zero business logic                                      │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Flow (Dependency Inversion Principle)

```
ChampionTracker → [IHallOfFameRepository] ← HallOfFameRepository
      ↓
  [IStrategy] ← Strategy (Template/LLM/FactorGraph)
      ↓
  to_dict() / from_dict() (Model Layer)
```

**Key Principles**:
- ChampionTracker depends on Repository **interface**, not implementation
- IStrategy defines domain contract, not persistence contract
- Serialization helpers are internal implementation details
- Dependency direction: High-level (Domain) → Low-level (Persistence)

## Components and Interfaces

### 1. IStrategy Protocol (NEW)

**Location**: `src/learning/interfaces.py`

**Purpose**: Define unified domain interface for all three strategy generation modes

**Interface Specification**:

```python
from typing import Protocol, runtime_checkable, Dict, Any, Optional
from src.backtest.metrics import StrategyMetrics

@runtime_checkable
class IStrategy(Protocol):
    """Unified strategy interface for Template, LLM, and Factor Graph modes.

    This Protocol defines the DOMAIN contract for strategy objects. It does
    NOT include persistence methods (save/load) as those belong to the
    Repository layer.

    Design Decision (Architecture Analysis):
    - Adding save/load here would violate Single Responsibility Principle
    - Would create Active Record anti-pattern (domain + persistence mixed)
    - Would reduce testability (domain models require I/O)
    - Would reduce flexibility (cannot swap persistence layer)

    Implementation Requirements:
    - All three strategy modes must implement these properties/methods
    - Runtime validation via isinstance(obj, IStrategy)
    - No inheritance required (structural subtyping)
    """

    @property
    def id(self) -> str:
        """Strategy unique identifier.

        Post-conditions:
        - MUST return non-empty string
        - MUST be stable (same value across calls)
        """
        ...

    @property
    def generation(self) -> int:
        """Strategy generation number.

        Post-conditions:
        - MUST return non-negative integer
        - MUST be immutable after creation
        """
        ...

    @property
    def metrics(self) -> Optional[StrategyMetrics]:
        """Strategy performance metrics.

        Post-conditions:
        - Returns None if strategy not yet evaluated
        - Returns StrategyMetrics instance if evaluated
        - MUST include sharpe_ratio if not None
        """
        ...

    def dominates(self, other: 'IStrategy') -> bool:
        """Compare this strategy against another using Pareto dominance.

        Behavioral Contract:
        - MUST compare via metrics.sharpe_ratio (primary)
        - MUST handle None metrics gracefully (return False)
        - MUST be consistent: if A.dominates(B) and B.dominates(A),
          then A and B have equivalent performance

        Args:
            other: Another strategy to compare against

        Returns:
            True if this strategy dominates other, False otherwise
        """
        ...

    def get_parameters(self) -> Dict[str, Any]:
        """Get strategy parameters.

        Behavioral Contract:
        - MUST return dictionary (may be empty)
        - MUST be JSON-serializable
        - Template mode: template parameters
        - LLM mode: empty dict (parameters in code)
        - Factor Graph mode: factor configuration

        Returns:
            Dictionary of strategy parameters
        """
        ...

    def get_metrics(self) -> Dict[str, float]:
        """Get strategy performance metrics as dictionary.

        Behavioral Contract:
        - MUST return dictionary with numeric values
        - MUST include 'sharpe_ratio' key if strategy evaluated
        - MUST return empty dict if strategy not evaluated

        Returns:
            Dictionary of performance metrics
        """
        ...
```

**Design Rationale**:
- `@runtime_checkable` enables isinstance() checks without inheritance
- Domain methods only: dominates(), get_parameters(), get_metrics()
- No persistence methods: save(), load() belong in Repository
- No serialization requirement: to_dict()/from_dict() are implementation details

### 2. HallOfFameRepository Extension (MODIFIED)

**Location**: `src/repository/hall_of_fame.py`

**Current Capability**: Supports Template/LLM mode (StrategyGenome dataclass)

**Required Extension**: Add Factor Graph Strategy object support

**New Methods**:

```python
class HallOfFameRepository:
    """Persistence layer for champion strategies (Template/LLM/Factor Graph).

    Current Architecture (9/10 score):
    - Zero business logic (no Sharpe comparison)
    - Pure file I/O operations
    - Tier-based storage (Champions/Contenders/Archive)
    - Atomic writes with backup mechanism
    - In-memory caching for performance

    Extension Design:
    - Add save_strategy() method for Factor Graph Strategy objects
    - Add load_strategy() method for Factor Graph restoration
    - Leverage existing Strategy.to_dict()/from_dict() methods
    - Maintain atomic write and backup mechanisms
    """

    def save_strategy(
        self,
        strategy: 'Strategy',  # From src.evolution.types
        tier: str = "champions",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save Factor Graph Strategy object to persistent storage.

        Design:
        1. Call strategy.to_dict() to get serializable representation
        2. Add metadata (strategy_id, generation, timestamp)
        3. Write to tier-specific file using atomic write mechanism
        4. Update in-memory cache
        5. Create backup if write succeeds

        Args:
            strategy: Strategy domain object from Factor Graph
            tier: Storage tier (champions/contenders/archive)
            metadata: Additional metadata to store

        Returns:
            True if save succeeds, False otherwise

        Implementation Notes:
        - Uses Strategy.to_dict() (already exists in types.py:229-272)
        - Preserves DAG topology in serialized format
        - Follows existing atomic write pattern (temp → rename)
        """
        ...

    def load_strategy(
        self,
        strategy_id: str,
        tier: str = "champions"
    ) -> Optional['Strategy']:
        """Load Factor Graph Strategy object from persistent storage.

        Design:
        1. Read from tier-specific file
        2. Find entry matching strategy_id
        3. Call Strategy.from_dict() to reconstruct object
        4. Validate DAG structure integrity
        5. Return reconstructed Strategy or None

        Args:
            strategy_id: Unique strategy identifier
            tier: Storage tier to search

        Returns:
            Strategy object if found, None otherwise

        Implementation Notes:
        - Uses Strategy.from_dict() (already exists in types.py:274-334)
        - Reconstructs full DAG structure with node relationships
        - Handles missing/corrupted data gracefully
        """
        ...

    def get_all_strategies(self, tier: str = "champions") -> List['Strategy']:
        """Retrieve all Factor Graph strategies from tier.

        Design:
        - Load all entries from tier file
        - Deserialize each using Strategy.from_dict()
        - Return list of Strategy objects
        - Cache results for performance

        Returns:
            List of Strategy objects (may be empty)
        """
        ...
```

**File Format Design (Factor Graph Extension)**:

```json
{
  "champions": [
    {
      "strategy_id": "strategy_gen_42_001",
      "strategy_generation": 42,
      "timestamp": "2025-11-25T10:30:00",
      "generation_method": "factor_graph",
      "strategy_data": {
        "id": "strategy_gen_42_001",
        "generation": 42,
        "parent_ids": ["strategy_gen_41_003"],
        "code": null,
        "parameters": {...},
        "metrics": {
          "sharpe_ratio": 2.5,
          "annual_return": 0.35,
          "max_drawdown": -0.15,
          ...
        },
        "dag_structure": {
          "nodes": [...],
          "edges": [...],
          "entry_point": "strategy_node"
        }
      }
    }
  ]
}
```

**Key Design Decisions**:
- Reuse existing Strategy.to_dict()/from_dict() methods (DRY principle)
- Maintain tier-based storage architecture (consistency)
- Atomic writes prevent corruption (reliability)
- In-memory cache for performance (optimization)

### 3. ChampionTracker Bug Fixes (MODIFIED)

**Location**: `src/learning/iteration_executor.py:1239`

**Current Issue**: Factor Graph mode missing `strategy` parameter

**Root Cause Analysis**:
```python
# iteration_executor.py:1239 (CURRENT - BUG)
updated = self.champion_tracker.update_champion(
    iteration_num=iteration_num,
    metrics=metrics,
    generation_method=generation_method,
    code=strategy_code,
    strategy_id=strategy_id,
    strategy_generation=strategy_generation
    # ❌ MISSING: strategy=strategy_obj
)

# ChampionTracker validation (champion_tracker.py:574-591)
if generation_method == "factor_graph":
    if not strategy or not strategy_id or strategy_generation is None:
        raise ValueError(
            "Factor Graph mode requires 'strategy', 'strategy_id', "
            "and 'strategy_generation' parameters"
        )
```

**Fix Design**:

```python
# iteration_executor.py:1239 (FIXED)
# Step 1: Retrieve Strategy object from registry
strategy_obj = None
if generation_method == "factor_graph" and strategy_id:
    strategy_obj = self._strategy_registry.get(strategy_id)
    if not strategy_obj:
        logger.warning(
            f"Strategy {strategy_id} not found in registry. "
            f"Champion update may fail."
        )

# Step 2: Pass strategy object to update_champion()
updated = self.champion_tracker.update_champion(
    iteration_num=iteration_num,
    metrics=metrics,
    generation_method=generation_method,
    code=strategy_code,
    strategy=strategy_obj,  # ✅ ADDED
    strategy_id=strategy_id,
    strategy_generation=strategy_generation
)
```

**Validation Logic** (already exists in ChampionTracker):
- Template mode: requires `code` parameter
- LLM mode: requires `code` parameter
- Factor Graph mode: requires `strategy`, `strategy_id`, `strategy_generation`

**Test Coverage Requirements**:
- Unit test: Mock ChampionTracker, verify correct parameters passed
- Integration test: End-to-end Factor Graph iteration with champion update
- Regression test: Template and LLM modes still work correctly

## Data Models

### 1. Strategy Domain Model (EXISTING - types.py)

**Current Status**: Already implements required functionality

```python
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class Strategy:
    """Factor Graph strategy domain model.

    Current Implementation Status:
    - ✅ to_dict() method exists (types.py:229-272)
    - ✅ from_dict() classmethod exists (types.py:274-334)
    - ✅ DAG structure serialization supported
    - ✅ Metrics serialization supported

    Design Analysis:
    - Serialization helpers are pure data transformation (no I/O)
    - Methods convert between object and dictionary representations
    - Suitable for use by HallOfFameRepository persistence layer
    """

    id: str
    generation: int
    parent_ids: List[str]
    code: Optional[str]  # None for Factor Graph
    parameters: Dict[str, Any]
    metrics: Optional['MultiObjectiveMetrics']

    # DAG structure
    dag_structure: Optional[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (EXISTING)."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Strategy':
        """Create from dictionary (EXISTING)."""
        ...
```

**No Changes Required**: Existing implementation sufficient for requirements

### 2. ChampionStrategy Data Model (EXISTING - champion_tracker.py)

```python
@dataclass
class ChampionStrategy:
    """Champion strategy record.

    Current Implementation:
    - Stores champion metadata and performance metrics
    - Used by ChampionTracker for comparison logic
    - Serializable via dataclasses.asdict()

    Fields:
    - iteration_num: When champion was discovered
    - code: Strategy code (None for Factor Graph)
    - parameters: Strategy parameters
    - metrics: Performance metrics (dict)
    - generation_method: "template", "llm", or "factor_graph"
    - strategy_id: Factor Graph strategy ID (optional)
    - strategy_generation: Factor Graph generation (optional)
    - timestamp: When champion was recorded
    """
    ...
```

**No Changes Required**: Existing implementation sufficient

### 3. IStrategy Protocol Mapping

**Mapping Three Modes to IStrategy**:

| Property/Method | Template Mode | LLM Mode | Factor Graph Mode |
|----------------|---------------|----------|-------------------|
| `id` | `f"template_{iteration}"` | `f"llm_{iteration}"` | `strategy.id` |
| `generation` | `iteration_num` | `iteration_num` | `strategy.generation` |
| `metrics` | `StrategyMetrics` | `StrategyMetrics` | `strategy.metrics` |
| `dominates(other)` | Compare sharpe_ratio | Compare sharpe_ratio | Compare sharpe_ratio |
| `get_parameters()` | Template params dict | `{}` (in code) | Factor config dict |
| `get_metrics()` | `metrics.to_dict()` | `metrics.to_dict()` | `metrics.to_dict()` |

**Implementation Strategy**: Adapter pattern not needed - existing classes already have these attributes/methods through duck typing.

## Error Handling

### 1. IStrategy Protocol Validation

**Runtime Checks** (Simplified per Audit Recommendation):
```python
def validate_strategy(obj: Any) -> None:
    """Validate object implements IStrategy protocol at runtime.

    The @runtime_checkable decorator on IStrategy Protocol enables
    isinstance() to verify all required attributes and methods exist.
    This eliminates the need for explicit hasattr() checks.

    Design Decision (Audit Feedback):
    - Original design had redundant hasattr() checks
    - isinstance() check is sufficient for Protocol validation
    - Simpler implementation reduces maintenance burden
    """
    if not isinstance(obj, IStrategy):
        raise TypeError(
            f"Object {type(obj).__name__} does not implement IStrategy protocol. "
            f"Required: id, generation, metrics properties and "
            f"dominates(), get_parameters(), get_metrics() methods."
        )
```

**Usage in ChampionTracker**:
```python
def update_champion(self, strategy: IStrategy, **kwargs) -> bool:
    # Runtime validation
    validate_strategy(strategy)

    # Proceed with update logic
    ...
```

### 2. Serialization Error Handling

**Strategy.to_dict() Failures**:
```python
def save_strategy(self, strategy: Strategy, **kwargs) -> bool:
    try:
        # Attempt serialization
        strategy_dict = strategy.to_dict()
    except Exception as e:
        logger.error(f"Strategy serialization failed: {e}")
        return False

    try:
        # Attempt file write
        self._atomic_write(tier_file, strategy_dict)
    except Exception as e:
        logger.error(f"Strategy persistence failed: {e}")
        # Attempt backup recovery
        self._restore_from_backup(tier_file)
        return False

    return True
```

**Strategy.from_dict() Failures**:
```python
def load_strategy(self, strategy_id: str, **kwargs) -> Optional[Strategy]:
    try:
        # Read file
        data = self._read_file(tier_file)
        strategy_dict = self._find_by_id(data, strategy_id)

        # Attempt deserialization
        strategy = Strategy.from_dict(strategy_dict)

        # Validate DAG structure integrity
        if not self._validate_dag(strategy):
            raise ValueError("DAG structure validation failed")

        return strategy

    except FileNotFoundError:
        logger.warning(f"Strategy file not found for tier: {tier}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Strategy deserialization failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading strategy: {e}")
        return None
```

### 3. Champion Update Error Handling

**Factor Graph Mode Validation**:
```python
# iteration_executor.py
strategy_obj = self._strategy_registry.get(strategy_id)

if generation_method == "factor_graph":
    if not strategy_obj:
        logger.error(
            f"Factor Graph champion update failed: "
            f"Strategy {strategy_id} not found in registry"
        )
        # Continue execution, don't crash iteration
        return IterationRecord(
            error_msg=f"Champion update failed: missing strategy",
            ...
        )

    # Validate Strategy implements IStrategy
    try:
        validate_strategy(strategy_obj)
    except (TypeError, AttributeError) as e:
        logger.error(f"Strategy validation failed: {e}")
        return IterationRecord(error_msg=str(e), ...)
```

**ChampionTracker Validation** (existing):
```python
# champion_tracker.py:574-591 (EXISTING)
if generation_method == "factor_graph":
    if not strategy or not strategy_id or strategy_generation is None:
        raise ValueError(
            "Factor Graph mode requires 'strategy', 'strategy_id', "
            "and 'strategy_generation' parameters"
        )
```

### 4. Graceful Degradation

**File Corruption Recovery**:
- Atomic writes prevent partial writes (temp file → rename)
- Backup files created after successful writes
- Restore from backup if main file corrupted
- Log errors but don't crash system

**Missing Data Handling**:
- Return None for missing strategies (don't raise)
- Return empty list for empty tiers (don't raise)
- Log warnings for missing required fields
- Skip corrupted entries, process remaining data

## Testing Strategy

### 1. TDD Implementation Sequence

**Phase 3: Factor Graph Serialization**

```
RED Phase:
1. test_strategy_to_dict_roundtrip() - FAIL (not implemented)
2. test_repository_save_strategy() - FAIL (not implemented)
3. test_repository_load_strategy() - FAIL (not implemented)
4. test_dag_structure_preservation() - FAIL (not implemented)

GREEN Phase:
1. Implement HallOfFameRepository.save_strategy()
2. Implement HallOfFameRepository.load_strategy()
3. Implement HallOfFameRepository.get_all_strategies()
4. Verify all tests PASS

REFACTOR Phase:
1. Extract common serialization logic
2. Optimize caching strategy
3. Improve error messages
4. Add performance optimizations
```

**Phase 4: Unified Interface**

```
RED Phase:
1. test_istrategy_protocol_definition() - FAIL (not defined)
2. test_template_implements_istrategy() - FAIL (not implemented)
3. test_llm_implements_istrategy() - FAIL (not implemented)
4. test_factorgraph_implements_istrategy() - FAIL (not implemented)
5. test_champion_update_factor_graph() - FAIL (bug not fixed)

GREEN Phase:
1. Define IStrategy Protocol in interfaces.py
2. Verify Template/LLM/Factor Graph satisfy Protocol (no code changes needed)
3. Fix iteration_executor.py:1239 bug
4. Verify all tests PASS

REFACTOR Phase:
1. Add comprehensive docstrings
2. Improve error messages
3. Add validation helpers
4. Document behavioral contracts
```

**Phase 5: Architecture Validation**

```
RED Phase:
1. test_champion_tracker_no_file_io() - FAIL (validation not implemented)
2. test_repository_no_business_logic() - FAIL (validation not implemented)
3. test_istrategy_no_persistence() - FAIL (validation not implemented)

GREEN Phase:
1. Implement architecture violation detectors
2. Scan ChampionTracker for file I/O patterns
3. Scan HallOfFameRepository for business logic patterns
4. Verify all tests PASS

REFACTOR Phase:
1. Document architecture tests in README
2. Add CI/CD integration
3. Create architecture decision records (ADRs)
```

### 2. Unit Tests

**IStrategy Protocol Tests** (`tests/unit/test_istrategy_protocol.py`):

```python
def test_istrategy_runtime_checkable():
    """Verify @runtime_checkable enables isinstance() checks."""
    from src.learning.interfaces import IStrategy
    from src.evolution.types import Strategy

    strategy = Strategy(...)
    assert isinstance(strategy, IStrategy)

def test_istrategy_required_properties():
    """Verify IStrategy requires id, generation, metrics properties."""
    class IncompleteStrategy:
        pass

    obj = IncompleteStrategy()
    assert not isinstance(obj, IStrategy)

def test_istrategy_required_methods():
    """Verify IStrategy requires dominates, get_parameters, get_metrics."""
    class PartialStrategy:
        id = "test"
        generation = 0
        metrics = None

    obj = PartialStrategy()
    assert not isinstance(obj, IStrategy)  # Missing methods
```

**Serialization Tests** (`tests/unit/test_strategy_serialization.py`):

```python
def test_strategy_to_dict_roundtrip():
    """Verify Strategy.to_dict() → from_dict() preserves data."""
    original = Strategy(
        id="test_001",
        generation=1,
        parent_ids=[],
        code=None,
        parameters={"param1": 10},
        metrics=MultiObjectiveMetrics(...),
        dag_structure={...}
    )

    # Serialize
    strategy_dict = original.to_dict()

    # Deserialize
    restored = Strategy.from_dict(strategy_dict)

    # Verify
    assert restored.id == original.id
    assert restored.generation == original.generation
    assert restored.dag_structure == original.dag_structure

def test_dag_structure_preservation():
    """Verify DAG topology preserved in serialization."""
    strategy = create_complex_dag_strategy()

    strategy_dict = strategy.to_dict()
    restored = Strategy.from_dict(strategy_dict)

    # Verify node count
    assert len(restored.dag_structure['nodes']) == len(strategy.dag_structure['nodes'])

    # Verify edge relationships
    assert restored.dag_structure['edges'] == strategy.dag_structure['edges']
```

**Repository Tests** (`tests/unit/test_hall_of_fame_repository.py`):

```python
def test_save_strategy_success():
    """Verify HallOfFameRepository.save_strategy() persists data."""
    repo = HallOfFameRepository(base_path="/tmp/test_repo")
    strategy = create_test_strategy()

    success = repo.save_strategy(strategy, tier="champions")

    assert success is True
    assert os.path.exists(repo._get_tier_file("champions"))

def test_load_strategy_success():
    """Verify HallOfFameRepository.load_strategy() restores data."""
    repo = HallOfFameRepository(base_path="/tmp/test_repo")
    original = create_test_strategy()

    # Save
    repo.save_strategy(original, tier="champions")

    # Load
    restored = repo.load_strategy(original.id, tier="champions")

    assert restored is not None
    assert restored.id == original.id
    assert restored.metrics == original.metrics

def test_load_strategy_not_found():
    """Verify load_strategy() returns None for missing strategies."""
    repo = HallOfFameRepository(base_path="/tmp/test_repo")

    result = repo.load_strategy("nonexistent_id")

    assert result is None  # Don't raise exception
```

### 3. Integration Tests

**Three-Mode Champion Update Test** (`tests/integration/test_champion_update_all_modes.py`):

```python
def test_template_mode_champion_update():
    """Verify Template mode champion update flow."""
    executor = TemplateIterationExecutor(...)

    record = executor.execute_iteration(iteration_num=0)

    assert record.champion_updated in [True, False]
    assert record.classification_level in ["LEVEL_0", "LEVEL_1", "LEVEL_2", "LEVEL_3"]

def test_llm_mode_champion_update():
    """Verify LLM mode champion update flow."""
    executor = StandardIterationExecutor(use_llm=True, ...)

    record = executor.execute_iteration(iteration_num=0)

    assert record.generation_method == "llm"
    # Verify champion update called with correct parameters

def test_factor_graph_mode_champion_update():
    """Verify Factor Graph mode champion update flow (BUG FIX VALIDATION)."""
    executor = StandardIterationExecutor(use_factor_graph=True, ...)

    record = executor.execute_iteration(iteration_num=0)

    assert record.generation_method == "factor_graph"

    # Verify strategy parameter passed correctly
    # This test should FAIL before fix, PASS after fix
    if record.champion_updated:
        champion = executor.champion_tracker.champion
        assert champion.strategy_id is not None
        assert champion.strategy_generation is not None
```

**Repository Integration Test** (`tests/integration/test_repository_strategy_persistence.py`):

```python
def test_end_to_end_strategy_persistence():
    """Verify complete save → load → verify cycle."""
    # Create Strategy
    strategy = create_factor_graph_strategy()

    # Persist via Repository
    repo = HallOfFameRepository()
    repo.save_strategy(strategy, tier="champions")

    # Load via Repository
    restored = repo.load_strategy(strategy.id)

    # Verify using IStrategy contract
    assert isinstance(restored, IStrategy)
    assert restored.dominates(strategy) is False  # Equal performance
    assert strategy.dominates(restored) is False  # Equal performance
```

### 4. Architecture Tests

**Layer Separation Tests** (`tests/architecture/test_layer_separation.py`):

```python
def test_champion_tracker_no_file_io():
    """Verify ChampionTracker contains zero file I/O operations."""
    import ast
    import inspect
    from src.learning.champion_tracker import ChampionTracker

    source = inspect.getsource(ChampionTracker)
    tree = ast.parse(source)

    # Scan for file I/O patterns
    forbidden_patterns = ['open(', 'with open', 'json.dump', 'json.load', 'pathlib.Path']

    for pattern in forbidden_patterns:
        assert pattern not in source, \
            f"ChampionTracker contains forbidden file I/O: {pattern}"

def test_repository_no_business_logic():
    """Verify HallOfFameRepository contains zero business logic."""
    import ast
    import inspect
    from src.repository.hall_of_fame import HallOfFameRepository

    source = inspect.getsource(HallOfFameRepository)

    # Scan for business logic patterns
    forbidden_patterns = ['sharpe_ratio', 'dominates', 'if metrics']

    for pattern in forbidden_patterns:
        assert pattern not in source, \
            f"HallOfFameRepository contains forbidden business logic: {pattern}"

def test_istrategy_protocol_no_persistence():
    """Verify IStrategy Protocol contains zero persistence methods."""
    from src.learning.interfaces import IStrategy
    import inspect

    methods = [m for m in dir(IStrategy) if not m.startswith('_')]

    forbidden_methods = ['save', 'load', 'persist', 'restore']

    for method in forbidden_methods:
        assert method not in methods, \
            f"IStrategy contains forbidden persistence method: {method}"
```

### 5. Performance Tests

**Serialization Performance** (`tests/performance/test_serialization_performance.py`):

```python
def test_strategy_to_dict_performance():
    """Verify Strategy.to_dict() completes within 10ms."""
    import time

    strategy = create_complex_dag_strategy()

    start = time.time()
    strategy_dict = strategy.to_dict()
    elapsed = time.time() - start

    assert elapsed < 0.010, f"to_dict() took {elapsed*1000:.1f}ms (target: <10ms)"

def test_strategy_from_dict_performance():
    """Verify Strategy.from_dict() completes within 20ms."""
    import time

    strategy_dict = create_serialized_strategy()

    start = time.time()
    strategy = Strategy.from_dict(strategy_dict)
    elapsed = time.time() - start

    assert elapsed < 0.020, f"from_dict() took {elapsed*1000:.1f}ms (target: <20ms)"

def test_champion_update_performance():
    """Verify champion update (with persistence) completes within 100ms."""
    import time

    tracker = ChampionTracker(...)

    start = time.time()
    updated = tracker.update_champion(
        iteration_num=0,
        code="test",
        metrics={"sharpe_ratio": 2.5}
    )
    elapsed = time.time() - start

    assert elapsed < 0.100, f"update_champion() took {elapsed*1000:.1f}ms (target: <100ms)"
```

### 6. Test Coverage Goals

**Coverage Targets** (per requirements NFR-2):
- ≥ 90% coverage for new code (Phase 3-4 implementations)
- 100% coverage for IStrategy Protocol interface
- 100% coverage for bug fixes (iteration_executor.py:1239)
- ≥ 85% coverage for HallOfFameRepository extensions

**Coverage Validation**:
```bash
pytest --cov=src/learning/interfaces \
       --cov=src/repository/hall_of_fame \
       --cov=src/learning/iteration_executor \
       --cov-report=html \
       --cov-fail-under=90
```

## Implementation Phases

### Phase 3: Factor Graph Serialization (2-3 days)

**TDD Cycle**:
1. **RED**: Write failing tests for HallOfFameRepository extensions
2. **GREEN**: Implement save_strategy(), load_strategy(), get_all_strategies()
3. **REFACTOR**: Optimize caching, improve error handling

**Deliverables**:
- HallOfFameRepository.save_strategy() method
- HallOfFameRepository.load_strategy() method
- HallOfFameRepository.get_all_strategies() method
- Unit tests (≥90% coverage)
- Integration tests (roundtrip validation)

### Phase 4: Unified Interface (2-3 days)

**TDD Cycle**:
1. **RED**: Write failing tests for IStrategy Protocol
2. **GREEN**: Define IStrategy in interfaces.py, fix iteration_executor.py:1239
3. **REFACTOR**: Add docstrings, validation helpers

**Deliverables**:
- IStrategy Protocol definition
- Bug fix for iteration_executor.py:1239
- Protocol unit tests
- Three-mode integration tests
- Champion update validation tests

### Phase 5: Architecture Validation (1-2 days)

**TDD Cycle**:
1. **RED**: Write failing architecture tests
2. **GREEN**: Verify architecture constraints pass
3. **REFACTOR**: Document design decisions, create ADRs

**Deliverables**:
- Architecture layer separation tests
- Performance benchmark tests
- Complete regression test suite
- Architecture decision records (ADRs)
- Updated README with architecture documentation

## Design Audit and Revisions

### Audit Summary (Zen Analysis - gemini-2.5-pro)

**Audit Date**: 2025-11-25
**Audit Result**: ✅ **Ready to Implement** (with minor revisions)
**Overall Assessment**: "Exceptionally thorough and well-structured design document with strong adherence to SOLID principles"

**Key Strengths Identified**:
1. ✅ Architectural purity (Repository Pattern correctly preserved)
2. ✅ Excellent TDD strategy with architecture tests
3. ✅ High completeness (functional, error handling, NFRs)
4. ✅ Pragmatic implementation plan with realistic estimates

**Recommendations and Responses**:

| Recommendation | Status | Rationale |
|----------------|--------|-----------|
| **#1**: Unify Repository Interface (`save(IStrategy)`) | ⚠️ **DEFER to Phase 6** | Would require refactoring existing `StrategyGenome` code (Template/LLM modes). Expanding scope increases risk. **Decision**: Keep parallel methods for Phase 3-5, unify in future refactor. |
| **#2**: Consolidate Persistence DTOs | ⚠️ **DEFER to Phase 6** | Same rationale as #1 - larger refactor best done separately after current phases complete. |
| **#3**: Simplify `IStrategy` Validation | ✅ **ACCEPTED** | Removed redundant `hasattr()` checks. `isinstance()` with `@runtime_checkable` Protocol is sufficient. Updated design.md Lines 482-502. |
| **#4**: Rename `dominates()` to `outperforms()` | ❌ **REJECTED** | `dominates()` is correct multi-objective optimization terminology (Pareto dominance). Name is future-proof even though currently using single-objective comparison. |

**Risk Assessment Updates**:

*New Risk Identified*: **Data Model Divergence**
- **Impact**: Medium
- **Probability**: High
- **Mitigation**: Phase 3-5 implements parallel methods with clear documentation. Phase 6 (future) will unify repository interface and consolidate DTOs into single `PersistedStrategy` format.

*New Risk Identified*: **Unintended Side Effects in ChampionTracker**
- **Impact**: High
- **Probability**: Medium
- **Mitigation**: Supplement planned TDD with exploratory testing focused on champion type transitions (e.g., LLM champion → Factor Graph champion).

### Future Refactoring (Phase 6 - Post-Implementation)

Once Phases 3-5 are complete and stable, consider these architectural improvements:

1. **Unified Repository Interface**:
   ```python
   class HallOfFameRepository:
       def save(self, strategy: IStrategy, tier: str) -> bool:
           """Unified save method accepting any IStrategy implementation."""
           ...

       def load(self, strategy_id: str, tier: str) -> Optional[IStrategy]:
           """Unified load method returning IStrategy implementation."""
           ...
   ```

2. **Consolidated Persistence DTO**:
   ```python
   @dataclass
   class PersistedStrategy:
       """Unified persistence format for all three strategy modes."""
       strategy_id: str
       generation_method: str  # "template" | "llm" | "factor_graph"
       parameters: Dict[str, Any]
       metrics: Dict[str, float]
       code: Optional[str]  # None for Factor Graph
       dag_structure: Optional[Dict]  # None for Template/LLM
       created_at: str
   ```

**Benefits of Phase 6 Refactor**:
- Single persistence contract reduces maintenance burden
- Eliminates mode-specific repository methods
- Simplifies future addition of new strategy modes
- Fully aligns with Dependency Inversion Principle

## Success Criteria

Based on requirements Success Metrics section:

1. **Functional Completeness**: ✅ Three-mode champion update all pass integration tests
2. **Architecture Quality**: ✅ Architecture tests verify Domain/Persistence zero coupling
3. **Code Coverage**: ✅ ≥ 90% coverage for new code
4. **Performance**: ✅ Serialization <10ms, deserialization <20ms
5. **Backward Compatibility**: ✅ Existing Template/LLM tests all pass

**Validation Command**:
```bash
# Run complete test suite
pytest tests/ -v --cov=src --cov-report=html --cov-fail-under=90

# Run architecture tests specifically
pytest tests/architecture/ -v

# Run performance benchmarks
pytest tests/performance/ -v --benchmark-only
```
