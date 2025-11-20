# TDD Plan Addendum - Gemini 2.5 Pro Audit Results

**Date**: 2025-11-20
**Auditor**: Gemini 2.5 Pro (via zen:chat MCP)
**Status**: Critical improvements identified

---

## Executive Summary

**Overall Assessment**: "Top-tier implementation plan" with excellent structure and TDD approach.

**Critical Finding**: Phase 1 incomplete field catalog (only first 20 fields shown) poses **high risk** of continued LLM hallucination. This must be fixed to achieve 80%+ success rate.

**Recommendation**: Apply all critical fixes before implementation begins.

---

## Audit Results

### 1. Completeness ✅ EXCELLENT

**Rating**: Very comprehensive
**Strengths**:
- Full lifecycle coverage (test → implement → refactor → validate)
- Timeline, risk management, rollback procedures included
- Correct prioritization (50% field errors addressed first)
- Specific metrics and validation criteria

### 2. Technical Accuracy ⚠️ GOOD with Critical Risks

**Rating**: Generally sound with 2 critical issues

#### ❌ Critical Issue #1: Incomplete Field Catalog (Phase 1, Line 164)

**Problem**: Plan shows only first 20 fundamental features
```python
# Current approach (RISKY)
VALID_FINLAB_FIELDS["fundamental_features"][:20]
```

**Risk**: LLM cannot use information it hasn't been given. Will continue hallucinating the 30+ unlisted fields.

**Impact**: **HIGH** - Directly undermines Phase 1's 30pp improvement target

**Solution**: Provide COMPLETE field list in compact format
```python
# Recommended approach
doc += "### Fundamental Features\n"
doc += "Use one of the following fields:\n"
doc += "```python\n"
doc += f"{VALID_FINLAB_FIELDS['fundamental_features']}\n"
doc += "```\n"
```

#### ⚠️ Critical Issue #2: Overly Complex Phase 4 (Lines 567-602)

**Problem**: Asking LLM to generate complex edge-case handling logic
```python
# Example of complex logic requested from LLM
if position.sum().sum() == 0:
    # Add fallback strategy...
```

**Risk**: Increases cognitive load, may result in inconsistent/incorrect application

**Impact**: MEDIUM - Reduces reliability of Phase 4 improvements

**Solution**: Move invariant edge-case logic to robust boilerplate. Focus LLM on core strategy function only.

### 3. Feasibility ✅ ACHIEVABLE

**Rating**: 2-3 day timeline is ambitious but achievable

**Timeline Breakdown**:
- Day 1 (Phases 1 & 2): Most intensive, field catalog compilation may take longer
- Day 2 (Phases 3 & 4): Reasonable
- Day 3 (Buffer): Crucial and realistic

**Critical Path**: Field catalog compilation and validation run duration

### 4. Missing Elements 🔍 Enhancement Opportunities

#### 1. Automated Feedback Loop (Future Enhancement)

**Concept**: Feed validator error messages back to LLM for self-correction
```python
# Example feedback loop
error_msg = "Field 'price:成交量' not found. Most similar: 'price:成交股數'"
corrected_code = llm.retry_with_feedback(original_code, error_msg)
```

**Impact**: Could push success rate beyond 85%
**Priority**: Phase 2 feature (post-initial implementation)

#### 2. System Prompt Definition

**Current**: Focuses on user-facing prompt content
**Missing**: Meta-instruction defining LLM persona and core directives

**Recommended System Prompt**:
```
You are an expert quantitative developer for the FinLab platform.
Your primary goal is to write correct, executable Python code for trading strategies.
Adhere strictly to the provided API and field catalog.
Before writing code, briefly outline the fields you will use and your approach.
```

**Impact**: Improves overall compliance and reduces errors
**Priority**: Add to Phase 1

#### 3. Token Count Monitoring

**Current**: Identifies risk but mitigation is vague (Line 678)
**Missing**: Explicit measurement action

**Recommended Addition** to each phase VALIDATE step:
```yaml
VALIDATE:
  - Run 20-iteration test
  - Measure and record final prompt token count
  - Verify < 100K token limit
  - Document token usage trend
```

**Impact**: Prevents token budget surprises
**Priority**: Add to all 4 phases

#### 4. Data Inconsistency Clarification

**Issue**: Line 21 says "API Misunderstanding: 12.4%", Line 631 says "API Errors: 6.2%"

**Required Action**: Clarify correct percentage to properly scope Phase 3

### 5. Improvement Suggestions

#### Priority 1: Complete Field List (CRITICAL)

**Action**: Modify Phase 1 implementation (Lines 163-166)

**Current Code**:
```python
# _build_api_documentation_section() - INCOMPLETE
doc += "### Fundamental Features\n"
for field in VALID_FINLAB_FIELDS["fundamental_features"][:20]:  # TRUNCATED!
    doc += f"- `{field}`\n"
```

**Fixed Code**:
```python
# _build_api_documentation_section() - COMPLETE
doc += "### Fundamental Features\n"
doc += "Use one of the following fields:\n"
doc += "```python\n"
doc += "# All valid fundamental_features fields:\n"
doc += f"{VALID_FINLAB_FIELDS['fundamental_features']}\n"
doc += "```\n\n"

