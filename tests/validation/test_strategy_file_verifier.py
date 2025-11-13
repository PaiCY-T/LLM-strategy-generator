"""
Tests for strategy file verification module (Phase 2 Task 6.1).

Tests the StrategyFileVerifier class and helper functions.
"""

import unittest
import tempfile
import json
from pathlib import Path
from src.validation.strategy_file_verifier import (
    StrategyFileVerifier,
    verify_strategies,
    StrategyFileInfo,
)


class TestStrategyFileVerifier(unittest.TestCase):
    """Test cases for StrategyFileVerifier class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)
        self.verifier = StrategyFileVerifier(str(self.project_root))

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_no_strategies_found(self):
        """Test when no strategy files exist."""
        results = self.verifier.verify()

        self.assertEqual(results.status, 'failed')
        self.assertEqual(results.total_strategies_found, 0)
        self.assertEqual(results.total_accessible, 0)
        self.assertIn('No strategy files found', results.summary)

    def test_find_loop_iterations(self):
        """Test finding loop iteration strategy files."""
        # Create sample loop iteration files
        (self.project_root / 'generated_strategy_loop_iter0.py').write_text('# Test strategy')
        (self.project_root / 'generated_strategy_loop_iter1.py').write_text('# Test strategy')

        results = self.verifier.verify()

        self.assertEqual(results.by_category['loop_iteration'], 2)
        self.assertEqual(results.total_strategies_found, 2)

    def test_find_fixed_iterations(self):
        """Test finding fixed iteration strategy files."""
        # Create sample fixed iteration files
        (self.project_root / 'generated_strategy_fixed_iter0.py').write_text('# Test strategy')
        (self.project_root / 'generated_strategy_fixed_iter1.py').write_text('# Test strategy')

        results = self.verifier.verify()

        self.assertEqual(results.by_category['fixed_iteration'], 2)
        self.assertEqual(results.total_strategies_found, 2)

    def test_find_mixed_strategies(self):
        """Test finding both loop and fixed iteration strategies."""
        # Create mixed files
        (self.project_root / 'generated_strategy_loop_iter0.py').write_text('# Test')
        (self.project_root / 'generated_strategy_loop_iter1.py').write_text('# Test')
        (self.project_root / 'generated_strategy_fixed_iter0.py').write_text('# Test')

        results = self.verifier.verify()

        self.assertEqual(results.by_category['loop_iteration'], 2)
        self.assertEqual(results.by_category['fixed_iteration'], 1)
        self.assertEqual(results.total_strategies_found, 3)
        self.assertEqual(results.total_accessible, 3)

    def test_innovations_file_detection(self):
        """Test detection of innovations.jsonl file."""
        # Create artifacts directory structure
        data_dir = self.project_root / 'artifacts' / 'data'
        data_dir.mkdir(parents=True)

        innovations = {
            'id': 'test_innov_001',
            'code': 'test_code',
            'rationale': 'test rationale',
        }
        innovations_path = data_dir / 'innovations.jsonl'
        innovations_path.write_text(json.dumps(innovations) + '\n')

        results = self.verifier.verify()

        self.assertTrue(results.innovations_file['exists'])
        self.assertTrue(results.innovations_file['is_readable'])
        self.assertGreater(results.innovations_file['size_bytes'], 0)

    def test_inaccessible_files(self):
        """Test detection of inaccessible files."""
        # Create a readable file
        readable = self.project_root / 'generated_strategy_loop_iter0.py'
        readable.write_text('# Test strategy')

        results = self.verifier.verify()

        self.assertEqual(results.total_strategies_found, 1)
        self.assertEqual(results.total_accessible, 1)
        # Set partial status with 1 readable strategy
        self.assertEqual(results.status, 'success')

    def test_get_report(self):
        """Test report generation."""
        # Create test files
        (self.project_root / 'generated_strategy_loop_iter0.py').write_text('# Test')
        self.verifier.verify()

        report = self.verifier.get_report()

        self.assertIn('STRATEGY FILE VERIFICATION REPORT', report)
        self.assertIn('SUCCESS', report)
        self.assertIn('Total strategies found: 1', report)
        self.assertIn('LOOP_ITERATION', report)

    def test_to_json(self):
        """Test JSON export."""
        # Create test files
        (self.project_root / 'generated_strategy_loop_iter0.py').write_text('# Test')
        self.verifier.verify()

        json_str = self.verifier.to_json()
        data = json.loads(json_str)

        self.assertEqual(data['total_strategies_found'], 1)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['files']), 1)

    def test_file_info_dataclass(self):
        """Test StrategyFileInfo dataclass."""
        info = StrategyFileInfo(
            path='/test/path.py',
            filename='path.py',
            size_bytes=1024,
            is_readable=True,
            category='loop_iteration'
        )

        self.assertEqual(info.path, '/test/path.py')
        self.assertEqual(info.filename, 'path.py')
        self.assertEqual(info.size_bytes, 1024)
        self.assertTrue(info.is_readable)


class TestVerifyStrategiesFunction(unittest.TestCase):
    """Test cases for convenience verify_strategies function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_verify_strategies_function(self):
        """Test the convenience function."""
        # Create test files
        (self.project_root / 'generated_strategy_loop_iter0.py').write_text('# Test')

        results = verify_strategies(str(self.project_root))

        self.assertEqual(results.total_strategies_found, 1)
        self.assertEqual(results.status, 'success')


class TestIntegrationWithRealProject(unittest.TestCase):
    """Integration tests with the real project (if it exists)."""

    def test_real_project_verification(self):
        """Test verification on real project if it exists."""
        project_root = Path('/mnt/c/Users/jnpi/documents/finlab')

        if not project_root.exists():
            self.skipTest("Real project not found")

        verifier = StrategyFileVerifier(str(project_root))
        results = verifier.verify()

        # Real project should have strategies
        self.assertGreater(results.total_strategies_found, 0)
        self.assertEqual(results.status, 'success')

        # Should have both types
        self.assertGreater(results.by_category.get('loop_iteration', 0), 0)

        # All found files should be accessible
        self.assertEqual(results.total_accessible, results.total_strategies_found)


if __name__ == '__main__':
    unittest.main()
