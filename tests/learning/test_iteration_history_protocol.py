"""Protocol Integration Tests for IterationHistory.

**TDD Phase: 5B.3.1 - RED (Write Failing Tests)**

Tests that IterationHistory conforms to IIterationHistory Protocol with
behavioral contract enforcement.

Test Categories:
1. Protocol Conformance - isinstance() checks
2. Method Signatures - Type hints match Protocol
3. Behavioral Contracts - Idempotency, atomicity, return guarantees
4. Edge Cases - Empty files, corrupted data, concurrent access

Expected Status: FAIL (IterationHistory doesn't match Protocol yet)

After 5B.3.2 GREEN phase: All tests should PASS
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List

from src.learning.interfaces import IIterationHistory
from src.learning.iteration_history import IterationHistory, IterationRecord


class TestIterationHistoryProtocolConformance:
    """Test that IterationHistory satisfies IIterationHistory Protocol."""

    def test_protocol_conformance_runtime_check(self):
        """Test runtime isinstance() check with Protocol.

        Behavioral Contract:
        - IterationHistory must be recognized as IIterationHistory instance
        - Uses @runtime_checkable decorator for structural subtyping
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # RED: This will FAIL until we add proper type hints
            assert isinstance(history, IIterationHistory), (
                "IterationHistory must satisfy IIterationHistory Protocol "
                "with @runtime_checkable"
            )
        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_method_signatures_match_protocol(self):
        """Test that method signatures match Protocol exactly.

        Required Methods:
        - save(record: Any) -> None
        - get_all() -> List[Any]
        - load_recent(N: int = 5) -> List[Any]
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Check method existence
            assert hasattr(history, 'save'), "Missing .save() method"
            assert hasattr(history, 'get_all'), "Missing .get_all() method"
            assert hasattr(history, 'load_recent'), "Missing .load_recent() method"

            # Check method signatures via type hints
            import inspect

            # .save() signature
            save_sig = inspect.signature(history.save)
            assert 'record' in save_sig.parameters, ".save() must have 'record' parameter"
            assert save_sig.return_annotation in (None, inspect.Signature.empty, type(None)), (
                ".save() must return None"
            )

            # .get_all() signature
            get_all_sig = inspect.signature(history.get_all)
            assert get_all_sig.return_annotation != inspect.Signature.empty, (
                ".get_all() must have return type hint"
            )

            # .load_recent() signature
            load_recent_sig = inspect.signature(history.load_recent)
            assert 'N' in load_recent_sig.parameters, ".load_recent() must have 'N' parameter"
            assert load_recent_sig.parameters['N'].default == 5, (
                ".load_recent(N=5) must have default value"
            )

        finally:
            Path(filepath).unlink(missing_ok=True)


class TestIterationHistoryBehavioralContracts:
    """Test behavioral contracts specified in IIterationHistory Protocol."""

    def test_save_idempotency(self):
        """Test that .save() is idempotent (saving same record twice is safe).

        Behavioral Contract from IIterationHistory.save():
        - MUST be idempotent: saving same record twice is safe (no duplicates)
        - MUST preserve record.iteration_num as unique key

        Expected Behavior:
        - Save record with iteration_num=0 twice
        - get_all() should return only ONE record (not two)
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Create test record
            record = IterationRecord(
                iteration_num=0,
                generation_method="llm",
                strategy_code="test_code",
                execution_result={"success": True},
                metrics={"sharpe_ratio": 1.5},
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            )

            # Save twice (idempotency test)
            history.save(record)
            history.save(record)

            # RED: This will FAIL - current implementation appends duplicate
            all_records = history.get_all()
            assert len(all_records) == 1, (
                f"Expected 1 record (idempotent save), got {len(all_records)}. "
                "IIterationHistory.save() MUST be idempotent (no duplicates)."
            )

            assert all_records[0].iteration_num == 0, "Record iteration_num mismatch"

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_save_atomic_write_protection(self):
        """Test that .save() uses atomic write mechanism.

        Behavioral Contract from IIterationHistory.save():
        - MUST use atomic write mechanism (temp file + os.replace())
        - File never left in corrupted state (atomic write)

        Test Strategy:
        - Save valid record (should succeed)
        - Verify file exists and is readable
        - Verify atomic write left no temp files
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            record = IterationRecord(
                iteration_num=0,
                generation_method="llm",
                strategy_code="test_code",
                execution_result={"success": True},
                metrics={"sharpe_ratio": 1.5},
                classification_level="LEVEL_3",
                timestamp=datetime.now().isoformat()
            )

            # Save record
            history.save(record)

            # Verify file exists and is readable
            assert Path(filepath).exists(), "History file must exist after save"

            # Verify no temp files left behind (.tmp files)
            parent_dir = Path(filepath).parent
            temp_files = list(parent_dir.glob("*.tmp"))
            assert len(temp_files) == 0, (
                f"Atomic write must clean up temp files, found: {temp_files}"
            )

            # Verify file is valid JSONL
            loaded_records = history.get_all()
            assert len(loaded_records) == 1, "File must be valid after atomic write"

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_get_all_returns_empty_list_not_none(self):
        """Test that .get_all() returns empty list (never None).

        Behavioral Contract from IIterationHistory.get_all():
        - MUST return empty list if no records exist (never None)
        - len(returned_list) >= 0 (never raises for empty file)
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Get all from empty file
            result = history.get_all()

            # RED: This should already PASS (current implementation returns [])
            assert result is not None, ".get_all() must never return None"
            assert isinstance(result, list), ".get_all() must return list"
            assert len(result) == 0, "Empty file should return empty list"

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_get_all_returns_ordered_by_iteration_num(self):
        """Test that .get_all() returns records ordered by iteration_num ascending.

        Behavioral Contract from IIterationHistory.get_all():
        - MUST return records ordered by iteration_num ascending
        - records[i].iteration_num <= records[i+1].iteration_num
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Save records in random order (2, 0, 1)
            for iteration_num in [2, 0, 1]:
                record = IterationRecord(
                    iteration_num=iteration_num,
                    generation_method="llm",
                    strategy_code=f"code_{iteration_num}",
                    execution_result={"success": True},
                    metrics={"sharpe_ratio": 1.0 + iteration_num * 0.1},
                    classification_level="LEVEL_3",
                    timestamp=datetime.now().isoformat()
                )
                history.save(record)

            # Get all (should be ordered)
            all_records = history.get_all()

            # RED: This might FAIL if current implementation doesn't sort
            # But also might PASS if idempotency check above fails (duplicates)
            assert len(all_records) == 3, f"Expected 3 records, got {len(all_records)}"

            # Check ordering
            iteration_nums = [r.iteration_num for r in all_records]
            assert iteration_nums == [0, 1, 2], (
                f"Records must be ordered by iteration_num ascending, got {iteration_nums}"
            )

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_load_recent_returns_empty_list_not_none(self):
        """Test that .load_recent() returns empty list (never None).

        Behavioral Contract from IIterationHistory.load_recent():
        - MUST return empty list if no records exist (never None)
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Load recent from empty file
            result = history.load_recent(N=5)

            # This should already PASS (current implementation returns [])
            assert result is not None, ".load_recent() must never return None"
            assert isinstance(result, list), ".load_recent() must return list"
            assert len(result) == 0, "Empty file should return empty list"

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_load_recent_returns_newest_first(self):
        """Test that .load_recent() returns newest records first (descending).

        Behavioral Contract from IIterationHistory.load_recent():
        - MUST return last N iterations ordered newest first (descending)
        - If len(returned_list) > 0, records[0] is most recent iteration
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Save 5 records (0, 1, 2, 3, 4)
            for iteration_num in range(5):
                record = IterationRecord(
                    iteration_num=iteration_num,
                    generation_method="llm",
                    strategy_code=f"code_{iteration_num}",
                    execution_result={"success": True},
                    metrics={"sharpe_ratio": 1.0 + iteration_num * 0.1},
                    classification_level="LEVEL_3",
                    timestamp=datetime.now().isoformat()
                )
                history.save(record)

            # Load recent 3
            recent = history.load_recent(N=3)

            # RED: This might FAIL if idempotency check fails (duplicates)
            assert len(recent) == 3, f"Expected 3 records, got {len(recent)}"

            # Check newest first (descending: 4, 3, 2)
            iteration_nums = [r.iteration_num for r in recent]
            assert iteration_nums == [4, 3, 2], (
                f"load_recent() must return newest first (descending), got {iteration_nums}"
            )

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_load_recent_handles_n_greater_than_total(self):
        """Test that .load_recent(N) returns fewer than N if total < N.

        Behavioral Contract from IIterationHistory.load_recent():
        - MUST return fewer than N if total records < N (never raises)
        - len(returned_list) <= N
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            history = IterationHistory(filepath=filepath)

            # Save only 2 records
            for iteration_num in range(2):
                record = IterationRecord(
                    iteration_num=iteration_num,
                    generation_method="llm",
                    strategy_code=f"code_{iteration_num}",
                    execution_result={"success": True},
                    metrics={"sharpe_ratio": 1.5},
                    classification_level="LEVEL_3",
                    timestamp=datetime.now().isoformat()
                )
                history.save(record)

            # Request 5 (more than available)
            recent = history.load_recent(N=5)

            # Should return only 2 (what's available)
            assert len(recent) <= 5, "Must return <= N records"
            assert len(recent) == 2, f"Should return all 2 available records, got {len(recent)}"

        finally:
            Path(filepath).unlink(missing_ok=True)


