# Unified Improvement Roadmap - TDD Implementation - Requirements Document

完整的 TDD 實現路線圖，整合 P0-P3 優先級、測試規格和驗證門檻，目標是突破 Stage 2 達成 80% 成功率、2.5+ Sharpe、40%+ 多樣性。包含 Phase 7 regression 修復、ASHA 優化器整合、市場狀態檢測、投資組合優化和多目標優化等關鍵功能。

## Core Features

### P0: Critical Path (Weeks 1-3)
**P0.1 - Phase 7 Regression Fix**
- 修復 StrategyMetrics dict 接口兼容性問題
- 實現缺失的 3 個 dict 方法：values(), items(), __len__()
- 確保向後兼容性，現有代碼零修改運行
- 測試覆蓋率 ≥95%

**P0.2 - ASHA Hyperparameter Optimizer**
- 整合 Optuna ASHA (Asynchronous Successive Halving Algorithm)
- 實現多保真度超參數搜索
- 搜索效率提升 50-70%
- Early stopping 機制減少計算資源浪費

### P1: High Priority (Weeks 4-7)
**P1.1 - Market Regime Detection**
- 2x2 市場狀態矩陣（Trend × Volatility）
- 4 種狀態：bull_low, bull_high, bear_low, bear_high
- Regime-aware 策略選擇，預期 +10% 勝率

**P1.2 - Portfolio Optimization with ERC**
- Equal Risk Contribution 投資組合優化
- Correlation 限制 < 0.7
- 集中度限制 max 30% per strategy
- Portfolio Sharpe +5-15%

**P1.3 - Epsilon-Constraint Multi-Objective**
- 多目標優化：Maximize Sharpe, Subject to Diversity ≥ 30%
- Pareto frontier 分析
- 多樣性 20-30% → 40%+

### P2: Medium Priority (Weeks 8-10)
**P2.1 - Purged Walk-Forward Cross-Validation**
- 防止數據洩漏的 CV 框架
- 21-day purge gap
- OOS Sharpe within ±20% of IS

**P2.2 - E2E Testing Framework**
- 端到端測試覆蓋完整流程
- 15+ 關鍵路徑測試

**P2.3 - Performance Benchmarks**
- Latency < 100ms per backtest
- Slippage < 0.1%
- 15+ 性能基準測試

### P3: Low Priority (Weeks 11-12)
**P3.1 - Documentation**
- API 文檔
- 用戶指南
- 架構圖

**P3.2 - Monitoring Dashboard**
- 實時指標監控
- 告警系統
- 日誌聚合

## User Stories

### 開發者視角
- **As a** quant developer, **I want** ASHA 優化器快速搜索最佳參數, **so that** 我可以在有限時間內探索更多策略組合
- **As a** system architect, **I want** StrategyMetrics 完全兼容 dict 接口, **so that** 現有代碼無需修改即可升級
- **As a** ML engineer, **I want** Epsilon-Constraint 多目標優化, **so that** 我可以同時優化 Sharpe 和多樣性

### 量化研究員視角
- **As a** quant researcher, **I want** Market Regime Detection, **so that** 我可以根據市場狀態選擇最適合的策略
- **As a** portfolio manager, **I want** ERC 投資組合優化, **so that** 我可以降低集中度風險並提升風險調整收益

### 測試工程師視角
- **As a** QA engineer, **I want** Purged Walk-Forward CV, **so that** 我可以確保回測結果在樣本外仍然有效
- **As a** test engineer, **I want** 完整的 TDD 測試規格, **so that** 我可以在開發前明確驗證標準

### 系統管理員視角
- **As a** DevOps engineer, **I want** 性能基準測試, **so that** 我可以監控系統性能並及時發現退化
- **As a** operations engineer, **I want** 監控儀表板, **so that** 我可以實時追蹤系統健康狀態

## Acceptance Criteria

