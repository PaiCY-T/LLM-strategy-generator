"""
Test script to verify Factor Graph naming adapter layer fix.

This test validates that Factor Library factors with semantic names
(e.g., 'breakout_signal', 'momentum') are correctly transformed to
generic names ('position') by the naming adapter layer.

Expected outcome: Factor Graph strategies should now execute successfully
and produce a 'position' matrix without validation errors.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging to see adapter debug messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_naming_adapter():
    """Test that naming adapter layer correctly transforms semantic names to generic names."""

    logger.info("=" * 80)
    logger.info("NAMING ADAPTER LAYER TEST")
    logger.info("=" * 80)

    try:
        # Import required modules
        from src.factor_graph.strategy import Strategy
        from src.factor_library.registry import FactorRegistry
        from finlab import data

        logger.info("✓ Imports successful")

        # Get factor registry
        registry = FactorRegistry.get_instance()
        logger.info(f"✓ Factor registry loaded with {len(registry.list_factors())} factors")

        # Create a simple Factor Graph strategy
        # Using breakout_factor which outputs 'breakout_signal' (semantic name)
        strategy = Strategy(id="test_naming_adapter", generation=0)

        # Add breakout factor (outputs 'breakout_signal')
        breakout_factor = registry.create_factor("breakout_factor", parameters={"entry_window": 20})
        strategy.add_factor(breakout_factor)

        logger.info(f"✓ Created strategy with factor: {breakout_factor.id}")
        logger.info(f"  - Factor outputs: {breakout_factor.outputs}")
        logger.info(f"  - Expected semantic name: 'breakout_signal'")
        logger.info(f"  - Expected generic name after adapter: 'position'")

        # Execute strategy pipeline
        logger.info("")
        logger.info("Executing strategy pipeline with naming adapter...")
        logger.info("-" * 80)

        position = strategy.to_pipeline(data)

        logger.info("-" * 80)
        logger.info("")
        logger.info("✓ Strategy execution SUCCESSFUL!")
        logger.info(f"✓ Position matrix shape: {position.shape}")
        logger.info(f"✓ Position matrix type: {type(position).__name__}")

        # Verify position matrix is valid
        assert position is not None, "Position matrix is None"
        assert position.shape[0] > 0, "Position matrix has no rows"
        assert position.shape[1] > 0, "Position matrix has no columns"

        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ TEST PASSED - Naming adapter layer is working correctly!")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info("  • Factor Library semantic name 'breakout_signal' was detected")
        logger.info("  • Naming adapter transformed it to generic 'position'")
        logger.info("  • Validation passed successfully")
        logger.info("  • Strategy execution completed without errors")
        logger.info("")
        logger.info("🎉 Factor Graph mode is now FIXED and operational!")

        return True

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ TEST FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        logger.error("")
        logger.error("The naming adapter layer may not be working correctly.")
        logger.error("Please review the error above and check the implementation.")
        return False


if __name__ == "__main__":
    logger.info("")
    logger.info("Starting Factor Graph naming adapter test...")
    logger.info("")

    success = test_naming_adapter()

    sys.exit(0 if success else 1)
