# Tasks Document: Comprehensive Improvement Plan (TDD)

## TDD Implementation Protocol

**Red-Green-Refactor Cycle**:
1. **RED**: Write failing test FIRST
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Clean up while maintaining tests

**Task Completion Criteria**:
- [ ] Test written and fails (RED)
- [ ] Implementation passes test (GREEN)
- [ ] Code cleaned up, tests still pass (REFACTOR)
- [ ] pytest coverage ≥ 80%

---

## Phase 1: P0 Critical Bug Fix

- [ ] 1. P0: Write Metrics Contract Tests
  - File: tests/templates/test_momentum_template.py
  - Write failing tests for _extract_metrics() contract
  - Test: execution_success field exists
  - Test: total_return field exists
  - Test: strategy classification not all LEVEL_0
  - Purpose: TDD RED phase - define expected behavior
  - _Leverage: src/templates/momentum_template.py (line 127-132)_
  - _Requirements: 1_
  - _Prompt: Role: TDD Python Developer | Task: Write failing tests for Metrics contract in tests/templates/test_momentum_template.py. Tests must verify _extract_metrics() returns execution_success=True and total_return field. Also verify StrategyMetrics.classify() doesn't return all LEVEL_0. | Restrictions: Tests MUST fail initially (RED phase), do not modify production code yet | Success: pytest tests/templates/test_momentum_template.py shows 3+ failing tests_

- [ ] 2. P0: Implement Metrics Contract Fix
  - File: src/templates/momentum_template.py
  - Fix _extract_metrics() to include execution_success
  - Add total_return field to metrics dict
  - Ensure all 7 required fields present
  - Purpose: TDD GREEN phase - minimal implementation
  - _Leverage: Task 1 failing tests_
  - _Requirements: 1_
  - _Prompt: Role: TDD Python Developer | Task: Modify MomentumTemplate._extract_metrics() in src/templates/momentum_template.py to pass tests from Task 1. Add execution_success: True and total_return fields. | Restrictions: Only add code needed to pass tests, no premature optimization | Success: pytest tests/templates/test_momentum_template.py all pass (GREEN phase)_

- [ ] 3. P0: Refactor Metrics Implementation
  - File: src/templates/momentum_template.py
  - Clean up _extract_metrics() implementation
  - Add docstring with contract specification
  - Extract constants if needed
  - Purpose: TDD REFACTOR phase - improve code quality
  - _Leverage: Task 2 passing tests_
  - _Requirements: 1_
  - _Prompt: Role: TDD Python Developer | Task: Refactor _extract_metrics() in src/templates/momentum_template.py. Add comprehensive docstring, improve readability, ensure all tests still pass. | Restrictions: Do not change behavior, tests must remain green | Success: Code cleaner, pytest still passes, radon cc < 10_

---

## Phase 2: P1 RSI Factor

- [ ] 4. P1-RSI: Write RSI Factor Tests (TDD RED)
  - File: tests/factor_library/test_rsi_factor.py (CREATE)
  - Test: RSI values in [0, 100] range
  - Test: Signal values in [-1.0, 1.0] range
  - Test: Oversold (RSI<30) generates positive signal
  - Test: Overbought (RSI>70) generates negative signal
  - Test: TTPT - no look-ahead bias
  - Purpose: TDD RED phase for RSI factor
  - _Leverage: src/factor_library/registry.py for factor interface_
  - _Requirements: 2_
  - _Prompt: Role: TDD Python Developer specializing in quantitative finance | Task: Create test file tests/factor_library/test_rsi_factor.py with failing tests for RSI factor. Include test_rsi_range_0_to_100(), test_signal_range_neg1_to_1(), test_oversold_positive_signal(), test_overbought_negative_signal(), test_no_lookahead_bias(). Use pytest fixtures with sample DataFrame. | Restrictions: Tests MUST fail, factor does not exist yet | Success: pytest shows 5 failing tests for nonexistent rsi_factor_

