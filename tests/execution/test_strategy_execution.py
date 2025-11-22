"""
Test Suite for Strategy Execution

Tests for StrategyFactory.execute() method (Task 19.3).

Test Coverage:
    - BacktestResult validation
    - StrategyFactory.create_strategy()
    - StrategyFactory.execute() with StrategyConfig
    - Success cases with valid strategies
    - Error handling (timeout, validation, execution errors)
    - Metrics calculation and conversion

Integration:
    - src/execution/strategy_factory.py: StrategyFactory
    - src/execution/backtest_result.py: BacktestResult
    - src/execution/strategy_config.py: StrategyConfig
    - src/backtest/executor.py: BacktestExecutor
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.execution.backtest_result import BacktestResult
from src.execution.strategy_factory import StrategyFactory
from src.execution.strategy_config import (
    StrategyConfig,
    FieldMapping,
    ParameterConfig,
    LogicConfig,
    ConstraintConfig,
)
from src.backtest.executor import ExecutionResult


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_strategy_config():
    """Create a valid sample StrategyConfig for testing."""
    return StrategyConfig(
        name="Test Momentum Strategy",
        type="momentum",
        description="Simple momentum strategy for testing",
        fields=[
            FieldMapping(
                canonical_name="price:收盤價",
                alias="close",
                usage="Signal generation - momentum calculation"
            )
        ],
        parameters=[
            ParameterConfig(
                name="momentum_period",
                type="integer",
                value=20,
                default=20,
                range=(10, 60),
                unit="trading_days"
            )
        ],
        logic=LogicConfig(
            entry="close > close.rolling(momentum_period).mean()",
            exit="None",
            dependencies=["price:收盤價"]
        ),
        constraints=[
            ConstraintConfig(
                type="parameter",
                condition="momentum_period > 0",
                severity="critical",
                message="Momentum period must be positive"
            )
        ]
    )


@pytest.fixture
def strategy_factory():
    """Create StrategyFactory instance for testing."""
    return StrategyFactory(timeout=420)


# ============================================================================
# BacktestResult Tests
# ============================================================================


class TestBacktestResult:
    """Test BacktestResult dataclass validation and behavior."""

    def test_successful_result_creation(self):
        """Test creating a successful BacktestResult."""
        result = BacktestResult(
            success=True,
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.10,
            win_rate=0.65,
            num_trades=150,
            execution_time=3.2
        )

        assert result.success is True
        assert result.sharpe_ratio == 1.5
        assert result.total_return == 0.25
        assert result.max_drawdown == -0.10
        assert result.win_rate == 0.65
        assert result.num_trades == 150
        assert result.execution_time == 3.2
        assert result.error is None

    def test_failed_result_creation(self):
        """Test creating a failed BacktestResult with error."""
        result = BacktestResult(
            success=False,
            error="TimeoutError: Backtest exceeded 420s timeout"
        )

        assert result.success is False
        assert result.error == "TimeoutError: Backtest exceeded 420s timeout"
        assert result.sharpe_ratio is None
        assert result.total_return is None

    def test_win_rate_validation(self):
        """Test win_rate must be in [0.0, 1.0]."""
        # Valid win_rate
        result = BacktestResult(success=True, win_rate=0.65)
        assert result.win_rate == 0.65

        # Invalid win_rate > 1.0
        with pytest.raises(ValueError, match="win_rate must be in"):
            BacktestResult(success=True, win_rate=1.5)

        # Invalid win_rate < 0.0
        with pytest.raises(ValueError, match="win_rate must be in"):
            BacktestResult(success=True, win_rate=-0.1)

    def test_num_trades_validation(self):
        """Test num_trades must be non-negative integer."""
        # Valid num_trades
        result = BacktestResult(success=True, num_trades=150)
        assert result.num_trades == 150

        # Invalid negative num_trades
        with pytest.raises(ValueError, match="num_trades must be non-negative"):
            BacktestResult(success=True, num_trades=-10)

        # Invalid non-integer num_trades
        with pytest.raises(ValueError, match="num_trades must be an integer"):
            BacktestResult(success=True, num_trades=150.5)

    def test_execution_time_validation(self):
        """Test execution_time must be non-negative."""
        # Valid execution_time
        result = BacktestResult(success=True, execution_time=3.2)
        assert result.execution_time == 3.2

        # Invalid negative execution_time
        with pytest.raises(ValueError, match="execution_time must be non-negative"):
            BacktestResult(success=True, execution_time=-1.0)

    def test_logical_consistency_validation(self):
        """Test success/error logical consistency."""
        # Success with error should fail
        with pytest.raises(ValueError, match="success=True is inconsistent"):
            BacktestResult(
                success=True,
                sharpe_ratio=1.5,
                error="Should not have error"
            )

        # Failure without error should fail
        with pytest.raises(ValueError, match="success=False requires error"):
            BacktestResult(success=False)


# ============================================================================
# StrategyFactory.create_strategy() Tests
# ============================================================================


class TestStrategyFactoryCreateStrategy:
    """Test StrategyFactory.create_strategy() method (Task 19.2)."""

    def test_create_strategy_from_valid_config(self, strategy_factory, sample_strategy_config):
        """Test creating strategy from valid StrategyConfig."""
        strategy = strategy_factory.create_strategy(sample_strategy_config)

        # For now, it returns the config itself
        assert strategy is not None
        assert strategy.name == "Test Momentum Strategy"

    def test_create_strategy_validates_dependencies(self, strategy_factory):
        """Test create_strategy validates logic dependencies."""
        # Create config with missing dependency
        invalid_config = StrategyConfig(
            name="Invalid Strategy",
            type="momentum",
            description="Strategy with missing dependency",
            fields=[
                FieldMapping(
                    canonical_name="price:收盤價",
                    alias="close",
                    usage="Signal generation"
                )
            ],
            parameters=[],
            logic=LogicConfig(
                entry="volume > 1000000",  # Uses 'volume' but not in fields
                exit="None",
                dependencies=["price:成交金額"]  # Not in fields
            ),
            constraints=[]
        )

        with pytest.raises(ValueError, match="unsatisfied dependencies"):
            strategy_factory.create_strategy(invalid_config)

    def test_create_strategy_type_validation(self, strategy_factory):
        """Test create_strategy validates input type."""
        with pytest.raises(TypeError, match="config must be a StrategyConfig"):
            strategy_factory.create_strategy("not a config")

        with pytest.raises(TypeError, match="config must be a StrategyConfig"):
            strategy_factory.create_strategy(None)


# ============================================================================
# StrategyFactory.execute() Tests
# ============================================================================


class TestStrategyFactoryExecute:
    """Test StrategyFactory.execute() method (Task 19.3)."""

    def test_execute_successful_backtest(
        self,
        strategy_factory,
        sample_strategy_config
    ):
        """Test successful strategy execution with valid metrics."""
        # Mock executor to return successful ExecutionResult
        mock_exec_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.5,
            total_return=0.25,
            max_drawdown=-0.10,
            execution_time=3.2
        )

        with patch.object(strategy_factory.executor, 'execute', return_value=mock_exec_result):
            # Mock finlab imports inside the execute() method
            with patch('builtins.__import__') as mock_import:
                # Set up finlab module mocks
                mock_finlab = Mock()
                mock_finlab.data = Mock()
                mock_finlab.backtest = Mock()

                def import_side_effect(name, *args, **kwargs):
                    if name == 'finlab':
                        return mock_finlab
                    # Use the real import for all other modules
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                result = strategy_factory.execute(sample_strategy_config)

        assert result.success is True
        assert result.sharpe_ratio == 1.5
        assert result.total_return == 0.25
        assert result.max_drawdown == -0.10
        assert result.execution_time == 3.2
        assert result.error is None

    def test_execute_timeout_error(
        self,
        strategy_factory,
        sample_strategy_config
    ):
        """Test execute handles timeout errors gracefully."""
        # Mock executor to return timeout error
        mock_exec_result = ExecutionResult(
            success=False,
            error_type="TimeoutError",
            error_message="Backtest execution exceeded timeout of 420 seconds",
            execution_time=420.0
        )

        with patch.object(strategy_factory.executor, 'execute', return_value=mock_exec_result):
            # Mock finlab imports
            with patch('builtins.__import__') as mock_import:
                mock_finlab = Mock()
                mock_finlab.data = Mock()
                mock_finlab.backtest = Mock()

                def import_side_effect(name, *args, **kwargs):
                    if name == 'finlab':
                        return mock_finlab
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                result = strategy_factory.execute(sample_strategy_config)

        assert result.success is False
        assert "TimeoutError" in result.error
        assert "420 seconds" in result.error
        assert result.execution_time == 420.0

    def test_execute_validation_error(
        self,
        strategy_factory
    ):
        """Test execute returns error for invalid strategy config."""
        # Create strategy with unsatisfied dependencies
        invalid_config = StrategyConfig(
            name="Invalid",
            type="momentum",
            description="Invalid strategy",
            fields=[
                FieldMapping(
                    canonical_name="price:收盤價",
                    alias="close",
                    usage="Signal"
                )
            ],
            parameters=[],
            logic=LogicConfig(
                entry="close > 0",
                exit="None",
                dependencies=["price:成交金額"]  # Not in fields
            ),
            constraints=[]
        )

        # Mock finlab imports
        with patch('builtins.__import__') as mock_import:
            mock_finlab = Mock()
            mock_finlab.data = Mock()
            mock_finlab.backtest = Mock()

            def import_side_effect(name, *args, **kwargs):
                if name == 'finlab':
                    return mock_finlab
                return __import__(name, *args, **kwargs)

            mock_import.side_effect = import_side_effect

            result = strategy_factory.execute(invalid_config)

        assert result.success is False
        assert "validation failed" in result.error.lower()
        assert "dependencies" in result.error.lower()

    def test_execute_syntax_error(
        self,
        strategy_factory,
        sample_strategy_config
    ):
        """Test execute handles syntax errors in strategy code."""
        # Mock executor to return syntax error
        mock_exec_result = ExecutionResult(
            success=False,
            error_type="SyntaxError",
            error_message="Invalid Python syntax: unexpected EOF at line 5",
            execution_time=0.1
        )

        with patch.object(strategy_factory.executor, 'execute', return_value=mock_exec_result):
            # Mock finlab imports
            with patch('builtins.__import__') as mock_import:
                mock_finlab = Mock()
                mock_finlab.data = Mock()
                mock_finlab.backtest = Mock()

                def import_side_effect(name, *args, **kwargs):
                    if name == 'finlab':
                        return mock_finlab
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                result = strategy_factory.execute(sample_strategy_config)

        assert result.success is False
        assert "SyntaxError" in result.error
        assert result.execution_time == 0.1

    def test_execute_with_custom_parameters(
        self,
        strategy_factory,
        sample_strategy_config
    ):
        """Test execute accepts custom backtest parameters."""
        mock_exec_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.2,
            total_return=0.15,
            max_drawdown=-0.08,
            execution_time=2.5
        )

        with patch.object(strategy_factory.executor, 'execute', return_value=mock_exec_result) as mock_execute:
            # Mock finlab imports
            with patch('builtins.__import__') as mock_import:
                mock_finlab = Mock()
                mock_finlab.data = Mock()
                mock_finlab.backtest = Mock()

                def import_side_effect(name, *args, **kwargs):
                    if name == 'finlab':
                        return mock_finlab
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                result = strategy_factory.execute(
                    sample_strategy_config,
                    start_date="2020-01-01",
                    end_date="2021-12-31",
                    fee_ratio=0.0,
                    tax_ratio=0.001,
                    timeout=300
                )

        # Verify execute was called with correct parameters
        mock_execute.assert_called_once()
        call_kwargs = mock_execute.call_args.kwargs
        assert call_kwargs['start_date'] == "2020-01-01"
        assert call_kwargs['end_date'] == "2021-12-31"
        assert call_kwargs['fee_ratio'] == 0.0
        assert call_kwargs['tax_ratio'] == 0.001
        assert call_kwargs['timeout'] == 300

    def test_execute_finlab_import_error(self, strategy_factory, sample_strategy_config):
        """Test execute handles finlab import errors gracefully."""
        # Patch the import inside execute() method
        import sys
        with patch.dict('sys.modules', {'finlab': None}):
            with patch('builtins.__import__', side_effect=ImportError("finlab not installed")):
                result = strategy_factory.execute(sample_strategy_config)

        assert result.success is False
        assert "Failed to import finlab" in result.error

    def test_execute_converts_execution_result_correctly(
        self,
        strategy_factory
    ):
        """Test _convert_execution_result correctly maps ExecutionResult to BacktestResult."""
        # Test successful conversion
        exec_result = ExecutionResult(
            success=True,
            sharpe_ratio=2.0,
            total_return=0.50,
            max_drawdown=-0.15,
            execution_time=5.0
        )

        backtest_result = strategy_factory._convert_execution_result(exec_result)

        assert backtest_result.success is True
        assert backtest_result.sharpe_ratio == 2.0
        assert backtest_result.total_return == 0.50
        assert backtest_result.max_drawdown == -0.15
        assert backtest_result.execution_time == 5.0
        assert backtest_result.error is None

        # Test failed conversion
        exec_result = ExecutionResult(
            success=False,
            error_type="ValueError",
            error_message="Invalid data",
            execution_time=0.5
        )

        backtest_result = strategy_factory._convert_execution_result(exec_result)

        assert backtest_result.success is False
        assert backtest_result.error == "ValueError: Invalid data"
        assert backtest_result.execution_time == 0.5


# ============================================================================
# Integration Tests
# ============================================================================


class TestStrategyFactoryIntegration:
    """Integration tests for complete workflow."""

    def test_complete_workflow_create_and_execute(
        self,
        strategy_factory,
        sample_strategy_config
    ):
        """Test complete workflow: create strategy and execute backtest."""
        # Step 1: Create strategy
        strategy = strategy_factory.create_strategy(sample_strategy_config)
        assert strategy is not None

        # Step 2: Execute backtest
        mock_exec_result = ExecutionResult(
            success=True,
            sharpe_ratio=1.8,
            total_return=0.30,
            max_drawdown=-0.12,
            execution_time=4.0
        )

        with patch.object(strategy_factory.executor, 'execute', return_value=mock_exec_result):
            # Mock finlab imports
            with patch('builtins.__import__') as mock_import:
                mock_finlab = Mock()
                mock_finlab.data = Mock()
                mock_finlab.backtest = Mock()

                def import_side_effect(name, *args, **kwargs):
                    if name == 'finlab':
                        return mock_finlab
                    return __import__(name, *args, **kwargs)

                mock_import.side_effect = import_side_effect

                result = strategy_factory.execute(strategy)

        # Step 3: Verify results
        assert result.success is True
        assert result.sharpe_ratio == 1.8
        assert result.total_return == 0.30
        assert result.max_drawdown == -0.12
        assert result.execution_time == 4.0

    def test_generate_strategy_code(self, strategy_factory, sample_strategy_config):
        """Test _generate_strategy_code produces valid Python code."""
        code = strategy_factory._generate_strategy_code(sample_strategy_config)

        # Verify code contains expected elements
        assert "data.get('price:收盤價')" in code
        assert "close =" in code
        assert "momentum_period = 20" in code
        assert "position =" in code
        assert "sim(" in code
        assert "report =" in code

        # Verify code is valid Python syntax
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError:
            pytest.fail("Generated code has syntax errors")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
