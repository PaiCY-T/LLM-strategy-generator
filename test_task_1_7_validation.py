"""
Quick test script for Task 1.7: _validate_params() method

This script validates the implementation of the _validate_params() method
in TemplateParameterGenerator class.
"""

from src.generators.template_parameter_generator import TemplateParameterGenerator


def test_valid_params():
    """Test validation with valid parameters"""
    generator = TemplateParameterGenerator()

    valid_params = {
        'momentum_period': 10,
        'ma_periods': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10,
        'stop_loss': 0.10,
        'resample': 'M',
        'resample_offset': 0
    }

    is_valid, errors = generator._validate_params(valid_params)

    print("Test 1: Valid parameters")
    print(f"  Result: {'PASS' if is_valid else 'FAIL'}")
    print(f"  Errors: {errors}")
    assert is_valid, f"Expected valid=True, got {is_valid}"
    assert len(errors) == 0, f"Expected no errors, got {errors}"
    print()


def test_missing_parameters():
    """Test validation with missing parameters"""
    generator = TemplateParameterGenerator()

    incomplete_params = {
        'momentum_period': 10,
        'ma_periods': 60,
        # Missing 6 other parameters
    }

    is_valid, errors = generator._validate_params(incomplete_params)

    print("Test 2: Missing parameters")
    print(f"  Result: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Errors: {errors}")
    assert not is_valid, "Expected invalid due to missing parameters"
    assert len(errors) > 0, "Expected error messages"
    assert "Missing required parameters" in errors[0], "Expected missing parameters error"
    print()


def test_invalid_value():
    """Test validation with invalid parameter value"""
    generator = TemplateParameterGenerator()

    invalid_params = {
        'momentum_period': 15,  # Invalid: not in [5, 10, 20, 30]
        'ma_periods': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10,
        'stop_loss': 0.10,
        'resample': 'M',
        'resample_offset': 0
    }

    is_valid, errors = generator._validate_params(invalid_params)

    print("Test 3: Invalid parameter value")
    print(f"  Result: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Errors: {errors}")
    assert not is_valid, "Expected invalid due to wrong value"
    assert len(errors) > 0, "Expected error messages"
    assert "momentum_period" in errors[0], "Expected momentum_period error"
    print()


def test_wrong_type():
    """Test validation with wrong data type"""
    generator = TemplateParameterGenerator()

    wrong_type_params = {
        'momentum_period': '10',  # Wrong type: should be int, not str
        'ma_periods': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10,
        'stop_loss': 0.10,
        'resample': 'M',
        'resample_offset': 0
    }

    is_valid, errors = generator._validate_params(wrong_type_params)

    print("Test 4: Wrong data type")
    print(f"  Result: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Errors: {errors}")
    assert not is_valid, "Expected invalid due to wrong type"
    assert len(errors) > 0, "Expected error messages"
    assert "wrong type" in errors[0], "Expected type error message"
    print()


def test_extra_parameters():
    """Test validation with extra unknown parameters"""
    generator = TemplateParameterGenerator()

    extra_params = {
        'momentum_period': 10,
        'ma_periods': 60,
        'catalyst_type': 'revenue',
        'catalyst_lookback': 3,
        'n_stocks': 10,
        'stop_loss': 0.10,
        'resample': 'M',
        'resample_offset': 0,
        'unknown_param': 999  # Extra parameter
    }

    is_valid, errors = generator._validate_params(extra_params)

    print("Test 5: Extra unknown parameters")
    print(f"  Result: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Errors: {errors}")
    assert not is_valid, "Expected invalid due to extra parameters"
    assert len(errors) > 0, "Expected error messages"
    assert "Unknown parameters" in errors[0], "Expected unknown parameters error"
    print()


def test_all_8_parameters_required():
    """Test that exactly 8 parameters are required"""
    generator = TemplateParameterGenerator()

    # Verify PARAM_GRID has 8 parameters
    param_count = len(generator.param_grid)
    print("Test 6: Verify 8 required parameters")
    print(f"  PARAM_GRID parameter count: {param_count}")
    print(f"  Parameters: {list(generator.param_grid.keys())}")
    assert param_count == 8, f"Expected 8 parameters, got {param_count}"
    print(f"  Result: PASS")
    print()


def test_multiple_errors():
    """Test validation with multiple errors"""
    generator = TemplateParameterGenerator()

    multi_error_params = {
        'momentum_period': 15,  # Invalid value
        'ma_periods': '60',     # Wrong type
        'catalyst_type': 'revenue',
        # Missing: catalyst_lookback, n_stocks, stop_loss, resample, resample_offset
    }

    is_valid, errors = generator._validate_params(multi_error_params)

    print("Test 7: Multiple validation errors")
    print(f"  Result: {'PASS' if not is_valid else 'FAIL'}")
    print(f"  Error count: {len(errors)}")
    for i, error in enumerate(errors, 1):
        print(f"  Error {i}: {error}")
    assert not is_valid, "Expected invalid due to multiple errors"
    assert len(errors) >= 3, f"Expected at least 3 errors, got {len(errors)}"
    print()


if __name__ == '__main__':
    print("=" * 70)
    print("Task 1.7 Validation Tests: _validate_params() method")
    print("=" * 70)
    print()

    try:
        test_valid_params()
        test_missing_parameters()
        test_invalid_value()
        test_wrong_type()
        test_extra_parameters()
        test_all_8_parameters_required()
        test_multiple_errors()

        print("=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        print()
        print("Task 1.7 Acceptance Criteria:")
        print("  - Returns (is_valid: bool, errors: List[str]) tuple")
        print("  - Checks all 8 required parameters present")
        print("  - Validates each value against PARAM_GRID")
        print("  - Returns detailed error messages for failures")
        print()

    except AssertionError as e:
        print("=" * 70)
        print(f"TEST FAILED: {e}")
        print("=" * 70)
        raise
