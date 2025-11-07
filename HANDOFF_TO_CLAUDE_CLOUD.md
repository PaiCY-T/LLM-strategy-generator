# Handoff to Claude Cloud - Hybrid Architecture Implementation

**Date**: 2025-11-08
**Current Status**: Architecture analysis complete, ready for Phase 1 investigation
**Priority**: 🔴 HIGH - Blocking pilot phase re-execution

---

## 當前狀況概述

### 已完成的工作 ✅

1. **Bug 修復完成**（learning_loop.py）
   - 修正 champion_tracker API 錯誤（3 處）
   - 創建整合測試驗證修復
   - 所有測試通過

2. **Pilot Phase 執行完成**
   - 300 次迭代全部完成
   - 結果：0/300 成功（NotImplementedError）
   - 原因：Factor Graph execution 未實作

3. **架構分析完成**（zen thinkdeep + zen chat）
   - 發現 5 個關鍵架構缺陷
   - 修正時程估計：1 天 → 2-3 天
   - 獲得 Gemini 2.5 Pro 專家審批

### 當前阻礙 🚫

**根本原因**：Factor Graph Strategy 物件無法執行回測

```python
# 當前錯誤
NotImplementedError: Factor Graph execution not yet integrated
```

**技術根源**：
- Learning loop 嘗試執行 Factor Graph strategies
- BacktestExecutor 只處理 Python code strings
- Strategy DAG 物件無法執行（沒有 `to_python_code()` 方法）

---

## 必須閱讀的文件 📚

### 1. 架構分析報告（按閱讀順序）

#### A. Executive Summary（先讀這個）
**文件**：`.spec-workflow/specs/phase3-learning-iteration/ARCHITECTURE_REVIEW_SUMMARY.md`

**內容**：
- 執行摘要（5 分鐘閱讀）
- P0/P1/P2 問題清單
- 修訂後的 6 階段實作計劃
- 立即行動項目

**關鍵章節**：
- "立即行動項目" → 明確下一步
- "修訂後的實作計劃" → 完整路線圖
- "對比原始提案" → 了解為何修訂

#### B. 完整技術分析（需要深入理解時讀）
**文件**：`.spec-workflow/specs/phase3-learning-iteration/HYBRID_ARCHITECTURE_REFINED_ANALYSIS.md`

**內容**：
- 完整 thinkdeep 分析（9,000+ 字）
- 所有證據和程式碼引用
- 詳細的問題分析
- 6 階段實作細節

**關鍵章節**：
- "Critical Findings" → 理解每個 P0 blocker
- "Revised Implementation Plan" → 詳細任務分解
- "File Changes Required" → 具體程式碼改動

#### C. 原始架構發現
**文件**：`.spec-workflow/specs/phase3-learning-iteration/CRITICAL_FINDING_FACTOR_GRAPH_ARCHITECTURE.md`

**內容**：
- 最初發現 `to_python_code()` 不存在
- 混合架構的初始提案
- 為什麼需要混合架構

### 2. 關鍵程式碼文件

需要理解的核心檔案：
```
src/learning/learning_loop.py          # 主學習循環（已修復）
src/learning/champion_tracker.py       # Champion 管理（需要重構）
src/backtest/executor.py               # 回測執行器（需要擴展）
src/factor_graph/strategy.py           # Strategy DAG 結構
artifacts/working/modules/performance_attributor.py  # 參數提取
```

---

## 🔴 立即行動：Phase 1 Investigation

### 優先級：CRITICAL（必須先完成）

#### 任務：調查 finlab API 相容性

**時間估計**：2-3 小時

**必須回答的問題**：

1. **finlab.backtest.sim() 是否接受 signal DataFrame？**
   ```python
   # 測試這個是否有效
   signals_df = strategy.to_pipeline(data)  # 返回 DataFrame
   positions = signals_df['positions']      # ← 欄位名稱是什麼？
   report = finlab.backtest.sim(positions, ...)  # ← 這樣可行嗎？
   ```

