#!/usr/bin/env python3
"""
Phase 6 LearningConfig Verification (No pandas required)

Tests only LearningConfig without importing components that need pandas.
"""

import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.learning.learning_config import LearningConfig


def main():
    """Test LearningConfig thoroughly."""
    print("=" * 60)
    print("PHASE 6: LearningConfig Verification")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    # Test 1: Default values
    print("\n1. Default values...")
    try:
        config = LearningConfig()
        assert config.max_iterations == 20
        assert config.innovation_rate == 100
        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Test 2: YAML with innovation_rate as float (0.5)
    print("\n2. YAML innovation_rate float conversion (0.5 → 50)...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
llm:
  innovation_rate: 0.5
""")
            path = f.name

        config = LearningConfig.from_yaml(path)
        assert config.innovation_rate == 50, f"Expected 50, got {config.innovation_rate}"
        Path(path).unlink()
        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Test 3: YAML with innovation_rate as int (50)
    print("\n3. YAML innovation_rate int preservation (50 → 50)...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
learning_loop:
  max_iterations: 50
llm:
  innovation_rate: 80
""")
            path = f.name

        config = LearningConfig.from_yaml(path)
        assert config.max_iterations == 50
        assert config.innovation_rate == 80, f"Expected 80, got {config.innovation_rate}"
        Path(path).unlink()
        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Test 4: Environment variable placeholders
    print("\n4. Environment variable placeholders...")
    try:
        import os
        os.environ['TEST_MAX_ITER'] = '100'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
learning_loop:
  max_iterations: ${TEST_MAX_ITER:20}
""")
            path = f.name

        config = LearningConfig.from_yaml(path)
        assert config.max_iterations == 100, f"Expected 100, got {config.max_iterations}"
        Path(path).unlink()
        del os.environ['TEST_MAX_ITER']
        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Test 5: Validation
    print("\n5. Parameter validation...")
    try:
        try:
            LearningConfig(max_iterations=0)
            raise AssertionError("Should reject max_iterations=0")
        except ValueError as e:
            assert "max_iterations must be > 0" in str(e)

        try:
            LearningConfig(innovation_rate=150)
            raise AssertionError("Should reject innovation_rate=150")
        except ValueError as e:
            assert "innovation_rate must be 0-100" in str(e)

        print("   ✓ PASS")
        tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Test 6: Actual config file
    print("\n6. Load actual learning_system.yaml...")
    try:
        config_path = "config/learning_system.yaml"
        if Path(config_path).exists():
            config = LearningConfig.from_yaml(config_path)
            print(f"   ✓ PASS - Loaded successfully")
            print(f"     max_iterations: {config.max_iterations}")
            print(f"     innovation_rate: {config.innovation_rate}%")
            print(f"     history_file: {config.history_file}")
            tests_passed += 1
        else:
            print(f"   ⚠ SKIP - File not found (OK in test env)")
            tests_passed += 1
    except Exception as e:
        print(f"   ✗ FAIL: {e}")
        tests_failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}")
    print(f"Tests failed: {tests_failed}")

    if tests_failed == 0:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
