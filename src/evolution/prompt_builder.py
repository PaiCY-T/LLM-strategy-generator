"""
Prompt builder for evolutionary strategy generation.

This module provides specialized prompt generation for NSGA-II population-based
learning, enabling LLM-based genetic operations (crossover, mutation, initialization).

Key Components:
- PromptBuilder: Central prompt generation coordinator
- build_crossover_prompt: Blend two parent strategies
- build_mutation_prompt: Generate mutated offspring
- build_initialization_prompt: Create new strategies from templates

Design Principles:
- Genetic Diversity: Encourage exploration while preserving successful patterns
- Code Quality: Generate syntactically correct, maintainable code
- Domain Knowledge: Incorporate financial trading constraints and best practices
- Explainability: Include rationale for genetic operations
"""

import logging
from typing import Any, Dict, Optional
from src.evolution.types import Strategy

logger: logging.Logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Prompt builder for evolutionary strategy generation.

    Generates specialized prompts for LLM-based genetic operations in the
    NSGA-II population-based learning system. Supports crossover, mutation,
    and initialization operations with domain-specific constraints.

    Attributes:
        base_constraints: Common constraints applied to all prompts
        template_guidelines: Template-specific generation guidelines

    Example:
        >>> builder = PromptBuilder()
        >>> prompt = builder.build_crossover_prompt(parent1, parent2)
        >>> # Use prompt with LLM to generate offspring code
    """

    def __init__(self):
        """Initialize PromptBuilder with common constraints and guidelines."""
        self.base_constraints = self._get_base_constraints()
        self.template_guidelines = self._get_template_guidelines()

        logger.info("PromptBuilder initialized for evolutionary operations")

    def _get_base_constraints(self) -> str:
        """
        Get base constraints applied to all prompts.

        Returns:
            Common constraints for code generation
        """
        return """
## CODE REQUIREMENTS

### Security & Safety
- NO import statements (data.get() provides all needed data)
- NO exec(), eval(), or other dangerous functions
- NO file I/O operations
- Use only positive shift values: .shift(1), .shift(2), etc.

### Code Quality
- Clear variable names and inline comments
- Proper error handling for edge cases
- Efficient pandas operations (vectorized when possible)
- Avoid look-ahead bias (only use past data)

### Data Access
- Use data.get('dataset_name') to access data
- Available datasets: 'price:收盤價', 'revenue:當月營收', 'price_earning_ratio:本益比', etc.
- All data is aligned to the same time index

### Strategy Structure
```python
# 1. Data retrieval and preprocessing
close = data.get('price:收盤價')
# ... other data sources

# 2. Factor calculation
factor1 = ...  # Calculate first factor
factor2 = ...  # Calculate second factor

# 3. Composite signal
signal = factor1 * weight1 + factor2 * weight2

# 4. Stock filtering and ranking
filtered_signal = signal[filters]  # Apply liquidity/quality filters
selected = filtered_signal.rank(axis=1, ascending=False) <= n_stocks

# 5. Position sizing (equal weight or factor-weighted)
positions = selected.astype(float) / selected.sum(axis=1)
```

### Output Requirements
- MUST return only valid Python code (no markdown, no explanations)
- Code should be self-contained and executable
- Include inline comments explaining logic
"""

    def _get_template_guidelines(self) -> Dict[str, str]:
        """
        Get template-specific generation guidelines.

        Returns:
            Dictionary mapping template types to their guidelines
        """
        return {
            'Momentum': """
### Momentum Template Guidelines
- Focus on price momentum, trend strength, and relative performance
- Use rolling returns, moving averages, or rate of change
- Consider multiple timeframes (20d, 60d, 120d)
- Apply liquidity filters to ensure tradability
- Example factors: 12-month momentum, 3-month reversal, moving average crossover
""",
            'Value': """
### Value Template Guidelines
- Focus on valuation metrics (P/E, P/B, EV/EBITDA)
- Consider fundamental quality (ROE, profit margins, debt levels)
- Use ranking or z-score normalization
- Filter for financial stability
- Example factors: earnings yield, book-to-market, FCF yield
""",
            'Quality': """
### Quality Template Guidelines
- Focus on profitability, growth stability, and financial health
- Use ROE, ROA, profit margin, earnings growth
- Consider consistency metrics (rolling std, coefficient of variation)
- Apply smoothing to reduce noise
- Example factors: ROE trend, earnings quality, debt-to-equity
""",
            'Mixed': """
