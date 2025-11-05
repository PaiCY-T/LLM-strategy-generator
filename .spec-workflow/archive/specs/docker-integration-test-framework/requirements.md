# Requirements Document

## Introduction

The Docker Integration Test Framework addresses critical integration failures in the autonomous learning system where components work correctly in isolation but fail when integrated together. The system currently experiences **100% Docker execution failure** and **diversity-aware prompting never activates** due to missing validation at integration boundaries.

This feature establishes systematic boundary validation through a three-tier testing strategy (unit, integration, E2E) and provides diagnostic instrumentation to catch integration issues early. The framework will prevent future integration failures and unblock the Stage 2 LLM innovation capability.

## Alignment with Product Vision

This feature directly supports Stage 2 (LLM + Population) activation by:

1. **Unblocking LLM Innovation**: Fixes 4 critical bugs preventing diversity-aware prompting from activating
2. **Enabling Structural Innovation**: Allows LLM-generated strategies to execute successfully in Docker sandbox (currently 0% → target 90%)
3. **Maintaining System Reliability**: Establishes testing infrastructure to prevent regression during Stage 2 activation
4. **Accelerating Development**: Reduces debugging time through systematic boundary validation and diagnostic logging

**Current Blocker**: Without this framework, the validated 90% LLM generation success rate (2025-10-30) cannot be realized because all generated strategies fail during Docker execution.

## Requirements

### Requirement 1: Fix Critical Docker Execution Failure

**User Story:** As a system operator, I want all Docker-executed strategies to run without SyntaxError, so that the autonomous learning loop can evaluate LLM-generated strategies.

#### Acceptance Criteria

1. WHEN the system assembles code for Docker execution THEN the system SHALL evaluate f-string templates before file write
2. WHEN Docker receives the complete code THEN the code SHALL contain no `{{}}` double-brace syntax
3. WHEN Docker executes the code THEN the exit code SHALL be 0 for valid strategies
4. WHEN execution completes successfully THEN the system SHALL extract metrics from the container

**Priority**: CRITICAL (hard blocker for all Docker executions)
**Current State**: 100% failure rate (exit code 1)
**Target State**: >80% execution success rate

### Requirement 2: Fix LLM API Routing Configuration

**User Story:** As a system operator, I want LLM model names to route to correct provider endpoints, so that diversity-aware prompting can activate.

#### Acceptance Criteria

