"""
FinLab DataFrame Container for Matrix-Native Factor Graph
==========================================================

Phase 2.0 Factor Graph V2 - Matrix-Native Architecture

This container wraps FinLab's Dates×Symbols matrix data format, providing
a consistent interface for Factor Graph execution while preserving the
native matrix structure.

Problem Solved:
--------------
Phase 1 Factor Graph expected DataFrame with columns (Observations×Features),
but FinLab data is naturally stored as matrices (Dates×Symbols). This mismatch
caused ValueError when trying to assign 2D matrices to 1D columns.

Solution:
--------
FinLabDataFrame stores named matrices (not columns) and provides matrix-based
operations. Factor logic works directly with Dates×Symbols matrices.

Architecture:
------------
    FinLab Data Module → FinLabDataFrame Container → Factor Logic
    (4563×2661 matrices)   (matrix storage)          (vectorized ops)

Usage Example:
-------------
    from finlab import data
    from src.factor_graph.finlab_dataframe import FinLabDataFrame

    # Create container with data module
    container = FinLabDataFrame(data_module=data)

    # Add matrices
    close = data.get('price:收盤價')
    container.add_matrix('close', close)

    # Factor logic can now access matrices
    close_matrix = container.get_matrix('close')
    momentum = (close_matrix / close_matrix.shift(20)) - 1
    container.add_matrix('momentum', momentum)

Design Principles:
-----------------
1. **Matrix-Native**: All data stored as Dates×Symbols DataFrames
2. **Type Safety**: Runtime validation of matrix shapes and types
3. **Lazy Loading**: Data loaded on-demand from data module
4. **Immutability**: Matrices cannot be modified after adding (copy on add)
5. **Clear Errors**: Descriptive error messages for debugging

See Also:
--------
- .spec-workflow/specs/factor-graph-matrix-native-redesign.md
- docs/FACTOR_GRAPH_COMPREHENSIVE_ANALYSIS.md
"""

