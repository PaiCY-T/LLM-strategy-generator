# Week 2+ Preparation

**Status**: ✅ Ready to Start
**Last Updated**: 2025-11-04
**Context**: Phase 1 Hardening Complete

## Phase 1 Hardening Complete ✅

**Completion Date**: 2025-11-04
**Results**: 86/87 tests passing, 1 skipped (expected)

### Accomplishments

- ✅ **Golden Master Test**: Behavioral equivalence framework established
- ✅ **JSONL Atomic Write**: Data corruption prevention implemented
- ✅ **Full Test Coverage**: 93% coverage (ConfigManager 98%, LLMClient 86%, IterationHistory 94%)
- ✅ **Zero Regressions**: All tests passing, backward compatible
- ✅ **Documentation**: Comprehensive guides created

### Safety Net in Place

1. **Golden Master Framework**:
   - Structural validation tests (2 passing)
   - Full pipeline test (1 skipped - awaiting real LLM integration)
   - Baseline snapshots for regression detection

2. **Data Integrity**:
   - Atomic writes via temp file + os.replace()
   - Thread-safe file locking
   - Corruption prevention validated

3. **Test Coverage**:
   - 86 tests passing (14 ConfigManager, 19 LLMClient, 43 IterationHistory, 9 atomic, 3 golden master, 8 integration)
   - High coverage (93% overall)
   - Fast execution (96.67s for full suite)

---

## Phase 2: Incremental DI Refactoring (Ongoing)

**Strategy**: Boy Scout Rule
**Status**: Ready to start
**Target**: +5 classes per week

### The Boy Scout Rule

> "Leave the code cleaner than you found it."

**Application**: Every time you modify a class that uses `ConfigManager.get_instance()` or other singletons, spend **15 minutes** refactoring it to use Dependency Injection.

### Why Boy Scout Rule?

**Advantages**:
- ✅ **Low Risk**: Changes are small and incremental
- ✅ **No Big Bang**: Avoid large, risky refactoring efforts
- ✅ **Natural Progression**: Refactor only what you're already modifying
- ✅ **Testable**: Each change is independently verifiable
- ✅ **Sustainable**: Fits within regular development workflow

**Disadvantages**:
- ⏱️ **Slower**: Takes multiple iterations to complete
- 📊 **Incomplete**: System may have mixed DI/Singleton patterns for a while

### Implementation Guidelines

#### 1. Identify Candidates

When you modify a file, check for:
- `ConfigManager.get_instance()` calls
- `LLMClient()` instantiation
- `IterationHistory()` instantiation (if multiple instances needed)
- Other singleton patterns

#### 2. Apply 15-Minute Refactoring

**Before** (Singleton):
```python
class MyClass:
    def __init__(self):
        self.config = ConfigManager.get_instance()
        self.llm = LLMClient()

    def do_something(self):
        setting = self.config.get("some.key", default=True)
        # ...
```

**After** (Dependency Injection):
```python
class MyClass:
    def __init__(self, config: ConfigManager, llm: LLMClient):
        self.config = config
        self.llm = llm

    def do_something(self):
        setting = self.config.get("some.key", default=True)
        # ...
```

**Test Updates**:
```python
def test_my_class():
    # Inject dependencies for testing
    config = ConfigManager.get_instance()
    llm = LLMClient()

    obj = MyClass(config=config, llm=llm)
    # ... test logic
```

#### 3. Document Changes

Add to progress tracking:
```markdown
### DI Refactoring Progress

- [x] ConfigManager extracted (Week 1)
- [x] LLMClient extracted (Week 1)
- [ ] autonomous_loop.py (main entry point)
- [ ] [New module name] (Date)
```

### Progress Tracking

**Week 1 Baseline**:
- ✅ ConfigManager: Extracted, 14 tests
- ✅ LLMClient: Extracted, 19 tests
- ✅ IterationHistory: Enhanced, 43 tests

**Week 2+ Candidates** (to be identified during modifications):
- [ ] `autonomous_loop.py` (main entry point)
- [ ] [Other modules as identified]

**Target**: +5 classes per week

