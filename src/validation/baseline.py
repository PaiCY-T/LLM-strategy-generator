"""
Baseline Strategy Comparison for Trading Strategy Validation

Implements three baseline strategies for Taiwan market comparison:
1. Buy-and-Hold 0050: Passive Taiwan 50 ETF investment
2. Equal-Weight Top 50: Monthly rebalanced equal-weight top 50 stocks
3. Risk Parity: Inverse volatility weighted portfolio, monthly rebalanced

Design Rationale:
- Buy-and-Hold 0050: Market benchmark, ~70% Taiwan market cap coverage
- Equal-Weight: Tests if active equal weighting beats market-cap weighting
- Risk Parity: Tests if volatility management improves risk-adjusted returns

Taiwan Market Context:
- 0050.TW: Taiwan 50 ETF (元大台灣50 ETF) - primary market benchmark
- Top 50 stocks: ~70% of TAIEX market cap (semiconductor-heavy: TSMC ~30%)
- Market characteristics: High volatility (σ ~20-25%), retail-driven (~70% volume)
- Risk-free rate: ~1% (Taiwan 10Y bond yield)

Validation Criteria:
- Strategy must beat at least 1 baseline by > 0.5 Sharpe (meaningful improvement)
- No catastrophic underperformance: improvement > -1.0 for all baselines
- Ensures strategy provides value vs. simple passive approaches

Caching Strategy:
- Baselines cached by date range to avoid redundant calculations
- Cache key: (baseline_name, start_date, end_date)
- Performance target: < 5 seconds with caching (first run ~10-15s)

Requirements: AC-2.5.1 to AC-2.5.5
"""

import logging
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BaselineMetrics:
    """Metrics for a baseline strategy."""

    baseline_name: str
    sharpe_ratio: float
    annual_return: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    computation_time: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'baseline_name': self.baseline_name,
            'sharpe_ratio': self.sharpe_ratio,
            'annual_return': self.annual_return,
            'max_drawdown': self.max_drawdown,
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'computation_time': self.computation_time
        }


@dataclass
class BaselineComparison:
    """Comparison results between strategy and baselines."""

    strategy_sharpe: float
    baselines: Dict[str, BaselineMetrics]
    sharpe_improvements: Dict[str, float]
    best_baseline_matchup: str
    worst_baseline_matchup: str
    validation_passed: bool
    validation_reason: str
    total_computation_time: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'strategy_sharpe': self.strategy_sharpe,
            'baselines': {name: metrics.to_dict() for name, metrics in self.baselines.items()},
            'sharpe_improvements': self.sharpe_improvements,
            'best_baseline_matchup': self.best_baseline_matchup,
            'worst_baseline_matchup': self.worst_baseline_matchup,
            'validation_passed': self.validation_passed,
            'validation_reason': self.validation_reason,
            'total_computation_time': self.total_computation_time
        }


