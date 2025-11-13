# Design Document - Phase 3: Data Integrity & Type Safety

## 1. Overview

### 1.1 Design Philosophy
本設計採用**三階段漸進式改善** (Three-Phase Progressive Enhancement) 策略，在不同層次提升數據完整性與類型安全：
1. **Phase 3.1 (Type Consistency - P0)**: 統一數據類型，消除 Dict/StrategyMetrics 混用
2. **Phase 3.2 (Schema Validation - P1)**: 運行時數據驗證，防止異常值傳播
3. **Phase 3.3 (Code Pre-Validation - P2, Optional)**: LLM代碼預檢查，降低執行失敗率

### 1.2 Key Design Decisions

**Decision 1: StrategyMetrics Dataclass Over Dict[str, float]**
- **Rationale**: 類型安全、IDE支持、自我文檔化
- **Benefits**:
  - 編譯時類型檢查 (mypy)
  - IDE自動補全與錯誤提示
  - 清晰的數據契約定義
- **Trade-off**: 需要向後兼容性支持 (通過 to_dict()/from_dict() 實現)
- **Implementation**: ✅ Already completed (TC1.1-1.5)

**Decision 2: Pydantic for Schema Validation**
- **Rationale**: 工業標準、性能優異、自我文檔化
- **Benefits**:
  - 運行時驗證 + 清晰錯誤訊息
  - 數據範圍約束 (Sharpe [-10, 10], Drawdown [-1, 0])
  - 與 FastAPI 等框架兼容（未來擴展）
- **Trade-off**: 新增依賴 (pydantic 2.x)，驗證開銷 <1ms (可接受)

**Decision 3: Conditional AST-based Code Validation (Phase 3.3)**
- **Rationale**: 僅在錯誤率 >20% 時實施，避免過度工程化
- **Decision Gate**: Phase 1+2 測試後決定是否實施
- **Implementation Strategy**: 如果需要，採用 ast 模組而非正則表達式

---

## 2. Architecture

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                 LLM Strategy Generation System               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Type Consistency (Phase 3.1) ✅ COMPLETE          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  StrategyMetrics Dataclass (src/backtest/metrics.py)   │ │
│  │  - sharpe_ratio: Optional[float]                       │ │
│  │  - total_return: Optional[float]                       │ │
│  │  - max_drawdown: Optional[float]                       │ │
│  │  - to_dict() -> Dict[str, Any]         (TC-1.1) ✅     │ │
│  │  - from_dict(data) -> StrategyMetrics  (TC-1.2) ✅     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  Integration Points ✅ COMPLETE                         │ │
│  │  - FeedbackGenerator.generate_feedback()    (TC-1.3) ✅│ │
│  │  - ChampionTracker.update_champion()        (TC-1.4) ✅│ │
│  │  - IterationExecutor._extract_metrics()     (TC-1.5) ✅│ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: Schema Validation (Phase 3.2) 🚧 PENDING          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ExecutionResultSchema (Pydantic Model)                 │ │
│  │  - sharpe_ratio: Field(ge=-10, le=10)                  │ │
│  │  - total_return: Field(ge=-1, le=10)                   │ │
│  │  - max_drawdown: Field(le=0)                           │ │
│  │  - Validator: Check NaN/Inf values                     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  StrategyMetricsSchema (Pydantic Model)                 │ │
│  │  - Strict type checking                                │ │
│  │  - Range validation                                    │ │
│  │  - Custom validators for edge cases                    │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  Integration Point                                      │ │
│  │  - BacktestExecutor.execute() → validate before return │ │
│  │  - Log ValidationError with field/value/constraint     │ │
│  │  - Return ExecutionResult(success=False) on failure    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Code Pre-Validation (Phase 3.3) ⏳ OPTIONAL       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  StrategyCodeValidator (AST-based)                      │ │
│  │  - Syntax error detection                              │ │
│  │  - Look-ahead bias detection (.shift(-1))              │ │
│  │  - API misuse detection (.rank() without axis)         │ │
│  │  - Required elements check (strategy/position/report)  │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │  Integration Point                                      │ │
│  │  - StructuredInnovator → validate before execution     │ │
│  │  - Log validation errors, attempt 1 retry              │ │
│  │  - Provide validation feedback to LLM                  │ │
│  └────────────────────────────────────────────────────────┘ │
│  Decision Gate: Implement ONLY if Phase 1+2 error rate >20%│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Diagram

