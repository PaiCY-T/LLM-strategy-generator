"""Experiment configuration tracking for reproducible learning experiments.

This module provides configuration snapshot capabilities for autonomous learning
iterations, enabling complete experiment reproducibility through comprehensive
tracking of model settings, prompts, thresholds, and environment state.

Usage Example:
    >>> from src.config import ExperimentConfig
    >>> import sys
    >>>
    >>> # Create configuration snapshot
    >>> config = ExperimentConfig(
    ...     iteration_num=0,
    ...     timestamp="2025-10-12T10:30:00.000000",
    ...     model_config={
    ...         "model_name": "gemini-2.5-flash",
    ...         "temperature": 0.7,
    ...         "max_tokens": 8192
    ...     },
    ...     prompt_config={
    ...         "version": "v3_comprehensive",
    ...         "template_path": "prompt_template_v3_comprehensive.txt",
    ...         "template_hash": "sha256:abc123..."
    ...     },
    ...     system_thresholds={
    ...         "anti_churn_threshold": 0.02,
    ...         "probation_period": 3,
    ...         "novelty_threshold": 0.05
    ...     },
    ...     environment_state={
    ...         "python_version": sys.version,
    ...         "packages": {"finlab": "0.4.6", "numpy": "1.24.0"},
    ...         "api_endpoints": ["https://generativelanguage.googleapis.com/v1beta"]
    ...     }
    ... )
    >>>
    >>> # Serialize to dictionary
    >>> config_dict = config.to_dict()
    >>>
    >>> # Deserialize from dictionary
    >>> restored_config = ExperimentConfig.from_dict(config_dict)
    >>>
    >>> # Use with ExperimentConfigManager for persistence
    >>> from src.config import ExperimentConfigManager
    >>> manager = ExperimentConfigManager("experiment_configs.json")
    >>> manager.save_config(config)
    >>> loaded_config = manager.load_config(iteration_num=0)
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ExperimentConfig:
    """Complete configuration snapshot for a single learning iteration.

    Captures all parameters and environment state necessary to reproduce
    an experiment exactly, including model settings, prompts, thresholds,
    and system environment.

    Attributes:
        iteration_num: Iteration number (0-indexed) for this configuration
        timestamp: ISO 8601 formatted timestamp of configuration creation
        model_config: Model configuration parameters including:
            - model_name: Name of the LLM model (e.g., "gemini-2.5-flash")
            - temperature: Sampling temperature (0.0-1.0)
            - max_tokens: Maximum token limit for generation
            - top_p: Optional nucleus sampling parameter
            - top_k: Optional top-k sampling parameter
        prompt_config: Prompt template configuration including:
            - version: Semantic version of prompt template (e.g., "v3_comprehensive")
            - template_path: Path to prompt template file
            - template_hash: Hash of template content for integrity verification
            - custom_instructions: Optional additional instructions
        system_thresholds: Learning system threshold parameters including:
            - anti_churn_threshold: Minimum improvement required (default: 0.02)
            - probation_period: Iterations before champion replacement (default: 3)
            - novelty_threshold: Minimum diversity score (default: 0.05)
            - max_iterations: Maximum iteration limit
        environment_state: System environment snapshot including:
            - python_version: Python interpreter version string
            - packages: Dict of package names to version strings
            - api_endpoints: List of API endpoints used
            - os_info: Optional OS information
            - hardware_info: Optional hardware specifications
        custom_config: Optional extensible configuration for experiment-specific
            parameters not covered by standard fields

    Example:
        >>> config = ExperimentConfig(
        ...     iteration_num=5,
        ...     timestamp=datetime.utcnow().isoformat(),
        ...     model_config={
        ...         "model_name": "gemini-2.5-flash",
        ...         "temperature": 0.7,
        ...         "max_tokens": 8192
        ...     },
        ...     prompt_config={
        ...         "version": "v3_comprehensive",
        ...         "template_path": "prompt_template_v3_comprehensive.txt",
        ...         "template_hash": "sha256:1a2b3c..."
        ...     },
        ...     system_thresholds={
        ...         "anti_churn_threshold": 0.02,
        ...         "probation_period": 3,
        ...         "novelty_threshold": 0.05,
        ...         "max_iterations": 30
        ...     },
        ...     environment_state={
        ...         "python_version": "3.10.12",
        ...         "packages": {"finlab": "0.4.6", "numpy": "1.24.0"},
        ...         "api_endpoints": ["https://generativelanguage.googleapis.com/v1beta"]
        ...     }
        ... )
    """

    iteration_num: int
    timestamp: str
    model_config: Dict[str, Any]
    prompt_config: Dict[str, Any]
    system_thresholds: Dict[str, Any]
    environment_state: Dict[str, Any]
    custom_config: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for JSON serialization.

        Returns:
            Dictionary representation of configuration with all fields

        Example:
            >>> config = ExperimentConfig(...)
            >>> config_dict = config.to_dict()
            >>> isinstance(config_dict, dict)
            True
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExperimentConfig':
        """Create ExperimentConfig instance from dictionary.

        Args:
            data: Dictionary containing configuration fields

        Returns:
            ExperimentConfig instance populated with data

        Example:
            >>> data = {
            ...     "iteration_num": 0,
            ...     "timestamp": "2025-10-12T10:30:00",
            ...     "model_config": {"model_name": "gemini-2.5-flash"},
            ...     "prompt_config": {"version": "v3"},
            ...     "system_thresholds": {"anti_churn_threshold": 0.02},
            ...     "environment_state": {"python_version": "3.10.12"}
            ... }
            >>> config = ExperimentConfig.from_dict(data)
            >>> config.iteration_num
            0
        """
        return cls(**data)

    def validate(self) -> List[str]:
        """Validate configuration for completeness and correctness.

        Checks that all required fields are present and have valid values.

        Returns:
            List of validation error messages (empty if valid)

        Example:
            >>> config = ExperimentConfig(...)
            >>> errors = config.validate()
            >>> len(errors) == 0  # True if valid
            True
        """
        errors = []

        # Validate iteration_num
        if self.iteration_num < 0:
            errors.append("iteration_num must be non-negative")

        # Validate timestamp format
        try:
            datetime.fromisoformat(self.timestamp)
        except ValueError:
            errors.append(f"Invalid timestamp format: {self.timestamp}")

        # Validate model_config
        required_model_keys = ["model_name", "temperature", "max_tokens"]
        for key in required_model_keys:
            if key not in self.model_config:
                errors.append(f"Missing required model_config key: {key}")

        if "temperature" in self.model_config:
            temp = self.model_config["temperature"]
            if not (0.0 <= temp <= 1.0):
                errors.append(f"temperature must be between 0.0 and 1.0, got {temp}")

        # Validate prompt_config
        required_prompt_keys = ["version", "template_path"]
        for key in required_prompt_keys:
            if key not in self.prompt_config:
                errors.append(f"Missing required prompt_config key: {key}")

        # Validate system_thresholds
        required_threshold_keys = ["anti_churn_threshold", "probation_period", "novelty_threshold"]
        for key in required_threshold_keys:
            if key not in self.system_thresholds:
                errors.append(f"Missing required system_thresholds key: {key}")

        # Validate environment_state
        required_env_keys = ["python_version", "packages", "api_endpoints"]
        for key in required_env_keys:
            if key not in self.environment_state:
                errors.append(f"Missing required environment_state key: {key}")

        return errors


class ExperimentConfigManager:
    """Manages persistence and retrieval of experiment configurations.

    Provides file-based storage for ExperimentConfig snapshots, enabling
    configuration tracking across multiple iterations and experiments.

    Attributes:
        config_file: Path to JSON file for persisting configurations
        configs: List of loaded ExperimentConfig instances

    Example:
        >>> manager = ExperimentConfigManager("configs.json")
        >>> config = ExperimentConfig(...)
        >>> manager.save_config(config)
        >>> loaded = manager.load_config(iteration_num=0)
        >>> all_configs = manager.get_all_configs()
    """

    def __init__(self, config_file: str = "experiment_configs.json"):
        """Initialize configuration manager.

        Args:
            config_file: Path to JSON file for persisting configurations
        """
        self.config_file = Path(config_file)
        self.configs: List[ExperimentConfig] = []

        # Load existing configurations if available
        if self.config_file.exists():
            self.load()

    def save_config(self, config: ExperimentConfig) -> None:
        """Save a configuration snapshot.

        Args:
            config: ExperimentConfig instance to save

        Example:
            >>> manager = ExperimentConfigManager()
            >>> config = ExperimentConfig(...)
            >>> manager.save_config(config)
        """
        # Validate before saving
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {errors}")

        # Add or update configuration
        existing_idx = None
        for idx, existing_config in enumerate(self.configs):
            if existing_config.iteration_num == config.iteration_num:
                existing_idx = idx
                break

        if existing_idx is not None:
            self.configs[existing_idx] = config
        else:
            self.configs.append(config)

        self.save()

    def load_config(self, iteration_num: int) -> Optional[ExperimentConfig]:
        """Load configuration for specific iteration.

        Args:
            iteration_num: Iteration number to retrieve

        Returns:
            ExperimentConfig if found, None otherwise

        Example:
            >>> manager = ExperimentConfigManager()
            >>> config = manager.load_config(iteration_num=5)
        """
        for config in self.configs:
            if config.iteration_num == iteration_num:
                return config
        return None

    def get_all_configs(self) -> List[ExperimentConfig]:
        """Get all stored configurations.

        Returns:
            List of all ExperimentConfig instances

        Example:
            >>> manager = ExperimentConfigManager()
            >>> all_configs = manager.get_all_configs()
            >>> len(all_configs)
            10
        """
        return self.configs.copy()

    def get_latest_config(self) -> Optional[ExperimentConfig]:
        """Get most recent configuration.

        Returns:
            Latest ExperimentConfig if available, None otherwise

        Example:
            >>> manager = ExperimentConfigManager()
            >>> latest = manager.get_latest_config()
        """
        if not self.configs:
            return None
        return max(self.configs, key=lambda c: c.iteration_num)

    def save(self) -> None:
        """Persist all configurations to JSON file."""
        data = {
            'configs': [config.to_dict() for config in self.configs],
            'metadata': {
                'total_configs': len(self.configs),
                'last_updated': datetime.utcnow().isoformat()
            }
        }

        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        """Load configurations from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.configs = [
                ExperimentConfig.from_dict(config_data)
                for config_data in data.get('configs', [])
            ]
        except Exception as e:
            print(f"Warning: Could not load configurations from {self.config_file}: {e}")
            self.configs = []

    def clear(self) -> None:
        """Clear all configurations and delete file."""
        self.configs = []
        if self.config_file.exists():
            self.config_file.unlink()

    def export_config(self, iteration_num: int, output_file: str) -> bool:
        """Export single configuration to separate file.

        Args:
            iteration_num: Iteration number to export
            output_file: Path to output JSON file

        Returns:
            True if successful, False otherwise

        Example:
            >>> manager = ExperimentConfigManager()
            >>> success = manager.export_config(5, "config_iter5.json")
        """
        config = self.load_config(iteration_num)
        if config is None:
            return False

        try:
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def import_config(self, input_file: str) -> Optional[ExperimentConfig]:
        """Import configuration from external file.

        Args:
            input_file: Path to JSON file containing configuration

        Returns:
            ExperimentConfig if successful, None otherwise

        Example:
            >>> manager = ExperimentConfigManager()
            >>> config = manager.import_config("config_iter5.json")
            >>> if config:
            ...     manager.save_config(config)
        """
        try:
            input_path = Path(input_file)
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            config = ExperimentConfig.from_dict(data)
            errors = config.validate()
            if errors:
                print(f"Invalid imported configuration: {errors}")
                return None

            return config
        except Exception as e:
            print(f"Error importing configuration: {e}")
            return None

    def capture_config_snapshot(
        self,
        autonomous_loop: Any,
        iteration_num: int
    ) -> ExperimentConfig:
        """Capture live configuration snapshot from AutonomousLoop instance.

        Extracts complete configuration state from a running autonomous loop,
        including model settings, prompt configuration, system thresholds,
        and environment state. Automatically saves the captured configuration.

        Args:
            autonomous_loop: AutonomousLoop instance to capture configuration from
            iteration_num: Current iteration number (0-indexed)

        Returns:
            ExperimentConfig instance with captured configuration data

        Example:
            >>> from autonomous_loop import AutonomousLoop
            >>> loop = AutonomousLoop(model="gemini-2.5-flash", max_iterations=10)
            >>> manager = ExperimentConfigManager()
            >>> config = manager.capture_config_snapshot(loop, iteration_num=0)
            >>> print(f"Captured model: {config.model_config['model_name']}")
            Captured model: gemini-2.5-flash
        """
        import sys
        import platform
        import hashlib
        import logging
        from pathlib import Path

        logger = logging.getLogger(__name__)

        # Initialize configuration dictionaries
        model_config: Dict[str, Any] = {}
        prompt_config: Dict[str, Any] = {}
        system_thresholds: Dict[str, Any] = {}
        environment_state: Dict[str, Any] = {}

        # Extract model configuration
        try:
            model_config['model_name'] = getattr(autonomous_loop, 'model', 'gemini-2.5-flash')
            # Temperature and max_tokens are not currently configurable in AutonomousLoop
            # Use reasonable defaults based on typical usage
            model_config['temperature'] = 1.0  # Default for creative strategy generation
            model_config['max_tokens'] = 8000  # Default for comprehensive strategy code
        except Exception as e:
            logger.warning(f"Error extracting model config: {e}")
            model_config = {
                'model_name': 'gemini-2.5-flash',
                'temperature': 1.0,
                'max_tokens': 8000
            }

        # Extract prompt configuration
        try:
            prompt_builder = getattr(autonomous_loop, 'prompt_builder', None)
            if prompt_builder:
                template_file = getattr(prompt_builder, 'template_file', None)
                if template_file:
                    template_path = Path(template_file)
                    prompt_config['template_path'] = str(template_path.name)

                    # Determine version from filename
                    filename = template_path.name
                    if 'v3' in filename.lower():
                        prompt_config['version'] = 'v3_comprehensive'
                    elif 'v2' in filename.lower():
                        prompt_config['version'] = 'v2'
                    elif 'v1' in filename.lower():
                        prompt_config['version'] = 'v1'
                    else:
                        prompt_config['version'] = 'unknown'

                    # Compute template hash if file exists
                    try:
                        if template_path.exists():
                            with open(template_path, 'rb') as f:
                                content = f.read()
                                hash_obj = hashlib.sha256(content)
                                prompt_config['template_hash'] = f"sha256:{hash_obj.hexdigest()}"
                        else:
                            prompt_config['template_hash'] = "file_not_found"
                    except Exception as e:
                        logger.warning(f"Error computing template hash: {e}")
                        prompt_config['template_hash'] = "error_computing_hash"
                else:
                    # No template file found
                    prompt_config['version'] = 'unknown'
                    prompt_config['template_path'] = 'not_found'
                    prompt_config['template_hash'] = 'not_available'
            else:
                # No prompt builder found
                prompt_config['version'] = 'unknown'
                prompt_config['template_path'] = 'not_found'
                prompt_config['template_hash'] = 'not_available'
        except Exception as e:
            logger.warning(f"Error extracting prompt config: {e}")
            prompt_config = {
                'version': 'unknown',
                'template_path': 'error',
                'template_hash': 'error'
            }

        # Extract system thresholds
        try:
            # Anti-churn threshold: Based on _update_champion logic
            # Default is 5% improvement required (1.05 multiplier)
            system_thresholds['anti_churn_threshold'] = 0.05

            # Probation period: Based on _update_champion logic
            # Default is 2 iterations within which 10% improvement is required
            system_thresholds['probation_period'] = 2

            # Novelty threshold: Not currently implemented in AutonomousLoop
            # Use reasonable default for strategy diversity tracking
            system_thresholds['novelty_threshold'] = 0.3

            # Max iterations from loop config
            max_iterations = getattr(autonomous_loop, 'max_iterations', 10)
            system_thresholds['max_iterations'] = max_iterations
        except Exception as e:
            logger.warning(f"Error extracting system thresholds: {e}")
            system_thresholds = {
                'anti_churn_threshold': 0.05,
                'probation_period': 2,
                'novelty_threshold': 0.3,
                'max_iterations': 10
            }

        # Capture environment state
        try:
            # Python version
            environment_state['python_version'] = sys.version

            # Key package versions
            packages: Dict[str, str] = {}
            try:
                import finlab
                packages['finlab'] = getattr(finlab, '__version__', 'unknown')
            except ImportError:
                packages['finlab'] = 'not_installed'

            try:
                import pandas
                packages['pandas'] = pandas.__version__
            except ImportError:
                packages['pandas'] = 'not_installed'

            try:
                import numpy
                packages['numpy'] = numpy.__version__
            except ImportError:
                packages['numpy'] = 'not_installed'

            try:
                import scipy
                packages['scipy'] = scipy.__version__
            except ImportError:
                packages['scipy'] = 'not_installed'

            environment_state['packages'] = packages

            # API endpoints detection
            api_endpoints: List[str] = []
            model_name = model_config.get('model_name', '')
            if 'gemini' in model_name.lower():
                api_endpoints.append('https://generativelanguage.googleapis.com/v1beta')
            elif 'openrouter' in model_name.lower() or 'google/' in model_name.lower():
                api_endpoints.append('https://openrouter.ai/api/v1')
            else:
                api_endpoints.append('unknown')

            environment_state['api_endpoints'] = api_endpoints

            # OS information
            environment_state['os_info'] = f"{platform.system()} {platform.release()}"
        except Exception as e:
            logger.warning(f"Error capturing environment state: {e}")
            environment_state = {
                'python_version': sys.version,
                'packages': {'finlab': 'unknown', 'pandas': 'unknown', 'numpy': 'unknown'},
                'api_endpoints': ['unknown'],
                'os_info': 'unknown'
            }

        # Create ExperimentConfig instance
        config = ExperimentConfig(
            iteration_num=iteration_num,
            timestamp=datetime.utcnow().isoformat(),
            model_config=model_config,
            prompt_config=prompt_config,
            system_thresholds=system_thresholds,
            environment_state=environment_state
        )

        # Automatically save configuration
        try:
            self.save_config(config)
            logger.info(f"Configuration snapshot saved for iteration {iteration_num}")
        except Exception as e:
            logger.error(f"Error saving configuration snapshot: {e}")
            # Don't raise - return config even if save fails

        return config

    def _compare_dicts(
        self,
        dict1: Optional[Dict[str, Any]],
        dict2: Optional[Dict[str, Any]],
        section_name: str
    ) -> Dict[str, Any]:
        """Compare two dictionaries and return structured diff.

        Args:
            dict1: First dictionary (old configuration)
            dict2: Second dictionary (new configuration)
            section_name: Name of configuration section being compared

        Returns:
            Dictionary containing:
                - changed_fields: List of field names that changed
                - details: List of change detail dictionaries with field, old_value,
                          new_value, and severity
                - has_changes: Boolean indicating if any changes exist

        Example:
            >>> manager = ExperimentConfigManager()
            >>> dict1 = {"temperature": 0.7, "model": "gemini-2.5-flash"}
            >>> dict2 = {"temperature": 0.8, "model": "gemini-2.5-flash"}
            >>> diff = manager._compare_dicts(dict1, dict2, "model_config")
            >>> diff['has_changes']
            True
            >>> diff['changed_fields']
            ['temperature']
        """
        # Handle None values
        if dict1 is None:
            dict1 = {}
        if dict2 is None:
            dict2 = {}

        changed_fields = []
        details = []

        # Get all unique keys
        all_keys = set(dict1.keys()) | set(dict2.keys())

        for key in sorted(all_keys):
            old_value = dict1.get(key)
            new_value = dict2.get(key)

            # Determine if there's a change
            if old_value != new_value:
                changed_fields.append(key)

                # Determine severity based on section and field
                severity = self._assess_field_severity(section_name, key, old_value, new_value)

                details.append({
                    'field': key,
                    'old_value': old_value,
                    'new_value': new_value,
                    'severity': severity
                })

        return {
            'changed_fields': changed_fields,
            'details': details,
            'has_changes': len(changed_fields) > 0
        }

    def _assess_field_severity(
        self,
        section_name: str,
        field_name: str,
        old_value: Any,
        new_value: Any
    ) -> str:
        """Assess severity of a configuration field change.

        Args:
            section_name: Configuration section name
            field_name: Field name within section
            old_value: Original field value
            new_value: New field value

        Returns:
            Severity level: 'critical', 'moderate', or 'minor'

        Severity Rules:
            - Critical: Model name changes, prompt template content changes
            - Moderate: Temperature/threshold changes, package version changes
            - Minor: Max tokens, OS info changes
        """
        # Critical changes
        critical_fields = {
            'model_config': ['model_name'],
            'prompt_config': ['template_hash']  # Content change
        }

        # Moderate changes
        moderate_fields = {
            'model_config': ['temperature', 'top_p', 'top_k'],
            'prompt_config': ['version', 'template_path'],
            'system_thresholds': ['anti_churn_threshold', 'probation_period',
                                 'novelty_threshold', 'max_iterations'],
            'environment_state': ['packages']  # Package version changes
        }

        # Check critical
        if section_name in critical_fields:
            if field_name in critical_fields[section_name]:
                return 'critical'

        # Check moderate
        if section_name in moderate_fields:
            if field_name in moderate_fields[section_name]:
                return 'moderate'

        # Default to minor
        return 'minor'

    def compute_config_diff(
        self,
        config1: Union[int, ExperimentConfig],
        config2: Union[int, ExperimentConfig]
    ) -> Dict[str, Any]:
        """Compare two experiment configurations and generate detailed diff.

        Compares all configuration sections (model, prompt, thresholds, environment)
        between two configurations and identifies all changes with severity assessment.

        Args:
            config1: Either iteration number (int) or ExperimentConfig instance
                    representing the baseline configuration
            config2: Either iteration number (int) or ExperimentConfig instance
                    representing the comparison configuration

        Returns:
            Dictionary containing:
                - iteration_nums: Tuple of [iter1, iter2] or [None, None] if configs provided
                - has_changes: Boolean indicating if any changes exist
                - change_summary: Human-readable summary string
                - changes: Detailed changes by section (model_config, prompt_config, etc.)
                - severity: Overall severity level (critical/moderate/minor/none)

        Raises:
            ValueError: If iteration number not found or invalid input provided

        Examples:
            >>> manager = ExperimentConfigManager()
            >>> # Compare by iteration numbers
            >>> diff = manager.compute_config_diff(0, 1)
            >>> print(diff['change_summary'])
            "2 changes: temperature, prompt_version"

            >>> # Compare config instances
            >>> config1 = manager.load_config(0)
            >>> config2 = manager.load_config(1)
            >>> diff = manager.compute_config_diff(config1, config2)
            >>> diff['has_changes']
            True

            >>> # No changes
            >>> diff = manager.compute_config_diff(0, 0)
            >>> diff['severity']
            'none'
        """
        import logging
        logger = logging.getLogger(__name__)

        # Resolve configs from iteration numbers if needed
        if isinstance(config1, int):
            iter1 = config1
            config1 = self.load_config(iter1)
            if config1 is None:
                return {
                    'error': f"Configuration for iteration {iter1} not found",
                    'iteration_nums': [iter1, None],
                    'has_changes': False,
                    'change_summary': 'Error: configuration not found',
                    'changes': {},
                    'severity': 'none'
                }
        else:
            iter1 = config1.iteration_num if config1 else None

        if isinstance(config2, int):
            iter2 = config2
            config2 = self.load_config(iter2)
            if config2 is None:
                return {
                    'error': f"Configuration for iteration {iter2} not found",
                    'iteration_nums': [iter1, iter2],
                    'has_changes': False,
                    'change_summary': 'Error: configuration not found',
                    'changes': {},
                    'severity': 'none'
                }
        else:
            iter2 = config2.iteration_num if config2 else None

        # Handle None configs
        if config1 is None or config2 is None:
            return {
                'error': 'One or both configurations are None',
                'iteration_nums': [iter1, iter2],
                'has_changes': False,
                'change_summary': 'Error: invalid configuration',
                'changes': {},
                'severity': 'none'
            }

        # Compare each section
        changes = {}
        all_changed_fields = []
        max_severity = 'none'

        # Compare model_config
        model_diff = self._compare_dicts(
            config1.model_config,
            config2.model_config,
            'model_config'
        )
        if model_diff['has_changes']:
            changes['model_config'] = model_diff
            all_changed_fields.extend([f"model.{f}" for f in model_diff['changed_fields']])
            # Update max severity
            for detail in model_diff['details']:
                if detail['severity'] == 'critical':
                    max_severity = 'critical'
                elif detail['severity'] == 'moderate' and max_severity != 'critical':
                    max_severity = 'moderate'
                elif detail['severity'] == 'minor' and max_severity == 'none':
                    max_severity = 'minor'

        # Compare prompt_config
        prompt_diff = self._compare_dicts(
            config1.prompt_config,
            config2.prompt_config,
            'prompt_config'
        )
        if prompt_diff['has_changes']:
            changes['prompt_config'] = prompt_diff
            all_changed_fields.extend([f"prompt.{f}" for f in prompt_diff['changed_fields']])
            for detail in prompt_diff['details']:
                if detail['severity'] == 'critical':
                    max_severity = 'critical'
                elif detail['severity'] == 'moderate' and max_severity != 'critical':
                    max_severity = 'moderate'
                elif detail['severity'] == 'minor' and max_severity == 'none':
                    max_severity = 'minor'

        # Compare system_thresholds
        threshold_diff = self._compare_dicts(
            config1.system_thresholds,
            config2.system_thresholds,
            'system_thresholds'
        )
        if threshold_diff['has_changes']:
            changes['system_thresholds'] = threshold_diff
            all_changed_fields.extend([f"threshold.{f}" for f in threshold_diff['changed_fields']])
            for detail in threshold_diff['details']:
                if detail['severity'] == 'critical':
                    max_severity = 'critical'
                elif detail['severity'] == 'moderate' and max_severity != 'critical':
                    max_severity = 'moderate'
                elif detail['severity'] == 'minor' and max_severity == 'none':
                    max_severity = 'minor'

        # Compare environment_state
        env_diff = self._compare_dicts(
            config1.environment_state,
            config2.environment_state,
            'environment_state'
        )
        if env_diff['has_changes']:
            changes['environment_state'] = env_diff
            all_changed_fields.extend([f"env.{f}" for f in env_diff['changed_fields']])
            for detail in env_diff['details']:
                if detail['severity'] == 'critical':
                    max_severity = 'critical'
                elif detail['severity'] == 'moderate' and max_severity != 'critical':
                    max_severity = 'moderate'
                elif detail['severity'] == 'minor' and max_severity == 'none':
                    max_severity = 'minor'

        # Generate change summary
        has_changes = len(all_changed_fields) > 0
        if not has_changes:
            change_summary = "No changes detected"
        else:
            # Get top 3 most important changed fields (prioritize critical/moderate)
            important_fields = []

            # Add critical changes first
            for section_changes in changes.values():
                for detail in section_changes['details']:
                    if detail['severity'] == 'critical':
                        important_fields.append(detail['field'])

            # Add moderate changes if space remains
            if len(important_fields) < 3:
                for section_changes in changes.values():
                    for detail in section_changes['details']:
                        if detail['severity'] == 'moderate' and detail['field'] not in important_fields:
                            important_fields.append(detail['field'])
                            if len(important_fields) >= 3:
                                break
                    if len(important_fields) >= 3:
                        break

            # Add minor changes if space remains
            if len(important_fields) < 3:
                for section_changes in changes.values():
                    for detail in section_changes['details']:
                        if detail['severity'] == 'minor' and detail['field'] not in important_fields:
                            important_fields.append(detail['field'])
                            if len(important_fields) >= 3:
                                break
                    if len(important_fields) >= 3:
                        break

            fields_str = ', '.join(important_fields[:3])
            if len(all_changed_fields) > 3:
                fields_str += f" (+{len(all_changed_fields) - 3} more)"

            change_summary = f"{len(all_changed_fields)} changes: {fields_str}"

        return {
            'iteration_nums': [iter1, iter2],
            'has_changes': has_changes,
            'change_summary': change_summary,
            'changes': changes,
            'severity': max_severity
        }


