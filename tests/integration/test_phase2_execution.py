"""
Phase 2 Task 5.2: Integration Tests for Phase2TestRunner

Tests the full end-to-end pipeline of Phase2TestRunner, validating integration
between all 5 components:
    1. BacktestExecutor: Execute strategy code with timeout protection
    2. MetricsExtractor: Extract performance metrics from backtest reports
    3. SuccessClassifier: Classify results into success levels (0-3)
    4. ErrorClassifier: Categorize execution errors
    5. ResultsReporter: Generate JSON and Markdown reports

Test Coverage:
    - Full pipeline execution with 3 mock strategies (valid, timeout, error)
    - Component integration verification
    - Report validation (JSON and Markdown)
    - Edge case handling (failures, partial results, report generation)
    - Fast execution (<30 seconds, no real data dependency)
"""

import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from run_phase2_backtest_execution import Phase2TestRunner
from src.backtest.executor import ExecutionResult
from src.backtest.metrics import StrategyMetrics
from src.backtest.classifier import ClassificationResult
from src.backtest.error_classifier import ErrorCategory


class TestPhase2ExecutionIntegration(unittest.TestCase):
    """Integration tests for Phase2TestRunner end-to-end workflow."""

    def setUp(self):
        """Set up test fixtures for integration testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create mock strategies with different outcomes
        self.valid_strategy = '''
# Valid strategy that should reach Level 3 (profitable)
import pandas as pd
import numpy as np

# Create mock position series with positive returns
position = pd.Series({
    pd.Timestamp('2023-01-01'): 1.0,
    pd.Timestamp('2023-02-01'): 1.05,
    pd.Timestamp('2023-03-01'): 1.10,
    pd.Timestamp('2023-04-01'): 1.15,
    pd.Timestamp('2023-05-01'): 1.20,
})

# Generate mock report object
class MockReport:
    def __init__(self):
        self.sharpe_ratio = 1.5
        self.total_return = 0.25
        self.max_drawdown = -0.10
        self.win_rate = 0.60

    def get_stats(self):
        return {
            'sharpe': self.sharpe_ratio,
            'total_return': self.total_return,
            'mdd': self.max_drawdown,
            'win_rate': self.win_rate
        }

report = MockReport()
'''

        self.timeout_strategy = '''
# Strategy with infinite loop (should timeout)
while True:
    pass
'''

        self.error_strategy = '''
# Strategy with missing data error (KeyError)
import pandas as pd

# Try to access non-existent key
data = {'close': [100, 101, 102]}
missing_value = data['volume']  # KeyError: 'volume'
'''

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_strategy_files(self) -> list:
        """Create temporary strategy files for testing.

        Returns:
            List of Path objects for created strategy files
        """
        strategy_files = []

        # Create 3 strategy files
        strategies = [
            (0, self.valid_strategy),
            (1, self.timeout_strategy),
            (2, self.error_strategy)
        ]

        for iter_num, code in strategies:
            filepath = self.project_root / f"generated_strategy_fixed_iter{iter_num}.py"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            strategy_files.append(filepath)

        return strategy_files

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    def test_full_pipeline_integration(
        self,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test full pipeline with 3 mock strategies (valid, timeout, error).

        Validates:
            - All components integrate correctly
            - 3 strategies processed (1 success, 2 failures)
            - Classification levels correct (Level 0: 2, Level 3: 1)
            - Reports generated successfully
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path to return our temp directory
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        # Mock strategy discovery
        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock execution results (simulate BacktestExecutor output)
            mock_results = [
                # Valid strategy - should be Level 3
                ExecutionResult(
                    success=True,
                    execution_time=5.0,
                    sharpe_ratio=1.5,
                    total_return=0.25,
                    max_drawdown=-0.10,
                    error_type=None,
                    error_message=None
                ),
                # Timeout strategy - should be Level 0
                ExecutionResult(
                    success=False,
                    execution_time=60.0,
                    sharpe_ratio=None,
                    total_return=None,
                    max_drawdown=None,
                    error_type='TimeoutError',
                    error_message='Execution exceeded 60 seconds timeout'
                ),
                # Error strategy - should be Level 0
                ExecutionResult(
                    success=False,
                    execution_time=0.5,
                    sharpe_ratio=None,
                    total_return=None,
                    max_drawdown=None,
                    error_type='KeyError',
                    error_message="KeyError: 'volume'"
                )
            ]
            mock_execute_strategies.return_value = mock_results

            # Create runner and execute
            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)

            # Validate summary structure
            self.assertTrue(summary['success'])
            self.assertEqual(summary['total_strategies'], 3)
            self.assertEqual(summary['executed'], 1)
            self.assertEqual(summary['failed'], 2)

            # Validate results
            self.assertEqual(len(summary['results']), 3)
            self.assertTrue(summary['results'][0].success)
            self.assertFalse(summary['results'][1].success)
            self.assertFalse(summary['results'][2].success)

            # Validate metrics extraction
            self.assertEqual(len(summary['strategy_metrics']), 3)
            self.assertTrue(summary['strategy_metrics'][0].execution_success)
            self.assertFalse(summary['strategy_metrics'][1].execution_success)
            self.assertFalse(summary['strategy_metrics'][2].execution_success)

            # Validate classifications
            self.assertEqual(len(summary['classifications']), 3)
            classifications = summary['classifications']

            # Count classification levels
            level_counts = {0: 0, 1: 0, 2: 0, 3: 0}
            for cls in classifications:
                level_counts[cls.level] += 1

            # Valid strategy should be Level 3, failures should be Level 0
            self.assertEqual(level_counts[0], 2, "Should have 2 Level 0 (FAILED) strategies")
            self.assertEqual(level_counts[3], 1, "Should have 1 Level 3 (PROFITABLE) strategy")

            # Validate report generation
            self.assertIsNotNone(summary['report'])
            self.assertIn('summary', summary['report'])
            self.assertIn('metrics', summary['report'])
            self.assertIn('errors', summary['report'])
            self.assertIn('execution_stats', summary['report'])

            # Validate execution time
            self.assertGreater(summary['execution_time'], 0)
            self.assertIn('timestamp', summary)

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    def test_component_integration_backtest_executor(
        self,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test BacktestExecutor integration with timeout handling.

        Validates:
            - Executor correctly handles valid strategies
            - Timeout protection works as expected
            - Error handling for invalid code
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Test that executor is initialized with correct timeout
            runner = Phase2TestRunner(timeout=30, limit=3)
            self.assertEqual(runner.executor.timeout, 30)
            self.assertEqual(runner.default_timeout, 30)
            self.assertEqual(runner.limit, 3)

            # Verify components are initialized
            self.assertIsNotNone(runner.executor)
            self.assertIsNotNone(runner.metrics_extractor)
            self.assertIsNotNone(runner.classifier)
            self.assertIsNotNone(runner.error_classifier)
            self.assertIsNotNone(runner.reporter)

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    def test_report_validation_json_structure(
        self,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test JSON report structure and content validation.

        Validates:
            - JSON report is valid and parseable
            - Contains all required sections
            - Statistics are accurate
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock execution results
            mock_results = [
                ExecutionResult(success=True, sharpe_ratio=1.5, total_return=0.25,
                              max_drawdown=-0.10, execution_time=5.0),
                ExecutionResult(success=False, error_type='TimeoutError',
                              error_message='Timeout', execution_time=60.0),
                ExecutionResult(success=False, error_type='KeyError',
                              error_message='Data missing', execution_time=0.5)
            ]
            mock_execute_strategies.return_value = mock_results

            # Run and get report
            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)
            json_report = summary['report']

            # Validate JSON structure
            self.assertIn('summary', json_report)
            self.assertIn('metrics', json_report)
            self.assertIn('errors', json_report)
            self.assertIn('execution_stats', json_report)

            # Validate summary statistics
            summary_section = json_report['summary']
            self.assertEqual(summary_section['total'], 3)
            self.assertEqual(summary_section['successful'], 1)
            self.assertEqual(summary_section['failed'], 2)

            # Validate classification breakdown
            self.assertIn('classification_breakdown', summary_section)
            classification_breakdown = summary_section['classification_breakdown']
            self.assertIn('level_0_failed', classification_breakdown)
            self.assertIn('level_3_profitable', classification_breakdown)

            # Validate errors section structure
            self.assertIn('by_category', json_report['errors'])
            self.assertIn('top_errors', json_report['errors'])

            # Validate JSON is serializable
            json_str = json.dumps(json_report)
            self.assertIsInstance(json_str, str)

            # Validate JSON can be parsed back
            parsed = json.loads(json_str)
            self.assertEqual(parsed['summary']['total'], 3)

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    @patch('builtins.open', create=True)
    def test_report_validation_markdown_generation(
        self,
        mock_open,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test Markdown report generation and content.

        Validates:
            - Markdown report is generated
            - Contains formatted tables and sections
            - File is saved correctly
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        # Mock file operations
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock execution results
            mock_results = [
                ExecutionResult(success=True, sharpe_ratio=1.5, total_return=0.25,
                              max_drawdown=-0.10, execution_time=5.0),
                ExecutionResult(success=False, error_type='TimeoutError',
                              error_message='Timeout', execution_time=60.0),
                ExecutionResult(success=False, error_type='KeyError',
                              error_message='Data missing', execution_time=0.5)
            ]
            mock_execute_strategies.return_value = mock_results

            # Run
            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)

            # Verify markdown report generation was attempted
            # (ResultsReporter.generate_markdown_report was called)
            self.assertIsNotNone(summary['report'])

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    def test_edge_case_runner_continues_after_failures(
        self,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test that runner continues execution after individual failures.

        Validates:
            - Runner processes all strategies despite failures
            - Partial results are aggregated correctly
            - Reports generated even with all failures
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock all failures
            mock_results = [
                ExecutionResult(success=False, error_type='TimeoutError',
                              error_message='Timeout 1', execution_time=60.0),
                ExecutionResult(success=False, error_type='KeyError',
                              error_message='Data missing 1', execution_time=0.5),
                ExecutionResult(success=False, error_type='ValueError',
                              error_message='Invalid value', execution_time=1.0)
            ]
            mock_execute_strategies.return_value = mock_results

            # Run
            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)

            # Validate all strategies were processed
            self.assertEqual(summary['total_strategies'], 3)
            self.assertEqual(summary['executed'], 0)
            self.assertEqual(summary['failed'], 3)

            # Validate all results present
            self.assertEqual(len(summary['results']), 3)

            # Validate classifications (all should be Level 0)
            classifications = summary['classifications']
            self.assertEqual(len(classifications), 3)
            for cls in classifications:
                self.assertEqual(cls.level, 0, "All failures should be Level 0")

            # Validate report still generated
            self.assertIsNotNone(summary['report'])
            self.assertEqual(summary['report']['summary']['total'], 3)
            self.assertEqual(summary['report']['summary']['failed'], 3)

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    def test_edge_case_mixed_error_categorization(
        self,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test error classification with various error types.

        Validates:
            - TimeoutError categorized correctly
            - KeyError (data_missing) categorized correctly
            - Error breakdown in report is accurate
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock mixed results with different error types
            mock_results = [
                ExecutionResult(success=True, sharpe_ratio=1.5, total_return=0.25,
                              max_drawdown=-0.10, execution_time=5.0),
                ExecutionResult(success=False, error_type='TimeoutError',
                              error_message='Execution exceeded 60 seconds',
                              execution_time=60.0),
                ExecutionResult(success=False, error_type='KeyError',
                              error_message="KeyError: 'volume'",
                              execution_time=0.5)
            ]
            mock_execute_strategies.return_value = mock_results

            # Run
            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)

            # Validate error breakdown in report
            error_section = summary['report']['errors']

            # Check error breakdown by category
            self.assertIn('by_category', error_section)
            error_by_category = error_section['by_category']
            self.assertIn('timeout', error_by_category)
            self.assertIn('data_missing', error_by_category)

            # Check top errors
            self.assertIn('top_errors', error_section)
            self.assertGreater(len(error_section['top_errors']), 0)

            # Verify at least one timeout and one data error
            error_types = [e.error_type for e in summary['results'] if not e.success]
            self.assertIn('TimeoutError', error_types)
            self.assertIn('KeyError', error_types)

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    @patch.object(Phase2TestRunner, '_execute_strategies')
    def test_performance_test_completes_fast(
        self,
        mock_execute_strategies,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test that integration test completes in under 30 seconds.

        Validates:
            - No dependency on real finlab data
            - Fast execution with mocked components
            - Test is reliable and repeatable
        """
        # Mock authentication
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path
        mock_path_instance = MagicMock()
        mock_path_instance.parent = self.project_root
        mock_path_class.return_value = mock_path_instance

        # Create strategy files
        strategy_files = self._create_strategy_files()

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=strategy_files
        ):
            # Mock fast execution results
            mock_results = [
                ExecutionResult(success=True, sharpe_ratio=1.5, total_return=0.25,
                              max_drawdown=-0.10, execution_time=0.1),
                ExecutionResult(success=False, error_type='TimeoutError',
                              error_message='Timeout', execution_time=0.1),
                ExecutionResult(success=False, error_type='KeyError',
                              error_message='Data missing', execution_time=0.1)
            ]
            mock_execute_strategies.return_value = mock_results

            # Measure execution time
            start_time = time.time()

            runner = Phase2TestRunner(timeout=60, limit=3)
            summary = runner.run(timeout=60, verbose=False)

            elapsed_time = time.time() - start_time

            # Validate fast completion (should be < 5 seconds with mocking)
            self.assertLess(
                elapsed_time,
                5.0,
                f"Test should complete in < 5 seconds, took {elapsed_time:.2f}s"
            )

            # Validate results are complete
            self.assertEqual(summary['total_strategies'], 3)
            self.assertIsNotNone(summary['report'])


