# P2.2.3 - Regime-Aware E2E Tests Analysis & Design

**Task**: P2.2.3 - Implement regime-aware E2E tests
**Estimate**: 4-5h
**Status**: READY TO IMPLEMENT
**Date**: 2025-11-15

## 1. Research Findings

### 1.1 Regime Detection Infrastructure (✅ IMPLEMENTED)

**Location**: `src/intelligence/regime_detector.py`

**Components Found**:
- ✅ `MarketRegime` enum with 4 regimes:
  - BULL_CALM: Uptrend + low volatility
  - BULL_VOLATILE: Uptrend + high volatility
  - BEAR_CALM: Downtrend + low volatility
  - BEAR_VOLATILE: Downtrend + high volatility

- ✅ `RegimeDetector` class:
  - Trend detection: SMA(50) vs SMA(200) crossover
  - Volatility detection: Annualized volatility vs 20% threshold
  - `detect_regime()`: Returns MarketRegime enum
  - `get_regime_stats()`: Returns detailed RegimeStats with confidence scores

- ✅ `RegimeStats` dataclass:
  - regime: MarketRegime
  - trend_direction: "bullish" or "bearish"
  - volatility_level: "calm" or "volatile"
  - annualized_volatility: float (0-1 scale)
  - sma_50, sma_200: Moving average values
  - confidence: float (0-1) based on data quality

### 1.2 Existing Test Coverage

**Unit Tests** (✅ PASSING):
- Location: `tests/unit/test_regime_detector.py`
- Coverage: 11 tests covering all 4 regimes, edge cases, accuracy requirements
- Status: GREEN - All tests passing

**Integration Tests** (✅ PASSING):
- Location: `tests/integration/test_regime_aware.py`
- Coverage: 4 tests for regime-aware strategy integration
- Key Tests:
  - `test_regime_aware_improves_performance_bull_market()`
  - `test_regime_aware_improves_performance_bear_market()`
  - `test_regime_aware_improves_performance_mixed_market()`
  - `test_regime_detector_integrates_with_strategy()`

**E2E Infrastructure** (✅ READY):
- Location: `tests/e2e/conftest.py`
- Fixtures available:
  - `market_data`: 756 days (3 years), 100 stocks
  - `test_environment`: Mock configuration
  - `validation_thresholds`: Performance gates

### 1.3 Gap Analysis

**What's Missing for E2E**:
1. ❌ No `tests/e2e/test_regime.py` (task requirement)
2. ❌ No end-to-end workflow test integrating:
   - Market data loading
   - Regime detection
   - Strategy selection based on regime
   - Performance validation across regime changes
3. ❌ No test for complete workflow: Data → Regime → Strategy → Backtest → Validation

**What's Already Working**:
- ✅ Regime detection algorithm (unit tested)
- ✅ Regime-aware strategy integration (integration tested)
- ✅ E2E test infrastructure (fixtures, thresholds)
- ✅ Mock framework for fast E2E tests

## 2. Design Decisions

### 2.1 Test Scope

Based on the task requirements and existing infrastructure, P2.2.3 should test:

1. **Complete Regime-Aware Workflow** (PRIMARY):
   - Load market data → Detect regime → Select strategy → Execute → Validate
   - Test regime transitions (bull→bear, calm→volatile)
   - Verify strategy adaptation improves performance

2. **Regime Detection Accuracy in E2E Context**:
   - Test regime detection with realistic market data
   - Verify detection latency < 100ms (Gate 7)
   - Verify detection stability (no rapid flipping)

3. **Multi-Regime Strategy Performance**:
   - Test strategy performance across all 4 regimes
   - Verify regime-aware strategies outperform regime-agnostic baseline
   - Verify OOS tolerance ±20% (Gate 5)

### 2.2 Test Strategy

**Follow existing E2E patterns from `test_evolution.py`**:
- ✅ Use `@pytest.mark.e2e` marker
- ✅ Use shared fixtures: `market_data`, `test_environment`, `validation_thresholds`
- ✅ Mock LLM calls for deterministic tests
- ✅ Use realistic backtest execution
- ✅ Target < 5 seconds total execution time

**Key Differences from Integration Tests**:
- Integration tests use `SimpleRegimeAwareStrategy` (test doubles)
- E2E tests should use **real regime detector + real strategy selection logic**
- E2E tests verify **complete system workflow**, not isolated components

### 2.3 Test Design (4-5 Tests)

**Test 1: Regime Detection E2E Workflow** (CORE)
- GIVEN market data with known regime characteristics
- WHEN regime detector runs on real market data
- THEN detect correct regime with high confidence (>0.7)
- VERIFY latency < 100ms (Gate 7)

**Test 2: Regime Transition Handling** (CRITICAL)
- GIVEN market data with regime change (bull→bear at midpoint)
- WHEN strategy adapts to detected regime
- THEN performance improves during regime transition
- VERIFY regime-aware strategy reduces drawdown vs baseline

