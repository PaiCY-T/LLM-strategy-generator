# 1週測試Export失敗根本原因分析

**分析時間**: 2025-10-19 17:50
**測試狀態**: Gen 93/1000 (~4小時) 時被停止
**問題**: 0個metrics文件，0個checkpoint文件

---

## 根本原因

### 問題1: Export僅在Evolution完成後執行

**`sandbox_deployment.py:332-343`**:
```python
results = evolution.run_evolution(
    generations=max_gens - start_generation,
    template_distribution=template_distribution,
    early_stopping=False,
    export_final_metrics=True  # ← 僅在最後export
)

# 以下code只有在evolution.run_evolution()完成後才會執行
self.export_metrics(evolution, max_gens)     # ← 第342行
self.save_checkpoint(evolution, max_gens)    # ← 第343行
```

**問題**: 測試被kill時只跑到Gen 93，從未到達第342-343行

### 問題2: MonitoredEvolution沒有週期性export

**`src/monitoring/evolution_integration.py:296-306`**:
```python
# Periodic metrics export
if (generation + 1) % self.metrics_export_interval == 0:
    logger.info(  # ← 只有logging，沒有實際export
        f"Gen {generation}: "
        f"avg_fitness={metrics.avg_fitness:.4f}, "
        ...
    )
```

**問題**:
- `metrics_export_interval=10` 被傳入但只用於logging
- **沒有調用** `self.export_prometheus()` 或 `self.export_json()`
- 實際export只發生在evolution結束時 (line 313-320)

### 問題3: Signal Handler無效

**`sandbox_deployment.py:271-279`**:
```python
def _signal_handler(self, signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    self.should_stop = True  # ← 設置flag但沒有檢查
```

**問題**:
1. `run_evolution()` **從未檢查** `self.should_stop` flag
2. 沒有機制在signal時觸發export
3. 我使用 `kill -9` 完全繞過了signal handler

---

## Export流程分析

### 實際Export觸發點

**僅3個地方會export**:
1. **Evolution正常完成** (line 342-343)
   - 需要全部1000代完成
   - 1週測試只跑了93代 → **未觸發**

2. **KeyboardInterrupt** (line 358-359)
   - 需要Ctrl+C或SIGINT
   - 使用 `kill -9` → **未觸發**

3. **Exception發生** (line 365-366)
   - 需要程式crash
   - 正常運行中 → **未觸發**

### 預期Export觸發點 (但未實現)

**應該每10代export** (配置中設定):
- `metrics_export_interval = 10` (line 59)
- 預期Gen 10, 20, 30, ..., 90應該export
- **實際**: 沒有實現週期性export

**應該每50代checkpoint** (配置中設定):
- `checkpoint_interval = 50` (line 58)
- 預期Gen 50應該checkpoint
- **實際**: 沒有實現週期性checkpoint

---

## 為何100代測試有產出？

回顧100代測試的成功export，原因是：

**100代測試的差異**:
```bash
# 100代測試使用了 --test flag
python3 sandbox_deployment.py --test
```

**`sandbox_deployment.py:301`**:
```python
max_gens = 100 if test_mode else self.max_generations
```

**結果**:
- 100代測試: 跑完100代 → `evolution.run_evolution()` 正常完成 → 執行line 342-343 → **export成功**
- 1週測試: 只跑93/1000代 → 被kill → 從未到達line 342-343 → **export失敗**

---

## 設計缺陷總結

### 錯誤假設
程式設計假設evolution會完整跑完，沒有考慮：
1. 長時間測試中途檢查需求
2. 非正常終止情況
3. 使用者需要監控進度

### 參數誤導
```python
checkpoint_interval: int = 50        # 誤導：暗示每50代checkpoint
metrics_export_interval: int = 10    # 誤導：暗示每10代export
```

**實際**: 這些參數被傳遞但 **從未用於週期性export**

---

## 解決方案

### 方案A: 修改MonitoredEvolution (推薦)

**位置**: `src/monitoring/evolution_integration.py:296-306`

**修改**:
```python
# Periodic metrics export
if (generation + 1) % self.metrics_export_interval == 0:
    logger.info(
        f"Gen {generation}: "
        f"avg_fitness={metrics.avg_fitness:.4f}, "
        f"best={metrics.best_fitness:.4f}, "
        f"diversity={metrics.unified_diversity:.4f}, "
        f"champion_template={metrics.champion_template}"
    )

    # 新增: 實際export metrics
    if export_callback:  # 由sandbox_deployment傳入
        export_callback(self, generation)
```