```
┌────────────┐
│  LLM API   │ (Phase 3.3 - Optional)
└────┬───────┘
     │ Generated Code
     ▼
┌─────────────────────────┐
│ StrategyCodeValidator   │ (AST check: syntax, bias, API)
│ - Syntax errors?        │
│ - Look-ahead bias?      │
│ - API misuse?           │
└────┬────────────────────┘
     │ Validated Code
     ▼
┌─────────────────────────┐
│ BacktestExecutor        │
│ - Execute strategy      │
│ - Extract metrics       │
└────┬────────────────────┘
     │ Raw Metrics
     ▼
┌─────────────────────────┐
│ ExecutionResultSchema   │ (Phase 3.2 - Pydantic)
│ - Validate sharpe [-10,10]
│ - Validate drawdown ≤0  │
│ - Validate return [-1,10]
└────┬────────────────────┘
     │ Validated Metrics
     ▼
┌─────────────────────────┐
│ StrategyMetrics         │ (Phase 3.1 ✅)
│ - Type-safe dataclass   │
│ - to_dict()/from_dict() │
└────┬────────────────────┘
     │
     ├──────────────────────────────────┐
     │                                  │
     ▼                                  ▼
┌──────────────────┐          ┌──────────────────┐
│ ChampionTracker  │          │ FeedbackGenerator│
│ update_champion()│          │ generate_feedback()
└──────────────────┘          └──────────────────┘
```

---

## 3. Component Design

### 3.1 Phase 3.1: Type Consistency ✅ COMPLETE

#### 3.1.1 StrategyMetrics Dataclass

**Location**: `src/backtest/metrics.py`

**Interface**:
```python
@dataclass
class StrategyMetrics:
    sharpe_ratio: Optional[float] = None
    total_return: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    execution_success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization"""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyMetrics':
        """Create from dict for backward compatibility"""
```

**Design Decisions**:
- ✅ Optional fields for graceful handling of missing metrics
- ✅ `execution_success` flag to distinguish valid vs invalid metrics
- ✅ `to_dict()`/`from_dict()` for backward compatibility with JSONL history
- ✅ `__post_init__` validates NaN → None conversion

**Status**: ✅ Implemented and tested

#### 3.1.2 Integration Points

**FeedbackGenerator** (TC-1.3 ✅):
```python
def generate_feedback(
    self,
    iteration_num: int,
    metrics: Optional[StrategyMetrics],  # ✅ Type-safe
    execution_result: Dict[str, Any],
    classification_level: Optional[str],
    error_msg: Optional[str] = None
) -> str:
    # Backward compatibility conversion
    if metrics is not None and isinstance(metrics, dict):
        metrics = StrategyMetrics.from_dict(metrics)
```

**ChampionTracker** (TC-1.4 ✅):
```python
def update_champion(
    self,
    iteration_num: int,
    code: Optional[str],
    metrics: Union[StrategyMetrics, Dict[str, float]],  # ✅ Accepts both
    **kwargs: Any
) -> bool:
    # Backward compatibility conversion
    if isinstance(metrics, dict):
        metrics = StrategyMetrics.from_dict(metrics)
```

**IterationExecutor** (TC-1.5 ✅):
```python
def _extract_metrics(self, execution_result: ExecutionResult) -> StrategyMetrics:
    """Extract performance metrics from execution result."""
    return StrategyMetrics(
        sharpe_ratio=execution_result.sharpe_ratio,
        total_return=execution_result.total_return,
        max_drawdown=execution_result.max_drawdown,
        execution_success=True
    )
```

---

### 3.2 Phase 3.2: Schema Validation 🚧 PENDING

#### 3.2.1 ExecutionResultSchema

**Location**: `src/validation/schemas.py` (new file)