doc += "### Financial Statement Fields\n"
doc += "```python\n"
doc += "# All valid financial_statement fields:\n"
doc += f"{VALID_FINLAB_FIELDS['financial_statement']}\n"
doc += "```\n\n"
```

**Token Impact**: ~500-1000 additional tokens (well within 100K limit)

#### Priority 2: Simplify Phase 4 via Enhanced Boilerplate

**Action**: Move edge-case handling from LLM-generated code to framework boilerplate

**Current Approach** (Complex, error-prone):
```python
# LLM asked to generate this
def strategy():
    # ... strategy logic ...

    # Edge case handling (complex!)
    if position.sum().sum() == 0:
        position = data.get('price:收盤價') > 0  # Fallback

    # Liquidity filtering (complex!)
    volume_filter = volume > volume.rolling(20).mean()
    position = position & volume_filter
```

**Recommended Approach** (Simple, reliable):
```python
# Framework boilerplate handles edge cases
def execute_strategy_with_safeguards(strategy_func, data):
    position = strategy_func(data)

    # Framework handles edge cases
    if position.sum().sum() == 0:
        logger.warning("Empty position, applying fallback")
        position = apply_fallback_strategy(data)

    # Framework handles liquidity filtering
    position = apply_liquidity_filter(position, data)

    return position

# LLM only generates this (simple!)
def strategy(data):
    close = data.get('price:收盤價')
    rsi = calculate_rsi(close, 14)
    return rsi < 30  # Simple, focused logic
```

**Impact**: Reduces LLM task complexity, increases reliability

#### Priority 3: Add Chain of Thought Prompting

**Action**: Add instruction to Phase 1 prompt template

**Addition to Prompt**:
```markdown
## Code Generation Instructions

Before writing the code, briefly outline your approach:
1. List the specific fields you will use (verify against the field catalog)
2. Describe the strategy logic in 2-3 sentences
3. Note any edge cases you're handling

Then write the complete strategy code.
```

**Impact**: Forces LLM to "think" and catch its own mistakes before coding
**Token Cost**: ~100 tokens
**Benefit**: Significant reduction in field hallucination and logic errors

#### Priority 4: Refine TDD Cycle for Determinism

**Current TDD Cycle**: RED → GREEN → REFACTOR → VALIDATE

**Proposed Enhanced Cycle**:
1. **RED**: Write deterministic unit test for new validator
2. **GREEN**: Implement validator logic (deterministic)
3. **PROMPT**: Update prompt with documentation/examples
4. **VALIDATE**: Run 20-iteration statistical test

**Benefit**: Separates building safety net (validators) from teaching LLM

---

## Recommended Implementation Changes

### Phase 1 Modifications

**File**: `src/innovation/prompt_builder.py`

#### Change 1.1: Complete Field Catalog (CRITICAL)

**Location**: TDD Cycle 1.2, GREEN step implementation

**Original** (Lines 163-166):
```python
def _build_api_documentation_section(self) -> str:
    doc = "## FinLab API Field Reference\n\n"
    doc += "### Fundamental Features\n"
    for field in VALID_FINLAB_FIELDS["fundamental_features"][:20]:
        doc += f"- `{field}`\n"
    return doc
```

**Fixed**:
```python
def _build_api_documentation_section(self) -> str:
    """Build complete API documentation with all valid fields."""
    doc = "## FinLab API Field Reference\n\n"

    # Fundamental features - COMPLETE LIST
    doc += "### Fundamental Features (Complete List)\n"
    doc += "```python\n"
    doc += "# All valid fundamental_features fields:\n"
    doc += "FUNDAMENTAL_FEATURES = [\n"
    for field in VALID_FINLAB_FIELDS["fundamental_features"]:
        doc += f"    '{field}',\n"
    doc += "]\n```\n\n"

    # Financial statements - COMPLETE LIST
    doc += "### Financial Statement Fields (Complete List)\n"
    doc += "```python\n"
    doc += "# All valid financial_statement fields:\n"
    doc += "FINANCIAL_STATEMENT_FIELDS = [\n"
    for field in VALID_FINLAB_FIELDS["financial_statement"]:
        doc += f"    '{field}',\n"
    doc += "]\n```\n\n"

    # Price fields
    doc += "### Price Fields\n"
    doc += "```python\n"
    doc += "PRICE_FIELDS = ['price:收盤價', 'price:開盤價', 'price:成交股數', "
    doc += "'price:最高價', 'price:最低價']\n"
    doc += "```\n\n"

    # Usage warning
    doc += "**IMPORTANT**: Only use fields from the lists above. "
    doc += "Using unlisted field names will cause execution errors.\n\n"

    return doc
