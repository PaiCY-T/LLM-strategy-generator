"""FeedbackGenerator - Generate actionable feedback for LLM strategy generation.

This module creates natural language feedback from iteration history to guide
the LLM in generating better trading strategies.

Key Features:
    - Context-aware feedback based on iteration outcome
    - Template-based generation for consistency
    - Trend analysis from recent history
    - Champion comparison for target setting
    - Length constraints (<500 words)

Integration:
    - IterationHistory: For trend analysis
    - ChampionTracker: For champion reference and targets

Example:
    >>> from src.learning.feedback_generator import FeedbackGenerator
    >>> from src.learning.iteration_history import IterationHistory
    >>> from src.learning.champion_tracker import ChampionTracker
    >>>
    >>> # Initialize generator
    >>> history = IterationHistory()
    >>> champion_tracker = ChampionTracker()
    >>> generator = FeedbackGenerator(history, champion_tracker)
    >>>
    >>> # Generate feedback for successful iteration
    >>> feedback = generator.generate_feedback(
    ...     iteration_num=10,
    ...     metrics={'sharpe_ratio': 1.5, 'annual_return': 0.25, 'max_drawdown': -0.12},
    ...     execution_result={'status': 'success', 'execution_time': 5.2},
    ...     classification_level='LEVEL_3'
    ... )
    >>> print(feedback)  # Natural language guidance for next iteration
    >>>
    >>> # Generate feedback for failed iteration
    >>> feedback = generator.generate_feedback(
    ...     iteration_num=11,
    ...     metrics=None,
    ...     execution_result={'status': 'error'},
    ...     classification_level=None,
    ...     error_msg='data.get() called with invalid key: market_value'
    ... )
    >>> print(feedback)  # Error-specific debugging guidance
"""

from typing import TYPE_CHECKING, Dict, Any, Optional, List
from dataclasses import dataclass
import logging

from src.backtest.metrics import StrategyMetrics

if TYPE_CHECKING:
    from src.learning.iteration_history import IterationHistory, IterationRecord
    from src.learning.champion_tracker import ChampionTracker

logger = logging.getLogger(__name__)

# Template constants (6 templates)
TEMPLATE_ITERATION_0 = """Starting iteration {iteration_num}. No previous history yet.

Goal: Generate a valid FinLab trading strategy with Sharpe Ratio >1.0

Guidelines:
- Use available data: {available_data}
- Start simple: test basic factor combinations
- Ensure code executes without errors
- Focus on positive returns first
"""

TEMPLATE_SUCCESS_SIMPLE = """Iteration {iteration_num}: SUCCESS

Performance:
- Sharpe: {current_sharpe:.3f}
- Classification: {classification_level}

Not enough history for trend analysis yet. Keep building on this success.

{champion_section}
"""

TEMPLATE_SUCCESS_IMPROVING = """Iteration {iteration_num}: EXCELLENT PROGRESS

Performance:
- Sharpe: {prev_sharpe:.3f} → {current_sharpe:.3f} {change_text}
- Classification: {classification_level}

Trend: {trend_summary}

{champion_section}

Keep this direction! Consider incremental improvements while maintaining risk controls.
"""

TEMPLATE_SUCCESS_DECLINING = """Iteration {iteration_num}: SUCCESS but declining performance

Performance:
- Sharpe: {prev_sharpe:.3f} → {current_sharpe:.3f} {change_text}
- Classification: {classification_level}

Trend: {trend_summary}

{champion_section}

Warning: Performance declining. Review recent changes and consider reverting to better-performing approach.
"""

TEMPLATE_TIMEOUT = """Iteration {iteration_num}: TIMEOUT ERROR

Execution exceeded time limit.

Common causes:
- Infinite loops in strategy logic
- Excessive data processing
- Complex calculations without optimization

Suggestions:
- Simplify logic
- Add early termination conditions
- Reduce data window size
- Use vectorized operations

{last_success_section}
"""

TEMPLATE_EXECUTION_ERROR = """Iteration {iteration_num}: EXECUTION ERROR

Error: {error_msg}

Common causes:
- Data access errors (check data.get() calls)
- Type errors (verify operations)
- Division by zero
- Missing dependencies

Debugging:
- Review error message carefully
- Check data availability
- Verify all operations

{last_success_section}
"""

TEMPLATE_TREND_ANALYSIS = """Trend Analysis (last {n_iterations} iterations):
{trend_details}

{momentum_analysis}
"""


