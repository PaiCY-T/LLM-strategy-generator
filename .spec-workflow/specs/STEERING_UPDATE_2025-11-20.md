# Steering Update - 2025-11-20

**Update Type**: LLM Prompt Engineering Improvement Initiative
**Date**: 2025-11-20
**Status**: ⚠️ PLANNING - New improvement roadmap created based on validation results

---

## Executive Summary

**Post-Fix Validation Test Completed** (60 iterations, 14.8 minutes):
- ✅ **Hybrid Mode**: 70% success (14/20) - **TARGET MET** (exactly on 70% target!)
- ⚠️ **LLM Only Mode**: 20% success (4/20) - **TARGET NOT MET** (80% target, 60pp gap)
- ✅ **Factor Graph Only**: 90% success (18/20) - **BASELINE MAINTAINED**

**Key Achievement**: Field name and token limit fixes successfully improved:
- Hybrid: 44% → 70% (+26pp improvement)
- LLM Only: 0% → 20% (+20pp improvement)

**Critical Finding**: LLM Only mode requires additional systematic improvements beyond field name fixes to reach 80%+ target.

---

## Validation Test Results

### Test Configuration
- **Test Date**: 2025-11-20 13:41:33
- **Total Duration**: 888 seconds (14.8 minutes)
- **Total Iterations**: 60 (20 per mode)
- **Test Script**: `run_20iteration_three_mode_test.py`
- **Results File**: `experiments/llm_learning_validation/results/20iteration_three_mode/results_20251120_134133.json`

### Performance Metrics by Mode

| Mode | Success Rate | Classification | Avg Sharpe | Best Sharpe | Duration |
|------|--------------|----------------|------------|-------------|----------|
| **Factor Graph Only** | 90.0% (18/20) | L0:2, L3:18 | 0.3012 | 0.3012 | 360.5s |
| **LLM Only** | 20.0% (4/20) | L0:16, L3:4 | 0.3669 | 0.7060 | 254.5s |
| **Hybrid** | 70.0% (14/20) | L0:5, L2:1, L3:14 | 0.3022 | 0.5476 | 272.7s |

### Target Evaluation

✅ **Hybrid Mode - TARGET MET**:
- Expected: 70%+ success rate
- Actual: 70.0% (exactly on target!)
- Improvement: From 44% baseline → 70% (+26pp)
- Conclusion: Field name fix successfully improved Hybrid mode

❌ **LLM Only Mode - TARGET NOT MET**:
- Expected: 80%+ success rate
- Actual: 20.0% (only 1/4 of target)
- Improvement: From 0% baseline → 20% (+20pp)
- Gap: 60 percentage points remaining (20% → 80%)
- Conclusion: Field name fix helped but insufficient

---

## Root Cause Analysis - LLM Only Failures (16/20)

### Error Pattern Distribution

| Error Pattern | Count | Percentage | Root Cause Category |
|---------------|-------|------------|---------------------|
| **Field not exists** | 8 | 50.0% | LLM hallucinates invalid field names |
| **Missing report variable** | 3 | 18.8% | Code structure violations |
| **Invalid Sharpe ratio** | 3 | 18.8% | Metric validation failures |
| **data.stocks AttributeError** | 1 | 6.2% | API misunderstanding |
| **Operands not aligned** | 1 | 6.2% | Data alignment issues |

### Detailed Root Cause Analysis

#### 1. Field Name Hallucination (50% of failures)
**Examples**: `close not exists`, `pb_ratio not exists`

**Analysis**: LLM continues to invent field names not present in FinLab API despite fixes to few-shot examples. The original fix only addressed specific `price:成交量` errors but didn't prevent new hallucinations.

**Impact**: 8/16 failures

#### 2. Code Structure Errors (18.8% of failures)
**Error**: `Strategy code did not create 'report' variable`

**Analysis**: Generated code fails to assign sim() result to required 'report' variable.

**Impact**: 3/16 failures

