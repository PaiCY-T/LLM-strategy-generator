# phase3-data-integrity-type-safety - Requirements Document

Phase 3 aims to improve data integrity and type safety in the LLM strategy generation system through three prioritized tasks: (1) Type Consistency [P0] - Fix Dict/StrategyMetrics mixing, add backward compatibility; (2) Schema Validation [P1] - Add Pydantic validation for ExecutionResult and StrategyMetrics; (3) LLM Code Pre-validation [P2, Optional] - AST-based code validation before execution (only if error rate >20%). Expected outcome: 50%+ reduction in data errors, full type safety, improved maintainability.

## Background & Context

### Current Problem
After Phase 1 fixes restored system execution to 100%, several underlying issues remain:
- **Bug #4 (Type Inconsistency)**: Mixed use of `Dict[str, float]` and `StrategyMetrics` dataclass causes type confusion
- **Data Validation Gap**: No runtime validation for anomalous values (e.g., Sharpe ratio = 100, positive drawdown)
- **LLM Code Quality**: Without pre-validation, malformed strategy code reaches execution stage

### Evidence from Phase 1
- 3/3 iterations executed successfully (100% execution rate)
- All metrics properly extracted
- Classification system functional
- But: Type safety issues remain, data validation missing

## Core Features

### Feature 1: Type Consistency Enhancement (P0 Priority)

**Description**: Eliminate `Dict[str, float]` and `StrategyMetrics` mixing by standardizing on `StrategyMetrics` dataclass with backward compatibility helpers.

**Components**:
1. Enhanced `StrategyMetrics` with `to_dict()` / `from_dict()` methods
2. Updated `FeedbackGenerator` to use `StrategyMetrics` exclusively
3. Updated `ChampionTracker` type annotations
4. Updated `IterationExecutor` metrics extraction

**Rationale**: Type safety prevents runtime errors, improves IDE support, and enables better mypy checking.

### Feature 2: Schema Validation Mechanism (P1 Priority)

**Description**: Add Pydantic-based runtime validation for `ExecutionResult` and `StrategyMetrics` to catch anomalous values early.

**Components**:
1. `ExecutionResultSchema` with field validators
   - Sharpe ratio range: [-10, 10]
   - Total return range: [-1, 10]
   - Max drawdown range: [-1, 0]
2. `StrategyMetricsSchema` with strict type checking
3. Integration into `BacktestExecutor.execute()`
4. Validation error handling and logging

**Rationale**: Catches data corruption early, prevents propagation of invalid values, self-documenting through schema constraints.

### Feature 3: LLM Code Pre-Validation (P2 Priority - Optional)

**Description**: AST-based code validation before execution to catch syntax errors, look-ahead bias, and API misuse.

**Conditional Implementation**: Only implement if Phase 1+2 show LLM error rate >20%

**Components**:
1. `StrategyCodeValidator` class with AST analysis
2. Syntax error detection
3. Look-ahead bias pattern detection (`.shift(-1)`)
4. Pandas API validation (`.rank()` without `axis`)
5. Integration into `StructuredInnovator`

**Rationale**: Proactive error prevention, better LLM feedback, reduced execution failures.

## User Stories

### Developer Stories

**DS-1: Type Safety for Development**
- As a **developer**, I want **mypy to catch type errors in the learning module**, so that **I can identify issues during development instead of runtime**.
- Acceptance: `mypy src/learning/` reports 0 errors

**DS-2: Backward Compatibility for Historical Data**
- As a **developer**, I want **existing JSONL history files to remain readable**, so that **I don't lose historical learning data**.
- Acceptance: All existing `*.jsonl` files load successfully with new code

**DS-3: Clear Validation Errors**
- As a **developer**, I want **validation errors to include clear messages**, so that **I can quickly identify and fix data issues**.
- Acceptance: ValidationError messages specify field name, value, and constraint

### System Stories

**SS-1: Data Integrity Protection**
- As the **LLM learning system**, I want **to reject anomalous metric values**, so that **corrupted data doesn't propagate through feedback loops**.
- Acceptance: Sharpe ratio >10 raises ValidationError before saving

**SS-2: Performance Preservation**
- As the **LLM learning system**, I want **validation overhead <1ms per iteration**, so that **learning loop performance remains acceptable**.
- Acceptance: Validation benchmark test passes (<1ms average)

