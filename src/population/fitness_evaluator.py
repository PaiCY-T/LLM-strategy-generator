"""
Fitness Evaluator with IS/OOS Data Split and Multi-Template Support.

Evaluates strategy performance on in-sample (IS) and out-of-sample (OOS) data
to prevent overfitting and validate robustness. Supports both single-template
and multi-template evolution modes.
"""

from typing import Dict, List, Any, Optional
from src.population.individual import Individual


class FitnessEvaluator:
    """
    Evaluates individual fitness on IS/OOS data splits with caching.

    Implements temporal data splitting to prevent overfitting:
    - In-Sample (IS): 2015-2020 for fitness optimization during evolution
    - Out-of-Sample (OOS): 2021-2024 for final validation

    Supports two modes:
    - Single-template mode (template != None): All individuals use same template
    - Multi-template mode (template == None): Each individual uses its own template_type

    Attributes:
        template: Strategy template for single-template mode (None for multi-template)
        data: Full Finlab data module reference
        is_start: Start date for IS period
        is_end: End date for IS period
        oos_start: Start date for OOS period
        oos_end: End date for OOS period
        _registry: TemplateRegistry instance for multi-template mode
        _cache: Dictionary mapping individual IDs to fitness/metrics
        _cache_hits: Count of cache hits
        _cache_misses: Count of cache misses
    """

    def __init__(
        self,
        template=None,
        data=None,
        is_start: str = '2015',
        is_end: str = '2020',
        oos_start: str = '2021',
        oos_end: str = '2024'
    ):
        """
        Initialize evaluator with IS/OOS data split.

        Args:
            template: Strategy template with generate_strategy() method.
                If None, enables multi-template mode where each Individual's
                template_type attribute determines which template to use.
                (default: None for multi-template mode)
            data: Full dataset (will be split into IS/OOS)
            is_start: Start date for in-sample period (default: '2015')
            is_end: End date for in-sample period (default: '2020')
            oos_start: Start date for out-of-sample period (default: '2021')
            oos_end: End date for out-of-sample period (default: '2024')

        Example (Single-template mode):
            >>> from src.templates.momentum_template import MomentumTemplate
            >>> template = MomentumTemplate()
            >>> evaluator = FitnessEvaluator(template, data)
            >>> fitness = evaluator.evaluate(individual, use_oos=False)

        Example (Multi-template mode):
            >>> evaluator = FitnessEvaluator(template=None, data=data)
            >>> # Individual's template_type determines which template to use
            >>> fitness = evaluator.evaluate(individual, use_oos=False)
        """
        self.template = template
        self.data = data

        # Store period boundaries
        self.is_start = is_start
        self.is_end = is_end
        self.oos_start = oos_start
        self.oos_end = oos_end

        # Initialize TemplateRegistry for multi-template mode
        if self.template is None:
            from src.utils.template_registry import TemplateRegistry
            self._registry = TemplateRegistry.get_instance()
        else:
            self._registry = None

        # Note: Actual IS/OOS split happens in _generate_and_backtest()
        # via DataCache filtering. We don't slice data here because
        # finlab.data is a module, not a DataFrame.
        # The period boundaries (is_start, is_end, oos_start, oos_end)
        # are used by _generate_and_backtest() to filter DataCache entries.

        # Cache for evaluated individuals (thread-safe dict for now)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def evaluate(
        self,
        individual: Individual,
        use_oos: bool = False
    ) -> Individual:
        """
        Evaluate individual fitness on IS or OOS data.

        During evolution, use_oos=False optimizes on in-sample data.
        For final validation, use_oos=True tests on out-of-sample data.

        Args:
            individual: Individual to evaluate
            use_oos: If True, evaluate on OOS data; if False, use IS data

        Returns:
            Individual: Same individual with fitness and metrics set

        Raises:
            ValueError: If individual is invalid
            RuntimeError: If strategy generation or backtest fails

        Example:
            >>> # Evolution (optimize on IS)
            >>> individual = evaluator.evaluate(individual, use_oos=False)
            >>> print(f"IS Sharpe: {individual.fitness}")
            >>>
            >>> # Validation (test on OOS)
            >>> individual = evaluator.evaluate(individual, use_oos=True)
            >>> print(f"OOS Sharpe: {individual.fitness}")
        """
        # Validate individual
        if not individual.is_valid():
            raise ValueError(f"Invalid individual: {individual}")

        # Check cache first (include template_type for defense-in-depth)
        cache_key = self._get_cache_key(individual.id, individual.template_type, use_oos)
        if cache_key in self._cache:
            self._cache_hits += 1
            cached_data = self._cache[cache_key]
            individual.fitness = cached_data['fitness']
            individual.metrics = cached_data['metrics']
            return individual

        # Cache miss - evaluate
        self._cache_misses += 1

        try:
            # Generate and backtest strategy with template routing
            strategy, metrics = self._generate_and_backtest(
                individual.parameters,
                use_oos,
                template_type=individual.template_type
            )

            # Extract fitness (Sharpe ratio)
            fitness = metrics.get('sharpe_ratio', 0.0)

            # Update individual
            individual.fitness = fitness
            individual.metrics = metrics

            # Cache results
            self._cache[cache_key] = {
                'fitness': fitness,
                'metrics': metrics
            }

            return individual

        except Exception as e:
            # On error, assign zero fitness
            individual.fitness = 0.0
            individual.metrics = {
                'annual_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': -1.0,
                'error': str(e)
            }

            # Cache failed evaluation to avoid retries
            self._cache[cache_key] = {
                'fitness': 0.0,
                'metrics': individual.metrics
            }

            return individual

    def evaluate_population(
        self,
        population: List[Individual],
        use_oos: bool = False
    ) -> List[Individual]:
        """
        Evaluate entire population in batch.

        Evaluates all individuals in the population on IS or OOS data.
        Leverages caching to avoid redundant evaluations.

        Args:
            population: List of individuals to evaluate
            use_oos: If True, evaluate on OOS data; if False, use IS data

        Returns:
            List[Individual]: Same population with all individuals evaluated

        Example:
            >>> # Evaluate initial population on IS
            >>> population = evaluator.evaluate_population(population)
            >>> avg_fitness = sum(ind.fitness for ind in population) / len(population)
            >>> print(f"Average IS Sharpe: {avg_fitness:.4f}")
        """
        evaluated_population = []

        for individual in population:
            evaluated_individual = self.evaluate(individual, use_oos)
            evaluated_population.append(evaluated_individual)

        return evaluated_population

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.

        Returns:
            Dict: Statistics with keys:
                - 'cache_size': Number of cached evaluations
                - 'cache_hits': Number of cache hits
                - 'cache_misses': Number of cache misses
                - 'hit_rate': Cache hit rate (0.0 to 1.0)
                - 'total_evaluations': Total evaluation requests

        Example:
            >>> stats = evaluator.get_cache_stats()
            >>> print(f"Cache hit rate: {stats['hit_rate']:.1%}")
            Cache hit rate: 23.5%
        """
        total = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total if total > 0 else 0.0

        return {
            'cache_size': len(self._cache),
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': hit_rate,
            'total_evaluations': total
        }

    def clear_cache(self) -> None:
        """
        Clear evaluation cache and reset statistics.

        Useful for testing or memory management.

        Example:
            >>> evaluator.clear_cache()
            >>> stats = evaluator.get_cache_stats()
            >>> assert stats['cache_size'] == 0
        """
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_cache_key(self, individual_id: str, template_type: str, use_oos: bool) -> str:
        """
        Generate cache key for individual, template, and data split.

        Defense-in-Depth Strategy:
        Explicitly includes template_type in cache key even though individual_id
        already encodes it via hash. This provides redundant protection against
        cache collisions if ID generation changes or hash collisions occur.

        Args:
            individual_id: Individual's unique ID (already includes template_type in hash)
            template_type: Template type name ('Momentum', 'Turtle', etc.)
            use_oos: Whether OOS data is used

        Returns:
            str: Cache key combining ID, template, and data split

        Example:
            >>> key = evaluator._get_cache_key('abc12345', 'Momentum', False)
            >>> assert key == 'abc12345_Momentum_is'
        """
        suffix = 'oos' if use_oos else 'is'
        return f"{individual_id}_{template_type}_{suffix}"

    def _generate_and_backtest(
        self,
        parameters: Dict[str, Any],
        use_oos: bool,
        template_type: Optional[str] = None
    ) -> tuple:
        """
        Generate strategy and backtest on selected data split with template routing.

        Implements IS/OOS data split by temporarily replacing DataCache entries
        with filtered data for the target period, then restoring after backtest.

        Template Routing:
        - Single-template mode (self.template != None): Uses self.template, ignores template_type
        - Multi-template mode (self.template == None): Gets template from registry using template_type

        Args:
            parameters: Strategy parameters
            use_oos: If True, backtest on OOS data; if False, use IS data
            template_type: Template type name for multi-template mode (optional)

        Returns:
            tuple: (strategy_object, metrics_dict)

        Raises:
            ValueError: If multi-template mode but template_type not provided
            RuntimeError: If strategy generation or backtest fails

        Implementation:
            1. Select template based on mode (single-template vs multi-template)
            2. Save original DataCache entries
            3. Replace with period-filtered data (IS or OOS)
            4. Generate strategy and backtest on filtered data
            5. Restore original DataCache entries
            6. Return results

        This approach ensures true IS/OOS separation without modifying
        the template interface.
        """
        from src.templates.data_cache import DataCache

        # Template selection logic
        if self.template is not None:
            # Single-template mode: use self.template (backward compatible)
            selected_template = self.template
        elif template_type is not None:
            # Multi-template mode: get template from registry
            selected_template = self._registry.get_template(template_type)
        else:
            # Error: multi-template mode but no template_type provided
            raise ValueError(
                "Multi-template mode (template=None) requires template_type parameter"
            )

        cache = DataCache.get_instance()

        # Select date range based on IS/OOS
        if use_oos:
            start_date = self.oos_start
            end_date = self.oos_end
        else:
            start_date = self.is_start
            end_date = self.is_end

        # Keys that need to be filtered for IS/OOS split
        KEYS_TO_FILTER = [
            'price:收盤價',
            'price:成交股數',
            'monthly_revenue:當月營收',
            'fundamental_features:ROE綜合損益',
        ]

        # Save original cache entries
        original_cache = {}
        for key in KEYS_TO_FILTER:
            if key in cache._cache:
                original_cache[key] = cache._cache[key]

        try:
            # Filter cached data to IS/OOS period
            for key in KEYS_TO_FILTER:
                if key in cache._cache:
                    full_data = original_cache[key]
                    # Filter to date range
                    filtered_data = full_data[start_date:end_date]
                    cache._cache[key] = filtered_data

            # Generate strategy on filtered data using selected template
            report, metrics = selected_template.generate_strategy(parameters)

            return report, metrics

        except Exception as e:
            raise RuntimeError(
                f"Strategy generation failed with parameters {parameters}: {str(e)}"
            ) from e

        finally:
            # Always restore original cache entries
            for key, original_data in original_cache.items():
                cache._cache[key] = original_data

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation
        """
        stats = self.get_cache_stats()
        return (
            f"FitnessEvaluator("
            f"IS={self.is_start}:{self.is_end}, "
            f"OOS={self.oos_start}:{self.oos_end}, "
            f"cache={stats['cache_size']}, "
            f"hit_rate={stats['hit_rate']:.1%})"
        )
