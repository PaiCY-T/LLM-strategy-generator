# Finlab 專案待辦事項清單

**生成日期**: 2025-10-11
**專案狀態**: Production Ready (MVP Complete, Zen Debug Complete)
**下一階段**: Template System Phase 2 + AST Migration

---

## 🎯 高優先級任務 (High Priority)

### P0: Template System Phase 2 實施

**狀態**: Ready for Review → Awaiting User Approval to Start
**預估時間**: 2-3 weeks
**相依性**: None (可立即開始)

#### 核心子任務:

1. **實現4個核心策略模板** (Week 1)
   - **TurtleTemplate**: 多層AND過濾模式
     - 6層過濾: 殖利率、技術、營收、品質、內部人、流動性
     - 參數網格: 14個參數
     - 預期Sharpe: 1.5-2.5
     - 驗證: Phase 1已證實80%成功率

   - **MastiffTemplate**: 逆勢反轉模式
     - 特色: 最低成交量選擇（創新策略）
     - 參數網格: 10個參數
     - 預期Sharpe: 1.2-2.0

   - **FactorTemplate**: 單因子聚焦模式
     - 低週轉率、穩定收益
     - 參數網格: 8個參數
     - 預期Sharpe: 0.8-1.3

   - **MomentumTemplate**: 動能+催化劑模式
     - 快速反應、高週轉
     - 參數網格: 9個參數
     - 預期Sharpe: 0.8-1.5

2. **建立Hall of Fame儲存庫系統** (Week 2)
   - **三層架構**:
     - Champions (Sharpe ≥2.0): `hall_of_fame/champions/`
     - Contenders (Sharpe 1.5-2.0): `hall_of_fame/contenders/`
     - Archive (Sharpe <1.5): `hall_of_fame/archive/`

   - **儲存規格**:
     - JSON格式序列化（已優化：2-5x faster than YAML）
     - 完整策略基因組: code, parameters, metrics, success_patterns
     - 新穎度評分: 使用vector caching（M1優化）
     - 相似度查詢: <500ms for 100 strategies

   - **整合點**:
     - 與現有champion tracking整合（C1修復確保統一API）
     - 使用NoveltyScorer vector caching（M1修復）
     - 自動分層管理（>100策略時壓縮Archive）

3. **建立模板驗證系統** (Week 2)
   - **驗證檢查**:
     - 參數範圍驗證
     - 架構模式驗證（TurtleTemplate需確認6層AND）
     - 生成代碼符合模板規格

   - **錯誤分類**:
     - CRITICAL: 阻止執行
     - MODERATE: 警告但繼續
     - LOW: 記錄但忽略

   - **參數敏感度測試** (Optional Quality Check):
     - 時間成本: 50-75 min per strategy（M2已記錄）
     - 使用場景: Champion最終驗證
     - 跳過場景: 快速開發迭代

4. **模板反饋整合** (Week 3)
   - 基於當前表現推薦最佳模板
   - Champion降級時建議同模板調參
   - 探索模式時推薦不同模板

**成功標準**:
- [ ] 4個模板全部實現並通過單元測試
- [ ] Hall of Fame儲存並管理30+ turtle變體（來自Phase 1）
- [ ] 模板驗證達到>90%錯誤捕獲率
- [ ] 30個turtle變體測試: ≥20/30 (67%) 達到Sharpe >1.5

**交付物**:
- `src/templates/turtle_template.py`
- `src/templates/mastiff_template.py`
- `src/templates/factor_template.py`
- `src/templates/momentum_template.py`
- `src/repository/hall_of_fame.py` (擴展)
- `src/validation/template_validator.py`
- `tests/test_templates.py`
- `TEMPLATE_SYSTEM_COMPLETE.md`

---

### P1: Phase 5 - AST-based Parameter Extraction Migration

**狀態**: Planned (技術債務)
**預估時間**: 1-2 weeks
**相依性**: MVP完成, Zen Debug完成
**當前狀態**: Regex實現（90%提取成功率）

#### 動機:

**當前Regex限制** (MVP 80/20解決方案):
- 模式匹配局限: 只能處理簡單參數模式
- 提取失敗: 10%複雜模式無法提取
- 維護成本: 每新增一種模式需更新regex
- 準確性: 依賴字符串匹配，易誤判

**AST優勢**:
- 語法樹分析: 100%覆蓋所有參數類型
- 語義理解: 區分變數定義、函數調用、運算式
- 可擴展性: 支援複雜巢狀結構
- 可靠性: 基於Python語法，不受格式影響

#### 實施計劃:

