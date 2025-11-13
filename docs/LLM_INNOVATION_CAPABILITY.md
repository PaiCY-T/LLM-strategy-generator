# LLM創新能力分析：因子與出場策略自動生成

**Date**: 2025-10-20
**Status**: 設計文檔
**Target**: Phase 2+ Enhancement

---

## 問題定義

### 用戶核心問題

**Q1**: 目前系統是否能讓LLM創造**全新的**進場因子或出場策略？
- 例如：PDF中提到的新因子（目前因子池不存在）
- 例如：5MA停損機制（目前出場機制不存在）

**Q2**: 是否有機制**鼓勵和記錄**LLM的創新？
- 如何保存成功的創新因子/策略？
- 如何避免重複探索相同的創新？
- 如何建立"創新知識庫"供未來參考？

### 答案總結

**當前狀況**: ❌ **目前系統無此能力**

**技術可行性**: ✅ **完全可行，但需額外設計**

**實施複雜度**: 🟡 **中等（需要強化validation）**

---

## 第一部分：現有系統能力邊界分析

### 1.1 進場因子池：固定的因子集合

**當前限制**（`src/templates/factor_template.py`）:

```python
# 固定的因子類型
PARAM_GRID = {
    'factor_type': ['pe_ratio', 'pb_ratio', 'roe', 'roa', 'revenue_growth', 'margin'],
    # ↑ 只有這6種因子，無法新增
}
```

**Prompt Template限制**（`prompt_template_v3_comprehensive.txt`）:

```text
### 5. Fundamental Features
- fundamental_features:ROE稅後 (ROE after tax)
- fundamental_features:ROA稅後息前 (ROA)
- fundamental_features:營業利益率 (Operating Margin)
...
↑ 列出固定的數據源，LLM被限制在這個範圍內
```

**結論**:
- ❌ LLM **無法創造新因子**（如：ROE × Revenue Growth / P/E的組合因子）
- ✅ LLM **可以組合現有因子**（weighted combination）
- ❌ LLM **無法引入外部因子**（如：PDF中提到的新因子）

---

### 1.2 出場策略：參數變異 vs. 機制創新

**Phase 1實施內容**（`src/mutation/exit_mutator.py`）:

```python
class ExitStrategyMutator:
    """
    實施三種變異類型：
    1. Parametric (80%): 改變參數值
       stop_atr_mult: 2.0 → 2.5
    2. Structural (15%): 添加/移除現有機制
       stop_exit | profit_exit → stop_exit | profit_exit | time_exit
    3. Relational (5%): 改變比較運算符
       close < stop_level → close <= stop_level
    """
```

**當前機制池**（Phase 0驗證）:
1. ATR Trailing Stop-Loss: `stop_level = highest_high - (atr * stop_atr_mult)`
2. Fixed Profit Target: `profit_target = entry_price + (atr * profit_atr_mult)`
3. Time-Based Exit: `time_exit = holding_days >= max_hold_days`

**結論**:
- ✅ 可以**調整參數**：stop_atr_mult從2.0變成3.0
- ✅ 可以**組合機制**：同時使用stop+profit+time
- ❌ **無法創造新機制**：如"5MA停損"、"RSI overbought出場"等

**用戶舉例**："5MA停損"機制

```python
# 這是全新的出場機制（目前系統無法自動生成）
sma5 = close.rolling(5).mean()
exit_signal = close < sma5  # 跌破5日均線即出場
```

---

### 1.3 Iteration Engine：Prompt-based策略生成

**當前運作方式**（`artifacts/working/modules/iteration_engine.py`）:

```python
# LLM通過prompt template生成策略
PROMPT_TEMPLATE_PATH = "prompt_template_v3_comprehensive.txt"

# Prompt內容（結構化限制）:
"""
Your code MUST follow this structure:
1. Load data using data.get() or data.indicator()
2. Calculate factors with .shift(1) to avoid look-ahead
3. Combine factors
4. Apply filters
5. Select stocks using is_largest() or is_smallest()
"""
```

**結論**:
- ✅ LLM **可以生成完整策略**（但限制在template範圍內）
- ✅ LLM **可以組合現有數據源**（creative combinations）
- ❌ LLM **無法突破prompt限制**（受結構化要求約束）
- ❌ LLM **無explicit instruction創新**（沒有被鼓勵創新）

---

## 第二部分：技術可行性分析

### 2.1 LLM創新能力：完全可行

**核心能力**:
1. **Code Generation**: LLM可以生成任意Python代碼
2. **Domain Knowledge**: Claude/GPT-4理解金融概念（MA, RSI, factor investing）
3. **Creativity**: 能夠組合概念創造新策略（如：結合5MA + ATR + Volume）

