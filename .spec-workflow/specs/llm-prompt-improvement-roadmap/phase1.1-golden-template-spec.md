# Phase 1.1: Golden Template Strategy - 完整規格文檔

## 執行摘要

**版本**: Phase 1.1.0 MVP
**日期**: 2025-11-21
**狀態**: 規格審查中
**預期效果**: LLM成功率 0% → 60%+

### 問題定義

**Phase 1測試結果** (2025-11-20):
- LLM Only: 0% (0/9 成功) ❌ 退步
- 主要錯誤: 78% (7/9) 缺少 `report = sim()` 呼叫
- 根因: 資訊過載 + 目標失焦 + 結構缺失

**與Baseline對比**:
- Pre-Phase 1: 20% (4/20)
- Phase 1: 0% (0/9)
- 退步幅度: -20%

### 解決方案: Golden Template策略

**核心理念**: 強制LLM遵循不可變的程式碼框架，將任務從"生成完整腳本"簡化為"填充策略邏輯"

**三大支柱**:
1. **Golden Template**: 不可變程式碼骨架 (第1位)
2. **簡化CoT**: 框架導向的4步驟思考流程 (第2位)
3. **參考置後**: 160欄位+API文檔移至APPENDIX (最後)

---

## 詳細設計規格

### 1. Golden Template 設計

#### 1.1 設計原則

| 原則 | 說明 | 實作方式 |
|------|------|----------|
| **絕對強制性** | 使用命令式語氣 | "You MUST", "Do NOT deviate" |
| **視覺化標記** | 明確填充區域 | START/END markers with `=====` lines |
| **不可變部分** | 回測執行不可改 | "DO NOT MODIFY BELOW THIS LINE" |
| **完整可執行** | Template本身可運行 | 包含完整的function + backtest execution |

#### 1.2 Template結構

```python
def strategy(data):
    """Trading strategy logic."""
    # ==========================================================
    # START: Your strategy logic ONLY goes in this block
    #
    # Instructions:
    # 1. Load data: close = data.get('price:收盤價')
    # 2. Calculate indicators: ma = close.rolling(20).mean()
    # 3. Define conditions: position = (close > ma)
    # 4. Handle NaN: position = position.fillna(False)
    # 5. Return position series
    # ==========================================================

    # Your code here (replace this comment)

    # ==========================================================
    # END: Your strategy logic
    # ==========================================================

    return position

# -----------------------------------------------------------------------
# Golden Template: Backtest Execution Section
# DO NOT MODIFY ANYTHING BELOW THIS LINE
# -----------------------------------------------------------------------
position = strategy(data)
position = position.loc[start_date:end_date]
report = sim(position, fee_ratio=fee_ratio, tax_ratio=tax_ratio, resample="M")
```

#### 1.3 關鍵設計決策

**Q: 為何不提供具體範例程式碼？**
A: 避免LLM直接複製範例。使用步驟指引而非具體code，確保LLM思考原創邏輯。

**Q: START/END標記會混淆LLM嗎？**
A: 使用視覺分隔線 `=====` + 明確指示 "EXCLUSIVELY in this block" 降低混淆。

**Q: 環境變數如何處理？**
A: 在註釋中說明 `data`, `start_date`, `fee_ratio` 等由FinLab環境提供。

---

### 2. 簡化CoT設計

#### 2.1 Phase 1 CoT問題

**舊CoT (抽象5步驟)**:
1. Analyze Requirements (分析需求)
2. Plan Strategy Logic (計畫策略)
3. Select Valid Fields (選擇欄位)
4. Implement with Proper Structure (實作)
5. Add Return Statement (加返回)

**問題**:
- Step 3在Step 4之前，但實作時需先看框架
- 過於抽象，消耗認知資源
- Step 5單獨強調return，但沒強調sim()

#### 2.2 Phase 1.1 CoT (具體4步驟)