- [ ] 5. P1-RSI: Implement RSI Factor (TDD GREEN)
  - File: src/factor_library/mean_reversion_factors.py (CREATE)
  - Implement rsi_factor() using talib.RSI via Finlab
  - Signal mapping: (50-RSI)/50 normalized to [-1, 1]
  - Add to factor registry
  - Purpose: TDD GREEN phase - pass RSI tests
  - _Leverage: Task 4 failing tests, talib integration via finlab_
  - _Requirements: 2_
  - _Prompt: Role: TDD Python Developer with TA-Lib experience | Task: Create src/factor_library/mean_reversion_factors.py with rsi_factor(container, parameters) function. Use talib.RSI, map to signal [-1, 1]. Register in factor registry. | Restrictions: Minimal implementation to pass tests | Success: pytest tests/factor_library/test_rsi_factor.py all pass_

- [ ] 6. P1-RSI: Refactor RSI Factor (TDD REFACTOR)
  - File: src/factor_library/mean_reversion_factors.py
  - Clean up implementation
  - Add comprehensive docstrings
  - Ensure edge case handling
  - Purpose: TDD REFACTOR phase
  - _Leverage: Task 5 passing tests_
  - _Requirements: 2_
  - _Prompt: Role: TDD Python Developer | Task: Refactor rsi_factor() in mean_reversion_factors.py. Add docstrings, improve error handling, ensure tests pass. | Restrictions: Maintain test compatibility | Success: Clean code, tests pass, radon cc < 10_

---

## Phase 3: P1 RVOL Factor

- [ ] 7. P1-RVOL: Write RVOL Factor Tests (TDD RED)
  - File: tests/factor_library/test_rvol_factor.py (CREATE)
  - Test: RVOL = current_volume / avg_volume
  - Test: RVOL > 1.5 triggers volume confirmation
  - Test: OBV + price confirmation signal
  - Test: TTPT - no look-ahead bias
  - Purpose: TDD RED phase for RVOL factor
  - _Leverage: Finlab data.get('price:成交金額')_
  - _Requirements: 3_
  - _Prompt: Role: TDD Python Developer specializing in volume analysis | Task: Create tests/factor_library/test_rvol_factor.py with tests for RVOL factor. Include test_rvol_calculation(), test_volume_confirmation_threshold(), test_obv_price_confirmation(), test_no_lookahead_bias(). | Restrictions: Tests MUST fail initially | Success: pytest shows 4 failing tests_

- [ ] 8. P1-RVOL: Implement RVOL Factor (TDD GREEN)
  - File: src/factor_library/mean_reversion_factors.py
  - Implement rvol_factor() with 20-day average
  - Add OBV calculation
  - Register in factor library
  - Purpose: TDD GREEN phase - pass RVOL tests
  - _Leverage: Task 7 failing tests_
  - _Requirements: 3_
  - _Prompt: Role: TDD Python Developer | Task: Add rvol_factor() to mean_reversion_factors.py. Calculate RVOL as current/20-day avg. Add OBV confirmation. | Restrictions: Minimal implementation | Success: pytest tests/factor_library/test_rvol_factor.py all pass_

---

## Phase 4: P1 Liquidity Filter

- [ ] 9. P1-LIQ: Write Liquidity Filter Tests (TDD RED)
  - File: tests/validation/test_liquidity_filter.py (CREATE)
  - Test: ADV < 40萬 → Tier 0 (Forbidden)
  - Test: 40萬 <= ADV < 100萬 → Tier 1 (Warning)
  - Test: 100萬 <= ADV < 500萬 → Tier 2 (Safe)
  - Test: ADV >= 500萬 → Tier 3 (Premium)
  - Test: strict_mode filters out Warning tier
  - Test: Forbidden tier signals zeroed
  - Purpose: TDD RED phase for LiquidityFilter
  - _Leverage: 40M TWD capital configuration_
  - _Requirements: 4_
  - _Prompt: Role: TDD Python Developer specializing in risk management | Task: Create tests/validation/test_liquidity_filter.py with comprehensive tests for LiquidityFilter class. Test all 4 liquidity tiers with exact thresholds (400k, 1M, 5M TWD). Test strict_mode and signal zeroing. | Restrictions: Tests MUST fail, class does not exist | Success: pytest shows 6+ failing tests_

