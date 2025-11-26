# 20次迭代三模式測試深度分析報告

**測試日期**：2025-11-15
**測試範圍**：60次迭代（Factor Graph Only: 20, LLM Only: 20, Hybrid: 20）
**分析師**：Claude Code + Zen MCP Thinkdeep

---

## 執行摘要

### ✅ 核心成就：SuccessClassifier 修復驗證成功

**分類邏輯正確性：100%**
- ✅ 所有 LEVEL_0（54個）：`execution_success=False`, `sharpe=None`
- ✅ 所有 LEVEL_3（6個）：`execution_success=True`, `sharpe>0`
- ✅ 沒有任何誤分類情況
- ✅ 修復完全成功，系統能正確識別策略品質

### 🚨 重大發現：Factor Graph 系統性架構缺陷

- **問題**：Factor Graph 完全失效（100% 失敗率）
- **影響**：Factor Graph Only mode 無法運作，Hybrid mode 效能下降 60%
- **嚴重性**：Critical (P0)
- **根因**：因子輸出命名與 FinLab 框架驗證需求不相容

---

## 1. 三種模式效能對比

### 1.1 總體效能指標

| 指標 | Factor Graph Only | LLM Only | Hybrid |
|------|------------------|----------|---------|
| **總迭代數** | 20 | 20 | 20 |
| **成功次數** | 0 | 5 | 1 |
| **成功率** | **0%** 🔴 | **25%** 🟢 | **5%** 🟡 |
| **LEVEL_3 計數** | 0 | 5 | 1 |
| **LEVEL_0 計數** | 20 | 15 | 19 |
| **平均 Sharpe** | N/A | 0.376 | 0.195 |
| **最佳 Sharpe** | N/A | 0.453 | 0.195 |
| **平均執行時間** | 3.9s/iter | 11.3s/iter | 6.8s/iter |
| **總執行時間** | 77s | 226s | 136s |

### 1.2 效能排名

**按成功率排序**：
1. 🥇 **LLM Only**: 25% 成功率
2. 🥈 **Hybrid**: 5% 成功率
3. 🥉 **Factor Graph Only**: 0% 成功率

**ROI 分析**（成功率/執行時間）：
- LLM Only: 0.022 (最佳)
- Hybrid: 0.007
- Factor Graph: 0.000

---

## 2. Factor Graph Only 模式分析

### 2.1 失敗統計

- **總迭代數**：20
- **成功次數**：0
- **失敗率**：100%
- **平均執行時間**：3.9秒/迭代

### 2.2 根本原因分析

**錯誤訊息**（所有 20 次迭代相同）：
```
ValueError: Strategy must have at least one factor producing position signals
(columns: ['position', 'positions', 'signal', 'signals']).
Current outputs: ['breakout_signal', 'momentum', 'rolling_trailing_stop_signal'].
```

**問題根源**：

1. **Factor Graph 產生的因子名稱**：
   - `breakout_signal`
   - `momentum`
   - `rolling_trailing_stop_signal`

2. **FinLab 框架要求的欄位名稱**：
   - `position` 或 `positions`
   - `signal` 或 `signals`

3. **結果**：命名不匹配 → 所有策略無法通過驗證 → 100% 失敗

### 2.3 問題分類

- **類型**：架構設計缺陷
- **範圍**：系統性問題（非個別策略問題）
- **影響**：完全阻斷 Factor Graph 功能
- **優先級**：P0（Critical）

---

## 3. LLM Only 模式分析

### 3.1 成功案例詳情

**總成功率：25%（5/20）**

| Iteration | Sharpe Ratio | Total Return | Max Drawdown | 分類 |
|-----------|-------------|--------------|--------------|------|
| 3 | 0.4532 | 92.08% | -38.25% | LEVEL_3 |
| 8 | 0.2645 | 40.60% | -62.22% | LEVEL_3 |
| 9 | 0.3650 | 68.46% | -43.72% | LEVEL_3 |
| 12 | 0.4464 | 94.44% | -42.18% | LEVEL_3 |
| 14 | 0.3512 | 62.30% | -44.43% | LEVEL_3 |

**成功策略特徵**：
- 平均 Sharpe：0.376
- Sharpe 範圍：0.265 - 0.453
- 平均報酬：71.6%
- 平均最大回撤：-46.2%

### 3.2 失敗案例分析

**總失敗率：75%（15/20）**

