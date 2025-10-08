"""
Failure Tracker Module

Tracks failed parameter configurations and generates learning directives
to avoid repeating unsuccessful changes.

This module implements dynamic failure pattern tracking that replaces static
AVOID lists in optimization prompts, enabling the system to learn from past
mistakes and accumulate optimization knowledge over time.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
from .constants import FAILURE_PATTERNS_FILE


@dataclass
class FailurePattern:
    """
    Represents a learned failure pattern from optimization history.

    Attributes:
        pattern_type: Category of failure (e.g., 'parameter_change')
        description: Human-readable explanation of what went wrong
        parameter: Name of the parameter that was changed
        change_from: Original value before the change
        change_to: New value that caused degradation
        performance_impact: Magnitude of performance drop (negative number)
        iteration_discovered: Which optimization iteration revealed this pattern
        timestamp: When this pattern was discovered (ISO format)
    """
    pattern_type: str
    description: str
    parameter: str
    change_from: Any
    change_to: Any
    performance_impact: float
    iteration_discovered: int
    timestamp: str

    def to_avoid_directive(self) -> str:
        """
        Convert this failure pattern to an AVOID directive string for prompts.

        Returns:
            Formatted string suitable for inclusion in optimization prompts
        """
        return f"Avoid: {self.description} (learned from iter {self.iteration_discovered})"


class FailureTracker:
    """
    Manages persistence and retrieval of failure patterns.

    Provides methods to:
    - Record new failure patterns from attribution analysis
    - Generate AVOID directives for optimization prompts
    - Persist patterns to JSON for accumulation across sessions
    - Detect duplicate patterns to avoid redundant learning
    """

    def __init__(self):
        """Initialize tracker and load existing patterns from disk."""
        self.patterns: List[FailurePattern] = self._load_patterns()

    def add_pattern(self, attribution: Dict[str, Any], iteration_num: int) -> None:
        """
        Add a new failure pattern if performance degraded.

        Examines attribution results for critical changes that coincided with
        performance degradation. Creates FailurePattern objects for each
        problematic change and persists them if not duplicates.

        Args:
            attribution: Dictionary containing:
                - critical_changes: List of parameter changes
                - performance_change: Float indicating improvement/degradation
            iteration_num: Current optimization iteration number
        """
        # Only track degraded performance
        performance_delta = attribution.get('performance_delta', 0.0)
        if performance_delta >= 0:
            # Performance improved or stayed same - not a failure
            return

        critical_changes = attribution.get('critical_changes', [])

        for change in critical_changes:
            # Generate human-readable description
            description = self._generate_description(change)

            # Create new failure pattern
            new_pattern = FailurePattern(
                pattern_type='parameter_change',
                description=description,
                parameter=change['parameter'],
                change_from=change['from'],
                change_to=change['to'],
                performance_impact=performance_delta,
                iteration_discovered=iteration_num,
                timestamp=datetime.now().isoformat()
            )

            # Check for duplicates before adding
            if not self._is_duplicate(new_pattern):
                self.patterns.append(new_pattern)

        # Persist to disk if any new patterns were added
        if critical_changes:
            self._save_patterns()

    def get_avoid_directives(self, max_patterns: int = 20) -> List[str]:
        """Generate list of AVOID directives for optimization prompts with pruning.

        Returns the most recent failure patterns to prevent unbounded growth
        in memory usage and prompt token consumption. Older patterns are excluded
        but remain in storage for potential future analysis.

        Args:
            max_patterns: Maximum number of patterns to return (default 20).
                         This limits prompt bloat while retaining recent learnings.

        Returns:
            List of formatted strings describing what to avoid,
            ordered by recency (most recent failures first),
            limited to max_patterns entries
        """
        # Sort by iteration number (descending) to prioritize recent learnings
        sorted_patterns = sorted(
            self.patterns,
            key=lambda p: p.iteration_discovered,
            reverse=True
        )

        # Return only the most recent max_patterns patterns
        recent_patterns = sorted_patterns[:max_patterns]

        return [pattern.to_avoid_directive() for pattern in recent_patterns]

    def _generate_description(self, change: Dict[str, str]) -> str:
        """
        Generate human-readable description of a parameter change.

        Provides intelligent descriptions for common parameter types with
        contextual information about what the change means.

        Args:
            change: Dictionary with 'parameter', 'from', 'to' keys

        Returns:
            Human-readable description of the problematic change
        """
        param = change['parameter']
        old_value = change['from']
        new_value = change['to']

        # Generate contextual descriptions for known parameters
        if 'roe_type' in param.lower():
            return f"Changing ROE type from '{old_value}' to '{new_value}'"

        elif 'liquidity_threshold' in param.lower():
            try:
                direction = "Increasing" if float(new_value) > float(old_value) else "Decreasing"
            except (ValueError, TypeError):
                direction = "Changing"
            return f"{direction} liquidity threshold from {old_value} to {new_value}"

        elif 'smoothing_window' in param.lower():
            try:
                direction = "Increasing" if int(new_value) > int(old_value) else "Decreasing"
            except (ValueError, TypeError):
                direction = "Changing"
            return f"{direction} smoothing window from {old_value} to {new_value} periods"

        elif 'weight' in param.lower():
            try:
                direction = "Increasing" if float(new_value) > float(old_value) else "Decreasing"
            except (ValueError, TypeError):
                direction = "Changing"
            return f"{direction} {param} from {old_value} to {new_value}"

        elif 'threshold' in param.lower():
            try:
                direction = "Raising" if float(new_value) > float(old_value) else "Lowering"
            except (ValueError, TypeError):
                direction = "Changing"
            return f"{direction} {param} from {old_value} to {new_value}"

        else:
            # Generic description for unknown parameters
            return f"Changing {param} from {old_value} to {new_value}"

    def _is_duplicate(self, new_pattern: FailurePattern) -> bool:
        """
        Check if a pattern already exists in the tracker.

        A pattern is considered duplicate if another pattern exists with:
        - Same parameter name
        - Same change_from value
        - Same change_to value

        Args:
            new_pattern: FailurePattern to check for duplicates

        Returns:
            True if duplicate exists, False otherwise
        """
        for existing in self.patterns:
            if (existing.parameter == new_pattern.parameter and
                str(existing.change_from) == str(new_pattern.change_from) and
                str(existing.change_to) == str(new_pattern.change_to)):
                return True
        return False

    def _save_patterns(self) -> None:
        """Persist all patterns to JSON file with atomic write.

        Uses tempfile + atomic rename to prevent corruption from concurrent access.
        Saves patterns in human-readable format with proper indentation.
        Creates parent directory if it doesn't exist.
        """
        import tempfile

        # Ensure directory exists (only if path includes directory)
        dir_path = os.path.dirname(FAILURE_PATTERNS_FILE)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

        # Convert patterns to dictionaries for JSON serialization
        patterns_data = [asdict(pattern) for pattern in self.patterns]

        # Write to temporary file first
        temp_fd, temp_path = tempfile.mkstemp(
            dir=dir_path or '.',
            prefix='.failure_patterns_',
            suffix='.tmp'
        )

        try:
            # Write patterns data to temp file
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(patterns_data, f, indent=2)

            # Atomic rename - POSIX guarantees atomicity
            os.replace(temp_path, FAILURE_PATTERNS_FILE)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise RuntimeError(f"Failed to save failure patterns: {e}")

    def _load_patterns(self) -> List[FailurePattern]:
        """
        Load patterns from JSON file.

        Returns:
            List of FailurePattern objects loaded from disk,
            or empty list if file doesn't exist or is corrupted
        """
        if not os.path.exists(FAILURE_PATTERNS_FILE):
            return []

        try:
            with open(FAILURE_PATTERNS_FILE, 'r') as f:
                patterns_data = json.load(f)

            # Convert dictionaries back to FailurePattern objects
            return [FailurePattern(**data) for data in patterns_data]

        except (json.JSONDecodeError, TypeError, KeyError) as e:
            # Handle corrupted JSON or invalid data structure
            print(f"Warning: Could not load failure patterns: {e}")
            print(f"Starting with empty pattern list")
            return []
