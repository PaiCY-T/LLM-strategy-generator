# 目錄差異比較指南

**目標**：系統性地比較 `finlab/` 和 `LLM-strategy-generator/` 的所有差異，決定哪些文件需要合併。

---

## 🎯 方案總覽

| 方案 | 工具 | 優點 | 缺點 | 推薦度 |
|------|------|------|------|--------|
| **方案 A** | 自定義 PowerShell 腳本 | 自動化、生成報告和同步腳本 | 需要執行權限 | ⭐⭐⭐⭐⭐ |
| **方案 B** | robocopy | Windows 內建、快速 | 輸出較難閱讀 | ⭐⭐⭐⭐ |
| **方案 C** | Beyond Compare | 視覺化、強大 | 需要安裝付費軟件 | ⭐⭐⭐⭐⭐ |
| **方案 D** | Git 工具 | 精確比較內容 | 需要手動處理 | ⭐⭐⭐ |
| **方案 E** | WinMerge | 免費、視覺化 | 需要安裝 | ⭐⭐⭐⭐ |

---

## 📋 方案 A：PowerShell 自動分析腳本（推薦）⭐⭐⭐⭐⭐

### 特點
- ✅ 自動掃描兩個目錄
- ✅ 生成詳細報告（只在父目錄、只在子目錄、內容不同、內容相同）
- ✅ 自動生成同步腳本
- ✅ 排除 `.git`、`__pycache__` 等不必要的文件

### 使用步驟

**步驟 1：執行比較腳本**

在 Windows PowerShell 中執行：

```powershell
cd C:\Users\jnpi\Documents\finlab\LLM-strategy-generator

# 執行比較腳本
powershell -ExecutionPolicy Bypass -File .\compare_directories.ps1
```

**步驟 2：查看報告**

腳本會生成：
- `directory_comparison_report/comparison_report_YYYYMMDD_HHMMSS.txt` - 詳細報告
- `directory_comparison_report/sync_script.ps1` - 自動同步腳本

```powershell
# 查看報告
notepad directory_comparison_report\comparison_report_*.txt
```

**步驟 3：執行同步（可選）**

```powershell
# 執行自動生成的同步腳本
powershell -ExecutionPolicy Bypass -File directory_comparison_report\sync_script.ps1
```

**步驟 4：檢查 Git 狀態**

```powershell
git status
git diff
```

---

## 📋 方案 B：使用 robocopy（Windows 內建）

### 特點
- ✅ Windows 內建，無需安裝
- ✅ 快速、可靠
- ❌ 輸出格式較難閱讀

### 使用步驟

```powershell
cd C:\Users\jnpi\Documents\finlab

# 列出只在源目錄的文件（不執行複製）
robocopy . LLM-strategy-generator /L /E /NJH /NJS /NP /NS /NDL /XD .git __pycache__ .pytest_cache LLM-strategy-generator /XF *.pyc > comparison_onlyinsource.txt

# 列出只在目標目錄的文件
robocopy LLM-strategy-generator . /L /E /NJH /NJS /NP /NS /NDL /XD .git __pycache__ .pytest_cache /XF *.pyc > comparison_onlyindest.txt

# 列出所有差異（包括修改時間、大小）
robocopy . LLM-strategy-generator /L /E /V /XD .git __pycache__ .pytest_cache LLM-strategy-generator /XF *.pyc > comparison_all.txt
```

**參數說明**：
- `/L` - 列表模式（不實際複製）
- `/E` - 包含子目錄（包括空目錄）
- `/NJH` - 無作業標題
- `/NJS` - 無作業摘要
- `/NP` - 不顯示進度
- `/NS` - 不顯示大小
- `/NDL` - 不列出目錄
- `/XD` - 排除目錄
- `/XF` - 排除文件
- `/V` - 詳細輸出

查看結果：
```powershell
notepad comparison_all.txt
```

---

## 📋 方案 C：Beyond Compare（商業軟件）⭐⭐⭐⭐⭐

### 特點
- ✅ 視覺化界面，易於使用
- ✅ 強大的比較功能（文本、二進制、圖片）
- ✅ 支持三方合併
- ❌ 需要購買授權

### 使用步驟

1. **下載安裝**：https://www.scootersoftware.com/
2. **啟動比較**：
   ```
   Beyond Compare
   → 新建會話 → 文件夾比較
   → 左側：C:\Users\jnpi\Documents\finlab
   → 右側：C:\Users\jnpi\Documents\finlab\LLM-strategy-generator
   → 排除：.git, __pycache__, *.pyc
   ```
3. **查看差異**：
   - 紅色：只在一邊存在
   - 黃色：內容不同
   - 綠色：內容相同
4. **選擇性複製**：選擇需要的文件 → 右鍵 → 複製到右側

---

## 📋 方案 D：Git 工具

### 方法 1：使用 Git 本身

```bash
cd C:\Users\jnpi\Documents\finlab

# 初始化臨時 Git repo（如果父目錄沒有 Git）
git init

# 添加所有文件
git add -A

# 比較差異
git diff --no-index --stat . LLM-strategy-generator
git diff --no-index --name-only . LLM-strategy-generator > files_diff.txt
```

### 方法 2：使用 Git Bash

```bash
# 使用 diff 命令
diff -rq /c/Users/jnpi/Documents/finlab /c/Users/jnpi/Documents/finlab/LLM-strategy-generator \
  --exclude=.git --exclude=__pycache__ --exclude=LLM-strategy-generator > diff_result.txt
```

---

## 📋 方案 E：WinMerge（免費開源）⭐⭐⭐⭐

