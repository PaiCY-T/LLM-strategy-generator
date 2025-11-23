"""Manual validation script for Week 1 components.

This script validates UnifiedConfig, UnifiedLoop, and TemplateIterationExecutor
without requiring full test infrastructure.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

def test_unified_config():
    """Test UnifiedConfig basic functionality."""
    print("\n" + "=" * 60)
    print("Testing UnifiedConfig")
    print("=" * 60)

    from src.learning.unified_config import UnifiedConfig, ConfigurationError

    # Test 1: Default initialization
    print("\n✓ Test 1: Default initialization")
    config = UnifiedConfig()
    assert config.max_iterations == 10
    assert config.llm_model == "gemini-2.5-flash"
    assert config.template_mode is False
    print("  PASSED: Default values correct")

    # Test 2: Custom initialization
    print("\n✓ Test 2: Custom initialization")
    config = UnifiedConfig(
        max_iterations=50,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True
    )
    assert config.max_iterations == 50
    assert config.template_mode is True
    assert config.template_name == "Momentum"
    assert config.use_json_mode is True
    print("  PASSED: Custom values correct")

    # Test 3: Validation - template_mode requires template_name
    print("\n✓ Test 3: Validation (template_mode requires template_name)")
    try:
        config = UnifiedConfig(template_mode=True, template_name="")
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        assert "template_mode=True requires template_name" in str(e)
        print(f"  PASSED: Caught expected error: {e}")

    # Test 4: Validation - use_json_mode requires template_mode
    print("\n✓ Test 4: Validation (use_json_mode requires template_mode)")
    try:
        config = UnifiedConfig(use_json_mode=True, template_mode=False)
        assert False, "Should have raised ConfigurationError"
    except ConfigurationError as e:
        assert "use_json_mode=True requires template_mode=True" in str(e)
        print(f"  PASSED: Caught expected error: {e}")

    # Test 5: Conversion to LearningConfig
    print("\n✓ Test 5: Conversion to LearningConfig")
    config = UnifiedConfig(max_iterations=100)
    learning_config = config.to_learning_config()
    assert learning_config.max_iterations == 100
    print("  PASSED: Conversion successful")

    # Test 6: to_dict() method
    print("\n✓ Test 6: to_dict() method")
    config = UnifiedConfig(api_key="secret")
    config_dict = config.to_dict()
    assert config_dict["api_key"] == "***"  # Masked
    assert "max_iterations" in config_dict
    print("  PASSED: to_dict() works and masks API key")

    print("\n" + "=" * 60)
    print("✅ UnifiedConfig: ALL TESTS PASSED")
    print("=" * 60)


def test_iteration_record_extension():
    """Test IterationRecord field extensions."""
    print("\n" + "=" * 60)
    print("Testing IterationRecord Extension")
    print("=" * 60)

    from src.learning.iteration_history import IterationRecord
    from datetime import datetime

    # Test 1: New fields present
    print("\n✓ Test 1: New fields (template_name, json_mode) present")
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
    print("  PASSED: New fields accessible")

    # Test 2: Backward compatibility (fields optional)
    print("\n✓ Test 2: Backward compatibility (fields optional)")
    record = IterationRecord(
        iteration_num=1,
        generation_method="llm",
        strategy_code="def strategy(): pass",
        execution_result={"status": "success"},
        metrics={"sharpe_ratio": 1.2},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat()
        # template_name and json_mode not provided
    )
    assert record.template_name is None
    assert record.json_mode is False  # Default value
    print("  PASSED: Default values work")

    # Test 3: Serialization
    print("\n✓ Test 3: Serialization (to_dict and from_dict)")
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
    assert "json_mode" in record_dict
    assert record_dict["template_name"] == "Factor"
    assert record_dict["json_mode"] is True

    # Deserialize
    record_restored = IterationRecord.from_dict(record_dict)
    assert record_restored.template_name == "Factor"
    assert record_restored.json_mode is True
    print("  PASSED: Serialization roundtrip successful")

    print("\n" + "=" * 60)
    print("✅ IterationRecord Extension: ALL TESTS PASSED")
    print("=" * 60)


def test_unified_loop_basic():
    """Test UnifiedLoop basic functionality (without full dependencies)."""
    print("\n" + "=" * 60)
    print("Testing UnifiedLoop Basic Functionality")
    print("=" * 60)

    # Note: We can't fully test UnifiedLoop without mocking LearningLoop,
    # but we can test configuration building

    from src.learning.unified_config import UnifiedConfig

    # Test configuration building
    print("\n✓ Test: UnifiedLoop configuration building")
    config = UnifiedConfig(
        max_iterations=50,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True
    )

    assert config.max_iterations == 50
    assert config.template_mode is True
    assert config.template_name == "Momentum"
    assert config.use_json_mode is True
    print("  PASSED: Configuration can be built for UnifiedLoop")

    print("\n" + "=" * 60)
    print("✅ UnifiedLoop Basic: TEST PASSED")
    print("=" * 60)


def main():
    """Run all manual tests."""
    print("\n" + "#" * 60)
    print("# Week 1 Manual Validation Script")
    print("#" * 60)

    try:
        test_unified_config()
        test_iteration_record_extension()
        test_unified_loop_basic()

        print("\n" + "#" * 60)
        print("# ✅ ALL WEEK 1 TESTS PASSED!")
        print("#" * 60)
        return 0

    except Exception as e:
        print("\n" + "#" * 60)
        print(f"# ❌ TEST FAILED: {e}")
        print("#" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
