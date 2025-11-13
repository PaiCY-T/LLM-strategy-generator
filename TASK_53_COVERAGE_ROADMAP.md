# Task 53 Coverage Improvement Roadmap
# Dedicated Coverage Sprint Plan

**Document Version**: 1.0
**Created**: 2025-10-19
**Status**: ⚠️ Deferred to Dedicated Sprint
**Current Coverage**: 45% | **Target**: 80%+ | **Gap**: 35%

---

## Executive Summary

Task 53 requires comprehensive test coverage improvements across 4 module categories. Current coverage at 45% (3,010 lines covered out of 5,439 total). Gap analysis complete with clear prioritization strategy. Estimated 8-12 hours for dedicated coverage sprint to achieve 80%+ target.

### Strategic Approach

**Phase 1**: High-impact modules (Repository YAML I/O) - 3-4 hours
**Phase 2**: Validation edge cases - 2-3 hours
**Phase 3**: Feedback rationale generation - 1-2 hours
**Phase 4**: Template error paths - 2-3 hours

**Total**: 8-12 hours dedicated effort

---

## Priority 1: Repository YAML I/O Tests (3-4 hours)

### Critical Module: `hall_of_fame_yaml.py`

**Current**: 0% coverage (0/235 lines)
**Target**: 60%+ coverage
**Impact**: Highest - Core persistence layer

#### Test Coverage Plan

##### 1. Basic YAML Operations (45 min)
```python
def test_save_genome_success():
    """Test successful genome serialization and save"""
    # Create genome
    # Save to YAML
    # Verify file exists
    # Verify YAML structure

def test_load_genome_success():
    """Test successful genome deserialization"""
    # Create YAML file
    # Load genome
    # Verify all fields
    # Verify types

def test_yaml_round_trip():
    """Test save -> load preserves data"""
    # Save genome
    # Load genome
    # Assert equality
```

##### 2. Error Handling (30 min)
```python
def test_save_genome_write_error():
    """Test handling of file write failures"""
    # Mock file I/O failure
    # Verify backup created
    # Verify error logged

def test_load_genome_parse_error():
    """Test handling of invalid YAML"""
    # Create invalid YAML
    # Attempt load
    # Verify graceful error

def test_corrupted_yaml_recovery():
    """Test backup restoration"""
    # Create corrupted file
    # Trigger recovery
    # Verify backup used
```

##### 3. Concurrent Access (30 min)
```python
def test_concurrent_save():
    """Test thread-safe saving"""
    # Create multiple threads
    # Save simultaneously
    # Verify no corruption

def test_atomic_operations():
    """Test atomic file operations"""
    # Verify temp file usage
    # Verify atomic rename
    # Verify no partial writes
```

##### 4. Integration Tests (60 min)
```python
def test_add_strategy_yaml_workflow():
    """End-to-end add strategy workflow"""
    # Create strategy
    # Add to repository
    # Verify YAML created
    # Verify tier classification
    # Verify index updated

def test_query_similar_yaml_integration():
    """Integration test for similarity queries"""
    # Populate repository
    # Query similar strategies
    # Verify YAML reads
    # Verify performance <500ms

def test_archival_yaml_workflow():
    """Test archival with YAML operations"""
    # Populate contenders
    # Trigger archival
    # Verify file moves
    # Verify YAML integrity
```

**Total Lines to Cover**: ~140 lines
**Expected Coverage**: 0% → 60% (+60%)

---

### Supporting Modules

#### `index_manager.py` (13% → 70%)
**Current**: 17/132 lines | **Target**: 92 lines

**Test Plan** (45 min):
```python
def test_build_index():
    """Test index construction"""

def test_update_index_atomic():
    """Test atomic index updates"""

def test_search_by_pattern():
    """Test pattern-based search"""

def test_search_by_metrics():
    """Test metric-based filtering"""

def test_index_corruption_recovery():
    """Test index rebuild on corruption"""
```

#### `maintenance.py` (14% → 70%)
**Current**: 20/146 lines | **Target**: 102 lines

**Test Plan** (45 min):
```python
def test_archive_low_performers():
    """Test archival trigger and execution"""

def test_compress_old_strategies():
    """Test gzip compression"""

def test_cleanup_old_backups():
    """Test backup retention"""

def test_run_all_maintenance():
    """Test orchestrator"""
```

