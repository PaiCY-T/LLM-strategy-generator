"""
Security tests for TemplateParameterGenerator input sanitization.

These tests verify that the _sanitize_parsed_dict() method correctly
rejects malicious LLM responses that could cause:
- DoS attacks via deep nesting or excessive keys
- Memory exhaustion via large arrays/objects
- Prototype pollution via __proto__ injection

Story: Security fix for critical issue #2 from code review
"""

import json
import pytest
from src.generators.template_parameter_generator import TemplateParameterGenerator


class TestSanitizeParsedDict:
    """Test suite for _sanitize_parsed_dict() security validation."""

    def test_sanitize_accepts_valid_flat_dict(self):
        """Valid flat dict with primitives should pass sanitization."""
        generator = TemplateParameterGenerator()

        valid_dict = {
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        }

        result = generator._sanitize_parsed_dict(valid_dict)

        assert result is not None
        assert result == valid_dict

    def test_sanitize_rejects_nested_dict(self):
        """Nested dicts should be rejected (DoS prevention)."""
        generator = TemplateParameterGenerator()

        malicious_dict = {
            'momentum_period': 10,
            'nested': {'deeply': {'nested': 'object'}}  # Nested dict
        }

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_rejects_nested_list(self):
        """Nested lists/arrays should be rejected (memory exhaustion prevention)."""
        generator = TemplateParameterGenerator()

        malicious_dict = {
            'momentum_period': 10,
            'huge_array': [1, 2, 3, 4, 5] * 1000  # Large array
        }

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_rejects_excessive_keys(self):
        """Dicts with >20 keys should be rejected (DoS prevention)."""
        generator = TemplateParameterGenerator()

        # Create dict with 25 keys (exceeds limit of 20)
        malicious_dict = {f'key_{i}': i for i in range(25)}

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_rejects_proto_pollution(self):
        """__proto__ key should be rejected (prototype pollution prevention)."""
        generator = TemplateParameterGenerator()

        malicious_dict = {
            'momentum_period': 10,
            '__proto__': {'polluted': 'value'}
        }

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_rejects_constructor_key(self):
        """constructor key should be rejected."""
        generator = TemplateParameterGenerator()

        malicious_dict = {
            'momentum_period': 10,
            'constructor': 'malicious'
        }

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_rejects_prototype_key(self):
        """prototype key should be rejected."""
        generator = TemplateParameterGenerator()

        malicious_dict = {
            'momentum_period': 10,
            'prototype': 'malicious'
        }

        result = generator._sanitize_parsed_dict(malicious_dict)

        assert result is None

    def test_sanitize_accepts_non_dict_returns_none(self):
        """Non-dict inputs should return None."""
        generator = TemplateParameterGenerator()

        # Test various non-dict types
        assert generator._sanitize_parsed_dict([1, 2, 3]) is None
        assert generator._sanitize_parsed_dict("string") is None
        assert generator._sanitize_parsed_dict(123) is None
        assert generator._sanitize_parsed_dict(None) is None

    def test_sanitize_allows_up_to_20_keys(self):
        """Up to 20 keys should be allowed (boundary test)."""
        generator = TemplateParameterGenerator()

        # Create dict with exactly 20 keys
        valid_dict = {f'key_{i}': i for i in range(20)}

        result = generator._sanitize_parsed_dict(valid_dict)

        assert result is not None
        assert result == valid_dict


class TestParseResponseWithSanitization:
    """Test that _parse_response() correctly calls sanitization."""

    def test_parse_response_sanitizes_valid_json(self):
        """Valid JSON should pass through sanitization."""
        generator = TemplateParameterGenerator()

        response = json.dumps({
            'momentum_period': 10,
            'ma_periods': 60,
            'catalyst_type': 'revenue',
            'catalyst_lookback': 3,
            'n_stocks': 10,
            'stop_loss': 0.10,
            'resample': 'M',
            'resample_offset': 0
        })

        params = generator._parse_response(response)

        assert params is not None
        assert params['momentum_period'] == 10

    def test_parse_response_rejects_malicious_nested_dict(self):
        """Malicious nested dict should be rejected after parsing."""
        generator = TemplateParameterGenerator()

        malicious_response = json.dumps({
            'momentum_period': 10,
            'nested': {'attack': 'payload'}
        })

        params = generator._parse_response(malicious_response)

        # Should return None (sanitization rejected it)
        assert params is None

    def test_parse_response_rejects_malicious_proto(self):
        """__proto__ pollution attempt should be rejected."""
        generator = TemplateParameterGenerator()

        malicious_response = json.dumps({
            'momentum_period': 10,
            '__proto__': {'isAdmin': True}
        })

        params = generator._parse_response(malicious_response)

        # Should return None (sanitization rejected it)
        assert params is None

    def test_parse_response_markdown_with_nested_rejected(self):
        """Markdown block with nested dict should be rejected."""
        generator = TemplateParameterGenerator()

        malicious_response = """
Here are the parameters:

```json
{
    "momentum_period": 10,
    "nested": {
        "attack": "deep nesting DoS"
    }
}
```
"""

        params = generator._parse_response(malicious_response)

        # Should return None (sanitization rejected nested structure)
        assert params is None


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
