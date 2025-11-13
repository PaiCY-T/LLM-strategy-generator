# Quality Assurance System - Product Specification

## 1. Product Vision

### 1.1 Executive Summary
Establish a lightweight static type checking system that prevents API contract violations before runtime, eliminating the class of integration errors discovered during Phase 8 E2E testing.

### 1.2 Problem Statement
**The Pain Point**: Phase 8 E2E testing revealed 8 critical API mismatches that caused runtime failures:
- Parameter name mismatches (`file_path` vs `filepath`, `champion` vs `champion_tracker`)
- Method signature errors (`execute_code()` vs `execute()`)
- Missing required parameters (`data`, `sim` not provided)
- Wrong classifier usage (`ErrorClassifier` vs `SuccessClassifier`)
- Deserialization field mismatches

**Root Cause**: Lack of compile-time validation. Python's dynamic typing allowed incompatible interfaces to remain undetected until runtime.

**Business Impact**:
- 1 full day spent debugging 8 preventable errors
- Risk of regression when code evolves
- Reduced confidence in autonomous system reliability
- Manual testing burden for every refactoring

### 1.3 Solution
A three-layer type safety system:

```
Layer 1: Type Hints
  └─> Function signature annotations (minimal overhead)

Layer 2: Protocol Interfaces
  └─> Structural type contracts for component boundaries

Layer 3: Static Analysis + CI
  └─> mypy enforcement + GitHub Actions automation
```

**Key Differentiator**: Gradual, non-invasive adoption without refactoring existing code.

## 2. Target User

### 2.1 Primary User
**Personal Trading System Developer** (Individual developer, not team)

**Characteristics**:
- Solo developer maintaining autonomous trading system
- Weekly/monthly trading cycles (not high-frequency)
- Values system reliability over rapid feature delivery
- Prefers evidence-based, engineering-driven approach
- Explicitly wants to avoid over-engineering

**Quote**: "這是個專給我個人使用，交易週期為週/月的交易系統，請勿過度工程化"

### 2.2 User Journey (Current vs Future)

**Current State (Before QA System)**:
```
1. Make code changes (refactoring, new features)
2. Run unit tests → All pass ✓
3. Commit and deploy
4. System runs autonomously
5. ERROR: Runtime failure from API mismatch
6. Debug for hours → Find parameter name typo
7. Fix and redeploy
8. Repeat cycle for next integration error
```

**Future State (After QA System)**:
```
1. Make code changes (refactoring, new features)
2. Save file → mypy runs in IDE
3. ERROR: Type mismatch detected immediately
4. Fix parameter name → mypy clears
5. Run unit tests → All pass ✓
6. Commit → CI runs mypy + E2E tests
7. All checks pass → Confident deployment
8. System runs autonomously without surprises
```

**Time Saved**: Hours of debugging → Seconds of fixing at development time

## 3. Value Proposition

### 3.1 Core Benefits

**1. Shift Errors Left (Runtime → Development Time)**
- Catch API mismatches when typing code
- Immediate feedback in IDE (< 1 second)
- Zero runtime surprises

**2. Refactoring Confidence**
- Change a function signature → mypy finds all call sites
- No more "I hope I didn't break anything"
- Safe evolution of autonomous system components

**3. Documentation as Code**
- Type hints serve as inline API documentation
- Protocol interfaces document component contracts
- Self-documenting codebase

**4. Regression Prevention**
- Phase 8's 8 errors can never happen again
- CI enforces type safety on every commit
- Automatic validation, zero manual effort

**5. Minimal Overhead**
- No runtime cost (type hints are comments)
- No new dependencies in production
- No code refactoring required (gradual adoption)

### 3.2 Return on Investment

**Investment**: 2-3 days development time
- Day 1: Protocol interfaces + mypy config
- Day 2: Type hints for public APIs
- Day 3: GitHub Actions CI setup

**Payoff**: Eliminates entire class of bugs
- Phase 8 debugging time saved: 1 day (immediate ROI)
- Future debugging time saved: ~2-4 hours per iteration
- Confidence in autonomous operation: Priceless

**Break-even**: After 1-2 refactoring cycles

## 4. Success Metrics

