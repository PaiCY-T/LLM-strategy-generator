#!/usr/bin/env python3
"""
60-Iteration Three-Mode Test (20 iterations × 3 modes)

Runs 20 iterations each across THREE strategy generation modes:
1. Factor Graph Only Mode (innovation_rate=0%)
2. LLM Only Mode (innovation_rate=100%)
3. Hybrid Mode (innovation_rate=50%)

Total: 60 iterations to compare three generation approaches

Usage:
    python3 run_20iteration_three_mode_test.py
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Add src to path for LearningLoop import
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop


def setup_logging(base_output_dir: str) -> logging.Logger:
    """Configure comprehensive logging for three-mode validation run.

    Args:
        base_output_dir: Base directory for output files

    Returns:
        Logger instance
    """
    log_dir = Path(base_output_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"60iteration_three_mode_test_{timestamp}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized: {log_file}")
    return logger


def run_mode_test(
    mode_name: str,
    config_path: str,
    logger: logging.Logger,
    base_output_dir: Path
) -> dict:
    """Run test for a specific generation mode (20 iterations from config file).

    Args:
        mode_name: Human-readable mode name (e.g., "Factor Graph Only")
        config_path: Path to YAML configuration file
        logger: Logger instance
        base_output_dir: Base directory for results

    Returns:
        dict: Test results including success rate, Sharpe ratios, metrics
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info(f"STARTING MODE: {mode_name}")
    logger.info("=" * 80)
    logger.info(f"Config File: {config_path}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("")

    try:
        # Load configuration from YAML
        config = LearningConfig.from_yaml(config_path)
        logger.info(f"✓ Configuration loaded successfully")
        logger.info(f"  Max Iterations: {config.max_iterations}")
        logger.info(f"  Innovation Mode: {config.innovation_mode}")
        logger.info(f"  Innovation Rate: {config.innovation_rate * 100:.0f}%")
        logger.info(f"  LLM Model: {config.llm_model}")
        logger.info("")

        # Initialize learning loop
        logger.info("Initializing LearningLoop...")
        loop = LearningLoop(config)
        logger.info("✓ LearningLoop initialized successfully")
        logger.info("")

        # Run iterations
        logger.info(f"Starting {config.max_iterations} iterations for {mode_name}...")
        logger.info("(This will take approximately 6-12 minutes depending on system performance)")
        logger.info("")

        start_time = datetime.now()
        loop.run()
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("")
        logger.info(f"✓ {mode_name} completed in {duration:.2f}s ({duration/60:.1f} minutes)")
        logger.info("")

        # Collect results from innovations.jsonl
        results = {
            "mode_name": mode_name,
            "config_path": config_path,
            "duration_seconds": duration,
            "total_iterations": config.max_iterations,
            "successful_iterations": 0,
            "success_rate": 0.0,
            "level_0_count": 0,
            "level_1_count": 0,
            "level_2_count": 0,
            "level_3_count": 0,
            "avg_sharpe": 0.0,
            "best_sharpe": 0.0,
            "champion_sharpe": 0.0,
            "errors": 0,
            "timestamp": datetime.now().isoformat()
        }

        # Read innovations.jsonl to extract metrics
        innovations_file = Path(config.history_file)
        if innovations_file.exists():
            sharpe_ratios = []
            with open(innovations_file, 'r') as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        classification = record.get("classification_level", "LEVEL_0")
                        
                        # Count classifications
                        if classification == "LEVEL_0":
                            results["level_0_count"] += 1
                        elif classification == "LEVEL_1":
                            results["level_1_count"] += 1
                        elif classification == "LEVEL_2":
                            results["level_2_count"] += 1
                        elif classification == "LEVEL_3":
                            results["level_3_count"] += 1
                            results["successful_iterations"] += 1
                        
                        # Collect Sharpe ratios
                        exec_result = record.get("execution_result", {})
                        sharpe = exec_result.get("sharpe_ratio", 0.0)
                        if sharpe is not None and sharpe > 0:
                            sharpe_ratios.append(sharpe)
                    except json.JSONDecodeError:
                        results["errors"] += 1

            # Calculate metrics
            if sharpe_ratios:
                results["avg_sharpe"] = sum(sharpe_ratios) / len(sharpe_ratios)
                results["best_sharpe"] = max(sharpe_ratios)
            
            results["success_rate"] = results["successful_iterations"] / results["total_iterations"]

        # Get champion Sharpe from champion.json
        champion_file = Path(config.champion_file)
        if champion_file.exists():
            with open(champion_file, 'r') as f:
                champion_data = json.load(f)
                results["champion_sharpe"] = champion_data.get("sharpe_ratio", 0.0)

        return results

    except Exception as e:
        logger.error(f"Error running {mode_name}: {e}", exc_info=True)
        return {
            "mode_name": mode_name,
            "config_path": config_path,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def main():
    """Run 60-iteration three-mode validation test."""
    # Setup
    base_output_dir = "experiments/llm_learning_validation/results/20iteration_three_mode"
    logger = setup_logging(base_output_dir)

    logger.info("")
    logger.info("=" * 80)
    logger.info("60-ITERATION THREE-MODE TEST")
    logger.info("=" * 80)
    test_start_time = datetime.now()
    logger.info(f"Test Start Time: {test_start_time.isoformat()}")
    logger.info(f"Output Directory: {base_output_dir}")
    logger.info("")
    logger.info("MODE CONFIGURATION:")
    logger.info("  1. Factor Graph Only: 20 iterations (0% LLM)")
    logger.info("  2. LLM Only: 20 iterations (100% LLM)")
    logger.info("  3. Hybrid: 20 iterations (50% LLM + 50% FG)")
    logger.info("  TOTAL: 60 iterations")
    logger.info("")

    # Define test modes
    test_modes = [
        {
            "name": "Factor Graph Only",
            "config": "experiments/llm_learning_validation/config_fg_only_20.yaml"
        },
        {
            "name": "LLM Only",
            "config": "experiments/llm_learning_validation/config_llm_only_20.yaml"
        },
        {
            "name": "Hybrid",
            "config": "experiments/llm_learning_validation/config_hybrid_20.yaml"
        }
    ]

    # Run all modes
    all_results = []
    for mode in test_modes:
        results = run_mode_test(
            mode_name=mode["name"],
            config_path=mode["config"],
            logger=logger,
            base_output_dir=Path(base_output_dir)
        )
        all_results.append(results)

    # Calculate overall statistics
    test_end_time = datetime.now()
    total_duration = (test_end_time - test_start_time).total_seconds()

    # Save comprehensive results
    output_file = Path(base_output_dir) / f"results_{test_start_time.strftime('%Y%m%d_%H%M%S')}.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    comprehensive_results = {
        "test_name": "60-iteration-three-mode-test",
        "test_date": test_start_time.isoformat(),
        "overall_duration_seconds": total_duration,
        "total_iterations": 60,
        "modes": all_results
    }

    with open(output_file, 'w') as f:
        json.dump(comprehensive_results, f, indent=2)

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
    logger.info(f"Total Iterations: 60 (20 × 3 modes)")
    logger.info("")

    for result in all_results:
        if "error" not in result:
            logger.info(f"{result['mode_name']}:")
            logger.info(f"  Success Rate: {result['success_rate']*100:.1f}%")
            logger.info(f"  Classification Breakdown:")
            logger.info(f"    LEVEL_0: {result['level_0_count']}")
            logger.info(f"    LEVEL_1: {result['level_1_count']}")
            logger.info(f"    LEVEL_2: {result['level_2_count']}")
            logger.info(f"    LEVEL_3: {result['level_3_count']}")
            logger.info(f"  Avg Sharpe: {result['avg_sharpe']:.4f}")
            logger.info(f"  Best Sharpe: {result['best_sharpe']:.4f}")
            logger.info(f"  Champion Sharpe: {result['champion_sharpe']:.4f}")
            logger.info(f"  Duration: {result['duration_seconds']:.2f}s")
            logger.info("")

    logger.info(f"Results saved to: {output_file}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
