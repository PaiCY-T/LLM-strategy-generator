"""
Momentum + Revenue Catalyst Strategy Template
==============================================

Implements a momentum strategy with revenue acceleration catalyst for stock selection.

Architecture:
-------------
The Momentum template combines price momentum with fundamental catalyst:
- Calculates price momentum using rolling mean of price changes
- Filters for multi-timeframe uptrend confirmation (3 MA filters)
- Requires revenue acceleration as fundamental catalyst
- Selects top N stocks by momentum score
- Monthly rebalancing for fast reaction to market changes

Strategy Characteristics:
------------------------
1. **Momentum Calculation**: Rolling mean of price percentage changes
   - Momentum period: 3-20 days (configurable)
   - Parameter: momentum_period (3, 5, 10, 20)

2. **Trend Confirmation**: Multi-timeframe MA filters ensure sustained uptrend
   - Short MA: 10-30 days (recent trend)
   - Medium MA: 40-80 days (intermediate trend)
   - Long MA: 100-150 days (long-term trend)
   - Parameters: ma_short, ma_medium, ma_long

3. **Revenue Catalyst**: Revenue acceleration filter
   - Requires short-term revenue MA > long-term revenue MA
   - Short: 2-4 months (recent performance)
   - Long: 10-15 months (baseline)
   - Parameters: revenue_short, revenue_long

4. **Portfolio Construction**: Top momentum stocks
   - Portfolio size: 5-20 stocks
   - Parameter: n_stocks

5. **Risk Management**: Stop loss protection
   - Stop loss: 8-15% maximum loss
   - Parameter: stop_loss

6. **Rebalancing**: Monthly rebalancing for fast adaptation
   - Fixed: Monthly ('M') to align with revenue announcements

Position Management:
-------------------
- Portfolio size: n_stocks (5-20 positions) - CONCENTRATED
- Risk controls: stop_loss (8-15%), take_profit (30% fixed)
- Position sizing: position_limit (20% fixed) - MODERATE CONCENTRATION
- Rebalancing: Monthly ('M') - MEDIUM TURNOVER

Performance Targets:
-------------------
- Sharpe Ratio: 0.8-1.5 (respectable risk-adjusted returns with momentum premium)
- Annual Return: 12-25% (higher than factor strategies, momentum premium capture)
- Max Drawdown: -30% to -18% (moderate risk due to concentrated positions)

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Requirement 1.7: Implements momentum + catalyst architecture
"""

from typing import Dict, List, Tuple
from src.templates.base_template import BaseTemplate


