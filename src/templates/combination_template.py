"""
Combination Strategy Template
==============================

Implements weighted combination of multiple existing strategy templates.

Architecture:
-------------
The Combination template validates if template combination can exceed single-template
performance ceiling by:
- Instantiating multiple sub-templates with independent parameters
- Combining positions using weighted allocation
- Rebalancing at specified frequency (M/W-FRI)
- Handling parameter mutation (delegate to sub-templates + weight mutation)

Strategy Characteristics:
------------------------
1. **Multi-Template Combination**: Combines 2-3 templates
   - Template options: turtle, momentum, mastiff
   - Parameters: templates (list of template names)

2. **Weighted Allocation**: Configurable weight distribution
   - Weight options: [0.5, 0.5], [0.7, 0.3], [0.4, 0.4, 0.2]
   - Parameters: weights (list matching templates length)

3. **Rebalancing Frequency**: Monthly or weekly portfolio rebalancing
   - Frequency options: 'M' (monthly), 'W-FRI' (weekly Friday)
   - Parameters: rebalance (str)

Position Management:
-------------------
- Portfolio: Weighted combination of sub-template positions
- Rebalancing: Monthly ('M') or Weekly ('W-FRI')
- Position sizing: Delegated to sub-templates

Performance Targets:
-------------------
- Sharpe Ratio: >2.5 (exceeds Turtle baseline 1.5-2.5)
- Annual Return: >30% (combination premium)
- Max Drawdown: -20% to -10% (improved risk management)

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Phase 1.5: Validates template combination effectiveness
"""

from typing import Dict, List, Tuple, Any
import numpy as np
import random
from src.templates.base_template import BaseTemplate


