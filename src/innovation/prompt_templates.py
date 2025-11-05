"""
Enhanced LLM Prompt Templates for Innovation Generation

Provides sophisticated prompt templates that guide LLMs to create high-quality,
novel, and explainable trading strategy innovations within finlab API constraints.
"""

from typing import List, Dict, Optional
from datetime import datetime

# Input size limits to prevent LLM context overflow and excessive API costs
MAX_PROMPT_LENGTH = 8000  # Maximum prompt characters
MAX_CODE_LENGTH = 1000  # Maximum generated code length
MAX_RATIONALE_LENGTH = 500  # Maximum rationale length
MAX_TOP_FACTORS = 10  # Maximum top factors to include
MAX_EXISTING_FACTORS = 30  # Maximum existing factors to include


# Base Innovation Prompt Template
INNOVATION_PROMPT_TEMPLATE = """
You are an expert quantitative researcher creating novel trading strategy factors for the Taiwan stock market.

**Task**: Generate a new factor expression using the finlab API that will be backtested on Taiwan stocks.

**Context**:
- Current Date: {current_date}
- Baseline Performance: Sharpe {baseline_sharpe:.3f}, Calmar {baseline_calmar:.3f}, MDD {baseline_mdd:.1%}
- Target: Sharpe ≥ {target_sharpe:.3f}, Calmar ≥ {target_calmar:.3f}, MDD ≤ 25%
- Best Performing Factors So Far:
{top_factors}

**Available Data** (Taiwan Stock Market):
- Price data: data.get('price:收盤價'), data.get('price:開盤價'), data.get('price:最高價'), data.get('price:最低價'), data.get('price:成交量')
- Fundamental data: data.get('fundamental_features:ROE稅後'), data.get('fundamental_features:本益比'), data.get('fundamental_features:淨值比'),
  data.get('fundamental_features:營收成長率'), data.get('fundamental_features:EPS成長率'), data.get('fundamental_features:營業毛利率'),
  data.get('fundamental_features:營業利益率'), data.get('fundamental_features:稅後淨利率'), data.get('fundamental_features:負債比率'),
  data.get('fundamental_features:流動比率'), data.get('fundamental_features:速動比率')
- Technical indicators: Use pandas/numpy operations (e.g., .rolling(), .shift(), .rank())

**Critical Constraints**:
1. Must use finlab.data.get() API with Taiwan field names
2. No external data sources allowed
3. No look-ahead bias - only use historical data (shift ≥ 1)
4. Expression must be vectorized (no loops)
5. Handle NaN values appropriately (.fillna(), .dropna())

**Innovation Requirements**:
1. **Novelty**: Create something NOT in this list of existing factors:
{existing_factors}

2. **Explainability**: Provide clear economic/statistical rationale for why this factor should work
   - Avoid tautologies like "buy low sell high" or "maximize profit"
   - Explain the market inefficiency or behavior this factor exploits
   - Minimum 20 characters, maximum 200 characters

3. **Robustness**: Design for generalization across different market regimes
   - Consider both bull and bear markets
   - Avoid overfitting to specific time periods
   - Use well-known financial concepts when possible

**Output Format**:
```python
# Factor Code (single expression, no functions)
factor = <your expression here>

# Rationale (20-200 characters)
# <explain the economic/statistical reasoning in 1-2 sentences>
```

**Example** (DO NOT COPY - this is just to show format):
```python
# Factor Code
factor = data.get('fundamental_features:ROE稅後') * data.get('fundamental_features:營收成長率') / data.get('fundamental_features:本益比').replace(0, np.nan)

# Rationale
# Combines profitability (ROE), growth momentum (revenue growth), and valuation (P/E) to identify undervalued growth stocks with strong fundamentals. High values indicate quality companies with strong growth at reasonable valuations.
```

**Important Reminders**:
- Your factor will be validated through 7 layers of testing
- It must pass walk-forward analysis (≥3 rolling windows)
- It must perform in all market regimes (Bull/Bear/Sideways)
- It must be ≥80% different from all existing factors
- Your rationale will be checked for tautologies

Now generate YOUR novel factor:
"""


