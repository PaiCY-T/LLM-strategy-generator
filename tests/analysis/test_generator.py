"""Tests for suggestion generator."""

import pytest
import json
from unittest.mock import Mock, AsyncMock
import pandas as pd

from src.backtest import BacktestResult, PerformanceMetrics
from src.analysis.generator import SuggestionGenerator
from src.analysis.claude_client import ClaudeClient
from src.analysis import Suggestion, SuggestionCategory


@pytest.fixture
def mock_claude_client() -> ClaudeClient:
    """Create mock Claude client."""
    return ClaudeClient(api_key="test-key", model="test-model")


@pytest.fixture
def generator(mock_claude_client: ClaudeClient) -> SuggestionGenerator:
    """Create suggestion generator."""
    return SuggestionGenerator(
        claude_client=mock_claude_client,
        min_suggestions=3,
        max_suggestions=5
    )


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
    """Create sample performance metrics."""
    return PerformanceMetrics(
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


@pytest.fixture
def valid_claude_response() -> str:
    """Create valid Claude response."""
    suggestions = [
        {
            "category": "risk_management",
            "title": "Add stop-loss protection",
            "description": "Implement dynamic stop-loss to limit downside risk",
            "rationale": "Current max drawdown is -15%, adding stop-loss can reduce it",
            "implementation_hint": "Use ATR-based trailing stop-loss",
            "impact_score": 8.0,
            "difficulty_score": 3.0
        },
        {
            "category": "entry_exit_conditions",
            "title": "Improve entry timing",
            "description": "Add momentum filter to entry conditions",
            "rationale": "Win rate can be improved with better entry timing",
            "implementation_hint": "Use RSI < 30 for oversold conditions",
            "impact_score": 7.0,
            "difficulty_score": 4.0
        },
        {
            "category": "position_sizing",
            "title": "Optimize position sizing",
            "description": "Use Kelly criterion for position sizing",
            "rationale": "Better risk-adjusted returns with optimal sizing",
            "implementation_hint": "Calculate Kelly percentage from win rate and avg win/loss",
            "impact_score": 9.0,
            "difficulty_score": 5.0
        }
    ]
    return json.dumps(suggestions)


class TestSuggestionGenerator:
    """Tests for SuggestionGenerator."""

    def test_initialization(self, mock_claude_client: ClaudeClient) -> None:
        """Test generator initialization."""
        generator = SuggestionGenerator(
            claude_client=mock_claude_client,
            min_suggestions=2,
            max_suggestions=10
        )

        assert generator.claude_client == mock_claude_client
        assert generator.min_suggestions == 2
        assert generator.max_suggestions == 10

    def test_build_analysis_prompt(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test analysis prompt building."""
        prompt = generator._build_analysis_prompt(
            sample_backtest_result,
            sample_metrics,
            None
        )

        # Check prompt contains key information
        assert "0.12" in prompt or "12.00%" in prompt  # Annualized return
        assert "1.5" in prompt or "1.50" in prompt  # Sharpe ratio
        assert "-0.15" in prompt or "-15.00%" in prompt  # Max drawdown
        assert "0.55" in prompt or "55.00%" in prompt  # Win rate
        assert "50" in prompt  # Total trades
        assert "JSON" in prompt  # Format instructions

    def test_build_analysis_prompt_with_context(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test prompt building with context."""
        context = {
            "strategy_code": "def strategy(): pass",
            "iteration_number": 5
        }

        prompt = generator._build_analysis_prompt(
            sample_backtest_result,
            sample_metrics,
            context
        )

        assert "strategy_code" in prompt.lower() or "strategy code" in prompt.lower()
        assert "def strategy(): pass" in prompt
        assert "5" in prompt  # Iteration number

    def test_get_system_prompt(self, generator: SuggestionGenerator) -> None:
        """Test system prompt generation."""
        system_prompt = generator._get_system_prompt()

        assert len(system_prompt) > 0
        assert "trading" in system_prompt.lower() or "strategy" in system_prompt.lower()
        assert "Taiwan" in system_prompt  # Market-specific

    def test_parse_suggestions_valid_json(
        self,
        generator: SuggestionGenerator,
        valid_claude_response: str
    ) -> None:
        """Test parsing valid JSON response."""
        suggestions = generator._parse_suggestions(valid_claude_response)

        assert len(suggestions) == 3
        assert all(isinstance(s, Suggestion) for s in suggestions)
        assert suggestions[0].title == "Add stop-loss protection"
        assert suggestions[0].category == SuggestionCategory.RISK_MANAGEMENT
        assert suggestions[0].impact_score == 8.0
        assert suggestions[0].difficulty_score == 3.0

    def test_parse_suggestions_with_markdown(
        self,
        generator: SuggestionGenerator,
        valid_claude_response: str
    ) -> None:
        """Test parsing JSON wrapped in markdown code blocks."""
        markdown_response = f"```json\n{valid_claude_response}\n```"

        suggestions = generator._parse_suggestions(markdown_response)

        assert len(suggestions) == 3
        assert suggestions[0].title == "Add stop-loss protection"

    def test_parse_suggestions_invalid_json(
        self,
        generator: SuggestionGenerator
    ) -> None:
        """Test parsing invalid JSON."""
        invalid_response = "This is not JSON"

        with pytest.raises(ValueError, match="Failed to parse JSON"):
            generator._parse_suggestions(invalid_response)

    def test_parse_suggestions_not_array(
        self,
        generator: SuggestionGenerator
    ) -> None:
        """Test parsing JSON that's not an array."""
        invalid_response = '{"key": "value"}'

        with pytest.raises(ValueError, match="Expected JSON array"):
            generator._parse_suggestions(invalid_response)

    def test_parse_category_valid(self, generator: SuggestionGenerator) -> None:
        """Test valid category parsing."""
        category = generator._parse_category("risk_management")
        assert category == SuggestionCategory.RISK_MANAGEMENT

        category = generator._parse_category("entry_exit_conditions")
        assert category == SuggestionCategory.ENTRY_EXIT_CONDITIONS

    def test_parse_category_invalid(self, generator: SuggestionGenerator) -> None:
        """Test invalid category parsing."""
        with pytest.raises(ValueError, match="Invalid category"):
            generator._parse_category("invalid_category")

    def test_validate_suggestions_valid_scores(
        self,
        generator: SuggestionGenerator
    ) -> None:
        """Test validation with valid scores."""
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Test",
                description="Test description",
                rationale="Test rationale",
                implementation_hint="Test hint",
                impact_score=8.0,
                difficulty_score=3.0
            )
        ]

        valid = generator._validate_suggestions(suggestions)
        assert len(valid) == 1

    def test_validate_suggestions_invalid_scores(
        self,
        generator: SuggestionGenerator
    ) -> None:
        """Test validation with invalid scores."""
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Invalid impact",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=15.0,  # Invalid: > 10
                difficulty_score=5.0
            ),
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Invalid difficulty",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=0.0  # Invalid: < 1
            ),
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Valid",
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=7.0,
                difficulty_score=4.0
            )
        ]

        valid = generator._validate_suggestions(suggestions)
        assert len(valid) == 1
        assert valid[0].title == "Valid"

    def test_validate_suggestions_missing_fields(
        self,
        generator: SuggestionGenerator
    ) -> None:
        """Test validation with missing required fields."""
        suggestions = [
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="",  # Empty title
                description="Test",
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=3.0
            ),
            Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Valid",
                description="",  # Empty description
                rationale="Test",
                implementation_hint="Test",
                impact_score=8.0,
                difficulty_score=3.0
            )
        ]

        valid = generator._validate_suggestions(suggestions)
        assert len(valid) == 0

    @pytest.mark.asyncio
    async def test_generate_suggestions_success(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics,
        valid_claude_response: str
    ) -> None:
        """Test successful suggestion generation."""
        # Mock Claude client response
        generator.claude_client.generate_analysis = AsyncMock(
            return_value=valid_claude_response
        )

        suggestions = await generator.generate_suggestions(
            sample_backtest_result,
            sample_metrics
        )

        assert len(suggestions) == 3
        assert all(isinstance(s, Suggestion) for s in suggestions)
        assert suggestions[0].category == SuggestionCategory.RISK_MANAGEMENT

    @pytest.mark.asyncio
    async def test_generate_suggestions_respects_max(
        self,
        mock_claude_client: ClaudeClient,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test that generator respects max_suggestions limit."""
        # Create generator with max=2
        generator = SuggestionGenerator(
            claude_client=mock_claude_client,
            min_suggestions=1,
            max_suggestions=2
        )

        # Response with 3 suggestions
        suggestions_data = [
            {
                "category": "risk_management",
                "title": f"Suggestion {i}",
                "description": "Test",
                "rationale": "Test",
                "implementation_hint": "Test",
                "impact_score": 8.0,
                "difficulty_score": 3.0
            }
            for i in range(3)
        ]
        response = json.dumps(suggestions_data)

        generator.claude_client.generate_analysis = AsyncMock(return_value=response)

        suggestions = await generator.generate_suggestions(
            sample_backtest_result,
            sample_metrics
        )

        # Should only return 2 suggestions (max limit)
        assert len(suggestions) == 2

    @pytest.mark.asyncio
    async def test_generate_suggestions_with_context(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics,
        valid_claude_response: str
    ) -> None:
        """Test generation with context."""
        context = {
            "strategy_code": "def strategy(): pass",
            "iteration_number": 3
        }

        generator.claude_client.generate_analysis = AsyncMock(
            return_value=valid_claude_response
        )

        suggestions = await generator.generate_suggestions(
            sample_backtest_result,
            sample_metrics,
            context
        )

        assert len(suggestions) == 3
        # Verify generate_analysis was called with context in prompt
        call_args = generator.claude_client.generate_analysis.call_args
        assert "def strategy(): pass" in call_args[1]["prompt"]

    @pytest.mark.asyncio
    async def test_generate_suggestions_api_failure(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test handling of API failures."""
        # Mock API failure
        generator.claude_client.generate_analysis = AsyncMock(
            side_effect=RuntimeError("API error")
        )

        with pytest.raises(RuntimeError, match="Failed to generate suggestions"):
            await generator.generate_suggestions(
                sample_backtest_result,
                sample_metrics
            )

    @pytest.mark.asyncio
    async def test_generate_suggestions_below_minimum(
        self,
        generator: SuggestionGenerator,
        sample_backtest_result: BacktestResult,
        sample_metrics: PerformanceMetrics
    ) -> None:
        """Test warning when below minimum suggestions."""
        # Response with only 1 suggestion (below min of 3)
        response = json.dumps([{
            "category": "risk_management",
            "title": "Only one",
            "description": "Test",
            "rationale": "Test",
            "implementation_hint": "Test",
            "impact_score": 8.0,
            "difficulty_score": 3.0
        }])

        generator.claude_client.generate_analysis = AsyncMock(return_value=response)

        suggestions = await generator.generate_suggestions(
            sample_backtest_result,
            sample_metrics
        )

        # Should still return the 1 valid suggestion despite warning
        assert len(suggestions) == 1
