"""
Smart Mutation Engine Usage Example

Demonstrates how to use the SmartMutationEngine for intelligent
operator selection and adaptive scheduling during evolution.

Task: C.5 - Smart Mutation Operators and Scheduling
"""

import numpy as np
from src.mutation.tier2 import (
    SmartMutationEngine,
    MutationScheduler,
    ParameterMutator
)


def main():
    """Demonstrate SmartMutationEngine usage."""

    print("=" * 70)
    print("Smart Mutation Engine - Usage Example")
    print("=" * 70)
    print()

    # ========================================================================
    # 1. Setup Mutation Operators
    # ========================================================================
    print("1. Setting up mutation operators...")
    print("-" * 70)

    # For now, we only have ParameterMutator implemented
    # Future operators: AddFactorMutator, RemoveFactorMutator, ReplaceFactorMutator
    operators = {
        "mutate_parameters": ParameterMutator(),
        # "add_factor": AddFactorMutator(),        # TODO: C.1
        # "remove_factor": RemoveFactorMutator(),  # TODO: C.2
        # "replace_factor": ReplaceFactorMutator() # TODO: C.3
    }

    print(f"Available operators: {list(operators.keys())}")
    print()

    # ========================================================================
    # 2. Configure Smart Mutation Engine
    # ========================================================================
    print("2. Configuring smart mutation engine...")
    print("-" * 70)

    config = {
        "initial_probabilities": {
            "mutate_parameters": 1.0  # Only operator available
        },
        "schedule": {
            "max_generations": 100,
            "early_rate": 0.7,      # High mutation early (exploration)
            "mid_rate": 0.4,        # Medium mutation mid (balanced)
            "late_rate": 0.2,       # Low mutation late (exploitation)
            "diversity_threshold": 0.3,
            "diversity_boost": 0.2
        },
        "adaptation": {
            "enable": True,
            "success_rate_weight": 0.3,
            "min_probability": 0.05,
            "update_interval": 5
        }
    }

    print("Configuration:")
    print(f"  Max generations: {config['schedule']['max_generations']}")
    print(f"  Early rate: {config['schedule']['early_rate']}")
    print(f"  Mid rate: {config['schedule']['mid_rate']}")
    print(f"  Late rate: {config['schedule']['late_rate']}")
    print(f"  Diversity boost: {config['schedule']['diversity_boost']}")
    print(f"  Adaptation enabled: {config['adaptation']['enable']}")
    print()

    # ========================================================================
    # 3. Initialize Engine
    # ========================================================================
    print("3. Initializing smart mutation engine...")
    print("-" * 70)

    engine = SmartMutationEngine(operators, config)

    print(f"Engine initialized with {len(operators)} operator(s)")
    print(f"Scheduler max generations: {engine.scheduler.max_generations}")
    print()

    # ========================================================================
    # 4. Simulate Evolution Across Generations
    # ========================================================================
    print("4. Simulating evolution across generations...")
    print("-" * 70)

    # Simulate 100 generations
    np.random.seed(42)  # For reproducibility

    generation_samples = [0, 10, 25, 50, 75, 90, 99]

    for generation in generation_samples:
        # Simulate varying diversity (high early, low late)
        diversity = 0.8 - (generation / 100) * 0.6

        # Simulate stagnation (increases over time)
        stagnation_count = max(0, generation - 50)

        # Get adaptive mutation rate
        mutation_rate = engine.scheduler.get_mutation_rate(
            generation=generation,
            diversity=diversity,
            stagnation_count=stagnation_count
        )

        # Get operator selection probabilities
        success_rates = engine.stats.get_all_rates()
        operator_probs = engine.scheduler.get_operator_probabilities(
            generation=generation,
            max_generations=100,
            success_rates=success_rates
        )

        print(f"\nGeneration {generation:3d}:")
        print(f"  Diversity: {diversity:.2f}")
        print(f"  Stagnation: {stagnation_count:2d}")
        print(f"  Mutation rate: {mutation_rate:.2f}")
        print(f"  Operator probabilities: {operator_probs}")

        # Select operator based on context
        context = {
            "generation": generation,
            "diversity": diversity,
            "population_size": 20
        }

        operator_name, operator = engine.select_operator(context)
        print(f"  Selected: {operator_name}")

        # Simulate mutation success (70% success rate)
        success = np.random.random() < 0.7
        engine.update_success_rate(operator_name, success)

    print()

    # ========================================================================
    # 5. Review Statistics
    # ========================================================================
    print("5. Reviewing mutation statistics...")
    print("-" * 70)

    stats = engine.get_statistics()

    print(f"\nTotal mutations attempted: {stats['total_attempts']}")
    print(f"Total successful mutations: {stats['total_successes']}")
    print(f"Overall success rate: {stats['total_successes'] / max(1, stats['total_attempts']):.2%}")

    print("\nPer-operator statistics:")
    for operator_name in operators.keys():
        attempts = stats['operator_attempts'].get(operator_name, 0)
        successes = stats['operator_successes'].get(operator_name, 0)
        success_rate = stats['operator_success_rates'].get(operator_name, 0.0)

        print(f"  {operator_name}:")
        print(f"    Attempts: {attempts}")
        print(f"    Successes: {successes}")
        print(f"    Success rate: {success_rate:.2%}")

    print()

    # ========================================================================
    # 6. Demonstrate Mutation Rate Scheduling
    # ========================================================================
    print("6. Mutation rate scheduling across generations...")
    print("-" * 70)

    print("\nMutation rates by generation phase:")
    rates = []
    for gen in range(0, 100, 10):
        rate = engine.scheduler.get_mutation_rate(
            generation=gen,
            diversity=0.5,  # Constant diversity
            stagnation_count=0  # No stagnation
        )
        rates.append(rate)
        phase = "Early" if gen < 20 else ("Mid" if gen < 70 else "Late")
        print(f"  Gen {gen:3d} ({phase:5s}): {rate:.2f}")

    print(f"\nAverage early rate (0-20): {np.mean(rates[:2]):.2f}")
    print(f"Average mid rate (20-70): {np.mean(rates[2:7]):.2f}")
    print(f"Average late rate (70-100): {np.mean(rates[7:]):.2f}")

    print()
    print("=" * 70)
    print("Example complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
