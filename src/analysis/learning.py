"""
Learning engine that tracks suggestion feedback and improves over time.

Tracks user acceptance/rejection of suggestions and learns patterns
to improve future suggestion generation and ranking.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import Suggestion

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class FeedbackRecord:
    """Record of user feedback on a suggestion.

    Attributes:
        timestamp: When feedback was recorded
        category: Suggestion category
        title: Suggestion title
        impact_score: Suggested impact score
        difficulty_score: Suggested difficulty score
        accepted: Whether user accepted the suggestion
        actual_improvement: Actual performance improvement (if measured)
        notes: Optional user notes
    """

    timestamp: str
    category: str
    title: str
    impact_score: float
    difficulty_score: float
    accepted: bool
    actual_improvement: Optional[float] = None
    notes: Optional[str] = None


class LearningEngineImpl:
    """Learning engine implementation.

    Tracks feedback history and learns patterns to improve future
    suggestion generation, ranking, and personalization.
    """

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        """Initialize learning engine.

        Args:
            storage_path: Path to store learning data (default: ./storage/learning.json)
        """
        self.storage_path = storage_path or Path("./storage/learning.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        self.feedback_history: List[FeedbackRecord] = []
        self._load_history()

        logger.info(
            f"LearningEngine initialized with {len(self.feedback_history)} "
            f"historical records"
        )

    async def record_feedback(
        self,
        suggestion: Suggestion,
        accepted: bool,
        result_improvement: Optional[float] = None,
        notes: Optional[str] = None
    ) -> None:
        """Record user feedback on a suggestion.

        Args:
            suggestion: The suggestion that received feedback
            accepted: Whether the suggestion was accepted
            result_improvement: Actual performance improvement (if measured)
            notes: Optional user notes
        """
        record = FeedbackRecord(
            timestamp=datetime.utcnow().isoformat(),
            category=suggestion.category.value,
            title=suggestion.title,
            impact_score=suggestion.impact_score,
            difficulty_score=suggestion.difficulty_score,
            accepted=accepted,
            actual_improvement=result_improvement,
            notes=notes
        )

        self.feedback_history.append(record)
        self._save_history()

        logger.info(
            f"Recorded feedback: category={record.category}, "
            f"accepted={accepted}, improvement={result_improvement}"
        )

    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning history.

        Analyzes feedback history to provide insights on:
        - Category acceptance rates
        - Impact vs. difficulty patterns
        - Actual vs. predicted improvements
        - Success patterns

        Returns:
            Dictionary with learning metrics and patterns
        """
        if not self.feedback_history:
            return {
                "total_feedback": 0,
                "overall_acceptance_rate": 0.0,
                "category_insights": {},
                "improvement_accuracy": 0.0,
                "top_categories": [],
                "recommendations": []
            }

        # Calculate overall metrics
        total = len(self.feedback_history)
        accepted = [f for f in self.feedback_history if f.accepted]
        acceptance_rate = len(accepted) / total

        # Category-level insights
        category_insights = self._analyze_by_category()

        # Improvement accuracy (for accepted suggestions with measured results)
        accuracy = self._calculate_improvement_accuracy()

        # Identify top-performing categories
        top_categories = self._get_top_categories()

        # Generate recommendations
        recommendations = self._generate_recommendations()

        insights = {
            "total_feedback": total,
            "overall_acceptance_rate": acceptance_rate,
            "total_accepted": len(accepted),
            "category_insights": category_insights,
            "improvement_accuracy": accuracy,
            "top_categories": top_categories,
            "recommendations": recommendations,
            "last_updated": datetime.utcnow().isoformat()
        }

        logger.debug(f"Generated learning insights: {json.dumps(insights, indent=2)}")
        return insights

    def _analyze_by_category(self) -> Dict[str, Dict[str, Any]]:
        """Analyze feedback by category.

        Returns:
            Dictionary mapping categories to their metrics
        """
        category_data: Dict[str, List[FeedbackRecord]] = {}

        # Group by category
        for record in self.feedback_history:
            if record.category not in category_data:
                category_data[record.category] = []
            category_data[record.category].append(record)

        # Calculate metrics per category
        insights = {}
        for category, records in category_data.items():
            accepted = [r for r in records if r.accepted]
            improvements = [
                r.actual_improvement for r in accepted
                if r.actual_improvement is not None
            ]

            insights[category] = {
                "total_suggestions": len(records),
                "accepted": len(accepted),
                "acceptance_rate": len(accepted) / len(records),
                "avg_impact_score": sum(r.impact_score for r in records) / len(records),
                "avg_difficulty_score": sum(r.difficulty_score for r in records) / len(records),
                "avg_improvement": sum(improvements) / len(improvements) if improvements else 0.0,
                "improvement_count": len(improvements)
            }

        return insights

    def _calculate_improvement_accuracy(self) -> float:
        """Calculate how accurately impact scores predict actual improvements.

        Returns:
            Accuracy score (0-1), where 1 means perfect prediction
        """
        # Get accepted suggestions with measured improvements
        measured = [
            r for r in self.feedback_history
            if r.accepted and r.actual_improvement is not None
        ]

        if not measured:
            return 0.0

        # Calculate correlation between predicted impact and actual improvement
        # Simplified accuracy: compare relative ordering
        accurate = 0
        total_comparisons = 0

        for i, r1 in enumerate(measured):
            for r2 in measured[i+1:]:
                total_comparisons += 1

                # Check if relative ordering matches
                predicted_order = r1.impact_score > r2.impact_score
                actual_order = (r1.actual_improvement or 0) > (r2.actual_improvement or 0)

                if predicted_order == actual_order:
                    accurate += 1

        return accurate / total_comparisons if total_comparisons > 0 else 0.0

    def _get_top_categories(self, top_n: int = 3) -> List[Dict[str, Any]]:
        """Get top-performing categories by acceptance and improvement.

        Args:
            top_n: Number of top categories to return

        Returns:
            List of top categories with metrics
        """
        category_insights = self._analyze_by_category()

        # Score categories by acceptance rate * average improvement
        scored_categories = []
        for category, metrics in category_insights.items():
            score = metrics["acceptance_rate"] * (1 + metrics["avg_improvement"])
            scored_categories.append({
                "category": category,
                "score": score,
                "acceptance_rate": metrics["acceptance_rate"],
                "avg_improvement": metrics["avg_improvement"],
                "total_suggestions": metrics["total_suggestions"]
            })

        # Sort by score
        scored_categories.sort(key=lambda x: x["score"], reverse=True)

        return scored_categories[:top_n]

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on learning history.

        Returns:
            List of recommendation strings
        """
        recommendations = []
        category_insights = self._analyze_by_category()

        # Recommend focusing on high-acceptance categories
        high_acceptance = [
            (cat, metrics) for cat, metrics in category_insights.items()
            if metrics["acceptance_rate"] > 0.7
        ]

        if high_acceptance:
            top_cat = max(high_acceptance, key=lambda x: x[1]["acceptance_rate"])
            recommendations.append(
                f"Focus on {top_cat[0]} suggestions "
                f"(acceptance rate: {top_cat[1]['acceptance_rate']:.1%})"
            )

        # Recommend against low-acceptance categories
        low_acceptance = [
            (cat, metrics) for cat, metrics in category_insights.items()
            if metrics["acceptance_rate"] < 0.3 and metrics["total_suggestions"] >= 3
        ]

        if low_acceptance:
            worst_cat = min(low_acceptance, key=lambda x: x[1]["acceptance_rate"])
            recommendations.append(
                f"Reconsider {worst_cat[0]} suggestions "
                f"(low acceptance rate: {worst_cat[1]['acceptance_rate']:.1%})"
            )

        # Recommend based on difficulty patterns
        avg_difficulty_accepted = [
            r.difficulty_score for r in self.feedback_history if r.accepted
        ]
        if avg_difficulty_accepted:
            avg_diff = sum(avg_difficulty_accepted) / len(avg_difficulty_accepted)
            if avg_diff < 4.0:
                recommendations.append(
                    f"User prefers low-difficulty suggestions (avg: {avg_diff:.1f}/10)"
                )
            elif avg_diff > 7.0:
                recommendations.append(
                    f"User accepts high-difficulty suggestions (avg: {avg_diff:.1f}/10)"
                )

        return recommendations

    def get_category_preferences(self) -> Dict[str, float]:
        """Get learned preferences for each category.

        Returns:
            Dictionary mapping categories to preference scores (0-1)
        """
        category_insights = self._analyze_by_category()

        preferences = {}
        for category, metrics in category_insights.items():
            # Preference score combines acceptance rate and average improvement
            acceptance_weight = 0.7
            improvement_weight = 0.3

            acceptance_score = metrics["acceptance_rate"]
            improvement_score = min(metrics["avg_improvement"] / 0.1, 1.0)  # Normalize

            preference = (
                acceptance_weight * acceptance_score +
                improvement_weight * improvement_score
            )
            preferences[category] = preference

        return preferences

    def _load_history(self) -> None:
        """Load feedback history from storage."""
        if not self.storage_path.exists():
            logger.info("No existing learning history found")
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.feedback_history = [
                FeedbackRecord(**record) for record in data
            ]

            logger.info(f"Loaded {len(self.feedback_history)} feedback records")

        except Exception as e:
            logger.error(f"Failed to load learning history: {e}")
            self.feedback_history = []

    def _save_history(self) -> None:
        """Save feedback history to storage."""
        try:
            data = [asdict(record) for record in self.feedback_history]

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.feedback_history)} feedback records")

        except Exception as e:
            logger.error(f"Failed to save learning history: {e}")