from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FinLabDataFrame:
    """
    Matrix-native container for FinLab Dates×Symbols data.

    This container replaces Phase 1's DataFrame approach with a matrix-centric
    design that aligns with FinLab's natural data format.

    Attributes:
        _matrices: Dictionary mapping matrix names to DataFrames
        _data_module: Reference to finlab.data module for lazy loading
        _base_shape: Expected shape (Dates, Symbols) for validation
        _metadata: Additional information about the container

    Example:
        >>> from finlab import data
        >>> container = FinLabDataFrame(data_module=data)
        >>> container.add_matrix('close', data.get('price:收盤價'))
        >>> close = container.get_matrix('close')
        >>> close.shape
        (4563, 2661)
    """

    def __init__(self, data_module: Any = None, base_shape: Optional[Tuple[int, int]] = None):
        """
        Initialize FinLabDataFrame container.

        Args:
            data_module: finlab.data module for lazy loading (optional)
            base_shape: Expected (Dates, Symbols) shape for validation (optional)
                       If not provided, will be inferred from first matrix added

        Example:
            >>> from finlab import data
            >>> container = FinLabDataFrame(data_module=data)
        """
        self._matrices: Dict[str, pd.DataFrame] = {}
        self._data_module = data_module
        self._base_shape = base_shape
        self._metadata: Dict[str, Any] = {}

        logger.debug(f"Initialized FinLabDataFrame with base_shape={base_shape}")

    def add_matrix(self, name: str, matrix: pd.DataFrame, validate: bool = True) -> None:
        """
        Add a Dates×Symbols matrix to the container.

        Args:
            name: Unique identifier for the matrix (e.g., 'close', 'momentum')
            matrix: Pandas DataFrame with shape (Dates, Symbols)
            validate: Whether to validate shape consistency (default: True)

        Raises:
            ValueError: If matrix shape doesn't match base_shape
            TypeError: If matrix is not a DataFrame
            KeyError: If matrix name already exists

        Example:
            >>> container.add_matrix('close', close_price_df)
            >>> container.add_matrix('momentum', momentum_df)
        """
        # Type validation
        if not isinstance(matrix, pd.DataFrame):
            raise TypeError(
                f"Expected pd.DataFrame, got {type(matrix).__name__}"
            )

        # Duplicate name check
        if name in self._matrices:
            raise KeyError(
                f"Matrix '{name}' already exists in container. "
                f"Use update_matrix() to modify existing matrices."
            )

        # Shape validation
        if validate:
            if self._base_shape is None:
                # First matrix - establish base shape
                self._base_shape = matrix.shape
                logger.debug(f"Established base_shape={self._base_shape} from matrix '{name}'")
            else:
                # Subsequent matrices - validate against base shape
                if matrix.shape != self._base_shape:
                    raise ValueError(
                        f"Matrix '{name}' shape {matrix.shape} does not match "
                        f"base shape {self._base_shape}"
                    )

        # Store copy to ensure immutability
        self._matrices[name] = matrix.copy()
        logger.debug(f"Added matrix '{name}' with shape {matrix.shape}")

    def get_matrix(self, name: str, lazy_load: bool = True) -> pd.DataFrame:
        """
        Get a matrix by name from the container.

        Args:
            name: Matrix identifier
            lazy_load: If True and matrix not found, try loading from data_module

        Returns:
            Pandas DataFrame with shape (Dates, Symbols)

        Raises:
            KeyError: If matrix not found and cannot be lazy loaded

        Example:
            >>> close = container.get_matrix('close')
            >>> close.shape
            (4563, 2661)
        """
        # Check if matrix exists in cache
        if name in self._matrices:
            return self._matrices[name]

        # Try lazy loading if enabled and data_module available
        if lazy_load and self._data_module is not None:
            try:
                matrix = self._lazy_load_matrix(name)
                if matrix is not None:
                    self.add_matrix(name, matrix, validate=True)
                    return self._matrices[name]
            except Exception as e:
                logger.warning(f"Lazy load failed for matrix '{name}': {e}")

        # Matrix not found
        raise KeyError(
            f"Matrix '{name}' not found in container. "
            f"Available matrices: {list(self._matrices.keys())}"
        )

    def has_matrix(self, name: str) -> bool:
        """
        Check if a matrix exists in the container.

        Args:
            name: Matrix identifier

        Returns:
            True if matrix exists, False otherwise

        Example:
            >>> container.has_matrix('close')
            True
            >>> container.has_matrix('nonexistent')
            False
        """
        return name in self._matrices

    def list_matrices(self) -> List[str]:
        """
        Get list of all matrix names in the container.

        Returns:
            List of matrix identifiers

        Example:
            >>> container.list_matrices()
            ['close', 'momentum', 'ma_filter', 'position']
        """
        return list(self._matrices.keys())

    def get_shape(self) -> Optional[Tuple[int, int]]:
        """
        Get the base shape (Dates, Symbols) of matrices in this container.

        Returns:
            Tuple of (dates, symbols) or None if no matrices added yet

        Example:
            >>> container.get_shape()
            (4563, 2661)
        """
        return self._base_shape

    def update_matrix(self, name: str, matrix: pd.DataFrame) -> None:
        """
        Update an existing matrix in the container.

        Args:
            name: Matrix identifier
            matrix: New DataFrame to replace existing one

        Raises:
            KeyError: If matrix doesn't exist
            ValueError: If new matrix shape doesn't match base shape

        Example:
            >>> container.update_matrix('momentum', updated_momentum_df)
        """
        if name not in self._matrices:
            raise KeyError(
                f"Matrix '{name}' does not exist. Use add_matrix() to create new matrices."
            )

        # Validate shape
        if self._base_shape is not None and matrix.shape != self._base_shape:
            raise ValueError(
                f"Updated matrix shape {matrix.shape} does not match "
                f"base shape {self._base_shape}"
            )

        self._matrices[name] = matrix.copy()
        logger.debug(f"Updated matrix '{name}'")

    def remove_matrix(self, name: str) -> None:
        """
        Remove a matrix from the container.

        Args:
            name: Matrix identifier

        Raises:
            KeyError: If matrix doesn't exist

        Example:
            >>> container.remove_matrix('temp_calculation')
        """
        if name not in self._matrices:
            raise KeyError(
                f"Cannot remove matrix '{name}' - does not exist"
            )

        del self._matrices[name]
        logger.debug(f"Removed matrix '{name}'")

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set metadata for the container.

        Args:
            key: Metadata key
            value: Metadata value

        Example:
            >>> container.set_metadata('backtest_period', '2020-2024')
        """
        self._metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata from the container.

        Args:
            key: Metadata key
            default: Default value if key doesn't exist

        Returns:
            Metadata value or default

        Example:
            >>> period = container.get_metadata('backtest_period')
        """
        return self._metadata.get(key, default)

    def _lazy_load_matrix(self, name: str) -> Optional[pd.DataFrame]:
        """
        Attempt to lazy load a matrix from the data module.

        This method maps matrix names to FinLab data queries.

        Args:
            name: Matrix identifier

        Returns:
            DataFrame if successfully loaded, None otherwise

        Note:
            This is an internal method. Override in subclasses to customize
            lazy loading behavior.
        """
        if self._data_module is None:
            return None

        # Map matrix names to FinLab data keys
        finlab_key_map = {
            'close': 'price:收盤價',
            'open': 'price:開盤價',
            'high': 'price:最高價',
            'low': 'price:最低價',
            'volume': 'price:成交股數',
            'market_cap': 'fundamental_features:市值',
            'revenue': 'fundamental_features:營收',
        }

        if name not in finlab_key_map:
            logger.debug(f"No lazy load mapping for matrix '{name}'")
            return None

        try:
            finlab_key = finlab_key_map[name]
            matrix = self._data_module.get(finlab_key)
            logger.info(f"Lazy loaded matrix '{name}' from FinLab key '{finlab_key}'")
            return matrix
        except Exception as e:
            logger.warning(f"Failed to lazy load matrix '{name}': {e}")
            return None

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        matrix_list = ', '.join(self._matrices.keys())
        return (
            f"FinLabDataFrame(matrices=[{matrix_list}], "
            f"shape={self._base_shape}, n_matrices={len(self._matrices)})"
        )

    def __str__(self) -> str:
        """Human-readable representation."""
        if not self._matrices:
            return "FinLabDataFrame(empty)"

        matrix_info = [f"  - {name}: {mat.shape}" for name, mat in self._matrices.items()]
        return f"FinLabDataFrame with {len(self._matrices)} matrices:\n" + "\n".join(matrix_info)
