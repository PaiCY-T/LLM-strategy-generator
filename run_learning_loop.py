#!/usr/bin/env python3
"""
Phase 6 Learning Loop Entry Point

Simple script to run the autonomous learning loop with configuration.

Usage:
    # Use default config (config/learning_system.yaml)
    python run_learning_loop.py

    # Use custom config
    python run_learning_loop.py --config path/to/config.yaml

    # Override max iterations
    python run_learning_loop.py --max-iterations 50

    # Resume from previous run
    python run_learning_loop.py --resume

Environment Variables:
    - GEMINI_API_KEY or OPENAI_API_KEY or OPENROUTER_API_KEY: LLM API key
    - MAX_ITERATIONS: Override max_iterations from config
    - LOG_LEVEL: Override log level (DEBUG/INFO/WARNING/ERROR)

Examples:
    # Run 100 iterations with Gemini API
    export GEMINI_API_KEY=your-key-here
    python run_learning_loop.py --max-iterations 100

    # Run with debug logging
    LOG_LEVEL=DEBUG python run_learning_loop.py

    # Resume interrupted run
    python run_learning_loop.py --resume
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Phase 6 Autonomous Learning Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/learning_system.yaml",
        help="Path to YAML config file (default: config/learning_system.yaml)"
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Override max_iterations from config"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last iteration (reads history file)"
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from config"
    )

    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue if iteration fails (don't stop on first error)"
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    print("=" * 60)
    print("Phase 6: Autonomous Learning Loop")
    print("=" * 60)
    print(f"Config file: {args.config}")
    print()

    # Load configuration
    try:
        config = LearningConfig.from_yaml(args.config)
        print(f"✓ Configuration loaded from {args.config}")
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        print(f"Using default configuration")
        config = LearningConfig()

    # Apply command line overrides
    if args.max_iterations is not None:
        config.max_iterations = args.max_iterations
        print(f"  Override: max_iterations = {args.max_iterations}")

    if args.log_level is not None:
        config.log_level = args.log_level
        print(f"  Override: log_level = {args.log_level}")

    if args.continue_on_error:
        config.continue_on_error = True
        print(f"  Override: continue_on_error = True")

    print()

    # Check API key
    if not config.api_key and config.innovation_mode and config.innovation_rate > 0:
        print("⚠️  WARNING: LLM innovation enabled but no API key found!")
        print("   Set GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY")
        print("   Falling back to Factor Graph for all iterations")
        print()

    # Validate configuration
    try:
        config._validate()
        print("✓ Configuration validated")
    except ValueError as e:
        print(f"✗ Invalid configuration: {e}")
        return 1

    print()

    # Create and run learning loop
    try:
        loop = LearningLoop(config)
        print("✓ Learning loop initialized")
        print()

        # Run the loop
        loop.run()

        print()
        print("=" * 60)
        print("✅ Learning loop completed successfully")
        print("=" * 60)
        return 0

    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("⚠️  Interrupted by user (CTRL+C)")
        print("=" * 60)
        print("You can resume by running:")
        print(f"  python {sys.argv[0]} --resume")
        return 130  # Standard exit code for SIGINT

    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Learning loop failed: {e}")
        print("=" * 60)
        logger.exception("Learning loop failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