**技術路徑**:

```python
# 方案A: 擴展Prompt Template（低風險）
"""
## Innovation Encouraged

You may CREATE NEW factors by combining existing data sources:
- Example: momentum_value = (price.pct_change(20) / pe_ratio).rank()
- Example: quality_growth = (roe * revenue_growth_rate).rank()

You may CREATE NEW exit mechanisms:
- Example: MA crossover exit (close < sma5)
- Example: RSI-based exit (rsi > 70)
- Example: Volume spike exit (volume > volume.rolling(20).mean() * 2)

Your innovation will be VALIDATED and PRESERVED if successful.
"""

# 方案B: 專門的創新模式（中風險）
def generate_innovative_strategy(llm, innovation_type):
    if innovation_type == 'new_factor':
        prompt = "Create a novel factor combining momentum, value, and quality..."
    elif innovation_type == 'new_exit':
        prompt = "Design an exit mechanism using technical indicators..."

    code = llm.generate(prompt)
    validated_code = validate_innovation(code)
    return validated_code

# 方案C: 演化式創新（高風險，高回報）
def evolutionary_innovation(population):
    # 讓LLM觀察高績效策略，提取pattern
    successful_patterns = extract_patterns(population.top_10_percent())

    # 要求LLM基於pattern創新
    prompt = f"Based on these successful patterns: {successful_patterns}, create a new variation..."
    innovative_code = llm.generate(prompt)

    return innovative_code
```

---

### 2.2 關鍵挑戰：Validation Framework

**挑戰1: 幻覺生成（Hallucination）**

LLM可能生成**語法正確但語義錯誤**的代碼：

```python
# 錯誤範例1: 未來資訊洩漏（Look-ahead Bias）
future_return = close.shift(-5).pct_change(5)  # ❌ 使用未來資料
signal = future_return > 0.1  # ❌ 這是作弊，不是策略

# 錯誤範例2: 不合理的因子
nonsense_factor = (roe * volume) / pb_ratio  # ❌ 語法正確但無意義

# 錯誤範例3: 不可執行的邏輯
exit_signal = (close > sma5) & (close < sma5)  # ❌ 邏輯矛盾
```

**解決方案**: **多層Validation**

```python
class InnovationValidator:
    """驗證LLM生成的創新策略"""

    def validate(self, code: str) -> ValidationResult:
        # Level 1: 語法檢查
        syntax_ok = self.check_syntax(code)

        # Level 2: 語義檢查
        semantic_ok = self.check_semantics(code)
        # - 檢查look-ahead bias（所有shift必須≥1）
        # - 檢查數據對齊（DataFrame shape一致）
        # - 檢查邏輯矛盾（and/or條件）

        # Level 3: 執行檢查
        execution_ok = self.check_execution(code)
        # - Sandbox執行
        # - 檢查runtime errors
        # - 檢查NaN/Inf處理

        # Level 4: 績效檢查
        performance_ok = self.check_performance(code)
        # - Sharpe > 0.3（基本閾值）
        # - Max Drawdown < 50%
        # - 交易頻率合理（不是每天交易）

        # Level 5: 創新度檢查
        novelty_ok = self.check_novelty(code)
        # - 與現有策略的相似度 < 80%
        # - 包含至少1個新的組合/機制

        return ValidationResult(all_ok=all([
            syntax_ok, semantic_ok, execution_ok,
            performance_ok, novelty_ok
        ]))
```

---

**挑戰2: 過度擬合（Overfitting）**

LLM可能生成**歷史數據上表現完美但無法泛化**的策略：

```python
# 危險範例：過度複雜的條件
signal = (
    (rsi > 30) & (rsi < 70) &
    (macd > 0.05) & (macd < 0.15) &
    (volume > volume.rolling(20).mean() * 1.8) &
    (volume < volume.rolling(20).mean() * 2.2) &
    (close > sma5) & (close < sma20) &
    ...  # 30個條件
)
# ↑ 完美擬合歷史，未來失效
```

**解決方案**: **Out-of-Sample Testing**

```python
def validate_generalization(code: str) -> bool:
    """驗證策略泛化能力"""

    # 1. In-Sample Testing (2018-2022)
    in_sample_sharpe = backtest(code, period='2018-2022')

    # 2. Out-of-Sample Testing (2023-2024)
    out_sample_sharpe = backtest(code, period='2023-2024')

    # 3. 檢查泛化能力
    generalization_ratio = out_sample_sharpe / in_sample_sharpe

    # 要求: OOS績效至少達到IS的70%
    return generalization_ratio >= 0.7
```

---

## 第三部分：創新記錄與知識管理

### 3.1 創新知識庫設計

