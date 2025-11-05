#!/usr/bin/env python3
"""
Command-line interface for running population-based evolution.

Usage:
    python run_population_evolution.py --generations 10
    python run_population_evolution.py --population-size 30 --generations 20 --checkpoint-dir checkpoints

Provides:
- Configurable population size and generation count
- Progress display with real-time metrics
- Checkpoint saving for recovery
- Final statistics summary

Requirements: R11.1 (Usability), R11.2 (Reproducibility)
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from src.evolution.population_manager import PopulationManager
from src.evolution.visualization import (
    plot_diversity_over_time,
    plot_pareto_front
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('population_evolution.log')
    ]
)
logger = logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Run population-based evolution for trading strategy generation',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--population-size',
        type=int,
        default=20,
        help='Population size (number of strategies)'
    )

    parser.add_argument(
        '--generations',
        type=int,
        default=10,
        help='Number of generations to evolve'
    )

    parser.add_argument(
        '--elite-count',
        type=int,
        default=2,
        help='Number of elite strategies to preserve'
    )

    parser.add_argument(
        '--tournament-size',
        type=int,
        default=3,
        help='Tournament size for parent selection'
    )

    parser.add_argument(
        '--mutation-rate',
        type=float,
        default=0.1,
        help='Initial mutation rate (0.0-1.0)'
    )

    parser.add_argument(
        '--checkpoint-dir',
        type=str,
        default='checkpoints',
        help='Directory for saving checkpoints'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='evolution_output',
        help='Directory for saving results and plots'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )

    return parser.parse_args()


def display_banner():
    """Display welcome banner."""
    banner = """
╔════════════════════════════════════════════════════════════╗
║       Population-Based Strategy Evolution System           ║
║                  NSGA-II Multi-Objective                   ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)


def display_progress(
    generation: int,
    total_generations: int,
    result
):
    """
    Display generation progress with key metrics.

    Args:
        generation: Current generation number
        total_generations: Total generations to run
        result: EvolutionResult from this generation
    """
    percent = (generation / total_generations) * 100

    print(f"\n{'='*70}")
    print(f"GENERATION {generation}/{total_generations} ({percent:.1f}% complete)")
    print(f"{'='*70}")

    # Population metrics
    print(f"Population Size:     {result.population.size}")
    print(f"Offspring Created:   {result.offspring_count}")
    print(f"Diversity Score:     {result.diversity_score:.3f}")

    # Pareto front
    pareto_front = [s for s in result.population.strategies if s.pareto_rank == 1]
    print(f"Pareto Front Size:   {len(pareto_front)}")

    # Best metrics
    best_sharpe = max(
        (s.metrics.sharpe_ratio for s in result.population.strategies if s.metrics and s.metrics.success),
        default=0.0
    )
    best_calmar = max(
        (s.metrics.calmar_ratio for s in result.population.strategies if s.metrics and s.metrics.success and s.metrics.calmar_ratio),
        default=0.0
    )

    print(f"Best Sharpe Ratio:   {best_sharpe:.3f}")
    print(f"Best Calmar Ratio:   {best_calmar:.3f}")

    # Timing
    print(f"\nTiming Breakdown:")
    print(f"  Selection:  {result.selection_time:.2f}s")
    print(f"  Crossover:  {result.crossover_time:.2f}s")
    print(f"  Mutation:   {result.mutation_time:.2f}s")
    print(f"  Evaluation: {result.evaluation_time:.2f}s")
    print(f"  Total:      {result.total_time:.2f}s")


