# QA Workflow - 品質保證流程

## 概述

**所有任務必須完成完整的 QA 流程並提供實證（solid evidence）才能標記為完成並進入下一個任務。**

此 QA 流程確保每個任務的產出都經過嚴格的品質驗證，防止技術債務累積。

---

## 🔄 強制性 QA 工作流程

每個任務必須按照以下步驟執行：

### 步驟 1️⃣: 實作 (Implementation)
- 完成任務規格中指定的實作
- 確保代碼遵循 PEP 8 標準
- 添加類型提示 (type hints) 和文檔字符串 (docstrings)
- 確保代碼可讀性和可維護性

**完成標準**:
- [ ] 代碼已撰寫完成
- [ ] 符合 PEP 8 標準
- [ ] 包含完整的類型提示
- [ ] 包含清晰的文檔字符串

---

### 步驟 2️⃣: 第一次 QA - 代碼審查 (Code Review)

**使用工具**: `mcp__zen__codereview`

**執行方式**:
```
使用 mcp__zen__codereview 工具審查以下文件:
- 文件路徑: [具體文件路徑]
- 審查類型: full (完整審查)
- 關注領域: quality, security, performance, architecture
- 模型: gemini-2.5-flash (快速且全面)
```

**審查重點**:
- ✅ **代碼品質**: 可讀性、可維護性、複雜度
- ✅ **安全性**: 潛在漏洞、輸入驗證、錯誤處理
- ✅ **性能**: 效率、資源使用、潛在瓶頸
- ✅ **架構**: 設計模式、SOLID 原則、模塊化

**必要動作**:
1. 運行 code review 工具
2. 仔細閱讀所有發現的問題
3. **修復所有 critical 和 high 級別的問題**
4. 考慮並解決 medium 級別的問題
5. 記錄 low 級別問題供未來改進

**完成標準**:
- [ ] Code review 已執行
- [ ] 所有 critical/high 問題已修復
- [ ] 審查報告已儲存
- [ ] 代碼品質評分達標 (無 major issues)

**證據範例**:
```
Evidence saved to: qa_reports/task-01-codereview.md
Overall Rating: PASS
Critical Issues: 0
High Issues: 0
Medium Issues: 2 (addressed)
```

---

### 步驟 3️⃣: 第二次 QA - 批判性驗證 (Critical Validation)

**使用工具**: `mcp__zen__challenge`

**執行方式**:
```
使用 mcp__zen__challenge 工具進行批判性驗證:
- 模型: gemini-2.5-pro (最高品質的批判性思考)
- 提示: "請批判性審查以下實作，驗證其正確性、完整性和潛在問題"
- 文件: [具體文件路徑]
```

**驗證目的**:
- 🔍 **正確性驗證**: 實作是否正確滿足需求
- 🔍 **完整性檢查**: 是否遺漏任何關鍵功能
- 🔍 **邊界案例**: 是否處理所有邊界情況
- 🔍 **潛在問題**: 識別可能的運行時問題
- 🔍 **最佳實踐**: 是否符合行業最佳實踐

**必要動作**:
1. 運行 challenge 工具使用 `gemini-2.5-pro` 模型
2. 仔細分析所有提出的質疑和建議
3. **解決所有有效的批評意見**
4. 對於不適用的意見，記錄理由說明
5. 必要時迭代改進直到驗證通過

**完成標準**:
- [ ] Challenge 驗證已執行
- [ ] 所有有效批評已解決
- [ ] 實作正確性已確認
- [ ] 邊界案例已處理
- [ ] 驗證報告已儲存

**證據範例**:
```
Evidence saved to: qa_reports/task-01-challenge.md
Validation Status: APPROVED
Critical Concerns: 0 (all addressed)
Implementation Correctness: VERIFIED
Edge Cases Handled: YES
```

---

### 步驟 4️⃣: 證據收集 (Evidence Collection)

**必須**為每個任務提供實證證明任務已完成且符合品質標準。

#### 代碼任務的證據要求:

**必備證據**:
1. ✅ **代碼審查報告** (Code Review Report)
   - 位置: `qa_reports/task-[XX]-codereview.md`
   - 狀態: PASS (無 major issues)

2. ✅ **批判性驗證報告** (Challenge Validation Report)
   - 位置: `qa_reports/task-[XX]-challenge.md`
   - 狀態: APPROVED (實作正確性已驗證)

