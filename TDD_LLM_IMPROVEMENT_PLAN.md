# TDD Implementation Plan: LLM Success Rate Improvement (20% → 80%)

**Project**: LLM Strategy Generator - Prompt Engineering Enhancement
**Goal**: Increase LLM-only mode success rate from 20% to 80%+ through TDD
**Baseline**: Post-fix validation test (2025-11-20)
**Duration**: 4 phases, ~2-3 days total

---

## Executive Summary

### Current State
- ✅ Hybrid: 70% success (target met)
- ❌ LLM Only: 20% success (60pp below 80% target)
- ✅ Factor Graph: 90% baseline

### Root Causes (16 failures analyzed)
1. **Field Name Hallucination** (50%, 8 failures) - LLM invents non-existent fields
2. **Code Structure Errors** (18.8%, 3 failures) - Missing `report` variable
3. **Invalid Metrics** (18.8%, 3 failures) - NaN/Inf Sharpe ratios
4. **API Misunderstanding** (12.4%, 2 failures) - Incorrect data object usage

### TDD Approach
Each phase follows **Red-Green-Refactor** cycle with validation:
- 🔴 **RED**: Write failing test demonstrating the issue
- 🟢 **GREEN**: Implement minimal fix to pass test
- 🔵 **REFACTOR**: Improve while keeping tests green
- ✅ **VALIDATE**: Run 20-iteration test to measure improvement

---

## Phase 1: Field Name Validation System

**Target**: 20% → 50% (+30pp)
**Impact**: Eliminates 50% of current failures
**Duration**: 4-6 hours
**Risk**: Low

### TDD Cycle 1.1: Field Catalog Creation

#### 🔴 RED - Create Failing Test

**File**: `tests/test_prompt_field_validation.py`

```python
import pytest
import re
from src.innovation.prompt_builder import PromptBuilder, VALID_FINLAB_FIELDS

def test_prompt_contains_complete_field_catalog():
    """Ensure prompt includes comprehensive FinLab field catalog"""
    builder = PromptBuilder()
    prompt = builder.build_creation_prompt("test feedback")

    # Verify all major field categories are documented
    assert "price:收盤價" in prompt
    assert "price:成交股數" in prompt  # Fixed field
    assert "fundamental_features:ROE" in prompt
    assert "financial_statement:現金" in prompt

    # Verify warning about invalid fields
    assert "ONLY use fields from" in prompt or "僅使用以上欄位" in prompt

def test_llm_generated_code_uses_valid_fields():
    """Integration test: LLM should only use valid fields"""
    # This will fail initially with 50% error rate
    results = run_test_iterations(mode="llm_only", iterations=10)

    field_errors = [r for r in results if "not exists" in r.error_message]
    field_error_rate = len(field_errors) / len(results)

    assert field_error_rate < 0.15, f"Field error rate too high: {field_error_rate:.1%}"
```

**Expected**: ❌ Tests fail - field catalog incomplete, error rate ~50%

#### 🟢 GREEN - Implement Solution

**File**: `src/innovation/prompt_builder.py`

**Step 1: Define Field Catalog Constant**