**失敗類型分布**：

| 錯誤類型 | 數量 | 佔比 | 主要原因 |
|---------|------|------|---------|
| Exception | 8 | 53% | 資料訪問錯誤（使用不存在的因子） |
| ValueError | 6 | 40% | 未建立 `report` 變數 |
| ValidationError | 1 | 7% | 其他驗證錯誤 |

**常見錯誤範例**：

1. **未建立 report 變數**（ValueError）：
   ```
   Strategy code did not create 'report' variable.
   Ensure code calls sim() and assigns result to 'report'
   ```

2. **資料不存在**（Exception）：
   ```
   Error: fundamental_features:股價淨值比 not exists
   ```

### 3.3 LLM 優勢分析

**成功因素**：
1. ✅ 能夠理解並遵循 FinLab 框架的命名規範
2. ✅ 正確使用 `position` 或 `signal` 等標準欄位名稱
3. ✅ 生成的策略符合回測執行要求
4. ✅ 25% 成功率顯示具備策略生成能力

**改進空間**：
1. ⚠️ 程式碼結構穩定性（40% 失敗因未建立 report）
2. ⚠️ 資料可用性驗證（53% 失敗因訪問不存在的因子）
3. ⚠️ 語法與邏輯驗證

---

## 4. Hybrid 模式分析

### 4.1 總體表現

- **總迭代數**：20
- **成功次數**：1
- **成功率**：5%
- **唯一成功**：Iteration 5（Sharpe=0.1953，由 LLM 生成）

### 4.2 生成方法分布

**完美的 50/50 分配**：

| 生成方法 | 迭代數 | 成功數 | 成功率 |
|---------|--------|--------|--------|
| LLM 生成 | 10 | 1 | **10%** |
| Factor Graph 生成 | 10 | 0 | **0%** |

### 4.3 關鍵發現

1. **唯一成功來自 LLM**：
   - Iteration 5 使用 LLM 生成
   - Sharpe=0.1953, Return=13.19%

2. **Factor Graph 在 Hybrid 中也完全失效**：
   - 10 次 Factor Graph 嘗試，0 次成功
   - 與 Factor Graph Only mode 一致的 100% 失敗率

3. **LLM 成功率差異**：
   - Hybrid 中的 LLM 成功率：10%（1/10）
   - LLM Only 中的成功率：25%（5/20）
   - 可能原因：樣本數較小導致的統計變異

### 4.4 理論預期 vs 實際表現

**理論預期**：
- 假設 LLM 成功率 25%，Factor Graph 成功率 0%
- Hybrid 預期成功率 = 0.5 × 0.25 + 0.5 × 0 = 12.5%

**實際表現**：
- 觀察到的成功率：5%（1/20）
- 低於理論預期，可能是樣本數不足（20次）

---

## 5. SuccessClassifier 分類邏輯驗證

### 5.1 分類標準回顧

| 分類 | 條件 | 描述 |
|------|------|------|
| LEVEL_0 | `execution_success = False` | 執行失敗（語法錯誤、運行崩潰） |
| LEVEL_1 | 指標覆蓋率 < 60% | 執行成功但指標不足 |
| LEVEL_2 | `sharpe_ratio ≤ 0` | 有效指標但策略不獲利 |
| LEVEL_3 | `sharpe_ratio > 0` | 獲利策略 |

### 5.2 驗證結果

**LEVEL_0 驗證**（54個樣本）：
- ✅ 所有 LEVEL_0 策略：`execution_success = False`
- ✅ 所有 LEVEL_0 策略：`sharpe_ratio = None`
- ✅ 分類正確：100%

**LEVEL_3 驗證**（6個樣本）：
- ✅ 所有 LEVEL_3 策略：`execution_success = True`
- ✅ 所有 LEVEL_3 策略：`sharpe_ratio > 0`
- ✅ Sharpe 範圍：0.1953 - 0.4532
- ✅ 分類正確：100%

**未觀察到的分類**：
- LEVEL_1：0個（無覆蓋率不足的情況）
- LEVEL_2：0個（無不獲利但有效的策略）

### 5.3 修復成功確認

**對比修復前的問題**：
- ❌ **修復前**：所有策略被錯誤分類為 LEVEL_0，即使有正向 Sharpe
- ✅ **修復後**：分類完全正確，Sharpe > 0 的策略正確分類為 LEVEL_3

