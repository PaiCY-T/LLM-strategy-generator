# 文檔整合遷移指南

**目標**：統一 Claude Desktop 和 Claude Code 的工作路徑，避免路徑不一致問題。

**狀態**：🔄 進行中

---

## 📊 問題診斷

### 原有問題
```
C:\Users\jnpi\Documents\finlab\          ← 舊的工作根目錄
├── docs/                                 ← Claude Desktop 引用這裡
├── .spec-workflow/specs/                 ← Claude Desktop 引用這裡
└── LLM-strategy-generator/               ← Git repo（新的根目錄）
    ├── docs/                             ← Claude Code 引用這裡
    ├── .spec-workflow/specs/             ← Claude Code 引用這裡
    └── src/
```

**結果**：兩個 Claude 環境的路徑永遠不一致！

---

## 🎯 解決方案（方案 B）

### 統一工作根目錄為：`LLM-strategy-generator/`

所有文檔整合到 Git repository 中，確保：
- ✅ Claude Desktop 和 Claude Code 使用相同路徑
- ✅ 所有文件在版本控制下
- ✅ 團隊協作時文檔同步

---

## 📋 遷移步驟

### **步驟 1：複製關鍵文檔到 Git Repo** ⬅️ **您現在在這裡**

在 Windows PowerShell 或命令行執行：

```powershell
# 切換到 finlab 父目錄
cd C:\Users\jnpi\Documents\finlab

# 複製關鍵分析文檔（如果存在）
xcopy docs\DEBUG_RECORD_LLM_AUTO_FIX.md LLM-strategy-generator\docs\ /Y
xcopy docs\FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md LLM-strategy-generator\docs\ /Y
xcopy docs\PHASE1_COMPLETION_SUMMARY.md LLM-strategy-generator\docs\ /Y

# 複製 spec 文檔（如果存在）
xcopy .spec-workflow\specs\factor-graph-matrix-native-redesign.md LLM-strategy-generator\.spec-workflow\specs\ /Y

# 驗證複製結果
dir LLM-strategy-generator\docs\DEBUG_RECORD_LLM_AUTO_FIX.md
dir LLM-strategy-generator\docs\FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md
dir LLM-strategy-generator\docs\PHASE1_COMPLETION_SUMMARY.md
dir LLM-strategy-generator\.spec-workflow\specs\factor-graph-matrix-native-redesign.md
```

**檢查點**：
- [ ] 4個關鍵文件已複製到 LLM-strategy-generator
- [ ] 文件內容完整無損

---

### **步驟 2：提交到 Git**

```powershell
# 切換到 Git repo
cd C:\Users\jnpi\Documents\finlab\LLM-strategy-generator

# 檢查新增的文件
git status

# 添加文件到暫存區
git add docs/DEBUG_RECORD_LLM_AUTO_FIX.md
git add docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md
git add docs/PHASE1_COMPLETION_SUMMARY.md
git add .spec-workflow/specs/factor-graph-matrix-native-redesign.md

# 提交（CLAUDE.md 已更新）
git add CLAUDE.md
git commit -m "docs: Consolidate documentation to unify Claude Desktop and Code paths"

# 推送到遠端
git push
```

**檢查點**：
- [ ] Git 提交成功
- [ ] 推送到遠端成功
- [ ] CLAUDE.md 路徑已更新

---

### **步驟 3：驗證 Claude Code 可訪問**

在當前 Claude Code 會話中驗證：

```bash
# Claude Code 容器會自動拉取最新代碼
ls -la docs/DEBUG_RECORD_LLM_AUTO_FIX.md
ls -la docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md
ls -la docs/PHASE1_COMPLETION_SUMMARY.md
ls -la .spec-workflow/specs/factor-graph-matrix-native-redesign.md
```

**檢查點**：
- [ ] Claude Code 可以訪問所有文件
- [ ] 文件路徑使用相對路徑

---

### **步驟 4：更新 Claude Desktop 工作目錄**

