"""Tests for analysis visualizer."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.analysis.visualizer import AnalysisVisualizer
from src.analysis import Suggestion, SuggestionCategory, AnalysisReport
from src.backtest import BacktestResult, PerformanceMetrics
import pandas as pd


@pytest.fixture
def visualizer() -> AnalysisVisualizer:
    """Create analysis visualizer."""
    return AnalysisVisualizer()


@pytest.fixture
def sample_suggestions() -> list[Suggestion]:
    """Create sample suggestions."""
    return [
        Suggestion(
            category=SuggestionCategory.RISK_MANAGEMENT,
            title="Add stop-loss protection",
            description="Implement dynamic stop-loss",
            rationale="Reduce drawdown",
            implementation_hint="Use ATR-based stop",
            impact_score=8.0,
            difficulty_score=3.0
        ),
        Suggestion(
            category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
            title="Improve entry timing",
            description="Add momentum filter",
            rationale="Better timing",
            implementation_hint="Use RSI",
            impact_score=7.0,
            difficulty_score=5.0
        ),
        Suggestion(
            category=SuggestionCategory.POSITION_SIZING,
            title="Optimize position sizing",
            description="Use Kelly criterion",
            rationale="Better risk-adjusted returns",
            implementation_hint="Calculate Kelly %",
            impact_score=9.0,
            difficulty_score=6.0
        )
    ]


@pytest.fixture
def sample_analysis_report() -> AnalysisReport:
    """Create sample analysis report."""
    backtest_result = BacktestResult(
        portfolio_positions=pd.DataFrame(),
        trade_records=pd.DataFrame({'pnl': [100, -50, 200]}),
        equity_curve=pd.Series([1000, 1100, 1050, 1250], dtype=float),
        raw_result=None
    )

    metrics = PerformanceMetrics(
        annualized_return=0.12,
        sharpe_ratio=1.5,
        max_drawdown=-0.15,
        total_trades=50,
        win_rate=0.55,
        profit_factor=1.8,
        avg_holding_period=7.5,
        best_trade=0.08,
        worst_trade=-0.05
    )

    suggestions = [
        Suggestion(
            category=SuggestionCategory.RISK_MANAGEMENT,
            title="Test suggestion",
            description="Test",
            rationale="Test",
            implementation_hint="Test",
            impact_score=8.0,
            difficulty_score=3.0
        )
    ]

    return AnalysisReport(
        backtest_result=backtest_result,
        performance_metrics=metrics,
        suggestions=suggestions,
        analysis_metadata={}
    )


class TestAnalysisVisualizer:
    """Tests for AnalysisVisualizer."""

    def test_initialization(self) -> None:
        """Test visualizer initialization."""
        visualizer = AnalysisVisualizer()
        assert visualizer is not None

    def test_create_suggestion_chart(
        self,
        visualizer: AnalysisVisualizer,
        sample_suggestions: list[Suggestion]
    ) -> None:
        """Test suggestion chart creation."""
        fig = visualizer.create_suggestion_chart(sample_suggestions)

        assert fig is not None
        # Verify figure has data
        assert len(fig.data) > 0
        # Verify scatter plot created
        assert fig.data[0].type == 'scatter'
        # Verify 3 suggestions plotted
        assert len(fig.data[0].x) == 3
        assert len(fig.data[0].y) == 3

    def test_create_suggestion_chart_empty(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test chart creation with empty suggestions."""
        fig = visualizer.create_suggestion_chart([])

        assert fig is not None
        # Should return empty figure with title
        assert "No Suggestions" in fig.layout.title.text

    def test_create_suggestion_chart_respects_max(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test that chart respects max_suggestions limit."""
        # Create 15 suggestions
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title=f"Suggestion {i}",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=7.0,
                difficulty_score=3.0
            )
            for i in range(15)
        ]

        fig = visualizer.create_suggestion_chart(suggestions, max_suggestions=5)

        # Should only plot 5 suggestions
        assert len(fig.data[0].x) == 5

    def test_create_suggestion_chart_long_titles(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test chart creation with long suggestion titles."""
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="This is a very long title that should be truncated to fit nicely in the visualization",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=3.0
            )
        ]

        fig = visualizer.create_suggestion_chart(suggestions)

        assert fig is not None
        # Title should be truncated in customdata
        assert len(fig.data[0].customdata[0][0]) <= 53  # 50 + "..."

    def test_create_priority_chart(
        self,
        visualizer: AnalysisVisualizer,
        sample_suggestions: list[Suggestion]
    ) -> None:
        """Test priority bar chart creation."""
        fig = visualizer.create_priority_chart(sample_suggestions)

        assert fig is not None
        assert len(fig.data) > 0
        # Verify bar chart
        assert fig.data[0].type == 'bar'
        # Verify 3 bars (one per suggestion)
        assert len(fig.data[0].x) == 3

    def test_create_category_distribution(
        self,
        visualizer: AnalysisVisualizer,
        sample_suggestions: list[Suggestion]
    ) -> None:
        """Test category distribution pie chart."""
        fig = visualizer.create_category_distribution(sample_suggestions)

        assert fig is not None
        assert len(fig.data) > 0
        # Verify pie chart
        assert fig.data[0].type == 'pie'
        # Verify 3 categories
        assert len(fig.data[0].values) == 3

    def test_create_learning_metrics_chart(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test learning metrics visualization."""
        learning_insights = {
            "total_feedback": 20,
            "overall_acceptance_rate": 0.65,
            "category_insights": {
                "risk_management": {
                    "total_suggestions": 10,
                    "accepted": 8,
                    "acceptance_rate": 0.8,
                    "avg_improvement": 0.05
                },
                "entry_exit_conditions": {
                    "total_suggestions": 5,
                    "accepted": 2,
                    "acceptance_rate": 0.4,
                    "avg_improvement": 0.03
                },
                "position_sizing": {
                    "total_suggestions": 5,
                    "accepted": 3,
                    "acceptance_rate": 0.6,
                    "avg_improvement": 0.04
                }
            }
        }

        fig = visualizer.create_learning_metrics_chart(learning_insights)

        assert fig is not None
        # Should have subplots
        assert len(fig.data) >= 2  # At least 2 traces

    def test_create_learning_metrics_chart_empty(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test learning metrics chart with empty data."""
        learning_insights = {
            "total_feedback": 0,
            "overall_acceptance_rate": 0.0,
            "category_insights": {}
        }

        fig = visualizer.create_learning_metrics_chart(learning_insights)

        assert fig is not None
        # Should handle empty data gracefully

    def test_create_report_visualizations(
        self,
        visualizer: AnalysisVisualizer,
        sample_analysis_report: AnalysisReport
    ) -> None:
        """Test complete report visualization generation."""
        figs = visualizer.create_report_visualizations(sample_analysis_report)

        assert isinstance(figs, dict)
        # Should have multiple visualizations
        assert "suggestion_scatter" in figs
        assert "priority_ranking" in figs
        assert "category_distribution" in figs

    def test_create_report_visualizations_no_suggestions(
        self,
        visualizer: AnalysisVisualizer
    ) -> None:
        """Test report visualizations with no suggestions."""
        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=pd.DataFrame(),
            equity_curve=pd.Series([1000], dtype=float),
            raw_result=None
        )

        metrics = PerformanceMetrics(
            annualized_return=0.10,
            sharpe_ratio=1.0,
            max_drawdown=-0.10,
            total_trades=10,
            win_rate=0.50,
            profit_factor=1.5,
            avg_holding_period=5.0,
            best_trade=0.05,
            worst_trade=-0.03
        )

        report = AnalysisReport(
            backtest_result=backtest_result,
            performance_metrics=metrics,
            suggestions=[],  # No suggestions
            analysis_metadata={}
        )

        figs = visualizer.create_report_visualizations(report)

        assert isinstance(figs, dict)
        # Should still return visualizations (with empty data)
        assert "suggestion_scatter" in figs
        assert "priority_ranking" in figs
        assert "category_distribution" in figs