```markdown
## Step 1: Understand the Golden Template Structure
- Part 1: Your strategy logic (between START/END)
- Part 2: Backtest execution (NEVER modify)
- **Your job**: Fill Part 1 ONLY

## Step 2: Identify Required Data Fields
- What market data needed?
- **Action**: Check PART 4: APPENDIX section
- Copy field names EXACTLY as shown

## Step 3: Plan Your Strategy Logic (Pseudocode)
- Entry logic: When to buy?
- Exit logic: When to sell?
- Risk management: Filters?

## Step 4: Implement Inside the Template
- Convert Step 3 to Python code
- Use data.get(), .shift(1), .fillna()
- Place code between START/END markers
```

#### 2.3 改進效果

| 指標 | Phase 1 | Phase 1.1 | 改善 |
|------|---------|-----------|------|
| CoT步驟數 | 5 | 4 | -20% |
| 框架提及次數 | 0 | 3 | +300% |
| APPENDIX引導 | 0 | 1 | New |
| Token消耗 | ~500 | ~200 | -60% |

---

### 3. Prompt結構重組

#### 3.1 Phase 1結構 (有問題)

```
1. System Prompt (CoT抽象)      ~500 tokens
2. Task Header                   ~100 tokens
3. Champion Context              ~200 tokens
4. Innovation Directive          ~100 tokens
5. Constraints (含160欄位)      ~1,500 tokens ← 問題
6. Failure Patterns              ~200 tokens
7. Creation Example              ~300 tokens
8. Output Format (有sim範例)    ~200 tokens  ← 被忽略
---
Total: ~3,800 tokens
```

**問題**: 輸出格式在最後，LLM讀到時注意力已被消耗

#### 3.2 Phase 1.1結構 (Golden Template)

```
1. Golden Template              ~300 tokens ← 第1位
2. Simplified CoT               ~200 tokens ← 框架導向
3. Task Header                  ~100 tokens
4. Champion Context             ~200 tokens
5. Innovation Directive         ~100 tokens
6. Failure Patterns             ~200 tokens
7. APPENDIX:
   - 160 Fields                ~1,500 tokens ← 需要時查閱
   - API Documentation          ~800 tokens
   - Validation Helper          ~300 tokens
---
Total: ~3,700 tokens (相近)
前500 tokens: Golden Template + CoT (核心指令)
```

**改進**: 核心指令在前，參考資料在後

---

## 實作規格

### 4. 程式碼變更清單

#### 4.1 新增方法 (3個)

**Method 1: `_build_golden_template()`**
```python
def _build_golden_template(self) -> str:
    """
    Build Golden Template section with immutable code structure.

    Requirements:
    - CRITICAL RULE header
    - Complete template with START/END markers
    - Backtest execution section marked as immutable
    - Clear instructions for filling

    Returns:
        str: Golden Template section (~300 tokens)
    """
```

**Method 2: `_build_simplified_cot()`**
```python
def _build_simplified_cot(self) -> str:
    """
    Build simplified CoT guidance focused on template filling.

    Requirements:
    - 4 concrete steps (understand → identify → plan → implement)
    - References to APPENDIX
    - Template-first approach

    Returns:
        str: Simplified CoT section (~200 tokens)
    """
```

**Method 3: `_build_appendix()`**
```python
def _build_appendix(self) -> str:
    """
    Build APPENDIX section with reference materials.

    Consolidates:
    - 160-field catalog (from _build_field_catalog)
    - API documentation (from _build_api_documentation)
    - Validation helpers (from _build_validation_helpers)

    Returns:
        str: Complete APPENDIX section (~2,600 tokens)
    """
```

#### 4.2 修改方法 (1個)

