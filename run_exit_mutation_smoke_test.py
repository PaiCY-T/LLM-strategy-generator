#!/usr/bin/env python3
"""
Exit Mutation Smoke Test Runner

Standalone smoke test script for quick validation of exit mutation integration.
Can be run manually or in CI/CD pipeline.

Usage:
    python run_exit_mutation_smoke_test.py [options]

Options:
    --generations N    Number of generations to evolve (default: 5)
    --population N     Population size (default: 20)
    --output FILE      Output report file (default: smoke_test_results.json)
    --verbose          Enable verbose logging

Exit Codes:
    0: All tests passed
    1: Test failures detected
    2: Fatal exception occurred
"""

import argparse
import json
import logging
import sys
import tempfile
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

from src.evolution.population_manager import PopulationManager
from src.evolution.types import Strategy


# Configure logging
def setup_logging(verbose: bool = False):
    """Configure logging with appropriate level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


# Sample strategy templates
SAMPLE_STRATEGIES = {
    'Momentum': """
# Momentum strategy with basic exit mechanism
close = data.get('price:收盤價')
returns = close.pct_change(20)
signal = returns.rank(axis=1)

# Entry: Top 20 stocks
selected = signal.rank(axis=1, ascending=False) <= 20
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Simple stop-loss at -5%
entry_price = close.shift(1)
stop_loss = positions * (close < entry_price * 0.95)
positions = positions - stop_loss
""",
    'Factor': """
# Factor strategy with trailing stop
close = data.get('price:收盤價')
pe = data.get('price_earning_ratio:本益比')
value = 1 / pe.clip(lower=1)
signal = value.rank(axis=1)

# Entry: Top 30 stocks
selected = signal.rank(axis=1, ascending=False) <= 30
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Trailing stop at -10%
highest_price = close.rolling(20).max()
trailing_stop = positions * (close < highest_price * 0.90)
positions = positions - trailing_stop
""",
    'Turtle': """
# Turtle strategy with take profit
close = data.get('price:收盤價')
high = close.rolling(20).max()
low = close.rolling(20).min()
donchian = (close - low) / (high - low)

# Entry: Breakout above 0.8
selected = donchian > 0.8
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Take profit at +15%
entry_price = close.shift(1)
take_profit = positions * (close > entry_price * 1.15)
positions = positions - take_profit
""",
    'Mastiff': """
# Quality strategy with compound exit
close = data.get('price:收盤價')
roe = close.pct_change(5)  # Placeholder for ROE
quality = roe.rolling(10).mean()
signal = quality.rank(axis=1)