#### 3. Invalid Metrics (18.8% of failures)
**Error**: `Metric validation failed: sharpe_ratio must be a valid number`

**Analysis**: Strategies produce NaN/Inf Sharpe ratios from flawed portfolio logic.

**Impact**: 3/16 failures

#### 4. API Misuse (6.2% of failures)
**Error**: `module 'finlab.data' has no attribute 'stocks'`

**Example**:
```python
# Incorrect LLM-generated code
pb_filter = (pb_rank < len(data.stocks) * 0.3)
```

**Impact**: 1/16 failures

---

## Applied Fixes (from Previous Session)

### Fix 1: Field Name Corrections
**File**: `src/innovation/prompt_builder.py`
**Lines**: 380, 431, 463

**Changes**: `price:成交量` → `price:成交股數`

**Impact**: Fixed specific field name errors in few-shot examples

### Fix 2: Token Limit Expansion
**File**: `src/innovation/prompt_builder.py`
**Lines**: 21-23

**Changes**: MAX_PROMPT_TOKENS: 2,000 → 100,000

**Justification**: Gemini 2.5 Flash supports 1,048,576 tokens (official limit)

**Impact**: Allows full CSV schema usage in prompts

---

## New Improvement Roadmap - 4-Phase TDD Plan

### Spec Location
**Directory**: `.spec-workflow/specs/llm-prompt-improvement-roadmap/`
**Documents**:
- `requirements.md`: Comprehensive requirements specification
- `TDD_LLM_IMPROVEMENT_PLAN.md`: Complete 4-phase TDD implementation plan
- `POST_FIX_VALIDATION_SUMMARY.md`: Full validation test results and analysis

### Phase Overview

#### Phase 1: Field Name Validation System
**Target**: 20% → 50% success rate (+30pp)
**Timeline**: 0.5 days
**Components**:
- Complete FinLab field catalog creation
- Field catalog integration into prompts
- Field validation helper functions
- Explicit invalid field warnings

**TDD Cycles**: 3 cycles (catalog creation, integration, validation helper)

#### Phase 2: Code Structure Enforcement
**Target**: 50% → 65% success rate (+15pp)
**Timeline**: 0.5 days
**Components**:
- Mandatory `report = sim(...)` pattern enforcement
- Code structure templates in prompts
- AST-based validation
- Structure compliance checks

**TDD Cycles**: 3 cycles (requirements, examples, validation)

#### Phase 3: API Documentation Enhancement
**Target**: 65% → 75% success rate (+10pp)
**Timeline**: 0.5 days
**Components**:
- Comprehensive FinLab data object documentation
- Correct API usage examples
- Common anti-patterns documentation
- Data access constraints

**TDD Cycles**: 3 cycles (data object docs, usage examples, anti-patterns)

#### Phase 4: Metric Validation & Edge Cases
**Target**: 75% → 85% success rate (+10pp)
**Timeline**: 0.5 days
**Components**:
- Metric validation guidelines
- Edge case handling examples
- Portfolio construction best practices
- Sharpe ratio validity checks

**TDD Cycles**: 3 cycles (validation guidelines, edge cases, best practices)

### Total Implementation Timeline
**Estimated Duration**: 2-3 days
**Validation Strategy**: 20-iteration tests after each phase, 50-iteration final validation

---

## Success Metrics

### Primary Targets
- **LLM Only Success Rate**: 20% → 85% (+65pp)
- **Hybrid Mode Success Rate**: Maintain ≥70% (no regression)
- **Factor Graph Success Rate**: Maintain ≥90% (no regression)

### Error Reduction Targets
- **Field Name Errors**: 50% → <15% of failures
- **Code Structure Errors**: 18.8% → <5% of failures
- **Invalid Metric Errors**: 18.8% → <5% of failures
- **API Misuse Errors**: 6.2% → <2% of failures

