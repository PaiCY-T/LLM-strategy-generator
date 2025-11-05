"""
Population-Based Evolutionary Learning System
==============================================

Multi-objective evolutionary optimization framework using NSGA-II algorithms
for population-based strategy evolution with Pareto-optimal selection.

Purpose:
    Replace single-champion system with population-based learning to improve:
    - Champion update rate: 0.5% → 10-20% (20-40x improvement)
    - Rolling variance: 1.001 → <0.5 (50% reduction)
    - Statistical significance: p<0.05, Cohen's d ≥0.4

Core Algorithms:
    - NSGA-II Multi-Objective Optimization
    - Pareto Ranking and Crowding Distance
    - Tournament Selection with diversity pressure
    - Crossover operators (uniform, single-point, two-point)
    - Mutation operators (gaussian, parameter-based)
    - Diversity maintenance mechanisms

Population Structure:
    - Population size: N≈20 strategies per generation
    - Multi-objective fitness: Sharpe + Calmar + Max Drawdown
    - Pareto front preservation across generations
    - Diversity metrics: phenotypic distance, parameter variance

Evolution Workflow:
    1. Initialize population with diverse strategies
    2. Evaluate multi-objective fitness (Sharpe, Calmar, Drawdown)
    3. NSGA-II selection: Pareto ranking + crowding distance
    4. Genetic operators: crossover and mutation
    5. Diversity maintenance: crowding distance + novelty
    6. Champion update: select from Pareto front
    7. Archive management: preserve elite solutions

Components (To be implemented):
    - SelectionOperator: Tournament selection with Pareto ranking
    - CrossoverOperator: Uniform, single-point, two-point crossover
    - MutationOperator: Gaussian mutation, parameter-specific
    - DiversityManager: Phenotypic distance, crowding maintenance
    - MultiObjectiveOptimizer: NSGA-II coordination
    - PopulationEvolver: End-to-end evolution orchestration

Integration Points:
    - src.population: Population management and individual representation
    - src.backtest: Multi-objective fitness evaluation
    - src.repository: Champion and archive persistence
    - src.feedback: Template-based diversity and exploration
    - artifacts.working.modules.autonomous_loop: Main evolution loop

Expected Improvements:
    - Diversity: Phenotypic variance across population
    - Exploration: Novel parameter combinations through crossover
    - Exploitation: Pareto-optimal convergence
    - Robustness: Multiple champion candidates on Pareto front
    - Statistical significance: p<0.05 with effect size d≥0.4

Requirements Reference:
    - R8.1: Integration with autonomous loop
    - R8.2: Population initialization
    - R8.3: NSGA-II selection
    - R8.4: Crossover operators
    - R8.5: Mutation operators
    - R8.6: Diversity maintenance
    - R8.7: Multi-objective optimization
    - R8.8: Archive management

Usage (After implementation):
    from src.evolution import (
        SelectionOperator,
        CrossoverOperator,
        MutationOperator,
        DiversityManager,
        MultiObjectiveOptimizer,
        PopulationEvolver
    )
    from src.population import PopulationManager

    # Initialize evolution system
    evolver = PopulationEvolver(
        population_size=20,
        selection_pressure=2,
        crossover_rate=0.8,
        mutation_rate=0.2
    )

    # Evolve population
    next_generation = evolver.evolve(
        current_population=population,
        fitness_scores=multi_objective_scores
    )

    # Access Pareto front
    pareto_champions = evolver.get_pareto_front()

References:
    - Deb, K., et al. (2002). A fast and elitist multiobjective genetic algorithm: NSGA-II
    - Population-based training for deep reinforcement learning
    - Multi-objective optimization in trading strategy design
"""

from .types import MultiObjectiveMetrics, Strategy, Population, EvolutionResult
from .multi_objective import (
    pareto_dominates,
    calculate_pareto_front,
    assign_pareto_ranks,
    calculate_crowding_distance
)

__all__ = [
    'MultiObjectiveMetrics',
    'Strategy',
    'Population',
    'EvolutionResult',
    'pareto_dominates',
    'calculate_pareto_front',
    'assign_pareto_ranks',
    'calculate_crowding_distance',
]
