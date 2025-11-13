#!/bin/bash
# Phase 3 Learning System: Automated Task Development Script
# Usage: ./develop_phase3_task.sh <task_id>
# Example: ./develop_phase3_task.sh 1.3

set -e

WORK_DIR="/mnt/c/Users/jnpi/documents/finlab"
cd "$WORK_DIR"

TASK_ID="${1:-1.3}"

echo "=========================================="
echo "Phase 3 Task $TASK_ID Development"
echo "=========================================="
echo ""

case "$TASK_ID" in
    "1.3")
        echo "Task 1.3: Add history management tests"
        echo "Creating tests/learning/test_iteration_history.py..."

        cat > tests/learning/__init__.py << 'EOF'
"""Tests for Phase 3 Learning System components."""
EOF

        cat > tests/learning/test_iteration_history.py << 'EOF'
"""
Tests for IterationHistory and IterationRecord.

Test coverage:
- Normal save/load operations
- load_recent() with various N values
- File corruption handling
- Missing file handling
- Validation
- Forward compatibility
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

from src.learning.iteration_history import IterationHistory, IterationRecord


def create_test_record(iteration_num: int = 0, sharpe: float = 1.2) -> IterationRecord:
    """Helper to create valid test record."""
    return IterationRecord(
        iteration_num=iteration_num,
        strategy_code=f"# Strategy code for iteration {iteration_num}\ndata.get('price:收盤價')",
        execution_result={
            "success": True,
            "error_type": None,
            "execution_time": 5.2
        },
        metrics={
            "sharpe_ratio": sharpe,
            "total_return": 0.35,
            "max_drawdown": -0.12
        },
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat(),
        champion_updated=False,
        feedback_used="Previous iteration feedback"
    )


class TestIterationRecord:
    """Test IterationRecord validation and serialization."""

    def test_valid_record_creation(self):
        """Test creating valid record."""
        record = create_test_record()
        assert record.iteration_num == 0
        assert record.metrics["sharpe_ratio"] == 1.2

    def test_validation_rejects_negative_iteration(self):
        """Test validation rejects negative iteration number."""
        with pytest.raises(ValueError, match="iteration_num must be non-negative"):
            IterationRecord(
                iteration_num=-1,
                strategy_code="code",
                execution_result={},
                metrics={},
                classification_level="LEVEL_0",
                timestamp=datetime.now().isoformat()
            )

    def test_validation_rejects_empty_code(self):
        """Test validation rejects empty strategy code."""
        with pytest.raises(ValueError, match="strategy_code cannot be empty"):
            IterationRecord(
                iteration_num=0,
                strategy_code="   ",
                execution_result={},
                metrics={},
                classification_level="LEVEL_0",
                timestamp=datetime.now().isoformat()
            )

    def test_validation_rejects_invalid_level(self):
        """Test validation rejects invalid classification level."""
        with pytest.raises(ValueError, match="classification_level must be one of"):
            IterationRecord(
                iteration_num=0,
                strategy_code="code",
                execution_result={},
                metrics={},
                classification_level="INVALID_LEVEL",
                timestamp=datetime.now().isoformat()
            )

    def test_validation_rejects_invalid_timestamp(self):
        """Test validation rejects invalid timestamp format."""
        with pytest.raises(ValueError, match="timestamp must be valid ISO 8601"):
            IterationRecord(
                iteration_num=0,
                strategy_code="code",
                execution_result={},
                metrics={},
                classification_level="LEVEL_0",
                timestamp="not-a-date"
            )

    def test_to_dict_serialization(self):
        """Test record serialization to dict."""
        record = create_test_record(iteration_num=5)
        data = record.to_dict()
        assert data["iteration_num"] == 5
        assert isinstance(data, dict)

    def test_from_dict_deserialization(self):
        """Test record deserialization from dict."""
        data = create_test_record(iteration_num=3).to_dict()
        record = IterationRecord.from_dict(data)
        assert record.iteration_num == 3

    def test_forward_compatibility_ignores_unknown_fields(self):
        """Test forward compatibility ignores unknown fields."""
        data = create_test_record().to_dict()
        data["unknown_field"] = "some value"
        data["future_feature"] = 123

        # Should not raise error
        record = IterationRecord.from_dict(data)
        assert record.iteration_num == 0


class TestIterationHistory:
    """Test IterationHistory persistence operations."""

    def test_save_and_load_single_record(self, tmp_path):
        """Test saving and loading single record."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        record = create_test_record(iteration_num=0)
        history.save(record)

        loaded = history.load_recent(N=1)
        assert len(loaded) == 1
        assert loaded[0].iteration_num == 0

    def test_load_recent_with_N_equals_1(self, tmp_path):
        """Test load_recent with N=1."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        for i in range(5):
            history.save(create_test_record(iteration_num=i))

        recent = history.load_recent(N=1)
        assert len(recent) == 1
        assert recent[0].iteration_num == 4  # Most recent

    def test_load_recent_with_N_equals_5(self, tmp_path):
        """Test load_recent with N=5."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        for i in range(10):
            history.save(create_test_record(iteration_num=i))

        recent = history.load_recent(N=5)
        assert len(recent) == 5
        assert recent[0].iteration_num == 9  # Newest first
        assert recent[4].iteration_num == 5

    def test_load_recent_with_N_equals_10(self, tmp_path):
        """Test load_recent with N=10."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        for i in range(7):
            history.save(create_test_record(iteration_num=i))

        recent = history.load_recent(N=10)
        assert len(recent) == 7  # Only 7 available

    def test_missing_file_returns_empty(self, tmp_path):
        """Test missing history file returns empty list."""
        history_file = tmp_path / "nonexistent.jsonl"
        history = IterationHistory(str(history_file))

        recent = history.load_recent(N=5)
        assert recent == []

    def test_corrupted_json_skipped_with_warning(self, tmp_path, caplog):
        """Test corrupted JSON lines are skipped."""
        history_file = tmp_path / "corrupted.jsonl"

        # Write valid and corrupted records
        with open(history_file, "w") as f:
            f.write(json.dumps(create_test_record(0).to_dict()) + "\n")
            f.write("{invalid json\n")  # Corrupted
            f.write(json.dumps(create_test_record(2).to_dict()) + "\n")

        history = IterationHistory(str(history_file))
        recent = history.load_recent(N=10)

        assert len(recent) == 2  # Only valid records
        assert "Skipping corrupted line" in caplog.text

    def test_partial_json_corruption(self, tmp_path):
        """Test partial JSON is skipped."""
        history_file = tmp_path / "partial.jsonl"

        with open(history_file, "w") as f:
            f.write(json.dumps(create_test_record(0).to_dict()) + "\n")
            f.write('{"iteration_num": 1, "strategy_code"')  # Incomplete

        history = IterationHistory(str(history_file))
        recent = history.load_recent(N=10)

        assert len(recent) == 1  # Only complete record

    def test_empty_lines_ignored(self, tmp_path):
        """Test empty lines are ignored."""
        history_file = tmp_path / "empty_lines.jsonl"

        with open(history_file, "w") as f:
            f.write(json.dumps(create_test_record(0).to_dict()) + "\n")
            f.write("\n")  # Empty line
            f.write("   \n")  # Whitespace line
            f.write(json.dumps(create_test_record(1).to_dict()) + "\n")

        history = IterationHistory(str(history_file))
        recent = history.load_recent(N=10)

        assert len(recent) == 2

    def test_get_all_loads_entire_history(self, tmp_path):
        """Test get_all() loads all records."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        for i in range(10):
            history.save(create_test_record(iteration_num=i))

        all_records = history.get_all()
        assert len(all_records) == 10
        assert all_records[0].iteration_num == 0  # Oldest first
        assert all_records[9].iteration_num == 9

    def test_count_returns_correct_number(self, tmp_path):
        """Test count() returns correct number of records."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        assert history.count() == 0

        for i in range(7):
            history.save(create_test_record(iteration_num=i))

        assert history.count() == 7

    def test_get_last_iteration_num(self, tmp_path):
        """Test get_last_iteration_num() returns last iteration."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        assert history.get_last_iteration_num() is None

        history.save(create_test_record(iteration_num=0))
        assert history.get_last_iteration_num() == 0

        history.save(create_test_record(iteration_num=5))
        assert history.get_last_iteration_num() == 5

    def test_clear_removes_file(self, tmp_path):
        """Test clear() removes history file."""
        history_file = tmp_path / "test_history.jsonl"
        history = IterationHistory(str(history_file))

        history.save(create_test_record())
        assert history_file.exists()

        history.clear()
        assert not history_file.exists()

    def test_performance_with_1000_records(self, tmp_path):
        """Test performance with large history (1000+ records)."""
        import time

        history_file = tmp_path / "large_history.jsonl"
        history = IterationHistory(str(history_file))

        # Write 1000 records
        for i in range(1000):
            history.save(create_test_record(iteration_num=i))

        # Measure load_recent performance
        start = time.time()
        recent = history.load_recent(N=10)
        elapsed = time.time() - start

        assert len(recent) == 10
        assert elapsed < 1.0  # Should be fast (<1 second)
EOF

        echo "✅ Test file created"
        echo ""
        echo "Running pytest..."
        python3 -m pytest tests/learning/test_iteration_history.py -v --tb=short

        if [ $? -eq 0 ]; then
            echo ""
            echo "✅ Task 1.3 completed successfully!"
            echo "   - All tests passing"
            echo "   - 18 test cases implemented"
            echo "   - Coverage: save/load, corruption, validation, performance"
        else
            echo ""
            echo "❌ Some tests failed. Review output above."
            exit 1
        fi
        ;;

    *)
        echo "❌ Unknown task ID: $TASK_ID"
        echo "Available tasks: 1.3"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Development Complete"
echo "=========================================="
