"""
Template Rationale Generator - Recommendation Explanation
=========================================================

Generate human-readable markdown explanations for template recommendations.
Provides comprehensive rationale including template selection, success rates,
parameter suggestions, and champion references.

Features:
    - Markdown-formatted explanations
    - Success rate statistics from analytics
    - Champion-based rationale
    - Performance-based rationale
    - Exploration mode justification
    - Parameter range explanations

Usage:
    from src.feedback import RationaleGenerator, TemplateAnalytics
    from src.feedback.template_feedback import TemplateRecommendation

    analytics = TemplateAnalytics()
    generator = RationaleGenerator(analytics)

    recommendation = TemplateRecommendation(
        template_name='TurtleTemplate',
        rationale='Performance-based selection',
        match_score=0.85,
        suggested_params={'n_stocks': 10}
    )

    markdown = generator.generate_rationale(
        recommendation=recommendation,
        current_metrics={'sharpe_ratio': 0.8}
    )
    print(markdown)

Requirements:
    - Requirement 2.15: Rationale generation
    - Requirement 4.1: Template recommendation explanation
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging


@dataclass
class StrategyGenome:
    """
    Minimal StrategyGenome type for champion references.

    Attributes:
        genome_id: Unique identifier
        template_name: Template used
        parameters: Parameter dictionary
        sharpe_ratio: Performance metric
    """
    genome_id: str
    template_name: str
    parameters: Dict[str, Any]
    sharpe_ratio: float


class RationaleGenerator:
    """
    Generate human-readable markdown explanations for template recommendations.

    Provides comprehensive, markdown-formatted explanations for why a specific
    template was recommended. Integrates with TemplateAnalytics for empirical
    success rate data and Hall of Fame for champion references.

    Output Format (Markdown):
        ## Template Recommendation: TurtleTemplate

        ### Selection Rationale
        - Performance-based selection (Sharpe 0.80)
        - Template success rate: 80% (12/15 attempts)

        ### Suggested Parameters
        - n_stocks: 10 (range: 8-12) - Number of stocks in portfolio
        - ma_short: 20 (range: 16-24) - Short moving average period

        ### Expected Characteristics
        - 6-layer AND filtering provides robustness
        - Revenue growth + price strength momentum

    Attributes:
        analytics: TemplateAnalytics instance for success rate data
        logger: Python logger for rationale generation tracking

    Example:
        >>> analytics = TemplateAnalytics()
        >>> generator = RationaleGenerator(analytics)
        >>>
        >>> recommendation = TemplateRecommendation(
        ...     template_name='TurtleTemplate',
        ...     rationale='Sharpe 0.8: Robust filtering needed',
        ...     match_score=0.85,
        ...     suggested_params={'n_stocks': 10, 'ma_short': 20}
        ... )
        >>>
        >>> markdown = generator.generate_rationale(recommendation)
        >>> print(markdown)

    Requirements:
        - Task 43: Rationale generation with markdown output
        - Requirement 2.15: Human-readable template explanations
    """

    # Performance tier definitions for tier classification
    PERFORMANCE_TIERS = {
        'champion': {'min_sharpe': 2.0, 'label': 'Champion tier'},
        'contender': {'min_sharpe': 1.5, 'label': 'Contender tier'},
        'solid': {'min_sharpe': 1.0, 'label': 'Solid performance'},
        'archive': {'min_sharpe': 0.5, 'label': 'Archive tier'},
        'poor': {'min_sharpe': 0.0, 'label': 'Poor performance'}
    }

    # Template descriptions for rationale generation (extended version of TEMPLATE_CHARACTERISTICS)
    TEMPLATE_DESCRIPTIONS = {
        'TurtleTemplate': {
            'architecture': '6-layer AND filtering',
            'selection': 'Revenue growth weighting with .is_largest()',
            'characteristics': 'Robust filtering, trend-following momentum',
            'expected_sharpe': (1.5, 2.5),
            'risk_profile': 'stable'
        },
        'MastiffTemplate': {
            'architecture': '6 contrarian conditions',
            'selection': 'Contrarian volume selection with .is_smallest()',
            'characteristics': 'High-conviction concentrated positions',
            'expected_sharpe': (1.2, 2.0),
            'risk_profile': 'concentrated'
        },
        'FactorTemplate': {
            'architecture': 'Single-factor cross-sectional ranking',
            'selection': 'Factor-based .rank() for relative strength',
            'characteristics': 'Simple, stable, low-volatility strategy',
            'expected_sharpe': (0.8, 1.3),
            'risk_profile': 'stable'
        },
        'MomentumTemplate': {
            'architecture': 'Momentum + catalyst combination',
            'selection': 'Momentum focus with .is_largest()',
            'characteristics': 'Fast iteration with rapid feedback cycles',
            'expected_sharpe': (0.8, 1.5),
            'risk_profile': 'fast'
        }
    }

    # Template characteristics for explanation
    TEMPLATE_CHARACTERISTICS = {
        'TurtleTemplate': {
            'architecture': '6-layer AND filtering',
            'selection_method': '.is_largest() for revenue growth weighting',
            'characteristics': 'Trend-following momentum strategy',
            'expected_sharpe': (1.5, 2.5),
            'parameter_descriptions': {
                'n_stocks': 'Number of stocks in portfolio',
                'ma_short': 'Short moving average period',
                'ma_long': 'Long moving average period',
                'stop_loss': 'Maximum loss per position',
                'yield_threshold': 'Minimum dividend yield',
                'op_margin_threshold': 'Minimum operating margin',
                'rev_short': 'Short revenue period',
                'rev_long': 'Long revenue period',
                'director_threshold': 'Minimum director ownership',
                'vol_min': 'Minimum volume filter',
                'vol_max': 'Maximum volume filter'
            }
        },
        'MastiffTemplate': {
            'architecture': '6 contrarian conditions',
            'selection_method': '.is_smallest() for contrarian volume selection',
            'characteristics': 'High-conviction concentrated positions',
            'expected_sharpe': (1.2, 2.0),
            'parameter_descriptions': {
                'n_stocks': 'Number of stocks (≤10 for concentration)',
                'price_high_period': 'Price high lookback period',
                'rev_decline_short': 'Revenue decline short period',
                'rev_decline_long': 'Revenue decline long period',
                'rev_growth_period': 'Revenue growth period',
                'momentum_period': 'Momentum filter period',
                'vol_period': 'Volume moving average period',
                'stop_loss': 'Stop loss threshold (≥6%)',
                'position_limit': 'Position size limit (≥15%)'
            }
        },
        'FactorTemplate': {
            'architecture': 'Single-factor cross-sectional ranking',
            'selection_method': '.rank() for relative strength',
            'characteristics': 'Simple, stable, low-volatility strategy',
            'expected_sharpe': (0.8, 1.3),
            'parameter_descriptions': {
                'n_stocks': 'Number of stocks in portfolio',
                'factor_type': 'Factor type (momentum, value, quality, volume)',
                'factor_threshold': 'Factor percentile threshold',
                'ma_confirm_short': 'Technical confirmation MA short',
                'ma_confirm_long': 'Technical confirmation MA long',
                'vol_min': 'Minimum volume threshold',
                'rebalance_freq': 'Rebalancing frequency'
            }
        },
        'MomentumTemplate': {
            'architecture': 'Momentum + catalyst combination',
            'selection_method': '.is_largest() for momentum focus',
            'characteristics': 'Fast iteration with rapid feedback cycles',
            'expected_sharpe': (0.8, 1.5),
            'parameter_descriptions': {
                'n_stocks': 'Number of stocks in portfolio',
                'momentum_period': 'Momentum calculation period',
                'rev_accel_short': 'Revenue acceleration short period',
                'rev_accel_long': 'Revenue acceleration long period',
                'vol_min': 'Minimum volume threshold',
                'rebalance_freq': 'Rebalancing frequency (W or M)'
            }
        }
    }

    def __init__(
        self,
        analytics: Any = None,  # TemplateAnalytics
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize rationale generator with analytics for success rate data.

        Args:
            analytics: TemplateAnalytics instance for empirical success rates
            logger: Optional logger for rationale generation tracking

        Example:
            >>> from src.feedback import TemplateAnalytics
            >>> analytics = TemplateAnalytics()
            >>> generator = RationaleGenerator(analytics)
        """
        self.analytics = analytics
        self.logger = logger or logging.getLogger(__name__)

        self.logger.info("RationaleGenerator initialized")

    def _get_performance_tier(self, sharpe_ratio: float) -> Dict:
        """
        Get performance tier classification based on Sharpe ratio.

        Args:
            sharpe_ratio: Sharpe ratio to classify

        Returns:
            Dict with 'min_sharpe' and 'label' keys

        Classification:
            - Champion tier: Sharpe ≥ 2.0
            - Contender tier: 1.5 ≤ Sharpe < 2.0
            - Solid performance: 1.0 ≤ Sharpe < 1.5
            - Archive tier: 0.5 ≤ Sharpe < 1.0
            - Poor performance: Sharpe < 0.5
        """
        if sharpe_ratio >= 2.0:
            return self.PERFORMANCE_TIERS['champion']
        elif sharpe_ratio >= 1.5:
            return self.PERFORMANCE_TIERS['contender']
        elif sharpe_ratio >= 1.0:
            return self.PERFORMANCE_TIERS['solid']
        elif sharpe_ratio >= 0.5:
            return self.PERFORMANCE_TIERS['archive']
        else:
            return self.PERFORMANCE_TIERS['poor']

    def generate_performance_rationale(
        self,
        template_name: str,
        sharpe: float,
        success_rate: float,
        drawdown: Optional[float] = None,
        iteration: Optional[int] = None
    ) -> str:
        """
        Generate performance-based template recommendation rationale.

        Args:
            template_name: Template name
            sharpe: Current Sharpe ratio
            success_rate: Template success rate (0.0-1.0)
            drawdown: Optional max drawdown
            iteration: Optional iteration number

        Returns:
            Human-readable rationale string
        """
        tier = self._get_performance_tier(sharpe)
        template_info = self.TEMPLATE_DESCRIPTIONS.get(template_name, {})

        lines = []
        lines.append(f"**{template_name}** selected based on performance tier:")
        lines.append(f"- Performance: {tier['label']} (Sharpe {sharpe:.2f})")
        lines.append(f"- Success rate: {success_rate:.0%}")

        if drawdown is not None:
            lines.append(f"- Max drawdown: {drawdown:.1%}")

        if iteration is not None:
            lines.append(f"- Iteration: {iteration}")

        # Add tier-specific guidance
        if sharpe < 0.5:
            lines.append("- ⚠️ Poor performance detected - rapid iteration recommended")
        elif sharpe >= 2.0:
            lines.append("- ✨ Champion-tier performance - maintain current approach")

        # Add template characteristics
        if 'characteristics' in template_info:
            lines.append(f"- Strategy: {template_info['characteristics']}")

        return '\n'.join(lines)

    def generate_exploration_rationale(
        self,
        template_name: str,
        iteration: int,
        recent_templates: list,
        success_rate: float
    ) -> str:
        """
        Generate exploration mode recommendation rationale.

        Args:
            template_name: Template name
            iteration: Current iteration
            recent_templates: List of recently used template names
            success_rate: Template success rate

        Returns:
            Human-readable rationale string
        """
        lines = []
        lines.append(f"**⚡ EXPLORATION MODE** - Iteration {iteration}")
        lines.append(f"Selected: {template_name}")
        lines.append(f"Success rate: {success_rate:.0%}")
        lines.append("")
        lines.append("Exploration objectives:")
        lines.append("- Test alternative template architectures")
        lines.append("- Prevent over-fitting to single template")
        lines.append("- Expand parameter search space (±30%)")

        # Show avoided templates
        if recent_templates:
            unique_recent = list(set(recent_templates))
            if len(unique_recent) > 0:
                lines.append("")
                lines.append("Avoiding recently used templates:")
                for template in unique_recent:
                    count = recent_templates.count(template)
                    lines.append(f"- {template} (used {count}x recently)")

        return '\n'.join(lines)

    def generate_champion_rationale(
        self,
        template_name: str,
        champion_id: str,
        champion_sharpe: float,
        champion_params: Dict
    ) -> str:
        """
        Generate champion-based recommendation rationale.

        Args:
            template_name: Template name
            champion_id: Champion genome ID
            champion_sharpe: Champion Sharpe ratio
            champion_params: Champion parameters

        Returns:
            Human-readable rationale string
        """
        lines = []
        lines.append(f"**{template_name}** - Champion-based recommendation")
        lines.append(f"- Based on champion: {champion_id}")
        lines.append(f"- Champion Sharpe: {champion_sharpe:.2f}")
        lines.append("")
        lines.append("Champion parameters:")

        # Format parameters
        for param, value in champion_params.items():
            if not param.startswith('champion_'):
                lines.append(f"- {param}={value}")

        lines.append("")
        lines.append("Variation strategy:")
        lines.append("- Parameters varied ±20% around champion configuration")
        lines.append("- Proven architecture with exploration around optimal values")

        return '\n'.join(lines)

    def generate_validation_rationale(
        self,
        template_name: str,
        num_param_errors: Optional[int] = 0,
        num_complexity_errors: Optional[int] = 0,
        simplified_from: Optional[str] = None
    ) -> str:
        """
        Generate validation feedback rationale.

        Args:
            template_name: Template name
            num_param_errors: Number of parameter validation errors
            num_complexity_errors: Number of complexity errors
            simplified_from: Original template if simplified

        Returns:
            Human-readable rationale string
        """
        lines = []

        if simplified_from:
            lines.append(f"**{template_name}** - Simplified from {simplified_from}")
            lines.append("- Template complexity reduced")
            lines.append("- Using simpler architecture for better validation")
        else:
            lines.append(f"**{template_name}** - Validation feedback")

        if num_param_errors > 0:
            lines.append(f"- Parameter errors detected: {num_param_errors}")
            lines.append("- Adjusting parameter ranges to meet validation requirements")

        if num_complexity_errors > 0:
            lines.append(f"- Complexity errors detected: {num_complexity_errors}")
            lines.append("- Reducing strategy complexity to pass validation")

        if num_param_errors == 0 and num_complexity_errors == 0:
            lines.append("- ✅ All validation checks passed")

        return '\n'.join(lines)

    def generate_risk_profile_rationale(
        self,
        template_name: str,
        risk_profile: str,
        success_rate: float
    ) -> str:
        """
        Generate risk profile-based rationale.

        Args:
            template_name: Template name
            risk_profile: Risk profile ('concentrated', 'stable', 'fast')
            success_rate: Template success rate

        Returns:
            Human-readable rationale string
        """
        lines = []
        lines.append(f"**{template_name}** - Risk profile: {risk_profile}")
        lines.append(f"Success rate: {success_rate:.0%}")
        lines.append("")

        # Risk profile descriptions
        if risk_profile == 'concentrated':
            lines.append("Concentrated strategy characteristics:")
            lines.append("- High-conviction positions (≤10 stocks)")
            lines.append("- Higher risk, higher reward potential")
            lines.append("- Requires strong risk management")
        elif risk_profile == 'stable':
            lines.append("Stable strategy characteristics:")
            lines.append("- Diversified portfolio approach")
            lines.append("- Lower volatility, consistent returns")
            lines.append("- Suitable for risk-averse profiles")
        elif risk_profile == 'fast':
            lines.append("Fast iteration characteristics:")
            lines.append("- Rapid feedback cycles (weekly/monthly)")
            lines.append("- Quick adaptation to market changes")
            lines.append("- Higher turnover, momentum focus")

        template_info = self.TEMPLATE_DESCRIPTIONS.get(template_name, {})
        if 'characteristics' in template_info:
            lines.append("")
            lines.append(f"Strategy: {template_info['characteristics']}")

        return '\n'.join(lines)

    def generate_rationale(
        self,
        recommendation: Any,  # TemplateRecommendation
        current_metrics: Optional[Dict[str, Any]] = None,
        champion_genome: Optional[StrategyGenome] = None
    ) -> str:
        """
        Generate human-readable markdown rationale for template recommendation.

        Creates comprehensive explanation including:
        - Template selection reason
        - Success rate statistics from analytics
        - Parameter suggestions with ranges and descriptions
        - Champion references (if applicable)
        - Exploration justification (if exploration mode)
        - Expected characteristics and architecture

        Output Format (Markdown):
            ## Template Recommendation: TurtleTemplate

            ### Selection Rationale
            - Performance-based selection (Sharpe 0.80)
            - Template success rate: 80% (12/15 attempts)
            - Match confidence: 85%

            ### Suggested Parameters
            - n_stocks: 10 (range: 8-12) - Number of stocks in portfolio
            - ma_short: 20 (range: 16-24) - Short moving average period
            - ma_long: 60 (range: 42-78) - Long moving average period

            ### Champion Reference
            - Based on champion genome_42 (Sharpe 2.30)
            - Champion template: TurtleTemplate

            ### Expected Characteristics
            - 6-layer AND filtering provides robustness
            - Trend-following momentum strategy
            - Expected Sharpe range: 1.5-2.5

        Args:
            recommendation: TemplateRecommendation object with template_name, rationale, etc.
            current_metrics: Optional current performance metrics (sharpe_ratio, etc.)
            champion_genome: Optional StrategyGenome for champion-based explanations

        Returns:
            Markdown-formatted rationale string

        Example:
            >>> recommendation = TemplateRecommendation(
            ...     template_name='TurtleTemplate',
            ...     rationale='Sharpe 0.8 in target range',
            ...     match_score=0.85,
            ...     suggested_params={'n_stocks': 10, 'ma_short': 20},
            ...     champion_reference='genome_42',
            ...     exploration_mode=False
            ... )
            >>>
            >>> markdown = generator.generate_rationale(recommendation)
            >>> print(markdown)

        Requirements:
            - Task 43: Generate markdown-formatted explanations
            - Requirement 2.15: Rationale generation
        """
        template_name = recommendation.template_name

        # Build markdown sections
        sections = []

        # Header
        sections.append(f"## Template Recommendation: {template_name}")
        sections.append("")

        # Section 1: Selection Rationale
        sections.append("### Selection Rationale")
        sections.extend(self._generate_selection_rationale(
            recommendation=recommendation,
            current_metrics=current_metrics
        ))
        sections.append("")

        # Section 2: Suggested Parameters
        if recommendation.suggested_params:
            sections.append("### Suggested Parameters")
            sections.extend(self._generate_parameter_explanations(
                template_name=template_name,
                suggested_params=recommendation.suggested_params
            ))
            sections.append("")

        # Section 3: Champion Reference (if applicable)
        if recommendation.champion_reference or champion_genome:
            sections.append("### Champion Reference")
            sections.extend(self._generate_champion_explanation(
                recommendation=recommendation,
                champion_genome=champion_genome
            ))
            sections.append("")

        # Section 4: Exploration Mode (if applicable)
        if recommendation.exploration_mode:
            sections.append("### Exploration Mode")
            sections.extend(self._generate_exploration_explanation(
                recommendation=recommendation
            ))
            sections.append("")

        # Section 5: Expected Characteristics
        sections.append("### Expected Characteristics")
        sections.extend(self._generate_characteristics_explanation(
            template_name=template_name
        ))
        sections.append("")

        # Join all sections
        markdown = "\n".join(sections)

        self.logger.info(
            f"Generated rationale for {template_name} "
            f"(exploration={recommendation.exploration_mode}, "
            f"champion={bool(recommendation.champion_reference)})"
        )

        return markdown

    def _generate_selection_rationale(
        self,
        recommendation: Any,
        current_metrics: Optional[Dict[str, Any]]
    ) -> list:
        """
        Generate selection rationale section.

        Args:
            recommendation: TemplateRecommendation object
            current_metrics: Optional current metrics

        Returns:
            List of markdown lines for selection rationale
        """
        lines = []

        # Primary rationale from recommendation
        lines.append(f"- {recommendation.rationale}")

        # Success rate from analytics (if available)
        if self.analytics:
            try:
                stats = self.analytics.get_template_statistics(recommendation.template_name)

                if stats.get('has_data', False):
                    total_usage = stats['total_usage']
                    success_rate = stats['success_rate']

                    # Calculate successful count
                    successful_count = int(total_usage * success_rate)

                    lines.append(
                        f"- Template success rate: {success_rate:.0%} "
                        f"({successful_count}/{total_usage} attempts)"
                    )

                    # Add average Sharpe if available
                    if stats.get('avg_sharpe', 0) > 0:
                        lines.append(f"- Historical average Sharpe: {stats['avg_sharpe']:.2f}")

                else:
                    lines.append("- No historical data available for this template")

            except Exception as e:
                self.logger.warning(f"Failed to fetch analytics for {recommendation.template_name}: {e}")

        # Match confidence score
        lines.append(f"- Match confidence: {recommendation.match_score:.0%}")

        # Current metrics context (if provided)
        if current_metrics:
            sharpe = current_metrics.get('sharpe_ratio', 0.0)
            if sharpe > 0:
                lines.append(f"- Current Sharpe ratio: {sharpe:.2f}")

        return lines

    def _generate_parameter_explanations(
        self,
        template_name: str,
        suggested_params: Dict[str, Any]
    ) -> list:
        """
        Generate parameter explanations section.

        Args:
            template_name: Template name
            suggested_params: Suggested parameter dictionary

        Returns:
            List of markdown lines for parameter explanations
        """
        lines = []

        # Get parameter descriptions for this template
        template_info = self.TEMPLATE_CHARACTERISTICS.get(template_name, {})
        param_descriptions = template_info.get('parameter_descriptions', {})

        # Format each parameter with description and range
        for param_name, param_value in suggested_params.items():
            # Skip metadata parameters
            if param_name in ['champion_id', 'champion_sharpe', 'champion_template', 'rationale']:
                continue

            # Get description
            description = param_descriptions.get(param_name, 'Parameter value')

            # Calculate range (±20% for exploration)
            range_str = ""
            if isinstance(param_value, (int, float)):
                lower = param_value * 0.8
                upper = param_value * 1.2

                if isinstance(param_value, int):
                    range_str = f" (range: {int(lower)}-{int(upper)})"
                else:
                    range_str = f" (range: {lower:.2f}-{upper:.2f})"

            # Format line
            lines.append(f"- {param_name}: {param_value}{range_str} - {description}")

        if not lines:
            lines.append("- No specific parameter suggestions (using template defaults)")

        return lines

    def _generate_champion_explanation(
        self,
        recommendation: Any,
        champion_genome: Optional[StrategyGenome]
    ) -> list:
        """
        Generate champion reference explanation section.

        Args:
            recommendation: TemplateRecommendation object
            champion_genome: Optional StrategyGenome for detailed info

        Returns:
            List of markdown lines for champion explanation
        """
        lines = []

        # If champion_genome provided, use it for detailed info
        if champion_genome:
            lines.append(f"- Based on champion {champion_genome.genome_id} (Sharpe {champion_genome.sharpe_ratio:.2f})")
            lines.append(f"- Champion template: {champion_genome.template_name}")

            # Include champion parameters
            if champion_genome.parameters:
                param_summary = ', '.join([
                    f"{k}={v}" for k, v in champion_genome.parameters.items()
                    if not k.startswith('champion_')
                ])
                if param_summary:
                    lines.append(f"- Champion parameters: {param_summary}")

        # Otherwise, use champion_reference from recommendation
        elif recommendation.champion_reference:
            lines.append(f"- Based on champion {recommendation.champion_reference}")

            # Extract champion info from suggested_params if available
            if 'champion_sharpe' in recommendation.suggested_params:
                champion_sharpe = recommendation.suggested_params['champion_sharpe']
                lines.append(f"- Champion Sharpe: {champion_sharpe:.2f}")

            if 'champion_template' in recommendation.suggested_params:
                champion_template = recommendation.suggested_params['champion_template']
                lines.append(f"- Champion template: {champion_template}")

        # Add variation note
        lines.append("- Variation range ±20% for exploration around proven configuration")

        return lines

    def _generate_exploration_explanation(
        self,
        recommendation: Any
    ) -> list:
        """
        Generate exploration mode justification section.

        Args:
            recommendation: TemplateRecommendation object

        Returns:
            List of markdown lines for exploration explanation
        """
        lines = []

        lines.append("- Exploration mode activated (every 5th iteration)")
        lines.append("- Template diversity: Testing alternative architectures")
        lines.append("- Expanded parameter ranges (±30%) for broader exploration")
        lines.append("- Prevents over-fitting to single template architecture")

        return lines

    def _generate_characteristics_explanation(
        self,
        template_name: str
    ) -> list:
        """
        Generate expected characteristics explanation section.

        Args:
            template_name: Template name

        Returns:
            List of markdown lines for characteristics explanation
        """
        lines = []

        template_info = self.TEMPLATE_CHARACTERISTICS.get(template_name, {})

        if not template_info:
            lines.append(f"- Template: {template_name}")
            return lines

        # Architecture
        architecture = template_info.get('architecture', 'Unknown architecture')
        lines.append(f"- {architecture}")

        # Selection method
        selection = template_info.get('selection_method', 'Unknown selection')
        lines.append(f"- {selection}")

        # Characteristics
        characteristics = template_info.get('characteristics', 'Strategy characteristics')
        lines.append(f"- {characteristics}")

        # Expected Sharpe range
        expected_sharpe = template_info.get('expected_sharpe', (0.0, 0.0))
        if expected_sharpe[0] > 0:
            lines.append(f"- Expected Sharpe range: {expected_sharpe[0]:.1f}-{expected_sharpe[1]:.1f}")

        return lines