**結論**：
- ✅ SuccessClassifier 初始化問題已完全修復
- ✅ 分類邏輯運作正常
- ✅ 系統能正確識別策略品質

---

## 6. 問題根因與技術細節

### 6.1 Factor Graph 命名衝突技術分析

**驗證流程**（`src/factor_graph/strategy.py:validate_data()`）：
```python
# 框架要求的信號欄位名稱
REQUIRED_SIGNAL_COLUMNS = ['position', 'positions', 'signal', 'signals']

# 實際檢查邏輯
signal_columns = [col for col in data.columns if col in REQUIRED_SIGNAL_COLUMNS]
if not signal_columns:
    raise ValueError(f"Strategy must have at least one factor producing position signals")
```

**Factor Graph 輸出**（實際）：
```python
# Factor Library 產生的欄位名稱
outputs = ['breakout_signal', 'momentum', 'rolling_trailing_stop_signal']
```

**問題**：
- Factor Library 使用描述性名稱（`breakout_signal`, `momentum`）
- 框架驗證層要求標準名稱（`signal`, `position`）
- 沒有命名映射或轉換機制
- 導致 100% 驗證失敗

### 6.2 影響範圍評估

**受影響的組件**：
1. ✅ Factor Graph Only mode：完全失效
2. ✅ Hybrid mode：50% 功能失效（Factor Graph 部分）
3. ❌ LLM Only mode：不受影響

**測試數據**：
- 總 Factor Graph 嘗試：30次（FG Only: 20 + Hybrid: 10）
- 成功次數：0
- 失敗率：100%

---

## 7. 解決方案與建議

### 7.1 修復方案比較

#### 方案 A：修改 Factor Library 輸出命名

**描述**：修改所有因子定義，使用標準欄位名稱

**優點**：
- ✅ 符合框架規範
- ✅ 根本性解決問題
- ✅ 未來維護簡單

**缺點**：
- ❌ 可能破壞現有代碼
- ❌ 需要修改大量因子定義
- ❌ 回歸測試工作量大

**實施複雜度**：高
**風險等級**：中-高

---

#### 方案 B：修改策略驗證邏輯

**描述**：允許自訂欄位名稱，只要有信號輸出即可

**優點**：
- ✅ 向後相容
- ✅ 靈活性高
- ✅ 不破壞現有代碼

**缺點**：
- ❌ 需要修改核心驗證邏輯
- ❌ 可能降低驗證嚴謹性
- ❌ 增加框架複雜度

**實施複雜度**：中
**風險等級**：中

---

#### 方案 C：添加命名轉換層（**推薦** ⭐）

**描述**：在因子輸出和策略驗證之間添加映射層

**實施位置**：`src/factor_graph/strategy.py:validate_data()`

**技術方案**：
```python
# 在 validate_data() 方法中添加映射邏輯
SIGNAL_NAME_MAPPING = {
    'breakout_signal': 'signal',
    'momentum_signal': 'signal',
    'rolling_trailing_stop_signal': 'signal',
    # ... 其他映射
}

# 轉換邏輯
def _map_signal_columns(self, data):
    """Map custom signal names to standard names."""
    for custom_name, standard_name in SIGNAL_NAME_MAPPING.items():
        if custom_name in data.columns and standard_name not in data.columns:
            data[standard_name] = data[custom_name]
    return data
```

**優點**：
- ✅ 最小侵入性
- ✅ 不破壞現有代碼
- ✅ 易於維護和擴展
- ✅ 快速實施（1-2天）
- ✅ 低風險

**缺點**：
- ⚠️ 增加一層抽象
- ⚠️ 需要維護映射表

**實施複雜度**：低
**風險等級**：低
**建議優先級**：**P0（立即執行）**

---

### 7.2 LLM 品質改善建議

#### 問題 1：未建立 report 變數（40% 失敗）

**改善方案**：
1. **強化 Prompt Template**：
   ```python
   # 添加明確的 report 變數要求
   prompt_template = """
   IMPORTANT: Your strategy MUST create a 'report' variable.

   Required structure:
   1. Define your strategy logic
   2. Call sim() to run backtest
   3. Assign result to 'report' variable

   Example:
   report = sim(...)  # REQUIRED!
   """
   ```

2. **預執行語法檢查**：
   - 在執行前檢查程式碼是否包含 `report =`
   - 提前發現並修正問題

