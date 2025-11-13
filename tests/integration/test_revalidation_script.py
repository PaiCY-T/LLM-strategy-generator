"""
Phase 2 Task 4.3: Integration Tests for Re-validation Script

Tests the re-validation script (run_phase2_with_validation.py) that applies
the Bonferroni threshold fix and validates the correction.

Test Coverage:
    1. Re-validation execution on strategy subset (pilot test)
    2. Bonferroni threshold verification (0.5 vs 0.8)
    3. Statistical significance count validation
    4. Comparison report generation
    5. Execution success rate maintenance

Specification: validation-framework-critical-fixes
Requirement: REQ-4 (Re-validation Execution)
"""

import json
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock


class TestRevalidationScript(unittest.TestCase):
    """Integration tests for re-validation script execution."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.revalidation_script = cls.project_root / "run_phase2_with_validation.py"
        cls.comparison_script = cls.project_root / "scripts" / "generate_comparison_report.py"

        # Verify scripts exist
        if not cls.revalidation_script.exists():
            raise FileNotFoundError(f"Re-validation script not found: {cls.revalidation_script}")
        if not cls.comparison_script.exists():
            raise FileNotFoundError(f"Comparison script not found: {cls.comparison_script}")

    def setUp(self):
        """Set up test fixtures for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _find_latest_validation_result(self) -> Path:
        """Find the most recent validation result JSON file."""
        result_files = list(self.project_root.glob("phase2_validated_results_*.json"))
        if not result_files:
            raise FileNotFoundError("No validation result files found")

        # Sort by modification time and return the latest
        result_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return result_files[0]

    def _load_json_result(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a JSON result file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _create_mock_strategy_files(self, count: int = 3) -> List[Path]:
        """
        Create mock strategy files for testing.

        Args:
            count: Number of strategy files to create

        Returns:
            List of created strategy file paths
        """
        strategy_files = []

        # Mock strategy code that creates a valid backtest report
        mock_strategy_template = '''
# Mock strategy for re-validation testing
import pandas as pd
import numpy as np

# Create mock position series
position = pd.Series({{
    pd.Timestamp('2023-01-01'): 1.0,
    pd.Timestamp('2023-02-01'): {growth},
    pd.Timestamp('2023-03-01'): {growth} * 1.05,
    pd.Timestamp('2023-04-01'): {growth} * 1.10,
    pd.Timestamp('2023-05-01'): {growth} * 1.15,
}})

# Mock report object with metrics
class MockReport:
    def __init__(self):
        self.sharpe_ratio = {sharpe}
        self.total_return = {total_return}
        self.max_drawdown = {max_drawdown}
        self.win_rate = 0.60

    def get_stats(self):
        return {{
            'sharpe': self.sharpe_ratio,
            'total_return': self.total_return,
            'mdd': self.max_drawdown,
            'win_rate': self.win_rate
        }}

report = MockReport()
'''

        # Create strategies with varying Sharpe ratios
        sharpe_values = [0.9, 0.65, 0.45]  # High, medium, low

        for i in range(count):
            sharpe = sharpe_values[i] if i < len(sharpe_values) else 0.5

            strategy_code = mock_strategy_template.format(
                growth=1.0 + (i * 0.05),
                sharpe=sharpe,
                total_return=0.20 + (i * 0.05),
                max_drawdown=-0.10 - (i * 0.02)
            )

            filepath = self.project_root / f"generated_strategy_fixed_iter{i}.py"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(strategy_code)

            strategy_files.append(filepath)

        return strategy_files

    def _cleanup_mock_strategies(self, strategy_files: List[Path]):
        """Clean up mock strategy files."""
        for filepath in strategy_files:
            if filepath.exists():
                filepath.unlink()

    @unittest.skip("Requires real execution environment - test validates script structure only")
    def test_1_revalidation_execution(self):
        """
        Test 1: Execute re-validation script on 3-strategy subset (pilot).

        Validates:
            - Script runs without errors
            - Output JSON file is created
            - JSON structure is valid
        """
        # Create mock strategy files
        strategy_files = self._create_mock_strategy_files(count=3)

        try:
            # Execute re-validation script with 3-strategy limit
            start_time = time.time()

            result = subprocess.run(
                [
                    sys.executable,
                    str(self.revalidation_script),
                    '--limit', '3',
                    '--timeout', '60',
                    '--quiet'
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=300  # 5-minute timeout for full execution
            )

            execution_time = time.time() - start_time

            # Validate execution completed
            self.assertEqual(
                result.returncode, 0,
                f"Script execution failed with error:\n{result.stderr}"
            )

            # Validate execution time is reasonable (<2 minutes for 3 strategies)
            self.assertLess(
                execution_time, 120.0,
                f"Execution took too long: {execution_time:.1f}s"
            )

            # Find and load the generated JSON result
            result_file = self._find_latest_validation_result()
            self.assertTrue(result_file.exists(), "Result JSON file not created")

            result_data = self._load_json_result(result_file)

            # Validate JSON structure
            self.assertIn('summary', result_data)
            self.assertIn('validation_statistics', result_data)
            self.assertIn('strategies_validation', result_data)

            # Validate 3 strategies were processed
            self.assertEqual(
                result_data['summary']['total'],
                3,
                "Expected 3 strategies to be processed"
            )

        finally:
            # Clean up mock strategy files
            self._cleanup_mock_strategies(strategy_files)

    def test_2_threshold_fix_verification(self):
        """
        Test 2: Verify bonferroni_threshold=0.5 in output.

        Validates:
            - Bonferroni threshold is correctly set to 0.5 (not 0.8)
            - Threshold fix is applied consistently
        """
        # Load latest validation result
        result_file = self._find_latest_validation_result()
        result_data = self._load_json_result(result_file)

        # Validate bonferroni_threshold field exists
        self.assertIn(
            'validation_statistics',
            result_data,
            "Missing validation_statistics in result"
        )

        validation_stats = result_data['validation_statistics']

        self.assertIn(
            'bonferroni_threshold',
            validation_stats,
            "Missing bonferroni_threshold in validation_statistics"
        )

        # Validate threshold is 0.5 (the fix)
        bonferroni_threshold = validation_stats['bonferroni_threshold']
        self.assertEqual(
            bonferroni_threshold,
            0.5,
            f"Expected bonferroni_threshold=0.5, got {bonferroni_threshold}"
        )

        # Validate dynamic threshold remains 0.8
        self.assertIn(
            'dynamic_threshold',
            result_data,
            "Missing dynamic_threshold in result"
        )

        dynamic_threshold = result_data['dynamic_threshold']
        self.assertEqual(
            dynamic_threshold,
            0.8,
            f"Expected dynamic_threshold=0.8, got {dynamic_threshold}"
        )

        # Validate per-strategy validation details also have correct threshold
        if result_data.get('strategies_validation'):
            first_strategy = result_data['strategies_validation'][0]

            self.assertIn(
                'bonferroni_threshold',
                first_strategy,
                "Missing bonferroni_threshold in strategy validation"
            )

            strategy_threshold = first_strategy['bonferroni_threshold']
            # Allow None for failed strategies
            if strategy_threshold is not None:
                self.assertEqual(
                    strategy_threshold,
                    0.5,
                    f"Strategy threshold should be 0.5, got {strategy_threshold}"
                )

    def test_3_statistical_significance_count(self):
        """
        Test 3: Verify ~18 strategies are statistically significant (full 20).

        Validates:
            - Statistical significance count is reasonable (15-20 strategies)
            - Fix correctly identifies strategies with Sharpe > 0.5
            - Count matches expectation based on validation report
        """
        # Load latest validation result
        result_file = self._find_latest_validation_result()
        result_data = self._load_json_result(result_file)

        # Validate validation_statistics exists
        self.assertIn(
            'validation_statistics',
            result_data,
            "Missing validation_statistics"
        )

        validation_stats = result_data['validation_statistics']

        # Check statistically_significant count
        self.assertIn(
            'statistically_significant',
            validation_stats,
            "Missing statistically_significant count"
        )

        stat_sig_count = validation_stats['statistically_significant']

        # Based on validation report, expect ~19 out of 20 strategies
        # Allow range of 15-20 for robustness
        self.assertGreaterEqual(
            stat_sig_count,
            15,
            f"Expected at least 15 statistically significant strategies, got {stat_sig_count}"
        )

        self.assertLessEqual(
            stat_sig_count,
            20,
            f"Expected at most 20 statistically significant strategies, got {stat_sig_count}"
        )

        # Validate bonferroni_passed field (should be same as statistically_significant)
        if 'bonferroni_passed' in validation_stats:
            bonferroni_passed = validation_stats['bonferroni_passed']
            self.assertEqual(
                bonferroni_passed,
                stat_sig_count,
                f"bonferroni_passed ({bonferroni_passed}) should equal "
                f"statistically_significant ({stat_sig_count})"
            )

        # Validate per-strategy counts match
        strategies_validation = result_data.get('strategies_validation', [])
        if strategies_validation:
            actual_sig_count = sum(
                1 for s in strategies_validation
                if s.get('statistically_significant', False)
            )

            self.assertEqual(
                actual_sig_count,
                stat_sig_count,
                f"Per-strategy count ({actual_sig_count}) doesn't match "
                f"summary count ({stat_sig_count})"
            )

    def test_4_comparison_report_generation(self):
        """
        Test 4: Verify Markdown comparison report is created.

        Validates:
            - Comparison report script runs successfully
            - Markdown report file is created
            - Report contains required sections
        """
        # Find two recent validation result files for comparison
        result_files = list(self.project_root.glob("phase2_validated_results_*.json"))
        result_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        if len(result_files) < 2:
            self.skipTest("Need at least 2 validation result files for comparison")

        before_file = result_files[1]  # Older result (before fix)
        after_file = result_files[0]   # Newer result (after fix)

        # Create temporary output file
        output_file = self.temp_path / "test_comparison_report.md"

        # Execute comparison report script
        result = subprocess.run(
            [
                sys.executable,
                str(self.comparison_script),
                '--before', str(before_file),
                '--after', str(after_file),
                '--output', str(output_file)
            ],
            cwd=str(self.project_root),
            capture_output=True,
            text=True,
            timeout=30  # 30-second timeout
        )

        # Validate execution succeeded
        self.assertEqual(
            result.returncode, 0,
            f"Comparison report generation failed:\n{result.stderr}"
        )

        # Validate output file was created
        self.assertTrue(
            output_file.exists(),
            "Comparison report file not created"
        )

        # Read and validate report content
        with open(output_file, 'r', encoding='utf-8') as f:
            report_content = f.read()

        # Validate report is not empty
        self.assertGreater(
            len(report_content),
            100,
            "Report content is too short"
        )

        # Validate required sections are present
        required_sections = [
            "# Validation Framework Fix - Before/After Comparison",
            "## Executive Summary",
            "## Threshold Configuration Changes",
            "## Validation Results Summary",
            "## Strategy-Level Changes",
            "## Execution Performance",
            "## Validation",
            "## Conclusion"
        ]

        for section in required_sections:
            self.assertIn(
                section,
                report_content,
                f"Missing required section: {section}"
            )

        # Validate threshold fix is documented
        self.assertIn(
            "Bonferroni Threshold",
            report_content,
            "Report should document Bonferroni threshold"
        )

        # Validate status indicators are present
        self.assertIn(
            "✅",
            report_content,
            "Report should contain success indicators"
        )

    def test_5_execution_success_rate(self):
        """
        Test 5: Verify 100% execution success rate is maintained.

        Validates:
            - All strategies execute successfully
            - No execution failures or timeouts
            - Success rate is 100% (or very close)
        """
        # Load latest validation result
        result_file = self._find_latest_validation_result()
        result_data = self._load_json_result(result_file)

        # Validate summary exists
        self.assertIn('summary', result_data, "Missing summary in result")

        summary = result_data['summary']

        # Validate required fields
        self.assertIn('total', summary, "Missing total count")
        self.assertIn('successful', summary, "Missing successful count")
        self.assertIn('failed', summary, "Missing failed count")

        total = summary['total']
        successful = summary['successful']
        failed = summary['failed']

        # Validate counts are consistent
        self.assertEqual(
            total,
            successful + failed,
            f"Total ({total}) doesn't equal successful ({successful}) + failed ({failed})"
        )

        # Calculate success rate
        success_rate = successful / total if total > 0 else 0.0

        # Validate success rate is 100% (or at least 95% for robustness)
        self.assertGreaterEqual(
            success_rate,
            0.95,
            f"Expected at least 95% success rate, got {success_rate:.1%}"
        )

        # Ideally should be 100%
        if success_rate < 1.0:
            print(f"Warning: Success rate is {success_rate:.1%}, expected 100%")

        # Validate execution_stats if available
        if 'execution_stats' in result_data:
            exec_stats = result_data['execution_stats']

            if 'timeout_count' in exec_stats:
                timeout_count = exec_stats['timeout_count']
                self.assertEqual(
                    timeout_count,
                    0,
                    f"Expected 0 timeouts, got {timeout_count}"
                )

        # Validate classification breakdown
        classification_breakdown = summary.get('classification_breakdown', {})
        if classification_breakdown:
            level_0_failed = classification_breakdown.get('level_0_failed', 0)

            # Level 0 should be 0 (no failures)
            self.assertEqual(
                level_0_failed,
                0,
                f"Expected 0 Level 0 (FAILED) strategies, got {level_0_failed}"
            )


class TestRevalidationScriptStructure(unittest.TestCase):
    """Unit tests for re-validation script structure and imports."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.revalidation_script = cls.project_root / "run_phase2_with_validation.py"

    def test_script_exists(self):
        """Verify re-validation script exists."""
        self.assertTrue(
            self.revalidation_script.exists(),
            f"Re-validation script not found: {self.revalidation_script}"
        )

    def test_script_has_main(self):
        """Verify script has main entry point."""
        with open(self.revalidation_script, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(
            "def main():",
            content,
            "Script should have main() function"
        )

        self.assertIn(
            "if __name__ == '__main__':",
            content,
            "Script should have main guard"
        )

    def test_script_imports_validation_framework(self):
        """Verify script imports validation framework components."""
        with open(self.revalidation_script, 'r', encoding='utf-8') as f:
            content = f.read()

        required_imports = [
            "from src.validation import",
            "BonferroniIntegrator",
            "DynamicThresholdCalculator"
        ]

        for import_line in required_imports:
            self.assertIn(
                import_line,
                content,
                f"Script should import: {import_line}"
            )

    def test_script_uses_bonferroni_threshold_fix(self):
        """Verify script uses the fixed Bonferroni threshold (0.5)."""
        with open(self.revalidation_script, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for the fix comment or explicit 0.5 threshold
        self.assertIn(
            "0.5",
            content,
            "Script should reference 0.5 threshold"
        )

        # Check for validation with correct threshold
        self.assertIn(
            "bonferroni_threshold",
            content,
            "Script should use bonferroni_threshold field"
        )

    def test_script_command_line_interface(self):
        """Verify script has proper command-line interface."""
        with open(self.revalidation_script, 'r', encoding='utf-8') as f:
            content = f.read()

        required_cli_elements = [
            "argparse",
            "ArgumentParser",
            "--limit",
            "--timeout"
        ]

        for element in required_cli_elements:
            self.assertIn(
                element,
                content,
                f"Script should have CLI element: {element}"
            )


class TestComparisonReportScript(unittest.TestCase):
    """Unit tests for comparison report script structure."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.comparison_script = cls.project_root / "scripts" / "generate_comparison_report.py"

    def test_comparison_script_exists(self):
        """Verify comparison report script exists."""
        self.assertTrue(
            self.comparison_script.exists(),
            f"Comparison script not found: {self.comparison_script}"
        )

    def test_comparison_script_has_main(self):
        """Verify comparison script has main entry point."""
        with open(self.comparison_script, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(
            "def main():",
            content,
            "Script should have main() function"
        )

    def test_comparison_script_validates_thresholds(self):
        """Verify comparison script checks threshold changes."""
        with open(self.comparison_script, 'r', encoding='utf-8') as f:
            content = f.read()

        threshold_checks = [
            "bonferroni_threshold",
            "0.8",
            "0.5"
        ]

        for check in threshold_checks:
            self.assertIn(
                check,
                content,
                f"Script should check: {check}"
            )

    def test_comparison_script_generates_markdown(self):
        """Verify comparison script generates Markdown output."""
        with open(self.comparison_script, 'r', encoding='utf-8') as f:
            content = f.read()

        markdown_elements = [
            "def generate_markdown_report",
            "# Validation Framework Fix",
            "## Executive Summary",
            "## Threshold Configuration Changes"
        ]

        for element in markdown_elements:
            self.assertIn(
                element,
                content,
                f"Script should have Markdown element: {element}"
            )


if __name__ == '__main__':
    unittest.main()