**Interface**:
```python
from pydantic import BaseModel, Field, field_validator

class ExecutionResultSchema(BaseModel):
    """Pydantic schema for validating ExecutionResult metrics."""

    sharpe_ratio: Optional[float] = Field(
        None,
        ge=-10.0,
        le=10.0,
        description="Sharpe ratio must be in range [-10, 10]"
    )

    total_return: Optional[float] = Field(
        None,
        ge=-1.0,
        le=10.0,
        description="Total return must be in range [-1, 10] (100% loss to 1000% gain)"
    )

    max_drawdown: Optional[float] = Field(
        None,
        le=0.0,
        description="Max drawdown must be non-positive (≤0)"
    )

    execution_success: bool = Field(
        default=False,
        description="Whether execution succeeded"
    )

    @field_validator('sharpe_ratio', 'total_return', 'max_drawdown')
    @classmethod
    def validate_no_nan_inf(cls, v: Optional[float]) -> Optional[float]:
        """Reject NaN/Inf values"""
        if v is not None:
            if np.isnan(v) or np.isinf(v):
                raise ValueError(f"Invalid value: {v} (NaN or Inf not allowed)")
        return v
```

**Design Decisions**:
- ✅ Pydantic 2.x for performance and features
- ✅ Reasonable ranges based on Taiwan market characteristics
- ✅ Custom validators for NaN/Inf edge cases
- ✅ Clear error messages with field names and constraints

#### 3.2.2 Integration into BacktestExecutor

**Location**: `src/backtest/executor.py`

**Modified Method**:
```python
def execute(self, strategy_code: str) -> ExecutionResult:
    """Execute strategy with schema validation."""
    try:
        # ... existing execution logic ...

        # Extract metrics
        raw_metrics = self._extract_metrics_from_report(report)

        # Validate metrics using Pydantic schema
        try:
            validated_metrics = ExecutionResultSchema(
                sharpe_ratio=raw_metrics.get('sharpe_ratio'),
                total_return=raw_metrics.get('total_return'),
                max_drawdown=raw_metrics.get('max_drawdown'),
                execution_success=True
            )

            return ExecutionResult(
                success=True,
                sharpe_ratio=validated_metrics.sharpe_ratio,
                total_return=validated_metrics.total_return,
                max_drawdown=validated_metrics.max_drawdown,
                execution_time=elapsed_time
            )

        except ValidationError as e:
            logger.error(
                f"Metrics validation failed: {e}\n"
                f"Field: {e.errors()[0]['loc']}\n"
                f"Value: {e.errors()[0]['input']}\n"
                f"Constraint: {e.errors()[0]['msg']}"
            )
            return ExecutionResult(
                success=False,
                error_type="ValidationError",
                error_message=str(e),
                execution_time=elapsed_time
            )

    except Exception as e:
        # ... existing error handling ...
```

**Design Decisions**:
- ✅ Validation happens BEFORE creating ExecutionResult
- ✅ ValidationError logged with full context (field, value, constraint)
- ✅ Failed validation returns `success=False` instead of crashing
- ✅ Performance overhead <1ms (Pydantic is highly optimized)

---

### 3.3 Phase 3.3: Code Pre-Validation ⏳ OPTIONAL

**Decision Gate**: Implement ONLY if Phase 1+2 show LLM error rate >20%

#### 3.3.1 StrategyCodeValidator

**Location**: `src/validation/code_validator.py` (new file)

**Interface**:
```python
import ast
from typing import List, Tuple

class ValidationError:
    """Code validation error with location and message."""
    category: str  # "syntax" | "look_ahead_bias" | "api_misuse"
    message: str
    line_number: Optional[int]
    severity: str  # "error" | "warning"

class StrategyCodeValidator:
    """AST-based code validation for LLM-generated strategies."""

    def validate(self, code: str) -> Tuple[bool, List[ValidationError]]:
        """Validate strategy code.

        Returns:
            (is_valid, errors)
        """
        errors = []

        # 1. Syntax validation
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            errors.append(ValidationError(
                category="syntax",
                message=f"Syntax error: {e.msg}",
                line_number=e.lineno,
                severity="error"
            ))
            return False, errors

        # 2. Look-ahead bias detection
        errors.extend(self._check_look_ahead_bias(tree))

        # 3. API misuse detection
        errors.extend(self._check_api_misuse(tree))

        # 4. Required elements check
        errors.extend(self._check_required_elements(tree))

        # Is valid if no errors (warnings are OK)
        is_valid = not any(e.severity == "error" for e in errors)

        return is_valid, errors

    def _check_look_ahead_bias(self, tree: ast.AST) -> List[ValidationError]:
        """Detect .shift(-1) patterns (future data leakage)."""

    def _check_api_misuse(self, tree: ast.AST) -> List[ValidationError]:
        """Detect common Pandas API misuse (e.g., .rank() without axis)."""

    def _check_required_elements(self, tree: ast.AST) -> List[ValidationError]:
        """Check for required variables: strategy, position, report."""
```

