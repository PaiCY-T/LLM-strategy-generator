# 目錄重組計劃

## 當前問題分析

### 根目錄混亂狀況
- **269個Python文件**: 大部分是 `generated_strategy_iter*.py` (150次迭代產物)
- **88個Markdown文件**: 各種總結報告、分析文檔
- **12個JSON文件**: 數據和配置文件混雜

### 影響
- ❌ 難以快速找到核心代碼
- ❌ 版本控制噪音（269個生成文件）
- ❌ 項目結構不清晰
- ❌ 新開發者難以理解

---

## 建議的目錄結構

```
finlab/
├── src/                          # 核心源代碼（已有）
│   ├── data/
│   ├── validation/
│   ├── repository/
│   ├── feedback/
│   ├── templates/
│   ├── analysis/
│   └── ...
│
├── tests/                        # 測試文件（已有）
│   └── ...
│
├── artifacts/                    # 🆕 迭代產物（新建）
│   ├── strategies/              # 生成的策略代碼
│   │   ├── iter_000-099/
│   │   │   ├── generated_strategy_iter0.py
│   │   │   ├── generated_strategy_iter1.py
│   │   │   └── ...
│   │   ├── iter_100-149/
│   │   └── best_strategy.py     # 當前最佳策略（符號鏈接）
│   │
│   ├── data/                    # 運行時數據
│   │   ├── champion_strategy.json
│   │   ├── iteration_history.json
│   │   ├── failure_patterns.json
│   │   └── iteration_history_backup_*.json
│   │
│   ├── reports/                 # 分析報告
│   │   ├── validation/
│   │   ├── performance/
│   │   ├── liquidity/
│   │   └── grid_search/
│   │
│   └── logs/                    # 日誌文件
│       └── *.log
│
├── docs/                         # 🆕 項目文檔（新建）
│   ├── summaries/               # 總結文檔
│   │   ├── MVP_COMPLETE.md
│   │   ├── ZEN_DEBUG_COMPLETE_SUMMARY.md
│   │   ├── FINAL_150_ITERATIONS_COMPLETE_SUMMARY.md
│   │   └── ...
│   │
│   ├── analysis/                # 分析文檔
│   │   ├── LIQUIDITY_MONITORING_PROJECT_SUMMARY.md
│   │   ├── MULTIFACTOR_OPTIMIZATION_SUMMARY.md
│   │   └── ...
│   │
│   ├── architecture/            # 架構文檔
│   │   ├── ARCHITECTURE.md
│   │   ├── TWO_STAGE_VALIDATION.md
│   │   └── FEEDBACK_SYSTEM.md
│   │
│   └── guides/                  # 使用指南
│       ├── QUICK_REFERENCE.md
│       ├── LIQUIDITY_COMPLIANCE_QUICK_REFERENCE.md
│       └── ...
│
├── config/                       # 🆕 配置文件（新建）
│   ├── datasets_curated_50.json
│   ├── dataset_mapping.json
│   └── system_validation_report.json
│
├── scripts/                      # 🆕 工具腳本（新建）
│   ├── cleanup_compliance_log.py
│   ├── analyze_*.py
│   ├── demo_*.py
│   └── reorganize_directory.py  # 目錄重組腳本
│
├── .claude/                      # Claude Code配置（已有）
│   ├── specs/
│   ├── steering/
│   ├── templates/
│   └── commands/
│
├── .finlab_cache/               # Finlab數據緩存（已有）
│
├── README.md                     # 主要文檔
├── STATUS.md                     # 當前狀態
├── CHANGELOG.md                  # 變更日誌
├── requirements.txt              # 依賴清單
└── PENDING_TASKS.md             # 待辦事項
```

---

## 重組計劃

### Phase 1: 創建新目錄結構（立即執行）

```bash
# 創建artifacts目錄
mkdir -p artifacts/strategies/iter_000-099
mkdir -p artifacts/strategies/iter_100-149
mkdir -p artifacts/data
mkdir -p artifacts/reports/{validation,performance,liquidity,grid_search}
mkdir -p artifacts/logs

# 創建docs目錄
mkdir -p docs/summaries
mkdir -p docs/analysis
mkdir -p docs/architecture
mkdir -p docs/guides

# 創建config目錄
mkdir -p config

# 創建scripts目錄
mkdir -p scripts
```

### Phase 2: 移動生成的策略文件

```bash
# 移動iter 0-99
mv generated_strategy_iter[0-9].py artifacts/strategies/iter_000-099/
mv generated_strategy_iter[0-9][0-9].py artifacts/strategies/iter_000-099/

# 移動iter 100-149
mv generated_strategy_iter1[0-4][0-9].py artifacts/strategies/iter_100-149/

# 移動其他策略文件
mv generated_strategy_loop_iter*.py artifacts/strategies/
mv best_strategy.py artifacts/strategies/ 2>/dev/null || true
mv multi_factor_*.py artifacts/strategies/ 2>/dev/null || true
mv smart_money_*.py artifacts/strategies/ 2>/dev/null || true
mv turtle_strategy_generator.py scripts/
```

### Phase 3: 移動JSON數據文件