### 4.1 Primary Success Metric
**Zero API Contract Violations in CI**: mypy reports 0 errors on all commits

**Target**:
- Week 1: mypy passing on core modules (learning/, backtest/, repository/)
- Week 2: mypy passing on entire codebase
- Ongoing: 100% CI pass rate for type checks

### 4.2 Secondary Success Metrics

**Development Velocity**:
- Refactoring time reduced by 30% (less debugging)
- IDE autocomplete accuracy > 90% (better type inference)
- Code review time reduced (type contracts explicit)

**System Reliability**:
- Runtime TypeErrors: Target 0 (from 8 in Phase 8)
- AttributeErrors from API misuse: Target 0
- Integration test failures from type issues: Target 0

**Code Quality**:
- Public API type coverage: Target 100%
- Protocol interface documentation: 8 key interfaces defined
- mypy strictness level: Normal (not strict, to avoid over-engineering)

### 4.3 User Satisfaction Metrics

**Developer Experience**:
- Time to detect API error: < 1 second (in IDE) vs hours (in runtime)
- Confidence deploying after refactoring: High (vs Low)
- Cognitive load understanding component contracts: Low (explicit types) vs High (read code)

## 5. Key Features

### 5.1 Feature 1: Static Type Checking with mypy

**What**: Python static type analyzer that validates code without running it

**Why**: Catch type errors at development time, not runtime

**Value**: Immediate feedback, zero overhead

**User Interaction**:
```bash
# Run manually during development
mypy src/learning/ src/backtest/ src/repository/

# Automatic in CI on every commit
# (GitHub Actions runs mypy)
```

**Success Criteria**:
- [ ] mypy configured with appropriate strictness
- [ ] 0 errors on target modules
- [ ] Integrated into development workflow

---

### 5.2 Feature 2: Protocol Interfaces for Component Boundaries

**What**: Structural type interfaces using Python Protocol (PEP 544)

**Why**: Document component contracts without tight coupling

**Value**: Clear API contracts, structural typing (duck typing with safety)

**Example**:
```python
# src/interfaces.py

from typing import Protocol

class HistoryProvider(Protocol):
    """Contract for components that provide iteration history"""
    def save(self, record: IterationRecord) -> None: ...
    def load_all(self) -> list[IterationRecord]: ...
    def get_champion(self) -> IterationRecord | None: ...

class BacktestExecutor(Protocol):
    """Contract for strategy backtesting components"""
    def execute(self, strategy_code: str, data: pd.DataFrame) -> BacktestResult: ...
```

**User Benefit**: Know exactly what methods a component needs without reading implementation

**Success Criteria**:
- [ ] 8 key Protocol interfaces defined
- [ ] All public APIs use Protocol types
- [ ] Documentation generated from interfaces

---

### 5.3 Feature 3: Type Hints on Public APIs

**What**: Python type annotations on function signatures

**Why**: Enable mypy validation and IDE autocomplete

**Value**: Self-documenting code, compiler-enforced correctness

**Coverage Target**: Public APIs only (80/20 principle)
- Learning system components (5 modules)
- Backtest executor
- Repository/Hall of Fame
- Feedback generator

**Not Covered** (to avoid over-engineering):
- Private helper functions
- Test code (already validated by pytest)
- One-off scripts

**Success Criteria**:
- [ ] 100% public API type coverage
- [ ] Type hints match actual usage
- [ ] mypy validates all call sites

---

### 5.4 Feature 4: GitHub Actions CI Integration

**What**: Automated type checking on every commit/PR

**Why**: Enforce type safety without manual intervention

**Value**: Prevent regressions, maintain quality automatically

**Workflow**:
```yaml
# .github/workflows/type-check.yml

name: Type Safety
on: [push, pull_request]

jobs:
  mypy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install mypy
      - run: mypy src/learning/ src/backtest/ src/repository/

  e2e-smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pytest tests/integration/test_phase8_e2e_smoke.py
```

**User Experience**:
- Commit code → CI runs automatically
- View results in GitHub PR checks
- Merge only when all checks pass

**Success Criteria**:
- [ ] CI runs on every commit
- [ ] E2E smoke tests included
- [ ] Clear error messages when checks fail