1. WHEN config specifies provider='google' and model='anthropic/claude-3.5-sonnet' THEN the system SHALL raise ValueError
2. WHEN config specifies provider='google' THEN the system SHALL only accept gemini-* models
3. WHEN config specifies provider='openrouter' THEN the system SHALL accept anthropic/* models
4. WHEN LLM initialization fails validation THEN the system SHALL log clear error message with correct provider

**Priority**: CRITICAL (blocks diversity-aware prompting)
**Current State**: anthropic model sent to Google API → 404 error → fallback to Factor Graph
**Target State**: Correct routing for all model/provider combinations

### Requirement 3: Establish Integration Boundary Validation

**User Story:** As a developer, I want automated tests at every integration boundary, so that data flows are verified before production.

#### Acceptance Criteria

1. WHEN code flows from LLM generation to Docker execution THEN integration tests SHALL verify code validity
2. WHEN Docker executes code THEN integration tests SHALL verify metrics extraction works
3. WHEN LLM config is parsed THEN integration tests SHALL verify API routing is correct
4. IF any integration boundary test fails THEN the system SHALL prevent deployment

**Priority**: HIGH (prevents future integration failures)
**Current State**: ZERO checkpoint validation
**Target State**: 100% integration boundary coverage

### Requirement 4: Add Diagnostic Instrumentation

**User Story:** As a developer, I want diagnostic logging at integration boundaries, so that I can debug integration failures quickly.

#### Acceptance Criteria

1. WHEN LLM is initialized THEN the system SHALL log provider name and model being used
2. WHEN code is assembled for Docker THEN the system SHALL log first 500 chars of complete code
3. WHEN Docker execution completes THEN the system SHALL log full result structure
4. WHEN integration tests run THEN tests SHALL verify diagnostic logs are generated

**Priority**: MEDIUM (improves debugging efficiency)
**Current State**: No diagnostic logging at boundaries
**Target State**: All boundaries instrumented with debug-level logs

### Requirement 5: Fix Exception Handling State Propagation

**User Story:** As a system operator, I want exceptions to trigger diversity fallback, so that the system can recover from LLM failures.

#### Acceptance Criteria

1. WHEN Docker execution raises an exception THEN the system SHALL set last_result = False
2. WHEN last_result is False THEN the next iteration SHALL use diversity LLM model
3. WHEN diversity fallback activates THEN the system SHALL log the fallback event
4. IF fallback succeeds THEN the system SHALL continue autonomous loop

**Priority**: MEDIUM (enables recovery mechanism)
**Current State**: Exceptions don't update state → diversity never triggers
**Target State**: Automatic diversity fallback on failures

### Requirement 6: Create Missing Configuration Module

**User Story:** As a system operator, I want configuration snapshots to be captured, so that experiments are reproducible.

#### Acceptance Criteria

1. WHEN the system imports src.config.experiment_config THEN the import SHALL succeed
2. WHEN a configuration snapshot is needed THEN ExperimentConfig.from_dict() SHALL create an instance
3. WHEN configuration is serialized THEN ExperimentConfig.to_dict() SHALL return a dictionary
4. IF the module doesn't exist THEN unit tests SHALL fail

**Priority**: LOW (non-fatal but breaks config tracking)
**Current State**: Module doesn't exist → import fails every iteration
**Target State**: Module exists with minimal implementation

### Requirement 7: Definition of Done & Handoff Conditions

**User Story:** As a project maintainer, I want clear completion criteria for this stabilization work and a defined handoff to future refactoring work, so that we separate "fixing a broken system" from "improving a working system."

#### Purpose

This requirement defines the **exit criteria** for the `docker-integration-test-framework` spec and the **entry criteria** for a subsequent `autonomous-loop-refactoring` spec. Meeting these conditions triggers evaluation of whether to initiate refactoring work.

#### Acceptance Criteria - ALL MUST BE MET TO CLOSE THIS SPEC

1. **BLOCKING**: WHEN Requirements 1-6 are not fully implemented THEN this spec SHALL NOT be marked complete
2. **BLOCKING**: WHEN system execution success rate is <80% THEN this spec SHALL NOT be marked complete
3. **BLOCKING**: WHEN characterization tests are not passing THEN this spec SHALL NOT be marked complete
4. **BLOCKING**: WHEN integration test suite is not complete THEN this spec SHALL NOT be marked complete
5. **BLOCKING**: IF any of the following conditions are false THEN this spec SHALL NOT be marked complete:
   - ✅ All 4 critical bugs fixed (R1, R2, R5, R6)
   - ✅ Test framework established and integrated into CI (R3)
   - ✅ Diagnostic instrumentation in place (R4)
   - ✅ Characterization test passes (validates baseline behavior)
   - ✅ System execution success rate >80% for 30+ consecutive iterations (verified via metrics)
   - ✅ Diversity-aware prompting activates ≥30% of eligible iterations (verified via logs)
   - ✅ No regression in direct-execution mode (all existing tests pass)
   - ✅ Maintenance difficulties observed and documented (evidence-based assessment)

**Priority**: CRITICAL (defines project completion)

**Validation Mechanism**:
- **Automated Validation**: Success rate, test coverage, and CI checks pulled from monitoring/CI systems
- **Manual Review**: Final sign-off confirming all 8 conditions met (checklist in closing PR)
- **Documentation**: Maintenance difficulties report documenting specific pain points encountered

**Rationale**:
- **Separation of Concerns**: Debugging and refactoring are distinct engineering tasks requiring different mindsets
- **Risk Management**: Refactoring requires a stable baseline to validate against
- **Strategic Decision Point**: Forces conscious decision about investing in refactoring vs. other priorities
- **Evidence-Based**: Requires actual data (success rates, logs) before declaring stability

#### Handoff to Refactoring Work

**IMPORTANT**: This spec contains NO refactoring work. The design and tasks documents focus exclusively on bug fixes and testing.

**Next Steps Upon Completion**:

Once all 8 conditions are met and verified, this spec is considered **COMPLETE**. At that point, a new specification (`autonomous-loop-refactoring`) SHOULD be drafted to address technical debt.

**Initial Refactoring Candidates** (for future spec):
1. **Extract SandboxDataMockGenerator**: If multiple mock strategies are needed for different test scenarios
2. **Separate MetricsExtractor**: If different extraction methods are needed for various execution modes
3. **Reorganize AutonomousLoop**: If the file exceeds 2000 lines and demonstrates maintenance difficulties

**Evidence Required for Future Spec**:
- Documented maintenance difficulties encountered during bug fixes
- Performance profiling showing bottlenecks
- Developer feedback on code comprehension challenges
- Analysis of change frequency and bug density in identified modules

**Workflow Integration**:
```
[Spec 1: docker-integration-test-framework]
  ├─ Phase: Stabilization
  ├─ Deliverable: Stable system (>80% success rate)
  └─ Exit Criteria: Requirement 7 (8 conditions)
       ↓
  [Manual Gate: Evaluate refactoring need]
       ↓
  [Spec 2: autonomous-loop-refactoring]  ← Future work
  ├─ Entry Criteria: Spec 1 complete + business case for refactoring
  ├─ Phase: Improvement
  └─ Safety Net: Test framework from Spec 1
```

**Work Estimate Comparison**:
- **This Spec (Stabilization)**: ~50 lines of bug fixes + ~375 lines of tests = 5-6 hours
- **Future Spec (Refactoring)**: TBD based on evidence gathered during stabilization (estimated 2-3 days)

**Key Principle**: Refactoring is NOT part of this specification. It is a potential future project that will be evaluated and designed AFTER the system is stable.

## Non-Functional Requirements

### Code Architecture and Modularity
- **Test Isolation**: All integration tests must use mocks for external dependencies (LLM APIs, Docker execution)
- **Hermetic Testing**: Tests must not depend on external state or network access
- **Clear Test Organization**: Separate unit tests (`tests/unit/`) from integration tests (`tests/integration/`)
- **Fixture Reusability**: Use pytest fixtures for common test setup (temp directories, mock configs)

### Performance
- **Test Execution Speed**: Unit tests SHALL complete in <1 second each
- **Integration Test Speed**: Integration tests SHALL complete in <5 seconds each
- **CI/CD Impact**: Full test suite SHALL complete in <2 minutes
- **Production Impact**: Checkpoint validation SHALL add <50ms overhead per iteration

### Security
- **No Secrets in Tests**: Test configurations SHALL NOT contain real API keys
- **Sandbox Validation**: Docker integration tests SHALL verify read-only filesystem is enforced
- **Code Injection Prevention**: Tests SHALL verify no arbitrary code execution in templates

### Reliability
- **Test Flakiness**: Zero tolerance for flaky tests (must be deterministic)
- **Backward Compatibility**: Bug fixes SHALL NOT break existing direct-execution mode
- **Regression Prevention**: All fixed bugs SHALL have permanent unit tests
- **Coverage**: Integration boundary tests SHALL cover 100% of identified boundaries

### Usability
- **Clear Error Messages**: Test failures SHALL identify exact integration point that failed
- **Test Documentation**: Each test SHALL have docstring explaining what it validates
- **Debugging Support**: Failed tests SHALL output diagnostic information (logs, intermediate state)
- **Developer Experience**: Running tests SHALL require zero manual setup (all mocked)
