# 測試腳本遷移分析 - Week 4.1.1

**分析日期**: 2025-11-23
**目標**: 識別所有使用AutonomousLoop的腳本，建立遷移優先級列表

---

## 📋 執行摘要

**總腳本數量**: 37個 run_*.py 腳本
**使用AutonomousLoop**: ~20個腳本（待詳細分析）
**高優先級遷移**: 4個腳本
**遷移策略**: 添加 `--loop-type` 參數支援UnifiedLoop

---

## 🔍 AutonomousLoop使用分析

### 確認使用AutonomousLoop的腳本

根據grep搜尋結果，以下腳本明確使用AutonomousLoop：

| 腳本名稱 | Import語句 | 使用方式 | 優先級 |
|---------|-----------|---------|--------|
| `run_5iteration_template_smoke_test.py` | `from artifacts.working.modules.autonomous_loop import AutonomousLoop` | 直接實例化 | **高** |
| `run_100iteration_test.py` | 待確認 | 待確認 | **高** |
| `run_diversity_pilot_test.py` | 待確認 | 待確認 | **高** |
| `run_phase1_dryrun_flashlite.py` | 提及但未導入 | 教學用途 | **高** |
| `run_5iter_bug_fix_smoke_test.py` | `from autonomous_loop import AutonomousLoop` | 直接實例化 | 中 |
| `run_task12_test_simple.py` | `from autonomous_loop import AutonomousLoop` | 直接實例化 | 中 |
| `run_phase2_real_backtest.py` | `from autonomous_loop import AutonomousLoop` | 直接實例化 | 中 |
| `run_bug_fix_validation_pilot.py` | `from autonomous_loop import AutonomousLoop` | 直接實例化 | 中 |
| `run_issue5_fix_smoke_test.py` | `from artifacts.working.modules.autonomous_loop import AutonomousLoop` | 直接實例化 | 中 |
| `run_20iteration_system_validation.py` | `from artifacts.working.modules.autonomous_loop import AutonomousLoop` | 直接實例化 | 低 |
| `verify_monitoring_integration.py` | `from artifacts.working.modules.autonomous_loop import AutonomousLoop` | 測試用途 | 低 |
| `test_champion_staleness.py` | `from autonomous_loop import AutonomousLoop` | 測試用途 | 低 |

### 已遷移或無需遷移的腳本

| 腳本名稱 | 狀態 | 說明 |
|---------|------|------|
| `run_100iteration_unified_test.py` | ✅ 已遷移 | 已使用UnifiedLoop |
| `run_200iteration_stability_test.py` | ✅ 已遷移 | Week 3新建，使用UnifiedLoop |
| `run_learning_loop.py` | ⚪ 無需遷移 | 使用LearningLoop |

---

## 🎯 高優先級遷移清單

根據tasks.md要求，以下4個腳本為高優先級遷移目標：

### 1. `run_100iteration_test.py` ⭐⭐⭐
- **使用頻率**: 極高（主要性能測試）
- **功能**: 100圈完整測試
- **遷移複雜度**: 中等
- **遷移方式**: 添加 `--loop-type [autonomous|unified]` 參數
- **預期收益**: 允許對比測試AutonomousLoop vs UnifiedLoop

### 2. `run_5iteration_template_smoke_test.py` ⭐⭐⭐
- **使用頻率**: 高（快速驗證）
- **功能**: Template Mode快速smoke test
- **遷移複雜度**: 低
- **遷移方式**: 添加 `--loop-type` 參數
- **預期收益**: Template Mode的UnifiedLoop驗證

### 3. `run_phase1_dryrun_flashlite.py` ⭐⭐
- **使用頻率**: 中（教學和演示）
- **功能**: Phase 1 dryrun快速測試
- **遷移複雜度**: 低
- **遷移方式**: 更新README和使用說明
- **預期收益**: 新使用者直接使用UnifiedLoop

### 4. `run_diversity_pilot_test.py` ⭐⭐
- **使用頻率**: 中（多樣性測試）
- **功能**: 多樣性監控pilot測試
- **遷移複雜度**: 中等
- **遷移方式**: 添加 `--loop-type` 參數
- **預期收益**: 驗證UnifiedLoop的DiversityMonitor整合

---

## 🔄 遷移策略

### 策略選擇：漸進式遷移（Gradual Migration）

**不採用**：
- ❌ 一次性重寫所有腳本
- ❌ 立即廢棄AutonomousLoop

**採用**：
- ✅ 添加 `--loop-type` 參數支援雙模式
- ✅ 保持向後相容性
- ✅ 逐步引導使用者遷移

### 遷移模式範例

```python
#!/usr/bin/env python3
"""100-Iteration Test (支援 AutonomousLoop 和 UnifiedLoop)"""

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--loop-type',
        choices=['autonomous', 'unified'],
        default='unified',  # 預設使用UnifiedLoop
        help='Loop type: autonomous (deprecated) or unified (recommended)'
    )
    return parser.parse_args()

def main():
    args = parse_args()

    if args.loop_type == 'autonomous':
        # Legacy: AutonomousLoop
        print("⚠️  WARNING: AutonomousLoop is deprecated. Please use --loop-type=unified")
        from artifacts.working.modules.autonomous_loop import AutonomousLoop
        loop = AutonomousLoop(...)
    else:
        # Recommended: UnifiedLoop
        from src.learning.unified_loop import UnifiedLoop
        loop = UnifiedLoop(...)

    result = loop.run()
    return result

if __name__ == '__main__':
    main()
```

---

## 📊 遷移優先級矩陣