- [ ] 10. P1-LIQ: Implement Liquidity Filter (TDD GREEN)
  - File: src/validation/liquidity_filter.py (CREATE)
  - Implement LiquidityFilter class
  - calculate_adv() with 20-day window
  - classify_liquidity() with 4 tiers
  - apply_filter() with strict_mode
  - Purpose: TDD GREEN phase
  - _Leverage: Task 9 failing tests_
  - _Requirements: 4_
  - _Prompt: Role: TDD Python Developer | Task: Create src/validation/liquidity_filter.py with LiquidityFilter class. Implement calculate_adv(), classify_liquidity(), apply_filter(). Thresholds: Forbidden<400k, Warning<1M, Safe<5M, Premium>=5M. | Restrictions: Pass all tests from Task 9 | Success: All liquidity tests pass_

- [ ] 11. P1-LIQ: Refactor Liquidity Filter (TDD REFACTOR)
  - File: src/validation/liquidity_filter.py
  - Add LiquidityTier IntEnum
  - Improve docstrings and type hints
  - Add position size constraints per tier
  - Purpose: TDD REFACTOR phase
  - _Leverage: Task 10 passing tests_
  - _Requirements: 4_
  - _Prompt: Role: TDD Python Developer | Task: Refactor LiquidityFilter. Add LiquidityTier IntEnum, comprehensive docstrings, type hints. Add position_limit_pct per tier. | Restrictions: Tests must remain green | Success: Clean code, full type coverage_

---

## Phase 5: P1 Execution Cost Model

- [ ] 12. P1-COST: Write Execution Cost Tests (TDD RED)
  - File: tests/validation/test_execution_cost.py (CREATE)
  - Test: Square Root Law formula correct
  - Test: Slippage capped at 500 bps
  - Test: Penalty tier < 20 bps = 0
  - Test: Penalty tier 20-50 bps = linear
  - Test: Penalty tier > 50 bps = quadratic
  - Purpose: TDD RED phase for ExecutionCostModel
  - _Leverage: Square Root Law: Slippage = Base + α × sqrt(Size/ADV) × Vol_
  - _Requirements: 5_
  - _Prompt: Role: TDD Python Developer with market microstructure knowledge | Task: Create tests/validation/test_execution_cost.py for ExecutionCostModel. Test calculate_slippage() with Square Root Law, test_slippage_cap_500bps(), test penalty tiers (no penalty<20, linear 20-50, quadratic>50). | Restrictions: Tests MUST fail | Success: pytest shows 5 failing tests_

- [ ] 13. P1-COST: Implement Execution Cost Model (TDD GREEN)
  - File: src/validation/execution_cost.py (CREATE)
  - Implement ExecutionCostModel class
  - calculate_slippage() with Square Root Law
  - calculate_liquidity_penalty() with tiered formula
  - Cap slippage at 500 bps
  - Purpose: TDD GREEN phase
  - _Leverage: Task 12 failing tests_
  - _Requirements: 5_
  - _Prompt: Role: TDD Python Developer | Task: Create src/validation/execution_cost.py with ExecutionCostModel. Implement Square Root Law: Slippage = base_cost + impact_coeff × sqrt(trade_size/ADV) × volatility. Cap at 500bps. Penalty: 0 if <20, linear 20-50, quadratic >50. | Restrictions: Pass all tests | Success: All execution cost tests pass_

---

## Phase 6: P1 Comprehensive Scorer