```

#### Change 1.2: Add System Prompt

**Location**: New method in PromptBuilder class

**New Code**:
```python
def _build_system_prompt(self) -> str:
    """Build system prompt defining LLM persona and directives."""
    return """You are an expert quantitative developer for the FinLab platform.

PRIMARY GOALS:
1. Write correct, executable Python code for trading strategies
2. Adhere strictly to the provided API and field catalog
3. Avoid field name hallucinations - ONLY use fields from the provided lists

WORKFLOW:
Before writing code, briefly outline:
- Specific fields you will use (verify against catalog)
- Strategy logic in 2-3 sentences
- Any edge cases to handle

Then write the complete, executable strategy code.
"""
```

#### Change 1.3: Add Token Monitoring to VALIDATE

**Location**: Each phase VALIDATE step

**Addition**:
```python
def validate_phase_completion(prompt: str, success_rate: float) -> dict:
    """Validate phase completion with token monitoring."""
    import tiktoken

    encoder = tiktoken.encoding_for_model("gpt-3.5-turbo")
    token_count = len(encoder.encode(prompt))

    return {
        "success_rate": success_rate,
        "token_count": token_count,
        "token_limit": 100000,
        "token_usage_pct": (token_count / 100000) * 100,
        "within_budget": token_count < 100000
    }
```

### Phase 4 Modifications

#### Change 4.1: Simplify Edge Case Handling

**Location**: TDD Cycle 4.2, GREEN step implementation

**Original Approach**: LLM generates edge-case logic

**New Approach**: Framework boilerplate handles edge cases

**New Framework Function**:
```python
def execute_strategy_with_safeguards(
    strategy_code: str,
    data: DataCache,
    min_position_size: float = 0.01
) -> pd.DataFrame:
    """Execute strategy with automatic edge-case handling."""

    # Execute LLM-generated strategy
    position = exec_strategy_code(strategy_code, data)

    # Safeguard 1: Handle empty positions
    if position.sum().sum() == 0:
        logger.warning("Empty position detected, applying fallback")
        position = apply_minimum_viable_strategy(data)

    # Safeguard 2: Liquidity filtering
    volume = data.get('price:成交股數')
    liquidity_filter = volume > volume.rolling(20).mean()
    position = position & liquidity_filter

    # Safeguard 3: Position size normalization
    position_sum = position.sum(axis=1)
    if (position_sum > 0).any():
        position = position.div(position_sum, axis=0).fillna(0)

    return position
```

**Updated Prompt Template** (Phase 4):
```markdown
## Simplified Strategy Generation

Write a function that returns a boolean DataFrame indicating position signals.
The framework will automatically handle:
- Empty position fallbacks
- Liquidity filtering
- Position size normalization

Focus your code on the core strategy logic only.
```

---

## Risk Assessment Changes

### Original Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Incomplete field catalog | Low | High | Field discovery |
| Token budget exceeded | Medium | Medium | Incremental approach |

### Updated Risks (Post-Audit)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Incomplete field catalog | ~~Low~~ **HIGH** | **CRITICAL** | ✅ **Provide complete list** |
| LLM cognitive overload (Phase 4) | **MEDIUM** | **HIGH** | ✅ **Simplify via boilerplate** |
| Token budget exceeded | Low | Medium | ✅ **Explicit monitoring** |
| System prompt missing | **HIGH** | **MEDIUM** | ✅ **Add persona definition** |

---

## Implementation Priorities

### Must-Have Before Starting (Critical Path)

1. ✅ **Fix Phase 1 field catalog** - Provide complete list (not first 20)
2. ✅ **Add system prompt** - Define LLM persona and directives
3. ✅ **Add token monitoring** - Explicit measurement in each VALIDATE step

### Should-Have for Phase 1

4. ✅ **Add Chain of Thought prompting** - Force LLM to outline before coding
5. ✅ **Clarify API error percentage** - Resolve 12.4% vs 6.2% discrepancy

### Should-Have for Phase 4

6. ✅ **Simplify edge-case handling** - Move to framework boilerplate
7. ✅ **Update Phase 4 prompt** - Focus LLM on core logic only

### Nice-to-Have (Future Enhancements)

8. ⏳ **Automated feedback loop** - Self-correction mechanism (Phase 2 feature)
9. ⏳ **Refined TDD cycle** - Separate deterministic from statistical testing

---

## Updated Success Metrics

### Phase 1 Revised Targets

**Original**: 20% → 50% success (+30pp)
**Revised with complete field catalog**: 20% → 55-60% success (+35-40pp)

**Justification**: Complete field list eliminates 80% of field hallucination risk (50% of failures), not just 60%.

### Overall Revised Targets

**Original**: 20% → 85% success
**Revised with all improvements**: 20% → 87-90% success

**Confidence**: High (90%+) if all critical fixes applied

---

## Conclusion

**Audit Verdict**: "Top-tier implementation plan" with critical improvements identified

**Critical Actions Required**:
1. Fix Phase 1 incomplete field catalog (HIGH RISK if not addressed)
2. Add system prompt for LLM persona definition
3. Simplify Phase 4 by moving edge cases to boilerplate
4. Add explicit token monitoring to all phases

**Recommendation**: Apply all critical fixes before beginning implementation. With fixes applied, confidence in achieving 80%+ success rate is very high (>90%).

**Next Step**: Update TDD_LLM_IMPROVEMENT_PLAN.md with these changes, then proceed with Phase 1 implementation.
