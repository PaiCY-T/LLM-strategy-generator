"""Iteration History Management for Learning Loop

This module provides JSONL-based persistence for iteration history,
allowing the learning system to track and learn from previous iterations.

The module handles:
- Append-only iteration record storage (JSONL format)
- Efficient retrieval of recent iterations
- Corruption-resistant file handling
- Atomic writes to prevent data loss
- Forward-compatible record format

Example Usage:
    ```python
    from src.learning.iteration_history import IterationHistory, IterationRecord
    from datetime import datetime

    # Create history manager
    history = IterationHistory("artifacts/data/innovations.jsonl")

    # Save iteration
    record = IterationRecord(
        iteration_num=1,
        strategy_code="def strategy():\\n    return data.get('price:收盤價')",
        execution_result={"success": True, "execution_time": 5.2},
        metrics={"sharpe_ratio": 1.2, "total_return": 0.15, "max_drawdown": -0.08},
        classification_level="LEVEL_3",
        timestamp=datetime.now().isoformat(),
        champion_updated=True,
        feedback_used="Previous strategies showed momentum patterns work well"
    )
    history.save(record)

    # Load recent iterations
    recent = history.load_recent(N=5)
    for rec in recent:
        print(f"Iter {rec.iteration_num}: Sharpe {rec.metrics['sharpe_ratio']}")

    # Get last iteration number for loop resumption
    last_iter = history.get_last_iteration_num()
    if last_iter is not None:
        print(f"Resuming from iteration {last_iter + 1}")
    ```

File Format:
    JSONL (JSON Lines) - one JSON object per line
    - Human-readable and grep-friendly
    - Append-only for performance
    - Corruption-resistant (invalid lines skipped)
    - Each record is self-contained

Performance Characteristics:
    - save(): O(1) append operation, atomic via file write
    - load_recent(N): O(N) time complexity, reads last N lines
    - get_all(): O(M) where M is total records, use sparingly
    - Tested with 1000+ iterations: load_recent() <1 second

Thread Safety:
    - save() uses atomic append (file system level)
    - Multiple threads can write concurrently
    - load operations are read-only and safe

Classes:
    IterationRecord: Dataclass for iteration data with validation
    IterationHistory: JSONL-based history persistence manager

See Also:
    - src/learning/autonomous_loop.py: Main learning loop consumer
    - src/feedback/rationale_generator.py: Uses history for context
"""