---

### 5.5 Feature 5: E2E Smoke Test Suite

**What**: Fast integration tests validating Phase 8 scenarios

**Why**: Catch the 8 specific errors that occurred in Phase 8

**Value**: Regression prevention, confidence in deployment

**Test Coverage**:
1. Parameter name consistency (file_path/filepath)
2. Method signature correctness (execute vs execute_code)
3. Required parameters present
4. Correct classifier usage
5. Deserialization compatibility

**Execution Time**: < 10 seconds (smoke tests only, not full E2E)

**Success Criteria**:
- [ ] All 8 Phase 8 errors have corresponding tests
- [ ] Tests fail if API contracts violated
- [ ] Integrated into CI pipeline

## 6. Non-Goals (Explicitly Out of Scope)

### 6.1 What We're NOT Building

**Strict Type Checking**:
- NO mypy `--strict` mode (too invasive)
- NO type stubs for third-party libraries
- NO exhaustive type coverage (focus on public APIs only)

**Advanced Type Features**:
- NO generics/TypeVar usage (unless necessary)
- NO complex type narrowing
- NO type guards (keep it simple)

**Runtime Type Validation**:
- NO pydantic models (adds dependency)
- NO runtime type checking (performance overhead)
- NO marshmallow schemas (not needed)

**Comprehensive CI Pipeline**:
- NO code coverage enforcement in CI (already done locally)
- NO linting enforcement (already using flake8)
- NO security scanning (out of scope)

**Documentation Generation**:
- NO Sphinx/MkDocs setup (manual docs sufficient)
- NO API reference generation (type hints are the docs)

### 6.2 Why These Are Out of Scope

**Principle**: 避免過度工程化 (Avoid Over-Engineering)

**Rationale**:
- Personal project, not enterprise team
- Weekly/monthly trading cycles (not mission-critical uptime)
- Solo developer (no onboarding needs)
- Focus on value: prevent Phase 8 errors, not build perfect type system

## 7. Design Principles

### 7.1 Gradual, Non-Invasive Adoption

**Principle**: Add types incrementally without refactoring existing code