# Category-Specific Prompt Templates
CATEGORY_PROMPTS = {
    'value': """
**Category Focus**: Value Investing

Create a factor that identifies undervalued stocks based on fundamental metrics.

**Value Factor Ideas**:
- Low P/E, P/B, P/S ratios relative to quality metrics
- High earnings yield, dividend yield, cash flow yield
- Price relative to book value, earnings, cash flow
- Quality-adjusted value (ROE/P/B, ROA/P/E)

**Taiwan Market Context**:
- Taiwan stocks often have high dividend yields
- Manufacturing companies may have low P/B ratios
- Consider sector-specific valuation norms
""",

    'quality': """
**Category Focus**: Quality Investing

Create a factor that identifies high-quality companies based on financial health.

**Quality Factor Ideas**:
- High ROE, ROA, profit margins
- Low debt ratios, high current ratios
- Consistent earnings growth, revenue growth
- Strong cash generation (operating cash flow)

**Taiwan Market Context**:
- Technology companies often have high ROE
- Export-oriented companies may have volatile margins
- Consider balance sheet strength in uncertain times
""",

    'growth': """
**Category Focus**: Growth Investing

Create a factor that identifies companies with strong growth momentum.

**Growth Factor Ideas**:
- Revenue growth, EPS growth rates
- Earnings surprises, guidance revisions
- Market share expansion indicators
- Sales efficiency (revenue per employee)

**Taiwan Market Context**:
- Tech sector shows high revenue growth
- Export growth correlates with global demand
- Seasonal patterns in growth rates
""",

    'momentum': """
**Category Focus**: Momentum Investing

Create a factor that captures price or earnings momentum.

**Momentum Factor Ideas**:
- Price momentum (12-month, 6-month returns)
- Moving average crossovers (50-day, 200-day)
- Relative strength vs market or sector
- Volume-weighted price trends

**Taiwan Market Context**:
- Momentum often persists for 3-6 months
- Consider volume as confirmation signal
- Sector rotation patterns in Taiwan market
""",

    'mixed': """
**Category Focus**: Multi-Factor Combination

Create a factor that combines multiple investment styles for robustness.

**Combination Ideas**:
- Quality × Value (ROE / P/B)
- Growth × Momentum (Revenue Growth × Price Momentum)
- Quality × Growth / Value (ROE × Revenue Growth / P/E)
- Fundamental Strength × Technical Signal

**Taiwan Market Context**:
- Combining factors can improve risk-adjusted returns
- Consider factor correlations
- Balance fundamental and technical signals
"""
}


# Helper Functions

def format_top_factors(top_factors: List[Dict], max_factors: int = 5) -> str:
    """Format top performing factors for prompt context."""
    if not top_factors:
        return "  (No top factors yet - this is the first iteration)"

    lines = []
    for i, factor in enumerate(top_factors[:max_factors], 1):
        sharpe = factor.get('sharpe_ratio', 0)
        code_preview = factor.get('code', '')[:60]
        lines.append(f"  {i}. Sharpe {sharpe:.3f}: {code_preview}...")

    return "\n".join(lines)


def format_existing_factors(existing_factors: List[str], max_display: int = 10) -> str:
    """Format existing factors for novelty enforcement."""
    if not existing_factors:
        return "  (No existing factors yet)"

    lines = []
    for i, factor_code in enumerate(existing_factors[:max_display], 1):
        code_preview = factor_code[:70]
        lines.append(f"  {i}. {code_preview}...")

    if len(existing_factors) > max_display:
        lines.append(f"  ... and {len(existing_factors) - max_display} more factors")

    return "\n".join(lines)


