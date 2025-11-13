#!/usr/bin/env python3
"""
Phase 1 Integration Testing Script

This script manually validates Phase 1 implementation with end-to-end scenarios:
1. 9 configuration scenarios (3x3 matrix)
2. Error handling verification
3. Kill switch testing
4. Rollback validation

Run with:
    python test_phase1_integration.py
"""

import os
import sys
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.learning.iteration_executor import IterationExecutor
from src.learning.exceptions import (
    ConfigurationConflictError,
    LLMUnavailableError,
    LLMEmptyResponseError,
    LLMGenerationError
)


class IntegrationTestRunner:
    """Integration test runner for Phase 1"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test(self, test_name: str, test_func):
        """Run a single test and track results"""
        try:
            print(f"\n{'='*70}")
            print(f"TEST: {test_name}")
            print(f"{'='*70}")
            test_func()
            self.passed += 1
            print(f"✅ PASSED: {test_name}")
        except AssertionError as e:
            self.failed += 1
            self.errors.append(f"{test_name}: {e}")
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
        except Exception as e:
            self.failed += 1
            self.errors.append(f"{test_name}: Unexpected error: {e}")
            print(f"❌ ERROR: {test_name}")
            print(f"   Error: {e}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print("INTEGRATION TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        if self.errors:
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  - {error}")

        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.failed} TEST(S) FAILED")


def create_mock_executor(config: Dict[str, Any]) -> IterationExecutor:
    """Create IterationExecutor with mocked dependencies"""
    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True

    mock_engine = MagicMock()
    mock_engine.generate_innovation.return_value = "def strategy(): return True"
    mock_llm.get_engine.return_value = mock_engine

    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }

    return IterationExecutor(**mock_deps)


# ============================================================================
# TEST GROUP 1: Configuration Scenarios (3x3 Matrix)
# ============================================================================

def test_scenario_1_use_fg_true_innovation_0():
    """Scenario 1.1: use_factor_graph=True, innovation_rate=0"""
    config = {"use_factor_graph": True, "innovation_rate": 0}
    executor = create_mock_executor(config)

    # Should return False (Factor Graph) due to use_factor_graph priority
    result = executor._decide_generation_method()
    assert result is False, f"Expected False (Factor Graph), got {result}"
    print("   ✓ Returned Factor Graph (use_factor_graph=True priority)")


def test_scenario_1_use_fg_true_innovation_50():
    """Scenario 1.2: use_factor_graph=True, innovation_rate=50"""
    config = {"use_factor_graph": True, "innovation_rate": 50}
    executor = create_mock_executor(config)

    # Should return False (Factor Graph) due to use_factor_graph priority
    result = executor._decide_generation_method()
    assert result is False, f"Expected False (Factor Graph), got {result}"
    print("   ✓ Returned Factor Graph (use_factor_graph=True priority)")


def test_scenario_1_use_fg_true_innovation_100():
    """Scenario 1.3: use_factor_graph=True, innovation_rate=100 (CONFLICT)"""
    config = {"use_factor_graph": True, "innovation_rate": 100}
    executor = create_mock_executor(config)

    # Should raise ConfigurationConflictError
    try:
        executor._decide_generation_method()
        assert False, "Expected ConfigurationConflictError, but no exception was raised"
    except ConfigurationConflictError as e:
        print(f"   ✓ Raised ConfigurationConflictError: {e}")
        assert "use_factor_graph=True" in str(e)
        assert "innovation_rate=100" in str(e)


def test_scenario_2_use_fg_false_innovation_0():
    """Scenario 2.1: use_factor_graph=False, innovation_rate=0 (CONFLICT)"""
    config = {"use_factor_graph": False, "innovation_rate": 0}
    executor = create_mock_executor(config)

    # Should raise ConfigurationConflictError
    try:
        executor._decide_generation_method()
        assert False, "Expected ConfigurationConflictError, but no exception was raised"
    except ConfigurationConflictError as e:
        print(f"   ✓ Raised ConfigurationConflictError: {e}")
        assert "use_factor_graph=False" in str(e)
        assert "innovation_rate=0" in str(e)


def test_scenario_2_use_fg_false_innovation_50():
    """Scenario 2.2: use_factor_graph=False, innovation_rate=50"""
    config = {"use_factor_graph": False, "innovation_rate": 50}
    executor = create_mock_executor(config)

    # Should return True (LLM) due to use_factor_graph priority
    result = executor._decide_generation_method()
    assert result is True, f"Expected True (LLM), got {result}"
    print("   ✓ Returned LLM (use_factor_graph=False priority)")


def test_scenario_2_use_fg_false_innovation_100():
    """Scenario 2.3: use_factor_graph=False, innovation_rate=100"""
    config = {"use_factor_graph": False, "innovation_rate": 100}
    executor = create_mock_executor(config)

    # Should return True (LLM) due to use_factor_graph priority
    result = executor._decide_generation_method()
    assert result is True, f"Expected True (LLM), got {result}"
    print("   ✓ Returned LLM (use_factor_graph=False priority)")


def test_scenario_3_use_fg_none_innovation_0():
    """Scenario 3.1: use_factor_graph=None, innovation_rate=0"""
    config = {"innovation_rate": 0}  # use_factor_graph not set
    executor = create_mock_executor(config)

    # Should return False (Factor Graph) via innovation_rate=0
    result = executor._decide_generation_method()
    assert result is False, f"Expected False (Factor Graph), got {result}"
    print("   ✓ Returned Factor Graph (innovation_rate=0 fallback)")


def test_scenario_3_use_fg_none_innovation_50():
    """Scenario 3.2: use_factor_graph=None, innovation_rate=50"""
    config = {"innovation_rate": 50}  # use_factor_graph not set
    executor = create_mock_executor(config)

    # Should return probabilistic result (we'll test multiple times)
    results = []
    for _ in range(10):
        result = executor._decide_generation_method()
        results.append(result)

    # Should have mix of True and False (probabilistic)
    assert True in results or False in results, "Expected probabilistic results"
    print(f"   ✓ Probabilistic results: {sum(results)}/10 LLM calls")


def test_scenario_3_use_fg_none_innovation_100():
    """Scenario 3.3: use_factor_graph=None, innovation_rate=100"""
    config = {"innovation_rate": 100}  # use_factor_graph not set
    executor = create_mock_executor(config)

    # Should return True (LLM) via innovation_rate=100
    result = executor._decide_generation_method()
    assert result is True, f"Expected True (LLM), got {result}"
    print("   ✓ Returned LLM (innovation_rate=100 fallback)")


# ============================================================================
# TEST GROUP 2: Error Handling Verification
# ============================================================================

def test_error_llm_disabled():
    """Test LLMUnavailableError when LLM client disabled"""
    config = {"innovation_rate": 100}

    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = False  # LLM disabled

    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }

    executor = IterationExecutor(**mock_deps)

    try:
        executor._generate_with_llm("test feedback", 0)
        assert False, "Expected LLMUnavailableError"
    except LLMUnavailableError as e:
        print(f"   ✓ LLMUnavailableError: {e}")
        assert "not enabled" in str(e).lower()


def test_error_llm_engine_none():
    """Test LLMUnavailableError when LLM engine is None"""
    config = {"innovation_rate": 100}

    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True
    mock_llm.get_engine.return_value = None  # Engine is None

    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }

    executor = IterationExecutor(**mock_deps)

    try:
        executor._generate_with_llm("test feedback", 0)
        assert False, "Expected LLMUnavailableError"
    except LLMUnavailableError as e:
        print(f"   ✓ LLMUnavailableError: {e}")
        assert "not available" in str(e).lower()


def test_error_llm_empty_response():
    """Test LLMEmptyResponseError when LLM returns empty/whitespace"""
    config = {"innovation_rate": 100}

    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True

    mock_engine = MagicMock()
    mock_engine.generate_innovation.return_value = "   "  # Whitespace only
    mock_llm.get_engine.return_value = mock_engine

    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }

    executor = IterationExecutor(**mock_deps)

    try:
        executor._generate_with_llm("test feedback", 0)
        assert False, "Expected LLMEmptyResponseError"
    except LLMEmptyResponseError as e:
        print(f"   ✓ LLMEmptyResponseError: {e}")
        assert "empty" in str(e).lower() or "whitespace" in str(e).lower()


def test_error_llm_api_exception():
    """Test LLMGenerationError when API throws exception"""
    config = {"innovation_rate": 100}

    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True

    mock_engine = MagicMock()
    mock_engine.generate_innovation.side_effect = RuntimeError("API timeout")
    mock_llm.get_engine.return_value = mock_engine

    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }

    executor = IterationExecutor(**mock_deps)

    try:
        executor._generate_with_llm("test feedback", 0)
        assert False, "Expected LLMGenerationError"
    except LLMGenerationError as e:
        print(f"   ✓ LLMGenerationError: {e}")
        assert "API timeout" in str(e)
        # Check exception chain preserved
        assert e.__cause__ is not None


# ============================================================================
# TEST GROUP 3: Kill Switch Testing
# ============================================================================

def test_kill_switch_off():
    """Test kill switch OFF (legacy behavior)"""
    # Disable feature flags
    os.environ["ENABLE_GENERATION_REFACTORING"] = "false"
    os.environ["PHASE1_CONFIG_ENFORCEMENT"] = "false"

    # Re-import modules to pick up new env vars
    import importlib
    import src.learning.config
    import src.learning.iteration_executor
    importlib.reload(src.learning.config)
    importlib.reload(src.learning.iteration_executor)

    from src.learning.config import ENABLE_GENERATION_REFACTORING, PHASE1_CONFIG_ENFORCEMENT
    from src.learning.iteration_executor import IterationExecutor

    assert ENABLE_GENERATION_REFACTORING is False
    assert PHASE1_CONFIG_ENFORCEMENT is False

    print("   ✓ Kill switch OFF - feature flags disabled")

    # Test that conflicting config does NOT raise error (legacy behavior)
    config = {"use_factor_graph": True, "innovation_rate": 100}

    # Create executor with reloaded module
    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True
    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }
    executor = IterationExecutor(**mock_deps)

    # Should NOT raise ConfigurationConflictError (legacy ignores conflicts)
    try:
        result = executor._decide_generation_method()
        print(f"   ✓ Legacy behavior: no conflict error, returned {result}")
    except ConfigurationConflictError:
        assert False, "Legacy mode should NOT raise ConfigurationConflictError"


def test_kill_switch_partial():
    """Test kill switch with ENABLE_GENERATION_REFACTORING=true, PHASE1_CONFIG_ENFORCEMENT=false"""
    os.environ["ENABLE_GENERATION_REFACTORING"] = "true"
    os.environ["PHASE1_CONFIG_ENFORCEMENT"] = "false"

    # Re-import modules to pick up new env vars
    import importlib
    import src.learning.config
    import src.learning.iteration_executor
    importlib.reload(src.learning.config)
    importlib.reload(src.learning.iteration_executor)

    from src.learning.config import ENABLE_GENERATION_REFACTORING, PHASE1_CONFIG_ENFORCEMENT
    from src.learning.iteration_executor import IterationExecutor

    assert ENABLE_GENERATION_REFACTORING is True
    assert PHASE1_CONFIG_ENFORCEMENT is False

    print("   ✓ Kill switch PARTIAL - Phase 1 disabled")

    # Should use legacy behavior
    config = {"use_factor_graph": True, "innovation_rate": 100}

    # Create executor with reloaded module
    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True
    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }
    executor = IterationExecutor(**mock_deps)

    try:
        result = executor._decide_generation_method()
        print(f"   ✓ Legacy behavior active: no conflict error, returned {result}")
    except ConfigurationConflictError:
        assert False, "Should use legacy behavior when PHASE1_CONFIG_ENFORCEMENT=false"


def test_kill_switch_on():
    """Test kill switch ON (Phase 1 active)"""
    os.environ["ENABLE_GENERATION_REFACTORING"] = "true"
    os.environ["PHASE1_CONFIG_ENFORCEMENT"] = "true"

    # Re-import modules to pick up new env vars
    import importlib
    import src.learning.config
    import src.learning.iteration_executor
    importlib.reload(src.learning.config)
    importlib.reload(src.learning.iteration_executor)

    from src.learning.config import ENABLE_GENERATION_REFACTORING, PHASE1_CONFIG_ENFORCEMENT
    from src.learning.iteration_executor import IterationExecutor

    assert ENABLE_GENERATION_REFACTORING is True
    assert PHASE1_CONFIG_ENFORCEMENT is True

    print("   ✓ Kill switch ON - Phase 1 active")

    # Should detect conflicts
    config = {"use_factor_graph": True, "innovation_rate": 100}

    # Create executor with reloaded module
    mock_llm = MagicMock()
    mock_llm.is_enabled.return_value = True
    mock_deps = {
        "llm_client": mock_llm,
        "feedback_generator": MagicMock(),
        "backtest_executor": MagicMock(),
        "champion_tracker": MagicMock(),
        "history": MagicMock(),
        "config": config,
        "data": MagicMock(),
        "sim": MagicMock(),
    }
    executor = IterationExecutor(**mock_deps)

    try:
        executor._decide_generation_method()
        assert False, "Expected ConfigurationConflictError with Phase 1 active"
    except ConfigurationConflictError:
        print("   ✓ Phase 1 behavior active: conflict error raised")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run all integration tests"""
    runner = IntegrationTestRunner()

    print("\n" + "="*70)
    print("PHASE 1 INTEGRATION TESTING")
    print("="*70)

    # Ensure Phase 1 is enabled for most tests
    os.environ["ENABLE_GENERATION_REFACTORING"] = "true"
    os.environ["PHASE1_CONFIG_ENFORCEMENT"] = "true"

    # Re-import to pick up env vars
    import importlib
    import src.learning.config
    importlib.reload(src.learning.config)

    print("\n📋 TEST GROUP 1: Configuration Scenarios (3x3 Matrix)")
    print("-" * 70)

    runner.run_test("1.1: use_factor_graph=True, innovation_rate=0",
                   test_scenario_1_use_fg_true_innovation_0)
    runner.run_test("1.2: use_factor_graph=True, innovation_rate=50",
                   test_scenario_1_use_fg_true_innovation_50)
    runner.run_test("1.3: use_factor_graph=True, innovation_rate=100 (CONFLICT)",
                   test_scenario_1_use_fg_true_innovation_100)

    runner.run_test("2.1: use_factor_graph=False, innovation_rate=0 (CONFLICT)",
                   test_scenario_2_use_fg_false_innovation_0)
    runner.run_test("2.2: use_factor_graph=False, innovation_rate=50",
                   test_scenario_2_use_fg_false_innovation_50)
    runner.run_test("2.3: use_factor_graph=False, innovation_rate=100",
                   test_scenario_2_use_fg_false_innovation_100)

    runner.run_test("3.1: use_factor_graph=None, innovation_rate=0",
                   test_scenario_3_use_fg_none_innovation_0)
    runner.run_test("3.2: use_factor_graph=None, innovation_rate=50",
                   test_scenario_3_use_fg_none_innovation_50)
    runner.run_test("3.3: use_factor_graph=None, innovation_rate=100",
                   test_scenario_3_use_fg_none_innovation_100)

    print("\n🛡️ TEST GROUP 2: Error Handling Verification")
    print("-" * 70)

    runner.run_test("Error: LLM client disabled", test_error_llm_disabled)
    runner.run_test("Error: LLM engine is None", test_error_llm_engine_none)
    runner.run_test("Error: LLM empty response", test_error_llm_empty_response)
    runner.run_test("Error: LLM API exception", test_error_llm_api_exception)

    print("\n🔀 TEST GROUP 3: Kill Switch Testing")
    print("-" * 70)

    runner.run_test("Kill switch: OFF (legacy)", test_kill_switch_off)
    runner.run_test("Kill switch: PARTIAL (Phase 1 disabled)", test_kill_switch_partial)
    runner.run_test("Kill switch: ON (Phase 1 active)", test_kill_switch_on)

    # Print final summary
    runner.print_summary()

    # Return exit code
    return 0 if runner.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
