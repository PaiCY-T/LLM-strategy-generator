#!/usr/bin/env python3
"""
Validation Script for YAML Strategy Examples Library
====================================================

This script validates all YAML strategy examples in the library:
1. Loads each YAML file
2. Validates against JSON Schema
3. Generates Python code
4. Validates generated code syntax with AST

Usage:
    python validate_all.py

Output:
    - Summary of validation results
    - Detailed error messages for failures
    - Statistics on coverage of strategy types and position sizing methods

Requirements:
    - src.generators.yaml_schema_validator
    - src.generators.yaml_to_code_generator
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
import yaml

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.generators.yaml_schema_validator import YAMLSchemaValidator
from src.generators.yaml_to_code_generator import YAMLToCodeGenerator


class YAMLExampleValidator:
    """Validator for YAML strategy examples library."""

    def __init__(self, examples_dir: str):
        """
        Initialize validator.

        Args:
            examples_dir: Directory containing YAML strategy examples
        """
        self.examples_dir = Path(examples_dir)
        self.validator = YAMLSchemaValidator()
        self.generator = YAMLToCodeGenerator(self.validator)
        self.results: List[Dict[str, Any]] = []

    def find_yaml_files(self) -> List[Path]:
        """
        Find all YAML files in examples directory.

        Returns:
            List of Path objects for YAML files
        """
        yaml_files = []
        for pattern in ['*.yaml', '*.yml']:
            yaml_files.extend(self.examples_dir.glob(pattern))

        # Filter out test files (keep only production examples)
        production_files = [
            f for f in yaml_files
            if not f.name.startswith('test_')
        ]

        return sorted(production_files)

    def validate_file(self, yaml_path: Path) -> Dict[str, Any]:
        """
        Validate a single YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Dictionary with validation results:
                - file: filename
                - valid: boolean
                - errors: list of error messages
                - strategy_type: strategy type if valid
                - position_sizing: position sizing method if valid
                - code_length: length of generated code if valid
        """
        result = {
            'file': yaml_path.name,
            'valid': False,
            'errors': [],
            'strategy_type': None,
            'position_sizing': None,
            'code_length': 0
        }

        try:
            # Load YAML file
            with open(yaml_path, 'r', encoding='utf-8') as f:
                spec = yaml.safe_load(f)

            # Extract metadata
            if spec and isinstance(spec, dict):
                metadata = spec.get('metadata', {})
                result['strategy_type'] = metadata.get('strategy_type')

                position_sizing = spec.get('position_sizing', {})
                result['position_sizing'] = position_sizing.get('method')

            # Generate code (includes validation)
            code, errors = self.generator.generate_from_file(str(yaml_path))

            if errors:
                result['errors'] = errors
                result['valid'] = False
            else:
                result['valid'] = True
                result['code_length'] = len(code) if code else 0

        except Exception as e:
            result['errors'] = [f"Unexpected error: {str(e)}"]
            result['valid'] = False

        return result

    def validate_all(self) -> None:
        """Validate all YAML files in the examples directory."""
        yaml_files = self.find_yaml_files()

        if not yaml_files:
            print(f"⚠️  No YAML files found in {self.examples_dir}")
            return

        print(f"Found {len(yaml_files)} YAML strategy examples")
        print("=" * 70)
        print()

        for yaml_path in yaml_files:
            print(f"Validating: {yaml_path.name}...")
            result = self.validate_file(yaml_path)
            self.results.append(result)

            if result['valid']:
                print(f"  ✓ Valid - Type: {result['strategy_type']}, "
                      f"Sizing: {result['position_sizing']}, "
                      f"Code: {result['code_length']} chars")
            else:
                print(f"  ✗ Invalid")
                for error in result['errors']:
                    print(f"    - {error}")

            print()

    def print_summary(self) -> None:
        """Print validation summary and statistics."""
        total = len(self.results)
        valid = sum(1 for r in self.results if r['valid'])
        invalid = total - valid

        print("=" * 70)
        print("VALIDATION SUMMARY")
        print("=" * 70)
        print(f"Total files:     {total}")
        print(f"Valid:           {valid} ({valid/total*100:.1f}%)")
        print(f"Invalid:         {invalid} ({invalid/total*100:.1f}%)")
        print()

        # Strategy type coverage
        strategy_types = {}
        for r in self.results:
            if r['valid'] and r['strategy_type']:
                strategy_types[r['strategy_type']] = strategy_types.get(r['strategy_type'], 0) + 1

        print("Strategy Type Coverage:")
        print("-" * 70)
        for stype, count in sorted(strategy_types.items()):
            print(f"  {stype:20s}: {count} strategies")
        print()

        # Position sizing coverage
        position_sizing = {}
        for r in self.results:
            if r['valid'] and r['position_sizing']:
                position_sizing[r['position_sizing']] = position_sizing.get(r['position_sizing'], 0) + 1

        print("Position Sizing Coverage:")
        print("-" * 70)
        for method, count in sorted(position_sizing.items()):
            print(f"  {method:20s}: {count} strategies")
        print()

        # Invalid files details
        if invalid > 0:
            print("Invalid Files:")
            print("-" * 70)
            for r in self.results:
                if not r['valid']:
                    print(f"  {r['file']}")
                    for error in r['errors']:
                        print(f"    - {error}")
            print()

        # Success criteria check
        print("Success Criteria:")
        print("-" * 70)
        print(f"  Total examples ≥ 10:              {'✓' if total >= 10 else '✗'} ({total})")
        print(f"  All examples valid:               {'✓' if invalid == 0 else '✗'} ({valid}/{total})")
        print(f"  All 3 strategy types covered:     {'✓' if len(strategy_types) >= 3 else '✗'} ({len(strategy_types)}/3)")

        # Check for all 5 position sizing methods
        required_methods = {'equal_weight', 'factor_weighted', 'risk_parity', 'volatility_weighted', 'custom_formula'}
        covered_methods = set(position_sizing.keys())
        all_methods_covered = required_methods.issubset(covered_methods)
        print(f"  All 5 position sizing covered:    {'✓' if all_methods_covered else '✗'} ({len(covered_methods)}/5)")
        if not all_methods_covered:
            missing = required_methods - covered_methods
            print(f"    Missing: {', '.join(missing)}")

        print()

    def get_exit_code(self) -> int:
        """
        Get exit code based on validation results.

        Returns:
            0 if all validations passed, 1 otherwise
        """
        return 0 if all(r['valid'] for r in self.results) else 1


def main():
    """Main validation function."""
    # Determine examples directory
    script_dir = Path(__file__).parent
    examples_dir = script_dir

    print("YAML Strategy Examples Library Validator")
    print("=" * 70)
    print(f"Examples directory: {examples_dir}")
    print()

    # Run validation
    validator = YAMLExampleValidator(str(examples_dir))
    validator.validate_all()
    validator.print_summary()

    # Exit with appropriate code
    exit_code = validator.get_exit_code()
    if exit_code == 0:
        print("✓ All validations passed!")
    else:
        print("✗ Some validations failed. See details above.")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
