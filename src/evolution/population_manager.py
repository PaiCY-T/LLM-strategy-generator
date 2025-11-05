"""
Population manager for NSGA-II evolutionary optimization.

This module implements the central coordinator for population-based learning,
orchestrating selection, crossover, mutation, and fitness evaluation.

Key Components:
- PopulationManager: Central evolution coordinator
- initialize_population: Create diverse initial population
- evaluate_population: Fitness evaluation with multi-objective metrics
- evolve_generation: Complete NSGA-II generation workflow
- elitism_replacement: Elite preservation and population replacement
- Checkpointing: Save/load population state for recovery
- Diversity monitoring: Prevent premature convergence

Design Principles:
- Modularity: Clean separation of concerns
- Robustness: Error handling and validation
- Observability: Comprehensive logging and metrics
- Recoverability: Checkpoint support for long-running evolution
"""

import logging
import json
import time
import yaml
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from src.evolution.types import Strategy, Population, EvolutionResult, MultiObjectiveMetrics
from src.evolution.selection import SelectionManager
from src.evolution.crossover import CrossoverManager
from src.evolution.mutation import MutationManager
from src.evolution.multi_objective import assign_pareto_ranks, calculate_crowding_distance
from src.evolution.diversity import (
    calculate_population_diversity,
    calculate_novelty_score,
    extract_feature_set
)
from src.backtest.metrics import calculate_calmar_ratio, calculate_metrics
from src.backtest import BacktestResult, PerformanceMetrics
from src.evolution.visualization import plot_pareto_front, plot_diversity_over_time

# Task 1.6: Import exit mutation framework components
from src.mutation.exit_mutation_operator import ExitMutationOperator, MutationResult
from src.mutation.exit_mutator import MutationConfig

logger: logging.Logger = logging.getLogger(__name__)