def display_final_summary(manager: PopulationManager, output_dir: Path):
    """
    Display final evolution summary.

    Args:
        manager: PopulationManager instance
        output_dir: Output directory for results
    """
    print(f"\n{'='*70}")
    print(f"EVOLUTION COMPLETE")
    print(f"{'='*70}")

    # Generation history
    print(f"\nTotal Generations:   {len(manager.generation_history)}")

    # Diversity trend
    diversity_history = [r.diversity_score for r in manager.generation_history]
    avg_diversity = sum(diversity_history) / len(diversity_history) if diversity_history else 0.0
    print(f"Average Diversity:   {avg_diversity:.3f}")

    # Best strategies
    final_population = manager.current_population
    strategies_with_metrics = [s for s in final_population if s.metrics and s.metrics.success]

    if strategies_with_metrics:
        best_sharpe_strategy = max(strategies_with_metrics, key=lambda s: s.metrics.sharpe_ratio)
        print(f"\nBest Strategy (Sharpe):")
        print(f"  ID:          {best_sharpe_strategy.id}")
        print(f"  Generation:  {best_sharpe_strategy.generation}")
        print(f"  Sharpe:      {best_sharpe_strategy.metrics.sharpe_ratio:.3f}")
        print(f"  Calmar:      {best_sharpe_strategy.metrics.calmar_ratio:.3f}" if best_sharpe_strategy.metrics.calmar_ratio else "  Calmar:      N/A")
        print(f"  Max DD:      {best_sharpe_strategy.metrics.max_drawdown:.3f}")

    # Pareto front
    pareto_front = [s for s in final_population if hasattr(s, 'pareto_rank') and s.pareto_rank == 1]
    print(f"\nFinal Pareto Front:  {len(pareto_front)} strategies")

    # Output files
    print(f"\nResults saved to:    {output_dir}")
    print(f"Logs saved to:       population_evolution.log")


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Display banner
    display_banner()

    # Create output directories
    checkpoint_dir = Path(args.checkpoint_dir)
    output_dir = Path(args.output_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Log configuration
    logger.info("="*70)
    logger.info("Configuration")
    logger.info("="*70)
    logger.info(f"Population Size:     {args.population_size}")
    logger.info(f"Generations:         {args.generations}")
    logger.info(f"Elite Count:         {args.elite_count}")
    logger.info(f"Tournament Size:     {args.tournament_size}")
    logger.info(f"Mutation Rate:       {args.mutation_rate}")
    logger.info(f"Checkpoint Dir:      {checkpoint_dir}")
    logger.info(f"Output Dir:          {output_dir}")

    # Initialize PopulationManager
    logger.info("\nInitializing PopulationManager...")
    manager = PopulationManager(
        population_size=args.population_size,
        elite_count=args.elite_count,
        tournament_size=args.tournament_size,
        mutation_rate=args.mutation_rate
    )

    # Initialize population
    print(f"\n{'='*70}")
    print(f"INITIALIZING POPULATION (N={args.population_size})")
    print(f"{'='*70}")
    logger.info("Generating initial population...")

    initial_population = manager.initialize_population()
    logger.info(f"Initial population created: {len(initial_population)} strategies")

    # Save initial checkpoint
    initial_checkpoint = checkpoint_dir / "generation_0.json"
    manager.save_checkpoint(str(initial_checkpoint))
    logger.info(f"Initial checkpoint saved: {initial_checkpoint}")

    # Run evolution
    try:
        for gen in range(1, args.generations + 1):
            logger.info(f"\nStarting generation {gen}/{args.generations}...")

            # Evolve generation
            result = manager.evolve_generation(gen)

            # Display progress
            display_progress(gen, args.generations, result)

            # Save checkpoint
            checkpoint_file = checkpoint_dir / f"generation_{gen}.json"
            manager.save_checkpoint(str(checkpoint_file))
            logger.debug(f"Checkpoint saved: {checkpoint_file}")

            # Generate visualizations
            try:
                # Pareto front plot
                plot_pareto_front(
                    population=manager.current_population,
                    generation=gen,
                    output_path=str(output_dir / f"generation_{gen}_pareto.png")
                )

                # Diversity plot
                diversity_history = [r.diversity_score for r in manager.generation_history]
                plot_diversity_over_time(
                    diversity_history=diversity_history,
                    output_path=str(output_dir / "diversity.png")
                )
            except Exception as e:
                logger.warning(f"Visualization failed: {e}")

    except KeyboardInterrupt:
        logger.warning("\nEvolution interrupted by user")
        print("\n\n⚠️  Evolution interrupted. Progress saved to checkpoints.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Evolution failed: {e}", exc_info=True)
        print(f"\n\n❌ Evolution failed: {e}")
        sys.exit(1)

    # Display final summary
    display_final_summary(manager, output_dir)

    # Save final population
    final_checkpoint = checkpoint_dir / "final_population.json"
    manager.save_checkpoint(str(final_checkpoint))
    logger.info(f"\nFinal population saved: {final_checkpoint}")

    print(f"\n✅ Evolution completed successfully!\n")
    return 0


if __name__ == '__main__':
    sys.exit(main())