2. **strategy.to_pipeline() 輸出格式是什麼？**
   - 返回什麼欄位？
   - "positions" 信號的欄位名稱是什麼？
   - 如何識別最終交易信號？

3. **如何從 signals 轉換為 metrics？**
   - 需要什麼中間步驟？
   - 是否有現成的 API？
   - 還是需要自己實作 Sharpe ratio 計算？

#### 調查方法建議

**方法 1：檢查 finlab 文檔**
```bash
# 尋找 finlab 文檔或範例
find . -name "*.md" -o -name "*.rst" | xargs grep -l "backtest\|sim"
```

**方法 2：檢查現有程式碼使用方式**
```bash
# 查看 finlab.backtest.sim 如何被使用
grep -r "finlab.backtest.sim" --include="*.py"
grep -r "to_pipeline" --include="*.py"
```

**方法 3：創建測試腳本**
```python
# test_finlab_api.py
from src.factor_graph.strategy import Strategy
import finlab

# 載入測試 Strategy
strategy = load_test_strategy()

# 執行 pipeline
signals_df = strategy.to_pipeline(test_data)
print("Output columns:", signals_df.columns.tolist())
print("Sample data:", signals_df.head())

# 嘗試轉換為回測
# ... 測試不同的 API 調用方式
```

#### 可能的結果與應對

**情境 A：finlab API 直接支援**（最佳）
- Phase 4 實作簡單（4-6 小時）
- 總時程維持 2-3 天

**情境 B：需要中間轉換層**（中等）
- Phase 4 需要額外邏輯（+2-3 小時）
- 總時程可能延長到 3 天

**情境 C：需要自己計算 metrics**（最壞）
- 需要實作 Sharpe ratio、returns、drawdown 計算
- Phase 4 變成 6-10 小時
- 總時程延長到 3-4 天

---

## 後續階段概覽

### Phase 2: Hybrid Dataclass（2-3 小時）
**依賴**：無（可以與 Phase 1 並行）

**任務**：
1. 實作混合 ChampionStrategy dataclass
2. 實作 Strategy DAG metadata 提取函數
3. 編寫單元測試

**可交付成果**：
- `src/learning/champion_strategy.py`（新文件）
- `tests/learning/test_champion_strategy.py`（新文件）

### Phase 3: ChampionTracker 重構（3-4 小時）
**依賴**：Phase 2

**任務**：
1. 重構 `_create_champion()` 為雙路徑
2. 處理 LLM ↔ Factor Graph 過渡情境
3. 更新 `promote_to_champion()`
4. 編寫單元測試

**關鍵檔案**：
- `src/learning/champion_tracker.py`（約 100 行改動）

### Phase 4: BacktestExecutor 擴展（4-6 小時）
**依賴**：Phase 1（CRITICAL）

**任務**：
1. 實作 `execute_strategy_dag()` 方法
2. 實作 metrics 提取邏輯
3. 更新路由邏輯
4. 編寫單元測試

**關鍵檔案**：
- `src/backtest/executor.py`（新增約 50 行）

### Phase 5: Strategy 序列化（4-6 小時）
**依賴**：Phase 2

**任務**：
1. 實作 JSON-like Strategy encoder/decoder
2. 更新 IterationHistory
3. 編寫序列化測試

**技術方案**：Custom JSON serialization（Option 3）

### Phase 6: 整合測試（2-3 小時）
**依賴**：Phase 2-5

**任務**：
1. 端到端整合測試（15 個測試）
2. 手動驗證
3. 文檔更新

---

## 關鍵技術決策 🎯

### 已確定的決策（請遵循）

1. **序列化方案：Option 3 (Custom JSON)**
   - 理由：可讀性、可版本控制、可除錯
   - 放棄：Option 1 (Registry) 太複雜，Option 2 (Pickle) 技術債高

2. **parameters/success_patterns：設為 Optional**
   - 理由：factor_graph 方法可能不適用這些概念
   - 實作：根據 generation_method 條件處理