@dataclass
class FeedbackContext:
    """Context for feedback generation.

    Attributes:
        iteration_num: Current iteration number (0-indexed)
        metrics: Performance metrics dict (may be None if execution failed)
        execution_result: Dict with 'status' key ('success', 'timeout', 'error')
        classification_level: Success level (LEVEL_1-5) or None
        error_msg: Error message if execution failed
    """
    iteration_num: int
    metrics: Optional[Dict[str, float]]
    execution_result: Dict[str, Any]
    classification_level: Optional[str]
    error_msg: Optional[str] = None


class FeedbackGenerator:
    """Generate actionable feedback for LLM-based strategy generation.

    Creates natural language feedback from iteration history to guide LLM
    in generating better trading strategies.

    Attributes:
        history: IterationHistory for trend analysis
        champion_tracker: ChampionTracker for champion reference
    """

    def __init__(self, history: 'IterationHistory', champion_tracker: 'ChampionTracker') -> None:
        """Initialize FeedbackGenerator.

        Args:
            history: IterationHistory instance
            champion_tracker: ChampionTracker instance
        """
        self.history = history
        self.champion_tracker = champion_tracker

    def generate_feedback(
        self,
        iteration_num: int,
        metrics: Optional[StrategyMetrics],
        execution_result: Dict[str, Any],
        classification_level: Optional[str],
        error_msg: Optional[str] = None
    ) -> str:
        """Generate context-appropriate feedback.

        Args:
            iteration_num: Current iteration number
            metrics: Performance metrics dict (may be None if execution failed)
            execution_result: Dict with 'status' key ('success', 'timeout', 'error')
            classification_level: Success level (LEVEL_1-5) or None
            error_msg: Error message if execution failed

        Returns:
            Formatted feedback string (<500 words)
        """
        # Phase 3: Convert dict to StrategyMetrics for backward compatibility
        if metrics is not None and isinstance(metrics, dict):
            metrics = StrategyMetrics.from_dict(metrics)

        context = FeedbackContext(
            iteration_num=iteration_num,
            metrics=metrics,
            execution_result=execution_result,
            classification_level=classification_level,
            error_msg=error_msg
        )

        # Select template based on scenario
        template, variables = self._select_template_and_variables(context)

        # Generate feedback
        feedback = template.format(**variables)

        # Validate length
        word_count = len(feedback.split())
        if word_count > 500:
            logger.warning(f"Feedback exceeds 500 words ({word_count}), truncating")
            words = feedback.split()[:500]
            feedback = ' '.join(words) + "..."

        return feedback

    def _select_template_and_variables(
        self, context: FeedbackContext
    ) -> tuple[str, Dict[str, Any]]:
        """Select appropriate template and prepare variables.

        Args:
            context: FeedbackContext with iteration details

        Returns:
            Tuple of (template_string, variables_dict)
        """
        # Iteration 0: No history
        if context.iteration_num == 0:
            return TEMPLATE_ITERATION_0, {
                'iteration_num': 0,
                'available_data': 'price, volume, market_cap, etc.'
            }

        # Get recent history for trend analysis
        recent_records = self.history.load_recent(N=5)

        # Execution error (fixed: check 'success' field instead of 'status')
        if not context.execution_result.get('success', False):
            last_success = self._find_last_success(recent_records)
            return TEMPLATE_EXECUTION_ERROR, {
                'iteration_num': context.iteration_num,
                'error_msg': context.error_msg or 'Unknown error',
                'last_success_section': self._format_last_success(last_success)
            }

        # Timeout
        if context.execution_result.get('status') == 'timeout':
            last_success = self._find_last_success(recent_records)
            return TEMPLATE_TIMEOUT, {
                'iteration_num': context.iteration_num,
                'last_success_section': self._format_last_success(last_success)
            }

        # Success: Check trend
        if context.metrics and len(recent_records) >= 2:
            current_sharpe = context.metrics.sharpe_ratio if context.metrics.sharpe_ratio is not None else 0
            prev_record = recent_records[1]  # Second most recent (first is current)
            prev_sharpe = prev_record.metrics.sharpe_ratio if prev_record.metrics and prev_record.metrics.sharpe_ratio is not None else 0

            # Trend analysis
            trend_summary = self._analyze_trend(recent_records)
            champion_section = self._format_champion_section(current_sharpe)

            if current_sharpe > prev_sharpe:
                # Improving - calculate change text based on previous Sharpe sign
                if prev_sharpe > 0:
                    improvement_pct = ((current_sharpe / prev_sharpe) - 1) * 100
                    change_text = f"(+{improvement_pct:.1f}%)"
                elif prev_sharpe < 0:
                    absolute_change = current_sharpe - prev_sharpe
                    change_text = f"({'+'if absolute_change >= 0 else ''}{absolute_change:.2f} absolute)"
                else:
                    change_text = "(from zero)"

                return TEMPLATE_SUCCESS_IMPROVING, {
                    'iteration_num': context.iteration_num,
                    'prev_sharpe': prev_sharpe,
                    'current_sharpe': current_sharpe,
                    'change_text': change_text,
                    'classification_level': context.classification_level or 'Unknown',
                    'trend_summary': trend_summary,
                    'champion_section': champion_section
                }
            else:
                # Declining - calculate change text based on previous Sharpe sign
                if prev_sharpe > 0:
                    decline_pct = ((current_sharpe / prev_sharpe) - 1) * 100
                    change_text = f"({decline_pct:.1f}%)"
                elif prev_sharpe < 0:
                    absolute_change = current_sharpe - prev_sharpe
                    change_text = f"({'+'if absolute_change >= 0 else ''}{absolute_change:.2f} absolute)"
                else:
                    change_text = "(from zero)"

                return TEMPLATE_SUCCESS_DECLINING, {
                    'iteration_num': context.iteration_num,
                    'prev_sharpe': prev_sharpe,
                    'current_sharpe': current_sharpe,
                    'change_text': change_text,
                    'classification_level': context.classification_level or 'Unknown',
                    'trend_summary': trend_summary,
                    'champion_section': champion_section
                }

        # Fallback: Simple success (iteration 1+ with insufficient history)
        current_sharpe = context.metrics.sharpe_ratio if context.metrics and context.metrics.sharpe_ratio is not None else 0
        return TEMPLATE_SUCCESS_SIMPLE, {
            'iteration_num': context.iteration_num,
            'current_sharpe': current_sharpe,
            'classification_level': context.classification_level or 'N/A',
            'champion_section': self._format_champion_section(current_sharpe)
        }

    def _analyze_trend(self, recent_records: List['IterationRecord']) -> str:
        """Analyze Sharpe ratio trend from recent records.

        Args:
            recent_records: List of IterationRecord (newest first)

        Returns:
            Trend summary string (e.g., "Sharpe improving: 0.5→0.8→1.2")
        """
        if len(recent_records) < 3:
            return "Limited history for trend analysis"

        # Extract Sharpe ratios (reverse to chronological order)
        sharpes = []
        for record in reversed(recent_records[-5:]):  # Last 5 iterations
            sharpe = record.metrics.sharpe_ratio if record.metrics and record.metrics.sharpe_ratio is not None else 0
            sharpes.append(sharpe)

        # Format trend
        trend_str = " → ".join([f"{s:.2f}" for s in sharpes])

        # Determine direction
        if sharpes[-1] > sharpes[-2] > sharpes[-3]:
            direction = "strongly improving"
        elif sharpes[-1] > sharpes[0]:
            direction = "improving"
        elif sharpes[-1] < sharpes[-2] < sharpes[-3]:
            direction = "declining"
        elif sharpes[-1] < sharpes[0]:
            direction = "weakening"
        else:
            direction = "fluctuating"

        return f"Sharpe {direction}: {trend_str}"

    def _format_champion_section(self, current_sharpe: float) -> str:
        """Format champion comparison section.

        Args:
            current_sharpe: Current iteration Sharpe ratio

        Returns:
            Formatted champion section string
        """
        if not self.champion_tracker.champion:
            return "No champion yet. You're setting the baseline!"

        champion_sharpe = self.champion_tracker.champion.metrics.sharpe_ratio if self.champion_tracker.champion.metrics and self.champion_tracker.champion.metrics.sharpe_ratio is not None else 0
        gap = current_sharpe - champion_sharpe
        gap_pct = (gap / champion_sharpe * 100) if champion_sharpe > 0 else 0

        if gap > 0:
            return f"Champion target: {champion_sharpe:.3f}\n✅ ABOVE champion by {gap_pct:.1f}%!"
        else:
            return f"Champion target: {champion_sharpe:.3f}\nGap to champion: {abs(gap_pct):.1f}% below"

    def _find_last_success(self, recent_records: List['IterationRecord']) -> Optional['IterationRecord']:
        """Find last successful iteration from recent records.

        Args:
            recent_records: List of IterationRecord

        Returns:
            Last successful IterationRecord or None
        """
        for record in recent_records:
            if record.execution_result.get('status') == 'success':
                return record
        return None

    def _format_last_success(self, last_success: Optional[Any]) -> str:
        """Format last success reference section.

        Args:
            last_success: Last successful IterationRecord or None

        Returns:
            Formatted section string
        """
        if not last_success:
            return "No recent successful iterations. Review fundamentals."

        sharpe = last_success.metrics.sharpe_ratio if last_success.metrics and last_success.metrics.sharpe_ratio is not None else 0
        iteration = last_success.iteration_num
        return f"Last success: Iteration {iteration} (Sharpe: {sharpe:.3f})\nConsider reverting to similar structure."
