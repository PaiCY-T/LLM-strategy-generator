# JSON Parameter Output Architecture - Design Document

## Overview

重構 LLM 策略生成系統，從直接生成代碼改為輸出結構化 JSON 參數。此架構變更將 LLM 的職責從「代碼生成者」轉變為「參數選擇專家」，由中介層負責代碼生成，從而消除大部分 PreservationValidator 失敗。

**核心理念**: LLM 只做參數決策，代碼生成完全由模板系統控制。

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Autonomous Loop (現有)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐    ┌────────────────────┐    ┌──────────────┐ │
│  │PromptBuilder    │───>│ LLM (Gemini/GPT)   │───>│JSON Response │ │
│  │(JSON-only mode) │    │ 輸出 JSON 參數      │    │              │ │
│  └─────────────────┘    └────────────────────┘    └──────┬───────┘ │
│                                                          │         │
│                                                          ▼         │
│                         ┌─────────────────────────────────────────┐│
│                         │    TemplateCodeGenerator (NEW)          ││
│                         │    ┌─────────────────────────────────┐  ││
│                         │    │ 1. JSON 解析 (extract JSON)      │  ││
│                         │    │ 2. Pydantic 驗證                 │  ││
│                         │    │ 3. 模板注入 (parameter injection)│  ││
│                         │    │ 4. 代碼生成                      │  ││
│                         │    └─────────────────────────────────┘  ││
│                         └───────────────┬─────────────────────────┘│
│                                         │                          │
│                    ┌────────────────────┴────────────────────┐     │
│                    │                                         │     │
│                    ▼                                         ▼     │
│        ┌─────────────────────┐              ┌──────────────────────┐
│        │ ValidationError    │              │ Generated Code      │
│        │ (結構化錯誤反饋)     │              │ (保證結構正確)        │
│        └─────────────────────┘              └──────────────────────┘
│                    │                                               │
│                    ▼                                               │
│        ┌─────────────────────┐                                     │
│        │ Retry with Feedback │                                     │
│        └─────────────────────┘                                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### C1: MomentumStrategyParams (Pydantic Schema)

**檔案位置**: `src/schemas/strategy_params.py`

```python
from pydantic import BaseModel, Field, model_validator
from typing import Literal

class MomentumStrategyParams(BaseModel):
    """Pydantic schema for Momentum strategy parameters."""

    # Momentum calculation
    momentum_period: Literal[5, 10, 20, 30] = Field(
        description="Momentum lookback period in days"
    )

    # Trend confirmation
    ma_periods: Literal[20, 60, 90, 120] = Field(
        description="Moving average period for trend confirmation"
    )

    # Catalyst type
    catalyst_type: Literal["revenue", "earnings"] = Field(
        description="Fundamental catalyst type"
    )

    # Catalyst detection
    catalyst_lookback: Literal[2, 3, 4, 6] = Field(
        description="Catalyst lookback window in months"
    )

    # Portfolio construction
    n_stocks: Literal[5, 10, 15, 20] = Field(
        description="Number of stocks in portfolio"
    )

    # Risk management
    stop_loss: Literal[0.08, 0.10, 0.12, 0.15] = Field(
        description="Stop loss percentage"
    )

    # Rebalancing
    resample: Literal["W", "M"] = Field(
        description="Rebalancing frequency (Weekly/Monthly)"
    )

    resample_offset: Literal[0, 1, 2, 3, 4] = Field(
        description="Rebalancing day offset"
    )

    @model_validator(mode='after')
    def validate_parameter_consistency(self) -> 'MomentumStrategyParams':
        """Cross-parameter validation for logical consistency."""
        # resample_offset only meaningful for weekly rebalancing
        if self.resample == "M" and self.resample_offset > 0:
            # Monthly rebalancing ignores offset, but allow it (no error)
            pass

        # momentum_period should be shorter than ma_periods for trend following
        if self.momentum_period > self.ma_periods:
            raise ValueError(
                f"momentum_period ({self.momentum_period}) should be <= ma_periods ({self.ma_periods}) "
                "for proper trend confirmation"
            )
        return self
```

