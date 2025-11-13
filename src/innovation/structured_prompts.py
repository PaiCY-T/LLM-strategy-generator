#!/usr/bin/env python3
"""
Enhanced LLM Prompts for Structured Innovation
Task 2.0: YAML/JSON-based Factor Generation

This module contains prompt templates to guide LLM in generating
novel factor definitions in YAML format.
"""

# Main prompt template for structured innovation
STRUCTURED_INNOVATION_PROMPT = """
## Task: Generate Novel Factor Definition (YAML)

You are tasked with creating a novel factor definition in YAML format.

## Available Fields (from Finlab data):
{available_fields}

## YAML Schema:
```yaml
factor:
  name: "<descriptive_name>"
  description: "<what this factor measures>"
  type: "composite"  # or "derived", "ratio", "aggregate"
  components:
    - field: "<field_name>"
    - field: "<field_name>"
      operation: "<multiply|divide|add|subtract|power|log|abs>"
    ...
  constraints:
    min_value: <number>
    max_value: <number>
    null_handling: "drop"  # or "fill_zero", "forward_fill", "backward_fill", "mean"
    outlier_handling: "none"  # or "clip", "winsorize", "remove"
  metadata:
    rationale: "<why this factor is valuable>"
    expected_direction: "higher_is_better"  # or "lower_is_better", "neutral"
    category: "mixed"  # or "value", "quality", "growth", "momentum", "size", "volatility", "liquidity"
```

## Guidelines:
1. **Create novel combinations** NOT in baseline (e.g., ROE × Revenue Growth / P/E)
2. **All fields must exist** in available_fields list
3. **Use valid operations**: multiply, divide, add, subtract, power, log, abs
4. **Set reasonable min/max constraints** based on expected value ranges
5. **Provide clear rationale** for the factor (at least 20 characters)
6. **Name convention**: Use descriptive names like "Quality_Growth_Value_Composite"
7. **First component** does not need an 'operation' field (it's the starting value)
8. **Subsequent components** must have an 'operation' field

## Factor Categories:
- **value**: Valuation-based factors (P/E, P/B, etc.)
- **quality**: Quality indicators (ROE, margins, cash flow quality)
- **growth**: Growth metrics (revenue growth, earnings growth)
- **momentum**: Price momentum and technical indicators
- **size**: Market cap and size-related factors
- **volatility**: Risk and volatility measures
- **liquidity**: Trading volume and liquidity
- **mixed**: Combination of multiple categories

## Output:
Return ONLY valid YAML. No explanation before or after.

## Example 1: Quality-Growth-Value Composite
```yaml
factor:
  name: "Quality_Growth_Value_Composite"
  description: "ROE × Revenue Growth / P/E ratio"
  type: "composite"
  components:
    - field: "roe"
    - field: "revenue_growth"
      operation: "multiply"
    - field: "pe_ratio"
      operation: "divide"
  constraints:
    min_value: 0
    max_value: 100
    null_handling: "drop"
    outlier_handling: "winsorize"
  metadata:
    rationale: "Combines profitability (ROE), growth momentum (Revenue Growth), and value (P/E). High values indicate quality companies with strong growth at reasonable valuations."
    expected_direction: "higher_is_better"
    category: "mixed"
```

## Example 2: Cash Flow Quality Indicator
```yaml
factor:
  name: "Cash_Flow_Quality_Indicator"
  description: "Operating Cash Flow / Net Income"
  type: "ratio"
  components:
    - field: "operating_cash_flow"
    - field: "net_income"
      operation: "divide"
  constraints:
    min_value: 0
    max_value: 10
    null_handling: "drop"
    outlier_handling: "clip"
  metadata:
    rationale: "Measures earnings quality by comparing cash flow to net income. Ratios above 1 indicate earnings are backed by actual cash generation, suggesting lower accounting manipulation risk."
    expected_direction: "higher_is_better"
    category: "quality"
```

Now generate a NOVEL factor definition that combines fields in a unique way.
"""


# Prompt with specific innovation focus
INNOVATION_FOCUSED_PROMPT = """
## Task: Generate INNOVATIVE Factor Definition (YAML)

Create a novel factor that combines fundamental and valuation metrics in a way NOT commonly seen in traditional factor models.

## Innovation Guidelines:
1. **Combine cross-category fields**: Mix value + quality, or growth + momentum
2. **Use non-obvious operations**: Consider ratios, products, or differences
3. **Target specific investment thesis**: Quality growth, value momentum, etc.
4. **Ensure practical utility**: Factor should be economically meaningful

## Available Fields:
{available_fields}

## Target Innovation Areas:
- Quality-adjusted value (e.g., ROE / P/B)
- Growth efficiency (e.g., Revenue Growth / Asset Turnover)
- Leverage-adjusted profitability (e.g., Operating Margin / Debt-to-Equity)
- Cash flow sustainability (e.g., Free Cash Flow / Capex)

Return ONLY valid YAML factor definition. No explanation.
"""