```python
# Add after imports, before class definition
VALID_FINLAB_FIELDS = {
    "price": [
        "price:收盤價",  # Closing price
        "price:開盤價",  # Opening price
        "price:最高價",  # High price
        "price:最低價",  # Low price
        "price:成交股數",  # Trading volume (FIXED - was 成交量)
        "price:成交金額",  # Trading value
        "price:漲跌幅",   # Price change %
    ],
    "fundamental_features": [
        "fundamental_features:ROE稅後",
        "fundamental_features:ROA綜合損益",
        "fundamental_features:營業利益率",
        "fundamental_features:稅後淨利率",
        "fundamental_features:每股盈餘",
        "fundamental_features:股東權益報酬率",
        "fundamental_features:資產報酬率",
        "fundamental_features:負債比率",
        "fundamental_features:流動比率",
        "fundamental_features:速動比率",
        # ... (add all 50+ fundamental fields)
    ],
    "price_earning_ratio": [
        "price_earning_ratio:股價淨值比",
        "price_earning_ratio:本益比",
        "price_earning_ratio:殖利率",
    ],
    "etl": [
        "etl:adj_close",
        "etl:market_value",
    ],
    "financial_statement": [
        "financial_statement:現金及約當現金",
        "financial_statement:應收帳款及票據",
        "financial_statement:存貨",
        # ... (add all financial statement fields)
    ]
}

# Helper function to get flat list
def get_all_valid_fields() -> list[str]:
    """Returns flat list of all valid FinLab field names"""
    fields = []
    for category_fields in VALID_FINLAB_FIELDS.values():
        fields.extend(category_fields)
    return fields
```

**Step 2: Update Prompt Template**

```python
def _build_api_documentation_section(self) -> str:
    """Build comprehensive API documentation with field catalog"""

    doc = """
## FinLab Data API 完整欄位目錄

**重要警告**: 僅使用以下列出的欄位。使用不存在的欄位會導致策略失敗。

### 價格數據 (Price Data)
使用方式: `data.get('price:欄位名')`

"""
    # Add price fields with examples
    for field in VALID_FINLAB_FIELDS["price"]:
        doc += f"- `{field}`\n"

    doc += """
**範例**:
```python
close = data.get('price:收盤價')  # 收盤價
volume = data.get('price:成交股數')  # 成交股數 (注意:不是成交量)
```

### 基本面數據 (Fundamental Features)
使用方式: `data.get('fundamental_features:欄位名')`

"""
    for field in VALID_FINLAB_FIELDS["fundamental_features"][:20]:  # First 20
        doc += f"- `{field}`\n"

    doc += "\n... (共50+個基本面欄位)\n\n"

    # Add other categories similarly

    doc += """
### ⚠️ 重要提醒
1. **僅使用上述欄位** - 不要臆造或猜測欄位名稱
2. **使用 .shift(1)** - 避免look-ahead bias
3. **檢查欄位存在性** - 使用前確認欄位有效
"""

    return doc
```

**Step 3: Integrate into Prompt**

```python
def build_creation_prompt(self, feedback: str) -> str:
    """Build strategy creation prompt with comprehensive field catalog"""

    prompt_parts = [
        self._build_task_description(),
        self._build_api_documentation_section(),  # NEW: Comprehensive field catalog
        self._build_code_requirements(),
        self._build_few_shot_examples(),
        f"\n## 任務\n{feedback}\n",
    ]

    return "\n\n".join(prompt_parts)
```

**Expected**: ✅ Tests pass - field catalog complete, error rate <15%

#### 🔵 REFACTOR - Improve Implementation

**Improvements**:
1. Extract field catalog to separate JSON file for maintainability
2. Add field category grouping for better organization
3. Include field descriptions and usage notes
4. Add validation helper in backtest executor

**File**: `src/innovation/field_catalog.json`

```json
{
  "categories": {
    "price": {
      "description": "即時價格數據",
      "prefix": "price:",
      "fields": [
        {"name": "收盤價", "full": "price:收盤價", "desc": "每日收盤價"},
        {"name": "成交股數", "full": "price:成交股數", "desc": "成交量(股數)", "note": "注意:不是成交量"}
      ]
    }
  }
}
```

**File**: `src/backtest/field_validator.py` (NEW)

```python
class FieldValidator:
    """Validates field names in generated strategy code"""

    def __init__(self):
        self.valid_fields = get_all_valid_fields()

    def extract_field_references(self, code: str) -> list[str]:
        """Extract all data.get() calls from code"""
        pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"
        return re.findall(pattern, code)

    def validate_fields(self, code: str) -> tuple[bool, list[str]]:
        """Returns (is_valid, invalid_fields)"""
        used_fields = self.extract_field_references(code)
        invalid = [f for f in used_fields if f not in self.valid_fields]
        return (len(invalid) == 0, invalid)
```

