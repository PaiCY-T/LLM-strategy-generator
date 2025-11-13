"""Tests for learning engine."""

import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile

from src.analysis.learning import LearningEngineImpl, FeedbackRecord
from src.analysis import Suggestion, SuggestionCategory


@pytest.fixture
def temp_storage() -> Path:
    """Create temporary storage path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


@pytest.fixture
def learning_engine(temp_storage: Path) -> LearningEngineImpl:
    """Create learning engine with temporary storage."""
    return LearningEngineImpl(storage_path=temp_storage)


@pytest.fixture
def sample_suggestion() -> Suggestion:
    """Create sample suggestion."""
    return Suggestion(
        category=SuggestionCategory.RISK_MANAGEMENT,
        title="Add stop-loss",
        description="Implement stop-loss protection",
        rationale="Reduce max drawdown",
        implementation_hint="Use ATR-based stop",
        impact_score=8.0,
        difficulty_score=3.0
    )


class TestLearningEngineImpl:
    """Tests for LearningEngineImpl."""

    def test_initialization(self, temp_storage: Path) -> None:
        """Test learning engine initialization."""
        engine = LearningEngineImpl(storage_path=temp_storage)

        assert engine.storage_path == temp_storage
        assert len(engine.feedback_history) == 0
        assert temp_storage.parent.exists()

    def test_initialization_default_path(self) -> None:
        """Test initialization with default storage path."""
        engine = LearningEngineImpl()

        assert engine.storage_path == Path("./storage/learning.json")
        assert isinstance(engine.feedback_history, list)

    @pytest.mark.asyncio
    async def test_record_feedback(
        self,
        learning_engine: LearningEngineImpl,
        sample_suggestion: Suggestion
    ) -> None:
        """Test recording feedback."""
        await learning_engine.record_feedback(
            suggestion=sample_suggestion,
            accepted=True,
            result_improvement=0.05,
            notes="Good suggestion"
        )

        assert len(learning_engine.feedback_history) == 1

        record = learning_engine.feedback_history[0]
        assert record.category == "risk_management"
        assert record.title == "Add stop-loss"
        assert record.accepted is True
        assert record.actual_improvement == 0.05
        assert record.notes == "Good suggestion"
        assert record.impact_score == 8.0
        assert record.difficulty_score == 3.0

    @pytest.mark.asyncio
    async def test_record_feedback_rejected(
        self,
        learning_engine: LearningEngineImpl,
        sample_suggestion: Suggestion
    ) -> None:
        """Test recording rejected feedback."""
        await learning_engine.record_feedback(
            suggestion=sample_suggestion,
            accepted=False
        )

        assert len(learning_engine.feedback_history) == 1

        record = learning_engine.feedback_history[0]
        assert record.accepted is False
        assert record.actual_improvement is None
        assert record.notes is None

    @pytest.mark.asyncio
    async def test_get_learning_insights_empty(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test insights with empty history."""
        insights = await learning_engine.get_learning_insights()

        assert insights["total_feedback"] == 0
        assert insights["overall_acceptance_rate"] == 0.0
        assert insights["category_insights"] == {}
        assert insights["improvement_accuracy"] == 0.0
        assert insights["top_categories"] == []
        assert insights["recommendations"] == []

    @pytest.mark.asyncio
    async def test_get_learning_insights_with_data(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test insights with feedback data."""
        # Add multiple feedback records
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title=f"Risk suggestion {i}",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=7.0 + i,
                difficulty_score=3.0
            )
            for i in range(3)
        ]

        for i, suggestion in enumerate(suggestions):
            await learning_engine.record_feedback(
                suggestion=suggestion,
                accepted=i < 2,  # Accept first 2
                result_improvement=0.05 if i < 2 else None
            )

        insights = await learning_engine.get_learning_insights()

        assert insights["total_feedback"] == 3
        assert insights["total_accepted"] == 2
        assert insights["overall_acceptance_rate"] == 2/3
        assert "risk_management" in insights["category_insights"]
        assert len(insights["top_categories"]) > 0

    def test_analyze_by_category(self, learning_engine: LearningEngineImpl) -> None:
        """Test category analysis."""
        # Add feedback records manually
        learning_engine.feedback_history = [
            FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title=f"Risk {i}",
                impact_score=8.0,
                difficulty_score=3.0,
                accepted=i < 3,
                actual_improvement=0.05 if i < 3 else None
            )
            for i in range(5)
        ]

        insights = learning_engine._analyze_by_category()

        assert "risk_management" in insights
        risk_insights = insights["risk_management"]
        assert risk_insights["total_suggestions"] == 5
        assert risk_insights["accepted"] == 3
        assert risk_insights["acceptance_rate"] == 3/5
        assert risk_insights["avg_impact_score"] == 8.0
        assert risk_insights["avg_difficulty_score"] == 3.0
        assert risk_insights["improvement_count"] == 3

    def test_calculate_improvement_accuracy(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test improvement accuracy calculation."""
        # Add records with known pattern
        learning_engine.feedback_history = [
            FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title="High impact",
                impact_score=9.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=0.08
            ),
            FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title="Medium impact",
                impact_score=6.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=0.04
            ),
            FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title="Low impact",
                impact_score=3.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=0.02
            )
        ]

        accuracy = learning_engine._calculate_improvement_accuracy()

        # All pairwise comparisons should match
        # (9 > 6 and 0.08 > 0.04), (9 > 3 and 0.08 > 0.02), (6 > 3 and 0.04 > 0.02)
        assert accuracy == 1.0

    def test_calculate_improvement_accuracy_no_data(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test accuracy with no measured improvements."""
        learning_engine.feedback_history = [
            FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title="Test",
                impact_score=8.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=None  # No measurement
            )
        ]

        accuracy = learning_engine._calculate_improvement_accuracy()
        assert accuracy == 0.0

    def test_get_top_categories(self, learning_engine: LearningEngineImpl) -> None:
        """Test top categories retrieval."""
        # Add records for multiple categories
        learning_engine.feedback_history = [
            # Risk management: high acceptance, good improvement
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title=f"Risk {i}",
                impact_score=8.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=0.06
            ) for i in range(5)],
            # Entry/Exit: medium acceptance
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="entry_exit_conditions",
                title=f"Entry {i}",
                impact_score=7.0,
                difficulty_score=4.0,
                accepted=i < 2,
                actual_improvement=0.03 if i < 2 else None
            ) for i in range(5)],
            # Position sizing: low acceptance
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="position_sizing",
                title=f"Size {i}",
                impact_score=6.0,
                difficulty_score=5.0,
                accepted=False
            ) for i in range(3)]
        ]

        top_categories = learning_engine._get_top_categories(top_n=2)

        assert len(top_categories) == 2
        # Risk management should be top
        assert top_categories[0]["category"] == "risk_management"
        assert top_categories[0]["acceptance_rate"] == 1.0

    def test_generate_recommendations(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test recommendation generation."""
        # Add feedback with clear patterns
        learning_engine.feedback_history = [
            # High-acceptance category
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title=f"Risk {i}",
                impact_score=8.0,
                difficulty_score=2.0,  # Low difficulty
                accepted=True
            ) for i in range(5)],
            # Low-acceptance category
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="timing_optimization",
                title=f"Timing {i}",
                impact_score=7.0,
                difficulty_score=8.0,  # High difficulty
                accepted=False
            ) for i in range(5)]
        ]

        recommendations = learning_engine._generate_recommendations()

        assert len(recommendations) > 0
        # Should recommend focusing on risk_management
        assert any("risk_management" in rec for rec in recommendations)
        # Should warn about timing_optimization
        assert any("timing_optimization" in rec for rec in recommendations)
        # Should note low difficulty preference
        assert any("low-difficulty" in rec.lower() for rec in recommendations)

    def test_get_category_preferences(
        self,
        learning_engine: LearningEngineImpl
    ) -> None:
        """Test category preference calculation."""
        learning_engine.feedback_history = [
            # Risk management: high acceptance and improvement
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="risk_management",
                title=f"Risk {i}",
                impact_score=8.0,
                difficulty_score=3.0,
                accepted=True,
                actual_improvement=0.08
            ) for i in range(5)],
            # Entry/Exit: low acceptance
            *[FeedbackRecord(
                timestamp=datetime.utcnow().isoformat(),
                category="entry_exit_conditions",
                title=f"Entry {i}",
                impact_score=7.0,
                difficulty_score=4.0,
                accepted=False
            ) for i in range(3)]
        ]

        preferences = learning_engine.get_category_preferences()

        assert "risk_management" in preferences
        assert "entry_exit_conditions" in preferences
        # Risk management should have higher preference
        assert preferences["risk_management"] > preferences["entry_exit_conditions"]

    def test_load_history(self, temp_storage: Path) -> None:
        """Test loading feedback history from storage."""
        # Create sample history file
        sample_data = [
            {
                "timestamp": "2025-01-01T00:00:00",
                "category": "risk_management",
                "title": "Test",
                "impact_score": 8.0,
                "difficulty_score": 3.0,
                "accepted": True,
                "actual_improvement": 0.05,
                "notes": "Test note"
            }
        ]

        with open(temp_storage, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f)

        # Load engine
        engine = LearningEngineImpl(storage_path=temp_storage)

        assert len(engine.feedback_history) == 1
        record = engine.feedback_history[0]
        assert record.category == "risk_management"
        assert record.title == "Test"
        assert record.accepted is True

    def test_load_history_nonexistent_file(self, temp_storage: Path) -> None:
        """Test loading with nonexistent file."""
        # Remove temp file if it exists
        if temp_storage.exists():
            temp_storage.unlink()

        engine = LearningEngineImpl(storage_path=temp_storage)

        assert len(engine.feedback_history) == 0

    @pytest.mark.asyncio
    async def test_save_history(
        self,
        learning_engine: LearningEngineImpl,
        sample_suggestion: Suggestion,
        temp_storage: Path
    ) -> None:
        """Test saving feedback history to storage."""
        # Add feedback
        await learning_engine.record_feedback(
            suggestion=sample_suggestion,
            accepted=True,
            result_improvement=0.05
        )

        # Verify file was saved
        assert temp_storage.exists()

        # Load and verify content
        with open(temp_storage, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]["category"] == "risk_management"
        assert data[0]["accepted"] is True

    @pytest.mark.asyncio
    async def test_storage_persistence(
        self,
        temp_storage: Path,
        sample_suggestion: Suggestion
    ) -> None:
        """Test that feedback persists across engine instances."""
        # Create first engine and add feedback
        engine1 = LearningEngineImpl(storage_path=temp_storage)
        await engine1.record_feedback(
            suggestion=sample_suggestion,
            accepted=True,
            result_improvement=0.05
        )

        # Create second engine and verify data loaded
        engine2 = LearningEngineImpl(storage_path=temp_storage)
        assert len(engine2.feedback_history) == 1
        assert engine2.feedback_history[0].category == "risk_management"