**Test 3: Multi-Regime Strategy Performance** (VALIDATION)
- GIVEN market data spanning all 4 regimes
- WHEN regime-aware strategy runs complete backtest
- THEN final Sharpe ratio ≥ baseline + 10% improvement
- VERIFY OOS tolerance ±20% (Gate 5)

**Test 4: Regime Detection Stability** (QUALITY)
- GIVEN rolling window regime detection
- WHEN detecting regime over time
- THEN no rapid regime flipping (stability threshold)
- VERIFY consistent regime detection across similar periods

**Test 5: Execution Time Constraint** (PERFORMANCE)
- GIVEN complete regime-aware workflow
- WHEN running regime detection + strategy selection + backtest
- THEN total execution time < 5.0 seconds
- VERIFY meets P2.2 acceptance criteria

## 3. Implementation Plan

### 3.1 File Structure

```
tests/e2e/test_regime.py       # New E2E test file
tests/e2e/conftest.py          # Use existing fixtures
```

### 3.2 Dependencies

**Existing (No new dependencies needed)**:
- `src/intelligence/regime_detector.py` (RegimeDetector, MarketRegime)
- `tests/e2e/conftest.py` (market_data, test_environment, validation_thresholds)
- `pytest` with `@pytest.mark.e2e`

**Mocking Strategy**:
- Mock LLM calls (similar to `test_evolution.py`)
- Use real RegimeDetector (no mocking)
- Use real backtest execution for accuracy

### 3.3 TDD Workflow

**Phase 1: RED** (Write failing tests)
- Create `tests/e2e/test_regime.py`
- Implement all 5 test methods (RED)
- Tests will fail because regime-aware workflow integration incomplete

**Phase 2: GREEN** (Minimal implementation)
- Integrate RegimeDetector with strategy selection
- Implement regime-aware workflow orchestration
- Make all tests pass with minimal code

**Phase 3: REFACTOR** (Improve code quality)
- Extract common patterns
- Optimize performance
- Add documentation
- Verify all tests still pass

### 3.4 Success Criteria

**Functional Requirements**:
- ✅ All 5 tests passing
- ✅ 0% error rate
- ✅ Regime detection accuracy ≥90% (from unit tests)
- ✅ Regime-aware strategy improves performance ≥10%

**Performance Requirements**:
- ✅ Execution time < 5.0 seconds total
- ✅ Regime detection latency < 100ms (Gate 7)
- ✅ OOS tolerance ±20% (Gate 5)

**Quality Requirements**:
- ✅ Follow E2E test patterns from `test_evolution.py`
- ✅ Use existing fixtures (no duplication)
- ✅ Clear docstrings (GIVEN-WHEN-THEN format)
- ✅ Deterministic tests (reproducible results)

## 4. Recommendation

### 4.1 Proceed with Implementation ✅

**Reasons**:
1. ✅ Regime detection infrastructure fully implemented and tested
2. ✅ Integration tests demonstrate regime-aware strategies work
3. ✅ E2E infrastructure ready (fixtures, mocks, patterns)
4. ✅ Clear task requirements in roadmap
5. ✅ Estimated 4-5h is realistic based on existing patterns

**Value Proposition**:
- Tests complete system integration (not just components)
- Validates regime detection improves real-world performance
- Ensures regime-aware workflows meet performance gates
- Provides regression protection for regime detection features

### 4.2 Implementation Approach

**Step 1**: Create `tests/e2e/test_regime.py` following TDD RED phase
**Step 2**: Implement tests based on design (Tests 1-5)
**Step 3**: Run tests (expect failures - RED phase)
**Step 4**: Implement minimal code to make tests pass (GREEN phase)
**Step 5**: Refactor and optimize (REFACTOR phase)
**Step 6**: Verify all acceptance criteria met

### 4.3 Risk Assessment

**Low Risk**:
- ✅ Infrastructure exists and works
- ✅ Pattern established in `test_evolution.py`
- ✅ No external dependencies needed
- ✅ Fast execution with mocking

**Mitigations**:
- Follow existing E2E patterns exactly
- Use proven fixtures and mocks
- Keep tests focused and minimal
- Verify execution time stays < 5s

## 5. Next Steps

**IMMEDIATE**:
1. Create `tests/e2e/test_regime.py` (RED phase)
2. Implement Test 1: Regime Detection E2E Workflow
3. Verify test fails as expected (TDD RED)

**SUBSEQUENT**:
4. Implement Tests 2-5 (all RED)
5. Implement regime-aware workflow integration (GREEN)
6. Verify all tests pass
7. Refactor and optimize
8. Update task status in roadmap

---

**Conclusion**: P2.2.3 is **READY TO IMPLEMENT** with clear requirements, existing infrastructure, and proven patterns. The regime detection system is fully functional, and E2E tests will validate complete system integration. Estimated 4-5h is realistic based on existing E2E test complexity.
