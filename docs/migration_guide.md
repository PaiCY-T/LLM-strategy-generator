# UnifiedLoop遷移指南

**版本**: v1.0
**更新日期**: 2025-11-23
**目標讀者**: 從AutonomousLoop遷移到UnifiedLoop的開發者

---

## 📋 目錄

1. [為什麼要遷移](#為什麼要遷移)
2. [主要差異](#主要差異)
3. [快速遷移步驟](#快速遷移步驟)
4. [配置對照表](#配置對照表)
5. [逐步遷移指南](#逐步遷移指南)
6. [測試腳本遷移](#測試腳本遷移)
7. [常見問題FAQ](#常見問題faq)
8. [疑難排解](#疑難排解)

---

## 為什麼要遷移

### UnifiedLoop的優勢

#### 1. **統一架構** 🏗️
- 整合AutonomousLoop和LearningLoop的最佳特性
- 單一入口點，簡化API
- Facade設計模式，降低複雜度

#### 2. **新功能支援** ✨
| 功能 | AutonomousLoop | UnifiedLoop |
|------|---------------|-------------|
| Template Mode | ✅ | ✅ |
| JSON Parameter Output | ❌ | ✅ |
| Learning Feedback | ✅ | ✅ |
| Monitoring系統 | ❌ | ✅ |
| Docker Sandbox | ❌ | ✅ |
| Checkpoint/Resume | 基礎 | 增強 |

#### 3. **更好的可維護性** 🔧
- 統一配置系統（UnifiedConfig）
- 清晰的組件職責
- 更完整的錯誤處理
- 更好的日誌系統

#### 4. **性能優化** ⚡
- 監控系統(<1%開銷)
- Docker隔離執行(安全性提升)
- 資源使用優化

#### 5. **未來發展** 🚀
- AutonomousLoop將逐步淘汰
- UnifiedLoop是未來開發重點
- 新功能只在UnifiedLoop中實作

---

## 主要差異

### 架構對比

```
AutonomousLoop架構:
    AutonomousLoop (單體)
    └─→ 直接管理所有組件

UnifiedLoop架構 (Facade Pattern):
    UnifiedLoop (外觀)
    ├─→ LearningLoop (核心邏輯)
    │   ├─→ IterationExecutor (標準模式)
    │   └─→ TemplateIterationExecutor (Template Mode)
    ├─→ MetricsCollector (監控)
    ├─→ ResourceMonitor (資源監控)
    └─→ DiversityMonitor (多樣性監控)
```

### 關鍵設計模式

**UnifiedLoop使用的設計模式**:
1. **Facade Pattern**: UnifiedLoop作為統一入口
2. **Strategy Pattern**: TemplateIterationExecutor vs StandardIterationExecutor
3. **Dependency Injection**: 組件通過構造函數注入

---

## 快速遷移步驟

### 5分鐘快速遷移

**步驟1**: 更新導入語句

```python
# Before (AutonomousLoop)
from artifacts.working.modules.autonomous_loop import AutonomousLoop

# After (UnifiedLoop)
from src.learning.unified_loop import UnifiedLoop
```

**步驟2**: 更新配置

```python
# Before (AutonomousLoop)
loop = AutonomousLoop(
    max_iterations=100,
    llm_model="gemini-2.5-flash",
    template_mode=True,
    template_name="Momentum",
    innovation_mode=True,
    history_file="iterations.jsonl",
    champion_file="champion.json"
)

# After (UnifiedLoop)
loop = UnifiedLoop(
    max_iterations=100,
    llm_model="gemini-2.5-flash",
    template_mode=True,
    template_name="Momentum",
    use_json_mode=True,          # 新功能！
    enable_learning=True,         # 對應innovation_mode
    enable_monitoring=True,       # 新功能！
    use_docker=False,             # 新功能！
    history_file="iterations.jsonl",
    champion_file="champion.json"
)
```

**步驟3**: 執行測試

```python
# API完全相容
result = loop.run()

# 結果結構相同
print(f"Iterations: {result['iterations_completed']}")
print(f"Champion: {result['champion']}")
```

---

## 配置對照表

### 完整參數映射

| AutonomousLoop參數 | UnifiedLoop參數 | 轉換邏輯 | 說明 |
|--------------------|----------------|---------|------|
| `max_iterations` | `max_iterations` | 直接映射 | 最大迭代次數 |
| `llm_model` | `llm_model` | 直接映射 | LLM模型名稱 |
| `api_key` | `api_key` | 直接映射 | API密鑰 |
| `llm_timeout` | `llm_timeout` | 直接映射 | LLM超時(秒) |
| `llm_temperature` | `llm_temperature` | 直接映射 | LLM溫度參數 |
| `llm_max_tokens` | `llm_max_tokens` | 直接映射 | 最大token數 |
| `template_mode` | `template_mode` | 直接映射 | 啟用Template Mode |
| `template_name` | `template_name` | 直接映射 | Template名稱 |
| `innovation_mode` | `enable_learning` | 語義映射 | 啟用學習反饋 |
| `innovation_rate` | N/A | 移除 | UnifiedLoop自動管理 |
| `history_file` | `history_file` | 直接映射 | 歷史記錄檔案路徑 |
| `history_window` | `history_window` | 直接映射 | 歷史窗口大小 |
| `champion_file` | `champion_file` | 直接映射 | Champion檔案路徑 |
| `timeout_seconds` | `timeout_seconds` | 直接映射 | 回測超時 |
| `start_date` | `start_date` | 直接映射 | 回測開始日期 |
| `end_date` | `end_date` | 直接映射 | 回測結束日期 |
| `fee_ratio` | `fee_ratio` | 直接映射 | 交易費用比例 |
| `tax_ratio` | `tax_ratio` | 直接映射 | 交易稅率 |
| `continue_on_error` | `continue_on_error` | 直接映射 | 錯誤時繼續 |
| `log_dir` | `log_dir` | 直接映射 | 日誌目錄 |
| `log_level` | `log_level` | 直接映射 | 日誌級別 |
| N/A | **`use_json_mode`** | 新參數 | 啟用JSON Parameter Output |
| N/A | **`enable_monitoring`** | 新參數 | 啟用監控系統 |
| N/A | **`use_docker`** | 新參數 | 啟用Docker Sandbox |

### 新增功能參數

#### 1. `use_json_mode` (JSON Parameter Output)
```python
# 啟用JSON模式（需要template_mode=True）
loop = UnifiedLoop(
    template_mode=True,
    use_json_mode=True,  # Pydantic驗證的參數輸出
    template_name="Momentum"
)
```

**優勢**:
- Pydantic模型驗證
- 類型安全
- 自動參數驗證
- 更好的錯誤訊息

#### 2. `enable_monitoring` (監控系統)
```python
# 啟用完整監控
loop = UnifiedLoop(
    enable_monitoring=True,  # 預設True
    # 自動啟用：
    # - MetricsCollector（Prometheus指標）
    # - ResourceMonitor（CPU/記憶體/<1%開銷）
    # - DiversityMonitor（多樣性追蹤）
)
```

**監控指標**:
- 迭代成功率
- Sharpe ratio趨勢
- Champion更新頻率
- 資源使用（CPU/記憶體/磁碟）
- 策略多樣性

#### 3. `use_docker` (Docker Sandbox)
```python
# 啟用Docker隔離執行
loop = UnifiedLoop(
    use_docker=True,  # 安全執行策略
    # Docker配置：
    # - 2GB記憶體限制
    # - 0.5 CPU限制
    # - 600秒超時
    # - 網路隔離
    # - 唯讀檔案系統
)
```

**安全特性**:
- AST程式碼驗證
- 容器隔離
- 資源限制
- 網路隔離
- Seccomp過濾

---

## 逐步遷移指南

### Phase 1: 準備階段

#### 1.1 環境檢查

```bash
# 檢查Python版本（需要3.10+）
python --version

# 檢查必要套件
pip install -r requirements.txt

# 檢查FINLAB_API_TOKEN
echo $FINLAB_API_TOKEN
```

#### 1.2 備份現有配置

```bash
# 備份history和champion檔案
cp artifacts/data/iterations.jsonl artifacts/data/iterations_backup.jsonl
cp artifacts/data/champion.json artifacts/data/champion_backup.json

# 備份配置檔案
cp config/learning_system.yaml config/learning_system_backup.yaml
```

### Phase 2: 程式碼遷移

#### 2.1 建立UnifiedLoop實例

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

    # Learning
    enable_learning=True,
    history_window=10,

    # 監控
    enable_monitoring=True,

    # Docker（選用）
    use_docker=False,

    # 回測配置
    timeout_seconds=420,
    start_date="2018-01-01",
    end_date="2024-12-31",
    fee_ratio=0.001425,
    tax_ratio=0.003,

    # 檔案路徑
    history_file="artifacts/data/iterations.jsonl",
    champion_file="artifacts/data/champion.json",
    log_dir="logs"
)
```

#### 2.2 執行和結果處理

```python
# 執行loop
result = loop.run()

# 處理結果（API相同）
print(f"✓ 完成 {result['iterations_completed']} 次迭代")

if result['champion']:
    print(f"✓ Champion Sharpe: {result['champion'].metrics.get('sharpe_ratio', 'N/A')}")

if result.get('interrupted'):
    print("⚠️  執行被中斷")
```

#### 2.3 存取歷史和Champion

```python
# 向後相容的API
champion = loop.champion
history = loop.history

# 查詢近期記錄
recent = history.load_recent(N=5)
for record in recent:
    print(f"Iteration {record.iteration_num}: {record.classification_level}")
```

### Phase 3: 測試和驗證

#### 3.1 小規模測試

```python
# 10圈驗證測試
loop = UnifiedLoop(
    max_iterations=10,
    template_mode=True,
    template_name="Momentum",
    use_json_mode=True
)

result = loop.run()
assert result['iterations_completed'] == 10
assert not result.get('interrupted')
```

#### 3.2 對比測試

```python
# 比較AutonomousLoop和UnifiedLoop結果
# （如果AutonomousLoop仍可用）

# AutonomousLoop baseline
from artifacts.working.modules.autonomous_loop import AutonomousLoop
auto_loop = AutonomousLoop(max_iterations=10, template_mode=True)
auto_result = auto_loop.run()

# UnifiedLoop 測試
from src.learning.unified_loop import UnifiedLoop
unified_loop = UnifiedLoop(max_iterations=10, template_mode=True)
unified_result = unified_loop.run()

# 比較結果
print(f"Autonomous: {auto_result['iterations_completed']}")
print(f"Unified: {unified_result['iterations_completed']}")
```

#### 3.3 生產環境測試

```bash
# 使用run_100iteration_test.py進行完整測試
python run_100iteration_test.py --loop-type unified --template-mode --use-json-mode
```

---

## 測試腳本遷移

### 支援雙模式的腳本範本

```python
#!/usr/bin/env python3
"""
測試腳本範本 - 支援AutonomousLoop和UnifiedLoop
"""

import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loop-type',
        choices=['autonomous', 'unified'],
        default='unified',  # 預設使用UnifiedLoop
        help='Loop type: autonomous (deprecated) or unified (recommended)'
    )
    parser.add_argument(
        '--template-mode',
        action='store_true',
        help='Enable Template Mode'
    )
    parser.add_argument(
        '--use-json-mode',
        action='store_true',
        help='Enable JSON Parameter Output (UnifiedLoop only)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum iterations'
    )
    return parser.parse_args()

def main():
    args = parse_args()

    if args.loop_type == 'autonomous':
        # Legacy模式
        print("⚠️  WARNING: AutonomousLoop is deprecated")
        print("   Please use: --loop-type unified")
        print()

        from artifacts.working.modules.autonomous_loop import AutonomousLoop

        loop = AutonomousLoop(
            max_iterations=args.max_iterations,
            template_mode=args.template_mode,
            template_name="Momentum" if args.template_mode else None
        )

    else:
        # 推薦模式
        from src.learning.unified_loop import UnifiedLoop

        loop = UnifiedLoop(
            max_iterations=args.max_iterations,
            template_mode=args.template_mode,
            template_name="Momentum" if args.template_mode else None,
            use_json_mode=args.use_json_mode,
            enable_learning=True,
            enable_monitoring=True
        )

    # 執行
    result = loop.run()

    # 報告結果
    print(f"\n✓ Test Complete:")
    print(f"  - Iterations: {result['iterations_completed']}")
    print(f"  - Champion: {result['champion'].metrics.get('sharpe_ratio') if result['champion'] else 'N/A'}")

    return result

if __name__ == '__main__':
    sys.exit(0 if main() else 1)
```

### 已遷移腳本列表

| 腳本 | 狀態 | 說明 |
|------|------|------|
| `run_100iteration_test.py` | ✅ 已遷移 | 支援--loop-type參數 |
| `run_100iteration_unified_test.py` | ✅ UnifiedLoop | 純UnifiedLoop腳本 |
| `run_200iteration_stability_test.py` | ✅ UnifiedLoop | Week 3新建 |

### 待遷移腳本

| 腳本 | 優先級 | 預估時間 |
|------|--------|---------|
| `run_5iteration_template_smoke_test.py` | 高 | 30分鐘 |
| `run_phase1_dryrun_flashlite.py` | 高 | 1小時 |
| `run_diversity_pilot_test.py` | 高 | 1小時 |
| 其他腳本 | 中-低 | 2-4小時 |

---

## 常見問題FAQ

### Q1: UnifiedLoop會比AutonomousLoop慢嗎？

**A**: 不會。性能對比測試顯示：
- 核心迭代速度：≤110%（幾乎相同）
- 監控開銷：<1%（可忽略）
- Docker模式：額外3-5秒容器啟動時間（但安全性大幅提升）

**建議**: 生產環境可禁用Docker（`use_docker=False`）以獲得最佳性能。

### Q2: 我的舊history和champion檔案能直接使用嗎？

**A**: 是的！UnifiedLoop完全相容：
- ✅ 可直接讀取AutonomousLoop的iterations.jsonl
- ✅ 可直接讀取champion.json
- ✅ 檔案格式100%相容

### Q3: 我可以同時使用AutonomousLoop和UnifiedLoop嗎？

**A**: 可以，但不推薦：
- ⚠️  兩者會共享同一個history/champion檔案
- ⚠️  可能造成資料競爭
- ✅ 如果要並行測試，請使用不同的檔案路徑

### Q4: JSON Parameter Output是必須的嗎？

**A**: 不是必須的：
- `use_json_mode=False`：使用標準參數生成（相容AutonomousLoop）
- `use_json_mode=True`：使用Pydantic驗證（推薦，更安全）

**建議**: 新專案使用`use_json_mode=True`。

### Q5: 如何禁用監控系統？

**A**: 設置`enable_monitoring=False`：
```python
loop = UnifiedLoop(
    enable_monitoring=False,  # 禁用所有監控
    # ...其他配置
)
```

無監控模式下，UnifiedLoop行為與AutonomousLoop幾乎完全相同。

### Q6: Docker Sandbox需要什麼前置條件？

**A**:
```bash
# 1. Docker daemon運行
sudo systemctl start docker

# 2. 建構Docker映像
docker build -t finlab-sandbox:latest -f Dockerfile.sandbox .

# 3. 安裝Docker SDK
pip install docker

# 4. 啟用Docker模式
loop = UnifiedLoop(use_docker=True)
```

**注意**: Docker模式會增加每次迭代3-5秒的容器啟動時間。

### Q7: 遷移失敗怎麼辦？

**A**: 回退步驟：
```bash
# 1. 恢復備份
cp artifacts/data/iterations_backup.jsonl artifacts/data/iterations.jsonl
cp artifacts/data/champion_backup.json artifacts/data/champion.json

# 2. 使用AutonomousLoop（如果仍可用）
python run_script.py --loop-type autonomous

# 3. 檢查日誌
tail -f logs/your_test.log

# 4. 報告issue
# https://github.com/your-repo/issues
```

### Q8: UnifiedLoop支援哪些模型？

**A**: 與AutonomousLoop相同：
- ✅ Google Gemini (gemini-2.5-flash, gemini-2.5-pro)
- ✅ OpenAI GPT (gpt-4, gpt-4-turbo)
- ✅ Anthropic Claude (claude-3-opus, claude-3-sonnet)
- ✅ 任何支援OpenAI API格式的模型

### Q9: 如何驗證遷移成功？

**A**: 運行驗證測試：
```bash
# 1. 小規模smoke test
python run_5iteration_template_smoke_test.py

# 2. 中規模驗證
python run_100iteration_test.py --loop-type unified --template-mode

# 3. 檢查結果
# - 所有迭代成功完成
# - Champion正確更新
# - History正確記錄
# - 無錯誤/警告
```

### Q10: 有遷移檢查清單嗎？

**A**: 是的！

#### 遷移前檢查清單
- [ ] 備份history和champion檔案
- [ ] 確認Python版本≥3.10
- [ ] 安裝所有依賴套件
- [ ] FINLAB_API_TOKEN已設置
- [ ] 閱讀遷移指南

#### 遷移執行檢查清單
- [ ] 更新導入語句
- [ ] 更新配置參數
- [ ] 運行小規模測試（5-10圈）
- [ ] 檢查結果正確性
- [ ] 運行完整測試（100圈）
- [ ] 對比與AutonomousLoop結果

#### 遷移完成檢查清單
- [ ] 所有測試通過
- [ ] 性能符合預期(≤110%)
- [ ] History/Champion檔案正確
- [ ] 無異常錯誤/警告
- [ ] 更新文檔和註釋
- [ ] 通知團隊成員

---

## 疑難排解

### 問題1: ImportError: No module named 'src.learning.unified_loop'

**原因**: Python路徑未正確設置

**解決方案**:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.unified_loop import UnifiedLoop
```

### 問題2: ConfigurationError: use_json_mode=True requires template_mode=True

**原因**: JSON模式需要Template Mode

**解決方案**:
```python
loop = UnifiedLoop(
    template_mode=True,  # 必須啟用
    use_json_mode=True,
    template_name="Momentum"  # 必須指定
)
```

### 問題3: Docker execution failed: Docker daemon not running

**原因**: Docker daemon未啟動

**解決方案**:
```bash
# Linux
sudo systemctl start docker

# macOS
open -a Docker

# 或禁用Docker模式
loop = UnifiedLoop(use_docker=False)
```

### 問題4: ResourceMonitor background thread not stopping

**原因**: 監控未正確關閉

**解決方案**:
```python
try:
    loop = UnifiedLoop(enable_monitoring=True)
    result = loop.run()
finally:
    # UnifiedLoop會自動清理，但確保完成
    pass
```

### 問題5: 性能比AutonomousLoop慢>10%

**診斷步驟**:
```python
# 1. 檢查監控是否啟用
loop = UnifiedLoop(enable_monitoring=False)  # 測試無監控模式

# 2. 檢查Docker是否啟用
loop = UnifiedLoop(use_docker=False)  # 測試無Docker模式

# 3. 檢查日誌級別
loop = UnifiedLoop(log_level="WARNING")  # 減少日誌輸出
```

### 問題6: Champion不更新

**可能原因**:
1. Classification level不是LEVEL_3
2. Sharpe ratio未超過現有Champion
3. 錯誤處理中斷了更新流程

**診斷**:
```python
# 檢查迭代記錄
history = loop.history
recent = history.load_recent(N=10)
for r in recent:
    print(f"Iter {r.iteration_num}: {r.classification_level}, Sharpe={r.metrics.sharpe_ratio if r.metrics else 'N/A'}")
```

### 問題7: Memory leak detected after 200 iterations

**檢查步驟**:
```bash
# 運行200圈穩定性測試
python run_200iteration_stability_test.py

# 檢查記憶體趨勢
cat results/stability_200iter_*.json | jq '.resource_trend.memory_slope'

# 如果>0.01，表示記憶體洩漏
```

**解決方案**: 報告issue並附上日誌

### 問題8: TypeError: 'NoneType' object is not subscriptable

**可能原因**: result為None

**解決方案**:
```python
result = loop.run()

# 檢查result不為None
if result is None:
    print("Loop execution failed, check logs")
else:
    print(f"Iterations: {result['iterations_completed']}")
```

---

## 聯繫支援

### 獲取幫助

**GitHub Issues**:
- 報告bug: https://github.com/your-repo/issues
- 功能請求: https://github.com/your-repo/issues/new

**文檔**:
- API Reference: `docs/api/unified_loop.md`
- Architecture: `docs/architecture.md`
- Getting Started: `docs/getting_started.md`

**社群**:
- Discussions: https://github.com/your-repo/discussions
- Slack: your-workspace.slack.com

---

## 附錄

### A. 完整範例程式碼

#### A.1 基本使用

```python
from src.learning.unified_loop import UnifiedLoop

# 最簡單的配置
loop = UnifiedLoop(
    max_iterations=10,
    template_mode=True,
    template_name="Momentum"
)

result = loop.run()
print(f"Complete: {result['iterations_completed']} iterations")
```

#### A.2 完整配置

```python
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(
    # === Loop控制 ===
    max_iterations=100,
    continue_on_error=False,

    # === LLM配置 ===
    llm_model="gemini-2.5-flash",
    llm_timeout=60,
    llm_temperature=0.7,
    llm_max_tokens=4000,

    # === Template Mode ===
    template_mode=True,
    template_name="Momentum",

    # === JSON Parameter Output ===
    use_json_mode=True,

    # === Learning Feedback ===
    enable_learning=True,
    history_window=10,

    # === 監控系統 ===
    enable_monitoring=True,

    # === Docker Sandbox ===
    use_docker=False,

    # === 回測配置 ===
    timeout_seconds=420,
    start_date="2018-01-01",
    end_date="2024-12-31",
    fee_ratio=0.001425,
    tax_ratio=0.003,
    resample="M",

    # === 檔案路徑 ===
    history_file="artifacts/data/iterations.jsonl",
    champion_file="artifacts/data/champion.json",
    log_dir="logs",

    # === 日誌 ===
    log_level="INFO",
    log_to_file=True,
    log_to_console=True
)

result = loop.run()
```

#### A.3 監控系統使用

```python
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(
    max_iterations=100,
    enable_monitoring=True  # 啟用監控
)

result = loop.run()

# 監控系統會自動收集：
# - 迭代成功率
# - Sharpe ratio趨勢
# - Champion更新頻率
# - CPU/記憶體/磁碟使用
# - 策略多樣性

# 指標保存在MetricsCollector中
```

#### A.4 Docker Sandbox使用

```python
from src.learning.unified_loop import UnifiedLoop

loop = UnifiedLoop(
    max_iterations=10,
    use_docker=True  # 啟用Docker隔離
)

result = loop.run()

# Docker會：
# 1. 在容器中執行策略
# 2. 限制資源（2GB記憶體、0.5 CPU）
# 3. 隔離網路
# 4. 驗證程式碼安全性
# 5. 自動清理容器
```

### B. 遷移檢查清單範本

```markdown
# UnifiedLoop遷移檢查清單

專案: _______________
負責人: _______________
日期: _______________

## 準備階段
- [ ] 閱讀遷移指南
- [ ] 備份資料檔案
- [ ] 確認環境需求
- [ ] 安裝必要套件

## 執行階段
- [ ] 更新導入語句
- [ ] 更新配置參數
- [ ] 小規模測試（10圈）
- [ ] 中規模測試（100圈）
- [ ] 完整功能測試

## 驗證階段
- [ ] 功能正確性驗證
- [ ] 性能對比驗證
- [ ] 資料相容性驗證
- [ ] 錯誤處理驗證

## 完成階段
- [ ] 更新文檔
- [ ] 通知團隊
- [ ] 刪除備份（確認無問題後）
- [ ] 關閉遷移issue

備註:
_______________________________________________
_______________________________________________
```

---

**文檔版本**: v1.0
**最後更新**: 2025-11-23
**審核人員**: Claude (Sonnet 4.5)
**狀態**: ✅ 完成

**下一步**: 參考[Getting Started Guide](./getting_started.md)開始使用UnifiedLoop！
