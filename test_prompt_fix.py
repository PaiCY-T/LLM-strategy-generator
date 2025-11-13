#!/usr/bin/env python3
"""
Quick test to validate the prompt template fix.
Runs 3 iterations to verify strategies now execute successfully.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.learning.learning_config import LearningConfig
from src.learning.learning_loop import LearningLoop

def main():
    print("=" * 80)
    print("PROMPT TEMPLATE FIX - VALIDATION TEST")
    print("=" * 80)
    print()
    print("Testing with 3 iterations (LLM Only mode)")
    print("Expected: Strategies should now execute successfully")
    print()

    # Create test configuration
    config = LearningConfig(
        max_iterations=3,
        innovation_mode="llm_only",
        innovation_rate=100,
        llm_model="gemini-2.0-flash-thinking-exp",
        history_file="artifacts/data/test_prompt_fix_innovations.jsonl",
        strategy_pool_path="artifacts/data/test_prompt_fix_pool.pkl",
        enable_factor_graph_v2=False  # Use original mode for quick test
    )

    print(f"Config: {config.max_iterations} iterations, {config.innovation_mode} mode")
    print()

    # Initialize and run
    try:
        loop = LearningLoop(config)
        loop.run()

        # Check results
        all_records = loop.history.get_all()
        total = len(all_records)

        level_0 = sum(1 for r in all_records if r.classification_level == "LEVEL_0")
        level_1_plus = sum(1 for r in all_records if r.classification_level in ["LEVEL_1", "LEVEL_2", "LEVEL_3"])

        # Count error types
        value_errors = sum(
            1 for r in all_records
            if r.classification_level == "LEVEL_0"
            and r.execution_result.get("error_type") == "ValueError"
            and "report" in r.execution_result.get("error_message", "")
        )

        print()
        print("=" * 80)
        print("TEST RESULTS")
        print("=" * 80)
        print(f"Total iterations: {total}")
        print(f"Successful (LEVEL_1+): {level_1_plus}")
        print(f"Failed (LEVEL_0): {level_0}")
        print(f"Missing 'report' errors: {value_errors}")
        print()

        if value_errors == 0:
            print("✅ FIX VERIFIED: No 'missing report' errors!")
            if level_1_plus > 0:
                print(f"✅ EXECUTION SUCCESS: {level_1_plus}/{total} strategies executed successfully")
            else:
                print("⚠️  EXECUTION: Strategies generated but may have other issues (not template-related)")
            return 0
        else:
            print(f"❌ FIX INCOMPLETE: {value_errors} strategies still have 'missing report' error")
            return 1

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
