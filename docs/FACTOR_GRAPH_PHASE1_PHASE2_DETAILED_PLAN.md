# Factor Graph Timeout 診斷與修復詳細計畫

> **文檔版本**: v1.0
> **創建日期**: 2025-11-16
> **規劃工具**: zen planner
> **預計執行時間**: 6-10 天

---

## 目錄

1. [規劃總結](#規劃總結)
2. [階段 1：緊急診斷](#階段-1緊急診斷)
3. [階段 2：快速修復](#階段-2快速修復)
4. [測試驗證策略](#測試驗證策略)
5. [實施流程圖](#實施流程圖)
6. [立即行動指南](#立即行動指南)
7. [交付物清單](#交付物清單)
8. [風險管理](#風險管理)

---

## 規劃總結

### 問題本質

Factor Graph 作為系統 80% 穩定 fallback 完全失效（100% timeout），必須緊急修復以恢復架構完整性。

**核心數據**：
- Factor Graph 成功率：0/20 (0%)
- LLM Only 成功率：5/20 (25%)
- Hybrid 成功率：3/20 (15%)
- 根本原因：計算階段懸掛（資料載入正常 <1s）

**架構理解**（關鍵修正）：
- LLM (20%)：創新引擎，引入新 factors 突破限制
- Factor Graph (80%)：穩定基線，優化已知 factors
- 目標：恢復 Factor Graph 作為可靠 fallback

### 解決策略

**兩階段漸進式修復**：

```
階段 1: 緊急診斷 (2-3天)
    ↓
關鍵決策點 (Task 1.3)
    ↓
階段 2: 快速修復 (3-5天)
    ↓
驗證達標 (≥70% 成功率)
```

**關鍵決策樹**：

```
Task 1.3 最小化測試
    ├─ 成功 (<30s) ──→ 路徑 A：複雜度問題 (80%機率)
    │                   └─ 簡化模板 + 診斷增強
    │
    ├─ 失敗 (>420s) ──→ 路徑 B：Factor 實作問題 (15%機率)
    │                   └─ 修復 Factor + 防禦層
    │
    └─ 錯誤 (<30s) ──→ 修復錯誤 + 重新評估
```

### 時間與成功率估算

**時間估算**：
- **樂觀情況**：6 天（診斷 2天 + 修復 3天 + 驗證 1天）
- **標準情況**：7-8 天（診斷 3天 + 修復 4天 + 驗證 1天）
- **悲觀情況**：10 天（診斷 3天 + 修復 5天 + 重試 2天）

**成功機率**：
- 達到基本可用（≥25%）：95% 信心
- 達到目標（≥70%）：75% 信心
- 超越目標（≥80%）：40% 信心

---

## 階段 1：緊急診斷

**目標**：精確定位瓶頸的具體位置和原因

**策略**：並行起點 + 順序決策

```
Day 1 並行任務
├─ 1.1 時序儀表 (2-3h)
└─ 1.2 模板檢查 (1-2h)
    ↓
Day 2 關鍵決策
└─ 1.3 最小化測試 (2-3h + 執行)
    ↓
Day 3 條件任務（視 1.3 結果）
├─ 1.4 Per-Factor 時序（如 1.3 失敗）
└─ 1.5 檢查實作（如 1.4 找到慢 factor）
```

### Task 1.1：實作時序儀表

**優先級**：P1 - 立即執行
**工作量**：2-3 小時
**檔案**：`src/factor_graph/strategy.py`

**目的**：識別 strategy.execute() 中哪個階段導致懸掛

**實作步驟**：

```python
# src/factor_graph/strategy.py - execute() 方法修改

def execute(self, sim):
    """Execute strategy with detailed timing instrumentation."""
    import time
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)

    # === PHASE 1: Data Loading ===
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 1 START: Data loading at {datetime.now()}")

    try:
        self._load_data()  # 或現有的資料載入方法
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 1 COMPLETE: Data loaded in {phase_time:.2f}s")
        logger.info(f"[TIMING] Loaded {len(self.data_frames)} data fields")

    except Exception as e:
        logger.error(f"[TIMING] Phase 1 FAILED: {e}")
        raise

    # === PHASE 2: Graph Execution (SUSPECT) ===
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 2 START: Graph execution at {datetime.now()}")
    logger.info(f"[TIMING] Factor count: {len(self.factor_graph.factors)}")

    try:
        result = self.factor_graph.execute(self.data_frames)
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 2 COMPLETE: Graph executed in {phase_time:.2f}s")

    except Exception as e:
        logger.error(f"[TIMING] Phase 2 FAILED: {e}")
        raise

    # === PHASE 3: Validation ===
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 3 START: Validation at {datetime.now()}")

    try:
        self._validate_result(result)
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 3 COMPLETE: Validated in {phase_time:.2f}s")

    except Exception as e:
        logger.error(f"[TIMING] Phase 3 FAILED: {e}")
        raise

    # === PHASE 4: Backtest ===
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 4 START: Backtest at {datetime.now()}")

    try:
        backtest_result = self._run_backtest(result, sim)
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 4 COMPLETE: Backtest in {phase_time:.2f}s")

        return backtest_result

    except Exception as e:
        logger.error(f"[TIMING] Phase 4 FAILED: {e}")
        raise
```

**預期輸出**：

```
[TIMING] Phase 1 START: Data loading at 2025-11-16 10:00:00
[TIMING] Phase 1 COMPLETE: Data loaded in 0.98s
[TIMING] Loaded 3 data fields
[TIMING] Phase 2 START: Graph execution at 2025-11-16 10:00:01
[TIMING] Factor count: 11
[系統在這裡懸掛 - 將揭示問題在 Phase 2]
```

**成功標準**：能夠確認瓶頸在 Phase 2 (graph execution)

---

### Task 1.2：檢查模板策略組成

**優先級**：P1 - 立即執行
**工作量**：1-2 小時

**目的**：了解 template_0, template_1, template_2 使用了多少 factors

**執行腳本**：

```bash
# 搜尋模板定義
find . -name "*.py" -o -name "*.json" -o -name "*.yaml" | xargs grep -l "template_0\|template_1\|template_2"

# 檢查 FactorGraph 初始化邏輯
grep -A 50 "class.*FactorGraph" src/factor_graph/*.py

# 搜尋 factor registry 使用
grep -rn -B 5 -A 10 "add_factor\|register_factor" src/factor_graph/
```

**需要回答的問題**：

1. 模板策略包含多少個 factors？
2. 是否使用了所有 13 個可用 factors？
3. Factor 之間的依賴關係深度如何？

**假設驗證**：

- **如果 template 使用 10+ factors** → 證實複雜度假設（80% 機率）
- **如果 template 使用 3-5 factors** → 問題在 factor 計算本身（需進入 1.3）

**輸出格式**：

```markdown
## 模板策略組成分析

### Template 0
- Factor 數量：[X]
- Factors 列表：[factor1, factor2, ...]
- 依賴深度：[X] 層

### Template 1
- Factor 數量：[X]
- Factors 列表：[...]
- 依賴深度：[X] 層

### Template 2
- Factor 數量：[X]
- Factors 列表：[...]
- 依賴深度：[X] 層

### 結論
- 平均 factor 數量：[X]
- 是否超過 5 個：[是/否]
- 複雜度評估：[低/中/高]
```

---

### Task 1.3：建立最小化測試策略

**優先級**：P1 - 關鍵診斷
**工作量**：2-3 小時（實作 + 執行）
**檔案**：`experiments/diagnostic_minimal_test.py`

**目的**：隔離問題 - 驗證簡單策略是否能成功執行

**實作代碼**：

```python
# experiments/diagnostic_minimal_test.py

"""
Minimal Factor Graph Test - 僅使用 1-2 個最簡單的 factors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop
from src.factor_graph.factor_graph import FactorGraph
from src.factor_library.registry import FactorRegistry
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_minimal_strategy():
    """建立僅包含 1 個 momentum factor 的最簡單策略"""

    registry = FactorRegistry()
    fg = FactorGraph()

    # 僅新增一個最簡單的 factor
    momentum = registry.get_factor("momentum_factor")
    fg.add_factor("momentum", momentum, params={"period": 20})

    logger.info(f"Created minimal strategy with {len(fg.factors)} factor(s)")
    return fg

def run_minimal_test():
    """執行最小化測試"""

    logger.info("=" * 80)
    logger.info("MINIMAL FACTOR GRAPH DIAGNOSTIC TEST")
    logger.info("=" * 80)
    logger.info("Testing with ONLY 1 momentum factor")
    logger.info("")

    # 建立最簡單的策略
    strategy = create_minimal_strategy()

    # 使用現有的 backtest executor 進行測試
    from src.backtest.executor import BacktestExecutor
    from src.data.finlab_adapter import FinlabDataAdapter

    executor = BacktestExecutor(timeout=420)
    data_adapter = FinlabDataAdapter()

    # 執行策略
    logger.info("Executing minimal strategy...")
    import time
    start = time.time()

    try:
        result = executor.execute_strategy(strategy, data_adapter.get_sim())
        elapsed = time.time() - start

        logger.info(f"✅ SUCCESS: Minimal strategy executed in {elapsed:.2f}s")
        logger.info(f"Sharpe Ratio: {result.get('sharpe_ratio', 'N/A')}")
        return True

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"❌ FAILED: Minimal strategy failed after {elapsed:.2f}s")
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = run_minimal_test()
    sys.exit(0 if success else 1)
```

**執行測試**：

```bash
python3 experiments/diagnostic_minimal_test.py
```

**決策邏輯**：

| 結果 | 執行時間 | 結論 | 下一步 |
|------|----------|------|--------|
| ✅ 成功 | <30s | 問題在於策略複雜度 | 進入階段 2.1 (簡化模板) |
| ❌ 失敗 | >420s timeout | 問題在單一 factor 計算 | 進入 1.4 (檢查 factor 實作) |
| ❌ 失敗 | <30s error | 發現新的錯誤類型 | 修復新錯誤 |

---

### Task 1.4：新增 Per-Factor 執行時序

**觸發條件**：Task 1.3 失敗 (timeout)
**優先級**：P1
**工作量**：3-4 小時
**檔案**：`src/factor_graph/factor_graph.py`

**目的**：如果連最簡單策略都失敗，需要追蹤每個 factor 的執行時間

**實作代碼**：

```python
# src/factor_graph/factor_graph.py - execute() 方法修改

def execute(self, data_frames):
    """Execute factor graph with per-factor timing."""
    import time
    from datetime import datetime
    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"[GRAPH] Starting DAG execution with {len(self.factors)} factors")

    # 拓撲排序
    execution_order = list(nx.topological_sort(self.graph))
    logger.info(f"[GRAPH] Execution order: {execution_order}")

    results = {}

    for i, factor_name in enumerate(execution_order, 1):
        factor_start = time.time()
        logger.info(f"[GRAPH] Factor {i}/{len(execution_order)}: {factor_name} START at {datetime.now()}")

        try:
            factor = self.factors[factor_name]
            params = self.graph.nodes[factor_name].get('params', {})

            # 執行 factor
            result = factor.calculate(data_frames, **params)

            factor_time = time.time() - factor_start
            logger.info(f"[GRAPH] Factor {factor_name} COMPLETE in {factor_time:.2f}s")

            # 檢查是否超過合理時間
            if factor_time > 60:
                logger.warning(f"[GRAPH] ⚠️  Factor {factor_name} took {factor_time:.2f}s (>60s threshold)")

            results[factor_name] = result

        except Exception as e:
            factor_time = time.time() - factor_start
            logger.error(f"[GRAPH] Factor {factor_name} FAILED after {factor_time:.2f}s: {e}")
            raise

    logger.info(f"[GRAPH] All {len(execution_order)} factors completed successfully")
    return self._combine_results(results)
```

**預期輸出**：

```
[GRAPH] Starting DAG execution with 11 factors
[GRAPH] Execution order: ['momentum', 'ma_filter', 'atr', ...]
[GRAPH] Factor 1/11: momentum START at 2025-11-16 10:00:01
[GRAPH] Factor momentum COMPLETE in 0.45s
[GRAPH] Factor 2/11: ma_filter START at 2025-11-16 10:00:02
[系統在這裡懸掛 - 將揭示是哪個 factor 導致問題]
```

---

### Task 1.5：檢查 Factor 實作

**觸發條件**：Task 1.4 找到特定慢 factor
**優先級**：P2
**工作量**：2-4 小時

**目的**：檢查導致懸掛的 factor 是否有無窮迴圈或 O(n²) 操作

**檢查腳本**：

```bash
# 檢查所有 factor 的實作
find src/factor_library -name "*.py" -exec echo "=== {} ===" \; -exec cat {} \;

# 特別注意：
# 1. 迴圈結構 (for, while)
# 2. 嵌套迴圈 (nested loops)
# 3. 大型滾動視窗 (rolling windows > 252)
# 4. Pandas apply() 呼叫
```

**尋找的問題模式**：

```python
# ❌ 危險：O(n²) 操作
for stock in stocks:
    for date in dates:
        calculate_something()  # 可能非常慢

# ❌ 危險：無限迴圈風險
while condition:
    # 沒有明確的退出條件

# ❌ 危險：過大的滾動視窗
df.rolling(window=1000).mean()  # 1000 天滾動平均可能太大

# ✅ 安全：向量化操作
result = df['close'].pct_change(periods=20)  # Pandas 內建向量化
```

---

### 階段 1 成功標準

完成診斷階段後，你將知道：

- [x] 瓶頸的精確位置（Phase 1/2/3/4 中的哪一個）
- [x] 模板策略的複雜度（使用了多少 factors）
- [x] 簡單策略是否能執行成功
- [x] 如果單一 factor 有問題，是哪一個 factor
- [x] 該 factor 的具體問題（無窮迴圈、O(n²)、記憶體等）

**輸出交付物**：

- `docs/FACTOR_GRAPH_DIAGNOSTIC_REPORT.md` - 診斷報告
- `docs/template_analysis.txt` - 模板組成分析
- `experiments/minimal_test_output.log` - 1.3 測試結果

**預計時間**：2-3 天（包含測試執行）

---

## 階段 2：快速修復

**目標**：基於診斷結果實施快速修復，使 Factor Graph 模式達到 ≥70% 成功率

**策略**：條件式修復路徑（根據階段 1 診斷結果選擇）

```
診斷結果
    ├─ 複雜度問題 (80%) ──→ 路徑 A
    ├─ Factor 問題 (15%) ──→ 路徑 B
    └─ 資料問題 (5%) ──→ 路徑 C
```

---

### 路徑 A：複雜度問題（最可能，80%機率）

**觸發條件**：1.3 最小化測試成功 + 1.2 顯示模板使用 >5 factors

#### Task 2.1A：簡化模板策略

**優先級**：P1 - 主要修復
**工作量**：6-8 小時（Day 4-5）
**檔案**：創建 `src/factor_graph/templates.py`

**實作策略**：

```python
# src/factor_graph/templates.py (新建檔案)

"""
Simplified Factor Graph Templates
簡化的 Factor Graph 模板 - 限制為 3-5 個高品質 factors
"""

from src.factor_library.registry import FactorRegistry
from src.factor_graph.factor_graph import FactorGraph

class TemplateStrategy:
    """Base class for template strategies."""

    MAX_FACTORS = 5  # 強制限制

    @staticmethod
    def create_momentum_template():
        """
        Template 0: Simple Momentum Strategy
        僅使用 3 個核心 momentum factors
        """
        registry = FactorRegistry()
        fg = FactorGraph()

        # Factor 1: 基本動量
        fg.add_factor("momentum",
                     registry.get_factor("momentum_factor"),
                     params={"period": 20})

        # Factor 2: 移動平均過濾
        fg.add_factor("ma_filter",
                     registry.get_factor("ma_filter_factor"),
                     params={"short_period": 20, "long_period": 60})

        # Factor 3: 簡單停損
        fg.add_factor("stop_loss",
                     registry.get_factor("trailing_stop_factor"),
                     params={"stop_pct": 0.15})

        return fg

    @staticmethod
    def create_breakout_template():
        """
        Template 1: Turtle Breakout Strategy
        僅使用 4 個 turtle factors
        """
        registry = FactorRegistry()
        fg = FactorGraph()

        # Factor 1: ATR 計算
        fg.add_factor("atr",
                     registry.get_factor("atr_factor"),
                     params={"period": 20})

        # Factor 2: 突破訊號
        fg.add_factor("breakout",
                     registry.get_factor("breakout_factor"),
                     params={"period": 55},
                     dependencies=["atr"])

        # Factor 3: 雙均線過濾
        fg.add_factor("dual_ma",
                     registry.get_factor("dual_ma_filter_factor"),
                     params={"fast": 10, "slow": 30})

        # Factor 4: ATR 停損
        fg.add_factor("atr_stop",
                     registry.get_factor("atr_stop_loss_factor"),
                     params={"multiplier": 2.0},
                     dependencies=["atr"])

        return fg

    @staticmethod
    def create_mean_reversion_template():
        """
        Template 2: Mean Reversion Strategy
        使用 5 個 factors (達到上限)
        """
        registry = FactorRegistry()
        fg = FactorGraph()

        # ... 類似實作，最多 5 個 factors

        return fg

# 使用範例
def get_template(template_id: int) -> FactorGraph:
    """Get simplified template by ID."""
    templates = [
        TemplateStrategy.create_momentum_template,      # template_0
        TemplateStrategy.create_breakout_template,      # template_1
        TemplateStrategy.create_mean_reversion_template # template_2
    ]

    if 0 <= template_id < len(templates):
        return templates[template_id]()
    else:
        raise ValueError(f"Invalid template_id: {template_id}")
```

**整合到 InnovationEngine**：

```python
# src/learning/innovation_engine.py - 修改

def generate_factor_graph_strategy(self):
    """Generate simplified Factor Graph strategy."""
    from src.factor_graph.templates import get_template
    import random

    # 隨機選擇一個簡化模板
    template_id = random.randint(0, 2)
    strategy = get_template(template_id)

    logger.info(f"Generated simplified template_{template_id}")
    logger.info(f"Factor count: {len(strategy.factors)} (max allowed: 5)")

    return {
        "strategy": strategy,
        "template_id": template_id,
        "factor_count": len(strategy.factors)
    }
```

**測試驗證**：

```bash
# 執行 3 次每個模板
for i in 0 1 2; do
    echo "Testing template_$i"
    # 執行測試邏輯
done
```

**預期效果**：

- 減少 50-70% 的計算量
- 執行時間從 >420s 降至 <60s
- 成功率從 0% 提升至 70%+

**回退計畫**：如果 5 factors 仍太多，降至 3 factors

---

#### Task 2.2A：增強診斷能力

**優先級**：P1 - 輔助改善
**工作量**：3-4 小時（Day 5）
**檔案**：`src/backtest/executor.py`

**實作內容**：

```python
# src/backtest/executor.py - 修改

class BacktestExecutor:
    def __init__(self, timeout: int = 900):  # 從 420s 增加到 900s (15分鐘)
        self.timeout = timeout
        logger.info(f"BacktestExecutor initialized with timeout={timeout}s")

    def execute_strategy(self, strategy, sim):
        """Execute with heartbeat logging."""
        import threading

        # 啟動心跳日誌執行緒
        heartbeat_event = threading.Event()

        def heartbeat():
            elapsed = 0
            while not heartbeat_event.is_set():
                time.sleep(30)  # 每 30 秒報告一次
                elapsed += 30
                logger.info(f"[HEARTBEAT] Strategy still executing... {elapsed}s elapsed")

        heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
        heartbeat_thread.start()

        try:
            # 原始執行邏輯
            result = self._execute_with_timeout(strategy, sim)
            return result

        finally:
            heartbeat_event.set()
            heartbeat_thread.join(timeout=1)
```

**預期輸出**：

```
[HEARTBEAT] Strategy still executing... 30s elapsed
[HEARTBEAT] Strategy still executing... 60s elapsed
[HEARTBEAT] Strategy still executing... 90s elapsed
[TIMING] Phase 2 COMPLETE: Graph executed in 85.3s
```

**好處**：即使未完全修復，也能獲得更多診斷資訊

---

### 路徑 B：Factor 實作問題（中等機率，15%）

**觸發條件**：1.3 最小化測試失敗 + 1.4 找到特定慢 factor

#### Task 2.1B：修復或替換問題 Factor

**優先級**：P1
**工作量**：4-8 小時（視問題複雜度）

**診斷輸入**（來自 1.4 + 1.5）：

- 確認是哪個 factor（例如：atr_factor）
- 確認問題類型（O(n²)、無窮迴圈、記憶體）

**修復策略**：

1. **向量化**：將 apply() 改為向量運算

```python
# ❌ 舊方法：逐行計算 (慢)
momentum = close.apply(lambda x: x / x.shift(period) - 1)

# ✅ 新方法：向量化 (快 10-100 倍)
momentum = close.pct_change(periods=period)
```

2. **Numba JIT**：對複雜計算使用 @jit 編譯

```python
from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_atr_numba(high, low, close, period):
    """JIT-compiled ATR calculation for 10-50x speedup."""
    # ... 實作
```

3. **算法優化**：減少迴圈、使用更高效算法

4. **暫時禁用**：如果無法快速修復，從模板中移除

**測試驗證**：

- 單元測試該 factor（<5s）
- 整合測試完整策略（<60s）

---

### 路徑 C：資料載入問題（低機率，5%）

**觸發條件**：1.1 顯示 Phase 1 >10s

#### Task 2.4C：選擇性資料載入

**優先級**：P2
**工作量**：3-4 小時

**實作策略**：

```python
# src/factor_graph/strategy.py - 選擇性載入

def _load_data(self):
    """Load only data required by factors in this strategy."""

    # 分析策略需要哪些資料欄位
    required_fields = self._analyze_required_data_fields()

    logger.info(f"Strategy requires {len(required_fields)} data fields")
    logger.info(f"Required fields: {required_fields}")

    # 僅載入需要的欄位
    for field in required_fields:
        if field not in self.data_frames:
            logger.info(f"Loading data field: {field}")
            self.data_frames[field] = self._load_single_field(field)

    logger.info(f"Data loading complete: {len(self.data_frames)} fields loaded")
```

**預期效果**：

- 從載入 200 個欄位減少到 10-20 個
- 載入時間從 10s 減少到 1-2s
- 記憶體使用減少 80-90%

---

### Task 2.3：Per-Factor 執行時限（防禦層）

**優先級**：P2（路徑 A）/ P1（路徑 B）
**工作量**：2-3 小時（Day 6）
**檔案**：`src/factor_graph/factor_graph.py`

**目的**：防止單一 factor 懸掛整個系統

**實作代碼**：

```python
# src/factor_graph/factor_graph.py - 新增 timeout 機制

import signal
from contextlib import contextmanager

class FactorExecutionTimeout(Exception):
    """Exception raised when factor execution exceeds time limit."""
    pass

@contextmanager
def factor_timeout(seconds: int):
    """Context manager for factor execution timeout."""
    def timeout_handler(signum, frame):
        raise FactorExecutionTimeout(f"Factor execution exceeded {seconds}s limit")

    # 設定 alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def execute(self, data_frames):
    """Execute with per-factor timeouts."""

    FACTOR_TIMEOUT = 120  # 每個 factor 最多 120 秒

    for factor_name in execution_order:
        try:
            with factor_timeout(FACTOR_TIMEOUT):
                result = factor.calculate(data_frames, **params)
                results[factor_name] = result

        except FactorExecutionTimeout as e:
            logger.error(f"Factor {factor_name} exceeded {FACTOR_TIMEOUT}s limit")
            raise

        except Exception as e:
            logger.error(f"Factor {factor_name} failed: {e}")
            raise

    return self._combine_results(results)
```

**保護效果**：

- 單一 factor 最多執行 120 秒
- 總執行時間 = factors 數量 × 120s (最壞情況)
- 5 個 factors = 最多 600s (10分鐘)

---

### 階段 2 整體時程

**樂觀情況（路徑 A）**：3 天

- Day 4-5: 2.1A 簡化模板（8 小時）
- Day 5: 2.2A 診斷增強（3 小時）
- Day 6: 測試驗證（達到 70%）

**標準情況（路徑 A + 防禦）**：4 天

- Day 4-5: 2.1A + 2.2A（11 小時）
- Day 6: 2.3 per-factor 限制（3 小時）
- Day 7: 完整測試驗證

**悲觀情況（路徑 B）**：5 天

- Day 4-5: 2.1B 修復 factor（6-8 小時）
- Day 6: 2.2A + 2.3（6 小時）
- Day 7: 2.1A 簡化模板（作為額外保護）
- Day 8: 完整測試驗證

---

### 階段 2 成功標準

完成後的預期狀態：

- [x] Factor Graph 成功率 ≥70%（穩定 fallback 目標）
- [x] 平均執行時間 <90s（可接受範圍）
- [x] 無系統懸掛（timeout 機制有效）
- [x] 清楚的錯誤訊息和進度日誌
- [x] 通過 20 iteration 三模式測試驗證

**風險緩解**：

- 如果 2.1A 只達到 50% → 進一步簡化至 3 factors
- 如果 2.1B 無法快速修復 → 暫時禁用該 factor
- 如果記憶體是瓶頸 → 實作 2.4C 資料優化
- 如果所有修復都不夠 → 升級至階段 3 架構優化

---

## 測試驗證策略

### 測試金字塔設計

```
階段 1 測試（診斷用）：
┌─────────────────────┐
│   20-iteration      │ ← 完整驗證（耗時）
│   三模式測試        │
├─────────────────────┤
│  單一 template      │ ← 模板驗證（中等）
│  測試 (3次執行)     │
├─────────────────────┤
│ 最小化測試 (1.3)    │ ← 快速診斷（<5分鐘）
│  1 factor測試       │
└─────────────────────┘

階段 2 測試（修復驗證）：
┌─────────────────────┐
│ 20-iteration完整測試 │ ← 最終驗證
├─────────────────────┤
│ 3×每個模板測試      │ ← 中層驗證
├─────────────────────┤
│ 單次快速測試        │ ← 開發時測試
└─────────────────────┘
```

### 分階段成功標準

**Level 1：基本可用（最低要求）**

- Factor Graph 成功率：≥25%
- 執行時間：<120s
- 系統穩定性：無懸掛
- 驗證：10 iteration 測試

**Level 2：穩定 Fallback（目標）**

- Factor Graph 成功率：≥70%
- 執行時間：<90s
- Sharpe 基線：≥0.3（可接受）
- 驗證：20 iteration 測試

**Level 3：優質表現（理想）**

- Factor Graph 成功率：≥80%
- 執行時間：<60s
- Sharpe 基線：≥0.5
- 驗證：50 iteration 測試

---

### 快速驗證腳本

**檔案**：`experiments/quick_validation.py`

```python
"""快速驗證腳本 - 3次測試確認修復有效"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_quick_validation(iterations=3):
    """快速驗證：執行3次 Factor Graph 測試"""

    # 使用 fg_only 配置
    config = LearningConfig.from_file(
        "experiments/llm_learning_validation/config_fg_only_20.yaml"
    )

    # 僅執行 3 次迭代
    config.max_iterations = iterations

    logger.info(f"Running {iterations} iterations for quick validation...")

    loop = LearningLoop(config)
    loop.run()

    # 分析結果
    from src.learning.iteration_history import IterationHistory
    history = IterationHistory(config.history_file)

    successes = sum(1 for r in history.records if r.get('metrics', {}).get('execution_success'))
    success_rate = successes / iterations if iterations > 0 else 0

    avg_time = sum(
        r.get('execution_result', {}).get('execution_time', 0)
        for r in history.records
    ) / iterations

    logger.info(f"")
    logger.info(f"=== QUICK VALIDATION RESULTS ===")
    logger.info(f"Iterations: {iterations}")
    logger.info(f"Successes: {successes}/{iterations}")
    logger.info(f"Success Rate: {success_rate:.1%}")
    logger.info(f"Avg Time: {avg_time:.1f}s")

    # 判定
    if success_rate >= 0.7:
        logger.info(f"✅ PASSED: Success rate meets target (≥70%)")
        return True
    elif success_rate >= 0.25:
        logger.info(f"⚠️  PARTIAL: Meets minimum (≥25%) but below target")
        return True
    else:
        logger.info(f"❌ FAILED: Below minimum threshold (<25%)")
        return False

if __name__ == "__main__":
    success = run_quick_validation()
    sys.exit(0 if success else 1)
```

---

## 實施流程圖

### 完整流程

```
開始
  ↓
[Day 1 並行]
  ├─ 1.1 時序儀表 (2-3h) ──────┐
  └─ 1.2 模板檢查 (1-2h) ──────┤
                                ↓
                          [產出診斷基線]
                                ↓
[Day 2 決策點]
  ↓
1.3 最小化測試 (2-3h + 執行)
  ↓
┌─────────┴─────────┐
│                   │
成功 (<30s)     失敗 (>420s)
│                   │
80%機率          15%機率
│                   │
複雜度問題      Factor問題
│                   │
└─→ [路徑A]    └─→ [路徑B]
    │               │
    ↓               ↓
[Day 4-5]      [Day 4-5]
2.1A 簡化      1.4 Per-Factor時序
模板(8h)       ↓
    ↓          1.5 檢查實作
2.2A 診斷      ↓
增強(3h)       2.1B 修復Factor (6-8h)
    ↓               ↓
[Day 6]        [Day 6-7]
2.3 防禦       2.2A + 2.3 (6h)
時限(3h)       ↓
    ↓          2.1A 補強
[Day 7]        ↓
測試驗證   [Day 8]
    │          測試驗證
    └─────┬────┘
          ↓
    成功率 ≥70%？
          ↓
    ┌─────┴─────┐
    是          否
    ↓           ↓
  完成      調整/升級
            (簡化至3因子
             或進階段3)
```

---

## 立即行動指南

### Day 1：診斷工具準備

**任務 1.1：實作時序儀表**

```bash
# 1. 找到 strategy.py 檔案
find src -name "*strategy*.py" -path "*/factor_graph/*"

# 2. 備份原始檔案
cp [找到的檔案] [找到的檔案].backup

# 3. 編輯檔案，在 execute() 方法加入時序日誌
# （參考階段 1 Task 1.1 的代碼）

# 4. 驗證語法
python3 -m py_compile [檔案路徑]
```

**任務 1.2：檢查模板組成**

```bash
# 執行搜尋
echo "=== Template Definition Search ===" > docs/template_analysis.txt
find src -name "*.py" | xargs grep -n "template_0\|template_1\|template_2" >> docs/template_analysis.txt

echo "" >> docs/template_analysis.txt
echo "=== FactorGraph Initialization ===" >> docs/template_analysis.txt
grep -rn -A 30 "def.*template\|class.*Template" src/factor_graph/ src/learning/ >> docs/template_analysis.txt

echo "" >> docs/template_analysis.txt
echo "=== Factor Registry Usage ===" >> docs/template_analysis.txt
grep -rn -B 5 -A 10 "add_factor\|register_factor" src/factor_graph/ >> docs/template_analysis.txt

# 查看結果
cat docs/template_analysis.txt
```

**Day 1 結束檢查**：

```bash
# 檢查時序儀表是否正確實作
grep -n "\[TIMING\]" src/factor_graph/strategy.py

# 檢查模板分析是否完成
wc -l docs/template_analysis.txt  # 應該有內容
```

---

### Day 2：關鍵決策點

**任務 1.3：建立並執行最小化測試**

```bash
# 1. 創建測試檔案（複製階段 1 Task 1.3 的代碼）
cat > experiments/diagnostic_minimal_test.py << 'EOF'
[完整代碼見 Task 1.3]
EOF

# 2. 執行測試
python3 experiments/diagnostic_minimal_test.py 2>&1 | tee experiments/minimal_test_output.log

# 3. 分析結果
grep -E "SUCCESS|FAILED|執行時間" experiments/minimal_test_output.log

# 4. 根據結果決定路徑
# - 如果成功 (<30s) → 進入路徑 A（複雜度問題）
# - 如果失敗 (>420s) → 進入路徑 B（Factor 問題）
# - 如果錯誤 (<30s error) → 修復錯誤後重試
```

---

### Day 3+：執行選定路徑

**路徑 A：複雜度問題（80%機率）**

```bash
# Day 4-5: 實作簡化模板
# 創建 src/factor_graph/templates.py（見階段 2 Task 2.1A）
# 整合到 InnovationEngine

# Day 6: 增加診斷能力
# 修改 BacktestExecutor timeout（見 Task 2.2A）

# Day 7: 驗證測試
python3 experiments/quick_validation.py
```

**路徑 B：Factor 實作問題（15%機率）**

```bash
# Day 4-5: 實作 per-factor timing（見 Task 1.4）
# 找出慢 factor
# 檢查並修復 factor 實作（見 Task 2.1B）

# Day 6-7: 整合修復 + 驗證
```

---

## 交付物清單

### 立即創建

- [x] `docs/FACTOR_GRAPH_TIMEOUT_IMPROVEMENT_PLAN.md` - 完整改善計畫 ✅
- [x] `docs/FACTOR_GRAPH_PHASE1_PHASE2_DETAILED_PLAN.md` - 本文檔 ✅
- [ ] `docs/template_analysis.txt` - Task 1.2 輸出
- [ ] `experiments/diagnostic_minimal_test.py` - Task 1.3 測試腳本
- [ ] `docs/PHASE1_PHASE2_PROGRESS_TRACKER.md` - 進度追蹤

### 階段 1 輸出

- [ ] `docs/FACTOR_GRAPH_DIAGNOSTIC_REPORT.md` - 診斷報告
- [ ] `experiments/minimal_test_output.log` - 1.3 測試結果

### 階段 2 輸出

- [ ] `src/factor_graph/templates.py` - 簡化模板（路徑 A）
- [ ] `experiments/quick_validation.py` - 快速驗證腳本
- [ ] `docs/FACTOR_GRAPH_FIX_REPORT.md` - 修復報告

---

## 風險管理

### 風險與應變

**風險 1：根本原因與假設不符**

- 機率：30%
- 影響：高（可能需要重新診斷）
- 應變：
  - 保持診斷階段的靈活性
  - 每個診斷步驟產出可驗證的結論
  - 如果假設被推翻，快速調整方向

**風險 2：Factor 實作有根本性問題**

- 機率：20%
- 影響：高（需要重寫 factors）
- 應變：
  - 優先修復最常用的 factors
  - 建立 factor 單元測試
  - 逐步替換問題 factors

**風險 3：硬體限制（記憶體/CPU）**

- 機率：15%
- 影響：中（可能需要優化資料結構）
- 應變：
  - 實作資料分批處理
  - 使用更高效的資料結構（NumPy 而非 Pandas）
  - 考慮使用資料庫而非記憶體載入

**風險 4：時程延遲**

- 機率：40%
- 影響：中（影響產品發布）
- 應變：
  - 階段 2 為最小可行版本（MVP）
  - 階段 3 可分批實施
  - 優先實作高 ROI 的優化項目

### 風險預警指標

- 🚨 1.3 測試結果不明確（30-420s之間）→ 需補充診斷
- 🚨 2.1A 只達到 50% → 進一步簡化至 3 factors
- 🚨 修復後仍有懸掛 → 檢查 timeout 機制
- 🚨 記憶體使用 >6GB → 實作 2.4C 資料優化

---

## 關鍵里程碑

### M1 (Day 1 EOD)：診斷工具就緒

- [x] 時序儀表實作完成
- [x] 模板組成分析完成
- [x] 知道每個模板使用多少 factors

### M2 (Day 2 EOD)：路徑選擇

- [x] 最小化測試執行完成
- [x] 結果明確（成功/失敗/錯誤）
- [x] 已選擇修復路徑（A/B/C）
- [x] Day 3-5 工作已排程

### M3 (Day 5-6)：修復實作

- [x] 選定的修復已實作
- [x] 初步測試通過（快速驗證）
- [x] 準備進入完整測試

### M4 (Day 7-8)：完整驗證

- [x] 20 iteration 測試通過
- [x] 成功率 ≥70%
- [x] 執行時間 <90s
- [x] 無懸掛現象

---

## 進度追蹤

### Day 1 進度報告範本

```markdown
## Day 1 進度報告

### 完成項目
- [x] 時序儀表實作
- [x] 模板組成分析

### 發現
- Template 0: [X] factors
- Template 1: [X] factors
- Template 2: [X] factors
- 複雜度評估: [低/中/高]

### 明天計畫
- 執行最小化測試（1.3）
- 根據結果選擇修復路徑

### 風險/阻礙
- [如有]
```

### 每日站會格式

1. 昨天完成了什麼？
2. 今天計畫做什麼？
3. 遇到什麼阻礙？
4. 是否需要調整計畫？

---

## 成功慶祝與失敗應變

### 如果達到 70% 目標

1. 產出最終報告
2. 更新文檔
3. 關閉診斷相關 TODOs
4. 計劃階段 3 優化（可選）

### 如果僅達到 25-69%

1. 分析差距原因
2. 實施額外簡化（3 factors）
3. 或部分實施階段 3 優化
4. 重新測試

### 如果低於 25%

1. 緊急回顧所有假設
2. 考慮架構級問題
3. 評估是否需要重寫 Factor 系統
4. 與 stakeholder 討論備選方案

---

## 最終檢查清單

開始執行前確認：

- [ ] 已閱讀完整改善計畫
- [ ] 理解階段 1-2 的目標和策略
- [ ] 已備份關鍵檔案
- [ ] 測試環境準備就緒
- [ ] 時間已安排（預留 6-10 天）
- [ ] 知道如何根據 1.3 結果選擇路徑

---

## 附錄

### 相關文檔

- `docs/FACTOR_GRAPH_TIMEOUT_IMPROVEMENT_PLAN.md` - 完整改善計畫（3階段）
- `.spec-workflow/steering/product.md` - 系統架構說明
- `.spec-workflow/steering/tech.md` - 技術架構文檔

### 參考資源

- Phase 2 Matrix-Native 實作文檔
- Factor Library Registry 說明
- FinLab 數據適配器文檔

---

**準備好了嗎？讓我們開始執行！**