**Method 4: `build_creation_prompt()` - 組合順序**
```python
def build_creation_prompt(...) -> str:
    """Phase 1.1 version with new structure."""

    # NEW ORDER
    prompt_parts = [
        self._build_golden_template(),      # PART 1: Framework FIRST
        self._build_simplified_cot(),       # PART 2: How to use
        self._get_creation_header(),        # PART 3: Task
        self._format_champion_inspiration(champion_approach),
        self._format_innovation_directive(innovation_directive),
        self._format_failure_avoidance(...),
        self._build_appendix(),             # PART 4: Reference LAST
    ]

    prompt = "\n\n".join(prompt_parts)
    return self._truncate_to_budget(prompt)
```

#### 4.3 需要複用的現有方法

- `_build_field_catalog()` - 160欄位列表 (已存在)
- `_build_api_documentation()` - API使用說明 (已存在)
- `_build_validation_helpers()` - 驗證函數 (已存在)
- `_format_champion_inspiration()` - 冠軍靈感 (已存在)
- `_format_failure_avoidance()` - 失敗模式 (已存在)

---

## 測試規格

### 5. 三層驗證策略

#### 5.1 Tier1: 結構化驗證 (Linter Test)

**目標**: 快速檢查程式碼結構，無需回測
**工具**: `tools/validate_structure.py`
**測試**: 10次生成
**閾值**: >90% 結構合格

**檢查項目**:
```python
checks = {
    'has_strategy_def': 'def strategy(' in code,
    'has_report_assignment': 'report = sim(' in code,
    'has_return_statement': 'return position' in code,
    'compiles_successfully': True,  # compile(code, ...)
    'no_lookahead_bias': '.shift(-' not in code
}
score = sum(checks.values()) / len(checks)
```

**決策**:
- ≥90%: 進入Tier2
- <90%: 診斷Golden Template設計 → 調整 → 重試

#### 5.2 Tier2: 金絲雀測試 (Canary Test)

**目標**: 小樣本端到端測試
**測試**: 3案例 × 3次 = 9次測試
**閾值**: >60% 整體成功率

**測試案例**:
```yaml
simple:
  description: "5日20日移動平均交叉動量策略"
  complexity: low
  expected_success: >80%

medium:
  description: "ROE+營收成長+價格動量組合策略"
  complexity: medium
  expected_success: >60%

complex:
  description: "產業別動態權重sector rotation策略"
  complexity: high
  expected_success: >40%
```

**決策**:
- Overall >60%: 進入完整測試
- <60%: 診斷CoT/APPENDIX → 調整 → 重試

#### 5.3 Tier3: 完整測試 (Full Test)

**目標**: 驗證Phase 1.1整體效果
**測試**: 20次迭代 × 3模式
**閾值**: LLM Only >60%

**對比分析**:
- vs Baseline (20%)
- vs Phase 1 (0%)
- vs Phase 1.1目標 (60%+)

---

## 單元測試規格

### 6. 測試案例

**File**: `tests/test_prompt_builder_phase11.py`

```python
class TestPhase11GoldenTemplate:
    """Phase 1.1 Golden Template implementation tests."""

    def test_golden_template_structure(self):
        """Golden Template has CRITICAL RULE + START/END + sim()."""
        template = builder._build_golden_template()
        assert "CRITICAL" in template
        assert "START" in template and "END" in template
        assert "report = sim(" in template

    def test_simplified_cot_steps(self):
        """Simplified CoT has 4 steps and references APPENDIX."""
        cot = builder._build_simplified_cot()
        assert "Step 1" in cot and "Step 4" in cot
        assert "APPENDIX" in cot

    def test_creation_prompt_order(self):
        """Prompt has correct order: Template < CoT < Appendix."""
        prompt = builder.build_creation_prompt(champion_approach="Momentum")
        template_pos = prompt.find("CRITICAL RULE")
        cot_pos = prompt.find("Chain of Thought")
        appendix_pos = prompt.find("APPENDIX")
        assert template_pos < cot_pos < appendix_pos

    def test_appendix_preserves_phase1_content(self):
        """APPENDIX contains all Phase 1 reference materials."""
        appendix = builder._build_appendix()
        assert "price:收盤價" in appendix  # Field catalog
        assert "data.get(" in appendix     # API docs
        assert "validate" in appendix.lower()  # Helpers
```