以後啟動 Claude CLI 時：

```powershell
# 切換到統一的工作根目錄
cd C:\Users\jnpi\Documents\finlab\LLM-strategy-generator

# 啟動 Claude CLI
claude
```

**重要**：不要在 `C:\Users\jnpi\Documents\finlab` 啟動，統一使用子目錄 `LLM-strategy-generator`！

---

## 📝 路徑對照表

### 更新前（❌ 錯誤）
| 元件 | 路徑 |
|------|------|
| Claude Desktop 根目錄 | `C:\Users\jnpi\Documents\finlab\` |
| Claude Code 根目錄 | `/home/user/LLM-strategy-generator/` |
| Agent templates | `/mnt/c/Users/jnpi/Documents/finlab/.spec-workflow/agent/` |
| Specs | `/mnt/c/Users/jnpi/Documents/finlab/.spec-workflow/specs/` |
| **結果** | ⚠️ **路徑不一致** |

### 更新後（✅ 正確）
| 元件 | 路徑 |
|------|------|
| Claude Desktop 根目錄 | `C:\Users\jnpi\Documents\finlab\LLM-strategy-generator\` |
| Claude Code 根目錄 | `/home/user/LLM-strategy-generator/` |
| Agent templates | `.spec-workflow/agent/` (相對路徑) |
| Specs | `.spec-workflow/specs/` (相對路徑) |
| Docs | `docs/` (相對路徑) |
| **結果** | ✅ **路徑完全一致** |

---

## 🎯 關鍵文件清單

需要複製的 4 個關鍵文件：

1. **DEBUG_RECORD_LLM_AUTO_FIX.md**
   - 位置：`docs/`
   - 用途：LLM 自動修復的調試記錄

2. **FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md**
   - 位置：`docs/`
   - 用途：Factor Graph 綜合分析

3. **PHASE1_COMPLETION_SUMMARY.md**
   - 位置：`docs/`
   - 用途：Phase 1 完成總結

4. **factor-graph-matrix-native-redesign.md**
   - 位置：`.spec-workflow/specs/`
   - 用途：Factor Graph Matrix 原生重設計規格

---

## ✅ 驗證清單

完成遷移後，確認以下事項：

### Git Repository
- [ ] 4個關鍵文件已添加到 Git
- [ ] CLAUDE.md 已更新為相對路徑
- [ ] 已提交並推送到遠端

### Claude Desktop
- [ ] 工作目錄切換到 `LLM-strategy-generator/`
- [ ] 啟動 `claude` 命令時在正確目錄

### Claude Code
- [ ] 可以訪問所有 4 個文件
- [ ] 路徑使用相對路徑（`.spec-workflow/`, `docs/`）

### 路徑一致性
- [ ] 兩個 Claude 環境使用相同的根目錄
- [ ] 所有文檔引用使用相對路徑
- [ ] CLAUDE.md 指向正確

---

## 🚀 下一步

完成遷移後：

1. **Claude Code 將讀取並分析 4 個文件**
2. **提供理解總結和實施方案**
3. **開始實際開發工作**

---

## 📞 問題排查

### Q: 複製文件後 Claude Code 看不到？
**A**: 需要 Git 推送後，Claude Code 才會同步。執行：
```bash
git pull  # 在容器中拉取最新代碼
```

### Q: 路徑還是找不到？
**A**: 確認：
1. 文件已提交到 Git
2. 使用相對路徑（不要用 `/mnt/c/...` 絕對路徑）
3. 在正確的根目錄啟動 Claude CLI

### Q: 需要保留父目錄的文檔嗎？
**A**: 建議：
- 保留作為備份
- 以後主要維護 `LLM-strategy-generator/` 中的版本
- Git 版本控制會保護歷史

---

**完成時間預估**：5-10 分鐘
**風險等級**：🟢 低（只是複製文件）
**影響範圍**：路徑統一，提升協作效率

---

**當前狀態**：等待步驟 1 完成（複製文件到 Git repo）
