"""
Unit tests for backtest engine.

Tests strategy validation, async execution, metrics calculation,
zero trades detection, and sandbox security.
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.backtest import BacktestResult, PerformanceMetrics
from src.backtest.engine import BacktestEngineImpl
from src.backtest.metrics import calculate_metrics
from src.backtest.sandbox import execute_with_limits
from src.backtest.validation import validate_strategy_code
from src.backtest.visualizer import generate_visualizations


class TestStrategyValidation:
    """Test strategy code validation."""

    def test_valid_code_passes(self) -> None:
        """Test that valid strategy code passes validation."""
        code = """
import pandas as pd
import numpy as np

# Valid strategy code
position = pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error is None

    def test_syntax_error_detected(self) -> None:
        """Test that syntax errors are detected."""
        code = """
def invalid_syntax(
    # Missing closing parenthesis
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert error is not None
        assert "syntax error" in error.lower()

    def test_restricted_import_blocked(self) -> None:
        """Test that restricted imports are blocked."""
        code = """
import os
import sys

# Trying to access file system
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert error is not None
        assert "forbidden import" in error.lower()

    def test_forbidden_builtin_blocked(self) -> None:
        """Test that forbidden builtins are blocked."""
        code = """
# Trying to use exec
exec("malicious_code()")
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert error is not None
        assert "forbidden" in error.lower()

    def test_file_io_blocked(self) -> None:
        """Test that file I/O operations are blocked."""
        code = """
# Trying to open file
with open('data.txt', 'r') as f:
    content = f.read()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is False
        assert error is not None
        assert "file i/o" in error.lower()

    def test_allowed_imports_accepted(self) -> None:
        """Test that allowed imports are accepted."""
        code = """
import pandas as pd
import numpy as np
from datetime import datetime
import finlab

position = pd.DataFrame()
"""
        is_valid, error = validate_strategy_code(code)
        assert is_valid is True
        assert error is None


class TestSandboxExecution:
    """Test sandbox code execution with resource limits."""

    def test_simple_execution(self) -> None:
        """Test basic code execution in sandbox."""
        code = "result = 2 + 2"
        result = execute_with_limits(code, timeout=10)
        assert result['result'] == 4

    def test_timeout_enforcement(self) -> None:
        """Test that timeout is enforced (skip on Windows/WSL)."""
        import sys
        import platform
        # Skip on Windows and WSL
        if sys.platform.startswith('win') or 'microsoft' in platform.uname().release.lower():
            pytest.skip("Resource limits not supported on Windows/WSL")

        code = """
import time
time.sleep(10)
"""
        from src.backtest.sandbox import TimeoutError
        with pytest.raises(TimeoutError):
            execute_with_limits(code, timeout=1)

    def test_restricted_builtins(self) -> None:
        """Test that restricted builtins are not available."""
        code = "result = open('test.txt', 'r')"
        with pytest.raises(Exception):
            execute_with_limits(code, timeout=10)

    def test_safe_builtins_available(self) -> None:
        """Test that safe builtins are available."""
        code = """
result = sum([1, 2, 3, 4, 5])
max_val = max([1, 2, 3])
"""
        result = execute_with_limits(code, timeout=10)
        assert result['result'] == 15
        assert result['max_val'] == 3

    def test_pandas_available(self) -> None:
        """Test that pandas is available in sandbox."""
        code = """
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
result = len(df)
"""
        result = execute_with_limits(code, timeout=10)
        assert result['result'] == 3


