"""
Configuration snapshot module for experiment tracking.

This module provides ExperimentConfig dataclass for capturing
configuration state at each iteration of autonomous learning.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class ExperimentConfig:
    """Captures configuration state for a single experiment iteration.

    This class stores a snapshot of the configuration used for an iteration,
    enabling reproducibility and configuration tracking across experiments.

    Attributes:
        iteration: Iteration number (0-indexed)
        config_snapshot: Dictionary containing all configuration parameters
        timestamp: Optional ISO format timestamp of when config was captured

    Examples:
        >>> config = ExperimentConfig(
        ...     iteration=0,
        ...     config_snapshot={'lr': 0.01, 'batch_size': 32},
        ...     timestamp='2025-11-02T08:00:00'
        ... )
        >>> config.iteration
        0
        >>> config_dict = config.to_dict()
        >>> restored = ExperimentConfig.from_dict(config_dict)
        >>> restored == config
        True
    """

    iteration: int
    config_snapshot: Dict[str, Any]
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ExperimentConfig':
        """Create ExperimentConfig from dictionary.

        Args:
            config_dict: Dictionary with 'iteration', 'config_snapshot',
                        and optional 'timestamp' keys

        Returns:
            ExperimentConfig instance

        Examples:
            >>> data = {
            ...     'iteration': 5,
            ...     'config_snapshot': {'param': 'value'},
            ...     'timestamp': '2025-11-02T08:00:00'
            ... }
            >>> config = ExperimentConfig.from_dict(data)
        """
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExperimentConfig to dictionary.

        Returns:
            Dictionary representation with all fields

        Examples:
            >>> config = ExperimentConfig(0, {'lr': 0.01})
            >>> config.to_dict()
            {'iteration': 0, 'config_snapshot': {'lr': 0.01}, 'timestamp': None}
        """
        return asdict(self)
