"""
Unit Tests for DockerConfig Module

Tests configuration loading, validation, and environment variable substitution.
Coverage target: 100% (simple dataclass with well-defined validation)
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.sandbox.docker_config import DockerConfig


class TestDockerConfigDefaults:
    """Test default configuration values."""

    def test_default_initialization(self):
        """Test DockerConfig initializes with sensible defaults."""
        config = DockerConfig()

        # Core settings
        assert config.enabled is True
        assert config.image == "python:3.10-slim"

        # Resource limits
        assert config.memory_limit == "2g"
        assert config.memory_swap_limit == "2g"
        assert config.cpu_limit == 0.5
        assert config.timeout_seconds == 600

        # Security settings
        assert config.network_mode == "none"
        assert config.read_only is True
        assert config.tmpfs_path == "/tmp"
        assert config.tmpfs_size == "1g"
        assert config.tmpfs_options == "rw,noexec,nosuid"
        assert config.seccomp_profile == "config/seccomp_profile.json"

        # Execution settings
        assert config.output_dir == "sandbox_output"
        assert config.cleanup_on_exit is True

        # Monitoring settings
        assert config.export_container_stats is True
        assert config.alert_on_orphaned_containers == 3
        assert config.prometheus_port == 8000

    def test_memory_swap_limit_defaults_to_memory_limit(self):
        """Test memory_swap_limit automatically set to memory_limit if None."""
        config = DockerConfig(memory_limit="4g", memory_swap_limit=None)
        assert config.memory_swap_limit == "4g"

    def test_custom_values(self):
        """Test initialization with custom values."""
        config = DockerConfig(
            enabled=False,
            image="custom:image",
            memory_limit="4g",
            cpu_limit=1.0,
            timeout_seconds=300,
        )

        assert config.enabled is False
        assert config.image == "custom:image"
        assert config.memory_limit == "4g"
        assert config.cpu_limit == 1.0
        assert config.timeout_seconds == 300


class TestDockerConfigValidation:
    """Test configuration parameter validation."""

    def test_valid_memory_limits(self):
        """Test various valid memory limit formats."""
        valid_limits = ["512m", "1g", "2G", "4096m", "1024k", "0.5g"]
        for limit in valid_limits:
            config = DockerConfig(memory_limit=limit)
            assert config.memory_limit == limit

    def test_invalid_memory_limit_format(self):
        """Test rejection of invalid memory limit formats."""
        invalid_limits = [
            "abc",  # No number
            "123",  # No unit
            "1x",   # Invalid unit
            "-1g",  # Negative
            "2.5.3m",  # Invalid number
        ]
        for limit in invalid_limits:
            with pytest.raises(ValueError, match="Invalid .* format"):
                DockerConfig(memory_limit=limit)

    def test_invalid_memory_limit_type(self):
        """Test rejection of non-string memory limits."""
        with pytest.raises(ValueError, match="must be string"):
            DockerConfig(memory_limit=123)

    def test_memory_limit_too_small(self):
        """Test rejection of memory limits below minimum (1MB)."""
        with pytest.raises(ValueError, match="too small"):
            DockerConfig(memory_limit="512k")  # < 1MB

    def test_memory_limit_too_large(self):
        """Test rejection of memory limits above maximum (64GB)."""
        with pytest.raises(ValueError, match="too large"):
            DockerConfig(memory_limit="128g")  # > 64GB

    def test_valid_cpu_limits(self):
        """Test various valid CPU limit values."""
        valid_limits = [0.1, 0.5, 1.0, 2.0, 4.0, 8.0]
        for limit in valid_limits:
            config = DockerConfig(cpu_limit=limit)
            assert config.cpu_limit == limit

    def test_invalid_cpu_limit_type(self):
        """Test rejection of non-numeric CPU limits."""
        with pytest.raises(ValueError, match="must be numeric"):
            DockerConfig(cpu_limit="0.5")

    def test_invalid_cpu_limit_negative(self):
        """Test rejection of negative CPU limits."""
        with pytest.raises(ValueError, match="must be positive"):
            DockerConfig(cpu_limit=-1.0)

    def test_invalid_cpu_limit_zero(self):
        """Test rejection of zero CPU limit."""
        with pytest.raises(ValueError, match="must be positive"):
            DockerConfig(cpu_limit=0)

    def test_invalid_cpu_limit_too_high(self):
        """Test rejection of unreasonably high CPU limits."""
        with pytest.raises(ValueError, match="too high"):
            DockerConfig(cpu_limit=128)

    def test_valid_timeout_values(self):
        """Test various valid timeout values."""
        valid_timeouts = [1, 60, 300, 600, 1800, 3600]
        for timeout in valid_timeouts:
            config = DockerConfig(timeout_seconds=timeout)
            assert config.timeout_seconds == timeout

    def test_invalid_timeout_type(self):
        """Test rejection of non-integer timeout."""
        with pytest.raises(ValueError, match="must be integer"):
            DockerConfig(timeout_seconds=60.5)

    def test_invalid_timeout_negative(self):
        """Test rejection of negative timeout."""
        with pytest.raises(ValueError, match="must be positive"):
            DockerConfig(timeout_seconds=-1)

    def test_invalid_timeout_zero(self):
        """Test rejection of zero timeout."""
        with pytest.raises(ValueError, match="must be positive"):
            DockerConfig(timeout_seconds=0)

    def test_invalid_timeout_too_high(self):
        """Test rejection of timeout exceeding 1 hour."""
        with pytest.raises(ValueError, match="too high"):
            DockerConfig(timeout_seconds=7200)

    def test_valid_network_modes(self):
        """Test all valid network modes."""
        valid_modes = ["none", "bridge", "host"]
        for mode in valid_modes:
            config = DockerConfig(network_mode=mode)
            assert config.network_mode == mode

    def test_invalid_network_mode(self):
        """Test rejection of invalid network mode."""
        with pytest.raises(ValueError, match="Invalid network_mode"):
            DockerConfig(network_mode="invalid")

    def test_valid_tmpfs_size(self):
        """Test valid tmpfs size validation."""
        config = DockerConfig(tmpfs_size="512m")
        assert config.tmpfs_size == "512m"

    def test_invalid_tmpfs_size(self):
        """Test rejection of invalid tmpfs size."""
        with pytest.raises(ValueError, match="Invalid .* format"):
            DockerConfig(tmpfs_size="invalid")

    def test_valid_alert_threshold(self):
        """Test valid alert threshold values."""
        valid_thresholds = [0, 1, 3, 10]
        for threshold in valid_thresholds:
            config = DockerConfig(alert_on_orphaned_containers=threshold)
            assert config.alert_on_orphaned_containers == threshold

    def test_invalid_alert_threshold_type(self):
        """Test rejection of non-integer alert threshold."""
        with pytest.raises(ValueError, match="must be integer"):
            DockerConfig(alert_on_orphaned_containers=3.5)

    def test_invalid_alert_threshold_negative(self):
        """Test rejection of negative alert threshold."""
        with pytest.raises(ValueError, match="must be non-negative"):
            DockerConfig(alert_on_orphaned_containers=-1)

    def test_valid_prometheus_port(self):
        """Test valid prometheus port values."""
        valid_ports = [1024, 8000, 9090, 65535]
        for port in valid_ports:
            config = DockerConfig(prometheus_port=port)
            assert config.prometheus_port == port

    def test_invalid_prometheus_port_type(self):
        """Test rejection of non-integer prometheus port."""
        with pytest.raises(ValueError, match="must be integer"):
            DockerConfig(prometheus_port="8000")

    def test_invalid_prometheus_port_too_low(self):
        """Test rejection of prometheus port below 1024."""
        with pytest.raises(ValueError, match="must be in range"):
            DockerConfig(prometheus_port=80)

    def test_invalid_prometheus_port_too_high(self):
        """Test rejection of prometheus port above 65535."""
        with pytest.raises(ValueError, match="must be in range"):
            DockerConfig(prometheus_port=70000)


class TestDockerConfigYAMLLoading:
    """Test loading configuration from YAML files."""

    def test_load_from_nonexistent_file_uses_defaults(self):
        """Test loading from missing file returns default config."""
        config = DockerConfig.from_yaml("nonexistent.yaml")
        assert config.memory_limit == "2g"
        assert config.cpu_limit == 0.5

    def test_load_from_empty_file_uses_defaults(self):
        """Test loading from empty YAML file returns default config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            config = DockerConfig.from_yaml(temp_path)
            assert config.memory_limit == "2g"
            assert config.cpu_limit == 0.5
        finally:
            Path(temp_path).unlink()

    def test_load_from_valid_yaml(self):
        """Test loading from valid YAML configuration."""
        yaml_content = """
docker:
  enabled: false
  image: custom:image
  memory_limit: 4g
  cpu_limit: 1.0
  timeout_seconds: 300

monitoring:
  export_container_stats: false
  prometheus_port: 9090
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = DockerConfig.from_yaml(temp_path)
            assert config.enabled is False
            assert config.image == "custom:image"
            assert config.memory_limit == "4g"
            assert config.cpu_limit == 1.0
            assert config.timeout_seconds == 300
            assert config.export_container_stats is False
            assert config.prometheus_port == 9090
        finally:
            Path(temp_path).unlink()

    def test_load_with_partial_config_uses_defaults(self):
        """Test loading YAML with partial config merges with defaults."""
        yaml_content = """