**Design Decisions**:
- ✅ AST-based (precise) rather than regex-based (fragile)
- ✅ <10ms validation overhead (AST parsing is fast)
- ✅ Distinguish errors (blocking) vs warnings (informational)
- ✅ Line numbers for debugging

#### 3.3.2 Integration into StructuredInnovator

**Location**: `src/innovation/structured_innovator.py`

**Modified Method**:
```python
def generate_strategy(self, feedback: str) -> Tuple[str, bool]:
    """Generate strategy with code validation."""

    # ... LLM generation logic ...

    # Validate generated code (Phase 3.3)
    validator = StrategyCodeValidator()
    is_valid, errors = validator.validate(generated_code)

    if not is_valid:
        logger.warning(
            f"Generated code failed validation:\n"
            f"{self._format_validation_errors(errors)}"
        )

        # Retry once with validation feedback
        retry_prompt = self._build_retry_prompt(feedback, errors)
        generated_code = self._call_llm(retry_prompt)

        # Re-validate
        is_valid, retry_errors = validator.validate(generated_code)
        if not is_valid:
            logger.error("Code still invalid after retry, using fallback")
            return self._fallback_strategy(), False

    return generated_code, True
```

**Design Decisions**:
- ✅ Validation happens BEFORE execution (fast fail)
- ✅ 1 retry with validation errors as LLM feedback
- ✅ Fallback to Factor Graph if retries fail
- ✅ All validation results logged for LLM training data

---

## 4. Performance Considerations

### 4.1 Performance Targets

| Component | Target Overhead | Actual (Measured) | Status |
|-----------|----------------|-------------------|--------|
| Type conversion (to_dict/from_dict) | <0.1ms | TBD | ✅ Negligible |
| Pydantic validation | <1ms | TBD | 🚧 To measure |
| AST code validation | <10ms | TBD | ⏳ To measure (if implemented) |
| Total iteration overhead | <5% | TBD | 🚧 To validate |

### 4.2 Optimization Strategies

**Phase 3.2 Optimization**:
- ✅ Pydantic 2.x uses Rust-based core (10-50x faster than v1)
- ✅ Validation only on success path (failures already slow)
- ✅ Schema compiled once, reused for all validations

**Phase 3.3 Optimization**:
- ✅ AST parsing is one-time cost per generation
- ✅ Validation runs in parallel with other pre-processing
- ✅ Caching parse trees for retry scenarios

---

## 5. Error Handling Strategy

### 5.1 Graceful Degradation

```
┌─────────────────────────┐
│ Validation Layer        │
└────┬────────────────────┘
     │ ValidationError
     ▼
┌─────────────────────────┐
│ Log Error               │ (field, value, constraint)
│ + Set success=False     │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ System Continues        │ (no crash, process next iteration)
└─────────────────────────┘
```

### 5.2 Error Logging Format

```python
logger.error(
    f"Schema validation failed:\n"
    f"  Field: {field_name}\n"
    f"  Value: {actual_value}\n"
    f"  Constraint: {constraint_message}\n"
    f"  Iteration: {iteration_num}"
)
```

**Benefits**:
- ✅ Clear debugging information
- ✅ No sensitive data leakage
- ✅ Structured for log analysis

---

## 6. Testing Strategy

### 6.1 Phase 3.1 Testing ✅ COMPLETE

- ✅ Unit tests for to_dict()/from_dict()
- ✅ Backward compatibility tests (JSONL loading)
- ✅ Integration tests with FeedbackGenerator/ChampionTracker
- ✅ Type checking with mypy (0 errors)

### 6.2 Phase 3.2 Testing 🚧 PENDING

**Test Categories**:
1. **Schema Validation Tests** (15+ tests)
   - Valid metrics pass validation
   - Out-of-range metrics fail (Sharpe >10, Drawdown >0)
   - NaN/Inf values fail
   - Clear error messages