**SS-3: Graceful Error Handling**
- As the **LLM learning system**, I want **validation errors to log clearly without crashing**, so that **the system can continue with valid iterations**.
- Acceptance: ValidationError logged, execution_result.success=False, iteration continues

### Optional: Code Quality Stories (Task 3.3)

**CQ-1: Early Syntax Detection**
- As the **LLM learning system**, I want **to detect syntax errors before execution**, so that **I can provide faster feedback to the LLM**.
- Acceptance: Syntax errors detected via AST, reported in <10ms

**CQ-2: Look-Ahead Bias Prevention**
- As the **LLM learning system**, I want **to detect future data usage patterns**, so that **strategies don't use invalid look-ahead bias**.
- Acceptance: `.shift(-1)` patterns detected and rejected

## Acceptance Criteria

### Task 3.1: Type Consistency (P0)

- [ ] **TC-1.1**: `StrategyMetrics` has `to_dict()` method converting to `Dict[str, float]`
- [ ] **TC-1.2**: `StrategyMetrics` has `from_dict()` classmethod creating instances from dict
- [ ] **TC-1.3**: `FeedbackGenerator.generate_feedback()` accepts `Optional[StrategyMetrics]`
- [ ] **TC-1.4**: `ChampionTracker.update_champion()` accepts `StrategyMetrics`
- [ ] **TC-1.5**: `IterationExecutor._extract_metrics()` returns `StrategyMetrics`
- [ ] **TC-1.6**: `mypy src/learning/` reports 0 type errors
- [ ] **TC-1.7**: All existing unit tests pass without modification
- [ ] **TC-1.8**: Historical JSONL files load successfully
- [ ] **TC-1.9**: Type conversion overhead <0.1ms (benchmarked)
- [ ] **TC-1.10**: 15+ type-related unit tests pass

### Task 3.2: Schema Validation (P1)

- [ ] **SV-2.1**: `ExecutionResultSchema` validates sharpe_ratio range [-10, 10]
- [ ] **SV-2.2**: `ExecutionResultSchema` validates max_drawdown <= 0
- [ ] **SV-2.3**: `ExecutionResultSchema` validates total_return range [-1, 10]
- [ ] **SV-2.4**: `BacktestExecutor.execute()` validates before creating ExecutionResult
- [ ] **SV-2.5**: Validation errors logged with field, value, constraint
- [ ] **SV-2.6**: Invalid data returns ExecutionResult(success=False, error_message=...)
- [ ] **SV-2.7**: Validation overhead <1ms per call (benchmarked)
- [ ] **SV-2.8**: 15+ schema validation tests pass
- [ ] **SV-2.9**: Integration test with schema validation passes
- [ ] **SV-2.10**: No false positives in validation (all valid strategies accepted)

### Task 3.3: Code Pre-Validation (P2 - Optional)

**Decision Gate**: Implement only if Phase 1+2 LLM error rate >20%

- [ ] **CPV-3.1**: `StrategyCodeValidator` detects syntax errors via AST
- [ ] **CPV-3.2**: Validator detects `.shift(-1)` look-ahead bias patterns
- [ ] **CPV-3.3**: Validator detects `.rank()` without `axis` parameter (warning)
- [ ] **CPV-3.4**: Validator checks for required elements: strategy, position, report
- [ ] **CPV-3.5**: `StructuredInnovator` validates generated code
- [ ] **CPV-3.6**: Validation errors logged, retries attempted (max 1 retry)
- [ ] **CPV-3.7**: Validation overhead <10ms per call (benchmarked)
- [ ] **CPV-3.8**: 20+ code validation tests pass
- [ ] **CPV-3.9**: Integration test with code validation passes
- [ ] **CPV-3.10**: LLM error rate reduced by 50%+

## Non-functional Requirements

### Performance Requirements

- **P-1**: Type conversion overhead <0.1ms per operation
- **P-2**: Schema validation overhead <1ms per iteration
- **P-3**: Code pre-validation overhead <10ms per generation (if implemented)
- **P-4**: No performance degradation in learning loop throughput
- **P-5**: Validation operations must not block iteration execution

### Security Requirements

- **S-1**: Schema validation prevents injection of malicious metric values
- **S-2**: Code validation (if implemented) detects malicious code patterns
- **S-3**: Validation errors must not leak sensitive information in logs
- **S-4**: Pydantic version pinned to avoid supply chain vulnerabilities

### Compatibility Requirements

