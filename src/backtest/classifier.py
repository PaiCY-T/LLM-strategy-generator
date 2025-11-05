"""Success classification system for backtest results.

Classifies backtest results into success levels based on execution status,
metrics coverage, and profitability. Implements a 4-level classification
system (FAILED, EXECUTED, VALID_METRICS, PROFITABLE) to categorize
strategy performance.

Classification Levels:
    - Level 0 (FAILED): Execution failed (execution_success=False)
    - Level 1 (EXECUTED): Executed but <60% metrics extracted
    - Level 2 (VALID_METRICS): >=60% metrics extracted (sharpe, return, drawdown)
    - Level 3 (PROFITABLE): Valid metrics AND >=40% strategies have positive Sharpe
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from .metrics import StrategyMetrics

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of strategy backtest classification.

    Represents the classification outcome for a backtest result, including
    the success level, detailed reasoning, metrics coverage percentage,
    and profitability statistics.

    Attributes:
        level: Classification level (0-3)
            - 0: FAILED - Execution failed
            - 1: EXECUTED - Executed but incomplete metrics
            - 2: VALID_METRICS - Sufficient metrics extracted
            - 3: PROFITABLE - Valid metrics with positive Sharpe ratio
        reason: Human-readable explanation of classification
        metrics_coverage: Percentage of metrics successfully extracted (0.0-1.0)
        profitable_count: Number of strategies with positive Sharpe ratio (for batch)
        total_count: Total number of strategies evaluated (for batch)

    Examples:
        >>> # Single strategy classification
        >>> result = ClassificationResult(
        ...     level=2,
        ...     reason="Valid metrics extracted (3/3: sharpe, return, drawdown)",
        ...     metrics_coverage=1.0,
        ...     profitable_count=None,
        ...     total_count=None
        ... )
        >>> print(f"Level {result.level}: {result.reason}")
        Level 2: Valid metrics extracted (3/3: sharpe, return, drawdown)

        >>> # Batch classification
        >>> batch_result = ClassificationResult(
        ...     level=3,
        ...     reason="Valid metrics with 50% strategies profitable (Sharpe > 0)",
        ...     metrics_coverage=0.95,
        ...     profitable_count=5,
        ...     total_count=10
        ... )
        >>> print(f"{batch_result.profitable_count}/{batch_result.total_count} profitable")
        5/10 profitable
    """

    level: int
    reason: str
    metrics_coverage: float
    profitable_count: Optional[int] = None
    total_count: Optional[int] = None