#### ✅ VALIDATE - Measure Improvement

**Test Command**:
```bash
python3 run_20iteration_test.py --mode llm_only
```

**Success Criteria**:
- LLM success rate: 35-50% (current: 20%)
- Field error rate: <15% (current: 50%)
- Hybrid mode: ≥70% (must not regress)

**Expected Results**:
```
LLM Only: 45% success (9/20) ✅ +25pp improvement
  Field errors: 10% (2/20) ✅ Major reduction
  Code structure errors: 15% (3/20) ⚠️ Still present
  Other errors: 30% (6/20) ⚠️ Still present
```

**Rollback Criteria**:
- If LLM <30% OR Hybrid <65%: Revert changes and retry

---

## Phase 2: Code Structure Enforcement

**Target**: 50% → 65% (+15pp)
**Impact**: Eliminates 18.8% of failures
**Duration**: 3-4 hours
**Risk**: Low

### TDD Cycle 2.1: Report Variable Requirement

#### 🔴 RED - Create Failing Test

**File**: `tests/test_code_structure_validation.py`

```python
def test_generated_code_creates_report_variable():
    """Ensure all generated code assigns sim() result to 'report'"""
    code = generate_strategy_with_llm()

    # Check for report assignment
    assert "report = sim(" in code, "Missing report variable assignment"

    # Verify it's not just in comments
    code_without_comments = remove_comments(code)
    assert "report = sim(" in code_without_comments

def test_code_structure_matches_template():
    """Verify generated code follows required structure"""
    code = generate_strategy_with_llm()

    required_elements = [
        "def strategy(data):",
        "position = ",
        "position.fillna(False)",
        "return position",
        "position = strategy(data)",
        "report = sim(",
    ]

    for element in required_elements:
        assert element in code, f"Missing required element: {element}"
```

**Expected**: ❌ Fails with ~18.8% error rate

#### 🟢 GREEN - Implement Solution

**Step 1: Add Code Structure Template**

```python
CODE_STRUCTURE_TEMPLATE = """
## 程式碼結構要求

**必須包含以下結構** (缺少任何部分將導致執行失敗):

1. **策略函數定義**:
```python
def strategy(data):
    # 策略邏輯
    return position
```

2. **執行回測** (必須完整包含):
```python
# 執行策略
position = strategy(data)
position = position.loc[start_date:end_date]

# 執行模擬 - 必須賦值給 report 變數
report = sim(
    position,
    fee_ratio=fee_ratio,
    tax_ratio=tax_ratio,
    resample="M"
)
```

**常見錯誤**:
❌ `sim(position, ...)` - 缺少 report 賦值
✅ `report = sim(position, ...)` - 正確

❌ 忘記 `position.fillna(False)`
✅ `position = position.fillna(False)`
"""
```

**Step 2: Add Structure Validation**

```python
class CodeStructureValidator:
    """Validates generated code structure"""

    REQUIRED_PATTERNS = [
        (r"def\s+strategy\s*\(", "Missing strategy function definition"),
        (r"return\s+position", "Strategy must return position"),
        (r"position\s*=\s*strategy\(data\)", "Missing strategy execution"),
        (r"report\s*=\s*sim\(", "Missing report = sim() assignment"),
        (r"\.fillna\(False\)", "Missing fillna(False) for position"),
    ]

    def validate(self, code: str) -> tuple[bool, list[str]]:
        """Returns (is_valid, missing_elements)"""
        errors = []
        for pattern, error_msg in self.REQUIRED_PATTERNS:
            if not re.search(pattern, code):
                errors.append(error_msg)
        return (len(errors) == 0, errors)
```

**Step 3: Enhance Few-Shot Examples**

