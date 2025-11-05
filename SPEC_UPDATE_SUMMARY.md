# Spec Update Summary - Scenario B (Structural Mutation Phase 2)

**Date**: 2025-10-20
**Trigger**: Phase 1.5 validation complete, Sharpe 1.378 < 2.5 threshold
**Decision**: ✅ Proceed to Scenario B with phased validation approach

---

## Phase 1.5 Final Results (Validated)

**Test Configuration**:
- Population: 20 strategies (CombinationTemplate)
- Generations: 20
- Process ID: fadd75

**Key Metrics**:
| Metric | Result | Status |
|--------|--------|--------|
| Best Sharpe | **1.378** | ❌ Below 2.5 threshold |
| Initial Range | 1.068 - 1.378 | Realistic (monthly data) |
| Diversity | 0.000 | ⚠️ Collapsed (all converged) |
| Generations without improvement | 20 | ⚠️ Optimization exhausted |

**Critical Observations**:
1. ✅ Corrected Sharpe confirmed (~1.37 as expected)
2. ❌ Parameter optimization reached ceiling
3. ⚠️ Diversity collapse indicates structural limitation
4. ✅ Decision gate verdict: Proceed to Scenario B

---

## Consensus Analysis Results

### Multi-Model Review (Gemini 2.5 Pro + Claude)

**Universal Agreement** ✅:
1. Exit strategies are THE critical missing component
2. User's architectural insight is valid (parameter optimization exhausted)
3. Exit Strategy Mutation Operator must be TOP priority
4. MVP approach preferred over full implementation
5. Phase 1.5 results justify Scenario B

**Key Recommendation**:
- **Phase 0 Validation FIRST** (1-2 weeks): Manual exit strategy test
- **Then Phase 1 MVP** (3-4 weeks): Exit mutation operator only
- **Then Phase 2** (6-8 weeks): Full structural mutation if MVP successful

**Timeline Update**:
- Original: 9-13 weeks (direct implementation)
- Updated: 12-17 weeks (with 3 decision gates)
- Risk reduction: Validate hypothesis before framework investment

---

## Spec Documents Updated

### ✅ requirements.md

**Changes Made**:
1. **Updated Phase 1.5 Results Section** (lines 18-35):
   - Added validated metrics (Sharpe 1.378, range 1.068-1.378)
   - Added diversity collapse observation (0.000)
   - Documented user insights (parameter optimization exhausted, exit strategies missing)

2. **Added REQ-6: Exit Strategy Mutation** (lines 146-201) ⭐ **HIGHEST PRIORITY**:
   - 5 exit mechanism categories:
     - Stop-Loss (fixed %, ATR-based, time-based)
     - Take-Profit (target, risk-reward, multiple targets)
     - Trailing Stops (%, ATR, MA-based)
     - Dynamic Exits (indicator-based, volatility-adjusted)
     - Risk Management (drawdown triggers, correlation-based)
   - Expected impact: Sharpe +0.3 to +0.8, Drawdown -15% to -40%
   - Phase 0 success criteria: ≥0.3 Sharpe improvement

3. **Updated Timeline Section** (lines 249-285):
   - Added Phase 0: Exit Strategy Hypothesis Validation (1-2 weeks)
   - Added Phase 1: Exit Strategy Mutation MVP (3-4 weeks)
   - Reorganized Phase 2.0-2.2 as CONDITIONAL on Phase 1 success
   - Total timeline: 12-17 weeks with 3 decision gates

**File**: `.spec-workflow/specs/structural-mutation-phase2/requirements.md`

### ⏳ tasks.md (IN PROGRESS)