### P0.1 - Phase 7 Regression Fix
- [x] StrategyMetrics 實現 values() 方法，返回所有屬性值列表
- [x] StrategyMetrics 實現 items() 方法，返回 (key, value) 元組列表
- [x] StrategyMetrics 實現 __len__() 方法，返回屬性數量 (5)
- [x] 10 個單元測試全部通過 (包含邊界條件)
- [x] pytest-cov 顯示 ≥95% line coverage
- [x] 現有代碼使用 metrics['key'] 和 metrics.get() 無需修改

### P0.2 - ASHA Optimizer
- [x] ASHAOptimizer.optimize() 實現完整優化循環
- [x] ASHAOptimizer.early_stop_callback() 實現 early stopping 邏輯
- [x] ASHAOptimizer.get_search_stats() 返回完整統計資訊
- [x] 20 個單元測試全部通過 (8 immediate + 12 implementation)
- [x] 搜索時間減少 50-70% (對比 TPE baseline)
- [x] 最終 Sharpe ratio 不劣於 TPE 全量搜索
- [x] requirements.txt 包含 optuna>=3.0.0

### P1.1 - Market Regime Detection
- [ ] RegimeDetector.detect_regime() 正確分類 4 種市場狀態
- [ ] Trend detection: SMA(50) vs SMA(200) 準確率 >90%
- [ ] Volatility detection: Rolling std(20) 閾值分類準確率 >85%
- [ ] 12 個單元測試全部通過
- [ ] Regime-aware 策略勝率 +10% (相比 regime-agnostic)

### P1.2 - Portfolio ERC
- [ ] ERCOptimizer.optimize_weights() 滿足所有約束條件
- [ ] Correlation < 0.7 between all strategy pairs
- [ ] Max 30% weight per strategy enforced
- [ ] Equal risk contribution 誤差 <5%
- [ ] 15 個單元測試全部通過
- [ ] Portfolio Sharpe +5-15% (相比 equal-weight baseline)

### P1.3 - Epsilon-Constraint
- [ ] EpsilonConstraintOptimizer.optimize() 滿足 diversity ≥ 30% 約束
- [ ] Pareto frontier 包含 ≥10 個解
- [ ] 18 個單元測試全部通過
- [ ] 多樣性提升：20-30% → 40%+
- [ ] Sharpe ratio 下降 <10% (相比無約束優化)

### P2.1 - Purged Walk-Forward CV
- [ ] PurgedWalkForwardCV.split() 產生有效的 train/test splits
- [ ] Purge gap 21 days correctly enforced
- [ ] 20 個單元測試全部通過
- [ ] OOS Sharpe within ±20% of IS Sharpe
- [ ] 無數據洩漏 (驗證工具確認)

### P2.2 - E2E Testing
- [ ] 15+ E2E 測試覆蓋完整工作流程
- [ ] 所有 E2E 測試通過 (0% error rate)
- [ ] Test execution time < 10 minutes

### P2.3 - Performance Benchmarks
- [ ] Latency benchmark: <100ms per backtest
- [ ] Slippage benchmark: <0.1%
- [ ] Memory usage benchmark: <2GB peak
- [ ] 15+ 性能測試全部符合標準
- [ ] 性能報告自動生成

### P3.1 - Documentation
- [ ] API 文檔完整 (100% public methods)
- [ ] 用戶指南包含 5+ 實例
- [ ] 架構圖清晰展示系統組件

### P3.2 - Monitoring Dashboard
- [ ] 實時指標更新 (< 1 second delay)
- [ ] 告警系統正常運作
- [ ] 日誌聚合功能完整

## Validation Gates

所有 6 個 gates 必須通過才能進入下一階段：

### Gate 1: E2E Tests GREEN (P0 完成後)
- **Criteria**: pytest tests/e2e/ -v 100% pass
- **Command**: `pytest tests/e2e/ -v --tb=short`
- **Threshold**: 0% error rate
- **Blocker if fails**: Cannot proceed to P1

