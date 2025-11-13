"""
Experiment Configuration Loader
================================

Loads and validates experiment configuration from YAML.
"""

from dataclasses import dataclass
from typing import Dict
from pathlib import Path
import yaml


@dataclass
class GroupConfig:
    """Configuration for a single experimental group."""
    name: str
    innovation_rate: float
    description: str

    def __post_init__(self):
        """Validate innovation_rate."""
        if not 0.0 <= self.innovation_rate <= 1.0:
            raise ValueError(f"innovation_rate must be in [0.0, 1.0], got {self.innovation_rate}")


@dataclass
class PhaseConfig:
    """Configuration for an experimental phase (Pilot or Full Study)."""
    iterations_per_run: int
    num_runs: int
    total_iterations: int
    description: str

    def __post_init__(self):
        """Validate totals.

        Note: Validation deferred to runtime when number of groups is known.
        For single-group experiments, total_iterations = iterations_per_run * num_runs * 1
        For multi-group experiments (A/B/C testing), multiply by number of groups
        """
        # Validation moved to ExperimentConfig.load() where number of groups is known
        pass


@dataclass
class NoveltyConfig:
    """Configuration for 3-layer novelty system."""
    weights: Dict[str, float]
    baseline_file: str
    template_dir: str

    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:  # Allow floating point tolerance
            raise ValueError(f"novelty weights must sum to 1.0, got {total}")


@dataclass
class ExperimentConfig:
    """Root experiment configuration."""
    name: str
    version: str
    description: str
    groups: Dict[str, GroupConfig]
    phases: Dict[str, PhaseConfig]
    novelty: NoveltyConfig
    statistics: Dict
    decision_criteria: Dict
    storage: Dict
    execution: Dict
    experimental: Dict = None  # Optional experimental features

    @classmethod
    def load(cls, config_path: Path) -> 'ExperimentConfig':
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config.yaml

        Returns:
            ExperimentConfig instance

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If configuration invalid
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config not found: {config_path}")

        with open(config_path) as f:
            data = yaml.safe_load(f)

        # Parse groups
        groups = {
            name: GroupConfig(**cfg)
            for name, cfg in data['groups'].items()
        }

        # Parse phases
        phases = {
            name: PhaseConfig(**cfg)
            for name, cfg in data['phases'].items()
        }

        # Validate phase total_iterations against actual number of groups
        num_groups = len(groups)
        for phase_name, phase in phases.items():
            expected = phase.iterations_per_run * phase.num_runs * num_groups
            if phase.total_iterations != expected:
                raise ValueError(
                    f"Phase '{phase_name}': total_iterations mismatch. "
                    f"Expected {expected} ({phase.iterations_per_run} iter/run × "
                    f"{phase.num_runs} runs × {num_groups} groups), "
                    f"got {phase.total_iterations}"
                )

        # Parse novelty config
        novelty = NoveltyConfig(**data['novelty'])

        return cls(
            name=data['experiment']['name'],
            version=data['experiment']['version'],
            description=data['experiment']['description'],
            groups=groups,
            phases=phases,
            novelty=novelty,
            statistics=data['statistics'],
            decision_criteria=data['decision_criteria'],
            storage=data['storage'],
            execution=data['execution'],
            experimental=data.get('experimental', {})  # Optional experimental features
        )

    def get_group(self, group_name: str) -> GroupConfig:
        """Get configuration for specific group."""
        if group_name not in self.groups:
            raise KeyError(f"Unknown group: {group_name}")
        return self.groups[group_name]

    def get_phase(self, phase_name: str) -> PhaseConfig:
        """Get configuration for specific phase."""
        if phase_name not in self.phases:
            raise KeyError(f"Unknown phase: {phase_name}")
        return self.phases[phase_name]

    def get_path(self, path_key: str) -> Path:
        """Get configured path as Path object.

        Args:
            path_key: Key from execution.paths (e.g., 'learning_config', 'results_dir', 'template_dir')

        Returns:
            Path object for the configured path

        Raises:
            KeyError: If path_key not found in configuration
        """
        paths = self.execution.get('paths', {})
        if path_key not in paths:
            raise KeyError(f"Path key '{path_key}' not found in execution.paths configuration")
        return Path(paths[path_key])
