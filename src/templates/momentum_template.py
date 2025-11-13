"""
Momentum + Catalyst Strategy Template
======================================

Implements a momentum strategy with fundamental catalyst (revenue or earnings) for stock selection.

Architecture:
-------------
The Momentum template combines price momentum with fundamental catalyst:
- Calculates price momentum using rolling returns
- Filters for moving average trend confirmation
- Requires revenue OR earnings catalyst as fundamental confirmation
- Selects top N stocks by momentum score
- Weekly or monthly rebalancing for fast reaction to market changes

Strategy Characteristics:
------------------------
1. **Momentum Calculation**: Rolling price momentum
   - Momentum window: 5-30 days lookback period
   - Parameter: momentum_period (5, 10, 20, 30)

2. **Trend Confirmation**: Single moving average filter
   - MA period: 20-120 days for trend confirmation
   - Parameter: ma_periods (20, 60, 90, 120)

3. **Catalyst Type**: Choose fundamental catalyst
   - Revenue: Revenue acceleration (short-term > long-term MA)
   - Earnings: Earnings momentum (ROE improvement)
   - Parameter: catalyst_type ('revenue', 'earnings')

4. **Catalyst Detection**: Lookback window for catalyst
   - Lookback: 2-6 months for catalyst detection
   - Parameter: catalyst_lookback (2, 3, 4, 6)

5. **Portfolio Construction**: Top momentum stocks
   - Portfolio size: 5-20 stocks
   - Parameter: n_stocks (5, 10, 15, 20)

6. **Risk Management**: Stop loss protection
   - Stop loss: 8-15% maximum loss
   - Parameter: stop_loss (0.08, 0.10, 0.12, 0.15)

7. **Rebalancing**: Configurable frequency
   - Frequency: Weekly or monthly rebalancing
   - Parameter: resample ('W', 'M')

8. **Rebalancing Offset**: Day offset for rebalancing
   - Offset: 0-4 days offset for weekly rebalancing
   - Parameter: resample_offset (0, 1, 2, 3, 4)

Position Management:
-------------------
- Portfolio size: n_stocks (5-20 positions) - MODERATE TO CONCENTRATED
- Risk controls: stop_loss (8-15%), take_profit (30% fixed)
- Position sizing: position_limit (20% fixed) - MODERATE CONCENTRATION
- Rebalancing: resample ('W' or 'M') with offset - FLEXIBLE TURNOVER

Performance Targets:
-------------------
- Sharpe Ratio: 0.8-1.5 (respectable risk-adjusted returns with momentum premium)
- Annual Return: 12-25% (higher than factor strategies, momentum premium capture)
- Max Drawdown: -30% to -18% (moderate risk due to momentum strategy nature)

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.2: 8-parameter PARAM_GRID (momentum_period, ma_periods, catalyst_type,
                   catalyst_lookback, n_stocks, stop_loss, resample, resample_offset)
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Requirement 1.7: Implements momentum + catalyst architecture
"""

from typing import Dict, List, Tuple
from src.templates.base_template import BaseTemplate


