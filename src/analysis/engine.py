"""
Main analysis engine implementation.

Orchestrates AI-powered and rule-based analysis to generate
comprehensive strategy improvement suggestions.
"""

import logging
from typing import Any, Dict, List, Optional

from ..backtest import BacktestResult, PerformanceMetrics
from . import AnalysisReport, Suggestion
from .claude_client import CircuitState, ClaudeClient
from .fallback import FallbackAnalyzer
from .generator import SuggestionGenerator
from .ranking import SuggestionRanker

# Configure logging
logger = logging.getLogger(__name__)


class AnalysisEngineImpl:
    """Main analysis engine implementation.

    Coordinates AI-powered and rule-based analysis to generate
    ranked improvement suggestions with automatic fallback.
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        min_suggestions: int = 3,
        max_suggestions: int = 5,
        impact_weight: float = 2.0,
        difficulty_weight: float = 1.0,
        enable_fallback: bool = True
    ) -> None:
        """Initialize analysis engine.

        Args:
            claude_client: Configured Claude API client
            min_suggestions: Minimum number of suggestions to generate
            max_suggestions: Maximum number of suggestions to generate
            impact_weight: Weight for impact in ranking
            difficulty_weight: Weight for difficulty in ranking
            enable_fallback: Whether to use fallback analyzer on API failure
        """
        self.claude_client = claude_client

        # Initialize components
        self.generator = SuggestionGenerator(
            claude_client=claude_client,
            min_suggestions=min_suggestions,
            max_suggestions=max_suggestions
        )

        self.ranker = SuggestionRanker(
            impact_weight=impact_weight,
            difficulty_weight=difficulty_weight
        )

        self.fallback = FallbackAnalyzer() if enable_fallback else None
        self.enable_fallback = enable_fallback

        logger.info(
            f"AnalysisEngine initialized with min={min_suggestions}, "
            f"max={max_suggestions}, fallback={enable_fallback}"
        )

    async def analyze_strategy(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisReport:
        """Analyze strategy and generate improvement suggestions.

        Generates suggestions using Claude AI, with automatic fallback
        to rule-based analysis if API is unavailable. Ranks suggestions
        by priority and returns comprehensive analysis report.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context (strategy code, history, etc.)

        Returns:
            AnalysisReport with suggestions and metadata

        Raises:
            RuntimeError: If analysis fails and no fallback available
        """
        logger.info("Starting strategy analysis...")

        # Generate suggestions
        suggestions = await self.generate_suggestions(
            backtest_result,
            performance_metrics,
            context
        )

        # Rank suggestions
        ranked_suggestions = self.ranker.rank_suggestions(suggestions)

        # Build metadata
        top_priority = (
            ranked_suggestions[0].priority_score if ranked_suggestions else 0.0
        )
        metadata = {
            "suggestion_count": len(ranked_suggestions),
            "analysis_method": self._get_analysis_method(),
            "circuit_breaker_state": self.claude_client.get_circuit_state().value,
            "top_priority_score": top_priority
        }

        if context:
            metadata.update(context)

        logger.info(
            f"Analysis complete: {len(ranked_suggestions)} suggestions, "
            f"method={metadata['analysis_method']}"
        )

        return AnalysisReport(
            backtest_result=backtest_result,
            performance_metrics=performance_metrics,
            suggestions=ranked_suggestions,
            analysis_metadata=metadata
        )

    async def generate_suggestions(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Suggestion]:
        """Generate improvement suggestions.

        Tries Claude AI first, falls back to rule-based analysis if needed.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context information

        Returns:
            List of improvement suggestions

        Raises:
            RuntimeError: If both AI and fallback fail
        """
        # Check circuit breaker state
        circuit_state = self.claude_client.get_circuit_state()

        # Try AI-powered generation if circuit is not open
        if circuit_state != CircuitState.OPEN:
            try:
                logger.info("Attempting AI-powered suggestion generation...")
                suggestions = await self.generator.generate_suggestions(
                    backtest_result,
                    performance_metrics,
                    context
                )

                if suggestions:
                    logger.info(f"AI generated {len(suggestions)} suggestions")
                    return suggestions

            except Exception as e:
                logger.warning(f"AI suggestion generation failed: {e}")

                if not self.enable_fallback:
                    raise RuntimeError(
                        f"AI suggestion generation failed and fallback disabled: {e}"
                    ) from e

        # Use fallback analyzer
        if self.fallback:
            logger.info("Using fallback rule-based analysis...")
            suggestions = self.fallback.generate_suggestions(
                backtest_result,
                performance_metrics,
                context
            )

            if suggestions:
                logger.info(f"Fallback generated {len(suggestions)} suggestions")
                return suggestions

            raise RuntimeError("Fallback analyzer failed to generate suggestions")

        raise RuntimeError(
            "Failed to generate suggestions: AI unavailable and fallback disabled"
        )

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Rank suggestions by priority.

        Args:
            suggestions: List of suggestions to rank

        Returns:
            Sorted list of suggestions (highest priority first)
        """
        return self.ranker.rank_suggestions(suggestions)

    def _get_analysis_method(self) -> str:
        """Determine which analysis method was used.

        Returns:
            Method name string
        """
        circuit_state = self.claude_client.get_circuit_state()

        if circuit_state == CircuitState.OPEN:
            return "fallback_only"
        elif circuit_state == CircuitState.HALF_OPEN:
            return "ai_testing"
        else:
            return "ai_primary"

    def get_status(self) -> Dict[str, Any]:
        """Get engine status information.

        Returns:
            Dictionary with status information
        """
        return {
            "circuit_state": self.claude_client.get_circuit_state().value,
            "fallback_enabled": self.enable_fallback,
            "ranker_weights": {
                "impact": self.ranker.impact_weight,
                "difficulty": self.ranker.difficulty_weight
            }
        }