- [ ] 14. P1-SCORE: Write Comprehensive Scorer Tests (TDD RED)
  - File: tests/validation/test_comprehensive_scorer.py (CREATE)
  - Test: Weights sum to 1.0
  - Test: Stability = 1 - CV(monthly_returns)
  - Test: Turnover cost = annual_turnover × commission × 2
  - Test: Score includes all 5 components
  - Test: Default weights (Calmar 30%, Sortino 25%, ...)
  - Purpose: TDD RED phase for ComprehensiveScorer
  - _Leverage: Multi-objective scoring formula_
  - _Requirements: 6_
  - _Prompt: Role: TDD Python Developer with portfolio analytics experience | Task: Create tests/validation/test_comprehensive_scorer.py for ComprehensiveScorer. Test weight_sum_equals_1(), stability_calculation_cv(), turnover_cost_formula(), score_has_all_components(), default_weights_match_spec(). | Restrictions: Tests MUST fail | Success: pytest shows 5 failing tests_

- [ ] 15. P1-SCORE: Implement Comprehensive Scorer (TDD GREEN)
  - File: src/validation/comprehensive_scorer.py (CREATE)
  - Implement ComprehensiveScorer class
  - Default weights: Calmar 30%, Sortino 25%, Stability 20%, Turnover 15%, Liquidity 10%
  - calculate_stability() using coefficient of variation
  - compute_score() returning component breakdown
  - Purpose: TDD GREEN phase
  - _Leverage: Task 14 failing tests_
  - _Requirements: 6_
  - _Prompt: Role: TDD Python Developer | Task: Create src/validation/comprehensive_scorer.py with ComprehensiveScorer. Implement calculate_stability() as 1-CV, calculate_turnover_cost(), compute_score() with 5 weighted components. | Restrictions: Pass all tests | Success: All scorer tests pass_

---

## Phase 7: P2 Bollinger %B Factor

- [ ] 16. P2-BB: Write Bollinger %B Tests (TDD RED)
  - File: tests/factor_library/test_bollinger_factor.py (CREATE)
  - Test: %B uses TA-Lib BBANDS
  - Test: %B < 0 marked as oversold
  - Test: %B > 1 marked as overbought
  - Test: TTPT - no look-ahead bias
  - Purpose: TDD RED phase for Bollinger %B
  - _Requirements: 7_
  - _Prompt: Role: TDD Python Developer | Task: Create tests/factor_library/test_bollinger_factor.py with tests for bollinger_percentb_factor(). Test %B calculation, oversold/overbought classification, TTPT compliance. | Restrictions: Tests MUST fail | Success: pytest shows 4 failing tests_

- [ ] 17. P2-BB: Implement Bollinger %B Factor (TDD GREEN)
  - File: src/factor_library/mean_reversion_factors.py
  - Add bollinger_percentb_factor()
  - Use talib.BBANDS() via Finlab
  - %B = (close - lower) / (upper - lower)
  - Purpose: TDD GREEN phase
  - _Leverage: Task 16 failing tests_
  - _Requirements: 7_
  - _Prompt: Role: TDD Python Developer | Task: Add bollinger_percentb_factor() to mean_reversion_factors.py. Use talib.BBANDS, calculate %B. | Restrictions: Pass tests | Success: All Bollinger tests pass_

---

## Phase 8: P2 Efficiency Ratio Factor

- [ ] 18. P2-ER: Write Efficiency Ratio Tests (TDD RED)
  - File: tests/factor_library/test_er_factor.py (CREATE)
  - Test: ER in [0, 1] range
  - Test: ER > 0.5 marked as trending
  - Test: ER < 0.3 marked as mean-reverting
  - Test: TTPT - no look-ahead bias
  - Purpose: TDD RED phase for Efficiency Ratio
  - _Requirements: 8_
  - _Prompt: Role: TDD Python Developer | Task: Create tests/factor_library/test_er_factor.py for efficiency_ratio_factor(). Test ER range [0,1], trending/reverting classification, TTPT. | Restrictions: Tests MUST fail | Success: pytest shows 4 failing tests_

