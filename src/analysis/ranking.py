"""
Suggestion ranking with weighted scoring system.

Ranks suggestions by priority based on impact potential and
implementation difficulty using configurable weighting.
"""

import logging
from typing import Any, Dict, List

from . import Suggestion

# Configure logging
logger = logging.getLogger(__name__)


class SuggestionRanker:
    """Ranks suggestions by priority.

    Uses weighted scoring to prioritize high-impact, low-difficulty
    suggestions while considering user preferences and learning history.

    Priority Formula:
        priority_score = (impact_score * impact_weight - difficulty_score * difficulty_weight) / 2

    Default weights emphasize impact over difficulty (2:1 ratio).
    """

    def __init__(
        self,
        impact_weight: float = 2.0,
        difficulty_weight: float = 1.0
    ) -> None:
        """Initialize suggestion ranker.

        Args:
            impact_weight: Weight for impact score (default: 2.0)
            difficulty_weight: Weight for difficulty score (default: 1.0)
        """
        if impact_weight <= 0:
            raise ValueError("impact_weight must be positive")
        if difficulty_weight <= 0:
            raise ValueError("difficulty_weight must be positive")

        self.impact_weight = impact_weight
        self.difficulty_weight = difficulty_weight

        logger.info(
            f"SuggestionRanker initialized with "
            f"impact_weight={impact_weight}, difficulty_weight={difficulty_weight}"
        )

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Rank suggestions by priority.

        Recalculates priority scores using configured weights and
        sorts suggestions in descending order of priority.

        Args:
            suggestions: List of suggestions to rank

        Returns:
            Sorted list of suggestions (highest priority first)
        """
        if not suggestions:
            logger.warning("No suggestions to rank")
            return []

        # Recalculate priority scores with custom weights
        for suggestion in suggestions:
            suggestion.priority_score = self._calculate_priority(
                suggestion.impact_score,
                suggestion.difficulty_score
            )

        # Sort by priority (descending)
        ranked = sorted(
            suggestions,
            key=lambda s: s.priority_score,
            reverse=True
        )

        logger.info(
            f"Ranked {len(ranked)} suggestions. "
            f"Top priority: {ranked[0].priority_score:.2f}"
        )

        return ranked

    def _calculate_priority(self, impact: float, difficulty: float) -> float:
        """Calculate priority score.

        Args:
            impact: Impact score (1-10)
            difficulty: Difficulty score (1-10)

        Returns:
            Priority score
        """
        return (impact * self.impact_weight - difficulty * self.difficulty_weight) / 2

    def get_top_n(
        self,
        suggestions: List[Suggestion],
        n: int
    ) -> List[Suggestion]:
        """Get top N suggestions by priority.

        Args:
            suggestions: List of suggestions
            n: Number of top suggestions to return

        Returns:
            Top N suggestions (sorted by priority)
        """
        if n <= 0:
            raise ValueError("n must be positive")

        ranked = self.rank_suggestions(suggestions)
        return ranked[:n]

    def filter_by_category(
        self,
        suggestions: List[Suggestion],
        categories: List[str]
    ) -> List[Suggestion]:
        """Filter suggestions by category.

        Args:
            suggestions: List of suggestions
            categories: List of category names to include

        Returns:
            Filtered and ranked suggestions
        """
        filtered = [
            s for s in suggestions
            if s.category.value in categories
        ]

        return self.rank_suggestions(filtered)

    def filter_by_threshold(
        self,
        suggestions: List[Suggestion],
        min_impact: float = 0.0,
        max_difficulty: float = 10.0,
        min_priority: float = 0.0
    ) -> List[Suggestion]:
        """Filter suggestions by score thresholds.

        Args:
            suggestions: List of suggestions
            min_impact: Minimum impact score
            max_difficulty: Maximum difficulty score
            min_priority: Minimum priority score

        Returns:
            Filtered and ranked suggestions
        """
        filtered = [
            s for s in suggestions
            if (s.impact_score >= min_impact and
                s.difficulty_score <= max_difficulty and
                s.priority_score >= min_priority)
        ]

        return self.rank_suggestions(filtered)


class AdaptiveRanker(SuggestionRanker):
    """Adaptive ranker that learns from user feedback.

    Adjusts ranking weights based on historical acceptance patterns
    to improve future suggestion prioritization.
    """

    def __init__(
        self,
        impact_weight: float = 2.0,
        difficulty_weight: float = 1.0,
        learning_rate: float = 0.1
    ) -> None:
        """Initialize adaptive ranker.

        Args:
            impact_weight: Initial weight for impact score
            difficulty_weight: Initial weight for difficulty score
            learning_rate: How quickly to adapt weights (0-1)
        """
        super().__init__(impact_weight, difficulty_weight)

        if not 0 < learning_rate <= 1:
            raise ValueError("learning_rate must be in (0, 1]")

        self.learning_rate = learning_rate
        self.feedback_history: List[Dict[str, Any]] = []

        logger.info(f"AdaptiveRanker initialized with learning_rate={learning_rate}")

    def record_feedback(
        self,
        suggestion: Suggestion,
        accepted: bool,
        improvement: float = 0.0
    ) -> None:
        """Record user feedback on a suggestion.

        Args:
            suggestion: The suggestion that received feedback
            accepted: Whether the suggestion was accepted
            improvement: Actual performance improvement (if accepted)
        """
        feedback = {
            "category": suggestion.category.value,
            "impact_score": suggestion.impact_score,
            "difficulty_score": suggestion.difficulty_score,
            "priority_score": suggestion.priority_score,
            "accepted": accepted,
            "improvement": improvement
        }

        self.feedback_history.append(feedback)

        # Adapt weights based on feedback
        if len(self.feedback_history) >= 5:
            self._adapt_weights()

        logger.debug(
            f"Recorded feedback: accepted={accepted}, "
            f"improvement={improvement:.4f}"
        )

    def _adapt_weights(self) -> None:
        """Adapt ranking weights based on feedback history.

        Analyzes acceptance patterns and adjusts weights to better
        predict which suggestions users find valuable.
        """
        if len(self.feedback_history) < 5:
            return

        # Calculate acceptance rate by score ranges
        accepted_feedback = [f for f in self.feedback_history if f["accepted"]]

        if not accepted_feedback:
            return

        # Calculate average scores for accepted suggestions
        n = len(accepted_feedback)
        avg_impact = sum(f["impact_score"] for f in accepted_feedback) / n
        avg_difficulty = (
            sum(f["difficulty_score"] for f in accepted_feedback) / n
        )

        # Adjust weights based on patterns
        # If accepted suggestions tend to have higher impact, increase impact weight
        if avg_impact > 7.0:
            adjustment = self.learning_rate * 0.1
            self.impact_weight += adjustment
            logger.debug(f"Increased impact_weight by {adjustment:.3f}")

        # If accepted suggestions tend to have lower difficulty, increase difficulty weight
        if avg_difficulty < 4.0:
            adjustment = self.learning_rate * 0.1
            self.difficulty_weight += adjustment
            logger.debug(f"Increased difficulty_weight by {adjustment:.3f}")

        logger.info(
            f"Adapted weights: impact={self.impact_weight:.2f}, "
            f"difficulty={self.difficulty_weight:.2f}"
        )

    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics.

        Returns:
            Dictionary with learning metrics
        """
        if not self.feedback_history:
            return {
                "total_feedback": 0,
                "acceptance_rate": 0.0,
                "avg_improvement": 0.0,
                "current_weights": {
                    "impact": self.impact_weight,
                    "difficulty": self.difficulty_weight
                }
            }

        accepted = [f for f in self.feedback_history if f["accepted"]]
        acceptance_rate = len(accepted) / len(self.feedback_history)

        improvements = [
            f["improvement"] for f in accepted if f["improvement"] > 0
        ]
        avg_improvement = (
            sum(improvements) / len(improvements) if improvements else 0.0
        )

        return {
            "total_feedback": len(self.feedback_history),
            "acceptance_rate": acceptance_rate,
            "avg_improvement": avg_improvement,
            "current_weights": {
                "impact": self.impact_weight,
                "difficulty": self.difficulty_weight
            }
        }
