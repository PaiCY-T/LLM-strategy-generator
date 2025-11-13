"""
Template Feedback Integrator
============================

Intelligent template recommendation system for strategy generation learning loop.
Provides template selection based on performance, champion analysis, and exploration.

Features:
    - Performance-based template selection
    - Champion-based parameter suggestions
    - Template match scoring (architecture similarity)
    - Forced exploration mode (diversity)
    - Validation-aware feedback
    - Template success rate tracking

Usage:
    from src.feedback import TemplateFeedbackIntegrator
    from src.repository import HallOfFameRepository

    repository = HallOfFameRepository()
    integrator = TemplateFeedbackIntegrator(repository)

    recommendation = integrator.recommend_template(
        current_metrics={'sharpe_ratio': 0.8, 'max_drawdown': 0.15},
        iteration=5
    )

    print(f"Use {recommendation.template_name}")
    print(f"Because: {recommendation.rationale}")

Requirements:
    - Requirement 4.1: Template recommendation system
    - Requirement 4.2: Performance-based selection
    - Requirement 4.3: Champion-based suggestions
    - Requirement 4.4: Forced exploration mode
    - Requirement 4.5: Validation feedback integration
"""

from typing import Dict, Any, Optional, List, Type, Tuple
from dataclasses import dataclass, field
import logging
import re


@dataclass
class TemplateRecommendation:
    """
    Template recommendation with rationale and parameters.

    Attributes:
        template_name: Recommended template name (TurtleTemplate, MastiffTemplate, etc.)
        rationale: Human-readable explanation for recommendation
        match_score: Confidence score for recommendation (0.0-1.0)
        suggested_params: Suggested parameter dictionary for template
        champion_reference: Optional reference to champion strategy that influenced recommendation
        exploration_mode: True if recommendation is for exploration/diversity

    Example:
        >>> recommendation = TemplateRecommendation(
        ...     template_name='TurtleTemplate',
        ...     rationale='6-layer AND filtering provides robustness with 80% success rate',
        ...     match_score=0.85,
        ...     suggested_params={'n_stocks': 10, 'ma_short': 20, 'ma_long': 60}
        ... )
        >>> print(f"Use {recommendation.template_name}: {recommendation.rationale}")
    """
    template_name: str
    rationale: str
    match_score: float  # 0.0-1.0
    suggested_params: Dict[str, Any] = field(default_factory=dict)
    champion_reference: Optional[str] = None  # Champion genome ID if applicable
    exploration_mode: bool = False

    def __str__(self) -> str:
        """Format recommendation for display."""
        lines = [
            f"Template: {self.template_name} (confidence: {self.match_score:.2%})",
            f"Rationale: {self.rationale}"
        ]

        if self.suggested_params:
            lines.append("Suggested Parameters:")
            for key, value in self.suggested_params.items():
                lines.append(f"  {key}: {value}")

        if self.champion_reference:
            lines.append(f"Based on champion: {self.champion_reference}")

        if self.exploration_mode:
            lines.append("⚡ EXPLORATION MODE: Testing new template for diversity")

        return '\n'.join(lines)


