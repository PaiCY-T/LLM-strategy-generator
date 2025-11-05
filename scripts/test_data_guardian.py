"""
Test DataGuardian Implementation

This script tests the DataGuardian security layer to ensure:
1. Hold-out set can be locked with cryptographic hash
2. Access is denied before Week 12
3. All access attempts are logged
4. Unlock requires correct authorization
5. Verification detects data tampering

Run this BEFORE starting Week 1 to ensure security layer is working.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.innovation.data_guardian import DataGuardian, SecurityError


def create_mock_holdout_data():
    """Create mock hold-out data for testing."""
    dates = pd.date_range('2019-01-01', '2025-10-23', freq='D')
    data = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, len(dates))
    }, index=dates)
    return data


def test_lock_holdout():
    """Test 1: Lock hold-out set."""
    print("\n" + "="*60)
    print("TEST 1: Lock Hold-Out Set")
    print("="*60)

    guardian = DataGuardian()
    holdout_data = create_mock_holdout_data()

    lock_record = guardian.lock_holdout(holdout_data)

    assert lock_record['holdout_hash'] is not None, "Hash not generated"
    assert lock_record['lock_timestamp'] is not None, "Timestamp not set"
    assert lock_record['access_allowed'] is False, "Access should be locked"

    print("✅ TEST 1 PASSED: Hold-out locked successfully")
    return guardian, holdout_data


def test_verify_holdout(guardian, holdout_data):
    """Test 2: Verify hold-out data integrity."""
    print("\n" + "="*60)
    print("TEST 2: Verify Hold-Out Data Integrity")
    print("="*60)

    # Verify original data
    assert guardian.verify_holdout(holdout_data), "Original data should verify"

    # Tamper with data
    tampered_data = holdout_data.copy()
    tampered_data.iloc[0, 0] = 999999  # Change first value

    # Verification should fail
    assert not guardian.verify_holdout(tampered_data), "Tampered data should NOT verify"

    print("✅ TEST 2 PASSED: Verification detects tampering")


def test_access_denied(guardian):
    """Test 3: Access denied before Week 12."""
    print("\n" + "="*60)
    print("TEST 3: Access Denied Before Week 12")
    print("="*60)

    # Try to access in Week 1-11
    for week in [1, 5, 11]:
        try:
            guardian.access_holdout(
                week_number=week,
                justification=f"Testing Week {week}"
            )
            raise AssertionError(f"Access should be denied in Week {week}")
        except SecurityError as e:
            print(f"✅ Week {week}: Access correctly denied")

    # Check access log
    status = guardian.get_lock_status()
    assert status['denied_attempts'] == 3, "Should have 3 denied attempts"

    print("✅ TEST 3 PASSED: Access correctly denied before Week 12")


def test_unlock_requirements(guardian):
    """Test 4: Unlock requires correct authorization."""
    print("\n" + "="*60)
    print("TEST 4: Unlock Requirements")
    print("="*60)

    # Wrong week number
    try:
        guardian.unlock_holdout(
            week_number=11,
            authorization_code="WEEK_12_FINAL_VALIDATION"
        )
        raise AssertionError("Unlock should fail with wrong week number")
    except SecurityError:
        print("✅ Wrong week number correctly rejected")

    # Wrong authorization code
    try:
        guardian.unlock_holdout(
            week_number=12,
            authorization_code="WRONG_CODE"
        )
        raise AssertionError("Unlock should fail with wrong authorization code")
    except SecurityError:
        print("✅ Wrong authorization code correctly rejected")

    # Correct unlock
    guardian.unlock_holdout(
        week_number=12,
        authorization_code="WEEK_12_FINAL_VALIDATION"
    )
    print("✅ Correct unlock successful")

    print("✅ TEST 4 PASSED: Unlock requirements enforced")


def test_access_granted(guardian):
    """Test 5: Access granted after unlock."""
    print("\n" + "="*60)
    print("TEST 5: Access Granted After Unlock")
    print("="*60)

    # Access should now be granted
    result = guardian.access_holdout(
        week_number=12,
        justification="Final validation of champion strategies"
    )
    assert result is True, "Access should be granted after unlock"

    # Check access log
    status = guardian.get_lock_status()
    assert status['granted_attempts'] == 1, "Should have 1 granted attempt"
    assert status['total_access_attempts'] == 4, "Should have 4 total attempts (3 denied + 1 granted)"

    print("✅ TEST 5 PASSED: Access granted after proper unlock")


def test_access_log(guardian):
    """Test 6: Access log completeness."""
    print("\n" + "="*60)
    print("TEST 6: Access Log Completeness")
    print("="*60)

    access_log = guardian.get_access_log()

    print(f"\nTotal access attempts: {len(access_log)}")
    for i, attempt in enumerate(access_log, 1):
        granted_str = "✅ GRANTED" if attempt['granted'] else "❌ DENIED"
        print(f"  {i}. Week {attempt['week_number']}: {granted_str}")
        print(f"     Justification: {attempt['justification']}")
        print(f"     Timestamp: {attempt['timestamp']}")

    assert len(access_log) == 4, "Should have 4 access attempts logged"
    assert sum(1 for a in access_log if a['granted']) == 1, "Should have 1 granted"
    assert sum(1 for a in access_log if not a['granted']) == 3, "Should have 3 denied"

    print("\n✅ TEST 6 PASSED: Access log is complete and accurate")


def run_all_tests():
    """Run all DataGuardian tests."""
    print("\n" + "="*60)
    print("DATAGUARDIAN SECURITY LAYER TEST SUITE")
    print("="*60)
    print("\nThis test suite validates that the hold-out set is properly")
    print("protected from premature access, fulfilling Condition 1 of the")
    print("Executive Approval.")
    print("\nTests:")
    print("1. Lock hold-out set with cryptographic hash")
    print("2. Verify data integrity detection")
    print("3. Access denied before Week 12")
    print("4. Unlock requirements enforced")
    print("5. Access granted after proper unlock")
    print("6. Access log completeness")

    try:
        # Run tests
        guardian, holdout_data = test_lock_holdout()
        test_verify_holdout(guardian, holdout_data)
        test_access_denied(guardian)
        test_unlock_requirements(guardian)
        test_access_granted(guardian)
        test_access_log(guardian)

        # Final summary
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        print("\nDataGuardian security layer is working correctly.")
        print("You may proceed with Week 1 implementation.")

        # Clean up test lock file
        from pathlib import Path
        lock_file = Path('.spec-workflow/specs/llm-innovation-capability/data_lock.json')
        if lock_file.exists():
            lock_file.unlink()
            print(f"\n🗑️  Cleaned up test lock file: {lock_file}")

        return True

    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"\nError: {e}")
        print("\nPlease fix the DataGuardian implementation before proceeding.")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
