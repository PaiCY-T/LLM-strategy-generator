"""
Rule-based fallback analysis when Claude API is unavailable.

Implements heuristic rules for common improvement patterns to ensure
system remains functional without AI assistance.
"""

import logging
from typing import Any, Dict, List, Optional

from ..backtest import BacktestResult, PerformanceMetrics
from . import Suggestion, SuggestionCategory

# Configure logging
logger = logging.getLogger(__name__)


class FallbackAnalyzer:
    """Rule-based fallback analyzer.

    Provides basic strategy analysis using predefined heuristic rules
    when Claude API is unavailable or when quick analysis is needed.
    """

    def __init__(self) -> None:
        """Initialize fallback analyzer."""
        logger.info("FallbackAnalyzer initialized")

    def generate_suggestions(
        self,
        backtest_result: BacktestResult,
        performance_metrics: PerformanceMetrics,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Suggestion]:
        """Generate suggestions using rule-based analysis.

        Args:
            backtest_result: Result from backtest execution
            performance_metrics: Calculated performance metrics
            context: Optional context information

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Apply heuristic rules
        suggestions.extend(self._check_risk_management(performance_metrics))
        suggestions.extend(self._check_win_rate(performance_metrics))
        suggestions.extend(self._check_profit_factor(performance_metrics))
        suggestions.extend(self._check_trade_count(performance_metrics))
        suggestions.extend(self._check_holding_period(performance_metrics))

        logger.info(f"Generated {len(suggestions)} fallback suggestions")
        return suggestions

    def _check_risk_management(
        self,
        metrics: PerformanceMetrics
    ) -> List[Suggestion]:
        """Check risk management metrics.

        Args:
            metrics: Performance metrics

        Returns:
            List of risk-related suggestions
        """
        suggestions = []

        # High drawdown check
        if metrics.max_drawdown < -0.20:  # > 20% drawdown
            impact = 9.0 if metrics.max_drawdown < -0.30 else 7.0
            suggestions.append(Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Reduce Maximum Drawdown",
                description=(
                    f"Current maximum drawdown of {metrics.max_drawdown:.2%} "
                    f"exceeds acceptable risk levels. Consider implementing "
                    f"tighter stop-loss rules or reducing position sizes during drawdown periods."
                ),
                rationale=(
                    "High drawdowns can lead to psychological stress and forced exits. "
                    "Reducing drawdown improves risk-adjusted returns and sustainability."
                ),
                implementation_hint=(
                    "1. Add trailing stop-loss at -10% to -15%\n"
                    "2. Reduce position size by 50% after 10% drawdown\n"
                    "3. Consider adding volatility-based position sizing"
                ),
                impact_score=impact,
                difficulty_score=3.0
            ))

        # Low Sharpe ratio check
        if metrics.sharpe_ratio < 1.0:
            impact = 8.0 if metrics.sharpe_ratio < 0.5 else 6.0
            suggestions.append(Suggestion(
                category=SuggestionCategory.RISK_MANAGEMENT,
                title="Improve Risk-Adjusted Returns",
                description=(
                    f"Sharpe ratio of {metrics.sharpe_ratio:.2f} indicates "
                    f"poor risk-adjusted returns. Focus on reducing volatility "
                    f"while maintaining or improving returns."
                ),
                rationale=(
                    "Higher Sharpe ratio indicates better risk-adjusted performance, "
                    "making the strategy more attractive to investors."
                ),
                implementation_hint=(
                    "1. Diversify across more stocks (8-15 positions)\n"
                    "2. Add market regime filters (trend/volatility)\n"
                    "3. Reduce position concentration (max 15% per position)"
                ),
                impact_score=impact,
                difficulty_score=5.0
            ))

        return suggestions

    def _check_win_rate(self, metrics: PerformanceMetrics) -> List[Suggestion]:
        """Check win rate metrics.

        Args:
            metrics: Performance metrics

        Returns:
            List of win rate suggestions
        """
        suggestions = []

        if metrics.win_rate < 0.45:  # < 45% win rate
            impact = 8.0 if metrics.win_rate < 0.35 else 6.0
            suggestions.append(Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="Improve Entry Signal Quality",
                description=(
                    f"Win rate of {metrics.win_rate:.2%} is below optimal levels. "
                    f"Consider refining entry conditions to filter out low-probability trades."
                ),
                rationale=(
                    "Low win rate suggests entry signals may be too aggressive or poorly timed. "
                    "Better entry timing can significantly improve overall profitability."
                ),
                implementation_hint=(
                    "1. Add confirmation indicators (volume, momentum)\n"
                    "2. Wait for pullbacks before entering\n"
                    "3. Avoid entering near resistance levels\n"
                    "4. Add trend filter (only trade with trend)"
                ),
                impact_score=impact,
                difficulty_score=4.0
            ))
        elif metrics.win_rate > 0.70:  # > 70% win rate
            suggestions.append(Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="Optimize Exit Strategy for Higher Returns",
                description=(
                    f"Win rate of {metrics.win_rate:.2%} is very high, "
                    f"suggesting you may be exiting winners too early. "
                    f"Consider letting winners run longer."
                ),
                rationale=(
                    "High win rate with modest returns suggests profit-taking is too aggressive. "
                    "Allowing winners to run can improve profit factor and total returns."
                ),
                implementation_hint=(
                    "1. Implement trailing stops instead of fixed targets\n"
                    "2. Use multiple exit points (partial exits)\n"
                    "3. Exit only on clear reversal signals\n"
                    "4. Increase profit target by 20-30%"
                ),
                impact_score=7.0,
                difficulty_score=3.0
            ))

        return suggestions

    def _check_profit_factor(self, metrics: PerformanceMetrics) -> List[Suggestion]:
        """Check profit factor metrics.

        Args:
            metrics: Performance metrics

        Returns:
            List of profit factor suggestions
        """
        suggestions = []

        if metrics.profit_factor < 1.5:
            impact = 9.0 if metrics.profit_factor < 1.2 else 7.0
            suggestions.append(Suggestion(
                category=SuggestionCategory.POSITION_SIZING,
                title="Improve Profit Factor Through Better Risk/Reward",
                description=(
                    f"Profit factor of {metrics.profit_factor:.2f} indicates "
                    f"average wins are not sufficiently larger than average losses. "
                    f"Aim for at least 2:1 reward-to-risk ratio."
                ),
                rationale=(
                    "Low profit factor means losing trades offset winning trades too much. "
                    "Improving this ratio is critical for long-term profitability."
                ),
                implementation_hint=(
                    "1. Set minimum 2:1 reward/risk before entering\n"
                    "2. Cut losses quickly with tight stops\n"
                    "3. Let winners run with trailing stops\n"
                    "4. Avoid trades with poor risk/reward setups"
                ),
                impact_score=impact,
                difficulty_score=4.0
            ))

        return suggestions

    def _check_trade_count(self, metrics: PerformanceMetrics) -> List[Suggestion]:
        """Check trade count metrics.

        Args:
            metrics: Performance metrics

        Returns:
            List of trade count suggestions
        """
        suggestions = []

        if metrics.total_trades < 20:
            suggestions.append(Suggestion(
                category=SuggestionCategory.ENTRY_EXIT_CONDITIONS,
                title="Increase Trade Frequency",
                description=(
                    f"Only {metrics.total_trades} trades executed. "
                    f"Consider relaxing entry conditions to capture more opportunities, "
                    f"especially for weekly/monthly trading cycles."
                ),
                rationale=(
                    "Low trade count limits statistical significance and potential returns. "
                    "More trades provide better diversification and smoother equity curve."
                ),
                implementation_hint=(
                    "1. Expand stock universe (add more candidates)\n"
                    "2. Relax entry thresholds by 10-20%\n"
                    "3. Consider multiple timeframes\n"
                    "4. Look for additional setup patterns"
                ),
                impact_score=6.0,
                difficulty_score=3.0
            ))
        elif metrics.total_trades > 200:
            suggestions.append(Suggestion(
                category=SuggestionCategory.COST_REDUCTION,
                title="Reduce Trading Frequency to Lower Costs",
                description=(
                    f"High trade count ({metrics.total_trades}) may be increasing "
                    f"transaction costs. Consider being more selective with entries "
                    f"to improve net returns."
                ),
                rationale=(
                    "Excessive trading increases costs and may indicate overtrading. "
                    "More selective entries can improve risk-adjusted returns."
                ),
                implementation_hint=(
                    "1. Increase entry signal threshold by 15-20%\n"
                    "2. Add minimum holding period (3-5 days)\n"
                    "3. Filter out marginal setups\n"
                    "4. Focus on highest-conviction trades"
                ),
                impact_score=5.0,
                difficulty_score=2.0
            ))

        return suggestions

    def _check_holding_period(self, metrics: PerformanceMetrics) -> List[Suggestion]:
        """Check holding period metrics.

        Args:
            metrics: Performance metrics

        Returns:
            List of holding period suggestions
        """
        suggestions = []

        # For weekly/monthly cycles, very short holding periods may be suboptimal
        if metrics.avg_holding_period > 0 and metrics.avg_holding_period < 3:
            suggestions.append(Suggestion(
                category=SuggestionCategory.TIMING_OPTIMIZATION,
                title="Extend Holding Period for Better Trend Capture",
                description=(
                    f"Average holding period of {metrics.avg_holding_period:.1f} days "
                    f"is very short for weekly/monthly trading cycles. "
                    f"Consider holding positions longer to capture larger moves."
                ),
                rationale=(
                    "Very short holding periods increase transaction costs and may "
                    "miss larger trend movements. Longer holds can improve returns."
                ),
                implementation_hint=(
                    "1. Replace fixed exits with trailing stops\n"
                    "2. Set minimum holding period of 5-7 days\n"
                    "3. Exit only on clear trend reversals\n"
                    "4. Use weekly timeframe for exits"
                ),
                impact_score=6.0,
                difficulty_score=3.0
            ))

        return suggestions