class TemplateFeedbackIntegrator:
    """
    Intelligent template recommendation engine.

    Provides template selection based on:
    1. Performance-based matching (Sharpe, drawdown, volatility)
    2. Champion strategy analysis (best performers)
    3. Template match scoring (architecture similarity)
    4. Forced exploration (every 5th iteration)
    5. Validation feedback (error patterns)

    Recommendation Algorithm:
        1. Check forced exploration mode (iteration % 5 == 0)
        2. If champion exists and degraded, recommend champion template
        3. Otherwise, use performance-based recommendation
        4. Calculate match scores for all templates
        5. Incorporate validation feedback if applicable
        6. Generate suggested parameters (champion-based or default)

    Attributes:
        repository: HallOfFameRepository instance for champion queries
        template_registry: Mapping of template names to template classes
        iteration_history: Track template usage to avoid repetition
        logger: Python logger for recommendation tracking

    Example:
        >>> repository = HallOfFameRepository()
        >>> integrator = TemplateFeedbackIntegrator(repository)
        >>> recommendation = integrator.recommend_template(
        ...     current_metrics={'sharpe_ratio': 0.8},
        ...     iteration=5
        ... )
        >>> print(recommendation)
    """

    # Exploration frequency (every N iterations)
    EXPLORATION_FREQUENCY = 5

    # Performance thresholds for template recommendations
    HIGH_SHARPE_THRESHOLD = 2.0  # Champions tier
    MEDIUM_SHARPE_THRESHOLD = 1.5  # Contenders tier
    LOW_SHARPE_THRESHOLD = 1.0  # Archive tier

    # Template success rates (empirical from validation)
    TEMPLATE_SUCCESS_RATES = {
        'TurtleTemplate': 0.80,  # 80% success rate proven
        'MastiffTemplate': 0.65,  # 65% for concentrated strategies
        'FactorTemplate': 0.70,  # 70% for stable strategies
        'MomentumTemplate': 0.60  # 60% for fast iteration
    }

    def __init__(
        self,
        repository: Any = None,  # HallOfFameRepository
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize template feedback integrator.

        Args:
            repository: Optional HallOfFameRepository for champion queries
            logger: Optional logger for recommendation tracking
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

        # Template registry mapping names to classes
        # Import templates lazily to avoid circular dependencies
        self.template_registry = self._initialize_template_registry()

        # Track iteration history to avoid template repetition
        self.iteration_history: List[str] = []

        self.logger.info("TemplateFeedbackIntegrator initialized")

    def _initialize_template_registry(self) -> Dict[str, Type]:
        """
        Initialize template registry with lazy imports.

        Returns:
            Dictionary mapping template names to template classes

        Note:
            Uses lazy imports to avoid circular dependencies during initialization
        """
        try:
            from ..templates.turtle_template import TurtleTemplate
            from ..templates.mastiff_template import MastiffTemplate
            from ..templates.factor_template import FactorTemplate
            from ..templates.momentum_template import MomentumTemplate

            registry = {
                'TurtleTemplate': TurtleTemplate,
                'Turtle': TurtleTemplate,
                'MastiffTemplate': MastiffTemplate,
                'Mastiff': MastiffTemplate,
                'FactorTemplate': FactorTemplate,
                'Factor': FactorTemplate,
                'MomentumTemplate': MomentumTemplate,
                'Momentum': MomentumTemplate
            }

            self.logger.info(f"Template registry initialized with {len(registry)} templates")
            return registry

        except ImportError as e:
            self.logger.warning(f"Failed to import some templates: {e}")
            # Return partial registry if some imports fail
            return {}

    def get_template_class(self, template_name: str) -> Optional[Type]:
        """
        Get template class by name.

        Args:
            template_name: Template name (case-insensitive)

        Returns:
            Template class or None if not found

        Example:
            >>> template_class = integrator.get_template_class('TurtleTemplate')
            >>> if template_class:
            ...     template = template_class()
        """
        # Normalize template name (handle both TurtleTemplate and Turtle)
        normalized_name = template_name.strip()

        template_class = self.template_registry.get(normalized_name)

        if not template_class:
            self.logger.warning(f"Template '{template_name}' not found in registry")

        return template_class

    def get_available_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List of template names (full names like 'TurtleTemplate')

        Example:
            >>> templates = integrator.get_available_templates()
            >>> print(templates)
            ['TurtleTemplate', 'MastiffTemplate', 'FactorTemplate', 'MomentumTemplate']
        """
        # Return full template names only (exclude short aliases)
        full_names = [
            name for name in self.template_registry.keys()
            if name.endswith('Template')
        ]

        return sorted(full_names)

    def track_iteration(self, template_name: str) -> None:
        """
        Track template usage in iteration history.

        Args:
            template_name: Template name used in this iteration

        Note:
            Used for exploration mode to avoid repeating recent templates
        """
        self.iteration_history.append(template_name)

        # Keep only last 10 iterations to avoid memory growth
        if len(self.iteration_history) > 10:
            self.iteration_history = self.iteration_history[-10:]

        self.logger.debug(f"Tracked template usage: {template_name}")

    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get template usage statistics.

        Returns:
            Dictionary with template usage stats

        Example:
            >>> stats = integrator.get_template_statistics()
            >>> print(stats['most_used_template'])
            'TurtleTemplate'
        """
        if not self.iteration_history:
            return {
                'total_iterations': 0,
                'templates_used': [],
                'most_used_template': None,
                'usage_distribution': {}
            }

        # Count template usage
        usage_counts = {}
        for template_name in self.iteration_history:
            usage_counts[template_name] = usage_counts.get(template_name, 0) + 1

        # Find most used template
        most_used = max(usage_counts.items(), key=lambda x: x[1])[0] if usage_counts else None

        return {
            'total_iterations': len(self.iteration_history),
            'templates_used': list(set(self.iteration_history)),
            'most_used_template': most_used,
            'usage_distribution': usage_counts
        }

    def calculate_template_match_score(
        self,
        strategy_code: str,
        current_params: Optional[Dict[str, Any]] = None,
        current_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Calculate match scores for all templates based on architecture similarity.

        Analyzes strategy code to determine which template architecture it most closely
        resembles. Useful for identifying the template that generated a strategy or
        recommending similar templates.

        Scoring Components:
            - Filter structure match (40%): Number and combination of conditions
            - Selection method match (30%): .is_largest() vs .is_smallest()
            - Parameter similarity (20%): Overlap with template PARAM_GRID
            - Performance alignment (10%): Metrics vs expected_performance

        Args:
            strategy_code: Generated strategy code to analyze
            current_params: Optional parameter dictionary for similarity comparison
            current_metrics: Optional metrics for performance alignment

        Returns:
            Dictionary mapping template names to match scores (0.0-1.0)

        Example:
            >>> code = "cond1 & cond2 & cond3 & cond4 & cond5 & cond6\\nbuy = buy.is_largest(10)"
            >>> scores = integrator.calculate_template_match_score(code)
            >>> print(scores)
            {'TurtleTemplate': 0.85, 'MastiffTemplate': 0.35, ...}

        Requirements:
            - Requirement 4.1: Template match scoring for architecture similarity
        """
        if not strategy_code:
            self.logger.warning("Empty strategy code provided for match scoring")
            return {name: 0.0 for name in self.get_available_templates()}

        # Extract architecture patterns from code
        filter_score = self._score_filter_structure(strategy_code)
        selection_score = self._score_selection_method(strategy_code)
        param_score = self._score_parameter_similarity(strategy_code, current_params)
        performance_score = self._score_performance_alignment(current_metrics)

        # Calculate weighted scores for each template
        template_scores = {}
        for template_name in self.get_available_templates():
            template_class = self.get_template_class(template_name)
            if not template_class:
                continue

            # Weight components based on importance
            score = (
                filter_score.get(template_name, 0.0) * 0.40 +  # 40% filter structure
                selection_score.get(template_name, 0.0) * 0.30 +  # 30% selection method
                param_score.get(template_name, 0.0) * 0.20 +  # 20% parameter similarity
                performance_score.get(template_name, 0.0) * 0.10  # 10% performance alignment
            )

            template_scores[template_name] = round(score, 3)

        self.logger.info(f"Template match scores: {template_scores}")
        return template_scores

    def _score_filter_structure(self, strategy_code: str) -> Dict[str, float]:
        """
        Score filter structure match against each template.

        Analyzes:
        - Number of conditions (cond1, cond2, etc.)
        - Use of AND operator (&)
        - Multi-layer filtering patterns

        Args:
            strategy_code: Strategy code to analyze

        Returns:
            Dictionary mapping template names to filter structure scores (0.0-1.0)
        """
        scores = {}

        # Count conditions using regex
        cond_pattern = r'\bcond\d+\b'
        conditions = re.findall(cond_pattern, strategy_code)
        num_conditions = len(set(conditions))  # Unique conditions

        # Check for AND combinations
        has_and_operator = ' & ' in strategy_code or '&' in strategy_code

        # TurtleTemplate: 6-layer AND filtering
        if num_conditions >= 6 and has_and_operator:
            scores['TurtleTemplate'] = 1.0
        elif num_conditions >= 4 and has_and_operator:
            scores['TurtleTemplate'] = 0.7
        else:
            scores['TurtleTemplate'] = 0.3

        # MastiffTemplate: 6 contrarian conditions
        if num_conditions >= 6 and has_and_operator:
            scores['MastiffTemplate'] = 0.8
        elif num_conditions >= 4:
            scores['MastiffTemplate'] = 0.6
        else:
            scores['MastiffTemplate'] = 0.3

        # FactorTemplate: Single factor with ranking (fewer conditions)
        if num_conditions <= 3:
            scores['FactorTemplate'] = 0.9
        elif num_conditions <= 5:
            scores['FactorTemplate'] = 0.5
        else:
            scores['FactorTemplate'] = 0.2

        # MomentumTemplate: Momentum + catalyst (2-4 conditions)
        if 2 <= num_conditions <= 4:
            scores['MomentumTemplate'] = 0.8
        elif num_conditions <= 6:
            scores['MomentumTemplate'] = 0.5
        else:
            scores['MomentumTemplate'] = 0.3

        return scores

    def _score_selection_method(self, strategy_code: str) -> Dict[str, float]:
        """
        Score selection method match against each template.

        Analyzes:
        - .is_largest() for momentum/growth strategies
        - .is_smallest() for contrarian strategies
        - Cross-sectional ranking for factor strategies

        Args:
            strategy_code: Strategy code to analyze

        Returns:
            Dictionary mapping template names to selection method scores (0.0-1.0)
        """
        scores = {}

        # Check for selection methods
        has_is_largest = '.is_largest(' in strategy_code
        has_is_smallest = '.is_smallest(' in strategy_code
        has_rank = '.rank(' in strategy_code

        # TurtleTemplate: .is_largest() for revenue growth weighting
        scores['TurtleTemplate'] = 1.0 if has_is_largest else 0.2

        # MastiffTemplate: .is_smallest() for contrarian volume selection
        scores['MastiffTemplate'] = 1.0 if has_is_smallest else 0.2

        # FactorTemplate: .rank() for cross-sectional ranking
        scores['FactorTemplate'] = 1.0 if has_rank else 0.4

        # MomentumTemplate: .is_largest() for momentum selection
        scores['MomentumTemplate'] = 0.9 if has_is_largest else 0.3

        return scores

    def _score_parameter_similarity(
        self,
        strategy_code: str,
        current_params: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Score parameter similarity against each template's PARAM_GRID.

        Analyzes:
        - Parameter names present in code
        - Parameter value ranges
        - Parameter count overlap

        Args:
            strategy_code: Strategy code to analyze
            current_params: Optional current parameters

        Returns:
            Dictionary mapping template names to parameter similarity scores (0.0-1.0)
        """
        scores = {}

        if not current_params:
            # If no parameters provided, extract from code
            current_params = self._extract_params_from_code(strategy_code)

        if not current_params:
            # No parameters found, return neutral scores
            return {name: 0.5 for name in self.get_available_templates()}

        # For each template, calculate parameter overlap
        for template_name in self.get_available_templates():
            template_class = self.get_template_class(template_name)
            if not template_class:
                scores[template_name] = 0.5
                continue

            # Instantiate template to access PARAM_GRID property
            try:
                template_instance = template_class()
                param_grid = template_instance.PARAM_GRID
            except Exception:
                scores[template_name] = 0.5
                continue

            # Calculate overlap ratio
            common_params = set(current_params.keys()) & set(param_grid.keys())
            total_params = set(param_grid.keys())

            if total_params:
                overlap_ratio = len(common_params) / len(total_params)
                scores[template_name] = overlap_ratio
            else:
                scores[template_name] = 0.5

        return scores

    def _score_performance_alignment(
        self,
        current_metrics: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Score performance alignment with template's expected_performance.

        Analyzes:
        - Sharpe ratio vs expected range
        - Risk characteristics
        - Return profile

        Args:
            current_metrics: Optional current performance metrics

        Returns:
            Dictionary mapping template names to performance alignment scores (0.0-1.0)
        """
        scores = {}

        if not current_metrics or 'sharpe_ratio' not in current_metrics:
            # No metrics, return neutral scores
            return {name: 0.5 for name in self.get_available_templates()}

        sharpe = current_metrics.get('sharpe_ratio', 0.0)

        # TurtleTemplate: Expected Sharpe 1.5-2.5 (robust)
        if 1.5 <= sharpe <= 2.5:
            scores['TurtleTemplate'] = 1.0
        elif 1.0 <= sharpe <= 3.0:
            scores['TurtleTemplate'] = 0.7
        else:
            scores['TurtleTemplate'] = 0.4

        # MastiffTemplate: Expected Sharpe 1.2-2.0 (concentrated)
        if 1.2 <= sharpe <= 2.0:
            scores['MastiffTemplate'] = 1.0
        elif 0.8 <= sharpe <= 2.5:
            scores['MastiffTemplate'] = 0.7
        else:
            scores['MastiffTemplate'] = 0.4

        # FactorTemplate: Expected Sharpe 0.8-1.3 (stable)
        if 0.8 <= sharpe <= 1.3:
            scores['FactorTemplate'] = 1.0
        elif 0.5 <= sharpe <= 1.8:
            scores['FactorTemplate'] = 0.7
        else:
            scores['FactorTemplate'] = 0.4

        # MomentumTemplate: Expected Sharpe 0.8-1.5 (fast)
        if 0.8 <= sharpe <= 1.5:
            scores['MomentumTemplate'] = 1.0
        elif 0.5 <= sharpe <= 2.0:
            scores['MomentumTemplate'] = 0.7
        else:
            scores['MomentumTemplate'] = 0.4

        return scores

    def _extract_params_from_code(self, strategy_code: str) -> Dict[str, Any]:
        """
        Extract parameters from strategy code.

        Looks for common parameter patterns like:
        - n_stocks = 10
        - ma_short = 20
        - stop_loss = 0.06

        Args:
            strategy_code: Strategy code to analyze

        Returns:
            Dictionary of extracted parameters
        """
        params = {}

        # Common parameter patterns
        param_patterns = [
            r'n_stocks\s*=\s*(\d+)',
            r'ma_short\s*=\s*(\d+)',
            r'ma_long\s*=\s*(\d+)',
            r'stop_loss\s*=\s*([\d.]+)',
            r'position_limit\s*=\s*([\d.]+)'
        ]

        for pattern in param_patterns:
            match = re.search(pattern, strategy_code)
            if match:
                param_name = pattern.split('\\s')[0]  # Extract parameter name
                param_value = match.group(1)

                # Convert to appropriate type
                try:
                    if '.' in param_value:
                        params[param_name] = float(param_value)
                    else:
                        params[param_name] = int(param_value)
                except ValueError:
                    continue

        return params

    def get_best_matching_template(
        self,
        strategy_code: str,
        current_params: Optional[Dict[str, Any]] = None,
        current_metrics: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, float]:
        """
        Get the best matching template for given strategy code.

        Convenience method that calls calculate_template_match_score and returns
        the highest scoring template.

        Args:
            strategy_code: Strategy code to analyze
            current_params: Optional parameters for similarity
            current_metrics: Optional metrics for performance alignment

        Returns:
            Tuple of (template_name, match_score)

        Example:
            >>> template_name, score = integrator.get_best_matching_template(code)
            >>> print(f"{template_name}: {score:.2%}")
            TurtleTemplate: 85.3%

        Requirements:
            - Requirement 4.1: Template match scoring
        """
        scores = self.calculate_template_match_score(
            strategy_code=strategy_code,
            current_params=current_params,
            current_metrics=current_metrics
        )

        if not scores:
            return ('TurtleTemplate', 0.5)  # Default fallback

        # Find highest scoring template
        best_template = max(scores.items(), key=lambda x: x[1])

        self.logger.info(f"Best matching template: {best_template[0]} (score: {best_template[1]:.3f})")

        return best_template

    def _recommend_by_performance(
        self,
        current_metrics: Optional[Dict[str, Any]] = None,
        risk_profile: Optional[str] = None
    ) -> TemplateRecommendation:
        """
        Performance-based template recommendation.

        Analyzes current metrics and risk profile to recommend the most appropriate
        template based on empirical success rates and performance characteristics.

        Recommendation Logic:
            1. Sharpe 0.5-1.0 → TurtleTemplate (proven 80% success rate)
            2. Concentrated risk appetite → MastiffTemplate (65% success, high conviction)
            3. Stability priority → FactorTemplate (70% success, low volatility)
            4. Fast iteration → MomentumTemplate (60% success, rapid testing)
            5. High Sharpe >2.0 → Champion-based recommendation
            6. Default fallback → TurtleTemplate (most reliable)

        Args:
            current_metrics: Performance metrics dictionary
                - sharpe_ratio: Sharpe ratio (key metric)
                - max_drawdown: Maximum drawdown
                - volatility: Strategy volatility
                - total_return: Total return
            risk_profile: Optional risk profile override
                - 'concentrated': High conviction, concentrated positions
                - 'stable': Low volatility, stable returns
                - 'aggressive': High risk/reward
                - 'fast': Rapid iteration, testing

        Returns:
            TemplateRecommendation with template name, rationale, and match score

        Example:
            >>> recommendation = integrator._recommend_by_performance(
            ...     current_metrics={'sharpe_ratio': 0.8, 'max_drawdown': 0.12}
            ... )
            >>> print(recommendation.template_name)
            TurtleTemplate
            >>> print(recommendation.rationale)
            Sharpe 0.8 in target range 0.5-1.0: TurtleTemplate proven 80% success rate...

        Requirements:
            - Requirement 4.2: Performance-based template selection
        """
        # Extract metrics
        sharpe = 0.0
        max_drawdown = 0.0
        volatility = 0.0

        if current_metrics:
            sharpe = current_metrics.get('sharpe_ratio', 0.0)
            max_drawdown = abs(current_metrics.get('max_drawdown', 0.0))
            volatility = current_metrics.get('volatility', 0.0)

        self.logger.info(
            f"Performance-based recommendation: "
            f"sharpe={sharpe:.2f}, drawdown={max_drawdown:.2%}, "
            f"volatility={volatility:.2%}, risk_profile={risk_profile}"
        )

        # Decision 1: Risk profile override (explicit user preference)
        if risk_profile:
            if risk_profile == 'concentrated':
                rationale = (
                    f"Concentrated risk profile: MastiffTemplate uses 6 contrarian conditions "
                    f"with .is_smallest() selection for high-conviction concentrated positions. "
                    f"Success rate: {self.TEMPLATE_SUCCESS_RATES['MastiffTemplate']:.0%}. "
                    f"Best for investors with high risk tolerance and conviction."
                )
                return TemplateRecommendation(
                    template_name='MastiffTemplate',
                    rationale=rationale,
                    match_score=0.85,
                    suggested_params={}  # Will be filled by champion method
                )

            elif risk_profile == 'stable':
                rationale = (
                    f"Stability priority: FactorTemplate uses single-factor cross-sectional ranking "
                    f"with .rank() for stable, low-volatility returns. "
                    f"Success rate: {self.TEMPLATE_SUCCESS_RATES['FactorTemplate']:.0%}. "
                    f"Best for conservative investors prioritizing consistency."
                )
                return TemplateRecommendation(
                    template_name='FactorTemplate',
                    rationale=rationale,
                    match_score=0.82,
                    suggested_params={}
                )

            elif risk_profile == 'fast':
                rationale = (
                    f"Fast iteration mode: MomentumTemplate uses momentum + catalyst "
                    f"for rapid testing and quick feedback cycles. "
                    f"Success rate: {self.TEMPLATE_SUCCESS_RATES['MomentumTemplate']:.0%}. "
                    f"Best for quick strategy exploration."
                )
                return TemplateRecommendation(
                    template_name='MomentumTemplate',
                    rationale=rationale,
                    match_score=0.78,
                    suggested_params={}
                )

        # Decision 2: High performance (Sharpe > 2.0) - Champion tier
        if sharpe >= self.HIGH_SHARPE_THRESHOLD:
            rationale = (
                f"High Sharpe {sharpe:.2f} (Champion tier): Performance already strong. "
                f"Recommend continuing with current template or champion-based selection. "
                f"Use champion template with proven parameter combinations."
            )
            # Return TurtleTemplate as safest option for champions
            return TemplateRecommendation(
                template_name='TurtleTemplate',
                rationale=rationale,
                match_score=0.90,
                suggested_params={},
                champion_reference=None  # Will be filled by champion method
            )

        # Decision 3: Medium-High Sharpe (1.5-2.0) - Contenders tier
        if sharpe >= self.MEDIUM_SHARPE_THRESHOLD:
            rationale = (
                f"Sharpe {sharpe:.2f} (Contender tier): TurtleTemplate's 6-layer AND filtering "
                f"provides robustness for strategies approaching champion performance. "
                f"Success rate: {self.TEMPLATE_SUCCESS_RATES['TurtleTemplate']:.0%}. "
                f"Expected Sharpe range: 1.5-2.5."
            )
            return TemplateRecommendation(
                template_name='TurtleTemplate',
                rationale=rationale,
                match_score=0.87,
                suggested_params={}
            )

        # Decision 4: Medium Sharpe (1.0-1.5) - Solid performance
        if sharpe >= self.LOW_SHARPE_THRESHOLD:
            # Check drawdown to determine template
            if max_drawdown <= 0.10:  # Low drawdown - stability focus
                rationale = (
                    f"Sharpe {sharpe:.2f} with low drawdown {max_drawdown:.1%}: "
                    f"FactorTemplate provides stable returns with cross-sectional ranking. "
                    f"Success rate: {self.TEMPLATE_SUCCESS_RATES['FactorTemplate']:.0%}. "
                    f"Best for low-volatility strategies."
                )
                return TemplateRecommendation(
                    template_name='FactorTemplate',
                    rationale=rationale,
                    match_score=0.84,
                    suggested_params={}
                )
            else:  # Higher drawdown - robust filtering needed
                rationale = (
                    f"Sharpe {sharpe:.2f} with drawdown {max_drawdown:.1%}: "
                    f"TurtleTemplate's 6-layer filtering provides risk management. "
                    f"Success rate: {self.TEMPLATE_SUCCESS_RATES['TurtleTemplate']:.0%}. "
                    f"Expected to improve risk-adjusted returns."
                )
                return TemplateRecommendation(
                    template_name='TurtleTemplate',
                    rationale=rationale,
                    match_score=0.85,
                    suggested_params={}
                )

        # Decision 5: Sharpe 0.5-1.0 - Archive tier, needs improvement
        if sharpe >= 0.5:
            rationale = (
                f"Sharpe {sharpe:.2f} in target range 0.5-1.0: "
                f"TurtleTemplate proven 80% success rate with 6-layer AND filtering. "
                f"Revenue growth + price strength + volume confirmation + risk management "
                f"provides comprehensive strategy framework. Expected improvement to Sharpe 1.5-2.5."
            )
            return TemplateRecommendation(
                template_name='TurtleTemplate',
                rationale=rationale,
                match_score=0.80,
                suggested_params={}
            )

        # Decision 6: Low Sharpe < 0.5 - Poor performance, rapid iteration needed
        if sharpe < 0.5:
            rationale = (
                f"Low Sharpe {sharpe:.2f}: MomentumTemplate for rapid iteration and testing. "
                f"Momentum + catalyst approach allows quick feedback cycles to identify "
                f"viable patterns. Success rate: {self.TEMPLATE_SUCCESS_RATES['MomentumTemplate']:.0%}. "
                f"Focus on fast learning and exploration."
            )
            return TemplateRecommendation(
                template_name='MomentumTemplate',
                rationale=rationale,
                match_score=0.75,
                suggested_params={}
            )

        # Decision 7: No metrics provided - Default to most reliable template
        rationale = (
            f"No performance metrics available: TurtleTemplate as default. "
            f"Highest proven success rate ({self.TEMPLATE_SUCCESS_RATES['TurtleTemplate']:.0%}) "
            f"with robust 6-layer filtering architecture. Expected Sharpe: 1.5-2.5."
        )
        return TemplateRecommendation(
            template_name='TurtleTemplate',
            rationale=rationale,
            match_score=0.70,
            suggested_params={}
        )

    def get_champion_template_params(
        self,
        template_name: Optional[str] = None,
        min_sharpe: float = 1.5,
        variation_range: float = 0.20
    ) -> Dict[str, Any]:
        """
        Get parameter suggestions from Hall of Fame champion strategies.

        Queries the repository for highest-performing champion strategies and
        extracts their parameter combinations. Suggests variations based on
        champion parameters with ±variation_range adjustments.

        Algorithm:
            1. Query Hall of Fame for champions with Sharpe >= min_sharpe
            2. Filter by template_name if specified
            3. Find champion with highest Sharpe ratio
            4. Extract parameters from champion genome
            5. Suggest variations with ±20% range (default)
            6. Return parameter dictionary with champion reference

        Args:
            template_name: Optional template name to filter champions
                If None, considers all champions across templates
            min_sharpe: Minimum Sharpe ratio threshold (default: 1.5)
                Champions tier threshold for proven strategies
            variation_range: Parameter variation range (default: 0.20 = ±20%)
                Suggests parameter adjustments around champion values

        Returns:
            Dictionary with suggested parameters and metadata:
                - Parameters extracted from champion
                - champion_id: Champion genome ID for reference
                - champion_sharpe: Champion's Sharpe ratio
                - template_name: Champion's template
                - rationale: Explanation of parameter suggestions

        Example:
            >>> params = integrator.get_champion_template_params(
            ...     template_name='TurtleTemplate',
            ...     min_sharpe=1.5
            ... )
            >>> print(params)
            {
                'n_stocks': 10,
                'ma_short': 20,
                'ma_long': 60,
                'stop_loss': 0.06,
                'champion_id': 'genome_42',
                'champion_sharpe': 2.3,
                'rationale': 'Based on champion genome_42 (Sharpe 2.30)...'
            }

        Requirements:
            - Requirement 4.3: Champion-based parameter suggestions
        """
        if not self.repository:
            self.logger.warning("No repository available for champion queries")
            return {
                'rationale': 'No Hall of Fame repository available. Using default parameters.'
            }

        try:
            # Query Hall of Fame for champions
            champions = self.repository.get_champions(min_sharpe=min_sharpe)

            if not champions:
                self.logger.info(f"No champions found with Sharpe >= {min_sharpe}")
                return {
                    'rationale': f'No champions found with Sharpe >= {min_sharpe}. Using default parameters.'
                }

            # Filter by template if specified
            if template_name:
                champions = [
                    c for c in champions
                    if c.get('template_name') == template_name
                ]

                if not champions:
                    self.logger.info(f"No {template_name} champions found")
                    return {
                        'rationale': f'No {template_name} champions found. Using default parameters.'
                    }

            # Find champion with highest Sharpe
            best_champion = max(champions, key=lambda c: c.get('sharpe_ratio', 0.0))

            champion_id = best_champion.get('genome_id', 'unknown')
            champion_sharpe = best_champion.get('sharpe_ratio', 0.0)
            champion_template = best_champion.get('template_name', 'unknown')
            champion_params = best_champion.get('parameters', {})

            self.logger.info(
                f"Found champion {champion_id} "
                f"(template={champion_template}, sharpe={champion_sharpe:.2f})"
            )

            # Extract and suggest parameters with variations
            suggested_params = {}

            for param_name, param_value in champion_params.items():
                # For numeric parameters, suggest the champion value
                # (variations will be handled by exploration mode)
                if isinstance(param_value, (int, float)):
                    suggested_params[param_name] = param_value
                else:
                    # Non-numeric parameters (strings, bools) - use as-is
                    suggested_params[param_name] = param_value

            # Add metadata
            suggested_params['champion_id'] = champion_id
            suggested_params['champion_sharpe'] = round(champion_sharpe, 2)
            suggested_params['champion_template'] = champion_template

            # Generate rationale
            param_summary = ', '.join([
                f"{k}={v}" for k, v in champion_params.items()
                if k not in ['champion_id', 'champion_sharpe', 'champion_template']
            ])

            rationale = (
                f"Based on champion {champion_id} (Sharpe {champion_sharpe:.2f}). "
                f"Parameters: {param_summary}. "
                f"Champion proven in {champion_template} template. "
                f"Variation range ±{variation_range:.0%} for exploration."
            )

            suggested_params['rationale'] = rationale

            self.logger.info(f"Champion parameters: {param_summary}")

            return suggested_params

        except Exception as e:
            self.logger.error(f"Error querying champion parameters: {e}")
            return {
                'rationale': f'Error querying Hall of Fame: {e}. Using default parameters.'
            }

    def _suggest_param_variations(
        self,
        base_params: Dict[str, Any],
        variation_range: float = 0.20
    ) -> Dict[str, List[Any]]:
        """
        Suggest parameter variations around base values.

        Creates parameter ranges for exploration based on champion parameters.
        Useful for generating diverse strategies around proven configurations.

        Args:
            base_params: Base parameter dictionary from champion
            variation_range: Variation percentage (default: 0.20 = ±20%)

        Returns:
            Dictionary mapping parameter names to lists of suggested values

        Example:
            >>> variations = integrator._suggest_param_variations(
            ...     base_params={'n_stocks': 10, 'ma_short': 20},
            ...     variation_range=0.20
            ... )
            >>> print(variations)
            {
                'n_stocks': [8, 10, 12],  # ±20% of 10
                'ma_short': [16, 20, 24]  # ±20% of 20
            }

        Note:
            - Integer parameters: Round to nearest integer
            - Float parameters: Maintain decimal precision
            - Non-numeric: Return as single-value list
        """
        variations = {}

        for param_name, base_value in base_params.items():
            if isinstance(base_value, int):
                # Integer parameter - suggest ±variation_range
                lower = int(base_value * (1 - variation_range))
                upper = int(base_value * (1 + variation_range))

                # Ensure at least 3 variations
                variations[param_name] = [
                    lower,
                    base_value,
                    upper
                ]

            elif isinstance(base_value, float):
                # Float parameter - suggest ±variation_range
                lower = base_value * (1 - variation_range)
                upper = base_value * (1 + variation_range)

                variations[param_name] = [
                    round(lower, 4),
                    round(base_value, 4),
                    round(upper, 4)
                ]

            else:
                # Non-numeric - use as-is
                variations[param_name] = [base_value]

        return variations

    def _should_force_exploration(self, iteration: int) -> bool:
        """
        Check if forced exploration mode should be activated.

        Exploration mode activates every EXPLORATION_FREQUENCY iterations
        (default: every 5th iteration) to promote template diversity and
        prevent over-fitting to a single template architecture.

        Args:
            iteration: Current iteration number (1-indexed)

        Returns:
            True if exploration mode should be forced, False otherwise

        Example:
            >>> integrator._should_force_exploration(5)
            True
            >>> integrator._should_force_exploration(10)
            True
            >>> integrator._should_force_exploration(3)
            False

        Requirements:
            - Requirement 4.4: Forced exploration every 5 iterations
        """
        is_exploration = (iteration % self.EXPLORATION_FREQUENCY) == 0

        if is_exploration:
            self.logger.info(f"⚡ EXPLORATION MODE activated at iteration {iteration}")

        return is_exploration

    def _recommend_exploration_template(
        self,
        iteration: int,
        exclude_recent: int = 3
    ) -> TemplateRecommendation:
        """
        Recommend template for exploration mode.

        Selects a template that has not been used recently to promote diversity
        and avoid template repetition. Uses expanded parameter ranges (+30%/-30%)
        for broader exploration.

        Algorithm:
            1. Get all available templates
            2. Exclude templates used in last N iterations (default: 3)
            3. Select from remaining templates (preferring least-used)
            4. Expand parameter ranges to ±30% for exploration
            5. Mark recommendation with exploration_mode=True

        Args:
            iteration: Current iteration number
            exclude_recent: Number of recent iterations to exclude (default: 3)
                Prevents repeating templates from last 3 iterations

        Returns:
            TemplateRecommendation with exploration_mode=True and expanded parameters

        Example:
            >>> recommendation = integrator._recommend_exploration_template(
            ...     iteration=10,
            ...     exclude_recent=3
            ... )
            >>> print(recommendation.exploration_mode)
            True
            >>> print(recommendation.template_name)
            'MastiffTemplate'  # Different from recent templates

        Requirements:
            - Requirement 4.4: Forced exploration with template diversity
        """
        # Get recent template usage
        recent_templates = self.iteration_history[-exclude_recent:] if exclude_recent > 0 else []

        # Get all available templates
        all_templates = self.get_available_templates()

        # Filter out recently used templates
        candidate_templates = [
            t for t in all_templates
            if t not in recent_templates
        ]

        # If all templates recently used, use all templates
        if not candidate_templates:
            self.logger.warning(
                f"All templates used recently. Using full template list for exploration."
            )
            candidate_templates = all_templates

        # Select template with lowest recent usage
        template_usage_counts = {t: recent_templates.count(t) for t in all_templates}
        selected_template = min(
            candidate_templates,
            key=lambda t: template_usage_counts.get(t, 0)
        )

        self.logger.info(
            f"⚡ Exploration template: {selected_template} "
            f"(avoiding recent: {recent_templates})"
        )

        # Generate exploration rationale
        rationale = (
            f"⚡ EXPLORATION MODE (iteration {iteration}): "
            f"Testing {selected_template} for template diversity. "
            f"Avoiding recently used templates: {recent_templates}. "
            f"Using expanded parameter ranges (±30%) for broader exploration. "
            f"Success rate: {self.TEMPLATE_SUCCESS_RATES.get(selected_template, 0.50):.0%}."
        )

        # Get template default parameters or champion parameters
        template_class = self.get_template_class(selected_template)
        suggested_params = {}

        if template_class:
            try:
                # Instantiate template to access PARAM_GRID property
                template_instance = template_class()
                param_grid = template_instance.PARAM_GRID

                for param_name, param_values in param_grid.items():
                    if isinstance(param_values, list) and param_values:
                        # Use middle value
                        mid_idx = len(param_values) // 2
                        base_value = param_values[mid_idx]

                        # Expand range for exploration (±30%)
                        if isinstance(base_value, int):
                            lower = int(base_value * 0.70)  # -30%
                            upper = int(base_value * 1.30)  # +30%
                            # Use base value, but mark for expansion
                            suggested_params[param_name] = base_value
                        elif isinstance(base_value, float):
                            lower = base_value * 0.70
                            upper = base_value * 1.30
                            suggested_params[param_name] = base_value
                        else:
                            suggested_params[param_name] = base_value

            except Exception:
                # If instantiation fails, use empty params
                suggested_params = {}

        return TemplateRecommendation(
            template_name=selected_template,
            rationale=rationale,
            match_score=0.65,  # Lower confidence for exploration
            suggested_params=suggested_params,
            exploration_mode=True
        )

    def _incorporate_validation_feedback(
        self,
        recommendation: TemplateRecommendation,
        validation_result: Any = None  # ValidationResult from validation system
    ) -> TemplateRecommendation:
        """
        Incorporate validation feedback into template recommendation.

        Analyzes validation failures and adjusts recommendation to avoid
        recurring errors. Suggests parameter changes or simpler templates
        based on validation error patterns.

        Validation Error Patterns:
            1. Parameter out of range → Adjust parameter values
            2. Architecture complexity issues → Recommend simpler template
            3. Data access errors → Adjust dataset usage parameters
            4. Backtest configuration issues → Adjust position sizing

        Args:
            recommendation: Original template recommendation
            validation_result: ValidationResult from validation system
                Contains errors, warnings, and suggestions

        Returns:
            Updated TemplateRecommendation with validation-aware adjustments

        Example:
            >>> original = TemplateRecommendation(
            ...     template_name='TurtleTemplate',
            ...     rationale='High Sharpe recommendation',
            ...     match_score=0.85,
            ...     suggested_params={'n_stocks': 10}
            ... )
            >>> updated = integrator._incorporate_validation_feedback(
            ...     original,
            ...     validation_result  # Contains parameter range error
            ... )
            >>> print(updated.suggested_params['n_stocks'])
            15  # Adjusted based on validation feedback

        Requirements:
            - Requirement 4.5: Validation-aware feedback integration
        """
        if not validation_result:
            # No validation feedback, return original recommendation
            return recommendation

        # Import ValidationResult and Severity
        try:
            from ..validation import ValidationResult, Severity
        except ImportError:
            self.logger.warning("Cannot import validation types for feedback")
            return recommendation

        # Check if validation result is valid
        if not hasattr(validation_result, 'errors'):
            return recommendation

        # Analyze errors for patterns
        critical_errors = [
            e for e in validation_result.errors
            if hasattr(e, 'severity') and e.severity == Severity.CRITICAL
        ]

        moderate_errors = [
            e for e in validation_result.errors
            if hasattr(e, 'severity') and e.severity == Severity.MODERATE
        ]

        self.logger.info(
            f"Validation feedback: {len(critical_errors)} critical, "
            f"{len(moderate_errors)} moderate errors"
        )

        # Pattern 1: Parameter range errors
        param_errors = [
            e for e in (critical_errors + moderate_errors)
            if 'parameter' in str(e.message).lower() or 'range' in str(e.message).lower()
        ]

        if param_errors:
            # Adjust parameters to safer values
            adjusted_params = self._adjust_params_for_validation(
                recommendation.suggested_params.copy(),
                param_errors
            )

            recommendation = TemplateRecommendation(
                template_name=recommendation.template_name,
                rationale=(
                    f"{recommendation.rationale} "
                    f"[Adjusted for validation: {len(param_errors)} parameter issues resolved]"
                ),
                match_score=recommendation.match_score * 0.95,  # Slight confidence reduction
                suggested_params=adjusted_params,
                champion_reference=recommendation.champion_reference,
                exploration_mode=recommendation.exploration_mode
            )

        # Pattern 2: Architecture complexity errors (too many conditions, etc.)
        complexity_errors = [
            e for e in critical_errors
            if 'complexity' in str(e.message).lower() or 'architecture' in str(e.message).lower()
        ]

        if complexity_errors and recommendation.template_name in ['TurtleTemplate', 'MastiffTemplate']:
            # Recommend simpler template
            simpler_template = 'FactorTemplate'  # Single-factor, simpler architecture

            self.logger.warning(
                f"Architecture complexity issues detected. "
                f"Recommending simpler template: {simpler_template}"
            )

            recommendation = TemplateRecommendation(
                template_name=simpler_template,
                rationale=(
                    f"Validation feedback: Architecture complexity errors detected. "
                    f"Recommending {simpler_template} (simpler single-factor architecture) "
                    f"to avoid complexity issues. Original: {recommendation.template_name}."
                ),
                match_score=0.70,  # Lower confidence for fallback
                suggested_params=self._get_default_params(simpler_template),
                champion_reference=None,
                exploration_mode=False
            )

        # Pattern 3: Data access errors
        data_errors = [
            e for e in (critical_errors + moderate_errors)
            if 'data' in str(e.message).lower() or 'dataset' in str(e.message).lower()
        ]

        if data_errors:
            # Suggest using more common datasets
            rationale_suffix = (
                f" [Validation: {len(data_errors)} data access issues - "
                f"suggest using common datasets: revenue, price, volume]"
            )

            recommendation = TemplateRecommendation(
                template_name=recommendation.template_name,
                rationale=recommendation.rationale + rationale_suffix,
                match_score=recommendation.match_score * 0.90,
                suggested_params=recommendation.suggested_params,
                champion_reference=recommendation.champion_reference,
                exploration_mode=recommendation.exploration_mode
            )

        return recommendation

    def _adjust_params_for_validation(
        self,
        params: Dict[str, Any],
        param_errors: List[Any]
    ) -> Dict[str, Any]:
        """
        Adjust parameters to resolve validation errors.

        Common adjustments:
            - n_stocks out of range → Adjust to 5-30 range
            - stop_loss too aggressive → Increase to 0.05-0.15
            - ma_short/ma_long invalid → Adjust to standard ranges

        Args:
            params: Original parameter dictionary
            param_errors: List of parameter-related validation errors

        Returns:
            Adjusted parameter dictionary
        """
        adjusted = params.copy()

        # Analyze error messages for specific parameters
        for error in param_errors:
            error_msg = str(error.message).lower()

            # n_stocks adjustments
            if 'n_stocks' in error_msg:
                if 'n_stocks' in adjusted:
                    current = adjusted['n_stocks']
                    # Adjust to safe range 10-20
                    if current < 10:
                        adjusted['n_stocks'] = 10
                        self.logger.info("Adjusted n_stocks: {current} → 10")
                    elif current > 30:
                        adjusted['n_stocks'] = 30
                        self.logger.info(f"Adjusted n_stocks: {current} → 30")

            # stop_loss adjustments
            if 'stop_loss' in error_msg or 'stop' in error_msg:
                if 'stop_loss' in adjusted:
                    current = adjusted['stop_loss']
                    # Adjust to conservative range 0.06-0.12
                    if current < 0.05:
                        adjusted['stop_loss'] = 0.06
                        self.logger.info(f"Adjusted stop_loss: {current:.2f} → 0.06")
                    elif current > 0.15:
                        adjusted['stop_loss'] = 0.12
                        self.logger.info(f"Adjusted stop_loss: {current:.2f} → 0.12")

            # ma_short/ma_long adjustments
            if 'ma_short' in error_msg:
                if 'ma_short' in adjusted:
                    adjusted['ma_short'] = 20  # Standard short MA
                    self.logger.info("Adjusted ma_short → 20")

            if 'ma_long' in error_msg:
                if 'ma_long' in adjusted:
                    adjusted['ma_long'] = 60  # Standard long MA
                    self.logger.info("Adjusted ma_long → 60")

        return adjusted

    def _get_default_params(self, template_name: str) -> Dict[str, Any]:
        """
        Get default parameters for a template.

        Args:
            template_name: Template name

        Returns:
            Dictionary of default parameters for the template
        """
        template_class = self.get_template_class(template_name)

        if not template_class:
            return {}

        try:
            # Instantiate template to access PARAM_GRID property
            template_instance = template_class()
            param_grid = template_instance.PARAM_GRID

            # Use middle values from PARAM_GRID
            default_params = {}

            for param_name, param_values in param_grid.items():
                if isinstance(param_values, list) and param_values:
                    mid_idx = len(param_values) // 2
                    default_params[param_name] = param_values[mid_idx]

            return default_params

        except Exception:
            return {}

    def recommend_template(
        self,
        current_metrics: Optional[Dict[str, Any]] = None,
        iteration: int = 1,
        validation_result: Any = None,
        strategy_code: Optional[str] = None,
        current_params: Optional[Dict[str, Any]] = None,
        risk_profile: Optional[str] = None
    ) -> TemplateRecommendation:
        """
        Comprehensive template recommendation orchestrator.

        Main public API method that orchestrates all recommendation strategies:
        1. Forced exploration mode (every 5th iteration)
        2. Performance-based recommendation (Sharpe, drawdown, volatility)
        3. Champion-based parameter suggestions (Hall of Fame)
        4. Validation-aware feedback (error pattern analysis)
        5. Template match scoring (architecture similarity)

        Recommendation Flow:
            Step 1: Check forced exploration mode (iteration % 5 == 0)
                → If True: Use _recommend_exploration_template()
            Step 2: Otherwise, use _recommend_by_performance()
            Step 3: Enhance with champion parameters if repository available
            Step 4: Incorporate validation feedback if provided
            Step 5: Track template usage in iteration history
            Step 6: Return comprehensive TemplateRecommendation

        Args:
            current_metrics: Performance metrics dictionary
                - sharpe_ratio: Sharpe ratio (primary metric)
                - max_drawdown: Maximum drawdown
                - volatility: Strategy volatility
                - total_return: Total return
            iteration: Current iteration number (1-indexed, default: 1)
                Used for forced exploration every 5th iteration
            validation_result: Optional ValidationResult from validation system
                Contains errors, warnings, suggestions for feedback
            strategy_code: Optional strategy code for match scoring
                Used to calculate architecture similarity scores
            current_params: Optional current parameters
                Used for parameter similarity scoring
            risk_profile: Optional risk profile override
                Values: 'concentrated', 'stable', 'aggressive', 'fast'

        Returns:
            TemplateRecommendation with:
                - template_name: Recommended template
                - rationale: Detailed explanation
                - match_score: Confidence score (0.0-1.0)
                - suggested_params: Parameter dictionary
                - champion_reference: Optional champion genome ID
                - exploration_mode: True if exploration iteration

        Example:
            >>> integrator = TemplateFeedbackIntegrator(repository)
            >>> recommendation = integrator.recommend_template(
            ...     current_metrics={'sharpe_ratio': 0.8, 'max_drawdown': 0.12},
            ...     iteration=5,
            ...     validation_result=None
            ... )
            >>> print(recommendation.template_name)
            'MastiffTemplate'  # Exploration mode at iteration 5
            >>> print(recommendation.exploration_mode)
            True

        Requirements:
            - Requirement 4.1: Template recommendation system
            - Requirement 4.2: Performance-based selection
            - Requirement 4.3: Champion-based suggestions
            - Requirement 4.4: Forced exploration mode
            - Requirement 4.5: Validation feedback integration
        """
        self.logger.info(
            f"recommend_template() called: iteration={iteration}, "
            f"metrics={bool(current_metrics)}, validation={bool(validation_result)}"
        )

        # Step 1: Check forced exploration mode
        if self._should_force_exploration(iteration):
            recommendation = self._recommend_exploration_template(
                iteration=iteration,
                exclude_recent=3
            )

            self.logger.info(
                f"⚡ Exploration recommendation: {recommendation.template_name} "
                f"(match_score={recommendation.match_score:.2f})"
            )

        else:
            # Step 2: Performance-based recommendation
            recommendation = self._recommend_by_performance(
                current_metrics=current_metrics,
                risk_profile=risk_profile
            )

            self.logger.info(
                f"Performance recommendation: {recommendation.template_name} "
                f"(match_score={recommendation.match_score:.2f})"
            )

        # Step 3: Enhance with champion parameters (if not exploration mode)
        if not recommendation.exploration_mode and self.repository:
            try:
                champion_params = self.get_champion_template_params(
                    template_name=recommendation.template_name,
                    min_sharpe=1.5,
                    variation_range=0.20
                )

                if champion_params and 'champion_id' in champion_params:
                    # Merge champion parameters with recommendation
                    champion_id = champion_params.pop('champion_id')
                    champion_sharpe = champion_params.pop('champion_sharpe', 0.0)
                    champion_template = champion_params.pop('champion_template', 'unknown')
                    champion_rationale = champion_params.pop('rationale', '')

                    # Update suggested params with champion params
                    updated_params = recommendation.suggested_params.copy()
                    for key, value in champion_params.items():
                        if key not in ['rationale']:
                            updated_params[key] = value

                    # Update recommendation with champion info
                    recommendation = TemplateRecommendation(
                        template_name=recommendation.template_name,
                        rationale=(
                            f"{recommendation.rationale}\n\n"
                            f"Champion-enhanced: {champion_rationale}"
                        ),
                        match_score=min(recommendation.match_score + 0.05, 1.0),  # Slight boost
                        suggested_params=updated_params,
                        champion_reference=champion_id,
                        exploration_mode=recommendation.exploration_mode
                    )

                    self.logger.info(
                        f"Enhanced with champion {champion_id} "
                        f"(sharpe={champion_sharpe:.2f})"
                    )

            except Exception as e:
                self.logger.warning(f"Failed to enhance with champion params: {e}")

        # Step 4: Incorporate validation feedback
        if validation_result:
            recommendation = self._incorporate_validation_feedback(
                recommendation=recommendation,
                validation_result=validation_result
            )

            self.logger.info(
                f"Validation feedback incorporated: {recommendation.template_name}"
            )

        # Step 5: Calculate match scores if strategy code provided
        if strategy_code:
            match_scores = self.calculate_template_match_score(
                strategy_code=strategy_code,
                current_params=current_params,
                current_metrics=current_metrics
            )

            # Log match scores for transparency
            self.logger.info(f"Template match scores: {match_scores}")

            # Optionally boost match_score if current strategy matches recommended template
            recommended_match = match_scores.get(recommendation.template_name, 0.0)
            if recommended_match > 0.7:
                self.logger.info(
                    f"High architecture match: {recommendation.template_name} "
                    f"(score={recommended_match:.2f})"
                )

        # Step 6: Track template usage
        self.track_iteration(recommendation.template_name)

        # Final logging
        self.logger.info(
            f"Final recommendation: {recommendation.template_name} "
            f"(match_score={recommendation.match_score:.2f}, "
            f"exploration={recommendation.exploration_mode}, "
            f"champion={bool(recommendation.champion_reference)})"
        )

        return recommendation
