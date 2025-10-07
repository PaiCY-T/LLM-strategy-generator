"""Integration tests for analysis engine."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch

from src.backtest import BacktestResult, PerformanceMetrics
from src.analysis.engine import AnalysisEngineImpl
from src.analysis.claude_client import ClaudeClient, CircuitState
from src.analysis import Suggestion, SuggestionCategory


@pytest.fixture
def sample_backtest_result() -> BacktestResult:
    """Create sample backtest result."""
    return BacktestResult(
        portfolio_positions=pd.DataFrame(),
        trade_records=pd.DataFrame({
            'pnl': [100, -50, 200, -30, 150]
        }),
        equity_curve=pd.Series([1000, 1100, 1050, 1250, 1220, 1370], dtype=float),
        raw_result=None
    )


@pytest.fixture
def sample_metrics() -> PerformanceMetrics:
    """Create sample performance metrics with issues to trigger fallback rules."""
    return PerformanceMetrics(
        annualized_return=0.08,
        sharpe_ratio=0.6,  # Low Sharpe (< 1.0) triggers suggestion
        max_drawdown=-0.25,  # High drawdown (< -0.20) triggers suggestion
        total_trades=50,
        win_rate=0.40,  # Low win rate (< 0.45) triggers suggestion
        profit_factor=1.3,  # Low profit factor (< 1.5) triggers suggestion
        avg_holding_period=7.5,
        best_trade=0.08,
        worst_trade=-0.05
    )


@pytest.fixture
def mock_claude_client() -> ClaudeClient:
    """Create mock Claude client."""
    return ClaudeClient(api_key="test-key", model="test-model")


class TestAnalysisEngineImpl:
    """Integration tests for analysis engine."""

    def test_initialization(self, mock_claude_client: ClaudeClient) -> None:
        """Test engine initialization."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client,
            min_suggestions=3,
            max_suggestions=5
        )

        assert engine.claude_client == mock_claude_client
        assert engine.generator is not None
        assert engine.ranker is not None
        assert engine.fallback is not None

    def test_initialization_without_fallback(
        self,
        mock_claude_client: ClaudeClient
    ) -> None:
        """Test initialization without fallback."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client,
            enable_fallback=False
        )

        assert engine.fallback is None

    @pytest.mark.asyncio
    async def test_generate_suggestions_uses_fallback_on_circuit_open(
        self,
        mock_claude_client: ClaudeClient,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test fallback when circuit breaker is open."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client,
            enable_fallback=True
        )

        # Force circuit open
        mock_claude_client.circuit_breaker._open_circuit()

        # Should use fallback
        suggestions = await engine.generate_suggestions(
            sample_backtest_result,
            sample_metrics
        )

        assert len(suggestions) > 0
        assert engine._get_analysis_method() == "fallback_only"

    @pytest.mark.asyncio
    async def test_analyze_strategy_returns_report(
        self,
        mock_claude_client: ClaudeClient,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test full strategy analysis."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client,
            enable_fallback=True
        )

        # Force use of fallback
        mock_claude_client.circuit_breaker._open_circuit()

        report = await engine.analyze_strategy(
            sample_backtest_result,
            sample_metrics
        )

        assert report.backtest_result == sample_backtest_result
        assert report.performance_metrics == sample_metrics
        assert len(report.suggestions) > 0
        assert "suggestion_count" in report.analysis_metadata

    @pytest.mark.asyncio
    async def test_rank_suggestions_sorts_by_priority(
        self,
        mock_claude_client: ClaudeClient
    ) -> None:
        """Test suggestion ranking."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client
        )

        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Low Priority",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=3.0,
                difficulty_score=7.0
            ),
            Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="High Priority",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=9.0,
                difficulty_score=2.0
            )
        ]

        ranked = engine.rank_suggestions(suggestions)

        assert ranked[0].title == "High Priority"
        assert ranked[1].title == "Low Priority"

    def test_get_status(self, mock_claude_client: ClaudeClient) -> None:
        """Test getting engine status."""
        engine = AnalysisEngineImpl(
            claude_client=mock_claude_client,
            enable_fallback=True
        )

        status = engine.get_status()

        assert "circuit_state" in status
        assert "fallback_enabled" in status
        assert "ranker_weights" in status
        assert status["fallback_enabled"] is True
        assert status["circuit_state"] == CircuitState.CLOSED.value
