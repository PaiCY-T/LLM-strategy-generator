#!/usr/bin/env python3
"""
YAML to Code Generation Demo
=============================

Demonstrates the complete YAML → Python code generation pipeline.

This script shows:
1. Loading YAML strategy specification
2. Validating against schema
3. Generating Python code
4. Validating syntax correctness
5. Displaying generated code

Usage:
    python examples/yaml_to_code_demo.py

Requirements:
    - src.generators.yaml_to_code_generator
    - src.generators.yaml_schema_validator
    - Test YAML files in tests/generators/test_data/
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.generators.yaml_to_code_generator import YAMLToCodeGenerator
from src.generators.yaml_schema_validator import YAMLSchemaValidator
import ast


def demo_single_strategy(yaml_path: str, generator: YAMLToCodeGenerator) -> None:
    """Demonstrate code generation for a single strategy."""
    print(f"\n{'='*80}")
    print(f"Processing: {Path(yaml_path).name}")
    print(f"{'='*80}")

    # Generate code from YAML file
    code, errors = generator.generate_from_file(yaml_path)

    if errors:
        print("\n❌ Generation FAILED")
        print("\nErrors:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        return

    print("\n✅ Generation SUCCESSFUL")

    # Validate syntax
    try:
        ast.parse(code)
        print("✅ Syntax validation PASSED")
    except SyntaxError as e:
        print(f"❌ Syntax validation FAILED: {e}")
        return

    # Display generated code statistics
    lines = code.split('\n')
    print(f"\nGenerated Code Statistics:")
    print(f"  - Total lines: {len(lines)}")
    print(f"  - Function definitions: {code.count('def ')}")
    print(f"  - FinLab API calls: {code.count('data.get(')}")
    print(f"  - Comments: {len([l for l in lines if l.strip().startswith('#')])}")

    # Display code preview (first 50 lines)
    print(f"\nCode Preview (first 50 lines):")
    print("-" * 80)
    for i, line in enumerate(lines[:50], 1):
        print(f"{i:3d} | {line}")
    if len(lines) > 50:
        print(f"... ({len(lines) - 50} more lines)")
    print("-" * 80)


def demo_batch_generation(yaml_dir: Path, generator: YAMLToCodeGenerator) -> None:
    """Demonstrate batch generation for all YAML files."""
    yaml_files = list(yaml_dir.glob("*.yaml"))

    print(f"\n{'='*80}")
    print(f"Batch Generation: {len(yaml_files)} strategies")
    print(f"{'='*80}")

    results = generator.generate_batch_from_files([str(f) for f in yaml_files])

    # Calculate statistics
    stats = generator.get_generation_stats(results)

    print(f"\nBatch Generation Statistics:")
    print(f"  - Total strategies: {stats['total']}")
    print(f"  - Successful: {stats['successful']} ({stats['success_rate']:.1f}%)")
    print(f"  - Failed: {stats['failed']}")

    if stats['error_types']:
        print(f"\nError Types:")
        for error_type, count in stats['error_types'].items():
            print(f"  - {error_type}: {count}")

    # Display results
    print(f"\nIndividual Results:")
    for yaml_file, (code, errors) in zip(yaml_files, results):
        status = "✅ SUCCESS" if not errors else "❌ FAILED"
        print(f"  {status} - {yaml_file.name}")
        if errors:
            for error in errors[:2]:  # Show first 2 errors
                print(f"      └─ {error[:100]}")


def main():
    """Main demo function."""
    print("="*80)
    print("YAML to Code Generation Demo")
    print("="*80)

    # Initialize generator
    print("\nInitializing YAMLToCodeGenerator...")
    validator = YAMLSchemaValidator()
    generator = YAMLToCodeGenerator(validator)
    print("✅ Generator initialized")

    # Get test data directory
    test_data_dir = project_root / "tests" / "generators" / "test_data"

    if not test_data_dir.exists():
        print(f"\n❌ Test data directory not found: {test_data_dir}")
        print("Please run the tests first to create test YAML files.")
        return

    # Demo 1: Single strategy generation (momentum)
    momentum_yaml = test_data_dir / "momentum_strategy.yaml"
    if momentum_yaml.exists():
        demo_single_strategy(str(momentum_yaml), generator)

    # Demo 2: Single strategy generation (factor combination)
    factor_yaml = test_data_dir / "factor_combination_strategy.yaml"
    if factor_yaml.exists():
        demo_single_strategy(str(factor_yaml), generator)

    # Demo 3: Batch generation
    demo_batch_generation(test_data_dir, generator)

    print(f"\n{'='*80}")
    print("Demo Complete!")
    print(f"{'='*80}")


if __name__ == '__main__':
    main()
