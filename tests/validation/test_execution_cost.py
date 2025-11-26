"""
TDD Tests for Execution Cost Model (Spec B P1).

Tests written FIRST following Red-Green-Refactor cycle.
Execution Cost Model with Square Root Law slippage calculation.

Test Coverage:
- Slippage calculation formula
- Penalty tiers
- Volatility adjustment
- Edge cases
"""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any


class TestExecutionCostModel:
    """TDD tests for Execution Cost Model - Write FIRST (RED phase)."""

    @pytest.fixture
    def cost_model(self):
        """Create ExecutionCostModel with default parameters."""
        from src.validation.execution_cost import ExecutionCostModel
        return ExecutionCostModel()

    @pytest.fixture
    def sample_data(self) -> Dict[str, pd.DataFrame]:
        """Sample data for testing."""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=50, freq='D')

        return {
            'trade_size': pd.DataFrame({
                '2330': [500_000] * 50,   # 500k TWD trade
                '2317': [100_000] * 50,   # 100k TWD trade
            }, index=dates),
            'adv': pd.DataFrame({
                '2330': [5_000_000] * 50,  # 5M ADV (10% participation)
                '2317': [1_000_000] * 50,  # 1M ADV (10% participation)
            }, index=dates),
            'returns': pd.DataFrame({
                '2330': np.random.randn(50) * 0.02,  # ~2% daily vol
                '2317': np.random.randn(50) * 0.03,  # ~3% daily vol
            }, index=dates),
        }

    def test_slippage_basic_formula(self, cost_model, sample_data):
        """RED: Slippage = Base + α × sqrt(Size/ADV) × Volatility"""
        slippage = cost_model.calculate_slippage(
            trade_size=sample_data['trade_size'],
            adv=sample_data['adv'],
            returns=sample_data['returns']
        )

        # Slippage should be positive
        assert (slippage >= 0).all().all(), "Slippage must be non-negative"

        # Slippage should be in reasonable range (< 500 bps typically)
        assert (slippage < 500).all().all(), "Slippage too high, check calculation"

    def test_slippage_increases_with_trade_size(self, cost_model):
        """RED: Larger trades should have higher slippage"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')

        small_trade = pd.DataFrame({'2330': [100_000] * 30}, index=dates)
        large_trade = pd.DataFrame({'2330': [1_000_000] * 30}, index=dates)
        adv = pd.DataFrame({'2330': [5_000_000] * 30}, index=dates)
        returns = pd.DataFrame({'2330': np.random.randn(30) * 0.02}, index=dates)

        slippage_small = cost_model.calculate_slippage(small_trade, adv, returns)
        slippage_large = cost_model.calculate_slippage(large_trade, adv, returns)

        # Average slippage for large trade should be higher
        assert slippage_large.mean().mean() > slippage_small.mean().mean(), \
            "Larger trades should have higher slippage"

    def test_slippage_decreases_with_adv(self, cost_model):
        """RED: Higher ADV should reduce slippage"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')

        trade_size = pd.DataFrame({'2330': [500_000] * 30}, index=dates)
        low_adv = pd.DataFrame({'2330': [1_000_000] * 30}, index=dates)
        high_adv = pd.DataFrame({'2330': [10_000_000] * 30}, index=dates)
        returns = pd.DataFrame({'2330': np.random.randn(30) * 0.02}, index=dates)

        slippage_low = cost_model.calculate_slippage(trade_size, low_adv, returns)
        slippage_high = cost_model.calculate_slippage(trade_size, high_adv, returns)

        # Slippage with high ADV should be lower
        assert slippage_high.mean().mean() < slippage_low.mean().mean(), \
            "Higher ADV should reduce slippage"

    def test_slippage_increases_with_volatility(self, cost_model):
        """RED: Higher volatility should increase slippage"""
        dates = pd.date_range('2023-01-01', periods=30, freq='D')

        trade_size = pd.DataFrame({'2330': [500_000] * 30}, index=dates)
        adv = pd.DataFrame({'2330': [5_000_000] * 30}, index=dates)
        low_vol = pd.DataFrame({'2330': np.random.randn(30) * 0.01}, index=dates)  # 1% vol
        high_vol = pd.DataFrame({'2330': np.random.randn(30) * 0.05}, index=dates)  # 5% vol

        slippage_low = cost_model.calculate_slippage(trade_size, adv, low_vol)
        slippage_high = cost_model.calculate_slippage(trade_size, adv, high_vol)

        # Slippage with high vol should be higher
        assert slippage_high.mean().mean() > slippage_low.mean().mean(), \
            "Higher volatility should increase slippage"

    def test_base_cost_parameter(self):
        """RED: Custom base cost should be applied"""
        from src.validation.execution_cost import ExecutionCostModel

        model_10bps = ExecutionCostModel(base_cost_bps=10)
        model_20bps = ExecutionCostModel(base_cost_bps=20)

        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        trade_size = pd.DataFrame({'2330': [500_000] * 10}, index=dates)
        adv = pd.DataFrame({'2330': [5_000_000] * 10}, index=dates)
        returns = pd.DataFrame({'2330': [0.0] * 10}, index=dates)  # Zero vol

        slippage_10 = model_10bps.calculate_slippage(trade_size, adv, returns)
        slippage_20 = model_20bps.calculate_slippage(trade_size, adv, returns)

        # Higher base cost should result in higher slippage
        assert slippage_20.mean().mean() > slippage_10.mean().mean()