class TestAsyncBacktestExecution:
    """Test async backtest execution."""

    @pytest.mark.asyncio
    async def test_run_backtest_with_mock(self) -> None:
        """Test async backtest execution with mocked finlab."""
        engine = BacktestEngineImpl(timeout=120)

        # Create sample strategy code
        strategy_code = """
import pandas as pd
position = pd.DataFrame({
    'A': [1, 0, 1],
    'B': [0, 1, 0]
}, index=pd.date_range('2023-01-01', periods=3))
"""

        # Mock finlab backtest
        mock_sim_result = Mock()
        mock_sim_result.trades = pd.DataFrame({
            'pnl': [0.05, -0.02, 0.03],
            'entry_date': pd.date_range('2023-01-01', periods=3),
            'exit_date': pd.date_range('2023-01-02', periods=3)
        })
        mock_sim_result.equity_curve = pd.Series(
            [100, 105, 103, 106],
            index=pd.date_range('2023-01-01', periods=4)
        )

        with patch('src.backtest.engine.backtest.sim', return_value=mock_sim_result):
            with patch('src.backtest.engine.finlab'):
                result = await engine.run_backtest(
                    strategy_code,
                    data_config={},
                    backtest_params={'sim_params': {}}
                )

        assert isinstance(result, BacktestResult)
        assert len(result.trade_records) == 3
        assert len(result.equity_curve) == 4

    @pytest.mark.asyncio
    async def test_invalid_code_raises_error(self) -> None:
        """Test that invalid code raises ValueError."""
        engine = BacktestEngineImpl(timeout=120)

        invalid_code = """
import os
os.system('rm -rf /')
"""

        with pytest.raises(ValueError, match="Invalid strategy code"):
            await engine.run_backtest(
                invalid_code,
                data_config={},
                backtest_params={}
            )

    @pytest.mark.asyncio
    async def test_zero_trades_detection(self) -> None:
        """Test that zero trades are detected and raise error."""
        with BacktestEngineImpl(timeout=120) as engine:
            strategy_code = """
import pandas as pd
position = pd.DataFrame({
    'A': [0, 0, 0],
}, index=pd.date_range('2023-01-01', periods=3))
"""

            # Mock finlab with zero trades
            mock_sim_result = Mock()
            mock_sim_result.trades = pd.DataFrame()  # Empty trades
            mock_sim_result.equity_curve = pd.Series(
                [100, 100, 100],
                index=pd.date_range('2023-01-01', periods=3)
            )

            with patch('src.backtest.engine.backtest.sim', return_value=mock_sim_result):
                with patch('src.backtest.engine.finlab'):
                    with pytest.raises(RuntimeError, match="zero trades"):
                        await engine.run_backtest(
                            strategy_code,
                            data_config={},
                            backtest_params={'sim_params': {}}
                        )


class TestPerformanceMetrics:
    """Test performance metrics calculation."""

    def test_calculate_metrics_with_mock_data(self) -> None:
        """Test metrics calculation with mock backtest data."""
        # Create mock backtest result
        equity_curve = pd.Series(
            [100, 105, 103, 108, 107, 112],
            index=pd.date_range('2023-01-01', periods=6)
        )

        trade_records = pd.DataFrame({
            'pnl': [0.05, -0.02, 0.05, -0.01, 0.05],
            'entry_date': pd.date_range('2023-01-01', periods=5),
            'exit_date': pd.date_range('2023-01-02', periods=5)
        })

        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=trade_records,
            equity_curve=equity_curve,
            raw_result=None
        )

        # Calculate metrics (will use fallback since finlab not installed)
        metrics = calculate_metrics(backtest_result)

        # Verify metrics structure
        assert isinstance(metrics, PerformanceMetrics)
        assert isinstance(metrics.annualized_return, float)
        assert isinstance(metrics.sharpe_ratio, float)
        assert isinstance(metrics.max_drawdown, float)
        assert metrics.total_trades == 5
        assert 0 <= metrics.win_rate <= 1

    def test_win_rate_calculation(self) -> None:
        """Test win rate calculation accuracy."""
        trade_records = pd.DataFrame({
            'pnl': [0.05, -0.02, 0.03, -0.01, 0.04],  # 3 wins, 2 losses
        })

        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=trade_records,
            equity_curve=pd.Series([100, 105]),
            raw_result=None
        )

        metrics = calculate_metrics(backtest_result)
        assert metrics.win_rate == 0.6  # 3/5 = 60%

    def test_profit_factor_calculation(self) -> None:
        """Test profit factor calculation accuracy."""
        trade_records = pd.DataFrame({
            'pnl': [0.10, -0.05, 0.05, -0.02],  # +0.15, -0.07
        })

        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=trade_records,
            equity_curve=pd.Series([100, 110]),
            raw_result=None
        )

        metrics = calculate_metrics(backtest_result)
        expected_pf = 0.15 / 0.07  # ~2.14
        assert abs(metrics.profit_factor - expected_pf) < 0.01

    def test_empty_trades_metrics(self) -> None:
        """Test metrics calculation with no trades."""
        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=pd.DataFrame(),
            equity_curve=pd.Series([100, 100, 100]),
            raw_result=None
        )

        metrics = calculate_metrics(backtest_result)
        assert metrics.total_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.profit_factor == 0.0


