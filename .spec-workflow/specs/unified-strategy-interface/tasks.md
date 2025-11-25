# unified-strategy-interface-refactor - Task List

## Implementation Tasks

### Phase 3: Factor Graph Serialization Support

- [x] **Task 3.1: Extend HallOfFameRepository for Strategy Object Persistence**
    - [x] 3.1.1. Add Strategy save/load methods to HallOfFameRepository
        - *Goal*: Enable HallOfFameRepository to persist Factor Graph Strategy objects
        - *Details*:
          - Add `save_strategy(strategy: Strategy, tier: str)` method
          - Add `load_strategy(tier: str) -> Optional[Strategy]` method
          - Use existing `Strategy.to_dict()` for serialization
          - Use existing `Strategy.from_dict()` for deserialization
          - Maintain tier-based storage (Champions/Contenders/Archive)
        - *Requirements*: AC-2 (requirements.md Line 102-106)
        - *Files*: `src/repository/hall_of_fame.py`

    - [x] 3.1.2. Write unit tests for Strategy serialization
        - *Goal*: Verify Strategy objects can be saved and loaded correctly
        - *Details*:
          - Test roundtrip: `save_strategy()` → `load_strategy()` → verify equality
          - Test DAG structure preservation (nodes, edges, topology)
          - Test metadata preservation (strategy_id, generation, parent_ids)
          - Test error handling (corrupted JSON, missing fields)
        - *Requirements*: AC-2 (requirements.md Line 107), AC-5 (Line 131)
        - *Files*: `tests/repository/test_hall_of_fame_strategy_persistence.py` (new)

- [ ] **Task 3.2: Validate DAG Structure Preservation**
    - [ ] 3.2.1. Implement DAG integrity tests
        - *Goal*: Ensure Factor Graph topology is preserved after serialization
        - *Details*:
          - Create complex Strategy with multiple Selection/Filter nodes
          - Serialize → Deserialize → Verify node relationships intact
          - Verify factor parameters preserved (lookback, threshold, etc.)
          - Test edge cases (empty DAG, single-node DAG, circular references)
        - *Requirements*: AC-2 (requirements.md Line 105-106)
        - *Files*: `tests/integration/test_factor_graph_serialization.py` (new)

### Phase 4: Unified Interface & Bug Fix

- [ ] **Task 4.1: Define IStrategy Protocol**
    - [ ] 4.1.1. Create IStrategy Protocol interface
        - *Goal*: Define unified domain contract for all strategy types
        - *Details*:
          - Create `src/learning/interfaces.py` (add to existing file)
          - Add `@runtime_checkable` decorator
          - Define properties: `id`, `generation`, `metrics`
          - Define methods: `dominates(other)`, `get_parameters()`, `get_metrics()`
          - **Do NOT include** `save()`, `load()`, `to_dict()`, `from_dict()` (Persistence Layer)
          - Add comprehensive docstrings with behavioral contracts
        - *Requirements*: AC-1 (requirements.md Line 89-97), US-1
        - *Files*: `src/learning/interfaces.py`

    - [ ] 4.1.2. Write IStrategy Protocol validation tests
        - *Goal*: Verify isinstance() checks work correctly for all strategy types
        - *Details*:
          - Test Template strategy implements IStrategy
          - Test LLM strategy implements IStrategy
          - Test Factor Graph Strategy implements IStrategy
          - Test negative case (object without required methods fails check)
          - Test `validate_strategy()` helper function
        - *Requirements*: AC-5 (requirements.md Line 129)
        - *Files*: `tests/unit/test_istrategy_protocol.py` (new)

- [ ] **Task 4.2: Fix Factor Graph Champion Update Bug**
    - [ ] 4.2.1. Fix iteration_executor.py:1239 missing strategy parameter
        - *Goal*: Fix Factor Graph champion update to pass strategy object
        - *Details*:
          - Locate `iteration_executor.py` line ~1239 (Factor Graph mode)
          - Retrieve `strategy_obj` from `self._strategy_registry[strategy_id]`
          - Pass `strategy=strategy_obj` to `ChampionTracker.update_champion()`
          - Verify Template/LLM modes still work (regression test)
        - *Requirements*: AC-3 (requirements.md Line 110-117), US-3
        - *Files*: `src/learning/iteration_executor.py`

    - [ ] 4.2.2. Write champion update integration tests
        - *Goal*: Verify all three modes update champion correctly
        - *Details*:
          - Test Template Mode: `update_champion()` receives correct parameters
          - Test LLM Mode: `update_champion()` receives correct parameters
          - Test Factor Graph Mode: `update_champion(strategy=strategy_obj)` works
          - Test champion persistence after update (HallOfFameRepository)
          - Mock HallOfFameRepository to isolate ChampionTracker logic
        - *Requirements*: AC-3 (requirements.md Line 116), AC-5 (Line 131)
        - *Files*: `tests/integration/test_champion_update_three_modes.py` (new)

