# Requirements Document

## Introduction

The Quality Assurance System establishes static type checking and continuous integration to prevent API contract violations discovered during Phase 8 E2E testing. This system introduces type safety through Python type hints and Protocol interfaces, enforced by mypy static analysis, with automated validation via GitHub Actions CI.

**Context**: Phase 8 E2E testing revealed 8 critical API mismatches that caused TypeError and AttributeError exceptions at runtime:
- Parameter name mismatches (`file_path` vs `filepath`, `champion` vs `champion_tracker`)
- Method signature errors (`execute_code()` vs `execute()`)
- Missing required parameters (`data`, `sim` not provided)
- Wrong classifier usage (`ErrorClassifier` vs `SuccessClassifier`)
- Deserialization field mismatches

These errors resulted from lack of static type checking—all were preventable through compile-time validation.

**Value Proposition**: This system provides a "safety net" that catches integration errors before runtime, reducing debugging time and preventing regression of fixed issues. The investment (2-3 days) prevents repeated debugging cycles like Phase 8 (1 day to fix 8 errors).

## Alignment with Product Vision

This feature aligns with product.md principles:

1. **避免過度工程化 (Avoid Over-Engineering)**: Minimal configuration, maximum value
   - Uses standard Python tools (mypy, Protocol, GitHub Actions)
   - No custom type stubs or complex infrastructure
   - Focus on public APIs only (80/20 principle)
   - Project principle: "這是個專給我個人使用，交易週期為週/月的交易系統，請勿過度工程化"

2. **System Quality Metrics**: Maintains high code quality standards
   - Current: 926+ tests passing, >80% code coverage
   - Addition: Static type checking layer
   - Integration: E2E tests automated in CI

3. **Autonomous Learning System Reliability**: Prevents system failures
   - Phase 3-6 refactoring (2,807 lines → 8 modules) introduced integration risk
   - Type safety ensures component contracts remain stable
   - Supports long-term autonomous operation without manual intervention

## Requirements

### Requirement 1: Static Type Checking for Public APIs

**User Story:** As a developer, I want static type checking on all public APIs, so that API contract violations are caught at development time rather than runtime.

#### Acceptance Criteria

1. WHEN developer modifies a function signature THEN mypy SHALL detect incompatible call sites before commit
2. WHEN new code is written THEN mypy SHALL validate parameter types match expected interfaces
3. WHEN integration tests run THEN type mismatches SHALL be caught by mypy (0 errors required)
4. IF a component expects `HistoryProvider` interface THEN mypy SHALL verify structural compatibility

**Rationale**: All 8 Phase 8 errors were type mismatches preventable by static checking:
- Fix #1, #2, #6: Parameter/method name mismatches
- Fix #3: Missing parameters
- Fix #4, #5: Wrong types/classes used
- Fix #7, #8: Design/serialization inconsistencies

### Requirement 2: Protocol Interface Definitions

**User Story:** As a developer, I want clear interface contracts via Protocol definitions, so that component dependencies are explicit and type-safe.

#### Acceptance Criteria

1. WHEN defining component interfaces THEN system SHALL use Protocol (PEP 544) for structural typing
2. WHEN components interact THEN they SHALL depend on Protocol interfaces, not concrete implementations
3. IF a component implements a Protocol THEN mypy SHALL verify structural compatibility without inheritance
4. WHEN reviewing code THEN developers SHALL see clear interface contracts in src/interfaces.py

**Key Protocols Required** (from expert analysis):
- `IHistoryRepository`: get_all(), save(), get_recent()
- `IChampionTracker`: get_champion(), update_champion()
- `ILLMClient`: generate(), is_enabled()
- `IBacktestExecutor`: execute() with data/sim parameters
- `IFeedbackGenerator`: generate_feedback() with correct signature

**Rationale**:
- Protocol enables duck typing with type safety (Python philosophy)
- Supports future implementation swaps (e.g., different history backends)
- Documents contracts without coupling to implementations

### Requirement 3: Gradual Type Adoption

**User Story:** As a maintainer, I want gradual type adoption starting with core modules, so that typing can be added incrementally without disrupting development.

