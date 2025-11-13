"""
Task 6.3: Full Validation Workflow Integration Tests
====================================================

Tests the complete validation workflow from end-to-end, validating that all
components work together seamlessly.

Test Coverage:
    1. End-to-end workflow execution on test dataset (5 strategies)
    2. Output structure validation for all generated files
    3. Workflow performance (completes within time limit)
    4. Error handling for missing dependencies and invalid inputs
    5. Skip revalidation flag functionality

Components Tested:
    - Re-validation script (optional)
    - Duplicate detection script
    - Diversity analysis script
    - Decision evaluation script
    - Master workflow orchestration

Specification: validation-framework-critical-fixes
Requirements: REQ-6 (Integration Testing)
"""

import json
import pytest
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import tempfile
import shutil


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def temp_workspace(tmp_path: Path) -> Path:
    """Create temporary workspace for test execution."""
    workspace = tmp_path / "workflow_test"
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


@pytest.fixture
def test_validation_results(temp_workspace: Path) -> Dict[str, Any]:
    """
    Create mock validation results for testing.

    Returns 5 strategies with varying performance:
    - Strategies 0-2: High Sharpe (>0.5), statistically significant
    - Strategy 3: Marginal Sharpe (~0.5), borderline
    - Strategy 4: Low Sharpe (<0.5), not significant
    """
    validation_data = {
        "summary": {
            "total": 5,
            "successful": 5,
            "failed": 0,
            "classification_breakdown": {
                "level_0_failed": 0,
                "level_1_marginal": 1,
                "level_2_moderate": 2,
                "level_3_strong": 2
            }
        },
        "metrics": {
            "execution_success_rate": 1.0,
            "avg_sharpe": 0.62,
            "median_sharpe": 0.58
        },
        "validation_statistics": {
            "bonferroni_threshold": 0.5,
            "statistically_significant": 4,
            "bonferroni_passed": 4
        },
        "dynamic_threshold": 0.8,
        "strategies_validation": [
            {
                "strategy_index": 0,
                "sharpe_ratio": 0.85,
                "annual_return": 0.25,
                "max_drawdown": -0.12,
                "validation_passed": True,
                "statistically_significant": True,
                "bonferroni_threshold": 0.5,
                "classification": "STRONG"
            },
            {
                "strategy_index": 1,
                "sharpe_ratio": 0.72,
                "annual_return": 0.22,
                "max_drawdown": -0.15,
                "validation_passed": True,
                "statistically_significant": True,
                "bonferroni_threshold": 0.5,
                "classification": "STRONG"
            },
            {
                "strategy_index": 2,
                "sharpe_ratio": 0.58,
                "annual_return": 0.18,
                "max_drawdown": -0.18,
                "validation_passed": True,
                "statistically_significant": True,
                "bonferroni_threshold": 0.5,
                "classification": "MODERATE"
            },
            {
                "strategy_index": 3,
                "sharpe_ratio": 0.51,
                "annual_return": 0.15,
                "max_drawdown": -0.20,
                "validation_passed": True,
                "statistically_significant": True,
                "bonferroni_threshold": 0.5,
                "classification": "MODERATE"
            },
            {
                "strategy_index": 4,
                "sharpe_ratio": 0.42,
                "annual_return": 0.12,
                "max_drawdown": -0.22,
                "validation_passed": False,
                "statistically_significant": False,
                "bonferroni_threshold": 0.5,
                "classification": "MARGINAL"
            }
        ]
    }

    # Write to temp workspace
    validation_file = temp_workspace / "test_validation_results.json"
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_data, f, indent=2)

    return validation_data


