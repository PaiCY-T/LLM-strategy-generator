"""Validation Configuration - Centralized validation thresholds and parameters.

This module provides centralized configuration for validation infrastructure,
replacing hard-coded magic numbers with named constants for better maintainability.

Task 8.6 (M3, M4): Configuration schema validation + Performance thresholds
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class PerformanceThresholds:
    """Performance thresholds for validation operations (Task 8.6 - M4).

    All thresholds based on NFR-P1 requirement: Layer 2 validation <5ms.

    Attributes:
        max_validation_latency_ms: Maximum allowed validation latency (default: 5.0ms)
        layer1_latency_budget_ms: Layer 1 (DataFieldManifest) budget (default: 1.0ms)
        layer2_latency_budget_ms: Layer 2 (FieldValidator) budget (default: 3.0ms)
        layer3_latency_budget_ms: Layer 3 (SchemaValidator) budget (default: 2.0ms)
        metadata_overhead_budget_ms: ValidationMetadata overhead (default: 0.1ms)
    """
    max_validation_latency_ms: float = 5.0
    layer1_latency_budget_ms: float = 1.0
    layer2_latency_budget_ms: float = 3.0
    layer3_latency_budget_ms: float = 2.0
    metadata_overhead_budget_ms: float = 0.1


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration (Task 8.6 - M3).

    Attributes:
        min_threshold: Minimum valid threshold (default: 1)
        max_threshold: Maximum valid threshold (default: 10, NFR-R3)
        default_threshold: Default threshold value (default: 2)
        hash_truncation_length: SHA256 hash truncation chars (default: 16)
    """
    min_threshold: int = 1
    max_threshold: int = 10
    default_threshold: int = 2
    hash_truncation_length: int = 16


@dataclass
class LLMValidationConfig:
    """LLM validation configuration (Task 8.6 - M3).

    Attributes:
        target_success_rate_min: Minimum target success rate % (default: 70.0)
        target_success_rate_max: Maximum target success rate % (default: 85.0)
        max_retry_attempts: Maximum retry attempts (default: 3)
    """
    target_success_rate_min: float = 70.0
    target_success_rate_max: float = 85.0
    max_retry_attempts: int = 3


