"""
PromptBuilder - Constructs effective LLM prompts with feedback loops

Creates modification and creation prompts that incorporate:
- Champion strategy feedback (code, metrics, success factors)
- Failure pattern extraction from historical failures
- FinLab API constraints and requirements
- Few-shot examples for guidance
- Token budget management (<100K tokens, well within Gemini 2.5 Flash 1M limit)

Requirements: 3.1, 3.2, 3.3
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


# Token budget constraints
MAX_PROMPT_TOKENS = 100000  # Gemini 2.5 Flash actual limit: 1,048,576 tokens (using ~10% for safety)
CHARS_PER_TOKEN = 4  # Rough estimate: 1 token ≈ 4 characters
MAX_PROMPT_CHARS = MAX_PROMPT_TOKENS * CHARS_PER_TOKEN  # ~400,000 chars

# Liquidity requirement (million TWD)
MIN_LIQUIDITY_MILLIONS = 150


class PromptBuilder:
    """
    Builds prompts for LLM-driven strategy innovation.

    Supports two modes:
    1. Modification: Modify existing champion strategy to improve metrics
    2. Creation: Create novel strategy inspired by champion approach

    Integrates feedback loops:
    - Success factors from champion code/metrics
    - Failure patterns from failure_patterns.json
    - FinLab API constraints
    """

    def __init__(self, failure_patterns_path: str = "artifacts/data/failure_patterns.json"):
        """
        Initialize PromptBuilder.

        Args:
            failure_patterns_path: Path to failure patterns JSON file
        """
        self.failure_patterns_path = failure_patterns_path
        self._cached_failure_patterns: Optional[List[Dict[str, Any]]] = None

    def build_modification_prompt(
        self,
        champion_code: str,
        champion_metrics: Dict[str, float],
        failure_history: Optional[List[Dict[str, Any]]] = None,
        target_metric: str = "sharpe_ratio"
    ) -> str:
        """
        Build prompt for modifying champion strategy to improve metrics.

        Args:
            champion_code: Current champion strategy code
            champion_metrics: Champion performance metrics (sharpe, mdd, win_rate, etc.)
            failure_history: Optional recent failure history (last 3 failures)
            target_metric: Which metric to optimize (default: sharpe_ratio)

        Returns:
            Complete modification prompt (under 2000 tokens)

        Example:
            >>> builder = PromptBuilder()
            >>> prompt = builder.build_modification_prompt(
            ...     champion_code="def strategy(data): ...",
            ...     champion_metrics={"sharpe_ratio": 0.85, "max_drawdown": 0.15},
            ...     target_metric="sharpe_ratio"
            ... )
        """
        # Extract success factors from champion
        success_factors = self.extract_success_factors(champion_code, champion_metrics)

        # Extract failure patterns (limit to recent ones)
        failure_patterns = []
        if failure_history:
            failure_patterns = self._format_failure_patterns(failure_history[:3])

        # Build prompt sections
        prompt_parts = [
            self._get_modification_header(),
            self._format_champion_context(champion_code, champion_metrics, success_factors),
            self._format_target_directive(target_metric, champion_metrics),
            self._format_constraints(),
            self._format_failure_avoidance(failure_patterns),
            self._get_modification_example(),
            self._get_output_format()
        ]

        # Combine and truncate if needed
        prompt = "\n\n".join(prompt_parts)
        return self._truncate_to_budget(prompt)

    def build_creation_prompt(
        self,
        champion_approach: str,
        failure_patterns: Optional[List[Dict[str, Any]]] = None,
        innovation_directive: str = "Create a novel strategy with different factor combinations"
    ) -> str:
        """
        Build prompt for creating novel strategy inspired by champion.

        Args:
            champion_approach: High-level description of champion's approach
            failure_patterns: Known failure patterns to avoid
            innovation_directive: Specific innovation guidance

        Returns:
            Complete creation prompt (under 2000 tokens)

        Example:
            >>> builder = PromptBuilder()
            >>> prompt = builder.build_creation_prompt(
            ...     champion_approach="Momentum-based factor with ROE filter",
            ...     innovation_directive="Explore value + quality combinations"
            ... )
        """
        # Load and extract failure patterns from JSON if not provided
        if failure_patterns is None:
            failure_patterns = self.extract_failure_patterns()

        # Build prompt sections - System Prompt MUST be first
        prompt_parts = [
            self._build_system_prompt(),  # NEW: System prompt as first section
            self._get_creation_header(),
            self._format_champion_inspiration(champion_approach),
            self._format_innovation_directive(innovation_directive),
            self._format_constraints(),
            self._format_failure_avoidance(self._format_failure_patterns(failure_patterns[:5])),
            self._get_creation_example(),
            self._get_output_format()
        ]

        # Combine and truncate if needed
        prompt = "\n\n".join(prompt_parts)
        return self._truncate_to_budget(prompt)

    def extract_success_factors(
        self,
        code: str,
        metrics: Dict[str, float]
    ) -> List[str]:
        """
        Extract success factors from champion code and metrics.

        Identifies key patterns that contributed to champion's success:
        - High-performing metrics (Sharpe, Calmar, Win Rate)
        - Code patterns (data sources, filters, factor combinations)
        - Risk management patterns (liquidity filters, rebalancing)

        Args:
            code: Champion strategy code
            metrics: Performance metrics

        Returns:
            List of success factor descriptions

        Example:
            >>> factors = builder.extract_success_factors(
            ...     code="factor = data.get('fundamental_features:ROE稅後') > 15",
            ...     metrics={"sharpe_ratio": 0.95, "max_drawdown": 0.12}
            ... )
            >>> # Returns: ["High Sharpe (0.95)", "Low drawdown (0.12)", "Uses ROE filter", ...]
        """
        factors = []

        # Metric-based success factors
        sharpe = metrics.get('sharpe_ratio', 0)
        if sharpe > 0.8:
            factors.append(f"High Sharpe ratio ({sharpe:.2f})")

        mdd = metrics.get('max_drawdown', 1.0)
        if mdd < 0.15:
            factors.append(f"Low max drawdown ({mdd:.2%})")

        win_rate = metrics.get('win_rate', 0)
        if win_rate > 0.6:
            factors.append(f"High win rate ({win_rate:.1%})")

        calmar = metrics.get('calmar_ratio', 0)
        if calmar > 2.0:
            factors.append(f"Strong Calmar ratio ({calmar:.2f})")

        # Code pattern analysis
        code_lower = code.lower()

        # Data source patterns
        if 'fundamental_features:roe' in code_lower:
            factors.append("Uses ROE quality filter")
        if 'fundamental_features:營收成長率' in code_lower or 'revenue_growth' in code_lower:
            factors.append("Incorporates revenue growth")
        if 'price:收盤價' in code_lower or 'close' in code_lower:
            factors.append("Uses price momentum")

        # Technical patterns
        if '.rolling(' in code_lower:
            factors.append("Uses moving averages/smoothing")
        if '.shift(' in code_lower:
            factors.append("Avoids look-ahead bias (proper shift)")
        if 'rank(' in code_lower:
            factors.append("Uses cross-sectional ranking")

        # Risk management patterns
        if 'liquidity' in code_lower or '成交量' in code_lower:
            factors.append("Applies liquidity filter")
        if 'fillna' in code_lower or 'dropna' in code_lower:
            factors.append("Handles missing data properly")

        # Filter patterns
        if '>' in code or '<' in code:
            factors.append("Uses threshold filters")
        if '&' in code or '|' in code:
            factors.append("Combines multiple conditions")

        return factors[:6]  # Limit to top 6 factors

    def extract_failure_patterns(
        self,
        failure_json_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract failure patterns from failure_patterns.json.

        Loads and parses failure patterns with performance impact analysis.
        Caches results for efficiency.

        Args:
            failure_json_path: Optional path override (uses default if None)

        Returns:
            List of failure pattern dictionaries

        Example:
            >>> patterns = builder.extract_failure_patterns()
            >>> # Returns: [{"pattern_type": "parameter_change", "description": "...", ...}, ...]
        """
        # Use cache if available
        if self._cached_failure_patterns is not None:
            return self._cached_failure_patterns

        # Determine path
        path = failure_json_path or self.failure_patterns_path

        try:
            with open(path, 'r', encoding='utf-8') as f:
                patterns: List[Dict[str, Any]] = json.load(f)

            # Cache for future use
            self._cached_failure_patterns = patterns
            return patterns

        except FileNotFoundError:
            # Return empty list if file doesn't exist (graceful degradation)
            return []
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse {path}: {e}")
            return []

    # ========================================================================
    # Private Helper Methods - Prompt Sections
    # ========================================================================

    def _get_modification_header(self) -> str:
        """Get modification prompt header."""
        return """# Task: Modify Champion Strategy to Improve Performance

You are an expert quantitative researcher specializing in Taiwan stock market strategies.
Your task is to modify the current champion strategy to improve its performance metrics.

**Instructions**:
- Preserve successful patterns from the champion
- Make targeted improvements to boost the target metric
- Maintain all FinLab API constraints
- Ensure no look-ahead bias
- Keep the strategy executable and robust"""

    def _build_system_prompt(self) -> str:
        """
        Build system prompt with LLM persona and Chain of Thought guidance.

        This system prompt should be the first section in all prompts to establish:
        1. LLM persona and role
        2. Primary goals and responsibilities
        3. Chain of Thought workflow for structured thinking
        4. Critical rules and constraints

        Requirements:
        - Task 1.2.5: Add system prompt with CoT guidance
        - REQ-1: Missing element from prompt audit

        Returns:
            str: Complete system prompt section

        Example:
            >>> builder = PromptBuilder()
            >>> system_prompt = builder._build_system_prompt()
            >>> "Expert Quantitative Trading Strategy Developer" in system_prompt
            True
            >>> "Step 1" in system_prompt or "1." in system_prompt
            True
        """
        return """# System Prompt

You are an **Expert Quantitative Trading Strategy Developer** specializing in Taiwan stock market strategies using FinLab data.

## Your Primary Responsibilities

1. **Generate Valid, Executable Trading Strategies**: Produce Python code that runs without errors
2. **Use Only Validated Field Names**: NEVER invent or hallucinate field names - use ONLY fields from VALID_FIELDS catalog
3. **Follow Required Code Structure**: Use proper function signature `def strategy(data)` with `return position` statement
4. **Avoid Look-Ahead Bias**: Always use `.shift(1)` or higher for fundamental data to prevent future data leakage
5. **Ensure Code Quality**: Write clean, maintainable, well-commented code

## Chain of Thought Workflow

Follow this structured thinking process when developing strategies:

**Step 1: Analyze Requirements**
- What is the trading strategy goal?
- What market conditions should trigger trades?
- What performance metrics should be optimized?

**Step 2: Plan Strategy Logic**
- What indicators or signals are needed?
- What are the entry/exit conditions?
- How will risk be managed?

**Step 3: Select Valid Fields from Catalog**
- Check VALID_FIELDS list for required data
- Use ONLY fields from the provided catalog
- DO NOT invent, modify, or hallucinate field names
- Verify field names are exact matches (case-sensitive)

**Step 4: Implement with Proper Structure**
- Define `strategy(data)` function with correct signature
- Use `data.get('field_name')` to access data
- Apply `.shift(1)` to fundamental data to avoid look-ahead bias
- Calculate indicators and signals using vectorized pandas operations
- Handle NaN values with `.fillna()` or `.dropna()`

**Step 5: Add Return Statement**
- MUST include: `return position`
- Position must be pandas Series of buy/sell signals (boolean or numeric)
- Ensure position series is properly indexed

## Critical Rules (NEVER VIOLATE)

- ❌ **NEVER** invent or hallucinate field names
- ❌ **NEVER** use fields not in VALID_FIELDS catalog
- ❌ **NEVER** use future data (avoid look-ahead bias)
- ✅ **ALWAYS** validate field names exist in catalog
- ✅ **ALWAYS** use `.shift(1)` for fundamental data
- ✅ **ALWAYS** include `return position` statement
- ✅ **ALWAYS** handle NaN values properly

---"""

    def _get_creation_header(self) -> str:
        """Get creation prompt header."""
        return """# Task: Create Novel Trading Strategy

You are an expert quantitative researcher specializing in Taiwan stock market strategies.
Your task is to create a novel strategy inspired by successful approaches but with new ideas.

**Instructions**:
- Draw inspiration from champion approach, but create something different
- Explore new factor combinations or data sources
- Maintain all FinLab API constraints
- Ensure no look-ahead bias
- Ensure the strategy is executable and robust"""

    def _format_champion_context(
        self,
        code: str,
        metrics: Dict[str, float],
        success_factors: List[str]
    ) -> str:
        """Format champion context section."""
        # Truncate code if too long
        code_preview = code[:400] + "..." if len(code) > 400 else code

        context = f"""## Current Champion Strategy

**Performance**:
- Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.3f}
- Max Drawdown: {metrics.get('max_drawdown', 0):.2%}
- Win Rate: {metrics.get('win_rate', 0):.1%}
- Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}

**Success Factors to Preserve**:
{self._format_list(success_factors)}

**Code Preview**:
```python
{code_preview}
```"""
        return context

    def _format_champion_inspiration(self, champion_approach: str) -> str:
        """Format champion inspiration section."""
        return f"""## Champion Approach (for Inspiration)

The current champion uses: {champion_approach}

**Your Task**: Create a NOVEL strategy that explores different directions while
maintaining robustness and alignment with FinLab constraints."""

    def _format_target_directive(
        self,
        target_metric: str,
        current_metrics: Dict[str, float]
    ) -> str:
        """Format target improvement directive."""
        current_value = current_metrics.get(target_metric, 0)
        metric_display = target_metric.replace('_', ' ').title()

        return f"""## Optimization Target

**Primary Goal**: Improve {metric_display}
- Current: {current_value:.3f}
- Target: >{current_value * 1.1:.3f} (+10% improvement)

**Constraints**:
- Maintain Max Drawdown <25%
- Maintain Win Rate >45%
- Preserve liquidity requirements (>{MIN_LIQUIDITY_MILLIONS}M TWD)"""

    def _format_innovation_directive(self, directive: str) -> str:
        """Format innovation directive section."""
        return f"""## Innovation Directive

{directive}

**Exploration Ideas**:
- Combine factors from different categories (value + momentum, quality + growth)
- Use alternative data transformations (ratios, ranks, z-scores)
- Explore sector-specific patterns
- Implement dynamic filters based on market conditions"""

    def _format_constraints(self) -> str:
        """Format FinLab API constraints section."""
        return f"""## FinLab API Constraints

**Required Function Signature**:
```python
def strategy(data):
    # Your strategy logic here
    # Must return: position series or stock selection boolean series
    return position
```

{self._build_api_documentation_section()}

**Critical Rules**:
1. No external imports - use only built-in pandas/numpy operations
2. No look-ahead bias - always use `.shift(1)` or higher for historical data
3. Handle NaN values - use `.fillna()` or `.dropna()`
4. Liquidity filter - ensure average daily volume >{MIN_LIQUIDITY_MILLIONS}M TWD
5. Rebalancing - support weekly or monthly rebalancing frequencies

**Validation**:
- Code must be executable without syntax errors
- Must handle edge cases (zero divisions, missing data)
- Must be vectorized (no loops over stocks)"""

    def _build_api_documentation_section(self) -> str:
        """
        Build complete API documentation section with ALL 160 fields.

        This method creates comprehensive API documentation that includes:
        1. Complete field catalog (160 fields) in Python list format
        2. Usage examples demonstrating data.get() with proper shift() usage
        3. Field name hallucination warnings to prevent invalid field usage

        Requirements:
        - REQ-1: Complete field catalog in prompts (Critical Fix #1)
        - Task 1.2: Python list format, usage examples, hallucination warning

        Returns:
            str: Complete API documentation section with field catalog, examples,
                 and validation warnings. Falls back to basic documentation if
                 field catalog file is not available.

        Example output structure:
            **Data Access** (Taiwan Stock Market):
            **CRITICAL WARNING**: Use ONLY these exact field names...
            VALID_FIELDS = ['price:收盤價', 'price:開盤價', ...]
            **Usage Examples**: data.get('price:收盤價'), ...
            **Field Name Validation Rules**: Do NOT invent...
        """
        # Load field catalog from fixtures
        field_catalog = self._load_field_catalog()
        if not field_catalog:
            return self._build_basic_api_documentation()

        # Build Python list representation of all fields
        field_list_str = self._format_field_list_as_python(field_catalog)

        # Build complete section
        return f"""**Data Access** (Taiwan Stock Market):

**CRITICAL WARNING**: Use ONLY these exact field names from the list below.
- Do NOT invent, create, or hallucinate field names
- Do NOT modify existing field names
- Using invalid or non-existent field names will cause runtime errors and strategy failure

**Complete Field Catalog** (160 verified fields):

Use only field names from the list below. Any field not in this list is INVALID.

```python
{field_list_str}
```

**Usage Examples**:

```python
# Example 1: Get closing price
close_price = data.get('price:收盤價')

# Example 2: Get ROE with shift to avoid look-ahead bias
roe = data.get('fundamental_features:ROE').shift(1)

# Example 3: Get financial statement data
cash = data.get('financial_statement:現金')

# Example 4: Combine multiple fields
revenue = data.get('fundamental_features:營業收入').shift(1)
assets = data.get('fundamental_features:總資產').shift(1)
roa = revenue / assets
```

**Field Name Validation Rules**:
- ✅ ONLY use field names from VALID_FIELDS list above
- ✅ Must use exact field names (case-sensitive, including category prefix)
- ❌ Do NOT create or invent new field names
- ❌ Do NOT modify field names (e.g., changing 'price:收盤價' to 'price:close')
- ❌ Invalid fields will cause KeyError at runtime and strategy rejection"""

    def _load_field_catalog(self) -> Optional[Dict[str, Any]]:
        """
        Load field catalog from JSON fixture file.

        The field catalog contains metadata for all 160 valid fields:
        - 7 price fields
        - 52 fundamental_features fields
        - 101 financial_statement fields

        Returns:
            Optional[Dict[str, Any]]: Field catalog dictionary, or None if file not found.

        Example return:
            {
                "price:收盤價": {"category": "price", "dtype": "float", ...},
                "fundamental_features:ROE": {...},
                ...
            }
        """
        catalog_path = Path(__file__).parent.parent.parent / "tests" / "fixtures" / "finlab_fields.json"
        try:
            with open(catalog_path, 'r', encoding='utf-8') as f:
                catalog: Dict[str, Any] = json.load(f)
                return catalog
        except FileNotFoundError:
            return None
        except json.JSONDecodeError:
            return None

    def _format_field_list_as_python(self, field_catalog: Dict[str, Any]) -> str:
        """
        Format field catalog as Python list string.

        Converts field catalog dictionary into a Python list representation
        suitable for inclusion in prompts. Fields are sorted alphabetically
        for consistency.

        Args:
            field_catalog: Dictionary of field metadata keyed by field name

        Returns:
            str: Python list representation with proper formatting:
                 VALID_FIELDS = [
                     'field1',
                     'field2',
                     ...
                 ]

        Example:
            >>> catalog = {"price:收盤價": {...}, "price:開盤價": {...}}
            >>> result = builder._format_field_list_as_python(catalog)
            >>> "VALID_FIELDS = [" in result
            True
            >>> "'price:收盤價'," in result
            True
        """
        field_names = sorted(field_catalog.keys())

        # Create Python list representation
        field_list_lines = ["VALID_FIELDS = ["]
        for field in field_names:
            field_list_lines.append(f"    '{field}',")
        field_list_lines.append("]")

        return "\n".join(field_list_lines)

    def _build_basic_api_documentation(self) -> str:
        """
        Fallback API documentation when field catalog is unavailable.

        Provides minimal API documentation with a few example fields.
        This is used when the field catalog JSON file cannot be loaded.

        Returns:
            str: Basic API documentation with example fields

        Note:
            This fallback should rarely be used. The main _build_api_documentation_section()
            should load the complete 160-field catalog from fixtures.
        """
        return """**Data Access** (Taiwan Stock Market):
- Price: `data.get('price:收盤價')`, `data.get('price:開盤價')`, `data.get('price:成交股數')`
- Fundamentals: `data.get('fundamental_features:ROE稅後')`, `data.get('fundamental_features:本益比')`
- Technical: Use pandas operations (`.rolling()`, `.shift()`, `.rank()`, etc.)"""

    def _format_failure_avoidance(self, failure_list: List[str]) -> str:
        """Format failure patterns to avoid."""
        if not failure_list:
            return "## Failure Patterns\n\nNo historical failures to avoid."

        return f"""## Failure Patterns to Avoid

Based on historical failures, AVOID these patterns:
{self._format_list(failure_list)}"""

    def _get_modification_example(self) -> str:
        """Get few-shot modification example."""
        return """## Example: Successful Modification

**Original Champion**:
```python
def strategy(data):
    # High ROE filter
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
```
Sharpe: 0.75, MDD: 18%

**Modified Version** (Improvement: +15% Sharpe):
```python
def strategy(data):
    # Add growth filter to high ROE
    roe = data.get('fundamental_features:ROE稅後')
    growth = data.get('fundamental_features:營收成長率')

    # Combine quality (ROE) with growth momentum
    quality_growth = (roe > 15) & (growth > 0.1)

    # Add liquidity filter
    volume = data.get('price:成交股數')
    liquidity = volume.rolling(20).mean() > 150_000_000

    return quality_growth & liquidity
```
Sharpe: 0.86 (+15%), MDD: 16%

**Modification Rationale**: Added growth filter to improve returns while maintaining
quality focus. Liquidity filter reduces transaction costs."""

    def _get_creation_example(self) -> str:
        """Get few-shot creation example."""
        return """## Example: Successful Novel Creation

**Champion Approach**: "Momentum-based with ROE filter"

**Novel Strategy** (Different approach: Value + Quality):
```python
def strategy(data):
    # Value: Low P/B ratio
    pb = data.get('fundamental_features:淨值比')

    # Quality: High profit margin
    profit_margin = data.get('fundamental_features:稅後淨利率')

    # Combine: Quality-adjusted value
    value_score = profit_margin / pb.replace(0, float('nan'))

    # Rank and select top 20%
    ranked = value_score.rank(pct=True, ascending=False)

    # Liquidity filter
    volume = data.get('price:成交股數')
    liquidity = volume.rolling(20).mean() > 150_000_000

    return (ranked > 0.8) & liquidity
```

**Creation Rationale**: Novel combination of value (P/B) and quality (profit margin).
Uses ranking instead of threshold to adapt to market conditions. Different from
champion's momentum approach."""

    def _get_output_format(self) -> str:
        """Get output format instructions."""
        return """## Output Format

Provide your strategy code in this exact format:

```python
def strategy(data):
    # Your strategy logic here
    # Include comments explaining key steps

    return position  # Return position series or boolean series

# Execute backtest (REQUIRED)
position = strategy(data)
position = position.loc[start_date:end_date]
report = sim(
    position,
    fee_ratio=fee_ratio,
    tax_ratio=tax_ratio,
    resample="M"
)
```

**Available Data Fields**:
Use only these verified field names from the `data` object:
- Price fields: `close`, `open`, `high`, `low`, `volume`
- Returns: `return`, `return_1d`, `return_5d`, `return_20d`
- Technical: `ma_5`, `ma_10`, `ma_20`, `ma_60`, `rsi`, `macd`
- Volume: `volume_ratio`, `turnover`
- Market: `market_cap`, `pe_ratio`, `pb_ratio`

**Common Mistakes to Avoid**:
1. ❌ Using non-existent fields like `營收成長率季增`, `EPS成長率`
2. ❌ Missing axis parameter in pandas operations: `data.rank()` → use `data.rank(axis=1)`
3. ❌ Look-ahead bias: Never use `.shift(-1)` (future data), always use `.shift(1)` (past data)
4. ❌ Forgetting to handle NaN values: Always use `.fillna(0)` or `.dropna()`

**Requirements**:
- Complete, executable Python function with backtest execution
- Must include the sim() call and report assignment as shown above
- No syntax errors
- Follows all FinLab constraints
- Includes brief inline comments
- Maximum 50 lines for strategy function"""

    # ========================================================================
    # Private Helper Methods - Formatting
    # ========================================================================

    def _format_list(self, items: List[str]) -> str:
        """Format list with bullet points."""
        if not items:
            return "- None"
        return "\n".join(f"- {item}" for item in items)

    def _format_failure_patterns(
        self,
        patterns: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Convert failure pattern dicts to readable strings.

        Args:
            patterns: List of failure pattern dictionaries

        Returns:
            List of formatted failure descriptions
        """
        formatted = []
        for pattern in patterns:
            desc = pattern.get('description', 'Unknown pattern')
            impact = pattern.get('performance_impact', 0)

            # Format with impact
            if impact < 0:
                formatted.append(f"{desc} (Impact: {impact:.2%} degradation)")
            else:
                formatted.append(desc)

        return formatted

    def _truncate_to_budget(self, prompt: str) -> str:
        """
        Truncate prompt to stay within token budget.

        Args:
            prompt: Full prompt text

        Returns:
            Truncated prompt if needed
        """
        if len(prompt) <= MAX_PROMPT_CHARS:
            return prompt

        # Truncate with warning
        truncated = prompt[:MAX_PROMPT_CHARS - 100]
        truncated += f"\n\n[... truncated to fit {MAX_PROMPT_TOKENS} token budget ...]"

        return truncated


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING PROMPT BUILDER")
    print("=" * 70)

    builder = PromptBuilder()

    # Test 1: Modification Prompt
    print("\n" + "=" * 70)
    print("Test 1: Modification Prompt")
    print("=" * 70)

    champion_code = """
def strategy(data):
    roe = data.get('fundamental_features:ROE稅後')
    return roe > 15
"""

    champion_metrics = {
        'sharpe_ratio': 0.85,
        'max_drawdown': 0.15,
        'win_rate': 0.58,
        'calmar_ratio': 2.3
    }

    mod_prompt = builder.build_modification_prompt(
        champion_code=champion_code,
        champion_metrics=champion_metrics,
        target_metric='sharpe_ratio'
    )

    print(f"\nModification Prompt Length: {len(mod_prompt)} chars")
    print(f"Estimated Tokens: ~{len(mod_prompt) // CHARS_PER_TOKEN}")
    print(f"\nPrompt Preview (first 500 chars):\n{mod_prompt[:500]}...")

    # Test 2: Creation Prompt
    print("\n" + "=" * 70)
    print("Test 2: Creation Prompt")
    print("=" * 70)

    creation_prompt = builder.build_creation_prompt(
        champion_approach="Momentum-based factor with ROE quality filter",
        innovation_directive="Explore value + quality combinations using P/B and profit margins"
    )

    print(f"\nCreation Prompt Length: {len(creation_prompt)} chars")
    print(f"Estimated Tokens: ~{len(creation_prompt) // CHARS_PER_TOKEN}")
    print(f"\nPrompt Preview (first 500 chars):\n{creation_prompt[:500]}...")

    # Test 3: Success Factor Extraction
    print("\n" + "=" * 70)
    print("Test 3: Success Factor Extraction")
    print("=" * 70)

    factors = builder.extract_success_factors(champion_code, champion_metrics)
    print(f"\nExtracted {len(factors)} success factors:")
    for i, factor in enumerate(factors, 1):
        print(f"  {i}. {factor}")

    # Test 4: Failure Pattern Extraction
    print("\n" + "=" * 70)
    print("Test 4: Failure Pattern Extraction")
    print("=" * 70)

    patterns = builder.extract_failure_patterns()
    print(f"\nExtracted {len(patterns)} failure patterns")
    if patterns:
        print(f"\nFirst pattern:")
        print(f"  Type: {patterns[0].get('pattern_type')}")
        print(f"  Description: {patterns[0].get('description')}")
        print(f"  Impact: {patterns[0].get('performance_impact', 0):.2%}")

    print("\n" + "=" * 70)
    print("PROMPT BUILDER TEST COMPLETE")
    print("=" * 70)