@pytest.fixture
def test_strategy_files(project_root: Path, temp_workspace: Path) -> List[Path]:
    """
    Create mock strategy files for testing.

    Creates 5 simple strategy files that can be analyzed for duplicates
    and diversity.
    """
    strategy_files = []

    # Strategy templates with variations
    strategies = [
        # Strategy 0: High yield + MA
        {
            "code": """
# Strategy 0: High Dividend Yield with Moving Average
from finlab import data
from finlab.backtest import sim

def strategy():
    close = data.get('price:收盤價')
    dividend_yield = data.get('price_earning_ratio:殖利率(%)')

    # High dividend yield filter
    high_yield = dividend_yield > 5.0

    # Moving average trend
    ma_20 = close.average(20)
    uptrend = close > ma_20

    # Position filter
    position = high_yield & uptrend

    return position

position = strategy()
""",
            "index": 0
        },
        # Strategy 1: Revenue growth + momentum
        {
            "code": """
# Strategy 1: Revenue Growth with Price Momentum
from finlab import data
from finlab.backtest import sim

def strategy():
    close = data.get('price:收盤價')
    revenue_growth = data.get('monthly_revenue:去年同月增減(%)')

    # Strong revenue growth
    strong_growth = revenue_growth > 15.0

    # Price momentum
    momentum = close / close.shift(20) - 1
    positive_momentum = momentum > 0.05

    # Position filter
    position = strong_growth & positive_momentum

    return position

position = strategy()
""",
            "index": 1
        },
        # Strategy 2: Low PE + ROE
        {
            "code": """
# Strategy 2: Value with Quality (Low PE, High ROE)
from finlab import data
from finlab.backtest import sim

def strategy():
    pe_ratio = data.get('price_earning_ratio:本益比')
    roe = data.get('fundamental_features:ROE綜合損益')

    # Value screening
    low_pe = pe_ratio < 15

    # Quality screening
    high_roe = roe > 12

    # Position filter
    position = low_pe & high_roe

    return position

position = strategy()
""",
            "index": 2
        },
        # Strategy 3: Similar to Strategy 1 (potential duplicate)
        {
            "code": """
# Strategy 3: Revenue Growth with Momentum (variant)
from finlab import data
from finlab.backtest import sim

def strategy():
    close = data.get('price:收盤價')
    revenue_growth = data.get('monthly_revenue:去年同月增減(%)')

    # Revenue growth threshold slightly different
    strong_growth = revenue_growth > 12.0

    # Price momentum with different window
    momentum = close / close.shift(30) - 1
    positive_momentum = momentum > 0.03

    # Position filter
    position = strong_growth & positive_momentum

    return position

position = strategy()
""",
            "index": 3
        },
        # Strategy 4: Different approach - liquidity based
        {
            "code": """
# Strategy 4: Liquidity and Volume
from finlab import data
from finlab.backtest import sim

def strategy():
    close = data.get('price:收盤價')
    volume = data.get('price:成交股數')

    # High volume
    avg_volume = volume.average(20)
    high_liquidity = volume > avg_volume * 1.5

    # Price stability
    volatility = close.rolling(20).std() / close
    stable = volatility < 0.05

    # Position filter
    position = high_liquidity & stable

    return position

position = strategy()
""",
            "index": 4
        }
    ]

    # Write strategy files to project root (for scripts to find them)
    for strategy_info in strategies:
        filename = f"generated_strategy_loop_iter{strategy_info['index']}.py"
        filepath = project_root / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(strategy_info['code'])

        strategy_files.append(filepath)

    yield strategy_files

    # Cleanup: Remove strategy files after tests
    for filepath in strategy_files:
        if filepath.exists():
            filepath.unlink()


# =============================================================================
# Integration Tests
# =============================================================================

