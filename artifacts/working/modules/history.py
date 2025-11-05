"""Iteration history tracking for autonomous learning loop.

Maintains a history of all generated strategies with their validation results,
execution outcomes, and extracted metrics. Enables learning from past iterations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from datetime import datetime
from pathlib import Path


@dataclass
class IterationRecord:
    """Record of a single strategy generation iteration."""

    iteration_num: int
    timestamp: str
    model: str
    code: str

    # Validation results
    validation_passed: bool
    validation_errors: List[str]

    # Execution results
    execution_success: bool
    execution_error: Optional[str]
    metrics: Optional[Dict[str, Any]]

    # Feedback for next iteration
    feedback: str

    # Data provenance tracking
    data_checksum: Optional[str] = None
    data_version: Optional[Dict[str, str]] = None

    # Experiment configuration tracking
    config_snapshot: Optional[Dict[str, Any]] = None

    # Template mode tracking (Phase 0: Task 2.4)
    mode: Optional[str] = None  # 'template' or 'freeform' (None for backward compatibility)
    parameters: Optional[Dict[str, Any]] = None  # Template parameters if mode='template'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IterationRecord':
        """Create from dictionary."""
        return cls(**data)


class IterationHistory:
    """Manages iteration history and learning feedback."""

    def __init__(self, history_file: str = "iteration_history.json"):
        """Initialize history manager.

        Args:
            history_file: Path to JSON file for persisting history
        """
        self.history_file = Path(history_file)
        self.records: List[IterationRecord] = []

        # Load existing history if available
        if self.history_file.exists():
            self.load()

    def add_record(
        self,
        iteration_num: int,
        model: str,
        code: str,
        validation_passed: bool,
        validation_errors: List[str],
        execution_success: bool,
        execution_error: Optional[str],
        metrics: Optional[Dict[str, Any]],
        feedback: str,
        data_checksum: Optional[str] = None,
        data_version: Optional[Dict[str, str]] = None,
        config_snapshot: Optional[Dict[str, Any]] = None,
        mode: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> IterationRecord:
        """Add a new iteration record.

        Args:
            iteration_num: Iteration number (0-indexed)
            model: Model name used for generation
            code: Generated strategy code
            validation_passed: Whether AST validation passed
            validation_errors: List of validation error messages
            execution_success: Whether execution succeeded
            execution_error: Execution error message if failed
            metrics: Extracted backtest metrics if successful
            feedback: Feedback summary for next iteration
            data_checksum: Dataset checksum for data provenance tracking
            data_version: Data version metadata (finlab_version, timestamp, row_counts)
            config_snapshot: Experiment configuration snapshot (ExperimentConfig.to_dict())
            mode: Execution mode ('template' or 'freeform', None for backward compatibility)
            parameters: Template parameters if mode='template'

        Returns:
            Created IterationRecord
        """
        record = IterationRecord(
            iteration_num=iteration_num,
            timestamp=datetime.utcnow().isoformat(),
            model=model,
            code=code,
            validation_passed=validation_passed,
            validation_errors=validation_errors,
            execution_success=execution_success,
            execution_error=execution_error,
            metrics=metrics,
            feedback=feedback,
            data_checksum=data_checksum,
            data_version=data_version,
            config_snapshot=config_snapshot,
            mode=mode,
            parameters=parameters
        )

        self.records.append(record)
        self.save()

        return record

    def get_record(self, iteration_num: int) -> Optional[IterationRecord]:
        """Get record by iteration number.

        Args:
            iteration_num: Iteration number to retrieve

        Returns:
            IterationRecord if found, None otherwise
        """
        for record in self.records:
            if record.iteration_num == iteration_num:
                return record
        return None

    def get_latest(self) -> Optional[IterationRecord]:
        """Get the most recent iteration record.

        Returns:
            Latest IterationRecord if history exists, None otherwise
        """
        return self.records[-1] if self.records else None

    def get_successful_iterations(self) -> List[IterationRecord]:
        """Get all iterations that passed validation and execution.

        Returns:
            List of successful IterationRecords
        """
        return [
            record for record in self.records
            if record.validation_passed and record.execution_success
        ]

    def generate_feedback_summary(self) -> str:
        """Generate feedback summary from all iterations.

        Creates a concise summary of:
        - Total iterations attempted
        - Success/failure breakdown
        - Common validation errors
        - Execution patterns
        - Best performing strategies

        Returns:
            Formatted feedback summary string
        """
        if not self.records:
            return "No previous iterations."

        total = len(self.records)
        validated = sum(1 for r in self.records if r.validation_passed)
        executed = sum(1 for r in self.records if r.execution_success)

        summary = f"Previous iterations: {total}\n"
        summary += f"- Validated: {validated}/{total}\n"
        summary += f"- Executed successfully: {executed}/{total}\n"

        # Collect validation errors
        validation_errors = []
        for record in self.records:
            if not record.validation_passed:
                validation_errors.extend(record.validation_errors)

        if validation_errors:
            summary += f"\nCommon validation errors:\n"
            error_counts = {}
            for error in validation_errors:
                # Extract error type (e.g., "Import statement", "Negative shift")
                error_type = error.split(':')[1].strip() if ':' in error else error
                error_counts[error_type] = error_counts.get(error_type, 0) + 1

            for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1])[:3]:
                summary += f"- {error_type} ({count}x)\n"

        # Best performing strategy
        successful = self.get_successful_iterations()
        if successful and any(r.metrics for r in successful):
            # Sort by sharpe_ratio if available
            with_metrics = [r for r in successful if r.metrics]
            if with_metrics:
                best = max(
                    with_metrics,
                    key=lambda r: r.metrics.get('sharpe_ratio', 0) if r.metrics else 0
                )
                if best.metrics:
                    summary += f"\nBest strategy (iteration {best.iteration_num}):\n"
                    summary += f"- Sharpe: {best.metrics.get('sharpe_ratio', 'N/A')}\n"
                    summary += f"- Return: {best.metrics.get('total_return', 'N/A')}\n"

        return summary

    def save(self) -> None:
        """Persist history to JSON file."""
        data = {
            'records': [record.to_dict() for record in self.records]
        }

        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        """Load history from JSON file."""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.records = [
                IterationRecord.from_dict(record_data)
                for record_data in data.get('records', [])
            ]
        except Exception as e:
            print(f"Warning: Could not load history from {self.history_file}: {e}")
            self.records = []

    def clear(self) -> None:
        """Clear all history records."""
        self.records = []
        if self.history_file.exists():
            self.history_file.unlink()


def main():
    """Test iteration history tracking."""
    print("Testing iteration history tracking...\n")

    # Create history manager
    history = IterationHistory("test_history.json")
    history.clear()

    # Add test records
    print("Adding test iterations...")

    # Iteration 0 - Success
    history.add_record(
        iteration_num=0,
        model="gemini-2.5-flash",
        code="# Test strategy 0\nposition = close.is_largest(10)\nreport = sim(position)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.2, 'total_return': 0.15},
        feedback="Good initial strategy"
    )

    # Iteration 1 - Validation failed
    history.add_record(
        iteration_num=1,
        model="gemini-2.5-flash",
        code="import os\nposition = close.is_largest(10)",
        validation_passed=False,
        validation_errors=["Line 1: Import statement not allowed"],
        execution_success=False,
        execution_error=None,
        metrics=None,
        feedback="Remove import statement"
    )

    # Iteration 2 - Success with better metrics
    history.add_record(
        iteration_num=2,
        model="gemini-2.5-flash",
        code="# Test strategy 2\nposition = close.is_largest(10)\nreport = sim(position)",
        validation_passed=True,
        validation_errors=[],
        execution_success=True,
        execution_error=None,
        metrics={'sharpe_ratio': 1.5, 'total_return': 0.20},
        feedback="Improved performance"
    )

    print(f"✅ Added {len(history.records)} records\n")

    # Test retrieval
    print("Testing retrieval...")
    latest = history.get_latest()
    print(f"Latest iteration: {latest.iteration_num}")
    print(f"Validation passed: {latest.validation_passed}")
    print(f"Execution success: {latest.execution_success}\n")

    # Test feedback generation
    print("Feedback summary:")
    print("-" * 60)
    print(history.generate_feedback_summary())
    print("-" * 60)

    # Cleanup
    history.clear()
    print("\n✅ Test complete")


if __name__ == '__main__':
    main()