class CombinationTemplate(BaseTemplate):
    """
    Weighted Combination Strategy Template.

    Implements a meta-strategy that combines multiple existing templates:
    - Instantiates sub-templates with independent parameters
    - Combines positions using weighted allocation
    - Rebalances at specified frequency
    - Mutates weights and template selection

    The strategy tests whether template combination can exceed single-template
    performance ceiling (Turtle Sharpe 1.5-2.5). If successful, Phase 1.5
    concludes with optimized combination logic. If unsuccessful, proceed to
    structural mutation design (Hybrid approach).

    Attributes:
        name (str): "Combination" - identifying name for this template
        pattern_type (str): "weighted_combination" - describes the combination strategy
        PARAM_GRID (Dict[str, List]): 3-parameter search space
        expected_performance (Dict[str, Tuple[float, float]]): Performance targets
            - sharpe_range: (2.5, 3.5) - exceeds Turtle ceiling
            - return_range: (0.30, 0.45) - combination premium
            - mdd_range: (-0.20, -0.10) - improved risk management
    """

    @property
    def name(self) -> str:
        """
        Return the template name.

        Returns:
            str: "Combination" - the identifying name for this template
        """
        return "Combination"

    @property
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: "weighted_combination" - describes the combination approach
        """
        return "weighted_combination"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 3 tunable parameters for template combination.
        Total search space: ~30-40 unique configurations

        Parameter Categories:
        --------------------
        Template Selection:
            - templates: List of template names to combine (2-3 templates)
                ['turtle', 'momentum'] - Trend + reversal
                ['turtle', 'mastiff'] - Conservative blend
                ['momentum', 'mastiff'] - Balanced
                ['turtle', 'momentum', 'mastiff'] - Full diversification

        Weight Allocation:
            - weights: Weight distribution across templates
                For 2-template combinations:
                    [0.5, 0.5] - Equal weight
                    [0.7, 0.3] - Dominant + satellite
                    [0.8, 0.2] - Primary + hedge
                For 3-template combinations:
                    [0.4, 0.4, 0.2] - Balanced with small hedge
                    [0.5, 0.3, 0.2] - Tiered allocation

        Rebalancing Frequency:
            - rebalance: Portfolio rebalancing frequency
                'M' - Monthly rebalancing (lower turnover)
                'W-FRI' - Weekly Friday rebalancing (more responsive)

        Design Rationale:
            - Start with proven templates (Turtle Sharpe 1.5-2.5)
            - Test equal, dominant, and satellite weight strategies
            - Monthly vs. weekly rebalancing trade-off
            - 2-3 templates max to avoid over-diversification

        Returns:
            Dict[str, List]: Parameter grid with 3 parameters

        Source:
            Design specified in .spec-workflow/specs/combination-template-phase15/design.md
        """
        return {
            'templates': [
                # 2-template combinations (temporarily exclude momentum due to resample incompatibility)
                ['turtle', 'mastiff']
                # TODO: Re-enable after fixing MomentumTemplate resample format
                # ['turtle', 'momentum'],
                # ['momentum', 'mastiff'],
                # ['turtle', 'momentum', 'mastiff']
            ],
            'weights': [
                # 2-template weights
                [0.5, 0.5],
                [0.7, 0.3],
                [0.8, 0.2]
            ],
            'rebalance': ['M', 'W-FRI']
        }

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These ranges represent aggressive targets that exceed single-template
        performance ceilings. The goal is to validate if template combination
        can deliver superior risk-adjusted returns compared to individual
        templates (particularly Turtle baseline of 1.5-2.5 Sharpe).

        Performance Targets:
        -------------------
        - Sharpe Ratio: 2.5-3.5 (exceeds Turtle ceiling of 1.5-2.5)
        - Annual Return: 30-45% (combination premium over single templates)
        - Max Drawdown: -20% to -10% (improved risk management)

        Returns:
            Dict[str, Tuple[float, float]]: Performance ranges with keys:
                - 'sharpe_range': (min_sharpe, max_sharpe)
                - 'return_range': (min_return, max_return) as decimals
                - 'mdd_range': (min_drawdown, max_drawdown) as negative decimals

        Note:
            These aggressive targets are intentionally set high to test the
            hypothesis that template combination can exceed single-template
            performance. Validation failure (Sharpe ≤2.5) indicates need for
            structural mutation approach (Phase 2).
        """
        return {
            'sharpe_range': (2.5, 3.5),
            'return_range': (0.30, 0.45),
            'mdd_range': (-0.20, -0.10)
        }

    def validate_params(self, params: Dict) -> Tuple[bool, List[str]]:
        """
        Validate parameter dictionary against PARAM_GRID.

        Performs comprehensive validation including:
        - Templates list validation (2-3 templates, valid template names)
        - Weights list validation (length matches templates, sum to 1.0)
        - Rebalance frequency validation ('M' or 'W-FRI')
        - No duplicate templates

        Args:
            params (Dict): Parameter dictionary to validate with keys:
                - templates (List[str]): Template names
                - weights (List[float]): Weight allocation
                - rebalance (str): Rebalancing frequency

        Returns:
            Tuple[bool, List[str]]: A tuple containing:
                - is_valid (bool): True if all validations pass, False otherwise
                - errors (List[str]): List of validation error messages (empty if valid)

        Example:
            >>> template = CombinationTemplate()
            >>> is_valid, errors = template.validate_params({
            ...     'templates': ['turtle', 'momentum'],
            ...     'weights': [0.7, 0.3],
            ...     'rebalance': 'M'
            ... })
            >>> print(is_valid)  # True
            >>> print(errors)    # []
        """
        errors: List[str] = []

        # Check for required parameters
        required_params = ['templates', 'weights', 'rebalance']
        missing_params = [p for p in required_params if p not in params]
        if missing_params:
            errors.append(f"Missing required parameters: {missing_params}")
            return False, errors

        # Validate templates
        templates = params['templates']
        if not isinstance(templates, list):
            errors.append(f"Parameter 'templates' must be a list, got {type(templates).__name__}")
        elif len(templates) < 2 or len(templates) > 3:
            errors.append(f"Parameter 'templates' must contain 2-3 templates, got {len(templates)}")
        else:
            # Check for valid template names
            available_templates = ['turtle', 'momentum', 'mastiff', 'factor']
            for template in templates:
                if template not in available_templates:
                    errors.append(
                        f"Invalid template '{template}'. "
                        f"Available templates: {available_templates}"
                    )

            # Check for duplicate templates
            if len(templates) != len(set(templates)):
                errors.append(f"Duplicate templates not allowed: {templates}")

        # Validate weights
        weights = params['weights']
        if not isinstance(weights, list):
            errors.append(f"Parameter 'weights' must be a list, got {type(weights).__name__}")
        elif len(templates) != len(weights):
            errors.append(
                f"Parameter 'weights' length ({len(weights)}) must match "
                f"templates length ({len(templates)})"
            )
        else:
            # Check weight sum (tolerance ±0.01)
            weight_sum = sum(weights)
            if not (0.99 <= weight_sum <= 1.01):
                errors.append(
                    f"Parameter 'weights' must sum to 1.0 (±0.01), got {weight_sum:.3f}"
                )

            # Check weight ranges (avoid extreme allocations)
            for i, weight in enumerate(weights):
                if not isinstance(weight, (int, float)):
                    errors.append(
                        f"Weight at index {i} must be numeric, got {type(weight).__name__}"
                    )
                elif weight < 0.0 or weight > 1.0:
                    errors.append(
                        f"Weight at index {i} must be in [0.0, 1.0], got {weight}"
                    )

        # Validate rebalance frequency
        rebalance = params['rebalance']
        if rebalance not in ['M', 'W-FRI']:
            errors.append(
                f"Parameter 'rebalance' must be 'M' or 'W-FRI', got '{rebalance}'"
            )

        is_valid = len(errors) == 0
        return is_valid, errors

    def mutate_parameters(self, params: Dict, mutation_rate: float = 0.1) -> Dict:
        """
        Mutate combination parameters with validation.

        Implements three-level mutation strategy:
        1. Template selection mutation (10% chance)
        2. Weight mutation (mutation_rate chance, Gaussian noise)
        3. Rebalance frequency mutation (5% chance)

        Args:
            params (Dict): Current parameter dictionary with keys:
                - templates (List[str]): Current template names
                - weights (List[float]): Current weight allocation
                - rebalance (str): Current rebalancing frequency
            mutation_rate (float): Probability of weight mutation (0.0-1.0)

        Returns:
            Dict: Mutated parameter dictionary with same structure as input

        Mutation Details:
            Template Mutation (10% chance):
                - Randomly selects one template index
                - Swaps with a different available template
                - Ensures no duplicate templates after swap

            Weight Mutation (mutation_rate chance):
                - Applies Gaussian noise (σ=0.1) to each weight
                - Clips weights to [0.1, 0.9] to avoid extreme allocations
                - Renormalizes to sum to 1.0

            Rebalance Mutation (5% chance):
                - Toggles between 'M' and 'W-FRI'
                - Tests different turnover strategies

        Example:
            >>> template = CombinationTemplate()
            >>> original = {
            ...     'templates': ['turtle', 'momentum'],
            ...     'weights': [0.7, 0.3],
            ...     'rebalance': 'M'
            ... }
            >>> mutated = template.mutate_parameters(original, mutation_rate=0.1)
            >>> # mutated may have different weights, templates, or rebalance frequency
        """
        mutated = {
            'templates': params['templates'].copy(),
            'weights': params['weights'].copy(),
            'rebalance': params['rebalance']
        }

        # Mutation 1: Template selection (10% chance)
        if random.random() < 0.1:
            available = ['turtle', 'momentum', 'mastiff', 'factor']
            # Remove current templates from available options
            available_swap = [t for t in available if t not in mutated['templates']]

            if available_swap:  # Only mutate if there are alternatives
                idx = random.randint(0, len(mutated['templates']) - 1)
                mutated['templates'][idx] = random.choice(available_swap)

        # Mutation 2: Weight mutation (Gaussian noise with renormalization)
        if random.random() < mutation_rate:
            weights = np.array(mutated['weights'])

            # Apply Gaussian noise (σ=0.1)
            noise = np.random.normal(0, 0.1, size=len(weights))
            weights = weights + noise

            # Clip to avoid extreme allocations [0.1, 0.9]
            weights = np.clip(weights, 0.1, 0.9)

            # Renormalize to sum to 1.0
            weights = weights / weights.sum()

            mutated['weights'] = weights.tolist()

        # Mutation 3: Rebalance frequency (5% chance)
        if random.random() < 0.05:
            mutated['rebalance'] = 'W-FRI' if mutated['rebalance'] == 'M' else 'M'

        return mutated

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete combination strategy generation workflow:
        1. Validates input parameters
        2. Instantiates sub-templates via TemplateRegistry
        3. Generates positions from each sub-template
        4. Combines positions using weighted allocation
        5. Executes Finlab backtest with rebalancing
        6. Extracts performance metrics and validates against targets

        Args:
            params (Dict): Parameter dictionary with values for all 3 parameters
                defined in PARAM_GRID. Required keys:
                - templates (List[str]): Template names (2-3 templates)
                - weights (List[float]): Weight allocation (sum to 1.0)
                - rebalance (str): Rebalancing frequency ('M' or 'W-FRI')

        Returns:
            Tuple[object, Dict]: A tuple containing:
                - report (object): Finlab backtest report object with complete
                    results including trades, equity curve, and metrics
                - metrics_dict (Dict): Dictionary with extracted metrics:
                    - 'annual_return' (float): Annual return as decimal
                    - 'sharpe_ratio' (float): Sharpe ratio
                    - 'max_drawdown' (float): Max drawdown as negative decimal
                    - 'success' (bool): True if strategy meets all performance
                        targets (Sharpe ≥2.5, Return ≥30%, MDD ≥-20%)

        Raises:
            ValueError: If parameters are invalid or fail validation
            RuntimeError: If strategy generation or backtesting fails
            Exception: If sub-template instantiation or position generation fails

        Performance:
            Target execution time: <60s per strategy generation
            (2-3× single template due to multiple sub-template backtests)

        Example:
            >>> template = CombinationTemplate()
            >>> params = {
            ...     'templates': ['turtle', 'momentum'],
            ...     'weights': [0.7, 0.3],
            ...     'rebalance': 'M'
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 2.75
        """
        # Validate parameters before execution
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Instantiate sub-templates via TemplateRegistry
            from src.utils.template_registry import TemplateRegistry

            registry = TemplateRegistry.get_instance()
            sub_templates = []

            for template_name in params['templates']:
                # Capitalize template name for registry lookup
                template_key = template_name.capitalize()
                sub_template = registry.get_template(template_key)
                sub_templates.append(sub_template)

            # Step 2: Generate positions from each sub-template with default params
            sub_positions_list = []
            for sub_template, weight in zip(sub_templates, params['weights']):
                # Get default parameters for sub-template
                sub_params = sub_template.get_default_params()

                # Generate strategy report
                sub_report, _ = sub_template.generate_strategy(sub_params)

                # Extract positions from report
                # positions is a DataFrame with stocks as columns, dates as index
                sub_positions = sub_report.position

                # Normalize positions to sum to 1.0 per timestamp
                sub_positions_norm = sub_positions.div(sub_positions.sum(axis=1), axis=0)

                # Apply weight
                sub_positions_weighted = sub_positions_norm * weight

                sub_positions_list.append(sub_positions_weighted)

            # Step 3: Combine weighted positions
            combined_positions = sum(sub_positions_list)

            # Step 4: Apply rebalancing frequency
            if params['rebalance'] == 'M':
                combined_positions = combined_positions.resample('ME').last().ffill()
            elif params['rebalance'] == 'W-FRI':
                combined_positions = combined_positions.resample('W-FRI').last().ffill()

            # Step 5: Execute backtest with combined positions
            from finlab import backtest

            strategy_name = (
                f"Combo_{'_'.join([t[:3] for t in params['templates']])}_"
                f"w{'_'.join([str(int(w*10)) for w in params['weights']])}_"
                f"{params['rebalance']}"
            )

            report = backtest.sim(
                combined_positions,
                resample=params['rebalance'],
                fee_ratio=1.425/1000/3,  # Taiwan stock transaction fee
                upload=False,  # Disable upload for sandbox testing
                name=strategy_name
            )

            # Step 6: Extract performance metrics
            annual_return = report.metrics.annual_return()
            sharpe_ratio = report.metrics.sharpe_ratio()
            max_drawdown = report.metrics.max_drawdown()

            # Step 7: Validate against performance targets
            expected_perf = self.expected_performance
            success = (
                sharpe_ratio >= expected_perf['sharpe_range'][0] and
                annual_return >= expected_perf['return_range'][0] and
                max_drawdown >= expected_perf['mdd_range'][0]
            )

            metrics = {
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'success': success
            }

            return report, metrics

        except ValueError as e:
            # Re-raise ValueError for parameter validation errors
            raise

        except KeyError as e:
            # Template not found in registry
            raise ValueError(
                f"Template not found in registry: {e}. "
                f"Available templates: {registry.get_available_templates()}"
            ) from e

        except AttributeError as e:
            # Backtest or metrics calculation error
            raise RuntimeError(
                f"Failed to extract metrics from backtest report: {e}. "
                f"Ensure backtest.sim() completed successfully and report "
                f"object has valid metrics attribute."
            ) from e

        except Exception as e:
            # General error with context logging
            raise RuntimeError(
                f"Strategy generation failed for CombinationTemplate with params {params}: {e}. "
                f"Check sub-template availability, position generation, and backtest execution."
            ) from e
