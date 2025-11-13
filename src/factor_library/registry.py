"""
Factor Registry Module
======================

Centralized Factor Registry for factor discovery, lookup, and management.
Provides the foundation for Tier 2 structural mutations (add, replace, mutate).

Architecture: Phase 2.0+ Factor Graph System
Task: B.4 - Factor Registry Implementation

Core Features:
-------------
1. Factor Registration: Register factors with metadata (name, factory, category, parameters)
2. Factor Discovery: List factors by category, search by name or ID
3. Factor Creation: Create factor instances with parameter validation
4. Parameter Management: Define valid ranges and defaults for each factor
5. Singleton Pattern: Single global registry instance for consistency

Available Factors:
-----------------
Momentum Factors (4):
    - momentum_factor: Price momentum using rolling mean of returns
    - ma_filter_factor: Moving average filter for trend confirmation
    - revenue_catalyst_factor: Revenue acceleration catalyst detection
    - earnings_catalyst_factor: Earnings momentum catalyst (ROE improvement)

Turtle Factors (4):
    - atr_factor: Average True Range calculation for volatility measurement
    - breakout_factor: N-day high/low breakout detection for entry signals
    - dual_ma_filter_factor: Dual moving average filter for trend confirmation
    - atr_stop_loss_factor: ATR-based stop loss calculation for risk management

Exit Factors (5):
    - trailing_stop_factor: Trailing stop loss that follows price
    - time_based_exit_factor: Exit positions after N periods
    - volatility_stop_factor: Volatility-based stop using standard deviation
    - profit_target_factor: Fixed profit target exit
    - composite_exit_factor: Combines multiple exit signals with OR logic

Example Usage:
-------------
    from src.factor_library.registry import FactorRegistry
    from src.factor_graph.factor_category import FactorCategory

    # Get registry instance
    registry = FactorRegistry.get_instance()

    # Discover factors by category
    momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
    exit_factors = registry.list_by_category(FactorCategory.EXIT)

    # Create factor with parameters
    momentum_factor = registry.create_factor(
        "momentum_factor",
        parameters={"momentum_period": 20}
    )

    # Validate parameters before creation
    is_valid, error_msg = registry.validate_parameters(
        "momentum_factor",
        {"momentum_period": 20}
    )

    # Get factor metadata
    metadata = registry.get_metadata("momentum_factor")
    print(f"Default parameters: {metadata['parameters']}")
    print(f"Parameter ranges: {metadata['parameter_ranges']}")

    # List all factors
    all_factors = registry.list_factors()
    print(f"Total factors: {len(all_factors)}")
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


@dataclass
class FactorMetadata:
    """
    Metadata for a registered factor.

    Attributes:
        name: Unique factor name/ID (e.g., "momentum_factor")
        factory: Factory function to create factor instances
        category: Factor category for discovery and mutation
        description: Human-readable description
        parameters: Default parameter values
        parameter_ranges: Valid ranges for each parameter
            Format: {"param_name": (min_value, max_value)} or {"param_name": [valid_values]}
    """
    name: str
    factory: Callable[..., Factor]
    category: FactorCategory
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    parameter_ranges: Dict[str, Any] = field(default_factory=dict)


class FactorRegistry:
    """
    Centralized Factor Registry for factor discovery, lookup, and management.

    Implements singleton pattern to ensure single global registry instance.
    Provides comprehensive factor management capabilities:
    - Registration with metadata
    - Discovery by category or name
    - Creation with parameter validation
    - Parameter range checking

    The registry is automatically populated with all 13 factors on first access.

    Example:
        >>> registry = FactorRegistry.get_instance()
        >>>
        >>> # Discover momentum factors
        >>> momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
        >>> print(f"Found {len(momentum_factors)} momentum factors")
        Found 5 momentum factors
        >>>
        >>> # Create factor with custom parameters
        >>> momentum = registry.create_factor(
        ...     "momentum_factor",
        ...     parameters={"momentum_period": 30}
        ... )
        >>>
        >>> # Validate parameters
        >>> is_valid, msg = registry.validate_parameters(
        ...     "momentum_factor",
        ...     {"momentum_period": 50}
        ... )
        >>> if not is_valid:
        ...     print(f"Invalid parameters: {msg}")
    """

    _instance: Optional['FactorRegistry'] = None
    _initialized: bool = False

    def __init__(self):
        """Initialize empty registry. Use get_instance() for singleton access."""
        self._factors: Dict[str, FactorMetadata] = {}
        self._category_index: Dict[FactorCategory, List[str]] = {
            category: [] for category in FactorCategory
        }

    @classmethod
    def get_instance(cls) -> 'FactorRegistry':
        """
        Get singleton registry instance, initializing if needed.

        Returns:
            FactorRegistry: Global registry instance with all factors registered

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> len(registry.list_factors()) >= 13  # 13 factors registered
            True
        """
        if cls._instance is None:
            cls._instance = cls()

        # Auto-initialize on first access
        if not cls._initialized:
            cls._instance._register_all_factors()
            cls._initialized = True

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton instance. Used for testing."""
        cls._instance = None
        cls._initialized = False

    def register_factor(
        self,
        name: str,
        factory: Callable[..., Factor],
        category: FactorCategory,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        parameter_ranges: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a factor with metadata.

        Args:
            name: Unique factor name/ID (e.g., "momentum_factor")
            factory: Factory function to create factor instances
            category: Factor category for discovery and mutation
            description: Human-readable description
            parameters: Default parameter values (optional)
            parameter_ranges: Valid ranges for each parameter (optional)
                Format: {"param": (min, max)} or {"param": [valid_values]}

        Raises:
            ValueError: If factor name already registered

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> registry.register_factor(
            ...     name="my_custom_factor",
            ...     factory=create_my_custom_factor,
            ...     category=FactorCategory.MOMENTUM,
            ...     description="My custom momentum factor",
            ...     parameters={"period": 14},
            ...     parameter_ranges={"period": (5, 100)}
            ... )
        """
        if name in self._factors:
            raise ValueError(f"Factor '{name}' already registered")

        metadata = FactorMetadata(
            name=name,
            factory=factory,
            category=category,
            description=description,
            parameters=parameters or {},
            parameter_ranges=parameter_ranges or {}
        )

        self._factors[name] = metadata
        self._category_index[category].append(name)

    def get_factor(self, name: str) -> Optional[FactorMetadata]:
        """
        Retrieve factor metadata by name.

        Args:
            name: Factor name/ID

        Returns:
            FactorMetadata if found, None otherwise

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> metadata = registry.get_factor("momentum_factor")
            >>> metadata.category == FactorCategory.MOMENTUM
            True
        """
        return self._factors.get(name)

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get factor metadata as dictionary.

        Args:
            name: Factor name/ID

        Returns:
            Dictionary with metadata fields, or None if not found

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> meta = registry.get_metadata("momentum_factor")
            >>> "parameters" in meta and "category" in meta
            True
        """
        metadata = self.get_factor(name)
        if metadata is None:
            return None

        return {
            "name": metadata.name,
            "category": metadata.category,
            "description": metadata.description,
            "parameters": metadata.parameters,
            "parameter_ranges": metadata.parameter_ranges,
        }

    def list_factors(self) -> List[str]:
        """
        List all registered factor names.

        Returns:
            List of factor names

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> factors = registry.list_factors()
            >>> "momentum_factor" in factors
            True
        """
        return list(self._factors.keys())

    def list_by_category(self, category: FactorCategory) -> List[str]:
        """
        List factors in a specific category.

        Args:
            category: Factor category to filter by

        Returns:
            List of factor names in the category

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> momentum_factors = registry.list_by_category(FactorCategory.MOMENTUM)
            >>> len(momentum_factors) >= 4  # At least 4 momentum factors
            True
        """
        return self._category_index.get(category, []).copy()

    def get_factory(self, name: str) -> Optional[Callable[..., Factor]]:
        """
        Get factory function for a factor.

        Args:
            name: Factor name/ID

        Returns:
            Factory function if found, None otherwise

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> factory = registry.get_factory("momentum_factor")
            >>> factor = factory(momentum_period=20)
            >>> factor.category == FactorCategory.MOMENTUM
            True
        """
        metadata = self.get_factor(name)
        return metadata.factory if metadata else None

    def create_factor(
        self,
        name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Factor:
        """
        Create a factor instance with parameters.

        Args:
            name: Factor name/ID
            parameters: Parameter values (uses defaults if not specified)

        Returns:
            Factor instance configured with parameters

        Raises:
            ValueError: If factor not found or parameters invalid

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> factor = registry.create_factor(
            ...     "momentum_factor",
            ...     parameters={"momentum_period": 20}
            ... )
            >>> factor.parameters["momentum_period"] == 20
            True
        """
        metadata = self.get_factor(name)
        if metadata is None:
            raise ValueError(f"Factor '{name}' not found in registry")

        # Use defaults for missing parameters
        final_params = metadata.parameters.copy()
        if parameters:
            final_params.update(parameters)

        # Validate parameters
        is_valid, error_msg = self.validate_parameters(name, final_params)
        if not is_valid:
            raise ValueError(f"Invalid parameters for factor '{name}': {error_msg}")

        # Create factor using factory
        try:
            return metadata.factory(**final_params)
        except Exception as e:
            raise ValueError(
                f"Failed to create factor '{name}' with parameters {final_params}: {str(e)}"
            ) from e

    def validate_parameters(
        self,
        name: str,
        parameters: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Validate parameters against registered ranges.

        Args:
            name: Factor name/ID
            parameters: Parameter values to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message is empty string

        Example:
            >>> registry = FactorRegistry.get_instance()
            >>> is_valid, msg = registry.validate_parameters(
            ...     "momentum_factor",
            ...     {"momentum_period": 20}
            ... )
            >>> is_valid
            True
            >>> is_valid, msg = registry.validate_parameters(
            ...     "momentum_factor",
            ...     {"momentum_period": 1}  # Too small
            ... )
            >>> is_valid
            False
        """
        metadata = self.get_factor(name)
        if metadata is None:
            return False, f"Factor '{name}' not found in registry"

        # Check for unknown parameters
        valid_params = set(metadata.parameters.keys())
        provided_params = set(parameters.keys())
        unknown_params = provided_params - valid_params
        if unknown_params:
            return False, f"Unknown parameters: {unknown_params}"

        # Validate each parameter against ranges
        for param_name, param_value in parameters.items():
            if param_name in metadata.parameter_ranges:
                range_spec = metadata.parameter_ranges[param_name]

                # Range specified as (min, max) tuple
                if isinstance(range_spec, tuple) and len(range_spec) == 2:
                    min_val, max_val = range_spec
                    if not (min_val <= param_value <= max_val):
                        return False, (
                            f"Parameter '{param_name}' value {param_value} "
                            f"out of range [{min_val}, {max_val}]"
                        )

                # Range specified as list of valid values
                elif isinstance(range_spec, list):
                    if param_value not in range_spec:
                        return False, (
                            f"Parameter '{param_name}' value {param_value} "
                            f"not in valid values: {range_spec}"
                        )

        return True, ""

    # Category-specific discovery methods for convenience

    def get_momentum_factors(self) -> List[str]:
        """Get list of momentum factor names."""
        return self.list_by_category(FactorCategory.MOMENTUM)

    def get_value_factors(self) -> List[str]:
        """Get list of value factor names."""
        return self.list_by_category(FactorCategory.VALUE)

    def get_quality_factors(self) -> List[str]:
        """Get list of quality factor names."""
        return self.list_by_category(FactorCategory.QUALITY)

    def get_risk_factors(self) -> List[str]:
        """Get list of risk factor names."""
        return self.list_by_category(FactorCategory.RISK)

    def get_exit_factors(self) -> List[str]:
        """Get list of exit factor names."""
        return self.list_by_category(FactorCategory.EXIT)

    def get_entry_factors(self) -> List[str]:
        """Get list of entry factor names."""
        return self.list_by_category(FactorCategory.ENTRY)

    def get_signal_factors(self) -> List[str]:
        """Get list of signal factor names."""
        return self.list_by_category(FactorCategory.SIGNAL)

    def _register_all_factors(self):
        """
        Register all 13 factors with metadata.

        Called automatically on first registry access.
        Registers:
        - 4 momentum factors (momentum, ma_filter, revenue_catalyst, earnings_catalyst)
        - 4 turtle factors (atr, breakout, dual_ma_filter, atr_stop_loss)
        - 5 exit factors (trailing_stop, time_exit, volatility_stop, profit_target, composite_exit)
        """
        # Import factory functions
        from .momentum_factors import (
            create_momentum_factor,
            create_ma_filter_factor,
            create_revenue_catalyst_factor,
            create_earnings_catalyst_factor,
        )
        from .turtle_factors import (
            create_atr_factor,
            create_breakout_factor,
            create_dual_ma_filter_factor,
            create_atr_stop_loss_factor,
        )
        from .exit_factors import (
            create_trailing_stop_factor,
            create_time_based_exit_factor,
            create_volatility_stop_factor,
            create_profit_target_factor,
            create_composite_exit_factor,
        )

        # Register Momentum Factors
        self.register_factor(
            name="momentum_factor",
            factory=create_momentum_factor,
            category=FactorCategory.MOMENTUM,
            description="Price momentum using rolling mean of returns",
            parameters={"momentum_period": 20},
            parameter_ranges={"momentum_period": (5, 100)}
        )

        self.register_factor(
            name="ma_filter_factor",
            factory=create_ma_filter_factor,
            category=FactorCategory.MOMENTUM,
            description="Moving average filter for trend confirmation",
            parameters={"ma_periods": 60},
            parameter_ranges={"ma_periods": (10, 200)}
        )

        self.register_factor(
            name="revenue_catalyst_factor",
            factory=create_revenue_catalyst_factor,
            category=FactorCategory.VALUE,
            description="Revenue acceleration catalyst detection",
            parameters={"catalyst_lookback": 3},
            parameter_ranges={"catalyst_lookback": (1, 12)}
        )

        self.register_factor(
            name="earnings_catalyst_factor",
            factory=create_earnings_catalyst_factor,
            category=FactorCategory.QUALITY,
            description="Earnings momentum catalyst using ROE",
            parameters={"catalyst_lookback": 3},
            parameter_ranges={"catalyst_lookback": (1, 12)}
        )

        # Register Turtle Factors
        self.register_factor(
            name="atr_factor",
            factory=create_atr_factor,
            category=FactorCategory.RISK,
            description="Average True Range for volatility measurement",
            parameters={"atr_period": 20},
            parameter_ranges={"atr_period": (5, 100)}
        )

        self.register_factor(
            name="breakout_factor",
            factory=create_breakout_factor,
            category=FactorCategory.ENTRY,
            description="N-day breakout detection for entry signals",
            parameters={"entry_window": 20},
            parameter_ranges={"entry_window": (5, 100)}
        )

        self.register_factor(
            name="dual_ma_filter_factor",
            factory=create_dual_ma_filter_factor,
            category=FactorCategory.MOMENTUM,
            description="Dual moving average filter for trend confirmation",
            parameters={"short_ma": 20, "long_ma": 60},
            parameter_ranges={
                "short_ma": (5, 100),
                "long_ma": (10, 200)
            }
        )

        self.register_factor(
            name="atr_stop_loss_factor",
            factory=create_atr_stop_loss_factor,
            category=FactorCategory.EXIT,
            description="ATR-based stop loss for risk management",
            parameters={"atr_multiplier": 2.0},
            parameter_ranges={"atr_multiplier": (0.5, 5.0)}
        )

        # Register Exit Factors
        self.register_factor(
            name="trailing_stop_factor",
            factory=create_trailing_stop_factor,
            category=FactorCategory.EXIT,
            description="Trailing stop loss that follows price",
            parameters={"trail_percent": 0.10, "activation_profit": 0.05},
            parameter_ranges={
                "trail_percent": (0.01, 0.50),
                "activation_profit": (0.0, 0.50)
            }
        )

        self.register_factor(
            name="time_based_exit_factor",
            factory=create_time_based_exit_factor,
            category=FactorCategory.EXIT,
            description="Exit positions after N periods",
            parameters={"max_holding_periods": 20},
            parameter_ranges={"max_holding_periods": (1, 200)}
        )

        self.register_factor(
            name="volatility_stop_factor",
            factory=create_volatility_stop_factor,
            category=FactorCategory.EXIT,
            description="Volatility-based stop using standard deviation",
            parameters={"std_period": 20, "std_multiplier": 2.0},
            parameter_ranges={
                "std_period": (5, 100),
                "std_multiplier": (0.5, 5.0)
            }
        )

        self.register_factor(
            name="profit_target_factor",
            factory=create_profit_target_factor,
            category=FactorCategory.EXIT,
            description="Fixed profit target exit",
            parameters={"target_percent": 0.30},
            parameter_ranges={"target_percent": (0.05, 2.0)}
        )

        self.register_factor(
            name="composite_exit_factor",
            factory=create_composite_exit_factor,
            category=FactorCategory.EXIT,
            description="Combines multiple exit signals with OR logic",
            parameters={"exit_signals": []},
            parameter_ranges={}  # No range validation for list parameter
        )
