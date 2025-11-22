"""Simplified integration test for Week 1 components.

This test validates the core Week 1 components without requiring all project dependencies.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

def test_unified_config_standalone():
    """Test UnifiedConfig independently."""
    print("\n" + "="*60)
    print("Test 1: UnifiedConfig Standalone Validation")
    print("="*60)

    from src.learning.unified_config import UnifiedConfig, ConfigurationError

    # Test 1.1: Default initialization
    config = UnifiedConfig()
    assert config.max_iterations == 10
    assert config.template_mode is False
    print("✓ Default initialization works")

    # Test 1.2: Template Mode
    config = UnifiedConfig(
        max_iterations=100,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True
    )
    assert config.template_mode is True
    assert config.use_json_mode is True
    print("✓ Template Mode configuration works")

    # Test 1.3: Validation
    try:
        UnifiedConfig(template_mode=True, template_name="")
        assert False, "Should have raised error"
    except ConfigurationError as e:
        assert "template_mode=True requires template_name" in str(e)
        print("✓ Validation works correctly")

    # Test 1.4: Conversion to LearningConfig
    learning_config = config.to_learning_config()
    assert learning_config.max_iterations == 100
    print("✓ Conversion to LearningConfig works")

    print("\n✅ UnifiedConfig: ALL TESTS PASSED")


def test_iteration_record_extension():
    """Test IterationRecord extension."""
    print("\n" + "="*60)
    print("Test 2: IterationRecord Extension")
    print("="*60)

    from src.learning.iteration_history import IterationRecord
    from datetime import datetime

    # Test 2.1: New fields present
    record = IterationRecord(
        iteration_num=0,
        generation_method="template",
        strategy_code="def strategy(): pass",
        execution_result={"status": "success"},
        metrics={"sharpe_ratio": 1.5},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat(),
        template_name="Momentum",
        json_mode=True
    )
    assert record.template_name == "Momentum"
    assert record.json_mode is True
    print("✓ New fields (template_name, json_mode) work")

    # Test 2.2: Backward compatibility
    record = IterationRecord(
        iteration_num=1,
        generation_method="llm",
        strategy_code="def strategy(): pass",
        execution_result={"status": "success"},
        metrics={"sharpe_ratio": 1.2},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat()
    )
    assert record.template_name is None
    assert record.json_mode is False
    print("✓ Backward compatibility maintained")

    # Test 2.3: Serialization roundtrip
    record = IterationRecord(
        iteration_num=2,
        generation_method="template",
        strategy_code="def strategy(): pass",
        execution_result={"status": "success"},
        metrics={"sharpe_ratio": 1.8},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat(),
        template_name="Factor",
        json_mode=True
    )
    record_dict = record.to_dict()
    assert "template_name" in record_dict
    assert record_dict["template_name"] == "Factor"
    assert record_dict["json_mode"] is True

    record_restored = IterationRecord.from_dict(record_dict)
    assert record_restored.template_name == "Factor"
    assert record_restored.json_mode is True
    print("✓ Serialization roundtrip works")

    print("\n✅ IterationRecord Extension: ALL TESTS PASSED")


def test_component_integration():
    """Test that components can be imported and initialized."""
    print("\n" + "="*60)
    print("Test 3: Component Integration")
    print("="*60)

    # Test 3.1: UnifiedConfig import
    from src.learning.unified_config import UnifiedConfig
    config = UnifiedConfig()
    print("✓ UnifiedConfig can be imported and initialized")

    # Test 3.2: UnifiedLoop import (without full initialization)
    try:
        # Note: We can't fully test UnifiedLoop without mocking dependencies,
        # but we can verify it imports correctly
        import src.learning.unified_loop
        print("✓ UnifiedLoop module can be imported")
    except ImportError as e:
        print(f"⚠️  UnifiedLoop import has dependency issues: {e}")
        print("   This is expected in minimal test environment")

    # Test 3.3: TemplateIterationExecutor import
    try:
        import src.learning.template_iteration_executor
        print("✓ TemplateIterationExecutor module can be imported")
    except ImportError as e:
        print(f"⚠️  TemplateIterationExecutor import has dependency issues: {e}")
        print("   This is expected in minimal test environment")

    print("\n✅ Component Integration: TESTS COMPLETED")


def main():
    """Run all simplified tests."""
    print("\n" + "#"*60)
    print("# Week 1 Simplified Integration Test")
    print("# Testing core components without full dependencies")
    print("#"*60)

    passed = 0
    failed = 0

    try:
        test_unified_config_standalone()
        passed += 1
    except Exception as e:
        print(f"\n❌ UnifiedConfig test failed: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    try:
        test_iteration_record_extension()
        passed += 1
    except Exception as e:
        print(f"\n❌ IterationRecord test failed: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    try:
        test_component_integration()
        passed += 1
    except Exception as e:
        print(f"\n❌ Component integration test failed: {e}")
        import traceback
        traceback.print_exc()
        failed += 1

    print("\n" + "#"*60)
    print(f"# Test Summary: {passed} passed, {failed} failed")
    print("#"*60)

    if failed == 0:
        print("\n✅ ALL WEEK 1 CORE TESTS PASSED!")
        print("\nNote: Full integration tests with UnifiedLoop and")
        print("TemplateIterationExecutor require complete project dependencies.")
        print("These will be tested in Week 2 with the full test harness.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
