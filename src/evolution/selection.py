"""
Selection mechanisms for population-based evolutionary learning.

Provides tournament selection, diversity-aware selection, and elitism preservation
for multi-objective evolutionary algorithms. Implements NSGA-II selection operators
with extensions for maintaining population diversity.

Core Components:
    SelectionManager: Main selection orchestrator for parent selection and elitism
    tournament_selection: Random tournament with stochastic selection
    select_parents: Batch parent pair selection for crossover
    calculate_selection_probability: Fitness + novelty combined probability
    get_elite_strategies: Top performers for elitism preservation

Selection Strategies:
    - Tournament selection: Random tournament with selection pressure (default 80%)
    - Diversity-aware: Combines Pareto rank with novelty score
    - Elitism: Preserve top performers by Sharpe/Calmar ratio

References:
    - Deb, K., et al. (2002). "A fast and elitist multiobjective genetic algorithm: NSGA-II"
    - Goldberg, D. E., & Deb, K. (1991). "A comparative analysis of selection schemes"
"""

from typing import List, Tuple, Optional
import random
import logging
from .types import Strategy
from .multi_objective import calculate_pareto_front, calculate_crowding_distance
from .diversity import calculate_novelty_score

logger: logging.Logger = logging.getLogger(__name__)


class SelectionManager:
    """
    Selection manager for evolutionary algorithm parent selection and elitism.

    Orchestrates tournament selection, diversity-aware selection probability,
    and elitism preservation for multi-objective optimization. Supports both
    fitness-based and diversity-based selection strategies.

    Attributes:
        tournament_size: Number of strategies in each tournament (default: 3)
        selection_pressure: Probability of selecting tournament winner (default: 0.8)
        elite_count: Number of elite strategies to preserve (default: 2)
        diversity_weight: Weight for novelty in selection probability (default: 0.3)

    Example:
        >>> manager = SelectionManager(tournament_size=3, selection_pressure=0.8)
        >>> parent_pairs = manager.select_parents(population, count=10)
        >>> elite = manager.get_elite_strategies(population, elite_count=2)

    Example (Diversity-aware selection):
        >>> manager = SelectionManager(diversity_weight=0.5)
        >>> prob = manager.calculate_selection_probability(strategy, population)
        >>> # Higher probability for fit AND novel strategies

    Notes:
        - Tournament size typically 2-5 (larger = more selection pressure)
        - Selection pressure 0.8 means 80% best, 20% random
        - Elite count typically 1-5% of population size
        - Diversity weight balances exploration (high) vs exploitation (low)

    References:
        - Deb, K., et al. (2002). NSGA-II Section 3.3: "Selection Operator"
        - Miller, B. L., & Goldberg, D. E. (1995). "Genetic Algorithms, Tournament Selection"
    """

    def __init__(
        self,
        tournament_size: int = 3,
        selection_pressure: float = 0.8,
        elite_count: int = 2,
        diversity_weight: float = 0.3
    ):
        """
        Initialize SelectionManager with configurable parameters.

        Args:
            tournament_size: Number of strategies per tournament (2-5 recommended)
            selection_pressure: Probability of selecting best in tournament (0.0-1.0)
            elite_count: Number of elite strategies to preserve each generation
            diversity_weight: Weight for novelty in selection (0.0=fitness only, 1.0=novelty only)

        Raises:
            ValueError: If parameters are out of valid ranges

        Example:
            >>> manager = SelectionManager(
            ...     tournament_size=3,
            ...     selection_pressure=0.8,
            ...     elite_count=2,
            ...     diversity_weight=0.3
            ... )
        """
        if tournament_size < 2:
            raise ValueError(f"tournament_size must be at least 2, got {tournament_size}")
        if not 0.0 <= selection_pressure <= 1.0:
            raise ValueError(f"selection_pressure must be in [0.0, 1.0], got {selection_pressure}")
        if elite_count < 0:
            raise ValueError(f"elite_count must be non-negative, got {elite_count}")
        if not 0.0 <= diversity_weight <= 1.0:
            raise ValueError(f"diversity_weight must be in [0.0, 1.0], got {diversity_weight}")

        self.tournament_size = tournament_size
        self.selection_pressure = selection_pressure
        self.elite_count = elite_count
        self.diversity_weight = diversity_weight

        logger.info(
            f"Initialized SelectionManager: tournament_size={tournament_size}, "
            f"selection_pressure={selection_pressure}, elite_count={elite_count}, "
            f"diversity_weight={diversity_weight}"
        )

    def tournament_selection(
        self,
        population: List[Strategy],
        tournament_size: Optional[int] = None,
        selection_pressure: Optional[float] = None
    ) -> Strategy:
        """
        Select single strategy via tournament selection with stochastic winner choice.

        Tournament selection randomly samples tournament_size strategies, sorts them
        by fitness (Pareto rank, then crowding distance), and stochastically selects
        the winner based on selection_pressure. This balances selection pressure with
        diversity preservation.

        Selection Logic:
            1. Random sample tournament_size strategies
            2. Calculate Pareto ranks for tournament participants
            3. Calculate crowding distances for tie-breaking
            4. Sort by: Pareto rank (ascending), crowding distance (descending)
            5. Select best with probability selection_pressure, otherwise random

        Args:
            population: List of Strategy instances to select from
            tournament_size: Size of tournament (uses self.tournament_size if None)
            selection_pressure: Selection pressure (uses self.selection_pressure if None)

        Returns:
            Strategy: Selected strategy from tournament

        Raises:
            ValueError: If population size < tournament_size

        Example (High selection pressure):
            >>> manager = SelectionManager(tournament_size=3, selection_pressure=0.9)
            >>> winner = manager.tournament_selection(population)
            >>> # 90% chance of selecting best, 10% random

        Example (Low selection pressure - more diversity):
            >>> manager = SelectionManager(tournament_size=3, selection_pressure=0.5)
            >>> winner = manager.tournament_selection(population)
            >>> # 50% chance of selecting best, 50% random

        Notes:
            - Tournament size affects selection pressure (larger = stronger pressure)
            - Selection pressure 0.8 is typical for NSGA-II
            - Random selection (20%) maintains diversity and prevents premature convergence
            - Tournament participants are sampled without replacement

        Complexity:
            - Time: O(T log T) where T = tournament_size
            - Space: O(T) for tournament participants

        References:
            - Miller, B. L., & Goldberg, D. E. (1995). "Genetic Algorithms, Tournament Selection"
            - Typical tournament size: 2-5 strategies
        """
        # Use instance defaults if parameters not provided
        if tournament_size is None:
            tournament_size = self.tournament_size
        if selection_pressure is None:
            selection_pressure = self.selection_pressure

        # Validation: ensure population is large enough for tournament
        if len(population) < tournament_size:
            raise ValueError(
                f"Population size ({len(population)}) must be >= tournament_size ({tournament_size})"
            )

        # Step 1: Random sample tournament participants (without replacement)
        tournament = random.sample(population, tournament_size)

        # Step 2: Calculate Pareto front for tournament
        pareto_front = calculate_pareto_front(tournament)

        # Create rank mapping: strategy -> pareto_rank (0 for front, 1 for dominated)
        rank_map = {}
        for strategy in pareto_front:
            rank_map[strategy.id] = 0  # Non-dominated (Pareto front)
        for strategy in tournament:
            if strategy.id not in rank_map:
                rank_map[strategy.id] = 1  # Dominated

        # Step 3: Calculate crowding distances for tie-breaking
        # Only calculate for strategies with same rank
        crowding_map = {}

        # For Pareto front strategies (rank 0)
        if len(pareto_front) > 1:
            distances = calculate_crowding_distance(pareto_front)
            crowding_map.update(distances)
        elif len(pareto_front) == 1:
            crowding_map[pareto_front[0].id] = float('inf')

        # For dominated strategies (rank 1), assign 0 crowding distance
        for strategy in tournament:
            if strategy.id not in crowding_map:
                crowding_map[strategy.id] = 0.0

        # Step 4: Sort tournament by Pareto rank (ascending), then crowding distance (descending)
        sorted_tournament = sorted(
            tournament,
            key=lambda s: (rank_map[s.id], -crowding_map[s.id])
        )

        # Step 5: Stochastic selection
        if random.random() < selection_pressure:
            # Select best (lowest Pareto rank, highest crowding distance)
            selected = sorted_tournament[0]
            logger.debug(
                f"Tournament selection: selected best (rank={rank_map[selected.id]}, "
                f"crowding={crowding_map[selected.id]:.4f})"
            )
        else:
            # Random selection from tournament for diversity
            selected = random.choice(sorted_tournament)
            logger.debug(
                f"Tournament selection: random selection for diversity "
                f"(rank={rank_map[selected.id]}, crowding={crowding_map[selected.id]:.4f})"
            )

        return selected

    def select_parents(
        self,
        population: List[Strategy],
        count: int
    ) -> List[Tuple[Strategy, Strategy]]:
        """
        Select multiple parent pairs for crossover operations.

        Performs batch parent selection by running tournament_selection twice
        per pair. Ensures each pair consists of unique parents (no self-pairing)
        to maintain genetic diversity in offspring.

        Args:
            population: List of Strategy instances to select from
            count: Number of parent pairs to select

        Returns:
            List[Tuple[Strategy, Strategy]]: List of parent pairs

        Raises:
            ValueError: If population size < 2 (cannot create unique pairs)

        Example:
            >>> manager = SelectionManager()
            >>> parent_pairs = manager.select_parents(population, count=10)
            >>> len(parent_pairs)
            10
            >>> parent_pairs[0][0].id != parent_pairs[0][1].id  # Unique parents
            True

        Example (Iterate over pairs for crossover):
            >>> parent_pairs = manager.select_parents(population, count=20)
            >>> for parent1, parent2 in parent_pairs:
            ...     offspring = crossover(parent1, parent2)

        Notes:
            - Each tournament_selection call is independent (parents can repeat across pairs)
            - Within-pair uniqueness enforced to avoid self-pairing
            - Count typically matches desired number of offspring
            - Uses instance tournament_size and selection_pressure

        Complexity:
            - Time: O(count * T log T) where T = tournament_size
            - Space: O(count) for parent pairs

        References:
            - Deb, K., et al. (2002). NSGA-II Section 3: "Mating Selection"
        """
        # Validation: need at least 2 strategies to create unique pairs
        if len(population) < 2:
            raise ValueError(
                f"Population size must be at least 2 to select unique pairs, got {len(population)}"
            )

        parent_pairs = []

        for _ in range(count):
            # Select first parent via tournament
            parent1 = self.tournament_selection(population)

            # Select second parent, ensuring uniqueness
            max_attempts = 100  # Prevent infinite loop
            attempts = 0
            while attempts < max_attempts:
                parent2 = self.tournament_selection(population)
                if parent2.id != parent1.id:
                    break
                attempts += 1

            if attempts >= max_attempts:
                # Fallback: select random different strategy
                available = [s for s in population if s.id != parent1.id]
                parent2 = random.choice(available)
                logger.warning(
                    f"Failed to select unique parent via tournament after {max_attempts} attempts. "
                    "Using random selection."
                )

            parent_pairs.append((parent1, parent2))

        logger.info(f"Selected {count} parent pairs for crossover")
        return parent_pairs

    def calculate_selection_probability(
        self,
        strategy: Strategy,
        population: List[Strategy]
    ) -> float:
        """
        Calculate diversity-aware selection probability combining fitness and novelty.

        Combines fitness (Pareto rank) with novelty (average distance to neighbors)
        to balance exploitation (selecting fit strategies) with exploration
        (selecting novel strategies). This prevents premature convergence.

        Formula:
            prob ∝ (1 / (pareto_rank + 1)) * (1 + diversity_weight * novelty_score)

        Where:
            - pareto_rank: 0 for non-dominated front, 1 for second front, etc.
            - novelty_score: Average Jaccard distance to k-nearest neighbors
            - diversity_weight: Balance between fitness (0.0) and novelty (1.0)

        Args:
            strategy: Strategy to calculate probability for
            population: Full population for Pareto rank and novelty calculation

        Returns:
            float: Unnormalized selection probability (higher = more likely)

        Example (High fitness, low novelty):
            >>> manager = SelectionManager(diversity_weight=0.3)
            >>> prob = manager.calculate_selection_probability(best_strategy, population)
            >>> # High probability due to fitness, slightly reduced by low novelty

        Example (Medium fitness, high novelty):
            >>> prob = manager.calculate_selection_probability(novel_strategy, population)
            >>> # Boosted probability due to high novelty despite medium fitness

        Notes:
            - Returns unnormalized probability (caller must normalize across population)
            - diversity_weight=0.0 → pure fitness-based selection
            - diversity_weight=1.0 → equal weight for fitness and novelty
            - Pareto rank 0 (non-dominated) gets highest fitness contribution
            - Novelty score uses k=5 nearest neighbors by default

        Typical Usage:
            >>> probs = [manager.calculate_selection_probability(s, pop) for s in pop]
            >>> normalized_probs = [p / sum(probs) for p in probs]
            >>> selected = random.choices(pop, weights=normalized_probs, k=10)

        Complexity:
            - Time: O(N² * F) for novelty calculation (N=population size, F=features)
            - Space: O(N) for distance calculations

        References:
            - Lehman, J., & Stanley, K. O. (2011). "Abandoning Objectives"
            - Typical diversity_weight: 0.2-0.4 for balanced exploration/exploitation
        """
        # Check if strategy is in population
        if strategy.id not in [s.id for s in population]:
            logger.warning(f"Strategy {strategy.id} not found in population for selection probability")
            return 0.0

        # Calculate Pareto rank (0 for non-dominated, 1 for dominated)
        pareto_front = calculate_pareto_front(population)
        pareto_rank = 1  # Default: dominated
        if strategy.id in [s.id for s in pareto_front]:
            pareto_rank = 0  # Non-dominated

        # Calculate novelty score
        try:
            novelty_score = calculate_novelty_score(
                strategy,
                population,
                k=min(5, len(population) - 1)  # Use k=5 or population_size-1, whichever is smaller
            )
        except ValueError as e:
            logger.warning(f"Failed to calculate novelty score: {e}. Using novelty=0.0")
            novelty_score = 0.0

        # Combine fitness and novelty
        # Fitness component: 1 / (pareto_rank + 1) - higher for lower ranks
        fitness_component = 1.0 / (pareto_rank + 1)

        # Novelty component: 1 + diversity_weight * novelty_score
        # diversity_weight=0 → no novelty bonus
        # diversity_weight=1 → full novelty bonus
        novelty_component = 1.0 + self.diversity_weight * novelty_score

        # Combined probability (unnormalized)
        probability = fitness_component * novelty_component

        logger.debug(
            f"Selection probability for strategy {strategy.id}: "
            f"pareto_rank={pareto_rank}, novelty={novelty_score:.4f}, "
            f"fitness_comp={fitness_component:.4f}, novelty_comp={novelty_component:.4f}, "
            f"prob={probability:.4f}"
        )

        return probability

    def get_elite_strategies(
        self,
        population: List[Strategy],
        elite_count: Optional[int] = None
    ) -> List[Strategy]:
        """
        Identify top-performing strategies for elitism preservation.

        Selects the best strategies based on Sharpe ratio (primary) and
        Calmar ratio (secondary) to preserve high-quality solutions across
        generations. Elitism ensures best solutions are never lost.

        Sorting Criteria:
            1. Sharpe ratio (descending) - risk-adjusted returns
            2. Calmar ratio (descending) - downside risk-adjusted returns

        Args:
            population: List of Strategy instances to select from
            elite_count: Number of elite strategies (uses self.elite_count if None)

        Returns:
            List[Strategy]: Top elite_count strategies

        Raises:
            ValueError: If elite_count > population size

        Example:
            >>> manager = SelectionManager(elite_count=2)
            >>> elite = manager.get_elite_strategies(population)
            >>> len(elite)
            2
            >>> # elite[0] has highest Sharpe ratio

        Example (Preserve elite to next generation):
            >>> elite = manager.get_elite_strategies(population, elite_count=3)
            >>> next_generation = elite + offspring[:population_size - 3]

        Notes:
            - Elite count typically 1-5% of population size
            - Sharpe ratio = mean_return / std_return (higher is better)
            - Calmar ratio = mean_return / max_drawdown (higher is better)
            - Strategies must have metrics.sharpe_ratio and metrics.calmar_ratio
            - Returns empty list if elite_count = 0

        Typical Elite Counts:
            - Population 20: elite_count=1-2 (5-10%)
            - Population 50: elite_count=2-3 (4-6%)
            - Population 100: elite_count=3-5 (3-5%)

        Complexity:
            - Time: O(N log N) for sorting
            - Space: O(N) for sorted copy

        References:
            - De Jong, K. A. (1975). "Elitism in Genetic Algorithms"
            - Deb, K., et al. (2002). NSGA-II Section 2.3: "Elitism"
        """
        # Use instance default if parameter not provided
        if elite_count is None:
            elite_count = self.elite_count

        # Validation
        if elite_count > len(population):
            raise ValueError(
                f"elite_count ({elite_count}) cannot exceed population size ({len(population)})"
            )

        if elite_count == 0:
            return []

        # Sort by Sharpe ratio (primary), Calmar ratio (secondary) - both descending
        # None metrics sort last (use float('inf') for descending sort with negation)
        sorted_population = sorted(
            population,
            key=lambda s: (
                -s.metrics.sharpe_ratio if s.metrics.sharpe_ratio is not None else float('inf'),
                -s.metrics.calmar_ratio if s.metrics.calmar_ratio is not None else float('inf')
            )
        )

        # Select top elite_count strategies
        elite_strategies = sorted_population[:elite_count]

        # Log elite strategies (handle None metrics gracefully)
        sharpe_str = ', '.join(
            f'{s.metrics.sharpe_ratio:.4f}' if s.metrics.sharpe_ratio is not None else 'None'
            for s in elite_strategies
        )
        logger.info(
            f"Selected {elite_count} elite strategies: "
            f"Sharpe ratios=[{sharpe_str}]"
        )

        return elite_strategies