### When to Skip Boy Scout Rule

Skip the 15-minute refactoring if:
1. **Hotfix**: Critical bug fix that can't wait
2. **Time Pressure**: Deadline-driven work
3. **Unclear Design**: Architecture not yet settled
4. **Too Complex**: Refactoring would take >1 hour

In these cases, add a TODO comment:
```python
# TODO: Refactor to use DI (Boy Scout Rule)
config = ConfigManager.get_instance()
```

---

## Phase 3: Strategic Upgrades (Demand-Driven)

**Status**: Not yet needed
**Triggers**: Documented below

### SQLite Migration

**Trigger Conditions** (any one):
1. **Need complex queries** on iteration history
   - Example: "Find all iterations where Sharpe > 2.0 AND max_drawdown < -0.2"
   - JSONL requires loading entire file and filtering in Python

2. **JSONL file exceeds 100MB**
   - Current: ~1KB per iteration × 10,000 iterations = ~10MB
   - 100MB threshold = ~100,000 iterations
   - At 100 iterations/day × 7 days = 700/week, this is **20+ weeks away**

3. **Concurrent multi-process writes required**
   - Current: Single-process learning loop
   - Future: Parallel population evolution across multiple processes
   - Not needed until parallel backtesting implemented

**Implementation Approach**:
1. Create `src/learning/sqlite_history.py` with same API as `IterationHistory`
2. Implement migration script: `scripts/migrate_jsonl_to_sqlite.py`
3. Update tests to work with both backends
4. Gradual rollout with feature flag

**Estimated Effort**: 2-3 days (16-24 hours)

### Full DI Refactoring

**Trigger Conditions** (any one):
1. **Need parallel backtesting capabilities**
   - Example: Run 10 strategies in parallel across 10 processes
   - Requires injectable, independent components

2. **Boy Scout Rule coverage exceeds 50%**
   - 50% of classes already refactored to DI
   - Remaining 50% would benefit from consistency

3. **Singleton-related bugs become frequent**
   - State pollution across tests
   - Difficult-to-debug initialization issues
   - Thread safety problems

**Implementation Approach**:
1. Complete remaining Boy Scout Rule refactorings
2. Refactor main entry point (`autonomous_loop.py`) to use DI
3. Create dependency injection container (e.g., using `dependency-injector`)
4. Update all tests to use DI patterns
5. Remove singleton patterns entirely

**Estimated Effort**: 1-2 weeks (40-80 hours)

---

## Immediate Next Steps (Week 2+)

### 1. Continue Regular Development

**Focus**: Build features, fix bugs, improve system
**Strategy**: Apply Boy Scout Rule when modifying singleton-based code
**Target**: +5 classes refactored per week (passive)

### 2. Monitor Metrics

**JSONL File Size**:
```bash
# Check current size
ls -lh artifacts/data/innovations.jsonl

# Set alert at 50MB (50% of 100MB threshold)
if [ $(stat -c%s artifacts/data/innovations.jsonl) -gt 52428800 ]; then
    echo "⚠️ JSONL file exceeds 50MB - consider SQLite migration"
fi
```

**DI Coverage**:
- Track number of classes refactored
- Calculate percentage: (DI classes / Total classes) × 100%
- Alert at 40% (approaching 50% threshold)

**Singleton Bug Frequency**:
- Track singleton-related issues
- If >2 bugs per month, consider full DI refactoring

### 3. Maintain Documentation

**Update Weekly**:
- `WEEK2_PREPARATION.md` (this document)
- `tasks.md` (progress tracking)
- Boy Scout Rule refactoring log

**Update on Demand**:
- `README.md` (when significant milestones reached)
- Architecture docs (when design changes)

---

## Success Criteria

### Phase 2 Success (Boy Scout Rule)

- ✅ +5 classes refactored per week (on average)
- ✅ DI coverage increases steadily
- ✅ Zero breaking changes
- ✅ Test coverage maintained >90%
- ✅ Documentation kept up to date

### Phase 3 Trigger Assessment

