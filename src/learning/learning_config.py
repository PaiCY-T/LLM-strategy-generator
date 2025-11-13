"""Learning Loop Configuration for Phase 6.

Provides comprehensive configuration management with:
- 21 parameters covering all aspects of learning loop
- YAML file loading with environment variable support
- Complete validation with clear error messages
- Type-safe dataclass structure
"""

import os
import yaml
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class LearningConfig:
    """Complete configuration for learning loop.

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

        === Innovation Mode ===
        innovation_mode: Enable LLM innovation
        innovation_rate: LLM vs Factor Graph ratio (0-100)
        llm_retry_count: LLM retries before Factor Graph fallback

        === Backtest Configuration ===
        timeout_seconds: Backtest timeout in seconds
        start_date: Backtest start date (YYYY-MM-DD)
        end_date: Backtest end date (YYYY-MM-DD)
        fee_ratio: Transaction fee ratio (0.0-0.1)
        tax_ratio: Transaction tax ratio (0.0-0.1)
        resample: Rebalancing frequency (D/W/M)

        === History & Files ===
        history_file: JSONL history file path
        history_window: Recent iterations for feedback
        champion_file: Champion JSON file path
        log_dir: Log directory path
        config_file: Config YAML file path

        === Logging ===
        log_level: Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)
        log_to_file: Write logs to file
        log_to_console: Write logs to console
    """

    # === Loop Control ===
    max_iterations: int = 20
    continue_on_error: bool = False

    # === LLM Configuration ===
    llm_model: str = "gemini-2.5-flash"
    api_key: Optional[str] = None
    llm_timeout: int = 60
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000

    # === Innovation Mode ===
    innovation_mode: bool = True
    innovation_rate: int = 100  # 100 = always LLM, 0 = always Factor Graph
    llm_retry_count: int = 3

    # === Backtest Configuration ===
    timeout_seconds: int = 420
    start_date: str = "2018-01-01"
    end_date: str = "2024-12-31"
    fee_ratio: float = 0.001425
    tax_ratio: float = 0.003
    resample: str = "M"  # Monthly

    # === History & Files ===
    history_file: str = "artifacts/data/innovations.jsonl"
    history_window: int = 5
    champion_file: str = "artifacts/data/champion.json"
    log_dir: str = "logs"
    config_file: str = "config/learning_system.yaml"

    # === Logging ===
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all configuration parameters.

        Raises:
            ValueError: If any parameter is invalid with clear error message
        """
        # 1. Iteration count
        if not isinstance(self.max_iterations, int):
            raise ValueError(f"max_iterations must be int, got {type(self.max_iterations).__name__}")
        if self.max_iterations <= 0:
            raise ValueError(f"max_iterations must be > 0, got {self.max_iterations}")
        if self.max_iterations > 1000:
            raise ValueError(f"max_iterations too large (> 1000): {self.max_iterations}")

        # 2. Innovation rate
        if not isinstance(self.innovation_rate, int):
            raise ValueError(f"innovation_rate must be int, got {type(self.innovation_rate).__name__}")
        if not 0 <= self.innovation_rate <= 100:
            raise ValueError(f"innovation_rate must be 0-100, got {self.innovation_rate}")

        # 3. Timeouts
        if self.timeout_seconds < 60:
            raise ValueError(f"timeout_seconds must be >= 60, got {self.timeout_seconds}")
        if self.llm_timeout < 10:
            raise ValueError(f"llm_timeout must be >= 10, got {self.llm_timeout}")

        # 4. Temperature
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError(f"llm_temperature must be 0.0-2.0, got {self.llm_temperature}")

        # 5. Max tokens
        if self.llm_max_tokens < 100:
            raise ValueError(f"llm_max_tokens must be >= 100, got {self.llm_max_tokens}")

        # 6. Date format and range validation
        try:
            start_dt = datetime.strptime(self.start_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"start_date invalid format (use YYYY-MM-DD): {self.start_date}")

        try:
            end_dt = datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"end_date invalid format (use YYYY-MM-DD): {self.end_date}")

        # Validate date range: start must be before end
        if start_dt >= end_dt:
            raise ValueError(
                f"start_date must be before end_date (got {self.start_date} >= {self.end_date})"
            )

        # 7. Resample frequency
        if self.resample not in ("D", "W", "M"):
            raise ValueError(f"resample must be D/W/M, got '{self.resample}'")

        # 8. Fee and tax ratios
        if not 0 <= self.fee_ratio < 0.1:
            raise ValueError(f"fee_ratio must be 0-0.1, got {self.fee_ratio}")
        if not 0 <= self.tax_ratio < 0.1:
            raise ValueError(f"tax_ratio must be 0-0.1, got {self.tax_ratio}")

        # 9. History window
        if self.history_window < 1:
            raise ValueError(f"history_window must be >= 1, got {self.history_window}")

        # 10. Log level
        valid_levels = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        if self.log_level not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got '{self.log_level}'")

        # 11. Retry count
        if self.llm_retry_count < 1:
            raise ValueError(f"llm_retry_count must be >= 1, got {self.llm_retry_count}")

    @classmethod
    def from_yaml(cls, config_path: str) -> "LearningConfig":
        """Load configuration from YAML file.

        Supports both nested structure (learning_system.yaml) and flat structure.
        Maps nested keys to flat LearningConfig attributes.

        Args:
            config_path: Path to YAML config file

        Returns:
            LearningConfig instance

        Example:
            >>> config = LearningConfig.from_yaml("config/learning_system.yaml")
            >>> config.max_iterations
            20
        """
        if not os.path.exists(config_path):
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return cls()  # Use defaults

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f)

            if not raw_config:
                logger.warning(f"Empty config file: {config_path}, using defaults")
                return cls()

            # Map nested structure to flat config
            config_dict = cls._map_nested_config(raw_config)

            # Environment variable override for API key
            if 'api_key' not in config_dict or not config_dict.get('api_key'):
                env_key = os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
                if env_key:
                    config_dict['api_key'] = env_key
                    logger.debug("Using API key from environment variable")

            # Add config_file path
            config_dict['config_file'] = config_path

            # Create instance with config
            return cls(**config_dict)

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {config_path}: {e}")
        except TypeError as e:
            raise ValueError(f"Invalid config parameters in {config_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise

    @staticmethod
    def _resolve_env_var(value: Any, default: Any, value_type: type = str) -> Any:
        """Resolve environment variable placeholder or return value.

        Args:
            value: Raw value (may contain ${ENV_VAR:default})
            default: Default value if resolution fails
            value_type: Type to convert to (int, float, str, bool)

        Returns:
            Resolved and typed value
        """
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            # Extract env var name and default: ${VAR_NAME:default_value}
            inner = value[2:-1]  # Remove ${ and }
            if ':' in inner:
                env_name, env_default = inner.split(':', 1)
                resolved = os.getenv(env_name, env_default)
            else:
                env_name = inner
                resolved = os.getenv(env_name)

            if resolved is None:
                return default

            # Type conversion
            try:
                if value_type == bool:
                    return resolved.lower() in ('true', '1', 'yes')
                elif value_type in (int, float):
                    return value_type(resolved)
                else:
                    return resolved
            except (ValueError, AttributeError):
                return default
        elif isinstance(value, str) and value_type != str:
            # String value but expecting different type (coerce)
            try:
                if value_type == bool:
                    return value.lower() in ('true', '1', 'yes')
                else:
                    return value_type(value)
            except (ValueError, AttributeError):
                return default
        elif value is None:
            return default
        else:
            return value

    @staticmethod
    def _map_nested_config(raw: Dict[str, Any]) -> Dict[str, Any]:
        """Map nested YAML structure to flat config dict.

        Handles both:
        - Nested structure: learning_loop.max_iterations, llm.model, etc.
        - Flat structure: max_iterations, llm_model, etc. (backward compat)
        - Environment variable placeholders: ${VAR_NAME:default}

        Args:
            raw: Raw YAML dict

        Returns:
            Flat config dict with LearningConfig attribute names
        """
        resolve = LearningConfig._resolve_env_var
        config = {}

        # === Loop Control ===
        learning_loop = raw.get('learning_loop', {})
        config['max_iterations'] = resolve(
            learning_loop.get('max_iterations', raw.get('max_iterations', 20)),
            20, int
        )
        config['continue_on_error'] = resolve(
            learning_loop.get('continue_on_error', raw.get('continue_on_error', False)),
            False, bool
        )

        # === LLM Configuration ===
        llm = raw.get('llm', {})
        config['llm_model'] = llm.get('model', raw.get('llm_model', 'gemini-2.5-flash'))

        # API key: try provider-specific keys, then generic
        api_key = None
        if 'openrouter' in llm and llm['openrouter'].get('api_key'):
            api_key = llm['openrouter']['api_key']
        elif 'gemini' in llm and llm['gemini'].get('api_key'):
            api_key = llm['gemini']['api_key']
        elif 'openai' in llm and llm['openai'].get('api_key'):
            api_key = llm['openai']['api_key']
        config['api_key'] = api_key or raw.get('api_key')

        # LLM generation settings
        generation = llm.get('generation', {})
        config['llm_timeout'] = resolve(
            generation.get('timeout', raw.get('llm_timeout', 60)),
            60, int
        )
        config['llm_temperature'] = resolve(
            generation.get('temperature', raw.get('llm_temperature', 0.7)),
            0.7, float
        )
        config['llm_max_tokens'] = resolve(
            generation.get('max_tokens', raw.get('llm_max_tokens', 4000)),
            4000, int
        )

        # === Innovation Mode ===
        config['innovation_mode'] = llm.get('enabled', raw.get('innovation_mode', True))

        # Innovation rate: handle both 0.0-1.0 (float) and 0-100 (int) formats
        innovation_rate_raw = llm.get('innovation_rate', raw.get('innovation_rate', 1.0))
        if isinstance(innovation_rate_raw, (int, float)):
            if innovation_rate_raw <= 1.0:
                # Float format (0.0-1.0), convert to 0-100
                config['innovation_rate'] = int(innovation_rate_raw * 100)
            else:
                # Already in 0-100 format
                config['innovation_rate'] = int(innovation_rate_raw)
        else:
            # String (environment variable placeholder), try to parse
            try:
                val = float(innovation_rate_raw)
                config['innovation_rate'] = int(val * 100) if val <= 1.0 else int(val)
            except (ValueError, TypeError):
                config['innovation_rate'] = 100  # Default

        llm_retry = learning_loop.get('llm', {})
        config['llm_retry_count'] = resolve(
            llm_retry.get('retry_count', raw.get('llm_retry_count', 3)),
            3, int
        )

        # === Backtest Configuration ===
        backtest = raw.get('backtest', {})
        config['timeout_seconds'] = resolve(
            learning_loop.get('backtest', {}).get('timeout_seconds', raw.get('timeout_seconds', 420)),
            420, int
        )
        config['start_date'] = backtest.get('default_start_date', raw.get('start_date', '2018-01-01'))
        config['end_date'] = backtest.get('default_end_date', raw.get('end_date', '2024-12-31'))

        transaction_costs = backtest.get('transaction_costs', {})
        config['fee_ratio'] = resolve(
            transaction_costs.get('default_fee_ratio', raw.get('fee_ratio', 0.001425)),
            0.001425, float
        )
        config['tax_ratio'] = resolve(
            transaction_costs.get('default_tax_ratio', raw.get('tax_ratio', 0.003)),
            0.003, float
        )
        config['resample'] = resolve(
            learning_loop.get('backtest', {}).get('resample', raw.get('resample', 'M')),
            'M', str
        )

        # === History & Files ===
        history = learning_loop.get('history', {})
        config['history_file'] = history.get('file', raw.get('history_file', 'artifacts/data/innovations.jsonl'))
        config['history_window'] = resolve(
            history.get('window', raw.get('history_window', 5)),
            5, int
        )

        champion = learning_loop.get('champion', {})
        config['champion_file'] = champion.get('file', raw.get('champion_file', 'artifacts/data/champion.json'))

        logging_cfg = learning_loop.get('logging', {})
        config['log_dir'] = logging_cfg.get('log_dir', raw.get('log_dir', 'logs'))

        # === Logging ===
        config['log_level'] = resolve(
            logging_cfg.get('log_level', raw.get('log_level', 'INFO')),
            'INFO', str
        )
        config['log_to_file'] = resolve(
            logging_cfg.get('log_to_file', raw.get('log_to_file', True)),
            True, bool
        )
        config['log_to_console'] = resolve(
            logging_cfg.get('log_to_console', raw.get('log_to_console', True)),
            True, bool
        )

        return config

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

            # Innovation Mode
            "innovation_mode": self.innovation_mode,
            "innovation_rate": self.innovation_rate,
            "llm_retry_count": self.llm_retry_count,

            # Backtest Configuration
            "timeout_seconds": self.timeout_seconds,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "fee_ratio": self.fee_ratio,
            "tax_ratio": self.tax_ratio,
            "resample": self.resample,

            # History & Files
            "history_file": self.history_file,
            "history_window": self.history_window,
            "champion_file": self.champion_file,
            "log_dir": self.log_dir,

            # Logging
            "log_level": self.log_level,
            "log_to_file": self.log_to_file,
            "log_to_console": self.log_to_console,
        }
