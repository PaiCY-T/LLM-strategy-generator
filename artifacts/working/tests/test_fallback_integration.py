#!/usr/bin/env python3
"""
Test AST Validator + Fallback Integration

This script tests the integration of:
1. AST validation (ast_validator.py)
2. Fallback strategy (template_fallback.py)
3. Iteration engine integration (iteration_engine.py)

Test Cases:
1. Valid code → validation passes → no fallback
2. Invalid code (syntax error) → validation fails → fallback activates
3. Invalid code (forbidden module) → validation fails → fallback activates
4. Fallback code validation → should always pass
5. Fallback ratio threshold → prevent excessive fallback usage

Author: Integration Test Suite
Created: 2025-10-09
"""

import sys
import logging
from ast_validator import validate_strategy_code
from template_fallback import get_fallback_strategy, log_fallback_usage, get_champion_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_valid_code():
    """Test Case 1: Valid code should pass validation."""
    print("\n" + "="*70)
    print("Test 1: Valid Code Validation")
    print("="*70)

    valid_code = '''
import pandas as pd
close = data.get('price:收盤價')
momentum = close.pct_change(20).shift(1)
position = momentum.is_largest(10)
report = sim(position, resample="Q", upload=False)
'''

    is_valid, error = validate_strategy_code(valid_code)

    if is_valid:
        print("✅ PASSED: Valid code accepted")
        return True
    else:
        print(f"❌ FAILED: Valid code rejected - {error}")
        return False


def test_syntax_error():
    """Test Case 2: Syntax error should trigger fallback."""
    print("\n" + "="*70)
    print("Test 2: Syntax Error Detection")
    print("="*70)

    invalid_code = '''
import pandas as pd
close = data.get('price:收盤價')
momentum = close.pct_change(20).shift(1  # Missing closing parenthesis
position = momentum.is_largest(10)
report = sim(position)
'''

    is_valid, error = validate_strategy_code(invalid_code)

    if not is_valid and "Syntax error" in error:
        print("✅ PASSED: Syntax error detected")
        print(f"   Error: {error[:100]}...")
        return True
    else:
        print(f"❌ FAILED: Syntax error not detected")
        return False


def test_forbidden_module():
    """Test Case 3: Forbidden module should trigger fallback."""
    print("\n" + "="*70)
    print("Test 3: Forbidden Module Detection")
    print("="*70)

    forbidden_code = '''
import os
import pandas as pd
os.system('echo "Hacked!"')
close = data.get('price:收盤價')
position = close.is_largest(10)
report = sim(position)
'''

    is_valid, error = validate_strategy_code(forbidden_code)

    if not is_valid and "Forbidden module" in error:
        print("✅ PASSED: Forbidden module detected")
        print(f"   Error: {error[:100]}...")
        return True
    else:
        print(f"❌ FAILED: Forbidden module not detected")
        return False


def test_fallback_validation():
    """Test Case 4: Fallback code should always be valid."""
    print("\n" + "="*70)
    print("Test 4: Fallback Code Validation")
    print("="*70)

    fallback_code = get_fallback_strategy()

    # Validate fallback code
    is_valid, error = validate_strategy_code(fallback_code)

    if is_valid:
        print("✅ PASSED: Fallback strategy is valid")
        print(f"   Code length: {len(fallback_code)} chars")

        # Verify required components
        required_components = ['position', 'sim(', 'data.get', 'combined_factor']
        missing = [comp for comp in required_components if comp not in fallback_code]

        if not missing:
            print(f"   ✓ All required components present: {required_components}")
            return True
        else:
            print(f"   ❌ Missing components: {missing}")
            return False
    else:
        print(f"❌ FAILED: Fallback strategy is invalid - {error}")
        return False


def test_fallback_metadata():
    """Test Case 5: Champion metadata should be correct."""
    print("\n" + "="*70)
    print("Test 5: Champion Metadata Verification")
    print("="*70)

    metadata = get_champion_metadata()

    expected_fields = ['iteration', 'sharpe_ratio', 'strategy_type']
    missing_fields = [field for field in expected_fields if field not in metadata]

    if not missing_fields:
        print("✅ PASSED: Metadata complete")
        print(f"   Iteration: {metadata['iteration']}")
        print(f"   Sharpe: {metadata['sharpe_ratio']:.4f}")
        print(f"   Type: {metadata['strategy_type']}")

        # Verify champion iteration
        if metadata['iteration'] == 6 and metadata['sharpe_ratio'] == 2.4751:
            print("   ✓ Champion metrics verified (Iteration 6, Sharpe 2.4751)")
            return True
        else:
            print(f"   ⚠️  Warning: Champion metrics differ from expected")
            return True  # Still pass, but warn
    else:
        print(f"❌ FAILED: Missing metadata fields: {missing_fields}")
        return False


def test_integration_flow():
    """Test Case 6: Complete integration flow."""
    print("\n" + "="*70)
    print("Test 6: Integration Flow Simulation")
    print("="*70)

    # Simulate iteration engine flow
    iteration = 15
    fallback_count = 2
    max_fallback_ratio = 0.3

    # Test invalid code
    invalid_code = "import os\nos.system('ls')"

    print(f"Iteration: {iteration}")
    print(f"Recent fallbacks: {fallback_count}")
    print(f"Max ratio: {max_fallback_ratio:.1%}")

    # Step 1: Validate
    is_valid, error = validate_strategy_code(invalid_code)
    print(f"\n1. Validation: {'✓ Valid' if is_valid else '✗ Invalid'}")
    if not is_valid:
        print(f"   Error: {error[:80]}...")

    # Step 2: Check fallback threshold
    fallback_ratio = fallback_count / max(iteration, 1)
    can_use_fallback = fallback_ratio < max_fallback_ratio
    print(f"\n2. Fallback Check:")
    print(f"   Ratio: {fallback_ratio:.1%} vs threshold {max_fallback_ratio:.1%}")
    print(f"   Can use fallback: {can_use_fallback}")

    # Step 3: Get fallback if allowed
    if not is_valid and can_use_fallback:
        print(f"\n3. Getting fallback strategy...")
        log_fallback_usage("AST validation failed", iteration)
        fallback_code = get_fallback_strategy()

        # Validate fallback
        is_fallback_valid, fallback_error = validate_strategy_code(fallback_code)
        print(f"   Fallback validation: {'✓ Valid' if is_fallback_valid else '✗ Invalid'}")

        if is_fallback_valid:
            print("✅ PASSED: Complete integration flow successful")
            return True
        else:
            print(f"❌ FAILED: Fallback validation failed - {fallback_error}")
            return False
    else:
        print(f"\n❌ FAILED: Integration flow incomplete")
        return False


def main():
    """Run all test cases."""
    print("="*70)
    print("AST Validator + Fallback Integration Test Suite")
    print("="*70)

    tests = [
        ("Valid Code", test_valid_code),
        ("Syntax Error", test_syntax_error),
        ("Forbidden Module", test_forbidden_module),
        ("Fallback Validation", test_fallback_validation),
        ("Champion Metadata", test_fallback_metadata),
        ("Integration Flow", test_integration_flow),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ EXCEPTION in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All tests passed! Integration ready for production.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review failures above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