**Planned Changes**:
1. Insert Phase 0 tasks (4 tasks, 1-2 weeks) at the beginning
2. Reorder mutation operators (Exit Strategy #1 priority)
3. Update task dependencies and timelines
4. Add decision gate checkpoints

**New Task Structure**:
```
Phase 0: Validation (Week 0) - 4 tasks
├─ Task 0.1: Manual exit strategy on Momentum template
├─ Task 0.2: Backtest comparison
├─ Task 0.3: Results analysis
└─ Task 0.4: Decision gate documentation

Phase 1: Exit MVP (Week 1-4) - 6 tasks (CONDITIONAL)
Phase 2.0: Full Implementation (Week 5-12) - 17 tasks (CONDITIONAL)
Phase 2.1: Validation (Week 13-14) - 7 tasks
Phase 2.2: Deployment (Week 15-17) - 3 tasks
```

### ⏳ design.md (PENDING)

**Planned Changes**:
1. Add ExitStrategyMutationOperator design
2. Update mutation operator priority order
3. Add Phase 0 validation design
4. Update architecture diagram

### ⏳ STATUS.md (PENDING)

**Planned Changes**:
1. Update decision gate status (Phase 1.5 → Scenario B confirmed)
2. Add Phase 0 milestone tracking
3. Update current objectives (start Phase 0 validation)
4. Remove blockers (Phase 1.5 complete)

---

## User Insights Incorporated

### Observation 1: Parameter Optimization Exhausted

**Evidence from Phase 1.5**:
- 20 generations without improvement
- Diversity collapse to 0.000
- All strategies converged to same turtle+mastiff combination

**System Response**:
- Added to requirements.md (User Insights section)
- Justifies structural mutation approach
- Confirms need to modify strategy structure, not just parameters

### Observation 2: Exit Strategies Missing

**Evidence from Templates**:
- `TurtleTemplate`: Only breakout entry, rebalancing exit
- `MomentumTemplate`: Only momentum entry, rebalancing exit
- `MastiffTemplate`: Only mean-reversion entry, rebalancing exit
- **NO sophisticated exits**: stop-loss, take-profit, trailing stops

**System Response**:
- Created REQ-6: Exit Strategy Mutation (HIGHEST PRIORITY)
- 5 exit mechanism categories designed
- Phase 0 validation to test hypothesis
- Expected 20-60% Sharpe improvement

**User Quote Integration**:
> "止損、止盈的策略也都該加入演算法的範籌，目前策略都是著重於進場的部份，如何出場其實並沒有很好的設計(如5ma均線、ATR追綜, etc.)"

Translated to REQ-6 acceptance criteria with specific mechanisms.

---

## Next Steps

### Immediate (This Session)
1. ✅ Update requirements.md with REQ-6 and Phase 0 timeline
2. ⏳ Update tasks.md with Phase 0 tasks and reordered priorities
3. ⏳ Update design.md with ExitStrategyMutationOperator
4. ⏳ Update STATUS.md with decision gate verdict

### Week 1 (Next Week)
1. Implement Phase 0 validation:
   - Create `momentum_exit_template.py` with manual exit strategies
   - Run backtest comparison (baseline vs. exits)
   - Analyze results and document in `EXIT_STRATEGY_VALIDATION.md`

2. Decision Gate 1:
   - **IF Sharpe improvement ≥0.3** → Proceed to Phase 1 MVP
   - **IF Sharpe improvement <0.3** → Re-evaluate approach

### Week 2-5 (If Phase 0 Succeeds)
1. Implement Phase 1 MVP (Exit Strategy Mutation Operator only)
2. Run 20-generation validation test
3. Decision Gate 2: Sharpe >2.0 → Proceed to full Phase 2

---

## Decision Gates Summary

| Gate | Metric | Threshold | Action if Pass | Action if Fail |
|------|--------|-----------|----------------|----------------|
| **Gate 0** | Phase 1.5 Sharpe | <2.5 | → Scenario B | → Scenario A |
| **Gate 1** | Exit hypothesis | +0.3 Sharpe | → Phase 1 MVP | → Alternative approach |
| **Gate 2** | Exit MVP | >2.0 Sharpe | → Full Phase 2 | → Optimize exits, retest |
| **Gate 3** | Full mutation | >2.5 Sharpe | → Production | → Phase 3 fallback |

**Current Status**: ✅ Gate 0 PASSED (Sharpe 1.378 < 2.5) → Scenario B confirmed

---

## Summary

**Phase 1.5 Validation**: ✅ Complete
- Sharpe: 1.378 (below 2.5 threshold)
- Decision: Proceed to Scenario B

**Consensus Analysis**: ✅ Complete
- Gemini 2.5 Pro: FOR structural mutation, prioritize exits
- Claude (critical review): Validate hypothesis first
- Recommendation: Phased approach with decision gates

**Requirements Update**: ✅ Complete
- REQ-6 added (Exit Strategy Mutation - TOP priority)
- Timeline updated (Phase 0 validation first)
- User insights incorporated

**Remaining Updates**: ⏳ In Progress
- tasks.md: Add Phase 0, reorder priorities
- design.md: Add ExitStrategyMutationOperator design
- STATUS.md: Update decision gate verdict

**Next Action**: Continue updating spec documents, then begin Phase 0 validation implementation.

---

**Last Updated**: 2025-10-20
**Generated by**: Claude Code SuperClaude
