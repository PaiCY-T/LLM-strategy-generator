#!/usr/bin/env python3
"""Test integration between iteration_engine and claude_api_client."""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_generate_strategy():
    """Test the generate_strategy function."""
    print("=" * 70)
    print("Testing generate_strategy() function")
    print("=" * 70)

    # Import after setting up logging
    from iteration_engine import generate_strategy

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        print("Set it with: export OPENROUTER_API_KEY='your-key-here'")
        return False

    print(f"✅ API key found: {api_key[:10]}...{api_key[-10:]}")
    print()

    try:
        # Test with iteration 0 (no feedback)
        print("Test 1: Generate strategy for iteration 0 (no feedback)")
        print("-" * 70)

        code = generate_strategy(iteration=0, feedback="")

        print(f"✅ Generated code: {len(code)} characters")
        print()
        print("Code preview (first 500 chars):")
        print("-" * 70)
        print(code[:500])
        print("-" * 70)
        print()

        # Validate code structure
        checks = {
            "Contains 'position'": "position" in code,
            "Contains 'sim('": "sim(" in code,
            "Contains 'data.get('": "data.get(" in code,
            "Contains '.shift(1)'": ".shift(1)" in code,
            "Length > 100 chars": len(code) > 100
        }

        print("Validation checks:")
        all_passed = True
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
            if not passed:
                all_passed = False
        print()

        if not all_passed:
            print("⚠️  Some validation checks failed")
            return False

        # Test with iteration 1 (with feedback)
        print("Test 2: Generate strategy for iteration 1 (with feedback)")
        print("-" * 70)

        feedback = """
Previous iteration had moderate performance:
- Total Return: 5.2%
- Sharpe Ratio: 0.45
- Max Drawdown: -8.1%

Issues identified:
- Strategy was too conservative with only 5 stocks selected
- Momentum signals were too short-term (only 20 days)
- No value factors included

Suggestions:
- Increase stock selection to 8-10 stocks
- Add longer-term momentum (60+ days)
- Consider adding value factors like P/E ratio
"""

        code2 = generate_strategy(iteration=1, feedback=feedback)

        print(f"✅ Generated code: {len(code2)} characters")
        print()
        print("Code preview (first 500 chars):")
        print("-" * 70)
        print(code2[:500])
        print("-" * 70)
        print()

        # Check if code is different from iteration 0
        if code == code2:
            print("⚠️  Warning: Generated code is identical to iteration 0")
        else:
            print("✅ Generated code differs from iteration 0 (feedback was used)")
        print()

        print("=" * 70)
        print("✅ All tests passed!")
        print("=" * 70)
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_generate_strategy()
    sys.exit(0 if success else 1)