# Prompt for specific factor category
CATEGORY_SPECIFIC_PROMPT = """
## Task: Generate {category} Factor Definition (YAML)

Create a novel factor specifically for the {category} category.

## Category Guidelines:
{category_guidelines}

## Available Fields:
{available_fields}

## Schema:
[Same schema as STRUCTURED_INNOVATION_PROMPT]

Return ONLY valid YAML factor definition. No explanation.
"""


# Category-specific guidelines
CATEGORY_GUIDELINES = {
    'value': """
    Focus on valuation metrics:
    - Combine P/E, P/B, P/S ratios
    - Compare price multiples to growth or quality metrics
    - Create value-quality composites
    Example: P/E / ROE (lower is better - cheap + high quality)
    """,

    'quality': """
    Focus on business quality indicators:
    - Profitability metrics (ROE, ROA, margins)
    - Financial health (debt ratios, current ratio)
    - Cash flow quality (OCF / Net Income)
    Example: (ROE + ROA) / Debt-to-Equity
    """,

    'growth': """
    Focus on growth metrics:
    - Revenue growth, earnings growth
    - Growth sustainability (growth + margins)
    - Growth efficiency (growth / assets)
    Example: Revenue Growth × Operating Margin
    """,

    'momentum': """
    Focus on price and volume momentum:
    - Price trends (close, high, low)
    - Volume patterns
    - Momentum quality (momentum + low volatility)
    Example: Volume / Shares Outstanding (liquidity proxy)
    """,

    'mixed': """
    Combine multiple categories:
    - Value + Quality
    - Growth + Momentum
    - Quality + Growth + Value
    Example: (ROE × Revenue Growth) / P/E
    """
}


# Function to format prompt with available fields
def format_innovation_prompt(
    available_fields: list,
    prompt_type: str = "structured",
    category: str = None
) -> str:
    """
    Format LLM prompt with available fields.

    Args:
        available_fields: List of available field names
        prompt_type: Type of prompt ("structured", "innovation", "category")
        category: Factor category for category-specific prompts

    Returns:
        Formatted prompt string
    """
    # Format field list
    fields_str = "\n".join([f"  - {field}" for field in sorted(available_fields)])

    if prompt_type == "structured":
        return STRUCTURED_INNOVATION_PROMPT.format(
            available_fields=fields_str
        )
    elif prompt_type == "innovation":
        return INNOVATION_FOCUSED_PROMPT.format(
            available_fields=fields_str
        )
    elif prompt_type == "category" and category:
        guidelines = CATEGORY_GUIDELINES.get(category, CATEGORY_GUIDELINES['mixed'])
        return CATEGORY_SPECIFIC_PROMPT.format(
            category=category,
            category_guidelines=guidelines,
            available_fields=fields_str
        )
    else:
        raise ValueError(f"Invalid prompt_type: {prompt_type}")


# Function to generate factor name suggestions
def generate_factor_name_suggestions(category: str = "mixed") -> list:
    """
    Generate factor name suggestions for inspiration.

    Args:
        category: Factor category

    Returns:
        List of suggested factor names
    """
    suggestions = {
        'value': [
            "Value_Quality_Ratio",
            "Cheap_Quality_Composite",
            "Earnings_Yield_Adjusted",
            "Book_to_Market_Quality"
        ],
        'quality': [
            "Profitability_Health_Score",
            "Cash_Flow_Quality_Index",
            "Margin_Stability_Factor",
            "Leverage_Adjusted_ROE"
        ],
        'growth': [
            "Sustainable_Growth_Score",
            "Growth_Efficiency_Ratio",
            "Revenue_Margin_Momentum",
            "Earnings_Acceleration_Index"
        ],
        'momentum': [
            "Volume_Weighted_Momentum",
            "Price_Strength_Indicator",
            "Liquidity_Momentum_Score",
            "Trend_Quality_Factor"
        ],
        'mixed': [
            "Quality_Growth_Value_Composite",
            "Fundamental_Momentum_Score",
            "Multi_Factor_Alpha_Index",
            "Comprehensive_Quality_Indicator"
        ]
    }
    return suggestions.get(category, suggestions['mixed'])


if __name__ == "__main__":
    # Example usage
    from src.innovation.structured_validator import StructuredInnovationValidator

    # Get available fields
    validator = StructuredInnovationValidator()
    available_fields = validator.get_available_fields()

    # Format standard innovation prompt
    prompt = format_innovation_prompt(
        available_fields=available_fields,
        prompt_type="structured"
    )

    print("="*70)
    print("STRUCTURED INNOVATION PROMPT")
    print("="*70)
    print(prompt)
    print()

    # Print category suggestions
    print("="*70)
    print("FACTOR NAME SUGGESTIONS")
    print("="*70)
    for category in ['value', 'quality', 'growth', 'mixed']:
        print(f"\n{category.upper()}:")
        for name in generate_factor_name_suggestions(category):
            print(f"  - {name}")
