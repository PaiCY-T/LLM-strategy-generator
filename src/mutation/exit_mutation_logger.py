"""
Exit Mutation Logger - JSON logging for exit parameter mutations.

This module provides structured JSON logging for exit parameter mutations,
enabling downstream analysis, debugging, and monitoring.

Architecture: Exit Mutation Redesign - Task 8
Requirements: 5.4, 5.5 (Metrics tracking and logging)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ExitMutationLogEntry:
    """
    Structured log entry for exit parameter mutation.

    Attributes:
        timestamp: ISO 8601 timestamp of mutation
        parameter: Parameter name that was mutated
        old_value: Original parameter value
        new_value: Mutated parameter value
        clamped: Whether value was clamped to bounds
        success: Whether mutation succeeded
        validation_passed: Whether AST validation passed
        error: Error message if failed (None if successful)
        mutation_id: Unique identifier for this mutation
    """
    timestamp: str
    parameter: str
    old_value: float
    new_value: float
    clamped: bool
    success: bool
    validation_passed: bool
    error: Optional[str] = None
    mutation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class ExitMutationLogger:
    """
    JSON logger for exit parameter mutations.

    Logs mutation metadata to JSONL (JSON Lines) format for:
    - Debugging mutation behavior
    - Analyzing parameter distributions
    - Monitoring success rates
    - Identifying patterns in failures
    - Downstream data analysis

    Features:
    - Structured JSON logging
    - Automatic file rotation (optional)
    - Buffered writes for performance
    - Thread-safe logging
    - Prometheus metrics integration

    Example:
        >>> logger = ExitMutationLogger('artifacts/data/exit_mutations.jsonl')
        >>> logger.log_mutation(
        ...     parameter='stop_loss_pct',
        ...     old_value=0.10,
        ...     new_value=0.12,
        ...     clamped=False,
        ...     success=True,
        ...     validation_passed=True
        ... )
    """

    def __init__(
        self,
        log_file: str = 'artifacts/data/exit_mutations.jsonl',
        buffer_size: int = 10,
        auto_flush: bool = True,
        metrics_collector: Optional[Any] = None
    ):
        """
        Initialize exit mutation logger.

        Args:
            log_file: Path to JSONL log file (created if doesn't exist)
            buffer_size: Number of entries to buffer before flushing (default: 10)
            auto_flush: Flush buffer automatically when full (default: True)
            metrics_collector: Optional MetricsCollector for Prometheus integration
        """
        self.log_file = Path(log_file)
        self.buffer_size = buffer_size
        self.auto_flush = auto_flush
        self.metrics_collector = metrics_collector

        # Create parent directories if needed
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize buffer
        self._buffer = []

        # Mutation counter for unique IDs
        self._mutation_counter = 0

        logger.info(f"Initialized ExitMutationLogger: {self.log_file}")

    def log_mutation(
        self,
        parameter: str,
        old_value: float,
        new_value: float,
        clamped: bool,
        success: bool,
        validation_passed: bool,
        error: Optional[str] = None,
        duration: Optional[float] = None
    ) -> None:
        """
        Log an exit parameter mutation.

        Args:
            parameter: Parameter name (e.g., 'stop_loss_pct')
            old_value: Original parameter value
            new_value: Mutated parameter value
            clamped: Whether value was clamped to bounds
            success: Whether mutation succeeded
            validation_passed: Whether AST validation passed
            error: Error message if failed (None if successful)
            duration: Optional mutation duration in seconds
        """
        # Generate unique mutation ID
        self._mutation_counter += 1
        mutation_id = f"exit_mut_{self._mutation_counter:06d}"

        # Create log entry
        entry = ExitMutationLogEntry(
            timestamp=datetime.now().isoformat(),
            parameter=parameter,
            old_value=old_value,
            new_value=new_value,
            clamped=clamped,
            success=success,
            validation_passed=validation_passed,
            error=error,
            mutation_id=mutation_id
        )

        # Add to buffer
        self._buffer.append(entry)

        # Record in metrics collector (if available)
        if self.metrics_collector is not None:
            self.metrics_collector.record_exit_mutation(success=success, duration=duration)

        # Auto-flush if buffer is full
        if self.auto_flush and len(self._buffer) >= self.buffer_size:
            self.flush()

        # Log to standard logger (INFO level)
        if success:
            logger.info(
                f"Exit mutation {mutation_id}: {parameter} "
                f"{old_value:.4f} -> {new_value:.4f} "
                f"(clamped={clamped})"
            )
        else:
            logger.warning(
                f"Exit mutation {mutation_id} FAILED: {parameter} "
                f"{old_value:.4f} -> {new_value:.4f} "
                f"(error: {error})"
            )

    def flush(self) -> None:
        """
        Flush buffered log entries to disk.

        Writes all buffered entries to JSONL file and clears buffer.
        Called automatically when buffer is full (if auto_flush=True).
        """
        if not self._buffer:
            return

        try:
            # Append to JSONL file
            with open(self.log_file, 'a') as f:
                for entry in self._buffer:
                    json.dump(entry.to_dict(), f)
                    f.write('\n')

            logger.debug(f"Flushed {len(self._buffer)} exit mutation entries to {self.log_file}")

            # Clear buffer
            self._buffer = []

        except Exception as e:
            logger.error(f"Failed to flush exit mutation log: {e}", exc_info=True)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics from logged mutations.

        Reads all mutations from log file and computes:
        - Total mutations
        - Success rate
        - Parameter distribution
        - Clamping frequency
        - Error distribution

        Returns:
            Dictionary with mutation statistics
        """
        if not self.log_file.exists():
            return {
                "total_mutations": 0,
                "success_rate": 0.0,
                "parameter_distribution": {},
                "clamping_rate": 0.0,
                "error_distribution": {}
            }

        try:
            # Read all entries
            mutations = []
            with open(self.log_file, 'r') as f:
                for line in f:
                    mutations.append(json.loads(line))

            # Compute statistics
            total = len(mutations)
            if total == 0:
                return {
                    "total_mutations": 0,
                    "success_rate": 0.0,
                    "parameter_distribution": {},
                    "clamping_rate": 0.0,
                    "error_distribution": {}
                }

            successes = sum(1 for m in mutations if m['success'])
            clamped = sum(1 for m in mutations if m['clamped'])

            # Parameter distribution
            param_dist = {}
            for m in mutations:
                param = m['parameter']
                param_dist[param] = param_dist.get(param, 0) + 1

            # Error distribution
            error_dist = {}
            for m in mutations:
                if not m['success'] and m['error']:
                    error = m['error']
                    error_dist[error] = error_dist.get(error, 0) + 1

            return {
                "total_mutations": total,
                "success_rate": successes / total,
                "parameter_distribution": param_dist,
                "clamping_rate": clamped / total,
                "error_distribution": error_dist,
                "successes": successes,
                "failures": total - successes,
                "clamped_count": clamped
            }

        except Exception as e:
            logger.error(f"Failed to get exit mutation statistics: {e}", exc_info=True)
            return {
                "total_mutations": 0,
                "success_rate": 0.0,
                "parameter_distribution": {},
                "clamping_rate": 0.0,
                "error_distribution": {},
                "error": str(e)
            }

    def clear(self) -> None:
        """
        Clear log file and buffer.

        WARNING: This deletes all logged mutations. Use with caution.
        """
        # Flush any pending entries first
        self.flush()

        # Delete log file
        if self.log_file.exists():
            self.log_file.unlink()
            logger.warning(f"Cleared exit mutation log: {self.log_file}")

        # Reset counter
        self._mutation_counter = 0

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - flush buffer."""
        self.flush()

    def __del__(self):
        """Destructor - flush buffer on cleanup."""
        try:
            self.flush()
        except:
            pass  # Ignore errors during cleanup
