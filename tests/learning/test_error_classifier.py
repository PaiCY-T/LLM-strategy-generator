"""
Tests for Learning Module Error Classifier - TDD RED Phase.

Validates that ErrorClassifier correctly implements IErrorClassifier Protocol
and satisfies behavioral contracts for deterministic error classification.

Test Coverage:
    - Protocol compliance (IErrorClassifier interface)
    - Deterministic classification (same input → same output)
    - Error categorization (SYNTAX, IMPORT, RUNTIME, VALIDATION, LOGIC)
    - Chinese error message handling
    - Edge cases (empty/None inputs)
    - Return value structure validation

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Phase 5B.4: Implement IErrorClassifier Protocol
"""

import pytest
from typing import Dict, Any
from src.learning.interfaces import IErrorClassifier


class TestProtocolCompliance:
    """Test that ErrorClassifier satisfies IErrorClassifier Protocol.

    TDD Phase: RED - These tests should FAIL initially because
    ErrorClassifier doesn't exist yet.
    """

    def test_error_classifier_implements_protocol(self) -> None:
        """ErrorClassifier must satisfy IErrorClassifier Protocol."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Runtime protocol check - should pass if structural typing is correct
        assert isinstance(classifier, IErrorClassifier), \
            "ErrorClassifier must implement IErrorClassifier Protocol"

    def test_classify_error_method_exists(self) -> None:
        """ErrorClassifier must provide classify_error() method."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Method must exist and be callable
        assert hasattr(classifier, 'classify_error'), \
            "ErrorClassifier must have classify_error method"
        assert callable(classifier.classify_error), \
            "classify_error must be callable"

    def test_classify_error_signature(self) -> None:
        """classify_error() must accept Dict[str, Any] and return Dict[str, Any]."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Test input: empty dict (edge case)
        result = classifier.classify_error({})

        # Result must be a dictionary
        assert isinstance(result, dict), \
            "classify_error must return Dict[str, Any]"

        # Test input: metrics with error info
        metrics = {
            'error_type': 'KeyError',
            'error_msg': "key 'price' not found"
        }
        result = classifier.classify_error(metrics)
        assert isinstance(result, dict), \
            "classify_error must return Dict for error input"


class TestBehavioralContracts:
    """Test behavioral contracts specified in IErrorClassifier Protocol.

    TDD Phase: RED - Tests enforce determinism, graceful handling, etc.
    """

    def test_deterministic_classification(self) -> None:
        """Same input MUST produce same category (deterministic)."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'SyntaxError',
            'error_msg': 'invalid syntax at line 5'
        }

        # Call multiple times with same input
        result1 = classifier.classify_error(metrics)
        result2 = classifier.classify_error(metrics)
        result3 = classifier.classify_error(metrics)

        # Results must be identical (deterministic)
        assert result1['category'] == result2['category'] == result3['category'], \
            "Classification must be deterministic for same input"
        assert result1['classification_level'] == result2['classification_level'], \
            "Classification level must be deterministic"

    def test_empty_input_returns_valid_classification(self) -> None:
        """Empty dict MUST return valid classification (default to UNKNOWN/RUNTIME)."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Empty metrics dict (no error info)
        result = classifier.classify_error({})

        # Must still return valid structure
        assert 'category' in result, "Must return category even for empty input"
        assert 'classification_level' in result, "Must return level even for empty input"

        # Should default to a safe category (RUNTIME or UNKNOWN)
        assert result['category'] is not None, "Category must not be None"

    def test_none_values_handled_gracefully(self) -> None:
        """None error_type/error_msg MUST be handled gracefully."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Test None error_type
        metrics1 = {'error_type': None, 'error_msg': 'some error'}
        result1 = classifier.classify_error(metrics1)
        assert 'category' in result1, "Must handle None error_type"

        # Test None error_msg
        metrics2 = {'error_type': 'ValueError', 'error_msg': None}
        result2 = classifier.classify_error(metrics2)
        assert 'category' in result2, "Must handle None error_msg"

        # Test both None
        metrics3 = {'error_type': None, 'error_msg': None}
        result3 = classifier.classify_error(metrics3)
        assert 'category' in result3, "Must handle all None values"


