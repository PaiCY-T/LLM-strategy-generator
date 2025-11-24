"""UnifiedLoop Configuration.

Provides unified configuration for UnifiedLoop, integrating parameters from both
AutonomousLoop and LearningLoop with Template Mode and JSON Parameter Output support.

This module supports the UnifiedLoop refactoring (Week 1-4) to create a single,
unified architecture that combines the best features of AutonomousLoop and LearningLoop.

Example Usage:
    ```python
    from src.learning.unified_config import UnifiedConfig

    # Create config with Template Mode
    config = UnifiedConfig(
        max_iterations=100,
        template_mode=True,
        template_name="Momentum",
        use_json_mode=True,
        enable_learning=True
    )

    # Convert to LearningConfig for LearningLoop
    learning_config = config.to_learning_config()

    # Validate configuration
    config.validate()
    ```

Design:
    - Integrates AutonomousLoop and LearningLoop parameters
    - Adds Template Mode and JSON Parameter Output support
    - Provides conversion to LearningConfig for compatibility
    - Includes comprehensive validation
    - Target: <100 lines of code

See Also:
    - src/learning/learning_config.py: Base LearningConfig
    - .spec-workflow/specs/unified-loop-refactor/design.md: Architecture design
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from src.learning.learning_config import LearningConfig

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


@dataclass
class UnifiedConfig:
    """Unified configuration for UnifiedLoop.

    Integrates parameters from AutonomousLoop and LearningLoop, adding support
    for Template Mode, JSON Parameter Output, Hybrid Mode, and Learning Feedback.

    Attributes:
        === Loop Control ===
        max_iterations: Maximum iterations to run (1-1000)
        continue_on_error: Continue if iteration fails

        === LLM Configuration ===
        llm_model: LLM model name
        api_key: API key (environment variable preferred)
        llm_timeout: LLM call timeout in seconds
        llm_temperature: LLM temperature parameter (0.0-2.0)
        llm_max_tokens: LLM max output tokens

        === Template Mode Parameters ===
        template_mode: Enable Template Mode (uses TemplateIterationExecutor)
        template_name: Template name (e.g., "Momentum", "Factor")

        === JSON Parameter Output Parameters ===
        use_json_mode: Enable JSON Parameter Output (requires template_mode=True)

        === Hybrid Mode Parameters ===
        innovation_rate: LLM probability percentage (0.0-100.0)
            - 100.0: Pure LLM mode (100% LLM generation)
            - 50.0: Hybrid mode (50% LLM, 50% Factor Graph)
            - 0.0: Pure Factor Graph mode (100% Factor Graph)
            Default: 100.0 (backward compatible with pure LLM mode)

        === Learning Feedback Parameters ===
        enable_learning: Enable Learning Feedback system
        history_window: Recent iterations for feedback generation

        === Monitoring Parameters ===
        enable_monitoring: Enable monitoring system (MetricsCollector, etc.)

        === Docker Sandbox Parameters ===
        use_docker: Enable Docker sandbox for strategy execution

        === Backtest Configuration ===
        timeout_seconds: Backtest timeout in seconds
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        fee_ratio: Transaction fee ratio (0.0-0.1)
        tax_ratio: Transaction tax ratio (0.0-0.1)
        resample: Rebalancing frequency (D/W/M)

        === History & Files ===
        history_file: JSONL history file path
        champion_file: Champion JSON file path
        log_dir: Log directory path
        config_file: Config YAML file path

        === Logging ===
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_to_file: Write logs to file
        log_to_console: Write logs to console

    Validation Rules:
        - innovation_rate must be in range [0.0, 100.0]
        - use_json_mode=True requires template_mode=True AND innovation_rate=100.0
        - template_mode=True requires template_name to be specified
        - max_iterations must be in range [1, 1000]

    Example:
        >>> # Pure LLM mode (default)
        >>> config = UnifiedConfig(max_iterations=100)
        >>> assert config.innovation_rate == 100.0

        >>> # Hybrid mode (50% LLM, 50% Factor Graph)
        >>> config = UnifiedConfig(
        ...     max_iterations=100,
        ...     innovation_rate=50.0
        ... )

        >>> # Pure Factor Graph mode
        >>> config = UnifiedConfig(
        ...     max_iterations=100,
        ...     innovation_rate=0.0
        ... )
    """

    # === Loop Control ===
    max_iterations: int = 10
    continue_on_error: bool = False

    # === LLM Configuration ===
    llm_model: str = "gemini-2.5-flash"
    api_key: Optional[str] = None
    llm_timeout: int = 60
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000

    # === Template Mode Parameters ===
    template_mode: bool = False
    template_name: str = "Momentum"

    # === JSON Parameter Output Parameters ===
    use_json_mode: bool = False

    # === Hybrid Mode Parameters ===
    innovation_rate: float = 100.0  # 0.0-100.0, LLM probability %
    # 100.0 = Pure LLM mode (default, backward compatible)
    # 50.0 = Hybrid mode (50% LLM, 50% Factor Graph)
    # 0.0 = Pure Factor Graph mode

    # === Learning Feedback Parameters ===
    enable_learning: bool = True
    history_window: int = 10

    # === Monitoring Parameters ===
    enable_monitoring: bool = True

    # === Docker Sandbox Parameters ===
    use_docker: bool = False  # Default False for compatibility

    # === Backtest Configuration ===
    timeout_seconds: int = 420
    start_date: str = "2018-01-01"
    end_date: str = "2024-12-31"
    fee_ratio: float = 0.001425
    tax_ratio: float = 0.003
    resample: str = "M"

    # === History & Files ===
    history_file: str = "artifacts/data/iterations.jsonl"
    champion_file: str = "artifacts/data/champion.json"
    log_dir: str = "logs"
    config_file: str = "config/learning_system.yaml"

    # === Logging ===
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration parameters.

        Raises:
            ConfigurationError: If any parameter is invalid
            ValueError: If numeric parameter is out of range
        """
        self._validate_template_mode()
        self._validate_innovation_rate()
        self._validate_json_mode_compatibility()
        self._validate_file_paths()
        self._validate_iteration_count()

    def _validate_template_mode(self) -> None:
        """Validate Template Mode configuration.

        Raises:
            ConfigurationError: If template_mode=True but template_name is not set
        """
        if self.template_mode and not self.template_name:
            raise ConfigurationError(
                "template_mode=True requires template_name to be specified"
            )

    def _validate_innovation_rate(self) -> None:
        """Validate innovation_rate parameter.

        Raises:
            ValueError: If innovation_rate is not in range [0.0, 100.0]
        """
        if not 0.0 <= self.innovation_rate <= 100.0:
            raise ValueError(
                f"innovation_rate must be between 0.0 and 100.0, got {self.innovation_rate}"
            )

    def _validate_json_mode_compatibility(self) -> None:
        """Validate JSON Mode compatibility with other parameters.

        JSON Mode requires:
        - template_mode=True
        - innovation_rate=100.0 (pure template mode, no LLM mixing)

        Raises:
            ConfigurationError: If JSON Mode requirements are not met
        """
        if self.use_json_mode and not self.template_mode:
            raise ConfigurationError(
                "use_json_mode=True requires template_mode=True"
            )

        if self.use_json_mode and self.innovation_rate < 100.0:
            raise ConfigurationError(
                f"use_json_mode=True requires innovation_rate=100 (pure template mode). "
                f"Got innovation_rate={self.innovation_rate}"
            )

    def _validate_file_paths(self) -> None:
        """Validate required file paths.

        Raises:
            ConfigurationError: If required file paths are not set
        """
        if not self.history_file:
            raise ConfigurationError("history_file is required")

        if not self.champion_file:
            raise ConfigurationError("champion_file is required")

    def _validate_iteration_count(self) -> None:
        """Validate iteration count range.

        Raises:
            ConfigurationError: If iteration count is invalid
        """
        if self.max_iterations <= 0:
            raise ConfigurationError(
                f"max_iterations must be > 0, got {self.max_iterations}"
            )

        if self.max_iterations > 1000:
            raise ConfigurationError(
                f"max_iterations too large (> 1000): {self.max_iterations}"
            )

    def to_learning_config(self) -> LearningConfig:
        """Convert to LearningConfig for LearningLoop compatibility.

        Maps UnifiedConfig parameters to LearningConfig, preserving all
        necessary configuration for the LearningLoop orchestrator.

        Returns:
            LearningConfig: Configuration for LearningLoop

        Example:
            >>> config = UnifiedConfig(max_iterations=50, template_mode=True)
            >>> learning_config = config.to_learning_config()
            >>> learning_config.max_iterations
            50
        """
        return LearningConfig(
            # Loop Control
            max_iterations=self.max_iterations,
            continue_on_error=self.continue_on_error,

            # LLM Configuration
            llm_model=self.llm_model,
            api_key=self.api_key,
            llm_timeout=self.llm_timeout,
            llm_temperature=self.llm_temperature,
            llm_max_tokens=self.llm_max_tokens,

            # Innovation Mode (mapped from template settings)
            innovation_mode=self.enable_learning,
            innovation_rate=int(self.innovation_rate),  # Convert float to int for LearningConfig
            llm_retry_count=3,

            # Backtest Configuration
            timeout_seconds=self.timeout_seconds,
            start_date=self.start_date,
            end_date=self.end_date,
            fee_ratio=self.fee_ratio,
            tax_ratio=self.tax_ratio,
            resample=self.resample,

            # History & Files
            history_file=self.history_file,
            history_window=self.history_window,
            champion_file=self.champion_file,
            log_dir=self.log_dir,
            config_file=self.config_file,

            # Logging
            log_level=self.log_level,
            log_to_file=self.log_to_file,
            log_to_console=self.log_to_console,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary of all configuration parameters
        """
        return {
            # Loop Control
            "max_iterations": self.max_iterations,
            "continue_on_error": self.continue_on_error,

            # LLM Configuration
            "llm_model": self.llm_model,
            "api_key": "***" if self.api_key else None,  # Mask API key
            "llm_timeout": self.llm_timeout,
            "llm_temperature": self.llm_temperature,
            "llm_max_tokens": self.llm_max_tokens,

            # Template Mode
            "template_mode": self.template_mode,
            "template_name": self.template_name,

            # JSON Parameter Output
            "use_json_mode": self.use_json_mode,

            # Hybrid Mode
            "innovation_rate": self.innovation_rate,

            # Learning Feedback
            "enable_learning": self.enable_learning,
            "history_window": self.history_window,

            # Monitoring
            "enable_monitoring": self.enable_monitoring,

            # Docker Sandbox
            "use_docker": self.use_docker,

            # Backtest Configuration
            "timeout_seconds": self.timeout_seconds,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "fee_ratio": self.fee_ratio,
            "tax_ratio": self.tax_ratio,
            "resample": self.resample,

            # History & Files
            "history_file": self.history_file,
            "champion_file": self.champion_file,
            "log_dir": self.log_dir,
            "config_file": self.config_file,

            # Logging
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_to_console": self.log_to_console,
        }
