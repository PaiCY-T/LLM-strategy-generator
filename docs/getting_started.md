# UnifiedLoop快速入門指南

**版本**: v1.0
**更新日期**: 2025-11-23
**目標讀者**: UnifiedLoop新使用者

---

## 📋 目錄

1. [5分鐘快速開始](#5分鐘快速開始)
2. [安裝和環境設置](#安裝和環境設置)
3. [基本概念](#基本概念)
4. [第一個UnifiedLoop程式](#第一個unifiedloop程式)
5. [Template Mode教學](#template-mode教學)
6. [JSON Parameter Output教學](#json-parameter-output教學)
7. [Learning Feedback教學](#learning-feedback教學)
8. [監控系統教學](#監控系統教學)
9. [Docker Sandbox教學](#docker-sandbox教學)
10. [最佳實踐](#最佳實踐)
11. [常見錯誤和解決方案](#常見錯誤和解決方案)
12. [下一步學習](#下一步學習)

---

## 5分鐘快速開始

### 最簡單的範例

```python
#!/usr/bin/env python3
"""最簡單的UnifiedLoop範例 - 5分鐘快速開始"""

import os
import sys

# 設置項目路徑
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.unified_loop import UnifiedLoop

# 確保API token已設置
if 'FINLAB_API_TOKEN' not in os.environ:
    print("請設置 FINLAB_API_TOKEN 環境變數")
    sys.exit(1)

# 創建UnifiedLoop實例
loop = UnifiedLoop(
    max_iterations=10,           # 運行10次迭代
    template_mode=True,          # 使用Template Mode
    template_name="Momentum"     # 使用Momentum模板
)

# 執行
print("開始執行UnifiedLoop...")
result = loop.run()

# 顯示結果
print(f"\n✓ 完成 {result['iterations_completed']} 次迭代")
if result['champion']:
    sharpe = result['champion'].metrics.get('sharpe_ratio', 'N/A')
    print(f"✓ Champion Sharpe Ratio: {sharpe}")
```

**運行**:
```bash
python quick_start.py
```

**預期輸出**:
```
開始執行UnifiedLoop...
[進度日誌...]
✓ 完成 10 次迭代
✓ Champion Sharpe Ratio: 1.2345
```

---

## 安裝和環境設置

### 系統需求

| 需求 | 版本 | 說明 |
|------|------|------|
| Python | 3.10+ | 必須 |
| pip | 最新 | 套件管理器 |
| Git | 2.0+ | 版本控制 |
| Docker | 20.0+ | 選用（Docker Sandbox） |

### 安裝步驟

#### 1. 克隆專案

```bash
git clone https://github.com/your-repo/LLM-strategy-generator.git
cd LLM-strategy-generator
```

#### 2. 安裝依賴套件

```bash
# 安裝所有依賴
pip install -r requirements.txt

# 確認安裝
python -c "from src.learning.unified_loop import UnifiedLoop; print('✓ UnifiedLoop installed')"
```

#### 3. 設置環境變數

```bash
# Finlab API Token（必須）
export FINLAB_API_TOKEN='your-finlab-api-token'

# Google Gemini API Key（如使用Gemini）
export GOOGLE_API_KEY='your-google-api-key'

# 或OpenAI API Key（如使用GPT）
export OPENAI_API_KEY='your-openai-api-key'
```

**永久設置**（Linux/macOS）:
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export FINLAB_API_TOKEN="your-token"' >> ~/.bashrc
echo 'export GOOGLE_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

**Windows**:
```powershell
# PowerShell
$env:FINLAB_API_TOKEN="your-token"
$env:GOOGLE_API_KEY="your-key"

# 永久設置
[System.Environment]::SetEnvironmentVariable('FINLAB_API_TOKEN', 'your-token', 'User')
```

#### 4. 驗證安裝

```bash
# 運行測試腳本
python run_5iteration_template_smoke_test.py

# 預期：5次迭代成功完成
```

---

## 基本概念

### UnifiedLoop是什麼？

**UnifiedLoop**是一個統一的學習循環框架，整合了：
- **LearningLoop**: 核心迭代邏輯
- **Template Mode**: 基於模板的策略生成
- **JSON Parameter Output**: Pydantic驗證的參數輸出
- **Learning Feedback**: 從歷史學習的反饋系統
- **Monitoring**: 性能和資源監控
- **Docker Sandbox**: 安全隔離執行

### 架構圖

```
┌─────────────────────────────────────┐
│         UnifiedLoop (Facade)        │
│                                     │
│  統一入口，簡化API                   │
└──────────────┬──────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌────────────┐      ┌──────────────┐
│ Learning   │      │  Monitoring  │
│ Loop       │      │  Systems     │
│            │      │              │
│ • Iteration│      │ • Metrics    │
│ • Template │      │ • Resource   │
│ • Feedback │      │ • Diversity  │
└────────────┘      └──────────────┘
```

### 核心組件

| 組件 | 職責 | 何時使用 |
|------|------|---------|
| **UnifiedLoop** | Facade入口，統一API | 總是使用 |
| **LearningLoop** | 迭代邏輯、Champion管理 | 自動（內部） |
| **TemplateIterationExecutor** | Template Mode執行器 | `template_mode=True` |
| **MetricsCollector** | 指標收集 | `enable_monitoring=True` |
| **DockerExecutor** | Docker隔離執行 | `use_docker=True` |

### 設計模式

**1. Facade Pattern**:
- UnifiedLoop作為統一外觀
- 隱藏內部複雜性
- 提供簡單API

**2. Strategy Pattern**:
- TemplateIterationExecutor vs StandardIterationExecutor
- 運行時選擇執行策略
- `template_mode`控制選擇

**3. Dependency Injection**:
- 組件通過構造函數注入
- 易於測試和替換
- 清晰的依賴關係

---

## 第一個UnifiedLoop程式

### Step 1: 導入UnifiedLoop

```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.unified_loop import UnifiedLoop
```

### Step 2: 創建UnifiedLoop實例

```python
loop = UnifiedLoop(
    # === 基本配置 ===
    max_iterations=10,        # 迭代次數

    # === Template Mode ===
    template_mode=True,       # 啟用Template Mode
    template_name="Momentum", # 使用Momentum模板

    # === LLM配置 ===
    llm_model="gemini-2.5-flash",  # LLM模型
    llm_temperature=0.7,           # 溫度參數

    # === 檔案路徑 ===
    history_file="artifacts/data/iterations.jsonl",
    champion_file="artifacts/data/champion.json"
)
```

### Step 3: 執行UnifiedLoop

```python
# 執行
result = loop.run()

# 結果是字典
print(f"Iterations completed: {result['iterations_completed']}")
print(f"Champion exists: {result['champion'] is not None}")
print(f"Interrupted: {result.get('interrupted', False)}")
```

### Step 4: 存取結果

```python
# 方式1: 從result字典
champion = result['champion']
if champion:
    print(f"Champion Sharpe: {champion.metrics.get('sharpe_ratio')}")

# 方式2: 從loop屬性（向後相容API）
champion = loop.champion
history = loop.history

# 查詢歷史記錄
recent = history.load_recent(N=5)
for record in recent:
    print(f"Iteration {record.iteration_num}: {record.classification_level}")
```

### 完整範例

```python
#!/usr/bin/env python3
"""完整的UnifiedLoop範例"""

import sys
import os
import logging

# 設置項目路徑
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.unified_loop import UnifiedLoop

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    # 檢查環境變數
    if 'FINLAB_API_TOKEN' not in os.environ:
        print("❌ 請設置 FINLAB_API_TOKEN 環境變數")
        return False

    print("\n" + "="*60)
    print("UnifiedLoop 完整範例")
    print("="*60)

    # 創建UnifiedLoop
    loop = UnifiedLoop(
        # Loop控制
        max_iterations=10,
        continue_on_error=False,

        # Template Mode
        template_mode=True,
        template_name="Momentum",

        # LLM配置
        llm_model="gemini-2.5-flash",
        llm_temperature=0.7,

        # 學習和監控
        enable_learning=True,
        enable_monitoring=True,

        # 檔案路徑
        history_file="artifacts/data/iterations.jsonl",
        champion_file="artifacts/data/champion.json",
        log_dir="logs"
    )

    # 執行
    print("\n開始執行...")
    result = loop.run()

    # 顯示結果
    print("\n" + "="*60)
    print("執行完成")
    print("="*60)
    print(f"✓ 完成迭代數: {result['iterations_completed']}")

    if result['champion']:
        sharpe = result['champion'].metrics.get('sharpe_ratio', 'N/A')
        print(f"✓ Champion Sharpe: {sharpe}")
    else:
        print("⚠️  未找到Champion")

    if result.get('interrupted'):
        print("⚠️  執行被中斷")

    # 查詢歷史
    history = loop.history
    recent = history.load_recent(N=3)

    print(f"\n最近3次迭代:")
    for record in recent:
        sharpe = record.metrics.sharpe_ratio if record.metrics else 'N/A'
        print(f"  - Iteration {record.iteration_num}: "
              f"{record.classification_level}, Sharpe={sharpe}")

    print("\n✅ 範例執行成功！")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
```

---

## Template Mode教學

### 什麼是Template Mode？

**Template Mode**使用預定義的策略模板來生成參數，而不是讓LLM自由生成程式碼。

**優勢**:
- ✅ 更穩定的輸出
- ✅ 更快的生成速度
- ✅ 更容易驗證和測試
- ✅ 參數範圍可控

### 可用模板

| 模板名稱 | 策略類型 | 參數範例 |
|---------|---------|---------|
| **Momentum** | 動量策略 | `window`, `threshold` |
| **MeanReversion** | 均值回歸 | `lookback`, `entry_std`, `exit_std` |
| **Factor** | 因子策略 | `factor_name`, `quantile`, `rebalance` |
| **Breakout** | 突破策略 | `period`, `multiplier` |

### 使用Template Mode

```python
loop = UnifiedLoop(
    max_iterations=10,

    # 啟用Template Mode
    template_mode=True,
    template_name="Momentum",  # 選擇模板

    # LLM只生成參數，不生成程式碼
    llm_model="gemini-2.5-flash"
)

result = loop.run()
```

### Momentum模板範例

**LLM生成的參數**:
```json
{
  "window": 20,
  "threshold": 0.02,
  "stop_loss": 0.05
}
```

**模板生成的程式碼**:
```python
import pandas as pd

# 計算動量
close = data.get("price:收盤價")
momentum = close.pct_change(20)  # window=20

# 生成信號
position = (momentum > 0.02).astype(int)  # threshold=0.02

# 執行回測
report = sim(
    position,
    stop_loss=0.05,  # stop_loss=0.05
    resample="M"
)
```

### Template Mode工作流程

```
1. LLM生成參數
   ↓
   {"window": 20, "threshold": 0.02}

2. 模板生成程式碼
   ↓
   momentum = close.pct_change(20)
   position = (momentum > 0.02).astype(int)

3. 執行回測
   ↓
   Sharpe Ratio: 1.23

4. 更新Champion（如果更好）
```

---

## JSON Parameter Output教學

### 什麼是JSON Parameter Output？

**JSON Parameter Output**使用Pydantic模型驗證LLM生成的參數。

**優勢**:
- ✅ 類型安全（int, float, str驗證）
- ✅ 範圍檢查（min, max約束）
- ✅ 必填欄位驗證
- ✅ 自動錯誤訊息

### 啟用JSON Mode

```python
loop = UnifiedLoop(
    max_iterations=10,

    # JSON Mode需要Template Mode
    template_mode=True,
    use_json_mode=True,  # 啟用JSON模式

    template_name="Momentum"
)
```

### Pydantic模型範例

```python
from pydantic import BaseModel, Field

class MomentumParams(BaseModel):
    """Momentum策略參數"""

    window: int = Field(
        default=20,
        ge=5,      # >= 5
        le=200,    # <= 200
        description="動量計算窗口"
    )

    threshold: float = Field(
        default=0.02,
        ge=0.0,    # >= 0.0
        le=0.5,    # <= 0.5
        description="進場閾值"
    )

    stop_loss: float = Field(
        default=0.05,
        ge=0.01,   # >= 0.01
        le=0.2,    # <= 0.2
        description="停損比例"
    )
```

### LLM輸出驗證

**有效輸出**:
```json
{
  "window": 20,
  "threshold": 0.02,
  "stop_loss": 0.05
}
```
✅ 驗證通過

**無效輸出**:
```json
{
  "window": 300,      // 超過le=200
  "threshold": "high",  // 類型錯誤（應為float）
  "stop_loss": -0.1     // 小於ge=0.01
}
```
❌ 驗證失敗，顯示詳細錯誤

### 錯誤處理

```python
# JSON Mode會自動處理驗證錯誤
loop = UnifiedLoop(
    template_mode=True,
    use_json_mode=True,
    template_name="Momentum"
)

result = loop.run()

# 查看驗證失敗的迭代
history = loop.history
for record in history.load_recent(N=10):
    if record.classification_level == "LEVEL_0":
        # 可能是參數驗證失敗
        print(f"Iteration {record.iteration_num}: {record.execution_result.get('error')}")
```

---

## Learning Feedback教學

### 什麼是Learning Feedback？

**Learning Feedback**從歷史迭代中學習，生成反饋指導下一次迭代。

**工作原理**:
```
迭代N結果 → 分析成功/失敗 → 生成反饋 → 迭代N+1參數生成
```

### 啟用Learning Feedback

```python
loop = UnifiedLoop(
    max_iterations=100,

    # 啟用學習反饋
    enable_learning=True,
    history_window=10,  # 使用最近10次迭代

    template_mode=True,
    template_name="Momentum"
)
```

### Feedback範例

**情境**: 上次迭代失敗（Sharpe < 0）

**生成的Feedback**:
```
上次迭代使用 window=5, threshold=0.1 導致Sharpe=-0.5（虧損）。
問題分析：
1. window=5 太短，噪音太大
2. threshold=0.1 太高，錯過許多機會

建議調整：
1. 增加window到15-30範圍
2. 降低threshold到0.02-0.05範圍
3. 考慮添加stop_loss保護
```

**下次LLM生成**:
```json
{
  "window": 25,      // ✓ 增加window
  "threshold": 0.03,  // ✓ 降低threshold
  "stop_loss": 0.05   // ✓ 添加stop_loss
}
```

### Feedback工作流程

```
1. 收集歷史（最近N次）
   ↓
   [Iter1: Sharpe=0.5, Iter2: Sharpe=-0.2, ...]

2. 分析模式
   ↓
   - 成功策略的共同特徵
   - 失敗策略的問題

3. 生成反饋
   ↓
   "window=20-30表現較好，threshold<0.05更穩定"

4. LLM使用反饋生成下次參數
   ↓
   {"window": 25, "threshold": 0.03}
```

### 查看Feedback效果

```python
# 執行loop
result = loop.run()

# 查看使用feedback的迭代
history = loop.history
for record in history.load_recent(N=10):
    if record.feedback_used:
        print(f"Iteration {record.iteration_num}:")
        print(f"  Feedback: {record.feedback_used[:200]}...")
        print(f"  Sharpe: {record.metrics.sharpe_ratio if record.metrics else 'N/A'}")
```

---

## 監控系統教學

### 什麼是監控系統？

UnifiedLoop整合3個監控組件：
1. **MetricsCollector**: Prometheus兼容指標
2. **ResourceMonitor**: CPU/記憶體/磁碟監控（背景執行緒）
3. **DiversityMonitor**: 策略多樣性追蹤

### 啟用監控

```python
loop = UnifiedLoop(
    max_iterations=100,

    # 啟用監控（預設True）
    enable_monitoring=True,

    template_mode=True,
    template_name="Momentum"
)

result = loop.run()

# 監控會在run()結束時自動關閉
```

### 監控指標

#### 1. MetricsCollector（學習指標）

| 指標 | 說明 | 單位 |
|------|------|------|
| `iteration_success_rate` | 迭代成功率 | % |
| `champion_update_count` | Champion更新次數 | 次 |
| `average_sharpe_ratio` | 平均Sharpe | - |
| `strategy_diversity` | 策略多樣性 | - |

#### 2. ResourceMonitor（系統資源）

| 指標 | 說明 | 單位 |
|------|------|------|
| `cpu_percent` | CPU使用率 | % |
| `memory_mb` | 記憶體使用 | MB |
| `disk_usage_percent` | 磁碟使用率 | % |

**背景執行緒**:
- 每5秒採樣一次
- <1%效能開銷
- 自動啟動/停止

#### 3. DiversityMonitor（多樣性）

| 指標 | 說明 | 閾值 |
|------|------|------|
| `diversity_score` | 多樣性分數 | 0-1 |
| `unique_templates` | 不同模板數 | - |
| `collapse_detected` | 崩潰檢測 | threshold=0.1 |

### 監控配置

```python
loop = UnifiedLoop(
    max_iterations=100,
    enable_monitoring=True,

    # 監控配置（自動）
    # - MetricsCollector: history_window=100
    # - ResourceMonitor: interval=5s
    # - DiversityMonitor: collapse_threshold=0.1
)
```

### 禁用監控（性能優化）

```python
loop = UnifiedLoop(
    max_iterations=100,

    # 禁用監控（微幅性能提升）
    enable_monitoring=False
)
```

### 監控開銷

| 組件 | CPU開銷 | 記憶體開銷 | 說明 |
|------|---------|-----------|------|
| MetricsCollector | <0.1% | ~10MB | 指標收集 |
| ResourceMonitor | <0.5% | ~5MB | 背景執行緒 |
| DiversityMonitor | <0.1% | ~5MB | 多樣性計算 |
| **總計** | **<1%** | **~20MB** | 可忽略 |

---

## Docker Sandbox教學

### 什麼是Docker Sandbox？

**Docker Sandbox**在隔離的Docker容器中執行策略，提供：
- ✅ 安全隔離
- ✅ 資源限制
- ✅ 網路隔離
- ✅ 程式碼驗證

### 前置需求

```bash
# 1. 安裝Docker
# Linux: sudo apt install docker.io
# macOS: brew install docker
# Windows: Docker Desktop

# 2. 啟動Docker daemon
sudo systemctl start docker  # Linux
# 或 open -a Docker  # macOS

# 3. 建構Docker映像
docker build -t finlab-sandbox:latest -f Dockerfile.sandbox .

# 4. 安裝Docker SDK
pip install docker
```

### 啟用Docker Sandbox

```python
loop = UnifiedLoop(
    max_iterations=10,

    # 啟用Docker沙盒
    use_docker=True,

    template_mode=True,
    template_name="Momentum"
)

result = loop.run()
```

### Docker配置

**自動配置**（從`config/docker_config.yaml`）:
```yaml
docker:
  enabled: true
  image: finlab-sandbox:latest

  # 資源限制
  memory_limit: "2g"      # 2GB記憶體
  cpu_limit: 0.5          # 0.5個CPU核心
  timeout_seconds: 600    # 10分鐘超時

  # 安全設置
  network_mode: "none"    # 網路隔離
  read_only: true         # 唯讀檔案系統
  tmpfs:
    path: "/tmp"
    size: "1g"
```

### Docker安全特性

| 特性 | 說明 | 效果 |
|------|------|------|
| **AST驗證** | 程式碼執行前檢查 | 阻擋危險操作 |
| **容器隔離** | 獨立容器執行 | 保護主機系統 |
| **資源限制** | CPU/記憶體上限 | 防止資源耗盡 |
| **網路隔離** | 無網路存取 | 防止數據洩漏 |
| **唯讀FS** | 檔案系統唯讀 | 防止惡意寫入 |
| **Seccomp** | 系統調用過濾 | 阻擋危險syscall |

### 性能影響

| 模式 | 每次迭代時間 | 說明 |
|------|-------------|------|
| **無Docker** | ~30-60秒 | 直接執行 |
| **Docker** | ~35-65秒 | +3-5秒容器啟動 |
| **增加** | +10-15% | 可接受的安全成本 |

### 錯誤處理

```python
loop = UnifiedLoop(
    max_iterations=10,
    use_docker=True
)

result = loop.run()

# 檢查Docker執行結果
history = loop.history
for record in history.load_recent(N=5):
    exec_result = record.execution_result

    if exec_result.get('docker_executed'):
        # Docker執行的迭代
        validated = exec_result.get('validated', False)
        print(f"Iteration {record.iteration_num}:")
        print(f"  Docker: Yes, Validated: {validated}")

        if not exec_result.get('status') == 'success':
            # Docker執行失敗
            error = exec_result.get('error', 'Unknown')
            print(f"  Error: {error}")
```

### 禁用Docker（測試/開發）

```python
loop = UnifiedLoop(
    max_iterations=10,

    # 禁用Docker（更快，但無安全保護）
    use_docker=False
)
```

---

## 最佳實踐

### 1. 配置組織

**推薦**: 使用配置字典

```python
# config.py
UNIFIED_LOOP_CONFIG = {
    # Loop控制
    "max_iterations": 100,
    "continue_on_error": False,

    # Template Mode
    "template_mode": True,
    "template_name": "Momentum",
    "use_json_mode": True,

    # LLM
    "llm_model": "gemini-2.5-flash",
    "llm_temperature": 0.7,

    # Learning & Monitoring
    "enable_learning": True,
    "enable_monitoring": True,
    "history_window": 10,

    # Docker
    "use_docker": False,  # 測試時禁用

    # 檔案
    "history_file": "artifacts/data/iterations.jsonl",
    "champion_file": "artifacts/data/champion.json",
    "log_dir": "logs",
    "log_level": "INFO"
}

# main.py
from config import UNIFIED_LOOP_CONFIG
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(**UNIFIED_LOOP_CONFIG)
result = loop.run()
```

### 2. 錯誤處理

**推薦**: 使用try-except

```python
import logging

logger = logging.getLogger(__name__)

try:
    loop = UnifiedLoop(**config)
    result = loop.run()

    logger.info(f"✓ Success: {result['iterations_completed']} iterations")

except KeyboardInterrupt:
    logger.warning("⚠️  Interrupted by user (Ctrl+C)")
    # UnifiedLoop會自動保存checkpoint

except Exception as e:
    logger.error(f"❌ Failed: {e}", exc_info=True)
    # 檢查日誌檔案進行診斷
```

### 3. 日誌配置

**推薦**: 設置適當日誌級別

```python
import logging

# 開發環境：DEBUG
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/debug.log'),
        logging.StreamHandler()
    ]
)

# 生產環境：INFO
loop = UnifiedLoop(
    log_level="INFO",      # WARNING for less verbose
    log_to_file=True,
    log_to_console=False   # 禁用控制台輸出
)
```

### 4. 性能優化

**開發環境**（快速迭代）:
```python
loop = UnifiedLoop(
    max_iterations=10,          # 少量迭代
    enable_monitoring=False,    # 禁用監控
    use_docker=False,           # 禁用Docker
    log_level="WARNING"         # 減少日誌
)
```

**生產環境**（完整功能）:
```python
loop = UnifiedLoop(
    max_iterations=100,         # 完整迭代
    enable_monitoring=True,     # 啟用監控
    use_docker=True,            # 啟用Docker（安全）
    log_level="INFO"            # 詳細日誌
)
```

### 5. 檔案組織

**推薦結構**:
```
project/
├── config/
│   ├── docker_config.yaml
│   └── learning_system.yaml
├── artifacts/
│   └── data/
│       ├── iterations.jsonl    # 歷史記錄
│       └── champion.json        # Champion
├── logs/
│   └── unified_loop_*.log      # 日誌檔案
├── scripts/
│   ├── run_10iter_test.py
│   ├── run_100iter_test.py
│   └── analyze_results.py
└── my_loop.py                  # 主程式
```

### 6. 版本控制

**不要提交**:
- `artifacts/data/*.jsonl` (歷史記錄)
- `logs/*.log` (日誌檔案)
- `.env` (環境變數)

**.gitignore**:
```gitignore
# UnifiedLoop artifacts
artifacts/data/*.jsonl
artifacts/data/*.json
logs/*.log

# Environment
.env
*.env

# Python
__pycache__/
*.pyc
```

### 7. 測試策略

**分層測試**:
```python
# 1. Smoke Test (5-10圈，5分鐘)
loop = UnifiedLoop(max_iterations=5)

# 2. Integration Test (30-50圈，30分鐘)
loop = UnifiedLoop(max_iterations=30)

# 3. Full Test (100圈，2-3小時)
loop = UnifiedLoop(max_iterations=100)

# 4. Stability Test (200圈，8-12小時)
python run_200iteration_stability_test.py
```

---

## 常見錯誤和解決方案

### 錯誤1: ImportError: No module named 'src.learning.unified_loop'

**原因**: Python路徑未設置

**解決**:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))  # 添加項目根目錄

from src.learning.unified_loop import UnifiedLoop
```

### 錯誤2: ValueError: FINLAB_API_TOKEN not set

**原因**: 環境變數未設置

**解決**:
```bash
# 設置環境變數
export FINLAB_API_TOKEN='your-token'

# 或在程式中設置（不推薦）
import os
os.environ['FINLAB_API_TOKEN'] = 'your-token'
```

### 錯誤3: ConfigurationError: use_json_mode=True requires template_mode=True

**原因**: JSON模式需要Template Mode

**解決**:
```python
loop = UnifiedLoop(
    template_mode=True,    # 必須啟用
    use_json_mode=True,
    template_name="Momentum"  # 必須指定
)
```

### 錯誤4: Docker execution failed: Docker daemon not running

**原因**: Docker未啟動

**解決**:
```bash
# 啟動Docker
sudo systemctl start docker  # Linux
open -a Docker              # macOS

# 或禁用Docker
loop = UnifiedLoop(use_docker=False)
```

### 錯誤5: 性能很慢（每次迭代>5分鐘）

**診斷**:
```python
# 1. 檢查是否啟用Docker（+3-5秒）
print(f"Docker enabled: {config.get('use_docker', False)}")

# 2. 檢查日誌級別
print(f"Log level: {config.get('log_level', 'INFO')}")

# 3. 檢查監控
print(f"Monitoring: {config.get('enable_monitoring', True)}")
```

**優化**:
```python
loop = UnifiedLoop(
    use_docker=False,        # 禁用Docker
    enable_monitoring=False, # 禁用監控
    log_level="WARNING"      # 減少日誌
)
```

---

## 下一步學習

### 進階主題

1. **自定義Template**
   - 建立自己的策略模板
   - 定義參數Pydantic模型
   - 實作`generate_code()`方法

2. **Checkpoint/Resume**
   - 使用checkpoint保存進度
   - 從checkpoint恢復執行
   - 長期測試最佳實踐

3. **統計分析**
   - 使用UnifiedTestHarness分析結果
   - Cohen's d效果量計算
   - 統計顯著性測試

4. **性能調優**
   - Prometheus監控集成
   - 資源使用優化
   - 平行執行策略

### 推薦閱讀

| 文檔 | 主題 | 難度 |
|------|------|------|
| [Migration Guide](./migration_guide.md) | 從AutonomousLoop遷移 | 中 |
| [API Reference](./api/unified_loop.md) | 完整API文檔 | 中 |
| [Architecture](./architecture.md) | 架構設計 | 高 |
| [Troubleshooting](./troubleshooting.md) | 故障排除 | 中 |

### 範例專案

```bash
# 1. 5圈快速測試
python run_5iteration_template_smoke_test.py

# 2. 100圈完整測試
python run_100iteration_test.py --loop-type unified --template-mode

# 3. 200圈穩定性測試
python run_200iteration_stability_test.py

# 4. 自定義腳本
cp examples/custom_loop.py my_experiment.py
python my_experiment.py
```

### 社群資源

- **GitHub Issues**: 報告bug和功能請求
- **Discussions**: 問答和討論
- **Wiki**: 社群貢獻的教學
- **Examples**: 範例程式碼庫

---

## 附錄

### A. 完整配置參數列表

<details>
<summary>點擊展開完整參數</summary>

```python
loop = UnifiedLoop(
    # === Loop控制 ===
    max_iterations=100,          # 最大迭代次數
    continue_on_error=False,     # 錯誤時是否繼續

    # === LLM配置 ===
    llm_model="gemini-2.5-flash",  # LLM模型名稱
    api_key=None,                  # API密鑰（或環境變數）
    llm_timeout=60,                # LLM超時（秒）
    llm_temperature=0.7,           # 溫度參數
    llm_max_tokens=4000,           # 最大token數

    # === Template Mode ===
    template_mode=False,           # 啟用Template Mode
    template_name="Momentum",      # Template名稱

    # === JSON Parameter Output ===
    use_json_mode=False,           # 啟用JSON模式

    # === Learning Feedback ===
    enable_learning=True,          # 啟用學習反饋
    history_window=10,             # 歷史窗口大小

    # === 監控系統 ===
    enable_monitoring=True,        # 啟用監控

    # === Docker Sandbox ===
    use_docker=False,              # 啟用Docker沙盒

    # === 回測配置 ===
    timeout_seconds=420,           # 回測超時（秒）
    start_date="2018-01-01",       # 回測開始日期
    end_date="2024-12-31",         # 回測結束日期
    fee_ratio=0.001425,            # 交易費用比例
    tax_ratio=0.003,               # 交易稅率
    resample="M",                  # 重新平衡頻率

    # === 檔案路徑 ===
    history_file="artifacts/data/iterations.jsonl",  # 歷史記錄
    champion_file="artifacts/data/champion.json",    # Champion檔案
    log_dir="logs",                                  # 日誌目錄
    config_file="config/learning_system.yaml",       # 配置檔案

    # === 日誌 ===
    log_level="INFO",              # 日誌級別
    log_to_file=True,              # 寫入檔案
    log_to_console=True            # 控制台輸出
)
```

</details>

### B. 環境變數

| 變數名稱 | 必須 | 說明 |
|---------|------|------|
| `FINLAB_API_TOKEN` | ✅ | Finlab API Token |
| `GOOGLE_API_KEY` | ⚪ | Google Gemini API（如使用Gemini） |
| `OPENAI_API_KEY` | ⚪ | OpenAI API（如使用GPT） |
| `ANTHROPIC_API_KEY` | ⚪ | Anthropic API（如使用Claude） |

### C. 常用指令

```bash
# 測試環境
python -c "from src.learning.unified_loop import UnifiedLoop; print('✓')"

# 5圈smoke test
python run_5iteration_template_smoke_test.py

# 100圈完整測試
python run_100iteration_test.py --loop-type unified

# 檢查日誌
tail -f logs/unified_loop_*.log

# 分析結果
python scripts/analyze_iterations.py artifacts/data/iterations.jsonl
```

---

**文檔版本**: v1.0
**最後更新**: 2025-11-23
**審核人員**: Claude (Sonnet 4.5)
**狀態**: ✅ 完成

**祝您使用UnifiedLoop順利！** 🚀