#### `pattern_search.py` (10% → 70%)
**Current**: 12/117 lines | **Target**: 82 lines

**Test Plan** (30 min):
```python
def test_search_by_pattern():
    """Test pattern matching"""

def test_get_common_patterns():
    """Test pattern frequency analysis"""

def test_prioritize_patterns():
    """Test pattern prioritization"""
```

**Estimated Time**: 3-4 hours
**Expected Impact**: Repository coverage 34% → 65% (+31%)

---

## Priority 2: Validation Edge Cases (2-3 hours)

### Critical Modules

#### `turtle_validator.py` (52% → 85%)
**Current**: 55/106 lines | **Target**: 90 lines

**Test Plan** (60 min):
```python
def test_validate_6_layer_architecture_missing_layer():
    """Test error when layer missing"""

def test_validate_interdependencies_ma_short_ge_ma_long():
    """Test MA interdependency violation"""

def test_validate_layer_integrity_insufficient_separation():
    """Test MA separation < 10 periods"""

def test_validate_revenue_weighting_edge_cases():
    """Test n_stocks boundary conditions"""

def test_validate_performance_targets_warnings():
    """Test performance target guidance"""
```

**Lines to Cover**: 35 lines
**Expected Coverage**: 52% → 85% (+33%)

#### `mastiff_validator.py` (55% → 85%)
**Current**: 73/132 lines | **Target**: 112 lines

**Test Plan** (60 min):
```python
def test_contrarian_pattern_missing_condition():
    """Test error when contrarian condition missing"""

def test_concentrated_holdings_violation():
    """Test n_stocks > 10 critical error"""

def test_strict_stop_loss_violation():
    """Test stop_loss < 6% critical error"""

def test_volume_weighting_verification():
    """Test volume weighting logic"""

def test_risk_management_validation():
    """Test position_limit and stop_loss ranges"""
```

**Lines to Cover**: 39 lines
**Expected Coverage**: 55% → 85% (+30%)

#### `validation_logger.py` (15% → 70%)
**Current**: 32/211 lines | **Target**: 148 lines

**Test Plan** (45 min):
```python
def test_log_failure_complete():
    """Test comprehensive failure logging"""

def test_generate_report_formatting():
    """Test report generation"""

def test_statistics_tracking():
    """Test pass rate tracking"""
```

**Lines to Cover**: 116 lines
**Expected Coverage**: 15% → 70% (+55%)

**Estimated Time**: 2-3 hours
**Expected Impact**: Validation coverage 52-55% → 70-85% (+20-30%)

---

## Priority 3: Feedback Rationale Generation (1-2 hours)

### Critical Module: `rationale_generator.py`

**Current**: 54% coverage (124/229 lines)
**Target**: 75% coverage
**Lines to Cover**: 48 lines

#### Test Coverage Plan (60-90 min)

##### 1. Rationale Type Coverage (30 min)
```python
def test_generate_performance_rationale_all_tiers():
    """Test rationale for all 5 performance tiers"""
    # Poor, Archive, Solid, Contender, Champion

def test_generate_exploration_rationale_variations():
    """Test exploration rationale with different avoided lists"""

def test_generate_champion_rationale_no_champion():
    """Test graceful handling when no champion"""

def test_generate_validation_rationale_multiple_errors():
    """Test rationale with mixed error types"""

def test_generate_risk_profile_rationale_all_profiles():
    """Test all risk profile types"""
```

##### 2. Edge Cases (30 min)
```python
def test_performance_tier_boundary_conditions():
    """Test Sharpe ratios at tier boundaries"""

def test_template_descriptions_complete():
    """Verify all templates have descriptions"""

def test_markdown_formatting_consistency():
    """Verify markdown structure"""

def test_rationale_with_missing_metrics():
    """Handle incomplete metric data"""
```

**Expected Coverage**: 54% → 75% (+21%)

### Supporting Module: `loop_integration.py`

**Current**: 64% coverage (72/113 lines)
**Target**: 80% coverage
**Lines to Cover**: 18 lines

#### Test Plan (30 min)
```python
def test_generate_enhanced_feedback_exception_handling():
    """Test all exception paths"""

def test_backward_compatibility_format():
    """Verify existing feedback format preserved"""

def test_template_recommendation_integration():
    """Test full integration workflow"""
```

