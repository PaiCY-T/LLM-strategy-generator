"""
Feedback Loop Integration
==========================

Integration bridge between template recommendation system and existing learning loop.
Maintains backward compatibility while adding template-based intelligence.

Features:
    - Backward compatible with existing feedback mechanisms
    - Template recommendation integration
    - Performance tracking and metrics extraction
    - Iteration history management
    - Validation result integration

Usage:
    from src.feedback.loop_integration import FeedbackLoopIntegrator

    integrator = FeedbackLoopIntegrator(
        template_integrator=template_integrator,
        repository=repository
    )

    feedback = integrator.process_iteration(
        iteration=5,
        strategy_code=code,
        backtest_result=result,
        validation_result=validation
    )

Requirements:
    - Integration requirement: Bridge template system with existing feedback
    - Backward compatibility with current learning loop
"""

from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, field


@dataclass
class IterationFeedback:
    """
    Comprehensive feedback for a single iteration.

    Combines template recommendation, performance metrics, validation results,
    and historical context for learning loop integration.

    Attributes:
        iteration: Iteration number
        template_recommendation: TemplateRecommendation object
        performance_metrics: Performance metrics dictionary
        validation_summary: Validation result summary
        suggested_improvements: List of suggested improvements
        historical_context: Historical iteration context
    """
    iteration: int
    template_recommendation: Any = None  # TemplateRecommendation
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_summary: Dict[str, Any] = field(default_factory=dict)
    suggested_improvements: List[str] = field(default_factory=list)
    historical_context: Dict[str, Any] = field(default_factory=dict)