- [ ] 19. P2-ER: Implement Efficiency Ratio Factor (TDD GREEN)
  - File: src/factor_library/regime_factors.py (CREATE)
  - Implement efficiency_ratio_factor()
  - ER = abs(close[-1] - close[0]) / sum(abs(daily_returns))
  - Register in factor library
  - Purpose: TDD GREEN phase
  - _Leverage: Task 18 failing tests_
  - _Requirements: 8_
  - _Prompt: Role: TDD Python Developer | Task: Create src/factor_library/regime_factors.py with efficiency_ratio_factor(). ER = net_change / total_path. | Restrictions: Pass tests | Success: All ER tests pass_

---

## Phase 9: P2 TTPT Framework

- [ ] 20. P2-TTPT: Write TTPT Framework Tests
  - File: tests/factor_library/test_lookahead_bias.py (CREATE)
  - Parametrize tests for all new factors
  - Test: Single perturbation (T+1 change)
  - Test: 100 random perturbations
  - Test: Multi-day perturbation (T+1, T+2, T+3)
  - Purpose: Framework for automated look-ahead bias detection
  - _Leverage: All new factors from Phase 2-8_
  - _Requirements: 9_
  - _Prompt: Role: TDD Python Developer specializing in backtesting validation | Task: Create tests/factor_library/test_lookahead_bias.py with TTPT framework. Use @pytest.mark.parametrize for all factors. Implement single_perturbation, 100_random_perturbations, multi_day_perturbation tests. | Restrictions: Framework must be reusable | Success: All new factors automatically tested for look-ahead bias_

- [ ] 21. P2-TTPT: Implement Runtime TTPT Monitor
  - File: src/validation/runtime_ttpt.py (CREATE)
  - Implement RuntimeTTPTMonitor class
  - 1% sampling rate for production
  - Log violations to monitoring system
  - Purpose: Runtime look-ahead bias detection
  - _Leverage: Task 20 TTPT framework_
  - _Requirements: 9_
  - _Prompt: Role: TDD Python Developer | Task: Create src/validation/runtime_ttpt.py with RuntimeTTPTMonitor. Sample 1% of factor calculations, run TTPT, log violations. | Restrictions: Minimal performance impact | Success: Runtime monitoring functional_

---

## Phase 10: Integration & CI/CD

- [ ] 22. Integration: Factor Registry Update
  - File: src/factor_library/registry.py
  - Register all new factors
  - Add category classification (mean_reversion, regime)
  - Update factor discovery
  - Purpose: Central factor management
  - _Leverage: All new factors from Phases 2-8_
  - _Requirements: All_
  - _Prompt: Role: TDD Python Developer | Task: Update src/factor_library/registry.py to register rsi_factor, rvol_factor, bollinger_percentb_factor, efficiency_ratio_factor. Add category metadata. | Restrictions: Maintain backward compatibility | Success: All factors discoverable via registry_

- [ ] 23. Integration: Validation Pipeline Update
  - File: src/validation/__init__.py
  - Export LiquidityFilter, ExecutionCostModel, ComprehensiveScorer
  - Create validation_pipeline() function
  - Purpose: Unified validation interface
  - _Leverage: Tasks 10, 13, 15_
  - _Requirements: 4, 5, 6_
  - _Prompt: Role: TDD Python Developer | Task: Update src/validation/__init__.py to export all validation components. Create validation_pipeline(metrics, adv, volatility) function. | Restrictions: Clean interface | Success: Single import for all validation_

- [ ] 24. CI/CD: Test Coverage Check
  - File: .github/workflows/test.yml (or equivalent)
  - Add pytest coverage reporting
  - Enforce ≥ 80% coverage threshold
  - Add TTPT tests to CI pipeline
  - Purpose: Automated quality gates
  - _Requirements: Non-functional_
  - _Prompt: Role: DevOps Engineer | Task: Update CI workflow to run pytest with coverage. Add coverage threshold check ≥ 80%. Include TTPT tests. | Restrictions: Fast CI execution | Success: CI blocks PRs with low coverage_

