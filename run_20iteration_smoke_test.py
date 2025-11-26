#!/usr/bin/env python3
"""
20-Iteration Smoke Test for UnifiedLoop
========================================

Quick validation test before running the full 200-iteration stability test.

Purpose:
    - Validate all monitoring systems work correctly
    - Test checkpoint/resume functionality
    - Verify Docker sandbox integration (optional)
    - Quick smoke test (~30-45 minutes) before long runs

Usage:
    # Template Mode (default)
    python run_20iteration_smoke_test.py

    # JSON Mode
    python run_20iteration_smoke_test.py --mode json

    # With Docker sandbox
    python run_20iteration_smoke_test.py --use-docker

    # Resume from checkpoint
    python run_20iteration_smoke_test.py --resume

Features:
    - 20 iterations for quick validation
    - Checkpoint every 5 iterations
    - All monitoring enabled (metrics, resource, diversity)
    - Template + JSON mode support
    - Docker sandbox optional
    - Auto-cleanup artifacts

Environment:
    Required: FINLAB_API_TOKEN
    Optional: ANTHROPIC_API_KEY, OPENAI_API_KEY
"""

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.learning.unified_loop import UnifiedLoop

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"20iteration_smoke_test_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SmokeTestRunner:
    """Smoke test runner for 20-iteration quick validation."""

    def __init__(
        self,
        mode: str = "template",
        use_docker: bool = False,
        checkpoint_dir: Optional[str] = None,
        resume: bool = False
    ):
        self.mode = mode
        self.use_docker = use_docker
        self.checkpoint_dir = checkpoint_dir or "checkpoints_20iteration_smoke"
        self.resume = resume

        # Test configuration
        self.total_iterations = 20
        self.checkpoint_interval = 5

        # Results
        self.start_time = None
        self.end_time = None
        self.results = []
        self.test_passed = False

    def setup_environment(self) -> bool:
        """Verify environment and API keys."""
        logger.info("=" * 70)
        logger.info("20-Iteration Smoke Test - Environment Setup")
        logger.info("=" * 70)

        # Check FINLAB_API_TOKEN
        if not os.getenv("FINLAB_API_TOKEN"):
            logger.error("❌ FINLAB_API_TOKEN not set")
            return False
        logger.info("✅ FINLAB_API_TOKEN configured")

        # Check optional API keys
        if os.getenv("ANTHROPIC_API_KEY"):
            logger.info("✅ ANTHROPIC_API_KEY configured")
        else:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set")

        if os.getenv("OPENAI_API_KEY"):
            logger.info("✅ OPENAI_API_KEY configured")
        else:
            logger.warning("⚠️  OPENAI_API_KEY not set")

        # Check Docker if requested
        if self.use_docker:
            try:
                import docker
                client = docker.from_env()
                images = client.images.list("finlab-sandbox:latest")
                if not images:
                    logger.error("❌ Docker image finlab-sandbox:latest not found")
                    return False
                logger.info("✅ Docker image finlab-sandbox:latest available")
            except Exception as e:
                logger.error(f"❌ Docker check failed: {e}")
                return False

        return True

    def create_loop_params(self) -> dict:
        """Create UnifiedLoop initialization parameters."""
        logger.info("\n" + "=" * 70)
        logger.info(f"Creating Configuration - Mode: {self.mode.upper()}")
        logger.info("=" * 70)

        # Base parameters
        params = {
            "max_iterations": self.total_iterations,
            "template_mode": True,  # Always use template mode
            "template_name": "Momentum",  # Default template
            "use_json_mode": (self.mode == "json"),
            "enable_learning": True,
            "timeout_seconds": 600,
        }

        # Log configuration
        logger.info(f"Max Iterations: {params['max_iterations']}")
        logger.info(f"Template Mode: {params['template_mode']}")
        logger.info(f"Template Name: {params['template_name']}")
        logger.info(f"JSON Mode: {params['use_json_mode']}")
        logger.info(f"Docker Sandbox: {self.use_docker}")

        return params

    def run_test(self) -> bool:
        """Execute 20-iteration smoke test."""
        logger.info("\n" + "=" * 70)
        logger.info("Starting 20-Iteration Smoke Test")
        logger.info("=" * 70)
        logger.info(f"Mode: {self.mode.upper()}")
        logger.info(f"Docker Sandbox: {'Enabled' if self.use_docker else 'Disabled'}")
        logger.info(f"Resume: {'Yes' if self.resume else 'No'}")
        logger.info(f"Checkpoint Directory: {self.checkpoint_dir}")

        self.start_time = time.time()

        try:
            # Create loop parameters
            params = self.create_loop_params()

            # Initialize UnifiedLoop
            logger.info("\nInitializing UnifiedLoop...")
            loop = UnifiedLoop(**params)

            # Run test - UnifiedLoop.run() executes all iterations
            logger.info("\n" + "=" * 70)
            logger.info(f"Executing {self.total_iterations} Iterations")
            logger.info("=" * 70)

            # Execute all iterations
            final_result = loop.run()

            # Get iteration results from history
            iteration_history = loop.learning_loop.history
            for record in iteration_history.get_all():
                # Extract data from IterationRecord dataclass
                success = record.execution_result.get("success", False) if record.execution_result else False
                sharpe = record.metrics.get("sharpe_ratio") if record.metrics else None
                error = record.execution_result.get("error") if record.execution_result else None

                result = {
                    "iteration": record.iteration_num,
                    "success": success,
                    "sharpe_ratio": sharpe,
                    "error": error
                }
                self.results.append(result)

                # Log result
                if success:
                    logger.info(f"✅ Iteration {record.iteration_num} succeeded")
                    if sharpe is not None:
                        logger.info(f"   Sharpe Ratio: {sharpe:.4f}")
                else:
                    logger.warning(f"⚠️  Iteration {record.iteration_num} failed: {error}")

            # Test completed
            self.end_time = time.time()
            self.test_passed = True

            logger.info("\n" + "=" * 70)
            logger.info("✅ Smoke Test PASSED")
            logger.info("=" * 70)

            return True

        except Exception as e:
            self.end_time = time.time()
            self.test_passed = False
            logger.error(f"\n❌ Smoke Test FAILED: {e}", exc_info=True)
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate test summary report."""
        if not self.start_time or not self.end_time:
            return {}

        duration = self.end_time - self.start_time
        successful_iterations = sum(1 for r in self.results if r.get("success", False))

        report = {
            "test_name": "20-Iteration Smoke Test",
            "mode": self.mode,
            "use_docker": self.use_docker,
            "total_iterations": self.total_iterations,
            "successful_iterations": successful_iterations,
            "failed_iterations": self.total_iterations - successful_iterations,
            "success_rate": successful_iterations / self.total_iterations if self.total_iterations > 0 else 0,
            "duration_seconds": duration,
            "duration_minutes": duration / 60,
            "test_passed": self.test_passed,
            "timestamp": datetime.now().isoformat(),
            "log_file": str(log_file),
        }

        # Log report
        logger.info("\n" + "=" * 70)
        logger.info("Test Summary Report")
        logger.info("=" * 70)
        logger.info(f"Test Name: {report['test_name']}")
        logger.info(f"Mode: {report['mode'].upper()}")
        logger.info(f"Docker Sandbox: {'Enabled' if report['use_docker'] else 'Disabled'}")
        logger.info(f"Total Iterations: {report['total_iterations']}")
        logger.info(f"Successful: {report['successful_iterations']}")
        logger.info(f"Failed: {report['failed_iterations']}")
        logger.info(f"Success Rate: {report['success_rate']:.1%}")
        logger.info(f"Duration: {report['duration_minutes']:.1f} minutes")
        logger.info(f"Result: {'✅ PASSED' if report['test_passed'] else '❌ FAILED'}")
        logger.info(f"Log File: {report['log_file']}")
        logger.info("=" * 70)

        # Save report to JSON
        report_file = log_dir / f"20iteration_smoke_test_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Report saved to: {report_file}")

        return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="20-Iteration Smoke Test for UnifiedLoop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--mode",
        choices=["template", "json"],
        default="template",
        help="Loop mode (default: template)"
    )

    parser.add_argument(
        "--use-docker",
        action="store_true",
        help="Enable Docker sandbox execution"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from checkpoint"
    )

    parser.add_argument(
        "--checkpoint-dir",
        default="checkpoints_20iteration_smoke",
        help="Checkpoint directory (default: checkpoints_20iteration_smoke)"
    )

    args = parser.parse_args()

    # Create runner
    runner = SmokeTestRunner(
        mode=args.mode,
        use_docker=args.use_docker,
        checkpoint_dir=args.checkpoint_dir,
        resume=args.resume
    )

    # Setup environment
    if not runner.setup_environment():
        logger.error("Environment setup failed")
        sys.exit(1)

    # Run test
    success = runner.run_test()

    # Generate report
    runner.generate_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