class TestErrorCategorization:
    """Test error classification into standard categories.

    Categories (from Protocol docstring):
        - SYNTAX: Python syntax errors (SyntaxError, IndentationError)
        - IMPORT: Module import errors (ImportError, ModuleNotFoundError)
        - RUNTIME: Runtime execution errors (KeyError, ValueError, TypeError)
        - VALIDATION: Data validation errors
        - LOGIC: Business logic errors

    TDD Phase: RED - Define expected behavior for each category.
    """

    def test_syntax_error_classification(self) -> None:
        """SyntaxError → SYNTAX category."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'SyntaxError',
            'error_msg': 'invalid syntax at line 10'
        }
        result = classifier.classify_error(metrics)

        # Normalize category to string for comparison (enum or string)
        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert 'syntax' in str(category).lower(), \
            "SyntaxError must map to SYNTAX category"

    def test_import_error_classification(self) -> None:
        """ImportError → IMPORT category."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'ImportError',
            'error_msg': "cannot import name 'missing_module'"
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert 'import' in str(category).lower() or 'syntax' in str(category).lower(), \
            "ImportError must map to IMPORT or SYNTAX category"

    def test_runtime_error_classification(self) -> None:
        """KeyError/ValueError/TypeError → RUNTIME category."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Test KeyError
        metrics1 = {
            'error_type': 'KeyError',
            'error_msg': "key 'price' not found"
        }
        result1 = classifier.classify_error(metrics1)
        category1 = result1['category']
        if hasattr(category1, 'value'):
            category1 = category1.value

        # KeyError should be RUNTIME or DATA_MISSING
        assert any(
            keyword in str(category1).lower()
            for keyword in ['runtime', 'data', 'missing']
        ), "KeyError must map to RUNTIME-related category"

        # Test ValueError (may be OTHER, CALCULATION, or DATA_MISSING)
        metrics2 = {
            'error_type': 'ValueError',
            'error_msg': 'invalid literal for int()'
        }
        result2 = classifier.classify_error(metrics2)
        category2 = result2['category']
        if hasattr(category2, 'value'):
            category2 = category2.value

        # ValueError can be OTHER, CALCULATION, or DATA_MISSING depending on message
        assert any(
            keyword in str(category2).lower()
            for keyword in ['runtime', 'calculation', 'validation', 'other', 'data', 'missing']
        ), "ValueError must map to a valid category"

    def test_indentation_error_classification(self) -> None:
        """IndentationError → SYNTAX category."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'IndentationError',
            'error_msg': 'expected an indented block'
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert 'syntax' in str(category).lower(), \
            "IndentationError must map to SYNTAX category"

    def test_name_error_classification(self) -> None:
        """NameError → SYNTAX category."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'NameError',
            'error_msg': "name 'undefined_var' is not defined"
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert 'syntax' in str(category).lower(), \
            "NameError must map to SYNTAX category"


class TestChineseErrorMessages:
    """Test support for Chinese error messages.

    TDD Phase: RED - Ensure Chinese messages are classified correctly.
    """

    def test_chinese_syntax_error(self) -> None:
        """Chinese syntax error message classification."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'SyntaxError',
            'error_msg': '語法錯誤：第10行'
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert 'syntax' in str(category).lower(), \
            "Chinese SyntaxError must map to SYNTAX category"

    def test_chinese_key_error(self) -> None:
        """Chinese KeyError message classification."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'KeyError',
            'error_msg': "找不到鍵 'price'"
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        # Should classify as DATA_MISSING or RUNTIME
        assert any(
            keyword in str(category).lower()
            for keyword in ['data', 'missing', 'runtime']
        ), "Chinese KeyError must map to DATA_MISSING or RUNTIME category"

    def test_chinese_import_error(self) -> None:
        """Chinese ImportError message classification."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'ModuleNotFoundError',
            'error_msg': "找不到模組 'pandas'"
        }
        result = classifier.classify_error(metrics)

        category = result['category']
        if hasattr(category, 'value'):
            category = category.value

        assert any(
            keyword in str(category).lower()
            for keyword in ['import', 'syntax']
        ), "Chinese ImportError must map to IMPORT or SYNTAX category"


