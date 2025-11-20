# Phase 1 改進歷史 - LLM Prompt優化進程

## 概述

本文檔記錄Phase 1 LLM Prompt改進的完整歷史，包括每個階段的目標、實作、測試結果與學習。

**Phase 1總體目標**: 將LLM策略生成成功率從20%基準線提升至55%+

---

## 📊 測試結果總覽

| 階段 | 日期 | LLM成功率 | 主要錯誤 | 狀態 |
|------|------|-----------|----------|------|
| **Baseline** | 2025-11-20 13:41 | **20%** (4/20) | 多樣化錯誤 | ✅ 基準 |
| **Phase 1.0** | 2025-11-20 23:27 | **0%** (0/9) | 78% 缺report | ❌ 退步 |
| **Phase 1.1** | 2025-11-21 (計畫中) | **60%+** (目標) | 預期<10% | 🔄 開發中 |

---

## Baseline - 初始狀態 (Pre-Phase 1)

### 測試資訊
- **日期**: 2025-11-20 13:41-13:56
- **配置**: `experiments/llm_learning_validation/config_llm_only_20.yaml`
- **模型**: google/gemini-2.5-flash (via OpenRouter)
- **迭代**: 20次

### 結果

**LLM Only**: 20.0% (4/20 成功)
```
成功案例: iterations 0, 3, 10, 13
失敗原因分佈:
- 欄位不存在/名稱錯誤: ~40%
- 執行錯誤 (邏輯問題): ~30%
- 其他錯誤: ~30%
```

**Factor Graph Only**: 90.0% (18/20 成功)
**Hybrid (70% LLM)**: 75.0% (15/20 成功)

### 關鍵發現
1. ✅ LLM能生成策略，但欄位名稱錯誤率高
2. ✅ Factor Graph穩定，證明系統基礎架構可靠
3. ✅ Hybrid模式顯示LLM有潛力，需改進prompt

### Baseline Prompt結構
```
1. Task description
2. Champion context (code + metrics)
3. FinLab constraints (基本欄位列表)
4. Failure patterns
5. Output format example
Total: ~2,000 tokens
```

**問題**:
- 欄位列表不完整 (僅~40個欄位)
- 無系統性思考流程指導
- 缺少欄位驗證機制

---

## Phase 1.0 - 初次改進 (失敗)

### 改進內容

**Task 1.1: 完整欄位目錄** (完成 2025-11-20 21:08)
- ✅ 擴充至160個完整欄位
- ✅ 分類: price (6), fundamental_features (66), financial_statement (88)
- ✅ 包含中英文對照
- Commit: `4cf54d3`

**Task 1.2: API文檔強化** (完成 2025-11-20 23:00)
- ✅ 加入data.get()使用說明
- ✅ 常見錯誤與避免方法
- ✅ 完整回測執行範例
- Commit: `b877752`, `e66b8fa`

**Task 1.2.5: 系統提示與CoT** (完成 2025-11-20 22:30)
- ✅ 加入LLM角色定義
- ✅ 5步驟Chain of Thought工作流程
- ✅ 關鍵規則清單
- Commit: `8a9decf`

**Task 1.3: 欄位驗證輔助函數** (完成 2025-11-20 22:45)
- ✅ validate_field_exists()範例
- ✅ 完整TDD測試
- Commit: `8a9decf`

### 測試資訊
- **日期**: 2025-11-20 23:27-23:35
- **配置**: `experiments/llm_learning_validation/config_phase1_llm_only_20.yaml`
- **模型**: google/gemini-2.5-flash
- **迭代**: 9次 (terminated due to error)

### 結果

**LLM Only**: 0% (0/9 成功) ❌
```
所有9次迭代都執行失敗
主要錯誤: 78% (7/9) 缺少 report = sim() 呼叫
其他錯誤:
- Stock ID錯誤: 1次
- Metric validation: 1次
```

**程式碼長度分佈**: 662-6,010 字元 (變異性大)

**第9次後**: LLM返回空響應 → 測試終止

### Phase 1.0 Prompt結構