class PopulationManager:
    """
    Central coordinator for NSGA-II population-based evolutionary optimization.

    Orchestrates the complete evolution workflow:
    1. Initialize diverse population
    2. Evaluate fitness (multi-objective metrics)
    3. Select parents (tournament selection with Pareto ranking)
    4. Generate offspring (crossover + mutation)
    5. Replace population (elitism + fitness-based selection)
    6. Monitor diversity and adapt parameters

    Attributes:
        population_size: Number of strategies in population (default: 20)
        elite_count: Number of elite strategies to preserve (default: 2)
        tournament_size: Tournament size for selection (default: 3)
        mutation_rate: Initial mutation rate (default: 0.1)
        current_population: Current generation population
        generation_history: List of EvolutionResult for each generation
    """

    def __init__(
        self,
        autonomous_loop: Optional[Any] = None,
        prompt_builder: Optional[Any] = None,
        code_validator: Optional[Any] = None,
        population_size: int = 20,
        elite_count: int = 2,
        tournament_size: int = 3,
        mutation_rate: float = 0.1,
        mutation_strength: float = 0.1,
        crossover_rate: float = 0.7,
        config_path: Optional[str] = None
    ):
        """
        Initialize PopulationManager with configuration.

        Args:
            autonomous_loop: Reference to autonomous loop for strategy evaluation
            prompt_builder: PromptBuilder for LLM code generation
            code_validator: CodeValidator for code validation
            population_size: Population size (default: 20)
            elite_count: Elite preservation count (default: 2)
            tournament_size: Tournament size (default: 3)
            mutation_rate: Mutation rate (default: 0.1)
            mutation_strength: Mutation strength (default: 0.1)
            crossover_rate: Crossover rate (default: 0.7)
            config_path: Path to learning_system.yaml (default: config/learning_system.yaml)
        """
        self.autonomous_loop = autonomous_loop
        self.prompt_builder = prompt_builder
        self.code_validator = code_validator

        self.population_size = population_size
        self.elite_count = elite_count
        self.tournament_size = tournament_size
        self.mutation_rate = mutation_rate
        self.mutation_strength = mutation_strength
        self.crossover_rate = crossover_rate

        # Initialize evolution components
        self.selection_manager = SelectionManager(
            tournament_size=tournament_size,
            elite_count=elite_count
        )

        self.crossover_manager = CrossoverManager(
            prompt_builder=prompt_builder,
            code_validator=code_validator,
            crossover_rate=crossover_rate
        ) if prompt_builder and code_validator else None

        self.mutation_manager = MutationManager(
            code_validator=code_validator,
            mutation_rate=mutation_rate,
            mutation_strength=mutation_strength
        ) if code_validator else None

        # Task 1.6: Initialize exit mutation operator
        self.exit_mutation_operator = ExitMutationOperator(max_retries=3)
        self._load_exit_mutation_config(config_path)

        # State tracking
        self.current_population: List[Strategy] = []
        self.generation_history: List[EvolutionResult] = []
        self.current_generation = 0

        # Task 1.6: Exit mutation statistics
        self.exit_mutation_stats = {
            'attempts': 0,
            'successes': 0,
            'failures': 0,
            'by_type': {'parametric': 0, 'structural': 0, 'relational': 0}
        }

        logger.info(
            f"PopulationManager initialized: population_size={population_size}, "
            f"elite_count={elite_count}, tournament_size={tournament_size}, "
            f"exit_mutation_enabled={self.exit_mutation_enabled}"
        )

    def _load_exit_mutation_config(self, config_path: Optional[str] = None) -> None:
        """
        Load exit mutation configuration from YAML file.

        Task 1.6: Load and parse exit mutation settings from learning_system.yaml

        Args:
            config_path: Path to config file (default: config/learning_system.yaml)
        """
        if config_path is None:
            config_path = "config/learning_system.yaml"

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            exit_config = config.get('exit_mutation', {})
            self.exit_mutation_enabled = exit_config.get('enabled', False)
            self.exit_mutation_probability = exit_config.get('exit_mutation_probability', 0.3)

            # Load mutation config
            mutation_config = exit_config.get('mutation_config', {})
            tier1_weight = mutation_config.get('tier1_weight', 0.5)
            tier2_weight = mutation_config.get('tier2_weight', 0.3)
            tier3_weight = mutation_config.get('tier3_weight', 0.2)

            # Load parameter ranges
            param_ranges = mutation_config.get('parameter_ranges', {})
            stop_loss_range = param_ranges.get('stop_loss_range', [0.8, 1.2])
            take_profit_range = param_ranges.get('take_profit_range', [0.9, 1.3])
            trailing_range = param_ranges.get('trailing_range', [0.85, 1.25])

            # Create MutationConfig (note: MutationConfig uses probability_weights, not tier_weights)
            self.exit_mutation_config = MutationConfig(
                probability_weights={
                    'parametric': tier1_weight,
                    'structural': tier2_weight,
                    'relational': tier3_weight
                },
                parameter_ranges={
                    'stop_loss': stop_loss_range,
                    'take_profit': take_profit_range,
                    'trailing': trailing_range
                }
            )

            # Load monitoring settings
            monitoring = exit_config.get('monitoring', {})
            self.exit_mutation_logging = monitoring.get('log_mutations', True)
            self.exit_mutation_track_types = monitoring.get('track_mutation_types', True)

            logger.info(
                f"Exit mutation config loaded: enabled={self.exit_mutation_enabled}, "
                f"probability={self.exit_mutation_probability}, "
                f"tier_weights=({tier1_weight}, {tier2_weight}, {tier3_weight})"
            )

        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self.exit_mutation_enabled = False
            self.exit_mutation_probability = 0.3
            self.exit_mutation_config = MutationConfig()
            self.exit_mutation_logging = True
            self.exit_mutation_track_types = True

        except Exception as e:
            logger.error(f"Error loading exit mutation config: {e}", exc_info=True)
            self.exit_mutation_enabled = False
            self.exit_mutation_probability = 0.3
            self.exit_mutation_config = MutationConfig()
            self.exit_mutation_logging = True
            self.exit_mutation_track_types = True

    def apply_exit_mutation(self, strategy: Strategy) -> Optional[Strategy]:
        """
        Apply exit strategy mutation to a strategy.

        Task 1.6: Integrate ExitMutationOperator into evolution workflow

        Workflow:
        1. Extract strategy code
        2. Apply mutation via ExitMutationOperator
        3. Create new Strategy with mutated code
        4. Log mutation result and update statistics

        Args:
            strategy: Original strategy to mutate

        Returns:
            Mutated strategy if successful, None if mutation fails
        """
        if not self.exit_mutation_enabled:
            return None

        # Update statistics
        self.exit_mutation_stats['attempts'] += 1

        try:
            # Apply mutation
            result: MutationResult = self.exit_mutation_operator.mutate_exit_strategy(
                code=strategy.code,
                config=self.exit_mutation_config
            )

            if result.success:
                # Create new strategy with mutated code
                mutated_strategy = Strategy(
                    id=f"{strategy.id}_exit_mutated",
                    generation=strategy.generation + 1,
                    parent_ids=[strategy.id],
                    code=result.code,
                    parameters=strategy.parameters,
                    template_type=strategy.template_type
                )

                # Update statistics
                self.exit_mutation_stats['successes'] += 1

                # Track mutation type if enabled
                if self.exit_mutation_track_types and result.profile:
                    for mechanism in result.profile.mechanisms:
                        # Infer type from mechanism (simplified)
                        if 'threshold' in mechanism.lower() or 'value' in mechanism.lower():
                            self.exit_mutation_stats['by_type']['parametric'] += 1
                        elif 'trailing' in mechanism.lower() or 'conditional' in mechanism.lower():
                            self.exit_mutation_stats['by_type']['structural'] += 1
                        else:
                            self.exit_mutation_stats['by_type']['relational'] += 1

                # Log success
                if self.exit_mutation_logging:
                    logger.info(
                        f"Exit mutation succeeded: {strategy.id[:8]} → {mutated_strategy.id[:8]}, "
                        f"mechanisms={result.profile.mechanisms if result.profile else 'unknown'}, "
                        f"attempts={result.attempts}"
                    )

                return mutated_strategy

            else:
                # Mutation failed
                self.exit_mutation_stats['failures'] += 1

                if self.exit_mutation_logging:
                    logger.warning(
                        f"Exit mutation failed for {strategy.id[:8]}: "
                        f"errors={result.errors}, attempts={result.attempts}"
                    )

                return None

        except Exception as e:
            self.exit_mutation_stats['failures'] += 1
            logger.error(f"Exception during exit mutation for {strategy.id[:8]}: {e}", exc_info=True)
            return None

    def initialize_population(
        self,
        template_types: Optional[List[str]] = None
    ) -> List[Strategy]:
        """
        Create initial diverse population using different templates.

        Args:
            template_types: List of template types to use (default: ['Momentum'])

        Returns:
            List of initialized strategies with evaluated metrics

        Note:
            This is a simplified implementation. Full version would use autonomous_loop
            to generate and evaluate strategies.
        """
        if template_types is None:
            template_types = ['Momentum']  # Only Momentum template is currently implemented

        logger.info(f"Initializing population of size {self.population_size}")

        population = []

        for i in range(self.population_size):
            # Cycle through templates for diversity
            template = template_types[i % len(template_types)]

            # Create strategy (placeholder - would use autonomous_loop in production)
            strategy = self._create_initial_strategy(i, template)
            population.append(strategy)

        logger.info(f"Created {len(population)} initial strategies")

        # Evaluate initial population
        evaluated_population = self.evaluate_population(population)

        self.current_population = evaluated_population
        self.current_generation = 0

        return evaluated_population

    def _create_initial_strategy(
        self,
        index: int,
        template_type: str
    ) -> Strategy:
        """Create initial strategy with diverse parameters matching template requirements."""
        # Generate diverse parameters matching MomentumTemplate PARAM_GRID
        # Use index to cycle through parameter options for diversity

        # MomentumTemplate PARAM_GRID (8 parameters required)
        momentum_periods = [5, 10, 20, 30]
        ma_periods_options = [20, 60, 90, 120]
        catalyst_types = ['revenue', 'earnings']
        catalyst_lookbacks = [2, 3, 4, 6]
        n_stocks_options = [5, 10, 15, 20]
        stop_loss_options = [0.08, 0.10, 0.12, 0.15]
        resample_options = ['W', 'M']
        resample_offset_options = [0, 1, 2, 3, 4]

        # Create diverse parameter combinations by cycling through options
        parameters = {
            'momentum_period': momentum_periods[index % len(momentum_periods)],
            'ma_periods': ma_periods_options[index % len(ma_periods_options)],
            'catalyst_type': catalyst_types[index % len(catalyst_types)],
            'catalyst_lookback': catalyst_lookbacks[index % len(catalyst_lookbacks)],
            'n_stocks': n_stocks_options[index % len(n_stocks_options)],
            'stop_loss': stop_loss_options[index % len(stop_loss_options)],
            'resample': resample_options[index % len(resample_options)],
            'resample_offset': resample_offset_options[index % len(resample_offset_options)]
        }

        # Generate placeholder code (actual strategy generation happens in template.generate_strategy)
        code_lines = [
            f"# Initial strategy {index} using {template_type} template",
            f"# Momentum period: {parameters['momentum_period']}",
            f"# MA periods: {parameters['ma_periods']}",
            f"# Catalyst: {parameters['catalyst_type']}",
            f"# Portfolio size: {parameters['n_stocks']} stocks",
            "",
            "# Placeholder code - actual strategy generated by template",
            f"close = data.get('price:收盤價')",
            f"momentum = close.pct_change({parameters['momentum_period']})",
            f"signal = momentum.rank(axis=1)"
        ]

        code = "\n".join(code_lines)

        return Strategy(
            id=f"init_{index}",
            generation=0,
            parent_ids=[],
            code=code,
            parameters=parameters,
            template_type=template_type
        )

    def evaluate_population(
        self,
        population: List[Strategy]
    ) -> List[Strategy]:
        """
        Evaluate population fitness with multi-objective metrics.

        For each strategy:
        1. Run backtest (via autonomous_loop)
        2. Extract multi-objective metrics
        3. Calculate Pareto ranks
        4. Calculate crowding distances
        5. Calculate novelty scores

        Args:
            population: List of strategies to evaluate

        Returns:
            List of strategies with updated fitness metrics
        """
        logger.info(f"Evaluating population of {len(population)} strategies")

        # Step 1: Evaluate each strategy (placeholder - would use autonomous_loop)
        for strategy in population:
            if strategy.metrics is None:
                strategy.metrics = self._evaluate_strategy(strategy)

        # Step 2: Calculate Pareto ranks
        ranks = assign_pareto_ranks(population)
        for strategy in population:
            strategy.pareto_rank = ranks.get(strategy.id, 999)

        # Step 3: Calculate crowding distances
        distances = calculate_crowding_distance(population)
        for strategy in population:
            strategy.crowding_distance = distances.get(strategy.id, 0.0)

        # Step 4: Calculate novelty scores
        # Adjust k based on population size (need at least k+1 strategies)
        k = min(5, max(1, len(population) - 1))

        for strategy in population:
            # Extract features from code
            features = extract_feature_set(strategy.code)
            # Calculate novelty with dynamic k
            strategy.novelty_score = calculate_novelty_score(strategy, population, k=k)

        logger.info(
            f"Evaluation complete: {len(population)} strategies evaluated, "
            f"Pareto ranks assigned, crowding distances calculated"
        )

        return population

    def _evaluate_strategy(self, strategy: Strategy) -> MultiObjectiveMetrics:
        """
        Evaluate single strategy using template's real finlab backtest.

        Workflow:
        1. Get template from registry based on strategy.template_type
        2. Run REAL backtest using template.generate_strategy()
        3. Extract metrics directly from finlab report (no fallback!)
        4. Map to MultiObjectiveMetrics with all 7 fields
        5. Handle missing metrics gracefully (default to 0.0)

        Args:
            strategy: Strategy to evaluate

        Returns:
            MultiObjectiveMetrics with extracted metrics

        Note:
            This now uses the template's actual finlab backtest instead of
            placeholder, ensuring consistent Sharpe calculations throughout.
        """
        try:
            # Step 1: Get template from registry (singleton pattern)
            from src.utils.template_registry import TemplateRegistry
            registry = TemplateRegistry.get_instance()

            # Validate template_type
            template_type = strategy.template_type if hasattr(strategy, 'template_type') else 'Momentum'
            if not registry.validate_template_type(template_type):
                logger.warning(f"Invalid template type '{template_type}', falling back to Momentum")
                template_type = 'Momentum'

            template = registry.get_template(template_type)

            # Step 2: Run REAL backtest using template (uses finlab internally)
            # This ensures consistent Sharpe calculation with initial population
            report, metadata = template.generate_strategy(strategy.parameters)

            # Step 3: Extract metrics directly from finlab report
            # NO FALLBACK - uses finlab's built-in calculations
            sharpe_ratio = report.metrics.sharpe_ratio()
            annual_return = report.metrics.annual_return()
            max_drawdown = report.metrics.max_drawdown()

            # Step 4: Calculate Calmar ratio
            calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0.0

            # Step 5: Use annual_return as total_return approximation
            # (Report object doesn't have equity_curve attribute)
            total_return = annual_return if annual_return is not None else 0.0

            # Step 6: Map to MultiObjectiveMetrics with graceful defaults
            return MultiObjectiveMetrics(
                sharpe_ratio=sharpe_ratio if sharpe_ratio is not None else 0.0,
                calmar_ratio=calmar if calmar is not None else 0.0,
                max_drawdown=max_drawdown if max_drawdown is not None else 0.0,
                total_return=total_return if total_return is not None else 0.0,
                win_rate=0.0,  # Could extract from trade_records if needed
                annual_return=annual_return if annual_return is not None else 0.0,
                success=True
            )

        except Exception as e:
            logger.warning(f"Backtest evaluation failed for strategy {strategy.id}: {e}", exc_info=True)
            # Return zero metrics on failure
            return MultiObjectiveMetrics(
                sharpe_ratio=0.0,
                calmar_ratio=0.0,
                max_drawdown=0.0,
                total_return=0.0,
                win_rate=0.0,
                annual_return=0.0,
                success=False
            )

    def _run_placeholder_backtest(self, strategy: Strategy) -> BacktestResult:
        """
        Placeholder backtest for testing integration.

        In production, this will be replaced with autonomous_loop.run_backtest().
        Returns synthetic BacktestResult with realistic structure.
        """
        import random
        import pandas as pd
        import numpy as np

        # Generate placeholder equity curve (100 days)
        days = 100
        daily_returns = np.random.normal(0.001, 0.02, days)  # 0.1% daily return, 2% volatility
        equity_curve = pd.Series((1 + daily_returns).cumprod(), name='equity')

        # Generate placeholder trade records
        trade_records = pd.DataFrame({
            'entry_date': pd.date_range('2024-01-01', periods=10),
            'exit_date': pd.date_range('2024-01-11', periods=10),
            'return': np.random.normal(0.02, 0.05, 10)  # 2% average return, 5% std
        })

        # Create BacktestResult
        return BacktestResult(
            portfolio_positions=pd.DataFrame(),  # Not used for metrics
            trade_records=trade_records,
            equity_curve=equity_curve,
            raw_result=None
        )

    def evolve_generation(
        self,
        generation_num: Optional[int] = None
    ) -> EvolutionResult:
        """
        Execute complete NSGA-II evolution generation.

        Workflow:
        1. Evaluate current population
        2. Select parents (tournament selection)
        3. Generate offspring (crossover + mutation)
        4. Replace population (elitism + fitness)
        5. Monitor diversity and adapt
        6. Log metrics and timing

        Args:
            generation_num: Generation number (auto-increment if None)

        Returns:
            EvolutionResult with complete statistics
        """
        if generation_num is None:
            generation_num = self.current_generation + 1

        logger.info(f"Evolving generation {generation_num}")

        start_time = time.time()
        timing = {}

        # Step 1: Evaluate population
        eval_start = time.time()
        evaluated_pop = self.evaluate_population(self.current_population)
        timing['evaluation'] = time.time() - eval_start

        # Step 2: Select parents
        select_start = time.time()
        num_offspring = self.population_size - self.elite_count
        parent_pairs = self.selection_manager.select_parents(evaluated_pop, num_offspring)
        timing['selection'] = time.time() - select_start

        # Step 3: Generate offspring (crossover + mutation + exit mutation)
        offspring_start = time.time()
        offspring = []
        for offspring_index, (parent1, parent2) in enumerate(parent_pairs):
            # Try crossover first
            child = None
            if self.crossover_manager:
                child = self.crossover_manager.crossover(parent1, parent2)

            # Task 1.6: Try exit mutation with configured probability
            # Apply exit mutation instead of parameter mutation based on probability
            if child is None and self.exit_mutation_enabled:
                # Decide whether to apply exit mutation or parameter mutation
                if random.random() < self.exit_mutation_probability:
                    # Apply exit mutation
                    child = self.apply_exit_mutation(parent1)
                    if child is not None and self.exit_mutation_logging:
                        logger.debug(
                            f"Applied exit mutation instead of parameter mutation "
                            f"for offspring from {parent1.id[:8]}"
                        )
                # Fallback to parameter mutation if exit mutation not selected or failed
                if child is None and self.mutation_manager:
                    child = self.mutation_manager.mutate(
                        parent1, self.prompt_builder
                    )
            elif child is None and self.mutation_manager:
                # Exit mutation disabled, use parameter mutation
                child = self.mutation_manager.mutate(
                    parent1, self.prompt_builder
                )

            # Placeholder offspring if both fail
            if child is None:
                child = self._create_offspring_placeholder(parent1, parent2, generation_num, offspring_index)

            if child:
                offspring.append(child)

        timing['offspring_generation'] = time.time() - offspring_start

        # Step 4: Replace population (elitism)
        replace_start = time.time()
        new_population = self.elitism_replacement(
            evaluated_pop, offspring, self.elite_count
        )
        timing['replacement'] = time.time() - replace_start

        # Step 5: Monitor and adapt diversity
        diversity_start = time.time()
        diversity_score = self.monitor_and_adapt_diversity(new_population)
        timing['diversity_monitoring'] = time.time() - diversity_start

        # Update state
        self.current_population = new_population
        self.current_generation = generation_num

        # Create result
        total_time = time.time() - start_time

        # Calculate average Sharpe for diversity metrics
        evaluated = [s for s in new_population if s.metrics]
        avg_sharpe = sum(s.metrics.sharpe_ratio for s in evaluated) / len(evaluated) if evaluated else 0.0

        result = EvolutionResult(
            generation=generation_num,
            population=Population(
                generation=generation_num,
                strategies=new_population,
                pareto_front=[s for s in new_population if s.pareto_rank == 1],
                diversity_metrics={
                    'diversity_score': diversity_score,
                    'avg_sharpe': avg_sharpe
                }
            ),
            elite_strategies=self.selection_manager.get_elite_strategies(evaluated_pop, self.elite_count),
            offspring_count=len(offspring),
            selection_time=timing['selection'],
            crossover_time=timing.get('crossover', 0.0),
            mutation_time=timing.get('mutation', 0.0),
            evaluation_time=timing['evaluation'],
            total_time=total_time,
            diversity_score=diversity_score,
            pareto_front_size=len([s for s in new_population if s.pareto_rank == 1])
        )

        self.generation_history.append(result)

        # Step 8: Generate progress visualizations
        try:
            # Plot Pareto front for this generation
            plot_pareto_front(
                population=new_population,
                generation=generation_num,
                output_path=f"plots/generation_{generation_num}_pareto.png"
            )

            # Plot diversity over time (cumulative)
            diversity_history = [r.diversity_score for r in self.generation_history]
            plot_diversity_over_time(
                diversity_history=diversity_history,
                output_path="plots/diversity.png"
            )
        except Exception as e:
            logger.warning(f"Visualization failed for generation {generation_num}: {e}")

        # Task 1.6: Log exit mutation statistics
        if self.exit_mutation_enabled and self.exit_mutation_stats['attempts'] > 0:
            success_rate = (
                self.exit_mutation_stats['successes'] / self.exit_mutation_stats['attempts']
                if self.exit_mutation_stats['attempts'] > 0 else 0.0
            )
            logger.info(
                f"Exit mutation stats: attempts={self.exit_mutation_stats['attempts']}, "
                f"successes={self.exit_mutation_stats['successes']}, "
                f"failures={self.exit_mutation_stats['failures']}, "
                f"success_rate={success_rate:.2%}"
            )

            if self.exit_mutation_track_types:
                logger.info(
                    f"Exit mutation types: "
                    f"parametric={self.exit_mutation_stats['by_type']['parametric']}, "
                    f"structural={self.exit_mutation_stats['by_type']['structural']}, "
                    f"relational={self.exit_mutation_stats['by_type']['relational']}"
                )

        logger.info(
            f"Generation {generation_num} complete: "
            f"diversity={diversity_score:.3f}, time={total_time:.2f}s"
        )

        return result

    def _create_offspring_placeholder(
        self,
        parent1: Strategy,
        parent2: Strategy,
        generation: int,
        offspring_index: int
    ) -> Strategy:
        """Create placeholder offspring when crossover/mutation fail."""
        return Strategy(
            id=f"gen{generation}_offspring_{offspring_index}",
            generation=generation,
            parent_ids=[parent1.id, parent2.id],
            code=f"# Offspring from {parent1.id[:8]} + {parent2.id[:8]}",
            parameters={**parent1.parameters}
        )

    def elitism_replacement(
        self,
        current_pop: List[Strategy],
        offspring: List[Strategy],
        elite_count: int
    ) -> List[Strategy]:
        """
        Form next generation with elitism preservation.

        Strategy:
        1. Preserve top elite_count strategies from current population
        2. Add all valid offspring
        3. Fill remaining slots with best strategies from current_pop
        4. Maintain population_size

        Args:
            current_pop: Current generation population
            offspring: Generated offspring
            elite_count: Number of elites to preserve

        Returns:
            Next generation population
        """
        # Get elite strategies
        elites = self.selection_manager.get_elite_strategies(current_pop, elite_count)

        # Combine elites and offspring
        combined = elites + offspring

        # If too many, keep best based on Pareto rank + crowding distance
        if len(combined) > self.population_size:
            combined.sort(
                key=lambda s: (s.pareto_rank, -s.crowding_distance)
            )
            new_population = combined[:self.population_size]
        elif len(combined) < self.population_size:
            # If too few, add best strategies from current_pop to fill up
            elite_ids = {s.id for s in elites}
            remaining = [s for s in current_pop if s.id not in elite_ids]
            remaining.sort(key=lambda s: (s.pareto_rank, -s.crowding_distance))

            # Add strategies until we reach population_size
            needed = self.population_size - len(combined)
            new_population = combined + remaining[:needed]
        else:
            new_population = combined

        logger.debug(
            f"Elitism replacement: {len(elites)} elites + "
            f"{len(offspring)} offspring → {len(new_population)} strategies"
        )

        return new_population

    def save_checkpoint(self, filepath: str) -> None:
        """
        Save population state to JSON checkpoint.

        Includes:
        - Current population
        - Generation history
        - Configuration parameters

        Args:
            filepath: Path to save checkpoint file
        """
        checkpoint = {
            'generation': self.current_generation,
            'population': [s.to_dict() for s in self.current_population],
            'generation_history': [
                {
                    'generation': r.generation,
                    'diversity_score': r.diversity_score,
                    'total_time': r.total_time,
                    'pareto_front_size': r.pareto_front_size
                }
                for r in self.generation_history
            ],
            'config': {
                'population_size': self.population_size,
                'elite_count': self.elite_count,
                'tournament_size': self.tournament_size,
                'mutation_rate': self.mutation_rate
            },
            'timestamp': datetime.now().isoformat()
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Checkpoint saved to {filepath}")

    def load_checkpoint(self, filepath: str) -> None:
        """
        Load population state from JSON checkpoint.

        Args:
            filepath: Path to checkpoint file

        Raises:
            FileNotFoundError: If checkpoint file not found
            ValueError: If checkpoint format invalid
        """
        with open(filepath, 'r') as f:
            checkpoint = json.load(f)

        self.current_generation = checkpoint['generation']

        # Restore population
        self.current_population = [
            Strategy.from_dict(s) for s in checkpoint['population']
        ]

        # Restore config
        config = checkpoint['config']
        self.population_size = config['population_size']
        self.elite_count = config['elite_count']
        self.tournament_size = config['tournament_size']
        self.mutation_rate = config['mutation_rate']

        logger.info(
            f"Checkpoint loaded from {filepath}: "
            f"generation={self.current_generation}, "
            f"population_size={len(self.current_population)}"
        )

    def monitor_and_adapt_diversity(
        self,
        population: List[Strategy]
    ) -> float:
        """
        Monitor diversity and adapt evolution parameters.

        Actions:
        - If diversity < 0.3: Increase mutation rate by 50%
        - If diversity < 0.2: Inject 2 random strategies

        Args:
            population: Current population

        Returns:
            Current diversity score
        """
        diversity = calculate_population_diversity(population)

        if diversity < 0.2:
            logger.warning(
                f"Severe diversity collapse: {diversity:.3f} < 0.2, "
                f"injecting random strategies"
            )
            # Inject 2 random strategies (would use autonomous_loop in production)
            # For now, just log the action
            self.mutation_rate = min(0.5, self.mutation_rate * 1.5)

        elif diversity < 0.3:
            logger.warning(
                f"Low diversity: {diversity:.3f} < 0.3, "
                f"increasing mutation rate"
            )
            self.mutation_rate = min(0.5, self.mutation_rate * 1.5)

        else:
            logger.debug(f"Diversity healthy: {diversity:.3f}")

        return diversity