- **C-1**: Backward compatible with existing JSONL history files
- **C-2**: Backward compatible with existing champion.json files
- **C-3**: Python 3.10+ type hints compatibility
- **C-4**: Pydantic 2.x compatibility (latest stable)
- **C-5**: Existing test suite passes without modification

### Maintainability Requirements

- **M-1**: All new code has 80%+ unit test coverage
- **M-2**: Schema definitions serve as self-documentation
- **M-3**: Validation error messages are clear and actionable
- **M-4**: Type hints enable IDE autocomplete and error detection
- **M-5**: Architecture documentation updated (data-validation.md)

### Reliability Requirements

- **R-1**: Validation failures do not crash the learning loop
- **R-2**: Validation errors are logged with full context
- **R-3**: System continues processing valid iterations after validation failure
- **R-4**: No data loss due to validation implementation
- **R-5**: Graceful degradation if validation encounters unexpected errors

## Success Metrics

### Immediate Metrics (Post-Implementation)

- **IM-1**: Type safety: 0 mypy errors in `src/learning/`
- **IM-2**: Test coverage: >=80% for new code (Tasks 3.1, 3.2, 3.3)
- **IM-3**: Performance: All benchmarks pass (overhead thresholds met)
- **IM-4**: Backward compatibility: 100% historical data readable
- **IM-5**: Validation effectiveness: Catches 100% of test anomalous values

### Long-Term Metrics (Post-Deployment)

- **LM-1**: LLM error rate: <10% (baseline: Phase 1 rate)
- **LM-2**: System stability: >95% uptime over 30 days
- **LM-3**: Iteration success rate: >50% (strategies with Sharpe >0.5)
- **LM-4**: Data quality: 0 data corruption incidents in 90 days
- **LM-5**: Developer productivity: 30% reduction in type-related debugging time

## Dependencies & Constraints

### Technical Dependencies

- **Python**: 3.10+ for enhanced type hints
- **Pydantic**: 2.x for schema validation (add to requirements.txt)
- **mypy**: Latest stable for type checking
- **pytest**: For unit and integration testing
- **pytest-cov**: For coverage measurement

### Existing System Dependencies

- Phase 1 fixes must be completed and validated
- `StrategyMetrics` dataclass exists in `src/learning/iteration_history.py`
- `ExecutionResult` dataclass exists in `src/learning/backtest_executor.py`
- JSONL history format is stable and documented

### Constraints

- **Time Constraint**: Tasks 3.1 + 3.2 should complete in 1-2 work days
- **Backward Compatibility**: Must not break existing functionality
- **Performance**: No >5% degradation in learning loop throughput
- **Simplicity**: Avoid over-engineering, prefer simple solutions

## Out of Scope

The following are explicitly **NOT** included in Phase 3:

1. **Database Migration**: Continue using JSONL files, no database introduction
2. **UI Changes**: No changes to logging, monitoring, or visualization
3. **Algorithm Changes**: No changes to LLM prompts, feedback logic, or classification
4. **Phase 1 Bug Fixes**: Phase 1 is complete, no reopening of Bug #1-5
5. **Performance Optimization**: Beyond validation overhead, no other optimizations
6. **Distributed Systems**: No multi-process or distributed validation
7. **Advanced Validation**: No ML-based anomaly detection, only rule-based validation

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Validation overhead >1ms | Medium | Medium | Benchmark early, optimize if needed |
| Backward compatibility breaks | Low | High | Comprehensive compatibility tests |
| False positive validations | Medium | Medium | Set conservative bounds, make warnings |
| Pydantic performance issues | Low | Medium | Benchmark, consider optional validation |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Task 3.3 scope creep | High | Medium | Strict time-boxing, clear decision criteria |
| Integration issues | Medium | Medium | Incremental integration, rollback capability |
| Testing takes longer | Medium | Low | Parallel test writing, focus on critical paths |

## Approval

### Requirements Review Checklist

- [ ] All core features clearly defined
- [ ] User stories cover developer and system perspectives
- [ ] Acceptance criteria are measurable and testable
- [ ] Non-functional requirements are specific and bounded
- [ ] Success metrics are quantifiable
- [ ] Dependencies and constraints are identified
- [ ] Out of scope items are explicit
- [ ] Risks are assessed with mitigations

### Stakeholder Approval

**Technical Lead**: _____________________ Date: _______

**QA Lead**: _____________________ Date: _______

**Project Manager**: _____________________ Date: _______