### Phase 5: Architecture Validation

- [ ] **Task 5.1: Architecture Layer Separation Tests**
    - [ ] 5.1.1. Verify ChampionTracker has no file I/O code
        - *Goal*: Ensure Domain layer contains zero persistence logic
        - *Details*:
          - Static analysis: grep for `open()`, `json.dump()`, `Path()` in `champion_tracker.py`
          - Verify all persistence calls delegate to HallOfFameRepository
          - Test: Mock HallOfFameRepository, verify ChampionTracker never accesses filesystem
        - *Requirements*: AC-4 (requirements.md Line 120-126)
        - *Files*: `tests/architecture/test_domain_layer_purity.py` (new)

    - [ ] 5.1.2. Verify HallOfFameRepository has no business logic
        - *Goal*: Ensure Persistence layer contains zero domain logic
        - *Details*:
          - Static analysis: grep for Sharpe comparison, strategy dominance in `hall_of_fame.py`
          - Verify HallOfFameRepository only does CRUD operations
          - Test: Repository should save any strategy regardless of metrics
        - *Requirements*: AC-4 (requirements.md Line 121)
        - *Files*: `tests/architecture/test_persistence_layer_purity.py` (new)

    - [ ] 5.1.3. Verify IStrategy has no persistence methods
        - *Goal*: Ensure Protocol interface is pure domain contract
        - *Details*:
          - Static analysis: verify IStrategy Protocol definition
          - Confirm no `save()`, `load()`, `to_dict()`, `from_dict()` in Protocol
          - Test: Implementation classes can have these methods (not required by Protocol)
        - *Requirements*: AC-4 (requirements.md Line 122)
        - *Files*: `tests/architecture/test_protocol_purity.py` (new)

- [ ] **Task 5.2: Performance & Regression Testing**
    - [ ] 5.2.1. Benchmark serialization performance
        - *Goal*: Verify serialization meets performance targets
        - *Details*:
          - Test `Strategy.to_dict()` < 10ms per strategy
          - Test `Strategy.from_dict()` < 20ms per strategy
          - Test `ChampionTracker.update_champion()` < 100ms (including persistence)
          - Test serialized JSON size < 100KB per strategy
        - *Requirements*: NFR-1 (requirements.md Line 137-143)
        - *Files*: `tests/performance/test_serialization_performance.py` (new)

    - [ ] 5.2.2. Run full regression test suite
        - *Goal*: Verify no existing functionality broken
        - *Details*:
          - Run all existing Template Mode tests
          - Run all existing LLM Mode tests
          - Run all existing Factor Graph Mode tests
          - Verify existing champion_strategy.json files still load
        - *Requirements*: NFR-3 (requirements.md Line 152-156)
        - *Files*: All existing test files

- [ ] **Task 5.3: Documentation & Review**
    - [x] 5.3.1. Update architecture documentation
        - *Goal*: Document Repository Pattern design decisions
        - *Details*:
          - Add section to `docs/ARCHITECTURE.md` explaining IStrategy Protocol
          - Document why persistence methods excluded from Protocol
          - Add sequence diagrams for Champion update flow (3 modes)
          - Document audit recommendations and decisions (ACCEPTED/DEFERRED/REJECTED)
        - *Requirements*: AC-4 (requirements.md Line 126)
        - *Files*: `docs/ARCHITECTURE.md`

    - [ ] 5.3.2. Code review and cleanup
        - *Goal*: Final quality check before merge
        - *Details*:
          - Review all modified files for code quality
          - Verify test coverage ≥ 90% for new code
          - Check all docstrings complete and accurate
          - Run linter and type checker
          - Update CHANGELOG.md with changes
        - *Requirements*: NFR-2 (requirements.md Line 145-150)
        - *Files*: All modified files

## Task Dependencies

### Detailed Dependency Graph

#### Phase 3: Factor Graph Serialization
```
3.1.1 (Implement save_strategy/load_strategy)
  ↓
  ├─→ 3.1.2 (Unit tests for Strategy persistence)
  └─→ 3.2.1 (DAG integrity tests)

Parallelization Opportunity: NONE (Sequential execution required)
Critical Path: 3.1.1 → 3.1.2 → 3.2.1 (18 hours)
```

**Dependencies**:
- 3.1.2 **DEPENDS ON** 3.1.1 (cannot test before implementation exists)
- 3.2.1 **DEPENDS ON** 3.1.1 (needs serialization methods to test DAG)
- 3.1.2 and 3.2.1 **CANNOT** run in parallel (both need stable 3.1.1)

