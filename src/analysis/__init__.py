"""
AI Analysis Layer.

Analyzes backtest results and generates specific improvement suggestions.
Implements both AI-powered and rule-based analysis strategies.

Key Components:
    - AnalysisEngine: Strategy analysis and suggestion generation
    - LearningEngine: Iteration history tracking and pattern identification
    - Suggestion ranking and prioritization
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ..backtest import BacktestResult, PerformanceMetrics


class SuggestionCategory(Enum):
    """Categories for strategy improvement suggestions."""

    RISK_MANAGEMENT = "risk_management"
    ENTRY_EXIT_CONDITIONS = "entry_exit_conditions"
    POSITION_SIZING = "position_sizing"
    TIMING_OPTIMIZATION = "timing_optimization"
    DIVERSIFICATION = "diversification"
    COST_REDUCTION = "cost_reduction"


class DifficultyLevel(Enum):
    """Implementation difficulty levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class ImpactLevel(Enum):
    """Expected impact levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Suggestion:
    """A single strategy improvement suggestion.

    Attributes:
        category: Category of the suggestion
        title: Short descriptive title
        description: Detailed description of the suggestion
        rationale: Why this suggestion is being made
        implementation_hint: How to implement this suggestion
        impact_score: Expected impact (1-10)
        difficulty_score: Implementation difficulty (1-10)
        priority_score: Combined priority score (calculated)
    """

    category: SuggestionCategory
    title: str
    description: str
    rationale: str
    implementation_hint: str
    impact_score: float
    difficulty_score: float
    priority_score: float = 0.0

    def __post_init__(self) -> None:
        """Calculate priority score after initialization."""
        # Priority = (Impact * 2 - Difficulty) / 2
        # Emphasizes high impact, low difficulty suggestions
        self.priority_score = (self.impact_score * 2 - self.difficulty_score) / 2


@dataclass
class AnalysisReport:
    """Complete analysis report for a backtest result.

    Attributes:
        backtest_result: The backtest result being analyzed
        performance_metrics: Calculated performance metrics
        suggestions: List of improvement suggestions
        analysis_metadata: Additional metadata about the analysis
    """

    backtest_result: BacktestResult
    performance_metrics: PerformanceMetrics
    suggestions: List[Suggestion]
    analysis_metadata: Dict[str, Any]


class AnalysisEngine:
    """Abstract base class for strategy analysis engines.

    Provides interface for analyzing backtest results and generating
    improvement suggestions using AI or rule-based approaches.
    """

    async def analyze_strategy(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> AnalysisReport:
        """Analyze strategy and generate improvement suggestions.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context (strategy code, history, etc.)

        Returns:
            AnalysisReport with suggestions and metadata

        Raises:
            RuntimeError: If analysis fails
        """
        raise NotImplementedError("Implemented in engine.py")

    async def generate_suggestions(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Suggestion]:
        """Generate improvement suggestions.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context information

        Returns:
            List of improvement suggestions

        Raises:
            RuntimeError: If suggestion generation fails
        """
        raise NotImplementedError("Implemented in engine.py")

    def rank_suggestions(
        self,
        suggestions: List[Suggestion]
    ) -> List[Suggestion]:
        """Rank suggestions by priority.

        Args:
            suggestions: List of suggestions to rank

        Returns:
            Sorted list of suggestions (highest priority first)
        """
        raise NotImplementedError("Implemented in ranking.py")


class LearningEngine:
    """Abstract base class for learning from iteration history.

    Tracks suggestion acceptance/rejection and learns patterns
    to improve future suggestions.
    """

    async def record_feedback(
        self,
        suggestion: Suggestion,
        accepted: bool,
        result_improvement: Optional[float] = None
    ) -> None:
        """Record user feedback on a suggestion.

        Args:
            suggestion: The suggestion that received feedback
            accepted: Whether the suggestion was accepted
            result_improvement: Performance improvement if accepted (optional)
        """
        raise NotImplementedError("Implemented in learning.py")

    async def get_learning_insights(self) -> Dict[str, Any]:
        """Get insights from learning history.

        Returns:
            Dictionary with learning metrics and patterns
        """
        raise NotImplementedError("Implemented in learning.py")


# Import duplicate detection (Task 2.1)
try:
    from .duplicate_detector import (
        DuplicateDetector,
        DuplicateGroup,
        StrategyInfo
    )
    _DUPLICATE_DETECTOR_AVAILABLE = True
except ImportError:
    _DUPLICATE_DETECTOR_AVAILABLE = False

# Import diversity analyzer (Task 3.1)
try:
    from .diversity_analyzer import (
        DiversityAnalyzer,
        DiversityReport
    )
    _DIVERSITY_ANALYZER_AVAILABLE = True
except ImportError:
    _DIVERSITY_ANALYZER_AVAILABLE = False

# Import decision framework (Task 5.1)
try:
    from .decision_framework import (
        DecisionFramework,
        DecisionReport,
        DecisionCriteria
    )
    _DECISION_FRAMEWORK_AVAILABLE = True
except ImportError:
    _DECISION_FRAMEWORK_AVAILABLE = False

__all__ = [
    "AnalysisEngine",
    "LearningEngine",
    "Suggestion",
    "AnalysisReport",
    "SuggestionCategory",
    "DifficultyLevel",
    "ImpactLevel"
]

# Add duplicate detection exports if available
if _DUPLICATE_DETECTOR_AVAILABLE:
    __all__.extend([
        "DuplicateDetector",
        "DuplicateGroup",
        "StrategyInfo"
    ])

# Add diversity analyzer exports if available
if _DIVERSITY_ANALYZER_AVAILABLE:
    __all__.extend([
        "DiversityAnalyzer",
        "DiversityReport"
    ])

# Add decision framework exports if available
if _DECISION_FRAMEWORK_AVAILABLE:
    __all__.extend([
        "DecisionFramework",
        "DecisionReport",
        "DecisionCriteria"
    ])