3. **提供程式碼範本**：
   - 給 LLM 完整的可運行範例
   - 確保基本結構正確

**預期改善**：失敗率從 40% 降至 10%

---

#### 問題 2：資料訪問錯誤（53% 失敗）

**改善方案**：
1. **提供可用因子清單**：
   ```python
   available_factors = """
   Available fundamental factors:
   - fundamental_features:ROA稅後息前
   - fundamental_features:營業毛利率
   - fundamental_features:每股盈餘
   ... (完整清單)

   DO NOT use factors not in this list!
   """
   ```

2. **因子驗證層**：
   - 在生成後驗證所有使用的因子是否存在
   - 提供替代建議

3. **動態因子發現**：
   - 在 prompt 中包含當前可用的因子
   - 確保 LLM 使用有效的資料源

**預期改善**：失敗率從 53% 降至 20%

---

### 7.3 Hybrid Mode 優化建議

#### 改善 1：動態 innovation_rate 調整

**目標**：根據成功率動態調整 LLM/Factor Graph 比例

**實施邏輯**：
```python
def adjust_innovation_rate(recent_success_rate: dict) -> float:
    """
    根據最近的成功率動態調整 innovation_rate

    Args:
        recent_success_rate: {'llm': 0.25, 'factor_graph': 0.0}

    Returns:
        調整後的 innovation_rate (0.0 - 1.0)
    """
    llm_rate = recent_success_rate['llm']
    fg_rate = recent_success_rate['factor_graph']

    if fg_rate == 0 and llm_rate > 0:
        # Factor Graph 完全失效，提高 LLM 比例
        return min(0.8, current_rate + 0.1)
    elif llm_rate > fg_rate * 2:
        # LLM 明顯優於 Factor Graph
        return min(0.7, current_rate + 0.05)
    else:
        # 保持平衡
        return 0.5
```

**預期效果**：Hybrid 成功率從 5% 提升至 15%+

---

#### 改善 2：智能回退機制

**目標**：Factor Graph 失敗時自動切換到 LLM

**實施邏輯**：
```python
class SmartFallbackStrategy:
    def generate_strategy(self, iteration: int):
        # 依照 innovation_rate 選擇生成方法
        use_llm = random.random() < self.innovation_rate

        if use_llm:
            return self.llm_generator.generate()
        else:
            # 嘗試 Factor Graph
            try:
                strategy = self.factor_graph_generator.generate()
                # 驗證策略
                if self._validate_strategy(strategy):
                    return strategy
                else:
                    # 驗證失敗，回退到 LLM
                    logger.warning("Factor Graph validation failed, falling back to LLM")
                    return self.llm_generator.generate()
            except Exception as e:
                # 生成失敗，回退到 LLM
                logger.error(f"Factor Graph generation failed: {e}, falling back to LLM")
                return self.llm_generator.generate()
```

**預期效果**：消除 Factor Graph 的 0% 成功率拖累

---

### 7.4 實施路線圖

#### Phase 1: 緊急修復（1-2 天）

**優先級**：P0 (Critical)
**目標**：修復 Factor Graph 命名問題

**行動項目**：
1. ✅ 實施方案 C：添加命名轉換層
2. ✅ 修改 `src/factor_graph/strategy.py:validate_data()`
3. ✅ 添加單元測試驗證修復
4. ✅ 重新執行 20 次 Factor Graph Only 測試

**成功標準**：
- Factor Graph 成功率 > 0%
- 至少 1 個策略能通過驗證

**責任人**：開發團隊
**預計完成**：2天內

---

#### Phase 2: 改善 LLM 品質（3-5 天）

**優先級**：P1 (High)
**目標**：提升 LLM 成功率從 25% 到 40%+

**行動項目**：
1. ✅ 分析 15 個 LLM 失敗案例的詳細原因
2. ✅ 改善 prompt template（report 變數、因子清單）
3. ✅ 實施預執行驗證層
4. ✅ A/B 測試新舊 prompt
5. ✅ 執行 50 次迭代驗證改善效果

**成功標準**：
- LLM 成功率 > 40%
- ValueError 錯誤減少 50%+
- Exception 錯誤減少 30%+

**責任人**：AI/ML 團隊
**預計完成**：5天內

---

#### Phase 3: 優化 Hybrid 策略（1 週）

**優先級**：P2 (Medium)
**目標**：智能化 Hybrid mode