#### Acceptance Criteria

1. WHEN configuring mypy THEN system SHALL use lenient base configuration (ignore_missing_imports=True)
2. WHEN core modules are fully typed THEN mypy SHALL enable strict checking per-module
3. IF historical code lacks types THEN mypy SHALL NOT block untyped code initially
4. WHEN adding types THEN implementation SHALL follow dependency order (bottom-up: dependencies → dependents)

**Implementation Order** (from dependency analysis):
- **Tier 1** (底層): IterationHistory, HallOfFameRepository, AntiChurnManager, LLMClient, BacktestExecutor
- **Tier 2** (中層): ChampionTracker, FeedbackGenerator
- **Tier 3** (高層): IterationExecutor, LearningLoop

**Rationale**:
- Avoid "boil the ocean" approach that generates thousands of errors
- Enable immediate value on newly typed code
- Tighten strictness as coverage increases

### Requirement 4: Continuous Integration Automation

**User Story:** As a developer, I want automated type checking and testing on every PR, so that integration errors are caught before merge.

#### Acceptance Criteria

1. WHEN pull request is created THEN GitHub Actions SHALL run mypy type checking automatically
2. WHEN pull request is created THEN GitHub Actions SHALL run E2E smoke tests automatically
3. IF mypy finds type errors THEN PR SHALL be blocked from merging
4. WHEN CI completes THEN feedback SHALL be provided within 5 minutes

**CI Workflow Required**:
- Job 1: Type Check (mypy src/)
- Job 2: E2E Tests (pytest test_phase8_e2e_smoke.py)
- Trigger: On PR to main, on push to main
- Python version: 3.11 (current project standard)

**Rationale**:
- Automates quality checks that were manual in Phase 8
- Prevents regression of fixed errors
- Fast feedback loop (5 minute target)

### Requirement 5: E2E Test Integration

**User Story:** As a developer, I want Phase 8 E2E smoke tests automated in CI, so that critical integration paths are validated on every change.

#### Acceptance Criteria

1. WHEN CI runs THEN test_phase8_e2e_smoke.py SHALL execute all 4 tests
2. IF any E2E test fails THEN CI SHALL fail and block PR merge
3. WHEN tests pass THEN CI SHALL report 4/4 tests passing
4. WHEN E2E tests run THEN they SHALL verify:
   - ChampionTracker initialization with all dependencies
   - update_champion API contract compliance
   - Full system initialization (8 components)
   - Single iteration integration flow

