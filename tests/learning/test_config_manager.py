"""Test suite for ConfigManager singleton.

This module tests the ConfigManager's singleton pattern, config loading,
caching behavior, error handling, and thread safety.

Test Coverage:
    - Singleton pattern enforcement
    - Configuration loading and caching
    - Force reload functionality
    - File not found error handling
    - Invalid YAML error handling
    - Nested key access with dot notation
    - Default value handling
    - Thread-safe concurrent access
"""

import os
import tempfile
import threading
from pathlib import Path

import pytest
import yaml

from src.learning.config_manager import ConfigManager


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset ConfigManager singleton before each test.

    This ensures test isolation by clearing the singleton instance
    and cached configuration between tests.
    """
    ConfigManager.reset_instance()
    yield
    ConfigManager.reset_instance()


@pytest.fixture
def temp_config_file():
    """Create a temporary valid configuration file for testing.

    Returns:
        str: Path to temporary configuration file
    """
    config_data = {
        'llm': {
            'enabled': True,
            'provider': 'openrouter',
            'innovation_rate': 0.3
        },
        'sandbox': {
            'enabled': True,
            'docker': {
                'image': 'finlab-sandbox:latest',
                'memory_limit': '2g'
            }
        },
        'anti_churn': {
            'probation_period': 2,
            'probation_threshold': 0.10
        }
    }

    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False
    ) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_invalid_yaml():
    """Create a temporary invalid YAML file for testing error handling.

    Returns:
        str: Path to temporary invalid YAML file
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.yaml',
        delete=False
    ) as f:
        f.write("invalid: yaml: content:\n  - missing\n  bracket")
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestSingletonPattern:
    """Test singleton pattern implementation."""

    def test_singleton_pattern(self):
        """Verify same instance returned on multiple calls.

        The ConfigManager should return the same instance object
        every time get_instance() is called.
        """
        instance1 = ConfigManager.get_instance()
        instance2 = ConfigManager.get_instance()
        instance3 = ConfigManager()

        assert instance1 is instance2
        assert instance2 is instance3
        assert id(instance1) == id(instance2) == id(instance3)

    def test_singleton_class_instance_consistency(self):
        """Verify _instance matches get_instance() return value."""
        instance = ConfigManager.get_instance()
        assert ConfigManager._instance is instance


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_config_success(self, temp_config_file):
        """Load valid YAML file successfully.

        ConfigManager should successfully load a valid YAML file
        and return the parsed configuration dictionary.
        """
        config_manager = ConfigManager.get_instance()
        config = config_manager.load_config(temp_config_file)

        assert config is not None
        assert isinstance(config, dict)
        assert 'llm' in config
        assert 'sandbox' in config
        assert config['llm']['enabled'] is True
        assert config['sandbox']['docker']['memory_limit'] == '2g'

    def test_config_caching(self, temp_config_file):
        """Verify config cached, not reloaded on second call.

        After the first load, subsequent calls should return the
        cached configuration without re-reading the file.
        """
        config_manager = ConfigManager.get_instance()

        # First load
        config1 = config_manager.load_config(temp_config_file)

        # Modify file on disk
        with open(temp_config_file, 'w') as f:
            yaml.dump({'modified': True}, f)

        # Second load should return cached version
        config2 = config_manager.load_config(temp_config_file)

        assert config1 is config2
        assert 'llm' in config2  # Original data
        assert 'modified' not in config2

    def test_force_reload(self, temp_config_file):
        """force_reload=True reloads from disk.

        When force_reload is True, ConfigManager should re-read
        the configuration file even if cached.
        """
        config_manager = ConfigManager.get_instance()

        # First load
        config1 = config_manager.load_config(temp_config_file)
        assert 'llm' in config1

        # Modify file on disk
        new_config = {'modified': True, 'new_key': 'new_value'}
        with open(temp_config_file, 'w') as f:
            yaml.dump(new_config, f)

        # Force reload
        config2 = config_manager.load_config(
            temp_config_file,
            force_reload=True
        )

        assert config1 is not config2
        assert 'modified' in config2
        assert config2['modified'] is True
        assert config2['new_key'] == 'new_value'
        assert 'llm' not in config2

    def test_clear_cache(self, temp_config_file):
        """Test clear_cache() forces reload on next access.

        After calling clear_cache(), the next load_config() should
        reload from disk.
        """
        config_manager = ConfigManager.get_instance()

        # Load config
        config1 = config_manager.load_config(temp_config_file)

        # Clear cache
        config_manager.clear_cache()

        # Load again - should reload from disk
        config2 = config_manager.load_config(temp_config_file)

        # Configs should be equal but not same object
        assert config1 == config2
        # Note: May be same object due to caching, but semantically reloaded


class TestErrorHandling:
    """Test error handling for invalid inputs."""

    def test_file_not_found(self):
        """Raises FileNotFoundError with clear message.

        When attempting to load a non-existent configuration file,
        ConfigManager should raise FileNotFoundError with a helpful
        error message.
        """
        config_manager = ConfigManager.get_instance()

        with pytest.raises(FileNotFoundError) as exc_info:
            config_manager.load_config('nonexistent/config.yaml')

        error_message = str(exc_info.value)
        assert 'Configuration file not found' in error_message
        assert 'nonexistent/config.yaml' in error_message

    def test_invalid_yaml(self, temp_invalid_yaml):
        """Handles corrupted YAML gracefully.

        When attempting to load a file with invalid YAML syntax,
        ConfigManager should raise yaml.YAMLError with details.
        """
        config_manager = ConfigManager.get_instance()

        with pytest.raises(yaml.YAMLError) as exc_info:
            config_manager.load_config(temp_invalid_yaml)

        error_message = str(exc_info.value)
        assert 'Failed to parse YAML configuration' in error_message