### Mixed Template Guidelines
- Combine multiple factor types (momentum + value + quality)
- Balance factor weights for diversification
- Use orthogonal factors to reduce correlation
- Apply robust normalization and outlier handling
- Example: 40% momentum + 30% value + 30% quality
"""
        }

    def build_crossover_prompt(
        self,
        parent1: Strategy,
        parent2: Strategy
    ) -> str:
        """
        Generate prompt for crossover operation blending two parent strategies.

        Creates a detailed prompt instructing the LLM to combine successful
        elements from both parents while maintaining code quality and introducing
        beneficial genetic diversity.

        Args:
            parent1: First parent strategy
            parent2: Second parent strategy

        Returns:
            Complete prompt string for LLM-based crossover

        Example:
            >>> prompt = builder.build_crossover_prompt(parent1, parent2)
            >>> offspring_code = llm.generate(prompt)
        """
        logger.debug(
            f"Building crossover prompt: {parent1.id[:8]} x {parent2.id[:8]}"
        )

        # Extract parent information
        parent1_params = parent1.parameters
        parent2_params = parent2.parameters

        parent1_metrics = self._format_metrics(parent1.metrics)
        parent2_metrics = self._format_metrics(parent2.metrics)

        # Build prompt sections
        sections = []

        sections.append("=" * 70)
        sections.append("GENETIC CROSSOVER: BLEND TWO SUCCESSFUL STRATEGIES")
        sections.append("=" * 70)
        sections.append("")

        sections.append("## OBJECTIVE")
        sections.append("")
        sections.append("Create an OFFSPRING strategy by combining the best elements from")
        sections.append("two parent strategies. The offspring should inherit successful")
        sections.append("characteristics from both parents while potentially discovering")
        sections.append("synergies between their approaches.")
        sections.append("")

        sections.append("## PARENT 1 INFORMATION")
        sections.append("")
        sections.append(f"ID: {parent1.id}")
        sections.append(f"Generation: {parent1.generation}")
        sections.append(f"Template: {parent1.template_type or 'Mixed'}")
        sections.append("")
        sections.append("Performance:")
        sections.append(parent1_metrics)
        sections.append("")
        sections.append("Parameters:")
        sections.append(self._format_parameters(parent1_params))
        sections.append("")
        sections.append("Code:")
        sections.append("```python")
        sections.append(parent1.code)
        sections.append("```")
        sections.append("")

        sections.append("## PARENT 2 INFORMATION")
        sections.append("")
        sections.append(f"ID: {parent2.id}")
        sections.append(f"Generation: {parent2.generation}")
        sections.append(f"Template: {parent2.template_type or 'Mixed'}")
        sections.append("")
        sections.append("Performance:")
        sections.append(parent2_metrics)
        sections.append("")
        sections.append("Parameters:")
        sections.append(self._format_parameters(parent2_params))
        sections.append("")
        sections.append("Code:")
        sections.append("```python")
        sections.append(parent2.code)
        sections.append("```")
        sections.append("")

        sections.append("## CROSSOVER INSTRUCTIONS")
        sections.append("")
        sections.append("Create offspring by combining elements from both parents:")
        sections.append("")
        sections.append("1. **Factor Combination**:")
        sections.append("   - Include factors from BOTH parents")
        sections.append("   - Blend factor weights (e.g., average, weighted by performance)")
        sections.append("   - Consider synergies between parent factors")
        sections.append("")
        sections.append("2. **Parameter Blending**:")
        sections.append("   - Lookback periods: Use intermediate value or weighted average")
        sections.append("   - Thresholds: Blend based on parent performance")
        sections.append("   - Stock count: Average or performance-weighted")
        sections.append("")
        sections.append("3. **Logic Integration**:")
        sections.append("   - Combine preprocessing approaches (smoothing, outlier handling)")
        sections.append("   - Merge filtering criteria (liquidity, quality, both)")
        sections.append("   - Integrate ranking/scoring methods")
        sections.append("")
        sections.append("4. **Genetic Diversity**:")
        sections.append("   - Don't just copy parent code - create meaningful synthesis")
        sections.append("   - Explore interactions between parent approaches")
        sections.append("   - Introduce minor variations (±5-10%) to explore nearby space")
        sections.append("")

        sections.append(self.base_constraints)
        sections.append("")

        sections.append("## EXPECTED OUTPUT")
        sections.append("")
        sections.append("Return ONLY executable Python code (no markdown, no explanations).")
        sections.append("The code should represent a novel strategy combining both parents.")
        sections.append("")
        sections.append("=" * 70)

        prompt = "\n".join(sections)

        logger.debug(f"Crossover prompt generated: {len(prompt)} characters")

        return prompt

    def build_mutation_prompt(
        self,
        strategy: Strategy,
        mutated_params: Dict[str, Any],
        exit_mutation_enabled: bool = False
    ) -> str:
        """
        Generate prompt for mutation operation with parameter modifications.

        Creates a detailed prompt instructing the LLM to regenerate the strategy
        code based on mutated parameters while preserving the core approach.

        Task 1.6: Added exit_mutation_enabled parameter to optionally include
        exit mutation context in the prompt.

        Args:
            strategy: Original strategy to mutate
            mutated_params: Mutated parameter dictionary
            exit_mutation_enabled: Include exit mutation examples/context (default: False)

        Returns:
            Complete prompt string for LLM-based mutation

        Example:
            >>> mutated_params = {'lookback': 25, 'threshold': 0.52}
            >>> prompt = builder.build_mutation_prompt(strategy, mutated_params)
            >>> mutant_code = llm.generate(prompt)
        """
        logger.debug(
            f"Building mutation prompt: {strategy.id[:8]} with "
            f"{len(mutated_params)} mutated parameters"
        )

        # Build prompt sections
        sections = []

        sections.append("=" * 70)
        sections.append("GENETIC MUTATION: MODIFY STRATEGY PARAMETERS")
        sections.append("=" * 70)
        sections.append("")

        sections.append("## OBJECTIVE")
        sections.append("")
        sections.append("Modify the existing strategy by updating its parameters while")
        sections.append("PRESERVING the core logic and structure. This introduces controlled")
        sections.append("variation to explore nearby regions of the solution space.")
        sections.append("")

        sections.append("## ORIGINAL STRATEGY")
        sections.append("")
        sections.append(f"ID: {strategy.id}")
        sections.append(f"Generation: {strategy.generation}")
        sections.append(f"Template: {strategy.template_type or 'Mixed'}")
        sections.append("")
        sections.append("Performance:")
        sections.append(self._format_metrics(strategy.metrics))
        sections.append("")
        sections.append("Original Parameters:")
        sections.append(self._format_parameters(strategy.parameters))
        sections.append("")
        sections.append("Original Code:")
        sections.append("```python")
        sections.append(strategy.code)
        sections.append("```")
        sections.append("")

        sections.append("## PARAMETER MUTATIONS")
        sections.append("")
        sections.append("Apply these parameter changes to the strategy:")
        sections.append("")

        # Show parameter changes
        for key, new_value in mutated_params.items():
            old_value = strategy.parameters.get(key, "N/A")

            if key == 'factor_weights' and isinstance(new_value, dict):
                sections.append(f"### {key}:")
                if isinstance(old_value, dict):
                    for factor, weight in new_value.items():
                        old_weight = old_value.get(factor, "N/A")
                        if isinstance(old_weight, (int, float)):
                            sections.append(
                                f"  - {factor}: {old_weight:.4f} → {weight:.4f}"
                            )
                        else:
                            sections.append(
                                f"  - {factor}: {old_weight} → {weight:.4f}"
                            )
                else:
                    for factor, weight in new_value.items():
                        sections.append(f"  - {factor}: {weight:.4f}")
            else:
                sections.append(f"- {key}: {old_value} → {new_value}")

        sections.append("")

        sections.append("## MUTATION INSTRUCTIONS")
        sections.append("")
        sections.append("Regenerate the strategy code with these guidelines:")
        sections.append("")
        sections.append("1. **Preserve Core Logic**:")
        sections.append("   - Keep the same factor types and calculation methods")
        sections.append("   - Maintain the overall structure and flow")
        sections.append("   - Preserve data sources and preprocessing approach")
        sections.append("")
        sections.append("2. **Apply Parameter Changes**:")
        sections.append("   - Update ALL mutated parameters in the code")
        sections.append("   - Adjust lookback periods, thresholds, weights as specified")
        sections.append("   - Ensure parameter changes are reflected correctly")
        sections.append("")
        sections.append("3. **Maintain Quality**:")
        sections.append("   - Keep code clean and well-commented")
        sections.append("   - Preserve error handling and edge case management")
        sections.append("   - Ensure logical consistency after parameter changes")
        sections.append("")
        sections.append("4. **Minor Refinements Allowed**:")
        sections.append("   - Small improvements to code clarity are acceptable")
        sections.append("   - Bug fixes are allowed if obvious issues exist")
        sections.append("   - DO NOT change the fundamental approach")
        sections.append("")

        # Task 1.6: Add exit mutation context if enabled
        if exit_mutation_enabled:
            sections.append("## EXIT STRATEGY MUTATIONS (Phase 1)")
            sections.append("")
            sections.append("Exit mutations can improve risk-adjusted performance (Sharpe, Calmar, drawdown).")
            sections.append("Consider these exit strategy enhancements:")
            sections.append("")
            sections.append("**Exit Strategy Types:**")
            sections.append("1. **Stop-Loss**: Limit downside risk (e.g., exit when loss exceeds -5%)")
            sections.append("2. **Take-Profit**: Lock in gains (e.g., exit when profit exceeds +10%)")
            sections.append("3. **Trailing Stop**: Protect profits dynamically (e.g., trail by 3%)")
            sections.append("4. **Conditional Exit**: Exit based on market conditions or indicators")
            sections.append("")
            sections.append("**Example Exit Implementations:**")
            sections.append("```python")
            sections.append("# Fixed stop-loss and take-profit")
            sections.append("stop_loss = positions * (close < entry_price * 0.95)")
            sections.append("take_profit = positions * (close > entry_price * 1.10)")
            sections.append("positions = positions - stop_loss - take_profit")
            sections.append("")
            sections.append("# Trailing stop")
            sections.append("high_water_mark = close.rolling(20).max()")
            sections.append("trailing_stop = positions * (close < high_water_mark * 0.97)")
            sections.append("positions = positions - trailing_stop")
            sections.append("")
            sections.append("# Conditional exit (volatility spike)")
            sections.append("volatility = close.pct_change().rolling(10).std()")
            sections.append("vol_exit = positions * (volatility > volatility.rolling(60).quantile(0.95))")
            sections.append("positions = positions - vol_exit")
            sections.append("```")
            sections.append("")
            sections.append("**Note**: Exit strategies are OPTIONAL enhancements. Only add if appropriate")
            sections.append("for the strategy's risk profile and trading style.")
            sections.append("")

        sections.append(self.base_constraints)
        sections.append("")

        sections.append("## EXPECTED OUTPUT")
        sections.append("")
        sections.append("Return ONLY executable Python code (no markdown, no explanations).")
        sections.append("The code should implement the SAME strategy with UPDATED parameters.")
        sections.append("")
        sections.append("=" * 70)

        prompt = "\n".join(sections)

        logger.debug(f"Mutation prompt generated: {len(prompt)} characters")

        return prompt

    def build_initialization_prompt(
        self,
        template_type: str = 'Mixed',
        generation: int = 0
    ) -> str:
        """
        Generate prompt for creating new strategy from template.

        Creates a detailed prompt for initializing a new strategy using
        template-specific guidelines. Used for population initialization
        and diversity injection.

        Args:
            template_type: Strategy template ('Momentum', 'Value', 'Quality', 'Mixed')
            generation: Generation number for context (default: 0)

        Returns:
            Complete prompt string for LLM-based initialization

        Example:
            >>> prompt = builder.build_initialization_prompt('Momentum')
            >>> strategy_code = llm.generate(prompt)
        """
        logger.debug(
            f"Building initialization prompt: template={template_type}, "
            f"generation={generation}"
        )

        # Build prompt sections
        sections = []

        sections.append("=" * 70)
        sections.append(f"STRATEGY INITIALIZATION: {template_type.upper()} TEMPLATE")
        sections.append("=" * 70)
        sections.append("")

        sections.append("## OBJECTIVE")
        sections.append("")
        sections.append(f"Create a NEW {template_type} trading strategy from scratch using")
        sections.append("the template guidelines below. This strategy will be part of a")
        sections.append("diverse population evolved using NSGA-II multi-objective optimization.")
        sections.append("")

        if generation == 0:
            sections.append("This is GENERATION 0 (initial population) - maximize diversity!")
            sections.append("")
        else:
            sections.append(f"This is GENERATION {generation} - creating diverse offspring.")
            sections.append("")

        # Add template-specific guidelines
        if template_type in self.template_guidelines:
            sections.append(self.template_guidelines[template_type])
            sections.append("")

        sections.append("## INITIALIZATION INSTRUCTIONS")
        sections.append("")
        sections.append("Create a novel strategy following these steps:")
        sections.append("")
        sections.append("1. **Data Selection**:")
        sections.append("   - Choose 2-4 relevant datasets for your template")
        sections.append("   - Consider data availability and quality")
        sections.append("   - Use diverse data sources (price, fundamentals, technical)")
        sections.append("")
        sections.append("2. **Factor Design**:")
        sections.append("   - Create 1-3 factors aligned with template philosophy")
        sections.append("   - Use proper normalization (rank, z-score, percentile)")
        sections.append("   - Apply smoothing if needed (rolling mean, EMA)")
        sections.append("")
        sections.append("3. **Signal Combination**:")
        sections.append("   - Combine factors with appropriate weights")
        sections.append("   - Weights should sum to 1.0 for factor_weights")
        sections.append("   - Consider factor orthogonality")
        sections.append("")
        sections.append("4. **Filtering & Selection**:")
        sections.append("   - Apply liquidity filters (volume, market cap)")
        sections.append("   - Add quality screens if appropriate")
        sections.append("   - Select top N stocks (typically 10-30)")
        sections.append("")
        sections.append("5. **Position Sizing**:")
        sections.append("   - Use equal weight or factor-weighted positions")
        sections.append("   - Ensure positions sum to 1.0 (100%)")
        sections.append("   - Handle edge cases (no valid stocks)")
        sections.append("")

        sections.append("## DIVERSITY CONSIDERATIONS")
        sections.append("")
        if generation == 0:
            sections.append("For initial population, ensure HIGH DIVERSITY:")
            sections.append("- Use different factor combinations")
            sections.append("- Vary lookback periods (20d, 60d, 120d, 252d)")
            sections.append("- Experiment with different thresholds and stock counts")
            sections.append("- Try various preprocessing approaches")
        else:
            sections.append("Maintain genetic diversity in the population:")
            sections.append("- Don't replicate existing strategies exactly")
            sections.append("- Explore different parameter combinations")
            sections.append("- Introduce novel factor interactions")

        sections.append("")

        sections.append(self.base_constraints)
        sections.append("")

        sections.append("## EXPECTED OUTPUT")
        sections.append("")
        sections.append("Return ONLY executable Python code (no markdown, no explanations).")
        sections.append(f"The code should implement a {template_type} strategy following")
        sections.append("the template guidelines above.")
        sections.append("")
        sections.append("=" * 70)

        prompt = "\n".join(sections)

        logger.debug(f"Initialization prompt generated: {len(prompt)} characters")

        return prompt

    def _format_metrics(self, metrics: Optional[Any]) -> str:
        """
        Format strategy metrics for display in prompts.

        Args:
            metrics: MultiObjectiveMetrics instance or None

        Returns:
            Formatted metrics string
        """
        if metrics is None:
            return "  (Not yet evaluated)"

        lines = []
        lines.append(f"  - Sharpe Ratio: {metrics.sharpe_ratio:.4f}")
        lines.append(f"  - Calmar Ratio: {metrics.calmar_ratio:.4f}")
        lines.append(f"  - Max Drawdown: {metrics.max_drawdown:.4f}")
        lines.append(f"  - Total Return: {metrics.total_return:.4f}")
        lines.append(f"  - Win Rate: {metrics.win_rate:.4f}")
        lines.append(f"  - Annual Return: {metrics.annual_return:.4f}")

        return "\n".join(lines)

    def _format_parameters(self, params: Dict[str, Any]) -> str:
        """
        Format strategy parameters for display in prompts.

        Args:
            params: Parameter dictionary

        Returns:
            Formatted parameters string
        """
        if not params:
            return "  (No parameters)"

        lines = []
        for key, value in params.items():
            if key == 'factor_weights' and isinstance(value, dict):
                lines.append(f"  - {key}:")
                for factor, weight in value.items():
                    lines.append(f"      {factor}: {weight:.4f}")
            else:
                lines.append(f"  - {key}: {value}")

        return "\n".join(lines)