class FeedbackLoopIntegrator:
    """
    Integration bridge for template feedback and learning loop.

    Integrates the new template recommendation system with existing learning
    loop infrastructure, maintaining backward compatibility while adding
    template-based intelligence.

    Workflow:
        1. Extract metrics from backtest result
        2. Get template recommendation
        3. Incorporate validation feedback
        4. Generate suggested improvements
        5. Track iteration history
        6. Return comprehensive IterationFeedback

    Example:
        >>> integrator = FeedbackLoopIntegrator(template_integrator, repository)
        >>> feedback = integrator.process_iteration(
        ...     iteration=5,
        ...     strategy_code=code,
        ...     backtest_result={'sharpe_ratio': 0.8},
        ...     validation_result=validation
        ... )
        >>> print(feedback.template_recommendation.template_name)
        'MastiffTemplate'  # Exploration mode

    Attributes:
        template_integrator: TemplateFeedbackIntegrator instance
        repository: HallOfFameRepository instance
        iteration_history: List of IterationFeedback objects
        logger: Python logger
    """

    def __init__(
        self,
        template_integrator: Any = None,  # TemplateFeedbackIntegrator
        repository: Any = None,  # HallOfFameRepository
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize feedback loop integrator.

        Args:
            template_integrator: TemplateFeedbackIntegrator instance
            repository: HallOfFameRepository instance
            logger: Optional logger
        """
        self.template_integrator = template_integrator
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

        # Track iteration history
        self.iteration_history: List[IterationFeedback] = []

        self.logger.info("FeedbackLoopIntegrator initialized")

    def process_iteration(
        self,
        iteration: int,
        strategy_code: Optional[str] = None,
        backtest_result: Optional[Dict[str, Any]] = None,
        validation_result: Any = None,
        current_params: Optional[Dict[str, Any]] = None,
        risk_profile: Optional[str] = None
    ) -> IterationFeedback:
        """
        Process a single iteration and generate comprehensive feedback.

        Main integration point for learning loop. Orchestrates template
        recommendation, metrics extraction, and feedback generation.

        Args:
            iteration: Iteration number
            strategy_code: Generated strategy code
            backtest_result: Backtest result dictionary
            validation_result: ValidationResult from validation system
            current_params: Current parameters used
            risk_profile: Optional risk profile

        Returns:
            IterationFeedback with comprehensive feedback

        Example:
            >>> feedback = integrator.process_iteration(
            ...     iteration=5,
            ...     strategy_code=code,
            ...     backtest_result={'sharpe_ratio': 0.8, 'max_drawdown': 0.12},
            ...     validation_result=validation
            ... )
        """
        self.logger.info(f"Processing iteration {iteration}")

        # Step 1: Extract performance metrics
        performance_metrics = self._extract_performance_metrics(backtest_result)

        # Step 2: Get template recommendation (if template_integrator available)
        template_recommendation = None
        if self.template_integrator:
            try:
                template_recommendation = self.template_integrator.recommend_template(
                    current_metrics=performance_metrics,
                    iteration=iteration,
                    validation_result=validation_result,
                    strategy_code=strategy_code,
                    current_params=current_params,
                    risk_profile=risk_profile
                )

                self.logger.info(
                    f"Template recommendation: {template_recommendation.template_name} "
                    f"(score={template_recommendation.match_score:.2f})"
                )

            except (ValueError, KeyError) as e:
                # Handle parameter validation errors
                self.logger.error(
                    f"Template recommendation failed due to invalid parameters: {e}"
                )
                template_recommendation = None

            except AttributeError as e:
                # Handle missing attributes or methods
                self.logger.error(
                    f"Template recommendation failed due to missing attribute: {e}"
                )
                template_recommendation = None

            except Exception as e:
                # Handle unexpected errors with fallback
                self.logger.error(
                    f"Template recommendation failed unexpectedly: {e}",
                    exc_info=True
                )
                template_recommendation = None

        # Step 3: Extract validation summary
        validation_summary = self._extract_validation_summary(validation_result)

        # Step 4: Generate suggested improvements
        suggested_improvements = self._generate_improvement_suggestions(
            performance_metrics=performance_metrics,
            validation_summary=validation_summary,
            template_recommendation=template_recommendation
        )

        # Step 5: Gather historical context
        historical_context = self._gather_historical_context(iteration)

        # Step 6: Create iteration feedback
        feedback = IterationFeedback(
            iteration=iteration,
            template_recommendation=template_recommendation,
            performance_metrics=performance_metrics,
            validation_summary=validation_summary,
            suggested_improvements=suggested_improvements,
            historical_context=historical_context
        )

        # Track in history
        self.iteration_history.append(feedback)

        # Keep only last 20 iterations to avoid memory growth
        if len(self.iteration_history) > 20:
            self.iteration_history = self.iteration_history[-20:]

        self.logger.info(f"Iteration {iteration} processed successfully")

        return feedback

    def _extract_performance_metrics(
        self,
        backtest_result: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract performance metrics from backtest result.

        Args:
            backtest_result: Backtest result dictionary

        Returns:
            Standardized performance metrics dictionary
        """
        if not backtest_result:
            return {}

        # Extract common metrics with fallbacks
        metrics = {
            'sharpe_ratio': backtest_result.get('sharpe_ratio', 0.0),
            'max_drawdown': abs(backtest_result.get('max_drawdown', 0.0)),
            'total_return': backtest_result.get('total_return', 0.0),
            'volatility': backtest_result.get('volatility', 0.0),
            'win_rate': backtest_result.get('win_rate', 0.0),
            'profit_factor': backtest_result.get('profit_factor', 0.0),
            'num_trades': backtest_result.get('num_trades', 0)
        }

        return metrics

    def _extract_validation_summary(
        self,
        validation_result: Any
    ) -> Dict[str, Any]:
        """
        Extract summary from validation result.

        Args:
            validation_result: ValidationResult object

        Returns:
            Validation summary dictionary
        """
        if not validation_result:
            return {'status': 'NOT_VALIDATED'}

        summary = {}

        # Extract basic info
        if hasattr(validation_result, 'status'):
            summary['status'] = validation_result.status
        else:
            summary['status'] = 'UNKNOWN'

        # Count errors by severity
        if hasattr(validation_result, 'errors'):
            try:
                from ..validation import Severity

                critical_count = sum(
                    1 for e in validation_result.errors
                    if hasattr(e, 'severity') and e.severity == Severity.CRITICAL
                )
                moderate_count = sum(
                    1 for e in validation_result.errors
                    if hasattr(e, 'severity') and e.severity == Severity.MODERATE
                )
                low_count = sum(
                    1 for e in validation_result.errors
                    if hasattr(e, 'severity') and e.severity == Severity.LOW
                )

                summary['critical_errors'] = critical_count
                summary['moderate_errors'] = moderate_count
                summary['low_errors'] = low_count
                summary['total_errors'] = len(validation_result.errors)

            except ImportError:
                summary['total_errors'] = len(validation_result.errors)

        # Count warnings
        if hasattr(validation_result, 'warnings'):
            summary['warnings'] = len(validation_result.warnings)

        return summary

    def _generate_improvement_suggestions(
        self,
        performance_metrics: Dict[str, Any],
        validation_summary: Dict[str, Any],
        template_recommendation: Any
    ) -> List[str]:
        """
        Generate improvement suggestions based on feedback.

        Args:
            performance_metrics: Performance metrics
            validation_summary: Validation summary
            template_recommendation: Template recommendation

        Returns:
            List of improvement suggestions
        """
        suggestions = []

        # Performance-based suggestions
        sharpe = performance_metrics.get('sharpe_ratio', 0.0)
        max_drawdown = performance_metrics.get('max_drawdown', 0.0)

        if sharpe < 0.5:
            suggestions.append(
                "Low Sharpe ratio detected. Consider template change for better risk-adjusted returns."
            )

        if max_drawdown > 0.20:
            suggestions.append(
                "High drawdown detected. Consider adding risk management filters or stop-loss mechanisms."
            )

        # Validation-based suggestions
        if validation_summary.get('critical_errors', 0) > 0:
            suggestions.append(
                f"Critical validation errors found ({validation_summary['critical_errors']}). "
                f"Address before proceeding."
            )

        if validation_summary.get('moderate_errors', 0) > 0:
            suggestions.append(
                f"Moderate validation errors ({validation_summary['moderate_errors']}). "
                f"Review and fix to improve strategy quality."
            )

        # Template recommendation suggestions
        if template_recommendation:
            if template_recommendation.exploration_mode:
                suggestions.append(
                    "⚡ Exploration mode active. Test different template architecture for diversity."
                )

            if template_recommendation.champion_reference:
                suggestions.append(
                    f"Champion-based parameters available. "
                    f"Consider using proven configuration from {template_recommendation.champion_reference}."
                )

        return suggestions

    def _gather_historical_context(self, current_iteration: int) -> Dict[str, Any]:
        """
        Gather historical context from previous iterations.

        Args:
            current_iteration: Current iteration number

        Returns:
            Historical context dictionary
        """
        if not self.iteration_history:
            return {
                'total_iterations': current_iteration,
                'avg_sharpe': 0.0,
                'best_sharpe': 0.0,
                'template_usage': {}
            }

        # Calculate statistics from history
        sharpe_ratios = [
            f.performance_metrics.get('sharpe_ratio', 0.0)
            for f in self.iteration_history
        ]

        template_names = [
            f.template_recommendation.template_name
            for f in self.iteration_history
            if f.template_recommendation
        ]

        # Template usage distribution
        template_usage = {}
        for template in template_names:
            template_usage[template] = template_usage.get(template, 0) + 1

        return {
            'total_iterations': current_iteration,
            'avg_sharpe': sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0.0,
            'best_sharpe': max(sharpe_ratios) if sharpe_ratios else 0.0,
            'worst_sharpe': min(sharpe_ratios) if sharpe_ratios else 0.0,
            'template_usage': template_usage,
            'recent_templates': template_names[-5:] if template_names else []
        }

    def get_iteration_summary(self, iteration: int) -> Optional[IterationFeedback]:
        """
        Get feedback summary for a specific iteration.

        Args:
            iteration: Iteration number

        Returns:
            IterationFeedback or None if not found
        """
        for feedback in reversed(self.iteration_history):
            if feedback.iteration == iteration:
                return feedback

        return None

    def get_learning_trajectory(self) -> Dict[str, Any]:
        """
        Get learning trajectory statistics across all iterations.

        Returns:
            Dictionary with learning trajectory stats
        """
        if not self.iteration_history:
            return {'status': 'NO_DATA'}

        sharpe_trajectory = [
            f.performance_metrics.get('sharpe_ratio', 0.0)
            for f in self.iteration_history
        ]

        # Calculate trend
        if len(sharpe_trajectory) >= 3:
            recent_avg = sum(sharpe_trajectory[-3:]) / 3
            early_avg = sum(sharpe_trajectory[:3]) / 3
            improvement = recent_avg - early_avg
        else:
            improvement = 0.0

        return {
            'total_iterations': len(self.iteration_history),
            'sharpe_trajectory': sharpe_trajectory,
            'current_sharpe': sharpe_trajectory[-1] if sharpe_trajectory else 0.0,
            'best_sharpe': max(sharpe_trajectory) if sharpe_trajectory else 0.0,
            'improvement_trend': improvement,
            'is_improving': improvement > 0
        }