- [ ] 25. Documentation: Update API Reference
  - File: docs/API_REFERENCE.md
  - Document all new factors
  - Document validation components
  - Add usage examples
  - Purpose: Developer documentation
  - _Requirements: All_
  - _Prompt: Role: Technical Writer | Task: Update docs/API_REFERENCE.md with documentation for new factors (RSI, RVOL, Bollinger, ER) and validation components (LiquidityFilter, ExecutionCostModel, ComprehensiveScorer). Include code examples. | Restrictions: Consistent style | Success: Complete API docs for new components_

---

## Parallel / Dependency Analysis

### Task Dependency Matrix

| Task | Depends On | Blocks | Can Parallel With |
|------|------------|--------|-------------------|
| 1 | - | 2 | 4, 7, 9, 12, 14, 16, 18 |
| 2 | 1 | 3 | 4, 7, 9, 12, 14, 16, 18 |
| 3 | 2 | 22 | 4, 7, 9, 12, 14, 16, 18 |
| 4 | - | 5 | 1, 7, 9, 12, 14, 16, 18 |
| 5 | 4 | 6, 20 | 2, 8, 10, 13, 15, 17, 19 |
| 6 | 5 | 22 | 3, 8, 11, 13, 15, 17, 19 |
| 7 | - | 8 | 1, 4, 9, 12, 14, 16, 18 |
| 8 | 7 | 20, 22 | 2, 5, 10, 13, 15, 17, 19 |
| 9 | - | 10 | 1, 4, 7, 12, 14, 16, 18 |
| 10 | 9 | 11, 23 | 2, 5, 8, 13, 15, 17, 19 |
| 11 | 10 | 22 | 3, 6, 8, 13, 15, 17, 19 |
| 12 | - | 13 | 1, 4, 7, 9, 14, 16, 18 |
| 13 | 12 | 23 | 2, 5, 8, 10, 15, 17, 19 |
| 14 | - | 15 | 1, 4, 7, 9, 12, 16, 18 |
| 15 | 14 | 23 | 2, 5, 8, 10, 13, 17, 19 |
| 16 | - | 17 | 1, 4, 7, 9, 12, 14, 18 |
| 17 | 16 | 20, 22 | 2, 5, 8, 10, 13, 15, 19 |
| 18 | - | 19 | 1, 4, 7, 9, 12, 14, 16 |
| 19 | 18 | 20, 22 | 2, 5, 8, 10, 13, 15, 17 |
| 20 | 5, 8, 17, 19 | 21 | - |
| 21 | 20 | - | 22, 23, 24 |
| 22 | 6, 8, 11, 17, 19 | 23 | 21, 24 |
| 23 | 10, 13, 15, 22 | 24 | 21, 25 |
| 24 | 23 | 25 | 21 |
| 25 | 22, 23 | - | 24 |

---

### Parallel Execution Waves