### 特點
- ✅ 免費開源
- ✅ 視覺化界面
- ✅ 支持文件夾比較和合併
- ❌ 需要安裝

### 使用步驟

1. **下載安裝**：https://winmerge.org/
2. **啟動比較**：
   ```
   WinMerge
   → 文件 → 打開 → 選擇文件夾
   → 左側：C:\Users\jnpi\Documents\finlab
   → 右側：C:\Users\jnpi\Documents\finlab\LLM-strategy-generator
   → 過濾器：排除 .git, __pycache__
   ```
3. **查看差異**：
   - 紅色：只在一邊存在
   - 黃色：內容不同
4. **複製文件**：選擇文件 → 複製到右側

---

## 🎯 推薦工作流程

### 階段 1：快速評估（5分鐘）

使用**方案 A (PowerShell 腳本)**：

```powershell
cd C:\Users\jnpi\Documents\finlab\LLM-strategy-generator
powershell -ExecutionPolicy Bypass -File .\compare_directories.ps1
```

這會給您一個完整的報告：
- 多少文件只在父目錄
- 多少文件內容不同
- 哪些文件是重要的

### 階段 2：手動審查（10-30分鐘）

查看報告，決定：
1. **必須複製**：只在父目錄且是重要文檔的文件
2. **需要合併**：兩邊都有但內容不同的文件
3. **可以忽略**：測試輸出、臨時文件、日誌等

### 階段 3：執行同步（5分鐘）

**選項 1：使用生成的腳本**
```powershell
powershell -ExecutionPolicy Bypass -File directory_comparison_report\sync_script.ps1
```

**選項 2：手動複製重要文件**
```powershell
xcopy docs\重要文件.md LLM-strategy-generator\docs\ /Y
```

### 階段 4：Git 提交（5分鐘）

```powershell
cd LLM-strategy-generator
git status
git add .
git commit -m "docs: Consolidate documentation from parent directory"
git push
```

---

## 📊 關鍵文件類型分類

### 必須複製 ✅
- **文檔**：`*.md`, `*.txt`, `*.rst`
- **規格**：`.spec-workflow/specs/*.md`
- **配置**：`*.yaml`, `*.toml`, `*.json`, `*.ini`

### 需要審查 ⚠️
- **代碼**：`*.py`, `*.js`, `*.ts`（可能有修改）
- **測試**：`tests/*.py`（可能有修改）
- **數據**：`*.csv`, `*.json`（檢查是否是測試數據）

### 可以忽略 ❌
- **Git**：`.git/`, `.gitignore`
- **Python**：`__pycache__/`, `*.pyc`, `.pytest_cache/`
- **虛擬環境**：`venv/`, `.venv/`, `env/`
- **IDE**：`.idea/`, `.vscode/`, `*.swp`
- **日誌**：`*.log`, `logs/`
- **輸出**：`output/`, `results/`, `*.pkl`

---

## 🚨 常見問題

### Q1: 腳本執行失敗，提示權限錯誤？

**A**: 使用 Bypass 執行策略：
```powershell
powershell -ExecutionPolicy Bypass -File .\compare_directories.ps1
```

或臨時設置執行策略：
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\compare_directories.ps1
```

### Q2: 報告太長，難以閱讀？

**A**: 使用過濾器查看特定類型：
```powershell
# 只查看 .md 文件
Get-Content comparison_report_*.txt | Select-String "\.md"

# 只查看 docs/ 目錄
Get-Content comparison_report_*.txt | Select-String "docs/"
```

### Q3: 如何只複製特定類型的文件？

**A**: 修改 `compare_directories.ps1` 中的排除模式，或使用 robocopy：
```powershell
# 只複製 .md 文件
robocopy C:\Users\jnpi\Documents\finlab C:\Users\jnpi\Documents\finlab\LLM-strategy-generator *.md /S /XD .git LLM-strategy-generator
```

### Q4: 兩邊都有但內容不同的文件，如何決定用哪個？

**A**: 查看修改時間和內容：
```powershell
# 比較修改時間
(Get-Item C:\Users\jnpi\Documents\finlab\docs\file.md).LastWriteTime
(Get-Item C:\Users\jnpi\Documents\finlab\LLM-strategy-generator\docs\file.md).LastWriteTime

# 使用 Git diff 比較內容
git diff --no-index C:\Users\jnpi\Documents\finlab\docs\file.md C:\Users\jnpi\Documents\finlab\LLM-strategy-generator\docs\file.md
```

一般規則：
- **文檔**：使用最新版本
- **代碼**：使用 Git repo 版本（已測試）
- **配置**：需要手動合併

---

## ✅ 檢查清單

完成目錄比較和同步後：

- [ ] 已執行目錄比較工具
- [ ] 已查看詳細報告
- [ ] 已識別必須複製的文件
- [ ] 已識別需要手動合併的文件
- [ ] 已執行文件同步
- [ ] 已用 `git status` 檢查變更
- [ ] 已用 `git diff` 確認內容
- [ ] 已提交到 Git
- [ ] 已推送到遠端
- [ ] Claude Code 可以訪問所有文件

---

## 🎯 下一步

完成目錄同步後：
1. ✅ 所有文檔統一在 `LLM-strategy-generator/`
2. ✅ Claude Desktop 和 Claude Code 路徑一致
3. ✅ 開始實際開發工作

---

**推薦方案**：先用**方案 A (PowerShell 腳本)**快速生成報告，再根據需要使用**方案 C (Beyond Compare)** 或**方案 E (WinMerge)** 進行視覺化審查。
