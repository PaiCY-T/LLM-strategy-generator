"""
Test Suite for YAMLToCodeGenerator
===================================

Comprehensive tests for the YAML to Code generation pipeline, ensuring:
1. All 3 strategy types generate valid code
2. All 5 position sizing methods work correctly
3. YAML validation errors are caught
4. AST validation errors are caught
5. End-to-end: YAML file → Python code
6. Batch processing capabilities
7. Error reporting and statistics

Coverage target: >85%

Test Structure:
---------------
- TestYAMLToCodeGeneratorBasic: Basic initialization and simple generation
- TestYAMLToCodeGeneratorStrategyTypes: All 3 strategy types
- TestYAMLToCodeGeneratorPositionSizing: All 5 position sizing methods
- TestYAMLToCodeGeneratorValidation: Validation error handling
- TestYAMLToCodeGeneratorFileOperations: File-based generation
- TestYAMLToCodeGeneratorBatch: Batch processing
- TestYAMLToCodeGeneratorErrorReporting: Error messages and statistics

Requirements Coverage:
----------------------
- Requirement 2.3: Syntactically correct Python code generation
- Requirement 2.4: Correct FinLab API usage
- Requirement 2.5: All indicator types and position sizing methods supported
- Requirement 5.2: Integration with validation and template modules
"""

import pytest
import ast
import yaml
from pathlib import Path
from typing import Dict, Any

from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_template import YAMLToCodeTemplate


# Test fixtures
@pytest.fixture
def validator():
    """Create YAMLSchemaValidator instance."""
    return YAMLSchemaValidator()


@pytest.fixture
def generator(validator):
    """Create YAMLToCodeGenerator instance with validator."""
    return YAMLToCodeGenerator(validator)


