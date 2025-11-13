# API Mismatch Prevention System (Phase 5) - Task List

## TDD (Test-Driven Development) Principles

This implementation follows **strict TDD methodology** with the RED-GREEN-REFACTOR cycle:

### Core TDD Workflow

```
🔴 RED Phase: Write Failing Test First
   ↓
🟢 GREEN Phase: Write Minimal Code to Pass
   ↓
🔵 REFACTOR Phase: Improve Code Quality
   ↓
✅ VALIDATE: Confirm Tests Still Pass
```

### TDD Requirements for All Tasks

**Mandatory Steps** (in order):
1. 📊 **Baseline**: Measure current test coverage BEFORE any changes
2. 🔴 **RED**: Write failing test that validates desired behavior
3. 🟢 **GREEN**: Implement minimal code to make test pass
4. 🔵 **REFACTOR**: Improve code quality while keeping tests green
5. ✅ **VALIDATE**: Run full test suite to ensure no regressions

**Acceptance Criteria Template**:
- ✅ Failing test exists BEFORE implementation begins
- ✅ Test passes after minimal implementation
- ✅ Code refactored for quality (if needed)
- ✅ Full test suite still passes (no regressions)
- ✅ Coverage increased or maintained

### TDD Philosophy for This Project

**Why TDD for API Mismatch Prevention**:
- ✅ Prevents regression of fixed API errors
- ✅ Documents expected behavior through tests
- ✅ Catches protocol violations at development time
- ✅ Enables confident refactoring

**Test Coverage Strategy**:
- **Baseline Coverage**: 111/111 unit tests passing (100%)
- **Target Coverage**: ≥80% critical interaction coverage (Phase 5C)
- **Measurement**: Coverage measured BEFORE and AFTER each task
- **Regression Prevention**: NEVER allow coverage to decrease

---

## Implementation Tasks

### Phase 5A: CI/CD Pipeline (Week 1)

- [ ] **5A.1. Configure mypy Type Checking Infrastructure**
    - [ ] 5A.1.1. Create mypy.ini configuration file
        - *Goal*: Establish gradual typing strategy with strict enforcement on Phase 1-4 modules
        - *Details*:
            - Configure `[mypy]` section with Python 3.11, strict mode enabled
            - Configure `[mypy-src.learning.*]` with full strict enforcement
            - Configure `[mypy-src.backtest.*]` with warnings only (legacy code)
            - Add `check_untyped_defs = False` for legacy modules (Gemini recommendation)
            - Configure third-party library ignores (finlab.*, pandas.*)
        - *Requirements*: FR-2.1, FR-2.2
        - *Acceptance Criteria*:
            - mypy.ini file created with gradual typing configuration
            - `mypy src/learning/` passes with 0 errors on Phase 1-4 code
            - Legacy modules show warnings only, no blocking errors
    - [ ] 5A.1.2. Validate mypy configuration
        - *Goal*: Ensure mypy catches known API mismatches and provides helpful errors
        - *Details*:
            - Run mypy on src/learning/ directory
            - Verify it detects property vs method confusion (e.g., .get_champion() vs .champion)
            - Verify error messages are clear and actionable
            - Measure execution time (target: <30s for full check)
        - *Requirements*: FR-2.3
        - *Acceptance Criteria*:
            - mypy execution completes in <30s
            - Known API mismatches are detected with clear error messages
            - 0 false positives on correctly typed code
    - *Estimated Time*: 2 hours

- [ ] **5A.2. Setup GitHub Actions CI/CD Workflow**
    - [ ] 5A.2.1. Create GitHub Actions workflow file
        - *Goal*: Automate type checking and testing on every commit and PR
        - *Details*:
            - Create `.github/workflows/ci.yml`
            - Configure job: type-check-and-test
            - Add steps: checkout, setup Python 3.11, install dependencies
            - Add mypy step with --show-error-codes flag
            - Add pytest step with coverage reporting
            - Configure caching for pip dependencies
            - Set execution time target: <2 minutes total
        - *Requirements*: FR-3.1, FR-3.2
        - *Acceptance Criteria*:
            - Workflow file created and committed
            - Workflow runs on push to main and all PRs
            - mypy and pytest steps execute successfully
    - [ ] 5A.2.2. Optimize CI/CD performance
        - *Goal*: Ensure CI/CD pipeline meets <2min execution target
        - *Details*:
            - Implement pip dependency caching
            - Scope mypy to src/ directory only (Gemini recommendation)
            - Run mypy and pytest in parallel if possible
            - Measure actual execution time on GitHub Actions
        - *Requirements*: FR-3.2
        - *Acceptance Criteria*:
            - Total workflow execution time <2 minutes
            - Dependency caching working (cache hit on subsequent runs)
            - Parallel execution configured where possible
    - [ ] 5A.2.3. Configure branch protection rules
        - *Goal*: Prevent merging code that fails type checking or tests
        - *Details*:
            - Configure GitHub branch protection for main branch
            - Require status checks to pass before merging
            - Require type-check-and-test workflow to pass
            - Allow administrators to bypass (for emergencies)
        - *Requirements*: FR-3.3
        - *Acceptance Criteria*:
            - Branch protection enabled on main branch
            - Cannot merge PR with failing type checks
            - Cannot merge PR with failing tests
    - *Estimated Time*: 4 hours

- [ ] **5A.3. Configure Pre-commit Hooks**
    - [ ] 5A.3.1. Create pre-commit configuration
        - *Goal*: Enable local type checking before commits to catch errors early
        - *Details*:
            - Create `.pre-commit-config.yaml`
            - Add mypy hook with mirrors-mypy repo (v1.11.0)
            - Configure args: --strict, --config-file=mypy.ini
            - Scope to src/ directory with `files: ^src/` (Gemini recommendation)
            - Set stages: [commit]
            - Add additional_dependencies for type stubs
        - *Requirements*: FR-4.1, FR-4.2
        - *Acceptance Criteria*:
            - .pre-commit-config.yaml created
            - Pre-commit hook installed and working
            - mypy runs on staged files before commit
    - [ ] 5A.3.2. Test pre-commit hook workflow
        - *Goal*: Verify pre-commit hook catches errors and allows bypass when needed
        - *Details*:
            - Test hook blocks commit with type errors
            - Test hook allows commit with clean code
            - Test bypass with `git commit --no-verify` (for WIP)
            - Measure execution time (target: <10s for typical commit)
        - *Requirements*: FR-4.3
        - *Acceptance Criteria*:
            - Hook blocks commits with type errors
            - Hook allows commits with clean code
            - Bypass works with --no-verify flag
            - Execution time <10s for typical commit (5s target from Gemini)
    - *Estimated Time*: 2 hours

- [ ] **5A.4. Validate CI/CD Pipeline End-to-End**
    - [ ] 5A.4.1. Test complete workflow
        - *Goal*: Verify all components work together correctly
        - *Details*:
            - Create test PR with intentional type error
            - Verify pre-commit hook catches error locally
            - Bypass pre-commit and push to test CI/CD
            - Verify GitHub Actions catches error and blocks merge
            - Fix error and verify green pipeline
        - *Requirements*: FR-3.4
        - *Acceptance Criteria*:
            - Pre-commit hook catches type errors
            - GitHub Actions catches errors missed locally
            - Branch protection prevents merge of failing code
            - Clean code passes all checks
    - [ ] 5A.4.2. Measure and document performance
        - *Goal*: Confirm performance targets are met
        - *Details*:
            - Measure pre-commit execution time (target: <10s)
            - Measure GitHub Actions execution time (target: <2min)
            - Document actual timings in validation report
            - Identify any bottlenecks for future optimization
        - *Requirements*: FR-2.3, FR-3.2, FR-4.3
        - *Acceptance Criteria*:
            - Pre-commit execution <10s documented
            - GitHub Actions execution <2min documented
            - Validation report created with timing metrics
    - *Estimated Time*: 2 hours