class TestIterationHistoryEdgeCases:
    """Test edge cases and error handling."""

    def test_save_skips_corrupted_lines_on_read(self):
        """Test that corrupted lines are skipped with warning log.

        Behavioral Contract from IIterationHistory.get_all():
        - MUST skip corrupted lines (log warning)
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            filepath = f.name

        try:
            # Write corrupted JSONL manually
            with open(filepath, 'w', encoding='utf-8') as f:
                # Valid record
                f.write('{"iteration_num": 0, "generation_method": "llm", "strategy_code": "code", "execution_result": {}, "metrics": {"sharpe_ratio": 1.0}, "classification_level": "LEVEL_3", "timestamp": "2025-11-03T12:00:00"}\n')
                # Corrupted line (invalid JSON)
                f.write('{"iteration_num": 1, "broken json\n')
                # Valid record
                f.write('{"iteration_num": 2, "generation_method": "llm", "strategy_code": "code", "execution_result": {}, "metrics": {"sharpe_ratio": 1.0}, "classification_level": "LEVEL_3", "timestamp": "2025-11-03T12:00:00"}\n')

            history = IterationHistory(filepath=filepath)

            # get_all() should skip corrupted line
            all_records = history.get_all()

            # Should return 2 valid records (skip corrupted)
            assert len(all_records) == 2, (
                f"Should skip corrupted lines, got {len(all_records)} records"
            )
            assert all_records[0].iteration_num == 0
            assert all_records[1].iteration_num == 2  # Skip iteration_num=1 (corrupted)

        finally:
            Path(filepath).unlink(missing_ok=True)

    def test_nonexistent_file_returns_empty_list(self):
        """Test that non-existent file returns empty list (never raises).

        Behavioral Contract:
        - get_all() and load_recent() must handle missing file gracefully
        """
        filepath = "/tmp/nonexistent_history_file_12345.jsonl"

        # Ensure file doesn't exist
        Path(filepath).unlink(missing_ok=True)

        history = IterationHistory(filepath=filepath)

        # Should not raise, return empty list
        all_records = history.get_all()
        assert all_records == [], "Non-existent file should return empty list"

        recent = history.load_recent(N=5)
        assert recent == [], "Non-existent file should return empty list"


class TestIterationHistoryRuntimeValidation:
    """Test runtime validation in LearningLoop.__init__().

    This test will be added in 5B.3.2 GREEN phase when we update LearningLoop.
    """

    def test_learning_loop_validates_iteration_history_protocol(self):
        """Test that LearningLoop validates IIterationHistory at runtime.

        Expected in 5B.3.2 GREEN:
        - LearningLoop.__init__() should call isinstance(history, IIterationHistory)
        - Should raise TypeError if validation fails

        This test is a placeholder - will be implemented in 5B.3.2.
        """
        pytest.skip("Will be implemented in 5B.3.2 GREEN phase")