class TestReturnValueStructure:
    """Test return value structure and required fields.

    Required fields (from Protocol):
        - category: ErrorCategory enum value
        - classification_level: str (LEVEL_X)
        - confidence: float 0.0-1.0 (optional)
        - details: dict (optional)

    TDD Phase: RED - Validate return value contract.
    """

    def test_return_value_has_category(self) -> None:
        """Return dict MUST have 'category' key."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'ValueError',
            'error_msg': 'invalid value'
        }
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Return dict must have 'category' key"
        assert result['category'] is not None, "Category must not be None"

    def test_return_value_has_classification_level(self) -> None:
        """Return dict MUST have 'classification_level' key."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'SyntaxError',
            'error_msg': 'invalid syntax'
        }
        result = classifier.classify_error(metrics)

        assert 'classification_level' in result, \
            "Return dict must have 'classification_level' key"
        assert isinstance(result['classification_level'], str), \
            "classification_level must be a string"

    def test_optional_confidence_field(self) -> None:
        """Return dict MAY have 'confidence' key (optional)."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'KeyError',
            'error_msg': 'key not found'
        }
        result = classifier.classify_error(metrics)

        # Confidence is optional but if present must be float 0.0-1.0
        if 'confidence' in result:
            assert isinstance(result['confidence'], float), \
                "confidence must be float if present"
            assert 0.0 <= result['confidence'] <= 1.0, \
                "confidence must be in range [0.0, 1.0]"

    def test_optional_details_field(self) -> None:
        """Return dict MAY have 'details' key (optional)."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        metrics = {
            'error_type': 'TypeError',
            'error_msg': 'type mismatch'
        }
        result = classifier.classify_error(metrics)

        # Details is optional but if present must be dict
        if 'details' in result:
            assert isinstance(result['details'], dict), \
                "details must be dict if present"


class TestEdgeCases:
    """Test edge cases and boundary conditions.

    TDD Phase: RED - Define expected behavior for edge cases.
    """

    def test_missing_error_type_key(self) -> None:
        """Metrics dict without 'error_type' key handled gracefully."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Only error_msg, no error_type
        metrics = {'error_msg': 'something went wrong'}
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must return category even without error_type"

    def test_missing_error_msg_key(self) -> None:
        """Metrics dict without 'error_msg' key handled gracefully."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Only error_type, no error_msg
        metrics = {'error_type': 'RuntimeError'}
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must return category even without error_msg"

    def test_extra_keys_ignored(self) -> None:
        """Extra keys in metrics dict are safely ignored."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Metrics with extra keys
        metrics = {
            'error_type': 'ValueError',
            'error_msg': 'invalid value',
            'extra_key1': 'ignored',
            'extra_key2': 12345,
            'traceback': 'full traceback...'
        }
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must classify even with extra keys"

    def test_empty_string_values(self) -> None:
        """Empty string values handled gracefully."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Empty strings
        metrics = {'error_type': '', 'error_msg': ''}
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must handle empty string values"

    def test_whitespace_only_values(self) -> None:
        """Whitespace-only values handled gracefully."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Whitespace-only strings
        metrics = {'error_type': '   ', 'error_msg': '\t\n  '}
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must handle whitespace-only values"

    def test_very_long_error_message(self) -> None:
        """Very long error messages don't cause issues."""
        from src.learning.error_classifier import ErrorClassifier

        classifier = ErrorClassifier()

        # Very long error message (10KB)
        long_msg = "x" * 10000 + "division by zero"
        metrics = {
            'error_type': 'ZeroDivisionError',
            'error_msg': long_msg
        }
        result = classifier.classify_error(metrics)

        assert 'category' in result, "Must handle very long error messages"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
