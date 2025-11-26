# TDD Implementation Roadmap - Unified Improvement Plan

**生成日期**: 2025-11-14
**規劃工具**: zen planner + zen testgen (gemini-2.5-pro)
**目標**: 突破 Stage 2，達成 80% 成功率、2.5+ Sharpe、40%+ 多樣性

---

## Executive Summary

### 問題定義
1. **Phase 7 regression**: StrategyMetrics 從 Dict 改為 dataclass，破壞向後兼容性
2. **19-day plateau**: 成功率卡在 35-40%，無法突破
3. **計算效率低下**: TPE 搜索在高維空間效率不足

### 解決方案
- **P0 (Critical)**: 修復 Phase 7 regression + 整合 ASHA 優化器
- **P1 (High)**: Regime Detection + Portfolio Optimization + Epsilon-Constraint
- **P2-P3 (Medium-Low)**: 驗證框架 + 文檔化

### 預期成果
- **成功率**: 35-40% → 80%
- **Sharpe Ratio**: 1.5-2.0 → 2.5+
- **多樣性**: 20-30% → 40%+
- **時間框架**: 12 weeks (153-179 hours，優化自原 640 hours)
- **平行處理節省**: 38-52 hours (33-38%)

---

## Priority Breakdown

### P0: Critical Path (Weeks 1-3, 8-12 hours)

#### P0.1: Phase 7 Regression Fix (Week 1, 4 hours)
**目標**: 修復 StrategyMetrics dict 接口兼容性

**實現細節**:
```python
# src/backtest/metrics.py
@dataclass
class StrategyMetrics:
    # 已實現 (4/7):
    def __getitem__(self, key: str) -> Any  # ✅
    def get(self, key: str, default=None) -> Any  # ✅
    def __contains__(self, key: str) -> bool  # ✅
    def keys(self) -> list  # ✅

    # 需實現 (3/7):
    def values(self) -> list  # ❌
    def items(self) -> list  # ❌
    def __len__(self) -> int  # ❌
```

**測試規格** (10 tests):
```python
# tests/unit/test_strategy_metrics_dict_interface.py

class TestStrategyMetricsDictInterface:
    # Category G: __len__ 方法 (2 tests)
    def test_len_returns_fixed_number_of_metrics(self)
    def test_len_is_constant_regardless_of_values(self)

    # Category H: values() 方法 (3 tests)
    def test_values_returns_list_of_metric_values(self)
    def test_values_order_matches_keys_order(self)
    def test_values_with_none_and_bool_values(self)

    # Category I: items() 方法 (3 tests)
    def test_items_returns_list_of_key_value_tuples(self)
    def test_items_content_and_order_are_correct(self)
    def test_items_on_empty_metrics(self)

    # Plus 10 existing tests for __getitem__, get(), __contains__, keys()
```

**關鍵邊界條件**:
1. None vs default 返回值差異 (get vs __getitem__)
2. AttributeError → KeyError 轉換
3. pandas NaN 處理 via __post_init__
4. execution_success bool 類型處理
5. 無效 key 錯誤消息格式

**驗證標準**:
- ✅ All 10 tests pass (RED → GREEN)
- ✅ pytest-cov ≥95% line coverage
- ✅ 向後兼容性：現有代碼零修改運行

---

#### P0.2: ASHA Hyperparameter Optimizer (Weeks 2-3, 8 hours)
**目標**: 整合 ASHA 多保真度搜索，提升 50-70% 搜索效率

**實現細節**:
```python
# src/learning/optimizer.py
class ASHAOptimizer:
    def __init__(
        self,
        n_iterations: int = 100,
        min_resource: int = 3,
        reduction_factor: int = 3,
        grace_period: int = 5
    ):
        # ✅ 已實現：參數驗證
        if reduction_factor < 2:
            raise ValueError(...)
        if min_resource < 1:
            raise ValueError(...)

    def create_study(self) -> optuna.Study:
        # ✅ 已實現：Optuna study 創建
        pruner = SuccessiveHalvingPruner(...)
        return optuna.create_study(direction='maximize', pruner=pruner)

    def optimize(...) -> Dict[str, Any]:
        # ❌ 待實現：主要優化循環
        pass

    def early_stop_callback(...) -> None:
        # ❌ 待實現：早期停止邏輯
        pass

    def get_search_stats(...) -> Dict[str, Any]:
        # ❌ 待實現：統計收集
        pass
```