class SuccessClassifier:
    """Classifies backtest results into success levels.

    Implements a 4-level classification system for backtest results:
        - Level 0 (FAILED): Execution failed
        - Level 1 (EXECUTED): Executed but <60% metrics coverage
        - Level 2 (VALID_METRICS): >=60% metrics coverage
        - Level 3 (PROFITABLE): Valid metrics with >=40% positive Sharpe

    The classifier evaluates:
        1. Execution success status
        2. Metrics extraction coverage percentage
        3. Profitability indicators (Sharpe ratio > 0)

    Examples:
        >>> classifier = SuccessClassifier()
        >>> metrics = StrategyMetrics(
        ...     sharpe_ratio=1.5,
        ...     total_return=0.25,
        ...     max_drawdown=-0.15,
        ...     execution_success=True
        ... )
        >>> result = classifier.classify_single(metrics)
        >>> print(f"Classification Level: {result.level}")
        Classification Level: 2
    """

    # Metrics used to evaluate coverage (the three core metrics)
    COVERAGE_METRICS = {'sharpe_ratio', 'total_return', 'max_drawdown'}

    # Threshold for valid metrics coverage (must extract at least 60%)
    METRICS_COVERAGE_THRESHOLD = 0.60

    # Threshold for profitable classification (40% of strategies must be profitable)
    PROFITABILITY_THRESHOLD = 0.40

    def classify_single(self, strategy_metrics: StrategyMetrics) -> ClassificationResult:
        """Classify a single backtest result.

        Evaluates a single strategy's metrics against the classification criteria.
        The process:
            1. Check if execution was successful
            2. Calculate metrics coverage (sharpe, return, drawdown)
            3. Classify into appropriate level
            4. Provide detailed reason for classification

        Args:
            strategy_metrics: StrategyMetrics object from metrics extraction

        Returns:
            ClassificationResult with level (0-3), reason, and coverage percentage

        Notes:
            - A metric is "extracted" if it is not None
            - Metrics coverage = count of extracted core metrics / 3
            - Level assignment:
              * 0: execution_success=False
              * 1: execution_success=True AND coverage < 60%
              * 2: execution_success=True AND coverage >= 60%
              * 3: Level 2 AND sharpe_ratio is not None AND sharpe_ratio > 0

        Examples:
            >>> classifier = SuccessClassifier()
            >>> # Failed execution
            >>> metrics = StrategyMetrics(execution_success=False)
            >>> result = classifier.classify_single(metrics)
            >>> print(result.level)
            0

            >>> # Valid metrics, profitable
            >>> metrics = StrategyMetrics(
            ...     sharpe_ratio=1.5,
            ...     total_return=0.25,
            ...     max_drawdown=-0.15,
            ...     execution_success=True
            ... )
            >>> result = classifier.classify_single(metrics)
            >>> print(result.level, result.metrics_coverage)
            3 1.0
        """
        logger.debug(
            f"Classifying single strategy: execution_success={strategy_metrics.execution_success}, "
            f"sharpe={strategy_metrics.sharpe_ratio}, "
            f"return={strategy_metrics.total_return}, "
            f"drawdown={strategy_metrics.max_drawdown}"
        )

        # Level 0: Execution failed
        if not strategy_metrics.execution_success:
            logger.debug("Classification: FAILED (execution_success=False)")
            return ClassificationResult(
                level=0,
                reason="Execution failed (execution_success=False)",
                metrics_coverage=0.0,
                profitable_count=None,
                total_count=None
            )

        # Calculate metrics coverage (percentage of core metrics extracted)
        metrics_coverage = self._calculate_metrics_coverage(strategy_metrics)
        extracted_count = int(metrics_coverage * len(self.COVERAGE_METRICS))

        logger.debug(
            f"Metrics coverage: {metrics_coverage:.1%} "
            f"({extracted_count}/{len(self.COVERAGE_METRICS)})"
        )

        # Level 1: Executed but insufficient metrics
        if metrics_coverage < self.METRICS_COVERAGE_THRESHOLD:
            reason = (
                f"Executed but insufficient metrics coverage "
                f"({extracted_count}/{len(self.COVERAGE_METRICS)}, need >= 60%)"
            )
            logger.debug(f"Classification: EXECUTED - {reason}")
            return ClassificationResult(
                level=1,
                reason=reason,
                metrics_coverage=metrics_coverage,
                profitable_count=None,
                total_count=None
            )

        # Determine if strategy is profitable (Sharpe > 0)
        is_profitable = (
            strategy_metrics.sharpe_ratio is not None
            and strategy_metrics.sharpe_ratio > 0
        )

        # Level 3: Valid metrics AND profitable
        if is_profitable:
            reason = (
                f"Valid metrics extracted ({extracted_count}/{len(self.COVERAGE_METRICS)}) "
                f"with profitable performance (Sharpe={strategy_metrics.sharpe_ratio:.2f})"
            )
            logger.debug(f"Classification: PROFITABLE - {reason}")
            return ClassificationResult(
                level=3,
                reason=reason,
                metrics_coverage=metrics_coverage,
                profitable_count=None,
                total_count=None
            )

        # Level 2: Valid metrics but not profitable
        reason = (
            f"Valid metrics extracted ({extracted_count}/{len(self.COVERAGE_METRICS)}) "
            f"but not profitable (Sharpe={strategy_metrics.sharpe_ratio})"
        )
        logger.debug(f"Classification: VALID_METRICS - {reason}")
        return ClassificationResult(
            level=2,
            reason=reason,
            metrics_coverage=metrics_coverage,
            profitable_count=None,
            total_count=None
        )

    def classify_batch(self, results: List[StrategyMetrics]) -> ClassificationResult:
        """Classify a batch of backtest results.

        Evaluates multiple strategy results and provides an aggregate
        classification. The process:
            1. Calculate overall metrics coverage across all results
            2. Count profitable strategies (Sharpe > 0)
            3. Classify batch into appropriate level

        Args:
            results: List of StrategyMetrics objects to classify

        Returns:
            ClassificationResult with aggregate level, reason, and profitability stats

        Notes:
            - Empty list is classified as Level 0 (FAILED)
            - Overall coverage = average coverage across all strategies
            - Profitable count = number of strategies with Sharpe > 0
            - Profitability ratio = profitable_count / total_count
            - Level assignment:
              * 0: No executed strategies (all failed)
              * 1: Average coverage < 60%
              * 2: Average coverage >= 60%
              * 3: Level 2 AND >= 40% strategies profitable

        Examples:
            >>> classifier = SuccessClassifier()
            >>> metrics_list = [
            ...     StrategyMetrics(
            ...         sharpe_ratio=1.5,
            ...         total_return=0.25,
            ...         max_drawdown=-0.15,
            ...         execution_success=True
            ...     ),
            ...     StrategyMetrics(
            ...         sharpe_ratio=0.5,
            ...         total_return=0.10,
            ...         max_drawdown=-0.20,
            ...         execution_success=True
            ...     ),
            ...     StrategyMetrics(execution_success=False),
            ... ]
            >>> result = classifier.classify_batch(metrics_list)
            >>> print(f"Level {result.level}: {result.profitable_count}/{result.total_count} profitable")
            Level 3: 2/3 profitable
        """
        logger.debug(f"Classifying batch of {len(results)} results")

        # Handle empty batch
        if not results:
            logger.warning("Empty batch provided for classification")
            return ClassificationResult(
                level=0,
                reason="No strategies to classify (empty batch)",
                metrics_coverage=0.0,
                profitable_count=0,
                total_count=0
            )

        # Separate executed from failed
        executed_results = [r for r in results if r.execution_success]
        failed_count = len(results) - len(executed_results)

        logger.debug(
            f"Batch analysis: {len(executed_results)} executed, {failed_count} failed"
        )

        # Level 0: All failed
        if not executed_results:
            reason = f"All strategies failed execution ({failed_count}/{len(results)})"
            logger.debug(f"Classification: FAILED - {reason}")
            return ClassificationResult(
                level=0,
                reason=reason,
                metrics_coverage=0.0,
                profitable_count=0,
                total_count=len(results)
            )

        # Calculate average metrics coverage
        avg_coverage = sum(
            self._calculate_metrics_coverage(m) for m in executed_results
        ) / len(executed_results)

        # Count profitable strategies (Sharpe > 0)
        profitable_count = sum(
            1 for m in executed_results
            if m.sharpe_ratio is not None and m.sharpe_ratio > 0
        )

        profitability_ratio = profitable_count / len(executed_results)

        logger.debug(
            f"Batch metrics: avg_coverage={avg_coverage:.1%}, "
            f"profitable={profitable_count}/{len(executed_results)} ({profitability_ratio:.1%})"
        )

        # Level 1: Insufficient coverage
        if avg_coverage < self.METRICS_COVERAGE_THRESHOLD:
            reason = (
                f"Executed batch with insufficient metrics coverage "
                f"(avg {avg_coverage:.1%}, need >= 60%), "
                f"{profitable_count}/{len(executed_results)} profitable"
            )
            logger.debug(f"Classification: EXECUTED - {reason}")
            return ClassificationResult(
                level=1,
                reason=reason,
                metrics_coverage=avg_coverage,
                profitable_count=profitable_count,
                total_count=len(executed_results)
            )

        # Level 3: Valid metrics AND sufficient profitability
        if profitability_ratio >= self.PROFITABILITY_THRESHOLD:
            reason = (
                f"Valid metrics with strong profitability "
                f"({profitable_count}/{len(executed_results)} profitable, "
                f"{profitability_ratio:.1%} >= 40%)"
            )
            logger.debug(f"Classification: PROFITABLE - {reason}")
            return ClassificationResult(
                level=3,
                reason=reason,
                metrics_coverage=avg_coverage,
                profitable_count=profitable_count,
                total_count=len(executed_results)
            )

        # Level 2: Valid metrics but insufficient profitability
        reason = (
            f"Valid metrics with limited profitability "
            f"({profitable_count}/{len(executed_results)} profitable, "
            f"{profitability_ratio:.1%} < 40%)"
        )
        logger.debug(f"Classification: VALID_METRICS - {reason}")
        return ClassificationResult(
            level=2,
            reason=reason,
            metrics_coverage=avg_coverage,
            profitable_count=profitable_count,
            total_count=len(executed_results)
        )

    def _calculate_metrics_coverage(self, metrics: StrategyMetrics) -> float:
        """Calculate coverage percentage for core metrics.

        Determines what percentage of the three core metrics (sharpe_ratio,
        total_return, max_drawdown) were successfully extracted and are not None.

        Args:
            metrics: StrategyMetrics object to evaluate

        Returns:
            Coverage percentage as float (0.0 to 1.0)
            - 0.0: No metrics extracted
            - 0.33: One metric extracted
            - 0.67: Two metrics extracted
            - 1.0: All three metrics extracted

        Examples:
            >>> classifier = SuccessClassifier()
            >>> metrics = StrategyMetrics(
            ...     sharpe_ratio=1.5,
            ...     total_return=0.25,
            ...     max_drawdown=None,  # Missing
            ...     execution_success=True
            ... )
            >>> coverage = classifier._calculate_metrics_coverage(metrics)
            >>> print(f"Coverage: {coverage:.1%}")
            Coverage: 66.7%
        """
        extracted_count = 0

        # Check sharpe_ratio
        if metrics.sharpe_ratio is not None:
            extracted_count += 1
            logger.debug("Sharpe ratio extracted")

        # Check total_return
        if metrics.total_return is not None:
            extracted_count += 1
            logger.debug("Total return extracted")

        # Check max_drawdown
        if metrics.max_drawdown is not None:
            extracted_count += 1
            logger.debug("Max drawdown extracted")

        coverage = extracted_count / len(self.COVERAGE_METRICS)
        logger.debug(
            f"Metrics coverage: {extracted_count}/{len(self.COVERAGE_METRICS)} = {coverage:.1%}"
        )

        return coverage
