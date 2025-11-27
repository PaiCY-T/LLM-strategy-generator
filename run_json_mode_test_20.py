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
from pathlib import Path
from datetime import datetime

# Setup logging
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/json_mode_test_{timestamp}.log"
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def verify_config(config):
    """驗證 JSON mode 配置正確"""
    assert config.template_mode is True, "template_mode must be True for JSON mode"
    assert config.use_json_mode is True, "use_json_mode must be True"
    assert config.generation_mode == 'json', f"generation_mode must be 'json', got '{config.generation_mode}'"
    logger.info("✅ JSON Mode configuration verified")
    logger.info(f"  - template_mode: {config.template_mode}")
    logger.info(f"  - template_name: {config.template_name}")
    logger.info(f"  - use_json_mode: {config.use_json_mode}")
    logger.info(f"  - generation_mode: {config.generation_mode}")

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

    # Import LearningLoop
    from src.learning.learning_loop import LearningLoop
    from src.learning.unified_config import UnifiedConfig

    # Create configuration for JSON mode test
    config = UnifiedConfig(
        max_iterations=20,
        llm_model="google/gemini-2.5-flash",

        # Enable Template Mode (Phase 1 已驗證)
        template_mode=True,
        template_name='Momentum',

        # Enable JSON Mode (首次真正測試)
        use_json_mode=True,
        generation_mode='json',

        # Other configuration
        history_file="experiments/llm_learning_validation/results/json_mode_test/history.jsonl",
        champion_file="experiments/llm_learning_validation/results/json_mode_test/champion.json",
        timeout_seconds=420,
        continue_on_error=True,
        log_level="INFO",
        log_to_file=True,
        log_to_console=True,
        log_dir="logs",
        llm_temperature=0.7,
        mutation_rate=0.2
    )

    # Verify JSON mode configuration
    verify_config(config)
    logger.info("")

    logger.info("Converting to LearningConfig for compatibility...")
    learning_config = config.to_learning_config()
    logger.info("")

    logger.info("Initializing LearningLoop with JSON mode...")

    # Create results directory
    Path("experiments/llm_learning_validation/results/json_mode_test").mkdir(parents=True, exist_ok=True)

    # Create and run learning loop
    loop = LearningLoop(config=learning_config)

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
