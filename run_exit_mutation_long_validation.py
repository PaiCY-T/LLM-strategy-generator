#!/usr/bin/env python3
"""
Exit Mutation Long-Running Validation Test
===========================================

Comprehensive 20-50 generation validation test to evaluate exit mutation framework
performance and stability before deciding between Phase 2a (Structured Innovation)
or Phase 2.0 (Full Structural Mutation).

Test Phases:
-----------
- Phase 1: Quick validation (10 generations, ~30-60 min)
- Phase 2: Standard validation (20 generations, ~1-2 hours)
- Phase 3: Extended validation (50 generations, ~4-6 hours, if Phase 2 promising)

Decision Criteria:
-----------------
Phase 2a (Structured Innovation):
  ✓ Best Sharpe >2.0 achieved
  ✓ Population diversity >3 structural patterns
  ✓ Exit mutation success rate ≥85%
  ✓ No critical stability issues
  ✓ System maintains performance over 20 generations

Phase 2.0 (Full Structural Mutation):
  ✗ Sharpe <2.0 (need more structural diversity)
  ✗ Low diversity (<3 patterns)
  ✗ Exit mutations plateau quickly
  ✗ Stability concerns

Usage:
------
python run_exit_mutation_long_validation.py [options]

Options:
  --phase {1,2,3}       Test phase (default: 2)
  --population N        Population size (default: 20)
  --output DIR          Output directory (default: validation_results)
  --checkpoint-freq N   Checkpoint every N generations (default: 5)
  --timeout MINUTES     Max test duration in minutes (default: 240 = 4 hours)
  --verbose             Enable verbose logging

Exit Codes:
  0: Validation passed - ready for Phase 2a
  1: Validation shows need for Phase 2.0
  2: Optimization needed before proceeding
  3: Fatal error occurred
"""

import argparse
import json
import logging
import os
import sys
import tempfile
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np

from src.evolution.population_manager import PopulationManager
from src.evolution.types import Strategy


# Configure logging
def setup_logging(verbose: bool = False, output_dir: Path = None):
    """Configure logging with file and console handlers."""
    level = logging.DEBUG if verbose else logging.INFO

    handlers = [logging.StreamHandler()]

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = output_dir / f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )

    return logging.getLogger(__name__)


# Test configuration
PHASE_CONFIGS = {
    1: {  # Quick validation
        'generations': 10,
        'expected_time': 30,  # minutes
        'description': 'Quick validation (10 generations)'
    },
    2: {  # Standard validation
        'generations': 20,
        'expected_time': 90,  # minutes
        'description': 'Standard validation (20 generations)'
    },
    3: {  # Extended validation
        'generations': 50,
        'expected_time': 240,  # minutes
        'description': 'Extended validation (50 generations)'
    }
}