**測試規格** (20 tests):
```python
# tests/learning/test_optimizer.py

# Phase 1: 可立即運行 (8 tests)
class TestASHAOptimizerInit:
    def test_init_with_default_parameters(self)  # ✅
    def test_init_with_custom_parameters(self)  # ✅
    def test_init_raises_error_invalid_reduction_factor(self)  # ✅
    def test_init_raises_error_invalid_min_resource(self)  # ✅

class TestCreateStudy:
    def test_create_study_returns_optuna_study(self)  # ✅
    def test_create_study_uses_maximize_direction(self)  # ✅
    def test_create_study_configures_asha_pruner(self)  # ✅

class TestIntegrationAndEdgeCases:
    def test_optimizer_configuration_persists(self)  # ✅

# Phase 2: 待實現 (12 tests with @pytest.mark.skip)
class TestOptimizeMethod:
    def test_optimize_returns_best_parameters(self)  # RED
    def test_optimize_handles_objective_function_errors(self)  # RED

class TestEarlyStopping:
    def test_early_stop_callback_prunes_poor_trials(self)  # RED
    def test_early_stop_callback_keeps_promising_trials(self)  # RED
    def test_grace_period_prevents_premature_pruning(self)  # RED
    def test_reduction_factor_determines_pruning_rate(self)  # RED

class TestGetSearchStats:
    def test_get_search_stats_includes_trial_counts(self)  # RED
    def test_get_search_stats_includes_best_performance(self)  # RED
    def test_get_search_stats_calculates_pruning_efficiency(self)  # RED

class TestParamSpace:
    def test_param_space_uniform_distribution(self)  # RED
    def test_param_space_integer_distribution(self)  # RED
    def test_param_space_categorical_choices(self)  # RED
```

**CRITICAL 前置條件**:
```bash
# BLOCKER: 添加 Optuna 依賴
echo "optuna>=3.0.0  # P0.2: ASHA hyperparameter optimization" >> requirements.txt
pip install optuna>=3.0.0
```

**驗證標準**:
- ✅ Phase 1: 8 tests pass immediately
- ✅ Phase 2: 12 skipped tests → GREEN after implementation
- ✅ 效率提升：搜索時間減少 50-70%
- ✅ 性能保持：最終 Sharpe ratio 不劣於 TPE

---

### P1: High Priority (Weeks 4-7, 24-32 hours)

#### P1.1: Market Regime Detection (Week 4, 8 hours)
**目標**: 2x2 矩陣，4 種市場狀態

```python
# src/regime/detector.py
class RegimeDetector:
    def detect_regime(self, market_data: pd.DataFrame) -> str:
        """
        Returns: 'bull_low' | 'bull_high' | 'bear_low' | 'bear_high'

        Trend: SMA(50) vs SMA(200)
        - Bull: SMA(50) > SMA(200)
        - Bear: SMA(50) < SMA(200)

        Volatility: Rolling std(20)
        - High: std > median(std) * 1.5
        - Low: std <= median(std) * 1.5
        """
        pass
```

**測試規格** (12 tests):
- Trend detection (4 tests): bull/bear 邊界條件
- Volatility detection (4 tests): high/low 閾值測試
- Regime classification (4 tests): 4 種狀態組合

**預期改善**: Regime-aware 策略 +10% 勝率

---

#### P1.2: Portfolio Optimization with ERC (Week 5, 8 hours)
**目標**: Equal Risk Contribution，降低集中度風險

```python
# src/portfolio/optimizer.py
class ERCOptimizer:
    def optimize_weights(
        self,
        returns: pd.DataFrame,
        correlation_threshold: float = 0.7,
        max_concentration: float = 0.3
    ) -> Dict[str, float]:
        """
        Constraints:
        - Correlation < 0.7 between strategies
        - Max 30% weight per strategy
        - Equal risk contribution
        """
        pass
```

**測試規格** (15 tests):
- Correlation constraint (5 tests)
- Concentration limit (5 tests)
- ERC calculation (5 tests)

**預期改善**: Portfolio Sharpe +5-15%

---

