"""Tests for validation result data structures."""
import pytest
from src.validation.validation_result import ValidationResult, FieldError, FieldWarning


class TestFieldError:
    def test_create_field_error_with_all_fields(self):
        """Test creating FieldError with all fields."""
        error = FieldError(
            line=10,
            column=15,
            field_name='price:成交量',
            error_type='invalid_field',
            message='Invalid field name',
            suggestion='Did you mean "price:成交金額"?'
        )
        assert error.line == 10
        assert error.column == 15
        assert error.field_name == 'price:成交量'
        assert error.error_type == 'invalid_field'
        assert error.message == 'Invalid field name'
        assert error.suggestion == 'Did you mean "price:成交金額"?'

    def test_field_error_without_suggestion(self):
        """Test creating FieldError without suggestion."""
        error = FieldError(
            line=5,
            column=10,
            field_name='invalid_field',
            error_type='syntax_error',
            message='Syntax error in field name'
        )
        assert error.suggestion is None

    def test_field_error_str_representation(self):
        """Test FieldError string representation."""
        error = FieldError(
            line=10, column=15, field_name='price:成交量',
            error_type='invalid_field', message='Invalid field',
            suggestion='Did you mean "price:成交金額"?'
        )
        error_str = str(error)
        assert '10:15' in error_str
        assert 'invalid_field' in error_str
        assert 'Invalid field' in error_str
        assert 'Did you mean' in error_str

    def test_field_error_str_without_suggestion(self):
        """Test FieldError string representation without suggestion."""
        error = FieldError(
            line=5, column=10, field_name='xyz',
            error_type='invalid', message='Bad field'
        )
        error_str = str(error)
        assert '5:10' in error_str
        assert 'Bad field' in error_str
        assert 'Did you mean' not in error_str


class TestFieldWarning:
    def test_create_field_warning(self):
        """Test creating FieldWarning."""
        warning = FieldWarning(
            line=5, column=10, field_name='turnover',
            warning_type='deprecated_alias',
            message='Alias "turnover" is deprecated',
            suggestion='Use "price:成交金額" instead'
        )
        assert warning.line == 5
        assert warning.column == 10
        assert warning.field_name == 'turnover'
        assert warning.warning_type == 'deprecated_alias'
        assert warning.message == 'Alias "turnover" is deprecated'
        assert warning.suggestion == 'Use "price:成交金額" instead'

    def test_field_warning_without_suggestion(self):
        """Test creating FieldWarning without suggestion."""
        warning = FieldWarning(
            line=3, column=5, field_name='old_field',
            warning_type='performance',
            message='This field may have performance impact'
        )
        assert warning.suggestion is None

    def test_field_warning_str_representation(self):
        """Test FieldWarning string representation."""
        warning = FieldWarning(
            line=5, column=10, field_name='turnover',
            warning_type='deprecated_alias',
            message='Deprecated alias',
            suggestion='Use "price:成交金額"'
        )
        warning_str = str(warning)
        assert '5:10' in warning_str
        assert 'deprecated_alias' in warning_str
        assert 'Deprecated alias' in warning_str
        assert 'Use "price:成交金額"' in warning_str