# Sample strategy templates with realistic exit mechanisms
SAMPLE_STRATEGIES = {
    'Momentum': """
# Momentum strategy with basic exit
close = data.get('price:收盤價')
returns = close.pct_change(20)
signal = returns.rank(axis=1)

# Entry
selected = signal.rank(axis=1, ascending=False) <= 20
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Stop-loss at -5%
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

# Entry
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

# Entry
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
roe = close.pct_change(5)
quality = roe.rolling(10).mean()
signal = quality.rank(axis=1)

# Entry
selected = signal.rank(axis=1, ascending=False) <= 25
positions = selected.astype(float) / selected.sum(axis=1)

# Exit: Combined stop-loss AND trailing stop
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
    generation: int = 0,
    sharpe: float = 1.0
) -> Strategy:
    """Create test strategy with metrics."""
    from src.evolution.types import MultiObjectiveMetrics

    code = SAMPLE_STRATEGIES.get(template_type, SAMPLE_STRATEGIES['Momentum'])

    # Vary sharpe slightly for diversity
    sharpe_variation = np.random.uniform(0.8, 1.2)
    adjusted_sharpe = sharpe * sharpe_variation

    # Create multi-objective metrics
    metrics = MultiObjectiveMetrics(
        sharpe_ratio=adjusted_sharpe,
        annual_return=adjusted_sharpe * 0.15,
        max_drawdown=-0.15 / max(adjusted_sharpe, 0.5),
        calmar_ratio=adjusted_sharpe * 0.8,
        total_return=adjusted_sharpe * 0.30,
        win_rate=0.55,
        success=True
    )

    strategy = Strategy(
        id=strategy_id,
        generation=generation,
        parent_ids=[],
        code=code,
        parameters={
            'template': template_type,
            'lookback': 20
        },
        template_type=template_type,
        metrics=metrics
    )

    return strategy


def create_config_file(checkpoint_dir: Path) -> str:
    """Create validation configuration file."""
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
        },
        'checkpointing': {
            'enabled': True,
            'checkpoint_dir': str(checkpoint_dir)
        }
    }

    config_path = checkpoint_dir / 'validation_config.yaml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)

    return str(config_path)


def save_checkpoint(
    generation: int,
    manager: PopulationManager,
    stats: Dict[str, Any],
    checkpoint_dir: Path
) -> None:
    """Save checkpoint for recovery."""
    checkpoint_path = checkpoint_dir / f'checkpoint_gen{generation:03d}.json'

    checkpoint_data = {
        'generation': generation,
        'timestamp': datetime.now().isoformat(),
        'population_size': len(manager.current_population),
        'statistics': stats,
        'exit_mutation_stats': {
            'attempts': manager.exit_mutation_stats['attempts'],
            'successes': manager.exit_mutation_stats['successes'],
            'failures': manager.exit_mutation_stats['failures'],
            'by_type': dict(manager.exit_mutation_stats['by_type'])
        }
    }

    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint_data, f, indent=2)


def analyze_diversity(manager: PopulationManager, logger: logging.Logger) -> Dict[str, Any]:
    """Analyze population diversity and structural patterns."""
    population = manager.current_population

    # Count unique exit patterns
    exit_patterns = set()
    for strategy in population:
        # Simple pattern detection based on keywords
        code = strategy.code.lower()
        if 'stop_loss' in code and 'trailing' in code:
            exit_patterns.add('compound_stop')
        elif 'stop_loss' in code:
            exit_patterns.add('stop_loss')
        elif 'trailing' in code:
            exit_patterns.add('trailing_stop')
        elif 'take_profit' in code:
            exit_patterns.add('take_profit')
        else:
            exit_patterns.add('basic')

    # Calculate Jaccard distance between strategies
    def code_similarity(code1: str, code2: str) -> float:
        """Calculate code similarity using set-based Jaccard."""
        tokens1 = set(code1.split())
        tokens2 = set(code2.split())
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0

    # Sample pairwise similarities
    n_samples = min(len(population), 20)
    sampled = np.random.choice(population, n_samples, replace=False)
    similarities = []

    for i in range(len(sampled)):
        for j in range(i+1, len(sampled)):
            sim = code_similarity(sampled[i].code, sampled[j].code)
            similarities.append(sim)

    avg_similarity = np.mean(similarities) if similarities else 0.0
    jaccard_diversity = 1.0 - avg_similarity

    return {
        'unique_patterns': len(exit_patterns),
        'exit_patterns': list(exit_patterns),
        'jaccard_diversity': jaccard_diversity,
        'avg_similarity': avg_similarity
    }


def detect_plateau(sharpe_history: List[float], window: int = 5) -> bool:
    """Detect if Sharpe improvement has plateaued."""
    if len(sharpe_history) < window:
        return False

    recent = sharpe_history[-window:]
    variance = np.var(recent)

    # Plateau if variance < 0.01 and improvement trend < 0.05
    if variance < 0.01:
        trend = recent[-1] - recent[0]
        return trend < 0.05

    return False


def calculate_improvement_rate(sharpe_history: List[float]) -> float:
    """Calculate Sharpe improvement slope."""
    if len(sharpe_history) < 2:
        return 0.0

    x = np.arange(len(sharpe_history))
    y = np.array(sharpe_history)

    # Linear regression
    coeffs = np.polyfit(x, y, 1)
    slope = coeffs[0]

    return slope


def run_validation_test(
    num_generations: int,
    population_size: int,
    checkpoint_freq: int,
    timeout_minutes: int,
    output_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run comprehensive validation test.

    Returns:
        Test results with decision recommendation
    """
    logger.info("=" * 80)
    logger.info("EXIT MUTATION LONG-RUNNING VALIDATION TEST")
    logger.info("=" * 80)
    logger.info(f"Configuration:")
    logger.info(f"  - Generations: {num_generations}")
    logger.info(f"  - Population: {population_size}")
    logger.info(f"  - Checkpoint frequency: {checkpoint_freq}")
    logger.info(f"  - Timeout: {timeout_minutes} minutes")
    logger.info(f"  - Output directory: {output_dir}")

    # Create checkpoint directory
    checkpoint_dir = output_dir / 'checkpoints'
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # Create config
    config_path = create_config_file(checkpoint_dir)
    logger.info(f"\n✓ Configuration saved to: {config_path}")

    # Initialize PopulationManager
    logger.info("\n" + "=" * 80)
    logger.info("INITIALIZATION")
    logger.info("=" * 80)

    start_time = time.time()
    timeout_seconds = timeout_minutes * 60

    manager = PopulationManager(
        population_size=population_size,
        elite_count=max(2, population_size // 10),
        tournament_size=3,
        mutation_rate=0.1,
        crossover_rate=0.7,
        config_path=config_path
    )

    logger.info(f"✓ PopulationManager initialized")
    logger.info(f"  - Exit mutations: {'ENABLED' if manager.exit_mutation_enabled else 'DISABLED'}")
    logger.info(f"  - Mutation probability: {manager.exit_mutation_probability:.2%}")

    # Create initial population
    templates = ['Momentum', 'Factor', 'Turtle', 'Mastiff']
    initial_population = [
        create_test_strategy(f"init_{i:03d}", templates[i % 4], 0, sharpe=np.random.uniform(0.8, 1.5))
        for i in range(population_size)
    ]

    manager.current_population = initial_population
    manager.current_generation = 0

    logger.info(f"✓ Initial population created: {len(initial_population)} strategies")
    logger.info(f"  - Templates: {templates}")

    # Tracking variables
    generation_stats = []
    sharpe_history = []
    best_sharpe = max(s.metrics.sharpe_ratio for s in initial_population)
    sharpe_history.append(best_sharpe)

    stability_issues = []

    logger.info(f"✓ Initial best Sharpe: {best_sharpe:.4f}")

    # Evolution loop
    logger.info("\n" + "=" * 80)
    logger.info("EVOLUTION")
    logger.info("=" * 80)

    for gen in range(1, num_generations + 1):
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            logger.warning(f"\n⏱  Timeout reached ({elapsed/60:.1f} min > {timeout_minutes} min)")
            logger.warning("Stopping evolution early")
            break

        logger.info(f"\nGeneration {gen}/{num_generations}")
        logger.info("-" * 60)

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

            # Get current best Sharpe (filter out strategies without metrics)
            strategies_with_metrics = [s for s in manager.current_population if s.metrics is not None]
            if strategies_with_metrics:
                current_best = max(s.metrics.sharpe_ratio for s in strategies_with_metrics)
            else:
                current_best = best_sharpe  # Keep previous best if no new metrics
            sharpe_history.append(current_best)

            if current_best > best_sharpe:
                improvement = current_best - best_sharpe
                best_sharpe = current_best
                logger.info(f"  🏆 NEW BEST: Sharpe {best_sharpe:.4f} (+{improvement:.4f})")

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

            # Analyze diversity
            diversity_metrics = analyze_diversity(manager, logger)

            # Calculate improvement rate
            improvement_rate = calculate_improvement_rate(sharpe_history)

            gen_stats = {
                'generation': gen,
                'best_sharpe': current_best,
                'avg_sharpe': np.mean([s.metrics.sharpe_ratio for s in strategies_with_metrics]) if strategies_with_metrics else 0.0,
                'mutation_attempts': gen_attempts,
                'mutation_successes': gen_successes,
                'mutation_failures': gen_failures,
                'success_rate': gen_success_rate,
                'diversity_score': result.diversity_score,
                'unique_patterns': diversity_metrics['unique_patterns'],
                'exit_patterns': diversity_metrics['exit_patterns'],
                'jaccard_diversity': diversity_metrics['jaccard_diversity'],
                'improvement_rate': improvement_rate,
                'pareto_front_size': result.pareto_front_size,
                'time': time.time() - gen_start_time,
                'elapsed_total': time.time() - start_time
            }

            generation_stats.append(gen_stats)

            logger.info(
                f"  ✓ Complete: "
                f"Sharpe={current_best:.4f}, "
                f"mutations={gen_attempts}, "
                f"success_rate={gen_success_rate:.2%}, "
                f"patterns={diversity_metrics['unique_patterns']}, "
                f"time={gen_stats['time']:.1f}s"
            )

            # Checkpoint
            if gen % checkpoint_freq == 0:
                save_checkpoint(gen, manager, gen_stats, checkpoint_dir)
                logger.info(f"  💾 Checkpoint saved")

        except Exception as e:
            logger.error(f"  ✗ Generation {gen} failed: {e}", exc_info=True)
            stability_issues.append({
                'generation': gen,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

            # Continue if not too many failures
            if len(stability_issues) > 3:
                logger.error("Too many stability issues - stopping test")
                break

    total_time = time.time() - start_time

    # Aggregate statistics
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSIS")
    logger.info("=" * 80)

    total_attempts = sum(s['mutation_attempts'] for s in generation_stats)
    total_successes = sum(s['mutation_successes'] for s in generation_stats)
    total_failures = sum(s['mutation_failures'] for s in generation_stats)
    overall_success_rate = total_successes / total_attempts if total_attempts > 0 else 0.0

    # Diversity analysis
    final_diversity = generation_stats[-1] if generation_stats else {}
    unique_patterns = final_diversity.get('unique_patterns', 0)
    final_jaccard = final_diversity.get('jaccard_diversity', 0.0)

    # Performance analysis
    sharpe_improvement = best_sharpe - sharpe_history[0]
    avg_improvement_rate = calculate_improvement_rate(sharpe_history)
    plateaued = detect_plateau(sharpe_history)

    # Build result
    result = {
        'test_name': 'Exit Mutation Long-Running Validation',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'num_generations': num_generations,
            'generations_completed': len(generation_stats),
            'population_size': population_size,
            'checkpoint_freq': checkpoint_freq,
            'timeout_minutes': timeout_minutes
        },
        'performance': {
            'initial_sharpe': sharpe_history[0],
            'final_sharpe': best_sharpe,
            'best_sharpe': best_sharpe,
            'sharpe_improvement': sharpe_improvement,
            'avg_improvement_rate': avg_improvement_rate,
            'plateaued': plateaued,
            'sharpe_history': sharpe_history
        },
        'diversity': {
            'unique_patterns': unique_patterns,
            'final_jaccard_diversity': final_jaccard,
            'exit_patterns': final_diversity.get('exit_patterns', [])
        },
        'mutation_statistics': {
            'total_attempts': total_attempts,
            'total_successes': total_successes,
            'total_failures': total_failures,
            'overall_success_rate': overall_success_rate,
            'by_type': dict(manager.exit_mutation_stats['by_type'])
        },
        'stability': {
            'issues_count': len(stability_issues),
            'issues': stability_issues
        },
        'generation_breakdown': generation_stats,
        'timing': {
            'total_time': total_time,
            'avg_generation_time': total_time / len(generation_stats) if generation_stats else 0
        }
    }

    # Decision gate evaluation
    logger.info("\n" + "=" * 80)
    logger.info("DECISION GATE EVALUATION")
    logger.info("=" * 80)

    phase2a_criteria = {
        'sharpe_target': best_sharpe >= 2.0,
        'diversity_target': unique_patterns >= 3,
        'success_rate_target': overall_success_rate >= 0.85,
        'stability_ok': len(stability_issues) == 0,
        'performance_maintained': not plateaued
    }

    phase2a_passed = all(phase2a_criteria.values())

    logger.info("\nPhase 2a (Structured Innovation) Readiness:")
    logger.info(f"  {'✓' if phase2a_criteria['sharpe_target'] else '✗'} Sharpe >2.0: {best_sharpe:.4f}")
    logger.info(f"  {'✓' if phase2a_criteria['diversity_target'] else '✗'} Diversity >3 patterns: {unique_patterns}")
    logger.info(f"  {'✓' if phase2a_criteria['success_rate_target'] else '✗'} Success rate ≥85%: {overall_success_rate:.2%}")
    logger.info(f"  {'✓' if phase2a_criteria['stability_ok'] else '✗'} No stability issues: {len(stability_issues)} issues")
    logger.info(f"  {'✓' if phase2a_criteria['performance_maintained'] else '✗'} Performance maintained: {'not plateaued' if not plateaued else 'PLATEAUED'}")

    if phase2a_passed:
        recommendation = 'PROCEED_TO_PHASE_2A'
        recommendation_text = "✅ READY FOR PHASE 2A (Structured Innovation)"
        exit_code = 0
    elif overall_success_rate < 0.85 or len(stability_issues) > 0:
        recommendation = 'OPTIMIZATION_NEEDED'
        recommendation_text = "⚠️  OPTIMIZATION NEEDED - Address stability/success rate issues"
        exit_code = 2
    else:
        recommendation = 'PROCEED_TO_PHASE_2_0'
        recommendation_text = "➡️  PROCEED TO PHASE 2.0 (Full Structural Mutation)"
        exit_code = 1

    result['decision'] = {
        'recommendation': recommendation,
        'recommendation_text': recommendation_text,
        'phase2a_criteria': phase2a_criteria,
        'phase2a_passed': phase2a_passed,
        'exit_code': exit_code
    }

    logger.info(f"\n{recommendation_text}")
    logger.info(f"Exit code: {exit_code}")

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Generations completed: {len(generation_stats)}/{num_generations}")
    logger.info(f"Total time: {total_time/60:.1f} minutes")
    logger.info(f"Best Sharpe: {best_sharpe:.4f} (improvement: +{sharpe_improvement:.4f})")
    logger.info(f"Unique exit patterns: {unique_patterns}")
    logger.info(f"Mutation success rate: {overall_success_rate:.2%}")
    logger.info(f"Stability issues: {len(stability_issues)}")

    return result


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Exit Mutation Long-Running Validation Test',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run Phase 2 validation (20 generations, recommended)
  python run_exit_mutation_long_validation.py

  # Run Phase 1 quick validation (10 generations)
  python run_exit_mutation_long_validation.py --phase 1

  # Run Phase 3 extended validation (50 generations)
  python run_exit_mutation_long_validation.py --phase 3

  # Custom configuration
  python run_exit_mutation_long_validation.py --phase 2 --population 50 --timeout 180
        """
    )

    parser.add_argument(
        '--phase',
        type=int,
        choices=[1, 2, 3],
        default=2,
        help='Test phase: 1=quick (10 gen), 2=standard (20 gen), 3=extended (50 gen)'
    )

    parser.add_argument(
        '--population',
        type=int,
        default=20,
        help='Population size (default: 20)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('validation_results'),
        help='Output directory (default: validation_results)'
    )

    parser.add_argument(
        '--checkpoint-freq',
        type=int,
        default=5,
        help='Checkpoint frequency in generations (default: 5)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='Timeout in minutes (default: auto based on phase)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Get phase configuration
    phase_config = PHASE_CONFIGS[args.phase]
    num_generations = phase_config['generations']
    timeout_minutes = args.timeout if args.timeout else phase_config['expected_time']

    # Setup output directory
    output_dir = args.output / f"phase{args.phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Setup logging
    logger = setup_logging(args.verbose, output_dir)

    logger.info(f"Phase {args.phase}: {phase_config['description']}")
    logger.info(f"Expected time: ~{timeout_minutes} minutes")

    try:
        # Run validation test
        result = run_validation_test(
            num_generations=num_generations,
            population_size=args.population,
            checkpoint_freq=args.checkpoint_freq,
            timeout_minutes=timeout_minutes,
            output_dir=output_dir,
            logger=logger
        )

        # Save results
        results_file = output_dir / 'validation_results.json'
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"\n✓ Results saved to: {results_file}")

        # Generate markdown report
        report_file = output_dir / 'EXIT_MUTATION_LONG_VALIDATION_REPORT.md'
        generate_report(result, report_file, logger)

        logger.info(f"✓ Report saved to: {report_file}")

        # Exit with decision code
        exit_code = result['decision']['exit_code']
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"\n❌ Fatal exception occurred: {e}", exc_info=True)
        sys.exit(3)


def generate_report(result: Dict[str, Any], report_file: Path, logger: logging.Logger) -> None:
    """Generate comprehensive markdown validation report."""
    with open(report_file, 'w') as f:
        f.write("# Exit Mutation Long-Running Validation Report\n\n")
        f.write(f"**Generated**: {result['timestamp']}\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"**Decision**: {result['decision']['recommendation_text']}\n\n")

        decision = result['decision']
        f.write("### Phase 2a Readiness Criteria\n\n")
        for criterion, passed in decision['phase2a_criteria'].items():
            status = "✅ PASS" if passed else "❌ FAIL"
            f.write(f"- {status}: {criterion.replace('_', ' ').title()}\n")

        # Performance Analysis
        f.write("\n## Performance Analysis\n\n")
        perf = result['performance']
        f.write(f"- **Initial Sharpe**: {perf['initial_sharpe']:.4f}\n")
        f.write(f"- **Final Sharpe**: {perf['final_sharpe']:.4f}\n")
        f.write(f"- **Best Sharpe**: {perf['best_sharpe']:.4f}\n")
        f.write(f"- **Improvement**: +{perf['sharpe_improvement']:.4f}\n")
        f.write(f"- **Avg Improvement Rate**: {perf['avg_improvement_rate']:.4f}/gen\n")
        f.write(f"- **Plateaued**: {'Yes ⚠️' if perf['plateaued'] else 'No ✅'}\n")

        # Sharpe progression chart
        f.write("\n### Sharpe Ratio Progression\n\n")
        f.write("```\n")
        history = perf['sharpe_history']
        for i, sharpe in enumerate(history):
            bar_length = int(sharpe * 20)
            bar = '█' * bar_length
            f.write(f"Gen {i:2d}: {sharpe:.4f} {bar}\n")
        f.write("```\n")

        # Diversity Analysis
        f.write("\n## Diversity Analysis\n\n")
        div = result['diversity']
        f.write(f"- **Unique Exit Patterns**: {div['unique_patterns']}\n")
        f.write(f"- **Jaccard Diversity**: {div['final_jaccard_diversity']:.3f}\n")
        f.write(f"- **Exit Patterns Found**:\n")
        for pattern in div['exit_patterns']:
            f.write(f"  - {pattern}\n")

        # Exit Mutation Analysis
        f.write("\n## Exit Mutation Analysis\n\n")
        mut = result['mutation_statistics']
        f.write(f"- **Total Attempts**: {mut['total_attempts']}\n")
        f.write(f"- **Successes**: {mut['total_successes']}\n")
        f.write(f"- **Failures**: {mut['total_failures']}\n")
        f.write(f"- **Success Rate**: {mut['overall_success_rate']:.2%}\n")

        f.write("\n### Mutation Types Distribution\n\n")
        by_type = mut['by_type']
        f.write(f"- Parametric: {by_type['parametric']}\n")
        f.write(f"- Structural: {by_type['structural']}\n")
        f.write(f"- Relational: {by_type['relational']}\n")

        # Stability Analysis
        f.write("\n## Stability Analysis\n\n")
        stab = result['stability']
        f.write(f"- **Total Issues**: {stab['issues_count']}\n")

        if stab['issues_count'] > 0:
            f.write("\n### Issues Detected\n\n")
            for issue in stab['issues']:
                f.write(f"- **Gen {issue['generation']}**: {issue['error']}\n")
        else:
            f.write("\n✅ No stability issues detected\n")

        # Generation Breakdown
        f.write("\n## Generation Breakdown\n\n")
        f.write("| Gen | Best Sharpe | Mutations | Success Rate | Patterns | Time |\n")
        f.write("|-----|-------------|-----------|--------------|----------|------|\n")

        for gen_stats in result['generation_breakdown']:
            f.write(
                f"| {gen_stats['generation']} | "
                f"{gen_stats['best_sharpe']:.4f} | "
                f"{gen_stats['mutation_attempts']} | "
                f"{gen_stats['success_rate']:.2%} | "
                f"{gen_stats['unique_patterns']} | "
                f"{gen_stats['time']:.1f}s |\n"
            )

        # Decision Recommendation
        f.write("\n## Decision Recommendation\n\n")
        f.write(f"**Recommendation**: {result['decision']['recommendation_text']}\n\n")

        if decision['recommendation'] == 'PROCEED_TO_PHASE_2A':
            f.write("### Next Steps\n\n")
            f.write("1. Proceed with Phase 2a (Structured Innovation)\n")
            f.write("2. Implement advanced exit strategies (conditional, time-based)\n")
            f.write("3. Add exit strategy combinations and hierarchies\n")
            f.write("4. Monitor continued performance improvement\n")
        elif decision['recommendation'] == 'PROCEED_TO_PHASE_2_0':
            f.write("### Next Steps\n\n")
            f.write("1. Proceed with Phase 2.0 (Full Structural Mutation)\n")
            f.write("2. Implement broader structural changes\n")
            f.write("3. Focus on increasing diversity and exploration\n")
            f.write("4. Monitor Sharpe improvement with new mutations\n")
        else:
            f.write("### Next Steps\n\n")
            f.write("1. Address exit mutation success rate issues\n")
            f.write("2. Fix stability problems before proceeding\n")
            f.write("3. Re-run validation after fixes\n")
            f.write("4. Consider parameter tuning for mutation operator\n")

        # Timing Summary
        f.write("\n## Timing Summary\n\n")
        timing = result['timing']
        f.write(f"- **Total Time**: {timing['total_time']/60:.1f} minutes\n")
        f.write(f"- **Avg Generation Time**: {timing['avg_generation_time']:.1f}s\n")

        params = result['parameters']
        f.write(f"- **Generations Completed**: {params['generations_completed']}/{params['num_generations']}\n")


if __name__ == "__main__":
    main()