#### P1.3: Epsilon-Constraint Multi-Objective (Week 6-7, 8-16 hours)
**目標**: 強制 30% 多樣性下限

```python
# src/optimization/epsilon_constraint.py
class EpsilonConstraintOptimizer:
    def optimize(
        self,
        sharpe_fn: Callable,
        diversity_fn: Callable,
        min_diversity: float = 0.3
    ) -> Dict[str, Any]:
        """
        Maximize: Sharpe ratio
        Subject to: diversity >= 0.3
        """
        pass
```

**測試規格** (18 tests):
- Constraint satisfaction (6 tests)
- Pareto frontier (6 tests)
- Trade-off analysis (6 tests)

**預期改善**: 多樣性 20-30% → 40%+

---

### P2: Medium Priority (Weeks 8-10, 48 hours)

#### P2.1: Purged Walk-Forward CV (Week 8, 16 hours)
**目標**: 防止數據洩漏，確保 OOS 有效性

```python
# src/validation/purged_cv.py
class PurgedWalkForwardCV:
    def __init__(
        self,
        n_splits: int = 5,
        purge_gap: int = 21  # 21 trading days
    ):
        pass

    def split(self, X: pd.DataFrame) -> Iterator:
        """
        Yields train/test splits with purge gap
        """
        pass
```

**測試規格** (20 tests)

**驗證門檻**: OOS Sharpe within ±20% of IS Sharpe

---

#### P2.2: E2E Testing Framework (Week 9, 16 hours)
**測試規格** (15 tests)

#### P2.3: Performance Benchmarks (Week 10, 16 hours)
**測試規格** (15 tests)

---

### P3: Low Priority (Weeks 11-12, 40 hours)

#### P3.1: Documentation (Week 11, 24 hours)
- API docs, user guides, architecture diagrams

#### P3.2: Monitoring Dashboard (Week 12, 16 hours)
- Real-time metrics, alerting, logging

---

## Validation Gates

所有 6 個 gates 必須 GREEN 才能進入下一階段：

### Gate 1: E2E Tests GREEN (P0 完成後)
```bash
pytest tests/e2e/ -v
# 預期: 100% pass, 0% error rate
```

### Gate 2: Regime-Aware Performance (P1.1 完成後)
```bash
python experiments/validate_regime_detection.py
# 預期: +10% win rate improvement
```

### Gate 3: Stage 2 Breakthrough (P1 完成後)
```bash
python experiments/validate_stage2_metrics.py
# 預期:
#   - Success rate: 80%+
#   - Sharpe ratio: 2.5+
#   - Diversity: 40%+
```

### Gate 4: Portfolio Optimization (P1.2 完成後)
```bash
python experiments/validate_portfolio_erc.py
# 預期: +5-15% portfolio Sharpe
```

### Gate 5: OOS Validation (P2.1 完成後)
```bash
python experiments/validate_purged_cv.py
# 預期: OOS Sharpe within ±20% of IS
```

### Gate 6: Production Readiness (P2-P3 完成後)
```bash
python experiments/validate_production_metrics.py
# 預期:
#   - Latency: <100ms per backtest
#   - Slippage: <0.1%
#   - Uptime: 99.9%+
```

---

## Parallel Processing Analysis

### 可平行化任務

**Cluster 1: P0 並行** (Week 1-3)
- P0.1 Phase 7 Fix (4h) || P0.2 ASHA Optimizer (8h)
- **節省時間**: 4 hours (33%)

**Cluster 2: P1 並行** (Week 4-7)
- P1.1 Regime Detection (8h)
- P1.2 Portfolio ERC (8h) || P1.3 Epsilon-Constraint (8h)
- **節省時間**: 8 hours (25%)

**Cluster 3: P2 並行** (Week 8-10)
- P2.1 Purged CV (16h)
- P2.2 E2E Testing (16h) || P2.3 Benchmarks (16h)
- **節省時間**: 16 hours (33%)

**Cluster 4: P3 並行** (Week 11-12)
- P3.1 Documentation (24h) || P3.2 Dashboard (16h)
- **節省時間**: 16 hours (40%)

**總節省**: 38-52 hours (33-38% 時間縮減)

---

## Time Allocation Summary