3. **過渡情境：使用模板庫**
   - 理由：LLM code → Strategy DAG 轉換太複雜
   - 實作：當 champion.strategy 為 None 時，從模板選起點

### 待決策的問題（需要 Phase 1 結果）

1. **Metrics 計算方法**
   - 等待 finlab API 調查結果
   - 決定採用情境 A/B/C

2. **DAG metadata schema**
   - 定義 Strategy DAG 的"parameters"
   - 定義 Strategy DAG 的"success_patterns"

---

## 測試策略 🧪

### 單元測試（每個 Phase）
- Phase 2: 15 tests (dataclass + metadata)
- Phase 3: 10 tests (tracker refactoring)
- Phase 4: 10 tests (executor extension)
- Phase 5: 10 tests (serialization)
- **小計**：45 tests

### 整合測試（Phase 6）
- LLM → Factor Graph transition: 5 tests
- Factor Graph → LLM transition: 5 tests
- Hybrid execution paths: 5 tests
- **小計**：15 tests

### 總計：60 tests

---

## 風險與應對 ⚠️

### 高風險（P0）

**風險 1：finlab API 不支援 signal DataFrame**
- **可能性**：中等
- **影響**：+1-2 天工作量
- **應對**：Phase 1 優先調查，確定後再繼續

**風險 2：Factor 物件無法序列化為 JSON**
- **可能性**：低-中等
- **影響**：需要退回 Pickle（技術債）
- **應對**：Phase 5 早期測試序列化

### 中風險（P1）

**風險 3：Metrics 不一致**
- **可能性**：中等
- **影響**：實驗結果不可比較
- **應對**：Phase 6 驗證測試

### 低風險（P2）

**風險 4：時程超支**
- **可能性**：中等
- **影響**：可能需要 3-4 天而非 2-3 天
- **應對**：保守估計，留有緩衝

---

## 檢查點與里程碑 📍

### Checkpoint 1：Phase 1 完成
**標準**：
- ✅ finlab API 相容性已確定
- ✅ Metrics 提取路徑已明確
- ✅ 更新 Phase 4 計劃（如需要）

**決策點**：是否繼續 Phase 4？還是需要調整方案？

### Checkpoint 2：Phase 2-3 完成
**標準**：
- ✅ ChampionStrategy dataclass 實作完成
- ✅ ChampionTracker 雙路徑重構完成
- ✅ 所有單元測試通過（25 tests）

**決策點**：繼續 Phase 4-5

### Checkpoint 3：Phase 4-5 完成
**標準**：
- ✅ BacktestExecutor 支援 Strategy 執行
- ✅ Strategy 序列化/反序列化完成
- ✅ 所有單元測試通過（45 tests）

**決策點**：開始整合測試

### Milestone：全部完成
**標準**：
- ✅ 所有 60 tests 通過
- ✅ 手動驗證成功
- ✅ 文檔更新完成
- ✅ **可以重新執行 pilot phase**

---

## 成功標準 ✨

### 技術標準

1. **功能完整性**
   - ✅ Factor Graph strategies 可以執行回測
   - ✅ LLM 和 Factor Graph 路徑都正常工作
   - ✅ Champion 可以在兩種方法間切換

2. **程式碼品質**
   - ✅ 60 tests 全部通過
   - ✅ 無回歸（現有 LLM 路徑不受影響）
   - ✅ 類型檢查通過（mypy）

3. **效能標準**
   - ✅ Strategy 執行時間 < LLM 執行時間
   - ✅ 序列化開銷可接受（< 100ms per strategy）

### 業務標準

1. **可以重新執行 pilot phase**
   - 300 iterations 可以完成
   - 獲得實際 Sharpe ratio metrics
   - 生成統計分析報告

2. **實驗可以繼續**
   - Full study 可以執行（3000 iterations）
   - 數據品質符合實驗要求

---

## 資源與參考 📚

### 相關文件位置

