# Week 1 Integration Tests - Quick Reference

## Test Execution

### Run All Integration Tests
```bash
python3 -m pytest tests/learning/test_week1_integration.py -v
```

### Run Specific Test
```bash
# Test 1: ConfigManager + LLMClient
python3 -m pytest tests/learning/test_week1_integration.py::test_config_manager_llm_client_integration -v

# Test 2: LLMClient + AutonomousLoop
python3 -m pytest tests/learning/test_week1_integration.py::test_llm_client_autonomous_loop_integration -v

# Test 3: IterationHistory + AutonomousLoop
python3 -m pytest tests/learning/test_week1_integration.py::test_iteration_history_autonomous_loop_integration -v

# Test 4: Full Week 1 Stack
python3 -m pytest tests/learning/test_week1_integration.py::test_full_week1_stack_integration -v
```

### Run Full Learning Test Suite
```bash
python3 -m pytest tests/learning/ -v
```

### Run with Coverage
```bash
python3 -m pytest tests/learning/test_week1_integration.py --cov=src.learning --cov-report=term-missing
```

---

## Test Summary

### Test Files
- **Integration Tests**: `tests/learning/test_week1_integration.py` (729 lines)
- **Unit Tests**:
  - `tests/learning/test_config_manager.py` (14 tests)
  - `tests/learning/test_llm_client.py` (19 tests)
  - `tests/learning/test_iteration_history.py` (34 tests)

### Total Test Coverage
- **Integration Tests**: 8 tests
- **Unit Tests**: 67 tests
- **Total**: 75 tests
- **Pass Rate**: 100% (75/75 passing)

---

## Integration Test Scenarios

### 1. ConfigManager + LLMClient Integration ✅
**What it tests**: Singleton pattern, zero config duplication
**Key assertions**:
- `client.config is config_manager._config` (no duplication)
- `config_manager.get('llm.provider')` (nested access)

### 2. LLMClient + AutonomousLoop Integration ✅
**What it tests**: LLM client usage in autonomous_loop.py workflow
**Key assertions**:
- `llm_client.is_enabled()` returns True
- `engine = llm_client.get_engine()` returns InnovationEngine
- `llm_client.get_innovation_rate()` returns 0.20

### 3. IterationHistory + AutonomousLoop Integration ✅
**What it tests**: Save/load workflow, persistence, ordering
**Key assertions**:
- `len(recent) == 3` (correct number loaded)
- `recent[0].iteration_num == 3` (newest first)
- Cross-instance persistence verified

### 4. Full Week 1 Stack Integration ✅
**What it tests**: Complete 2-iteration learning workflow
**Key assertions**:
- All modules initialized without errors
- ConfigManager used by LLMClient (no duplication)
- 2 complete iterations executed successfully
- Performance < 2s per iteration

### 5. Edge Cases ✅
- Missing config graceful handling
- Empty history initialization
- Concurrent writes thread safety

---

## Performance Targets

| Test | Target | Actual | Status |
|------|--------|--------|--------|
| Full Stack Integration | <2s per iteration | 0.9s | ✅ 55% faster |
| ConfigManager + LLMClient | <1s | 0.3s | ✅ 70% faster |
| IterationHistory Load | <1s | 0.4s | ✅ 60% faster |
| Concurrent Writes | <1s | 0.3s | ✅ 70% faster |

---

## Integration Points Verified

### ConfigManager
- ✅ Singleton pattern enforcement
- ✅ Used by LLMClient (zero duplication)
- ✅ Nested config access (dot notation)
- ✅ Thread-safe concurrent access

### LLMClient
- ✅ Uses ConfigManager internally
- ✅ InnovationEngine initialization
- ✅ Provider configuration
- ✅ Innovation rate (0.0-1.0)
- ✅ Graceful error handling

### IterationHistory
- ✅ JSONL persistence (append-only)
- ✅ load_recent(N) newest-first ordering
- ✅ get_last_iteration_num() for resumption
- ✅ Cross-instance persistence
- ✅ Thread-safe atomic writes

---

## Common Issues & Solutions

### Issue: Tests fail with "ConfigManager singleton not reset"
**Solution**: The `reset_singletons` fixture should run automatically. If not:
```python
ConfigManager.reset_instance()
```

### Issue: Tests timeout or hang
**Solution**: Check that InnovationEngine is properly mocked:
```python
with patch('src.learning.llm_client.InnovationEngine', return_value=mock_engine):
    # Your test code
```

### Issue: History file conflicts between tests
**Solution**: Use `tmp_path` fixture for isolated test directories:
```python
def test_something(tmp_path):
    history_path = tmp_path / "test_history.jsonl"
    history = IterationHistory(str(history_path))
```

---

## Adding New Integration Tests

### Template
```python
def test_new_integration(test_config_path, test_history_path, mock_innovation_engine):
    """Describe what integration you're testing.

    Success Criteria:
        - Criterion 1
        - Criterion 2
    """
    # Setup
    with patch('src.learning.llm_client.InnovationEngine', return_value=mock_innovation_engine):
        # Test code here
        pass

    # Assertions
    assert condition, "Error message"
```

### Best Practices
1. **Use fixtures**: `test_config_path`, `test_history_path`, `mock_innovation_engine`
2. **Mock external dependencies**: Always mock InnovationEngine
3. **Reset state**: `reset_singletons` fixture runs automatically
4. **Document success criteria**: Clear docstrings with expected outcomes
5. **Performance validation**: Add timing assertions for critical paths

---

## Week 1 Checkpoint Status

### Modules Tested
- ✅ `src/learning/config_manager.py` (ConfigManager)
- ✅ `src/learning/llm_client.py` (LLMClient)
- ✅ `src/learning/iteration_history.py` (IterationHistory)

### Integration Test Results
- **Total Tests**: 8
- **Passing**: 8 (100%)
- **Failing**: 0
- **Performance**: Exceeds targets by 55-70%

### Next Steps
1. **Week 2**: Integrate modules into autonomous_loop.py
2. **Week 3**: Refactor feedback loop
3. **Week 4**: Refactor mutation system

---

## Related Documentation
- **Full Report**: `.spec-workflow/specs/phase3-learning-iteration/INTEGRATION_TEST_REPORT.md`
- **ConfigManager Docs**: `src/learning/config_manager.py` (docstrings)
- **LLMClient Docs**: `src/learning/llm_client.py` (docstrings)
- **IterationHistory Docs**: `src/learning/iteration_history.py` (docstrings)

---

**Last Updated**: 2025-11-03
**Test Suite Version**: Week 1 Integration Tests v1.0
**Status**: ✅ All tests passing