```
1. System Prompt (CoT 5步驟)           ~500 tokens
2. Task Header                          ~100 tokens
3. Champion Context                     ~200 tokens
4. Innovation Directive                 ~100 tokens
5. Constraints (含160欄位)             ~1,500 tokens ← 問題區
6. API Documentation                    ~800 tokens  ← 問題區
7. Validation Helper                    ~300 tokens
8. Failure Patterns                     ~200 tokens
9. Output Format                        ~200 tokens  ← 被忽略
---
Total: ~3,900 tokens
```

### 根本原因分析

**我的診斷**:
1. 資訊過載: 3,644 tokens欄位說明在前
2. 程式碼框架缺失: 輸出格式在最後被忽略
3. Token分佈: 前1,500 tokens被欄位列表消耗

**Gemini 2.5 Pro專家分析** (2025-11-21):
1. **認知隧道效應**: LLM注意力被欄位細節消耗
2. **指令層級模糊**: 無法區分"必須遵守"vs"可供參考"
3. **CoT副作用**: 抽象流程消耗認知資源，到實作階段已力不從心

**共識結論**:
> LLM成為了"策略分析師"而非"程式碼生成器"。
> 過度關注欄位細節，忽略了程式碼框架。

### 學習
- ❌ 更多資訊 ≠ 更好的結果
- ❌ 欄位目錄放前面會干擾核心任務
- ❌ 抽象CoT對程式碼生成效果差
- ✅ Factor Graph 100%成功證明基礎設施穩定
- ✅ 問題在Prompt結構而非系統架構

---

## Phase 1.1 - Golden Template策略 (開發中)

### 設計理念

**核心洞察**:
> 將任務從"生成完整回測腳本"簡化為"填充策略邏輯"

**Golden Template三大支柱**:
1. **不可變框架**: 回測執行部分不可修改
2. **框架優先**: Template在第1位，欄位參考在最後
3. **簡化CoT**: 從抽象5步驟→具體4步驟 (框架導向)

### 改進內容

**變更1: Golden Template (新增)**
```python
def strategy(data):
    # ==========================================================
    # START: Your strategy logic ONLY goes here
    # (步驟指引，無具體程式碼範例)
    # ==========================================================

    # Your code here

    # ==========================================================
    # END
    # ==========================================================
    return position

# --- DO NOT MODIFY BELOW THIS LINE ---
position = strategy(data)
report = sim(position, ...)
```

**設計特點**:
- ✅ 絕對強制性語氣: "You MUST", "Do NOT deviate"
- ✅ 視覺化標記: START/END with `=====` lines
- ✅ 步驟指引替代具體範例 (避免複製)
- ✅ 完整可執行的Template

**變更2: 簡化CoT (重構)**
```
舊: 分析→計畫→選欄位→實作→返回 (5步驟，抽象)
新: 理解模板→選欄位→設計邏輯→實作 (4步驟，具體)
```

**關鍵改進**:
- Step 1優先: 理解Template結構 (框架導向)
- Step 2: 明確指示查閱APPENDIX
- Step 3: Pseudocode規劃 (降低認知負擔)
- Step 4: 填充模板 (聚焦單一任務)

**變更3: 參考資料置後 (重組)**
```
新結構:
1. Golden Template              ~300 tokens ← 第1位
2. Simplified CoT               ~200 tokens ← 框架導向
3. Task + Champion Context      ~300 tokens
4. APPENDIX (最後):
   - 160 Fields                ~1,500 tokens
   - API Documentation          ~800 tokens
   - Validation Helper          ~300 tokens
```

**Token分佈優化**:
- 前500 tokens: Template + CoT (核心指令)
- 後2,600 tokens: 參考資料 (需要時查閱)

### 實作任務

**程式碼變更**:
- [ ] 新增 `_build_golden_template()`
- [ ] 新增 `_build_simplified_cot()`
- [ ] 新增 `_build_appendix()`
- [ ] 修改 `build_creation_prompt()` 組合順序

**測試開發**:
- [ ] `test_golden_template_structure()`
- [ ] `test_simplified_cot_steps()`
- [ ] `test_creation_prompt_order()`
- [ ] `test_appendix_preserves_content()`

**驗證工具**:
- [ ] `tools/validate_structure.py` (結構化驗證)
- [ ] 金絲雀測試案例 (simple/medium/complex)

### 驗證策略