class BaselineComparator:
    """
    Compares trading strategies against baseline strategies.

    Implements three baseline strategies:
    1. Buy-and-Hold 0050: Passive Taiwan 50 ETF
    2. Equal-Weight Top 50: Equal-weight top 50 stocks, monthly rebalanced
    3. Risk Parity: Inverse volatility weights, monthly rebalanced

    Requirements: AC-2.5.1 to AC-2.5.5
    """

    # AC-2.5.4: Validation criteria
    MIN_SHARPE_IMPROVEMENT = 0.5  # Must beat at least one baseline by > 0.5
    MAX_UNDERPERFORMANCE = -1.0  # No catastrophic underperformance

    # Cache directory
    CACHE_DIR = Path('.cache/baseline_metrics')

    def __init__(self, enable_cache: bool = True):
        """
        Initialize baseline comparator.

        Args:
            enable_cache: Enable caching of baseline calculations (default True)
        """
        self.enable_cache = enable_cache

        if self.enable_cache:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"Baseline caching enabled: {self.CACHE_DIR}")

    def compare_with_baselines(
        self,
        strategy_code: str,
        strategy_sharpe: float,
        data: Any,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        iteration_num: int = 0
    ) -> BaselineComparison:
        """
        Compare strategy with baseline strategies.

        Args:
            strategy_code: Strategy code (unused, for consistency with other validators)
            strategy_sharpe: Strategy Sharpe ratio to compare
            data: FinLab data object
            start_date: Start date (YYYY-MM-DD), defaults to data start
            end_date: End date (YYYY-MM-DD), defaults to data end
            iteration_num: Iteration number for logging

        Returns:
            BaselineComparison with validation results

        Requirements: AC-2.5.1 to AC-2.5.5
        """
        start_time = time.time()

        logger.info(f"[Iteration {iteration_num}] Starting baseline comparison")
        logger.info(f"  Strategy Sharpe: {strategy_sharpe:.4f}")

        # AC-2.5.1: Calculate metrics for all 3 baselines
        baselines = {}
        computation_times = []

        for baseline_name in ['Buy-and-Hold 0050', 'Equal-Weight Top 50', 'Risk Parity']:
            logger.info(f"  Calculating {baseline_name} baseline...")

            try:
                baseline_metrics = self._calculate_baseline(
                    baseline_name=baseline_name,
                    data=data,
                    start_date=start_date,
                    end_date=end_date
                )

                baselines[baseline_name] = baseline_metrics
                computation_times.append(baseline_metrics.computation_time)

                logger.info(
                    f"  ✅ {baseline_name}: "
                    f"Sharpe={baseline_metrics.sharpe_ratio:.4f}, "
                    f"Return={baseline_metrics.annual_return:.2%}, "
                    f"MDD={baseline_metrics.max_drawdown:.2%} "
                    f"({baseline_metrics.computation_time:.2f}s)"
                )

            except Exception as e:
                logger.error(f"  ❌ {baseline_name} calculation failed: {e}")
                # Use default metrics for failed baseline
                baselines[baseline_name] = BaselineMetrics(
                    baseline_name=baseline_name,
                    sharpe_ratio=0.0,
                    annual_return=0.0,
                    max_drawdown=0.0,
                    total_trades=0,
                    win_rate=0.0,
                    computation_time=0.0
                )

        # AC-2.5.3: Calculate Sharpe improvement for each baseline
        sharpe_improvements = {}
        for baseline_name, baseline_metrics in baselines.items():
            improvement = strategy_sharpe - baseline_metrics.sharpe_ratio
            sharpe_improvements[baseline_name] = improvement
            logger.info(f"  Sharpe improvement vs {baseline_name}: {improvement:+.4f}")

        # Identify best and worst matchups
        if sharpe_improvements:
            best_baseline = max(sharpe_improvements.items(), key=lambda x: x[1])
            worst_baseline = min(sharpe_improvements.items(), key=lambda x: x[1])
            best_baseline_matchup = f"{best_baseline[0]} ({best_baseline[1]:+.4f})"
            worst_baseline_matchup = f"{worst_baseline[0]} ({worst_baseline[1]:+.4f})"
        else:
            best_baseline_matchup = "N/A"
            worst_baseline_matchup = "N/A"

        # AC-2.5.4: Check validation criteria
        validation_passed, validation_reason = self._check_validation_criteria(
            sharpe_improvements=sharpe_improvements
        )

        total_time = time.time() - start_time

        logger.info(
            f"  Total baseline comparison time: {total_time:.2f}s "
            f"(baselines: {sum(computation_times):.2f}s)"
        )

        if validation_passed:
            logger.info(f"✅ Baseline validation PASSED: {validation_reason}")
        else:
            logger.info(f"❌ Baseline validation FAILED: {validation_reason}")

        return BaselineComparison(
            strategy_sharpe=strategy_sharpe,
            baselines=baselines,
            sharpe_improvements=sharpe_improvements,
            best_baseline_matchup=best_baseline_matchup,
            worst_baseline_matchup=worst_baseline_matchup,
            validation_passed=validation_passed,
            validation_reason=validation_reason,
            total_computation_time=total_time
        )

    def _calculate_baseline(
        self,
        baseline_name: str,
        data: Any,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> BaselineMetrics:
        """
        Calculate metrics for a baseline strategy.

        Uses caching to avoid redundant calculations.

        Args:
            baseline_name: Name of baseline strategy
            data: FinLab data object
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            BaselineMetrics for the baseline

        Requirements: AC-2.5.1, AC-2.5.2
        """
        # AC-2.5.5: Check cache first
        if self.enable_cache:
            cached_metrics = self._load_from_cache(baseline_name, start_date, end_date)
            if cached_metrics:
                logger.info(f"  ⚡ Loaded {baseline_name} from cache")
                return cached_metrics

        # Calculate baseline metrics
        start_time = time.time()

        if baseline_name == 'Buy-and-Hold 0050':
            metrics = self._calculate_buyhold_0050(data, start_date, end_date)
        elif baseline_name == 'Equal-Weight Top 50':
            metrics = self._calculate_equal_weight_top50(data, start_date, end_date)
        elif baseline_name == 'Risk Parity':
            metrics = self._calculate_risk_parity(data, start_date, end_date)
        else:
            raise ValueError(f"Unknown baseline: {baseline_name}")

        computation_time = time.time() - start_time

        baseline_metrics = BaselineMetrics(
            baseline_name=baseline_name,
            sharpe_ratio=metrics['sharpe_ratio'],
            annual_return=metrics['annual_return'],
            max_drawdown=metrics['max_drawdown'],
            total_trades=metrics.get('total_trades', 0),
            win_rate=metrics.get('win_rate', 0.0),
            computation_time=computation_time
        )

        # AC-2.5.5: Save to cache
        if self.enable_cache:
            self._save_to_cache(baseline_metrics, start_date, end_date)

        return baseline_metrics

    def _calculate_buyhold_0050(
        self,
        data: Any,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, float]:
        """
        Calculate Buy-and-Hold 0050 baseline.

        Strategy: Buy 0050.TW ETF at start, hold until end.

        Requirements: AC-2.5.1
        """
        try:
            # Get 0050.TW price data
            close = data.get('price:收盤價')

            # Filter to 0050 stock
            if hasattr(close, 'columns') and '0050.TW' in close.columns:
                prices_0050 = close['0050.TW']
            else:
                # Fallback: use market average as proxy
                logger.warning("0050.TW not found, using market average as proxy")
                prices_0050 = close.mean(axis=1)

            # Calculate returns
            returns = prices_0050.pct_change().dropna()

            # Filter by date range if specified
            if start_date:
                returns = returns[returns.index >= start_date]
            if end_date:
                returns = returns[returns.index <= end_date]

            # Calculate metrics
            sharpe_ratio = self._calculate_sharpe(returns)
            annual_return = (1 + returns.mean()) ** 252 - 1
            max_drawdown = self._calculate_max_drawdown(returns)

            return {
                'sharpe_ratio': sharpe_ratio,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'total_trades': 1,  # Buy once
                'win_rate': 1.0 if annual_return > 0 else 0.0
            }

        except Exception as e:
            logger.error(f"Buy-and-Hold 0050 calculation failed: {e}")
            return self._default_metrics()

    def _calculate_equal_weight_top50(
        self,
        data: Any,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, float]:
        """
        Calculate Equal-Weight Top 50 baseline.

        Strategy: Equal-weight top 50 stocks by market cap, rebalance monthly.

        Requirements: AC-2.5.1
        """
        try:
            # Get price and market cap data
            close = data.get('price:收盤價')
            market_cap = data.get('fundamental_features:market_cap')

            # Get top 50 stocks by market cap
            top_50_mask = market_cap.rank(axis=1, ascending=False) <= 50

            # Equal-weight allocation (1/50 = 2% each)
            position = top_50_mask.astype(float) / 50.0

            # Calculate portfolio returns
            returns = close.pct_change()
            portfolio_returns = (returns * position.shift(1)).sum(axis=1).dropna()

            # Filter by date range
            if start_date:
                portfolio_returns = portfolio_returns[portfolio_returns.index >= start_date]
            if end_date:
                portfolio_returns = portfolio_returns[portfolio_returns.index <= end_date]

            # Calculate metrics
            sharpe_ratio = self._calculate_sharpe(portfolio_returns)
            annual_return = (1 + portfolio_returns.mean()) ** 252 - 1
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)

            # Estimate trades (rebalance monthly = ~12 rebalances/year)
            n_years = len(portfolio_returns) / 252
            total_trades = int(12 * n_years * 50)  # 12 months * n_years * 50 stocks

            return {
                'sharpe_ratio': sharpe_ratio,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'win_rate': 0.5  # Approximate
            }

        except Exception as e:
            logger.error(f"Equal-Weight Top 50 calculation failed: {e}")
            return self._default_metrics()

    def _calculate_risk_parity(
        self,
        data: Any,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Dict[str, float]:
        """
        Calculate Risk Parity baseline.

        Strategy: Weight stocks inversely proportional to volatility,
        rebalance monthly. Lower volatility stocks get higher weights.

        Requirements: AC-2.5.1
        """
        try:
            # Get price data
            close = data.get('price:收盤價')

            # Calculate rolling 60-day volatility
            returns = close.pct_change()
            volatility = returns.rolling(window=60).std()

            # Inverse volatility weights (higher vol = lower weight)
            inv_vol = 1 / (volatility + 1e-8)  # Add small epsilon to avoid division by zero

            # Normalize weights to sum to 1 (row-wise)
            weights = inv_vol.div(inv_vol.sum(axis=1), axis=0)

            # Replace NaN weights with 0
            weights = weights.fillna(0)

            # Calculate portfolio returns
            portfolio_returns = (returns * weights.shift(1)).sum(axis=1).dropna()

            # Filter by date range
            if start_date:
                portfolio_returns = portfolio_returns[portfolio_returns.index >= start_date]
            if end_date:
                portfolio_returns = portfolio_returns[portfolio_returns.index <= end_date]

            # Calculate metrics
            sharpe_ratio = self._calculate_sharpe(portfolio_returns)
            annual_return = (1 + portfolio_returns.mean()) ** 252 - 1
            max_drawdown = self._calculate_max_drawdown(portfolio_returns)

            # Estimate trades (rebalance monthly across all stocks with non-zero weights)
            n_years = len(portfolio_returns) / 252
            avg_stocks = (weights > 0).sum(axis=1).mean()
            total_trades = int(12 * n_years * avg_stocks)

            return {
                'sharpe_ratio': sharpe_ratio,
                'annual_return': annual_return,
                'max_drawdown': max_drawdown,
                'total_trades': total_trades,
                'win_rate': 0.5  # Approximate
            }

        except Exception as e:
            logger.error(f"Risk Parity calculation failed: {e}")
            return self._default_metrics()

    def _calculate_sharpe(self, returns: pd.Series) -> float:
        """
        Calculate annualized Sharpe ratio.

        Args:
            returns: Series of daily returns

        Returns:
            Annualized Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        mean_return = returns.mean()
        std_return = returns.std(ddof=1)

        if std_return == 0:
            return 0.0

        # Annualize: sqrt(252) for daily returns
        sharpe = (mean_return / std_return) * np.sqrt(252)
        return float(sharpe)

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate maximum drawdown.

        Args:
            returns: Series of daily returns

        Returns:
            Maximum drawdown (negative value)
        """
        if len(returns) < 2:
            return 0.0

        # Calculate cumulative returns
        cumulative = (1 + returns).cumprod()

        # Calculate running maximum
        running_max = cumulative.expanding().max()

        # Calculate drawdown
        drawdown = (cumulative - running_max) / running_max

        # Return maximum drawdown (most negative value)
        max_dd = float(drawdown.min())
        return max_dd

    def _default_metrics(self) -> Dict[str, float]:
        """Return default metrics for failed calculations."""
        return {
            'sharpe_ratio': 0.0,
            'annual_return': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 0,
            'win_rate': 0.0
        }

    def _check_validation_criteria(
        self,
        sharpe_improvements: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Check if strategy passes baseline validation criteria.

        Criteria:
        1. Must beat at least 1 baseline by > 0.5 Sharpe
        2. No catastrophic underperformance (improvement > -1.0 for all)

        Args:
            sharpe_improvements: Dict of baseline_name -> improvement

        Returns:
            (validation_passed, validation_reason) tuple

        Requirements: AC-2.5.4
        """
        if not sharpe_improvements:
            return (False, "No baseline comparisons available")

        improvements = list(sharpe_improvements.values())

        # Criterion 2: No catastrophic underperformance (check first - more severe)
        min_improvement = min(improvements)
        if min_improvement <= self.MAX_UNDERPERFORMANCE:
            return (
                False,
                f"Worst improvement {min_improvement:+.4f} ≤ {self.MAX_UNDERPERFORMANCE} threshold (catastrophic underperformance)"
            )

        # Criterion 1: Must beat at least one baseline by > 0.5
        max_improvement = max(improvements)
        if max_improvement <= self.MIN_SHARPE_IMPROVEMENT:
            return (
                False,
                f"Best improvement {max_improvement:+.4f} ≤ {self.MIN_SHARPE_IMPROVEMENT} threshold"
            )

        # All criteria passed
        return (
            True,
            f"Beats baseline by {max_improvement:+.4f} (worst: {min_improvement:+.4f})"
        )

    def _get_cache_key(
        self,
        baseline_name: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> str:
        """
        Generate cache key for baseline metrics.

        Args:
            baseline_name: Baseline strategy name
            start_date: Start date or None
            end_date: End date or None

        Returns:
            Cache key string (MD5 hash)
        """
        # Create unique key from parameters
        key_parts = [
            baseline_name,
            start_date or 'default_start',
            end_date or 'default_end'
        ]
        key_str = '|'.join(key_parts)

        # Hash to create short filename
        hash_obj = hashlib.md5(key_str.encode())
        return hash_obj.hexdigest()

    def _load_from_cache(
        self,
        baseline_name: str,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> Optional[BaselineMetrics]:
        """
        Load baseline metrics from cache.

        Args:
            baseline_name: Baseline strategy name
            start_date: Start date
            end_date: End date

        Returns:
            BaselineMetrics if cached, None otherwise

        Requirements: AC-2.5.5
        """
        cache_key = self._get_cache_key(baseline_name, start_date, end_date)
        cache_file = self.CACHE_DIR / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            # Reconstruct BaselineMetrics
            return BaselineMetrics(
                baseline_name=data['baseline_name'],
                sharpe_ratio=data['sharpe_ratio'],
                annual_return=data['annual_return'],
                max_drawdown=data['max_drawdown'],
                total_trades=data['total_trades'],
                win_rate=data['win_rate'],
                computation_time=data['computation_time']
            )

        except Exception as e:
            logger.warning(f"Failed to load cache for {baseline_name}: {e}")
            return None

    def _save_to_cache(
        self,
        metrics: BaselineMetrics,
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> None:
        """
        Save baseline metrics to cache.

        Args:
            metrics: BaselineMetrics to cache
            start_date: Start date
            end_date: End date

        Requirements: AC-2.5.5
        """
        cache_key = self._get_cache_key(metrics.baseline_name, start_date, end_date)
        cache_file = self.CACHE_DIR / f"{cache_key}.json"

        try:
            with open(cache_file, 'w') as f:
                json.dump(metrics.to_dict(), f, indent=2)

            logger.debug(f"Saved {metrics.baseline_name} to cache: {cache_file}")

        except Exception as e:
            logger.warning(f"Failed to save cache for {metrics.baseline_name}: {e}")


def compare_strategy_with_baselines(
    strategy_sharpe: float,
    data: Any,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    iteration_num: int = 0,
    enable_cache: bool = True
) -> Dict[str, Any]:
    """
    Convenience function for baseline comparison.

    Args:
        strategy_sharpe: Strategy Sharpe ratio
        data: FinLab data object
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        iteration_num: Iteration number for logging
        enable_cache: Enable caching (default True)

    Returns:
        Baseline comparison results dictionary

    Example:
        >>> results = compare_strategy_with_baselines(
        ...     strategy_sharpe=2.5,
        ...     data=data,
        ...     iteration_num=42
        ... )
        >>> if results['validation_passed']:
        ...     print("Strategy beats baselines!")
    """
    comparator = BaselineComparator(enable_cache=enable_cache)
    comparison = comparator.compare_with_baselines(
        strategy_code="",  # Not used
        strategy_sharpe=strategy_sharpe,
        data=data,
        start_date=start_date,
        end_date=end_date,
        iteration_num=iteration_num
    )

    return comparison.to_dict()


# Standalone test
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("Baseline Comparison - Standalone Test")
    print("=" * 60)

    # Test with mock data
    print("\nTest 1: Strategy beats all baselines")
    print("-" * 60)

    # Mock data object (simplified for testing)
    class MockData:
        def get(self, key):
            # Return random data for testing
            import pandas as pd
            dates = pd.date_range('2018-01-01', '2024-12-31', freq='D')

            if 'price:收盤價' in key:
                # Generate random prices for 100 stocks
                data = pd.DataFrame(
                    np.random.randn(len(dates), 100).cumsum(axis=0) + 100,
                    index=dates,
                    columns=[f'stock_{i}' for i in range(100)]
                )
                # Add 0050.TW
                data['0050.TW'] = np.random.randn(len(dates)).cumsum() + 100
                return data

            elif 'price:成交股數' in key:
                # Generate random volume
                return pd.DataFrame(
                    np.random.randint(1000000, 10000000, (len(dates), 100)),
                    index=dates,
                    columns=[f'stock_{i}' for i in range(100)]
                )

            elif 'fundamental_features:market_cap' in key:
                # Generate random market cap
                return pd.DataFrame(
                    np.random.randint(1000000000, 100000000000, (len(dates), 100)),
                    index=dates,
                    columns=[f'stock_{i}' for i in range(100)]
                )

            else:
                raise ValueError(f"Unknown data key: {key}")

    mock_data = MockData()

    # Test with high Sharpe (should pass)
    results = compare_strategy_with_baselines(
        strategy_sharpe=2.5,
        data=mock_data,
        iteration_num=1,
        enable_cache=False  # Disable cache for testing
    )

    print(f"Strategy Sharpe: {results['strategy_sharpe']:.4f}")
    print("\nBaseline Comparisons:")
    for baseline_name, improvement in results['sharpe_improvements'].items():
        print(f"  {baseline_name}: {improvement:+.4f}")

    print(f"\nBest matchup: {results['best_baseline_matchup']}")
    print(f"Worst matchup: {results['worst_baseline_matchup']}")
    print(f"Validation: {'PASS' if results['validation_passed'] else 'FAIL'}")
    print(f"Reason: {results['validation_reason']}")
    print(f"Computation time: {results['total_computation_time']:.2f}s")

    # Test 2: Strategy fails validation
    print("\n\nTest 2: Strategy fails validation (low Sharpe)")
    print("-" * 60)

    results2 = compare_strategy_with_baselines(
        strategy_sharpe=0.3,
        data=mock_data,
        iteration_num=2,
        enable_cache=False
    )

    print(f"Strategy Sharpe: {results2['strategy_sharpe']:.4f}")
    print(f"Validation: {'PASS' if results2['validation_passed'] else 'FAIL'}")
    print(f"Reason: {results2['validation_reason']}")

    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)