def create_innovation_prompt(
    baseline_metrics: Dict[str, float],
    existing_factors: List[str],
    top_factors: List[Dict],
    category: Optional[str] = None,
    pattern_context: Optional[str] = None
) -> str:
    """
    Create innovation prompt for LLM.

    Args:
        baseline_metrics: Baseline performance metrics (sharpe, calmar, mdd)
        existing_factors: List of existing factor code to avoid
        top_factors: Top performing factors for context
        category: Optional category focus (value, quality, growth, momentum, mixed)
        pattern_context: Optional pattern extraction context (Phase 3)

    Returns:
        Formatted prompt string
    """
    # Input size validation: Limit top_factors and existing_factors
    if len(top_factors) > MAX_TOP_FACTORS:
        print(f"⚠️  Truncating top_factors from {len(top_factors)} to {MAX_TOP_FACTORS}")
        top_factors = top_factors[:MAX_TOP_FACTORS]

    if len(existing_factors) > MAX_EXISTING_FACTORS:
        print(f"⚠️  Truncating existing_factors from {len(existing_factors)} to {MAX_EXISTING_FACTORS}")
        existing_factors = existing_factors[:MAX_EXISTING_FACTORS]

    # Calculate adaptive thresholds
    baseline_sharpe = baseline_metrics.get('mean_sharpe', 0.680)
    baseline_calmar = baseline_metrics.get('mean_calmar', 2.406)
    baseline_mdd = baseline_metrics.get('mean_mdd', 0.20)

    target_sharpe = baseline_sharpe * 1.2  # 20% improvement
    target_calmar = baseline_calmar * 1.2

    # Base prompt
    prompt = INNOVATION_PROMPT_TEMPLATE.format(
        current_date=datetime.now().strftime('%Y-%m-%d'),
        baseline_sharpe=baseline_sharpe,
        baseline_calmar=baseline_calmar,
        baseline_mdd=baseline_mdd,
        target_sharpe=target_sharpe,
        target_calmar=target_calmar,
        top_factors=format_top_factors(top_factors),
        existing_factors=format_existing_factors(existing_factors)
    )

    # Add category-specific guidance if provided
    if category and category in CATEGORY_PROMPTS:
        prompt += "\n\n" + CATEGORY_PROMPTS[category]

    # Phase 3: Add pattern extraction context (with size limit)
    if pattern_context:
        # Truncate pattern context if too long
        if len(pattern_context) > 1000:
            print(f"⚠️  Truncating pattern_context from {len(pattern_context)} to 1000 chars")
            pattern_context = pattern_context[:1000] + "... (truncated)"

        prompt += "\n\n**Pattern Insights from Successful Innovations**:\n"
        prompt += pattern_context
        prompt += "\n\nConsider using these proven patterns while maintaining novelty.\n"

    # Validate final prompt length
    if len(prompt) > MAX_PROMPT_LENGTH:
        print(f"⚠️  WARNING: Prompt length ({len(prompt)}) exceeds limit ({MAX_PROMPT_LENGTH})")
        print(f"   Consider reducing top_factors or existing_factors")

    return prompt


def create_structured_innovation_prompt(
    baseline_metrics: Dict[str, float],
    available_fields: List[str],
    category: Optional[str] = None
) -> str:
    """
    Create prompt for structured (YAML) innovation.

    Args:
        baseline_metrics: Baseline performance metrics
        available_fields: List of available finlab data fields
        category: Optional category focus

    Returns:
        Formatted YAML innovation prompt
    """
    baseline_sharpe = baseline_metrics.get('mean_sharpe', 0.680)
    target_sharpe = baseline_sharpe * 1.2

    prompt = f"""
You are creating a YAML factor definition for Taiwan stock trading.

**Task**: Generate a YAML factor definition using available finlab fields.

**Available Fields**:
{', '.join(available_fields[:20])}
... and {len(available_fields) - 20} more fields

**Performance Target**: Sharpe ≥ {target_sharpe:.3f}

**YAML Format**:
```yaml
factor:
  name: "<descriptive_name>"
  description: "<what this factor measures>"
  type: "composite"  # or "derived", "ratio", "aggregate"
  components:
    - field: "<field_name>"
    - field: "<field_name>"
      operation: "multiply"  # or "divide", "add", "subtract"
  constraints:
    min_value: 0
    max_value: 100
    null_handling: "drop"  # or "fill_zero", "forward_fill"
  metadata:
    rationale: "<economic reasoning - 20+ characters>"
    expected_direction: "higher_is_better"  # or "lower_is_better"
    category: "{category or 'mixed'}"
```

**Guidelines**:
1. Use only fields from the available_fields list
2. Valid operations: multiply, divide, add, subtract, power, log, abs
3. Provide clear rationale (no tautologies)
4. Set reasonable min/max constraints

Now generate your YAML factor definition:
"""

    return prompt


