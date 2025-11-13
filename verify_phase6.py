#!/usr/bin/env python3
"""
Phase 6 Verification Script

Simple verification without pytest to check Phase 6 components work correctly.
Tests basic functionality of:
- LearningConfig
- IterationExecutor
- LearningLoop
"""

import sys
import tempfile
import traceback
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_learning_config():
    """Test LearningConfig basic functionality."""
    print("=" * 60)
    print("TEST: LearningConfig")
    print("=" * 60)

    from src.learning.learning_config import LearningConfig

    # Test 1: Default values
    print("\n1. Testing default values...")
    config = LearningConfig()
    assert config.max_iterations == 20, "Default max_iterations should be 20"
    assert config.innovation_rate == 100, "Default innovation_rate should be 100"
    assert config.log_level == "INFO", "Default log_level should be INFO"
    print("   ✓ Default values correct")

    # Test 2: Custom values
    print("\n2. Testing custom values...")
    config = LearningConfig(
        max_iterations=50,
        innovation_rate=80,
        log_level="DEBUG"
    )
    assert config.max_iterations == 50
    assert config.innovation_rate == 80
    assert config.log_level == "DEBUG"
    print("   ✓ Custom values accepted")

    # Test 3: Validation
    print("\n3. Testing validation...")
    try:
        LearningConfig(max_iterations=0)
        assert False, "Should reject max_iterations=0"
    except ValueError as e:
        assert "max_iterations must be > 0" in str(e)
        print("   ✓ Validation rejects invalid values")

    # Test 4: YAML loading (flat structure)
    print("\n4. Testing YAML loading (flat structure)...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("max_iterations: 30\ninnovation_rate: 50\n")
        config_path = f.name

    try:
        config = LearningConfig.from_yaml(config_path)
        assert config.max_iterations == 30
        assert config.innovation_rate == 50
        print("   ✓ YAML loading works (flat structure)")
    finally:
        Path(config_path).unlink()

    # Test 5: YAML loading (nested structure)
    print("\n5. Testing YAML loading (nested structure)...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
learning_loop:
  max_iterations: 100
  history:
    window: 10
llm:
  enabled: true
  innovation_rate: 0.5
""")
        config_path = f.name

    try:
        config = LearningConfig.from_yaml(config_path)
        assert config.max_iterations == 100
        assert config.innovation_rate == 50  # 0.5 * 100
        assert config.history_window == 10
        print("   ✓ YAML loading works (nested structure)")
    finally:
        Path(config_path).unlink()

    # Test 6: to_dict
    print("\n6. Testing to_dict()...")
    config = LearningConfig(api_key="secret")
    config_dict = config.to_dict()
    assert config_dict["api_key"] == "***", "API key should be masked"
    assert "max_iterations" in config_dict
    print("   ✓ to_dict() works and masks API key")

    print("\n✅ LearningConfig: ALL TESTS PASSED")
    return True


def test_iteration_executor():
    """Test IterationExecutor basic functionality."""
    print("\n" + "=" * 60)
    print("TEST: IterationExecutor")
    print("=" * 60)

    from unittest.mock import Mock
    from src.learning.iteration_executor import IterationExecutor

    # Create mocks
    print("\n1. Testing initialization...")
    mock_components = {
        'llm_client': Mock(),
        'feedback_generator': Mock(),
        'backtest_executor': Mock(),
        'champion_tracker': Mock(),
        'history': Mock(),
        'config': {
            'innovation_rate': 100,
            'history_window': 5,
            'timeout_seconds': 420,
        }
    }

    executor = IterationExecutor(**mock_components)
    assert executor.llm_client is not None
    assert executor.metrics_extractor is not None
    assert executor.error_classifier is not None
    print("   ✓ IterationExecutor initialized")

    # Test 2: Decision logic
    print("\n2. Testing generation method decision...")
    executor.config['innovation_rate'] = 100
    assert executor._decide_generation_method() is True, "Should always use LLM"

    executor.config['innovation_rate'] = 0
    assert executor._decide_generation_method() is False, "Should always use Factor Graph"
    print("   ✓ Decision logic works")

    # Test 3: Factor Graph fallback
    print("\n3. Testing Factor Graph fallback...")
    code, strategy_id, generation = executor._generate_with_factor_graph(0)
    assert code is None
    assert strategy_id is not None
    assert "fallback" in strategy_id
    print("   ✓ Factor Graph fallback returns placeholder")

    print("\n✅ IterationExecutor: ALL TESTS PASSED")
    return True


def test_learning_loop():
    """Test LearningLoop basic functionality."""
    print("\n" + "=" * 60)
    print("TEST: LearningLoop")
    print("=" * 60)

    from src.learning.learning_config import LearningConfig
    from src.learning.learning_loop import LearningLoop

    with tempfile.TemporaryDirectory() as tmpdir:
        # Test 1: Initialization
        print("\n1. Testing initialization...")
        config = LearningConfig(
            max_iterations=3,
            history_file=str(Path(tmpdir) / "history.jsonl"),
            champion_file=str(Path(tmpdir) / "champion.json"),
            log_dir=str(Path(tmpdir) / "logs"),
            log_to_file=False,
            log_to_console=False,
        )

        loop = LearningLoop(config)
        assert loop.config == config
        assert loop.history is not None
        assert loop.champion_tracker is not None
        assert loop.iteration_executor is not None
        assert loop.interrupted is False
        print("   ✓ LearningLoop initialized with all components")

        # Test 2: Start iteration (no history)
        print("\n2. Testing start iteration determination...")
        start = loop._get_start_iteration()
        assert start == 0, "Should start from 0 with no history"
        print("   ✓ Starts from 0 with no history")

        # Test 3: Start iteration (with history)
        print("\n3. Testing resumption logic...")
        from src.learning.iteration_history import IterationRecord
        for i in range(2):
            record = IterationRecord(
                iteration_num=i,
                generation_method="llm",
                strategy_code="# code",
                execution_result={'success': True},
                metrics={'sharpe_ratio': 1.5},
                classification_level="LEVEL_3",
                timestamp="2024-01-01T00:00:00"
            )
            loop.history.save_record(record)

        start = loop._get_start_iteration()
        assert start == 2, "Should resume from iteration 2"
        print("   ✓ Resumption logic works")

        # Test 4: History persistence
        print("\n4. Testing history persistence...")
        all_records = loop.history.get_all()
        assert len(all_records) == 2
        assert all_records[0].iteration_num == 0
        assert all_records[1].iteration_num == 1
        print("   ✓ History persisted correctly")

        print("\n✅ LearningLoop: ALL TESTS PASSED")
        return True


def test_integration():
    """Test Phase 6 integration."""
    print("\n" + "=" * 60)
    print("TEST: Phase 6 Integration")
    print("=" * 60)

    from src.learning.learning_config import LearningConfig

    # Test: Load actual config file
    print("\n1. Testing actual config file loading...")
    config_path = "config/learning_system.yaml"
    if Path(config_path).exists():
        config = LearningConfig.from_yaml(config_path)
        print(f"   ✓ Loaded {config_path}")
        print(f"     - max_iterations: {config.max_iterations}")
        print(f"     - innovation_rate: {config.innovation_rate}")
        print(f"     - history_file: {config.history_file}")
    else:
        print(f"   ⚠ Config file not found: {config_path} (OK in test env)")

    print("\n✅ Phase 6 Integration: ALL TESTS PASSED")
    return True


def main():
    """Run all verification tests."""
    print("\n" + "=" * 60)
    print("PHASE 6 VERIFICATION")
    print("=" * 60)
    print()

    results = []

    # Run tests
    tests = [
        ("LearningConfig", test_learning_config),
        ("IterationExecutor", test_iteration_executor),
        ("LearningLoop", test_learning_loop),
        ("Integration", test_integration),
    ]

    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            print(f"\n❌ {name} FAILED: {e}")
            traceback.print_exc()
            results.append((name, False, str(e)))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success, _ in results if success)
    total = len(results)

    for name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {name}")
        if error:
            print(f"           Error: {error}")

    print()
    print(f"Results: {passed}/{total} test suites passed")

    if passed == total:
        print("\n🎉 ALL PHASE 6 COMPONENTS VERIFIED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test suite(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
