"""
Test JSON Mode Generation - 20 Iterations LLM-Only

Bug #3 Fix Validation:
- Tests new JSON parameter generation mode
- LLM generates ONLY entry/exit condition parameters
- Templates provide code structure
- Validates against example/ directory pattern
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Fix Unicode encoding for Windows cp950
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/json_mode_test_{timestamp}.log"
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run 20-iteration JSON mode test."""

    logger.info("=" * 80)
    logger.info("JSON MODE TEST - 20 ITERATIONS LLM-ONLY")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Bug #3 Fix Validation:")
    logger.info("  - JSON parameter generation mode")
    logger.info("  - LLM generates entry/exit condition parameters only")
    logger.info("  - Templates provide code structure")
    logger.info("  - Matches example/ directory pattern")
    logger.info("")
    logger.info("Configuration:")
    logger.info("  - Generation Mode: JSON (parameters only)")
    logger.info("  - Template: MomentumTemplate")
    logger.info("  - Innovation Rate: 100% (llm_only)")
    logger.info("  - Model: google/gemini-2.5-flash")
    logger.info("  - Max Iterations: 20")
    logger.info(f"  - Log File: {log_file}")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Import UnifiedLoop (supports Template Mode + JSON Mode)
    from src.learning.unified_loop import UnifiedLoop

    logger.info("Initializing UnifiedLoop with JSON mode...")

    # Create results directory
    Path("experiments/llm_learning_validation/results/json_mode_test").mkdir(parents=True, exist_ok=True)

    # Create and run unified loop (no config conversion needed!)
    loop = UnifiedLoop(
        model="google/gemini-2.5-flash",  # OpenRouter paid model
        max_iterations=20,

        # Enable Template Mode (Phase 1 validated)
        template_mode=True,
        template_name='Momentum',

        # Enable JSON Mode (first real test)
        use_json_mode=True,

        # Pure LLM mode
        enable_learning=True,

        # File paths
        history_file="experiments/llm_learning_validation/results/json_mode_test/history.jsonl",
        champion_file="experiments/llm_learning_validation/results/json_mode_test/champion.json",
        config_file="config/learning_system.yaml",

        # Backtest settings
        timeout_seconds=420,

        # Other settings
        continue_on_error=True,
        log_level="INFO",
        log_to_file=True,
        log_to_console=True,
        log_dir="logs",
        llm_temperature=0.7,
        innovation_rate=100.0  # Pure LLM mode
    )

    # Verify configuration
    logger.info("")
    logger.info("JSON Mode Configuration:")
    logger.info(f"  - template_mode: {loop.template_mode}")
    logger.info(f"  - template_name: {loop.config.template_name}")
    logger.info(f"  - use_json_mode: {loop.use_json_mode}")
    logger.info(f"  - innovation_rate: {loop.config.innovation_rate}% (Pure LLM)")

    logger.info("Starting learning loop...")
    logger.info("")

    # Run the loop
    try:
        loop.run()
        logger.info("")
        logger.info("=" * 80)
        logger.info("JSON MODE TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Validation Results:")
        logger.info(f"  - Log File: {log_file}")
        logger.info(f"  - History: experiments/llm_learning_validation/results/json_mode_test/history.jsonl")
        logger.info(f"  - Champion: experiments/llm_learning_validation/results/json_mode_test/champion.json")
        logger.info("")
        logger.info("Next Steps:")
        logger.info("  1. Check log file for LLM success rate (should be > 0%)")
        logger.info("  2. Verify generated code matches example/ directory pattern")
        logger.info("  3. If successful, disable full_code and yaml modes")
        logger.info("")
        return 0

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("=" * 80)
        logger.warning("TEST INTERRUPTED BY USER")
        logger.warning("=" * 80)
        return 1

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error(f"TEST FAILED: {e}")
        logger.error("=" * 80)
        logger.exception("Full traceback:")
        return 2

if __name__ == "__main__":
    sys.exit(main())