**優點**:
- 真正實現週期性export
- 符合參數命名預期
- 可監控長時間測試

**缺點**:
- 需要修改2個檔案
- 需要增加callback機制

### 方案B: 使用SIGTERM而非SIGKILL

**替代kill命令**:
```bash
# 當前使用 (不會觸發export)
kill -9 12055

# 改用 (會觸發signal handler)
kill -15 12055  # SIGTERM
# 或
kill -2 12055   # SIGINT (Ctrl+C)
```

**需要配合修改signal handler**:
```python
def _signal_handler(self, signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    self.should_stop = True

    # 新增: 立即觸發export
    if hasattr(self, 'current_evolution'):
        self.export_metrics(self.current_evolution,
                          len(self.current_evolution.metrics_tracker.generation_history))
        self.save_checkpoint(self.current_evolution,
                           len(self.current_evolution.metrics_tracker.generation_history))
```

**優點**:
- 允許graceful shutdown
- 可在中斷時保存進度

**缺點**:
- 仍無法解決"需要手動中斷才export"的問題
- 不適合真正的1週無人值守測試

### 方案C: 後處理現有logs (權宜之計)

從logs重建metrics：

```python
# 從 sandbox_week_test.log 解析
# 每代都有: "Gen 93: avg_fitness=1.8435, best=2.0737, diversity=0.0000"
# 可重建基本metrics
```

**優點**:
- 不需修改code
- 可恢復已失去的數據

**缺點**:
- 數據不完整 (缺少詳細metrics)
- 無法恢復checkpoint (無法resume)

---

## 推薦行動

### 立即 (使用現有系統)

1. **不要重跑1週測試** - 會重複相同問題
2. **分析現有logs** - 雖然沒有export，Gen 93的log仍有價值
3. **運行100代測試** - 已知可以完整export

### 短期 (修復export問題)

實施 **方案A + 方案B組合**:

1. 修改 `MonitoredEvolution` 實現真正的週期性export
2. 改進 signal handler 實現graceful shutdown with export
3. 測試修復後的版本 (先跑50代驗證)

### 中期 (基於Phase 0決策)

根據 `PHASE0_TEST_RESULTS_20251019.md` 的 **FAILURE決策**:

**不應繼續投資在長時間測試上**，而是：
1. 接受Phase 1 Population-Based Learning路線
2. 將工程資源投入Phase 1改進
3. 1週測試的Gen 93數據作為"確認diversity collapse"的額外證據

---

## 數據恢復可能性

### 可恢復
- ✅ 每代fitness (從logs)
- ✅ 每代diversity (從logs)
- ✅ Template分佈 (從logs)
- ✅ Alert記錄 (從logs)

### 無法恢復
- ❌ 詳細population state
- ❌ 個體參數
- ❌ Prometheus格式metrics
- ❌ Checkpoint (無法resume)

### 恢復腳本範例

```python
import re
from pathlib import Path

log_file = Path("sandbox_week_test.log")
metrics = []

for line in log_file.read_text().splitlines():
    match = re.search(r'Gen (\d+): avg_fitness=([\d.]+), best=([\d.]+), diversity=([\d.]+)', line)
    if match:
        gen, avg, best, div = match.groups()
        metrics.append({
            'generation': int(gen),
            'avg_fitness': float(avg),
            'best_fitness': float(best),
            'diversity': float(div)
        })

# 輸出重建的metrics
import json
with open('recovered_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```

---

## 結論

**根本原因**: 週期性export功能 **存在於配置參數中但未在code中實現**

**影響範圍**: 任何未完整跑完的測試都不會產生export

**建議決策**:
1. ❌ **不重跑1週測試** (會重複問題 + Phase 0已是FAILURE)
2. ✅ **恢復Gen 93 logs數據** (補充Phase 0分析)
3. ✅ **進入Phase 1** (基於PHASE0_TEST_RESULTS決策)
4. ⏳ **修復export機制** (若未來需要長時間測試)

---

**報告生成**: 2025-10-19
**分析者**: Claude Code
**狀態**: 根本原因已確認 ✅