**Expected Coverage**: 64% → 80% (+16%)

**Estimated Time**: 1-2 hours
**Expected Impact**: Feedback coverage 54-64% → 75-80% (+16-21%)

---

## Priority 4: Template Error Paths (2-3 hours)

### Critical Module: `data_cache.py`

**Current**: 16% coverage (14/86 lines)
**Target**: 70% coverage
**Lines to Cover**: 46 lines

#### Test Coverage Plan (90 min)

##### 1. Cache Operations (30 min)
```python
def test_cache_hit():
    """Test successful cache retrieval"""

def test_cache_miss_lazy_load():
    """Test lazy loading on cache miss"""

def test_preload_all_datasets():
    """Test bulk preloading"""

def test_get_stats():
    """Test cache statistics"""
```

##### 2. Error Handling (30 min)
```python
def test_data_loading_failure():
    """Test graceful handling of load errors"""

def test_invalid_key_error():
    """Test handling of invalid cache keys"""

def test_cache_clear():
    """Test cache invalidation"""
```

##### 3. Performance (30 min)
```python
def test_preload_performance():
    """Verify <10s preload time"""

def test_cache_hit_latency():
    """Verify <1ms cache hit"""

def test_memory_usage():
    """Monitor cache memory footprint"""
```

**Expected Coverage**: 16% → 70% (+54%)

### Supporting Module: `base_template.py`

**Current**: 66% coverage (59/90 lines)
**Target**: 85% coverage
**Lines to Cover**: 17 lines

#### Test Plan (45 min)
```python
def test_validate_params_edge_cases():
    """Test boundary parameter values"""

def test_validate_interdependency_complex():
    """Test complex parameter dependencies"""

def test_get_default_params_all_templates():
    """Verify defaults for all 4 templates"""
```

**Expected Coverage**: 66% → 85% (+19%)

### Supporting Module: `momentum_template.py`

**Current**: 79% coverage (68/86 lines)
**Target**: 90% coverage
**Lines to Cover**: 9 lines

#### Test Plan (30 min)
```python
def test_catalyst_type_earnings():
    """Test earnings catalyst path"""

def test_error_handling_backtest_failure():
    """Test backtest failure handling"""
```

**Expected Coverage**: 79% → 90% (+11%)

**Estimated Time**: 2-3 hours
**Expected Impact**: Template coverage 66-79% → 85-90% (+11-19%)

---

## Coverage Sprint Execution Plan

### Day 1 (4-5 hours)

**Morning Session** (2.5-3 hours)
- ✅ Repository YAML I/O - `hall_of_fame_yaml.py` (2 hours)
- ✅ Index Manager tests (30 min)
- ✅ Maintenance tests (30 min)

**Afternoon Session** (1.5-2 hours)
- ✅ Validation: TurtleValidator (1 hour)
- ✅ Validation: MastiffValidator (30-60 min)

### Day 2 (4-5 hours)

**Morning Session** (2-2.5 hours)
- ✅ Feedback: RationaleGenerator (1-1.5 hours)
- ✅ Feedback: LoopIntegration (30-60 min)

**Afternoon Session** (2-2.5 hours)
- ✅ Templates: DataCache (1.5 hours)
- ✅ Templates: BaseTemplate & MomentumTemplate (1 hour)

### Day 3 (Optional - 2 hours)

**Cleanup Session**
- ✅ Run full coverage report
- ✅ Identify remaining gaps
- ✅ Add missing edge case tests
- ✅ Final verification

---

## Expected Outcomes

### Coverage Improvements

| Module Category | Before | After | Gain |
|----------------|--------|-------|------|
| **Templates** | 66-91% | 85-91% | +4-19% |
| **Repository** | 0-65% | 60-70% | +30-60% |
| **Feedback** | 54-95% | 75-95% | +11-21% |
| **Validation** | 15-99% | 70-99% | +20-55% |
| **OVERALL** | **45%** | **75-80%** | **+30-35%** |

### Quality Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total Coverage | 45% | 75-80% | +30-35% |
| Test Count | 292 | ~450 | +158 tests |
| Lines Covered | 3,010 | 4,080-4,351 | +1,070-1,341 |
| Production Ready | ⚠️ Partial | ✅ Full | Quality Gate Met |

---

## Implementation Guidelines

### Test Writing Best Practices

