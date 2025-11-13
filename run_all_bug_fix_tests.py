#!/usr/bin/env python3
"""
Standalone Test Runner for Docker Integration Test Framework
Runs all bug fix tests without pytest to avoid logger conflicts
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "artifacts" / "working" / "modules"))

def test_llm_validation():
    """Test Bug #2 fix: LLM API validation"""
    from src.innovation.llm_strategy_generator import _validate_model_provider_match

    tests_passed = 0
    tests_total = 0

    # Test 1: Valid configurations
    tests_total += 1
    try:
        _validate_model_provider_match('google', 'gemini-2.5-flash')
        _validate_model_provider_match('openrouter', 'anthropic/claude-3.5-sonnet')
        _validate_model_provider_match('openai', 'gpt-4')
        tests_passed += 1
        print("  ✅ Valid configurations accepted")
    except Exception as e:
        print(f"  ❌ Valid configurations failed: {e}")

    # Test 2: Invalid configurations raise ValueError
    tests_total += 1
    try:
        try:
            _validate_model_provider_match('google', 'anthropic/claude-3.5-sonnet')
            print("  ❌ Should have raised ValueError for google+anthropic")
        except ValueError:
            tests_passed += 1
            print("  ✅ Invalid configurations rejected")
    except Exception as e:
        print(f"  ❌ Validation test failed: {e}")

    return tests_passed, tests_total

def test_experiment_config():
    """Test Bug #3 fix: ExperimentConfig module"""
    from src.config.experiment_config import ExperimentConfig

    tests_passed = 0
    tests_total = 0

    # Test 1: Module import
    tests_total += 1
    try:
        config = ExperimentConfig(iteration=1, config_snapshot={'test': 'value'})
        tests_passed += 1
        print("  ✅ ExperimentConfig module exists and imports")
    except Exception as e:
        print(f"  ❌ Module import failed: {e}")

    # Test 2: Round-trip serialization
    tests_total += 1
    try:
        original = ExperimentConfig(iteration=5, config_snapshot={'lr': 0.01})
        dict_form = original.to_dict()
        restored = ExperimentConfig.from_dict(dict_form)
        assert restored.iteration == original.iteration
        assert restored.config_snapshot == original.config_snapshot
        tests_passed += 1
        print("  ✅ Round-trip serialization works")
    except Exception as e:
        print(f"  ❌ Serialization test failed: {e}")

    return tests_passed, tests_total

def test_exception_state():
    """Test Bug #4 fix: Exception state propagation"""
    from unittest.mock import Mock
    from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

    tests_passed = 0
    tests_total = 0

    # Test 1: last_result attribute exists
    tests_total += 1
    try:
        mock_docker = Mock()
        mock_logger = Mock()
        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )
        assert hasattr(wrapper, 'last_result')
        assert wrapper.last_result is None
        tests_passed += 1
        print("  ✅ last_result attribute exists")
    except Exception as e:
        print(f"  ❌ Attribute test failed: {e}")

    # Test 2: Exception sets last_result = False
    tests_total += 1
    try:
        mock_docker = Mock()
        mock_logger = Mock()
        mock_docker.execute.side_effect = Exception("Docker failed")

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        # Execute should catch exception and fallback
        success, metrics, error = wrapper.execute_strategy(
            code="position = close.is_largest(10)",
            data=Mock(),
            timeout=120
        )

        assert wrapper.last_result is False, f"Expected False, got {wrapper.last_result}"
        tests_passed += 1
        print("  ✅ Exception sets last_result = False")
    except Exception as e:
        print(f"  ❌ Exception state test failed: {e}")

    return tests_passed, tests_total

def test_fstring_evaluation():
    """Test Bug #1 fix: F-string evaluation"""
    from unittest.mock import Mock
    from artifacts.working.modules.autonomous_loop import SandboxExecutionWrapper

    tests_passed = 0
    tests_total = 0

    # Test: No {{}} in assembled code
    tests_total += 1
    try:
        mock_docker = Mock()
        mock_logger = Mock()

        captured_code = None
        def capture_execute(code, timeout, validate):
            nonlocal captured_code
            captured_code = code
            return {'success': True, 'signal': {}, 'error': None}

        mock_docker.execute = capture_execute

        wrapper = SandboxExecutionWrapper(
            sandbox_enabled=True,
            docker_executor=mock_docker,
            event_logger=mock_logger
        )

        wrapper.execute_strategy(code="position = close.is_largest(10)", data=Mock(), timeout=120)

        assert captured_code is not None
        assert '{{' not in captured_code, "Found {{}} double braces"
        assert '}}' not in captured_code, "Found {{}} double braces"
        tests_passed += 1
        print("  ✅ No {{}} double braces in assembled code")
    except Exception as e:
        print(f"  ❌ F-string evaluation test failed: {e}")

    return tests_passed, tests_total

def main():
    print("=" * 80)
    print("DOCKER INTEGRATION TEST FRAMEWORK - BUG FIX VALIDATION")
    print("=" * 80)
    print()

    total_passed = 0
    total_tests = 0

    print("Testing Bug #2: LLM API Validation")
    passed, total = test_llm_validation()
    total_passed += passed
    total_tests += total
    print()

    print("Testing Bug #3: ExperimentConfig Module")
    passed, total = test_experiment_config()
    total_passed += passed
    total_tests += total
    print()

    print("Testing Bug #4: Exception State Propagation")
    passed, total = test_exception_state()
    total_passed += passed
    total_tests += total
    print()

    print("Testing Bug #1: F-String Evaluation")
    passed, total = test_fstring_evaluation()
    total_passed += passed
    total_tests += total
    print()

    print("=" * 80)
    print(f"SUMMARY: {total_passed}/{total_tests} tests passed")
    print("=" * 80)

    if total_passed == total_tests:
        print("\n✅ ALL BUG FIXES VALIDATED")
        return 0
    else:
        print(f"\n❌ {total_tests - total_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