2. **Integration Tests**
   - BacktestExecutor validation integration
   - Error logging verification
   - Performance benchmarks (<1ms)

3. **Edge Cases**
   - Extreme valid values (Sharpe = 9.99, Drawdown = -0.9999)
   - Zero values (Sharpe = 0, Return = 0)
   - None values (optional fields)

### 6.3 Phase 3.3 Testing ⏳ CONDITIONAL

**Decision Gate**: Implement ONLY if error rate >20%

**Test Categories** (if implemented):
1. **Code Validation Tests** (20+ tests)
   - Syntax error detection
   - Look-ahead bias detection (.shift(-1))
   - API misuse detection (.rank() without axis)
   - Required elements check

2. **Integration Tests**
   - StructuredInnovator integration
   - Retry logic validation
   - Fallback behavior

3. **Performance Tests**
   - Validation overhead <10ms
   - No regression in generation throughput

---

## 7. Migration & Backward Compatibility

### 7.1 Backward Compatibility Strategy

**Phase 3.1** ✅:
- ✅ `Union[StrategyMetrics, Dict[str, float]]` parameter types
- ✅ Automatic conversion via `from_dict()` in all entry points
- ✅ Historical JSONL files remain readable
- ✅ Zero breaking changes

**Phase 3.2** 🚧:
- ✅ Non-breaking: Validation happens in execution layer only
- ✅ Existing code paths unchanged
- ✅ Failed validation = `success=False` (existing behavior)

**Phase 3.3** ⏳:
- ✅ Opt-in: Only activates if error rate threshold met
- ✅ Fallback mechanism preserves existing behavior
- ✅ Can be disabled via feature flag

### 7.2 Migration Checklist

- [x] Phase 3.1: Type consistency migration ✅ COMPLETE
- [ ] Phase 3.2: Add Pydantic to requirements.txt
- [ ] Phase 3.2: Create schemas.py module
- [ ] Phase 3.2: Integrate validation into BacktestExecutor
- [ ] Phase 3.2: Add validation tests
- [ ] Phase 3.3: Decision gate evaluation (error rate check)
- [ ] Phase 3.3: Implement code validator (if needed)
- [ ] Phase 3.3: Integration tests (if needed)

---

## 8. Deployment & Rollout Plan

### 8.1 Phased Rollout

**Week 1**: Phase 3.1 ✅ COMPLETE
- ✅ Deploy type consistency improvements
- ✅ Monitor for regressions
- ✅ Validate backward compatibility

**Week 2**: Phase 3.2 Schema Validation
- 🚧 Day 1-2: Implement Pydantic schemas
- 🚧 Day 3-4: Integrate into BacktestExecutor
- 🚧 Day 5: Testing and validation

**Week 3+**: Phase 3.3 (Conditional)
- ⏳ Evaluate error rate from Phase 1+2
- ⏳ If >20%, implement code validator
- ⏳ Otherwise, mark as "Not Needed" and close

### 8.2 Rollback Plan

**Phase 3.2 Rollback**:
- Remove validation from BacktestExecutor
- Revert to previous execution flow
- No data migration needed (backward compatible)

**Phase 3.3 Rollback**:
- Disable code validator via feature flag
- No system changes needed (opt-in design)

---

## 9. Acceptance Criteria

### 9.1 Phase 3.1 ✅ COMPLETE

- [x] All TC-1.1 to TC-1.10 acceptance criteria met
- [x] mypy reports 0 type errors
- [x] All existing tests pass
- [x] Backward compatibility validated

### 9.2 Phase 3.2 🚧 PENDING

- [ ] All SV-2.1 to SV-2.10 acceptance criteria met
- [ ] Pydantic validation overhead <1ms
- [ ] Integration tests pass
- [ ] No false positives in validation

### 9.3 Phase 3.3 ⏳ CONDITIONAL

**Decision Gate**: Implement ONLY if Phase 1+2 error rate >20%

- [ ] Decision gate evaluated (error rate measured)
- [ ] If implemented: All CPV-3.1 to CPV-3.10 acceptance criteria met
- [ ] If not implemented: Document decision and close

---

**Document Version**: 1.0
**Last Updated**: 2025-11-13
**Status**: Draft
**Author**: Claude Code AI
**Reviewers**: Pending