3. ✅ **Linter 輸出** (無錯誤)
   ```bash
   flake8 src/[module]/ --max-line-length=100
   # 或
   pylint src/[module]/ --max-line-length=100
   ```
   - 結果: 0 errors (warnings 可接受)

4. ✅ **類型檢查輸出** (無錯誤)
   ```bash
   mypy src/[module]/ --strict
   ```
   - 結果: Success: no issues found

**額外證據（若適用）**:
5. ✅ **單元測試結果** (Unit Test Results)
   ```bash
   pytest tests/[module]/ -v --cov
   ```
   - 所有測試通過
   - 覆蓋率 ≥80%

6. ✅ **手動測試清單** (Manual Testing Checklist)
   - 記錄關鍵功能的手動測試結果

#### 測試任務的證據要求:

**必備證據**:
1. ✅ **測試執行輸出**
   ```bash
   pytest tests/[specific_test].py -v
   ```
   - 所有測試通過

2. ✅ **覆蓋率報告**
   ```bash
   pytest --cov=src/[module] --cov-report=html
   ```
   - 覆蓋率達到目標閾值（通常 ≥80%）

3. ✅ **代碼審查確認測試品質**
   - 測試涵蓋所有關鍵路徑
   - 測試案例清晰且可維護

#### UI 任務的證據要求:

**必備證據**:
1. ✅ **UI 組件截圖**
   - 位置: `qa_reports/screenshots/task-[XX]-ui.png`
   - 顯示功能正常運作

2. ✅ **代碼審查確認 UI 最佳實踐**
   - Streamlit 組件使用正確
   - 響應式設計實作

3. ✅ **手動測試清單完成**
   - [ ] UI 正確渲染
   - [ ] 用戶互動功能正常
   - [ ] 錯誤處理正確顯示
   - [ ] 支持的語言切換正常（zh-TW/en-US）

#### 整合任務的證據要求:

**必備證據**:
1. ✅ **端到端測試輸出**
   ```bash
   pytest tests/integration/test_[feature].py -v
   ```
   - 所有整合測試通過

2. ✅ **系統行為驗證**
   - 組件間交互正常
   - 數據流正確
   - 錯誤處理機制有效

3. ✅ **性能測試結果**（若適用）
   - 響應時間符合 NFR 要求
   - 資源使用在合理範圍內

---

### 步驟 5️⃣: 標記完成 (Mark Complete)

**只有在所有證據收集完成後才能標記任務為完成。**

**完成檢查清單**:
- [ ] 步驟 1: 實作已完成
- [ ] 步驟 2: Code review 已執行且 PASS
- [ ] 步驟 3: Challenge 驗證已執行且 APPROVED
- [ ] 步驟 4: 所有必要證據已收集並記錄
- [ ] 證據位置已文檔化
- [ ] 任務勾選框已標記 ✅

**記錄證據位置**:
在任務清單中添加證據註記：
```markdown
- [x] 1. Create project directory structure
  ...
  **Evidence Collected**:
  - Code Review: qa_reports/task-01-codereview.md (PASS)
  - Challenge: qa_reports/task-01-challenge.md (APPROVED)
  - Directory Structure: qa_reports/task-01-tree-output.txt
  - Linter: qa_reports/task-01-flake8.txt (0 errors)
```

**進入下一個任務**:
- ✅ 確認當前任務所有證據完備
- ✅ 確認沒有 blocking issues
- ✅ 開始下一個任務的實作

---

## 📁 證據組織結構

建議的證據文件組織：

```
qa_reports/
├── task-01-codereview.md          # Code review 報告
├── task-01-challenge.md           # Challenge 驗證報告
├── task-01-tree-output.txt        # 其他證據
├── task-01-flake8.txt             # Linter 輸出
├── task-02-codereview.md
├── task-02-challenge.md
├── task-02-unittest-output.txt
├── screenshots/
│   ├── task-59-dashboard-ui.png   # UI 截圖
│   └── task-60-input-ui.png
└── integration/
    ├── task-69-e2e-test.txt       # 整合測試結果
    └── task-71-performance.txt    # 性能測試結果
```

---

## 🚫 常見錯誤和注意事項

### ❌ 不可接受的做法:

1. **跳過 QA 步驟**
   - ❌ 直接標記完成而不運行 code review
   - ❌ 忽略 challenge 驗證步驟
   - ✅ 必須完成所有 QA 步驟

2. **忽略發現的問題**
   - ❌ Code review 發現問題但不修復
   - ❌ Challenge 提出的批評不處理
   - ✅ 所有 critical/high 問題必須修復

3. **缺乏證據**
   - ❌ 聲稱完成但沒有證據支持
   - ❌ 只有部分證據
   - ✅ 必須提供所有必要證據

4. **低品質證據**
   - ❌ Linter 有多個錯誤但忽略
   - ❌ 測試覆蓋率低於閾值
   - ✅ 所有證據必須顯示符合標準

### ✅ 最佳實踐:

1. **持續品質**
   - 每個任務都維持高品質標準
   - 不要累積技術債務
   - 及早發現和修復問題

2. **完整文檔**
   - 所有 QA 報告保存完整
   - 證據清晰且易於驗證
   - 記錄重要決策和理由

3. **迭代改進**
   - 如果驗證失敗，修復後重新驗證
   - 不要因為一次失敗就放棄
   - 每次迭代都是學習機會

4. **保持誠實**
   - 如實報告問題
   - 不要隱藏失敗的測試
   - 承認不確定的地方並尋求幫助

---

## 📊 QA 流程範例

### 範例: Task 6 - Create data manager interface

#### 實作階段:
```python
# src/data/__init__.py
from typing import Optional, List, Tuple
from datetime import datetime
import pandas as pd

class DataManager:
    """管理 Finlab API 數據下載和緩存"""

    def download_data(self, dataset: str, force_refresh: bool = False) -> pd.DataFrame:
        """下載指定數據集"""
        pass

    def get_cached_data(self, dataset: str) -> Optional[pd.DataFrame]:
        """獲取緩存的數據"""
        pass

    def check_data_freshness(self, dataset: str) -> Tuple[bool, datetime]:
        """檢查數據新鮮度"""
        pass

    def list_available_datasets(self) -> List[str]:
        """列出可用數據集"""
        pass

    def cleanup_old_cache(self, days_threshold: int = 30) -> int:
        """清理舊緩存"""
        pass
```

#### QA Step 1 - Code Review:
```
使用 mcp__zen__codereview:
- 文件: src/data/__init__.py
- 審查類型: full
- 模型: gemini-2.5-flash

結果:
✅ Code Quality: GOOD
✅ Type Hints: Complete
✅ Docstrings: Present
⚠️ Issue: Methods are stubs (expected for interface)
Overall: PASS
```

#### QA Step 2 - Challenge Validation:
```
使用 mcp__zen__challenge with gemini-2.5-pro:
提示: "請驗證此 DataManager 接口設計的正確性和完整性"

驗證結果:
✅ Interface design is appropriate
✅ Type hints are correct
✅ Method signatures match design.md
✅ Docstrings are clear
Overall: APPROVED
```

#### Evidence Collection:
```
Evidence saved:
1. qa_reports/task-06-codereview.md (PASS)
2. qa_reports/task-06-challenge.md (APPROVED)
3. qa_reports/task-06-mypy.txt (Success: no issues found)
4. qa_reports/task-06-flake8.txt (0 errors)
```

#### Task Marked Complete:
```markdown
- [x] 6. Create data manager interface
  ...
  **Evidence Collected**:
  - Code Review: qa_reports/task-06-codereview.md (PASS)
  - Challenge: qa_reports/task-06-challenge.md (APPROVED)
  - Type Check: qa_reports/task-06-mypy.txt (SUCCESS)
  - Linter: qa_reports/task-06-flake8.txt (0 errors)
```

---

## 🎯 成功標準

一個任務被視為**成功完成**當且僅當:

1. ✅ **實作完成**: 代碼已撰寫並符合規格
2. ✅ **Code Review PASS**: 無 major issues
3. ✅ **Challenge APPROVED**: 實作正確性已驗證
4. ✅ **證據完整**: 所有必要證據已收集
5. ✅ **品質達標**: Linter、type checker、tests 全部通過
6. ✅ **文檔完整**: 證據位置已記錄

**遵循此流程確保每個任務都是高品質、可維護、無技術債務的產出。**
