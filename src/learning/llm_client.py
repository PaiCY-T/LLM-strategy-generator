"""
LLM Client for strategy generation via InnovationEngine.

This module encapsulates LLM initialization logic extracted from
autonomous_loop.py (lines 637-781), using ConfigManager for centralized
configuration management.

The LLMClient provides a clean interface for LLM-based strategy generation,
handling provider initialization, error handling, and configuration loading.

Architecture:
    - ConfigManager: Centralized config loading (no duplication)
    - InnovationEngine: LLM provider abstraction and strategy generation
    - Error handling: Graceful fallback on initialization failures

Example Usage:
    ```python
    from src.learning.llm_client import LLMClient

    # Initialize client
    client = LLMClient(config_path="config/learning_system.yaml")

    # Check if enabled
    if client.is_enabled():
        engine = client.get_engine()
        # Use engine for strategy generation...
    ```

Classes:
    LLMClient: Client for LLM-based strategy generation

Configuration:
    Uses ConfigManager to load configuration from learning_system.yaml:
    - llm.enabled: Enable/disable LLM generation (bool)
    - llm.provider: Provider name (openrouter/gemini/openai)
    - llm.model: Model name (e.g., gemini-2.5-flash)
    - llm.generation.max_tokens: Maximum tokens per response (int)
    - llm.generation.temperature: Sampling temperature (float)
    - llm.generation.timeout: API timeout in seconds (int)
    - API keys from environment variables (OPENROUTER_API_KEY, etc.)

Task: Phase 3 Learning Iteration - Task 1.2 (LLMClient Extraction)
Dependencies: Task 1.1 (ConfigManager) COMPLETE
Extracted from: artifacts/working/modules/autonomous_loop.py lines 637-781
"""

import os
import re
import logging
from typing import Optional, Dict, Any

from src.learning.config_manager import ConfigManager
from src.innovation.innovation_engine import InnovationEngine


logger = logging.getLogger(__name__)