docker:
  memory_limit: 4g
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            config = DockerConfig.from_yaml(temp_path)
            assert config.memory_limit == "4g"  # From YAML
            assert config.cpu_limit == 0.5  # Default
            assert config.enabled is True  # Default
        finally:
            Path(temp_path).unlink()

    def test_load_from_malformed_yaml(self):
        """Test loading from malformed YAML raises ValueError."""
        yaml_content = """
docker:
  enabled: true
  invalid yaml here
  more invalid: [
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Failed to parse YAML"):
                DockerConfig.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_with_invalid_parameters(self):
        """Test loading YAML with invalid parameters raises ValueError."""
        yaml_content = """
docker:
  cpu_limit: -1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="must be positive"):
                DockerConfig.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink()


class TestDockerConfigEnvVarSubstitution:
    """Test environment variable substitution in configuration."""

    def test_env_var_substitution_with_value(self):
        """Test environment variable is substituted when set."""
        yaml_content = """
docker:
  image: ${DOCKER_IMAGE}
  timeout_seconds: 600
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ['DOCKER_IMAGE'] = "custom:test"
            config = DockerConfig.from_yaml(temp_path)
            assert config.image == "custom:test"
        finally:
            os.environ.pop('DOCKER_IMAGE', None)
            Path(temp_path).unlink()

    def test_env_var_substitution_with_default(self):
        """Test environment variable uses default when not set."""
        yaml_content = """