```
.spec-workflow/specs/phase3-learning-iteration/
├── ARCHITECTURE_REVIEW_SUMMARY.md           # 執行摘要（先讀這個）
├── HYBRID_ARCHITECTURE_REFINED_ANALYSIS.md  # 完整分析
└── CRITICAL_FINDING_FACTOR_GRAPH_ARCHITECTURE.md  # 原始發現

src/learning/
├── learning_loop.py          # 主循環（已修復）
├── champion_tracker.py       # 需要重構
├── iteration_executor.py     # 需要了解
└── feedback_generator.py     # 了解參考

src/backtest/
└── executor.py              # 需要擴展

src/factor_graph/
├── strategy.py              # Strategy DAG 結構
└── mutations.py             # 變異函數

tests/integration/
└── test_learning_loop_champion_integration.py  # 整合測試範例
```

### Git 歷史參考

```bash
# 查看最近的修復
git log --oneline -10

# 查看 learning_loop.py 的改動
git log -p src/learning/learning_loop.py

# 查看整合測試
git log -p tests/integration/test_learning_loop_champion_integration.py
```

---

## 交接清單 ✓

### 給 Claude Cloud 的檢查清單

- [ ] 已閱讀 ARCHITECTURE_REVIEW_SUMMARY.md
- [ ] 理解 5 個 P0/P1 架構缺陷
- [ ] 理解為何時程從 1 天變成 2-3 天
- [ ] 理解 Phase 1 為何是最高優先級
- [ ] 已閱讀 HYBRID_ARCHITECTURE_REFINED_ANALYSIS.md（至少 "Critical Findings" 部分）
- [ ] 理解混合架構的技術方案
- [ ] 準備好開始 Phase 1 investigation

### 開始工作前

1. **拉取最新代碼**
   ```bash
   git pull origin main
   ```

2. **確認文件位置**
   ```bash
   ls -la .spec-workflow/specs/phase3-learning-iteration/
   ```

3. **閱讀執行摘要**（5-10 分鐘）
   ```bash
   cat .spec-workflow/specs/phase3-learning-iteration/ARCHITECTURE_REVIEW_SUMMARY.md
   ```

4. **開始 Phase 1**
   - 時間：預留 2-3 小時
   - 目標：回答 3 個關鍵問題
   - 輸出：API 相容性文件

---

## 聯絡與支援 📞

### 如果遇到問題

1. **技術問題**
   - 參考完整分析文件
   - 查看原始程式碼
   - 檢查測試案例

2. **方向不明確**
   - 重新閱讀 ARCHITECTURE_REVIEW_SUMMARY.md
   - 查看 "立即行動項目" 章節

3. **需要更多背景**
   - 閱讀 CRITICAL_FINDING_FACTOR_GRAPH_ARCHITECTURE.md
   - 查看 git 歷史

---

## 預期時程 📅

假設從今天開始：

- **Day 1 上午**：Phase 1 investigation（2-3 小時）
- **Day 1 下午**：Phase 2 implementation（2-3 小時）
- **Day 2 上午**：Phase 3 implementation（3-4 小時）
- **Day 2 下午**：Phase 4 implementation（4-6 小時）或延續到 Day 3
- **Day 3 上午**：Phase 5 implementation（4-6 小時）
- **Day 3 下午**：Phase 6 integration tests（2-3 小時）

**總時程**：2.5 - 3.5 天實際開發時間

---

## 最後提醒 💡

### 關鍵成功因素

1. **不要跳過 Phase 1**
   - 這是最重要的調查
   - 決定後續 90% 的實作細節

2. **遵循已確定的技術決策**
   - Option 3 (JSON serialization)
   - Optional parameters/success_patterns
   - 模板庫處理過渡

3. **保持測試覆蓋率**
   - 每個 Phase 都要寫測試
   - 整合測試必須涵蓋過渡情境

4. **及時更新文檔**
   - Phase 1 結果要記錄
   - 重要決策要更新到文件

---

**準備好了嗎？從 Phase 1 開始！** 🚀

祝順利！如有問題，所有答案都在文件裡。