- [ ] **5A.5. Document Developer Workflow**
    - [ ] 5A.5.1. Create developer guide
        - *Goal*: Enable developers to understand and use the type checking system
        - *Details*:
            - Document how to install pre-commit hooks
            - Document how to run mypy locally
            - Document how to interpret mypy error messages
            - Document when and how to bypass pre-commit (WIP commits)
            - Document GitHub Actions workflow and branch protection
            - Include common error scenarios and fixes
        - *Requirements*: FR-3.4
        - *Acceptance Criteria*:
            - Developer guide created (markdown format)
            - Guide covers installation, usage, and troubleshooting
            - Examples of common errors and fixes included
    - [ ] 5A.5.2. Create runbook for CI/CD issues
        - *Goal*: Provide troubleshooting guide for CI/CD problems
        - *Details*:
            - Document how to diagnose CI/CD failures
            - Document how to bypass branch protection (emergency)
            - Document how to update mypy configuration
            - Document how to add new type stubs
        - *Requirements*: FR-3.4
        - *Acceptance Criteria*:
            - Runbook created with troubleshooting procedures
            - Emergency bypass procedure documented
            - Configuration update procedure documented
    - *Estimated Time*: 4 hours

**Phase 5A Total: 14 hours**

---

### Phase 5B: Interface Contracts (Week 2)