1. **Arrange-Act-Assert Pattern**
   ```python
   def test_feature():
       # Arrange: Set up test data
       genome = create_test_genome()

       # Act: Execute functionality
       result = repository.add_strategy(genome)

       # Assert: Verify outcomes
       assert result.success is True
       assert os.path.exists(result.file_path)
   ```

2. **Use Fixtures for Common Setup**
   ```python
   @pytest.fixture
   def sample_genome():
       return StrategyGenome(
           genome_id='test_001',
           template_name='TurtleTemplate',
           parameters={'n_stocks': 10},
           sharpe_ratio=1.8
       )
   ```

3. **Mock External Dependencies**
   ```python
   @patch('src.repository.hall_of_fame_yaml.Path.open')
   def test_save_with_io_error(mock_open):
       mock_open.side_effect = IOError("Disk full")
       # Test error handling
   ```

4. **Parameterize for Multiple Scenarios**
   ```python
   @pytest.mark.parametrize("sharpe,expected_tier", [
       (2.5, "champion"),
       (1.8, "contender"),
       (1.2, "solid"),
       (0.8, "archive"),
       (0.3, "poor")
   ])
   def test_performance_tier(sharpe, expected_tier):
       tier = get_performance_tier(sharpe)
       assert tier == expected_tier
   ```

### Coverage Verification

**Run Coverage Report**:
```bash
python3 -m pytest tests/ \
    --cov=src/templates \
    --cov=src/feedback \
    --cov=src/repository \
    --cov=src/validation \
    --cov-report=html \
    --cov-report=term-missing
```

**View HTML Report**:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

**Check Specific Module**:
```bash
python3 -m pytest tests/repository/test_hall_of_fame_yaml.py \
    --cov=src/repository/hall_of_fame_yaml \
    --cov-report=term-missing
```

---

## Success Criteria

### Must Have (P0)
- ✅ Overall coverage ≥75%
- ✅ Repository modules ≥60%
- ✅ Validation modules ≥70%
- ✅ All tests passing
- ✅ No regressions in existing tests

### Should Have (P1)
- ✅ Overall coverage ≥80%
- ✅ Critical modules (YAML I/O) ≥70%
- ✅ Edge case coverage for validators
- ✅ Performance tests for caching

### Nice to Have (P2)
- Integration tests for end-to-end workflows
- Load testing for concurrent access
- Benchmarking for performance baselines
- Mutation testing for test quality

---

## Risk Mitigation

### Potential Issues

1. **Time Overrun**
   - **Risk**: Tests take longer than 8-12 hours
   - **Mitigation**: Focus on P0 modules first, defer P2 items

2. **Mocking Complexity**
   - **Risk**: File I/O mocking becomes complex
   - **Mitigation**: Use `tmp_path` fixture for real file operations

3. **Test Flakiness**
   - **Risk**: Concurrent tests may be flaky
   - **Mitigation**: Use thread-safe test utilities, retry logic

4. **Coverage Tool Limitations**
   - **Risk**: Some code paths hard to test
   - **Mitigation**: Document intentionally untested paths

---

## Post-Sprint Validation

### Verification Checklist

- [ ] Run full test suite (all 450+ tests passing)
- [ ] Generate coverage report (verify ≥75%)
- [ ] Check for test flakiness (run 3 times)
- [ ] Review coverage gaps (document remaining)
- [ ] Update test documentation
- [ ] Commit with message: "test: Add comprehensive coverage for Task 53"

### Documentation Updates

- [ ] Update `docs/architecture/TEMPLATE_SYSTEM_TESTING.md`
- [ ] Add new test examples to `tests/README.md`
- [ ] Document remaining coverage gaps
- [ ] Update CI/CD configuration for coverage thresholds

---

## Conclusion

Task 53 requires dedicated 8-12 hour sprint with clear prioritization strategy. Focus on Repository YAML I/O and Validation edge cases for maximum impact. Expected outcome: 45% → 75-80% coverage, achieving production-ready quality standards.

**Recommendation**: Schedule 2-day sprint with focused morning/afternoon sessions. Use this roadmap as execution guide with clear success criteria and verification steps.

---

**Document Created**: 2025-10-19
**Author**: Claude Code (Sonnet 4.5)
**Status**: Ready for Sprint Planning
**Estimated ROI**: High (Production readiness achieved)