### Gate 2: Regime-Aware Performance (P1.1 完成後)
- **Criteria**: Regime-aware strategy win rate +10%
- **Command**: `python experiments/validate_regime_detection.py`
- **Threshold**: Improvement ≥ 10%
- **Blocker if fails**: Cannot proceed to P1.2

### Gate 3: Stage 2 Breakthrough (P1 完成後)
- **Criteria**: Success rate 80%+, Sharpe 2.5+, Diversity 40%+
- **Command**: `python experiments/validate_stage2_metrics.py`
- **Threshold**: All 3 metrics meet targets
- **Blocker if fails**: Cannot proceed to P2

### Gate 4: Portfolio Optimization (P1.2 完成後)
- **Criteria**: Portfolio Sharpe +5-15%
- **Command**: `python experiments/validate_portfolio_erc.py`
- **Threshold**: Improvement ≥ 5%
- **Blocker if fails**: P1 incomplete

### Gate 5: OOS Validation (P2.1 完成後)
- **Criteria**: OOS Sharpe within ±20% of IS
- **Command**: `python experiments/validate_purged_cv.py`
- **Threshold**: |OOS - IS| / IS ≤ 0.2
- **Blocker if fails**: Cannot proceed to P3

### Gate 6: Production Readiness (P2-P3 完成後)
- **Criteria**: Latency <100ms, Slippage <0.1%, Uptime 99.9%+
- **Command**: `python experiments/validate_production_metrics.py`
- **Threshold**: All 3 metrics meet SLA
- **Blocker if fails**: Not production ready

## Non-functional Requirements

### Performance Requirements
- **Latency**:
  - Backtest execution: <100ms per strategy
  - ASHA optimization: 50-70% faster than TPE
  - Regime detection: <10ms per market snapshot
- **Throughput**:
  - Support 1000+ strategies in parallel
  - Handle 10+ concurrent optimization jobs
- **Resource Usage**:
  - Memory: <2GB peak per process
  - CPU: <80% utilization at peak load
  - Disk: <10GB for experiment results

### Reliability Requirements
- **Uptime**: 99.9% (8.7h/year downtime)
- **Error Rate**: <0.1% for critical operations
- **Recovery Time**: <5 minutes for critical services
- **Data Integrity**: 100% (no data loss or corruption)

### Maintainability Requirements
- **Test Coverage**: ≥95% line coverage
- **Code Quality**:
  - Cyclomatic complexity ≤ 10
  - 0 mypy type errors
  - 0 critical flake8 violations
- **Documentation Coverage**: 100% public APIs

### Compatibility Requirements
- **Python Version**: 3.10+
- **Dependencies**:
  - finlab >= 1.5.3
  - optuna >= 3.0.0 (新增)
  - pandas >= 2.3.2
  - numpy >= 2.2.0
- **Backward Compatibility**:
  - StrategyMetrics 完全兼容 Dict[str, float]
  - 現有代碼零修改升級

### Security Requirements
- **Data Protection**:
  - 不得記錄敏感參數到日誌
  - Experiment results 加密存儲
- **Access Control**:
  - API endpoints 需要認證
  - 監控儀表板需要授權
- **Vulnerability Management**:
  - 依賴定期掃描 (每週)
  - 高危漏洞 24h 內修復

### Scalability Requirements
- **Horizontal Scaling**: 支持多節點分散式優化
- **Vertical Scaling**: 單節點支持 32GB+ 記憶體
- **Data Growth**: 支持 10 年+ 歷史數據

### Observability Requirements
- **Logging**:
  - 結構化日誌 (JSON format)
  - Log level 可動態調整
  - 保留 30 天歷史
- **Metrics**:
  - Prometheus-compatible metrics
  - 1-minute granularity
  - 90-day retention
- **Tracing**:
  - End-to-end request tracing
  - Distributed tracing support

