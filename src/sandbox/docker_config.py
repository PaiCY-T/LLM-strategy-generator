"""
Docker Configuration Module

Manages Docker sandbox configuration loading and validation.
Provides centralized configuration for container resource limits and security settings.
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import yaml


@dataclass
class DockerConfig:
    """
    Configuration for Docker sandbox execution environment.

    This dataclass encapsulates all Docker container settings including:
    - Resource limits (memory, CPU, timeout)
    - Security profiles (network isolation, read-only filesystem)
    - Container image and runtime settings
    - Output and monitoring configuration

    Attributes:
        enabled: Whether Docker sandbox is enabled (default: True)
        image: Docker image name (default: python:3.10-slim)
        memory_limit: Memory limit with unit (e.g., "2g", "512m")
        memory_swap_limit: Memory + swap limit (default: same as memory_limit)
        cpu_limit: CPU cores limit as float (e.g., 0.5 = half a core)
        timeout_seconds: Maximum execution time before container is killed
        network_mode: Docker network mode (default: "none" for isolation)
        read_only: Whether container filesystem is read-only
        tmpfs_path: Path for writable tmpfs mount
        tmpfs_size: Size limit for tmpfs (e.g., "1g")
        tmpfs_options: Mount options for tmpfs
        seccomp_profile: Path to seccomp security profile JSON
        output_dir: Directory for strategy output results
        cleanup_on_exit: Whether to remove container after execution
        export_container_stats: Whether to export container metrics
        alert_on_orphaned_containers: Threshold for alerting on orphaned containers
        prometheus_port: Port for Prometheus metrics export
    """

    # Core Docker settings
    enabled: bool = True
    # Task 21: Pin to specific digest for supply chain security
    image: str = "python:3.10-slim@sha256:e0c4fae70d550834a40f6c3e0326e02cfe239c2351d922e1fb1577a3c6ebde02"

    # Resource limits
    memory_limit: str = "2g"
    memory_swap_limit: Optional[str] = None  # Defaults to memory_limit
    cpu_limit: float = 0.5
    timeout_seconds: int = 600

    # Security settings
    network_mode: str = "none"
    read_only: bool = True
    tmpfs_path: str = "/tmp"
    tmpfs_size: str = "1g"
    tmpfs_options: str = "rw,noexec,nosuid"
    seccomp_profile: str = "config/seccomp_profile.json"

    # Execution settings
    output_dir: str = "sandbox_output"
    cleanup_on_exit: bool = True

    # Monitoring settings
    export_container_stats: bool = True
    alert_on_orphaned_containers: int = 3
    prometheus_port: int = 8000
    runtime_monitor_enabled: bool = True  # Task 17: Active security monitoring

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Set memory_swap_limit to memory_limit if not specified
        if self.memory_swap_limit is None:
            self.memory_swap_limit = self.memory_limit

        # Validate all parameters
        self._validate()

    def _validate(self):
        """
        Validate all configuration parameters.

        Raises:
            ValueError: If any parameter is invalid
        """
        # Validate memory limits
        self._validate_memory_limit(self.memory_limit, "memory_limit")
        if self.memory_swap_limit:
            self._validate_memory_limit(self.memory_swap_limit, "memory_swap_limit")

        # Validate CPU limit
        if not isinstance(self.cpu_limit, (int, float)):
            raise ValueError(f"cpu_limit must be numeric, got {type(self.cpu_limit)}")
        if self.cpu_limit <= 0:
            raise ValueError(f"cpu_limit must be positive, got {self.cpu_limit}")
        if self.cpu_limit > 64:  # Reasonable upper bound
            raise ValueError(f"cpu_limit too high (max 64), got {self.cpu_limit}")

        # Validate timeout
        if not isinstance(self.timeout_seconds, int):
            raise ValueError(f"timeout_seconds must be integer, got {type(self.timeout_seconds)}")
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be positive, got {self.timeout_seconds}")
        if self.timeout_seconds > 3600:  # 1 hour max
            raise ValueError(f"timeout_seconds too high (max 3600), got {self.timeout_seconds}")

        # Validate tmpfs size
        self._validate_memory_limit(self.tmpfs_size, "tmpfs_size")

        # Validate network mode
        valid_network_modes = ["none", "bridge", "host"]
        if self.network_mode not in valid_network_modes:
            raise ValueError(
                f"Invalid network_mode '{self.network_mode}', "
                f"must be one of {valid_network_modes}"
            )

        # Validate alert threshold
        if not isinstance(self.alert_on_orphaned_containers, int):
            raise ValueError(
                f"alert_on_orphaned_containers must be integer, "
                f"got {type(self.alert_on_orphaned_containers)}"
            )
        if self.alert_on_orphaned_containers < 0:
            raise ValueError(
                f"alert_on_orphaned_containers must be non-negative, "
                f"got {self.alert_on_orphaned_containers}"
            )

        # Validate prometheus port
        if not isinstance(self.prometheus_port, int):
            raise ValueError(f"prometheus_port must be integer, got {type(self.prometheus_port)}")
        if not (1024 <= self.prometheus_port <= 65535):
            raise ValueError(
                f"prometheus_port must be in range 1024-65535, got {self.prometheus_port}"
            )

    def _validate_memory_limit(self, value: str, param_name: str):
        """
        Validate memory limit format and value.

        Args:
            value: Memory limit string (e.g., "2g", "512m")
            param_name: Parameter name for error messages

        Raises:
            ValueError: If memory limit format or value is invalid
        """
        if not isinstance(value, str):
            raise ValueError(f"{param_name} must be string, got {type(value)}")

        # Match format: number + unit (k/m/g/t, case insensitive)
        pattern = r'^(\d+(?:\.\d+)?)(k|m|g|t)$'
        match = re.match(pattern, value.lower())

        if not match:
            raise ValueError(
                f"Invalid {param_name} format '{value}'. "
                f"Expected format: <number><unit> (e.g., '2g', '512m', '1024k')"
            )

        size, unit = match.groups()
        size = float(size)

        # Convert to bytes for validation
        unit_multipliers = {
            'k': 1024,
            'm': 1024 ** 2,
            'g': 1024 ** 3,
            't': 1024 ** 4,
        }
        bytes_value = size * unit_multipliers[unit]

        # Validate reasonable bounds (1MB to 64GB)
        min_bytes = 1024 ** 2  # 1MB
        max_bytes = 64 * (1024 ** 3)  # 64GB

        if bytes_value < min_bytes:
            raise ValueError(
                f"{param_name} too small (min 1m), got '{value}' "
                f"({bytes_value / (1024**2):.2f}MB)"
            )

        if bytes_value > max_bytes:
            raise ValueError(
                f"{param_name} too large (max 64g), got '{value}' "
                f"({bytes_value / (1024**3):.2f}GB)"
            )

    @classmethod
    def from_yaml(cls, path: Optional[str] = None) -> 'DockerConfig':
        """
        Load Docker configuration from YAML file.

        Supports environment variable substitution for sensitive values.
        Falls back to sensible defaults if file doesn't exist.

        Args:
            path: Path to docker_config.yaml (default: config/docker_config.yaml)

        Returns:
            DockerConfig instance with loaded or default values

        Raises:
            ValueError: If configuration file is malformed or contains invalid values
        """
        if path is None:
            path = "config/docker_config.yaml"

        config_path = Path(path)

        # Use defaults if file doesn't exist
        if not config_path.exists():
            return cls()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Failed to parse YAML from {path}: {e}")
        except Exception as e:
            raise ValueError(f"Failed to read config file {path}: {e}")

        if not config_data:
            # Empty file, use defaults
            return cls()

        # Extract docker section
        docker_config = config_data.get('docker', {})
        monitoring_config = config_data.get('monitoring', {})

        # Substitute environment variables
        docker_config = cls._substitute_env_vars(docker_config)
        monitoring_config = cls._substitute_env_vars(monitoring_config)

        # Flatten tmpfs nested dict to individual parameters
        if 'tmpfs' in docker_config and isinstance(docker_config['tmpfs'], dict):
            tmpfs = docker_config.pop('tmpfs')
            docker_config['tmpfs_path'] = tmpfs.get('path', '/tmp')
            docker_config['tmpfs_size'] = tmpfs.get('size', '1g')
            docker_config['tmpfs_options'] = tmpfs.get('options', 'rw,noexec,nosuid')

        # Merge docker and monitoring configs
        merged_config = {**docker_config, **monitoring_config}

        # Create instance with loaded values
        try:
            return cls(**merged_config)
        except TypeError as e:
            raise ValueError(f"Invalid configuration parameters in {path}: {e}")

    @staticmethod
    def _substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively substitute environment variables in config values.

        Supports format: ${ENV_VAR} or ${ENV_VAR:default_value}

        Args:
            config: Configuration dictionary

        Returns:
            Dictionary with environment variables substituted
        """
        if not isinstance(config, dict):
            return config

        result = {}
        env_pattern = r'\$\{([^:}]+)(?::([^}]*))?\}'

        for key, value in config.items():
            if isinstance(value, str):
                # Find all environment variable references
                matches = re.finditer(env_pattern, value)
                new_value = value

                for match in matches:
                    env_var = match.group(1)
                    default = match.group(2) if match.group(2) is not None else ""
                    env_value = os.getenv(env_var, default)
                    new_value = new_value.replace(match.group(0), env_value)

                result[key] = new_value
            elif isinstance(value, dict):
                result[key] = DockerConfig._substitute_env_vars(value)
            else:
                result[key] = value

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary format.

        Returns:
            Dictionary representation of configuration
        """
        return {
            'docker': {
                'enabled': self.enabled,
                'image': self.image,
                'memory_limit': self.memory_limit,
                'memory_swap_limit': self.memory_swap_limit,
                'cpu_limit': self.cpu_limit,
                'timeout_seconds': self.timeout_seconds,
                'network_mode': self.network_mode,
                'read_only': self.read_only,
                'tmpfs': {
                    'path': self.tmpfs_path,
                    'size': self.tmpfs_size,
                    'options': self.tmpfs_options,
                },
                'seccomp_profile': self.seccomp_profile,
                'output_dir': self.output_dir,
                'cleanup_on_exit': self.cleanup_on_exit,
            },
            'monitoring': {
                'export_container_stats': self.export_container_stats,
                'alert_on_orphaned_containers': self.alert_on_orphaned_containers,
                'prometheus_port': self.prometheus_port,
            }
        }
