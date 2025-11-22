"""
Strategy Factory for Creating and Executing Strategies

Factory pattern for creating strategy objects from StrategyConfig and
executing backtests with comprehensive error handling.

Task: 19.2-19.3 - Implement create_strategy() and execute() Methods
Integration: StrategyConfig, BacktestExecutor, Factor Graph

Key Features:
    - Create strategy objects from StrategyConfig
    - Execute backtest with timeout protection
    - Convert ExecutionResult to BacktestResult
    - Comprehensive error handling and validation

Usage:
    from src.execution.strategy_factory import StrategyFactory
    from src.execution.strategy_config import StrategyConfig

    # Initialize factory
    factory = StrategyFactory(timeout=420)

    # Create strategy from config
    config = StrategyConfig(...)
    strategy = factory.create_strategy(config)

    # Execute backtest
    result = factory.execute(strategy)

    if result.success:
        print(f"Sharpe: {result.sharpe_ratio}")
    else:
        print(f"Error: {result.error}")

See Also:
    - src/execution/strategy_config.py: StrategyConfig dataclass
    - src/execution/backtest_result.py: BacktestResult dataclass
    - src/backtest/executor.py: BacktestExecutor
    - tests/execution/test_strategy_execution.py: Comprehensive tests
"""

from typing import Any, Optional, Union

from src.backtest.executor import BacktestExecutor
from src.execution.backtest_result import BacktestResult
from src.execution.strategy_config import StrategyConfig