**Monthly Check** (assess whether triggers are met):
- [ ] JSONL file size > 50MB? (No = continue JSONL)
- [ ] DI coverage > 40%? (No = continue Boy Scout Rule)
- [ ] Singleton bugs > 2/month? (No = continue current approach)
- [ ] Need parallel backtesting? (No = continue single-process)

If all answers are "No", continue with current approach.

---

## Risk Mitigation

### Potential Risks

1. **Boy Scout Rule Ignored**:
   - **Risk**: Team forgets to apply 15-minute refactoring
   - **Mitigation**: Add to code review checklist

2. **Inconsistent DI Patterns**:
   - **Risk**: Some classes use DI, others use singletons
   - **Mitigation**: Document standard DI patterns in this file

3. **Testing Overhead**:
   - **Risk**: DI requires more test setup code
   - **Mitigation**: Create test utility functions for dependency creation

4. **Performance Regression**:
   - **Risk**: DI introduces overhead
   - **Mitigation**: Benchmark critical paths, use Golden Master tests

### Monitoring

**Weekly**:
- Review Boy Scout Rule progress
- Check test coverage metrics
- Verify zero regressions

**Monthly**:
- Assess Phase 3 trigger conditions
- Review DI coverage percentage
- Plan next month's focus areas

---

## Resources

### Documentation

- **Week 1 Plan**: [WEEK1_REFACTORING_PLAN.md](./WEEK1_REFACTORING_PLAN.md)
- **Hardening Plan**: [WEEK1_HARDENING_PLAN.md](./WEEK1_HARDENING_PLAN.md)
- **Week 1 Summary**: [WEEK1_COMPLETE_WITH_HARDENING.md](./WEEK1_COMPLETE_WITH_HARDENING.md)
- **Tasks Dashboard**: [tasks.md](./tasks.md)

### Testing

- **Golden Master Tests**: `tests/learning/test_golden_master_deterministic.py`
- **Integration Tests**: `tests/learning/test_week1_integration.py`
- **Coverage Reports**: `pytest tests/learning/ --cov=src/learning --cov-report=term-missing`

### Example Refactorings

**ConfigManager Extraction** (Week 1):
- Before: Inline YAML loading in `autonomous_loop.py`
- After: Extracted to `src/learning/config_manager.py`
- Tests: 14 tests, 98% coverage

**LLMClient Extraction** (Week 1):
- Before: Inline LiteLLM initialization in `autonomous_loop.py`
- After: Extracted to `src/learning/llm_client.py`
- Tests: 19 tests, 86% coverage

---

## Questions & Answers

### Q1: When should I apply the Boy Scout Rule?

**A**: Every time you modify a file that uses singletons. Set a 15-minute timer and refactor during that time. If you can't finish in 15 minutes, revert and add a TODO comment.

### Q2: What if I'm working on a hotfix?

**A**: Skip the Boy Scout Rule for hotfixes. Add a TODO comment and come back to it later during regular maintenance.

### Q3: How do I know if I should migrate to SQLite?

**A**: Check the three trigger conditions monthly. If any one is met, plan the migration. Current estimate: **20+ weeks away**.

### Q4: Should I refactor everything to DI now?

**A**: No. Apply the Boy Scout Rule incrementally. Full DI refactoring is only needed when triggers are met (50% coverage, parallel backtesting, or frequent singleton bugs).

### Q5: How do I track DI coverage?

**A**: Count classes using DI vs. total classes. Update the progress tracking section in this document.

---

## Conclusion

Week 2+ focuses on **incremental improvement** through the Boy Scout Rule, with strategic upgrades triggered by actual needs rather than premature optimization.

**Key Principles**:
1. ✅ **Incremental**: Apply DI during regular development
2. ✅ **Demand-Driven**: Migrate to SQLite or full DI only when needed
3. ✅ **Sustainable**: Maintain test coverage and documentation
4. ✅ **Zero Regressions**: Use Golden Master tests to prevent breakage

**Status**: ✅ Ready to start Week 2+

---

**Document Version**: 1.0
**Last Updated**: 2025-11-04
**Next Review**: Weekly (check Boy Scout Rule progress)