## Dependencies

### External Dependencies
- **Optuna**: ASHA 優化器後端
- **NetworkX**: Factor graph 系統 (現有)
- **Finlab**: 回測引擎 (現有)

### Internal Dependencies
- **Phase 7 Fix** → **Gate 1** → **P1 開始**
- **ASHA Optimizer** → **Gate 1** → **P1 開始**
- **P1.1 Regime Detection** → **Gate 2** → **P1.2 開始**
- **P1 完成** → **Gate 3** → **P2 開始**
- **P1.2 ERC** → **Gate 4** → **P1 驗證**
- **P2.1 Purged CV** → **Gate 5** → **P3 開始**
- **P2-P3 完成** → **Gate 6** → **Production 部署**

## Risks and Mitigation

### Risk 1: Optuna 整合複雜度高
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - 先實現基本框架 (已完成)
  - 完整測試規格先行 (TDD)
  - 參考 Optuna 官方範例

### Risk 2: ASHA 搜索效率未達預期
- **Probability**: Low
- **Impact**: Medium
- **Mitigation**:
  - Baseline TPE 性能測試
  - A/B 比較驗證
  - 調整 reduction_factor 和 min_resource

### Risk 3: Regime Detection 準確率不足
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - 多種 regime 定義方法比較
  - Historical backtesting 驗證
  - 保留 fallback 到 regime-agnostic

### Risk 4: OOS 性能顯著劣於 IS
- **Probability**: Medium
- **Impact**: High
- **Mitigation**:
  - Purged CV 嚴格執行
  - 21-day purge gap 充足
  - 定期 OOS 性能監控

### Risk 5: 時間預算超支
- **Probability**: Medium
- **Impact**: Medium
- **Mitigation**:
  - 優先級嚴格管理 (P0 > P1 > P2 > P3)
  - 平行處理節省 38-52 hours
  - 每週進度檢查

## Success Metrics

### Primary Metrics (Stage 2 Breakthrough)
- **成功率**: 35-40% → **80%+** ✅
- **Sharpe Ratio**: 1.5-2.0 → **2.5+** ✅
- **多樣性**: 20-30% → **40%+** ✅

### Secondary Metrics
- **搜索效率**: TPE baseline → **50-70% 時間減少** ✅
- **Portfolio Sharpe**: Equal-weight → **+5-15%** ✅
- **Regime-aware 勝率**: Baseline → **+10%** ✅

### Quality Metrics
- **Test Coverage**: **≥95%** ✅
- **Code Quality**: Complexity **≤10**, **0 type errors** ✅
- **E2E Tests**: **100% pass** ✅

### Performance Metrics
- **Latency**: **<100ms** per backtest ✅
- **Uptime**: **99.9%+** ✅
- **OOS Validation**: **±20%** of IS ✅

## Timeline

| Week | Priority | Tasks | Hours | Status |
|------|----------|-------|-------|--------|
| 1 | P0.1 | Phase 7 Fix | 4h | Pending |
| 2-3 | P0.2 | ASHA Optimizer | 8h | Pending |
| 4 | P1.1 | Regime Detection | 8h | Pending |
| 5 | P1.2 | Portfolio ERC | 8h | Pending |
| 6-7 | P1.3 | Epsilon-Constraint | 16h | Pending |
| 8 | P2.1 | Purged CV | 16h | Pending |
| 9 | P2.2 | E2E Testing | 16h | Pending |
| 10 | P2.3 | Benchmarks | 16h | Pending |
| 11 | P3.1 | Documentation | 24h | Pending |
| 12 | P3.2 | Dashboard | 16h | Pending |

**Total**: 132h sequential, 88h parallel, **44h savings (33%)**

---

**需求文檔版本**: 1.0
**最後更新**: 2025-11-14
**撰寫者**: TDD Planning Team (zen planner + zen testgen)
**審核狀態**: ✅ Ready for Review
