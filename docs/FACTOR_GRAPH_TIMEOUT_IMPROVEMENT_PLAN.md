# Factor Graph Timeout 問題完整改善方案

## 執行摘要

**問題**: Factor Graph 模式 100% timeout (0/20 成功)，而 LLM Only 模式有 25% 成功率
**根本原因**: 策略執行階段的計算瓶頸（非資料載入）
**證據**: 資料載入 <1秒，然後系統懸掛 5+ 小時
**信心度**: 中等 (60%) - 需要額外診斷確認具體原因

---

## 三階段改善計畫

### 第一階段：緊急診斷 (2-3 天)
**目標**: 精確定位瓶頸的具體位置和原因

#### 1.1 新增執行階段時序儀表 (P1 - 立即執行)

**目的**: 識別 strategy.execute() 中哪個階段導致懸掛

**實作步驟**:

```python
# src/factor_graph/strategy.py - execute() 方法修改

def execute(self, sim):
    """Execute strategy with detailed timing instrumentation."""
    import time
    from datetime import datetime

    logger = logging.getLogger(__name__)

    # Phase 1: Data Loading
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 1 START: Data loading at {datetime.now()}")

    try:
        self._load_data()
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 1 COMPLETE: Data loaded in {phase_time:.2f}s")
        logger.info(f"[TIMING] Loaded {len(self.data_frames)} data fields")

    except Exception as e:
        logger.error(f"[TIMING] Phase 1 FAILED: {e}")
        raise

    # Phase 2: Graph Execution (SUSPECT)
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

    # Phase 3: Validation
    phase_start = time.time()
    logger.info(f"[TIMING] Phase 3 START: Validation at {datetime.now()}")

    try:
        self._validate_result(result)
        phase_time = time.time() - phase_start
        logger.info(f"[TIMING] Phase 3 COMPLETE: Validated in {phase_time:.2f}s")

    except Exception as e:
        logger.error(f"[TIMING] Phase 3 FAILED: {e}")
        raise

    # Phase 4: Backtest
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

**預期輸出**:
```
[TIMING] Phase 1 START: Data loading at 2025-11-16 10:00:00
[TIMING] Phase 1 COMPLETE: Data loaded in 0.98s
[TIMING] Loaded 3 data fields
[TIMING] Phase 2 START: Graph execution at 2025-11-16 10:00:01
[TIMING] Factor count: 11
[系統在這裡懸掛 - 將揭示問題在 Phase 2]
```

**成功標準**: 能夠確認瓶頸在 Phase 2 (graph execution)

---

#### 1.2 檢查模板策略組成 (P1 - 立即執行)

**目的**: 了解 template_0, template_1, template_2 使用了多少 factors

**實作步驟**:

```bash
# 搜尋模板策略定義
find . -name "*.py" -o -name "*.json" -o -name "*.yaml" | xargs grep -l "template_0\|template_1\|template_2"

