# Hybrid Architecture Review Summary

**Date**: 2025-11-08
**Status**: ✅ **APPROVED with Revisions**
**Reviewers**: zen thinkdeep + zen chat (Gemini 2.5 Pro)

---

## Executive Summary

完成了對 Factor Graph + LLM 混合架構的系統性審查，包括：
1. ✅ zen thinkdeep 深度分析（發現 5 個關鍵架構缺陷）
2. ✅ zen chat 專家審批（Gemini 2.5 Pro 確認分析準確性）
3. ✅ 補充考量（回饋循環設計）

**核心結論**：混合架構方向正確，但實作複雜度被嚴重低估。

**時程修正**：
- 原始估計：1 天（4-6 小時）
- 修正估計：2-3 天（17-25 小時）
- 變化幅度：+200% 到 +300%

---

## 關鍵發現彙總

### P0 級阻礙（必須在實作前解決）

#### 1. Metrics 提取路徑未定義
**問題**：`strategy.to_pipeline()` 返回 signals DataFrame，不是回測指標

**證據**（src/factor_graph/strategy.py:384-433）：
```python
def to_pipeline(self, data: pd.DataFrame) -> pd.DataFrame:
    """Returns DataFrame with all factor outputs computed in dependency order.
    Original data columns are preserved, factor outputs are added."""
```

**影響**：
- LLM 路徑：`exec(code)` → finlab.backtest.sim() → report → extract metrics ✅
- Factor Graph 路徑：`strategy.to_pipeline(data)` → signals DataFrame → **❌ 未定義** → metrics

**關鍵問題**：
1. finlab.backtest.sim() 是否接受 signal DataFrame？
2. 如何識別最終的 "positions" 信號？
3. to_pipeline() 使用什麼欄位命名慣例？

**必要行動**：調查 finlab backtest API

#### 2. Parameter 提取不相容
**問題**：`extract_strategy_params(code)` 解析 Python 程式碼字串，無法處理 Strategy DAG 物件

**證據**（artifacts/working/modules/performance_attributor.py:14-100）：
```python
def extract_strategy_params(code: str) -> Dict[str, Any]:
    """使用 regex 模式提取策略參數"""
    datasets = re.findall(r"data\.get\(['\"]([^'\"]+)['\"]\)", code)
    liquidity_threshold = re.search(r'(?:trading_value|liquidity).*?>\s*([\d_e\.]+)', code)
    # ... 只能處理程式碼字串
```

**必要改變**：
- ChampionTracker 需要**雙重提取路徑**
- 為 Strategy DAG 定義"parameters"概念
- 為 Strategy DAG 定義"success_patterns"概念

#### 3. ChampionStrategy 欄位缺失
**問題**：提案的 dataclass 過於簡化

**需要的完整結構**：
```python
@dataclass
class ChampionStrategy:
    # 混合欄位
    code: Optional[str] = None
    strategy: Optional[Strategy] = None
    generation_method: str  # "llm" or "factor_graph"

    # 共用欄位
    metrics: Dict[str, float] = field(default_factory=dict)
    iteration_num: int
    timestamp: str

    # LLM 特定欄位（factor_graph 時為 Optional）
    parameters: Optional[Dict[str, Any]] = None
    success_patterns: Optional[List[str]] = None
```

### P1 級關鍵問題

#### 4. Strategy 序列化方案不足
**推薦方案**：Option 3 (Custom JSON serialization)

```python
{
    "iteration_num": 5,
    "generation_method": "factor_graph",
    "strategy_metadata": {
        "strategy_id": "momentum_v5",
        "generation": 1,
        "parent_ids": ["momentum_v4"],
        "factors": [
            {"id": "rsi_14", "type": "RSI", "params": {"period": 14}},
            {"id": "entry", "type": "Signal", "params": {...}, "depends_on": ["rsi_14"]}
        ],
        "dag_edges": [["rsi_14", "entry"]]
    },
    "metrics": {"sharpe_ratio": 0.85}
}
```

**優點**：可讀、可版本控制、可除錯、跨平台
**工作量**：+4-6 小時

#### 5. ChampionTracker 重構範圍
不是"最小改動"，而是實質重構：
- _create_champion() 需要雙路徑邏輯
- 新增 extract_strategy_dag_metadata() 函數
- 新增 extract_dag_patterns() 函數
- 更新 promote_to_champion()
- 實作 Strategy 序列化

---

## 專家審批結果（Gemini 2.5 Pro）

### 分析完整性：✅ 極佳，但有一個補充考量

**補充考量：回饋循環（Feedback Loop）**

報告詳細說明了如何**儲存** Strategy 物件為 Champion，但沒有明確指出 FactorGraphGenerator 如何**獲取** Strategy 物件作為變異基礎。

