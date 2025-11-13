# Phase 3 Tasks: Champion Trap Fix

**Spec ID**: learning-system-stability-fixes
**Phase**: Phase 3 - Champion Trap Fix
**Status**: 🔄 IN PROGRESS
**Created**: 2025-10-13
**Priority**: P0 Critical
**Based on**: Multi-AI Root Cause Analysis (Ultrathink + O3-Mini + Gemini 2.5 Pro)

---

## Implementation Strategy

**Bottom-Up Approach**:
1. Core mechanism fixes (Hybrid Threshold) → Immediate impact
2. Prevention systems (Staleness, Multi-Objective) → Long-term robustness
3. Validation and tuning → Production readiness

**Atomic Task Rules**:
- Each task: 30-60 minutes
- Touch 1-3 files
- Clear success criteria
- Independent or明確dependencies

---

## Priority 1: Hybrid Threshold Mechanism (CRITICAL)

_Requirements: F10.1-F10.4, Story 10.1_
_Goal: Fix champion update blockage by accepting realistic improvements_

### Task 1: Update Configuration Schema
- [ ] 1.1 Add new fields to `config/learning_system.yaml`
  - Add `post_probation_relative_threshold: 0.01` (1%, down from 0.05)
  - Add `additive_threshold: 0.02` (new absolute improvement)
  - Document threshold meanings with examples
  - Add `threshold_logging_enabled: true`
  - **Files**: `config/learning_system.yaml`
  - **Success**: YAML parses correctly, new fields accessible
  - **Time**: 15 minutes

### Task 2: Extend Anti-Churn Manager
- [ ] 2.1 Update `AntiChurnManager` class in `src/config/anti_churn_manager.py`
  - Add `self.additive_threshold` attribute
  - Load from config in `__init__()`
  - Add property getter `get_additive_threshold()`
  - Update docstrings explaining hybrid threshold logic
  - **Files**: `src/config/anti_churn_manager.py`
  - **Dependencies**: Task 1.1
  - **Success**: Manager loads additive threshold correctly
  - **Time**: 20 minutes

### Task 3: Implement Hybrid Threshold Logic
- [ ] 3.1 Modify `_update_champion()` in `artifacts/working/modules/autonomous_loop.py`
  - Calculate both thresholds:
    * `relative_required = champion_sharpe * (1 + relative_threshold)`
    * `absolute_required = champion_sharpe + additive_threshold`
  - Accept if EITHER condition met:
    * `current_sharpe >= relative_required` OR
    * `current_sharpe >= absolute_required`
  - Log which condition triggered (relative/absolute/both)
  - **Files**: `artifacts/working/modules/autonomous_loop.py`
  - **Dependencies**: Task 2.1
  - **Success**: Logic accepts strategies meeting either threshold
  - **Time**: 30 minutes

### Task 4: Add Threshold Effectiveness Tracking
- [ ] 4.1 Track threshold metrics in `autonomous_loop.py`
  - Count acceptances by type (relative/absolute/both)
  - Calculate acceptance rate
  - Store in `iteration_history.json` as `threshold_trigger`
  - Log threshold effectiveness every 10 iterations
  - **Files**: `artifacts/working/modules/autonomous_loop.py`, `iteration_history.json`
  - **Dependencies**: Task 3.1
  - **Success**: Metrics logged and trackable
  - **Time**: 25 minutes

### Task 5: Historical Backtest Validation
- [ ] 5.1 Create validation script `scripts/validate_hybrid_threshold.py`
  - Load 313 historical iterations
  - Replay champion update decisions with new thresholds
  - Calculate new champion update frequency
  - Identify which rejected strategies would be accepted
  - Generate comparison report (old vs new thresholds)
  - **Target**: 10-20% update frequency (vs current 0%)
  - **Target**: At least 2 of 4 rejected strategies accepted
  - **Files**: New file `scripts/validate_hybrid_threshold.py`
  - **Dependencies**: Task 3.1
  - **Success**: Report shows 10-20% update frequency
  - **Time**: 45 minutes

### Task 6: Unit Tests for Hybrid Threshold
- [ ] 6.1 Create test suite `tests/test_hybrid_threshold.py`
  - Test relative threshold only (Sharpe 1.0 → 1.011 with 1% threshold)
  - Test absolute threshold only (Sharpe 2.47 → 2.49 with 0.02 threshold)
  - Test both thresholds met (Sharpe 2.47 → 2.52)
  - Test neither threshold met (Sharpe 2.47 → 2.48)
  - Test threshold logging correctness
  - **Files**: New file `tests/test_hybrid_threshold.py`
  - **Dependencies**: Task 3.1
  - **Success**: All tests passing
  - **Time**: 30 minutes

---

## Priority 2: Champion Staleness Mechanism (HIGH)

_Requirements: F11.1-F11.4, Story 10.2_
_Goal: Prevent long-term stagnation from outlier champions_