class TestValidationResult:
    def test_create_empty_validation_result(self):
        """Test creating empty ValidationResult."""
        result = ValidationResult()
        assert result.errors == []
        assert result.warnings == []
        assert result.is_valid is True

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors."""
        error = FieldError(
            line=10, column=15, field_name='price:成交量',
            error_type='invalid_field', message='Invalid',
            suggestion='price:成交金額'
        )
        result = ValidationResult(errors=[error])
        assert len(result.errors) == 1
        assert result.is_valid is False

    def test_validation_result_with_warnings_only(self):
        """Test ValidationResult with warnings but no errors."""
        warning = FieldWarning(
            line=5, column=10, field_name='turnover',
            warning_type='deprecated', message='Old alias'
        )
        result = ValidationResult(warnings=[warning])
        assert len(result.warnings) == 1
        assert result.is_valid is True  # Warnings don't affect validity

    def test_validation_result_with_errors_and_warnings(self):
        """Test ValidationResult with both errors and warnings."""
        error = FieldError(
            line=10, column=15, field_name='bad',
            error_type='invalid', message='Invalid field'
        )
        warning = FieldWarning(
            line=5, column=10, field_name='turnover',
            warning_type='deprecated', message='Old alias'
        )
        result = ValidationResult(errors=[error], warnings=[warning])
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.is_valid is False

    def test_add_error_method(self):
        """Test adding error dynamically."""
        result = ValidationResult()
        assert result.is_valid is True

        result.add_error(
            line=10, column=15, field_name='xyz',
            error_type='invalid', message='Bad field'
        )
        assert len(result.errors) == 1
        assert result.errors[0].line == 10
        assert result.errors[0].column == 15
        assert result.errors[0].field_name == 'xyz'
        assert result.is_valid is False

    def test_add_error_with_suggestion(self):
        """Test adding error with suggestion."""
        result = ValidationResult()
        result.add_error(
            line=10, column=15, field_name='price:成交量',
            error_type='invalid_field', message='Invalid field',
            suggestion='Did you mean "price:成交金額"?'
        )
        assert len(result.errors) == 1
        assert result.errors[0].suggestion == 'Did you mean "price:成交金額"?'

    def test_add_warning_method(self):
        """Test adding warning dynamically."""
        result = ValidationResult()
        result.add_warning(
            line=5, column=10, field_name='turnover',
            warning_type='deprecated', message='Old alias'
        )
        assert len(result.warnings) == 1
        assert result.warnings[0].line == 5
        assert result.warnings[0].field_name == 'turnover'
        assert result.is_valid is True  # Warnings don't affect validity

    def test_add_multiple_errors_and_warnings(self):
        """Test adding multiple errors and warnings."""
        result = ValidationResult()

        result.add_error(line=10, column=15, field_name='err1',
                        error_type='invalid', message='Error 1')
        result.add_error(line=20, column=25, field_name='err2',
                        error_type='invalid', message='Error 2')
        result.add_warning(line=5, column=10, field_name='warn1',
                          warning_type='deprecated', message='Warning 1')
        result.add_warning(line=15, column=20, field_name='warn2',
                          warning_type='performance', message='Warning 2')

        assert len(result.errors) == 2
        assert len(result.warnings) == 2
        assert result.is_valid is False

    def test_validation_result_str_with_errors(self):
        """Test ValidationResult string representation with errors."""
        result = ValidationResult()
        result.add_error(line=10, column=15, field_name='bad',
                        error_type='invalid', message='Invalid field')
        result_str = str(result)
        assert 'Errors (1)' in result_str
        assert 'Line 10:15' in result_str

    def test_validation_result_str_with_warnings(self):
        """Test ValidationResult string representation with warnings."""
        result = ValidationResult()
        result.add_warning(line=5, column=10, field_name='old',
                          warning_type='deprecated', message='Deprecated')
        result_str = str(result)
        assert 'Warnings (1)' in result_str
        assert 'Line 5:10' in result_str

    def test_validation_result_str_empty(self):
        """Test ValidationResult string representation when empty."""
        result = ValidationResult()
        result_str = str(result)
        assert '✅ Validation passed' in result_str

    def test_validation_result_str_with_both(self):
        """Test ValidationResult string representation with errors and warnings."""
        result = ValidationResult()
        result.add_error(line=10, column=15, field_name='bad',
                        error_type='invalid', message='Invalid')
        result.add_warning(line=5, column=10, field_name='old',
                          warning_type='deprecated', message='Deprecated')
        result_str = str(result)
        assert 'Errors (1)' in result_str
        assert 'Warnings (1)' in result_str
