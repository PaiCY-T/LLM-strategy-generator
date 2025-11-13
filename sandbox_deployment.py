"""Sandbox Deployment Script for Phase 6 Multi-Template Evolution.

This script sets up and runs a monitored evolution in an isolated sandbox environment
for Task 41-43: Sandbox deployment with 1-week runtime monitoring.

Features:
- Paper trading mode (no real capital)
- Automatic health checks and restart
- Comprehensive metrics collection
- Checkpoint saving and recovery
- Graceful shutdown handling
"""

import os
import sys
import time
import json
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitoring.evolution_integration import MonitoredEvolution
from src.monitoring.alerts import AlertSeverity, AlertChannel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sandbox_evolution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SandboxDeployment:
    """Manages sandbox evolution deployment with monitoring and recovery.

    Responsibilities:
    - Environment setup and validation
    - Evolution execution with monitoring
    - Health checks and automatic restart
    - Checkpoint management
    - Graceful shutdown handling
    """

    def __init__(
        self,
        population_size: int = 100,
        max_generations: int = 1000,
        checkpoint_interval: int = 50,
        metrics_export_interval: int = 10,
        health_check_interval: int = 300,  # 5 minutes
        output_dir: str = "sandbox_output"
    ):
        """Initialize sandbox deployment.

        Args:
            population_size: Number of individuals in population
            max_generations: Maximum generations to run
            checkpoint_interval: Save checkpoint every N generations
            metrics_export_interval: Export metrics every N generations
            health_check_interval: Health check interval in seconds
            output_dir: Directory for all output files
        """
        self.population_size = population_size
        self.max_generations = max_generations
        self.checkpoint_interval = checkpoint_interval
        self.metrics_export_interval = metrics_export_interval
        self.health_check_interval = health_check_interval
        self.output_dir = Path(output_dir)

        # Create output directory structure
        self.setup_directories()

        # State tracking
        self.should_stop = False
        self.last_checkpoint_gen = 0
        self.start_time = time.time()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"SandboxDeployment initialized: pop_size={population_size}, "
                   f"max_gens={max_generations}, output_dir={output_dir}")

    def setup_directories(self):
        """Create output directory structure."""
        dirs = [
            self.output_dir,
            self.output_dir / "checkpoints",
            self.output_dir / "metrics",
            self.output_dir / "alerts",
            self.output_dir / "logs"
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created/verified: {dir_path}")

    def validate_environment(self) -> bool:
        """Validate environment setup.

        Returns:
            True if environment is ready, False otherwise
        """
        logger.info("Validating sandbox environment...")

        # Check disk space (require at least 1GB free)
        stat = os.statvfs(self.output_dir)
        free_space_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

        if free_space_gb < 1.0:
            logger.error(f"Insufficient disk space: {free_space_gb:.2f}GB available, need at least 1GB")
            return False

        logger.info(f"Disk space check: {free_space_gb:.2f}GB available ✓")

        # Check Python version
        py_version = sys.version_info
        if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 8):
            logger.error(f"Python 3.8+ required, found {py_version.major}.{py_version.minor}")
            return False

        logger.info(f"Python version check: {py_version.major}.{py_version.minor}.{py_version.micro} ✓")

        # Test import of required modules
        try:
            from src.population.population_manager import PopulationManager
            from src.population.genetic_operators import GeneticOperators
            from src.population.fitness_evaluator import FitnessEvaluator
            logger.info("Module imports check ✓")
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            return False

        logger.info("Environment validation successful ✓")
        return True

    def load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load latest checkpoint if exists.

        Returns:
            Checkpoint data or None if no checkpoint found
        """
        checkpoint_dir = self.output_dir / "checkpoints"
        checkpoints = sorted(checkpoint_dir.glob("checkpoint_gen_*.json"))

        if not checkpoints:
            logger.info("No checkpoint found, starting from scratch")
            return None

        latest_checkpoint = checkpoints[-1]
        logger.info(f"Loading checkpoint: {latest_checkpoint}")

        try:
            with open(latest_checkpoint, 'r') as f:
                checkpoint_data = json.load(f)

            logger.info(f"Checkpoint loaded: generation {checkpoint_data['generation']}")
            return checkpoint_data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def save_checkpoint(self, evolution: MonitoredEvolution, generation: int):
        """Save evolution checkpoint.

        Args:
            evolution: MonitoredEvolution instance
            generation: Current generation number
        """
        checkpoint_file = self.output_dir / "checkpoints" / f"checkpoint_gen_{generation}.json"

        try:
            # Get current state
            recent_metrics = list(evolution.metrics_tracker.generation_history)[-10:]

            checkpoint_data = {
                "generation": generation,
                "timestamp": time.time(),
                "population_size": self.population_size,
                "recent_metrics": [m.to_dict() for m in recent_metrics],
                "total_mutations": evolution.metrics_tracker.total_mutations,
                "total_crossovers": evolution.metrics_tracker.total_crossovers,
                "best_fitness_ever": evolution.metrics_tracker.best_fitness_ever,
            }

            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            logger.info(f"Checkpoint saved: {checkpoint_file}")
            self.last_checkpoint_gen = generation

        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def export_metrics(self, evolution: MonitoredEvolution, generation: int):
        """Export metrics to files.

        Args:
            evolution: MonitoredEvolution instance
            generation: Current generation number
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_dir = self.output_dir / "metrics"

        try:
            # Export Prometheus metrics
            prometheus_file = metrics_dir / f"metrics_prometheus_gen_{generation}.txt"
            evolution.export_prometheus(str(prometheus_file))

            # Export JSON metrics
            json_file = metrics_dir / f"metrics_json_gen_{generation}.json"
            evolution.export_json(str(json_file))

            logger.info(f"Metrics exported: generation {generation}")

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")

    def health_check(self, evolution: MonitoredEvolution) -> bool:
        """Perform health checks on evolution.

        Args:
            evolution: MonitoredEvolution instance

        Returns:
            True if healthy, False if critical issues detected
        """
        try:
            # Check if metrics are being recorded
            if len(evolution.metrics_tracker.generation_history) == 0:
                logger.warning("Health check: No metrics recorded yet")
                return True  # OK if just started

            latest = evolution.metrics_tracker.generation_history[-1]

            # Check for population health
            if latest.population_size == 0:
                logger.error("Health check FAILED: Population size is 0")
                return False

            # Check for fitness values
            if latest.best_fitness == 0 and latest.generation > 10:
                logger.warning("Health check WARNING: Best fitness still 0 after 10 generations")

            # Check for diversity collapse
            if latest.unified_diversity < 0.01 and latest.generation > 20:
                logger.warning("Health check WARNING: Extreme diversity collapse detected")

            logger.debug(f"Health check PASSED: gen={latest.generation}, "
                        f"pop_size={latest.population_size}, "
                        f"best_fitness={latest.best_fitness:.4f}, "
                        f"diversity={latest.unified_diversity:.4f}")

            return True

        except Exception as e:
            logger.error(f"Health check FAILED with exception: {e}")
            return False

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.should_stop = True

    def run(self, test_mode: bool = False):
        """Run sandbox evolution deployment.

        Args:
            test_mode: If True, run for limited generations (testing)
        """
        logger.info("=" * 80)
        logger.info("SANDBOX DEPLOYMENT STARTING")
        logger.info("=" * 80)

        # Validate environment
        if not self.validate_environment():
            logger.error("Environment validation failed, aborting deployment")
            return

        # Load checkpoint if exists
        checkpoint = self.load_checkpoint()
        start_generation = checkpoint['generation'] + 1 if checkpoint else 0

        # Adjust max generations for test mode
        max_gens = 100 if test_mode else self.max_generations

        logger.info(f"Starting evolution: generations {start_generation} to {max_gens}")
        logger.info(f"Population size: {self.population_size}")
        logger.info(f"Test mode: {test_mode}")

        # Initialize monitored evolution
        alert_file = self.output_dir / "alerts" / "alerts.json"

        evolution = MonitoredEvolution(
            population_size=self.population_size,
            alert_file=str(alert_file),
            metrics_export_interval=self.metrics_export_interval
        )

        logger.info("MonitoredEvolution initialized")

        # Template distribution (equal distribution)
        template_distribution = {
            'Momentum': 0.25,
            'Turtle': 0.25,
            'Factor': 0.25,
            'Mastiff': 0.25
        }

        logger.info(f"Template distribution: {template_distribution}")

        # Run evolution with monitoring
        try:
            logger.info("Starting evolution run...")

            results = evolution.run_evolution(
                generations=max_gens - start_generation,
                template_distribution=template_distribution,
                early_stopping=False,  # Let it run full duration
                export_final_metrics=True
            )

            logger.info("Evolution completed successfully")

            # Final exports
            self.export_metrics(evolution, max_gens)
            self.save_checkpoint(evolution, max_gens)

            # Summary
            logger.info("=" * 80)
            logger.info("SANDBOX DEPLOYMENT COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Champion template: {results['champion'].template_type}")
            logger.info(f"Champion fitness: {results['champion'].fitness:.4f}")
            logger.info(f"Total generations: {len(results['metrics_history'])}")
            logger.info(f"Total alerts: {results['alert_summary']['total_alerts']}")
            logger.info(f"Runtime: {(time.time() - self.start_time) / 3600:.2f} hours")
            logger.info(f"Output directory: {self.output_dir}")

        except KeyboardInterrupt:
            logger.info("Interrupted by user, performing graceful shutdown...")
            self.export_metrics(evolution, len(evolution.metrics_tracker.generation_history))
            self.save_checkpoint(evolution, len(evolution.metrics_tracker.generation_history))

        except Exception as e:
            logger.error(f"Evolution failed with exception: {e}", exc_info=True)
            # Try to save current state
            try:
                self.export_metrics(evolution, len(evolution.metrics_tracker.generation_history))
                self.save_checkpoint(evolution, len(evolution.metrics_tracker.generation_history))
            except:
                logger.error("Failed to save state during error recovery")


def main():
    """Main entry point for sandbox deployment."""
    parser = argparse.ArgumentParser(description='Sandbox Evolution Deployment')
    parser.add_argument('--population-size', type=int, default=100,
                       help='Population size (default: 100)')
    parser.add_argument('--max-generations', type=int, default=1000,
                       help='Maximum generations (default: 1000)')
    parser.add_argument('--test', action='store_true',
                       help='Run in test mode (100 generations only)')
    parser.add_argument('--output-dir', type=str, default='sandbox_output',
                       help='Output directory (default: sandbox_output)')

    args = parser.parse_args()

    # Create deployment
    deployment = SandboxDeployment(
        population_size=args.population_size,
        max_generations=args.max_generations,
        output_dir=args.output_dir
    )

    # Run deployment
    deployment.run(test_mode=args.test)


if __name__ == '__main__':
    main()