# 檢查 FactorGraph 初始化邏輯
grep -A 50 "class.*FactorGraph" src/factor_graph/*.py
```

**需要回答的問題**:
1. 模板策略包含多少個 factors？
2. 是否使用了所有 13 個可用 factors？
3. Factor 之間的依賴關係深度如何？

**假設驗證**:
- **如果 template 使用 10+ factors** → 證實複雜度假設（80% 機率）
- **如果 template 使用 3-5 factors** → 問題在 factor 計算本身（需進入 1.3）

---

#### 1.3 建立最小化測試策略 (P1 - 關鍵診斷)

**目的**: 隔離問題 - 驗證簡單策略是否能成功執行

**實作步驟**:

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

**執行測試**:
```bash
python3 experiments/diagnostic_minimal_test.py
```

**可能結果與對應行動**:

| 結果 | 執行時間 | 結論 | 下一步 |
|------|----------|------|--------|
| ✅ 成功 | <30s | 問題在於策略複雜度 | 進入階段 2.1 (簡化模板) |
| ❌ 失敗 | >420s timeout | 問題在單一 factor 計算 | 進入 1.4 (檢查 factor 實作) |
| ❌ 失敗 | <30s error | 發現新的錯誤類型 | 修復新錯誤 |

---

#### 1.4 新增 Per-Factor 執行時序 (P1 - 如果 1.3 失敗)

**目的**: 如果連最簡單策略都失敗，需要追蹤每個 factor 的執行時間

**實作步驟**:

```python
# src/factor_graph/factor_graph.py - execute() 方法修改

def execute(self, data_frames):
    """Execute factor graph with per-factor timing."""
    import time
    from datetime import datetime

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

**預期輸出**:
```
[GRAPH] Starting DAG execution with 11 factors
[GRAPH] Execution order: ['momentum', 'ma_filter', 'atr', ...]
[GRAPH] Factor 1/11: momentum START at 2025-11-16 10:00:01
[GRAPH] Factor momentum COMPLETE in 0.45s
[GRAPH] Factor 2/11: ma_filter START at 2025-11-16 10:00:02
[系統在這裡懸掛 - 將揭示是哪個 factor 導致問題]
```

---

#### 1.5 檢查 Factor 實作 (P2 - 視 1.4 結果)

**目的**: 檢查導致懸掛的 factor 是否有無窮迴圈或 O(n²) 操作

**實作步驟**:

```bash
# 檢查所有 factor 的實作
find src/factor_library -name "*.py" -exec echo "=== {} ===" \; -exec cat {} \;

# 特別注意：
# 1. 迴圈結構 (for, while)
# 2. 嵌套迴圈 (nested loops)
# 3. 大型滾動視窗 (rolling windows > 252)
# 4. Pandas apply() 呼叫
```

**尋找的問題模式**:
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

### 診斷階段總結

**完成診斷階段後，你將知道**:
1. ✅ 瓶頸的精確位置（Phase 1/2/3/4 中的哪一個）
2. ✅ 模板策略的複雜度（使用了多少 factors）
3. ✅ 簡單策略是否能執行成功
4. ✅ 如果單一 factor 有問題，是哪一個 factor
5. ✅ 該 factor 的具體問題（無窮迴圈、O(n²)、記憶體等）

**預計時間**: 2-3 天（包含測試執行）
**輸出**: 具體的根本原因報告和下一步行動

---

## 第二階段：快速修復 (3-5 天)

**目標**: 基於診斷結果實施快速修復，使 Factor Graph 模式達到 ≥25% 成功率

### 2.1 簡化模板策略 (P1 - 如果診斷顯示複雜度問題)

**診斷觸發條件**: 1.3 最小化測試成功 + 模板使用 >5 factors

**實作策略**:

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

**整合到 InnovationEngine**:

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

**預期效果**:
- 減少 50-70% 的計算量
- 執行時間從 >420s 降至 <60s
- 成功率從 0% 提升至 25-40%

---

### 2.2 增加 Timeout 並新增進度日誌 (P1 - 輔助診斷)

**目的**: 在修復完成前，提供更多除錯資訊

**實作步驟**:

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

**預期輸出**:
```
[HEARTBEAT] Strategy still executing... 30s elapsed
[HEARTBEAT] Strategy still executing... 60s elapsed
[HEARTBEAT] Strategy still executing... 90s elapsed
[TIMING] Phase 2 COMPLETE: Graph executed in 85.3s
```

---

### 2.3 實作 Per-Factor 執行時限 (P2 - 防禦性程式設計)

**目的**: 防止單一 factor 懸掛整個系統

**實作策略**:

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

**保護效果**:
- 單一 factor 最多執行 120 秒
- 總執行時間 = factors 數量 × 120s (最壞情況)
- 5 個 factors = 最多 600s (10分鐘)

---

### 2.4 優化資料載入 (P2 - 如果診斷顯示資料問題)

**診斷觸發條件**: Phase 1 (資料載入) 超過 10 秒

**實作策略**:

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

def _analyze_required_data_fields(self):
    """Analyze which data fields are required by factors."""
    required = set()

    for factor_name in self.factor_graph.factors:
        factor = self.factor_graph.factors[factor_name]

        # 檢查 factor 的資料需求
        if hasattr(factor, 'required_data'):
            required.update(factor.required_data)

    return list(required)
```

**預期效果**:
- 從載入 200 個欄位減少到 10-20 個
- 載入時間從 10s 減少到 1-2s
- 記憶體使用減少 80-90%

---

### 快速修復階段總結

**完成後的預期狀態**:
- ✅ Factor Graph 成功率: 0% → 25-40%
- ✅ 平均執行時間: >420s → 30-90s
- ✅ 系統穩定性: 無懸掛、清楚的錯誤訊息
- ✅ 除錯能力: 詳細的時序和進度日誌

**預計時間**: 3-5 天（包含測試驗證）
**風險**: 如果根本原因與假設不符，可能需要返回診斷階段

---

## 第三階段：架構優化 (1-2 週)

**目標**: 長期優化，使 Factor Graph 達到與 LLM 相當或更好的效能

### 3.1 Factor 計算優化 (P1 - 效能提升)

**目的**: 優化個別 factor 的計算效率

**實作策略**:

#### 3.1.1 向量化所有 Pandas 操作

```python
# src/factor_library/momentum_factors.py - 優化範例

class MomentumFactor:
    def calculate(self, data, period=20):
        """Optimized momentum calculation."""
        close = data.get('close')

        # ❌ 舊方法：逐行計算 (慢)
        # momentum = close.apply(lambda x: x / x.shift(period) - 1)

        # ✅ 新方法：向量化 (快 10-100 倍)
        momentum = close.pct_change(periods=period)

        return momentum
```

#### 3.1.2 使用 Numba JIT 編譯

```python
# src/factor_library/turtle_factors.py - 使用 Numba 加速

from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_atr_numba(high, low, close, period):
    """JIT-compiled ATR calculation for 10-50x speedup."""
    n = len(high)
    tr = np.zeros(n)
    atr = np.zeros(n)

    # True Range 計算
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, hc, lc)

    # ATR 滾動平均
    atr[:period] = np.nan
    atr[period] = tr[1:period+1].mean()

    for i in range(period+1, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period

    return atr

class ATRFactor:
    def calculate(self, data, period=20):
        """ATR with Numba acceleration."""
        high = data.get('high').values
        low = data.get('low').values
        close = data.get('close').values

        atr_values = calculate_atr_numba(high, low, close, period)

        # 轉回 DataFrame
        return pd.DataFrame(atr_values,
                          index=data.get('close').index,
                          columns=data.get('close').columns)
```

**預期加速**: 10-50 倍（視 factor 複雜度）

---

### 3.2 結果快取系統 (P1 - 避免重複計算)

**目的**: Factor 計算結果可在不同策略間重複使用

**實作策略**:

```python
# src/factor_graph/cache.py (新建檔案)

"""
Factor Calculation Cache
避免重複計算相同的 factors
"""

import hashlib
import pickle
from pathlib import Path

class FactorCache:
    """Cache for factor calculation results."""

    def __init__(self, cache_dir="experiments/factor_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, factor_name, params, data_hash):
        """Generate unique cache key."""
        key_str = f"{factor_name}_{params}_{data_hash}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, factor_name, params, data_hash):
        """Retrieve cached result if available."""
        key = self.get_cache_key(factor_name, params, data_hash)
        cache_file = self.cache_dir / f"{key}.pkl"

        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, factor_name, params, data_hash, result):
        """Cache calculation result."""
        key = self.get_cache_key(factor_name, params, data_hash)
        cache_file = self.cache_dir / f"{key}.pkl"

        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
```

**整合到 FactorGraph**:

```python
# src/factor_graph/factor_graph.py - 新增快取

from src.factor_graph.cache import FactorCache

class FactorGraph:
    def __init__(self):
        self.cache = FactorCache()
        # ... 其他初始化

    def execute(self, data_frames):
        """Execute with caching."""

        # 計算資料雜湊（相同資料可重複使用快取）
        data_hash = self._hash_data(data_frames)

        for factor_name in execution_order:
            factor = self.factors[factor_name]
            params = self.graph.nodes[factor_name].get('params', {})

            # 嘗試從快取取得
            cached_result = self.cache.get(factor_name, params, data_hash)

            if cached_result is not None:
                logger.info(f"Factor {factor_name} loaded from cache")
                results[factor_name] = cached_result
                continue

            # 計算並快取
            logger.info(f"Factor {factor_name} calculating...")
            result = factor.calculate(data_frames, **params)
            self.cache.set(factor_name, params, data_hash, result)

            results[factor_name] = result

        return self._combine_results(results)
```

**預期效果**:
- 第一次執行: 正常時間
- 後續執行: 80-95% 時間節省
- 特別有利於迭代學習（相同資料重複使用）

---

### 3.3 記憶體使用監控與限制 (P2 - 防止記憶體問題)

**目的**: 防止記憶體耗盡導致系統變慢

**實作策略**:

```python
# src/utils/memory_monitor.py (新建檔案)

"""
Memory Usage Monitoring
監控並限制記憶體使用
"""

import psutil
import logging

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Monitor memory usage during execution."""

    def __init__(self, max_memory_gb=8.0):
        self.max_memory_bytes = max_memory_gb * 1024 * 1024 * 1024
        self.process = psutil.Process()

    def check_memory(self):
        """Check current memory usage."""
        mem_info = self.process.memory_info()
        current_mb = mem_info.rss / (1024 * 1024)
        max_mb = self.max_memory_bytes / (1024 * 1024)

        usage_pct = (mem_info.rss / self.max_memory_bytes) * 100

        logger.info(f"[MEMORY] Current: {current_mb:.1f}MB / {max_mb:.1f}MB ({usage_pct:.1f}%)")

        if usage_pct > 90:
            raise MemoryError(f"Memory usage exceeded 90% ({current_mb:.1f}MB)")

        return current_mb
```

**整合到 BacktestExecutor**:

```python
# src/backtest/executor.py - 新增記憶體監控

from src.utils.memory_monitor import MemoryMonitor

class BacktestExecutor:
    def __init__(self, timeout=900, max_memory_gb=8.0):
        self.timeout = timeout
        self.memory_monitor = MemoryMonitor(max_memory_gb)

    def execute_strategy(self, strategy, sim):
        """Execute with memory monitoring."""

        # 執行前檢查
        self.memory_monitor.check_memory()

        # 執行策略
        result = strategy.execute(sim)

        # 執行後檢查
        self.memory_monitor.check_memory()

        return result
```

---

### 3.4 並行 Factor 計算 (P3 - 進階優化)

**目的**: 利用多核心平行計算獨立的 factors

**實作策略**:

```python
# src/factor_graph/parallel_executor.py (新建檔案)

"""
Parallel Factor Execution
平行執行獨立的 factors
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import networkx as nx

class ParallelFactorExecutor:
    """Execute independent factors in parallel."""

    def __init__(self, max_workers=4):
        self.max_workers = max_workers

    def execute_parallel(self, factor_graph, data_frames):
        """Execute factors in parallel based on dependency graph."""

        # 識別可平行執行的 factor 組
        levels = list(nx.topological_generations(factor_graph.graph))

        logger.info(f"Factor execution levels: {len(levels)}")
        for i, level in enumerate(levels):
            logger.info(f"  Level {i}: {len(level)} factors (parallel)")

        results = {}

        # 逐層執行（層內平行）
        for level_num, level_factors in enumerate(levels):
            logger.info(f"Executing level {level_num} with {len(level_factors)} factors")

            if len(level_factors) == 1:
                # 單一 factor，直接執行
                factor_name = list(level_factors)[0]
                results[factor_name] = self._execute_single_factor(
                    factor_name, factor_graph, data_frames, results
                )
            else:
                # 多個 factors，平行執行
                with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {}

                    for factor_name in level_factors:
                        future = executor.submit(
                            self._execute_single_factor,
                            factor_name, factor_graph, data_frames, results
                        )
                        futures[future] = factor_name

                    for future in as_completed(futures):
                        factor_name = futures[future]
                        results[factor_name] = future.result()

        return factor_graph._combine_results(results)

    def _execute_single_factor(self, factor_name, factor_graph, data_frames, previous_results):
        """Execute a single factor."""
        factor = factor_graph.factors[factor_name]
        params = factor_graph.graph.nodes[factor_name].get('params', {})

        # 合併先前的結果（依賴項）
        combined_data = {**data_frames, **previous_results}

        return factor.calculate(combined_data, **params)
```

**預期加速**: 2-4 倍（取決於 factor 依賴關係）

---

### 架構優化階段總結

**完成後的預期狀態**:
- ✅ Factor 計算效率: 提升 10-50 倍（向量化 + Numba）
- ✅ 重複計算: 減少 80-95%（快取系統）
- ✅ 記憶體安全: 防止記憶體耗盡
- ✅ 多核心利用: 2-4 倍加速（平行執行）
- ✅ 整體效能: Factor Graph 可能超越 LLM 模式

**預計時間**: 1-2 週
**長期效益**: 系統可擴展至更複雜的策略

---

## 實施時程表

### 第 1-3 天：緊急診斷
- Day 1: 實作時序儀表 (1.1) + 檢查模板 (1.2)
- Day 2: 建立並執行最小化測試 (1.3)
- Day 3: 根據結果實作 per-factor timing (1.4) 或檢查 factor 實作 (1.5)

### 第 4-8 天：快速修復
- Day 4-5: 簡化模板策略 (2.1)
- Day 6: 增加 timeout 和進度日誌 (2.2)
- Day 7: 實作 per-factor 時限 (2.3)
- Day 8: 測試驗證，確保達到 25%+ 成功率

### 第 9-22 天：架構優化
- Day 9-12: Factor 計算優化 (3.1) - 向量化 + Numba
- Day 13-15: 快取系統 (3.2)
- Day 16-18: 記憶體監控 (3.3)
- Day 19-21: 平行執行 (3.4) - 選擇性實作
- Day 22: 整合測試與效能評估

---

## 成功指標

### 階段 1 成功標準（診斷）
- ✅ 確認瓶頸的精確位置
- ✅ 了解模板策略組成
- ✅ 最小化測試結果明確
- ✅ 產出具體的根本原因報告

### 階段 2 成功標準（快速修復）
- ✅ Factor Graph 成功率 ≥ 25%
- ✅ 平均執行時間 < 90 秒
- ✅ 無系統懸掛或 deadlock
- ✅ 清楚的錯誤訊息和日誌

### 階段 3 成功標準（架構優化）
- ✅ Factor Graph 成功率 ≥ 40%
- ✅ 平均執行時間 < 30 秒
- ✅ 記憶體使用 < 4GB
- ✅ Factor 計算效率提升 10 倍以上
- ✅ 快取命中率 > 80%

### 最終目標
- 🎯 Factor Graph 效能 ≥ LLM Only 模式
- 🎯 Hybrid 模式成為最佳選擇（結合兩者優勢）
- 🎯 系統穩定性和可維護性顯著提升

---

## 風險與應變計畫

### 風險 1: 根本原因與假設不符
**機率**: 30%
**影響**: 高（可能需要重新診斷）
**應變**:
- 保持診斷階段的靈活性
- 每個診斷步驟產出可驗證的結論
- 如果假設被推翻，快速調整方向

### 風險 2: Factor 實作有根本性問題
**機率**: 20%
**影響**: 高（需要重寫 factors）
**應變**:
- 優先修復最常用的 factors
- 建立 factor 單元測試
- 逐步替換問題 factors

### 風險 3: 硬體限制（記憶體/CPU）
**機率**: 15%
**影響**: 中（可能需要優化資料結構）
**應變**:
- 實作資料分批處理
- 使用更高效的資料結構（NumPy 而非 Pandas）
- 考慮使用資料庫而非記憶體載入

### 風險 4: 時程延遲
**機率**: 40%
**影響**: 中（影響產品發布）
**應變**:
- 階段 2 為最小可行版本（MVP）
- 階段 3 可分批實施
- 優先實作高 ROI 的優化項目

---

## 資源需求

### 開發資源
- 1 位資深工程師（全職）
- 測試環境（WSL2 + 8GB RAM 最低）
- 約 50-100 小時開發時間

### 測試資源
- 回測資料（已有）
- 每個階段需要 3-5 次完整測試週期
- 每次測試 6-12 分鐘（修復後）

### 監控工具
- Python profiler (cProfile)
- Memory profiler (memory_profiler)
- Logging framework (已有)
- 時序分析工具（自行實作）

---

## 下一步行動

### 立即執行（今天）
1. ✅ 確認此改善計畫
2. 🔄 實作時序儀表（1.1）
3. 🔄 檢查模板策略組成（1.2）

### 明天
4. 建立最小化測試（1.3）
5. 執行診斷測試
6. 分析結果並調整計畫

### 本週內
7. 完成診斷階段（1.1-1.5）
8. 產出根本原因報告
9. 開始快速修復（2.1-2.2）

---

## 附錄：問題追蹤

### 已確認問題
- ✅ P0 命名不相容：已修復（naming adapter + boolean conversion）
- ✅ Factor Graph 100% timeout：根本原因已初步識別

### 待確認問題
- ❓ 模板策略使用多少 factors？
- ❓ 哪個 factor 導致懸掛？
- ❓ 計算瓶頸的具體位置？
- ❓ 是否有記憶體問題？

### 技術債務
- 🔧 缺少 per-factor 執行時序
- 🔧 缺少記憶體監控
- 🔧 缺少 factor 單元測試
- 🔧 缺少計算結果快取

---

**本文件狀態**: v1.0 - 初始完整計畫
**最後更新**: 2025-11-16
**負責人**: [待指派]
**審核狀態**: 待審核