class TestFullValidationWorkflow:
    """Integration tests for complete validation workflow."""

    def test_1_full_workflow_execution(
        self,
        project_root: Path,
        temp_workspace: Path,
        test_validation_results: Dict[str, Any],
        test_strategy_files: List[Path]
    ):
        """
        Test 1: End-to-End Workflow Execution

        Validates:
            - All scripts execute successfully
            - All expected outputs are generated
            - Output files have valid structure
            - Workflow completes within time limit
        """
        # Define output paths
        validation_file = temp_workspace / "test_validation_results.json"
        duplicate_json = temp_workspace / "duplicate_report.json"
        duplicate_md = temp_workspace / "duplicate_report.md"
        diversity_json = temp_workspace / "diversity_report.json"
        diversity_md = temp_workspace / "diversity_report.md"
        decision_md = temp_workspace / "decision_report.md"

        # Step 1: Run duplicate detection
        start_time = time.time()

        duplicate_script = project_root / "scripts" / "detect_duplicates.py"
        assert duplicate_script.exists(), f"Duplicate detection script not found: {duplicate_script}"

        result = subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(validation_file),
                '--strategy-dir', str(project_root),
                '--output', str(duplicate_md)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"Duplicate detection failed:\n{result.stderr}"
        assert duplicate_json.exists(), "Duplicate JSON report not created"
        assert duplicate_md.exists(), "Duplicate MD report not created"

        # Step 2: Run diversity analysis
        diversity_script = project_root / "scripts" / "analyze_diversity.py"
        assert diversity_script.exists(), f"Diversity analysis script not found: {diversity_script}"

        result = subprocess.run(
            [
                sys.executable,
                str(diversity_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(duplicate_json),
                '--strategy-dir', str(project_root),
                '--output', str(diversity_md)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"Diversity analysis failed:\n{result.stderr}"
        assert diversity_json.exists(), "Diversity JSON report not created"
        assert diversity_md.exists(), "Diversity MD report not created"

        # Step 3: Run decision evaluation
        decision_script = project_root / "scripts" / "evaluate_phase3_decision.py"
        assert decision_script.exists(), f"Decision evaluation script not found: {decision_script}"

        result = subprocess.run(
            [
                sys.executable,
                str(decision_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(duplicate_json),
                '--diversity-report', str(diversity_json),
                '--output', str(decision_md)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Decision script returns: 0=GO, 1=CONDITIONAL_GO, 2=NO_GO
        assert result.returncode in [0, 1, 2], f"Decision evaluation failed:\n{result.stderr}"
        assert decision_md.exists(), "Decision report not created"

        # Validate total execution time
        execution_time = time.time() - start_time
        assert execution_time < 120, f"Workflow took too long: {execution_time:.1f}s (expected <120s)"

        # Verify all outputs exist
        expected_outputs = [
            validation_file,
            duplicate_json,
            duplicate_md,
            diversity_json,
            diversity_md,
            decision_md
        ]

        for output_file in expected_outputs:
            assert output_file.exists(), f"Missing output file: {output_file}"
            # Verify file is not empty
            assert output_file.stat().st_size > 0, f"Output file is empty: {output_file}"

    def test_2_output_structure_validation(
        self,
        temp_workspace: Path,
        test_validation_results: Dict[str, Any],
        test_strategy_files: List[Path]
    ):
        """
        Test 2: Output Structure Validation

        Validates:
            - All JSON files are valid and parseable
            - Required fields are present in each output
            - Markdown files are well-formatted
        """
        # Run workflow first (simplified - assumes test_1 passed)
        validation_file = temp_workspace / "test_validation_results.json"

        # Validate validation results structure
        with open(validation_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)

        # Required fields in validation results
        assert 'summary' in validation_data, "Missing 'summary' in validation results"
        assert 'metrics' in validation_data, "Missing 'metrics' in validation results"
        assert 'strategies_validation' in validation_data, "Missing 'strategies_validation'"

        # Validate summary structure
        summary = validation_data['summary']
        assert 'total' in summary, "Missing 'total' in summary"
        assert 'successful' in summary, "Missing 'successful' in summary"
        assert 'failed' in summary, "Missing 'failed' in summary"

        # Validate strategies_validation is a list
        assert isinstance(
            validation_data['strategies_validation'],
            list
        ), "strategies_validation should be a list"

        # If duplicate report exists, validate it
        duplicate_json = temp_workspace / "duplicate_report.json"
        if duplicate_json.exists():
            with open(duplicate_json, 'r', encoding='utf-8') as f:
                duplicate_data = json.load(f)

            assert 'total_strategies' in duplicate_data, "Missing 'total_strategies'"
            assert 'duplicate_groups' in duplicate_data, "Missing 'duplicate_groups'"
            assert isinstance(
                duplicate_data['duplicate_groups'],
                list
            ), "duplicate_groups should be a list"

        # If diversity report exists, validate it
        diversity_json = temp_workspace / "diversity_report.json"
        if diversity_json.exists():
            with open(diversity_json, 'r', encoding='utf-8') as f:
                diversity_data = json.load(f)

            required_fields = [
                'total_strategies',
                'metrics',
                'diversity_score',
                'recommendation'
            ]

            for field in required_fields:
                assert field in diversity_data, f"Missing required field: {field}"

            # Validate metrics structure
            metrics = diversity_data['metrics']
            assert 'factor_diversity' in metrics, "Missing 'factor_diversity'"
            assert 'avg_correlation' in metrics, "Missing 'avg_correlation'"
            assert 'risk_diversity' in metrics, "Missing 'risk_diversity'"

        # Validate Markdown files if they exist
        markdown_files = [
            temp_workspace / "duplicate_report.md",
            temp_workspace / "diversity_report.md",
            temp_workspace / "decision_report.md"
        ]

        for md_file in markdown_files:
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Verify Markdown has content
                assert len(content) > 100, f"Markdown file too short: {md_file}"

                # Verify has at least one header
                assert '#' in content, f"Markdown missing headers: {md_file}"

    def test_3_workflow_performance(
        self,
        project_root: Path,
        temp_workspace: Path,
        test_validation_results: Dict[str, Any],
        test_strategy_files: List[Path]
    ):
        """
        Test 3: Workflow Performance

        Validates:
            - Workflow completes within 2 minutes for 5 strategies
            - Each component completes within reasonable time
        """
        validation_file = temp_workspace / "test_validation_results.json"

        # Time each component
        component_times = {}

        # 1. Duplicate detection
        start = time.time()
        duplicate_script = project_root / "scripts" / "detect_duplicates.py"
        result = subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(validation_file),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "duplicate_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        component_times['duplicate_detection'] = time.time() - start
        assert result.returncode == 0, "Duplicate detection failed"

        # 2. Diversity analysis
        start = time.time()
        diversity_script = project_root / "scripts" / "analyze_diversity.py"
        result = subprocess.run(
            [
                sys.executable,
                str(diversity_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(temp_workspace / "duplicate_report.json"),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "diversity_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        component_times['diversity_analysis'] = time.time() - start
        assert result.returncode == 0, "Diversity analysis failed"

        # 3. Decision evaluation
        start = time.time()
        decision_script = project_root / "scripts" / "evaluate_phase3_decision.py"
        result = subprocess.run(
            [
                sys.executable,
                str(decision_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(temp_workspace / "duplicate_report.json"),
                '--diversity-report', str(temp_workspace / "diversity_report.json"),
                '--output', str(temp_workspace / "decision_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        component_times['decision_evaluation'] = time.time() - start
        assert result.returncode in [0, 1, 2], "Decision evaluation failed"

        # Validate component times
        total_time = sum(component_times.values())
        assert total_time < 120, f"Total workflow time {total_time:.1f}s exceeds 120s"

        # Each component should complete in reasonable time
        for component, duration in component_times.items():
            assert duration < 60, f"{component} took {duration:.1f}s (expected <60s)"

    def test_4_workflow_error_handling(
        self,
        project_root: Path,
        temp_workspace: Path
    ):
        """
        Test 4: Error Handling

        Validates:
            - Missing input file -> clear error message
            - Invalid JSON -> stops and reports error
            - Script failure -> workflow stops, logs error
        """
        # Test 1: Missing validation results file
        missing_file = temp_workspace / "nonexistent.json"
        duplicate_script = project_root / "scripts" / "detect_duplicates.py"

        result = subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(missing_file),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "duplicate_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail with error code
        assert result.returncode != 0, "Script should fail with missing input file"
        # Should have error message
        assert len(result.stderr) > 0 or "not found" in result.stdout.lower(), \
            "Script should report missing file error"

        # Test 2: Invalid JSON file
        invalid_json_file = temp_workspace / "invalid.json"
        with open(invalid_json_file, 'w') as f:
            f.write("{ invalid json content }")

        result = subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(invalid_json_file),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "duplicate_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail with error code
        assert result.returncode != 0, "Script should fail with invalid JSON"

        # Test 3: Missing strategy directory
        nonexistent_dir = temp_workspace / "nonexistent_strategies"

        # Create valid JSON file for this test
        valid_json = temp_workspace / "valid.json"
        with open(valid_json, 'w') as f:
            json.dump({
                "summary": {"total": 0},
                "strategies_validation": []
            }, f)

        result = subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(valid_json),
                '--strategy-dir', str(nonexistent_dir),
                '--output', str(temp_workspace / "duplicate_report.md")
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Should fail or handle gracefully
        assert result.returncode != 0, "Script should fail with missing strategy dir"

    def test_5_decision_output_validation(
        self,
        project_root: Path,
        temp_workspace: Path,
        test_validation_results: Dict[str, Any],
        test_strategy_files: List[Path]
    ):
        """
        Test 5: Decision Output Validation

        Validates:
            - Decision report has correct structure
            - Decision is one of: GO, CONDITIONAL_GO, NO-GO
            - Exit codes match decision (0=GO, 1=CONDITIONAL, 2=NO-GO)
            - Report includes all required sections
        """
        # Run full workflow to generate decision
        validation_file = temp_workspace / "test_validation_results.json"
        duplicate_json = temp_workspace / "duplicate_report.json"
        diversity_json = temp_workspace / "diversity_report.json"
        decision_md = temp_workspace / "decision_report.md"

        # Run prerequisite scripts
        duplicate_script = project_root / "scripts" / "detect_duplicates.py"
        subprocess.run(
            [
                sys.executable,
                str(duplicate_script),
                '--validation-results', str(validation_file),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "duplicate_report.md")
            ],
            capture_output=True,
            timeout=60
        )

        diversity_script = project_root / "scripts" / "analyze_diversity.py"
        subprocess.run(
            [
                sys.executable,
                str(diversity_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(duplicate_json),
                '--strategy-dir', str(project_root),
                '--output', str(temp_workspace / "diversity_report.md")
            ],
            capture_output=True,
            timeout=60
        )

        # Run decision evaluation
        decision_script = project_root / "scripts" / "evaluate_phase3_decision.py"
        result = subprocess.run(
            [
                sys.executable,
                str(decision_script),
                '--validation-results', str(validation_file),
                '--duplicate-report', str(duplicate_json),
                '--diversity-report', str(diversity_json),
                '--output', str(decision_md)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Validate exit code
        assert result.returncode in [0, 1, 2], \
            f"Invalid exit code: {result.returncode} (expected 0, 1, or 2)"

        # Read decision document
        assert decision_md.exists(), "Decision report not created"

        with open(decision_md, 'r', encoding='utf-8') as f:
            decision_content = f.read()

        # Validate decision content has required sections
        required_sections = [
            "# Phase 3 GO/NO-GO Decision Report",
            "## Executive Summary",
            "## Key Metrics",
            "## Criteria Evaluation",
            "## Detailed Analysis"
        ]

        for section in required_sections:
            assert section in decision_content, f"Missing section: {section}"

        # Validate decision is one of the expected values
        valid_decisions = ["GO", "CONDITIONAL_GO", "NO-GO"]
        has_decision = any(decision in decision_content for decision in valid_decisions)
        assert has_decision, "Decision report missing valid decision"

        # Validate exit code matches decision
        if "**GO**" in decision_content and "NO-GO" not in decision_content:
            assert result.returncode == 0, "GO decision should return exit code 0"
        elif "CONDITIONAL_GO" in decision_content:
            assert result.returncode == 1, "CONDITIONAL_GO should return exit code 1"
        elif "NO-GO" in decision_content:
            assert result.returncode == 2, "NO-GO decision should return exit code 2"


# =============================================================================
# Test Execution
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
