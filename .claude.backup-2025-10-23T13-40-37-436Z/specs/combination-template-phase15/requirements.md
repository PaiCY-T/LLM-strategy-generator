# Requirements: CombinationTemplate Phase 1.5

**Spec ID**: combination-template-phase15
**Status**: Draft
**Created**: 2025-10-20
**Priority**: High (Decision Gate for Structural Mutation)

## Executive Summary

Phase 1.5 is a **quick validation experiment** (1-2 weeks) to test whether **template combination** can break the single-template performance ceiling before investing 6-8 weeks in structural mutation capabilities.

**Decision Gate**: If CombinationTemplate achieves Sharpe >2.5, structural mutation may not be needed.

---

## Background & Context

### Current State
- **Turtle Template**: Sharpe 1.5-2.5 (proven ceiling)
- **Momentum Template**: Sharpe 0.8-1.5 (lower but different characteristics)
- **Mastiff Template**: Sharpe varies
- **Population Evolution**: Works well, but limited to parameter search within single templates

### Problem Statement
**Unknown**: Can weighted combination of existing templates exceed single-template performance ceiling?

**Why Now**: Multi-model consensus (Opus + O3 + Gemini) unanimously recommends validating simple solution before complex structural mutation implementation.

### Success Criteria
- **Primary**: Achieve Sharpe >2.5 in 20-generation validation test
- **Secondary**: Generate stable, non-degenerate strategies
- **Tertiary**: Reuse ≥95% of existing infrastructure

---

## Functional Requirements

### R1: Template Combination Strategy
**Priority**: P0 (Core)
**Description**: Implement weighted combination of existing strategy templates

**Acceptance Criteria**:
- [x] Support 2-3 template combinations
- [x] Weighted allocation (e.g., 0.5/0.5, 0.7/0.3, 0.4/0.4/0.2)
- [x] Independent parameter mutation per template
- [x] Rebalancing frequency control (Monthly/Weekly)

**Constraints**:
- Must use existing StrategyTemplate interface
- Zero changes to population_manager.py
- Zero changes to mutation.py

### R2: Template Registry Integration
**Priority**: P0 (Core)
**Description**: Register CombinationTemplate for automatic discovery

**Acceptance Criteria**:
- [x] Auto-discovery via template_registry.py
- [x] Seamless integration with existing template selection
- [x] Backward compatibility with single templates

### R3: Parameter Search Space
**Priority**: P1 (High)
**Description**: Define mutation-friendly parameter grid

**Acceptance Criteria**:
- [x] Template selection combinations
- [x] Weight distributions
- [x] Rebalancing frequencies
- [x] Total search space >50 configurations

### R4: Testing Infrastructure
**Priority**: P0 (Core)
**Description**: Comprehensive unit and integration tests

**Acceptance Criteria**:
- [x] Unit tests: Parameter validation, position sizing, rebalancing
- [x] Integration test: 10-generation smoke test
- [x] Validation test: 20-generation performance test
- [x] Test coverage ≥80% for new code

---

## Non-Functional Requirements

### NF1: Performance
- Strategy generation: <5s per strategy
- Backtest execution: Comparable to single templates
- No memory leaks in multi-generation runs

### NF2: Code Quality
- Follow existing project conventions
- Type hints for all public methods
- Docstrings for all classes/methods
- Linting: flake8, mypy clean

### NF3: Maintainability
- File size: <300 lines
- Single Responsibility Principle
- Zero technical debt introduction

### NF4: Risk Management
- No modifications to existing templates
- Rollback plan: Simply remove from registry
- Fail-safe: Invalid combinations raise clear errors

---

## Out of Scope

### Explicitly NOT Included
- ❌ Multi-strategy portfolio optimization (future Phase 2)
- ❌ Dynamic weight adjustment during backtest
- ❌ Template-specific logic fusion (e.g., merging factor conditions)
- ❌ New factor creation or structural mutation
- ❌ UI/visualization for combination analysis

---

## Dependencies

### Technical Dependencies
- **Existing**: src/templates/*.py (turtle, momentum, mastiff, factor)
- **Existing**: src/utils/template_registry.py
- **Existing**: tests/templates/test_*.py (test patterns)

### Data Dependencies
- FinLab API (existing data pipeline)
- Historical price/fundamental data (2019-2024)

### Team Dependencies
- None (single developer, 1-2 week timeline)

---

## Acceptance Criteria (Overall)

### Must Have (Phase 1.5 Complete)
- [x] CombinationTemplate implemented and tested
- [x] Unit tests passing (≥80% coverage)
- [x] 10-generation smoke test successful
- [x] 20-generation validation test completed
- [x] Results compared against Turtle baseline (Sharpe 1.5-2.5)

### Decision Gate Outcomes
**Scenario A**: Sharpe >2.5 achieved
→ **Action**: Optimize combinations, end Phase 1.5, no structural mutation needed

**Scenario B**: Sharpe ≤2.5
→ **Action**: Analyze failure modes, proceed to structural mutation design

**Scenario C**: Unstable results (high variance)
→ **Action**: Extend to 50-generation test, gather more data

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Combination produces degenerate strategies | Medium | High | Add validation checks, min diversity constraints |
| Performance not better than best single template | High | Medium | Expected outcome, validates need for structural mutation |
| Integration breaks existing tests | Low | High | Comprehensive regression testing before merge |
| Implementation takes >2 weeks | Low | Low | Scope is minimal, 150-200 lines of code |

---

## Timeline

**Week 1**:
- Days 1-2: Implement CombinationTemplate + unit tests
- Days 3-4: Integration testing + smoke test
- Day 5: Documentation + code review

**Week 2**:
- Days 1-3: 20-generation validation test
- Day 4: Results analysis + decision gate
- Day 5: Documentation + handoff

---

## Appendix: Multi-Model Consensus Summary

**Opus** (Deep Analysis): Suggested testing template combination first, questioned necessity of evolution
**OpenAI O3** (For Stance): Supported Hybrid approach but agreed baseline test needed
**Gemini 2.5 Pro** (Against Stance): Strong recommendation for CombinationTemplate as Phase 1.5

**Unanimous Agreement**: Test simple solution before 6-8 week complex implementation.