**Phase 3 → Phase 4 Relationship**: **INDEPENDENT** (can run in parallel)

---

#### Phase 4: Unified Interface & Bug Fix
```
4.1.1 (Define IStrategy Protocol) ║ 4.2.1 (Fix iteration_executor.py bug)
  ↓                                ║   ↓
4.1.2 (Protocol validation tests) ║ 4.2.2 (Champion update integration tests)

Parallelization Opportunity: HIGH
  - Track 1: 4.1.1 → 4.1.2 (8 hours)
  - Track 2: 4.2.1 → 4.2.2 (8 hours)
  → Both tracks run in parallel → Total: 8 hours (not 16!)

Critical Path: 4.1 OR 4.2 (whichever finishes last, estimated 8 hours each)
```

**Dependencies**:
- 4.1.2 **DEPENDS ON** 4.1.1 (must define Protocol before testing)
- 4.2.2 **DEPENDS ON** 4.2.1 (must fix bug before testing fix)
- 4.1.1 **INDEPENDENT OF** 4.2.1 (Protocol definition doesn't touch iteration_executor.py)
- 4.1.2 **INDEPENDENT OF** 4.2.2 (different test targets)

**Phase 4 → Phase 3 Relationship**: **INDEPENDENT** (no file conflicts)

---

#### Phase 5: Architecture Validation
```
[Phase 3 Complete] ──┐
                      ├─→ 5.1.1 (Domain layer tests)    ║ 5.2.1 (Performance tests)
[Phase 4 Complete] ──┘    ↓                             ║
                          5.1.2 (Persistence tests)     ║
                            ↓                           ║
                          5.1.3 (Protocol purity tests) ║
                            ↓                           ↓
                          5.2.2 (Regression tests - requires ALL previous tasks)
                            ↓
                          5.3.1 (Architecture docs)
                            ↓
                          5.3.2 (Code review)

Parallelization Opportunity: MEDIUM
  - 5.1 (all subtasks) can run in parallel with 5.2.1
  - 5.2.2 must wait for everything to complete
  - 5.3 can start once 5.1 and 5.2.1 done

Critical Path: 5.1 (6h) || 5.2.1 (2h) → 5.2.2 (4h) → 5.3 (4h) = 14 hours
  (Instead of 16 hours if sequential)
```

**Dependencies**:
- **ALL Phase 5 tasks** require Phase 3 AND Phase 4 complete
- 5.1.1, 5.1.2, 5.1.3 **INDEPENDENT** (can run in parallel if resources available)
- 5.2.1 **INDEPENDENT OF** 5.1.x (can run in parallel)
- 5.2.2 **DEPENDS ON** ALL previous tasks (regression must test everything)
- 5.3.1 **DEPENDS ON** Phase 3 + Phase 4 complete
- 5.3.2 **DEPENDS ON** 5.3.1 (review after documentation)

---

### Cross-Phase Parallel Execution Analysis

#### Optimal Parallel Strategy (2 Developers)

**Week 1: Phase 3 || Phase 4**
```
Developer A (Track 1):          Developer B (Track 2):
Day 1-2: 3.1.1 → 3.1.2 (12h)    Day 1: 4.1.1 → 4.1.2 (8h)
Day 3: 3.2.1 (6h)                Day 2: 4.2.1 → 4.2.2 (8h)
                                 Day 3: Phase 4 validation (idle)
```

**Result**: Phase 3 (18h) and Phase 4 (16h) complete in **3 days** (instead of 5-6 days sequential)

**Week 2: Phase 5**
```
Developer A:                    Developer B:
Day 1: 5.1.1 → 5.1.2 → 5.1.3   Day 1: 5.2.1 (Performance tests)
       (6h)                             (2h) + 4h idle
Day 2: 5.2.2 (Regression) - both developers collaborate (4h)
Day 3: 5.3.1 + 5.3.2 (4h)
```

**Result**: Phase 5 complete in **2.5 days** (instead of 2 days sequential)

---

### Single Developer Sequential Execution

**Week 1-2: No Parallelization**
```
Day 1-2: Phase 3 (3.1.1 → 3.1.2 → 3.2.1) = 18 hours
Day 3-4: Phase 4 (4.1.1 → 4.1.2 → 4.2.1 → 4.2.2) = 16 hours
Day 5-6: Phase 5 (5.1 → 5.2 → 5.3) = 16 hours
```

**Result**: Total 50 hours = **6.25 working days** (rounded to 7 days)

---

### Task Dependency Matrix

| Task    | Depends On            | Can Run Parallel With | Blocks           |
|---------|----------------------|----------------------|------------------|
| 3.1.1   | None                 | 4.1.1, 4.2.1         | 3.1.2, 3.2.1     |
| 3.1.2   | 3.1.1                | 4.1.2, 4.2.2         | 3.2.1            |
| 3.2.1   | 3.1.1                | 4.x (all)            | Phase 5          |
| 4.1.1   | None                 | 3.x (all), 4.2.1     | 4.1.2            |
| 4.1.2   | 4.1.1                | 3.x (all), 4.2.2     | Phase 5          |
| 4.2.1   | None                 | 3.x (all), 4.1.1     | 4.2.2            |
| 4.2.2   | 4.2.1                | 3.x (all), 4.1.2     | Phase 5          |
| 5.1.x   | Phase 3 + 4          | 5.2.1                | 5.2.2            |
| 5.2.1   | Phase 3              | 5.1.x                | 5.2.2            |
| 5.2.2   | ALL previous         | None                 | 5.3              |
| 5.3.1   | Phase 3 + 4          | None (sequential)    | 5.3.2            |
| 5.3.2   | 5.3.1                | None                 | Project Complete |

---

### Recommended Execution Strategy

#### Strategy A: Single Developer (Sequential)
- **Duration**: 6-7 working days
- **Pros**: Simple coordination, no merge conflicts
- **Cons**: Slower delivery
- **Recommended**: Small team, tight coordination not feasible

#### Strategy B: Two Developers (Parallel Phase 3 + 4)
- **Duration**: 3-4 working days (40% time reduction)
- **Pros**: Faster delivery, clear separation of concerns
- **Cons**: Requires coordination at Phase 5, potential merge conflicts
- **Recommended**: **OPTIMAL for this project** (no file overlap between Phase 3 and 4)

#### Strategy C: Three+ Developers (Maximum Parallelization)
- **Duration**: 3 working days (minimal improvement over Strategy B)
- **Pros**: Slightly faster Phase 5
- **Cons**: Overhead, coordination complexity, diminishing returns
- **Recommended**: Only if developers already familiar with codebase

## Estimated Timeline

### Phase 3: Factor Graph Serialization (2-3 days)
- Task 3.1: HallOfFameRepository extension - **12 hours**
  - 3.1.1: Implementation (6 hours)
  - 3.1.2: Unit tests (6 hours)
- Task 3.2: DAG validation - **6 hours**
  - 3.2.1: Integration tests (6 hours)

### Phase 4: Unified Interface (2-3 days)
- Task 4.1: IStrategy Protocol - **8 hours**
  - 4.1.1: Protocol definition (3 hours)
  - 4.1.2: Protocol tests (5 hours)
- Task 4.2: Bug fix - **8 hours**
  - 4.2.1: Fix iteration_executor.py (2 hours)
  - 4.2.2: Integration tests (6 hours)

### Phase 5: Architecture Validation (1-2 days)
- Task 5.1: Architecture tests - **6 hours**
  - 5.1.1: Domain layer tests (2 hours)
  - 5.1.2: Persistence layer tests (2 hours)
  - 5.1.3: Protocol purity tests (2 hours)
- Task 5.2: Performance & regression - **6 hours**
  - 5.2.1: Performance benchmarks (2 hours)
  - 5.2.2: Regression testing (4 hours)
- Task 5.3: Documentation - **4 hours**
  - 5.3.1: Architecture docs (2 hours)
  - 5.3.2: Code review (2 hours)

**Total Estimated Time: 50 hours (5-7 working days)**

## Success Metrics

1. **Functional Completeness**: All 3 modes (Template/LLM/Factor Graph) champion update tests pass
2. **Architecture Quality**: All architecture tests pass (Domain/Persistence/Protocol layer separation verified)
3. **Code Coverage**: ≥ 90% test coverage for new code
4. **Performance**: Serialization < 10ms, Deserialization < 20ms, Champion update < 100ms
5. **Backward Compatibility**: All existing Template/LLM tests pass (no regression)

## Risk Mitigation

### Risk 1: Factor Graph DAG Serialization Complexity
- **Mitigation**: Start with simple Strategy (1-2 nodes), gradually increase complexity
- **Fallback**: Use manual validation if automated tests too complex

### Risk 2: Backward Compatibility Break
- **Mitigation**: Run regression tests after each phase, not just at end
- **Fallback**: Use feature flag to enable/disable new Strategy persistence

### Risk 3: Performance Regression
- **Mitigation**: Establish performance baseline before changes, compare after each phase
- **Fallback**: Optimize serialization (caching, lazy loading) if targets missed