**Week 1: AST Extractor核心實現**
1. 創建`ast_parameter_extractor.py`:
   - 使用Python `ast`模組解析策略代碼
   - 識別`data.get()`, `.rolling()`, `.shift()`, `.average()`等調用
   - 提取參數值和上下文

2. 單元測試（覆蓋率>90%）:
   - 測試所有8個關鍵參數提取
   - 測試複雜巢狀結構
   - 測試邊界情況（負數、科學記號、變數引用）

**Week 2: 整合與驗證**
3. 整合到`performance_attributor.py`:
   - 替換`extract_strategy_params()`實現
   - 保持向後兼容API
   - 添加fallback機制（AST失敗 → regex備份）

4. 回歸測試:
   - 對歷史150次迭代重新提取參數
   - 比較AST vs Regex提取結果
   - 驗證提升準確率（目標: 90% → 98%+）

5. 更新文檔:
   - `ARCHITECTURE.md`: 更新參數提取流程圖
   - `performance_attributor.py`: 更新docstring

**成功標準**:
- [ ] AST提取成功率: >98%（比Regex的90%提升8%）
- [ ] 向後兼容: 所有現有功能正常運作
- [ ] 性能: AST提取時間 <200ms（與Regex相當）
- [ ] 測試覆蓋率: >90%

**交付物**:
- `src/analysis/ast_parameter_extractor.py` (NEW)
- `performance_attributor.py` (MODIFIED)
- `tests/test_ast_extraction.py` (NEW)
- `AST_MIGRATION_COMPLETE.md`

---

## 🔧 中優先級任務 (Medium Priority)

### P2: Long-term Stability Monitoring

**狀態**: Recommended Post-MVP
**預估時間**: Ongoing (1-2 hours setup + daily monitoring)
**相依性**: MVP完成

**目標**:
- 驗證系統在20-50次迭代的穩定性
- 識別長期失敗模式和趨勢
- 收集數據以優化參數和閾值

**實施計劃**:

1. **創建監控腳本** (30 min):
   ```python
   # monitor_long_term.py

   import logging
   from autonomous_loop import AutonomousLoop
   from datetime import datetime

   def run_long_term_monitoring(num_iterations=30):
       """Run extended validation and collect metrics."""

       loop = AutonomousLoop(model='google/gemini-2.5-flash', max_iterations=num_iterations)

       metrics_log = []
       for i in range(num_iterations):
           success, feedback = loop.run_iteration(i, data)

           # Log metrics
           if success:
               metrics = loop.history.get_metrics(i)
               metrics_log.append({
                   'iteration': i,
                   'sharpe': metrics['sharpe_ratio'],
                   'champion_updated': loop.champion.iteration_num == i if loop.champion else False,
                   'timestamp': datetime.now().isoformat()
               })

           # Checkpoint every 10 iterations
           if (i + 1) % 10 == 0:
               save_checkpoint(metrics_log, i+1)

       # Generate stability report
       generate_stability_report(metrics_log)
   ```

2. **定義監控指標** (15 min):
   - Champion穩定性: 更新頻率、改進幅度
   - Preservation有效性: 違反頻率、重試成功率
   - 執行失敗率: 趨勢分析、失敗類型分類
   - Sharpe分佈: 平均值、標準差、最大回撤

3. **設置自動化報告** (30 min):
   - 每10次迭代生成中期報告
   - 最終生成完整穩定性分析
   - 識別需要調整的參數

**成功標準**:
- [ ] 完成20-50次迭代監控
- [ ] Champion更新頻率: 2-5次 (健康範圍)
- [ ] Preservation違反率: <10%
- [ ] 執行成功率: >70%

**交付物**:
- `monitor_long_term.py`
- `LONG_TERM_STABILITY_REPORT.md`

---

### P2: M3 Optional Optimization - Unified Dataset Registry

**狀態**: Optional (Zen Debug建議)
**預估時間**: 1 hour
**優先級**: Very Low (no bug, architectural cleanup only)

**當前狀態**:
- Zen Debug M3驗證: **NO BUG** - 最小重疊，架構合理
- NoveltyScorer有獨立dataset registry用於特徵提取
- DataValidator有KNOWN_DATASETS registry用於驗證

**動機** (可選):
- 減少維護成本（單一數據源）
- 確保dataset列表一致性
- 簡化新dataset添加流程

**實施計劃** (如果執行):

1. 創建共享registry (20 min):
   ```python
   # src/constants.py or src/registry/datasets.py

   FINLAB_DATASETS = {
       # Price data
       'price:收盤價', 'price:開盤價', 'price:最高價', 'price:最低價',
       'price:成交股數', 'price:成交金額',

       # Revenue data
       'monthly_revenue:當月營收', 'monthly_revenue:去年同期營收',
       'monthly_revenue:上月營收', 'monthly_revenue:去年當月營收',

       # ... all 50+ datasets ...
   }
   ```

