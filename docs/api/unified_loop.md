# UnifiedLoop API Reference

**版本**: v1.0
**更新日期**: 2025-11-23
**Python版本**: 3.10+

---

## 目錄

1. [UnifiedLoop類別](#unifiedloop類別)
2. [UnifiedConfig類別](#unifiedconfig類別)
3. [TemplateIterationExecutor類別](#templateiterationexecutor類別)
4. [數據模型](#數據模型)
5. [異常類別](#異常類別)
6. [工具函數](#工具函數)

---

## UnifiedLoop類別

### 類別定義

```python
class UnifiedLoop:
    """
    統一學習循環Facade。

    整合LearningLoop、Template Mode、JSON Parameter Output、
    Learning Feedback、Monitoring和Docker Sandbox功能。

    設計模式：
        - Facade Pattern: 統一入口，簡化API
        - Strategy Pattern: TemplateIterationExecutor vs StandardIterationExecutor
        - Dependency Injection: 組件通過構造函數注入
    """
```

### 構造函數

#### `__init__(**kwargs) -> None`

創建UnifiedLoop實例。

**參數**:

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `max_iterations` | `int` | `10` | 最大迭代次數（1-1000） |
| `continue_on_error` | `bool` | `False` | 錯誤時是否繼續 |
| `llm_model` | `str` | `"gemini-2.5-flash"` | LLM模型名稱 |
| `api_key` | `Optional[str]` | `None` | API密鑰（或使用環境變數） |
| `llm_timeout` | `int` | `60` | LLM調用超時（秒） |
| `llm_temperature` | `float` | `0.7` | LLM溫度參數（0.0-2.0） |
| `llm_max_tokens` | `int` | `4000` | LLM最大輸出token數 |
| `template_mode` | `bool` | `False` | 啟用Template Mode |
| `template_name` | `str` | `"Momentum"` | Template名稱 |
| `use_json_mode` | `bool` | `False` | 啟用JSON Parameter Output |
| `enable_learning` | `bool` | `True` | 啟用Learning Feedback |
| `history_window` | `int` | `10` | 歷史窗口大小 |
| `enable_monitoring` | `bool` | `True` | 啟用監控系統 |
| `use_docker` | `bool` | `False` | 啟用Docker Sandbox |
| `timeout_seconds` | `int` | `420` | 回測超時（秒） |
| `start_date` | `str` | `"2018-01-01"` | 回測開始日期（YYYY-MM-DD） |
| `end_date` | `str` | `"2024-12-31"` | 回測結束日期（YYYY-MM-DD） |
| `fee_ratio` | `float` | `0.001425` | 交易費用比例（0.0-0.1） |
| `tax_ratio` | `float` | `0.003` | 交易稅率（0.0-0.1） |
| `resample` | `str` | `"M"` | 重新平衡頻率（D/W/M） |
| `history_file` | `str` | `"artifacts/data/iterations.jsonl"` | 歷史記錄檔案路徑 |
| `champion_file` | `str` | `"artifacts/data/champion.json"` | Champion檔案路徑 |
| `log_dir` | `str` | `"logs"` | 日誌目錄路徑 |
| `config_file` | `str` | `"config/learning_system.yaml"` | 配置檔案路徑 |
| `log_level` | `str` | `"INFO"` | 日誌級別 |
| `log_to_file` | `bool` | `True` | 寫入日誌檔案 |
| `log_to_console` | `bool` | `True` | 輸出到控制台 |

**引發異常**:
- `ConfigurationError`: 配置參數無效
- `RuntimeError`: 組件初始化失敗

**範例**:

```python
from src.learning.unified_loop import UnifiedLoop

# 最小配置
loop = UnifiedLoop(
    max_iterations=10,
    template_mode=True,
    template_name="Momentum"
)

# 完整配置
loop = UnifiedLoop(
    # Loop控制
    max_iterations=100,
    continue_on_error=False,

    # LLM配置
    llm_model="gemini-2.5-flash",
    llm_timeout=60,
    llm_temperature=0.7,

    # Template Mode
    template_mode=True,
    template_name="Momentum",
    use_json_mode=True,

    # Learning & Monitoring
    enable_learning=True,
    enable_monitoring=True,
    history_window=10,

    # Docker
    use_docker=False,

    # 回測
    timeout_seconds=420,
    start_date="2018-01-01",
    end_date="2024-12-31",

    # 檔案
    history_file="artifacts/data/iterations.jsonl",
    champion_file="artifacts/data/champion.json",
    log_dir="logs"
)
```

---

### 公開方法

#### `run() -> Dict[str, Any]`

執行主循環。

**返回值**:

```python
{
    "iterations_completed": int,      # 完成的迭代次數
    "champion": Optional[ChampionRecord],  # Champion記錄
    "interrupted": bool               # 是否被中斷
}
```

**引發異常**:
- `Exception`: 執行失敗時拋出

**範例**:

```python
loop = UnifiedLoop(max_iterations=10)

try:
    result = loop.run()
    print(f"Completed: {result['iterations_completed']}")
    if result['champion']:
        print(f"Champion Sharpe: {result['champion'].metrics.get('sharpe_ratio')}")
except Exception as e:
    print(f"Failed: {e}")
```

**行為**:
1. 執行LearningLoop.run()
2. 收集執行結果
3. 在finally區塊中關閉監控系統
4. 返回結果字典

---

### 公開屬性

#### `champion: Optional[ChampionRecord]`

當前Champion策略（向後相容API）。

**類型**: `Optional[ChampionRecord]`

**範例**:

```python
loop = UnifiedLoop(max_iterations=10)
result = loop.run()

# 方式1: 從result
champion = result['champion']

# 方式2: 從屬性（向後相容）
champion = loop.champion

if champion:
    print(f"Sharpe: {champion.metrics.get('sharpe_ratio')}")
    print(f"Iteration: {champion.iteration_num}")
    print(f"Code:\n{champion.strategy_code}")
```

---

#### `history: IterationHistory`

迭代歷史管理器（向後相容API）。

**類型**: `IterationHistory`

**範例**:

```python
loop = UnifiedLoop(max_iterations=10)
result = loop.run()

# 存取歷史
history = loop.history

# 查詢最近N次迭代
recent = history.load_recent(N=5)
for record in recent:
    print(f"Iteration {record.iteration_num}: {record.classification_level}")

# 查詢所有迭代
all_records = history.get_all()
print(f"Total iterations: {len(all_records)}")

# 查詢成功迭代
successful = [r for r in all_records if r.classification_level == "LEVEL_3"]
print(f"Successful iterations: {len(successful)}")
```

---

### 私有方法（內部使用）

#### `_initialize_monitoring() -> None`

初始化監控系統（Week 3.1）。

**組件**:
- MetricsCollector: Prometheus指標收集
- ResourceMonitor: 背景執行緒資源監控
- DiversityMonitor: 策略多樣性追蹤

**行為**:
- 檢查`config.enable_monitoring`標誌
- 初始化3個監控組件
- 啟動ResourceMonitor背景執行緒
- 失敗時graceful degradation

---

#### `_shutdown_monitoring() -> None`

關閉監控系統（Week 3.1）。

**行為**:
- 停止ResourceMonitor背景執行緒
- 匯出最終指標
- 在`run()`的finally區塊中自動調用
- 確保資源清理

---

## UnifiedConfig類別

### 類別定義

```python
@dataclass
class UnifiedConfig:
    """
    UnifiedLoop統一配置。

    整合AutonomousLoop和LearningLoop參數，添加Template Mode、
    JSON Parameter Output、Learning Feedback、Monitoring和Docker Sandbox支援。
    """
```

### 配置參數

#### Loop控制

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `max_iterations` | `int` | `10` | 1-1000 | 最大迭代次數 |
| `continue_on_error` | `bool` | `False` | - | 錯誤時是否繼續 |

#### LLM配置

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `llm_model` | `str` | `"gemini-2.5-flash"` | - | LLM模型名稱 |
| `api_key` | `Optional[str]` | `None` | - | API密鑰（優先使用環境變數） |
| `llm_timeout` | `int` | `60` | >0 | LLM調用超時（秒） |
| `llm_temperature` | `float` | `0.7` | 0.0-2.0 | 溫度參數 |
| `llm_max_tokens` | `int` | `4000` | >0 | 最大輸出token數 |

#### Template Mode參數

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `template_mode` | `bool` | `False` | - | 啟用Template Mode |
| `template_name` | `str` | `"Momentum"` | - | Template名稱 |

#### JSON Parameter Output參數

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `use_json_mode` | `bool` | `False` | 需要template_mode=True | 啟用JSON模式 |

#### Learning Feedback參數

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `enable_learning` | `bool` | `True` | - | 啟用學習反饋 |
| `history_window` | `int` | `10` | >0 | 歷史窗口大小 |

#### 監控參數

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `enable_monitoring` | `bool` | `True` | - | 啟用監控系統 |

#### Docker Sandbox參數

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `use_docker` | `bool` | `False` | - | 啟用Docker沙盒 |

#### 回測配置

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `timeout_seconds` | `int` | `420` | >0 | 回測超時（秒） |
| `start_date` | `str` | `"2018-01-01"` | YYYY-MM-DD | 回測開始日期 |
| `end_date` | `str` | `"2024-12-31"` | YYYY-MM-DD | 回測結束日期 |
| `fee_ratio` | `float` | `0.001425` | 0.0-0.1 | 交易費用比例 |
| `tax_ratio` | `float` | `0.003` | 0.0-0.1 | 交易稅率 |
| `resample` | `str` | `"M"` | D/W/M | 重新平衡頻率 |

#### 檔案路徑

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `history_file` | `str` | `"artifacts/data/iterations.jsonl"` | - | 歷史記錄檔案 |
| `champion_file` | `str` | `"artifacts/data/champion.json"` | - | Champion檔案 |
| `log_dir` | `str` | `"logs"` | - | 日誌目錄 |
| `config_file` | `str` | `"config/learning_system.yaml"` | - | 配置檔案 |

#### 日誌配置

| 參數 | 類型 | 預設值 | 約束 | 說明 |
|------|------|--------|------|------|
| `log_level` | `str` | `"INFO"` | DEBUG/INFO/WARNING/ERROR/CRITICAL | 日誌級別 |
| `log_to_file` | `bool` | `True` | - | 寫入檔案 |
| `log_to_console` | `bool` | `True` | - | 控制台輸出 |

---

### 方法

#### `validate() -> None`

驗證配置參數。

**檢查項目**:
1. Template Mode需要template_name
2. JSON Mode需要Template Mode
3. history_file和champion_file必須指定
4. max_iterations在1-1000範圍內

**引發異常**:
- `ConfigurationError`: 配置無效

**範例**:

```python
from src.learning.unified_config import UnifiedConfig

# 有效配置
config = UnifiedConfig(
    template_mode=True,
    template_name="Momentum",
    use_json_mode=True
)
config.validate()  # ✓ 通過

# 無效配置
try:
    config = UnifiedConfig(
        use_json_mode=True,  # 需要template_mode=True
        template_mode=False
    )
    config.validate()
except ConfigurationError as e:
    print(f"Error: {e}")
    # Error: use_json_mode=True requires template_mode=True
```

---

#### `to_learning_config() -> LearningConfig`

轉換為LearningConfig（LearningLoop兼容）。

**返回值**: `LearningConfig`實例

**範例**:

```python
unified_config = UnifiedConfig(
    max_iterations=100,
    template_mode=True,
    enable_learning=True
)

learning_config = unified_config.to_learning_config()
# 用於LearningLoop
```

---

#### `to_dict() -> Dict[str, Any]`

轉換為字典。

**返回值**: 所有配置參數的字典

**範例**:

```python
config = UnifiedConfig(max_iterations=100)
config_dict = config.to_dict()

print(config_dict['max_iterations'])  # 100
print(config_dict['template_mode'])   # False
print(config_dict['api_key'])         # '***' (masked)
```

---

## TemplateIterationExecutor類別

### 類別定義

```python
class TemplateIterationExecutor:
    """
    Template Mode迭代執行器。

    使用template-based參數生成替代freeform LLM或Factor Graph。
    整合Learning Feedback指導參數選擇。

    設計模式：
        - Strategy Pattern: 替代StandardIterationExecutor
        - Template Method Pattern: 10步驟迭代流程
    """
```

### 構造函數

#### `__init__(llm_client, feedback_generator, backtest_executor, champion_tracker, history, template_name, use_json_mode, config, **kwargs) -> None`

創建TemplateIterationExecutor實例。

**參數**:

| 參數 | 類型 | 說明 |
|------|------|------|
| `llm_client` | `LLMClient` | LLM客戶端 |
| `feedback_generator` | `FeedbackGenerator` | 反饋生成器 |
| `backtest_executor` | `BacktestExecutor` | 回測執行器 |
| `champion_tracker` | `ChampionTracker` | Champion追蹤器 |
| `history` | `IterationHistory` | 歷史管理器 |
| `template_name` | `str` | Template名稱 |
| `use_json_mode` | `bool` | JSON模式 |
| `config` | `Dict[str, Any]` | 配置字典 |

**引發異常**:
- `ValueError`: template_name無效
- `RuntimeError`: 組件初始化失敗

**範例**:

```python
from src.learning.template_iteration_executor import TemplateIterationExecutor
from src.learning.llm_client import LLMClient
# ... 其他導入

executor = TemplateIterationExecutor(
    llm_client=llm_client,
    feedback_generator=feedback_gen,
    backtest_executor=backtest_exec,
    champion_tracker=champion,
    history=hist,
    template_name="Momentum",
    use_json_mode=True,
    config={"history_window": 10, "use_docker": False}
)
```

---

### 公開方法

#### `execute_iteration(iteration_num: int, **kwargs) -> IterationRecord`

執行單次迭代。

**10步驟流程**:
1. 載入近期歷史
2. 生成反饋（如果啟用且非首次）
3. Template Mode決策
4. 生成參數（via TemplateParameterGenerator）
5. 生成策略程式碼（via TemplateCodeGenerator）
6. 執行策略（via BacktestExecutor或DockerExecutor）
7. 提取指標（via MetricsExtractor）
8. 分類成功（via SuccessClassifier）
9. 更新Champion（如果更好）
10. 創建並返回IterationRecord

**參數**:

| 參數 | 類型 | 說明 |
|------|------|------|
| `iteration_num` | `int` | 迭代編號（0-indexed） |
| `**kwargs` | `Any` | 額外參數 |

**返回值**: `IterationRecord`

**範例**:

```python
executor = TemplateIterationExecutor(...)

# 執行第0次迭代
record = executor.execute_iteration(0)

print(f"Iteration: {record.iteration_num}")
print(f"Classification: {record.classification_level}")
print(f"Sharpe: {record.metrics.sharpe_ratio if record.metrics else 'N/A'}")
print(f"Champion updated: {record.champion_updated}")
```

---

### 私有方法（內部使用）

#### `_generate_parameters(iteration_num: int, feedback: Optional[str]) -> Dict[str, Any]`

生成參數。

**參數**:
- `iteration_num`: 迭代編號
- `feedback`: 反饋字符串

**返回值**: 參數字典

---

#### `_generate_code(params: Dict[str, Any]) -> str`

從模板和參數生成程式碼。

**參數**:
- `params`: 參數字典

**返回值**: 生成的策略程式碼

---

#### `_create_error_record(iteration_num: int, error_msg: str, params: Dict[str, Any] = None, code: str = "") -> IterationRecord`

創建錯誤記錄。

**參數**:
- `iteration_num`: 迭代編號
- `error_msg`: 錯誤訊息
- `params`: 參數（如果已生成）
- `code`: 程式碼（如果已生成）

**返回值**: 錯誤IterationRecord

---

## 數據模型

### IterationRecord

迭代記錄數據類。

```python
@dataclass
class IterationRecord:
    """單次迭代的完整記錄"""

    iteration_num: int                    # 迭代編號
    generation_method: str                # 生成方法（"template"/"llm"/"factor_graph"）
    strategy_code: str                    # 策略程式碼
    execution_result: Dict[str, Any]      # 執行結果
    metrics: Optional[StrategyMetrics]    # 策略指標
    classification_level: str             # 分類級別（LEVEL_0-LEVEL_3）
    timestamp: str                        # 時間戳（ISO格式）
    champion_updated: bool                # Champion是否更新
    feedback_used: Optional[str]          # 使用的反饋
    template_name: Optional[str]          # Template名稱
    json_mode: Optional[bool]             # 是否JSON模式
```

**範例**:

```python
record = IterationRecord(
    iteration_num=0,
    generation_method="template",
    strategy_code="...",
    execution_result={"status": "success"},
    metrics=StrategyMetrics(sharpe_ratio=1.5),
    classification_level="LEVEL_3",
    timestamp="2025-11-23T10:00:00",
    champion_updated=True,
    feedback_used="Previous iteration...",
    template_name="Momentum",
    json_mode=True
)

# 存取屬性
print(record.iteration_num)        # 0
print(record.sharpe_ratio)          # 1.5
print(record.classification_level)  # LEVEL_3
```

---

### ChampionRecord

Champion記錄數據類。

```python
@dataclass
class ChampionRecord:
    """Champion策略記錄"""

    iteration_num: int                # Champion迭代編號
    strategy_code: str                # 策略程式碼
    params: Dict[str, Any]            # 參數
    metrics: Dict[str, float]         # 指標字典
    generation_method: str            # 生成方法
    timestamp: str                    # 時間戳
```

**範例**:

```python
champion = loop.champion

if champion:
    print(f"Iteration: {champion.iteration_num}")
    print(f"Sharpe: {champion.metrics.get('sharpe_ratio')}")
    print(f"Method: {champion.generation_method}")
    print(f"Params: {champion.params}")
```

---

### StrategyMetrics

策略指標數據類。

```python
@dataclass
class StrategyMetrics:
    """策略性能指標"""

    sharpe_ratio: float              # Sharpe Ratio
    total_return: float              # 總回報
    max_drawdown: float              # 最大回撤
    win_rate: Optional[float]        # 勝率
    annual_return: Optional[float]   # 年化回報
```

**範例**:

```python
metrics = StrategyMetrics(
    sharpe_ratio=1.5,
    total_return=0.85,
    max_drawdown=-0.15,
    win_rate=0.6,
    annual_return=0.25
)

print(f"Sharpe: {metrics.sharpe_ratio}")
print(f"Return: {metrics.total_return * 100}%")
print(f"Drawdown: {metrics.max_drawdown * 100}%")
```

---

## 異常類別

### ConfigurationError

配置錯誤異常。

```python
class ConfigurationError(Exception):
    """配置參數無效時引發"""
    pass
```

**引發情況**:
- `use_json_mode=True`但`template_mode=False`
- `template_mode=True`但`template_name`未指定
- `max_iterations`超出1-1000範圍
- 必須的檔案路徑未指定

**範例**:

```python
from src.learning.unified_config import UnifiedConfig, ConfigurationError

try:
    config = UnifiedConfig(
        use_json_mode=True,
        template_mode=False  # 錯誤！
    )
    config.validate()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    # Configuration error: use_json_mode=True requires template_mode=True
```

---

## 工具函數

### load_config(config_file: str) -> UnifiedConfig

從YAML檔案載入配置。

**參數**:
- `config_file`: YAML檔案路徑

**返回值**: `UnifiedConfig`實例

**範例**:

```python
from src.learning.unified_loop import load_config

config = load_config("config/my_config.yaml")
loop = UnifiedLoop(**config.to_dict())
```

---

### create_default_config() -> UnifiedConfig

創建預設配置。

**返回值**: 預設`UnifiedConfig`實例

**範例**:

```python
from src.learning.unified_loop import create_default_config

config = create_default_config()
# 修改部分參數
config.max_iterations = 100
config.template_mode = True

loop = UnifiedLoop(**config.to_dict())
```

---

## 使用範例

### 範例1: 基本使用

```python
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(
    max_iterations=10,
    template_mode=True,
    template_name="Momentum"
)

result = loop.run()
print(f"Completed: {result['iterations_completed']}")
```

### 範例2: 完整配置

```python
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(
    # Loop
    max_iterations=100,
    continue_on_error=False,

    # LLM
    llm_model="gemini-2.5-flash",
    llm_temperature=0.7,

    # Template
    template_mode=True,
    template_name="Momentum",
    use_json_mode=True,

    # Learning
    enable_learning=True,
    history_window=10,

    # Monitoring
    enable_monitoring=True,

    # Docker
    use_docker=False,

    # Files
    history_file="artifacts/data/iterations.jsonl",
    champion_file="artifacts/data/champion.json"
)

result = loop.run()
```

### 範例3: 存取歷史和Champion

```python
loop = UnifiedLoop(max_iterations=10)
result = loop.run()

# Champion
champion = loop.champion
if champion:
    print(f"Champion Sharpe: {champion.metrics.get('sharpe_ratio')}")

# 歷史
history = loop.history
recent = history.load_recent(N=5)
for record in recent:
    print(f"Iteration {record.iteration_num}: {record.classification_level}")
```

### 範例4: 錯誤處理

```python
from src.learning.unified_loop import UnifiedLoop
import logging

logger = logging.getLogger(__name__)

try:
    loop = UnifiedLoop(
        max_iterations=100,
        template_mode=True
    )
    result = loop.run()
    logger.info(f"Success: {result['iterations_completed']} iterations")

except KeyboardInterrupt:
    logger.warning("Interrupted by user")

except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
```

---

## 版本資訊

### v1.0 (2025-11-23)

**新增**:
- UnifiedLoop類別（Facade Pattern）
- UnifiedConfig類別
- TemplateIterationExecutor類別
- 監控系統整合（MetricsCollector, ResourceMonitor, DiversityMonitor）
- Docker Sandbox整合（DockerExecutor）
- JSON Parameter Output支援
- Learning Feedback系統

**相容性**:
- Python 3.10+
- 向後相容AutonomousLoop API（champion, history屬性）
- 100%配置參數相容

---

**文檔版本**: v1.0
**最後更新**: 2025-11-23
**審核人員**: Claude (Sonnet 4.5)
**狀態**: ✅ 完成