**行動項目**：
1. ✅ 實施動態 innovation_rate 調整邏輯
2. ✅ 添加智能回退機制
3. ✅ 建立性能監控儀表板
4. ✅ 執行 100 次迭代驗證改善效果

**成功標準**：
- Hybrid 成功率 > 15%
- 系統能自動適應模式表現
- 減少無效的 Factor Graph 嘗試

**責任人**：系統架構團隊
**預計完成**：1週內

---

## 8. 風險評估與限制

### 8.1 已知限制

1. **樣本數限制**：
   - 各模式僅 20 次迭代
   - 可能存在統計誤差
   - 建議：執行更大規模測試（50-100 次/模式）

2. **測試環境限制**：
   - 單一時間段的市場資料
   - 可能不代表所有市場情況
   - 建議：多時間段回測驗證

3. **LLM 可變性**：
   - 成功率受 prompt 品質影響
   - LLM API 可能有變化
   - 建議：監控 LLM 穩定性

### 8.2 風險管理建議

1. **短期風險緩解**：
   - 暫時使用 LLM Only mode
   - 等待 Factor Graph 修復完成
   - 監控 LLM 成本和穩定性

2. **中期風險管理**：
   - 建立多時間段驗證機制
   - 增加測試覆蓋率
   - 實施自動化監控

3. **長期架構改善**：
   - 標準化命名規範
   - 建立更嚴格的驗證層
   - 改善錯誤處理和回復機制

---

## 9. 總結與建議

### 9.1 核心結論

**✅ 驗證成功**：
- SuccessClassifier 修復完全成功
- 分類邏輯 100% 準確
- 系統能正確識別策略品質

**🚨 緊急問題**：
- Factor Graph 完全失效（100% 失敗率）
- 需要立即修復命名不相容問題
- 影響範圍：Factor Graph Only 和 Hybrid mode

**📈 系統潛力**：
- LLM 模式展現良好效能（25% 成功率，平均 Sharpe 0.376）
- 有明確的改進路徑和方向
- Factor Graph 修復後預期整體效能大幅提升

### 9.2 立即行動建議

**本週內（P0）**：
1. ✅ 實施方案 C：添加命名轉換層
2. ✅ 修復 Factor Graph 命名問題
3. ✅ 驗證修復效果

**下週（P1）**：
1. ✅ 改善 LLM prompt template
2. ✅ 添加預執行驗證
3. ✅ 重新測試 LLM 效能

**本月內（P2）**：
1. ✅ 實施 Hybrid mode 智能化
2. ✅ 建立監控系統
3. ✅ 執行大規模驗證測試

### 9.3 預期成果

**短期**（1-2週）：
- Factor Graph 恢復運作
- LLM 成功率提升至 40%
- Hybrid mode 成功率提升至 15%

**中期**（1-2個月）：
- 系統穩定運行
- 三種模式都有良好表現
- 建立完整的監控和驗證機制

**長期**（3-6個月）：
- 架構優化完成
- 成功率持續提升
- 策略品質穩定改善

---

## 附錄

### A. 測試數據詳情

**測試環境**：
- Python 版本：3.11
- FinLab 框架版本：latest
- 測試日期：2025-11-15
- 總執行時間：440 秒（7.3 分鐘）

**配置檔案**：
- Factor Graph Only: `config_fg_only_20.yaml`
- LLM Only: `config_llm_only_20.yaml`
- Hybrid: `config_hybrid_20.yaml`

**結果檔案**：
- 總結：`results_20251115_224320.json`
- FG Only：`fg_only_20/innovations.jsonl`
- LLM Only：`llm_only_20/innovations.jsonl`
- Hybrid：`hybrid_20/innovations.jsonl`

### B. 相關程式碼位置

- SuccessClassifier：`src/backtest/classifier.py`
- 策略驗證：`src/factor_graph/strategy.py:validate_data()`
- 回測執行器：`src/backtest/executor.py`
- Factor Library：`src/factor_library/registry.py`
- 迭代執行器：`src/learning/iteration_executor.py`

### C. 參考文獻

1. SuccessClassifier 修復記錄：commit 6f15251
2. 測試腳本：`run_20iteration_three_mode_test.py`
3. 分類系統文檔：`docs/CLASSIFICATION_SYSTEM.md`

---

**報告完成日期**：2025-11-15
**分析工具**：Claude Code + Zen MCP Thinkdeep
**下次更新**：Phase 1 修復完成後
