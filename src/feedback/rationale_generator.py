"""
Template Rationale Generator
=============================

Natural language rationale generation for template recommendations.
Provides detailed, human-readable explanations for template selection decisions.

Features:
    - Performance-based rationale generation
    - Champion-reference explanations
    - Exploration mode justifications
    - Validation feedback incorporation
    - Multi-factor decision explanation

Usage:
    from src.feedback.rationale_generator import RationaleGenerator

    generator = RationaleGenerator()
    rationale = generator.generate_performance_rationale(
        template_name='TurtleTemplate',
        sharpe=0.8,
        success_rate=0.80
    )
    print(rationale)

Requirements:
    - Requirement 4.1: Template recommendation rationale generation
"""

from typing import Dict, Any, Optional, List


class RationaleGenerator:
    """
    Generate natural language rationales for template recommendations.

    Provides comprehensive, human-readable explanations for why a specific
    template was recommended based on performance metrics, champion analysis,
    exploration mode, or validation feedback.

    Rationale Components:
        1. Primary reason: Performance tier, exploration mode, or validation
        2. Template characteristics: Architecture, expected performance
        3. Success rate: Empirical success rate from historical data
        4. Expected improvement: Target metrics based on template
        5. Champion reference: If applicable, reference to champion strategy

    Example:
        >>> generator = RationaleGenerator()
        >>> rationale = generator.generate_performance_rationale(
        ...     template_name='TurtleTemplate',
        ...     sharpe=0.8,
        ...     success_rate=0.80,
        ...     expected_sharpe_range=(1.5, 2.5)
        ... )
        >>> print(rationale)
        Sharpe 0.80 in Archive tier (0.5-1.0): TurtleTemplate proven 80% success rate...

    Attributes:
        template_descriptions: Mapping of template names to architecture descriptions
        performance_tiers: Sharpe ratio tier definitions
    """

    # Template architecture descriptions
    TEMPLATE_DESCRIPTIONS = {
        'TurtleTemplate': {
            'architecture': '6-layer AND filtering with revenue growth + price strength',
            'selection': '.is_largest() for momentum weighting',
            'characteristics': 'Robust multi-factor strategy',
            'expected_sharpe': (1.5, 2.5),
            'risk_profile': 'Medium risk, high consistency'
        },
        'MastiffTemplate': {
            'architecture': '6 contrarian conditions with volume analysis',
            'selection': '.is_smallest() for contrarian selection',
            'characteristics': 'High-conviction concentrated positions',
            'expected_sharpe': (1.2, 2.0),
            'risk_profile': 'High risk, high reward'
        },
        'FactorTemplate': {
            'architecture': 'Single-factor cross-sectional ranking',
            'selection': '.rank() for relative strength',
            'characteristics': 'Simple, stable, low-volatility',
            'expected_sharpe': (0.8, 1.3),
            'risk_profile': 'Low risk, stable returns'
        },
        'MomentumTemplate': {
            'architecture': 'Momentum + catalyst combination',
            'selection': '.is_largest() for momentum focus',
            'characteristics': 'Fast iteration, rapid feedback',
            'expected_sharpe': (0.8, 1.5),
            'risk_profile': 'Medium risk, fast learning'
        }
    }

    # Performance tier definitions
    PERFORMANCE_TIERS = {
        'champion': {'min_sharpe': 2.0, 'label': 'Champion tier'},
        'contender': {'min_sharpe': 1.5, 'label': 'Contender tier'},
        'solid': {'min_sharpe': 1.0, 'label': 'Solid performance'},
        'archive': {'min_sharpe': 0.5, 'label': 'Archive tier'},
        'poor': {'min_sharpe': 0.0, 'label': 'Poor performance'}
    }

    def __init__(self):
        """Initialize rationale generator."""
        pass

    def generate_performance_rationale(
        self,
        template_name: str,
        sharpe: float,
        success_rate: float,
        expected_sharpe_range: Optional[tuple] = None,
        drawdown: Optional[float] = None
    ) -> str:
        """
        Generate performance-based rationale.

        Args:
            template_name: Recommended template name
            sharpe: Current Sharpe ratio
            success_rate: Template success rate (0.0-1.0)
            expected_sharpe_range: Expected Sharpe range (min, max)
            drawdown: Optional maximum drawdown

        Returns:
            Natural language rationale string

        Example:
            >>> rationale = generator.generate_performance_rationale(
            ...     template_name='TurtleTemplate',
            ...     sharpe=0.8,
            ...     success_rate=0.80
            ... )
        """
        # Determine performance tier
        tier = self._get_performance_tier(sharpe)
        tier_label = tier['label']

        # Get template info
        template_info = self.TEMPLATE_DESCRIPTIONS.get(template_name, {})
        architecture = template_info.get('architecture', 'Unknown architecture')
        characteristics = template_info.get('characteristics', 'Strategy characteristics')

        if not expected_sharpe_range:
            expected_sharpe_range = template_info.get('expected_sharpe', (1.0, 2.0))

        # Build rationale components
        components = []

        # 1. Performance tier and current metrics
        if sharpe >= 2.0:
            components.append(
                f"High Sharpe {sharpe:.2f} ({tier_label}): Performance already strong. "
                f"{template_name} maintains robust architecture with proven success."
            )
        elif sharpe >= 1.5:
            components.append(
                f"Sharpe {sharpe:.2f} ({tier_label}): {template_name} provides "
                f"robustness for strategies approaching champion performance."
            )
        elif sharpe >= 1.0:
            if drawdown and drawdown <= 0.10:
                components.append(
                    f"Sharpe {sharpe:.2f} with low drawdown {drawdown:.1%} ({tier_label}): "
                    f"{template_name} provides stable returns."
                )
            else:
                components.append(
                    f"Sharpe {sharpe:.2f} ({tier_label}): {template_name} "
                    f"provides risk management through comprehensive filtering."
                )
        elif sharpe >= 0.5:
            components.append(
                f"Sharpe {sharpe:.2f} in target range 0.5-1.0 ({tier_label}): "
                f"{template_name} proven {success_rate:.0%} success rate."
            )
        else:
            components.append(
                f"Low Sharpe {sharpe:.2f} ({tier_label}): {template_name} "
                f"for rapid iteration and testing to identify viable patterns."
            )

        # 2. Template architecture
        components.append(f"{architecture}.")

        # 3. Template characteristics and expected performance
        components.append(
            f"{characteristics}. "
            f"Expected Sharpe range: {expected_sharpe_range[0]:.1f}-{expected_sharpe_range[1]:.1f}."
        )

        # 4. Success rate
        components.append(f"Success rate: {success_rate:.0%}.")

        return ' '.join(components)

    def generate_exploration_rationale(
        self,
        template_name: str,
        iteration: int,
        recent_templates: List[str],
        success_rate: float
    ) -> str:
        """
        Generate exploration mode rationale.

        Args:
            template_name: Recommended template for exploration
            iteration: Current iteration number
            recent_templates: Recently used templates
            success_rate: Template success rate

        Returns:
            Natural language rationale string

        Example:
            >>> rationale = generator.generate_exploration_rationale(
            ...     template_name='MastiffTemplate',
            ...     iteration=10,
            ...     recent_templates=['TurtleTemplate', 'TurtleTemplate', 'FactorTemplate'],
            ...     success_rate=0.65
            ... )
        """
        template_info = self.TEMPLATE_DESCRIPTIONS.get(template_name, {})
        architecture = template_info.get('architecture', 'Unknown architecture')

        rationale_parts = [
            f"⚡ EXPLORATION MODE (iteration {iteration}):",
            f"Testing {template_name} for template diversity.",
            f"{architecture}.",
            f"Avoiding recently used templates: {recent_templates}.",
            f"Using expanded parameter ranges (±30%) for broader exploration.",
            f"Success rate: {success_rate:.0%}."
        ]

        return ' '.join(rationale_parts)

    def generate_champion_rationale(
        self,
        template_name: str,
        champion_id: str,
        champion_sharpe: float,
        champion_params: Dict[str, Any]
    ) -> str:
        """
        Generate champion-based rationale.

        Args:
            template_name: Champion template name
            champion_id: Champion genome ID
            champion_sharpe: Champion Sharpe ratio
            champion_params: Champion parameters

        Returns:
            Natural language rationale string

        Example:
            >>> rationale = generator.generate_champion_rationale(
            ...     template_name='TurtleTemplate',
            ...     champion_id='genome_42',
            ...     champion_sharpe=2.3,
            ...     champion_params={'n_stocks': 10, 'ma_short': 20}
            ... )
        """
        # Format parameters
        param_summary = ', '.join([
            f"{k}={v}" for k, v in champion_params.items()
            if not k.startswith('champion_')
        ])

        rationale_parts = [
            f"Based on champion {champion_id} (Sharpe {champion_sharpe:.2f}).",
            f"Parameters: {param_summary}.",
            f"Champion proven in {template_name} template.",
            f"Variation range ±20% for exploration around proven configuration."
        ]

        return ' '.join(rationale_parts)

    def generate_validation_rationale(
        self,
        template_name: str,
        num_param_errors: int = 0,
        num_complexity_errors: int = 0,
        num_data_errors: int = 0,
        simplified_from: Optional[str] = None
    ) -> str:
        """
        Generate validation feedback rationale.

        Args:
            template_name: Recommended template after validation
            num_param_errors: Number of parameter errors
            num_complexity_errors: Number of complexity errors
            num_data_errors: Number of data errors
            simplified_from: Original template if simplified

        Returns:
            Natural language rationale string

        Example:
            >>> rationale = generator.generate_validation_rationale(
            ...     template_name='FactorTemplate',
            ...     num_complexity_errors=2,
            ...     simplified_from='TurtleTemplate'
            ... )
        """
        rationale_parts = []

        if simplified_from:
            rationale_parts.append(
                f"Validation feedback: Architecture complexity errors detected. "
                f"Recommending {template_name} (simpler architecture) "
                f"to avoid complexity issues. Original: {simplified_from}."
            )
        else:
            rationale_parts.append(f"Validation feedback incorporated:")

            if num_param_errors > 0:
                rationale_parts.append(
                    f"{num_param_errors} parameter issues resolved through adjustment."
                )

            if num_complexity_errors > 0:
                rationale_parts.append(
                    f"{num_complexity_errors} complexity issues addressed."
                )

            if num_data_errors > 0:
                rationale_parts.append(
                    f"{num_data_errors} data access issues - "
                    f"suggest using common datasets (revenue, price, volume)."
                )

        return ' '.join(rationale_parts)

    def generate_risk_profile_rationale(
        self,
        template_name: str,
        risk_profile: str,
        success_rate: float
    ) -> str:
        """
        Generate risk profile-based rationale.

        Args:
            template_name: Recommended template
            risk_profile: Risk profile ('concentrated', 'stable', 'fast')
            success_rate: Template success rate

        Returns:
            Natural language rationale string

        Example:
            >>> rationale = generator.generate_risk_profile_rationale(
            ...     template_name='MastiffTemplate',
            ...     risk_profile='concentrated',
            ...     success_rate=0.65
            ... )
        """
        template_info = self.TEMPLATE_DESCRIPTIONS.get(template_name, {})
        architecture = template_info.get('architecture', 'Unknown architecture')
        selection = template_info.get('selection', 'Unknown selection')
        risk_desc = template_info.get('risk_profile', 'Unknown risk profile')

        rationale_map = {
            'concentrated': (
                f"Concentrated risk profile: {template_name} uses {architecture} "
                f"with {selection} for high-conviction concentrated positions. "
                f"Success rate: {success_rate:.0%}. "
                f"Best for investors with high risk tolerance and conviction."
            ),
            'stable': (
                f"Stability priority: {template_name} uses {architecture} "
                f"with {selection} for stable, low-volatility returns. "
                f"Success rate: {success_rate:.0%}. "
                f"Best for conservative investors prioritizing consistency."
            ),
            'fast': (
                f"Fast iteration mode: {template_name} uses {architecture} "
                f"for rapid testing and quick feedback cycles. "
                f"Success rate: {success_rate:.0%}. "
                f"Best for quick strategy exploration."
            )
        }

        return rationale_map.get(risk_profile, f"{template_name} recommended. {risk_desc}.")

    def _get_performance_tier(self, sharpe: float) -> Dict[str, Any]:
        """
        Get performance tier based on Sharpe ratio.

        Args:
            sharpe: Sharpe ratio

        Returns:
            Dictionary with tier info
        """
        if sharpe >= self.PERFORMANCE_TIERS['champion']['min_sharpe']:
            return self.PERFORMANCE_TIERS['champion']
        elif sharpe >= self.PERFORMANCE_TIERS['contender']['min_sharpe']:
            return self.PERFORMANCE_TIERS['contender']
        elif sharpe >= self.PERFORMANCE_TIERS['solid']['min_sharpe']:
            return self.PERFORMANCE_TIERS['solid']
        elif sharpe >= self.PERFORMANCE_TIERS['archive']['min_sharpe']:
            return self.PERFORMANCE_TIERS['archive']
        else:
            return self.PERFORMANCE_TIERS['poor']
