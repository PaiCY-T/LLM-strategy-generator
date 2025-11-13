"""Tests for fallback analyzer."""

import pytest
import pandas as pd

from src.backtest import BacktestResult, PerformanceMetrics
from src.analysis.fallback import FallbackAnalyzer
from src.analysis import SuggestionCategory


@pytest.fixture
def sample_backtest_result() -> BacktestResult:
    """Create sample backtest result."""
    return BacktestResult(
        portfolio_positions=pd.DataFrame(),
        trade_records=pd.DataFrame(),
        equity_curve=pd.Series([100, 105, 110], dtype=float),
        raw_result=None
    )


class TestFallbackAnalyzer:
    """Tests for fallback analyzer."""

    def test_initialization(self) -> None:
        """Test analyzer initialization."""
        analyzer = FallbackAnalyzer()
        assert analyzer is not None

    def test_generate_suggestions_high_drawdown(
        self,
        sample_backtest_result: BacktestResult
    ) -> None:
        """Test suggestions for high drawdown."""
        metrics = PerformanceMetrics(
            annualized_return=0.10,
            sharpe_ratio=1.5,
            max_drawdown=-0.25,  # High drawdown
            total_trades=50,
            win_rate=0.55,
            profit_factor=1.8
        )

        analyzer = FallbackAnalyzer()
        suggestions = analyzer.generate_suggestions(
            sample_backtest_result,
            metrics
        )

        # Should suggest risk management improvements
        risk_suggestions = [
            s for s in suggestions
            if s.category == SuggestionCategory.RISK_MANAGEMENT
        ]
        assert len(risk_suggestions) > 0
        assert any("drawdown" in s.title.lower() for s in risk_suggestions)

    def test_generate_suggestions_low_win_rate(
        self,
        sample_backtest_result: BacktestResult
    ) -> None:
        """Test suggestions for low win rate."""
        metrics = PerformanceMetrics(
            annualized_return=0.08,
            sharpe_ratio=1.0,
            max_drawdown=-0.15,
            total_trades=50,
            win_rate=0.35,  # Low win rate
            profit_factor=1.5
        )

        analyzer = FallbackAnalyzer()
        suggestions = analyzer.generate_suggestions(
            sample_backtest_result,
            metrics
        )

        # Should suggest entry/exit improvements
        entry_suggestions = [
            s for s in suggestions
            if s.category == SuggestionCategory.ENTRY_EXIT_CONDITIONS
        ]
        assert len(entry_suggestions) > 0

    def test_generate_suggestions_low_profit_factor(
        self,
        sample_backtest_result: BacktestResult
    ) -> None:
        """Test suggestions for low profit factor."""
        metrics = PerformanceMetrics(
            annualized_return=0.05,
            sharpe_ratio=0.8,
            max_drawdown=-0.10,
            total_trades=50,
            win_rate=0.50,
            profit_factor=1.1  # Low profit factor
        )

        analyzer = FallbackAnalyzer()
        suggestions = analyzer.generate_suggestions(
            sample_backtest_result,
            metrics
        )

        # Should suggest position sizing improvements
        sizing_suggestions = [
            s for s in suggestions
            if s.category == SuggestionCategory.POSITION_SIZING
        ]
        assert len(sizing_suggestions) > 0

    def test_generate_suggestions_low_trade_count(
        self,
        sample_backtest_result: BacktestResult
    ) -> None:
        """Test suggestions for low trade count."""
        metrics = PerformanceMetrics(
            annualized_return=0.12,
            sharpe_ratio=1.5,
            max_drawdown=-0.10,
            total_trades=15,  # Low trade count
            win_rate=0.60,
            profit_factor=2.0
        )

        analyzer = FallbackAnalyzer()
        suggestions = analyzer.generate_suggestions(
            sample_backtest_result,
            metrics
        )

        # Should suggest increasing trade frequency
        trade_suggestions = [
            s for s in suggestions
            if "frequency" in s.title.lower() or "trade" in s.title.lower()
        ]
        assert len(trade_suggestions) > 0

    def test_generate_suggestions_validates_scores(
        self,
        sample_backtest_result: BacktestResult
    ) -> None:
        """Test that all suggestions have valid scores."""
        metrics = PerformanceMetrics(
            annualized_return=0.10,
            sharpe_ratio=0.5,
            max_drawdown=-0.25,
            total_trades=30,
            win_rate=0.40,
            profit_factor=1.3
        )

        analyzer = FallbackAnalyzer()
        suggestions = analyzer.generate_suggestions(
            sample_backtest_result,
            metrics
        )

        # All suggestions should have valid scores
        for suggestion in suggestions:
            assert 1 <= suggestion.impact_score <= 10
            assert 1 <= suggestion.difficulty_score <= 10
            assert suggestion.priority_score > 0
