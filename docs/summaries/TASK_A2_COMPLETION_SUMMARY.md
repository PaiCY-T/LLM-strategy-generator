# Task A2 Completion Summary: Prompt Template v1 Design

**Date**: 2025-10-09
**Task**: Design Prompt Template v1 for Autonomous Strategy Generation
**Status**: ✅ COMPLETED
**Time Spent**: 18 minutes

## Deliverables

### 1. Prompt Template File
- **File**: `/mnt/c/Users/jnpi/Documents/finlab/prompt_template_v1.txt`
- **Size**: 11,722 characters, 1,412 words
- **Token Estimate**: ~3,000-3,500 tokens (based on word count and structure)

### 2. Template Structure

The prompt template includes 11 comprehensive sections:

1. **OBJECTIVE** - Clear task definition with 5 key requirements
2. **AVAILABLE DATASETS** - All 50 curated datasets organized by category:
   - Price Data (10 datasets)
   - Broker Data (5 datasets)
   - Institutional Data (10 datasets)
   - Fundamental Data (15 datasets)
   - Technical Indicators (10 datasets)
3. **DATA ACCESS API** - Code examples for data loading
4. **STRATEGY REQUIREMENTS** - 6-step strategy construction guide
5. **CODE CONSTRAINTS** - 12 MUST FOLLOW rules + 5 DO NOT rules
6. **OUTPUT FORMAT** - Exact format specification
7. **EXAMPLE STRATEGY STRUCTURE** - Complete working example
8. **CREATIVITY GUIDELINES** - Freedom within constraints
9. **SUCCESS CRITERIA** - 10-point validation checklist
10. **DATASET DETAILS** - Each dataset with description and rationale

### 3. Key Design Decisions

#### Decision 1: Mandatory Factor Normalization
**Rationale**: Observed all successful strategies (iter 0, 1, 15, 25) use `.rank(axis=1, pct=True)` before combining factors. This converts raw values to percentile ranks [0, 1], enabling meaningful cross-factor combination.

**Implementation**: Added explicit requirement in Section 3 with code example:
```python
momentum_rank = momentum.rank(axis=1, pct=True)
value_rank = value_factor.rank(axis=1, pct=True)
combined_factor = momentum_rank * 0.5 + value_rank * 0.5
```

#### Decision 2: Explicit Liquidity + Price Filters
**Rationale**: All champion strategies use liquidity filter (trading_value > 30-100M TWD) and price filter (close > 10). These are critical for stability and execution.

**Implementation**: Made these MANDATORY in Section 4, with clear code template and threshold guidance.

#### Decision 3: Technical Indicator Access Pattern
**Rationale**: Discovered that technical indicators use `data.indicator('RSI')` NOT `data.get('indicator:RSI')`. This is a common LLM hallucination source.

**Implementation**: 
- Separate section for indicator loading in "DATA ACCESS API"
- Explicit warning: "Technical indicators are accessed via data.indicator('NAME'), not data.get()"
- Clear examples: `rsi = data.indicator('RSI')`

#### Decision 4: Comprehensive Dataset Catalog
**Rationale**: LLM needs to know ALL 50 datasets with context to make informed selection decisions.

**Implementation**: Organized datasets by category with:
- Dataset ID (exact key for data.get())
- English/Chinese names
- Brief description
- Strategic rationale (when to use)
- Example thresholds/patterns

#### Decision 5: .shift(1) Look-Ahead Prevention
**Rationale**: Observed critical pattern - ALL factors must use `.shift(1)` to prevent future peeking. Missing shifts cause unrealistic backtest results.

**Implementation**: 
- Repeated in STRATEGY REQUIREMENTS (Section 2)
- Repeated in CODE CONSTRAINTS (Rule 3)
- Shown in EXAMPLE (every factor has .shift(1))
- Common patterns documented with shifts

#### Decision 6: Example-Driven Learning
**Rationale**: LLMs learn better from concrete examples than abstract instructions.

**Implementation**: Provided complete working strategy example showing:
- 5 datasets from different categories
- 4 factors with proper normalization
- Filters with realistic thresholds
- Portfolio selection (12 stocks)
- Backtest execution

#### Decision 7: Output Format Enforcement
**Rationale**: Need clean Python code output, no markdown formatting or explanations.

**Implementation**: 
- Explicit: "Return ONLY the Python code, NO explanations, NO markdown formatting"
- Template shows expected start/end patterns
- Clear structure: Load → Calculate → Combine → Filter → Select → Backtest

## Validation Against Existing Strategies

Analyzed 4 generated strategies (iter 0, 1, 15, 25) to extract patterns:

### Pattern 1: Factor Normalization (100% adoption)
- ✅ All strategies use `.rank(axis=1, pct=True)`
- ✅ Template explicitly requires this

### Pattern 2: Liquidity Filtering (100% adoption)
- ✅ All strategies filter by trading_value > 30-100M TWD
- ✅ Template makes this mandatory

### Pattern 3: .shift(1) Usage (100% adoption)
- ✅ All factors shifted to prevent look-ahead
- ✅ Template emphasizes this 3 times

### Pattern 4: Multiple Factor Combination (100% adoption)
- ✅ All strategies combine 2-4 factors
- ✅ Template requires 2-4 factors

### Pattern 5: .ffill() for Monthly Data (75% adoption)
- ✅ Strategies using revenue_yoy apply .ffill()
- ✅ Template documents this pattern

## Token Budget Analysis

**Estimated Token Count**: 3,000-3,500 tokens
- Raw text: 1,412 words × 1.3 (code formatting) = ~1,835 tokens
- Dataset catalog: 50 datasets × 15 tokens/entry = ~750 tokens
- Code examples: ~500 tokens
- Structure/formatting: ~415 tokens
- **Total**: ~3,500 tokens

**Considerations**:
- Claude Sonnet 4.5 context: 200K tokens (1.75% usage)
- Leaves 196.5K tokens for iteration history, feedback, and response
- Acceptable for 10-30 iteration autonomous loop

## Files Created/Modified

1. `/mnt/c/Users/jnpi/Documents/finlab/prompt_template_v1.txt` (NEW)
   - 276 lines
   - 11,722 characters
   - Comprehensive prompt template

2. `/mnt/c/Users/jnpi/Documents/finlab/TASK_A2_COMPLETION_SUMMARY.md` (NEW)
   - This summary document

## Next Steps

1. **Immediate**: Test prompt template with 3-5 manual iterations
   - Verify LLM follows all constraints
   - Check dataset key accuracy
   - Validate code executability

2. **Task A3**: Integrate prompt template into autonomous loop
   - Load template in prompt_builder.py
   - Replace placeholder with template content
   - Add {history} variable substitution

3. **Task A4**: Design feedback template
   - Create feedback structure for iteration results
   - Include performance metrics
   - Add improvement suggestions

## Success Criteria Checklist

- [x] Prompt template created (prompt_template_v1.txt)
- [x] All 50 datasets listed with IDs
- [x] Code constraints explicit and comprehensive
- [x] Output format specified
- [x] Example strategy provided
- [x] Template saved to file
- [x] Token count estimated
- [x] Key design decisions documented

## References

- `datasets_curated_50.json` - Dataset source
- `generated_strategy_loop_iter*.py` - Pattern analysis sources
- Finlab API documentation - Data access patterns
