"""Tests for suggestion ranking."""

import pytest

from src.analysis import Suggestion, SuggestionCategory
from src.analysis.ranking import SuggestionRanker, AdaptiveRanker


class TestSuggestionRanker:
    """Tests for suggestion ranker."""

    def test_initialization(self) -> None:
        """Test ranker initialization."""
        ranker = SuggestionRanker(impact_weight=2.0, difficulty_weight=1.0)
        assert ranker.impact_weight == 2.0
        assert ranker.difficulty_weight == 1.0

    def test_initialization_invalid_weights(self) -> None:
        """Test initialization with invalid weights."""
        with pytest.raises(ValueError, match="must be positive"):
            SuggestionRanker(impact_weight=0)

        with pytest.raises(ValueError, match="must be positive"):
            SuggestionRanker(difficulty_weight=-1)

    def test_rank_suggestions(self) -> None:
        """Test ranking suggestions by priority."""
        ranker = SuggestionRanker()

        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Low Impact, Low Difficulty",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=3.0,
                difficulty_score=2.0
            ),
            Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="High Impact, Low Difficulty",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=9.0,
                difficulty_score=3.0
            ),
            Suggestion(
                category=SuggestionCategory.POSITION_SIZING,
                title="High Impact, High Difficulty",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=8.0
            )
        ]

        ranked = ranker.rank_suggestions(suggestions)

        # High impact, low difficulty should be first
        assert ranked[0].title == "High Impact, Low Difficulty"
        # High impact, high difficulty should be second
        assert ranked[1].title == "High Impact, High Difficulty"
        # Low impact should be last
        assert ranked[2].title == "Low Impact, Low Difficulty"

    def test_rank_empty_list(self) -> None:
        """Test ranking empty list."""
        ranker = SuggestionRanker()
        ranked = ranker.rank_suggestions([])
        assert ranked == []

    def test_get_top_n(self) -> None:
        """Test getting top N suggestions."""
        ranker = SuggestionRanker()

        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title=f"Suggestion {i}",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=float(10 - i),
                difficulty_score=5.0
            )
            for i in range(5)
        ]

        top_3 = ranker.get_top_n(suggestions, 3)
        assert len(top_3) == 3
        assert top_3[0].title == "Suggestion 0"  # Highest impact

    def test_get_top_n_invalid(self) -> None:
        """Test get_top_n with invalid n."""
        ranker = SuggestionRanker()
        with pytest.raises(ValueError, match="must be positive"):
            ranker.get_top_n([], 0)

    def test_filter_by_category(self) -> None:
        """Test filtering by category."""
        ranker = SuggestionRanker()

        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Risk 1",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=3.0
            ),
            Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="Entry 1",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=7.0,
                difficulty_score=4.0
            ),
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Risk 2",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=6.0,
                difficulty_score=2.0
            )
        ]

        filtered = ranker.filter_by_category(
            suggestions,
            ["risk_management"]
        )

        assert len(filtered) == 2
        assert all(s.category == SuggestionCategory.RISK_MANAGEMENT for s in filtered)

    def test_filter_by_threshold(self) -> None:
        """Test filtering by score thresholds."""
        ranker = SuggestionRanker()

        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="High Impact",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=9.0,
                difficulty_score=3.0
            ),
            Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="Low Impact",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=4.0,
                difficulty_score=2.0
            ),
            Suggestion(
                category=SuggestionCategory.POSITION_SIZING,
                title="High Difficulty",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=9.0
            )
        ]

        filtered = ranker.filter_by_threshold(
            suggestions,
            min_impact=7.0,
            max_difficulty=5.0
        )

        assert len(filtered) == 1
        assert filtered[0].title == "High Impact"


class TestAdaptiveRanker:
    """Tests for adaptive ranker."""

    def test_initialization(self) -> None:
        """Test adaptive ranker initialization."""
        ranker = AdaptiveRanker(learning_rate=0.1)
        assert ranker.learning_rate == 0.1
        assert len(ranker.feedback_history) == 0

    def test_initialization_invalid_learning_rate(self) -> None:
        """Test initialization with invalid learning rate."""
        with pytest.raises(ValueError, match="learning_rate"):
            AdaptiveRanker(learning_rate=0)

        with pytest.raises(ValueError, match="learning_rate"):
            AdaptiveRanker(learning_rate=1.5)

    def test_record_feedback(self) -> None:
        """Test recording feedback."""
        ranker = AdaptiveRanker()

        suggestion = Suggestion(
            category=SuggestionCategory.RISK_MANAGEMENT,
            title="Test",
            description="Test",
            rationale="Test",
            implementation_hint="Test",
            impact_score=8.0,
            difficulty_score=3.0
        )

        ranker.record_feedback(suggestion, accepted=True, improvement=0.05)
        assert len(ranker.feedback_history) == 1

    def test_get_learning_stats(self) -> None:
        """Test getting learning statistics."""
        ranker = AdaptiveRanker()

        # No feedback yet
        stats = ranker.get_learning_stats()
        assert stats["total_feedback"] == 0
        assert stats["acceptance_rate"] == 0.0

        # Add some feedback
        suggestion = Suggestion(
            category=SuggestionCategory.RISK_MANAGEMENT,
            title="Test",
            description="Test",
            rationale="Test",
            implementation_hint="Test",
            impact_score=8.0,
            difficulty_score=3.0
        )

        ranker.record_feedback(suggestion, accepted=True, improvement=0.05)
        ranker.record_feedback(suggestion, accepted=False)

        stats = ranker.get_learning_stats()
        assert stats["total_feedback"] == 2
        assert stats["acceptance_rate"] == 0.5
        assert stats["avg_improvement"] == 0.05
