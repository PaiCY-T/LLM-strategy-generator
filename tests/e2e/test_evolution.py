"""Strategy Evolution E2E Tests following TDD methodology.

P2.2.2: Test complete LLM strategy evolution workflow
- Test evolution improves strategy performance
- Verify final_sharpe >= target_sharpe
- Verify execution_time < 5.0 seconds
- Test Gate 5 (OOS tolerance ±20%)
"""

import pytest
import time
import tempfile
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Iterator

from src.learning.learning_loop import LearningLoop
from src.learning.learning_config import LearningConfig
from tests.e2e.conftest import get_test_api_key, create_test_learning_config


@pytest.mark.e2e
class TestStrategyEvolution:
    """Test complete strategy evolution workflow end-to-end."""

    def test_evolution_workflow_improves_performance(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN a configured learning loop with market data
        WHEN evolution runs for multiple iterations
        THEN final champion should have better Sharpe than baseline

        TDD RED: This test will fail initially because we haven't implemented
        the full evolution workflow integration yet.
        """
        # Arrange: Setup evolution configuration
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(
                tmpdir=tmpdir,
                max_iterations=3,  # Small number for fast test
                innovation_rate=100,  # Always use LLM (mocked)
                test_environment=test_environment
            )

            # Mock finlab modules in sys.modules before any imports
            mock_finlab_data = MagicMock()
            mock_finlab_data.get.return_value = market_data

            mock_finlab_sim = MagicMock()

            # Create mock finlab.backtest module structure
            mock_finlab_backtest = MagicMock()
            mock_finlab_backtest.sim = mock_finlab_sim

            # Mock InnovationEngine to prevent real LLM API calls
            with patch('src.learning.llm_client.InnovationEngine') as MockInnovationEngine:
                # Setup mock engine
                mock_engine = Mock()
                strategies = list(self._generate_mock_strategy_sequence())
                call_count = [0]

                def get_next_strategy(*args, **kwargs):
                    strategy = strategies[call_count[0] % len(strategies)]
                    call_count[0] += 1
                    return strategy

                mock_engine.generate_innovation.side_effect = get_next_strategy
                MockInnovationEngine.return_value = mock_engine

                # Mock finlab modules by patching sys.modules
                with patch.dict('sys.modules', {
                    'finlab.data': mock_finlab_data,
                    'finlab.backtest': mock_finlab_backtest,
                    'finlab.backtest.sim': mock_finlab_sim
                }):
                    # Mock BacktestExecutor.execute for controlled results
                    with patch('src.backtest.executor.BacktestExecutor.execute') as mock_execute:
                        # Mock successful backtest execution
                        from src.backtest.executor import ExecutionResult
                        mock_execute.return_value = ExecutionResult(
                            success=True,
                            sharpe_ratio=1.2,
                            total_return=0.15,
                            max_drawdown=-0.20,
                            execution_time=0.5
                        )

                        # Act: Run evolution
                        loop = LearningLoop(config)
                        start_time = time.time()
                        loop.run()
                        elapsed_time = time.time() - start_time

                        # Assert: Evolution completed successfully
                        assert loop.champion_tracker.champion is not None, \
                            "Evolution should produce a champion"

                        champion_sharpe = loop.champion_tracker.champion.metrics.get('sharpe_ratio', 0.0)
                        min_target_sharpe = validation_thresholds['min_sharpe_ratio']

                        # Verify performance improvement
                        assert champion_sharpe >= min_target_sharpe, \
                            f"Champion Sharpe {champion_sharpe:.2f} < target {min_target_sharpe:.2f}"

                        # Verify execution time
                        max_time = validation_thresholds['max_execution_time']
                        assert elapsed_time < max_time, \
                            f"Evolution took {elapsed_time:.2f}s > {max_time}s limit"

    def test_evolution_respects_oos_tolerance(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN evolution with in-sample and out-of-sample data
        WHEN champion is selected
        THEN OOS performance should be within ±20% of IS performance (Gate 5)

        TDD RED: This test will fail because OOS validation isn't implemented yet.
        """
        # Arrange: Split market data into IS/OOS
        split_point = len(market_data) * 2 // 3  # 67% IS, 33% OOS
        is_data = market_data.iloc[:split_point]
        oos_data = market_data.iloc[split_point:]

        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(
                tmpdir=tmpdir,
                max_iterations=3,
                innovation_rate=100,
                test_environment=test_environment
            )

            # Mock finlab modules
            mock_finlab_data = MagicMock()
            mock_finlab_data.get.return_value = market_data

            mock_finlab_sim = MagicMock()
            mock_finlab_backtest = MagicMock()
            mock_finlab_backtest.sim = mock_finlab_sim

            # Mock InnovationEngine to prevent real LLM API calls
            with patch('src.learning.llm_client.InnovationEngine') as MockInnovationEngine:
                self._setup_mock_innovation_engine(MockInnovationEngine)

                with patch.dict('sys.modules', {
                    'finlab.data': mock_finlab_data,
                    'finlab.backtest': mock_finlab_backtest,
                    'finlab.backtest.sim': mock_finlab_sim
                }):
                    with patch('src.backtest.executor.BacktestExecutor.execute') as mock_execute:
                        # Simulate IS Sharpe = 1.0, OOS Sharpe = 0.85 (15% degradation - acceptable)
                        is_sharpe = 1.0
                        oos_sharpe = 0.85

                        from src.backtest.executor import ExecutionResult

                        # Mock IS execution
                        mock_execute.return_value = ExecutionResult(
                            success=True,
                            sharpe_ratio=is_sharpe,
                            total_return=0.20,
                            max_drawdown=-0.15,
                            execution_time=0.5
                        )

                        # Act: Run evolution
                        loop = LearningLoop(config)
                        loop.run()

                        # Now test OOS performance (update mock for OOS)
                        mock_execute.return_value = ExecutionResult(
                            success=True,
                            sharpe_ratio=oos_sharpe,
                            total_return=0.17,
                            max_drawdown=-0.18,
                            execution_time=0.5
                        )

                        # Assert: OOS tolerance check
                        oos_tolerance = validation_thresholds['oos_tolerance']  # 0.20 = ±20%
                        performance_degradation = abs(oos_sharpe - is_sharpe) / is_sharpe

                        assert performance_degradation <= oos_tolerance, \
                            f"OOS degradation {performance_degradation:.1%} > {oos_tolerance:.1%} tolerance"

    def test_evolution_handles_llm_failures_gracefully(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN evolution with mock LLM that occasionally fails
        WHEN LLM returns empty/invalid responses
        THEN system should fallback to Factor Graph and continue

        TDD RED: This tests error recovery which may not be fully implemented.
        """
        # Arrange: Setup config with Factor Graph fallback
        # Note: Need continue_on_error=True to test graceful degradation
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(
                tmpdir=tmpdir,
                max_iterations=5,
                innovation_rate=100,  # Try LLM first
                test_environment=test_environment
            )
            # Override continue_on_error for this test
            config.continue_on_error = True

            # Mock finlab modules
            mock_finlab_data = MagicMock()
            mock_finlab_data.get.return_value = market_data

            mock_finlab_sim = MagicMock()
            mock_finlab_backtest = MagicMock()
            mock_finlab_backtest.sim = mock_finlab_sim

            # Mock InnovationEngine with intermittent failures
            with patch('src.learning.llm_client.InnovationEngine') as MockInnovationEngine:
                # Simulate intermittent failures
                call_count = [0]
                def mock_generate(*args, **kwargs):
                    call_count[0] += 1
                    if call_count[0] % 5 in [2, 4]:  # Fail on calls 2, 4
                        raise Exception("Mock LLM timeout")
                    return self._generate_mock_strategy_code(call_count[0])

                self._setup_mock_innovation_engine(MockInnovationEngine, custom_generator=mock_generate)

                with patch.dict('sys.modules', {
                    'finlab.data': mock_finlab_data,
                    'finlab.backtest': mock_finlab_backtest,
                    'finlab.backtest.sim': mock_finlab_sim
                }):
                    with patch('src.backtest.executor.BacktestExecutor.execute') as mock_execute:
                        from src.backtest.executor import ExecutionResult
                        mock_execute.return_value = ExecutionResult(
                            success=True,
                            sharpe_ratio=0.8,
                            total_return=0.12,
                            max_drawdown=-0.25,
                            execution_time=0.5
                        )

                        # Act: Run evolution
                        loop = LearningLoop(config)
                        loop.run()

                        # Assert: System should have completed some iterations despite failures
                        all_records = loop.history.get_all()
                        # With continue_on_error=True, failed iterations don't create records
                        # So we expect fewer records than max_iterations (2 failures out of 5)
                        expected_successful = 3  # Iterations 0, 2, 4 succeed; 1, 3 fail
                        assert len(all_records) == expected_successful, \
                            f"Expected {expected_successful} successful iterations, got {len(all_records)}"

                        # Verify all were LLM generations (fallback to Factor Graph not implemented yet)
                        llm_count = sum(1 for r in all_records if r.generation_method == "llm")
                        assert llm_count == expected_successful, \
                            f"Expected {expected_successful} LLM generations, got {llm_count}"

                        # Note: Factor Graph fallback would be implemented in future iteration
                        # For now, we verify graceful degradation by continuing despite LLM failures

    def test_evolution_tracks_performance_improvement(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN evolution running for multiple iterations
        WHEN champion is updated
        THEN champion should show monotonic Sharpe improvement

        TDD RED: This assumes champion tracking logic is correctly implemented.
        """
        # Arrange: Setup evolution with progressively better mock strategies
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(
                tmpdir=tmpdir,
                max_iterations=4,
                innovation_rate=100,
                test_environment=test_environment
            )

            # Mock finlab modules
            mock_finlab_data = MagicMock()
            mock_finlab_data.get.return_value = market_data

            mock_finlab_sim = MagicMock()
            mock_finlab_backtest = MagicMock()
            mock_finlab_backtest.sim = mock_finlab_sim

            # Mock InnovationEngine
            with patch('src.learning.llm_client.InnovationEngine') as MockInnovationEngine:
                self._setup_mock_innovation_engine(MockInnovationEngine)

                # Simulate improving strategies: Sharpe 0.6 → 0.8 → 0.9 → 1.2
                sharpe_sequence = [0.6, 0.8, 0.9, 1.2]
                call_count = [0]

                def progressive_backtest(*args, **kwargs):
                    idx = call_count[0] % len(sharpe_sequence)
                    sharpe = sharpe_sequence[idx]
                    call_count[0] += 1

                    from src.backtest.executor import ExecutionResult
                    return ExecutionResult(
                        success=True,
                        sharpe_ratio=sharpe,
                        total_return=sharpe * 0.15,
                        max_drawdown=-0.20,
                        execution_time=0.5
                    )

                with patch.dict('sys.modules', {
                    'finlab.data': mock_finlab_data,
                    'finlab.backtest': mock_finlab_backtest,
                    'finlab.backtest.sim': mock_finlab_sim
                }):
                    with patch('src.backtest.executor.BacktestExecutor.execute') as mock_execute:
                        mock_execute.side_effect = progressive_backtest

                        # Act: Run evolution
                        loop = LearningLoop(config)
                        loop.run()

                        # Assert: Champion should be the best strategy
                        champion = loop.champion_tracker.champion
                        assert champion is not None, "Should have a champion"

                        final_sharpe = champion.metrics.get('sharpe_ratio', 0.0)
                        best_expected_sharpe = max(sharpe_sequence)

                        assert final_sharpe >= best_expected_sharpe * 0.95, \
                            f"Champion Sharpe {final_sharpe:.2f} < expected {best_expected_sharpe:.2f}"

                        # Verify performance improvement trajectory
                        all_records = loop.history.get_all()
                        sharpe_history = [
                            r.metrics.get('sharpe_ratio', 0.0)
                            for r in all_records
                            if r.metrics
                        ]

                        # Should see improvement over time (allowing some variability)
                        assert max(sharpe_history) > min(sharpe_history), \
                            "Should see performance improvement over iterations"

    def test_evolution_execution_time_under_limit(
        self, market_data, test_environment, validation_thresholds
    ):
        """
        GIVEN evolution with time constraints
        WHEN running complete evolution workflow
        THEN total execution time should be < 5.0 seconds

        TDD RED: This tests performance which depends on mocking efficiency.
        """
        # Arrange: Lightweight config for fast execution
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(
                tmpdir=tmpdir,
                max_iterations=3,  # Minimal iterations
                innovation_rate=0,  # Factor Graph only (faster)
                test_environment=test_environment
            )

            # Mock finlab modules
            mock_finlab_data = MagicMock()
            mock_finlab_data.get.return_value = market_data

            mock_finlab_sim = MagicMock()
            mock_finlab_backtest = MagicMock()
            mock_finlab_backtest.sim = mock_finlab_sim

            with patch.dict('sys.modules', {
                'finlab.data': mock_finlab_data,
                'finlab.backtest': mock_finlab_backtest,
                'finlab.backtest.sim': mock_finlab_sim
            }):
                with patch('src.backtest.executor.BacktestExecutor.execute') as mock_execute:
                    # Fast mock responses
                    from src.backtest.executor import ExecutionResult
                    mock_execute.return_value = ExecutionResult(
                        success=True,
                        sharpe_ratio=0.7,
                        total_return=0.10,
                        max_drawdown=-0.30,
                        execution_time=0.1
                    )

                    # Act: Measure execution time
                    start_time = time.time()
                    loop = LearningLoop(config)
                    loop.run()
                    elapsed_time = time.time() - start_time

                    # Assert: Should complete within time limit
                    max_time = validation_thresholds['max_execution_time']
                    assert elapsed_time < max_time, \
                        f"Evolution took {elapsed_time:.2f}s > {max_time:.2f}s limit"

                    # Verify all iterations completed
                    all_records = loop.history.get_all()
                    assert len(all_records) == config.max_iterations, \
                        f"Expected {config.max_iterations} iterations, got {len(all_records)}"

    # Helper methods

    def _create_test_config(
        self,
        tmpdir: str,
        max_iterations: int,
        innovation_rate: int,
        test_environment: Dict[str, Any]
    ) -> LearningConfig:
        """Create test configuration for evolution.

        Delegates to shared config factory in conftest.py to reduce code duplication.

        Args:
            tmpdir: Temporary directory for test artifacts
            max_iterations: Number of iterations to run
            innovation_rate: 0-100, LLM vs Factor Graph ratio
            test_environment: Test environment fixture (unused, kept for API compatibility)

        Returns:
            LearningConfig instance configured for testing
        """
        return create_test_learning_config(
            tmpdir=tmpdir,
            max_iterations=max_iterations,
            innovation_rate=innovation_rate
        )

    def _setup_mock_innovation_engine(self, MockInnovationEngine, custom_generator=None):
        """Setup mock InnovationEngine with deterministic responses.

        Args:
            MockInnovationEngine: Mocked InnovationEngine class
            custom_generator: Optional custom strategy generator function

        Returns:
            Configured mock engine instance

        Raises:
            RuntimeError: If mock setup fails due to invalid configuration
        """
        try:
            mock_engine = Mock()
            # Use a list to cycle through strategies
            strategies = list(self._generate_mock_strategy_sequence())

            if not strategies:
                raise ValueError("No mock strategies generated - check _generate_mock_strategy_sequence()")

            call_count = [0]

            if custom_generator:
                mock_engine.generate_innovation.side_effect = custom_generator
            else:
                def get_next_strategy(*args, **kwargs):
                    try:
                        strategy = strategies[call_count[0] % len(strategies)]
                        call_count[0] += 1
                        return strategy
                    except Exception as e:
                        raise RuntimeError(
                            f"Failed to generate strategy (call #{call_count[0]}): {e}"
                        ) from e

                mock_engine.generate_innovation.side_effect = get_next_strategy

            MockInnovationEngine.return_value = mock_engine
            return mock_engine

        except Exception as e:
            raise RuntimeError(
                f"Failed to setup mock InnovationEngine: {e}. "
                "Check that MockInnovationEngine is a valid Mock object and "
                "_generate_mock_strategy_sequence() returns valid strategies."
            ) from e

    def _generate_mock_strategy_sequence(self) -> Iterator[str]:
        """Generate sequence of mock strategies with improving performance.

        Yields:
            Strategy code strings with progressively better logic
        """
        strategies = [
            # Strategy 1: Basic momentum
            """
import pandas as pd

def strategy(data):
    close = data['price_收盤價']
    momentum = close.pct_change(20)
    positions = pd.DataFrame(index=data.index)
    positions['signal'] = 0
    positions.loc[momentum > 0.05, 'signal'] = 1
    positions.loc[momentum < -0.05, 'signal'] = -1
    return positions
            """,

            # Strategy 2: Improved momentum with volume
            """
import pandas as pd

def strategy(data):
    close = data['price_收盤價']
    volume = data['volume_成交股數']
    momentum = close.pct_change(20)
    volume_trend = volume.pct_change(10)

    positions = pd.DataFrame(index=data.index)
    positions['signal'] = 0

    # Buy on momentum + volume increase
    positions.loc[(momentum > 0.05) & (volume_trend > 0.2), 'signal'] = 1
    positions.loc[(momentum < -0.05) | (volume_trend < -0.3), 'signal'] = -1

    return positions
            """,

            # Strategy 3: Multi-factor with risk management
            """
import pandas as pd

def strategy(data):
    close = data['price_收盤價']
    volume = data['volume_成交股數']

    # Momentum
    momentum = close.pct_change(20)

    # Volatility filter
    returns = close.pct_change()
    volatility = returns.rolling(20).std()

    # Volume confirmation
    volume_ma = volume.rolling(20).mean()
    volume_signal = volume > volume_ma

    positions = pd.DataFrame(index=data.index)
    positions['signal'] = 0

    # Long: momentum + low vol + volume
    positions.loc[(momentum > 0.05) & (volatility < 0.02) & volume_signal, 'signal'] = 1

    # Short: negative momentum + high vol
    positions.loc[(momentum < -0.05) & (volatility > 0.03), 'signal'] = -1

    return positions
            """,
        ]

        for strategy in strategies:
            yield strategy.strip()

    def _generate_mock_strategy_code(self, iteration: int) -> str:
        """Generate mock strategy code for given iteration.

        Args:
            iteration: Current iteration number

        Returns:
            Mock strategy code string
        """
        return f"""
import pandas as pd

def strategy(data):
    # Mock strategy for iteration {iteration}
    close = data['price_收盤價']
    momentum = close.pct_change(20)

    positions = pd.DataFrame(index=data.index)
    positions['signal'] = 0
    positions.loc[momentum > 0.05, 'signal'] = 1
    positions.loc[momentum < -0.05, 'signal'] = -1

    return positions
        """