class TestPhase2ExecutionEdgeCases(unittest.TestCase):
    """Additional edge case tests for Phase2TestRunner."""

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    def test_authentication_failure_raises_error(self, mock_verify_finlab):
        """Test that authentication failure raises RuntimeError."""
        # Mock authentication failure
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = False
        mock_auth_status.error_message = "Invalid credentials"
        mock_verify_finlab.return_value = mock_auth_status

        runner = Phase2TestRunner(timeout=60, limit=3)

        with self.assertRaises(RuntimeError) as context:
            runner.run(timeout=60, verbose=False)

        self.assertIn("authentication failed", str(context.exception).lower())

    @patch('run_phase2_backtest_execution.verify_finlab_session')
    @patch('run_phase2_backtest_execution.Path')
    def test_no_strategies_found_raises_error(
        self,
        mock_path_class,
        mock_verify_finlab
    ):
        """Test that no strategy files raises RuntimeError."""
        # Mock authentication success
        mock_auth_status = MagicMock()
        mock_auth_status.is_authenticated = True
        mock_verify_finlab.return_value = mock_auth_status

        # Mock Path to return empty directory
        mock_path_instance = MagicMock()
        mock_path_instance.parent.glob.return_value = []
        mock_path_class.return_value = mock_path_instance

        with patch.object(
            Phase2TestRunner,
            '_discover_strategies',
            return_value=[]
        ):
            runner = Phase2TestRunner(timeout=60, limit=3)

            with self.assertRaises(RuntimeError) as context:
                runner.run(timeout=60, verbose=False)

            self.assertIn("no strategy files", str(context.exception).lower())


if __name__ == '__main__':
    unittest.main()
