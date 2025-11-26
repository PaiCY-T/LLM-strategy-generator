"""
Integration Tests for P1 Components with Existing System

Tests the integration of Spec B P1 components with the existing LLM strategy
generation workflow. Validates that new components work correctly with:
- Factor library integration
- Validation layer integration
- Scoring system integration
- End-to-end strategy evaluation

Test Structure:
1. Factor Library Integration
   - RSI and RVOL factors with real data
   - Integration with template parameter generator
   - Factor signal generation and validation

2. Validation Layer Integration
   - Liquidity filter with backtest results
   - Execution cost calculation with trade data
   - Integration with existing metrics

3. Comprehensive Scoring Integration
   - Multi-objective scoring with real strategies
   - Integration with champion tracker
   - Ranking and selection workflow

4. End-to-End Workflow
   - Strategy generation → Factor calculation → Validation → Scoring
   - Full pipeline with P1 components
   - Performance and correctness validation
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

from src.factor_library.mean_reversion_factors import rsi_factor, rvol_factor
from src.validation.liquidity_filter import LiquidityFilter, LiquidityTier
from src.validation.execution_cost import ExecutionCostModel
from src.validation.comprehensive_scorer import ComprehensiveScorer
from src.backtest.metrics import StrategyMetrics


class TestFactorLibraryIntegration:
    """Test factor library integration with existing system."""

    def test_rsi_factor_with_real_data_shape(self):
        """Test RSI factor generates valid signals with realistic data."""
        # Simulate 100 days of price data - use DataFrame, not Series
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        close = pd.DataFrame({
            'stock_1': 100 + np.cumsum(np.random.randn(100) * 2)  # Random walk
        }, index=dates)

        result = rsi_factor(close, {'rsi_period': 14})

        assert 'signal' in result
        assert len(result['signal']) == len(close)
        assert result['signal'].min().min() >= -1.0
        assert result['signal'].max().max() <= 1.0

    def test_rvol_factor_with_real_data_shape(self):
        """Test RVOL factor generates valid signals with realistic data."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        volume = pd.DataFrame({
            'stock_1': np.random.randint(1_000_000, 10_000_000, 100)
        }, index=dates)

        result = rvol_factor(volume, {'rvol_period': 20})

        assert 'signal' in result
        assert len(result['signal']) == len(volume)
        assert result['signal'].min().min() >= -1.0
        assert result['signal'].max().max() <= 1.0

    def test_combined_factors_signal_generation(self):
        """Test combining RSI and RVOL signals."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        close = pd.DataFrame({
            'stock_1': 100 + np.cumsum(np.random.randn(100) * 2)
        }, index=dates)
        volume = pd.DataFrame({
            'stock_1': np.random.randint(1_000_000, 10_000_000, 100)
        }, index=dates)

        rsi_result = rsi_factor(close, {'rsi_period': 14})
        rvol_result = rvol_factor(volume, {'rvol_period': 20})

        # Combine signals (simple average)
        combined_signal = (rsi_result['signal'] + rvol_result['signal']) / 2

        assert len(combined_signal) == len(close)
        assert combined_signal.min().min() >= -1.0
        assert combined_signal.max().max() <= 1.0
        assert not combined_signal.isna().all().all()


class TestValidationLayerIntegration:
    """Test validation layer integration with backtest results."""

    def test_liquidity_filter_with_backtest_data(self):
        """Test liquidity filter processes backtest-style data."""
        # Simulate 30 stocks, 100 days
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        stocks = [f'stock_{i}' for i in range(30)]

        # Create volume data (some stocks liquid, some illiquid)
        volume_data = []
        for stock in stocks:
            if stock.endswith('0'):  # Every 10th stock is illiquid
                daily_vol = np.random.randint(100_000, 500_000, 100)
            else:
                daily_vol = np.random.randint(5_000_000, 20_000_000, 100)
            volume_data.append(pd.Series(daily_vol, index=dates, name=stock))

        volume_df = pd.concat(volume_data, axis=1)
        close_df = pd.DataFrame(
            np.random.randn(100, 30) * 10 + 100,
            index=dates,
            columns=stocks
        )

        # Calculate dollar volume
        dollar_volume = volume_df * close_df

        # Apply liquidity filter
        filter = LiquidityFilter(capital=40_000_000)
        signals = pd.DataFrame(
            np.random.randn(100, 30) * 0.5,
            index=dates,
            columns=stocks
        )

        filtered = filter.apply_filter(signals, dollar_volume)

        # Verify illiquid stocks have reduced signals (or equal if already low)
        illiquid_stocks = [s for s in stocks if s.endswith('0')]
        for stock in illiquid_stocks:
            assert filtered[stock].abs().mean() <= signals[stock].abs().mean()

    def test_execution_cost_with_strategy_metrics(self):
        """Test execution cost calculation with realistic strategy data."""
        model = ExecutionCostModel()

        # Simulate strategy with 100 trades - use scalar method
        trade_sizes = np.random.uniform(500_000, 5_000_000, 100)
        advs = np.random.uniform(10_000_000, 100_000_000, 100)
        volatilities = np.random.uniform(0.01, 0.05, 100)  # 1-5% daily vol

        slippages = []
        for size, adv, vol in zip(trade_sizes, advs, volatilities):
            # Use new scalar method
            slippage = model.calculate_single_slippage(size, adv, vol)
            slippages.append(slippage)

        avg_slippage_bps = np.mean(slippages)

        # Verify slippage is reasonable
        assert 0 <= avg_slippage_bps <= 100  # Between 0-1%
        assert len(slippages) == 100

    def test_validation_pipeline_integration(self):
        """Test full validation pipeline with all components."""
        # Setup
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        stocks = [f'stock_{i}' for i in range(10)]

        close = pd.DataFrame(
            100 + np.cumsum(np.random.randn(100, 10) * 2, axis=0),
            index=dates,
            columns=stocks
        )
        volume = pd.DataFrame(
            np.random.randint(1_000_000, 10_000_000, (100, 10)),
            index=dates,
            columns=stocks
        )
        dollar_volume = close * volume

        # Generate signals using RSI
        signals = pd.DataFrame(index=dates, columns=stocks)
        for stock in stocks:
            # Convert Series to DataFrame for factor input
            close_df = pd.DataFrame({stock: close[stock]})
            rsi_result = rsi_factor(close_df, {'rsi_period': 14})
            signals[stock] = rsi_result['signal'][stock]

        # Apply liquidity filter
        filter = LiquidityFilter(capital=40_000_000)
        filtered_signals = filter.apply_filter(signals, dollar_volume)

        # Calculate execution costs
        cost_model = ExecutionCostModel()
        position_sizes = filtered_signals.abs() * 40_000_000 * 0.05  # 5% per position

        total_costs = []
        for date in dates[:50]:  # Sample first 50 days
            if date in position_sizes.index:
                daily_positions = position_sizes.loc[date]
                daily_adv = dollar_volume.loc[date]
                daily_returns = close.pct_change().loc[date] if date in close.index else pd.Series(0, index=stocks)

                for stock in stocks:
                    if daily_positions[stock] > 0 and daily_adv[stock] > 0:
                        # Use scalar method for single trade
                        vol = abs(daily_returns[stock]) if not pd.isna(daily_returns[stock]) else 0.02
                        slippage = cost_model.calculate_single_slippage(
                            daily_positions[stock],
                            daily_adv[stock],
                            vol
                        )
                        total_costs.append(slippage)

        # Verify pipeline produces reasonable results
        assert len(filtered_signals) == len(signals)
        assert len(total_costs) > 0
        assert np.mean(total_costs) >= 0


class TestComprehensiveScoringIntegration:
    """Test comprehensive scoring integration with existing metrics."""

    def test_scorer_with_strategy_metrics(self):
        """Test scorer processes StrategyMetrics correctly."""
        scorer = ComprehensiveScorer()

        # Simulate realistic strategy performance
        monthly_returns = pd.Series(np.random.randn(12) * 0.05 + 0.02)  # 2% avg, 5% vol

        metrics = {
            'calmar_ratio': 2.5,
            'sortino_ratio': 3.0,
            'monthly_returns': monthly_returns,
            'annual_turnover': 2.0,
            'avg_slippage_bps': 25.0
        }

        result = scorer.compute_score(metrics)

        assert 'total_score' in result
        assert 0 <= result['total_score'] <= 1
        assert 'components' in result  # Note: key is 'components', not 'component_scores'
        assert len(result['components']) == 5

    def test_strategy_ranking_workflow(self):
        """Test ranking multiple strategies using comprehensive scorer."""
        scorer = ComprehensiveScorer()

        strategies = []
        for i in range(5):
            # Generate diverse strategy profiles
            monthly_ret = pd.Series(np.random.randn(12) * 0.05 + 0.02 * (i + 1) / 5)

            metrics = {
                'calmar_ratio': 1.5 + i * 0.5,
                'sortino_ratio': 2.0 + i * 0.3,
                'monthly_returns': monthly_ret,
                'annual_turnover': 3.0 - i * 0.4,
                'avg_slippage_bps': 30.0 - i * 5
            }

            score_result = scorer.compute_score(metrics)
            strategies.append({
                'id': f'strategy_{i}',
                'score': score_result['total_score'],
                'metrics': metrics
            })

        # Rank strategies
        ranked = sorted(strategies, key=lambda x: x['score'], reverse=True)

        assert len(ranked) == 5
        assert ranked[0]['score'] >= ranked[-1]['score']

        # Verify best strategy has reasonable characteristics
        best = ranked[0]
        assert best['metrics']['calmar_ratio'] > 1.0
        assert best['metrics']['sortino_ratio'] > 1.5


class TestEndToEndWorkflow:
    """Test end-to-end workflow with P1 components."""

    @pytest.fixture
    def market_data(self):
        """Generate realistic market data for testing."""
        dates = pd.date_range('2024-01-01', periods=252, freq='D')  # 1 year
        stocks = [f'stock_{i}' for i in range(20)]

        # Price data with trends and mean reversion
        close = pd.DataFrame(index=dates, columns=stocks)
        volume = pd.DataFrame(index=dates, columns=stocks)

        for stock in stocks:
            # Random walk with drift
            prices = 100 + np.cumsum(np.random.randn(252) * 2 + 0.05)
            close[stock] = prices

            # Volume with autocorrelation
            vol = np.random.randint(2_000_000, 15_000_000, 252)
            volume[stock] = vol

        return {
            'close': close,
            'volume': volume,
            'dollar_volume': close * volume
        }

    def test_full_pipeline_single_strategy(self, market_data):
        """Test complete pipeline for single strategy evaluation."""
        close = market_data['close']
        volume = market_data['volume']
        dollar_volume = market_data['dollar_volume']

        # Step 1: Generate factor signals
        rsi_signals = pd.DataFrame(index=close.index, columns=close.columns)
        rvol_signals = pd.DataFrame(index=close.index, columns=close.columns)

        for stock in close.columns:
            # Convert Series to DataFrame for factor functions
            close_df = pd.DataFrame({stock: close[stock]})
            volume_df = pd.DataFrame({stock: volume[stock]})

            rsi_result = rsi_factor(close_df, {'rsi_period': 14})
            rvol_result = rvol_factor(volume_df, {'rvol_period': 20})

            rsi_signals[stock] = rsi_result['signal'][stock]
            rvol_signals[stock] = rvol_result['signal'][stock]

        # Combine signals
        combined_signals = (rsi_signals + rvol_signals) / 2

        # Step 2: Apply liquidity filter
        liquidity_filter = LiquidityFilter(capital=40_000_000)
        filtered_signals = liquidity_filter.apply_filter(combined_signals, dollar_volume)

        # Step 3: Calculate execution costs
        cost_model = ExecutionCostModel()
        position_sizes = filtered_signals.abs() * 40_000_000 * 0.05

        slippages = []
        for date in close.index[20:50]:  # Sample period
            if date in position_sizes.index and date in dollar_volume.index:
                for stock in close.columns:
                    pos_size = position_sizes.loc[date, stock]
                    adv = dollar_volume.loc[date, stock]

                    if pos_size > 0 and adv > 0:
                        returns = close[stock].pct_change()
                        vol = returns.std() if len(returns) > 0 else 0.02
                        # Use scalar method
                        slippage = cost_model.calculate_single_slippage(
                            pos_size, adv, vol
                        )
                        slippages.append(slippage)

        avg_slippage_bps = np.mean(slippages) if slippages else 0

        # Step 4: Calculate returns and score
        returns = close.pct_change()
        strategy_returns = (filtered_signals.shift(1) * returns).mean(axis=1)
        monthly_returns = strategy_returns.resample('ME').sum()

        # Calculate Calmar and Sortino approximations
        annual_return = strategy_returns.mean() * 252
        max_dd = (strategy_returns.cumsum() - strategy_returns.cumsum().cummax()).min()
        calmar = abs(annual_return / max_dd) if max_dd < 0 else 0

        downside_returns = strategy_returns[strategy_returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 1
        sortino = annual_return / downside_std if downside_std > 0 else 0

        # Step 5: Comprehensive scoring
        scorer = ComprehensiveScorer()
        score_result = scorer.compute_score({
            'calmar_ratio': max(calmar, 0),
            'sortino_ratio': max(sortino, 0),
            'monthly_returns': monthly_returns,
            'annual_turnover': 2.0,
            'avg_slippage_bps': avg_slippage_bps
        })

        # Verify pipeline produces valid results
        assert 'total_score' in score_result
        assert 0 <= score_result['total_score'] <= 1
        assert len(filtered_signals) == len(close)
        assert avg_slippage_bps >= 0

    def test_multiple_strategies_comparison(self, market_data):
        """Test comparing multiple strategies through full pipeline."""
        close = market_data['close']
        volume = market_data['volume']
        dollar_volume = market_data['dollar_volume']

        strategies = []

        # Test 3 different RSI configurations
        for rsi_period in [10, 14, 20]:
            # Generate signals
            signals = pd.DataFrame(index=close.index, columns=close.columns)
            for stock in close.columns:
                # Convert Series to DataFrame for factor function
                close_df = pd.DataFrame({stock: close[stock]})
                rsi_result = rsi_factor(close_df, {'rsi_period': rsi_period})
                signals[stock] = rsi_result['signal'][stock]

            # Apply validation
            liquidity_filter = LiquidityFilter(capital=40_000_000)
            filtered = liquidity_filter.apply_filter(signals, dollar_volume)

            # Calculate returns
            returns = close.pct_change()
            strategy_returns = (filtered.shift(1) * returns).mean(axis=1)
            monthly_returns = strategy_returns.resample('ME').sum()

            # Score
            annual_return = strategy_returns.mean() * 252
            annual_vol = strategy_returns.std() * np.sqrt(252)
            sharpe = annual_return / annual_vol if annual_vol > 0 else 0

            scorer = ComprehensiveScorer()
            score_result = scorer.compute_score({
                'calmar_ratio': max(sharpe, 0),
                'sortino_ratio': max(sharpe * 1.2, 0),
                'monthly_returns': monthly_returns,
                'annual_turnover': 2.0,
                'avg_slippage_bps': 25.0
            })

            strategies.append({
                'rsi_period': rsi_period,
                'score': score_result['total_score'],
                'sharpe': sharpe
            })

        # Rank strategies
        ranked = sorted(strategies, key=lambda x: x['score'], reverse=True)

        assert len(ranked) == 3
        assert ranked[0]['score'] >= ranked[-1]['score']

        # Verify all strategies have valid scores
        for s in strategies:
            assert 0 <= s['score'] <= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