### C2: StrategyParamRequest (LLM Output Schema)

**檔案位置**: `src/schemas/strategy_params.py`

```python
class StrategyParamRequest(BaseModel):
    """Schema for LLM JSON output format."""

    reasoning: str = Field(
        min_length=50,
        max_length=500,
        description="Explanation for parameter choices"
    )

    params: MomentumStrategyParams = Field(
        description="Strategy parameters"
    )
```

### C3: TemplateCodeGenerator (中介層)

**檔案位置**: `src/generators/template_code_generator.py`

**Interface**:
```python
class TemplateCodeGenerator:
    """Generates strategy code from validated JSON parameters."""

    def __init__(self, template: BaseTemplate):
        """Initialize with strategy template."""

    def generate(self, llm_output: str) -> GenerationResult:
        """
        Parse LLM output, validate parameters, generate code.

        Args:
            llm_output: Raw LLM response (may contain markdown)

        Returns:
            GenerationResult with either code or structured errors
        """

    def _extract_json(self, raw_output: str) -> str:
        """Extract JSON from LLM output (handles markdown blocks)."""

    def _validate_params(self, json_str: str) -> StrategyParamRequest:
        """Validate JSON against Pydantic schema."""

    def _inject_params(self, params: MomentumStrategyParams) -> str:
        """Inject validated params into template code."""
```

**GenerationResult**:
```python
@dataclass
class GenerationResult:
    """Result of code generation attempt."""
    success: bool
    code: Optional[str] = None
    params: Optional[MomentumStrategyParams] = None
    errors: List[ValidationError] = field(default_factory=list)

    def get_feedback_prompt(self) -> str:
        """Generate LLM-friendly error feedback for retry."""
```

### C4: StructuredErrorFeedback

**檔案位置**: `src/feedback/structured_error.py`

**Interface**:
```python
@dataclass
class ValidationErrorDetail:
    """Single validation error with context."""
    field_path: str           # e.g., "params.momentum_period"
    error_type: str           # "invalid_value", "missing_field", "type_error"
    given_value: Any          # What LLM provided
    allowed_values: List[Any] # Valid options
    suggestion: str           # Human-readable fix suggestion

class StructuredErrorFeedback:
    """Generates LLM-friendly error feedback."""

    def format_errors(self, errors: List[ValidationErrorDetail]) -> str:
        """Format errors as retry prompt."""

    def integrate_with_prompt(
        self,
        original_prompt: str,
        errors: List[ValidationErrorDetail]
    ) -> str:
        """Add error feedback to next LLM prompt."""
```

## Data Models

### JSON Output Format (LLM → System)

```json
{
  "reasoning": "選擇 20 天動量週期配合 60 天均線，因為中期趨勢更穩定。收入催化劑在台股較可靠。15 支股票平衡分散與集中。10% 停損適合動量策略波動性。",
  "params": {
    "momentum_period": 20,
    "ma_periods": 60,
    "catalyst_type": "revenue",
    "catalyst_lookback": 3,
    "n_stocks": 15,
    "stop_loss": 0.10,
    "resample": "W",
    "resample_offset": 0
  }
}
```

### Error Feedback Format (System → LLM)

```
## VALIDATION ERRORS (Please Fix)

1. **params.momentum_period**: Invalid value
   - Given: 25
   - Allowed: [5, 10, 20, 30]
   - Suggestion: Use 20 (closest valid value)

2. **params.stop_loss**: Type error
   - Given: "10%"
   - Expected: float
   - Allowed: [0.08, 0.10, 0.12, 0.15]
   - Suggestion: Use 0.10 instead of "10%"

Please output corrected JSON with valid values.
```

## Error Handling

### Error Types and Recovery