def extract_code_and_rationale(llm_response: str) -> tuple[Optional[str], Optional[str]]:
    """
    Extract factor code and rationale from LLM response.

    Args:
        llm_response: Raw LLM response text

    Returns:
        (code, rationale) tuple or (None, None) if extraction fails
    """
    lines = llm_response.split('\n')

    code = None
    rationale = None

    for i, line in enumerate(lines):
        # Extract code (line starting with "factor = ")
        if line.strip().startswith('factor ='):
            code = line.strip()

        # Extract rationale (comment line starting with "#" after code)
        if code and line.strip().startswith('#') and not line.strip().startswith('# Factor Code'):
            rationale_text = line.strip().lstrip('#').strip()
            if len(rationale_text) >= 20:  # Minimum length
                rationale = rationale_text
                break

    return code, rationale


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING PROMPT TEMPLATES")
    print("=" * 70)

    # Mock baseline metrics
    baseline_metrics = {
        'mean_sharpe': 0.680,
        'mean_calmar': 2.406,
        'mean_mdd': 0.20
    }

    # Mock existing factors
    existing_factors = [
        "data.get('fundamental_features:ROE稅後')",
        "data.get('price:收盤價').rolling(20).mean()",
        "data.get('fundamental_features:本益比') / data.get('fundamental_features:淨值比')"
    ]

    # Mock top factors
    top_factors = [
        {'code': "data.get('fundamental_features:ROE稅後') * data.get('fundamental_features:營收成長率')",
         'sharpe_ratio': 0.85}
    ]

    # Test 1: Base innovation prompt
    print("\nTest 1: Base Innovation Prompt")
    print("-" * 70)
    prompt = create_innovation_prompt(baseline_metrics, existing_factors, top_factors)
    print(prompt[:500] + "...\n")

    # Test 2: Category-specific prompt (Value)
    print("\nTest 2: Value Category Prompt")
    print("-" * 70)
    value_prompt = create_innovation_prompt(
        baseline_metrics, existing_factors, top_factors, category='value'
    )
    print("✅ Value prompt created (length: {} chars)".format(len(value_prompt)))

    # Test 3: Extract code and rationale
    print("\nTest 3: Extract Code and Rationale")
    print("-" * 70)

    mock_response = """
```python
# Factor Code
factor = data.get('fundamental_features:ROE稅後') / data.get('fundamental_features:淨值比').replace(0, np.nan)

# Rationale
# Quality-adjusted value factor that identifies companies with high return on equity relative to price-to-book ratio, indicating undervalued quality stocks.
```
"""

    code, rationale = extract_code_and_rationale(mock_response)
    print(f"✅ Extracted code: {code}")
    print(f"✅ Extracted rationale: {rationale}")

    # Test 4: Structured YAML prompt
    print("\nTest 4: Structured YAML Prompt")
    print("-" * 70)

    available_fields = [
        'roe', 'revenue_growth', 'pe_ratio', 'pb_ratio', 'operating_margin',
        'debt_to_equity', 'current_ratio', 'close', 'volume'
    ]

    yaml_prompt = create_structured_innovation_prompt(
        baseline_metrics, available_fields, category='quality'
    )
    print(yaml_prompt[:500] + "...\n")

    print("=" * 70)
    print("PROMPT TEMPLATE TEST COMPLETE")
    print("=" * 70)
