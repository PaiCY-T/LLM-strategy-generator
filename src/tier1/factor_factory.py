"""
Factor Factory Module
=====================

Factory for creating Factor instances from configuration dictionaries.
Provides safe parameter binding and validation using FactorRegistry metadata.

Architecture: Structural Mutation Phase 2 - Phase D.2
Task: D.2 - YAML → Factor Interpreter

Features:
---------
1. Create Factor instances from type name and parameters
2. Query FactorRegistry for factor metadata
3. Validate parameters against registry specs
4. Handle parameter type conversion (string→int, etc.)
5. Provide clear error messages with suggestions

Usage Example:
-------------
    from src.tier1.factor_factory import FactorFactory
    from src.factor_library import FactorRegistry

    # Create factory
    registry = FactorRegistry.get_instance()
    factory = FactorFactory(registry)

    # Create factor from config
    factor = factory.create_factor(
        factor_id="momentum_20",
        factor_type="momentum_factor",
        parameters={"momentum_period": 20}
    )

    # Use in strategy
    strategy.add_factor(factor)
"""

from typing import Dict, Any, Optional
from src.factor_library import FactorRegistry
from src.factor_graph import Factor


class FactorFactoryError(Exception):
    """
    Raised when factor creation fails.

    This exception provides detailed information about why factor
    creation failed, including:
    - The specific error that occurred
    - The factor type and ID involved
    - Available factor types (when type not found)
    - Parameter validation errors
    """

    def __init__(
        self,
        message: str,
        factor_id: Optional[str] = None,
        factor_type: Optional[str] = None,
        parameter: Optional[str] = None
    ):
        """
        Initialize FactorFactoryError with context.

        Args:
            message: Error message describing what went wrong
            factor_id: ID of factor being created (optional)
            factor_type: Type of factor being created (optional)
            parameter: Name of problematic parameter (optional)
        """
        super().__init__(message)
        self.message = message
        self.factor_id = factor_id
        self.factor_type = factor_type
        self.parameter = parameter

    def __str__(self) -> str:
        """Format error message with context."""
        msg = self.message

        # Add context information
        context_parts = []
        if self.factor_id:
            context_parts.append(f"Factor ID: {self.factor_id}")
        if self.factor_type:
            context_parts.append(f"Factor Type: {self.factor_type}")
        if self.parameter:
            context_parts.append(f"Parameter: {self.parameter}")

        if context_parts:
            msg += f"\nContext: {', '.join(context_parts)}"

        return msg


