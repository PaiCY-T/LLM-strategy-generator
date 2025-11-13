#!/usr/bin/env python3
"""
Test script for diversity analysis (Task 3.2)
Tests all major functionality of scripts/analyze_diversity.py
"""

import json
import sys
from pathlib import Path
import subprocess

def test_basic_execution():
    """Test basic script execution without duplicate report"""
    print("Test 1: Basic execution without duplicate report...")

    result = subprocess.run([
        'python3', 'scripts/analyze_diversity.py',
        '--validation-results', 'phase2_validated_results_20251101_060315.json',
        '--output', 'test_diversity_basic.md'
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Script failed with exit code {result.returncode}"

    # Check output files exist
    assert Path('test_diversity_basic.md').exists(), "Markdown report not created"
    assert Path('test_diversity_basic.json').exists(), "JSON report not created"
    assert Path('test_diversity_basic_correlation_heatmap.png').exists(), "Heatmap not created"
    assert Path('test_diversity_basic_factor_usage.png').exists(), "Factor usage chart not created"

    # Load and validate JSON report
    with open('test_diversity_basic.json', 'r') as f:
        report = json.load(f)

    assert 'total_strategies' in report, "Missing total_strategies field"
    assert 'diversity_score' in report, "Missing diversity_score field"
    assert 'recommendation' in report, "Missing recommendation field"
    assert 'metrics' in report, "Missing metrics field"
    assert 'factors' in report, "Missing factors field"

    # Validate metrics
    assert 0 <= report['diversity_score'] <= 100, "Diversity score out of range"
    assert report['recommendation'] in ['SUFFICIENT', 'MARGINAL', 'INSUFFICIENT'], "Invalid recommendation"

    print("✓ Test 1 passed")
    return True


def test_with_duplicate_report():
    """Test execution with duplicate report"""
    print("Test 2: Execution with duplicate report...")

    result = subprocess.run([
        'python3', 'scripts/analyze_diversity.py',
        '--validation-results', 'phase2_validated_results_20251101_060315.json',
        '--duplicate-report', 'duplicate_report.json',
        '--output', 'test_diversity_duplicates.md'
    ], capture_output=True, text=True)

    assert result.returncode == 0, f"Script failed with exit code {result.returncode}"

    # Check output files exist
    assert Path('test_diversity_duplicates.md').exists(), "Markdown report not created"
    assert Path('test_diversity_duplicates.json').exists(), "JSON report not created"

    print("✓ Test 2 passed")
    return True


def test_error_handling():
    """Test error handling for missing files"""
    print("Test 3: Error handling for missing validation file...")

    result = subprocess.run([
        'python3', 'scripts/analyze_diversity.py',
        '--validation-results', 'nonexistent_file.json',
        '--output', 'test_diversity_error.md'
    ], capture_output=True, text=True)

    assert result.returncode == 1, "Script should fail with exit code 1"
    assert "File not found" in result.stderr or "not found" in result.stderr, "Expected error message not found"

    print("✓ Test 3 passed")
    return True


def test_help_output():
    """Test help output"""
    print("Test 4: Help output...")

    result = subprocess.run([
        'python3', 'scripts/analyze_diversity.py',
        '--help'
    ], capture_output=True, text=True)

    assert result.returncode == 0, "Help should succeed"
    assert '--validation-results' in result.stdout, "Missing validation-results option"
    assert '--duplicate-report' in result.stdout, "Missing duplicate-report option"
    assert '--output' in result.stdout, "Missing output option"

    print("✓ Test 4 passed")
    return True


def test_report_contents():
    """Test report contents match specification"""
    print("Test 5: Validate report contents...")

    # Load JSON report
    with open('test_diversity_basic.json', 'r') as f:
        report = json.load(f)

    # Check required fields per specification
    assert 'total_strategies' in report
    assert 'excluded_strategies' in report
    assert 'metrics' in report
    assert 'diversity_score' in report
    assert 'recommendation' in report
    assert 'warnings' in report
    assert 'factors' in report

    # Check metrics structure
    metrics = report['metrics']
    assert 'factor_diversity' in metrics
    assert 'avg_correlation' in metrics
    assert 'risk_diversity' in metrics

    # Check factors structure
    factors = report['factors']
    assert 'unique_count' in factors
    assert 'avg_per_strategy' in factors
    assert 'usage_distribution' in factors

    # Load Markdown report
    with open('test_diversity_basic.md', 'r') as f:
        md_content = f.read()

    # Check required sections in Markdown
    assert '# Strategy Diversity Analysis Report' in md_content
    assert '## Summary' in md_content
    assert '## Key Metrics' in md_content
    assert '## Factor Analysis' in md_content
    assert '## Correlation Analysis' in md_content
    assert '## Risk Analysis' in md_content
    assert '## Recommendations' in md_content
    assert '## Visualizations' in md_content

    print("✓ Test 5 passed")
    return True


def cleanup():
    """Clean up test files"""
    print("\nCleaning up test files...")
    test_files = [
        'test_diversity_basic.md',
        'test_diversity_basic.json',
        'test_diversity_basic_correlation_heatmap.png',
        'test_diversity_basic_factor_usage.png',
        'test_diversity_duplicates.md',
        'test_diversity_duplicates.json',
        'test_diversity_duplicates_correlation_heatmap.png',
        'test_diversity_duplicates_factor_usage.png',
        'test_diversity_error.md',
        'test_diversity_error.json'
    ]

    for file in test_files:
        path = Path(file)
        if path.exists():
            path.unlink()

    print("✓ Cleanup complete")


def main():
    """Run all tests"""
    print("="*60)
    print("Testing scripts/analyze_diversity.py (Task 3.2)")
    print("="*60)
    print()

    tests = [
        test_basic_execution,
        test_with_duplicate_report,
        test_error_handling,
        test_help_output,
        test_report_contents
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
        print()

    # Cleanup
    cleanup()

    # Summary
    print("="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)

    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
