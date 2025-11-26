"""
End-to-End Strategy Pipeline Tests

Tests the complete strategy generation, validation, and scoring pipeline
with P1 components integrated. Validates:

1. Template-based strategy generation
2. Factor signal generation and validation
3. Liquidity filtering and position sizing
4. Execution cost estimation
5. Comprehensive scoring and ranking
6. Champion update workflow

This test suite ensures that all P1 components work together correctly
in a realistic LLM strategy evolution workflow.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from unittest.mock import Mock, MagicMock, patch

from src.factor_library.mean_reversion_factors import rsi_factor, rvol_factor
from src.validation.liquidity_filter import LiquidityFilter
from src.validation.execution_cost import ExecutionCostModel
from src.validation.comprehensive_scorer import ComprehensiveScorer


class TestE2EStrategyPipeline:
    """End-to-end tests for complete strategy pipeline."""

    @pytest.fixture
    def mock_market_environment(self):
        """Create comprehensive mock market environment."""
        np.random.seed(42)

        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        stocks = [f'STOCK_{i:04d}' for i in range(50)]

        # Generate realistic price data with different characteristics
        close_data = {}
        volume_data = {}

        for i, stock in enumerate(stocks):
            # Create different market regimes for different stocks
            if i % 3 == 0:  # Trending stocks
                trend = np.linspace(0, 20, len(dates))
                noise = np.random.randn(len(dates)) * 2
                prices = 100 + trend + noise
            elif i % 3 == 1:  # Mean-reverting stocks
                prices = 100 + np.sin(np.linspace(0, 8*np.pi, len(dates))) * 15
                prices += np.random.randn(len(dates)) * 2
            else:  # Random walk stocks
                prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)

            close_data[stock] = pd.Series(prices, index=dates)

            # Volume with varying liquidity
            if i < 10:  # High liquidity
                vol = np.random.randint(10_000_000, 50_000_000, len(dates))
            elif i < 30:  # Medium liquidity
                vol = np.random.randint(2_000_000, 10_000_000, len(dates))
            else:  # Low liquidity
                vol = np.random.randint(100_000, 2_000_000, len(dates))

            volume_data[stock] = pd.Series(vol, index=dates)

        close = pd.DataFrame(close_data)
        volume = pd.DataFrame(volume_data)
        dollar_volume = close * volume

        return {
            'close': close,
            'volume': volume,
            'dollar_volume': dollar_volume,
            'dates': dates,
            'stocks': stocks
        }

    def test_strategy_generation_to_scoring(self, mock_market_environment):
        """Test complete flow: generation → validation → scoring."""
        env = mock_market_environment
        close = env['close']
        volume = env['volume']
        dollar_volume = env['dollar_volume']

        # === STEP 1: Strategy Generation (Simulated) ===
        # In real system, this would come from LLM/Template generator
        strategy_config = {
            'name': 'RSI_RVOL_MeanReversion',
            'factors': [
                {'type': 'rsi', 'period': 14, 'weight': 0.6},
                {'type': 'rvol', 'period': 20, 'weight': 0.4}
            ],
            'capital': 40_000_000,
            'max_position_pct': 0.05
        }

        # === STEP 2: Factor Signal Generation ===
        rsi_signals = pd.DataFrame(index=close.index, columns=close.columns)
        rvol_signals = pd.DataFrame(index=close.index, columns=close.columns)

        for stock in close.columns:
            # Calculate RSI - Convert Series to DataFrame for factor function
            close_df = pd.DataFrame({stock: close[stock]})
            rsi_result = rsi_factor(close_df, {
                'rsi_period': strategy_config['factors'][0]['period']
            })
            rsi_signals[stock] = rsi_result['signal'][stock]

            # Calculate RVOL - Convert Series to DataFrame for factor function
            volume_df = pd.DataFrame({stock: volume[stock]})
            rvol_result = rvol_factor(volume_df, {
                'rvol_period': strategy_config['factors'][1]['period']
            })
            rvol_signals[stock] = rvol_result['signal'][stock]

        # Combine with weights
        combined_signals = (
            rsi_signals * strategy_config['factors'][0]['weight'] +
            rvol_signals * strategy_config['factors'][1]['weight']
        )

        # === STEP 3: Liquidity Filtering ===
        liquidity_filter = LiquidityFilter(capital=strategy_config['capital'])
        filtered_signals = liquidity_filter.apply_filter(combined_signals, dollar_volume)

        # === STEP 4: Position Sizing ===
        position_sizes = filtered_signals.abs() * strategy_config['capital'] * strategy_config['max_position_pct']

        # === STEP 5: Execution Cost Estimation ===
        cost_model = ExecutionCostModel()
        execution_costs = []

        for date in close.index[50:100]:  # Sample period
            if date in position_sizes.index:
                for stock in close.columns:
                    pos_size = position_sizes.loc[date, stock]
                    adv = dollar_volume.loc[date, stock]

                    if pos_size > 0 and adv > 0:
                        returns = close[stock].pct_change()
                        vol = returns.std() if len(returns) > 0 else 0.02
                        # Use scalar method for single trade
                        slippage = cost_model.calculate_single_slippage(pos_size, adv, vol)
                        execution_costs.append(slippage)

        avg_slippage_bps = np.mean(execution_costs) if execution_costs else 0

        # === STEP 6: Performance Calculation ===
        returns = close.pct_change()
        strategy_returns = (filtered_signals.shift(1) * returns).mean(axis=1)
        strategy_returns = strategy_returns.dropna()

        # Calculate performance metrics
        annual_return = strategy_returns.mean() * 252
        annual_vol = strategy_returns.std() * np.sqrt(252)
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0

        # Calculate drawdown
        cumulative = (1 + strategy_returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()

        calmar = abs(annual_return / max_drawdown) if max_drawdown < 0 else 0

        # Calculate Sortino
        downside_returns = strategy_returns[strategy_returns < 0]
        downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else annual_vol
        sortino = annual_return / downside_vol if downside_vol > 0 else 0

        # Monthly returns
        monthly_returns = strategy_returns.resample('ME').sum()

        # === STEP 7: Comprehensive Scoring ===
        scorer = ComprehensiveScorer()
        score_result = scorer.compute_score({
            'calmar_ratio': max(calmar, 0),
            'sortino_ratio': max(sortino, 0),
            'monthly_returns': monthly_returns,
            'annual_turnover': 2.5,
            'avg_slippage_bps': avg_slippage_bps
        })

        # === VALIDATION ===
        assert score_result['total_score'] > 0, "Score should be positive"
        assert 0 <= score_result['total_score'] <= 1, "Score should be in [0, 1]"
        assert len(filtered_signals) == len(close), "Filtered signals should match input length"
        assert avg_slippage_bps >= 0, "Average slippage should be non-negative"
        assert 'components' in score_result, "Should have component scores"

        # Log results for debugging
        print(f"\n=== Strategy Evaluation Results ===")
        print(f"Total Score: {score_result['total_score']:.4f}")
        print(f"Sharpe Ratio: {sharpe:.2f}")
        print(f"Calmar Ratio: {calmar:.2f}")
        print(f"Sortino Ratio: {sortino:.2f}")
        print(f"Max Drawdown: {max_drawdown:.2%}")
        print(f"Annual Return: {annual_return:.2%}")
        print(f"Avg Slippage (bps): {avg_slippage_bps:.1f}")

    def test_multiple_strategy_generation_and_ranking(self, mock_market_environment):
        """Test generating and ranking multiple strategies."""
        env = mock_market_environment
        close = env['close']
        volume = env['volume']
        dollar_volume = env['dollar_volume']

        # Test different strategy configurations
        strategy_configs = [
            {
                'name': 'Aggressive_RSI',
                'rsi_period': 10,
                'rvol_period': 15,
                'rsi_weight': 0.8,
                'rvol_weight': 0.2
            },
            {
                'name': 'Balanced_RSI_RVOL',
                'rsi_period': 14,
                'rvol_period': 20,
                'rsi_weight': 0.5,
                'rvol_weight': 0.5
            },
            {
                'name': 'Conservative_RSI',
                'rsi_period': 20,
                'rvol_period': 30,
                'rsi_weight': 0.6,
                'rvol_weight': 0.4
            }
        ]

        results = []
        liquidity_filter = LiquidityFilter(capital=40_000_000)
        cost_model = ExecutionCostModel()
        scorer = ComprehensiveScorer()

        for config in strategy_configs:
            # Generate signals
            rsi_signals = pd.DataFrame(index=close.index, columns=close.columns)
            rvol_signals = pd.DataFrame(index=close.index, columns=close.columns)

            for stock in close.columns:
                # Convert Series to DataFrame for factor functions
                close_df = pd.DataFrame({stock: close[stock]})
                rsi_result = rsi_factor(close_df, {'rsi_period': config['rsi_period']})
                rsi_signals[stock] = rsi_result['signal'][stock]

                volume_df = pd.DataFrame({stock: volume[stock]})
                rvol_result = rvol_factor(volume_df, {'rvol_period': config['rvol_period']})
                rvol_signals[stock] = rvol_result['signal'][stock]

            # Combine and filter
            combined = rsi_signals * config['rsi_weight'] + rvol_signals * config['rvol_weight']
            filtered = liquidity_filter.apply_filter(combined, dollar_volume)

            # Calculate performance
            returns = close.pct_change()
            strategy_returns = (filtered.shift(1) * returns).mean(axis=1).dropna()

            annual_return = strategy_returns.mean() * 252
            annual_vol = strategy_returns.std() * np.sqrt(252)

            cumulative = (1 + strategy_returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = drawdown.min()

            calmar = abs(annual_return / max_drawdown) if max_drawdown < 0 else 0

            downside_returns = strategy_returns[strategy_returns < 0]
            downside_vol = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else annual_vol
            sortino = annual_return / downside_vol if downside_vol > 0 else 0

            monthly_returns = strategy_returns.resample('ME').sum()

            # Score
            score_result = scorer.compute_score({
                'calmar_ratio': max(calmar, 0),
                'sortino_ratio': max(sortino, 0),
                'monthly_returns': monthly_returns,
                'annual_turnover': 2.0,
                'avg_slippage_bps': 25.0
            })

            results.append({
                'config': config,
                'score': score_result['total_score'],
                'calmar': calmar,
                'sortino': sortino,
                'annual_return': annual_return
            })

        # Rank strategies
        ranked = sorted(results, key=lambda x: x['score'], reverse=True)

        # === VALIDATION ===
        assert len(ranked) == len(strategy_configs), "Should rank all strategies"
        assert ranked[0]['score'] >= ranked[-1]['score'], "Should be sorted descending"

        # All strategies should have valid scores
        for r in ranked:
            assert 0 <= r['score'] <= 1, f"Invalid score: {r['score']}"

        # Log ranking
        print(f"\n=== Strategy Ranking ===")
        for i, r in enumerate(ranked, 1):
            print(f"{i}. {r['config']['name']}: Score={r['score']:.4f}, "
                  f"Calmar={r['calmar']:.2f}, Return={r['annual_return']:.2%}")

    def test_strategy_evolution_workflow(self, mock_market_environment):
        """Test iterative strategy improvement workflow."""
        env = mock_market_environment
        close = env['close']
        volume = env['volume']
        dollar_volume = env['dollar_volume']

        # Simulate 5 generations of strategy evolution
        liquidity_filter = LiquidityFilter(capital=40_000_000)
        scorer = ComprehensiveScorer()

        champion = None
        champion_score = 0
        history = []

        for generation in range(5):
            # Mutate parameters (simulated evolution)
            rsi_period = 14 + np.random.randint(-4, 5)
            rvol_period = 20 + np.random.randint(-5, 6)
            rsi_weight = 0.5 + np.random.uniform(-0.2, 0.2)
            rvol_weight = 1.0 - rsi_weight

            # Generate and evaluate
            rsi_signals = pd.DataFrame(index=close.index, columns=close.columns)
            rvol_signals = pd.DataFrame(index=close.index, columns=close.columns)

            for stock in close.columns[:20]:  # Use subset for speed
                # Convert Series to DataFrame for factor functions
                close_df = pd.DataFrame({stock: close[stock]})
                rsi_result = rsi_factor(close_df, {'rsi_period': max(5, min(30, rsi_period))})
                rsi_signals[stock] = rsi_result['signal'][stock]

                volume_df = pd.DataFrame({stock: volume[stock]})
                rvol_result = rvol_factor(volume_df, {'rvol_period': max(10, min(40, rvol_period))})
                rvol_signals[stock] = rvol_result['signal'][stock]

            combined = rsi_signals * rsi_weight + rvol_signals * rvol_weight
            filtered = liquidity_filter.apply_filter(combined, dollar_volume)

            # Performance
            returns = close.pct_change()
            strategy_returns = (filtered.shift(1) * returns).mean(axis=1).dropna()

            annual_return = strategy_returns.mean() * 252
            monthly_returns = strategy_returns.resample('ME').sum()

            # Quick score estimation
            score_result = scorer.compute_score({
                'calmar_ratio': 1.5,
                'sortino_ratio': 2.0,
                'monthly_returns': monthly_returns,
                'annual_turnover': 2.0,
                'avg_slippage_bps': 25.0
            })

            current_score = score_result['total_score']

            # Update champion
            if current_score > champion_score:
                champion = {
                    'generation': generation,
                    'rsi_period': rsi_period,
                    'rvol_period': rvol_period,
                    'score': current_score
                }
                champion_score = current_score

            history.append({
                'generation': generation,
                'score': current_score,
                'is_champion': current_score == champion_score
            })

        # === VALIDATION ===
        assert champion is not None, "Should have a champion"
        assert len(history) == 5, "Should have 5 generations"
        assert champion_score > 0, "Champion should have positive score"

        # Print evolution history
        print(f"\n=== Evolution History ===")
        for h in history:
            marker = "⭐" if h['is_champion'] else "  "
            print(f"{marker} Gen {h['generation']}: Score={h['score']:.4f}")
        print(f"\nChampion: Gen {champion['generation']}, Score={champion_score:.4f}")


class TestPipelineRobustness:
    """Test pipeline robustness and error handling."""

    def test_handles_missing_data_gracefully(self):
        """Test pipeline handles missing data without crashes."""
        # Create data with NaN values
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        close = pd.DataFrame({
            'test_stock': np.random.randn(100) * 10 + 100
        }, index=dates)
        close.iloc[10:20] = np.nan  # Introduce NaN values

        volume = pd.DataFrame({
            'test_stock': np.random.randint(1_000_000, 10_000_000, 100)
        }, index=dates)

        # Should handle NaN gracefully
        rsi_result = rsi_factor(close, {'rsi_period': 14})
        rvol_result = rvol_factor(volume, {'rvol_period': 20})

        assert 'signal' in rsi_result
        assert 'signal' in rvol_result

    def test_extreme_market_conditions(self):
        """Test pipeline with extreme market volatility."""
        dates = pd.date_range('2024-01-01', periods=100, freq='D')

        # Extreme volatility scenario
        close = pd.DataFrame({
            'test_stock': 100 + np.cumsum(np.random.randn(100) * 20)  # 20% daily moves
        }, index=dates)
        volume = pd.DataFrame({
            'test_stock': np.random.randint(100_000, 100_000_000, 100)  # Huge vol swings
        }, index=dates)

        rsi_result = rsi_factor(close, {'rsi_period': 14})
        rvol_result = rvol_factor(volume, {'rvol_period': 20})

        # Should produce bounded signals
        assert rsi_result['signal'].min().min() >= -1.0
        assert rsi_result['signal'].max().max() <= 1.0
        assert rvol_result['signal'].min().min() >= -1.0
        assert rvol_result['signal'].max().max() <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
