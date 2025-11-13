# src/learning/exceptions.py
"""
Exception hierarchy for LLM strategy generation system.

This module defines a comprehensive exception hierarchy for explicit error handling,
supporting Phase 0 and Phase 1 error handling improvements.

Exception Hierarchy:
    GenerationError (Base)
    ├── ConfigurationError
    │   └── ConfigurationConflictError
    └── LLMGenerationError
        ├── LLMUnavailableError
        └── LLMEmptyResponseError
"""
from typing import Any, Dict, List, Optional


class GenerationError(Exception):
    """Base exception for all generation-related errors.

    This is the root exception for all errors that occur during strategy generation,
    including configuration, LLM interaction, and validation errors.

    Attributes:
        message: Human-readable error description
        context: Optional dict with additional error context
    """

    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (context: {context_str})"
        return self.message


class ConfigurationError(GenerationError):
    """Base exception for configuration-related errors.

    Raised when there are issues with strategy generation configuration,
    including invalid values, missing required settings, or logical conflicts.

    Examples:
        - Invalid parameter values (e.g., negative innovation_rate)
        - Missing required configuration fields
        - Configuration conflicts (handled by ConfigurationConflictError)
    """
    pass


class ConfigurationConflictError(ConfigurationError):
    """Raised when configuration has conflicting settings.

    This exception is raised when mutually exclusive or incompatible
    configuration options are specified together.

    Examples:
        - use_factor_graph=True AND innovation_rate=100
          (Factor graph requires innovation_rate < 100 for LLM generation)
        - evolution_mode='crossover' without parent strategies
        - Invalid combinations of template_mode and evolution settings

    Attributes:
        conflicts: List of conflicting configuration keys
        suggested_fix: Optional suggestion for resolving the conflict
    """

    def __init__(self, message: str, conflicts: Optional[List[str]] = None, suggested_fix: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, context)
        self.conflicts = conflicts or []
        self.suggested_fix = suggested_fix

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.conflicts:
            base_msg += f" [conflicts: {', '.join(self.conflicts)}]"
        if self.suggested_fix:
            base_msg += f" [suggested fix: {self.suggested_fix}]"
        return base_msg


class LLMGenerationError(GenerationError):
    """Base exception for LLM generation failures.

    Raised when errors occur during LLM-based strategy generation,
    including client initialization, API calls, and response processing.

    Examples:
        - LLM client not available (handled by LLMUnavailableError)
        - Empty LLM response (handled by LLMEmptyResponseError)
        - API timeout or rate limiting
        - Invalid LLM response format
    """
    pass


class LLMUnavailableError(LLMGenerationError):
    """Raised when LLM client or engine is not available.

    This exception is raised when the system cannot access the LLM service,
    either because the client is not initialized or the service is unavailable.

    Examples:
        - LLM client is None
        - API credentials missing or invalid
        - Network connectivity issues
        - LLM service temporarily unavailable

    Attributes:
        llm_type: Type of LLM that was unavailable (e.g., 'claude', 'openai')
        retry_possible: Whether retrying the operation might succeed
    """

    def __init__(self, message: str, llm_type: Optional[str] = None, retry_possible: bool = False, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, context)
        self.llm_type = llm_type
        self.retry_possible = retry_possible

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.llm_type:
            base_msg += f" [llm_type: {self.llm_type}]"
        if self.retry_possible:
            base_msg += " [retry may help]"
        return base_msg


class LLMEmptyResponseError(LLMGenerationError):
    """Raised when LLM returns empty code.

    This exception is raised when the LLM successfully responds but returns
    no usable code, either because the response is empty or contains only
    comments/whitespace.

    Examples:
        - LLM returns empty string
        - Response contains only comments
        - Response is only whitespace
        - Code extraction yields no executable code

    Attributes:
        raw_response: The raw LLM response (may be None or empty)
        prompt_info: Optional dict with information about the prompt used
    """

    def __init__(self, message: str, raw_response: Optional[str] = None, prompt_info: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message, context)
        self.raw_response = raw_response
        self.prompt_info = prompt_info or {}

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.raw_response is not None:
            response_preview = self.raw_response[:50] + "..." if len(self.raw_response) > 50 else self.raw_response
            base_msg += f" [response preview: '{response_preview}']"
        if self.prompt_info:
            base_msg += f" [prompt: {self.prompt_info}]"
        return base_msg
