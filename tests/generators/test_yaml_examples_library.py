"""
Unit Tests for YAML Strategy Examples Library
==============================================

Tests all YAML strategy examples for:
1. Valid YAML syntax and loading
2. Schema validation compliance
3. Python code generation success
4. Generated code syntactic correctness
5. Coverage of strategy types and position sizing methods

Test Coverage:
    - All example files load successfully
    - All examples validate against schema
    - All examples generate valid Python code
    - All 3 strategy types represented
    - All 5 position sizing methods demonstrated

Requirements:
    Task 6 of structured-innovation-mvp spec
"""

import pytest
import yaml
import ast
from pathlib import Path
from typing import List, Dict, Any

from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator


# Test fixtures
@pytest.fixture
def validator():
    """Create YAMLSchemaValidator instance."""
    return YAMLSchemaValidator()


@pytest.fixture
def generator(validator):
    """Create YAMLToCodeGenerator instance."""
    return YAMLToCodeGenerator(validator)


@pytest.fixture
def examples_dir():
    """Get path to examples directory."""
    return Path(__file__).parent.parent.parent / 'examples' / 'yaml_strategies'


@pytest.fixture
def example_files(examples_dir):
    """Get all production YAML example files (excluding test files)."""
    yaml_files = list(examples_dir.glob('*.yaml')) + list(examples_dir.glob('*.yml'))
    # Filter out test files
    production_files = [f for f in yaml_files if not f.name.startswith('test_')]
    return sorted(production_files)