2. 更新使用點 (30 min):
   - `data_validator.py`: Import from shared registry
   - `novelty_scorer.py`: Import from shared registry
   - 保持向後兼容

3. 測試 (10 min):
   - 驗證所有validator測試通過
   - 驗證novelty scorer測試通過

**成功標準**:
- [ ] 單一數據源
- [ ] 所有測試通過
- [ ] 向後兼容

**交付物**:
- `src/registry/datasets.py` (NEW) or update `constants.py`
- `data_validator.py` (MODIFIED)
- `novelty_scorer.py` (MODIFIED)

---

## 🚀 功能增強 (Feature Enhancements)

### P3: IC/ICIR Factor Evaluation System

**狀態**: Planned Enhancement
**預估時間**: 2-3 days
**業務價值**: 因子品質量化評估

**目標**:
實現Information Coefficient (IC) 和 Information Coefficient IR (ICIR) 評估，用於量化因子預測能力和穩定性。

**技術規格**:

**IC計算**:
```python
IC = correlation(factor_values[t], forward_returns[t+1])
```

**ICIR計算**:
```python
ICIR = mean(IC) / std(IC)
```

**實施計劃**:

1. **創建IC計算器** (Day 1):
   ```python
   # src/analysis/ic_calculator.py

   class ICCalculator:
       def calculate_ic(self, factor_values: pd.DataFrame, forward_returns: pd.DataFrame) -> pd.Series:
           """Calculate rolling IC for factor."""
           pass

       def calculate_icir(self, ic_series: pd.Series, window: int = 20) -> float:
           """Calculate ICIR over rolling window."""
           pass

       def generate_ic_report(self, factor_ic: pd.Series) -> dict:
           """Generate comprehensive IC analysis report."""
           pass
   ```

2. **整合到validation流程** (Day 2):
   - 在strategy backtesting後計算IC
   - 將IC/ICIR添加到metrics字典
   - 更新champion selection考慮IC/ICIR

3. **反饋系統整合** (Day 2-3):
   - 低IC (<0.05) 因子觸發警告
   - 建議改進方向（提高IC）
   - 在evolutionary prompts中包含IC分析

**成功標準**:
- [ ] IC計算器實現並通過測試
- [ ] IC/ICIR整合到backtest報告
- [ ] IC分析整合到反饋系統

**交付物**:
- `src/analysis/ic_calculator.py`
- `tests/test_ic_calculator.py`
- `IC_ICIR_INTEGRATION.md`

---

### P3: Dynamic Temperature Adjustment

**狀態**: Planned Enhancement
**預估時間**: 1 day
**業務價值**: 根據迭代階段優化創造力和穩定性平衡

**當前狀態**:
- Temperature固定為0.7
- 所有迭代使用相同創造力水平

**動機**:
- **早期探索** (Iter 0-3): 高溫度(0.8-1.0) 鼓勵多樣性
- **穩定優化** (Iter 4-7): 中溫度(0.5-0.7) 平衡創造力與穩定性
- **精細調整** (Iter 8+): 低溫度(0.3-0.5) 小幅調整Champion參數

**實施計劃**:

```python
# src/utils/temperature_scheduler.py

class TemperatureScheduler:
    def get_temperature(self, iteration_num: int, has_champion: bool, force_exploration: bool) -> float:
        """Dynamic temperature based on iteration phase."""

        if force_exploration:
            return 0.9  # High creativity for exploration mode

        if not has_champion:
            return 0.8  # Moderate-high for initial search

        # Progressive cooling schedule
        if iteration_num < 4:
            return 0.7  # Moderate for early optimization
        elif iteration_num < 8:
            return 0.5  # Lower for stable improvement
        else:
            return 0.4  # Low for fine-tuning
```

**成功標準**:
- [ ] Temperature scheduler實現
- [ ] 整合到prompt generation
- [ ] A/B測試驗證效果（vs固定溫度）

**交付物**:
- `src/utils/temperature_scheduler.py`
- `DYNAMIC_TEMPERATURE_RESULTS.md`

---

### P4: Parallel Iteration Execution

**狀態**: Future Enhancement
**預估時間**: 1 week
**業務價值**: 5-10x速度提升for grid search

**當前狀態**:
- 串行執行: 每次迭代30-45s
- 10次迭代總時間: ~7 minutes

**目標**:
- 並行執行3-5個候選策略
- 總時間縮短至~2 minutes for 10 iterations

**技術挑戰**:
- 資料共享: 多進程間共享finlab data
- LLM API限制: Rate limiting處理
- 結果聚合: 選擇最佳候選