class FactorFactory:
    """
    Factory for creating Factor instances from configuration.

    The factory queries the FactorRegistry for factor types and metadata,
    validates parameters, and creates Factor instances with proper parameter
    binding. It provides comprehensive error handling and validation.

    Responsibilities:
    - Query FactorRegistry for factor types and metadata
    - Instantiate factors with parameters
    - Validate parameter types and bounds
    - Handle missing optional parameters
    - Provide clear, actionable error messages

    Example:
        >>> from src.factor_library import FactorRegistry
        >>> registry = FactorRegistry.get_instance()
        >>> factory = FactorFactory(registry)
        >>>
        >>> # Create momentum factor
        >>> factor = factory.create_factor(
        ...     factor_id="momentum_20",
        ...     factor_type="momentum_factor",
        ...     parameters={"momentum_period": 20}
        ... )
        >>> factor.id
        'momentum_20'
        >>> factor.parameters["momentum_period"]
        20
        >>>
        >>> # Create factor with default parameters
        >>> factor = factory.create_factor(
        ...     factor_id="ma_filter_60",
        ...     factor_type="ma_filter_factor",
        ...     parameters={}  # Uses default ma_periods=60
        ... )
        >>> factor.parameters["ma_periods"]
        60
    """

    def __init__(self, registry: FactorRegistry):
        """
        Initialize FactorFactory with registry.

        Args:
            registry: FactorRegistry instance for factor creation
                Used to query factor types, metadata, and factory functions
        """
        self.registry = registry

    def create_factor(
        self,
        factor_id: str,
        factor_type: str,
        parameters: Dict[str, Any]
    ) -> Factor:
        """
        Create Factor instance from configuration.

        This method creates a Factor instance by:
        1. Validating the factor type exists in registry
        2. Merging provided parameters with defaults from registry
        3. Validating parameters against registry specs
        4. Calling the factory function from registry

        Args:
            factor_id: Unique instance ID for this factor
                Used as the Factor.id field
            factor_type: Type name from registry (e.g., "momentum_factor")
            parameters: Factor parameters (merged with registry defaults)

        Returns:
            Factor instance with configured parameters

        Raises:
            FactorFactoryError: If factor type not found, parameters invalid,
                or factory function fails

        Example:
            >>> factory = FactorFactory(FactorRegistry.get_instance())
            >>>
            >>> # Create with explicit parameters
            >>> factor = factory.create_factor(
            ...     factor_id="rsi_14",
            ...     factor_type="momentum_factor",
            ...     parameters={"momentum_period": 14}
            ... )
            >>>
            >>> # Create with defaults
            >>> factor = factory.create_factor(
            ...     factor_id="atr_20",
            ...     factor_type="atr_factor",
            ...     parameters={}  # Uses default atr_period=20
            ... )
        """
        # Step 1: Check if factor type exists in registry
        metadata = self.registry.get_metadata(factor_type)
        if metadata is None:
            # Provide helpful error with available types
            available_types = sorted(self.registry.list_factors())
            raise FactorFactoryError(
                f"Unknown factor type '{factor_type}'. "
                f"Available types: {', '.join(available_types)}",
                factor_id=factor_id,
                factor_type=factor_type
            )

        # Step 2: Validate and normalize parameters
        try:
            validated_params = self._validate_parameters(
                factor_type=factor_type,
                parameters=parameters,
                metadata=metadata
            )
        except FactorFactoryError:
            raise  # Re-raise as-is
        except Exception as e:
            raise FactorFactoryError(
                f"Parameter validation failed: {str(e)}",
                factor_id=factor_id,
                factor_type=factor_type
            ) from e

        # Step 3: Create factor using registry
        # The registry.create_factor() method handles factory function calls
        try:
            factor = self.registry.create_factor(
                name=factor_type,
                parameters=validated_params
            )
        except Exception as e:
            raise FactorFactoryError(
                f"Failed to create factor: {str(e)}",
                factor_id=factor_id,
                factor_type=factor_type
            ) from e

        # Step 4: Override factor ID with the one from config
        # The registry creates factors with default IDs, but we want to use
        # the ID from the YAML config for dependency tracking
        factor.id = factor_id

        return factor

    def _validate_parameters(
        self,
        factor_type: str,
        parameters: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate and normalize parameters against registry metadata.

        This method:
        1. Merges provided parameters with defaults from registry
        2. Validates parameter bounds using registry specs
        3. Checks for unknown parameters
        4. Handles type conversions (if needed)

        Args:
            factor_type: Factor type name
            parameters: Provided parameters
            metadata: Factor metadata from registry

        Returns:
            Validated and normalized parameters dictionary

        Raises:
            FactorFactoryError: If parameters are invalid
        """
        # Get default parameters from metadata
        default_params = metadata.get('parameters', {})

        # Start with defaults and override with provided parameters
        final_params = default_params.copy()
        final_params.update(parameters)

        # Validate using registry
        is_valid, error_msg = self.registry.validate_parameters(
            name=factor_type,
            parameters=final_params
        )

        if not is_valid:
            raise FactorFactoryError(
                f"Invalid parameters: {error_msg}",
                factor_type=factor_type
            )

        return final_params

    def get_available_types(self) -> list:
        """
        Get list of available factor types from registry.

        Returns:
            List of factor type names

        Example:
            >>> factory = FactorFactory(FactorRegistry.get_instance())
            >>> types = factory.get_available_types()
            >>> "momentum_factor" in types
            True
            >>> len(types) >= 13
            True
        """
        return self.registry.list_factors()

    def get_metadata(self, factor_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a factor type.

        Args:
            factor_type: Factor type name

        Returns:
            Metadata dictionary if found, None otherwise

        Example:
            >>> factory = FactorFactory(FactorRegistry.get_instance())
            >>> metadata = factory.get_metadata("momentum_factor")
            >>> metadata['parameters']['momentum_period']
            20
        """
        return self.registry.get_metadata(factor_type)