**目標**: 保存和追蹤LLM的成功創新

**數據結構**:

```python
# innovations.jsonl (append-only log)
{
    "innovation_id": "innov_20251020_001",
    "type": "new_exit_mechanism",
    "name": "5MA_Stop_Loss",
    "description": "Exit when price drops below 5-day moving average",
    "code_snippet": "sma5 = close.rolling(5).mean()\nexit_signal = close < sma5",
    "creator": "claude-sonnet-4",
    "timestamp": "2025-10-20T15:30:00",
    "discovery_iteration": 127,
    "validation_results": {
        "syntax": "PASS",
        "semantic": "PASS",
        "execution": "PASS",
        "in_sample_sharpe": 1.45,
        "out_sample_sharpe": 1.12,
        "generalization_ratio": 0.77
    },
    "adoption_count": 5,  # 被其他策略採用次數
    "performance_rank": "top_10_percent",
    "tags": ["technical_indicator", "exit_strategy", "moving_average"]
}
```

**知識庫功能**:

```python
class InnovationRepository:
    """創新知識庫"""

    def save_innovation(self, innovation: Innovation):
        """保存新創新"""
        # 1. 檢查重複性
        if self.is_duplicate(innovation):
            logger.info(f"Innovation {innovation.name} already exists")
            return

        # 2. 附加metadata
        innovation.tags = self.auto_tag(innovation)
        innovation.similarity_vector = self.compute_embedding(innovation.code)

        # 3. 寫入JSONL
        with open('innovations.jsonl', 'a') as f:
            f.write(json.dumps(innovation.to_dict()) + '\n')

    def search_similar(self, code: str, threshold: float = 0.8) -> List[Innovation]:
        """搜尋相似創新（避免重複探索）"""
        query_embedding = self.compute_embedding(code)

        similar = []
        for innovation in self.load_all():
            similarity = cosine_similarity(query_embedding, innovation.similarity_vector)
            if similarity > threshold:
                similar.append(innovation)

        return similar

    def get_successful_patterns(self, top_n: int = 10) -> List[Innovation]:
        """獲取最成功的創新（供LLM學習）"""
        innovations = self.load_all()
        innovations.sort(key=lambda x: x.validation_results['in_sample_sharpe'], reverse=True)
        return innovations[:top_n]
```

---

### 3.2 創新回饋迴圈

**設計目標**: 讓LLM從成功創新中學習

```python
def generate_next_iteration_with_innovation_context(iteration: int):
    """整合創新知識庫的策略生成"""

    # 1. 獲取當前最成功的創新
    repo = InnovationRepository()
    top_innovations = repo.get_successful_patterns(top_n=5)

    # 2. 構建prompt context
    innovation_context = ""
    for innov in top_innovations:
        innovation_context += f"""
        成功創新案例：{innov.name}
        - 描述：{innov.description}
        - 代碼：{innov.code_snippet}
        - 績效：Sharpe {innov.validation_results['in_sample_sharpe']:.2f}
        """

    # 3. 增強prompt
    enhanced_prompt = f"""
    {base_prompt}

    ## 過往成功的創新案例
    {innovation_context}

    ## 創新鼓勵
    你可以：
    1. 借鑒上述成功案例的思路
    2. 創造新的因子組合或出場機制
    3. 嘗試未探索的技術指標組合

    你的創新將被驗證，若成功將永久保存供未來參考。
    """

    # 4. 生成策略
    new_strategy = llm.generate(enhanced_prompt)

    return new_strategy
```

---

## 第四部分：實施方案建議

### 4.1 Phase 2: 創新能力MVP（最小可行產品）

**目標**: 在現有系統基礎上，增加基本創新能力

**工作項目**:

| Task | Description | Effort | Priority |
|------|-------------|--------|----------|
| 2.1 | 擴展Prompt Template鼓勵創新 | 2 days | P0 |
| 2.2 | 實施InnovationValidator（5-layer） | 5 days | P0 |
| 2.3 | 建立InnovationRepository（JSONL-based） | 3 days | P0 |
| 2.4 | 整合創新context到iteration loop | 2 days | P0 |
| 2.5 | 20-iteration smoke test with innovation | 1 day | P0 |

**預期成果**:
- ✅ LLM可以創造新的因子組合（如：ROE × Revenue Growth）
- ✅ LLM可以創造新的出場機制（如：5MA停損）
- ✅ 創新被自動驗證和保存
- ✅ 成功創新可供未來參考

---

### 4.2 Phase 3: 演化式創新（Advanced）

**目標**: 讓LLM主動探索創新空間

**工作項目**:

| Task | Description | Effort | Priority |
|------|-------------|--------|----------|
| 3.1 | 實施Pattern Extraction（從top策略提取pattern） | 5 days | P1 |
| 3.2 | 創新多樣性機制（diversity reward） | 3 days | P1 |
| 3.3 | 演化樹追蹤（innovation lineage） | 3 days | P2 |
| 3.4 | 自適應創新探索（adaptive exploration rate） | 4 days | P2 |

**預期成果**:
- ✅ LLM主動識別高績效pattern
- ✅ 鼓勵多樣性探索（避免局部最優）
- ✅ 追蹤創新演化路徑（哪些創新來自哪些先驅）
- ✅ 根據績效動態調整創新頻率

---

## 第五部分：風險評估與緩解

### 5.1 技術風險

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| LLM幻覺生成無效策略 | High | Medium | 5-layer validation + sandbox execution |
| 過度擬合歷史數據 | High | High | Out-of-sample testing (70% threshold) |
| 創新過於激進導致虧損 | Medium | Medium | 績效閾值（Sharpe >0.3, MDD <50%） |
| 創新知識庫爆炸增長 | Low | High | 定期清理低績效創新（bottom 20%） |

### 5.2 績效風險

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 創新策略績效不如baseline | Medium | Medium | 保留fallback機制（Phase 0 templates） |
| 創新探索浪費計算資源 | Low | High | 設定創新頻率上限（20% iterations） |
| 創新策略過於複雜難以維護 | Medium | Low | 複雜度限制（max 100 lines code） |

---

## 第六部分：結論與建議

### 答案總結

**Q1: 目前系統是否能讓LLM創造全新因子/出場策略？**

❌ **當前系統無此能力**
- 進場因子池固定（pe_ratio, roe等6種）
- 出場機制固定（ATR stop, profit target, time exit）
- Prompt template限制了創新空間

✅ **技術上完全可行**
- LLM具備code generation能力
- 只需擴展prompt + 強化validation
- 預估2週可完成MVP

**Q2: 是否有機制記錄和鼓勵創新？**

❌ **當前無此機制**

✅ **可以設計實施**
- InnovationRepository（JSONL-based）
- 創新回饋迴圈（learning from success）
- 演化樹追蹤（innovation lineage）

---

### 實施建議

**短期（2週）: Phase 2 MVP**
1. 擴展prompt template鼓勵創新
2. 實施5-layer validation framework
3. 建立基本InnovationRepository
4. 運行20-iteration smoke test

**預期成果**: LLM可創造並驗證新因子/出場策略

**中期（1個月）: Phase 3 演化式創新**
1. Pattern extraction from top performers
2. Diversity rewards for exploration
3. Adaptive innovation rate based on performance

**預期成果**: 自主探索創新空間，持續改進策略庫

---

### 範例：5MA停損機制的生成流程

**用戶需求**: "我想用5MA作為停損點"

**實施路徑**:

```python
# Step 1: LLM生成創新代碼
prompt = """
用戶要求：使用5日移動平均線作為停損機制

請生成出場邏輯代碼：
- 當價格跌破5MA時出場
- 確保沒有look-ahead bias
- 整合進現有position tracking邏輯
"""

generated_code = llm.generate(prompt)
# Output:
"""
# 計算5日移動平均
sma5 = close.rolling(5).mean().shift(1)  # shift(1)避免look-ahead

# 出場信號：價格跌破5MA
exit_signal = close < sma5

# 修改position（從持有變為離場）
modified_positions = positions & ~exit_signal
"""

# Step 2: Validation
validator = InnovationValidator()
result = validator.validate(generated_code)
# ✅ Syntax: PASS
# ✅ Semantic: PASS (no look-ahead, logical)
# ✅ Execution: PASS
# ✅ Performance: Sharpe 1.23 (in-sample), 0.95 (out-sample)
# ✅ Novelty: NEW (not in existing repository)

# Step 3: Save to Repository
if result.success:
    innovation = Innovation(
        name="5MA_Stop_Loss",
        type="exit_mechanism",
        code=generated_code,
        validation=result
    )
    repo.save_innovation(innovation)
    logger.info("✅ 5MA停損機制已保存到創新知識庫")

# Step 4: Future Reference
# 未來iteration可以參考這個成功案例：
top_exits = repo.get_successful_patterns(type='exit_mechanism')
# Returns: [5MA_Stop_Loss, ATR_Trailing, RSI_Overbought_Exit, ...]
```

---

**Last Updated**: 2025-10-20
**Author**: Claude Code SuperClaude
**Status**: 設計文檔（待實施）
**Related Docs**:
- `EXIT_MUTATION_AST_DESIGN.md` (Phase 1)
- `PHASE0_PHASE1_COMPLETE_SUMMARY.md` (Current status)