@pytest.fixture
def test_data_dir():
    """Get path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def minimal_valid_spec():
    """Minimal valid YAML spec for testing."""
    return {
        'metadata': {
            'name': 'Test Strategy',
            'description': 'A minimal test strategy for unit testing',
            'strategy_type': 'momentum',
            'rebalancing_frequency': 'M',
            'version': '1.0.0'
        },
        'indicators': {
            'technical_indicators': [
                {
                    'name': 'rsi_14',
                    'type': 'RSI',
                    'period': 14,
                    'source': "data.get('RSI_14')"
                }
            ]
        },
        'entry_conditions': {
            'threshold_rules': [
                {
                    'condition': 'rsi_14 > 30'
                }
            ],
            'logical_operator': 'AND'
        },
        'position_sizing': {
            'method': 'equal_weight',
            'max_positions': 20
        }
    }


# =============================================================================
# Basic Tests
# =============================================================================

class TestYAMLToCodeGeneratorBasic:
    """Test basic initialization and simple generation."""

    def test_init_with_validator(self, validator):
        """Test initialization with provided validator."""
        generator = YAMLToCodeGenerator(validator)
        assert generator.validator is validator
        assert isinstance(generator.template, YAMLToCodeTemplate)
        assert generator.validate_semantics is True

    def test_init_without_validator(self):
        """Test initialization with default validator."""
        generator = YAMLToCodeGenerator()
        assert isinstance(generator.validator, YAMLSchemaValidator)
        assert isinstance(generator.template, YAMLToCodeTemplate)

    def test_init_with_semantics_flag(self, validator):
        """Test initialization with semantic validation disabled."""
        generator = YAMLToCodeGenerator(validator, validate_semantics=False)
        assert generator.validate_semantics is False

    def test_generate_minimal_spec(self, generator, minimal_valid_spec):
        """Test generation from minimal valid spec."""
        code, errors = generator.generate(minimal_valid_spec)

        # Should succeed
        assert errors == []
        assert code is not None
        assert len(code) > 0

        # Should be valid Python
        ast.parse(code)

        # Should contain strategy function
        assert 'def strategy(data):' in code
        assert 'rsi_14' in code


# =============================================================================
# Strategy Types Tests
# =============================================================================

class TestYAMLToCodeGeneratorStrategyTypes:
    """Test all 3 strategy types generate valid code."""

    def test_momentum_strategy(self, generator, test_data_dir):
        """Test momentum strategy type."""
        yaml_path = test_data_dir / "momentum_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        # Should succeed
        assert errors == []
        assert code is not None

        # Should be valid Python
        ast.parse(code)

        # Should contain momentum-specific elements
        assert 'def strategy(data):' in code
        assert 'rsi_14' in code
        assert 'ma_50' in code
        assert 'ma_200' in code
        assert 'RSI Momentum Strategy' in code

    def test_mean_reversion_strategy(self, generator, test_data_dir):
        """Test mean reversion strategy type."""
        yaml_path = test_data_dir / "mean_reversion_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        # Should succeed
        assert errors == []
        assert code is not None

        # Should be valid Python
        ast.parse(code)

        # Should contain mean reversion elements
        assert 'def strategy(data):' in code
        assert 'bb_upper' in code or 'bb_lower' in code
        assert 'rsi_14' in code
        assert 'Bollinger Band Mean Reversion' in code

    def test_factor_combination_strategy(self, generator, test_data_dir):
        """Test factor combination strategy type."""
        yaml_path = test_data_dir / "factor_combination_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        # Should succeed
        assert errors == []
        assert code is not None

        # Should be valid Python
        ast.parse(code)

        # Should contain factor combination elements
        assert 'def strategy(data):' in code
        assert 'roe' in code
        assert 'revenue_growth' in code
        assert 'quality_score' in code
        assert 'Quality Growth Momentum' in code


# =============================================================================
# Position Sizing Methods Tests
# =============================================================================

class TestYAMLToCodeGeneratorPositionSizing:
    """Test all 5 position sizing methods."""

    def test_equal_weight_sizing(self, generator, test_data_dir):
        """Test equal_weight position sizing."""
        yaml_path = test_data_dir / "momentum_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Should contain equal weight logic
        assert 'position = entry_mask.astype(float)' in code
        assert 'Equal weight' in code

    def test_factor_weighted_sizing(self, generator, test_data_dir):
        """Test factor_weighted position sizing."""
        yaml_path = test_data_dir / "factor_combination_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Should contain factor weighting logic
        assert 'weights = quality_score[entry_mask]' in code
        assert 'Weight by factor score' in code

    def test_volatility_weighted_sizing(self, generator, test_data_dir):
        """Test volatility_weighted position sizing."""
        yaml_path = test_data_dir / "volatility_weighted_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Should contain volatility weighting logic
        assert 'volatility = returns.rolling(60).std()' in code
        assert 'inv_vol = 1.0 / volatility' in code
        assert 'Volatility-weighted' in code

    def test_risk_parity_sizing(self, generator, test_data_dir):
        """Test risk_parity position sizing."""
        yaml_path = test_data_dir / "mean_reversion_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Should contain risk parity logic
        assert 'volatility = returns.rolling(60).std()' in code
        assert 'inv_vol = 1.0 / volatility' in code
        assert 'Risk parity' in code

    def test_custom_formula_sizing(self, generator, test_data_dir):
        """Test custom_formula position sizing."""
        yaml_path = test_data_dir / "custom_formula_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Should contain custom formula logic
        assert 'custom_weights = combined_score' in code
        assert 'Custom position sizing formula' in code


# =============================================================================
# Validation Tests
# =============================================================================

class TestYAMLToCodeGeneratorValidation:
    """Test validation error handling."""

    def test_missing_required_field(self, generator):
        """Test validation error for missing required field."""
        invalid_spec = {
            'metadata': {
                'name': 'Invalid Strategy'
                # Missing strategy_type and rebalancing_frequency
            }
        }

        code, errors = generator.generate(invalid_spec)

        # Should fail validation
        assert code is None
        assert len(errors) > 0
        assert any('required' in error.lower() for error in errors)

    def test_invalid_strategy_type(self, generator, minimal_valid_spec):
        """Test validation error for invalid strategy type."""
        invalid_spec = minimal_valid_spec.copy()
        invalid_spec['metadata']['strategy_type'] = 'invalid_type'

        code, errors = generator.generate(invalid_spec)

        # Should fail validation
        assert code is None
        assert len(errors) > 0
        assert any('strategy_type' in error for error in errors)

    def test_invalid_position_sizing_method(self, generator, minimal_valid_spec):
        """Test validation error for invalid position sizing method."""
        invalid_spec = minimal_valid_spec.copy()
        invalid_spec['position_sizing']['method'] = 'invalid_method'

        code, errors = generator.generate(invalid_spec)

        # Should fail validation
        assert code is None
        assert len(errors) > 0

    def test_indicator_reference_validation(self, generator):
        """Test semantic validation for undefined indicator references."""
        spec = {
            'metadata': {
                'name': 'Test Strategy',
                'description': 'Test strategy for indicator reference validation',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'rsi_14',
                        'type': 'RSI',
                        'period': 14,
                        'source': "data.get('RSI_14')"
                    }
                ]
            },
            'entry_conditions': {
                'ranking_rules': [
                    {
                        'field': 'undefined_indicator',  # Not defined in indicators
                        'method': 'top_percent',
                        'value': 20
                    }
                ]
            },
            'position_sizing': {
                'method': 'equal_weight'
            }
        }

        code, errors = generator.generate(spec)

        # Should fail semantic validation
        assert code is None
        assert len(errors) > 0
        # Check for undefined indicator error
        error_text = ' '.join(errors)
        assert 'undefined_indicator' in error_text or 'not found' in error_text.lower()

    def test_validate_only_method(self, generator, minimal_valid_spec):
        """Test validate_only method."""
        is_valid, errors = generator.validate_only(minimal_valid_spec)

        assert is_valid is True
        assert errors == []

    def test_validate_only_invalid_spec(self, generator):
        """Test validate_only with invalid spec."""
        invalid_spec = {'metadata': {'name': 'Invalid'}}

        is_valid, errors = generator.validate_only(invalid_spec)

        assert is_valid is False
        assert len(errors) > 0


# =============================================================================
# File Operations Tests
# =============================================================================

class TestYAMLToCodeGeneratorFileOperations:
    """Test file-based generation."""

    def test_generate_from_file_success(self, generator, test_data_dir):
        """Test successful generation from file."""
        yaml_path = test_data_dir / "momentum_strategy.yaml"
        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

    def test_generate_from_file_not_found(self, generator):
        """Test error handling for non-existent file."""
        code, errors = generator.generate_from_file('nonexistent.yaml')

        assert code is None
        assert len(errors) > 0
        assert any('not found' in error.lower() for error in errors)

    def test_generate_from_invalid_yaml_file(self, generator, tmp_path):
        """Test error handling for invalid YAML syntax."""
        # Create invalid YAML file
        invalid_yaml = tmp_path / "invalid.yaml"
        invalid_yaml.write_text("invalid: yaml: syntax: [unclosed")

        code, errors = generator.generate_from_file(str(invalid_yaml))

        assert code is None
        assert len(errors) > 0
        assert any('parsing error' in error.lower() for error in errors)

    def test_generate_from_file_with_pathlib(self, generator, test_data_dir):
        """Test generate_from_file with pathlib.Path object."""
        yaml_path = test_data_dir / "momentum_strategy.yaml"
        code, errors = generator.generate_from_file(yaml_path)

        assert errors == []
        assert code is not None


# =============================================================================
# Batch Processing Tests
# =============================================================================

class TestYAMLToCodeGeneratorBatch:
    """Test batch processing capabilities."""

    def test_generate_batch_all_valid(self, generator, test_data_dir):
        """Test batch generation with all valid specs."""
        # Load all test YAML files
        specs = []
        for yaml_file in test_data_dir.glob("*.yaml"):
            with open(yaml_file) as f:
                spec = yaml.safe_load(f)
                specs.append(spec)

        results = generator.generate_batch(specs)

        # All should succeed
        assert len(results) == len(specs)
        for code, errors in results:
            assert errors == []
            assert code is not None
            ast.parse(code)

    def test_generate_batch_mixed_results(self, generator, minimal_valid_spec):
        """Test batch generation with mixed valid/invalid specs."""
        specs = [
            minimal_valid_spec,
            {'invalid': 'spec'},  # Invalid
            minimal_valid_spec,
        ]

        results = generator.generate_batch(specs)

        assert len(results) == 3
        # First and third should succeed
        assert results[0][1] == []
        assert results[2][1] == []
        # Second should fail
        assert results[1][0] is None
        assert len(results[1][1]) > 0

    def test_generate_batch_from_files(self, generator, test_data_dir):
        """Test batch file generation."""
        yaml_files = [str(f) for f in test_data_dir.glob("*.yaml")]

        results = generator.generate_batch_from_files(yaml_files)

        # All should succeed
        assert len(results) == len(yaml_files)
        for code, errors in results:
            assert errors == []
            assert code is not None
            ast.parse(code)

    def test_generate_batch_empty_list(self, generator):
        """Test batch generation with empty list."""
        results = generator.generate_batch([])
        assert results == []


# =============================================================================
# Error Reporting and Statistics Tests
# =============================================================================

class TestYAMLToCodeGeneratorErrorReporting:
    """Test error messages and statistics."""

    def test_clear_error_messages(self, generator):
        """Test that error messages are clear and actionable."""
        invalid_spec = {
            'metadata': {
                'name': 'Test'
                # Missing required fields
            }
        }

        code, errors = generator.generate(invalid_spec)

        assert len(errors) > 0
        # Error messages should be descriptive (length > 10)
        for error in errors:
            assert len(error) > 10
            # Should contain informative keywords
            error_lower = error.lower()
            assert ('required' in error_lower or 'missing' in error_lower or
                    'too short' in error_lower or 'property' in error_lower)

    def test_get_generation_stats_all_success(self, generator, minimal_valid_spec):
        """Test statistics for all successful generations."""
        results = [(code, []) for _ in range(5) for code in ['valid_code']]

        stats = generator.get_generation_stats(results)

        assert stats['total'] == 5
        assert stats['successful'] == 5
        assert stats['failed'] == 0
        assert stats['success_rate'] == 100.0
        assert stats['error_types'] == {}

    def test_get_generation_stats_mixed(self, generator):
        """Test statistics for mixed results."""
        results = [
            ('code1', []),
            (None, ['validation error']),
            ('code2', []),
            (None, ['syntax error']),
            (None, ['template error']),
        ]

        stats = generator.get_generation_stats(results)

        assert stats['total'] == 5
        assert stats['successful'] == 2
        assert stats['failed'] == 3
        assert stats['success_rate'] == 40.0
        assert 'validation_error' in stats['error_types']
        assert 'syntax_error' in stats['error_types']
        assert 'template_error' in stats['error_types']

    def test_get_generation_stats_error_categorization(self, generator):
        """Test error type categorization."""
        results = [
            (None, ['YAML validation failed']),
            (None, ['Generated code has syntax errors']),
            (None, ['Template rendering failed']),
            (None, ['File not found']),
            (None, ['Unknown error']),
        ]

        stats = generator.get_generation_stats(results)

        error_types = stats['error_types']
        assert error_types.get('validation_error', 0) > 0
        assert error_types.get('syntax_error', 0) > 0
        assert error_types.get('template_error', 0) > 0
        assert error_types.get('file_not_found', 0) > 0
        assert error_types.get('other_error', 0) > 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestYAMLToCodeGeneratorIntegration:
    """Integration tests for complete pipeline."""

    def test_end_to_end_momentum(self, generator, test_data_dir):
        """Test complete end-to-end pipeline for momentum strategy."""
        yaml_path = test_data_dir / "momentum_strategy.yaml"

        # Load YAML
        with open(yaml_path) as f:
            spec = yaml.safe_load(f)

        # Validate spec
        is_valid, errors = generator.validate_only(spec)
        assert is_valid
        assert errors == []

        # Generate code
        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None

        # Validate Python syntax
        ast.parse(code)

        # Check FinLab API usage
        assert "data.get('price:收盤價')" in code
        assert "data.get('price:成交股數')" in code
        assert "data.get('RSI_14')" in code
        assert "data.get('MA_50')" in code

        # Check entry conditions
        assert 'rsi_14 > 30' in code
        assert 'ma_50 > ma_200' in code

        # Check position sizing
        assert 'position = entry_mask.astype(float)' in code

    def test_end_to_end_factor_combination(self, generator, test_data_dir):
        """Test complete end-to-end pipeline for factor combination strategy."""
        yaml_path = test_data_dir / "factor_combination_strategy.yaml"

        code, errors = generator.generate_from_file(str(yaml_path))

        assert errors == []
        assert code is not None
        ast.parse(code)

        # Check all components
        assert "data.get('ROE')" in code
        assert "data.get('revenue_growth')" in code
        assert 'quality_score = roe * (1 + revenue_growth)' in code
        assert 'ranking_mask' in code
        assert 'weights = quality_score[entry_mask]' in code

    def test_syntax_correctness_guarantee(self, generator, test_data_dir):
        """Test that ALL generated code is syntactically correct."""
        yaml_files = list(test_data_dir.glob("*.yaml"))

        for yaml_file in yaml_files:
            code, errors = generator.generate_from_file(str(yaml_file))

            # Every valid spec should generate valid Python
            if not errors:
                # Should not raise SyntaxError
                ast.parse(code)

                # Should have strategy function
                tree = ast.parse(code)
                functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                function_names = [f.name for f in functions]
                assert 'strategy' in function_names


# =============================================================================
# Edge Cases and Robustness Tests
# =============================================================================

class TestYAMLToCodeGeneratorEdgeCases:
    """Test edge cases and robustness."""

    def test_empty_spec(self, generator):
        """Test handling of empty spec."""
        code, errors = generator.generate({})

        assert code is None
        assert len(errors) > 0

    def test_none_spec(self, generator):
        """Test handling of None spec."""
        code, errors = generator.generate(None)

        assert code is None
        assert len(errors) > 0

    def test_minimal_indicators(self, generator):
        """Test with single minimal indicator."""
        spec = {
            'metadata': {
                'name': 'Minimal Strategy',
                'description': 'Minimal test strategy with single indicator',
                'strategy_type': 'momentum',
                'rebalancing_frequency': 'M'
            },
            'indicators': {
                'technical_indicators': [
                    {
                        'name': 'close',
                        'type': 'SMA',
                        'period': 1,
                        'source': "data.get('price:收盤價')"
                    }
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': 'close > 0'}
                ]
            },
            'position_sizing': {
                'method': 'equal_weight'
            }
        }

        code, errors = generator.generate(spec)
        assert errors == []
        assert code is not None
        ast.parse(code)

    def test_max_complexity_spec(self, generator):
        """Test with maximum complexity spec."""
        spec = {
            'metadata': {
                'name': 'Complex Strategy',
                'description': 'Maximum complexity test',
                'strategy_type': 'factor_combination',
                'rebalancing_frequency': 'M',
                'version': '1.0.0'
            },
            'indicators': {
                'technical_indicators': [
                    {'name': f'indicator_{i}', 'type': 'RSI', 'period': 14, 'source': f"data.get('RSI_{i}')"}
                    for i in range(5)
                ],
                'fundamental_factors': [
                    {'name': f'factor_{i}', 'field': 'ROE', 'source': f"data.get('ROE_{i}')"}
                    for i in range(5)
                ],
                'custom_calculations': [
                    {'name': f'calc_{i}', 'expression': f'indicator_{i} * factor_{i}'}
                    for i in range(3)
                ]
            },
            'entry_conditions': {
                'threshold_rules': [
                    {'condition': f'indicator_{i} > 30'}
                    for i in range(5)
                ],
                'logical_operator': 'AND'
            },
            'position_sizing': {
                'method': 'equal_weight'
            }
        }

        code, errors = generator.generate(spec)
        # Complex spec should still work
        assert errors == []
        assert code is not None
        ast.parse(code)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