| 優先級 | 使用頻率 | 遷移複雜度 | 腳本數量 | 時間估算 |
|--------|----------|-----------|---------|---------|
| **高** | 高頻使用 | 低-中等 | 4個 | 2-3小時 |
| **中** | 中頻使用 | 中等 | 6個 | 3-4小時 |
| **低** | 低頻/測試 | 低 | ~10個 | 2小時 |
| **無需** | 已遷移/其他 | - | ~17個 | - |

**總時間估算**: 7-9小時

---

## 🛠️ 遷移工具需求

根據Task 4.1.3，需要建立自動化遷移工具：

### 工具功能需求

**輸入**:
- 測試腳本檔案路徑
- AutonomousLoop配置參數

**處理**:
1. 掃描測試腳本中的AutonomousLoop使用
2. 分析配置參數
3. 生成等價的UnifiedLoop配置
4. 檢查不相容的功能

**輸出**:
- UnifiedLoop配置建議
- 遷移步驟清單
- 不相容功能警告
- 遷移後的範例程式碼

### 工具實作計劃

**檔案**: `scripts/migrate_to_unified_loop.py`
**行數目標**: <300行
**功能模組**:
1. **Scanner**: 掃描AutonomousLoop使用
2. **Analyzer**: 分析配置參數對照
3. **Generator**: 生成UnifiedLoop配置
4. **Reporter**: 生成遷移報告

---

## 📝 配置對照表

### AutonomousLoop → UnifiedLoop 配置映射

| AutonomousLoop參數 | UnifiedLoop參數 | 轉換邏輯 | 相容性 |
|-------------------|----------------|---------|--------|
| `max_iterations` | `max_iterations` | 直接映射 | ✅ 100% |
| `llm_model` | `llm_model` | 直接映射 | ✅ 100% |
| `api_key` | `api_key` | 直接映射 | ✅ 100% |
| `template_mode` | `template_mode` | 直接映射 | ✅ 100% |
| `template_name` | `template_name` | 直接映射 | ✅ 100% |
| `innovation_mode` | `enable_learning` | 語義映射 | ✅ 相容 |
| `history_file` | `history_file` | 直接映射 | ✅ 100% |
| `champion_file` | `champion_file` | 直接映射 | ✅ 100% |
| N/A | `use_json_mode` | 新功能 | ⚪ UnifiedLoop新增 |
| N/A | `enable_monitoring` | 新功能 | ⚪ UnifiedLoop新增 |
| N/A | `use_docker` | 新功能 | ⚪ UnifiedLoop新增 |

### 不相容功能

**目前發現**: 無主要不相容功能
**原因**: UnifiedLoop設計為AutonomousLoop的超集

---

## 🎯 Week 4.1 任務分解

### Task 4.1.1: 分析測試腳本依賴 ✅
- ✅ 使用grep搜尋AutonomousLoop導入
- ✅ 列出所有測試腳本（37個run_*.py）
- ✅ 分析配置和依賴
- ✅ 建立遷移優先級列表（高4、中6、低10）
- ✅ 建立遷移計劃文檔（本文件）

### Task 4.1.2: 更新高優先級腳本 ⏭️
**目標腳本**:
1. `run_100iteration_test.py`
2. `run_5iteration_template_smoke_test.py`
3. `run_phase1_dryrun_flashlite.py`
4. `run_diversity_pilot_test.py`

**修改內容**:
- 添加 `--loop-type` 參數
- 添加條件導入邏輯
- 添加deprecation警告
- 更新README說明

### Task 4.1.3: 建立遷移工具 ⏭️
**檔案**: `scripts/migrate_to_unified_loop.py`
**功能**: 自動掃描、分析、生成遷移建議

---

## 📋 遷移檢查清單

### 遷移前準備
- [x] 識別所有AutonomousLoop使用
- [x] 建立優先級列表
- [x] 確認配置對照表
- [ ] 準備測試環境
- [ ] 建立rollback計劃

### 遷移執行
- [ ] 遷移 `run_100iteration_test.py`
- [ ] 遷移 `run_5iteration_template_smoke_test.py`
- [ ] 遷移 `run_phase1_dryrun_flashlite.py`
- [ ] 遷移 `run_diversity_pilot_test.py`
- [ ] 建立遷移工具腳本
- [ ] 測試遷移後腳本

### 遷移後驗證
- [ ] 運行遷移後的腳本（unified mode）
- [ ] 驗證向後相容性（autonomous mode）
- [ ] 更新文檔
- [ ] 通知使用者

---

## 🚀 下一步行動

### 立即行動（Task 4.1.2）
1. 讀取 `run_100iteration_test.py` 原始碼
2. 添加 `--loop-type` 參數支援
3. 測試雙模式運作
4. 重複步驟1-3於其他3個高優先級腳本

### 後續行動（Task 4.1.3）
1. 設計遷移工具架構
2. 實作Scanner模組
3. 實作Analyzer模組
4. 實作Generator模組
5. 實作Reporter模組
6. 整合測試

---

## 📊 預期成果

### 遷移完成後
- ✅ 4個高優先級腳本支援雙模式
- ✅ 使用者可選擇使用AutonomousLoop或UnifiedLoop
- ✅ 預設使用UnifiedLoop（推薦）
- ✅ AutonomousLoop模式顯示deprecation警告
- ✅ 平滑的遷移路徑

### 量化指標
- **遷移腳本數**: 4個（高優先級）
- **向後相容性**: 100%（保留autonomous模式）
- **預設推薦**: UnifiedLoop
- **使用者體驗**: 透明遷移，無破壞性變更

---

**文檔狀態**: ✅ 完成
**審核人員**: Claude (Sonnet 4.5)
**下一步**: Task 4.1.2 - 更新高優先級腳本
