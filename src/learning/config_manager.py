"""Centralized configuration management for learning system.

This module provides a singleton ConfigManager for loading and caching
configuration from config/learning_system.yaml. It eliminates config loading
duplication across the codebase and provides thread-safe access to config values.

Typical Usage:
    >>> from src.learning.config_manager import ConfigManager
    >>> config_manager = ConfigManager.get_instance()
    >>> config = config_manager.load_config()
    >>> llm_enabled = config_manager.get('llm.enabled', False)

Thread Safety:
    The singleton pattern is implemented with thread-safe instance creation.
    Config loading is protected against concurrent access.
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Singleton manager for centralized configuration access.

    This class provides thread-safe singleton access to configuration loaded
    from config/learning_system.yaml. It caches the loaded configuration to
    avoid repeated file I/O operations.

    Attributes:
        _instance: Singleton instance of ConfigManager
        _config: Cached configuration dictionary
        _lock: Threading lock for thread-safe operations
    """

    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ConfigManager':
        """Create or return singleton instance.

        Thread-safe singleton implementation using double-checked locking.

        Returns:
            ConfigManager: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'ConfigManager':
        """Get the singleton instance of ConfigManager.

        This is the recommended way to access the ConfigManager.

        Returns:
            ConfigManager: The singleton instance

        Example:
            >>> config_manager = ConfigManager.get_instance()
            >>> config = config_manager.load_config()
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_config(
        self,
        config_path: str = "config/learning_system.yaml",
        force_reload: bool = False
    ) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Loads configuration from the specified path and caches it for future
        access. If configuration is already loaded, returns cached version
        unless force_reload is True.

        Args:
            config_path: Path to configuration file, relative to project root
                        or absolute path. Defaults to "config/learning_system.yaml"
            force_reload: If True, reload configuration even if cached.
                         Defaults to False.

        Returns:
            Dict[str, Any]: Configuration dictionary

        Raises:
            FileNotFoundError: If config file does not exist
            yaml.YAMLError: If YAML file is malformed

        Example:
            >>> config_manager = ConfigManager.get_instance()
            >>> config = config_manager.load_config()
            >>> config = config_manager.load_config(force_reload=True)
        """
        with self._lock:
            # Return cached config unless force_reload is requested
            if self._config is not None and not force_reload:
                return self._config

            # Resolve config path relative to project root
            resolved_path = self._resolve_config_path(config_path)

            # Check if file exists
            if not resolved_path.exists():
                raise FileNotFoundError(
                    f"Configuration file not found: {config_path}\n"
                    f"Resolved path: {resolved_path}\n"
                    f"Current working directory: {os.getcwd()}"
                )

            # Load YAML configuration
            try:
                with open(resolved_path, 'r') as f:
                    self._config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(
                    f"Failed to parse YAML configuration: {config_path}\n"
                    f"Error: {e}"
                ) from e

            return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key with optional default.

        Supports nested key access using dot notation (e.g., 'llm.enabled').
        If configuration is not loaded, loads it automatically.

        Args:
            key: Configuration key (supports dot notation for nested access)
            default: Default value to return if key not found

        Returns:
            Any: Configuration value or default if not found

        Example:
            >>> config_manager = ConfigManager.get_instance()
            >>> llm_enabled = config_manager.get('llm.enabled', False)
            >>> sandbox_config = config_manager.get('sandbox', {})
        """
        # Load config if not already loaded
        if self._config is None:
            self.load_config()

        # Support dot notation for nested keys
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def _resolve_config_path(self, config_path: str) -> Path:
        """Resolve configuration path relative to project root.

        If config_path is absolute, returns it as-is. If relative, resolves
        it relative to the project root directory.

        Args:
            config_path: Configuration file path (absolute or relative)

        Returns:
            Path: Resolved absolute path to configuration file
        """
        path = Path(config_path)

        # If absolute path, return as-is
        if path.is_absolute():
            return path

        # Try relative to project root
        # This file is in src/learning/, so project root is ../..
        project_root = Path(__file__).parent.parent.parent
        resolved_path = project_root / config_path

        return resolved_path

    def clear_cache(self) -> None:
        """Clear cached configuration.

        Forces next load_config() call to reload from disk.
        Useful for testing or runtime configuration updates.

        Example:
            >>> config_manager = ConfigManager.get_instance()
            >>> config_manager.clear_cache()
            >>> config = config_manager.load_config()  # Reloads from disk
        """
        with self._lock:
            self._config = None

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing only).

        WARNING: This method is intended for testing purposes only.
        It clears the singleton instance and cached configuration.
        Do not use in production code.

        Example:
            >>> ConfigManager.reset_instance()
            >>> config_manager = ConfigManager.get_instance()  # New instance
        """
        with cls._lock:
            cls._instance = None
            cls._config = None
