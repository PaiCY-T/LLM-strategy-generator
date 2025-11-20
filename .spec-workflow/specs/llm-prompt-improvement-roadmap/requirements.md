# LLM Prompt Engineering Improvement Roadmap - Requirements Document

Systematic improvement of LLM prompt engineering to increase strategy generation success rate from 20% to 85% through 4-phase TDD implementation. Addresses field name validation, code structure enforcement, API documentation enhancement, and metric validation.

## Problem Statement

**Current State (2025-11-20)**:
- **LLM Only Mode**: 20% success rate (4/20 iterations) - far below 80% target
- **Hybrid Mode**: 70% success rate (14/20 iterations) - meets target
- **Factor Graph Only**: 90% success rate (18/20 iterations) - baseline

**Root Cause Analysis (16 LLM failures)**:
1. **Field Name Hallucination** (50%, 8 failures): LLM generates invalid FinLab field names not in API
2. **Code Structure Errors** (18.8%, 3 failures): Missing `report` variable assignment
3. **Invalid Metrics** (18.8%, 3 failures): NaN/Inf Sharpe ratios from flawed portfolio logic
4. **API Misuse** (6.2%, 1 failure): Incorrect usage of `data.stocks` (doesn't exist)
5. **Data Alignment** (6.2%, 1 failure): Operand alignment issues

**Gap**: 60 percentage points improvement needed (20% → 80% minimum target, ideally 85%+)

## Core Features

### Feature 1: Field Name Validation System
**Objective**: Eliminate field name hallucination errors (50% of current failures)

**Components**:
- Complete FinLab field catalog integrated into prompt
- Pre-generation field validation
- Post-generation field extraction and verification
- Explicit invalid field warnings in few-shot examples

**Target Impact**: 20% → 50% success rate (+30pp)

### Feature 2: Code Structure Enforcement
**Objective**: Ensure all generated code follows required structure patterns

**Components**:
- Mandatory `report = sim(...)` pattern enforcement
- Code structure templates in prompt
- AST-based validation of generated code
- Structure compliance checks before execution

**Target Impact**: 50% → 65% success rate (+15pp)

### Feature 3: API Documentation Enhancement
**Objective**: Prevent API misuse and incorrect data access patterns

**Components**:
- Comprehensive FinLab data object documentation
- Correct API usage examples
- Common anti-patterns and corrections
- Data access constraints and best practices

**Target Impact**: 65% → 75% success rate (+10pp)

### Feature 4: Metric Validation & Edge Cases
**Objective**: Ensure strategies produce valid performance metrics

**Components**:
- Metric validation guidelines in prompt
- Edge case handling examples (empty portfolios, zero positions)
- Sharpe ratio validity checks
- Portfolio construction best practices

**Target Impact**: 75% → 85% success rate (+10pp)

## User Stories

### As a Strategy Learning System Developer
- I want LLM-generated strategies to use only valid FinLab field names, so that field name errors are eliminated
- I want all generated code to follow required structure patterns, so that execution succeeds
- I want comprehensive API documentation in prompts, so that LLM understands correct usage
- I want metric validation guidance, so that strategies produce valid performance metrics

### As a Trading System Operator
- I want LLM mode to achieve ≥80% success rate, so that it's viable for production use
- I want Hybrid mode to maintain ≥70% success rate, so that blended strategies are reliable
- I want clear error messages when generation fails, so that I can diagnose issues

### As a System Maintainer
- I want TDD-based implementation, so that each improvement is validated before integration
- I want regression test suite, so that new changes don't break existing functionality
- I want phased rollout, so that improvements can be rolled back if needed

## Acceptance Criteria

### Phase 1: Field Name Validation (Target: 20% → 50%)
- [x] Complete FinLab field catalog created and documented
- [ ] Field catalog integrated into prompt_builder.py prompts
- [ ] Field validation helper function implemented
- [ ] 20-iteration validation test shows ≥35% success rate (minimum)
- [ ] 50-iteration validation test shows ≥50% success rate (target)
- [ ] Field name errors reduced from 50% to <15% of failures

### Phase 2: Code Structure Enforcement (Target: 50% → 65%)
- [ ] Code structure requirements added to prompt template
- [ ] Mandatory `report = sim(...)` pattern documented
- [ ] Structure validation examples in few-shot demonstrations
- [ ] 20-iteration test shows ≥55% success rate (minimum)
- [ ] 50-iteration test shows ≥65% success rate (target)
- [ ] Code structure errors reduced from 18.8% to <5% of failures

### Phase 3: API Documentation Enhancement (Target: 65% → 75%)
- [ ] FinLab data object structure documented in prompt
- [ ] Correct API usage examples added (≥5 examples)
- [ ] Common anti-patterns documented with corrections
- [ ] 20-iteration test shows ≥65% success rate (minimum)
- [ ] 50-iteration test shows ≥75% success rate (target)
- [ ] API misuse errors reduced from 6.2% to <2% of failures

### Phase 4: Metric Validation & Edge Cases (Target: 75% → 85%)
- [ ] Metric validation guidelines added to prompt
- [ ] Edge case handling examples (empty portfolios, zero positions)
- [ ] Portfolio construction best practices documented
- [ ] 20-iteration test shows ≥75% success rate (minimum)
- [ ] 50-iteration test shows ≥85% success rate (target)
- [ ] Invalid metric errors reduced from 18.8% to <5% of failures

### Overall Success Criteria
- [ ] LLM Only mode achieves ≥80% success rate (20-iteration test)
- [ ] LLM Only mode achieves ≥85% success rate (50-iteration test)
- [ ] Hybrid mode maintains ≥70% success rate (regression)
- [ ] Factor Graph mode maintains ≥90% success rate (regression)
- [ ] All changes validated with RED-GREEN-REFACTOR-VALIDATE TDD cycle
- [ ] Comprehensive test suite covers all 4 phases
- [ ] Documentation updated with new prompt patterns

## Non-functional Requirements

### Performance Requirements
- **NFR-P1**: Prompt generation latency increase <10ms per phase
- **NFR-P2**: Total prompt token count <100,000 (within Gemini 2.5 Flash limit)
- **NFR-P3**: Strategy generation time <15 seconds per iteration (unchanged)
- **NFR-P4**: Backtest execution time <5 seconds per strategy (unchanged)

### Quality Requirements
- **NFR-Q1**: Test coverage ≥90% for all new validation code
- **NFR-Q2**: All TDD cycles must pass RED → GREEN → REFACTOR → VALIDATE
- **NFR-Q3**: Zero regressions in Factor Graph and Hybrid modes
- **NFR-Q4**: Code quality maintained (no increase in complexity metrics)

### Maintainability Requirements
- **NFR-M1**: Field catalog must be updateable via configuration (not hardcoded)
- **NFR-M2**: Validation logic must be modular and independently testable
- **NFR-M3**: Each phase must be independently deployable with feature flags
- **NFR-M4**: Rollback capability for each phase within 5 minutes

### Documentation Requirements
- **NFR-D1**: Each phase documented with validation test results
- **NFR-D2**: Prompt engineering patterns documented for future reference
- **NFR-D3**: API usage guidelines updated and version-controlled
- **NFR-D4**: TDD test code serves as executable documentation

### Security Requirements
- **NFR-S1**: No sensitive data (API keys, credentials) in prompts
- **NFR-S2**: Generated code must not execute arbitrary system commands
- **NFR-S3**: Field validation must prevent injection attacks via field names

### Compatibility Requirements
- **NFR-C1**: Compatible with Gemini 2.5 Flash (1M token limit)
- **NFR-C2**: Backward compatible with existing prompt_builder.py interface
- **NFR-C3**: Compatible with FinLab API v1.x (current version)
- **NFR-C4**: Python 3.11+ compatibility maintained

## Success Metrics

### Primary Metrics
- **LLM Success Rate**: 20% → 85% (+65pp improvement)
- **Field Name Errors**: 50% → <15% of failures (-35pp)
- **Code Structure Errors**: 18.8% → <5% of failures (-13.8pp)
- **Invalid Metric Errors**: 18.8% → <5% of failures (-13.8pp)
- **API Misuse Errors**: 6.2% → <2% of failures (-4.2pp)

### Secondary Metrics
- **Hybrid Mode Success Rate**: Maintain ≥70%
- **Factor Graph Success Rate**: Maintain ≥90%
- **Average Sharpe Ratio**: Maintain or improve current 0.367 (LLM mode)
- **Test Suite Coverage**: ≥90%
- **Implementation Timeline**: 2-3 days (per TDD plan)

### Validation Metrics
- **Phase 1 Validation**: ≥50% success rate (20-iteration test)
- **Phase 2 Validation**: ≥65% success rate (20-iteration test)
- **Phase 3 Validation**: ≥75% success rate (20-iteration test)
- **Phase 4 Validation**: ≥85% success rate (20-iteration test)

## Dependencies

### Technical Dependencies
- Gemini 2.5 Flash API (Google AI)
- FinLab API v1.x (Taiwan stock data)
- pytest testing framework
- Python 3.11+ runtime
- Existing prompt_builder.py module

### Data Dependencies
- Complete FinLab field catalog (price, fundamental_features, etc.)
- Historical test results (POST_FIX_VALIDATION_SUMMARY.md)
- Existing few-shot examples in prompt_builder.py
- Strategy backtest validation framework

### Process Dependencies
- TDD methodology (RED-GREEN-REFACTOR-VALIDATE cycle)
- 20-iteration validation tests (post-phase)
- 50-iteration validation tests (final validation)
- Feature flag system for phased rollout

## Constraints

### Technical Constraints
- Prompt size limited to 100,000 tokens (Gemini 2.5 Flash safe limit)
- Field catalog must match FinLab API exactly (no hallucinations)
- Generated code must execute in sandbox environment (<30s timeout)
- Validation must complete within iteration time budget (<20s per strategy)

### Business Constraints
- Must not degrade Factor Graph or Hybrid mode performance (no regressions)
- Implementation timeline: 2-3 days (avoid over-engineering)
- Must be compatible with existing learning loop infrastructure
- Changes must be reversible via feature flags

### Resource Constraints
- Development team: 1 developer
- Testing environment: Local WSL2 + Python 3.11
- API rate limits: Gemini 2.5 Flash (60 requests/minute)
- Compute resources: 8GB RAM, 4 CPU cores

## Out of Scope

The following are explicitly **not included** in this implementation:

1. **LLM Model Changes**: No fine-tuning or model replacement (use Gemini 2.5 Flash as-is)
2. **Backtest Framework Changes**: No modifications to sim() or backtest execution
3. **Factor Graph Redesign**: Factor graph logic remains unchanged
4. **UI/Dashboard**: No user interface changes
5. **Real-time Monitoring**: No production monitoring system (dev/test only)
6. **Multi-LLM Support**: Only Gemini 2.5 Flash support (no OpenAI, Claude, etc.)
7. **Automated Prompt Optimization**: Manual prompt engineering only (no meta-learning)
8. **Data Pipeline Changes**: FinLab data cache and retrieval unchanged

## References

### Related Documents
- `TDD_LLM_IMPROVEMENT_PLAN.md`: Complete 4-phase TDD implementation plan
- `POST_FIX_VALIDATION_SUMMARY.md`: Post-fix validation test results (2025-11-20)
- `src/innovation/prompt_builder.py`: Current prompt engineering implementation
- `experiments/llm_learning_validation/results/llm_only_20/innovations.jsonl`: Detailed failure logs

### Test Results
- Test Date: 2025-11-20
- Total Iterations: 60 (20 per mode)
- Duration: 888 seconds (14.8 minutes)
- Results File: `experiments/llm_learning_validation/results/20iteration_three_mode/results_20251120_134133.json`

### Key Findings
- Field name errors: 8/16 failures (50%)
- Code structure errors: 3/16 failures (18.8%)
- Invalid metrics: 3/16 failures (18.8%)
- API misuse: 1/16 failures (6.2%)
- Data alignment: 1/16 failures (6.2%)