@dataclass
class ValidationConfig:
    """Centralized validation configuration (Task 8.6 - M3).

    Provides schema-validated configuration for all validation components,
    replacing hard-coded values with centralized, documented settings.

    Attributes:
        performance: Performance thresholds for validation operations
        circuit_breaker: Circuit breaker configuration
        llm_validation: LLM validation configuration

    Example:
        >>> config = ValidationConfig()
        >>> assert config.performance.max_validation_latency_ms == 5.0
        >>> assert config.circuit_breaker.default_threshold == 2
        >>> assert config.llm_validation.target_success_rate_min == 70.0
    """
    performance: PerformanceThresholds = None
    circuit_breaker: CircuitBreakerConfig = None
    llm_validation: LLMValidationConfig = None

    def __post_init__(self):
        """Initialize nested configs with defaults if not provided."""
        if self.performance is None:
            self.performance = PerformanceThresholds()
        if self.circuit_breaker is None:
            self.circuit_breaker = CircuitBreakerConfig()
        if self.llm_validation is None:
            self.llm_validation = LLMValidationConfig()

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ValidationConfig':
        """Create ValidationConfig from dictionary (Task 8.6 - M3).

        Args:
            config_dict: Configuration dictionary with nested structure

        Returns:
            ValidationConfig instance with validated settings

        Example:
            >>> config_dict = {
            ...     'performance': {'max_validation_latency_ms': 5.0},
            ...     'circuit_breaker': {'default_threshold': 2}
            ... }
            >>> config = ValidationConfig.from_dict(config_dict)
            >>> assert config.performance.max_validation_latency_ms == 5.0
        """
        performance_dict = config_dict.get('performance', {})
        circuit_breaker_dict = config_dict.get('circuit_breaker', {})
        llm_validation_dict = config_dict.get('llm_validation', {})

        return cls(
            performance=PerformanceThresholds(**performance_dict),
            circuit_breaker=CircuitBreakerConfig(**circuit_breaker_dict),
            llm_validation=LLMValidationConfig(**llm_validation_dict)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ValidationConfig to dictionary (Task 8.6 - M3).

        Returns:
            Configuration dictionary with nested structure

        Example:
            >>> config = ValidationConfig()
            >>> config_dict = config.to_dict()
            >>> assert 'performance' in config_dict
            >>> assert 'circuit_breaker' in config_dict
        """
        return {
            'performance': {
                'max_validation_latency_ms': self.performance.max_validation_latency_ms,
                'layer1_latency_budget_ms': self.performance.layer1_latency_budget_ms,
                'layer2_latency_budget_ms': self.performance.layer2_latency_budget_ms,
                'layer3_latency_budget_ms': self.performance.layer3_latency_budget_ms,
                'metadata_overhead_budget_ms': self.performance.metadata_overhead_budget_ms
            },
            'circuit_breaker': {
                'min_threshold': self.circuit_breaker.min_threshold,
                'max_threshold': self.circuit_breaker.max_threshold,
                'default_threshold': self.circuit_breaker.default_threshold,
                'hash_truncation_length': self.circuit_breaker.hash_truncation_length
            },
            'llm_validation': {
                'target_success_rate_min': self.llm_validation.target_success_rate_min,
                'target_success_rate_max': self.llm_validation.target_success_rate_max,
                'max_retry_attempts': self.llm_validation.max_retry_attempts
            }
        }

    def validate(self) -> None:
        """Validate configuration values (Task 8.6 - M3).

        Raises:
            ValueError: If any configuration value is invalid

        Example:
            >>> config = ValidationConfig()
            >>> config.validate()  # No exception raised
            >>>
            >>> config.circuit_breaker.min_threshold = -1
            >>> config.validate()  # Raises ValueError
            Traceback (most recent call last):
                ...
            ValueError: Circuit breaker min_threshold must be >= 0
        """
        # Validate performance thresholds
        if self.performance.max_validation_latency_ms <= 0:
            raise ValueError("max_validation_latency_ms must be > 0")

        if self.performance.layer1_latency_budget_ms <= 0:
            raise ValueError("layer1_latency_budget_ms must be > 0")

        if self.performance.layer2_latency_budget_ms <= 0:
            raise ValueError("layer2_latency_budget_ms must be > 0")

        if self.performance.layer3_latency_budget_ms <= 0:
            raise ValueError("layer3_latency_budget_ms must be > 0")

        # Validate circuit breaker config
        if self.circuit_breaker.min_threshold < 0:
            raise ValueError("Circuit breaker min_threshold must be >= 0")

        if self.circuit_breaker.max_threshold <= self.circuit_breaker.min_threshold:
            raise ValueError("Circuit breaker max_threshold must be > min_threshold")

        if not (self.circuit_breaker.min_threshold <= self.circuit_breaker.default_threshold <= self.circuit_breaker.max_threshold):
            raise ValueError("Circuit breaker default_threshold must be within [min_threshold, max_threshold]")

        if self.circuit_breaker.hash_truncation_length <= 0:
            raise ValueError("hash_truncation_length must be > 0")

        # Validate LLM validation config
        if not (0 <= self.llm_validation.target_success_rate_min <= 100):
            raise ValueError("target_success_rate_min must be in [0, 100]")

        if not (0 <= self.llm_validation.target_success_rate_max <= 100):
            raise ValueError("target_success_rate_max must be in [0, 100]")

        if self.llm_validation.target_success_rate_min > self.llm_validation.target_success_rate_max:
            raise ValueError("target_success_rate_min must be <= target_success_rate_max")

        if self.llm_validation.max_retry_attempts < 0:
            raise ValueError("max_retry_attempts must be >= 0")


# Global default configuration instance
DEFAULT_VALIDATION_CONFIG = ValidationConfig()
