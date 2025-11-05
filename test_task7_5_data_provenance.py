"""Test Task 7.5: IterationRecord data provenance fields."""

import sys
from pathlib import Path

# Add working modules to path
sys.path.insert(0, str(Path(__file__).parent / "artifacts" / "working" / "modules"))

from history import IterationRecord


def test_backward_compatibility():
    """Test that existing code works without new fields."""
    print("Testing backward compatibility...")

    # Create record without new fields (old style)
    record = IterationRecord(
        iteration_num=0,
        timestamp="2025-10-12T08:00:00",
        model="gemini-2.5-flash",
        code="position = close.is_largest(10)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback="Good strategy"
    )

    # Verify new fields have default None values
    assert record.data_checksum is None, "data_checksum should default to None"
    assert record.data_version is None, "data_version should default to None"

    # Test serialization
    data_dict = record.to_dict()
    assert 'data_checksum' in data_dict, "to_dict() should include data_checksum"
    assert 'data_version' in data_dict, "to_dict() should include data_version"
    assert data_dict['data_checksum'] is None
    assert data_dict['data_version'] is None

    # Test deserialization without new fields (backward compatibility)
    old_style_dict = {
        'iteration_num': 1,
        'timestamp': '2025-10-12T09:00:00',
        'model': 'gemini-2.5-flash',
        'code': 'position = close.is_largest(20)',
        'validation_passed': True,
        'validation_errors': [],
        'execution_success': True,
        'execution_error': None,
        'metrics': {'sharpe_ratio': 1.2},
        'feedback': 'Test'
    }

    record2 = IterationRecord.from_dict(old_style_dict)
    assert record2.data_checksum is None, "Missing field should default to None"
    assert record2.data_version is None, "Missing field should default to None"

    print("✅ Backward compatibility: PASS")


def test_new_fields():
    """Test new data provenance fields."""
    print("\nTesting new data provenance fields...")

    # Create record with new fields
    data_version = {
        'finlab_version': '1.2.3',
        'data_pull_timestamp': '2025-10-12T08:00:00',
        'dataset_row_counts': {'close': 1000, 'volume': 1000}
    }

    record = IterationRecord(
        iteration_num=0,
        timestamp="2025-10-12T08:00:00",
        model="gemini-2.5-flash",
        code="position = close.is_largest(10)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback="Good strategy",
        data_checksum="abc123def456",
        data_version=data_version
    )

    # Verify fields are set
    assert record.data_checksum == "abc123def456", "data_checksum not set correctly"
    assert record.data_version == data_version, "data_version not set correctly"
    assert record.data_version['finlab_version'] == '1.2.3'

    # Test serialization
    data_dict = record.to_dict()
    assert data_dict['data_checksum'] == "abc123def456"
    assert data_dict['data_version'] == data_version
    assert data_dict['data_version']['finlab_version'] == '1.2.3'

    # Test deserialization
    record2 = IterationRecord.from_dict(data_dict)
    assert record2.data_checksum == "abc123def456"
    assert record2.data_version == data_version
    assert record2.data_version['data_pull_timestamp'] == '2025-10-12T08:00:00'

    print("✅ New fields functionality: PASS")


def test_partial_fields():
    """Test providing only some of the new fields."""
    print("\nTesting partial field specification...")

    # Only checksum, no version
    record1 = IterationRecord(
        iteration_num=0,
        timestamp="2025-10-12T08:00:00",
        model="gemini-2.5-flash",
        code="position = close.is_largest(10)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback="Good strategy",
        data_checksum="abc123"
    )

    assert record1.data_checksum == "abc123"
    assert record1.data_version is None

    # Only version, no checksum
    record2 = IterationRecord(
        iteration_num=1,
        timestamp="2025-10-12T08:00:00",
        model="gemini-2.5-flash",
        code="position = close.is_largest(10)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback="Good strategy",
        data_version={'finlab_version': '1.0.0'}
    )

    assert record2.data_checksum is None
    assert record2.data_version == {'finlab_version': '1.0.0'}

    print("✅ Partial field specification: PASS")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 7.5: IterationRecord Data Provenance Fields Test")
    print("=" * 60)

    try:
        test_backward_compatibility()
        test_new_fields()
        test_partial_fields()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("- ✅ Backward compatibility maintained")
        print("- ✅ data_checksum field works correctly")
        print("- ✅ data_version field works correctly")
        print("- ✅ to_dict() handles new fields automatically")
        print("- ✅ from_dict() handles new fields automatically")
        print("- ✅ Optional fields default to None")

        return 0
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