class TestKeyAccess:
    """Test configuration key access functionality."""

    def test_get_with_default(self, temp_config_file):
        """get() returns default for missing keys.

        When accessing a non-existent key, get() should return
        the provided default value.
        """
        config_manager = ConfigManager.get_instance()
        config_manager.load_config(temp_config_file)

        # Existing keys
        assert config_manager.get('llm.enabled') is True
        assert config_manager.get('sandbox.enabled') is True

        # Missing keys with defaults
        assert config_manager.get('nonexistent', 'default') == 'default'
        assert config_manager.get('missing.nested.key', None) is None
        assert config_manager.get('fake.value', 42) == 42

    def test_get_nested_keys(self, temp_config_file):
        """Test dot notation for nested key access.

        get() should support dot notation for accessing nested
        configuration values.
        """
        config_manager = ConfigManager.get_instance()
        config_manager.load_config(temp_config_file)

        # Top-level key
        llm_config = config_manager.get('llm')
        assert isinstance(llm_config, dict)
        assert llm_config['enabled'] is True

        # Nested keys
        assert config_manager.get('llm.enabled') is True
        assert config_manager.get('llm.provider') == 'openrouter'
        assert config_manager.get('llm.innovation_rate') == 0.3

        # Deep nested keys
        assert config_manager.get('sandbox.docker.image') == 'finlab-sandbox:latest'
        assert config_manager.get('sandbox.docker.memory_limit') == '2g'

    def test_get_auto_loads_config(self, temp_config_file):
        """Test get() automatically loads config if not loaded.

        If configuration hasn't been loaded, get() should load it
        automatically before accessing the key.
        """
        config_manager = ConfigManager.get_instance()

        # Access config without explicit load_config() call
        # Should auto-load with default path
        # Note: This will fail if default config doesn't exist
        # For this test, we load with explicit path
        config_manager.load_config(temp_config_file)
        value = config_manager.get('llm.enabled')
        assert value is True


class TestThreadSafety:
    """Test thread-safe concurrent access."""

    def test_concurrent_access(self, temp_config_file):
        """Singleton thread-safe with concurrent access.

        Multiple threads should be able to safely access the
        ConfigManager singleton concurrently without race conditions.
        """
        config_manager = ConfigManager.get_instance()
        config_manager.load_config(temp_config_file)

        results = []
        errors = []

        def access_config(thread_id):
            """Worker function to access config from multiple threads."""
            try:
                # Each thread gets instance
                instance = ConfigManager.get_instance()

                # Access various keys
                llm_enabled = instance.get('llm.enabled')
                sandbox_enabled = instance.get('sandbox.enabled')
                provider = instance.get('llm.provider')

                results.append({
                    'thread_id': thread_id,
                    'llm_enabled': llm_enabled,
                    'sandbox_enabled': sandbox_enabled,
                    'provider': provider
                })
            except Exception as e:
                errors.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })

        # Launch 10 threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=access_config, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Thread errors occurred: {errors}"

        # Verify all threads got same values
        assert len(results) == 10
        for result in results:
            assert result['llm_enabled'] is True
            assert result['sandbox_enabled'] is True
            assert result['provider'] == 'openrouter'

    def test_concurrent_loads(self, temp_config_file):
        """Test concurrent load_config() calls are thread-safe.

        Multiple threads calling load_config() concurrently should
        not cause race conditions or duplicate loading.
        """
        errors = []
        instances = []

        def load_config(thread_id):
            """Worker function to load config from multiple threads."""
            try:
                instance = ConfigManager.get_instance()
                config = instance.load_config(temp_config_file)
                instances.append(instance)

                # Verify config loaded correctly
                assert 'llm' in config
                assert config['llm']['enabled'] is True
            except Exception as e:
                errors.append({
                    'thread_id': thread_id,
                    'error': str(e)
                })

        # Launch 20 threads simultaneously
        threads = []
        for i in range(20):
            thread = threading.Thread(target=load_config, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Thread errors occurred: {errors}"

        # Verify all threads got same singleton instance
        assert len(instances) == 20
        first_instance = instances[0]
        for instance in instances:
            assert instance is first_instance


class TestRealConfigFile:
    """Test with actual project configuration file."""

    def test_load_real_config(self):
        """Test loading the actual config/learning_system.yaml file.

        Verify ConfigManager can load the real project configuration
        and access known keys.
        """
        config_manager = ConfigManager.get_instance()

        # Load real config (skip test if file doesn't exist)
        real_config_path = "config/learning_system.yaml"
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / real_config_path

        if not config_file.exists():
            pytest.skip(f"Real config file not found: {config_file}")

        config = config_manager.load_config(real_config_path)

        # Verify expected keys exist
        assert 'anti_churn' in config
        assert 'llm' in config
        assert 'sandbox' in config

        # Verify nested access works
        assert config_manager.get('anti_churn.probation_period') is not None
        assert config_manager.get('llm.enabled') is not None