**解決方案**：
```python
# IterationExecutor 根據 generation_method 選擇路徑
if champion.generation_method == "llm":
    base_code = champion.code
    new_code = llm_client.generate(base_code)
elif champion.generation_method == "factor_graph":
    base_strategy = champion.strategy  # ✅ 直接從 champion 獲取
    new_strategy = factor_graph_generator.generate_mutation(base_strategy)
```

**過渡情境處理**（LLM champion → Factor Graph 變異）：
```python
if innovation_mode == "factor_graph" and champion.strategy is None:
    # 從模板庫選擇初始 Strategy，不變異 champion
    base_strategy = factor_graph_template_library.get_random_template()
else:
    base_strategy = champion.strategy
```

### 風險評估：✅ 準確且合理

- **P0 分級正確**：finlab API 相容性是最高優先級未知風險
- **P1 分級正確**：指標一致性和測試覆蓋率對品質關鍵但不會立即阻塞
- **P2 分級合適**：時程超支和技術債是標準專案風險

### 實作計劃：✅ 合理且務實

2-3 天估計基於當前已知資訊是良好的估算。考慮到潛在的討論和意外問題，**2.5 到 3.5 天是更安全的預期**。

### 技術方案選擇：✅ Option 3 是明確最佳選擇

JSON 序列化的前期投資將在專案整個生命週期中獲得回報（可讀性、可版本控制、可除錯性）。

### 關鍵決策點：✅ 必須先調查 finlab API

在 Phase 1 調查完成前，任何 BacktestExecutor 的程式碼實作都是有風險的。

**最壞情況**：需要自己計算 Sharpe ratio 等指標，可能額外增加 1-2 天
**最佳情況**：有直接 API 接受 DataFrame，實作將很簡單

---

## 修訂後的實作計劃

### Phase 1: 調查與準備（2-3 小時）❗ 最高優先級
**任務**：
1. 調查 finlab.backtest.sim() API
   - 是否接受 signal DataFrame？
   - 如何從 to_pipeline() 輸出轉換為回測指標？
   - 需要什麼格式和欄位名稱？

2. 研究 NetworkX graph 序列化
   - 驗證 JSON-like 方法的可行性

3. 定義 Strategy DAG metadata schema
   - DAG 的有意義"parameters"是什麼？
   - 可以從 DAG 結構提取什麼"success_patterns"？

**可交付成果**：API 相容性文件、序列化 schema

### Phase 2: 核心混合 Dataclass（2-3 小時）
**任務**：
1. 實作 ChampionStrategy 混合 dataclass
   - 添加所有必要欄位
   - 實作 __post_init__ 驗證
   - 編寫 10 個單元測試

2. 實作 Strategy DAG metadata 提取
   - extract_strategy_dag_metadata(strategy) 函數
   - extract_dag_patterns(strategy) 函數
   - 編寫 5 個單元測試

**可交付成果**：champion_strategy.py、test_champion_strategy.py

### Phase 3: ChampionTracker 重構（3-4 小時）
**任務**：
1. 重構 _create_champion() 為雙路徑
2. 更新 promote_to_champion() 處理 Strategy 物件
3. 實作條件式 parameter/pattern 提取
4. 處理過渡情境（LLM → Factor Graph）
5. 編寫 10 個單元測試

**可交付成果**：更新的 champion_tracker.py、test_champion_tracker.py

### Phase 4: BacktestExecutor Strategy 支援（4-6 小時）
**依賴**：Phase 1 必須完成

**任務**：
1. 實作 execute_strategy_dag() 方法
2. 實作 _extract_metrics_from_signals() helper
3. 更新 execute() 方法根據輸入類型路由
4. 編寫 10 個單元測試

**可交付成果**：更新的 executor.py、test_executor.py

### Phase 5: Strategy 序列化（4-6 小時）
**任務**：
1. 實作 JSON-like Strategy encoder
2. 實作 Strategy decoder
3. 更新 IterationHistory 處理 Strategy 物件
4. 編寫 10 個序列化往返測試

**可交付成果**：strategy_serialization.py、更新的 iteration_history.py

### Phase 6: 整合與測試（2-3 小時）
**任務**：
1. 編寫 15 個整合測試：
   - LLM → Factor Graph champion 過渡
   - Factor Graph → LLM champion 過渡
   - 混合執行路徑端到端
   - 序列化/反序列化往返
   - 指標提取一致性驗證

2. 手動測試與驗證

**可交付成果**：test_hybrid_integration.py、驗證報告

---

## 時程彙總