class TestLiquidityPenalty:
    """Tests for liquidity penalty calculation."""

    @pytest.fixture
    def cost_model(self):
        from src.validation.execution_cost import ExecutionCostModel
        return ExecutionCostModel()

    def test_no_penalty_below_20bps(self, cost_model):
        """RED: No penalty for slippage < 20 bps"""
        penalty = cost_model.calculate_liquidity_penalty(
            strategy_return=0.20,  # 20% return
            avg_slippage_bps=15    # 15 bps slippage
        )
        assert penalty == 0.0, "No penalty for slippage < 20 bps"

    def test_linear_penalty_20_to_50bps(self, cost_model):
        """RED: Linear penalty for 20 <= slippage < 50 bps"""
        penalty_20 = cost_model.calculate_liquidity_penalty(0.20, 20)
        penalty_35 = cost_model.calculate_liquidity_penalty(0.20, 35)
        penalty_50 = cost_model.calculate_liquidity_penalty(0.20, 50)

        # Penalty should be 0 at 20 bps
        assert penalty_20 == 0.0

        # Penalty should be between 0 and 0.5 for 35 bps
        assert 0 < penalty_35 < 0.5

        # Penalty should be 0.5 at 50 bps
        assert abs(penalty_50 - 0.5) < 0.01

    def test_quadratic_penalty_above_50bps(self, cost_model):
        """RED: Quadratic penalty for slippage > 50 bps"""
        penalty_50 = cost_model.calculate_liquidity_penalty(0.20, 50)
        penalty_75 = cost_model.calculate_liquidity_penalty(0.20, 75)
        penalty_100 = cost_model.calculate_liquidity_penalty(0.20, 100)

        # Penalty should increase quadratically above 50 bps
        # 75 bps: penalty = 0.5 + (75-50)^2 / 10000 = 0.5 + 0.0625 = 0.5625
        assert penalty_75 > penalty_50

        # 100 bps: penalty = 0.5 + (100-50)^2 / 10000 = 0.5 + 0.25 = 0.75
        assert penalty_100 > penalty_75


class TestNetReturn:
    """Tests for net return calculation."""

    @pytest.fixture
    def cost_model(self):
        from src.validation.execution_cost import ExecutionCostModel
        return ExecutionCostModel()

    def test_net_return_deducts_slippage(self, cost_model):
        """RED: Net return should deduct slippage from gross return"""
        gross_return = 0.20  # 20%
        avg_slippage_bps = 30  # 30 bps

        net_return = cost_model.calculate_net_return(gross_return, avg_slippage_bps)

        # Net return should be less than gross return
        assert net_return < gross_return

        # Net return should be approximately gross - slippage%
        # 30 bps = 0.30% = 0.003, so net should be ~0.197
        expected_net = gross_return - (avg_slippage_bps / 10000)
        assert abs(net_return - expected_net) < 0.001


class TestExecutionCostModelEdgeCases:
    """Edge case tests."""

    @pytest.fixture
    def cost_model(self):
        from src.validation.execution_cost import ExecutionCostModel
        return ExecutionCostModel()

    def test_zero_trade_size(self, cost_model):
        """RED: Zero trade size should have minimal slippage"""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        trade_size = pd.DataFrame({'2330': [0.0] * 10}, index=dates)
        adv = pd.DataFrame({'2330': [5_000_000] * 10}, index=dates)
        returns = pd.DataFrame({'2330': np.random.randn(10) * 0.02}, index=dates)

        slippage = cost_model.calculate_slippage(trade_size, adv, returns)

        # Slippage should be base cost only (since sqrt(0) = 0)
        assert slippage.mean().mean() == cost_model.base_cost_bps

    def test_very_low_adv(self, cost_model):
        """RED: Very low ADV should result in high slippage"""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        trade_size = pd.DataFrame({'2330': [500_000] * 10}, index=dates)
        adv = pd.DataFrame({'2330': [100_000] * 10}, index=dates)  # Very low ADV
        returns = pd.DataFrame({'2330': np.random.randn(10) * 0.02}, index=dates)

        slippage = cost_model.calculate_slippage(trade_size, adv, returns)

        # Slippage should be high due to low ADV
        assert slippage.mean().mean() > 50, "Low ADV should result in high slippage"

    def test_nan_handling(self, cost_model):
        """RED: NaN values should be handled gracefully"""
        dates = pd.date_range('2023-01-01', periods=10, freq='D')
        trade_size = pd.DataFrame({'2330': [500_000] * 10}, index=dates)
        adv = pd.DataFrame({'2330': [5_000_000] * 10}, index=dates)
        returns = pd.DataFrame({'2330': [np.nan] * 10}, index=dates)

        # Should not crash
        slippage = cost_model.calculate_slippage(trade_size, adv, returns)
        assert slippage is not None

    def test_empty_dataframes(self, cost_model):
        """RED: Empty DataFrames should return empty result"""
        empty_df = pd.DataFrame()
        slippage = cost_model.calculate_slippage(empty_df, empty_df, empty_df)
        assert slippage.empty