- [ ] **5B.1. Design and Implement Protocol Interfaces (TDD-Driven)**
    - [ ] 5B.1.0. 📊 BASELINE: Measure Current State
        - *TDD Phase*: **BASELINE**
        - *Goal*: Establish baseline before Protocol introduction
        - *Details*:
            - Run `pytest tests/learning/ --cov=src/learning --cov-report=term`
            - Document current test count: 111/111 passing
            - Document current coverage: Phase 1-4 modules
            - Identify which existing classes will implement Protocols
            - Capture current API usage patterns (grep for .champion, .save, .classify_error)
        - *Acceptance Criteria*:
            - ✅ Baseline coverage documented (should be 100% for Phase 1-4)
            - ✅ Current API patterns captured
            - ✅ Existing implementations identified (ChampionTracker, IterationHistory, ErrorClassifier)
    - [ ] 5B.1.1. 🔴 RED: Write Protocol Compliance Tests FIRST
        - *TDD Phase*: **RED (Write Failing Tests)**
        - *Goal*: Create failing tests that will pass once Protocols are implemented
        - *Details*:
            - Create `tests/learning/test_protocol_compliance.py`
            - Write test_champion_tracker_implements_protocol():
                - Import ChampionTracker (exists)
                - Try: `assert isinstance(champion_tracker, IChampionTracker)` → FAILS (Protocol doesn't exist yet)
            - Write test_iteration_history_implements_protocol():
                - Import IterationHistory (exists)
                - Try: `assert isinstance(history, IIterationHistory)` → FAILS (Protocol doesn't exist yet)
            - Write test_error_classifier_implements_protocol():
                - Import ErrorClassifier (exists)
                - Try: `assert isinstance(classifier, IErrorClassifier)` → FAILS (Protocol doesn't exist yet)
            - Run tests: **EXPECT ALL 3 TESTS TO FAIL** (ImportError: IChampionTracker not found)
        - *Acceptance Criteria*:
            - ✅ test_protocol_compliance.py created with 3 failing tests
            - ✅ Tests fail with ImportError (Protocols don't exist yet)
            - ✅ Test structure is correct (will pass once Protocols exist)
    - [ ] 5B.1.2. 🟢 GREEN: Create Minimal Protocol Definitions
        - *TDD Phase*: **GREEN (Minimal Implementation)**
        - *Goal*: Define Protocols with minimal structure to make tests pass
        - *Details*:
            - Create `src/learning/interfaces.py`
            - Import typing.Protocol, runtime_checkable, Optional, List
            - Define IChampionTracker Protocol with @runtime_checkable:
                - Add .champion property signature (minimal docstring)
                - Add .update_champion() method signature
            - Define IIterationHistory Protocol with @runtime_checkable:
                - Add .save() method signature
                - Add .get_all() method signature
                - Add .get_by_iteration() method signature
            - Define IErrorClassifier Protocol with @runtime_checkable:
                - Add .classify_error() method signature
            - Run tests: **EXPECT isinstance() tests to PASS** (structural typing)
        - *Acceptance Criteria*:
            - ✅ src/learning/interfaces.py created
            - ✅ All 3 Protocol compliance tests now PASS
            - ✅ mypy validates Protocol syntax (no errors)
            - ✅ Minimal implementation only (no comprehensive docs yet)
    - [ ] 5B.1.3. 🔵 REFACTOR: Add Behavioral Contracts & Documentation
        - *TDD Phase*: **REFACTOR (Improve Quality)**
        - *Goal*: Enhance Protocols with comprehensive behavioral contracts while keeping tests green
        - *Details*:
            - Enhance IChampionTracker docstrings:
                - Add behavioral contract (referential stability, idempotency)
                - Add pre-conditions and post-conditions
                - Add usage examples
            - Enhance IIterationHistory docstrings:
                - Add behavioral contract (idempotency, ordering guarantee)
                - Document state change guarantees
            - Enhance IErrorClassifier docstrings:
                - Add deterministic behavior guarantee
            - Run tests: **EXPECT ALL TESTS STILL PASS** (no behavior change)
        - *Acceptance Criteria*:
            - ✅ Comprehensive behavioral contracts added
            - ✅ Pre/post conditions documented
            - ✅ All Protocol compliance tests still PASS
            - ✅ mypy still validates with no errors
    - [ ] 5B.1.4. 🔴 RED: Write Runtime Validation Tests FIRST
        - *TDD Phase*: **RED (Write Failing Tests)**
        - *Goal*: Create tests for validation utility before it exists
        - *Details*:
            - Create `tests/learning/test_runtime_validation.py`
            - Write test_validate_protocol_compliance_passes_for_valid_object():
                - Mock object with .champion property and .update_champion() method
                - Try: `validate_protocol_compliance(mock, IChampionTracker, "test")` → FAILS (function doesn't exist)
            - Write test_validate_protocol_compliance_fails_for_invalid_object():
                - Mock object WITHOUT .champion property
                - Try: `validate_protocol_compliance(mock, IChampionTracker, "test")` → FAILS (function doesn't exist)
                - Expect TypeError with helpful message
            - Run tests: **EXPECT ImportError** (validate_protocol_compliance doesn't exist)
        - *Acceptance Criteria*:
            - ✅ test_runtime_validation.py created with failing tests
            - ✅ Tests fail with ImportError (function doesn't exist yet)
    - [ ] 5B.1.5. 🟢 GREEN: Implement Minimal Runtime Validation
        - *TDD Phase*: **GREEN (Minimal Implementation)**
        - *Goal*: Create validation.py with minimal code to pass tests
        - *Details*:
            - Create `src/learning/validation.py`
            - Implement validate_protocol_compliance() function:
                - Accept obj, protocol, context parameters
                - Use isinstance() check with @runtime_checkable Protocol
                - Raise TypeError if check fails
                - Return obj if check passes
            - Run tests: **EXPECT tests to PASS**
        - *Acceptance Criteria*:
            - ✅ src/learning/validation.py created
            - ✅ validate_protocol_compliance() function works
            - ✅ All validation tests PASS
    - [ ] 5B.1.6. 🔵 REFACTOR: Add Diagnostic Messages
        - *TDD Phase*: **REFACTOR (Improve Quality)**
        - *Goal*: Enhance error messages with missing attribute diagnostics
        - *Details*:
            - Implement _get_missing_attrs() helper function
            - Enhance TypeError message to include missing attributes
            - Add comprehensive docstrings with usage examples
            - Add type hints for all parameters
            - Run tests: **EXPECT all tests STILL PASS** (behavior unchanged, better errors)
        - *Acceptance Criteria*:
            - ✅ Error messages include missing attributes list
            - ✅ Comprehensive docstrings added
            - ✅ All tests still PASS
            - ✅ mypy validates with no errors
    - *Estimated Time*: 5 hours (was 4h, +1h for TDD steps)

- [ ] **5B.2. Implement IChampionTracker Protocol**
    - [ ] 5B.2.1. Update ChampionTracker class
        - *Goal*: Ensure ChampionTracker conforms to IChampionTracker Protocol
        - *Details*:
            - Review existing ChampionTracker implementation
            - Verify .champion property (not .get_champion() method)
            - Verify .update_champion() method signature matches Protocol
            - Add behavioral contract docstrings if missing
            - Add pre/post condition documentation
        - *Requirements*: FR-1.1
        - *Acceptance Criteria*:
            - ChampionTracker conforms to IChampionTracker Protocol
            - mypy validates compliance with no errors
            - Behavioral contracts documented in docstrings
    - [ ] 5B.2.2. Add unit tests for Protocol compliance
        - *Goal*: Verify ChampionTracker implements Protocol correctly
        - *Details*:
            - Create test_champion_tracker_protocol.py
            - Test isinstance(champion_tracker, IChampionTracker) passes
            - Test .champion property returns Optional[IterationRecord]
            - Test .update_champion() behavior (idempotency, force flag)
            - Test referential stability (calling .champion twice)
        - *Requirements*: FR-1.3
        - *Acceptance Criteria*:
            - Unit tests created and passing
            - Protocol compliance validated via isinstance()
            - Behavioral contracts tested
    - *Estimated Time*: 3 hours

- [ ] **5B.3. Implement IIterationHistory and IErrorClassifier Protocols**
    - [ ] 5B.3.1. Update IterationHistory class
        - *Goal*: Ensure IterationHistory conforms to IIterationHistory Protocol
        - *Details*:
            - Review existing IterationHistory implementation
            - Verify .save() method (not .save_record())
            - Verify .get_all() returns List[IterationRecord]
            - Verify .get_by_iteration() method exists
            - Add behavioral contract docstrings (idempotency, ordering)
        - *Requirements*: FR-1.1
        - *Acceptance Criteria*:
            - IterationHistory conforms to IIterationHistory Protocol
            - mypy validates compliance
            - Behavioral contracts documented
    - [ ] 5B.3.2. Update ErrorClassifier class
        - *Goal*: Ensure ErrorClassifier conforms to IErrorClassifier Protocol
        - *Details*:
            - Review existing ErrorClassifier implementation
            - Verify .classify_error() method signature
            - Add deterministic behavior documentation
            - Clarify difference from SuccessClassifier.classify_single()
        - *Requirements*: FR-1.1
        - *Acceptance Criteria*:
            - ErrorClassifier conforms to IErrorClassifier Protocol
            - mypy validates compliance
            - Method clearly distinguished from SuccessClassifier
    - [ ] 5B.3.3. Add unit tests for Protocol compliance
        - *Goal*: Verify both classes implement Protocols correctly
        - *Details*:
            - Test isinstance() checks for both classes
            - Test IterationHistory.save() idempotency
            - Test IterationHistory.get_all() ordering guarantee
            - Test ErrorClassifier.classify_error() determinism
        - *Requirements*: FR-1.3
        - *Acceptance Criteria*:
            - Unit tests created and passing for both classes
            - Protocol compliance validated via isinstance()
    - *Estimated Time*: 3 hours

- [ ] **5B.4. Add Runtime Validation to LearningLoop**
    - [ ] 5B.4.1. Update LearningLoop.__init__()
        - *Goal*: Add runtime validation at module boundaries
        - *Details*:
            - Import validate_protocol_compliance from src.learning.validation
            - Import Protocol interfaces from src.learning.interfaces
            - Add validation for ChampionTracker initialization
                - Call validate_protocol_compliance(tracker, IChampionTracker, "ChampionTracker init")
            - Add validation for IterationHistory initialization
                - Call validate_protocol_compliance(history, IIterationHistory, "IterationHistory init")
            - Wrap in try/except to provide clear error messages
        - *Requirements*: DESIGN_IMPROVEMENTS Layer 3.5
        - *Acceptance Criteria*:
            - Runtime validation added to LearningLoop.__init__()
            - Validation occurs at component initialization
            - Clear error messages on protocol violations
    - [ ] 5B.4.2. Test runtime validation behavior
        - *Goal*: Verify runtime validation catches protocol violations
        - *Details*:
            - Create test with mock object missing .champion property
            - Verify TypeError raised with helpful message
            - Create test with mock object missing .update_champion() method
            - Verify error message lists missing attributes
            - Measure validation overhead (target: <100ms)
        - *Requirements*: DESIGN_IMPROVEMENTS Risk Mitigation
        - *Acceptance Criteria*:
            - Runtime validation catches protocol violations
            - Error messages list missing attributes
            - Validation overhead <100ms documented
    - *Estimated Time*: 3 hours

- [ ] **5B.5. Validate mypy Strict Compliance**
    - [ ] 5B.5.1. Run mypy on all modified files
        - *Goal*: Ensure all Protocol implementations pass strict type checking
        - *Details*:
            - Run mypy on src/learning/ directory
            - Verify 0 errors on Phase 1-4 modules
            - Fix any type errors discovered
            - Verify Protocol usage is correct
        - *Requirements*: FR-2.1
        - *Acceptance Criteria*:
            - mypy passes with 0 errors on src/learning/
            - All Protocol implementations validated
    - [ ] 5B.5.2. Test @runtime_checkable overhead
        - *Goal*: Measure performance impact of runtime validation
        - *Details*:
            - Benchmark LearningLoop initialization time (before/after)
            - Measure validation overhead for each component
            - Verify target: <100ms total overhead
            - Document results in validation report
        - *Requirements*: DESIGN_IMPROVEMENTS Risk Mitigation
        - *Acceptance Criteria*:
            - Performance benchmarks collected
            - Validation overhead <100ms confirmed
            - Results documented in validation report
    - [ ] 5B.5.3. Update documentation
        - *Goal*: Document Protocol usage and runtime validation
        - *Details*:
            - Document Protocol definitions in interfaces.py
            - Document runtime validation in validation.py
            - Document usage in LearningLoop
            - Include examples of common Protocol violations
        - *Requirements*: FR-1.3
        - *Acceptance Criteria*:
            - Protocol documentation complete
            - Runtime validation usage documented
            - Examples provided for developers
    - *Estimated Time*: 3 hours

**Phase 5B Total: 16 hours**

---

### Phase 5C: Integration Testing (Week 3)

- [ ] **5C.1. Design Integration Test Strategy**
    - [ ] 5C.1.1. Define test scope and objectives
        - *Goal*: Plan integration tests that validate behavioral outcomes, not just interfaces
        - *Details*:
            - Identify critical component boundaries
                - ChampionTracker ↔ IterationHistory
                - ChampionTracker ↔ HallOfFameRepository
                - FeedbackGenerator ↔ ChampionTracker + IterationHistory
                - IterationExecutor ↔ All components
            - Define behavioral test criteria (Gemini recommendation)
                - Test outcomes and state changes, not just method calls
                - Verify idempotency guarantees
                - Verify referential stability
            - Define critical path test scenarios
                - Main success flow (strategy gen → backtest → champion update)
                - Critical failures (timeout, API errors, file corruption)
        - *Requirements*: FR-5.1, FR-5.2, DESIGN_IMPROVEMENTS Section 3
        - *Acceptance Criteria*:
            - Test scope document created
            - Critical boundaries identified
            - Behavioral test criteria defined
    - [ ] 5C.1.2. Create test infrastructure
        - *Goal*: Setup integration test framework and fixtures
        - *Details*:
            - Create tests/integration/ directory structure
            - Create shared fixtures for component setup
            - Create helper utilities for test data generation
            - Configure pytest for integration tests (markers, etc.)
        - *Requirements*: FR-5.1
        - *Acceptance Criteria*:
            - tests/integration/ directory created
            - Shared fixtures implemented
            - pytest configured for integration tests
    - *Estimated Time*: 3 hours

- [ ] **5C.2. ChampionTracker Integration Tests**
    - [ ] 5C.2.1. Test ChampionTracker ↔ IterationHistory integration
        - *Goal*: Verify champion updates are persisted correctly
        - *Details*:
            - Test champion update triggers history save
            - Test champion retrieval after save (referential stability)
            - Test idempotency (updating with same record twice)
            - Test force flag behavior
            - Focus on behavioral outcomes (Gemini recommendation)
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - Integration tests created and passing
            - Behavioral outcomes validated (not just interface calls)
            - Idempotency verified
    - [ ] 5C.2.2. Test ChampionTracker ↔ HallOfFameRepository integration
        - *Goal*: Verify champion strategies saved to Hall of Fame correctly
        - *Details*:
            - Test champion code saved to file system
            - Test champion metrics persisted
            - Test champion retrieval after save
            - Test file corruption handling
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - Hall of Fame integration tests passing
            - File system operations validated
            - Error handling tested
    - [ ] 5C.2.3. Test ChampionTracker ↔ AntiChurnManager integration
        - *Goal*: Verify anti-churn logic prevents spurious champion changes
        - *Details*:
            - Test champion updates with small metric improvements (blocked)
            - Test champion updates with significant improvements (allowed)
            - Test force flag overrides anti-churn
            - Verify behavioral outcomes (champion state changes)
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - Anti-churn integration tests passing
            - State changes validated
    - *Estimated Time*: 4 hours

- [ ] **5C.3. IterationHistory Integration Tests**
    - [ ] 5C.3.1. Test IterationHistory persistence behavior
        - *Goal*: Verify save/load operations maintain data integrity
        - *Details*:
            - Test save() method actually persists data (Gemini recommendation)
            - Test get_all() returns persisted records in order
            - Test get_by_iteration() retrieves correct record
            - Test idempotency (saving same record twice)
            - Test file corruption recovery
        - *Requirements*: FR-5.2, DESIGN_IMPROVEMENTS Section 3
        - *Acceptance Criteria*:
            - Persistence tests validate outcomes, not just calls
            - Idempotency verified
            - Ordering guarantee tested
    - [ ] 5C.3.2. Test IterationHistory ↔ File System integration
        - *Goal*: Verify JSONL file operations work correctly
        - *Details*:
            - Test file creation on first save
            - Test append behavior on subsequent saves
            - Test file locking (concurrent access)
            - Test large file handling (>1000 iterations)
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - File system integration tests passing
            - Concurrent access handled correctly
            - Large file performance acceptable
    - *Estimated Time*: 4 hours

- [ ] **5C.4. Component Interaction Tests**
    - [ ] 5C.4.1. Test FeedbackGenerator integration
        - *Goal*: Verify feedback generation uses correct APIs from dependencies
        - *Details*:
            - Test FeedbackGenerator ↔ ChampionTracker (uses .champion property)
            - Test FeedbackGenerator ↔ IterationHistory (uses .get_all())
            - Test feedback generation with no champion
            - Test feedback generation with champion
            - Verify behavioral outcomes (correct feedback strings)
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - FeedbackGenerator integration tests passing
            - API usage validated (no get_champion() calls)
            - Behavioral outcomes correct
    - [ ] 5C.4.2. Test IterationExecutor integration
        - *Goal*: Verify IterationExecutor coordinates all components correctly
        - *Details*:
            - Test IterationExecutor ↔ ChampionTracker (champion updates)
            - Test IterationExecutor ↔ IterationHistory (record saves)
            - Test IterationExecutor ↔ FeedbackGenerator (feedback retrieval)
            - Test IterationExecutor ↔ BacktestExecutor (backtest execution)
            - Test critical path: strategy gen → backtest → champion update → save
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - IterationExecutor integration tests passing
            - Critical path validated end-to-end
            - All component interactions tested
    - [ ] 5C.4.3. Test error handling across components
        - *Goal*: Verify components handle errors from dependencies correctly
        - *Details*:
            - Test backtest timeout handling
            - Test file I/O errors (disk full, permissions)
            - Test invalid data handling (corrupted JSONL)
            - Test LLM API errors
            - Verify graceful degradation and error propagation
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - Error handling tests passing
            - Graceful degradation verified
            - Error propagation tested
    - *Estimated Time*: 6 hours

- [ ] **5C.5. End-to-End Iteration Flow Test**
    - [ ] 5C.5.1. Create E2E test scenario
        - *Goal*: Validate complete iteration flow from start to finish
        - *Details*:
            - Setup: Initialize all components (ChampionTracker, History, etc.)
            - Execute: Run complete iteration (gen → backtest → classify → save)
            - Verify: Check all state changes and side effects
                - Strategy generated and backtested
                - Metrics extracted and classified
                - Champion updated if applicable
                - History saved with correct record
            - Test both success and failure scenarios
        - *Requirements*: FR-5.2, DESIGN_IMPROVEMENTS Section 3
        - *Acceptance Criteria*:
            - E2E test created and passing
            - Success scenario validated
            - Failure scenarios tested
    - [ ] 5C.5.2. Test iteration resumption
        - *Goal*: Verify system can resume from saved state correctly
        - *Details*:
            - Run 3 iterations and save state
            - Create new LearningLoop instance
            - Verify it resumes from iteration 3
            - Verify champion state restored correctly
            - Verify history continuity
        - *Requirements*: FR-5.2
        - *Acceptance Criteria*:
            - Resumption test passing
            - State restoration verified
            - Continuity maintained
    - *Estimated Time*: 5 hours

- [ ] **5C.6. Achieve 80% Integration Test Coverage**
    - [ ] 5C.6.1. Measure integration test coverage
        - *Goal*: Verify integration tests cover ≥80% of critical interactions
        - *Details*:
            - Run pytest with coverage on integration tests
            - Focus on coverage of component boundaries
            - Identify gaps in critical path coverage
            - Prioritize tests for uncovered critical interactions
        - *Requirements*: FR-5.3
        - *Acceptance Criteria*:
            - Coverage report generated
            - Critical interaction coverage measured
            - Gaps identified and prioritized
    - [ ] 5C.6.2. Fill coverage gaps
        - *Goal*: Add tests to reach 80% coverage target (Gemini: critical interactions, not LOC)
        - *Details*:
            - Add tests for identified gaps
            - Focus on critical interactions and edge cases
            - Avoid testing implementation details
            - Maintain behavioral test focus
        - *Requirements*: FR-5.3, DESIGN_IMPROVEMENTS Section 3
        - *Acceptance Criteria*:
            - ≥80% coverage of critical interactions achieved
            - New tests follow behavioral validation approach
    - [ ] 5C.6.3. Document integration test results
        - *Goal*: Create comprehensive validation report
        - *Details*:
            - Document all integration test scenarios
            - Document coverage metrics
            - Document any known limitations or edge cases
            - Include recommendations for future testing
        - *Requirements*: FR-5.3
        - *Acceptance Criteria*:
            - Validation report created
            - Coverage metrics documented
            - Recommendations provided
    - *Estimated Time*: 4 hours

**Phase 5C Total: 26 hours**

---

## Task Dependencies

### Phase 5A: CI/CD Pipeline
- **5A.1** must be completed before **5A.2** (CI needs mypy config)
- **5A.2** and **5A.3** can be developed in parallel (independent)
- **5A.4** depends on completion of **5A.1**, **5A.2**, **5A.3** (end-to-end validation)
- **5A.5** can be written in parallel with implementation (documentation)

### Phase 5B: Interface Contracts
- **5B.1** must be completed first (defines all Protocols)
- **5B.2**, **5B.3**, **5B.4** can be developed in parallel after **5B.1**
- **5B.5** depends on completion of **5B.1**, **5B.2**, **5B.3**, **5B.4** (final validation)

### Phase 5C: Integration Testing
- **5C.1** must be completed first (test strategy and infrastructure)
- **5C.2**, **5C.3**, **5C.4** can be developed in parallel after **5C.1**
- **5C.5** depends on completion of **5C.2**, **5C.3**, **5C.4** (uses all components)
- **5C.6** depends on completion of all other 5C tasks (measures overall coverage)

### Cross-Phase Dependencies
- **Phase 5B** can start before **Phase 5A** is complete (parallel development)
- **Phase 5C** should start after **5B.1** is complete (needs Protocol definitions)
- **Phase 5C** benefits from **5A.2** being complete (CI runs integration tests)

### Critical Path
The critical path (31 hours with parallelization) is:
1. 5A.1 (2h) → 5A.2 (4h) → 5A.4 (2h) = 8h
2. 5B.1 (4h) → 5B.5 (3h) = 7h
3. 5C.1 (3h) → 5C.2 (4h) → 5C.5 (5h) → 5C.6 (4h) = 16h
**Total Critical Path: 31 hours**

---

## Parallel Execution Plan

### Week 1 Execution Strategy (Phase 5A - 14h Sequential → 8h Parallel)

**Day 1 (Morning 2h)**: Sequential Foundation
- ✅ **5A.1**: Configure mypy.ini (2h) - MUST complete first

**Day 1 (Afternoon 4h) + Day 2 (Morning 2h)**: Parallel Track Split
- **Track A** (4h): 5A.2 - Setup GitHub Actions workflow
- **Track B** (2h): 5A.3 - Configure pre-commit hooks
- **Track C** (Ongoing): 5A.5 - Start documentation (can work alongside implementation)

**Day 2 (Afternoon 2h)**: Integration & Validation
- ✅ **5A.4**: Validate CI/CD pipeline end-to-end (requires 5A.1, 5A.2, 5A.3 complete)

**Day 2-3 (Remaining 4h)**: Documentation Finalization
- ✅ **5A.5**: Complete developer workflow documentation

**Parallel Speedup**: 14h sequential → 8h with 2 parallel tracks = **43% time reduction**

---

### Week 2 Execution Strategy (Phase 5B - 16h Sequential → 11h Parallel)

**Day 1 (Morning 4h)**: Sequential Foundation
- ✅ **5B.1**: Design Protocol interfaces + runtime validation (4h) - MUST complete first

**Day 1 (Afternoon 3h) + Day 2 (6h)**: Triple Parallel Track
- **Track A** (3h): 5B.2 - Implement IChampionTracker Protocol
- **Track B** (3h): 5B.3 - Implement IIterationHistory + IErrorClassifier Protocols
- **Track C** (3h): 5B.4 - Add runtime validation to LearningLoop

**Day 2 (Afternoon 3h)**: Final Validation
- ✅ **5B.5**: Validate mypy strict compliance (requires all implementations complete)

**Parallel Speedup**: 16h sequential → 11h with 3 parallel tracks = **31% time reduction**

**Note**: Phase 5B can START on Day 1 Week 1 (parallel with 5A) if needed, since 5B.1 doesn't depend on Phase 5A completion.

---

### Week 3 Execution Strategy (Phase 5C - 26h Sequential → 16h Parallel)

**Day 1 (Morning 3h)**: Sequential Foundation
- ✅ **5C.1**: Design integration test strategy + infrastructure (3h) - MUST complete first

**Day 1 (Afternoon 4h) + Day 2 (Full 8h) + Day 3 (2h)**: Triple Parallel Track
- **Track A** (4h): 5C.2 - ChampionTracker integration tests
- **Track B** (4h): 5C.3 - IterationHistory integration tests
- **Track C** (6h): 5C.4 - Component interaction tests (largest task)

**Day 3 (Afternoon 5h)**: E2E Testing
- ✅ **5C.5**: End-to-end iteration flow test (requires all component tests complete)

**Day 4 (4h)**: Coverage Achievement
- ✅ **5C.6**: Achieve 80% integration test coverage (requires all tests complete)

**Parallel Speedup**: 26h sequential → 16h with 3 parallel tracks = **38% time reduction**

---

## Optimal Parallelization Matrix

### Parallelization Opportunities

| Phase | Sequential Time | Parallel Time | Tracks | Speedup | Key Blocker |
|-------|----------------|---------------|---------|---------|-------------|
| **5A** | 14h | 8h | 2-3 | 43% | 5A.1 (mypy.ini must complete first) |
| **5B** | 16h | 11h | 3 | 31% | 5B.1 (Protocols must be defined first) |
| **5C** | 26h | 16h | 3 | 38% | 5C.1 (test infrastructure must exist) |
| **Total** | **56h** | **31h** (critical path) | N/A | **45% overall** | Sequential foundations |

### Recommended Parallel Workflow

```
Week 1 Timeline (Phase 5A):
┌─────────────────────────────────────────────────────────┐
│ Day 1 AM:  5A.1 (2h) ✓ Foundation                      │
├─────────────────────────────────────────────────────────┤
│ Day 1 PM:  5A.2 (4h) ║ 5A.3 (2h) ║ 5A.5 (ongoing)      │
├─────────────────────────────────────────────────────────┤
│ Day 2 AM:  5A.2 cont ║ 5A.5 cont                        │
├─────────────────────────────────────────────────────────┤
│ Day 2 PM:  5A.4 (2h) ✓ Integration                     │
├─────────────────────────────────────────────────────────┤
│ Day 3:     5A.5 (4h) ✓ Documentation                   │
└─────────────────────────────────────────────────────────┘
Total: 3 days (vs 5 days sequential)

Week 2 Timeline (Phase 5B):
┌─────────────────────────────────────────────────────────┐
│ Day 1 AM:  5B.1 (4h) ✓ Foundation                      │
├─────────────────────────────────────────────────────────┤
│ Day 1 PM:  5B.2 (3h) ║ 5B.3 (3h) ║ 5B.4 (3h)           │
├─────────────────────────────────────────────────────────┤
│ Day 2 AM:  5B.2 cont ║ 5B.3 cont ║ 5B.4 cont           │
├─────────────────────────────────────────────────────────┤
│ Day 2 PM:  5B.5 (3h) ✓ Validation                      │
└─────────────────────────────────────────────────────────┘
Total: 2 days (vs 3 days sequential)

Week 3 Timeline (Phase 5C):
┌─────────────────────────────────────────────────────────┐
│ Day 1 AM:  5C.1 (3h) ✓ Foundation                      │
├─────────────────────────────────────────────────────────┤
│ Day 1 PM:  5C.2 (4h) ║ 5C.3 (4h) ║ 5C.4 (6h)           │
├─────────────────────────────────────────────────────────┤
│ Day 2:     5C.2 cont ║ 5C.3 cont ║ 5C.4 cont (8h)      │
├─────────────────────────────────────────────────────────┤
│ Day 3 AM:  5C.4 cont (2h remaining)                     │
├─────────────────────────────────────────────────────────┤
│ Day 3 PM:  5C.5 (5h) E2E testing                        │
├─────────────────────────────────────────────────────────┤
│ Day 4:     5C.6 (4h) ✓ Coverage                        │
└─────────────────────────────────────────────────────────┘
Total: 4 days (vs 6.5 days sequential)
```

### Cross-Phase Parallelization (Advanced)

**Aggressive Parallel Strategy**: Start Phase 5B during Week 1

```
Week 1 (Days 1-3): Phase 5A + Start 5B
┌─────────────────────────────────────────────────────────┐
│ Day 1 AM:  5A.1 (2h) ✓                                  │
│ Day 1 PM:  5A.2 (4h) ║ 5A.3 (2h) ║ 5B.1 START (2h)     │
│ Day 2 AM:  5A.2 cont ║ 5B.1 cont (2h) ✓                 │
│ Day 2 PM:  5A.4 (2h) ✓ ║ 5B.2 START (2h)               │
│ Day 3:     5A.5 (4h) ║ 5B.2 cont (1h) ✓                 │
└─────────────────────────────────────────────────────────┘

Week 2 (Days 4-6): Complete 5B + Start 5C
┌─────────────────────────────────────────────────────────┐
│ Day 4:     5B.3 (3h) ║ 5B.4 (3h)                        │
│ Day 5:     5B.5 (3h) ✓ ║ 5C.1 START (3h) ✓             │
│ Day 6:     5C.2 (4h) ║ 5C.3 (4h) START                  │
└─────────────────────────────────────────────────────────┘

Week 3 (Days 7-9): Complete 5C
┌─────────────────────────────────────────────────────────┐
│ Day 7:     5C.3 cont ║ 5C.4 (6h) START                  │
│ Day 8:     5C.4 cont (2h) + 5C.5 (5h)                   │
│ Day 9:     5C.6 (4h) ✓                                  │
└─────────────────────────────────────────────────────────┘
```

**Maximum Speedup**: 56h → ~22h calendar time with aggressive cross-phase parallelization = **61% time reduction**

**Risk**: Higher cognitive load managing multiple phases simultaneously

---

## Parallelization Guidelines

### Safe Parallelization Rules
1. ✅ **ALWAYS complete foundation tasks first** (5A.1, 5B.1, 5C.1)
2. ✅ **NEVER parallelize dependent tasks** (e.g., 5A.4 needs 5A.1+5A.2+5A.3)
3. ✅ **Documentation can run parallel** with implementation (5A.5 during 5A.2/5A.3)
4. ✅ **Cross-phase parallel safe** if no dependencies (5B can start during 5A)
5. ⚠️ **Be cautious with 3+ parallel tracks** (cognitive load, context switching)

### Resource Requirements for Parallel Execution
- **2 Parallel Tracks**: 1 developer (context switching acceptable)
- **3 Parallel Tracks**: 2-3 developers OR 1 developer with careful time-boxing
- **Cross-Phase Parallel**: Requires clear task separation and discipline

### When to Use Parallel Execution
- ✅ **Use 2-track parallel**: Always recommended (minimal overhead)
- ✅ **Use 3-track parallel**: When tight deadlines or multiple developers
- ⚠️ **Use cross-phase parallel**: Only if comfortable with complex task juggling
- ❌ **Avoid >3 tracks**: Diminishing returns, high cognitive load

---

## Estimated Timeline

### Phase 5A: CI/CD Pipeline (Week 1)
- **5A.1**: Configure mypy.ini - 2 hours
- **5A.2**: Setup GitHub Actions - 4 hours
- **5A.3**: Configure pre-commit hooks - 2 hours
- **5A.4**: Validate CI/CD pipeline - 2 hours
- **5A.5**: Document developer workflow - 4 hours
- **Phase 5A Total**: 14 hours

### Phase 5B: Interface Contracts (Week 2) - TDD-Driven
- **5B.1**: Protocol interfaces (TDD: BASELINE→RED→GREEN→REFACTOR) - 5 hours (was 4h)
  - 5B.1.0: 📊 Baseline measurement (0.5h)
  - 5B.1.1: 🔴 RED - Write failing Protocol tests (1h)
  - 5B.1.2: 🟢 GREEN - Minimal Protocol definitions (1h)
  - 5B.1.3: 🔵 REFACTOR - Add behavioral contracts (1h)
  - 5B.1.4: 🔴 RED - Write failing validation tests (0.5h)
  - 5B.1.5: 🟢 GREEN - Minimal validation implementation (0.5h)
  - 5B.1.6: 🔵 REFACTOR - Add diagnostics (0.5h)
- **5B.2**: Implement IChampionTracker (TDD cycle) - 3 hours
- **5B.3**: Implement IIterationHistory + IErrorClassifier (TDD cycle) - 3 hours
- **5B.4**: Add runtime validation to LearningLoop (TDD cycle) - 3 hours
- **5B.5**: Validate mypy compliance + Final validation - 3 hours
- **Phase 5B Total**: 17 hours (was 16h, +1h for TDD rigor)

### Phase 5C: Integration Testing (Week 3)
- **5C.1**: Design test strategy - 3 hours
- **5C.2**: ChampionTracker integration tests - 4 hours
- **5C.3**: IterationHistory integration tests - 4 hours
- **5C.4**: Component interaction tests - 6 hours
- **5C.5**: E2E iteration flow test - 5 hours
- **5C.6**: Achieve 80% coverage - 4 hours
- **Phase 5C Total**: 26 hours

### Overall Timeline
- **Total Sequential Time**: 56 hours (7 working days)
- **Total Parallel Time**: ~31 hours (4 working days with optimal parallelization)
- **Recommended Schedule**: 3 weeks, one phase per week

---

## Success Criteria

### Phase 5A Success Criteria
- ✅ mypy.ini configured with gradual typing strategy
- ✅ GitHub Actions workflow running in <2 minutes
- ✅ Pre-commit hooks running in <10 seconds (target: 5s)
- ✅ Branch protection preventing merge of failing code
- ✅ Developer documentation complete

### Phase 5B Success Criteria
- ✅ All three Protocols defined with @runtime_checkable
- ✅ Behavioral contracts documented in docstrings
- ✅ Runtime validation implemented at module boundaries
- ✅ Validation overhead <100ms measured
- ✅ mypy --strict passes on all Phase 1-4 modules

### Phase 5C Success Criteria
- ✅ ≥80% coverage of critical component interactions
- ✅ Behavioral validation tests (outcomes, not just calls)
- ✅ E2E iteration flow test passing
- ✅ All 8 known API errors prevented by test suite
- ✅ Validation report documenting test results

### Overall Success Criteria
- ✅ All 111 existing unit tests still passing
- ✅ ≥20 new integration tests created
- ✅ mypy catches API mismatches before runtime
- ✅ CI/CD pipeline blocks merge of type errors
- ✅ Runtime validation catches legacy module violations
- ✅ Developer workflow documented and tested

---

## Risk Mitigation

### R1: mypy False Positives (Medium)
- **Mitigation**: Incremental rollout (strict on Phase 1-4, lenient on legacy)
- **Contingency**: Use # type: ignore comments sparingly with justification
- **Monitoring**: Track false positive rate, adjust mypy config if >5%

### R2: CI/CD Performance (Medium)
- **Mitigation**: Aggressive caching, scope mypy to src/ only
- **Contingency**: Split checks into parallel jobs if >2min
- **Monitoring**: Track execution time, optimize if approaching limit

### R3: Integration Test Brittleness (High)
- **Mitigation**: Focus on behavioral outcomes, not implementation details
- **Contingency**: Use test helpers to isolate brittleness
- **Monitoring**: Track test flakiness, refactor if >2% failure rate

### R4: Developer Adoption (Medium)
- **Mitigation**: Comprehensive documentation, clear examples
- **Contingency**: Provide bypass options (--no-verify) for WIP
- **Monitoring**: Collect developer feedback, iterate on workflow

### R5: Runtime Validation Overhead (Low)
- **Mitigation**: Benchmark overhead, target <100ms
- **Contingency**: Make runtime validation optional via config flag
- **Monitoring**: Measure initialization time, disable if >100ms impact

---

## Notes

### Gemini 2.5 Pro Audit Recommendations Incorporated
1. ✅ Use typing.Protocol instead of abc.ABC (structural typing)
2. ✅ Add @runtime_checkable decorator to all Protocols
3. ✅ Implement runtime validation at module boundaries (Layer 3.5)
4. ✅ Enhanced Protocol docstrings with behavioral contracts
5. ✅ Integration tests focus on outcomes, not just interface calls
6. ✅ Optimized mypy.ini with check_untyped_defs = False
7. ✅ Optimized pre-commit config with files: ^src/
8. ✅ Corrected "Design ABCs" typo to "Design Protocols"

### Testing Philosophy
- **Focus**: Critical interactions over raw LOC coverage %
- **Approach**: Behavioral validation (outcomes and state changes)
- **Priority**: Main success flow → Critical failures → Edge cases
- **Target**: 80% critical interaction coverage (not raw coverage)

### Performance Targets
- **mypy execution**: <30s for full check
- **Pre-commit hook**: <10s (target: 5s)
- **GitHub Actions**: <2min total
- **Runtime validation**: <100ms overhead
- **Integration tests**: <1min total execution

### Maintenance Considerations
- Protocols are less invasive than ABCs (structural typing)
- Gradual typing allows legacy code to coexist
- Pre-commit hooks are optional (can bypass for WIP)
- Runtime validation is scoped to boundaries only
- Integration tests will require maintenance as system evolves

---

## TDD Cycle Summary

### Complete TDD Workflow for Phase 5

This section provides a comprehensive overview of how TDD principles are applied throughout Phase 5 implementation.

### Phase-by-Phase TDD Application

#### Phase 5A: CI/CD Pipeline (Infrastructure TDD)
**TDD Approach**: Configuration-as-Code with Validation Tests

```
📊 BASELINE (0.5h):
   - Document current mypy errors (expect 0 on Phase 1-4)
   - Capture current test execution time
   ↓
🔴 RED (0.5h):
   - Create failing test: mypy_detects_known_api_mismatches()
   - Test expects mypy to catch .get_champion() vs .champion confusion
   - Run: EXPECT test to FAIL (mypy.ini doesn't exist yet)
   ↓
🟢 GREEN (1h):
   - Create mypy.ini with minimal configuration
   - Run test: EXPECT test to PASS (mypy catches known errors)
   ↓
🔵 REFACTOR (0.5h):
   - Optimize mypy.ini (gradual typing, performance)
   - Add detailed comments and documentation
   - Run test: EXPECT test STILL PASSES
```

**Coverage Impact**: CI/CD infrastructure, not code coverage

---

#### Phase 5B: Interface Contracts (Pure TDD)
**TDD Approach**: Test-First Protocol Design

```
📊 BASELINE (0.5h):
   - Run: pytest --cov=src/learning (document: 111/111 tests, X% coverage)
   - Identify existing implementations (ChampionTracker, IterationHistory, ErrorClassifier)
   ↓
🔴 RED - Protocol Compliance (1h):
   - Create: tests/learning/test_protocol_compliance.py
   - Write 3 failing tests:
     * test_champion_tracker_implements_ichampiontracker()
     * test_iteration_history_implements_iiterationhistory()
     * test_error_classifier_implements_ierrorclassifier()
   - Run: pytest test_protocol_compliance.py
   - EXPECT: ImportError (IChampionTracker not found) ← DESIRED FAILURE
   ↓
🟢 GREEN - Minimal Protocols (1h):
   - Create: src/learning/interfaces.py
   - Define 3 minimal @runtime_checkable Protocols:
     * IChampionTracker (champion property, update_champion method)
     * IIterationHistory (save, get_all, get_by_iteration methods)
     * IErrorClassifier (classify_error method)
   - Run: pytest test_protocol_compliance.py
   - EXPECT: 3/3 tests PASS ← SUCCESS (isinstance() validates structural typing)
   ↓
🔵 REFACTOR - Behavioral Contracts (1h):
   - Enhance Protocol docstrings:
     * Add behavioral contracts (idempotency, referential stability)
     * Add pre/post conditions
     * Add usage examples
   - Run: pytest test_protocol_compliance.py
   - EXPECT: 3/3 tests STILL PASS ← SAFETY (no behavior change)
   ↓
🔴 RED - Runtime Validation (0.5h):
   - Create: tests/learning/test_runtime_validation.py
   - Write failing tests for validate_protocol_compliance()
   - Run: pytest test_runtime_validation.py
   - EXPECT: ImportError (function doesn't exist) ← DESIRED FAILURE
   ↓
🟢 GREEN - Minimal Validation (0.5h):
   - Create: src/learning/validation.py
   - Implement minimal validate_protocol_compliance()
   - Run: pytest test_runtime_validation.py
   - EXPECT: Tests PASS ← SUCCESS
   ↓
🔵 REFACTOR - Diagnostics (0.5h):
   - Add _get_missing_attrs() helper
   - Enhance error messages with missing attribute lists
   - Run: pytest (all tests)
   - EXPECT: All tests STILL PASS ← SAFETY
```

**Coverage Impact**: +2 new test files, +6 tests minimum

---

#### Phase 5C: Integration Testing (Test-First Integration)
**TDD Approach**: Behavioral Validation Tests

```
📊 BASELINE (0.5h):
   - Run: pytest --cov=src/learning --cov-report=term
   - Document: Current integration test count (before Phase 5C)
   - Document: Current critical interaction coverage baseline
   ↓
🔴 RED - Integration Tests (12h total):
   - Create integration tests BEFORE expecting them to pass:
     * test_champion_tracker_iteration_history_integration()
       - Write test expecting champion saves to trigger history updates
       - Run: EXPECT FAIL (integration not validated yet)
     * test_feedback_generator_uses_correct_apis()
       - Write test expecting .champion property usage (not .get_champion())
       - Run: EXPECT FAIL or PASS (if already correct)
     * test_e2e_iteration_flow()
       - Write test for complete iteration (gen→backtest→save)
       - Run: EXPECT conditional (depends on existing implementation)
   ↓
🟢 GREEN - Fix Violations (if any):
   - If integration tests reveal API mismatches: fix them
   - If tests pass immediately: implementation already correct
   - Run: pytest tests/integration/
   - EXPECT: All integration tests PASS
   ↓
🔵 REFACTOR - Enhance Tests (2h):
   - Add behavioral outcome validation (Gemini recommendation)
   - Add idempotency tests
   - Add edge case coverage
   - Run: pytest (all tests)
   - EXPECT: All tests STILL PASS
   ↓
✅ VALIDATE - Coverage (4h):
   - Run: pytest --cov=src/learning --cov-report=html
   - Measure: Critical interaction coverage
   - EXPECT: ≥80% critical interaction coverage achieved
```

**Coverage Impact**: +20 integration tests minimum, +20% critical interaction coverage

---

### TDD Metrics & Checkpoints

#### Required Checkpoints at Each Phase

| Checkpoint | Measurement | Success Criteria |
|------------|-------------|------------------|
| **Baseline** | Current test count & coverage | Documented before any changes |
| **RED Phase** | Failing test count | ≥1 failing test exists before implementation |
| **GREEN Phase** | Passing test count | New tests pass, old tests still pass |
| **REFACTOR Phase** | Code quality metrics | Tests still pass, quality improved |
| **Final Validation** | Total coverage | Coverage ≥ baseline (never decrease) |

#### Coverage Evolution Expected

```
Baseline (Before Phase 5):
  Unit Tests: 111/111 passing (100%)
  Integration Tests: ~10 (estimated)
  Critical Interaction Coverage: Unknown (baseline)

After Phase 5A:
  Unit Tests: 111/111 passing (maintained)
  Integration Tests: ~10 (maintained)
  Infrastructure Tests: +CI/CD validation

After Phase 5B:
  Unit Tests: 111+6 = 117 passing (Protocol + validation tests)
  Integration Tests: ~10 (maintained)
  Coverage: Maintained or increased

After Phase 5C:
  Unit Tests: 117 passing (maintained)
  Integration Tests: 10+20 = 30 minimum
  Critical Interaction Coverage: ≥80%
  Total Test Count: 147+ tests
```

---

### TDD Anti-Patterns to Avoid

❌ **DON'T**: Write implementation before tests
✅ **DO**: Write failing test first, then implement

❌ **DON'T**: Skip RED phase ("I know it will fail")
✅ **DO**: Run test and confirm it fails for the RIGHT reason

❌ **DON'T**: Write complex implementation in GREEN phase
✅ **DO**: Write minimal code to pass, refactor later

❌ **DON'T**: Skip REFACTOR phase ("It works, ship it")
✅ **DO**: Improve code quality while tests are green

❌ **DON'T**: Let coverage decrease during refactoring
✅ **DO**: Maintain or increase coverage at all times

---

### TDD Validation Checklist

Use this checklist to ensure TDD rigor is maintained:

**Before Starting Any Task**:
- [ ] 📊 Baseline coverage measured and documented
- [ ] Current test count recorded
- [ ] Existing behavior understood

**During RED Phase**:
- [ ] 🔴 Failing test written and committed
- [ ] Test fails for the CORRECT reason (not syntax error)
- [ ] Test clearly documents expected behavior

**During GREEN Phase**:
- [ ] 🟢 Minimal implementation written (no over-engineering)
- [ ] New test passes
- [ ] ALL existing tests still pass (no regressions)

**During REFACTOR Phase**:
- [ ] 🔵 Code quality improved (complexity reduced, duplication removed)
- [ ] ALL tests still pass (behavior unchanged)
- [ ] Coverage maintained or increased

**After Task Completion**:
- [ ] ✅ Final test suite passes (no failures)
- [ ] Coverage ≥ baseline (documented)
- [ ] Commit message references TDD cycle completion

---

### TDD Tools & Commands

**Measure Baseline Coverage**:
```bash
# Before starting any task
pytest tests/learning/ --cov=src/learning --cov-report=term > baseline_coverage.txt
```

**Run Specific Test File (RED/GREEN validation)**:
```bash
# Run only the new test file to verify RED→GREEN transition
pytest tests/learning/test_protocol_compliance.py -v
```

**Run Full Test Suite (REFACTOR validation)**:
```bash
# After refactoring, confirm all tests still pass
pytest tests/learning/ -v
```

**Measure Coverage Increase**:
```bash
# After completing task
pytest tests/learning/ --cov=src/learning --cov-report=html
# Compare to baseline_coverage.txt
```

**Continuous TDD Feedback Loop**:
```bash
# Watch mode for instant feedback
pytest-watch tests/learning/ -- --cov=src/learning
```

---

### Expected TDD Outcomes

By following strict TDD throughout Phase 5:

✅ **Prevented Regressions**:
- All 8 known API errors prevented from re-occurring
- Test suite catches violations before runtime

✅ **Living Documentation**:
- Tests document expected Protocol behavior
- Behavioral contracts serve as executable specs

✅ **Confident Refactoring**:
- Can improve code quality without fear
- Tests provide safety net for changes

✅ **Higher Quality**:
- Simpler implementations (minimal code in GREEN phase)
- Better design (refactoring with test safety)

✅ **Faster Debugging**:
- Tests pinpoint exact failure location
- Clear expected vs actual behavior

---

**Total Time with TDD Rigor**: 57h (was 56h, +1h for TDD discipline = 1.8% overhead for massive quality gain)
