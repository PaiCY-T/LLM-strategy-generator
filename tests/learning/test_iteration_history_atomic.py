"""Atomic Write Tests for IterationHistory

Tests the atomic write mechanism that prevents data corruption
when writes are interrupted (crashes, CTRL+C, power loss).

The atomic write pattern:
1. Write all records to temporary file
2. Use os.replace() for atomic file replacement
3. Original file never corrupted even if interrupted
"""

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime

from src.learning.iteration_history import IterationHistory, IterationRecord


def create_test_record(iteration_num: int, sharpe: float = 1.0) -> IterationRecord:
    """Helper to create test record"""
    return IterationRecord(
        iteration_num=iteration_num,
        strategy_code=f"# Strategy {iteration_num}\ndata.get('price:收盤價')",
        execution_result={"success": True, "execution_time": 1.0},
        metrics={"sharpe_ratio": sharpe, "total_return": 0.1, "max_drawdown": -0.05},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat(),
        champion_updated=False
    )


class TestAtomicWrite:
    """Test atomic write mechanism prevents corruption"""

    def test_atomic_write_prevents_corruption(self, tmp_path):
        """Verify write interruption does not corrupt history file

        This is the core test for Task H1.2 - ensures that even if
        os.replace() crashes, the original file remains intact.
        """
        # Setup
        history_file = tmp_path / 'test_history.jsonl'
        history = IterationHistory(str(history_file))

        # 1. Write initial record
        record0 = create_test_record(0, sharpe=1.0)
        history.save(record0)

        # Verify initial state
        records = history.get_all()
        assert len(records) == 1
        assert records[0].iteration_num == 0
        assert records[0].metrics['sharpe_ratio'] == 1.0

        # 2. Simulate crash during os.replace()
        # This is the critical moment - if crash happens here,
        # the original file must remain uncorrupted
        with patch('os.replace', side_effect=Exception("Simulated crash during os.replace")):
            try:
                record1 = create_test_record(1, sharpe=1.2)
                history.save(record1)
                assert False, "Should have raised exception"
            except IOError:
                pass  # Expected

        # 3. CRITICAL VERIFICATION: Original file must be intact
        # This is what atomic write protects against
        records = history.get_all()
        assert len(records) == 1, \
            "Original file should still have exactly 1 record after crash"
        assert records[0].iteration_num == 0, \
            "Original record should be unchanged"
        assert records[0].metrics['sharpe_ratio'] == 1.0, \
            "Original data should be intact"

        # 4. Verify we can continue after crash
        record2 = create_test_record(2, sharpe=1.5)
        history.save(record2)
        records = history.get_all()
        assert len(records) == 2
        assert records[0].iteration_num == 0
        assert records[1].iteration_num == 2

    def test_atomic_write_success(self, tmp_path):
        """Verify normal write operations succeed correctly"""
        history_file = tmp_path / 'test_history_success.jsonl'
        history = IterationHistory(str(history_file))

        # Write 5 records sequentially
        for i in range(5):
            record = create_test_record(i, sharpe=1.0 + i * 0.1)
            history.save(record)

        # Verify all records saved correctly
        records = history.get_all()
        assert len(records) == 5
        assert [r.iteration_num for r in records] == [0, 1, 2, 3, 4]

        # Verify metrics preserved
        for i, record in enumerate(records):
            expected_sharpe = 1.0 + i * 0.1
            assert abs(record.metrics['sharpe_ratio'] - expected_sharpe) < 0.001

    def test_temp_file_cleanup_on_error(self, tmp_path):
        """Verify temporary file is cleaned up on write error"""
        history_file = tmp_path / 'test_history.jsonl'
        history = IterationHistory(str(history_file))
        tmp_file = Path(str(history_file) + '.tmp')

        # Simulate error during file write (before os.replace)
        with patch('builtins.open', side_effect=Exception("Disk full")):
            try:
                record = create_test_record(0, sharpe=1.0)
                history.save(record)
                assert False, "Should have raised exception"
            except IOError:
                pass  # Expected

        # Verify temp file doesn't exist (cleaned up)
        assert not tmp_file.exists(), \
            "Temporary file should be cleaned up on error"

    def test_atomic_write_with_existing_data(self, tmp_path):
        """Verify atomic write works correctly with existing records"""
        history_file = tmp_path / 'test_history.jsonl'
        history = IterationHistory(str(history_file))

        # Create initial data
        for i in range(3):
            history.save(create_test_record(i, sharpe=1.0 + i * 0.1))

        # Simulate crash on 4th write
        with patch('os.replace', side_effect=Exception("Crash")):
            try:
                history.save(create_test_record(3, sharpe=1.3))
            except IOError:
                pass

        # Verify original 3 records intact
        records = history.get_all()
        assert len(records) == 3
        assert [r.iteration_num for r in records] == [0, 1, 2]

        # Verify can recover and continue
        history.save(create_test_record(3, sharpe=1.3))
        records = history.get_all()
        assert len(records) == 4
        assert [r.iteration_num for r in records] == [0, 1, 2, 3]

    def test_crash_during_temp_file_write(self, tmp_path):
        """Verify original file safe if crash during temp file write"""
        history_file = tmp_path / 'test_history.jsonl'
        history = IterationHistory(str(history_file))

        # Write initial record
        history.save(create_test_record(0, sharpe=1.0))

        # Simulate crash during temp file write (before os.replace)
        original_open = open
        def failing_open(path, mode, **kwargs):
            if '.tmp' in str(path) and mode == 'w':
                raise Exception("Crash during temp file write")
            return original_open(path, mode, **kwargs)

        with patch('builtins.open', side_effect=failing_open):
            try:
                history.save(create_test_record(1, sharpe=1.2))
            except IOError:
                pass

        # Verify original file completely intact
        records = history.get_all()
        assert len(records) == 1
        assert records[0].iteration_num == 0

    def test_no_data_loss_on_repeated_crashes(self, tmp_path):
        """Verify no data loss even with repeated crash attempts"""
        history_file = tmp_path / 'test_history.jsonl'
        history = IterationHistory(str(history_file))

        # Write initial records
        for i in range(3):
            history.save(create_test_record(i, sharpe=1.0 + i * 0.1))

        # Simulate multiple crash attempts
        for _ in range(5):
            with patch('os.replace', side_effect=Exception("Crash")):
                try:
                    history.save(create_test_record(99, sharpe=9.9))
                except IOError:
                    pass

        # Verify original data still intact after multiple crashes
        records = history.get_all()
        assert len(records) == 3
        assert [r.iteration_num for r in records] == [0, 1, 2]

        # Verify all data correct
        for i, record in enumerate(records):
            assert record.metrics['sharpe_ratio'] == 1.0 + i * 0.1


