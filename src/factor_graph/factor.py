"""
Factor Base Class

Defines the atomic strategy component in the Factor Graph architecture.
A Factor represents a single computational step with explicit inputs, outputs, and execution logic.

Architecture: Phase 2.0+ Factor Graph System
"""

from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any
import pandas as pd

from .factor_category import FactorCategory


@dataclass
class Factor:
    """
    Atomic strategy component in Factor Graph architecture.

    A Factor represents a single computational step in a trading strategy,
    with explicit dependencies (inputs) and outputs. Factors can be composed
    into DAGs to create complete trading strategies.

    The Factor interface enables:
    - Dependency tracking through explicit inputs/outputs
    - Compositional strategy design (DAG of Factors)
    - Category-aware mutation operations
    - Parameter tuning and optimization
    - Modular testing and validation

    Attributes:
        id: Unique identifier for this factor instance
            Format: lowercase with underscores (e.g., "rsi_14", "atr_stop_loss")
        name: Human-readable name for documentation and UI
            Format: Title case (e.g., "RSI Momentum Signal", "ATR Stop Loss")
        category: Factor category for mutation and discovery
        inputs: List of required data columns (dependencies)
            Examples: ["close"], ["high", "low", "close"], ["positions", "atr"]
        outputs: List of produced data columns
            Examples: ["rsi_14"], ["positions"], ["exit_signal"]
        logic: Callable that implements factor computation
            Signature: (data: pd.DataFrame, parameters: Dict[str, Any]) -> pd.DataFrame
        parameters: Tunable parameters for optimization
            Examples: {"period": 14}, {"atr_multiplier": 2.0, "period": 20}
        description: Human-readable description for documentation (optional)

    Example:
        >>> def calculate_rsi(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        ...     period = params["period"]
        ...     delta = data["close"].diff()
        ...     gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        ...     loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        ...     rs = gain / loss
        ...     data["rsi"] = 100 - (100 / (1 + rs))
        ...     data["rsi_signal"] = (data["rsi"] > params["overbought"]).astype(int) - \\
        ...                          (data["rsi"] < params["oversold"]).astype(int)
        ...     return data
        >>>
        >>> rsi_factor = Factor(
        ...     id="rsi_14",
        ...     name="RSI Momentum Signal",
        ...     category=FactorCategory.MOMENTUM,
        ...     inputs=["close"],
        ...     outputs=["rsi", "rsi_signal"],
        ...     logic=calculate_rsi,
        ...     parameters={"period": 14, "overbought": 70, "oversold": 30},
        ...     description="RSI-based momentum signal with overbought/oversold levels"
        ... )
        >>>
        >>> # Validate inputs
        >>> rsi_factor.validate_inputs(["open", "high", "low", "close", "volume"])
        True
        >>>
        >>> # Execute factor
        >>> data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
        >>> result = rsi_factor.execute(data)
        >>> "rsi" in result.columns and "rsi_signal" in result.columns
        True

    Design Notes:
        - Factors are immutable after creation (dataclass with frozen=False for flexibility)
        - Logic functions should be pure (no side effects, deterministic)
        - Output columns must not conflict with other factors in the DAG
        - Inputs must be available (base data or previous factor outputs)
        - Parameters should have sensible defaults and validation
    """

    id: str
    name: str
    category: FactorCategory
    inputs: List[str]
    outputs: List[str]
    logic: Callable[[pd.DataFrame, Dict[str, Any]], pd.DataFrame]
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self):
        """Validate factor configuration after initialization."""
        # Validate id format (lowercase with underscores)
        if not self.id:
            raise ValueError("Factor id cannot be empty")
        if not self.id.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"Factor id must be alphanumeric with underscores/hyphens: '{self.id}'"
            )

        # Validate name
        if not self.name:
            raise ValueError("Factor name cannot be empty")

        # Validate category
        if not isinstance(self.category, FactorCategory):
            raise TypeError(
                f"Factor category must be FactorCategory enum, got {type(self.category)}"
            )

        # Validate inputs
        if not self.inputs:
            raise ValueError("Factor must have at least one input column")
        if not all(isinstance(inp, str) for inp in self.inputs):
            raise TypeError("Factor inputs must be list of strings")
        if len(self.inputs) != len(set(self.inputs)):
            raise ValueError(f"Factor inputs contain duplicates: {self.inputs}")

        # Validate outputs
        if not self.outputs:
            raise ValueError("Factor must produce at least one output column")
        if not all(isinstance(out, str) for out in self.outputs):
            raise TypeError("Factor outputs must be list of strings")
        if len(self.outputs) != len(set(self.outputs)):
            raise ValueError(f"Factor outputs contain duplicates: {self.outputs}")

        # Validate logic callable
        if not callable(self.logic):
            raise TypeError("Factor logic must be callable")

        # Validate parameters
        if not isinstance(self.parameters, dict):
            raise TypeError("Factor parameters must be dict")

    def validate_inputs(self, available_columns: List[str]) -> bool:
        """
        Check if all required inputs are available.

        Args:
            available_columns: List of column names available in the data
                (typically base OHLCV data + outputs from previous factors)

        Returns:
            True if all required inputs are in available_columns, False otherwise

        Example:
            >>> factor = Factor(
            ...     id="test", name="Test", category=FactorCategory.MOMENTUM,
            ...     inputs=["close", "volume"], outputs=["signal"],
            ...     logic=lambda d, p: d, parameters={}
            ... )
            >>> factor.validate_inputs(["open", "high", "low", "close", "volume"])
            True
            >>> factor.validate_inputs(["close"])  # Missing volume
            False
        """
        return all(inp in available_columns for inp in self.inputs)

    def execute(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Execute factor logic and return data with new columns.

        This method applies the factor's logic function to the input data,
        producing the specified output columns.

        Args:
            data: Input DataFrame with required input columns
                Must contain all columns specified in self.inputs

        Returns:
            DataFrame with new columns added (specified in self.outputs)
            Original data is preserved, new columns are appended

        Raises:
            KeyError: If required input columns are missing
            Exception: Any exception raised by the logic function

        Example:
            >>> def add_sma(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            ...     period = params["period"]
            ...     data["sma"] = data["close"].rolling(window=period).mean()
            ...     return data
            >>>
            >>> factor = Factor(
            ...     id="sma_20", name="SMA 20", category=FactorCategory.MOMENTUM,
            ...     inputs=["close"], outputs=["sma"],
            ...     logic=add_sma, parameters={"period": 20}
            ... )
            >>>
            >>> data = pd.DataFrame({"close": [100, 102, 101, 103, 105]})
            >>> result = factor.execute(data)
            >>> "sma" in result.columns
            True

        Design Notes:
            - Logic functions should not modify input data in-place
            - Output columns should be added to a copy of the input data
            - Exceptions from logic functions are propagated to the caller
            - Validation of input availability should be done before calling execute()
        """
        # Validate inputs are available
        missing = [inp for inp in self.inputs if inp not in data.columns]
        if missing:
            raise KeyError(
                f"Factor '{self.id}' requires columns {self.inputs}, "
                f"but {missing} are missing from data"
            )

        # Execute logic function
        try:
            result = self.logic(data.copy(), self.parameters)
        except Exception as e:
            raise RuntimeError(
                f"Factor '{self.id}' execution failed: {str(e)}"
            ) from e

        # Validate outputs are produced
        missing_outputs = [out for out in self.outputs if out not in result.columns]
        if missing_outputs:
            raise RuntimeError(
                f"Factor '{self.id}' logic did not produce expected outputs: {missing_outputs}"
            )

        return result

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"Factor(id='{self.id}', name='{self.name}', "
            f"category={repr(self.category)}, inputs={self.inputs}, "
            f"outputs={self.outputs}, parameters={self.parameters})"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.name} ({self.category}): {self.inputs} → {self.outputs}"