# Entry: Top 25 stocks
selected = signal.rank(axis=1, ascending=False) <= 25
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Combined stop-loss (-8%) AND trailing stop (-12%)
entry_price = close.shift(1)
stop_loss = positions * (close < entry_price * 0.92)
highest_price = close.rolling(15).max()
trailing_stop = positions * (close < highest_price * 0.88)
positions = positions - stop_loss - trailing_stop
"""
}


def create_test_strategy(
    strategy_id: str,
    template_type: str,
    generation: int = 0
) -> Strategy:
    """Create test strategy with realistic code."""
    code = SAMPLE_STRATEGIES.get(template_type, SAMPLE_STRATEGIES['Momentum'])

    return Strategy(
        id=strategy_id,
        generation=generation,
        parent_ids=[],
        code=code,
        parameters={
            'template': template_type,
            'lookback': 20
        },
        template_type=template_type
    )


def create_config_file() -> str:
    """Create temporary config file with exit mutations enabled."""
    config = {
        'exit_mutation': {
            'enabled': True,
            'exit_mutation_probability': 0.3,
            'mutation_config': {
                'tier1_weight': 0.5,
                'tier2_weight': 0.3,
                'tier3_weight': 0.2,
                'parameter_ranges': {
                    'stop_loss_range': [0.8, 1.2],
                    'take_profit_range': [0.9, 1.3],
                    'trailing_range': [0.85, 1.25]
                }
            },
            'validation': {
                'max_retries': 3,
                'validation_timeout': 5
            },
            'monitoring': {
                'log_mutations': True,
                'track_mutation_types': True,
                'log_validation': True
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        return f.name


def run_smoke_test(
    num_generations: int,
    population_size: int,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run smoke test with specified parameters.

    Args:
        num_generations: Number of generations to evolve
        population_size: Population size
        logger: Logger instance

    Returns:
        Test results dictionary
    """
    logger.info("=" * 80)
    logger.info("Exit Mutation Smoke Test")
    logger.info("=" * 80)
    logger.info(f"Parameters: generations={num_generations}, population_size={population_size}")

    # Create config
    config_path = create_config_file()

    try:
        # Initialize PopulationManager
        logger.info("\n1. Initializing PopulationManager...")
        start_time = time.time()

        manager = PopulationManager(
            population_size=population_size,
            elite_count=max(2, population_size // 10),  # 10% elites
            tournament_size=3,
            mutation_rate=0.1,
            crossover_rate=0.7,
            config_path=config_path
        )

        logger.info(f"   ✓ PopulationManager initialized ({time.time() - start_time:.2f}s)")
        logger.info(f"   - Exit mutations: {'ENABLED' if manager.exit_mutation_enabled else 'DISABLED'}")
        logger.info(f"   - Mutation probability: {manager.exit_mutation_probability:.2%}")

        # Create initial population
        logger.info("\n2. Creating initial population...")
        start_time = time.time()

        templates = ['Momentum', 'Factor', 'Turtle', 'Mastiff']
        initial_population = [
            create_test_strategy(f"init_{i:03d}", templates[i % 4], 0)
            for i in range(population_size)
        ]

        manager.current_population = initial_population
        manager.current_generation = 0

        logger.info(f"   ✓ Population created ({time.time() - start_time:.2f}s)")
        logger.info(f"   - Size: {len(initial_population)} strategies")
        logger.info(f"   - Templates: {templates}")

        # Run evolution
        logger.info(f"\n3. Running {num_generations}-generation evolution...")

        generation_stats = []
        total_start_time = time.time()

        for gen in range(1, num_generations + 1):
            logger.info(f"\n   Generation {gen}/{num_generations}")
            logger.info(f"   {'-' * 60}")

            gen_start_time = time.time()

            # Record stats before generation
            stats_before = {
                'attempts': manager.exit_mutation_stats['attempts'],
                'successes': manager.exit_mutation_stats['successes'],
                'failures': manager.exit_mutation_stats['failures']
            }

            try:
                # Evolve generation
                result = manager.evolve_generation(generation_num=gen)

                # Record stats after generation
                stats_after = {
                    'attempts': manager.exit_mutation_stats['attempts'],
                    'successes': manager.exit_mutation_stats['successes'],
                    'failures': manager.exit_mutation_stats['failures']
                }

                # Calculate generation-specific stats
                gen_attempts = stats_after['attempts'] - stats_before['attempts']
                gen_successes = stats_after['successes'] - stats_before['successes']
                gen_failures = stats_after['failures'] - stats_before['failures']
                gen_success_rate = gen_successes / gen_attempts if gen_attempts > 0 else 0.0

                gen_stats = {
                    'generation': gen,
                    'attempts': gen_attempts,
                    'successes': gen_successes,
                    'failures': gen_failures,
                    'success_rate': gen_success_rate,
                    'diversity': result.diversity_score,
                    'pareto_front_size': result.pareto_front_size,
                    'time': time.time() - gen_start_time
                }

                generation_stats.append(gen_stats)

                logger.info(
                    f"   ✓ Generation {gen} complete: "
                    f"mutations={gen_attempts}, "
                    f"success_rate={gen_success_rate:.2%}, "
                    f"diversity={result.diversity_score:.3f}, "
                    f"time={gen_stats['time']:.2f}s"
                )

            except Exception as e:
                logger.error(f"   ✗ Generation {gen} failed: {e}", exc_info=True)
                raise

        total_evolution_time = time.time() - total_start_time

        # Aggregate statistics
        logger.info(f"\n4. Aggregating results...")

        total_attempts = sum(s['attempts'] for s in generation_stats)
        total_successes = sum(s['successes'] for s in generation_stats)
        total_failures = sum(s['failures'] for s in generation_stats)
        overall_success_rate = total_successes / total_attempts if total_attempts > 0 else 0.0

        # Build result
        result = {
            'test_name': 'Exit Mutation Smoke Test',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'num_generations': num_generations,
                'population_size': population_size,
                'elite_count': manager.elite_count,
                'mutation_probability': manager.exit_mutation_probability
            },
            'statistics': {
                'total_attempts': total_attempts,
                'total_successes': total_successes,
                'total_failures': total_failures,
                'overall_success_rate': overall_success_rate,
                'by_type': dict(manager.exit_mutation_stats['by_type'])
            },
            'generation_breakdown': generation_stats,
            'timing': {
                'total_evolution_time': total_evolution_time,
                'avg_generation_time': total_evolution_time / num_generations
            },
            'success': True,
            'errors': []
        }

        # Validation checks
        logger.info("\n5. Validating results...")

        validation_errors = []

        # Check 1: Minimum attempts
        if total_attempts < 10:
            validation_errors.append(f"Too few mutation attempts: {total_attempts} < 10")

        # Check 2: Success rate
        if overall_success_rate < 0.70:
            validation_errors.append(
                f"Success rate below target: {overall_success_rate:.2%} < 70% (target: ≥90%)"
            )

        # Check 3: No fatal exceptions (already checked by successful execution)
        logger.info(f"   ✓ No fatal exceptions")

        # Check 4: Statistics consistency
        if total_successes + total_failures != total_attempts:
            validation_errors.append(
                f"Statistics inconsistency: {total_successes} + {total_failures} != {total_attempts}"
            )

        result['validation_errors'] = validation_errors
        result['success'] = len(validation_errors) == 0

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("SMOKE TEST SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total exit mutation attempts: {total_attempts}")
        logger.info(f"Total successes: {total_successes}")
        logger.info(f"Total failures: {total_failures}")
        logger.info(f"Overall success rate: {overall_success_rate:.2%}")
        logger.info(f"Total evolution time: {total_evolution_time:.2f}s")
        logger.info(f"Average generation time: {total_evolution_time / num_generations:.2f}s")

        if manager.exit_mutation_track_types:
            by_type = manager.exit_mutation_stats['by_type']
            logger.info(f"\nMutation types:")
            logger.info(f"  Parametric: {by_type['parametric']}")
            logger.info(f"  Structural: {by_type['structural']}")
            logger.info(f"  Relational: {by_type['relational']}")

        logger.info(f"\nPer-generation breakdown:")
        for stats in generation_stats:
            logger.info(
                f"  Gen {stats['generation']}: "
                f"{stats['attempts']} attempts, "
                f"{stats['successes']} successes, "
                f"rate={stats['success_rate']:.2%}, "
                f"diversity={stats['diversity']:.3f}"
            )

        if validation_errors:
            logger.warning(f"\n⚠️  Validation warnings ({len(validation_errors)}):")
            for error in validation_errors:
                logger.warning(f"  - {error}")
            logger.info("\n" + "=" * 80)
            logger.info("SMOKE TEST COMPLETED WITH WARNINGS")
            logger.info("=" * 80)
        else:
            logger.info("\n" + "=" * 80)
            logger.info("✅ SMOKE TEST PASSED")
            logger.info("=" * 80)

        return result

    finally:
        # Cleanup config file
        Path(config_path).unlink()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Exit Mutation Smoke Test Runner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with defaults (5 generations, 20 population)
  python run_exit_mutation_smoke_test.py

  # Run with custom parameters
  python run_exit_mutation_smoke_test.py --generations 10 --population 50

  # Run with verbose logging and custom output
  python run_exit_mutation_smoke_test.py --verbose --output my_results.json
        """
    )

    parser.add_argument(
        '--generations',
        type=int,
        default=5,
        help='Number of generations to evolve (default: 5)'
    )

    parser.add_argument(
        '--population',
        type=int,
        default=20,
        help='Population size (default: 20)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='smoke_test_results.json',
        help='Output report file (default: smoke_test_results.json)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.verbose)

    try:
        # Run smoke test
        result = run_smoke_test(
            num_generations=args.generations,
            population_size=args.population,
            logger=logger
        )

        # Save results
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"\nResults saved to: {output_path}")

        # Exit with appropriate code
        if result['success']:
            logger.info("\n✅ Smoke test passed - exit code 0")
            sys.exit(0)
        else:
            logger.warning("\n⚠️  Smoke test completed with warnings - exit code 1")
            sys.exit(1)

    except Exception as e:
        logger.error(f"\n❌ Fatal exception occurred: {e}", exc_info=True)
        logger.error("Smoke test failed - exit code 2")
        sys.exit(2)


if __name__ == "__main__":
    main()