def main():
    """Test experiment configuration tracking."""
    import sys

    print("Testing experiment configuration tracking...\n")

    # Create configuration manager
    manager = ExperimentConfigManager("test_experiment_configs.json")
    manager.clear()

    # Create test configuration
    print("Creating test configuration...")
    config = ExperimentConfig(
        iteration_num=0,
        timestamp=datetime.utcnow().isoformat(),
        model_config={
            "model_name": "gemini-2.5-flash",
            "temperature": 0.7,
            "max_tokens": 8192,
            "top_p": 0.95
        },
        prompt_config={
            "version": "v3_comprehensive",
            "template_path": "prompt_template_v3_comprehensive.txt",
            "template_hash": "sha256:abc123def456",
            "custom_instructions": "Focus on high Sharpe ratio"
        },
        system_thresholds={
            "anti_churn_threshold": 0.02,
            "probation_period": 3,
            "novelty_threshold": 0.05,
            "max_iterations": 30
        },
        environment_state={
            "python_version": sys.version,
            "packages": {
                "finlab": "0.4.6",
                "numpy": "1.24.0",
                "pandas": "2.0.0"
            },
            "api_endpoints": ["https://generativelanguage.googleapis.com/v1beta"],
            "os_info": "Linux 5.15.153.1-microsoft-standard-WSL2"
        },
        custom_config={
            "experiment_name": "baseline_test",
            "researcher": "autonomous_system"
        }
    )

    # Validate configuration
    print("Validating configuration...")
    errors = config.validate()
    if errors:
        print(f"❌ Validation errors: {errors}")
        return
    print("✅ Configuration valid\n")

    # Save configuration
    print("Saving configuration...")
    manager.save_config(config)
    print(f"✅ Saved to {manager.config_file}\n")

    # Load configuration
    print("Loading configuration...")
    loaded_config = manager.load_config(iteration_num=0)
    if loaded_config:
        print(f"✅ Loaded configuration for iteration {loaded_config.iteration_num}")
        print(f"   Model: {loaded_config.model_config['model_name']}")
        print(f"   Temperature: {loaded_config.model_config['temperature']}")
        print(f"   Prompt version: {loaded_config.prompt_config['version']}\n")

    # Test serialization
    print("Testing serialization...")
    config_dict = config.to_dict()
    restored_config = ExperimentConfig.from_dict(config_dict)
    print(f"✅ Serialization: {restored_config.iteration_num == config.iteration_num}\n")

    # Test export/import
    print("Testing export/import...")
    export_success = manager.export_config(0, "test_config_export.json")
    if export_success:
        print("✅ Export successful")
        imported_config = manager.import_config("test_config_export.json")
        if imported_config:
            print(f"✅ Import successful: iteration {imported_config.iteration_num}\n")

    # Add second configuration
    print("Adding second configuration...")
    config2 = ExperimentConfig(
        iteration_num=1,
        timestamp=datetime.utcnow().isoformat(),
        model_config={
            "model_name": "gemini-2.5-flash",
            "temperature": 0.8,
            "max_tokens": 8192
        },
        prompt_config={
            "version": "v3_comprehensive",
            "template_path": "prompt_template_v3_comprehensive.txt",
            "template_hash": "sha256:abc123def456"
        },
        system_thresholds={
            "anti_churn_threshold": 0.02,
            "probation_period": 3,
            "novelty_threshold": 0.05
        },
        environment_state={
            "python_version": sys.version,
            "packages": {"finlab": "0.4.6"},
            "api_endpoints": ["https://generativelanguage.googleapis.com/v1beta"]
        }
    )
    manager.save_config(config2)

    # Get all configurations
    all_configs = manager.get_all_configs()
    print(f"✅ Total configurations: {len(all_configs)}\n")

    # Get latest configuration
    latest = manager.get_latest_config()
    if latest:
        print(f"Latest configuration: iteration {latest.iteration_num}")
        print(f"Temperature: {latest.model_config['temperature']}\n")

    # Test configuration diff
    print("Testing configuration diff...")
    diff = manager.compute_config_diff(0, 1)
    print(f"Comparing iterations {diff['iteration_nums'][0]} and {diff['iteration_nums'][1]}")
    print(f"Has changes: {diff['has_changes']}")
    print(f"Change summary: {diff['change_summary']}")
    print(f"Overall severity: {diff['severity']}")
    if diff['has_changes']:
        for section, section_diff in diff['changes'].items():
            print(f"\n  {section}:")
            for detail in section_diff['details']:
                print(f"    - {detail['field']}: {detail['old_value']} → {detail['new_value']} ({detail['severity']})")
    print()

    # Test identical configs (no changes)
    print("Testing identical config comparison...")
    diff_same = manager.compute_config_diff(0, 0)
    print(f"Comparing iteration 0 with itself")
    print(f"Has changes: {diff_same['has_changes']}")
    print(f"Change summary: {diff_same['change_summary']}")
    print(f"Severity: {diff_same['severity']}\n")

    # Test comparing config instances
    print("Testing direct config instance comparison...")
    loaded_config1 = manager.load_config(0)
    loaded_config2 = manager.load_config(1)
    if loaded_config1 and loaded_config2:
        diff_instance = manager.compute_config_diff(loaded_config1, loaded_config2)
        print(f"Direct comparison: {diff_instance['change_summary']}\n")

    # Cleanup
    manager.clear()
    Path("test_config_export.json").unlink(missing_ok=True)
    print("✅ Test complete")


if __name__ == '__main__':
    main()