### Task 7: Staleness Configuration
- [ ] 7.1 Add staleness parameters to `config/learning_system.yaml`
  - Add `staleness_check_interval: 50` (check every N iterations)
  - Add `staleness_cohort_percentile: 0.10` (top 10%)
  - Add `staleness_min_cohort_size: 5` (minimum for comparison)
  - Add `staleness_enabled: true` (feature flag)
  - Document staleness mechanism
  - **Files**: `config/learning_system.yaml`
  - **Dependencies**: None (parallel with Task 1.1)
  - **Success**: Configuration loaded correctly
  - **Time**: 15 minutes

### Task 8: Staleness Check Implementation
- [x] 8.1 Add `_check_champion_staleness()` method to `autonomous_loop.py` ✅ COMPLETE
  - Extract last N strategies from history
  - Calculate top 10% threshold (e.g., 90th percentile)
  - Extract strategies above threshold (top 10% cohort)
  - Calculate cohort median Sharpe
  - Compare champion Sharpe vs cohort median
  - Return demotion recommendation if champion < cohort median
  - **Files**: `artifacts/working/modules/autonomous_loop.py`
  - **Dependencies**: Task 7.1
  - **Success**: Method correctly identifies stale champions
  - **Time**: 40 minutes
  - **Completed**: 2025-10-13

### Task 9: Automatic Champion Demotion
- [ ] 9.1 Implement staleness-triggered demotion in `autonomous_loop.py`
  - Call `_check_champion_staleness()` every N iterations
  - If stale, select best strategy from recent cohort
  - Demote current champion to Hall of Fame
  - Promote best cohort strategy to champion
  - Log demotion reason, metrics, and cohort stats
  - **Files**: `artifacts/working/modules/autonomous_loop.py`
  - **Dependencies**: Task 8.1
  - **Success**: Demotion executed and logged correctly
  - **Time**: 35 minutes

### Task 10: Staleness Unit Tests
- [ ] 10.1 Create test suite `tests/test_champion_staleness.py`
  - Test staleness detection (champion < cohort median)
  - Test staleness not triggered (champion > cohort median)
  - Test insufficient cohort size (skip staleness check)
  - Test demotion and promotion mechanics
  - Test edge case: champion is also best in cohort
  - **Files**: New file `tests/test_champion_staleness.py`
  - **Dependencies**: Task 9.1
  - **Success**: All tests passing
  - **Time**: 35 minutes

---

## Priority 3: Multi-Objective Validation (MEDIUM)

_Requirements: F12.1-F12.4, Story 10.3_
_Goal: Prevent brittle strategy selection_

### Task 11: Calmar Ratio Calculation
- [ ] 11.1 Add `calculate_calmar_ratio()` to metrics module
  - Formula: `annual_return / abs(max_drawdown)`
  - Handle edge cases (zero/NaN drawdown)
  - Return None for invalid calculations
  - Add unit tests for edge cases
  - **Files**: `artifacts/working/modules/metrics.py` or new `src/metrics/calmar.py`
  - **Dependencies**: None
  - **Success**: Calmar calculated correctly for test cases
  - **Time**: 25 minutes

### Task 12: Multi-Objective Configuration
- [ ] 12.1 Add multi-objective parameters to `config/learning_system.yaml`
  - Add `multi_objective_enabled: true`
  - Add `calmar_retention_ratio: 0.90` (maintain 90%)
  - Add `max_drawdown_tolerance: 1.10` (allow 10% worse)
  - Document metric relationships
  - **Files**: `config/learning_system.yaml`
  - **Dependencies**: None (parallel with Task 7.1)
  - **Success**: Configuration loaded correctly
  - **Time**: 10 minutes

### Task 13: Multi-Objective Validation Logic
- [ ] 13.1 Add `_validate_multi_objective()` to `autonomous_loop.py`
  - Check Sharpe ratio (via hybrid threshold)
  - Check Calmar ratio: `new_calmar >= old_calmar * calmar_retention_ratio`
  - Check Max drawdown: `new_drawdown <= old_drawdown * max_drawdown_tolerance`
  - Return validation result + failed criteria
  - Log which criteria passed/failed
  - **Files**: `artifacts/working/modules/autonomous_loop.py`
  - **Dependencies**: Task 11.1, Task 12.1
  - **Success**: Validation rejects brittle strategies
  - **Time**: 35 minutes

### Task 14: Integrate Multi-Objective into Champion Update
- [ ] 14.1 Update `_update_champion()` to call multi-objective validation
  - After hybrid threshold passes, check multi-objective
  - Reject if multi-objective fails
  - Log rejection reason (Sharpe passed but Calmar/Drawdown failed)
  - Track multi-objective rejection rate
  - **Files**: `artifacts/working/modules/autonomous_loop.py`
  - **Dependencies**: Task 13.1
  - **Success**: Brittle strategies rejected with clear logs
  - **Time**: 20 minutes

