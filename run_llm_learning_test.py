"""100-iteration test with LLM Learning Mode enabled.

This test enables:
1. Template Mode: Uses Momentum golden template for consistent parameters
2. JSON Parameter Output Mode: LLM outputs JSON parameters validated by Pydantic
3. LLM Learning Mode: Uses FeedbackGenerator to provide learning feedback based on performance

Expected outcome:
- 100% validation success rate (from Template + JSON modes)
- Learning feedback loop guiding parameter selection
- Continuous improvement over iterations
"""

import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/llm_learning_test_{Path(__file__).stem}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run 100-iteration test with LLM learning enabled."""

    logger.info("=" * 80)
    logger.info("100-ITERATION TEST WITH LLM LEARNING MODE")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Configuration:")
    logger.info("  - Template Mode: ENABLED (Momentum template)")
    logger.info("  - JSON Mode: ENABLED (Phase 1.1 JSON Parameter Output)")
    logger.info("  - LLM Learning: ENABLED (FeedbackGenerator with performance feedback)")
    logger.info("  - Model: google/gemini-2.5-flash")
    logger.info("  - Max Iterations: 100")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Import LearningLoop
    from src.learning.learning_loop import LearningLoop
    from src.learning.learning_config import LearningConfig

    # Create configuration with learning enabled
    config = LearningConfig(
        max_iterations=100,
        llm_model="google/gemini-2.5-flash",
        history_file="iteration_history.json",
        champion_file="champion.json",
        timeout_seconds=120,
        continue_on_error=True,
        log_level="INFO",
        log_to_file=True,
        log_to_console=True,
        log_dir="logs"
    )

    logger.info("Initializing LearningLoop with LLM learning...")

    # Create and run learning loop
    loop = LearningLoop(config=config)

    logger.info("Starting learning loop...")
    logger.info("")

    # Run the loop
    try:
        loop.run()
        logger.info("")
        logger.info("=" * 80)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
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