```python
def _build_few_shot_examples(self) -> str:
    """Enhanced examples with structure highlighting"""

    example = """
## 範例策略

```python
def strategy(data):
    '''動能策略範例'''
    close = data.get('price:收盤價')

    # 計算20日報酬率
    returns_20d = (close / close.shift(20) - 1).shift(1)

    # 選擇前30%股票
    position = returns_20d > returns_20d.quantile(0.7, axis=1)
    position = position.fillna(False)  # ✅ 必須: 處理 NaN

    return position  # ✅ 必須: 返回 position

# ✅ 必須: 執行策略
position = strategy(data)
position = position.loc[start_date:end_date]

# ✅ 必須: 賦值給 report 變數
report = sim(
    position,
    fee_ratio=fee_ratio,
    tax_ratio=tax_ratio,
    resample="M"
)
```

**關鍵點**:
1. ✅ `report = sim(...)` - 必須賦值
2. ✅ `position.fillna(False)` - 處理 NaN
3. ✅ `return position` - 函數必須返回
"""
    return example
```

#### 🔵 REFACTOR - Add Pre-execution Validation

**File**: `src/backtest/executor.py`

```python
def _validate_code_structure(self, code: str) -> tuple[bool, str]:
    """Validate code structure before execution"""
    validator = CodeStructureValidator()
    is_valid, errors = validator.validate(code)

    if not is_valid:
        error_msg = "Code structure validation failed:\n" + "\n".join(f"- {e}" for e in errors)
        return False, error_msg

    return True, ""

def execute_strategy(self, code: str) -> ExecutionResult:
    """Execute strategy with pre-validation"""

    # Pre-execution validation
    is_valid, error_msg = self._validate_code_structure(code)
    if not is_valid:
        return ExecutionResult(
            success=False,
            error_type="StructureValidationError",
            error_message=error_msg
        )

    # Proceed with execution
    return self._execute_in_process(code)
```

#### ✅ VALIDATE - Measure Improvement

**Success Criteria**:
- LLM success rate: 60-65% (previous: 45%)
- Code structure errors: <5% (previous: 18.8%)

**Expected Results**:
```
LLM Only: 62% success (12-13/20) ✅ +17pp from Phase 1
  Field errors: 10% ✅ Maintained
  Code structure errors: 3% ✅ Major reduction
  Invalid metrics: 15% ⚠️ Still present
  Other errors: 10% ⚠️ Still present
```

---

## Phase 3: API Documentation Enhancement

**Target**: 65% → 75% (+10pp)
**Impact**: Reduces API misunderstanding errors
**Duration**: 2-3 hours
**Risk**: Medium

### TDD Cycle 3.1: API Usage Clarification

#### 🔴 RED - Test

```python
def test_no_data_stocks_attribute():
    """Ensure generated code doesn't use non-existent data.stocks"""
    code = generate_strategy_with_llm()

    # Check for common API misuses
    assert "data.stocks" not in code, "data.stocks does not exist"
    assert "len(data.stocks)" not in code

    # Suggest correct alternatives
    if "data.stocks" in code:
        print("Use len(close.columns) or position.shape[1] instead")
```

#### 🟢 GREEN - Solution

**Add API Clarification Section**:

```python
API_CLARIFICATION = """
## FinLab Data API 使用說明

### 數據對象結構

`data` 對象是 FinLab 的數據容器，使用 `.get()` 方法獲取數據:

```python
# ✅ 正確用法
close = data.get('price:收盤價')  # 返回 DataFrame
volume = data.get('price:成交股數')

# 獲取股票數量
num_stocks = len(close.columns)  # ✅ 正確
num_stocks = close.shape[1]      # ✅ 正確

# ❌ 錯誤用法
num_stocks = len(data.stocks)    # data.stocks 不存在!
```

### 常見錯誤與修正

| 錯誤寫法 | 正確寫法 | 說明 |
|---------|---------|------|
| `len(data.stocks)` | `len(close.columns)` | 獲取股票數量 |
| `data.stocks * 0.3` | `position.shape[1] * 0.3` | 計算百分比 |
| `close not exists` | 檢查拼寫: `price:收盤價` | 使用正確欄位名 |
"""
```