**最佳化執行策略**：將獨立任務分組為可並行執行的 Wave

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ WAVE 1: All TDD RED Tests (可完全並行)                                       │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│ │  1  │ │  4  │ │  7  │ │  9  │ │ 12  │ │ 14  │ │ 16  │ │ 18  │           │
│ │ P0  │ │ RSI │ │RVOL │ │ LIQ │ │COST │ │SCORE│ │ BB  │ │ ER  │           │
│ │ RED │ │ RED │ │ RED │ │ RED │ │ RED │ │ RED │ │ RED │ │ RED │           │
│ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘           │
│    │       │       │       │       │       │       │       │               │
│    ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼               │
├─────────────────────────────────────────────────────────────────────────────┤
│ WAVE 2: All TDD GREEN Implementations (可完全並行)                           │
│ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐           │
│ │  2  │ │  5  │ │  8  │ │ 10  │ │ 13  │ │ 15  │ │ 17  │ │ 19  │           │
│ │ P0  │ │ RSI │ │RVOL │ │ LIQ │ │COST │ │SCORE│ │ BB  │ │ ER  │           │
│ │GREEN│ │GREEN│ │GREEN│ │GREEN│ │GREEN│ │GREEN│ │GREEN│ │GREEN│           │
│ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘           │
│    │       │       │       │       │       │       │       │               │
│    ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼               │
├─────────────────────────────────────────────────────────────────────────────┤
│ WAVE 3: Refactor + TTPT (部分並行)                                          │
│ ┌─────┐ ┌─────┐         ┌─────┐                                            │
│ │  3  │ │  6  │         │ 11  │         ┌─────────────────────┐            │
│ │ P0  │ │ RSI │         │ LIQ │         │        20           │            │
│ │REFAC│ │REFAC│         │REFAC│         │   TTPT Framework    │            │
│ └──┬──┘ └──┬──┘         └──┬──┘         │ (需 5,8,17,19 完成) │            │
│    │       │               │             └─────────┬───────────┘            │
│    │       │               │                       │                        │
│    ▼       ▼               ▼                       ▼                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ WAVE 4: Integration (依序執行)                                               │
│ ┌─────┐ ┌─────┐ ┌─────┐         ┌─────┐ ┌─────┐                            │
│ │ 21  │→│ 22  │→│ 23  │    →    │ 24  │→│ 25  │                            │
│ │TTPT │ │Reg. │ │Valid│         │CI/CD│ │Docs │                            │
│ │ Mon │ │Upd. │ │Pipe │         │     │ │     │                            │
│ └─────┘ └─────┘ └─────┘         └─────┘ └─────┘                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Critical Path Analysis

**關鍵路徑** (決定最短完成時間)：

```
[1] → [2] → [3] → [22] → [23] → [24] → [25]
 │                  ↑
 │    [4] → [5] → [6] ─┤
 │    [7] → [8] ───────┤
 │    [9] → [10] → [11]┤
 │    [12] → [13] ─────┤
 │    [14] → [15] ─────┤
 │    [16] → [17] ─────┤
 │    [18] → [19] ─────┘
 │              ↓
 └──────────→ [20] → [21]
```

**關鍵路徑長度**: 7 tasks (1→2→3→22→23→24→25)
**最長非關鍵路徑**: TTPT 路徑 (5,8,17,19→20→21)

---

### Parallelism Opportunities

#### Wave 1 - Maximum Parallelism (8 parallel tasks)
所有 TDD RED 測試可同時執行：
- **並行度**: 8
- **預估時間**: 2-3h (最長單一任務)
- **Tasks**: 1, 4, 7, 9, 12, 14, 16, 18

#### Wave 2 - High Parallelism (8 parallel tasks)
所有 GREEN 實作可同時執行：
- **並行度**: 8
- **預估時間**: 3-4h (最長單一任務)
- **Tasks**: 2, 5, 8, 10, 13, 15, 17, 19

#### Wave 3 - Medium Parallelism (4 parallel tasks)
Refactor 任務 + TTPT：
- **並行度**: 4
- **預估時間**: 3-4h
- **Tasks**: 3, 6, 11, 20

#### Wave 4 - Sequential (5 tasks)
整合任務需依序執行：
- **並行度**: 1-2
- **預估時間**: 4-6h
- **Tasks**: 21, 22, 23, 24, 25

---

### Resource Allocation Strategy

| Wave | Tasks | Max Parallelism | Developer Resources |
|------|-------|-----------------|---------------------|
| 1 | 8 (RED) | 8 | 8 devs OR 2 devs × 4 rounds |
| 2 | 8 (GREEN) | 8 | 8 devs OR 2 devs × 4 rounds |
| 3 | 4 (REFACTOR + TTPT) | 4 | 4 devs OR 1 dev × 4 rounds |
| 4 | 5 (Integration) | 2 | 2 devs sequential |

**Single Developer Timeline**:
- Wave 1: 8 tasks × 0.5h avg = 4h
- Wave 2: 8 tasks × 1h avg = 8h
- Wave 3: 4 tasks × 1h avg = 4h
- Wave 4: 5 tasks × 1.5h avg = 7.5h
- **Total**: ~24h (3 working days)