class TestAtomicWritePerformance:
    """Test performance characteristics of atomic write"""

    def test_write_performance_under_10k_records(self, tmp_path):
        """Verify atomic write is acceptable for < 10k records

        According to spec, atomic write should be suitable for < 10,000 records.
        This test verifies the O(N) performance is acceptable.
        """
        history_file = tmp_path / 'performance_test.jsonl'
        history = IterationHistory(str(history_file))

        # Write 100 records (representative test)
        import time
        start = time.time()
        for i in range(100):
            history.save(create_test_record(i, sharpe=1.0))
        elapsed = time.time() - start

        # Should complete in reasonable time (< 10 seconds for 100 records)
        assert elapsed < 10.0, \
            f"Writing 100 records took {elapsed:.2f}s, should be < 10s"

        # Verify all records saved correctly
        records = history.get_all()
        assert len(records) == 100


class TestAtomicWriteEdgeCases:
    """Test edge cases for atomic write"""

    def test_empty_history_atomic_write(self, tmp_path):
        """Verify atomic write works on empty history file"""
        history_file = tmp_path / 'empty_test.jsonl'
        history = IterationHistory(str(history_file))

        # File doesn't exist yet
        assert not history_file.exists()

        # First write should create file atomically
        history.save(create_test_record(0, sharpe=1.0))

        # Verify file created and record saved
        assert history_file.exists()
        records = history.get_all()
        assert len(records) == 1

    def test_unicode_content_atomic_write(self, tmp_path):
        """Verify atomic write handles Unicode content correctly"""
        history_file = tmp_path / 'unicode_test.jsonl'
        history = IterationHistory(str(history_file))

        # Create record with Chinese characters
        record = IterationRecord(
            iteration_num=0,
            strategy_code="# 中文策略\ndata.get('price:收盤價')",
            execution_result={"success": True, "execution_time": 1.0},
            metrics={"sharpe_ratio": 1.5, "total_return": 0.2, "max_drawdown": -0.08},
            classification_level="LEVEL_3",
            timestamp=datetime.now().isoformat(),
            feedback_used="使用動量因子策略"
        )

        history.save(record)

        # Verify Unicode preserved
        loaded = history.get_all()
        assert len(loaded) == 1
        assert "中文策略" in loaded[0].strategy_code
        assert loaded[0].feedback_used == "使用動量因子策略"