**Tier1: 結構化驗證** (10次生成)
- 目標: >90% 結構合格
- 檢查: has_strategy_def, has_report, has_return, compiles, no_lookahead
- 決策: <90% → 調整Golden Template

**Tier2: 金絲雀測試** (3案例×3次=9次)
- Simple: >80% 成功率
- Medium: >60% 成功率
- Complex: >40% 成功率
- Overall: >60% 成功率
- 決策: <60% → 調整CoT/APPENDIX

**Tier3: 完整測試** (20次×3模式)
- 目標: LLM Only >60%
- 對比: vs Baseline (20%), vs Phase 1 (0%)

### 預期效果

| 指標 | Phase 1.0 | Phase 1.1預期 | 改善幅度 |
|------|-----------|---------------|----------|
| 結構合格率 | 0% | >90% | +90pp |
| report缺失錯誤 | 78% | <10% | -68pp |
| LLM成功率 | 0% | 60%+ | +60pp |

**信心等級**:
- Golden Template解決report缺失: 95%
- 成功率提升至60%+: 85%
- 不降低創意多樣性: 75%

### 風險與緩解

**風險1**: APPENDIX查閱率低
- 機率: 25%
- 緩解: CoT Step 2明確指示查閱
- 備案: 嵌入Top 20常用欄位於Template

**風險2**: START/END標記混淆
- 機率: 15%
- 緩解: 視覺分隔線 + "EXCLUSIVELY"
- 備案: 更激進約束 (e.g. 輸出必須以特定字串開始)

**風險3**: 過度約束降低創意
- 機率: 25%
- 緩解: 僅約束結構，不約束邏輯
- 驗證: 策略多樣性指標 >0.6

### 實作時程

```
Day 1 (2025-11-21):
[Hour 1-2] 編碼4個方法 + 單元測試
[Hour 3]   Tier1+Tier2驗證

Day 2 (視驗證結果):
[Option A] Tier2≥60% → 完整測試 (20次×3模式)
[Option B] Tier2<60% → 診斷調整 → 重試
```

### 參考資料

- 完整規格: `docs/phase1.1-golden-template-spec.md`
- 深度分析: zen:thinkdeep 6-step analysis (confidence: certain)
- 專家建議: Gemini 2.5 Pro analysis (95%共識度)

---

## 學習總結

### 關鍵洞察

1. **資訊密度 vs 指令優先級**
   - ✅ 核心指令必須在前500 tokens
   - ❌ 參考資料過早出現會干擾注意力
   - 🎯 解決: 框架優先，參考置後

2. **LLM認知模式**
   - ✅ LLM遵循"所看即所做"原則
   - ❌ 抽象CoT不適合程式碼生成
   - 🎯 解決: 具體步驟，框架導向

3. **強制性 vs 建議性**
   - ✅ "You MUST" > "Please follow"
   - ❌ "建議格式"常被忽略
   - 🎯 解決: Golden Template不可變

4. **任務簡化**
   - ✅ "填充"比"生成"更可控
   - ❌ 開放式任務錯誤率高
   - 🎯 解決: START/END明確填充區

### 通用原則

**Prompt設計黃金法則**:
1. 框架優先，細節在後
2. 強制性語氣，視覺化標記
3. 具體步驟，避免抽象
4. 任務簡化，降低認知負擔
5. 快速驗證，迭代改進

**測試策略最佳實踐**:
1. 分層驗證: 結構→小樣本→完整
2. 早期失敗: Tier1不過不進Tier2
3. 診斷優先: 失敗時分析根因
4. 增量改進: 每次只改一個變數

---

## 下一步計畫

### Phase 1.1 (當前)
- [ ] 完成Golden Template MVP實作
- [ ] 通過Tier1+Tier2驗證
- [ ] 完整測試20次×3模式

### Phase 1.2 (如需要)
- modification prompt應用Golden Template
- 欄位使用頻率分析
- Top 20常用欄位前置

### Phase 2 (Phase 1成功後)
- 策略多樣性優化
- 欄位組合pattern mining
- Few-shot learning強化

---

**文檔維護**: 每個Phase完成後更新此文檔
**最後更新**: 2025-11-21 (Phase 1.1規劃階段)