class MomentumTemplate(BaseTemplate):
    """
    Momentum + Revenue Catalyst Strategy Template.

    Implements a quantitative momentum strategy that:
    - Calculates price momentum using rolling mean of returns
    - Filters for multi-timeframe uptrend confirmation
    - Requires revenue acceleration as fundamental catalyst
    - Selects top N stocks by momentum score
    - Rebalances monthly for fast reaction to market changes

    The strategy combines technical momentum with fundamental catalyst: only
    stocks showing sustained price momentum AND revenue acceleration are
    selected. This dual-filter approach reduces false momentum signals while
    capturing stocks with both technical and fundamental strength.

    Momentum Strategy Characteristics:
    ----------------------------------
    - **Fast Reaction**: Monthly rebalancing captures momentum shifts quickly
    - **Dual Confirmation**: Price momentum + revenue catalyst reduces false signals
    - **Trend Following**: Multi-timeframe MA filters ensure sustained uptrends
    - **Moderate Concentration**: 5-20 positions balance concentration vs. diversification
    - **Momentum Premium**: Targets momentum factor premium documented in literature

    Attributes:
        name (str): "Momentum" - identifying name for this template
        pattern_type (str): "momentum_catalyst" - describes the momentum + catalyst strategy
        PARAM_GRID (Dict[str, List]): 8-parameter search space with 11,664 combinations
        expected_performance (Dict[str, Tuple[float, float]]): Performance targets
            - sharpe_range: (0.8, 1.5)
            - return_range: (0.12, 0.25)
            - mdd_range: (-0.30, -0.18)
    """

    @property
    def name(self) -> str:
        """
        Return the template name.

        Returns:
            str: "Momentum" - the identifying name for this template
        """
        return "Momentum"

    @property
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: "momentum_catalyst" - describes the momentum + revenue catalyst approach
        """
        return "momentum_catalyst"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 8 tunable parameters with their possible values.
        Total search space: 4 × 3 × 3 × 3 × 3 × 3 × 4 × 3 = 11,664 combinations

        Parameter Categories:
        --------------------
        Momentum Calculation:
            - momentum_period: Rolling period for momentum calculation (4 options)
                3: Very short-term momentum (3-day)
                5: Short-term momentum (5-day, matching example)
                10: Medium-term momentum (10-day)
                20: Longer-term momentum (20-day)

        Trend Confirmation Filters:
            - ma_short: Short-term MA period for recent trend (3 options)
                10: Very recent trend (2 weeks)
                20: Recent trend (1 month, matching example)
                30: Recent trend (1.5 months)

            - ma_medium: Medium-term MA period for intermediate trend (3 options)
                40: Short-medium trend (2 months)
                60: Medium trend (3 months, matching example)
                80: Longer-medium trend (4 months)

            - ma_long: Long-term MA period for sustained trend (3 options)
                100: Long trend (5 months)
                120: Long trend (6 months, matching example)
                150: Very long trend (7.5 months)

        Revenue Catalyst Filters:
            - revenue_short: Short-term revenue MA in months (3 options)
                2: Very recent revenue (2 months)
                3: Recent revenue (3 months, matching example)
                4: Short-term revenue (4 months)

            - revenue_long: Long-term revenue MA in months (3 options)
                10: Long-term baseline (10 months)
                12: Annual baseline (12 months, matching example)
                15: Extended baseline (15 months)

        Portfolio Construction:
            - n_stocks: Number of stocks to select (4 options)
                5: Highly concentrated (top momentum plays)
                10: Concentrated (matching example)
                15: Balanced diversification
                20: Diversified momentum portfolio

        Risk Management:
            - stop_loss: Maximum loss per position (3 options)
                0.08: Tight stop (8% loss limit)
                0.10: Moderate stop (10% loss limit, matching example)
                0.15: Loose stop (15% loss limit)

        Fixed Parameters (not in PARAM_GRID):
            - resample: 'M' (monthly rebalancing, matching example)
            - take_profit: 0.30 (30% target profit)
            - position_limit: 0.20 (20% per stock, moderate concentration)
            - fee_ratio: 1.425/1000/3 (standard Taiwan stock market fee)

        Returns:
            Dict[str, List]: Parameter grid with 8 parameters

        Momentum Strategy Design Rationale:
            - Momentum period: 3-20 days captures short to medium-term momentum
            - MA filters: Multi-timeframe confirmation reduces false signals
            - Revenue catalyst: Fundamental confirmation of business strength
            - Portfolio size: 5-20 stocks balances concentration with diversification
            - Stop loss: 8-15% controls downside risk in momentum reversals
            - Monthly rebalancing: Fast reaction to momentum shifts, aligns with revenue data
        """
        return {
            'momentum_period': [3, 5, 10, 20],
            'ma_short': [10, 20, 30],
            'ma_medium': [40, 60, 80],
            'ma_long': [100, 120, 150],
            'revenue_short': [2, 3, 4],
            'revenue_long': [10, 12, 15],
            'n_stocks': [5, 10, 15, 20],
            'stop_loss': [0.08, 0.10, 0.15]
        }

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These ranges represent realistic targets based on the strategy's
        momentum + catalyst approach. Momentum strategies typically deliver
        higher returns than factor strategies but with higher volatility.

        Performance Targets:
        -------------------
        - Sharpe Ratio: 0.8-1.5 (respectable risk-adjusted returns)
            Higher than Factor (0.8-1.3) due to momentum premium
            Lower than Turtle (1.5-2.5) due to higher volatility
            Similar to upper range of Mastiff (1.2-2.0)

        - Annual Return: 12-25% (higher returns from momentum premium)
            Higher than Factor (10-20%) due to momentum premium capture
            Lower than Turtle (20-35%) due to less stringent filtering
            Similar to Mastiff (15-30%) with concentrated positions

        - Max Drawdown: -30% to -18% (moderate risk profile)
            Worse than Turtle (-25% to -10%) and Factor (-25% to -15%)
            Better than Mastiff (-30% to -15%) in downside protection
            Reflects momentum strategy whipsaw risk during reversals

        Returns:
            Dict[str, Tuple[float, float]]: Performance ranges with keys:
                - 'sharpe_range': (min_sharpe, max_sharpe)
                - 'return_range': (min_return, max_return) as decimals
                - 'mdd_range': (min_drawdown, max_drawdown) as negative decimals

        Note:
            These ranges guide parameter optimization and validate strategy
            effectiveness. Actual performance depends on:
            - Momentum period (shorter = higher turnover and volatility)
            - MA filter settings (stricter = fewer trades, lower drawdowns)
            - Revenue catalyst (stronger = better fundamental backing)
            - Market regime (momentum works best in trending markets)

        Momentum Strategy Performance Characteristics:
            - **Momentum Premium**: Captures well-documented momentum factor returns
            - **Higher Volatility**: Concentrated positions and trend following
            - **Regime Dependency**: Performs best in trending markets, struggles in choppy markets
            - **Fast Adaptation**: Monthly rebalancing captures momentum shifts quickly
            - **Drawdown Risk**: Vulnerable to sudden momentum reversals
        """
        return {
            'sharpe_range': (0.8, 1.5),
            'return_range': (0.12, 0.25),
            'mdd_range': (-0.30, -0.18)
        }

    def _get_cached_data(self, key: str, verbose: bool = False):
        """
        Get cached data using the DataCache singleton.

        This helper method provides convenient access to the shared DataCache
        instance, avoiding redundant data loading operations.

        Args:
            key (str): Data key to retrieve (e.g., 'price:收盤價')
            verbose (bool): If True, prints loading messages. Default: False

        Returns:
            Any: Cached data object (typically DataFrame or Series)

        Raises:
            Exception: If data loading fails (propagated from DataCache)
        """
        from src.templates.data_cache import DataCache
        cache = DataCache.get_instance()
        return cache.get(key, verbose=verbose)

    def _calculate_momentum(self, params: Dict):
        """
        Calculate price momentum using rolling mean of price changes.

        This method computes momentum score as the rolling mean of daily
        percentage price changes over a specified period. Higher momentum
        scores indicate stronger recent price appreciation.

        Args:
            params (Dict): Parameter dictionary containing:
                - momentum_period (int): Rolling period for momentum calculation

        Returns:
            Any: Momentum data object (finlab data structure) containing momentum
                scores for all stocks across time. Positive values indicate
                upward momentum, negative values indicate downward momentum.

        Implementation Details:
            Momentum Calculation Formula:
                1. Calculate daily returns: close / close.shift() - 1
                2. Apply rolling mean: .rolling(momentum_period).mean()
                3. Result: average daily return over the momentum period

            Example (momentum_period=5):
                - Day 1-5 returns: [0.02, 0.01, -0.01, 0.03, 0.02]
                - Momentum score: mean([0.02, 0.01, -0.01, 0.03, 0.02]) = 0.014
                - Interpretation: Stock has averaged 1.4% daily return over 5 days

        Note:
            This momentum calculation matches the example pattern from
            月營收與動能策略選股.py which uses:
            `pct_change = (close / close.shift() - 1).rolling(5).mean()`
        """
        close = self._get_cached_data('price:收盤價')

        # Calculate daily percentage changes
        daily_returns = close / close.shift() - 1

        # Apply rolling mean to smooth momentum signal
        momentum = daily_returns.rolling(params['momentum_period']).mean()

        return momentum

    def _apply_revenue_catalyst(self, params: Dict):
        """
        Apply revenue acceleration catalyst filter.

        This method creates a filter that selects stocks showing revenue
        acceleration: short-term revenue MA must be greater than long-term
        revenue MA, indicating improving business fundamentals.

        Args:
            params (Dict): Parameter dictionary containing:
                - revenue_short (int): Short-term revenue MA period in months
                - revenue_long (int): Long-term revenue MA period in months

        Returns:
            Any: Revenue catalyst condition object (finlab boolean data structure)
                where True indicates revenue acceleration detected

        Implementation Details:
            Revenue Catalyst Logic:
                - Load monthly revenue data: 'monthly_revenue:當月營收'
                - Calculate short-term MA: revenue.average(revenue_short)
                - Calculate long-term MA: revenue.average(revenue_long)
                - Condition: short_ma > long_ma (acceleration)

            Example (revenue_short=3, revenue_long=12):
                - 3-month revenue MA: 500M (recent average)
                - 12-month revenue MA: 450M (baseline)
                - Condition: 500M > 450M → True (revenue accelerating)

        Note:
            This matches the example pattern from 月營收與動能策略選股.py:
            `當月營收.average(3) > 當月營收.average(12)`

            Revenue acceleration indicates:
            - Growing business momentum
            - Improving fundamentals
            - Potential sustained price appreciation
            - Reduced risk of momentum reversal
        """
        revenue = self._get_cached_data('monthly_revenue:當月營收')

        # Calculate short-term and long-term revenue moving averages
        revenue_short_ma = revenue.average(params['revenue_short'])
        revenue_long_ma = revenue.average(params['revenue_long'])

        # Revenue acceleration: short-term > long-term
        revenue_catalyst = revenue_short_ma > revenue_long_ma

        return revenue_catalyst

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete momentum + catalyst strategy workflow:
        1. Validate input parameters against PARAM_GRID
        2. Calculate price momentum using rolling mean of returns
        3. Apply multi-timeframe MA filters for trend confirmation
        4. Apply revenue acceleration catalyst filter
        5. Select top N stocks by momentum score
        6. Execute Finlab backtest with monthly rebalancing
        7. Extract performance metrics and validate against targets

        Args:
            params (Dict): Parameter dictionary with values for all 8 parameters
                defined in PARAM_GRID. Required keys:
                - momentum_period (int): Rolling period for momentum (3, 5, 10, 20)
                - ma_short (int): Short MA period (10, 20, 30)
                - ma_medium (int): Medium MA period (40, 60, 80)
                - ma_long (int): Long MA period (100, 120, 150)
                - revenue_short (int): Short revenue MA (2, 3, 4)
                - revenue_long (int): Long revenue MA (10, 12, 15)
                - n_stocks (int): Portfolio size (5, 10, 15, 20)
                - stop_loss (float): Max loss per position (0.08, 0.10, 0.15)

        Returns:
            Tuple[object, Dict]: A tuple containing:
                - report (object): Finlab backtest report object with complete
                    results including trades, equity curve, and metrics
                - metrics_dict (Dict): Dictionary with extracted metrics:
                    - 'annual_return' (float): Annual return as decimal
                    - 'sharpe_ratio' (float): Sharpe ratio
                    - 'max_drawdown' (float): Max drawdown as negative decimal
                    - 'success' (bool): True if strategy meets all performance
                        targets (Sharpe ≥0.8, Return ≥12%, MDD ≥-30%)

        Raises:
            ValueError: If parameters are invalid or fail validation
            RuntimeError: If strategy generation or backtesting fails
            Exception: If data loading or calculation operations fail

        Performance:
            Target execution time: <30s per strategy generation
            Leverages DataCache to avoid redundant data loading

        Example:
            >>> template = MomentumTemplate()
            >>> params = {
            ...     'momentum_period': 5, 'ma_short': 20, 'ma_medium': 60,
            ...     'ma_long': 120, 'revenue_short': 3, 'revenue_long': 12,
            ...     'n_stocks': 10, 'stop_loss': 0.10
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 1.15
        """
        # Validate parameters before execution (Code Review Issue #4 fix)
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Calculate price momentum
            momentum = self._calculate_momentum(params)

            # Step 2: Load price data for MA filters
            close = self._get_cached_data('price:收盤價')

            # Step 3: Create multi-timeframe MA filters for trend confirmation
            ma_short_filter = close > close.average(params['ma_short'])
            ma_medium_filter = close > close.average(params['ma_medium'])
            ma_long_filter = close > close.average(params['ma_long'])

            # Step 4: Apply revenue acceleration catalyst
            revenue_catalyst = self._apply_revenue_catalyst(params)

            # Step 5: Combine all conditions with AND logic
            # All conditions must be true: all MA filters + revenue catalyst
            all_conditions = (
                ma_short_filter &
                ma_medium_filter &
                ma_long_filter &
                revenue_catalyst
            )

            # Step 6: Select top N stocks by momentum score
            # Filter by conditions, then select highest momentum stocks
            final_selection = momentum[all_conditions].is_largest(params['n_stocks'])

            # Step 7: Execute backtest with monthly rebalancing
            import finlab.backtest as backtest

            # Generate strategy name for identification
            strategy_name = (
                f"Momentum_MP{params['momentum_period']}_"
                f"MA{params['ma_short']}-{params['ma_medium']}-{params['ma_long']}_"
                f"Rev{params['revenue_short']}-{params['revenue_long']}_"
                f"N{params['n_stocks']}_SL{int(params['stop_loss']*100)}"
            )

            # Fixed parameters for momentum strategy
            # Monthly rebalancing aligns with revenue data release schedule
            report = backtest.sim(
                final_selection,
                resample='M',  # Monthly rebalancing (fixed)
                fee_ratio=1.425/1000/3,  # Standard Taiwan stock market fee
                stop_loss=params['stop_loss'],
                take_profit=0.30,  # Fixed 30% target profit
                position_limit=0.20,  # Fixed 20% per stock (moderate concentration)
                name=strategy_name
            )

            # Step 8: Extract metrics from backtest report
            metrics_dict = self._extract_metrics(report)

            # Step 9: Validate metrics against expected performance targets
            metrics_dict['success'] = self._validate_performance(metrics_dict)

            return report, metrics_dict

        except ValueError as e:
            # Re-raise ValueError for parameter validation errors
            raise
        except Exception as e:
            # Wrap other exceptions in RuntimeError with context
            raise RuntimeError(
                f"Strategy generation failed for MomentumTemplate with params {params}: {str(e)}"
            ) from e

    def _extract_metrics(self, report) -> Dict:
        """
        Extract performance metrics from backtest report.

        Args:
            report: Finlab backtest report object

        Returns:
            Dict: Metrics dictionary with keys:
                - 'annual_return' (float): Annual return as decimal
                - 'sharpe_ratio' (float): Sharpe ratio
                - 'max_drawdown' (float): Max drawdown as negative decimal

        Raises:
            AttributeError: If report is missing required metrics
        """
        try:
            # Extract metrics using report.metrics API (consistent with Turtle/Mastiff templates)
            # This is more robust than dictionary access
            metrics = {
                'annual_return': report.metrics.annual_return(),
                'sharpe_ratio': report.metrics.sharpe_ratio(),
                'max_drawdown': report.metrics.max_drawdown()
            }

            return metrics

        except AttributeError as e:
            raise AttributeError(
                f"Failed to extract metrics from backtest report: {str(e)}"
            ) from e

    def _validate_performance(self, metrics: Dict) -> bool:
        """
        Validate strategy performance against expected targets.

        Args:
            metrics (Dict): Metrics dictionary with annual_return, sharpe_ratio, max_drawdown

        Returns:
            bool: True if all metrics meet or exceed targets, False otherwise

        Performance Targets:
            - Sharpe Ratio ≥ 0.8 (lower bound of sharpe_range)
            - Annual Return ≥ 12% (lower bound of return_range)
            - Max Drawdown ≥ -30% (upper bound of mdd_range, less negative)
        """
        expected = self.expected_performance

        # Check if metrics meet minimum thresholds
        sharpe_ok = metrics['sharpe_ratio'] >= expected['sharpe_range'][0]
        return_ok = metrics['annual_return'] >= expected['return_range'][0]
        mdd_ok = metrics['max_drawdown'] >= expected['mdd_range'][0]

        return sharpe_ok and return_ok and mdd_ok