### Task 15: Multi-Objective Unit Tests
- [ ] 15.1 Create test suite `tests/test_multi_objective.py`
  - Test all criteria pass (accept champion)
  - Test Sharpe passes, Calmar fails (reject)
  - Test Sharpe passes, drawdown fails (reject)
  - Test Calmar and drawdown pass, Sharpe fails (reject)
  - Test edge cases (NaN, zero values)
  - **Files**: New file `tests/test_multi_objective.py`
  - **Dependencies**: Task 14.1
  - **Success**: All tests passing
  - **Time**: 30 minutes

---

## Integration and Validation

_Requirements: Story 10.4, Story 10.5_
_Goal: Verify complete system works end-to-end_

### Task 16: Integration Test Suite
- [ ] 16.1 Create `tests/test_phase3_integration.py`
  - Test complete champion update flow with all Phase 3 features
  - Test hybrid threshold + multi-objective + staleness together
  - Test configuration loading for all Phase 3 parameters
  - Test logging and tracking for all Phase 3 metrics
  - Simulate 20-iteration scenario with known outcomes
  - **Files**: New file `tests/test_phase3_integration.py`
  - **Dependencies**: Tasks 6.1, 10.1, 15.1
  - **Success**: All integration tests passing
  - **Time**: 45 minutes

### Task 17: Historical Replay Validation
- [ ] 17.1 Run complete historical replay with Phase 3 enabled
  - Use `scripts/validate_hybrid_threshold.py` (enhanced)
  - Replay all 313 iterations with Phase 3 logic
  - Calculate champion update frequency
  - Identify which strategies would be accepted/rejected
  - Generate detailed comparison report
  - **Target**: Champion update frequency 10-20%
  - **Target**: At least 2 of 4 rejected strategies now accepted
  - **Files**: Enhanced `scripts/validate_hybrid_threshold.py`
  - **Dependencies**: Task 16.1
  - **Success**: Update frequency in target range
  - **Time**: 30 minutes

### Task 18: 100-Iteration Validation Test
- [ ] 18.1 Run production readiness test with Phase 3 enabled
  - Execute `run_100iteration_test.py` with new configuration
  - Monitor champion update frequency in real-time
  - Calculate Cohen's d, p-value, rolling variance
  - Generate production readiness report
  - **Target**: Cohen's d ≥ 0.4
  - **Target**: P-value < 0.05
  - **Target**: Rolling variance < 0.5
  - **Target**: Champion update frequency 10-20%
  - **Files**: `run_100iteration_test.py`, `100_ITERATION_TEST_STATUS.md`
  - **Dependencies**: Task 17.1
  - **Success**: All 4 metrics pass (vs 0/4 before)
  - **Time**: 2-3 hours runtime + 30 min analysis

---

## Documentation and Finalization

### Task 19: Update Design Documentation
- [ ] 19.1 Document Phase 3 design in `design.md`
  - Add hybrid threshold algorithm pseudocode
  - Add staleness mechanism flow diagram
  - Add multi-objective validation decision tree
  - Document configuration parameters
  - Add example scenarios and outcomes
  - **Files**: `.spec-workflow/specs/learning-system-stability-fixes/design.md`
  - **Dependencies**: All implementation tasks
  - **Success**: Design doc comprehensive and clear
  - **Time**: 45 minutes

### Task 20: Update Status Report
- [ ] 20.1 Update `STATUS.md` with Phase 3 completion
  - Mark Phase 3 complete
  - Update overall completion percentage
  - Add Phase 3 validation results
  - Document production readiness status
  - Update next steps
  - **Files**: `.spec-workflow/specs/learning-system-stability-fixes/STATUS.md`
  - **Dependencies**: Task 18.1
  - **Success**: Status accurately reflects completion
  - **Time**: 20 minutes

---

## Task Summary

**Total Tasks**: 20
**Estimated Time**: 10-12 hours
**Critical Path**: Tasks 1→2→3→5→17→18 (Hybrid Threshold + Validation)

### Completion Checklist

**Priority 1 (CRITICAL)**: Tasks 1-6 ✅ Must complete first
- [ ] Hybrid threshold implemented and tested
- [ ] Historical backtest shows 10-20% update frequency
- [ ] At least 2/4 rejected strategies now accepted

**Priority 2 (HIGH)**: Tasks 7-10 ✅ Prevents future stagnation
- [ ] Staleness mechanism implemented and tested
- [ ] Automatic demotion functional

**Priority 3 (MEDIUM)**: Tasks 11-15 ✅ Improves robustness
- [ ] Multi-objective validation implemented and tested
- [ ] Brittle strategies rejected

**Integration**: Tasks 16-18 ✅ Validates complete system
- [ ] Integration tests passing
- [ ] Historical replay successful
- [ ] 100-iteration test passes all metrics

**Documentation**: Tasks 19-20 ✅ Finalize deliverables
- [ ] Design documented
- [ ] Status updated

---

**Phase 3 Status**: 🔄 IN PROGRESS (0/20 tasks complete)
**Next Action**: Begin Task 1.1 (Update Configuration Schema)
**Expected Completion**: 2025-10-14 to 2025-10-16