class LLMClient:
    """
    Client for LLM-based strategy generation.

    Handles LLM initialization, configuration loading, and provides a clean
    interface for accessing the InnovationEngine. Replicates the exact
    behavior of autonomous_loop.py's LLM initialization logic (lines 637-781).

    Attributes:
        config_manager (ConfigManager): Singleton config manager instance
        config (Dict[str, Any]): Loaded configuration dictionary
        engine (Optional[InnovationEngine]): InnovationEngine instance if enabled
        enabled (bool): True if LLM is enabled and engine created successfully

    Thread Safety:
        ConfigManager uses thread-safe singleton pattern. Multiple LLMClient
        instances can be created safely from different threads.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize LLM client with configuration.

        Loads configuration using ConfigManager, then initializes
        InnovationEngine if LLM is enabled. Handles all errors gracefully,
        disabling LLM on any initialization failure.

        Args:
            config_path: Path to YAML config file. If None, uses default
                        "config/learning_system.yaml"

        Raises:
            None: All errors handled gracefully, LLM disabled on failures

        Behavior:
            - Loads config via ConfigManager (singleton, no duplication)
            - Checks llm.enabled flag in config
            - If enabled, creates InnovationEngine with configured parameters
            - On any error, logs warning and sets enabled=False
            - Replicates autonomous_loop.py lines 647-766 exactly
        """
        # Initialize ConfigManager (singleton, thread-safe)
        self.config_manager = ConfigManager.get_instance()
        self.config: Dict[str, Any] = {}
        self.engine: Optional[InnovationEngine] = None
        self.enabled: bool = False

        # Load configuration and initialize LLM
        self._load_config(config_path)
        self._initialize()

    def _load_config(self, config_path: Optional[str]) -> None:
        """
        Load configuration using ConfigManager.

        Args:
            config_path: Path to config file or None for default

        Side Effects:
            Sets self.config to loaded configuration
            On error, sets self.config to empty dict
        """
        try:
            if config_path:
                # Force reload to ensure fresh config for each instance
                self.config = self.config_manager.load_config(config_path, force_reload=True)
            else:
                self.config = self.config_manager.load_config()

            logger.debug(f"Configuration loaded from {config_path or 'default path'}")

        except FileNotFoundError as e:
            logger.warning(f"Config file not found: {e}, LLM disabled")
            self.config = {}
        except Exception as e:
            logger.warning(f"Failed to load LLM config: {e}, LLM disabled")
            self.config = {}

    def _initialize(self) -> None:
        """
        Initialize InnovationEngine based on configuration.

        Replicates the exact logic from autonomous_loop.py lines 647-766:
        1. Check if llm.enabled is True (with env var substitution)
        2. Extract provider, model, and generation parameters
        3. Create InnovationEngine with configured parameters
        4. Handle errors gracefully, disable LLM on any failure
        5. Log initialization success/failure

        Side Effects:
            Sets self.enabled to True if successful, False otherwise
            Sets self.engine to InnovationEngine instance or None
            Logs INFO on success, WARNING/ERROR on failures
        """
        # Default: LLM disabled (backward compatibility)
        self.enabled = False

        try:
            # Get LLM configuration section
            llm_config = self.config.get('llm', {})

            if not llm_config:
                logger.info("No LLM configuration found, LLM disabled (backward compatibility)")
                return

            # Check if LLM is enabled (with env var override support)
            # Matches autonomous_loop.py lines 662-673
            enabled_str = str(llm_config.get('enabled', 'false'))

            # Handle ${ENV_VAR:default} syntax
            if enabled_str.startswith('${') and enabled_str.endswith('}'):
                env_spec = enabled_str[2:-1]
                if ':' in env_spec:
                    env_var, default_val = env_spec.split(':', 1)
                    enabled_str = os.environ.get(env_var, default_val)
                else:
                    enabled_str = os.environ.get(env_spec, 'false')

            llm_enabled = enabled_str.lower() in ('true', '1', 'yes')

            if not llm_enabled:
                logger.info("LLM innovation mode disabled (backward compatibility)")
                return

            # Extract LLM configuration parameters
            # Matches autonomous_loop.py lines 675-693
            provider_name = llm_config.get('provider')
            if not provider_name:
                logger.warning("LLM provider not specified, using default 'openrouter'")
                provider_name = 'openrouter'

            # Handle ${ENV_VAR:default} syntax for model field
            model_str = str(llm_config.get('model', 'gemini-2.5-flash'))
            if model_str.startswith('${') and model_str.endswith('}'):
                env_spec = model_str[2:-1]
                if ':' in env_spec:
                    env_var, default_val = env_spec.split(':', 1)
                    model = os.environ.get(env_var, default_val)
                else:
                    model = os.environ.get(env_spec, 'gemini-2.5-flash')
            else:
                model = model_str

            # Extract generation parameters with defaults
            generation_config = llm_config.get('generation', {})
            timeout = generation_config.get('timeout', 60)
            max_tokens = generation_config.get('max_tokens', 2000)
            temperature = generation_config.get('temperature', 0.7)

            # Optional: innovation_rate (for autonomous_loop.py compatibility)
            self.innovation_rate = llm_config.get('innovation_rate', 0.20)

            # Validate innovation_rate
            # Matches autonomous_loop.py lines 696-702
            if not (0.0 <= self.innovation_rate <= 1.0):
                logger.warning(
                    f"Invalid innovation_rate {self.innovation_rate}, must be 0.0-1.0. "
                    f"Defaulting to 0.20"
                )
                self.innovation_rate = 0.20

            # Initialize InnovationEngine
            # Matches autonomous_loop.py lines 704-747
            try:
                self.engine = InnovationEngine(
                    provider_name=provider_name,
                    model=model,
                    max_retries=3,
                    timeout=timeout,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                # Mark as successfully enabled
                self.enabled = True

                logger.info(
                    f"InnovationEngine initialized: provider={provider_name}, "
                    f"model={model}, innovation_rate={self.innovation_rate:.1%}"
                )

            except Exception as e:
                logger.error(f"Failed to initialize InnovationEngine: {e}", exc_info=True)
                logger.warning("LLM mode disabled due to initialization failure")
                self.enabled = False
                self.engine = None

        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}, LLM disabled")
            self.enabled = False
            self.engine = None

    def is_enabled(self) -> bool:
        """
        Check if LLM-based generation is enabled.

        Returns:
            bool: True if LLM is enabled and engine created successfully,
                  False otherwise

        Example:
            ```python
            client = LLMClient()
            if client.is_enabled():
                engine = client.get_engine()
                # Use engine...
            else:
                # Fall back to non-LLM generation
            ```
        """
        return self.enabled and self.engine is not None

    def get_engine(self) -> Optional[InnovationEngine]:
        """
        Get the InnovationEngine instance.

        Returns:
            Optional[InnovationEngine]: InnovationEngine if enabled and
                                       initialized successfully, None otherwise

        Example:
            ```python
            client = LLMClient()
            engine = client.get_engine()
            if engine:
                result = engine.generate_strategy(...)
            ```
        """
        if not self.is_enabled():
            logger.debug("LLM not enabled, returning None")
            return None

        return self.engine

    def get_innovation_rate(self) -> float:
        """
        Get the configured innovation rate.

        Returns:
            float: Innovation rate (0.0-1.0), percentage of iterations
                   using LLM generation

        Example:
            ```python
            client = LLMClient()
            rate = client.get_innovation_rate()
            # Use rate to decide if this iteration should use LLM
            ```
        """
        return getattr(self, 'innovation_rate', 0.20)

    def extract_python_code(self, llm_response: str) -> Optional[str]:
        """
        Extract Python code from LLM response.

        Handles multiple formats:
        - Markdown code blocks with language identifier (```python...```)
        - Markdown code blocks without language identifier (```...```)
        - Plain text code (no markdown)
        - Multiple code blocks (returns first valid one)

        Validation:
        - Code must be non-empty after trimming whitespace
        - Code must contain at least one Python keyword:
          'def', 'import', 'data.get', or 'class'
        - Returns None if no valid Python code is found

        Args:
            llm_response: Raw LLM response text, may contain markdown,
                         explanatory text, or just code

        Returns:
            Extracted Python code (trimmed), or None if no valid code found

        Example:
            >>> client = LLMClient()
            >>> response = "Here's a strategy:\\n```python\\ndef strategy():\\n    pass\\n```"
            >>> code = client.extract_python_code(response)
            >>> assert code == "def strategy():\\n    pass"

            >>> response = "```\\nimport pandas as pd\\ndata.get('price')\\n```"
            >>> code = client.extract_python_code(response)
            >>> assert "import pandas" in code

            >>> response = "Invalid response with no code"
            >>> code = client.extract_python_code(response)
            >>> assert code is None

        Implementation:
            Uses regex to find markdown code blocks (```python or ```).
            Falls back to treating entire response as code if no blocks found.
            Validates extracted code contains Python syntax markers.

        Thread Safety:
            This method is thread-safe (no shared state modification).
        """
        if not llm_response or not isinstance(llm_response, str):
            return None

        # Try to extract markdown code blocks
        # Pattern matches ```python or ``` followed by code, then ```
        # Uses DOTALL flag to match across newlines
        pattern = r'```(?:python)?\s*(.*?)```'
        matches = re.findall(pattern, llm_response, re.DOTALL)

        # Try each matched code block (first valid one wins)
        for code_block in matches:
            code = code_block.strip()
            if self._is_valid_python_code(code):
                return code

        # Fallback: treat entire response as code (for plain text responses)
        code = llm_response.strip()
        if self._is_valid_python_code(code):
            return code

        # No valid code found
        return None

    def _is_valid_python_code(self, code: str) -> bool:
        """
        Validate that code string looks like Python code.

        Validation checks:
        - Code is non-empty after trimming
        - Contains at least one Python keyword or pattern:
          * 'def' (function definition)
          * 'import' (import statement)
          * 'data.get' (FinLab data access pattern)
          * 'class' (class definition)

        Args:
            code: Code string to validate

        Returns:
            bool: True if code appears to be valid Python, False otherwise

        Example:
            >>> client = LLMClient()
            >>> client._is_valid_python_code("def foo(): pass")
            True
            >>> client._is_valid_python_code("import pandas")
            True
            >>> client._is_valid_python_code("data.get('price')")
            True
            >>> client._is_valid_python_code("class MyClass: pass")
            True
            >>> client._is_valid_python_code("just some text")
            False
            >>> client._is_valid_python_code("")
            False

        Implementation:
            Simple keyword-based validation. Does not parse AST or
            check syntax validity (that's handled by downstream validators).
        """
        if not code:
            return False

        # Check for Python syntax markers
        python_markers = ['def', 'import', 'data.get', 'class']
        return any(marker in code for marker in python_markers)
