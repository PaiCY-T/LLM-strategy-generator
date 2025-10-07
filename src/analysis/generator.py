"""
Suggestion generation from backtest results using Claude AI.

Analyzes backtest results and generates actionable improvement suggestions
based on performance metrics, trade patterns, and risk characteristics.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from ..backtest import BacktestResult, PerformanceMetrics
from . import Suggestion, SuggestionCategory
from .claude_client import ClaudeClient

# Configure logging
logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """Generates improvement suggestions using Claude AI.

    Analyzes backtest results to identify areas for improvement and
    generates specific, actionable suggestions with impact/difficulty scores.
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        min_suggestions: int = 3,
        max_suggestions: int = 5
    ) -> None:
        """Initialize suggestion generator.

        Args:
            claude_client: Configured Claude API client
            min_suggestions: Minimum number of suggestions to generate
            max_suggestions: Maximum number of suggestions to generate
        """
        self.claude_client = claude_client
        self.min_suggestions = min_suggestions
        self.max_suggestions = max_suggestions

    async def generate_suggestions(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Suggestion]:
        """Generate improvement suggestions from backtest results.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context (strategy code, history, etc.)

        Returns:
            List of improvement suggestions

        Raises:
            RuntimeError: If suggestion generation fails
        """
        try:
            # Build analysis prompt
            prompt = self._build_analysis_prompt(
                backtest_result,
                performance_metrics,
                context
            )

            # Get Claude's analysis
            logger.info("Requesting suggestions from Claude API...")
            response = await self.claude_client.generate_analysis(
                prompt=prompt,
                system_prompt=self._get_system_prompt(),
                max_tokens=4096,
                temperature=0.7
            )

            # Parse suggestions from response
            suggestions = self._parse_suggestions(response)

            # Validate and filter
            valid_suggestions = self._validate_suggestions(suggestions)

            if len(valid_suggestions) < self.min_suggestions:
                logger.warning(
                    f"Only {len(valid_suggestions)} valid suggestions generated, "
                    f"expected at least {self.min_suggestions}"
                )

            logger.info(f"Generated {len(valid_suggestions)} suggestions")
            return valid_suggestions[:self.max_suggestions]

        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            raise RuntimeError(f"Failed to generate suggestions: {e}") from e

    def _build_analysis_prompt(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build analysis prompt for Claude.

        Args:
            backtest_result: Backtest result
            performance_metrics: Performance metrics
            context: Optional context

        Returns:
            Formatted prompt string
        """
        # Build performance summary
        perf_summary = f"""
**Performance Metrics:**
- Annualized Return: {performance_metrics.annualized_return:.2%}
- Sharpe Ratio: {performance_metrics.sharpe_ratio:.2f}
- Max Drawdown: {performance_metrics.max_drawdown:.2%}
- Win Rate: {performance_metrics.win_rate:.2%}
- Profit Factor: {performance_metrics.profit_factor:.2f}
- Total Trades: {performance_metrics.total_trades}
- Avg Holding Period: {performance_metrics.avg_holding_period:.1f} days
- Best Trade: {performance_metrics.best_trade:.2%}
- Worst Trade: {performance_metrics.worst_trade:.2%}
"""

        # Build trade analysis
        trade_count = len(backtest_result.trade_records)
        trade_summary = f"\n**Trade Analysis:**\n- Total Trades: {trade_count}\n"

        # Add context if provided
        context_str = ""
        if context:
            if "strategy_code" in context:
                context_str += "\n**Strategy Code:**\n```python\n"
                context_str += context["strategy_code"]
                context_str += "\n```\n"
            if "iteration_number" in context:
                context_str += f"\n**Iteration:** {context['iteration_number']}\n"

        # Build full prompt
        min_s = self.min_suggestions
        max_s = self.max_suggestions
        prompt = f"""
Analyze this trading strategy backtest result and provide {min_s}-{max_s} \
specific improvement suggestions.

{perf_summary}
{trade_summary}
{context_str}

**Instructions:**
1. Identify the most impactful areas for improvement
2. For each suggestion, provide:
   - Category (risk_management, entry_exit_conditions, position_sizing,
     timing_optimization, diversification, or cost_reduction)
   - Title (concise, actionable)
   - Description (detailed explanation)
   - Rationale (why this will help)
   - Implementation Hint (how to implement)
   - Impact Score (1-10, expected performance improvement)
   - Difficulty Score (1-10, implementation complexity)

3. Focus on:
   - Risk management if max drawdown is concerning
   - Win rate optimization if it's below 50%
   - Position sizing if profit factor is low
   - Exit timing if holding period is suboptimal
   - Entry conditions if trade count is too low/high

**Response Format:**
Return a JSON array of suggestions. Each suggestion must have:
{{
  "category": "string",
  "title": "string",
  "description": "string",
  "rationale": "string",
  "implementation_hint": "string",
  "impact_score": number,
  "difficulty_score": number
}}

**IMPORTANT:** Return ONLY the JSON array, no additional text.
"""
        return prompt

    def _get_system_prompt(self) -> str:
        """Get system prompt for Claude.

        Returns:
            System prompt string
        """
        return """
You are an expert quantitative trading strategy analyst specializing in Taiwan stock market.
You analyze backtest results and provide specific, actionable improvement suggestions.

Your suggestions should be:
1. Data-driven: Based on actual metrics, not assumptions
2. Specific: Clear, actionable recommendations
3. Prioritized: High impact, reasonable difficulty
4. Realistic: Implementable for weekly/monthly trading cycles
5. Risk-aware: Always consider risk management

Focus on practical improvements that can be implemented by retail traders.
"""

    def _parse_suggestions(self, response: str) -> List[Suggestion]:
        """Parse suggestions from Claude's response.

        Args:
            response: Raw response from Claude

        Returns:
            List of parsed suggestions

        Raises:
            ValueError: If parsing fails
        """
        try:
            # Extract JSON from response (handle potential markdown code blocks)
            json_str = response.strip()

            # Remove markdown code blocks if present
            if json_str.startswith("```"):
                lines = json_str.split("\n")
                # Find first and last non-``` lines
                start = 0
                end = len(lines)
                for i, line in enumerate(lines):
                    if not line.strip().startswith("```"):
                        start = i
                        break
                for i in range(len(lines) - 1, -1, -1):
                    if not lines[i].strip().startswith("```"):
                        end = i + 1
                        break
                json_str = "\n".join(lines[start:end])

            # Parse JSON
            data = json.loads(json_str)

            if not isinstance(data, list):
                raise ValueError("Expected JSON array of suggestions")

            # Convert to Suggestion objects
            suggestions = []
            for item in data:
                try:
                    # Map category string to enum
                    category_str = item["category"].lower()
                    category = self._parse_category(category_str)

                    suggestion = Suggestion(
                        category=category,
                        title=item["title"],
                        description=item["description"],
                        rationale=item["rationale"],
                        implementation_hint=item["implementation_hint"],
                        impact_score=float(item["impact_score"]),
                        difficulty_score=float(item["difficulty_score"])
                    )
                    suggestions.append(suggestion)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse suggestion: {e}")
                    continue

            return suggestions

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response: {response}")
            raise ValueError(f"Failed to parse JSON response: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error parsing suggestions: {e}")
            raise

    def _parse_category(self, category_str: str) -> SuggestionCategory:
        """Parse category string to enum.

        Args:
            category_str: Category string

        Returns:
            SuggestionCategory enum value

        Raises:
            ValueError: If category is invalid
        """
        category_map = {
            "risk_management": SuggestionCategory.RISK_MANAGEMENT,
            "entry_exit_conditions": SuggestionCategory.ENTRY_EXIT_CONDITIONS,
            "position_sizing": SuggestionCategory.POSITION_SIZING,
            "timing_optimization": SuggestionCategory.TIMING_OPTIMIZATION,
            "diversification": SuggestionCategory.DIVERSIFICATION,
            "cost_reduction": SuggestionCategory.COST_REDUCTION
        }

        if category_str not in category_map:
            raise ValueError(f"Invalid category: {category_str}")

        return category_map[category_str]

    def _validate_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Validate and filter suggestions.

        Args:
            suggestions: List of suggestions to validate

        Returns:
            List of valid suggestions
        """
        valid = []

        for suggestion in suggestions:
            # Validate scores
            if not (1 <= suggestion.impact_score <= 10):
                logger.warning(
                    f"Invalid impact score {suggestion.impact_score} "
                    f"for suggestion: {suggestion.title}"
                )
                continue

            if not (1 <= suggestion.difficulty_score <= 10):
                logger.warning(
                    f"Invalid difficulty score {suggestion.difficulty_score} "
                    f"for suggestion: {suggestion.title}"
                )
                continue

            # Validate required fields
            if not suggestion.title or not suggestion.description:
                logger.warning("Suggestion missing required fields")
                continue

            valid.append(suggestion)

        return valid