class MomentumTemplate(BaseTemplate):
    """
    Momentum + Catalyst Strategy Template.

    Implements a quantitative momentum strategy that:
    - Calculates price momentum using rolling returns
    - Filters for moving average trend confirmation
    - Requires revenue OR earnings catalyst as fundamental confirmation
    - Selects top N stocks by momentum score
    - Rebalances weekly or monthly with configurable offset for fast reaction

    The strategy combines technical momentum with fundamental catalyst: only
    stocks showing sustained price momentum AND fundamental catalyst are
    selected. This dual-filter approach reduces false momentum signals while
    capturing stocks with both technical and fundamental strength.

    Momentum Strategy Characteristics:
    ----------------------------------
    - **Fast Reaction**: Weekly/monthly rebalancing captures momentum shifts quickly
    - **Dual Confirmation**: Price momentum + fundamental catalyst reduces false signals
    - **Flexible Catalyst**: Choose between revenue or earnings catalyst
    - **Trend Following**: MA filter ensures sustained uptrends
    - **Moderate Concentration**: 5-20 positions balance concentration vs. diversification
    - **Momentum Premium**: Targets momentum factor premium documented in literature

    Attributes:
        name (str): "Momentum" - identifying name for this template
        pattern_type (str): "momentum_catalyst" - describes the momentum + catalyst strategy
        PARAM_GRID (Dict[str, List]): 8-parameter search space with 3,072 combinations
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
            str: "momentum_catalyst" - describes the momentum + catalyst approach
        """
        return "momentum_catalyst"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 8 tunable parameters with their possible values.
        Total search space: 4 × 4 × 2 × 4 × 4 × 4 × 2 × 5 = 10,240 combinations

        Parameter Categories:
        --------------------
        Momentum Calculation:
            - momentum_period: Lookback period for momentum calculation (4 options)
                5: Very short-term momentum (1 week)
                10: Short-term momentum (2 weeks)
                20: Medium-term momentum (1 month)
                30: Longer-term momentum (1.5 months)

        Trend Confirmation:
            - ma_periods: Moving average period for trend filter (4 options)
                20: Short-term trend (1 month)
                60: Medium-term trend (3 months)
                90: Long-term trend (4.5 months)
                120: Very long-term trend (6 months)

        Catalyst Selection:
            - catalyst_type: Type of fundamental catalyst (2 options)
                'revenue': Revenue acceleration catalyst
                'earnings': Earnings momentum catalyst (ROE)

        Catalyst Detection:
            - catalyst_lookback: Lookback window for catalyst detection (4 options)
                2: Very recent catalyst (2 months)
                3: Recent catalyst (3 months)
                4: Short-term catalyst (4 months)
                6: Medium-term catalyst (6 months)

        Portfolio Construction:
            - n_stocks: Number of stocks to select (4 options)
                5: Highly concentrated (top momentum plays)
                10: Concentrated portfolio
                15: Balanced diversification
                20: Diversified momentum portfolio

        Risk Management:
            - stop_loss: Maximum loss per position (4 options)
                0.08: Tight stop (8% loss limit)
                0.10: Moderate stop (10% loss limit)
                0.12: Moderate-loose stop (12% loss limit)
                0.15: Loose stop (15% loss limit)

        Rebalancing Frequency:
            - resample: Rebalancing frequency (2 options)
                'W': Weekly rebalancing (higher turnover, faster reaction)
                'M': Monthly rebalancing (lower turnover, reduced costs)

        Rebalancing Timing:
            - resample_offset: Day offset for rebalancing (5 options)
                0: Monday (for weekly) or 1st (for monthly)
                1: Tuesday (for weekly) or offset by 1 day
                2: Wednesday (for weekly) or offset by 2 days
                3: Thursday (for weekly) or offset by 3 days
                4: Friday (for weekly) or offset by 4 days

        Fixed Parameters (not in PARAM_GRID):
            - take_profit: 0.30 (30% target profit)
            - position_limit: 0.20 (20% per stock, moderate concentration)
            - fee_ratio: 1.425/1000/3 (standard Taiwan stock market fee)

        Returns:
            Dict[str, List]: Parameter grid with 8 parameters

        Momentum Strategy Design Rationale:
            - Momentum window: 5-30 days captures short to medium-term momentum
            - MA periods: 20-120 days provides single trend confirmation
            - Catalyst type: Flexibility to choose revenue or earnings catalyst
            - Catalyst lookback: 2-6 months aligns with reporting frequency
            - Portfolio size: 5-20 stocks balances concentration with diversification
            - Stop loss: 8-15% controls downside risk in momentum reversals
            - Resample: Weekly/monthly balances reaction speed vs. transaction costs
            - Offset: Timing flexibility to avoid crowded rebalancing dates
        """
        return {
            'momentum_period': [5, 10, 20, 30],
            'ma_periods': [20, 60, 90, 120],
            'catalyst_type': ['revenue', 'earnings'],
            'catalyst_lookback': [2, 3, 4, 6],
            'n_stocks': [5, 10, 15, 20],
            'stop_loss': [0.08, 0.10, 0.12, 0.15],
            'resample': ['W', 'M'],
            'resample_offset': [0, 1, 2, 3, 4]
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
            - Momentum window (shorter = higher turnover and volatility)
            - MA filter settings (stricter = fewer trades, lower drawdowns)
            - Catalyst choice (revenue vs. earnings different cycle timing)
            - Rebalancing frequency (weekly = higher costs, monthly = lower costs)
            - Market regime (momentum works best in trending markets)

        Momentum Strategy Performance Characteristics:
            - **Momentum Premium**: Captures well-documented momentum factor returns
            - **Higher Volatility**: Concentrated positions and trend following
            - **Regime Dependency**: Performs best in trending markets, struggles in choppy markets
            - **Fast Adaptation**: Weekly/monthly rebalancing captures momentum shifts quickly
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
        Calculate price momentum using rolling returns.

        This method computes momentum score as the rolling mean of daily
        percentage price changes over a specified lookback window. Higher
        momentum scores indicate stronger recent price appreciation.

        Args:
            params (Dict): Parameter dictionary containing:
                - momentum_period (int): Lookback period for momentum calculation

        Returns:
            Any: Momentum data object (finlab data structure) containing momentum
                scores for all stocks across time. Positive values indicate
                upward momentum, negative values indicate downward momentum.

        Implementation Details:
            Momentum Calculation Formula:
                1. Calculate daily returns: close / close.shift() - 1
                2. Apply rolling mean: .rolling(momentum_period).mean()
                3. Result: average daily return over the momentum window

            Example (momentum_period=5):
                - Day 1-5 returns: [0.02, 0.01, -0.01, 0.03, 0.02]
                - Momentum score: mean([0.02, 0.01, -0.01, 0.03, 0.02]) = 0.014
                - Interpretation: Stock has averaged 1.4% daily return over 5 days

        Note:
            This momentum calculation uses a simple rolling mean of returns,
            which is a standard approach in momentum literature. Alternative
            formulations could use total returns, risk-adjusted returns, or
            other momentum measures.
        """
        close = self._get_cached_data('etl:adj_close')  # ✅ Adjusted for dividends/splits

        # Calculate daily percentage changes
        daily_returns = close / close.shift() - 1

        # Apply rolling mean to calculate momentum score
        momentum = daily_returns.rolling(params['momentum_period']).mean()

        return momentum

    def _apply_revenue_catalyst(self, params: Dict):
        """
        Apply revenue acceleration catalyst filter.

        This method creates a filter that selects stocks showing revenue
        acceleration: short-term revenue MA must be greater than long-term
        revenue MA (baseline), indicating improving business fundamentals.

        Args:
            params (Dict): Parameter dictionary containing:
                - catalyst_lookback (int): Lookback window for short-term MA in months

        Returns:
            Any: Revenue catalyst condition object (finlab boolean data structure)
                where True indicates revenue acceleration detected

        Implementation Details:
            Revenue Catalyst Logic:
                - Load monthly revenue data: 'monthly_revenue:當月營收'
                - Calculate short-term MA: revenue.average(catalyst_lookback)
                - Calculate long-term MA: revenue.average(12) as baseline
                - Condition: short_ma > long_ma (acceleration)

            Example (catalyst_lookback=3):
                - 3-month revenue MA: 500M (recent average)
                - 12-month revenue MA: 450M (annual baseline)
                - Condition: 500M > 450M → True (revenue accelerating)

        Note:
            Revenue acceleration indicates:
            - Growing business momentum
            - Improving fundamentals
            - Potential sustained price appreciation
            - Reduced risk of momentum reversal

            The 12-month baseline is fixed as it represents annual revenue
            performance, while the short-term window is configurable via
            catalyst_lookback to detect acceleration at different timescales.
        """
        revenue = self._get_cached_data('monthly_revenue:當月營收')

        # Calculate short-term and long-term revenue moving averages
        # Short-term uses catalyst_lookback parameter
        # Long-term fixed at 12 months (annual baseline)
        revenue_short_ma = revenue.average(params['catalyst_lookback'])
        revenue_long_ma = revenue.average(12)

        # Revenue acceleration: short-term > long-term
        revenue_catalyst = revenue_short_ma > revenue_long_ma

        return revenue_catalyst

    def _apply_earnings_catalyst(self, params: Dict):
        """
        Apply earnings momentum catalyst filter using ROE.

        This method creates a filter that selects stocks showing earnings
        momentum: current ROE must be improving compared to historical baseline,
        indicating improving profitability and capital efficiency.

        Args:
            params (Dict): Parameter dictionary containing:
                - catalyst_lookback (int): Lookback window for ROE comparison in months

        Returns:
            Any: Earnings catalyst condition object (finlab boolean data structure)
                where True indicates earnings momentum detected

        Implementation Details:
            Earnings Catalyst Logic:
                - Load ROE data: 'fundamental_features:ROE綜合損益'
                - Calculate short-term ROE MA: roe.average(catalyst_lookback)
                - Calculate long-term ROE MA: roe.average(8) as baseline
                - Condition: short_ma > long_ma (improving)

            Example (catalyst_lookback=3):
                - 3-quarter ROE MA: 15% (recent profitability)
                - 8-quarter ROE MA: 12% (2-year baseline)
                - Condition: 15% > 12% → True (earnings improving)

        Note:
            Earnings momentum (ROE improvement) indicates:
            - Improving profitability
            - Better capital efficiency
            - Strong fundamental support for price momentum
            - Lower risk of earnings disappointment

            The 8-quarter baseline represents 2 years of earnings history,
            while the short-term window uses catalyst_lookback to detect
            improvements at different timescales.
        """
        roe = self._get_cached_data('fundamental_features:ROE綜合損益')

        # Calculate short-term and long-term ROE moving averages
        # Short-term uses catalyst_lookback parameter
        # Long-term fixed at 8 quarters (2-year baseline)
        roe_short_ma = roe.average(params['catalyst_lookback'])
        roe_long_ma = roe.average(8)

        # Earnings momentum: short-term ROE > long-term ROE
        earnings_catalyst = roe_short_ma > roe_long_ma

        return earnings_catalyst

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete momentum + catalyst strategy workflow:
        1. Validate input parameters against PARAM_GRID
        2. Calculate price momentum using rolling returns
        3. Apply moving average filter for trend confirmation
        4. Apply revenue OR earnings catalyst filter based on catalyst_type
        5. Select top N stocks by momentum score
        6. Execute Finlab backtest with weekly/monthly rebalancing and offset
        7. Extract performance metrics and validate against targets

        Args:
            params (Dict): Parameter dictionary with values for all 8 parameters
                defined in PARAM_GRID. Required keys:
                - momentum_period (int): Lookback period for momentum (5, 10, 20, 30)
                - ma_periods (int): MA period for trend filter (20, 60, 90, 120)
                - catalyst_type (str): Catalyst type ('revenue', 'earnings')
                - catalyst_lookback (int): Catalyst detection window (2, 3, 4, 6)
                - n_stocks (int): Portfolio size (5, 10, 15, 20)
                - stop_loss (float): Max loss per position (0.08, 0.10, 0.12, 0.15)
                - resample (str): Rebalancing frequency ('W' or 'M')
                - resample_offset (int): Rebalancing offset days (0, 1, 2, 3, 4)

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
            ...     'momentum_period': 10, 'ma_periods': 60, 'catalyst_type': 'revenue',
            ...     'catalyst_lookback': 3, 'n_stocks': 10, 'stop_loss': 0.10,
            ...     'resample': 'M', 'resample_offset': 0
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 1.15
        """
        # Validate parameters before execution
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Calculate price momentum
            momentum = self._calculate_momentum(params)

            # Step 2: Load price data and create MA filter for trend confirmation
            close = self._get_cached_data('etl:adj_close')  # ✅ Adjusted for dividends/splits
            ma_filter = close > close.average(params['ma_periods'])

            # Step 3: Apply catalyst filter based on catalyst_type
            if params['catalyst_type'] == 'revenue':
                catalyst = self._apply_revenue_catalyst(params)
            elif params['catalyst_type'] == 'earnings':
                catalyst = self._apply_earnings_catalyst(params)
            else:
                raise ValueError(
                    f"Invalid catalyst_type '{params['catalyst_type']}'. "
                    f"Must be 'revenue' or 'earnings'"
                )

            # Step 4: Combine all conditions with AND logic
            # Both MA filter and catalyst must be true
            all_conditions = ma_filter & catalyst

            # Step 5: Select top N stocks by momentum score
            # Filter by conditions, then select highest momentum stocks
            final_selection = momentum[all_conditions].is_largest(params['n_stocks'])

            # Step 6: Execute backtest with configurable rebalancing
            import finlab.backtest as backtest

            # Generate strategy name for identification
            strategy_name = (
                f"Momentum_MW{params['momentum_period']}_MA{params['ma_periods']}_"
                f"{params['catalyst_type'][:3]}{params['catalyst_lookback']}_"
                f"N{params['n_stocks']}_SL{int(params['stop_loss']*100)}_"
                f"{params['resample']}{params['resample_offset']}"
            )

            # Build resample string with offset if needed
            # For weekly: 'W', 'W-TUE', 'W-WED', 'W-THU', 'W-FRI'
            # For monthly: 'M', 'MS+1D', 'MS+2D', 'MS+3D', 'MS+4D'
            if params['resample'] == 'W':
                if params['resample_offset'] == 0:
                    resample_str = 'W-MON'
                elif params['resample_offset'] == 1:
                    resample_str = 'W-TUE'
                elif params['resample_offset'] == 2:
                    resample_str = 'W-WED'
                elif params['resample_offset'] == 3:
                    resample_str = 'W-THU'
                else:  # 4
                    resample_str = 'W-FRI'
            else:  # 'M'
                if params['resample_offset'] == 0:
                    resample_str = 'M'
                else:
                    # For monthly with offset, we use month start plus offset days
                    resample_str = f"MS+{params['resample_offset']}"

            # Fixed parameters for momentum strategy
            report = backtest.sim(
                final_selection,
                resample=resample_str,  # Weekly or monthly with offset
                fee_ratio=1.425/1000/3,  # Standard Taiwan stock market fee
                stop_loss=params['stop_loss'],
                take_profit=0.30,  # Fixed 30% target profit
                position_limit=0.20,  # Fixed 20% per stock (moderate concentration)
                upload=False,  # Disable upload for sandbox testing
                name=strategy_name
            )

            # Step 7: Extract metrics from backtest report
            metrics_dict = self._extract_metrics(report)

            # Step 8: Validate metrics against expected performance targets
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
            # Extract metrics using report.metrics API (consistent with other templates)
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
