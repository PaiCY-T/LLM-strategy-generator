# Implementation Tasks: CombinationTemplate Phase 1.5

**Spec ID**: combination-template-phase15
**Total Tasks**: 5 atomic tasks
**Estimated Time**: 1-2 weeks
**Approach**: Bottom-up (Core → Tests → Validation)

---

## Task List

- [x] 1. Implement CombinationTemplate core class
  - Create `src/templates/combination_template.py` with weighted position generation
  - Implement parameter validation and mutation logic
  - Add rebalancing frequency support (M/W-FRI)
  - Define PARAM_GRID with 2-3 template combinations
  - _Effort: 3-4 hours_
  - _Files: src/templates/combination_template.py_
  - _Leverage: src/templates/turtle_template.py (structure), src/templates/momentum_template.py (patterns)_
  - _Success: Class instantiates, generates positions, passes basic validation_

- [x] 2. Add unit tests for CombinationTemplate
  - Create `tests/templates/test_combination_template.py`
  - Test parameter validation (weights sum, template existence)
  - Test position generation (weighted sum correctness)
  - Test mutation (weight normalization, template swapping)
  - Test rebalancing (monthly vs. weekly)
  - _Effort: 2-3 hours_
  - _Files: tests/templates/test_combination_template.py_
  - _Requirements: 1_
  - _Success: ≥80% code coverage, all tests passing_

- [x] 3. Register CombinationTemplate in template registry
  - Add to `src/utils/template_registry.py`
  - Verify auto-discovery works with population manager
  - _Effort: 15 minutes_
  - _Files: src/utils/template_registry.py_
  - _Requirements: 1_
  - _Success: Template appears in TEMPLATE_REGISTRY, population manager can instantiate_

- [x] 4. Run 10-generation smoke test
  - Create integration test script or use existing test harness
  - Verify population evolves without crashes
  - Check basic metrics (Sharpe >0 for 50% of strategies)
  - _Effort: 1 hour_
  - _Requirements: 1, 2, 3_
  - _Success: Test completes, no exceptions, basic performance threshold met_
  - _Result: 4/5 criteria passed, Best Sharpe 6.296_

- [x] 5. Execute 20-generation validation test
  - Run `run_20generation_validation.py` with combination template
  - Compare results against Turtle baseline (Sharpe 1.5-2.5)
  - Analyze results for decision gate
  - Document findings in STATUS.md
  - _Effort: 2-3 hours (includes test runtime)_
  - _Requirements: 1, 2, 3, 4_
  - _Success: Validation complete, decision gate criteria evaluated, findings documented_
  - _Result: Best Sharpe 6.296, Scenario A triggered (template combination sufficient)_

---

## Task Execution Order

**Sequential Execution** (no parallelization possible):
1. Task 1 (Core implementation) → Foundation for all others
2. Task 2 (Unit tests) → Validates Task 1 correctness
3. Task 3 (Registration) → Enables integration
4. Task 4 (Smoke test) → Quick validation before expensive test
5. Task 5 (Validation test) → Final decision gate

**Critical Path**: All tasks are on critical path (1 → 2 → 3 → 4 → 5)

---

## Acceptance Criteria (Overall)

### Phase 1.5 Complete When:
- [x] All 5 tasks completed
- [x] Unit tests passing with ≥80% coverage
- [x] 10-generation smoke test successful
- [x] 20-generation validation test executed
- [x] Decision gate analysis documented (Scenario A/B/C)

### Decision Gate Outcomes:
**Scenario A** (Sharpe >2.5): Template combination sufficient, end Phase 1.5
**Scenario B** (Sharpe ≤2.5): Proceed to structural mutation design
**Scenario C** (Inconclusive): Extend validation test

---

## Notes

- All tasks use existing infrastructure (no changes to population_manager.py, mutation.py)
- Rollback plan: Remove from registry, delete 2 files
- Risk: Low (1-2 week investment, 100% code reuse)