**實施計劃** (待詳細設計):
1. 創建parallel executor使用multiprocessing
2. 實現data preloading和共享記憶體
3. 實現API rate limiting和retry邏輯
4. 更新autonomous loop支持並行模式

---

### P4: Web UI Dashboard (Streamlit)

**狀態**: Future Enhancement
**預估時間**: 2 weeks
**業務價值**: 即時監控和控制

**功能規劃**:
- 即時迭代進度顯示
- Champion evolution視覺化
- Performance metrics圖表（Sharpe趨勢、回撤等）
- Failure pattern分析
- 手動觸發iteration
- 參數調整介面

**技術棧**:
- Streamlit (快速原型)
- Plotly (互動式圖表)
- Real-time updates (WebSocket)

---

## 📚 文檔與測試 (Documentation & Testing)

### P2: Documentation Updates

**預估時間**: 2-3 hours

**需更新文檔**:

1. **README.md** (30 min):
   - 添加Post-MVP功能說明
   - 添加Steering Documents引用
   - 更新Quick Start with template system
   - 添加成功指標（70% success, Sharpe 2.48）

2. **ARCHITECTURE.md** (60 min):
   - 添加Template System架構圖
   - 更新Hall of Fame三層結構圖
   - 添加Vector Caching優化說明
   - 添加AST Migration路線圖

3. **API.md** (NEW - 30 min):
   - 記錄所有公開API
   - Template類介面
   - Hall of Fame查詢API
   - Validation API

4. **CHANGELOG.md** (30 min):
   - 記錄MVP完成 (2025-10-08)
   - 記錄Zen Debug完成 (2025-10-11)
   - 記錄所有bug修復和優化

---

## 📊 優先級矩陣

| 任務 | 優先級 | 預估時間 | 業務價值 | 技術風險 | 建議執行順序 |
|------|--------|---------|---------|---------|-------------|
| Template System Phase 2 | P0 | 2-3 weeks | 極高 | 低 | 1 |
| AST Migration (Phase 5) | P1 | 1-2 weeks | 高 | 中 | 2 |
| Long-term Monitoring | P2 | Ongoing | 中 | 低 | 3 |
| IC/ICIR Evaluation | P3 | 2-3 days | 中 | 低 | 4 |
| Dynamic Temperature | P3 | 1 day | 低-中 | 低 | 5 |
| Documentation Updates | P2 | 2-3 hours | 中 | 低 | 6 |
| M3 Unified Registry | P2 | 1 hour | 低 | 低 | 7 (Optional) |
| Parallel Execution | P4 | 1 week | 中 | 高 | 8 (Future) |
| Web UI Dashboard | P4 | 2 weeks | 中 | 中 | 9 (Future) |

---

## 🎯 建議執行路線圖

### 🚀 Phase A: Template System (Immediate - Week 1-3)

**目標**: 實現可重用策略模板系統，消除90%策略重複問題

1. Week 1: 實現4個核心模板
2. Week 2: 建立Hall of Fame系統
3. Week 3: 模板驗證與反饋整合
4. Milestone: 30個turtle變體達到67%+ Sharpe >1.5成功率

---

### 🔬 Phase B: AST Migration (Week 4-5)

**目標**: 提升參數提取準確率從90% → 98%+

1. Week 4: AST Extractor實現與測試
2. Week 5: 整合、驗證、文檔更新
3. Milestone: 歷史150次迭代重新驗證通過

---

### 📊 Phase C: Quality Enhancement (Week 6-7)

**目標**: 增強系統品質評估和監控能力

1. Week 6: IC/ICIR評估系統 + 長期監控腳本
2. Week 7: 動態溫度調整 + 文檔更新
3. Milestone: 50次迭代穩定性驗證通過

---

### 🌐 Phase D: Future Enhancements (Month 3+)

**可選功能**（根據業務需求決定）:
- Parallel execution
- Web UI dashboard
- Multi-market support
- Production deployment

---

## ✅ 下一步行動

### 立即執行 (This Week):

1. **用戶確認Steering Documents** (今天):
   - 審閱 `product.md`, `tech.md`, `structure.md`
   - 確認項目方向和技術決策
   - 提供修改意見（如有）

2. **啟動Template System Phase 2** (Week 1):
   - 用戶批准requirements.md
   - 開始Task 1: TurtleTemplate實現
   - 建立開發分支: `feature/template-system-phase2`

3. **設置監控基礎** (今天-明天):
   - 創建 `monitor_long_term.py` 腳本
   - 開始收集baseline metrics

---

**文檔版本**: 1.0
**最後更新**: 2025-10-11
**下次審閱**: Template System Phase 2完成後