---

## 預期效果與風險

### 7. 量化預期

| 指標 | Phase 1 | Phase 1.1預期 | 改善 | 信心 |
|------|---------|---------------|------|------|
| 結構合格率 | 0% | >90% | +90pp | 95% |
| report缺失錯誤 | 78% | <10% | -68pp | 95% |
| LLM Only成功率 | 0% | 60%+ | +60pp | 85% |
| 金絲雀整體 | - | >60% | - | 85% |
| 策略多樣性 | - | >0.6 | - | 75% |

### 8. 風險管理

**已緩解風險**:
- ✅ START/END標記混淆 → 視覺分隔線
- ✅ Template範例複製 → 步驟指引無code
- ✅ 過度約束創意 → 僅約束結構
- ✅ 環境變數依賴 → 註釋說明

**剩餘不確定性** (需實測):
- ⚠️ APPENDIX查閱率 (75%信心)
- ⚠️ START/END實際效果 (85%信心)
- ⚠️ 創意多樣性維持 (75%信心)

**回退策略**:
- Tier1<90%: 調整Golden Template語氣/標記
- Tier2<60%: 調整CoT步驟或嵌入Top 20欄位
- 完整<40%: Phase 1.2替代策略 (two-stage generation)

---

## 實作時程

### 9. MVP開發計畫 (3小時)

**Hour 1-2: 編碼與測試**
```
T+0:00  新增 _build_golden_template() (30min)
T+0:30  新增 _build_simplified_cot() (20min)
T+0:50  新增 _build_appendix() (20min)
T+1:10  修改 build_creation_prompt() (20min)
T+1:30  編寫單元測試 (20min)
T+1:50  本地驗證與除錯 (10min)
```

**Hour 3: 快速驗證**
```
T+2:00  建立 validate_structure.py (15min)
T+2:15  Tier1: 10次生成 + 結構驗證 (10min)
T+2:25  分析Tier1結果 (5min)
T+2:30  Tier2: 9次金絲雀測試 (20min)
T+2:50  分析Tier2結果 (10min)
T+3:00  決策點: 進入完整測試 或 調整
```

---

## 成功標準

### 10. 階段性目標

**MVP成功標準**:
- ✅ Tier1結構驗證 >90%
- ✅ Tier2金絲雀測試 >60%
- ✅ 3小時內完成MVP開發與驗證

**Phase 1.1成功標準**:
- ✅ LLM Only成功率 >60% (20次迭代)
- ✅ vs Baseline改善 +40pp
- ✅ vs Phase 1改善 +60pp
- ✅ 策略多樣性維持 >0.6

**最終目標** (Phase 1原始):
- 🎯 LLM Only成功率 >55%
- 🎯 Field errors <15% of failures

---

## 附錄

### A. 參考文獻

1. Phase 1測試報告: `experiments/llm_learning_validation/results/phase1_*`
2. Gemini 2.5 Pro專家分析: zen:chat conversation 2025-11-21
3. 深度思考分析: zen:thinkdeep analysis (6 steps, confidence: certain)
4. Baseline結果: LLM Only 20% (4/20), 2025-11-20

### B. 詞彙表

- **Golden Template**: 不可變的程式碼框架，LLM只能填充指定區域
- **START/END Markers**: 視覺化標記，明確指示LLM的填充區域
- **Tier1/Tier2/Tier3**: 三層驗證策略 (結構/金絲雀/完整)
- **APPENDIX**: 參考資料區，包含160欄位、API文檔、驗證函數

### C. 變更歷史

| 版本 | 日期 | 變更 | 作者 |
|------|------|------|------|
| 1.0 | 2025-11-21 | 初版規格 | Claude + 深度思考分析 |

---

**文檔狀態**: ✅ 審查就緒
**下一步**: B→更新專案文檔→C→A