| Priority | Tasks | Sequential | Parallel | Savings |
|----------|-------|------------|----------|---------|
| **P0** | 2 | 12h | 8h | 4h (33%) |
| **P1** | 3 | 32h | 24h | 8h (25%) |
| **P2** | 3 | 48h | 32h | 16h (33%) |
| **P3** | 2 | 40h | 24h | 16h (40%) |
| **Total** | 10 | 132h | 88h | 44h (33%) |

**加上驗證測試時間**: 153-179 hours total

---

## TDD Cycle Workflow

### Red Phase
```bash
# 1. 運行現有測試
pytest tests/unit/test_strategy_metrics_dict_interface.py -v
# 預期: 10 tests, 3 methods missing → FAIL

pytest tests/learning/test_optimizer.py -v
# 預期: 8 pass, 12 skipped
```

### Green Phase
```bash
# 2. 實現最小代碼使測試通過
# P0.1: Implement values(), items(), __len__()
# P0.2: Implement optimize(), early_stop_callback(), get_search_stats()

# 3. 重新運行測試
pytest tests/unit/test_strategy_metrics_dict_interface.py -v
# 預期: 10 tests PASS

pytest tests/learning/test_optimizer.py -v
# 預期: 20 tests PASS (remove @pytest.mark.skip)
```

### Refactor Phase
```bash
# 4. 優化代碼品質
radon cc src/backtest/metrics.py src/learning/optimizer.py
# 目標: Complexity ≤ 10

mypy src/backtest/metrics.py src/learning/optimizer.py
# 目標: 0 type errors

# 5. 確認測試仍然通過
pytest tests/ --cov=src --cov-report=term-missing
# 目標: ≥95% coverage
```

---

## Expert Synthesis

本規劃整合了 3 位專家的意見：

### Expert 1: Quant Researcher (Sharpe 焦點)
- **貢獻**: ASHA 多保真度搜索，TPE/BO 優化
- **預期改善**: 搜索效率 +50-70%

### Expert 2: ML Engineer (多樣性焦點)
- **貢獻**: Epsilon-Constraint 多目標優化
- **預期改善**: 多樣性 20-30% → 40%+

### Expert 3: Risk Manager (穩健性焦點)
- **貢獻**: Purged Walk-Forward CV，ERC Portfolio
- **預期改善**: OOS 穩定性 ±20%，Portfolio Sharpe +5-15%

---

## Dependency Graph

```
P0.1 Phase 7 Fix ────────────────┐
                                  ├──→ Gate 1 (E2E GREEN)
P0.2 ASHA Optimizer ─────────────┘
                                  │
                                  ↓
P1.1 Regime Detection ───────────┐
                                  ├──→ Gate 2 (+10% regime-aware)
P1.2 Portfolio ERC ──────────────┤
                                  ├──→ Gate 3 (Stage 2 突破)
P1.3 Epsilon-Constraint ─────────┘    Gate 4 (+5-15% portfolio)
                                  │
                                  ↓
P2.1 Purged CV ──────────────────┐
                                  ├──→ Gate 5 (OOS ±20%)
P2.2 E2E Testing ────────────────┤
P2.3 Benchmarks ─────────────────┘
                                  │
                                  ↓
P3.1 Documentation ──────────────┐
                                  ├──→ Gate 6 (Production Ready)
P3.2 Dashboard ──────────────────┘
```

---

## Next Actions

### Immediate (Today)
1. ✅ 添加 Optuna 依賴到 requirements.txt
2. ✅ 創建 test_optimizer.py 測試文件
3. ✅ 運行 Phase 1 測試驗證框架

### Week 1
1. 實現 StrategyMetrics.values(), items(), __len__()
2. 運行 10 個 dict interface 測試
3. 達成 Gate 1: E2E Tests GREEN

### Week 2-3
1. 實現 ASHAOptimizer.optimize() 主循環
2. 實現 early_stop_callback() 邏輯
3. 實現 get_search_stats() 統計
4. 移除 @pytest.mark.skip，運行 20 個測試
5. 驗證搜索效率提升 50-70%

### Week 4+
按照 P1 → P2 → P3 順序執行，確保每個 Gate 通過後再進入下一階段。

---

**文檔版本**: 1.0
**最後更新**: 2025-11-14
**負責人**: TDD Implementation Team
**審核狀態**: ✅ Ready for Implementation
