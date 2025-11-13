"""Example usage of DiversityMonitor for population-based learning systems.

This example demonstrates how to integrate DiversityMonitor into an evolutionary
learning loop to track population diversity and detect diversity collapse.

Requirements: Task 2 - DiversityMonitor usage example
"""

from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.diversity_monitor import DiversityMonitor


def main():
    """Example evolutionary loop with diversity monitoring."""

    # Initialize metrics collector and diversity monitor
    metrics_collector = MetricsCollector()
    diversity_monitor = DiversityMonitor(
        metrics_collector=metrics_collector,
        collapse_threshold=0.1,
        collapse_window=5
    )

    print("=" * 70)
    print("DiversityMonitor Example - Evolutionary Learning Loop")
    print("=" * 70)

    # Simulate an evolutionary learning loop
    population_size = 50
    last_champion_update = 0

    # Example 1: Normal evolution with healthy diversity
    print("\n[Example 1: Healthy Diversity Evolution]")
    print("-" * 70)

    for iteration in range(10):
        # Simulate population diversity (healthy range: 0.5-0.9)
        diversity = 0.8 - (iteration * 0.02)  # Slowly decreasing
        unique_count = int(population_size * diversity)

        # Record diversity metrics
        diversity_monitor.record_diversity(
            iteration=iteration,
            diversity=diversity,
            unique_count=unique_count,
            total_count=population_size
        )

        # Simulate champion update every 3 iterations
        if iteration > 0 and iteration % 3 == 0:
            old_sharpe = 1.5 + (last_champion_update * 0.1)
            new_sharpe = 1.5 + (iteration * 0.1)
            diversity_monitor.record_champion_update(
                iteration=iteration,
                old_sharpe=old_sharpe,
                new_sharpe=new_sharpe
            )
            last_champion_update = iteration

        # Calculate and display staleness
        if last_champion_update > 0:
            staleness = diversity_monitor.calculate_staleness(
                current_iteration=iteration
            )
            status = diversity_monitor.get_status()

            print(f"Iteration {iteration}: "
                  f"Diversity={diversity:.3f}, "
                  f"Unique={unique_count}/{population_size}, "
                  f"Staleness={staleness} iterations")
        else:
            print(f"Iteration {iteration}: "
                  f"Diversity={diversity:.3f}, "
                  f"Unique={unique_count}/{population_size}, "
                  f"(No champion yet)")

        # Check for diversity collapse
        if diversity_monitor.check_diversity_collapse():
            print(f"  ⚠️  WARNING: Diversity collapse detected!")

    # Example 2: Diversity collapse scenario
    print("\n[Example 2: Diversity Collapse Scenario]")
    print("-" * 70)

    diversity_monitor.reset()  # Reset for new example

    for iteration in range(10):
        # Simulate diversity collapse (all values below threshold)
        if iteration < 5:
            diversity = 0.05  # Very low diversity
            unique_count = 2
        else:
            # Recovery after collapse
            diversity = 0.6 + (iteration - 5) * 0.05
            unique_count = int(population_size * diversity)

        diversity_monitor.record_diversity(
            iteration=iteration,
            diversity=diversity,
            unique_count=unique_count,
            total_count=population_size
        )

        is_collapsed = diversity_monitor.check_diversity_collapse()

        collapse_indicator = "🔴" if is_collapsed else "🟢"
        print(f"Iteration {iteration}: "
              f"{collapse_indicator} "
              f"Diversity={diversity:.3f}, "
              f"Unique={unique_count}/{population_size}, "
              f"Collapse={'YES' if is_collapsed else 'NO'}")

    # Display final status
    print("\n[Final Status]")
    print("-" * 70)
    status = diversity_monitor.get_status()

    print(f"Current Diversity: {status['current_diversity']:.3f}")
    print(f"Unique Count: {status['unique_count']}/{status['total_count']}")
    print(f"Champion Staleness: {status['staleness']} iterations")
    print(f"Diversity History Length: {status['diversity_history_length']}")
    print(f"Collapse Detected: {status['collapse_detected']}")

    if status['collapse_detected']:
        print(f"Collapse First Detected at Iteration: {status['collapse_iteration']}")

    print(f"\nDiversity History (last {status['collapse_window']} values):")
    print(f"  {[f'{d:.3f}' for d in diversity_monitor.get_diversity_history()]}")

    # Example 3: Demonstrate staleness tracking
    print("\n[Example 3: Champion Staleness Tracking]")
    print("-" * 70)

    diversity_monitor.reset()

    # Record initial champion update
    diversity_monitor.record_champion_update(
        iteration=0,
        old_sharpe=1.5,
        new_sharpe=1.8
    )

    # Simulate iterations without champion update
    for iteration in range(1, 25):
        staleness = diversity_monitor.calculate_staleness(current_iteration=iteration)

        staleness_indicator = "⚠️ " if staleness >= 20 else "✓ "
        print(f"Iteration {iteration}: "
              f"{staleness_indicator}"
              f"Champion staleness = {staleness} iterations "
              f"{'(ALERT!)' if staleness >= 20 else ''}")

        # Simulate champion update at iteration 15
        if iteration == 15:
            diversity_monitor.record_champion_update(
                iteration=iteration,
                old_sharpe=1.8,
                new_sharpe=2.1
            )
            print(f"  → Champion UPDATED! (1.8 → 2.1)")

    print("\n" + "=" * 70)
    print("DiversityMonitor Example Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
