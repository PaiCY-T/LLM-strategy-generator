"""
Configuration Management for Finlab Backtesting Optimization System.

This module provides centralized configuration management using a Settings class
that handles Finlab API configuration, file paths, logging settings, and UI language.

Environment Variables:
    FINLAB_API_TOKEN: Required. Finlab API authentication token
    CLAUDE_API_KEY: Required. Claude API key for AI analysis
    LOG_LEVEL: Optional. Logging level (default: INFO)
    UI_LANGUAGE: Optional. UI language (default: zh-TW)

Example:
    >>> from config.settings import Settings
    >>> settings = Settings()
    >>> print(settings.finlab_api_token)
    >>> print(settings.data_cache_path)
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Type aliases for clarity
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
UILanguage = Literal["zh-TW", "en-US"]

# Valid values for runtime validation
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
VALID_UI_LANGUAGES = {"zh-TW", "en-US"}


@dataclass
class FinlabConfig:
    """Finlab API configuration settings."""

    api_token: str
    storage_path: Path = field(default_factory=lambda: Path("./data/finlab_cache"))
    cache_retention_days: int = 30
    default_datasets: list[str] = field(
        default_factory=lambda: [
            "price:收盤價",
            "price:開盤價",
            "price:最高價",
            "price:最低價",
        ]
    )


@dataclass
class BacktestConfig:
    """Backtesting engine configuration settings."""

    default_fee_ratio: float = 0.001425  # Taiwan stock transaction fee
    default_tax_ratio: float = 0.003  # Taiwan stock transaction tax
    default_resample: str = "D"  # Daily resampling
    timeout_seconds: int = 120


@dataclass
class AnalysisConfig:
    """AI analysis engine configuration settings."""

    claude_api_key: str
    claude_model: str = "claude-sonnet-4.5"
    max_suggestions: int = 5
    min_suggestions: int = 3
    suggestion_categories: list[str] = field(
        default_factory=lambda: [
            "risk_management",
            "entry_exit_conditions",
            "position_sizing",
            "timing_optimization",
        ]
    )


@dataclass
class StorageConfig:
    """Storage and database configuration settings."""

    database_path: Path = field(
        default_factory=lambda: Path("./storage/iterations.db")
    )
    backup_path: Path = field(default_factory=lambda: Path("./storage/backups"))
    backup_retention_days: int = 30


@dataclass
class UIConfig:
    """User interface configuration settings."""

    default_language: UILanguage = "zh-TW"
    theme: str = "light"
    chart_colors: dict[str, str] = field(
        default_factory=lambda: {
            "profit": "#4CAF50",
            "loss": "#F44336",
            "neutral": "#2196F3",
        }
    )


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    level: LogLevel = "INFO"
    log_dir: Path = field(default_factory=lambda: Path("./logs"))
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class Settings:
    """
    Centralized configuration management for the application.

    Loads configuration from environment variables and provides typed access
    to all configuration settings across different subsystems.

    Attributes:
        finlab: Finlab API configuration
        backtest: Backtesting engine configuration
        analysis: AI analysis engine configuration
        storage: Storage and database configuration
        ui: User interface configuration
        logging: Logging configuration

    Raises:
        ValueError: If required environment variables are missing

    Example:
        >>> settings = Settings()
        >>> print(settings.finlab.api_token)
        >>> print(settings.ui.default_language)
    """

    def __init__(self) -> None:
        """
        Initialize Settings by loading from environment variables.

        Raises:
            ValueError: If FINLAB_API_TOKEN or CLAUDE_API_KEY are not set
        """
        # Validate required environment variables
        finlab_token = os.getenv("FINLAB_API_TOKEN")
        claude_key = os.getenv("CLAUDE_API_KEY")

        if not finlab_token:
            raise ValueError(
                "FINLAB_API_TOKEN environment variable is required. "
                "Please set it in .env file or environment."
            )

        if not claude_key:
            raise ValueError(
                "CLAUDE_API_KEY environment variable is required. "
                "Please set it in .env file or environment."
            )

        # Initialize configuration sections
        self.finlab = FinlabConfig(api_token=finlab_token)

        self.backtest = BacktestConfig()

        self.analysis = AnalysisConfig(claude_api_key=claude_key)

        self.storage = StorageConfig()

        # Validate and set UI language
        ui_lang = os.getenv("UI_LANGUAGE", "zh-TW")
        if ui_lang not in VALID_UI_LANGUAGES:
            raise ValueError(
                f"Invalid UI_LANGUAGE '{ui_lang}'. "
                f"Must be one of {', '.join(sorted(VALID_UI_LANGUAGES))}"
            )
        self.ui = UIConfig(default_language=ui_lang)  # type: ignore[arg-type]

        # Validate and set log level
        log_level = os.getenv("LOG_LEVEL", "INFO")
        if log_level not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid LOG_LEVEL '{log_level}'. "
                f"Must be one of {', '.join(sorted(VALID_LOG_LEVELS))}"
            )
        self.logging = LoggingConfig(level=log_level)  # type: ignore[arg-type]

        # Create necessary directories
        self._create_directories()

    def _create_directories(self) -> None:
        """Create required directories if they don't exist."""
        directories = [
            self.finlab.storage_path,
            self.storage.database_path.parent,
            self.storage.backup_path,
            self.logging.log_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def finlab_api_token(self) -> str:
        """Get Finlab API token."""
        return self.finlab.api_token

    @property
    def claude_api_key(self) -> str:
        """Get Claude API key."""
        return self.analysis.claude_api_key

    @property
    def data_cache_path(self) -> Path:
        """Get data cache directory path."""
        return self.finlab.storage_path

    @property
    def database_path(self) -> Path:
        """Get database file path."""
        return self.storage.database_path

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.logging.level

    @property
    def ui_language(self) -> str:
        """Get UI language setting."""
        return self.ui.default_language

    def __repr__(self) -> str:
        """Return string representation masking sensitive data."""
        return (
            f"Settings("
            f"finlab_token=*****, "
            f"claude_key=*****, "
            f"language={self.ui_language}, "
            f"log_level={self.log_level})"
        )
