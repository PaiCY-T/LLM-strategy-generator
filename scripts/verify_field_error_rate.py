#!/usr/bin/env python3
"""
Field Error Rate Verification Script

This script analyzes test results to verify that the field_error_rate = 0%
after implementing Layer 1 (DataFieldManifest), Layer 2 (FieldValidator),
and Layer 3 (Config-based architecture).

The script:
1. Loads DataFieldManifest for field validation
2. Reads innovations.jsonl from test results directories
3. Extracts field references from generated strategies using AST parsing
4. Validates each field using manifest.validate_field()
5. Calculates field_error_rate = (invalid_fields / total_fields) * 100
6. Reports results by mode (Factor Graph, LLM Only, Hybrid)

Expected Result: field_error_rate = 0.0% for all modes
"""

import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Import DataFieldManifest from Layer 1
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.data_fields import DataFieldManifest


class FieldExtractor(ast.NodeVisitor):
    """
    AST-based field extractor for strategy code.

    Extracts data.get() calls to identify all field references.
    """

    def __init__(self):
        self.fields: Set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function calls to find data.get() calls."""
        # Check if this is a data.get() call
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'get' and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'data'):

            # Extract the field name from the first argument
            if node.args and isinstance(node.args[0], ast.Constant):
                field_name = node.args[0].value
                if isinstance(field_name, str):
                    self.fields.add(field_name)

        # Continue visiting child nodes
        self.generic_visit(node)


def extract_fields_from_code(strategy_code: str) -> Set[str]:
    """
    Extract all field references from strategy code using AST parsing.

    Args:
        strategy_code: Python strategy code as string

    Returns:
        Set of field names referenced in the code
    """
    if not strategy_code:
        return set()

    try:
        # Parse the code into an AST
        tree = ast.parse(strategy_code)

        # Extract fields using visitor pattern
        extractor = FieldExtractor()
        extractor.visit(tree)

        return extractor.fields
    except SyntaxError:
        # If code has syntax errors, return empty set
        return set()


def analyze_innovations_file(
    file_path: Path,
    manifest: DataFieldManifest
) -> Tuple[int, int, List[str]]:
    """
    Analyze a single innovations.jsonl file for field errors.

    Args:
        file_path: Path to innovations.jsonl file
        manifest: DataFieldManifest instance for validation

    Returns:
        Tuple of (total_fields, invalid_fields, invalid_field_list)
    """
    total_fields = 0
    invalid_fields = 0
    invalid_field_list = []

    if not file_path.exists():
        return 0, 0, []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue

                try:
                    record = json.loads(line)
                    strategy_code = record.get('strategy_code')

                    if not strategy_code:
                        # Factor Graph mode - no LLM-generated code
                        continue

                    # Extract fields from code
                    fields = extract_fields_from_code(strategy_code)

                    # Validate each field
                    for field in fields:
                        total_fields += 1

                        # Validate using DataFieldManifest
                        is_valid = manifest.validate_field(field)

                        if not is_valid:
                            invalid_fields += 1
                            if field not in invalid_field_list:
                                invalid_field_list.append(field)

                except json.JSONDecodeError:
                    continue

    except FileNotFoundError:
        return 0, 0, []

    return total_fields, invalid_fields, invalid_field_list


def verify_field_error_rate() -> None:
    """
    Main verification function.

    Analyzes all test results and reports field error rates.
    """
    print("=" * 80)
    print("FIELD ERROR RATE VERIFICATION")
    print("=" * 80)
    print()

    # Initialize DataFieldManifest
    cache_path = Path(__file__).parent.parent / 'tests' / 'fixtures' / 'finlab_fields.json'

    if not cache_path.exists():
        print(f"ERROR: Field cache not found at {cache_path}")
        print("Please run: python scripts/discover_finlab_fields.py")
        return

    manifest = DataFieldManifest(str(cache_path))
    print(f"Loaded DataFieldManifest: {manifest}")
    print()

    # Define test directories to analyze
    results_base = Path(__file__).parent.parent / 'experiments' / 'llm_learning_validation' / 'results'

    test_directories = {
        'Factor Graph (50 iter)': results_base / 'fg_only_50',
        'LLM Only (50 iter)': results_base / 'llm_only_50',
        'Hybrid (50 iter)': results_base / 'hybrid_50',
        'Factor Graph (20 iter)': results_base / 'fg_only_20',
        'LLM Only (20 iter)': results_base / 'llm_only_20',
        'Hybrid (20 iter)': results_base / 'hybrid_20',
    }

    # Results storage
    results = {}
    overall_total = 0
    overall_invalid = 0
    all_invalid_fields = set()

    print("Analyzing test results...")
    print()

    for mode_name, test_dir in test_directories.items():
        innovations_file = test_dir / 'innovations.jsonl'

        if not innovations_file.exists():
            print(f"  {mode_name}: SKIP (no data)")
            results[mode_name] = None
            continue

        # Analyze file
        total, invalid, invalid_list = analyze_innovations_file(innovations_file, manifest)

        # Calculate error rate
        if total > 0:
            error_rate = (invalid / total) * 100
        else:
            error_rate = 0.0

        # Store results
        results[mode_name] = {
            'total_fields': total,
            'invalid_fields': invalid,
            'error_rate': error_rate,
            'invalid_field_list': invalid_list
        }

        # Update overall totals
        overall_total += total
        overall_invalid += invalid
        all_invalid_fields.update(invalid_list)

        # Print mode results
        status = "PASS" if error_rate == 0.0 else "FAIL"
        if total > 0:
            print(f"  {mode_name}:")
            print(f"    Total fields: {total}")
            print(f"    Invalid fields: {invalid}")
            print(f"    Error rate: {error_rate:.2f}%")
            print(f"    Status: {status}")
            if invalid_list:
                print(f"    Invalid: {', '.join(invalid_list)}")
            print()
        else:
            print(f"  {mode_name}: SKIP (no fields)")
            print()

    # Print overall summary
    print("=" * 80)
    print("OVERALL VERIFICATION SUMMARY")
    print("=" * 80)
    print()

    if overall_total > 0:
        overall_error_rate = (overall_invalid / overall_total) * 100

        print(f"Total fields analyzed: {overall_total}")
        print(f"Invalid fields found: {overall_invalid}")
        print(f"Overall error rate: {overall_error_rate:.2f}%")
        print()

        if overall_invalid > 0:
            print("VERIFICATION FAILED")
            print()
            print("Invalid fields found:")
            for field in sorted(all_invalid_fields):
                # Get suggestion if available
                is_valid, suggestion = manifest.validate_field_with_suggestion(field)
                if suggestion:
                    print(f"  - {field} ({suggestion})")
                else:
                    print(f"  - {field}")
            print()
            print("Layer 1 (DataFieldManifest) implementation needs review.")
        else:
            print("VERIFICATION PASSED")
            print()
            print("All fields validated successfully!")
            print("Field error rate = 0.0%")
            print()
            print("Layer 1 (DataFieldManifest) working as expected.")
    else:
        print("WARNING: No fields found to analyze")
        print()
        print("Possible reasons:")
        print("- Test results not available")
        print("- Factor Graph mode only (no LLM-generated code)")
        print("- Need to run tests first")

    print()
    print("=" * 80)


if __name__ == '__main__':
    verify_field_error_rate()