### Quality Targets
- **Test Coverage**: ≥90% for all validation code
- **TDD Compliance**: All changes follow RED-GREEN-REFACTOR-VALIDATE cycle
- **Zero Regressions**: Factor Graph and Hybrid modes maintain performance

---

## Action Items

### Immediate Next Steps
1. **Review Requirements** (`.spec-workflow/specs/llm-prompt-improvement-roadmap/requirements.md`)
2. **Approve TDD Plan** (`.spec-workflow/specs/llm-prompt-improvement-roadmap/TDD_LLM_IMPROVEMENT_PLAN.md`)
3. **Schedule Phase 1 Implementation** (Field Name Validation System)

### Phase 1 Prerequisites
- [x] Complete FinLab field catalog documented
- [x] Current prompt_builder.py code analyzed
- [x] Test framework validated (run_20iteration_three_mode_test.py)
- [x] Validation test baselines established (POST_FIX_VALIDATION_SUMMARY.md)

### Implementation Approach
- **Methodology**: TDD (Test-Driven Development)
- **Validation**: 20-iteration tests after each phase
- **Rollback**: Feature flags for each phase (independent deployment)
- **Timeline**: 2-3 days total (0.5 days per phase)

---

## Risk Assessment

### Technical Risks
- **Medium**: Prompt token budget may require optimization across phases
- **Low**: Validation tests may need adjustment for new prompts
- **Low**: FinLab API field catalog may be incomplete

### Mitigation Strategies
- **Token Budget**: Monitor prompt size after each phase (<100K tokens)
- **Test Adjustment**: Update validation thresholds based on empirical results
- **Field Catalog**: Verify against FinLab API documentation before Phase 1

### Rollback Plan
- Each phase independently deployable via feature flags
- Can revert to previous phase within 5 minutes
- All changes version-controlled with clear commit messages

---

## Dependencies

### Technical Dependencies
- Gemini 2.5 Flash API (Google AI) - ✅ Available
- FinLab API v1.x (Taiwan stock data) - ✅ Available
- pytest testing framework - ✅ Installed
- Python 3.11+ runtime - ✅ Installed

### Process Dependencies
- TDD methodology approval - ⏳ Pending
- 20-iteration test validation framework - ✅ Validated
- Feature flag system design - ⏳ Pending (Phase 1)
- FinLab field catalog completion - ⏳ Pending (Phase 1)

---

## Related Documents

### Spec Documents
- `.spec-workflow/specs/llm-prompt-improvement-roadmap/requirements.md`
- `.spec-workflow/specs/llm-prompt-improvement-roadmap/TDD_LLM_IMPROVEMENT_PLAN.md`
- `.spec-workflow/specs/llm-prompt-improvement-roadmap/POST_FIX_VALIDATION_SUMMARY.md`

### Implementation Files
- `src/innovation/prompt_builder.py` (to be modified)
- `experiments/llm_learning_validation/config_llm_only_20.yaml` (test config)
- `run_20iteration_three_mode_test.py` (validation framework)

### Test Results
- `experiments/llm_learning_validation/results/20iteration_three_mode/results_20251120_134133.json`
- `experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl`
- `experiments/llm_learning_validation/results/hybrid_20/innovations.jsonl`
- `experiments/llm_learning_validation/results/fg_only_20/innovations.jsonl`

---

## Conclusion

**Partial Success**: Field name and token limit fixes achieved significant improvements in Hybrid mode (44% → 70%, meeting target) and showed LLM Only is viable (0% → 20%), but additional systematic improvements are required.

**Root Cause**: Original fix addressed only specific field name errors. LLM continues to make various errors including field hallucination, code structure violations, API misunderstanding, and invalid metric generation.

**Recommendation**: Proceed with 4-phase TDD improvement plan to close the remaining 60pp gap (20% → 80%+) in LLM Only success rate through systematic prompt engineering enhancements.

**Next Action**: Review and approve requirements and TDD plan, then begin Phase 1 implementation (Field Name Validation System).