| Error Type | Detection | Recovery Strategy |
|------------|-----------|-------------------|
| JSON Parse Error | `json.JSONDecodeError` | Extract from markdown, retry with format hint |
| Missing Field | Pydantic `validation_error` | Report missing field, provide default suggestion |
| Invalid Value | Pydantic `literal_error` | Show allowed values, suggest closest valid |
| Type Error | Pydantic `type_error` | Show expected type with example |
| Reasoning Too Short | Pydantic `string_too_short` | Request more detailed explanation |

### Retry Logic

```python
MAX_RETRIES = 3

for attempt in range(MAX_RETRIES):
    result = generator.generate(llm_output)

    if result.success:
        return result.code

    # Build retry prompt with structured feedback
    retry_prompt = result.get_feedback_prompt()
    llm_output = llm_client.generate(retry_prompt)

# All retries failed
raise GenerationFailedError(result.errors)
```

## Testing Strategy

### TDD Test Categories

**Unit Tests** (`tests/unit/test_strategy_params.py`):
- Schema validation for all valid parameter combinations
- Schema rejection for invalid values
- JSON Schema export correctness

**Unit Tests** (`tests/unit/test_template_code_generator.py`):
- JSON extraction from various markdown formats
- Parameter injection correctness
- Error collection and formatting

**Unit Tests** (`tests/unit/test_structured_error.py`):
- Error message formatting
- Prompt integration
- Multi-error handling

**Integration Tests** (`tests/integration/test_json_parameter_flow.py`):
- End-to-end JSON → Code generation
- Retry with feedback loop
- Integration with existing AutonomousLoop

### Test Coverage Targets

| Component | Coverage Target |
|-----------|-----------------|
| MomentumStrategyParams | 100% (all valid/invalid combinations) |
| TemplateCodeGenerator | ≥95% |
| StructuredErrorFeedback | ≥90% |
| Integration flow | ≥85% |

## Integration with Existing System

### 與現有組件的兼容性

1. **TemplateParameterGenerator**:
   - 現有 `_build_prompt()` 將改為輸出 JSON-only prompt
   - 現有 `generate_parameters()` 調用 TemplateCodeGenerator

2. **AutonomousLoop**:
   - 無需修改，TemplateCodeGenerator 輸出與現有格式兼容

3. **PreservationValidator**:
   - 保留作為備用驗證層
   - JSON 模式下預期 ~50% 失敗率降低

4. **MomentumTemplate**:
   - 現有 `PARAM_GRID` 作為 Pydantic schema 來源
   - 現有 `generate_code()` 由 TemplateCodeGenerator 調用

### 漸進式遷移計劃

1. **Phase 1**: 實現 Pydantic schema 和 TemplateCodeGenerator
2. **Phase 2**: 修改 TemplateParameterGenerator 使用 JSON-only prompt
3. **Phase 3**: 整合結構化錯誤反饋
4. **Phase 4**: 驗證並調整 retry 邏輯

## Future Improvements (Phase 2)

根據專家審計建議，以下改進項目將在 MVP 驗證後進行：

### 1. Jinja2 模板引擎
當前使用簡單字串注入，未來可升級為 Jinja2 以支援：
- 條件邏輯 (`{% if catalyst_type == 'earnings' %}`)
- 迴圈和過濾器
- 更複雜的策略模板

### 2. 多策略擴展架構
設計 discriminated union 支援多種策略類型：
```python
class StrategyParamRequest(BaseModel):
    strategy_type: Literal["momentum", "mean_reversion", "volatility"]
    parameters: Union[MomentumParams, MeanReversionParams, VolatilityParams]
```

### 3. Reasoning 分離
將 reasoning 從 JSON 中分離以減少解析風險：
```
REASONING:
選擇參數的理由...

JSON:
{"params": {...}}
```

### 4. 更多跨參數驗證
根據實際使用經驗增加 `@model_validator` 規則