**Test Coverage**:
- Test 1: ChampionTracker receives hall_of_fame, history, anti_churn (Fix #1 verification)
- Test 2: update_champion called with iteration_num, code, metrics only (Fix #2 verification)
- Test 3: All 8 components initialize without errors
- Test 4: Complete iteration executes end-to-end

**Rationale**:
- Existing test_phase8_e2e_smoke.py proved valuable (found 8 errors)
- Should be permanent regression prevention tool
- Validates critical paths that unit tests miss

## Non-Functional Requirements

### Code Architecture and Modularity

- **Single Responsibility Principle**:
  - src/interfaces.py: Protocol definitions only
  - mypy.ini: Configuration only
  - CI workflow: Quality checks only (type + tests)

- **Modular Design**:
  - Type hints added to existing modules (non-invasive)
  - Protocols define interfaces without changing implementations
  - CI workflow isolated in .github/workflows/

- **Dependency Management**:
  - Circular import prevention via src/interfaces.py centralization
  - Type checking dependencies: mypy, pytest (dev dependencies)
  - No new runtime dependencies

- **Clear Interfaces**:
  - Protocol definitions document all component contracts
  - Type hints serve as inline documentation
  - Explicit parameter types and return values

### Performance

- **Type Checking Speed**: mypy src/ SHALL complete in <30 seconds
- **CI Pipeline Speed**: Total CI run time SHALL be <5 minutes
- **Development Impact**: Type checking SHALL NOT slow down edit-test cycle (run on commit, not save)
- **Runtime Impact**: Type hints have ZERO runtime overhead (Python ignores them at runtime)

### Security

- **No New Attack Surface**: Type hints are Python comments (no security impact)
- **CI Token Security**: GitHub Actions secrets for API tokens if needed (not required for this spec)
- **Dependency Security**: mypy and pytest are mature, widely-used tools (minimal risk)

### Reliability

- **Backward Compatibility**: 100% backward compatible with existing code
  - Type hints are optional gradual typing
  - Existing code continues working during transition
  - Forward-compatible: old code can call new typed code

- **Failure Modes**:
  - mypy errors block PR (intentional - prevents bad code)
  - CI failure blocks merge (intentional - quality gate)
  - Graceful degradation: If mypy unavailable, tests still run

- **Migration Safety**:
  - No breaking changes to existing APIs
  - Type annotations only (no logic changes)
  - Phase 8 E2E tests verify no regression

### Usability

- **Developer Experience**:
  - IDE autocomplete improved (VSCode, PyCharm recognize types)
  - Clear error messages from mypy (pinpoint exact mismatch)
  - Self-documenting code (types show expected contracts)

- **Learning Curve**:
  - Python developers familiar with type hints (PEP 484 since 2014)
  - Protocol is standard library (typing.Protocol since Python 3.8)
  - mypy is industry standard (used by Dropbox, Instagram, etc.)

- **Documentation**:
  - Type hints serve as inline API documentation
  - Protocols document interface contracts
  - mypy errors guide towards correct usage

## Success Criteria

1. **Zero mypy Errors**: mypy src/ reports 0 errors on main branch
2. **100% Protocol Coverage**: All 5 core interfaces defined in src/interfaces.py
3. **CI Automation**: GitHub Actions runs type check + E2E tests on every PR
4. **No Phase 8 Regression**: All 8 fixed errors caught by mypy if reintroduced
5. **Fast Feedback**: CI completes in <5 minutes

## Out of Scope

The following are explicitly NOT included in this spec:

1. **100% Type Coverage**: Focus on public APIs only (80/20 principle)
2. **Pre-commit Hooks**: Keep development workflow simple (avoid friction)
3. **Custom Type Stubs**: Use standard library types and third-party stubs
4. **Unit Test Expansion**: E2E tests only (unit tests are separate concern)
5. **Docstring Type Migration**: Keep existing Google-style docstrings (no migration needed)

## Dependencies and Assumptions

**Dependencies**:
- Python 3.10+ (current project requirement)
- mypy ≥1.18.0 (latest stable version)
- pytest ≥8.4.0 (already in requirements-dev.txt)
- GitHub repository with Actions enabled

**Assumptions**:
- Development continues on main branch (GitHub Flow model)
- PR-based code review workflow
- Test suite maintained (926 tests currently passing)
- Type hints will be added incrementally (not all at once)

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Developer resistance to types | Slow adoption | Low | Type hints are optional, gradual adoption, IDE benefits clear |
| mypy false positives | Frustration | Medium | Lenient base config, per-module strictness, can add `# type: ignore` if needed |
| CI slowdown | Longer feedback | Low | Optimize mypy caching, parallel jobs, <5min target |
| Breaking changes during typing | System instability | Very Low | Type hints are pure annotations (no runtime effect), Phase 8 E2E tests catch regressions |

## Future Enhancements

Not in current scope but potential future additions:

1. **Runtime Type Validation**: pydantic models for data validation (separate spec)
2. **Strict Mode Expansion**: Gradually enable strict mode for all modules (ongoing)
3. **Type Coverage Metrics**: Track percentage of typed functions (monitoring)
4. **IDE Integration Guides**: VSCode/PyCharm setup documentation (docs)
5. **Pre-commit Hook (Optional)**: Local type checking before commit (future opt-in)

---

**Document Version**: 1.0
**Status**: Draft - Pending Approval
**Last Updated**: 2025-11-06
**Author**: Development Team
**Reviewers**: TBD
**Related Docs**:
- Phase 8 E2E Test Report (PHASE8_E2E_TEST_REPORT.md)
- Tech Stack (steering/tech.md)
- Project Structure (steering/structure.md)