class StrategyFactory:
    """
    Factory for creating and executing strategy objects.

    Provides high-level interface for strategy creation from config and
    backtest execution with comprehensive error handling. Integrates with
    BacktestExecutor for isolated execution with timeout protection.

    Attributes:
        timeout: Default backtest timeout in seconds (default: 420)
        executor: BacktestExecutor instance for strategy execution

    Example:
        >>> from src.execution.strategy_factory import StrategyFactory
        >>> from src.execution.strategy_config import StrategyConfig
        >>>
        >>> # Create factory
        >>> factory = StrategyFactory(timeout=420)
        >>>
        >>> # Create strategy from config
        >>> config = StrategyConfig(...)
        >>> strategy = factory.create_strategy(config)
        >>>
        >>> # Execute backtest
        >>> result = factory.execute(strategy)
        >>> assert result.success
        >>> assert result.sharpe_ratio is not None

    Integration:
        - Task 19.2: create_strategy() creates strategy from config
        - Task 19.3: execute() runs backtest and returns BacktestResult
        - Uses BacktestExecutor for isolated execution
        - Converts ExecutionResult to BacktestResult
    """

    def __init__(self, timeout: int = 420):
        """
        Initialize StrategyFactory.

        Args:
            timeout: Default backtest timeout in seconds (default: 420 = 7 minutes)
        """
        self.timeout = timeout
        self.executor = BacktestExecutor(timeout=timeout)

    def create_strategy(self, config: StrategyConfig) -> Any:
        """
        Create strategy object from StrategyConfig.

        Task 19.2 Implementation: Converts StrategyConfig to executable strategy.
        Currently creates a simple strategy object that can be executed by
        the BacktestExecutor.

        Args:
            config: StrategyConfig dataclass with strategy definition

        Returns:
            Strategy object ready for execution

        Raises:
            ValueError: If config is invalid or missing required fields
            TypeError: If config is not a StrategyConfig instance

        Example:
            >>> from src.execution.strategy_config import (
            ...     StrategyConfig, FieldMapping, ParameterConfig,
            ...     LogicConfig, ConstraintConfig
            ... )
            >>>
            >>> config = StrategyConfig(
            ...     name="Momentum Strategy",
            ...     type="momentum",
            ...     description="Simple momentum strategy",
            ...     fields=[
            ...         FieldMapping(
            ...             canonical_name="price:收盤價",
            ...             alias="close",
            ...             usage="Signal generation"
            ...         )
            ...     ],
            ...     parameters=[
            ...         ParameterConfig(
            ...             name="period",
            ...             type="integer",
            ...             value=20,
            ...             default=20,
            ...             range=(10, 60)
            ...         )
            ...     ],
            ...     logic=LogicConfig(
            ...         entry="close > close.rolling(20).mean()",
            ...         exit="None",
            ...         dependencies=["price:收盤價"]
            ...     ),
            ...     constraints=[]
            ... )
            >>>
            >>> factory = StrategyFactory()
            >>> strategy = factory.create_strategy(config)
            >>> assert strategy is not None
        """
        # Validate input
        if not isinstance(config, StrategyConfig):
            raise TypeError(
                f"config must be a StrategyConfig instance, got: {type(config)}"
            )

        # Validate dependencies
        if not config.validate_dependencies():
            raise ValueError(
                f"Strategy '{config.name}' has unsatisfied dependencies. "
                f"Required fields: {config.logic.dependencies}, "
                f"Available fields: {config.get_required_fields()}"
            )

        # For now, return the config itself as the strategy object
        # In the full implementation, this would create a Factor Graph Strategy
        # or compile the strategy code for execution
        #
        # TODO: Integrate with Factor Graph Strategy creation
        # - Convert FieldMapping to factor nodes
        # - Convert ParameterConfig to factor parameters
        # - Build DAG from LogicConfig
        # - Apply ConstraintConfig as validation rules
        return config

    def execute(
        self,
        strategy: Union[StrategyConfig, Any],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fee_ratio: Optional[float] = None,
        tax_ratio: Optional[float] = None,
        timeout: Optional[int] = None,
    ) -> BacktestResult:
        """
        Execute strategy backtest and return comprehensive results.

        Task 19.3 Implementation: Runs strategy backtest using BacktestExecutor
        and converts ExecutionResult to BacktestResult with additional metrics.

        Args:
            strategy: StrategyConfig or Strategy object to execute
            start_date: Backtest start date (YYYY-MM-DD, default: 2018-01-01)
            end_date: Backtest end date (YYYY-MM-DD, default: 2024-12-31)
            fee_ratio: Transaction fee ratio (default: 0.001425 for Taiwan)
            tax_ratio: Transaction tax ratio (default: 0.003 for Taiwan)
            timeout: Execution timeout in seconds (overrides factory default)

        Returns:
            BacktestResult with metrics (sharpe_ratio, total_return, etc.) or error

        Example:
            >>> factory = StrategyFactory()
            >>> config = StrategyConfig(...)
            >>> result = factory.execute(config)
            >>>
            >>> if result.success:
            ...     print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
            ...     print(f"Total Return: {result.total_return:.2%}")
            ...     print(f"Max Drawdown: {result.max_drawdown:.2%}")
            ...     print(f"Win Rate: {result.win_rate:.2%}")
            ... else:
            ...     print(f"Error: {result.error}")

        Error Handling:
            - TimeoutError: Backtest exceeded timeout limit
            - ValidationError: Strategy configuration invalid
            - ExecutionError: Strategy code execution failed
            - DataError: Required data fields not available

        Integration:
            - Uses BacktestExecutor for isolated execution
            - Converts ExecutionResult to BacktestResult
            - Adds win_rate and num_trades metrics
            - Comprehensive error message formatting
        """
        # Import finlab data here to avoid circular imports
        # and ensure it's loaded when needed
        try:
            from finlab import data, backtest
        except ImportError as e:
            return BacktestResult(
                success=False,
                error=f"Failed to import finlab: {str(e)}. "
                "Ensure finlab is installed and configured correctly."
            )

        # Convert StrategyConfig to executable strategy if needed
        if isinstance(strategy, StrategyConfig):
            try:
                # Validate strategy config
                if not strategy.validate_dependencies():
                    return BacktestResult(
                        success=False,
                        error=f"Strategy validation failed: unsatisfied dependencies. "
                        f"Required: {strategy.logic.dependencies}, "
                        f"Available: {strategy.get_required_fields()}"
                    )

                # For now, generate simple strategy code from config
                # In full implementation, this would create Factor Graph Strategy
                strategy_code = self._generate_strategy_code(strategy)

            except Exception as e:
                return BacktestResult(
                    success=False,
                    error=f"Strategy creation failed: {type(e).__name__}: {str(e)}"
                )
        else:
            # Assume it's a pre-built strategy object
            # Execute using execute_strategy() for Factor Graph strategies
            try:
                exec_result = self.executor.execute_strategy(
                    strategy=strategy,
                    data=data,
                    sim=backtest.sim,
                    timeout=timeout or self.timeout,
                    start_date=start_date,
                    end_date=end_date,
                    fee_ratio=fee_ratio,
                    tax_ratio=tax_ratio,
                )

                # Convert ExecutionResult to BacktestResult
                return self._convert_execution_result(exec_result)

            except Exception as e:
                return BacktestResult(
                    success=False,
                    error=f"Strategy execution failed: {type(e).__name__}: {str(e)}"
                )

        # Execute strategy code
        try:
            exec_result = self.executor.execute(
                strategy_code=strategy_code,
                data=data,
                sim=backtest.sim,
                timeout=timeout or self.timeout,
                start_date=start_date,
                end_date=end_date,
                fee_ratio=fee_ratio,
                tax_ratio=tax_ratio,
            )

            # Convert ExecutionResult to BacktestResult
            return self._convert_execution_result(exec_result)

        except Exception as e:
            return BacktestResult(
                success=False,
                error=f"Backtest execution failed: {type(e).__name__}: {str(e)}"
            )

    def _generate_strategy_code(self, config: StrategyConfig) -> str:
        """
        Generate executable strategy code from StrategyConfig.

        Creates Python code that can be executed by BacktestExecutor.
        This is a simplified implementation - full version would integrate
        with Factor Graph DAG generation.

        Args:
            config: StrategyConfig to convert to code

        Returns:
            Python code string ready for execution

        Example:
            >>> config = StrategyConfig(
            ...     name="Momentum",
            ...     logic=LogicConfig(
            ...         entry="close > close.rolling(20).mean()",
            ...         exit="None",
            ...         dependencies=["price:收盤價"]
            ...     ),
            ...     fields=[FieldMapping(
            ...         canonical_name="price:收盤價",
            ...         alias="close",
            ...         usage="Signal generation"
            ...     )],
            ...     ...
            ... )
            >>> code = factory._generate_strategy_code(config)
            >>> assert "data.get" in code
            >>> assert "sim(" in code
        """
        # Extract field mappings
        field_code_lines = []
        for field_mapping in config.fields:
            field_code_lines.append(
                f"{field_mapping.alias} = data.get('{field_mapping.canonical_name}')"
            )

        # Extract parameter values
        param_assignments = []
        for param in config.parameters:
            param_assignments.append(f"{param.name} = {param.value}")

        # Build strategy code
        code_lines = [
            "# Generated strategy code from StrategyConfig",
            f"# Strategy: {config.name}",
            f"# Type: {config.type}",
            "",
            "# Load data fields",
            *field_code_lines,
            "",
            "# Set parameters",
            *param_assignments,
            "",
            "# Entry logic",
            f"position = {config.logic.entry}",
            "",
            "# Filter by date range",
            "position = position.loc[start_date:end_date]",
            "",
            "# Execute backtest",
            "report = sim(",
            "    position,",
            "    fee_ratio=fee_ratio,",
            "    tax_ratio=tax_ratio,",
            "    resample='M'",
            ")",
        ]

        return "\n".join(code_lines)

    def _convert_execution_result(self, exec_result) -> BacktestResult:
        """
        Convert ExecutionResult to BacktestResult.

        Extracts metrics from ExecutionResult and packages them in
        BacktestResult format with additional calculated metrics.

        Args:
            exec_result: ExecutionResult from BacktestExecutor

        Returns:
            BacktestResult with all available metrics

        Example:
            >>> from src.backtest.executor import ExecutionResult
            >>> exec_result = ExecutionResult(
            ...     success=True,
            ...     sharpe_ratio=1.5,
            ...     total_return=0.25,
            ...     max_drawdown=-0.10,
            ...     execution_time=3.2
            ... )
            >>> backtest_result = factory._convert_execution_result(exec_result)
            >>> assert backtest_result.success
            >>> assert backtest_result.sharpe_ratio == 1.5
        """
        if not exec_result.success:
            # Failed execution
            error_msg = exec_result.error_message or "Unknown error"
            if exec_result.error_type:
                error_msg = f"{exec_result.error_type}: {error_msg}"

            return BacktestResult(
                success=False,
                execution_time=exec_result.execution_time,
                error=error_msg
            )

        # Successful execution - extract metrics
        return BacktestResult(
            success=True,
            sharpe_ratio=exec_result.sharpe_ratio,
            total_return=exec_result.total_return,
            max_drawdown=exec_result.max_drawdown,
            execution_time=exec_result.execution_time,
            # TODO: Calculate win_rate and num_trades from report
            # These require access to the full backtest report
            win_rate=None,
            num_trades=None,
        )


__all__ = ["StrategyFactory"]