**Team (4 Developers) Timeline**:
- Wave 1: 8 tasks / 4 devs = 2h
- Wave 2: 8 tasks / 4 devs = 2h
- Wave 3: 4 tasks / 4 devs = 1h
- Wave 4: 5 tasks / 2 devs = 4h
- **Total**: ~9h (1+ working day)

---

### Dependency Risk Assessment

| Dependency Chain | Risk Level | Mitigation |
|------------------|------------|------------|
| 1→2→3 (P0 Bug) | LOW | 獨立路徑，無外部依賴 |
| 4→5→6→20 (RSI→TTPT) | MEDIUM | TTPT 依賴多個因子完成 |
| 9→10→11→23 (LIQ→Pipeline) | MEDIUM | Validation 整合依賴 |
| 22→23→24→25 | HIGH | 串行整合，延遲會累積 |

---

### Blocking Dependencies Visualization

```
INDEPENDENT (可立即開始):
├── Task 1  (P0 Metrics Test)
├── Task 4  (RSI Test)
├── Task 7  (RVOL Test)
├── Task 9  (Liquidity Test)
├── Task 12 (Cost Test)
├── Task 14 (Scorer Test)
├── Task 16 (Bollinger Test)
└── Task 18 (ER Test)

BLOCKED BY SINGLE TASK:
├── Task 2  ← blocked by [1]
├── Task 5  ← blocked by [4]
├── Task 8  ← blocked by [7]
├── Task 10 ← blocked by [9]
├── Task 13 ← blocked by [12]
├── Task 15 ← blocked by [14]
├── Task 17 ← blocked by [16]
├── Task 19 ← blocked by [18]
├── Task 3  ← blocked by [2]
├── Task 6  ← blocked by [5]
├── Task 11 ← blocked by [10]
└── Task 21 ← blocked by [20]

BLOCKED BY MULTIPLE TASKS:
├── Task 20 ← blocked by [5, 8, 17, 19]
├── Task 22 ← blocked by [6, 8, 11, 17, 19]
├── Task 23 ← blocked by [10, 13, 15, 22]
├── Task 24 ← blocked by [23]
└── Task 25 ← blocked by [22, 23]
```

---

## Dependency Graph

```
Phase 1 (P0 Bug Fix):
  [1] → [2] → [3]

Phase 2-3 (P1 Factors):
  [4] → [5] → [6]  (RSI)
  [7] → [8]         (RVOL)

Phase 4-6 (P1 Validation):
  [9] → [10] → [11]   (Liquidity)
  [12] → [13]          (Execution Cost)
  [14] → [15]          (Scorer)

Phase 7-8 (P2 Factors):
  [16] → [17]  (Bollinger)
  [18] → [19]  (ER)

Phase 9 (P2 TTPT):
  [5,8,17,19] → [20] → [21]

Phase 10 (Integration):
  [6,8,11,13,15,17,19] → [22] → [23] → [24] → [25]
```

---

## Estimation Summary

| Phase | Tasks | Estimated Hours | Priority |
|-------|-------|-----------------|----------|
| 1: P0 Bug Fix | 3 | 2-3h | Critical |
| 2: RSI Factor | 3 | 4-5h | P1 |
| 3: RVOL Factor | 2 | 3-4h | P1 |
| 4: Liquidity Filter | 3 | 4-5h | P1 |
| 5: Execution Cost | 2 | 3-4h | P1 |
| 6: Comprehensive Scorer | 2 | 3-4h | P1 |
| 7: Bollinger %B | 2 | 2-3h | P2 |
| 8: Efficiency Ratio | 2 | 2-3h | P2 |
| 9: TTPT Framework | 2 | 4-5h | P2 |
| 10: Integration | 4 | 4-6h | All |
| **Total** | **25** | **31-42h** | - |