docker:
  image: ${DOCKER_IMAGE:python:3.11-slim}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Ensure env var is not set
            os.environ.pop('DOCKER_IMAGE', None)
            config = DockerConfig.from_yaml(temp_path)
            assert config.image == "python:3.11-slim"
        finally:
            Path(temp_path).unlink()

    def test_env_var_substitution_empty_default(self):
        """Test environment variable with empty default when not set."""
        yaml_content = """
docker:
  seccomp_profile: ${SECCOMP_PROFILE:}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ.pop('SECCOMP_PROFILE', None)
            config = DockerConfig.from_yaml(temp_path)
            assert config.seccomp_profile == ""
        finally:
            Path(temp_path).unlink()

    def test_multiple_env_vars_in_same_value(self):
        """Test multiple environment variables in single value."""
        yaml_content = """
docker:
  image: ${REGISTRY}/python:${VERSION}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            os.environ['REGISTRY'] = "myregistry.com"
            os.environ['VERSION'] = "3.10"
            config = DockerConfig.from_yaml(temp_path)
            assert config.image == "myregistry.com/python:3.10"
        finally:
            os.environ.pop('REGISTRY', None)
            os.environ.pop('VERSION', None)
            Path(temp_path).unlink()


class TestDockerConfigToDictConversion:
    """Test conversion of config to dictionary format."""

    def test_to_dict_with_defaults(self):
        """Test to_dict() with default configuration."""
        config = DockerConfig()
        config_dict = config.to_dict()

        assert config_dict['docker']['enabled'] is True
        assert config_dict['docker']['image'] == "python:3.10-slim"
        assert config_dict['docker']['memory_limit'] == "2g"
        assert config_dict['docker']['cpu_limit'] == 0.5
        assert config_dict['docker']['tmpfs']['path'] == "/tmp"
        assert config_dict['monitoring']['export_container_stats'] is True

    def test_to_dict_with_custom_values(self):
        """Test to_dict() with custom configuration."""
        config = DockerConfig(
            enabled=False,
            memory_limit="4g",
            cpu_limit=1.0,
            prometheus_port=9090,
        )
        config_dict = config.to_dict()

        assert config_dict['docker']['enabled'] is False
        assert config_dict['docker']['memory_limit'] == "4g"
        assert config_dict['docker']['cpu_limit'] == 1.0
        assert config_dict['monitoring']['prometheus_port'] == 9090

    def test_to_dict_structure(self):
        """Test to_dict() returns correct nested structure."""
        config = DockerConfig()
        config_dict = config.to_dict()

        # Check top-level keys
        assert 'docker' in config_dict
        assert 'monitoring' in config_dict

        # Check docker section has all required keys
        docker_keys = [
            'enabled', 'image', 'memory_limit', 'memory_swap_limit',
            'cpu_limit', 'timeout_seconds', 'network_mode', 'read_only',
            'tmpfs', 'seccomp_profile', 'output_dir', 'cleanup_on_exit'
        ]
        for key in docker_keys:
            assert key in config_dict['docker']

        # Check tmpfs is nested dict
        assert isinstance(config_dict['docker']['tmpfs'], dict)
        assert 'path' in config_dict['docker']['tmpfs']
        assert 'size' in config_dict['docker']['tmpfs']
        assert 'options' in config_dict['docker']['tmpfs']

        # Check monitoring section has all required keys
        monitoring_keys = [
            'export_container_stats', 'alert_on_orphaned_containers',
            'prometheus_port'
        ]
        for key in monitoring_keys:
            assert key in config_dict['monitoring']


class TestDockerConfigIntegration:
    """Integration tests with actual config file."""

    def test_load_from_actual_config_file(self):
        """Test loading from actual config/docker_config.yaml."""
        config_path = "config/docker_config.yaml"
        if not Path(config_path).exists():
            pytest.skip("config/docker_config.yaml not found")

        config = DockerConfig.from_yaml(config_path)

        # Verify required security settings
        assert config.network_mode == "none", "Production config must use network isolation"
        assert config.read_only is True, "Production config must use read-only filesystem"
        assert config.cleanup_on_exit is True, "Production config must cleanup containers"

    def test_roundtrip_to_dict_and_back(self):
        """Test converting to dict and loading back preserves values."""
        original = DockerConfig(
            memory_limit="4g",
            cpu_limit=1.0,
            timeout_seconds=300,
        )

        config_dict = original.to_dict()

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_dict, f)
            temp_path = f.name

        try:
            loaded = DockerConfig.from_yaml(temp_path)
            assert loaded.memory_limit == original.memory_limit
            assert loaded.cpu_limit == original.cpu_limit
            assert loaded.timeout_seconds == original.timeout_seconds
        finally:
            Path(temp_path).unlink()
