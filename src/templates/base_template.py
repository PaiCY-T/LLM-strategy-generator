"""
Base Template Abstract Class
=============================

Defines the abstract interface that all strategy templates must implement.

Features:
- Abstract properties for template metadata and configuration
- Shared DataCache integration to avoid repeated data.get() calls (Task 3)
- Parameter validation with type checking and range validation
- Default parameter generation from PARAM_GRID midpoints
- Comprehensive type hints and docstrings

Performance:
- Template instantiation: <100ms target (NFR Performance.1)
- DataCache singleton provides centralized caching across all templates
- Cache statistics tracking for performance monitoring
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class BaseTemplate(ABC):
    """
    Abstract base class for all strategy templates.

    All concrete strategy templates must inherit from this class and implement
    the abstract properties and methods defined below.

    Attributes:
        name (str): Human-readable template name
        pattern_type (str): Strategy pattern type (e.g., 'turtle', 'momentum', 'value')
        PARAM_GRID (Dict[str, List]): Parameter grid defining search space
        expected_performance (Dict[str, float]): Expected performance metrics
            - 'sharpe_ratio': Expected Sharpe ratio
            - 'annual_return': Expected annual return (as decimal)
            - 'max_drawdown': Expected max drawdown (as negative decimal)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return the human-readable name of this template.

        Returns:
            str: Template name (e.g., "High Dividend Turtle Strategy")
        """
        pass

    @property
    @abstractmethod
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: Pattern type (e.g., 'turtle', 'momentum', 'value', 'growth')
        """
        pass

    @property
    @abstractmethod
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        The parameter grid should define all tunable parameters and their
        possible values for grid search optimization.

        Returns:
            Dict[str, List]: Parameter grid where keys are parameter names
                and values are lists of possible values

        Example:
            {
                'yield_threshold': [4.0, 5.0, 6.0, 7.0, 8.0],
                'ma_short': [10, 20, 30],
                'n_stocks': [5, 10, 15, 20]
            }
        """
        pass

    @property
    @abstractmethod
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These metrics serve as targets for parameter optimization and
        validation of strategy effectiveness.

        Returns:
            Dict[str, Tuple[float, float]]: Expected performance ranges with keys:
                - 'sharpe_range': Expected Sharpe ratio range (e.g., (1.5, 2.5))
                - 'return_range': Expected annual return range as decimals (e.g., (0.20, 0.35))
                - 'mdd_range': Expected max drawdown range as negative decimals (e.g., (-0.25, -0.10))

        Example:
            {
                'sharpe_range': (1.5, 2.5),
                'return_range': (0.20, 0.35),
                'mdd_range': (-0.25, -0.10)
            }
        """
        pass

    @abstractmethod
    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This is the core method that must be implemented by all concrete templates.
        It should create and backtest a strategy using the provided parameters.

        Args:
            params (Dict): Parameter dictionary with values for all parameters
                defined in PARAM_GRID

        Returns:
            Tuple[object, Dict]: A tuple containing:
                - report (object): Backtest report object with metrics
                - metrics_dict (Dict): Dictionary with extracted metrics:
                    - 'annual_return' (float): Annual return as decimal
                    - 'sharpe_ratio' (float): Sharpe ratio
                    - 'max_drawdown' (float): Max drawdown as negative decimal
                    - 'success' (bool): Whether strategy meets performance targets

        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If strategy generation or backtesting fails

        Example:
            report, metrics = template.generate_strategy({
                'yield_threshold': 6.0,
                'ma_short': 20,
                'n_stocks': 10
            })
        """
        pass

    @staticmethod
    def _get_cached_data(key: str) -> Any:
        """
        Load and cache data to avoid repeated data.get() calls.

        This static method delegates to the shared DataCache singleton to ensure
        consistent caching behavior across all templates and strategy generators.

        Pattern leveraged from turtle_strategy_generator.py:71-76
        Now uses shared DataCache from src.templates.data_cache (Task 3)

        Args:
            key (str): Data key to load (e.g., 'price:收盤價', 'price:成交股數')

        Returns:
            Any: Cached data object (typically a DataFrame or Series)

        Note:
            - Data is loaded once and cached via DataCache singleton
            - Prints loading message on first access to each dataset
            - Safe to call multiple times with the same key
            - Cache shared across all templates for optimal performance

        Example:
            close = BaseTemplate._get_cached_data('price:收盤價')
            volume = BaseTemplate._get_cached_data('price:成交股數')
        """
        from src.templates.data_cache import get_cached_data
        return get_cached_data(key, verbose=True)

    def _validate_type(self, param_name: str, value: Any, expected_type: type) -> str | None:
        """
        Validate parameter type.

        Args:
            param_name (str): Name of the parameter being validated
            value (Any): Value to check
            expected_type (type): Expected type (int, float, str, etc.)

        Returns:
            str | None: Error message if validation fails, None if valid

        Example:
            error = self._validate_type('ma_short', 20, int)
            # Returns: None (valid)

            error = self._validate_type('ma_short', '20', int)
            # Returns: "Parameter 'ma_short' has wrong type: expected int, got str"
        """
        if not isinstance(value, expected_type):
            return (
                f"Parameter '{param_name}' has wrong type: "
                f"expected {expected_type.__name__}, got {type(value).__name__}"
            )
        return None

    def _validate_range(self, param_name: str, value: Any, allowed_values: List) -> str | None:
        """
        Validate parameter value is within allowed range.

        Args:
            param_name (str): Name of the parameter being validated
            value (Any): Value to check
            allowed_values (List): List of allowed values from PARAM_GRID

        Returns:
            str | None: Error message if validation fails, None if valid

        Example:
            error = self._validate_range('ma_short', 20, [10, 20, 30])
            # Returns: None (valid)

            error = self._validate_range('ma_short', 25, [10, 20, 30])
            # Returns: "Parameter 'ma_short' value 25 not in allowed values: [10, 20, 30]"
        """
        if value not in allowed_values:
            return (
                f"Parameter '{param_name}' value {value} not in allowed values: {allowed_values}"
            )
        return None

    def _validate_interdependency(self, params: Dict, rules: List[Tuple[str, str, str]]) -> List[str]:
        """
        Validate parameter interdependencies.

        Checks relationships between parameters where one parameter must be
        less than or greater than another parameter.

        Args:
            params (Dict): Parameter dictionary to validate
            rules (List[Tuple[str, str, str]]): List of validation rules where each tuple is:
                (param1_name, operator, param2_name)
                operator: '<' (less than), '>' (greater than), '<=' (less than or equal),
                         '>=' (greater than or equal)

        Returns:
            List[str]: List of validation error messages (empty if all rules pass)

        Example:
            errors = self._validate_interdependency(
                {'ma_short': 20, 'ma_long': 50},
                [('ma_short', '<', 'ma_long')]
            )
            # Returns: [] (valid, 20 < 50)

            errors = self._validate_interdependency(
                {'ma_short': 50, 'ma_long': 20},
                [('ma_short', '<', 'ma_long')]
            )
            # Returns: ["Parameter 'ma_short' (50) must be < 'ma_long' (20)"]
        """
        errors: List[str] = []

        for param1, operator, param2 in rules:
            # Skip if either parameter is missing (will be caught by other validation)
            if param1 not in params or param2 not in params:
                continue

            value1 = params[param1]
            value2 = params[param2]

            # Perform comparison based on operator
            valid = False
            if operator == '<':
                valid = value1 < value2
            elif operator == '>':
                valid = value1 > value2
            elif operator == '<=':
                valid = value1 <= value2
            elif operator == '>=':
                valid = value1 >= value2
            else:
                errors.append(f"Unknown operator '{operator}' in interdependency rule")
                continue

            if not valid:
                errors.append(
                    f"Parameter '{param1}' ({value1}) must be {operator} '{param2}' ({value2})"
                )

        return errors

    def validate_params(self, params: Dict) -> Tuple[bool, List[str]]:
        """
        Validate parameter dictionary against PARAM_GRID.

        Performs comprehensive validation including:
        - Presence of all required parameters
        - Type checking for each parameter value
        - Range validation (value must be in PARAM_GRID list)
        - Interdependency validation (if defined by subclass)

        Args:
            params (Dict): Parameter dictionary to validate

        Returns:
            Tuple[bool, List[str]]: A tuple containing:
                - is_valid (bool): True if all validations pass, False otherwise
                - errors (List[str]): List of validation error messages (empty if valid)

        Example:
            is_valid, errors = template.validate_params({
                'yield_threshold': 6.0,
                'ma_short': 20
            })
            if not is_valid:
                print("Validation errors:", errors)
        """
        errors: List[str] = []
        param_grid = self.PARAM_GRID

        # Check for missing parameters
        missing_params = set(param_grid.keys()) - set(params.keys())
        if missing_params:
            errors.append(f"Missing required parameters: {sorted(missing_params)}")

        # Check for extra parameters
        extra_params = set(params.keys()) - set(param_grid.keys())
        if extra_params:
            errors.append(f"Unknown parameters: {sorted(extra_params)}")

        # Validate each parameter value using helper methods
        for param_name, param_value in params.items():
            if param_name not in param_grid:
                continue  # Already reported as extra parameter

            allowed_values = param_grid[param_name]

            # Type checking using _validate_type
            if allowed_values:
                expected_type = type(allowed_values[0])
                type_error = self._validate_type(param_name, param_value, expected_type)
                if type_error:
                    errors.append(type_error)
                    continue

            # Range validation using _validate_range
            range_error = self._validate_range(param_name, param_value, allowed_values)
            if range_error:
                errors.append(range_error)

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_default_params(self) -> Dict:
        """
        Generate default parameters using PARAM_GRID midpoints.

        For each parameter in PARAM_GRID, selects the middle value from the
        list of possible values. This provides a reasonable starting point for
        strategy testing and optimization.

        Returns:
            Dict: Parameter dictionary with default values

        Example:
            # If PARAM_GRID has:
            # {'yield_threshold': [4.0, 5.0, 6.0, 7.0, 8.0], 'ma_short': [10, 20, 30]}

            defaults = template.get_default_params()
            # Returns: {'yield_threshold': 6.0, 'ma_short': 20}
        """
        default_params: Dict = {}
        param_grid = self.PARAM_GRID

        for param_name, allowed_values in param_grid.items():
            if not allowed_values:
                raise ValueError(f"Parameter '{param_name}' has empty value list in PARAM_GRID")

            # Select middle value from the list
            middle_index = len(allowed_values) // 2
            default_params[param_name] = allowed_values[middle_index]

        return default_params

    def __repr__(self) -> str:
        """
        Return string representation of the template.

        Returns:
            str: String representation including name and pattern type
        """
        return f"{self.__class__.__name__}(name='{self.name}', pattern_type='{self.pattern_type}')"