#### ✅ VALIDATE

**Success Criteria**: LLM 70-75%, API errors <3%

---

## Phase 4: Metric Validation & Edge Cases

**Target**: 75% → 85% (+10pp)
**Impact**: Handles NaN/Inf metrics
**Duration**: 2-3 hours
**Risk**: Low

### TDD Cycle 4.1: Metric Validation

#### 🔴 RED - Test

```python
def test_generated_strategy_produces_valid_sharpe():
    """Ensure strategy produces valid Sharpe ratio"""
    results = run_test_iterations(mode="llm_only", iterations=10)

    for result in results:
        if result.success:
            assert result.sharpe_ratio is not None
            assert not math.isnan(result.sharpe_ratio)
            assert not math.isinf(result.sharpe_ratio)
            assert -5 < result.sharpe_ratio < 10  # Reasonable range
```

#### 🟢 GREEN - Solution

**Add Edge Case Handling Guidance**:

```python
EDGE_CASE_GUIDANCE = """
## 邊緣案例處理

### 避免無效指標

**問題**: 策略可能產生 NaN 或 Inf 的 Sharpe ratio

**解決方案**:

```python
# 1. 確保有足夠的交易信號
min_stocks = 5
position_count = position.sum(axis=1)
position = position[position_count >= min_stocks]

# 2. 處理 NaN 值
position = position.fillna(False)

# 3. 避免空倉
if position.sum().sum() == 0:
    # 添加基本動能作為後備
    returns_20d = (close / close.shift(20) - 1).shift(1)
    position = returns_20d > 0
```

### 流動性過濾

```python
# 確保選擇流動性充足的股票
trading_value = data.get('price:成交金額')
avg_value_20d = trading_value.rolling(20).mean().shift(1)
liquidity_filter = avg_value_20d > 50_000_000  # 50M TWD

# 結合到position
position = position & liquidity_filter
```
"""
```

#### ✅ VALIDATE

**Success Criteria**: LLM 80-85%, invalid metric errors <3%

---

## Test Execution & Validation

### Test Commands

```bash
# Run single phase test (20 iterations)
python3 run_20iteration_test.py --mode llm_only

# Run full validation (60 iterations, all modes)
python3 run_20iteration_three_mode_test.py

# Monitor progress
./monitor_test.sh
```

### Success Criteria Matrix

| Phase | LLM Target | Field Errors | Structure Errors | API Errors | Metric Errors |
|-------|-----------|--------------|------------------|------------|---------------|
| Baseline | 20% | 50% | 18.8% | 6.2% | 18.8% |
| Phase 1 | 45% | <15% | 18.8% | 6.2% | 18.8% |
| Phase 2 | 62% | <15% | <5% | 6.2% | 18.8% |
| Phase 3 | 72% | <15% | <5% | <3% | 18.8% |
| Phase 4 | 82% | <15% | <5% | <3% | <5% |

### Rollback Triggers

- LLM success rate decreases by >5pp
- Hybrid success rate drops below 65%
- Factor Graph success rate drops below 85%

---

## Implementation Timeline

### Day 1
- **Morning** (3-4h): Phase 1 - Field Catalog
  - Write tests
  - Implement field catalog
  - Run validation
- **Afternoon** (3-4h): Phase 2 - Code Structure
  - Write structure tests
  - Add validation
  - Run validation

### Day 2
- **Morning** (2-3h): Phase 3 - API Documentation
  - Clarify API usage
  - Add examples
  - Run validation
- **Afternoon** (2-3h): Phase 4 - Metric Validation
  - Add edge case handling
  - Final validation
  - Document results

### Day 3 (Buffer)
- Fix any regressions
- Fine-tune based on results
- Final comprehensive test