class TestVisualization:
    """Test visualization generation."""

    def test_generate_all_charts(self) -> None:
        """Test that all expected charts are generated."""
        equity_curve = pd.Series(
            [100, 105, 103, 108],
            index=pd.date_range('2023-01-01', periods=4)
        )

        trade_records = pd.DataFrame({
            'pnl': [0.05, -0.02, 0.03, -0.01, 0.04],
        })

        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=trade_records,
            equity_curve=equity_curve,
            raw_result=None
        )

        charts = generate_visualizations(backtest_result)

        # Verify all charts exist
        assert 'equity_curve' in charts
        assert 'drawdown' in charts
        assert 'trade_distribution' in charts

        # Verify charts are Plotly figures
        from plotly.graph_objs import Figure
        assert isinstance(charts['equity_curve'], Figure)
        assert isinstance(charts['drawdown'], Figure)
        assert isinstance(charts['trade_distribution'], Figure)

    def test_empty_data_handling(self) -> None:
        """Test visualization with empty data."""
        backtest_result = BacktestResult(
            portfolio_positions=pd.DataFrame(),
            trade_records=pd.DataFrame(),
            equity_curve=pd.Series(dtype=float),
            raw_result=None
        )

        # Should not raise exception
        charts = generate_visualizations(backtest_result)

        # Charts should still be created (as error placeholders)
        assert len(charts) == 3


class TestBacktestEngineIntegration:
    """Integration tests for complete backtest workflow."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self) -> None:
        """Test complete backtest workflow from code to visualizations."""
        with BacktestEngineImpl(timeout=120) as engine:
            strategy_code = """
import pandas as pd
position = pd.DataFrame({
    'AAPL': [1, 0, 1],
    'GOOGL': [0, 1, 0]
}, index=pd.date_range('2023-01-01', periods=3))
"""

            # Mock finlab
            mock_sim_result = Mock()
            mock_sim_result.trades = pd.DataFrame({
                'pnl': [0.05, -0.02, 0.03, 0.01],
                'entry_date': pd.date_range('2023-01-01', periods=4),
                'exit_date': pd.date_range('2023-01-02', periods=4)
            })
            mock_sim_result.equity_curve = pd.Series(
                [100, 105, 103, 106, 107],
                index=pd.date_range('2023-01-01', periods=5)
            )

            with patch('src.backtest.engine.backtest.sim', return_value=mock_sim_result):
                with patch('src.backtest.engine.finlab'):
                    # Run backtest
                    result = await engine.run_backtest(
                        strategy_code,
                        data_config={},
                        backtest_params={'sim_params': {}}
                    )

            # Calculate metrics
            metrics = calculate_metrics(result)

            # Generate visualizations
            charts = generate_visualizations(result)

        # Verify complete workflow
        assert isinstance(result, BacktestResult)
        assert isinstance(metrics, PerformanceMetrics)
        assert len(charts) == 3
        assert metrics.total_trades == 4
        assert metrics.win_rate > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