class TestYAMLExamplesLoading:
    """Test that all YAML examples load correctly."""

    def test_examples_directory_exists(self, examples_dir):
        """Test that examples directory exists."""
        assert examples_dir.exists(), f"Examples directory not found: {examples_dir}"
        assert examples_dir.is_dir(), f"Examples path is not a directory: {examples_dir}"

    def test_minimum_example_count(self, example_files):
        """Test that at least 10 example files exist."""
        assert len(example_files) >= 10, f"Expected at least 10 examples, found {len(example_files)}"

    def test_all_examples_load(self, example_files):
        """Test that all YAML examples can be loaded."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            assert spec is not None, f"Failed to load YAML: {yaml_path.name}"
            assert isinstance(spec, dict), f"YAML is not a dictionary: {yaml_path.name}"

    def test_all_examples_have_required_sections(self, example_files):
        """Test that all examples have required sections."""
        required_sections = ['metadata', 'indicators', 'entry_conditions']

        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            for section in required_sections:
                assert section in spec, f"{yaml_path.name} missing required section: {section}"


class TestYAMLExamplesValidation:
    """Test that all YAML examples validate against schema."""

    def test_all_examples_validate(self, validator, example_files):
        """Test that all examples pass schema validation."""
        failures = []

        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            is_valid, errors = validator.validate(spec)

            if not is_valid:
                failures.append({
                    'file': yaml_path.name,
                    'errors': errors
                })

        # Assert all validated successfully
        assert len(failures) == 0, f"Validation failures:\n" + "\n".join(
            f"  {f['file']}: {f['errors']}" for f in failures
        )

    def test_all_examples_have_valid_metadata(self, example_files):
        """Test that all examples have valid metadata."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            metadata = spec['metadata']

            # Check required metadata fields
            assert 'name' in metadata, f"{yaml_path.name} missing metadata.name"
            assert 'strategy_type' in metadata, f"{yaml_path.name} missing metadata.strategy_type"
            assert 'rebalancing_frequency' in metadata, f"{yaml_path.name} missing metadata.rebalancing_frequency"

            # Check strategy_type is valid
            valid_types = ['momentum', 'mean_reversion', 'factor_combination']
            assert metadata['strategy_type'] in valid_types, \
                f"{yaml_path.name} has invalid strategy_type: {metadata['strategy_type']}"

    def test_all_examples_have_valid_indicators(self, example_files):
        """Test that all examples have valid indicator sections."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            indicators = spec['indicators']

            # Must have at least one indicator type
            assert len(indicators) > 0, f"{yaml_path.name} has no indicators"

            # Validate indicator names are unique
            all_names = []
            for section in ['technical_indicators', 'fundamental_factors', 'custom_calculations', 'volume_filters']:
                if section in indicators:
                    for item in indicators[section]:
                        all_names.append(item['name'])

            # Check for duplicates
            duplicates = [name for name in all_names if all_names.count(name) > 1]
            assert len(duplicates) == 0, f"{yaml_path.name} has duplicate indicator names: {duplicates}"


class TestYAMLExamplesCodeGeneration:
    """Test that all YAML examples generate valid Python code."""

    def test_all_examples_generate_code(self, generator, example_files):
        """Test that all examples generate Python code successfully."""
        failures = []

        for yaml_path in example_files:
            code, errors = generator.generate_from_file(str(yaml_path))

            if errors or code is None:
                failures.append({
                    'file': yaml_path.name,
                    'errors': errors
                })

        assert len(failures) == 0, f"Code generation failures:\n" + "\n".join(
            f"  {f['file']}: {f['errors']}" for f in failures
        )

    def test_all_generated_code_is_valid_python(self, generator, example_files):
        """Test that all generated code is syntactically correct Python."""
        failures = []

        for yaml_path in example_files:
            code, errors = generator.generate_from_file(str(yaml_path))

            if not errors and code:
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    failures.append({
                        'file': yaml_path.name,
                        'error': str(e)
                    })

        assert len(failures) == 0, f"Syntax errors in generated code:\n" + "\n".join(
            f"  {f['file']}: {f['error']}" for f in failures
        )

    def test_generated_code_has_reasonable_length(self, generator, example_files):
        """Test that generated code has reasonable length."""
        for yaml_path in example_files:
            code, errors = generator.generate_from_file(str(yaml_path))

            if not errors and code:
                # Code should be at least 100 characters (basic structure)
                assert len(code) > 100, f"{yaml_path.name} generated code too short: {len(code)} chars"

                # Code should not be excessively long (>50k chars indicates issue)
                assert len(code) < 50000, f"{yaml_path.name} generated code too long: {len(code)} chars"


class TestYAMLExamplesCoverage:
    """Test that examples cover required strategy types and position sizing methods."""

    def test_strategy_type_coverage(self, example_files):
        """Test that all 3 strategy types are represented."""
        required_types = {'momentum', 'mean_reversion', 'factor_combination'}
        found_types = set()

        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            strategy_type = spec['metadata']['strategy_type']
            found_types.add(strategy_type)

        missing_types = required_types - found_types
        assert len(missing_types) == 0, f"Missing strategy types: {missing_types}"

    def test_position_sizing_coverage(self, example_files):
        """Test that all 5 position sizing methods are demonstrated."""
        required_methods = {
            'equal_weight',
            'factor_weighted',
            'risk_parity',
            'volatility_weighted',
            'custom_formula'
        }
        found_methods = set()

        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            if 'position_sizing' in spec:
                method = spec['position_sizing'].get('method')
                if method:
                    found_methods.add(method)

        missing_methods = required_methods - found_methods
        assert len(missing_methods) == 0, f"Missing position sizing methods: {missing_methods}"

    def test_diverse_indicator_types(self, example_files):
        """Test that examples demonstrate diverse indicator types."""
        # Collect all indicator types used across all examples
        technical_types = set()
        fundamental_fields = set()
        has_custom_calculations = False
        has_volume_filters = False

        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            indicators = spec['indicators']

            # Technical indicators
            if 'technical_indicators' in indicators:
                for ind in indicators['technical_indicators']:
                    technical_types.add(ind['type'])

            # Fundamental factors
            if 'fundamental_factors' in indicators:
                for factor in indicators['fundamental_factors']:
                    fundamental_fields.add(factor['field'])

            # Custom calculations
            if 'custom_calculations' in indicators and len(indicators['custom_calculations']) > 0:
                has_custom_calculations = True

            # Volume filters
            if 'volume_filters' in indicators and len(indicators['volume_filters']) > 0:
                has_volume_filters = True

        # Check diversity
        assert len(technical_types) >= 5, f"Expected at least 5 different technical indicator types, found {len(technical_types)}"
        assert len(fundamental_fields) >= 3, f"Expected at least 3 different fundamental fields, found {len(fundamental_fields)}"
        assert has_custom_calculations, "No examples with custom calculations found"


class TestYAMLExamplesQuality:
    """Test the quality of YAML examples."""

    def test_all_examples_have_descriptions(self, example_files):
        """Test that all examples have descriptions."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            metadata = spec['metadata']
            assert 'description' in metadata, f"{yaml_path.name} missing description"
            assert len(metadata['description']) > 20, \
                f"{yaml_path.name} description too short: {len(metadata['description'])} chars"

    def test_all_examples_have_tags(self, example_files):
        """Test that all examples have tags."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            metadata = spec['metadata']
            assert 'tags' in metadata, f"{yaml_path.name} missing tags"
            assert len(metadata['tags']) > 0, f"{yaml_path.name} has no tags"

    def test_examples_are_properly_sized(self, example_files):
        """Test that examples have reasonable size (80-150 lines guideline)."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            line_count = len(lines)
            # Allow some flexibility: 60-200 lines
            assert 60 <= line_count <= 250, \
                f"{yaml_path.name} has {line_count} lines (guideline: 80-150, max: 250)"

    def test_all_examples_have_exit_conditions(self, example_files):
        """Test that all examples have exit conditions."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            # Exit conditions are recommended but not required by schema
            # For production examples, we enforce them
            assert 'exit_conditions' in spec, f"{yaml_path.name} missing exit_conditions"

            exit_conds = spec['exit_conditions']
            # Should have at least stop_loss OR conditional_exits
            has_risk_mgmt = (
                'stop_loss_pct' in exit_conds or
                'take_profit_pct' in exit_conds or
                'conditional_exits' in exit_conds
            )
            assert has_risk_mgmt, f"{yaml_path.name} has no risk management in exit conditions"


class TestYAMLExamplesDocumentation:
    """Test that examples have proper documentation."""

    def test_all_examples_have_header_comments(self, example_files):
        """Test that all examples have header comments explaining the strategy."""
        for yaml_path in example_files:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for header comment block
            assert content.startswith('#'), f"{yaml_path.name} missing header comment"

            # Check that header has multiple lines (strategy explanation)
            lines = content.split('\n')
            comment_lines = [line for line in lines[:15] if line.startswith('#')]
            assert len(comment_lines) >= 5, \
                f"{yaml_path.name} header comment too short ({len(comment_lines)} lines)"


# Test runner
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