**Implementation**:
- Start with Protocol interfaces (zero code changes)
- Add type hints file-by-file (non-breaking)
- Run mypy in parallel (doesn't block development)
- Enable stricter checks over time (gradual)

**Anti-Pattern to Avoid**: "Big bang" type migration that refactors entire codebase

---

### 7.2 Focus on Public APIs (80/20 Rule)

**Principle**: Type the 20% of code that provides 80% of value

**Target**:
- Public module interfaces (learning system, backtest executor)
- Component boundaries (Protocol contracts)
- Integration points (where Phase 8 errors occurred)

**Explicitly Not Typed**:
- Private helper functions
- Internal utilities
- Test code (already validated)

**Benefit**: Maximum safety with minimum effort

---

### 7.3 Developer Experience First

**Principle**: Types should help, not hinder

**Guidelines**:
- Use `Optional` instead of `Union[T, None]` (more readable)
- Prefer simple types over complex generics
- Add type comments when mypy struggles (pragmatic)
- Ignore types when necessary (`# type: ignore` is acceptable)

**Success Measure**: Developer happily uses types, not fights them

---

### 7.4 Zero Runtime Overhead

**Principle**: Type hints are development-time only

**Implementation**:
- Type hints are comments (no runtime interpretation)
- No runtime validation libraries (pydantic, marshmallow)
- No performance impact on autonomous system
- Type checking happens in CI/IDE, not production

**Guarantee**: Production system runs at same speed as before

## 8. Technical Constraints

### 8.1 Environment Constraints

**Python Version**: 3.10+ required
- PEP 544 Protocol support
- Modern type hint syntax (Union, Optional, etc.)
- Current project already on Python 3.10+

**Dependencies**:
- Development: mypy ≥ 1.18.0
- Production: Zero new dependencies
- CI: GitHub Actions (already available)

**Compatibility**:
- Must work with existing codebase (no refactoring)
- Must integrate with pytest (926 existing tests)
- Must respect project structure (src/ layout)

### 8.2 Timeline Constraints

**Total Time Budget**: 2-3 days

**Breakdown**:
- Day 1: Protocol interfaces + mypy config (4-6 hours)
- Day 2: Type hints on public APIs (6-8 hours)
- Day 3: CI integration + smoke tests (4-6 hours)

**Constraint**: Must be completed without blocking other development

**Strategy**: Work in isolated branch, merge when fully validated

### 8.3 Quality Constraints

**Mypy Pass Rate**: 100% on target modules
- No compromises on type safety
- Address all mypy errors (no suppressions without justification)

**Test Pass Rate**: 100% (926 existing tests + new smoke tests)
- Type hints must not break existing tests
- New smoke tests must all pass

**Code Coverage**: Maintain > 80%
- Adding types should not reduce coverage
- Smoke tests should increase coverage if anything

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| mypy reports too many false positives | Medium | High | Start with lenient config, tighten gradually |
| Type hints break existing code | Low | High | Add types in separate commits, test thoroughly |
| Third-party libraries lack type stubs | Medium | Medium | Use `# type: ignore` pragmatically |
| CI slowdown from mypy execution | Low | Low | mypy is fast (< 10 seconds on this codebase) |

### 9.2 Adoption Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Developer finds types annoying | Medium | Medium | Keep types simple, pragmatic over perfect |
| Types become outdated | Low | Medium | CI enforces correctness on every commit |
| Over-engineering creep | Medium | High | Explicit non-goals section, stick to 80/20 |

### 9.3 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Takes longer than 3 days | Medium | Low | Acceptable, quality over speed |
| Blocks other development | Low | Medium | Work in branch, merge when complete |
| Doesn't prevent future bugs | Low | High | Smoke tests validate effectiveness |

## 10. Success Criteria Summary

### 10.1 Minimum Viable Success

**Must Have** (Required for approval):
- [ ] mypy passes on learning/, backtest/, repository/ modules
- [ ] 8 Protocol interfaces defined and documented
- [ ] GitHub Actions CI runs mypy on every commit
- [ ] Phase 8's 8 errors have smoke test coverage
- [ ] Zero regressions in existing 926 tests

**Outcome**: Type safety established, Phase 8 errors prevented

### 10.2 Target Success

**Should Have** (Desired outcomes):
- [ ] 100% public API type hint coverage
- [ ] IDE autocomplete working perfectly
- [ ] Developer can refactor confidently
- [ ] CI catches type errors before merge
- [ ] < 5 `# type: ignore` suppressions

**Outcome**: Smooth developer experience, high confidence

### 10.3 Stretch Success

**Nice to Have** (Bonus achievements):
- [ ] mypy strictness increased to higher level
- [ ] Type coverage expanded to internal functions
- [ ] Documentation generated from type hints
- [ ] Type-driven refactoring opportunities identified

**Outcome**: World-class type safety for personal project

## 11. Appendix

### 11.1 Related Documents

- **Requirements**: `requirements.md` - Detailed requirements and acceptance criteria
- **Design**: `design.md` - Technical architecture and implementation plan
- **Tasks**: `tasks.md` - Step-by-step implementation guide

### 11.2 References

**Python Type System**:
- PEP 484: Type Hints
- PEP 544: Protocol (Structural Subtyping)
- PEP 586: Literal Types
- mypy documentation: https://mypy.readthedocs.io/

**Project Context**:
- Phase 8 E2E Testing Results (revealed 8 API errors)
- Phase 3-6 Refactoring (2,807 lines → 8 modules)
- Current Test Suite (926 tests, >80% coverage)

### 11.3 Key Terminology

- **Type Hints**: Annotations on function signatures (e.g., `def foo(x: int) -> str`)
- **Protocol**: Structural type interface (duck typing with static checking)
- **Static Type Checking**: Analyzing code without running it (mypy)
- **API Contract**: Agreement on function signatures and behavior
- **Gradual Typing**: Incrementally adding types to existing codebase
- **Structural Typing**: Type compatibility based on structure, not inheritance

### 11.4 Version History

- **v1.0.0** (2025-11-06): Initial product specification
  - Defined vision and value proposition
  - Established success metrics and non-goals
  - Documented design principles and constraints