| Phase | 任務 | 小時 | 依賴 |
|-------|------|------|------|
| 1. 調查 | finlab API、序列化研究 | 2-3h | 無 |
| 2. Hybrid Dataclass | ChampionStrategy、metadata 提取 | 2-3h | Phase 1 |
| 3. ChampionTracker | 雙重提取路徑、過渡邏輯 | 3-4h | Phase 2 |
| 4. BacktestExecutor | Strategy 執行、metrics | 4-6h | Phase 1 |
| 5. Serialization | JSON encoder/decoder | 4-6h | Phase 2 |
| 6. Integration | 端到端測試 | 2-3h | Phase 2-5 |
| **總計** | | **17-25h** | **2-3 天** |

---

## 風險評估

### 高風險（P0）
1. **finlab API 相容性**：如果不能接受 signal DataFrame，需要替代方案
2. **Factor 序列化**：如果 Factor 物件無法序列化為 JSON，可能需要退回 Pickle

### 中風險（P1）
1. **指標提取一致性**：確保 Strategy DAG 執行產生與程式碼執行相同的指標
2. **測試覆蓋率**：需要 40+ 新測試，實作期間可能發現邊界情況

### 低風險（P2）
1. **時程超支**：複雜重構可能超過 3 天
2. **技術債**：序列化複雜性可能帶來維護負擔

---

## 立即行動項目

### 🔴 關鍵優先級（必須立即執行）
1. **Phase 1: finlab API 調查**
   - 這是解鎖所有後續工作的關鍵
   - 在投入編碼前必須完成
   - 預估：2-3 小時

### 🟡 次要優先級（Phase 1 完成後）
2. **定義 DAG metadata schema**
   - 確立 Strategy DAG 的"parameters"和"success_patterns"定義
   - 預估：30 分鐘

3. **原型序列化方法**
   - 驗證 JSON-like 方法對 Strategy + Factor 物件可行
   - 預估：1 小時

### 🟢 實作階段（調查完成後）
4. **Phase 2-6 按順序執行**
   - 遵循修訂後的實作計劃
   - 每個 Phase 完成後進行檢查點審查

---

## 架構決策記錄

### 決策 1：採用 Option 3 (JSON 序列化)
**理由**：長期可維護性優於短期開發速度
**權衡**：+4-6 小時前期投資，但避免技術債

### 決策 2：parameters/success_patterns 設為 Optional
**理由**：factor_graph generation_method 可能不適用這些概念
**實作**：在提取時根據 generation_method 條件處理

### 決策 3：過渡情境使用模板庫
**理由**：LLM code → Factor Graph Strategy 轉換過於複雜
**實作**：當 champion.strategy 為 None 時，從模板庫選擇起點

---

## 對比原始提案

| 面向 | 原始提案 | 精煉分析 | 變化 |
|------|----------|----------|------|
| 時程 | 1 天（4-6h） | 2-3 天（17-25h） | +200-300% |
| ChampionStrategy 欄位 | 4 個欄位 | 8 個欄位 | +100% |
| ChampionTracker 改動 | "約 20 行" | 實質重構 | N/A |
| 新增函數 | 1 個 | 6+ 個函數 | +500% |
| 測試數量 | "約 40 個" | 60+ 個測試 | +50% |
| 序列化方案 | "選項 1 或 2" | 選項 3（自訂 JSON） | 更高複雜度 |
| Metrics 提取 | "相同邏輯" | 完全不同路徑 | N/A |

---

## 最終結論與建議

### 核心結論
混合架構提案在**方向上完全正確且必要**，但顯著**低估了實作複雜度**。

提案假設兩條路徑可以共享實作（"相同邏輯"），但證據顯示它們需要**平行實作**：
1. Parameter/pattern 提取
2. 執行結果的 metrics 提取
3. 序列化/反序列化
4. Champion 升級邏輯

### 最終建議
✅ **繼續採用混合架構**，但分配 **2-3 天**而非 1 天，並在承諾實作方法前完成 Phase 1 調查。

### 下一步行動
1. 🔴 **立即開始 Phase 1 finlab API 調查**（2-3 小時）
2. 🟡 基於調查結果更新 Phase 4 實作計劃
3. 🟢 獲得批准後開始 Phase 2-6 實作

---

## 附件文件

1. **HYBRID_ARCHITECTURE_REFINED_ANALYSIS.md**
   - 完整的 thinkdeep 分析報告
   - 所有 P0/P1/P2 問題的詳細說明
   - 證據來源和程式碼引用

2. **CRITICAL_FINDING_FACTOR_GRAPH_ARCHITECTURE.md**
   - 原始架構不相容發現
   - to_python_code() 不存在的驗證
   - 初始混合架構提案

---

**分析完成**：2025-11-08
**審查者**：zen thinkdeep + zen chat (Gemini 2.5 Pro)
**信心程度**：HIGH（所有阻礙都已識別並附證據）
**狀態**：✅ 批准修訂後的實作計劃，等待 Phase 1 調查結果
