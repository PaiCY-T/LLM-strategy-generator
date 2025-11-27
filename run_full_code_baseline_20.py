"""Run 20-iteration baseline test with FULL CODE mode (no JSON mode).

This baseline test is part of Phase 2.3 to compare JSON mode vs full code mode.

Test Configuration:
- template_mode=False (full code generation by LLM)
- use_json_mode=False (no JSON parameter output)
- innovation_rate=100.0 (pure LLM mode)
- max_iterations=20

Expected Behavior:
- LLM generates complete strategy code (not just parameters)
- No template caching (slower but more flexible)
- Direct comparison baseline for JSON mode testing

Success Criteria:
- All 20 iterations complete
- Valid metrics extracted
- Success rate measured
- Comparison with JSON mode test results
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Fix Unicode encoding for Windows cp950
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Configure logging
log_file = f'logs/full_code_baseline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
os.makedirs('logs', exist_ok=True)

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
    """Run full code baseline test."""
    logger.info("=" * 80)
    logger.info("Phase 2.3: Full Code Baseline Test (20 iterations)")
    logger.info("=" * 80)

    # Test configuration
    logger.info("\nTest Configuration:")
    logger.info("  - Mode: FULL CODE (no template, no JSON mode)")
    logger.info("  - Model: google/gemini-2.5-flash")
    logger.info("  - Iterations: 20")
    logger.info("  - Innovation Rate: 100.0% (Pure LLM)")
    logger.info("  - Output: experiments/llm_learning_validation/results/full_code_baseline/")

    # Import after environment setup
    from src.learning.unified_loop import UnifiedLoop

    # Create output directory
    output_dir = "experiments/llm_learning_validation/results/full_code_baseline"
    os.makedirs(output_dir, exist_ok=True)

    # Initialize UnifiedLoop with FULL CODE mode
    logger.info("\nInitializing UnifiedLoop with FULL CODE configuration...")

    try:
        loop = UnifiedLoop(
            model="google/gemini-2.5-flash",
            max_iterations=20,
            template_mode=False,  # [CRITICAL] Full code generation by LLM
            use_json_mode=False,  # [CRITICAL] No JSON parameter output
            enable_learning=True,
            innovation_rate=100.0,  # Pure LLM mode (no Factor Graph)
            history_file=f"{output_dir}/history.jsonl",
            champion_file=f"{output_dir}/champion.json",
            timeout_seconds=420,
            continue_on_error=True,
        )

        logger.info("[OK] UnifiedLoop initialized successfully")
        logger.info("\nConfiguration Verification:")
        logger.info(f"  - template_mode: {loop.config.template_mode}")
        logger.info(f"  - use_json_mode: {loop.config.use_json_mode}")
        logger.info(f"  - innovation_rate: {loop.config.innovation_rate}% (Pure LLM)")

        # Run test
        logger.info("\n" + "=" * 80)
        logger.info("Starting Full Code Baseline Test Execution")
        logger.info("=" * 80)
        logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Expected Duration: 20-60 minutes (full code generation is slower)")
        logger.info("")

        # Execute learning loop
        loop.run()

        # Test completion
        logger.info("\n" + "=" * 80)
        logger.info("Full Code Baseline Test Completed")
        logger.info("=" * 80)
        logger.info(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Log File: {log_file}")
        logger.info(f"History: {output_dir}/history.jsonl")
        logger.info(f"Champion: {output_dir}/champion.json")

        # Verify output files
        history_file = f"{output_dir}/history.jsonl"
        champion_file = f"{output_dir}/champion.json"

        if os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                line_count = sum(1 for _ in f)
            logger.info(f"\n[OK] History file created: {line_count} iterations")
        else:
            logger.warning(f"\n[WARN] History file not found: {history_file}")

        if os.path.exists(champion_file):
            logger.info(f"[OK] Champion file created: {champion_file}")
        else:
            logger.warning(f"[WARN] Champion file not found: {champion_file}")

        logger.info("\n" + "=" * 80)
        logger.info("SUCCESS: Full Code Baseline Test Complete")
        logger.info("=" * 80)
        logger.info("\nNext Steps:")
        logger.info("1. Verify results with: python3 analyze_baseline_results.py")
        logger.info("2. Compare with JSON mode: python3 compare_json_vs_baseline.py")
        logger.info("3. Review detailed log: cat " + log_file)

    except Exception as e:
        logger.error("\n" + "=" * 80)
        logger.error("FAILED: Full Code Baseline Test Error")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()