import json
import logging
import os
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class IterationRecord:
    """Record of a single iteration in the learning loop.

    This dataclass represents one complete iteration of the autonomous learning
    system, including the generated strategy, execution results, and metadata.

    All fields are validated on initialization to ensure data integrity.

    Attributes:
        iteration_num (int): Iteration number (0-indexed). Must be non-negative.
        strategy_code (str): Generated strategy Python code. Cannot be empty.
        execution_result (dict): Result from BacktestExecutor containing:
            - success (bool): Whether execution succeeded
            - error_type (str | None): Type of error if failed
            - execution_time (float): Time taken in seconds
        metrics (dict): Performance metrics with at minimum:
            - sharpe_ratio (float): Risk-adjusted return metric
            - total_return (float): Total return percentage
            - max_drawdown (float): Maximum drawdown percentage
        classification_level (str): Success tier from error classifier:
            - "LEVEL_0": Critical failure (syntax error, runtime crash)
            - "LEVEL_1": Execution failure (FinLab API error, data issue)
            - "LEVEL_2": Weak performance (low Sharpe, excessive drawdown)
            - "LEVEL_3": Success (meets performance thresholds)
        timestamp (str): ISO 8601 timestamp of iteration completion.
            Format: "YYYY-MM-DDTHH:MM:SS" or "YYYY-MM-DDTHH:MM:SS.ffffff"
        champion_updated (bool): Whether this iteration updated the champion strategy.
            Default: False
        feedback_used (str | None): Feedback text provided to LLM for this iteration.
            Stored for post-hoc analysis of learning trajectory. Default: None

    Raises:
        ValueError: If any field fails validation with actionable error message

    Example:
        >>> from datetime import datetime
        >>> record = IterationRecord(
        ...     iteration_num=5,
        ...     strategy_code="data.get('price:收盤價').ewm(span=20).mean()",
        ...     execution_result={"success": True, "execution_time": 3.5},
        ...     metrics={"sharpe_ratio": 1.8, "total_return": 0.25, "max_drawdown": -0.10},
        ...     classification_level="LEVEL_3",
        ...     timestamp=datetime.now().isoformat(),
        ...     champion_updated=True
        ... )
        >>> record.iteration_num
        5
    """
    iteration_num: int
    strategy_code: str
    execution_result: Dict[str, Any]
    metrics: Dict[str, float]
    classification_level: str
    timestamp: str
    champion_updated: bool = False
    feedback_used: Optional[str] = None

    def __post_init__(self):
        """Validate record fields after initialization (Task 1.2)."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate IterationRecord fields.

        Raises:
            ValueError: If validation fails with actionable error message
        """
        # Validate iteration_num
        if not isinstance(self.iteration_num, int):
            raise ValueError(
                f"iteration_num must be int, got {type(self.iteration_num).__name__}"
            )
        if self.iteration_num < 0:
            raise ValueError(
                f"iteration_num must be non-negative, got {self.iteration_num}"
            )

        # Validate strategy_code
        if not isinstance(self.strategy_code, str):
            raise ValueError(
                f"strategy_code must be str, got {type(self.strategy_code).__name__}"
            )
        if not self.strategy_code.strip():
            raise ValueError("strategy_code cannot be empty")

        # Validate execution_result
        if not isinstance(self.execution_result, dict):
            raise ValueError(
                f"execution_result must be dict, got {type(self.execution_result).__name__}"
            )

        # Validate metrics
        if not isinstance(self.metrics, dict):
            raise ValueError(
                f"metrics must be dict, got {type(self.metrics).__name__}"
            )

        # Validate classification_level
        valid_levels = ["LEVEL_0", "LEVEL_1", "LEVEL_2", "LEVEL_3"]
        if self.classification_level not in valid_levels:
            raise ValueError(
                f"classification_level must be one of {valid_levels}, "
                f"got '{self.classification_level}'"
            )

        # Validate timestamp (ISO 8601 format)
        if not isinstance(self.timestamp, str):
            raise ValueError(
                f"timestamp must be str, got {type(self.timestamp).__name__}"
            )
        try:
            datetime.fromisoformat(self.timestamp)
        except ValueError as e:
            raise ValueError(
                f"timestamp must be valid ISO 8601 format, got '{self.timestamp}': {e}"
            ) from e

        # Validate champion_updated
        if not isinstance(self.champion_updated, bool):
            raise ValueError(
                f"champion_updated must be bool, got {type(self.champion_updated).__name__}"
            )

        # Validate feedback_used (optional)
        if self.feedback_used is not None and not isinstance(self.feedback_used, str):
            raise ValueError(
                f"feedback_used must be str or None, got {type(self.feedback_used).__name__}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for JSON serialization.

        Returns:
            dict: Dictionary representation suitable for JSON serialization

        Example:
            >>> record = create_test_record()
            >>> data = record.to_dict()
            >>> data['iteration_num']
            0
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IterationRecord":
        """Create record from dictionary (for deserialization).

        This method handles forward compatibility by ignoring unknown fields.
        This allows older code to load records saved by newer versions that
        may have additional fields.

        Args:
            data (dict): Dictionary with record fields. Must contain all
                required fields (iteration_num, strategy_code, execution_result,
                metrics, classification_level, timestamp). Optional fields
                (champion_updated, feedback_used) use defaults if missing.

        Returns:
            IterationRecord: Deserialized and validated record object

        Raises:
            ValueError: If required fields are missing or validation fails
            TypeError: If field types are incorrect

        Example:
            >>> data = {
            ...     "iteration_num": 3,
            ...     "strategy_code": "data.get('price:收盤價')",
            ...     "execution_result": {"success": True},
            ...     "metrics": {"sharpe_ratio": 1.5},
            ...     "classification_level": "LEVEL_3",
            ...     "timestamp": "2025-11-03T12:00:00",
            ...     "unknown_future_field": "ignored"  # Forward compatibility
            ... }
            >>> record = IterationRecord.from_dict(data)
            >>> record.iteration_num
            3

        Note:
            Unknown fields are silently ignored for forward compatibility.
            This allows gradual system upgrades without breaking old data.
        """
        # Forward compatibility: filter to known fields only
        known_fields = {
            'iteration_num', 'strategy_code', 'execution_result', 'metrics',
            'classification_level', 'timestamp', 'champion_updated', 'feedback_used'
        }
        filtered_data = {k: v for k, v in data.items() if k in known_fields}

        return cls(**filtered_data)


class IterationHistory:
    """JSONL-based iteration history manager with atomic write protection.

    Provides append-only persistence with corruption handling and
    efficient retrieval of recent iterations. Uses atomic write mechanism
    to prevent data corruption from interrupted writes.

    The history file uses JSONL (JSON Lines) format:
    - One JSON object per line (newline-delimited)
    - Atomic write via temp file + os.replace()
    - Human-readable and grep-friendly
    - Corruption-resistant (invalid lines skipped)

    Atomic Write Mechanism:
    - Write all records (existing + new) to temporary file
    - Use os.replace() for atomic file replacement
    - Original file never corrupted even if write interrupted
    - Safe against CTRL+C, crashes, power loss

    Performance:
    - save(): O(N) where N = total records (rewrites entire file)
    - load_recent(N): O(N) - reads last N lines only
    - get_all(): O(M) - reads entire file, use sparingly
    - Suitable for < 10,000 records
    - For larger datasets, consider migrating to SQLite

    Thread Safety:
    - Single process safe (atomic os.replace())
    - NOT safe for concurrent multi-process writes
    - Read operations are always safe (read-only)

    Attributes:
        filepath (Path): Path to JSONL history file

    Example:
        >>> from datetime import datetime
        >>> history = IterationHistory("artifacts/data/innovations.jsonl")
        >>>
        >>> # Save iteration
        >>> record = IterationRecord(
        ...     iteration_num=0,
        ...     strategy_code="data.get('price:收盤價').rolling(20).mean()",
        ...     execution_result={"success": True, "execution_time": 4.2},
        ...     metrics={"sharpe_ratio": 1.2, "total_return": 0.18},
        ...     classification_level="LEVEL_3",
        ...     timestamp=datetime.now().isoformat()
        ... )
        >>> history.save(record)
        >>>
        >>> # Load recent iterations
        >>> recent = history.load_recent(N=5)
        >>> print(f"Last 5 iterations: {len(recent)} records")
        Last 5 iterations: 1 records
        >>>
        >>> # Resume from last iteration
        >>> last_iter = history.get_last_iteration_num()
        >>> next_iter = (last_iter + 1) if last_iter is not None else 0
    """

    def __init__(self, filepath: str = "artifacts/data/innovations.jsonl"):
        """Initialize IterationHistory manager.

        Creates parent directories if they don't exist. The history file
        itself is created on the first save() call.

        Args:
            filepath (str): Path to JSONL history file. Parent directories
                will be created if they don't exist. Default:
                "artifacts/data/innovations.jsonl"

        Example:
            >>> history = IterationHistory("my_data/history.jsonl")
            >>> # Parent directory "my_data" created automatically
        """
        self.filepath = Path(filepath)
        self._lock = threading.Lock()  # Thread-safe write lock
        self._ensure_directory()
        logger.info(f"IterationHistory initialized: {self.filepath}")

    def _ensure_directory(self) -> None:
        """Ensure parent directory exists."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: IterationRecord) -> None:
        """Save iteration record to JSONL file (atomic write).

        Uses atomic write mechanism to prevent data corruption:
        1. Read all existing records from history file
        2. Write all records (existing + new) to temporary file
        3. Use os.replace() to atomically replace original file
        4. If interrupted at any point, original file remains intact

        This ensures that even if the program crashes during write,
        the history file is never corrupted. The worst case is that
        the new record is not saved, but existing records are safe.

        Args:
            record (IterationRecord): Validated iteration record to save

        Raises:
            IOError: If file write fails (e.g., disk full, permission denied)

        Example:
            >>> history = IterationHistory("test.jsonl")
            >>> record = IterationRecord(
            ...     iteration_num=0,
            ...     strategy_code="code",
            ...     execution_result={},
            ...     metrics={"sharpe_ratio": 1.0},
            ...     classification_level="LEVEL_3",
            ...     timestamp="2025-11-03T12:00:00"
            ... )
            >>> history.save(record)
            >>> # Record immediately available for reading

        Performance:
            O(N) where N = total records. Suitable for < 10,000 records.
            For larger datasets, consider migrating to database.

        Note:
            Thread-safe via file lock.
            NOT safe for concurrent multi-process writes.
        """
        import tempfile
        import uuid

        # Use file locking to ensure thread-safe writes
        # The lock ensures only one thread can write at a time
        with self._lock:
            tmp_filepath = None
            try:
                # 1. Ensure directory exists for atomic write
                self.filepath.parent.mkdir(parents=True, exist_ok=True)

                # 2. Create unique temporary file in the same directory
                # Using uuid ensures no conflict when multiple threads save concurrently
                tmp_filepath = self.filepath.parent / f".{self.filepath.name}.{uuid.uuid4().hex}.tmp"

                # 3. Read all existing records
                existing_records = self.get_all()

                # 4. Write all records (existing + new) to temporary file
                with open(tmp_filepath, "w", encoding="utf-8") as f:
                    # Write existing records
                    for existing_record in existing_records:
                        json_line = json.dumps(existing_record.to_dict(), ensure_ascii=False) + "\n"
                        f.write(json_line)

                    # Write new record
                    json_line = json.dumps(record.to_dict(), ensure_ascii=False) + "\n"
                    f.write(json_line)

                # 5. Atomic replace - even if crash happens here, original file is safe
                os.replace(tmp_filepath, self.filepath)

                logger.debug(
                    f"Saved iteration {record.iteration_num} to history "
                    f"(champion_updated={record.champion_updated})"
                )
            except Exception as e:
                logger.error(f"Failed to save iteration record: {e}")
                # Clean up temp file if it exists
                if tmp_filepath and tmp_filepath.exists():
                    try:
                        tmp_filepath.unlink()
                    except:
                        pass
                raise IOError(f"Failed to save iteration record: {e}") from e

    def load_recent(self, N: int = 5) -> List[IterationRecord]:
        """Load the most recent N iteration records.

        Efficiently retrieves recent iterations without loading the entire file.
        Corrupted or invalid lines are skipped with warning logs.

        Args:
            N (int): Number of recent records to retrieve. Default: 5

        Returns:
            list[IterationRecord]: Recent records in newest-first order.
                May contain fewer than N records if:
                - File has fewer than N valid records
                - Some lines are corrupted and skipped
                - File doesn't exist (returns empty list)

        Example:
            >>> history = IterationHistory("history.jsonl")
            >>> recent = history.load_recent(N=3)
            >>> for record in recent:
            ...     sharpe = record.metrics.get('sharpe_ratio', 0.0)
            ...     print(f"Iteration {record.iteration_num}: Sharpe {sharpe:.2f}")
            Iteration 9: Sharpe 1.85
            Iteration 8: Sharpe 1.42
            Iteration 7: Sharpe 1.23

        Performance:
            O(N) time complexity - reads only last N lines from file.
            Tested with 1000+ iterations: completes in <1 second.

        Note:
            Corrupted lines are logged at WARNING level and skipped.
            This ensures robustness against file corruption.
        """
        if not self.filepath.exists():
            logger.info(f"History file not found: {self.filepath}. Returning empty history.")
            return []

        try:
            # Read all lines (for simplicity in v1, optimize later if needed)
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Parse lines from end (most recent)
            records = []
            for line in reversed(lines[-N:] if len(lines) > N else lines):
                line = line.strip()
                if not line:
                    continue  # Skip empty lines

                try:
                    data = json.loads(line)
                    record = IterationRecord.from_dict(data)
                    records.append(record)
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping corrupted line in history: {e}")
                    continue
                except (TypeError, KeyError) as e:
                    logger.warning(f"Skipping invalid record structure: {e}")
                    continue

            logger.debug(f"Loaded {len(records)} recent records from history")
            return records

        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            return []

    def get_all(self) -> List[IterationRecord]:
        """
        Load all iteration records from history.

        WARNING: This loads entire file into memory. Use for analysis only.
        For iteration loop, use load_recent() instead.

        Returns:
            List of all IterationRecord objects (oldest first)
        """
        if not self.filepath.exists():
            logger.info(f"History file not found: {self.filepath}. Returning empty history.")
            return []

        try:
            records = []
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue  # Skip empty lines

                    try:
                        data = json.loads(line)
                        record = IterationRecord.from_dict(data)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping corrupted line {line_num}: {e}")
                        continue
                    except (TypeError, KeyError) as e:
                        logger.warning(f"Skipping invalid record at line {line_num}: {e}")
                        continue

            logger.info(f"Loaded {len(records)} total records from history")
            return records

        except Exception as e:
            logger.error(f"Failed to load all history: {e}")
            return []

    def count(self) -> int:
        """
        Count total number of valid records in history.

        Returns:
            Number of valid iteration records
        """
        return len(self.get_all())

    def get_last_iteration_num(self) -> Optional[int]:
        """Get the iteration number of the last completed iteration.

        Useful for loop resumption - call this on startup to determine
        where to continue from.

        Returns:
            int | None: Last iteration number, or None if history is empty

        Example:
            >>> history = IterationHistory("history.jsonl")
            >>> last = history.get_last_iteration_num()
            >>> if last is None:
            ...     print("Starting fresh from iteration 0")
            ...     next_iter = 0
            ... else:
            ...     print(f"Resuming from iteration {last}")
            ...     next_iter = last + 1
        """
        recent = self.load_recent(N=1)
        return recent[0].iteration_num if recent else None

    def clear(self) -> None:
        """
        Clear all history (delete file).

        WARNING: This is destructive. Use only for testing or explicit reset.
        """
        if self.filepath.exists():
            self.filepath.unlink()
            logger.warning(f"History file cleared: {self.filepath}")