---

## Risk Management

### Identified Risks

1. **Token Limit Exceeded** (Low)
   - Mitigation: Monitor prompt length, compress if needed
   - Current: ~15K tokens, limit: 100K

2. **Hybrid Mode Regression** (Medium)
   - Mitigation: Test after each phase, rollback if <65%
   - Monitoring: Continuous validation

3. **Unexpected Error Patterns** (Medium)
   - Mitigation: Analyze failures after each phase
   - Adjustment: Add new tests as needed

4. **LLM Behavior Change** (Low)
   - Mitigation: Pin Gemini model version
   - Testing: Consistent test environment

### Contingency Plans

**If Phase 1 < 35%**:
- Simplify field catalog
- Add more prominent warnings
- Enhance few-shot examples

**If Phase 2 < 55%**:
- Add explicit structure template
- Implement pre-execution validation
- Provide structure checklist

**If Final < 75%**:
- Iterate on problematic areas
- Add more few-shot examples
- Consider prompt restructuring

---

## Measurement & Metrics

### Primary Metrics

1. **LLM Success Rate**: (successful_iterations / total_iterations)
2. **Error Rate by Type**: Track each error category
3. **Sharpe Quality**: Average Sharpe of successful strategies

### Secondary Metrics

1. **Prompt Token Usage**: Monitor prompt length
2. **Execution Time**: LLM generation + backtest time
3. **Consistency**: Success rate variance across runs

### Reporting Template

```
Phase X Validation Results
==========================
LLM Success Rate: XX/20 (XX%)
  - Change from previous: +XXpp
  - Target: XXX%
  - Status: ✅/❌

Error Breakdown:
  - Field errors: X (XX%)
  - Structure errors: X (XX%)
  - API errors: X (XX%)
  - Metric errors: X (XX%)

Regression Check:
  - Hybrid: XX/20 (XX%) - ✅ No regression
  - Factor Graph: XX/20 (XX%) - ✅ No regression

Next Steps: [Continue to Phase X+1 / Rollback / Iterate]
```

---

## Appendix A: Complete Test Suite

```python
# tests/test_llm_improvement.py

class TestPhase1FieldValidation:
    def test_field_catalog_completeness(self):
        """All major field categories are documented"""
        pass

    def test_llm_uses_valid_fields_only(self):
        """LLM generated code uses only valid fields"""
        pass

class TestPhase2CodeStructure:
    def test_report_variable_exists(self):
        """Generated code creates report variable"""
        pass

    def test_structure_validation(self):
        """Code follows required structure"""
        pass

class TestPhase3APIUsage:
    def test_no_invalid_api_calls(self):
        """No use of non-existent data attributes"""
        pass

class TestPhase4MetricValidation:
    def test_valid_sharpe_ratios(self):
        """Strategies produce valid Sharpe ratios"""
        pass

    def test_edge_case_handling(self):
        """Strategies handle edge cases properly"""
        pass
```

---

## Appendix B: Reference Documents

1. **POST_FIX_VALIDATION_SUMMARY.md** - Baseline test results
2. **src/innovation/prompt_builder.py** - Prompt engineering code
3. **experiments/llm_learning_validation/results/** - Test result data
4. **tests/** - Test suite

---

## Success Definition

**Project succeeds when**:
- ✅ LLM success rate ≥ 80%
- ✅ Hybrid success rate ≥ 70% (maintained)
- ✅ Factor Graph ≥ 85% (maintained)
- ✅ All error types < 5%
- ✅ Average Sharpe quality maintained or improved

**Documentation Delivery**:
- ✅ TDD test suite committed
- ✅ Updated prompt_builder.py with comprehensive docs
- ✅ Validation results documented
- ✅ Lessons learned documented

---

**Document Version**: 1.0
**Created**: 2025-11-20
**Owner**: LLM Strategy Generator Team
**Status**: Ready for Implementation
