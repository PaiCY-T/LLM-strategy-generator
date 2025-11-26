"""Tests for structured error feedback with suggestions."""
import pytest
from src.validation.field_validator import FieldValidator
from src.config.data_fields import DataFieldManifest


@pytest.fixture
def validator():
    """Create FieldValidator with DataFieldManifest."""
    manifest = DataFieldManifest('tests/fixtures/finlab_fields.json')
    return FieldValidator(manifest)


class TestStructuredErrorMessages:
    def test_error_includes_line_number(self, validator):
        """Test that error message includes line number."""
        code = """
def strategy(data):
    price = data.get('price:成交量')  # Line 3 - Invalid field
    return price > 100
"""
        result = validator.validate(code)
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.line == 3
        assert 'Line 3' in str(error)

    def test_error_includes_column_number(self, validator):
        """Test that error message includes column position."""
        code = """price = data.get('price:成交量')"""
        result = validator.validate(code)
        assert len(result.errors) == 1
        error = result.errors[0]
        assert error.column > 0  # Should have column info

    def test_error_includes_field_name(self, validator):
        """Test that error identifies the invalid field name."""
        code = """price = data.get('price:成交量')"""
        result = validator.validate(code)
        error = result.errors[0]
        assert error.field_name == 'price:成交量'
        assert 'price:成交量' in str(error)

    def test_error_includes_suggestion(self, validator):
        """Test that error includes helpful suggestion."""
        code = """price = data.get('price:成交量')"""
        result = validator.validate(code)
        error = result.errors[0]
        assert error.suggestion is not None
        assert 'price:成交金額' in error.suggestion
        assert "Did you mean" in error.suggestion


class TestMultipleErrorsFormatting:
    def test_multiple_errors_each_have_line_numbers(self, validator):
        """Test multiple errors maintain separate line numbers."""
        code = """
def strategy(data):
    field1 = data.get('price:成交量')  # Line 3 - Error 1
    field2 = data.get('turnover')     # Line 4 - Error 2 (but actually valid via correction)
    field3 = data.get('invalid_xyz')  # Line 5 - Error 3
    return True
"""
        result = validator.validate(code)

        # Should have errors for invalid fields
        assert len(result.errors) >= 2

        # Check distinct line numbers
        line_numbers = [error.line for error in result.errors]
        assert len(set(line_numbers)) == len(line_numbers)  # All unique

    def test_error_summary_readable(self, validator):
        """Test that error summary is human-readable."""
        code = """price = data.get('price:成交量')"""
        result = validator.validate(code)

        summary = str(result)
        assert 'Errors (1)' in summary or 'Error' in summary
        assert 'price:成交量' in summary
        assert 'Did you mean' in summary


class TestSuggestionQuality:
    def test_common_mistake_gets_exact_suggestion(self, validator):
        """Test common mistakes get exact, helpful suggestions."""
        code = """volume = data.get('turnover')"""
        result = validator.validate(code)

        # 'turnover' is in COMMON_CORRECTIONS → should get suggestion
        if len(result.errors) > 0:  # If treated as error
            error = result.errors[0]
            assert error.suggestion is not None
            assert 'price:成交金額' in error.suggestion

    def test_unknown_field_gets_null_or_fuzzy_suggestion(self, validator):
        """Test completely unknown fields get appropriate feedback."""
        code = """x = data.get('completely_unknown_xyz_123')"""
        result = validator.validate(code)

        assert len(result.errors) >= 1
        error = result.errors[0]
        # Either no suggestion or a low-confidence fuzzy match
        assert error.suggestion is None or 'low confidence' in error.suggestion.lower()

    def test_valid_field_no_error(self, validator):
        """Test valid fields produce no errors."""
        code = """price = data.get('close')"""  # Valid alias
        result = validator.validate(code)
        assert len(result.errors) == 0


class TestErrorMessageFormats:
    def test_error_str_format_consistent(self, validator):
        """Test that error __str__ format is consistent."""
        code = """x = data.get('price:成交量')"""
        result = validator.validate(code)

        error = result.errors[0]
        error_str = str(error)

        # Should follow format: "Line X:Y - error_type: message (suggestion)"
        assert 'Line' in error_str
        assert ':' in error_str
        assert 'Did you mean' in error_str or 'suggestion' in error_str.lower()

    def test_validation_result_str_format(self, validator):
        """Test ValidationResult string format."""
        code = """
x = data.get('price:成交量')
y = data.get('turnover')
"""
        result = validator.validate(code)
        result_str = str(result)

        # Should list all errors
        assert 'Errors' in result_str or 'Error' in result_str
        # Should show count
        assert str(len(result.errors)) in result_str or 'Errors (' in result_str