```bash
# 移動運行時數據
mv champion_strategy.json artifacts/data/
mv iteration_history.json artifacts/data/
mv iteration_history_backup_*.json artifacts/data/
mv failure_patterns.json artifacts/data/
mv liquidity_compliance.json artifacts/data/
mv historical_analysis.json artifacts/data/
mv mvp_final_clean_history.json artifacts/data/

# 移動配置文件
mv datasets_curated_50.json config/
mv dataset_mapping.json config/
mv system_validation_report.json config/

# 移動grid search結果
mv turtle_grid_search_*.json artifacts/reports/grid_search/
```

### Phase 4: 移動文檔文件

```bash
# 移動總結文檔
mv *_SUMMARY.md docs/summaries/
mv *_COMPLETE.md docs/summaries/
mv ZEN_DEBUG_*.md docs/summaries/

# 移動分析文檔
mv LIQUIDITY_*.md docs/analysis/
mv MULTIFACTOR_*.md docs/analysis/
mv ANALYSIS_*.md docs/analysis/

# 移動架構文檔
mv TWO_STAGE_VALIDATION.md docs/architecture/
mv FEEDBACK_SYSTEM.md docs/architecture/ 2>/dev/null || true

# 移動指南文檔
mv QUICK_REFERENCE.md docs/guides/
mv *_QUICK_REFERENCE.md docs/guides/
```

### Phase 5: 移動工具腳本

```bash
# 移動分析腳本
mv analyze_*.py scripts/
mv demo_*.py scripts/
mv cleanup_*.py scripts/
mv extract_*.py scripts/
mv show_*.py scripts/
mv test_*.py tests/ 2>/dev/null || true  # 測試文件移到tests/

# 移動驗證腳本
mv run_*.py scripts/
mv validate_*.py scripts/
```

### Phase 6: 清理和驗證

```bash
# 創建符號鏈接（方便快速訪問）
ln -s artifacts/strategies/best_strategy.py best_strategy.py
ln -s artifacts/data/champion_strategy.json champion_strategy.json
ln -s artifacts/data/iteration_history.json iteration_history.json

# 更新.gitignore
cat >> .gitignore <<EOF

# Artifacts (generated files)
artifacts/strategies/generated_strategy_iter*.py
artifacts/logs/*.log
artifacts/reports/*.json

# Keep structure but ignore generated content
!artifacts/strategies/.gitkeep
!artifacts/data/.gitkeep
!artifacts/reports/.gitkeep
!artifacts/logs/.gitkeep
EOF

# 添加.gitkeep保持目錄結構
touch artifacts/strategies/.gitkeep
touch artifacts/data/.gitkeep
touch artifacts/reports/.gitkeep
touch artifacts/logs/.gitkeep
```

---

## 自動化重組腳本

我可以為您創建 `scripts/reorganize_directory.py` 自動執行以上所有步驟。

**優點**:
- ✅ 自動化、安全（先備份）
- ✅ 可回滾（保留備份）
- ✅ 驗證移動結果
- ✅ 生成移動報告

**執行時間**: ~2-3 minutes

---

## 後續調整

### 更新代碼中的路徑引用

需要更新的文件：
1. `autonomous_loop.py`: champion/history文件路徑
2. `src/repository/hall_of_fame.py`: 策略存儲路徑
3. `scripts/*`: 所有腳本的數據路徑

### 更新.claude/steering/structure.md

反映新的目錄結構。

---

## 決策點

### 🔴 立即決定

**是否執行目錄重組？**
- ✅ **推薦執行**: 清理項目結構，便於長期維護
- ⚠️ **風險**: 需要更新代碼中的路徑引用（~1-2 hours工作）

**執行方式選擇：**
1. **自動化腳本** (推薦): 我創建 `reorganize_directory.py` 自動執行
2. **手動執行**: 您逐步執行bash命令
3. **暫緩**: 保持現狀，標記為Technical Debt

---

## 建議行動

### 選項A: 立即執行完整重組（推薦）

**時間**: 2-3 hours（包含代碼路徑更新）

**步驟**:
1. 我創建自動化重組腳本（15 min）
2. 創建完整備份（5 min）
3. 執行重組（5 min）
4. 更新代碼路徑引用（1-2 hours）
5. 測試驗證（30 min）

**收益**:
- ✅ 清晰的項目結構
- ✅ 便於未來維護
- ✅ 版本控制更清晰

### 選項B: 分階段執行（穩健）

**Phase A** (今天 - 30 min):
- 只移動生成的策略文件到 `artifacts/strategies/`
- 更新 `.gitignore` 忽略這些文件
- 測試基本功能

**Phase B** (明天 - 1 hour):
- 移動JSON數據到 `artifacts/data/`
- 更新代碼路徑引用
- 測試完整流程

**Phase C** (後天 - 30 min):
- 移動文檔到 `docs/`
- 移動腳本到 `scripts/`
- 更新structure.md

### 選項C: 暫緩（不推薦）

保持現狀，但標記為P2 Technical Debt。

---

**您希望選擇哪個選項？**
1. 立即執行完整重組（選項A）
2. 分階段執行（選項B）
3. 暫緩，先完成Template System Phase 2

**如果選擇A或B，我可以立即創建自動化腳本協助執行。**
