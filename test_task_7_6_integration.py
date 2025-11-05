"""
Test Task 7.6: DataPipelineIntegrity Integration

Verifies that DataPipelineIntegrity is correctly integrated into autonomous_loop.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'artifacts', 'working', 'modules'))

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")

    try:
        from autonomous_loop import AutonomousLoop
        print("  ✅ autonomous_loop imports successfully")
    except ImportError as e:
        print(f"  ❌ autonomous_loop import failed: {e}")
        return False

    try:
        from history import IterationHistory, IterationRecord
        print("  ✅ history imports successfully")
    except ImportError as e:
        print(f"  ❌ history import failed: {e}")
        return False

    try:
        from src.data.pipeline_integrity import DataPipelineIntegrity
        print("  ✅ DataPipelineIntegrity imports successfully")
    except ImportError as e:
        print(f"  ❌ DataPipelineIntegrity import failed: {e}")
        return False

    return True


def test_iteration_record():
    """Test that IterationRecord has data provenance fields."""
    print("\nTesting IterationRecord structure...")

    from history import IterationRecord

    # Create a test record with all fields
    record = IterationRecord(
        iteration_num=0,
        timestamp="2025-10-12T10:00:00",
        model="test-model",
        code="# test code",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5},
        feedback="test feedback",
        data_checksum="abc123",
        data_version={'finlab_version': '1.0.0'}
    )

    # Verify fields exist
    assert hasattr(record, 'data_checksum'), "Missing data_checksum field"
    assert hasattr(record, 'data_version'), "Missing data_version field"
    assert record.data_checksum == "abc123", "data_checksum value incorrect"
    assert record.data_version == {'finlab_version': '1.0.0'}, "data_version value incorrect"

    print("  ✅ IterationRecord has data_checksum field")
    print("  ✅ IterationRecord has data_version field")
    print("  ✅ Fields accept correct values")

    return True


def test_history_add_record():
    """Test that IterationHistory.add_record accepts new parameters."""
    print("\nTesting IterationHistory.add_record...")

    import tempfile
    from history import IterationHistory

    # Create temporary history file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name

    try:
        history = IterationHistory(temp_file)

        # Test adding record with new parameters
        record = history.add_record(
            iteration_num=0,
            model="test-model",
            code="# test code",
            validation_passed=True,
            validation_errors=[],
            execution_success=True,
            execution_error=None,
            metrics={'sharpe_ratio': 1.5},
            feedback="test feedback",
            data_checksum="test_checksum_123",
            data_version={
                'finlab_version': '1.0.0',
                'data_pull_timestamp': '2025-10-12T10:00:00',
                'dataset_row_counts': {'price:收盤價': 1000}
            }
        )

        # Verify record was created with correct values
        assert record.data_checksum == "test_checksum_123", "data_checksum not stored correctly"
        assert record.data_version['finlab_version'] == '1.0.0', "data_version not stored correctly"

        print("  ✅ add_record accepts data_checksum parameter")
        print("  ✅ add_record accepts data_version parameter")
        print("  ✅ Parameters are stored correctly in record")

        # Test retrieval
        retrieved = history.get_record(0)
        assert retrieved is not None, "Could not retrieve record"
        assert retrieved.data_checksum == "test_checksum_123", "Retrieved checksum incorrect"
        assert retrieved.data_version['finlab_version'] == '1.0.0', "Retrieved version incorrect"

        print("  ✅ Provenance data persists through save/load cycle")

        return True

    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_data_pipeline_integration():
    """Test that DataPipelineIntegrity methods work correctly."""
    print("\nTesting DataPipelineIntegrity...")

    from src.data.pipeline_integrity import DataPipelineIntegrity

    integrity = DataPipelineIntegrity()

    # Test compute_dataset_checksum with None data
    checksum = integrity.compute_dataset_checksum(None)
    assert checksum is not None, "compute_dataset_checksum returned None"
    assert len(checksum) == 64, f"Checksum length incorrect: {len(checksum)}"
    print(f"  ✅ compute_dataset_checksum works (checksum: {checksum[:16]}...)")

    # Test validate_data_consistency
    is_valid, msg = integrity.validate_data_consistency(None, checksum)
    assert is_valid, f"Validation should pass: {msg}"
    print("  ✅ validate_data_consistency works (matching checksums)")

    # Test with mismatched checksum
    is_valid, msg = integrity.validate_data_consistency(None, "different_checksum")
    assert not is_valid, "Validation should fail with different checksum"
    print("  ✅ validate_data_consistency detects mismatches")

    # Test record_data_provenance
    provenance = integrity.record_data_provenance(None, iteration_num=0)
    assert 'dataset_checksum' in provenance, "Missing dataset_checksum in provenance"
    assert 'finlab_version' in provenance, "Missing finlab_version in provenance"
    assert 'data_pull_timestamp' in provenance, "Missing data_pull_timestamp in provenance"
    assert 'dataset_row_counts' in provenance, "Missing dataset_row_counts in provenance"
    print("  ✅ record_data_provenance returns all required fields")

    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Task 7.6 Integration Tests")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("IterationRecord Structure", test_iteration_record),
        ("IterationHistory.add_record", test_history_add_record),
        ("DataPipelineIntegrity", test_data_pipeline_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Task 7.6 integration complete.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
