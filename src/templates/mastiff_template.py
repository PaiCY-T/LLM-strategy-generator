"""
Mastiff Strategy Template
=========================

Implements the Contrarian Reversal Mastiff Strategy.

Architecture:
-------------
The Mastiff template implements a contrarian reversal strategy that buys
underperforming stocks with low trading volume, expecting mean reversion.
This approach is contrarian to popular momentum strategies that buy winners.

Strategy Characteristics:
------------------------
1. **Price Reversal**: Targets stocks that have dropped significantly from recent highs
   - Identifies stocks at potential reversal points
   - Parameter: price_drop_threshold (-5% to -15%)

2. **Low Volume Selection**: Focuses on neglected stocks with low trading activity
   - Uses volume percentile to find under-the-radar opportunities
   - Parameters: low_volume_days (5-20), volume_percentile (10-30)

3. **Revenue Quality**: Ensures fundamental quality despite price weakness
   - Filters by revenue growth to avoid value traps
   - Parameter: revenue_growth_min (-5% to 5%)

4. **Valuation Filter**: Selects reasonably valued stocks
   - Uses P/E ratio as a valuation screen
   - Parameter: pe_max (15-25)

Position Management:
-------------------
- Portfolio size: n_stocks (3-10 positions) - CONCENTRATED
- Risk controls: stop_loss (10-20%), take_profit (30-80%)
- Position sizing: position_limit (15-30% per stock) - HIGH CONCENTRATION
- Rebalancing: resample ('M' monthly or 'W-FRI' weekly)

Performance Targets:
-------------------
- Sharpe Ratio: 1.2-2.0 (respectable risk-adjusted returns)
- Annual Return: 15-30% (solid growth from contrarian plays)
- Max Drawdown: -30% to -15% (higher volatility expected)

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Requirement 1.5: Implements contrarian reversal architecture
"""

from typing import Dict, List, Tuple
from src.templates.base_template import BaseTemplate


class MastiffTemplate(BaseTemplate):
    """
    Contrarian Reversal Mastiff Strategy Template.

    Implements a contrarian reversal strategy that identifies:
    - Underperforming stocks with recent price drops
    - Low volume (neglected) stocks under the radar
    - Fundamental quality (revenue growth, reasonable valuation)
    - Mean reversion opportunities

    The strategy uses contrarian logic: buys stocks that others are ignoring
    or selling, expecting mean reversion and recovery. This approach aims for
    high-conviction concentrated positions with asymmetric upside potential.

    Attributes:
        name (str): "Mastiff" - identifying name for this template
        pattern_type (str): "contrarian_reversal" - describes the contrarian strategy
        PARAM_GRID (Dict[str, List]): 10-parameter search space with 1,555,200 combinations
        expected_performance (Dict[str, Tuple[float, float]]): Performance targets
            - sharpe_range: (1.2, 2.0)
            - return_range: (0.15, 0.30)
            - mdd_range: (-0.30, -0.15)
    """

    @property
    def name(self) -> str:
        """
        Return the template name.

        Returns:
            str: "Mastiff" - the identifying name for this template
        """
        return "Mastiff"

    @property
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: "contrarian_reversal" - describes the contrarian approach
        """
        return "contrarian_reversal"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 10 tunable parameters with their possible values.
        Total search space: 3 * 3 * 3 * 3 * 3 * 4 * 3 * 3 * 4 * 2
        = 1,555,200 combinations

        Parameter Categories:
        --------------------
        Reversal Detection:
            - low_volume_days: Days for volume comparison (5, 10, 20)
            - volume_percentile: Low volume threshold (10, 20, 30)
            - price_drop_threshold: Minimum price drop signal (-0.05, -0.10, -0.15)

        Fundamental Quality:
            - pe_max: Maximum P/E ratio filter (15, 20, 25)
            - revenue_growth_min: Minimum revenue growth (-5, 0, 5)

        Position Management:
            - n_stocks: Portfolio size - CONCENTRATED (3, 5, 8, 10)
            - stop_loss: Maximum loss per position (0.10, 0.15, 0.20)
            - take_profit: Target profit per position (0.30, 0.50, 0.80)
            - position_limit: Max position size - HIGH CONCENTRATION (0.15, 0.20, 0.25, 0.30)
            - resample: Rebalancing frequency ('M' monthly, 'W-FRI' weekly)

        Returns:
            Dict[str, List]: Parameter grid with 10 parameters

        Source:
            Leveraged from example/藏獒.py (contrarian low-volume strategy)
        """
        return {
            'low_volume_days': [5, 10, 20],
            'volume_percentile': [10, 20, 30],
            'price_drop_threshold': [-0.05, -0.10, -0.15],
            'pe_max': [15, 20, 25],
            'revenue_growth_min': [-5, 0, 5],
            'n_stocks': [3, 5, 8, 10],
            'stop_loss': [0.10, 0.15, 0.20],
            'take_profit': [0.30, 0.50, 0.80],
            'position_limit': [0.15, 0.20, 0.25, 0.30],
            'resample': ['M', 'W-FRI']
        }

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These ranges represent realistic targets based on the strategy's
        contrarian reversal approach. The strategy prioritizes asymmetric
        upside opportunities with higher volatility than Turtle strategy.

        Performance Targets:
        -------------------
        - Sharpe Ratio: 1.2-2.0 (respectable risk-adjusted returns)
        - Annual Return: 15-30% (solid contrarian gains)
        - Max Drawdown: -30% to -15% (higher volatility from concentrated positions)

        Returns:
            Dict[str, Tuple[float, float]]: Performance ranges with keys:
                - 'sharpe_range': (min_sharpe, max_sharpe)
                - 'return_range': (min_return, max_return) as decimals
                - 'mdd_range': (min_drawdown, max_drawdown) as negative decimals

        Note:
            These ranges guide parameter optimization and validate strategy
            effectiveness. Actual performance depends on market conditions
            and parameter selection. Contrarian strategies may experience
            higher volatility than momentum strategies.
        """
        return {
            'sharpe_range': (1.2, 2.0),
            'return_range': (0.15, 0.30),
            'mdd_range': (-0.30, -0.15)
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

    def _create_contrarian_conditions(self, params: Dict):
        """
        Create 6 contrarian reversal conditions for stock selection.

        Implements the contrarian reversal strategy that combines:
        - Condition 1: Price High Filter (近期股價創高)
        - Condition 2: Revenue Decline Filter (營收衰退過濾)
        - Condition 3: Revenue Growth Filter (營收成長篩選)
        - Condition 4: Revenue Bottom Detection (營收觸底)
        - Condition 5: Momentum Filter (動能篩選)
        - Condition 6: Liquidity Constraints (流動性篩選)

        All conditions are combined with AND logic: stocks must pass ALL 6 conditions
        to be included in the portfolio.

        Args:
            params (Dict): Parameter dictionary containing:
                - low_volume_days (int): Days for volume comparison (5-20 days)
                - volume_percentile (int): Low volume threshold (10-30 percentile)
                - price_drop_threshold (float): Min price drop from high (-0.05 to -0.15)
                - pe_max (int): Maximum P/E ratio filter (15-25)
                - revenue_growth_min (int): Min revenue growth threshold (-5 to 5%)

        Returns:
            Any: Combined condition object (finlab data structure) representing
                stocks that pass all 6 contrarian filtering conditions

        Source:
            Leveraged from example/藏獒.py:11-27 (contrarian reversal logic)

        Implementation Details:
            Condition 1 - Price High Filter:
                Identifies stocks creating 250-day (1-year) price highs
                Uses: 'price:收盤價' with rolling max comparison

            Condition 2 - Revenue Decline Filter:
                Excludes stocks with 3+ consecutive months of >10% YoY revenue decline
                Uses: 'monthly_revenue:去年同月增減(%)' with sustain logic

            Condition 3 - Revenue Growth Filter:
                Excludes stocks with excessive growth (8+ months of >60% YoY growth in 12 months)
                Prevents catching overheated growth stocks
                Uses: 'monthly_revenue:去年同月增減(%)' with sustain logic

            Condition 4 - Revenue Bottom Detection:
                Confirms revenue bottoming: 3 consecutive months where
                (12-month min revenue / current revenue) < 0.8
                Uses: 'monthly_revenue:當月營收' with rolling min comparison

            Condition 5 - Momentum Filter:
                Requires 3 consecutive months of MoM revenue growth > -40%
                Ensures momentum is not too negative
                Uses: 'monthly_revenue:上月比較增減(%)'

            Condition 6 - Liquidity:
                10-day average volume must exceed 200k shares for adequate liquidity
                Uses: 'price:成交股數' with average calculation
        """
        # Load all required datasets using DataCache
        close = self._get_cached_data('price:收盤價')
        vol = self._get_cached_data('price:成交股數')
        rev = self._get_cached_data('monthly_revenue:當月營收')
        rev_year_growth = self._get_cached_data('monthly_revenue:去年同月增減(%)')
        rev_month_growth = self._get_cached_data('monthly_revenue:上月比較增減(%)')

        # Calculate volume moving average (10-day)
        vol_ma = vol.average(10)

        # Condition 1: Price High Filter (股價創年新高)
        # Stock price equals its 250-day (1-year) rolling maximum
        cond1 = (close == close.rolling(250).max())

        # Condition 2: Revenue Decline Filter (排除月營收連3月衰退10%以上)
        # Exclude stocks with 3+ consecutive months of >10% YoY revenue decline
        # The ~ operator negates the condition to filter OUT declining stocks
        cond2 = ~(rev_year_growth < -10).sustain(3)

        # Condition 3: Revenue Growth Filter (排除月營收成長趨勢過老)
        # Exclude stocks with excessive growth trend (8+ months of >60% YoY growth in 12 months)
        # This prevents catching overheated or maturing growth stocks
        cond3 = ~(rev_year_growth > 60).sustain(12, 8)

        # Condition 4: Revenue Bottom Detection (確認營收底部)
        # Confirms revenue is recovering from bottom:
        # 3 consecutive months where (12-month min / current) < 0.8
        # Indicates current revenue is >25% above recent lows
        cond4 = ((rev.rolling(12).min()) / (rev) < 0.8).sustain(3)

        # Condition 5: Momentum Filter (單月營收月增率連續3月大於-40%)
        # Requires 3 consecutive months with MoM revenue growth > -40%
        # Ensures momentum decay is not too severe
        cond5 = (rev_month_growth > -40).sustain(3)

        # Condition 6: Liquidity Constraints (流動性條件)
        # 10-day average volume must exceed 200k shares
        # Ensures adequate liquidity for entry and exit
        cond6 = vol_ma > 200 * 1000

        # Combine all conditions with AND operator
        # Stocks must pass ALL 6 contrarian conditions
        cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6

        return cond_all

    def _apply_volume_weighting(self, conditions, params: Dict):
        """
        Apply volume weighting and select lowest volume stocks (contrarian selection).

        This method implements the final stage of contrarian stock selection by:
        1. Weighting conditions by 10-day average trading volume
        2. Filtering out stocks with non-positive weighted scores
        3. Selecting the N stocks with LOWEST weighted scores (contrarian approach)

        The volume weighting combined with .is_smallest() creates a contrarian
        selection strategy that identifies neglected, under-the-radar stocks with
        low trading activity. This approach is fundamentally different from momentum
        strategies that chase high-volume, popular stocks.

        **CRITICAL CONTRARIAN LOGIC**:
        - Uses .is_smallest() to select LOW-volume stocks (not .is_largest())
        - Buys stocks that others are ignoring or selling
        - Expects mean reversion from undervalued, neglected positions
        - Opposite of momentum strategies that buy winners

        Args:
            conditions: Combined condition object from contrarian filtering
            params (Dict): Parameter dictionary containing:
                - n_stocks (int): Number of stocks to select for portfolio (3-10)
                    MUST be ≤10 for concentrated contrarian positioning

        Returns:
            Any: Final selection condition object representing the N stocks
                with LOWEST volume-weighted scores (contrarian selection)

        Source:
            Leveraged from example/藏獒.py:31-34 (volume weighting and contrarian selection)

        Implementation Details:
            Step 1: Load volume data
                Uses: 'price:成交股數' (trading volume in shares)
                Calculate: 10-day moving average for smoothing

            Step 2: Apply volume weighting
                Multiply filter conditions by volume moving average
                This weights each stock by its trading activity level

            Step 3: Filter positive values
                Remove stocks with negative or zero weighted scores
                buy = buy[buy > 0]

            Step 4: Contrarian Selection (KEY DIFFERENCE)
                Use .is_smallest(n_stocks) to select LOWEST volume stocks
                This is the essence of the contrarian reversal strategy

                Comparison:
                - TurtleTemplate: .is_largest() → HIGH revenue growth (momentum)
                - MastiffTemplate: .is_smallest() → LOW volume (contrarian)

        Position Management:
            - Concentrated holdings: n_stocks ≤10 (typically 3-10 positions)
            - High conviction: position_limit 15-30% per stock
            - Asymmetric upside: Mean reversion potential from neglected stocks

        Example:
            If conditions represent 50 stocks passing all 6 filters:
            - Weight each by its 10-day avg volume (e.g., 300K, 150K, 500K shares)
            - Keep only positive scores
            - Select 5 stocks with SMALLEST volume (e.g., 80K, 95K, 110K, 125K, 140K)
            - Result: Portfolio of 5 neglected, low-liquidity contrarian plays
        """
        # Load trading volume data (成交股數 - trading volume in shares)
        vol = self._get_cached_data('price:成交股數')

        # Calculate 10-day moving average for volume smoothing
        vol_ma = vol.average(10)

        # Apply volume weighting to prioritize based on trading activity
        # This weights conditions by trading volume patterns
        weighted_conditions = conditions * vol_ma

        # Filter out non-positive weighted scores and select N stocks with
        # LOWEST volume (contrarian selection - opposite of momentum strategies)
        # This is the key contrarian logic: buy neglected stocks, not popular ones
        final_selection = weighted_conditions[weighted_conditions > 0].is_smallest(params['n_stocks'])

        return final_selection

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete contrarian reversal strategy generation workflow:
        1. Validates input parameters against PARAM_GRID
        2. Creates 6 contrarian reversal filtering conditions
        3. Applies low-volume weighting and selects bottom N stocks
        4. Executes Finlab backtest with risk management parameters
        5. Extracts performance metrics and validates against targets

        Args:
            params (Dict): Parameter dictionary with values for all 10 parameters
                defined in PARAM_GRID. Required keys:
                - low_volume_days (int): Days for volume comparison (5, 10, 20)
                - volume_percentile (int): Low volume threshold (10, 20, 30)
                - price_drop_threshold (float): Min price drop (-0.05, -0.10, -0.15)
                - pe_max (int): Maximum P/E ratio (15, 20, 25)
                - revenue_growth_min (int): Min revenue growth (-5, 0, 5)
                - n_stocks (int): Portfolio size (3, 5, 8, 10)
                - stop_loss (float): Max loss per position (0.10, 0.15, 0.20)
                - take_profit (float): Target profit (0.30, 0.50, 0.80)
                - position_limit (float): Max position size (0.15, 0.20, 0.25, 0.30)
                - resample (str): Rebalancing frequency ('M' or 'W-FRI')

        Returns:
            Tuple[object, Dict]: A tuple containing:
                - report (object): Finlab backtest report object with complete
                    results including trades, equity curve, and metrics
                - metrics_dict (Dict): Dictionary with extracted metrics:
                    - 'annual_return' (float): Annual return as decimal
                    - 'sharpe_ratio' (float): Sharpe ratio
                    - 'max_drawdown' (float): Max drawdown as negative decimal
                    - 'success' (bool): True if strategy meets all performance
                        targets (Sharpe ≥1.2, Return ≥15%, MDD ≥-30%)

        Raises:
            ValueError: If parameters are invalid or fail validation
            RuntimeError: If strategy generation or backtesting fails
            Exception: If data loading or filtering operations fail

        Performance:
            Target execution time: <30s per strategy generation
            Leverages DataCache to avoid redundant data loading

        Source:
            Leveraged from example/藏獒.py:36 (contrarian backtest execution)

        Example:
            >>> template = MastiffTemplate()
            >>> params = {
            ...     'low_volume_days': 10, 'volume_percentile': 20,
            ...     'price_drop_threshold': -0.10, 'pe_max': 20,
            ...     'revenue_growth_min': 0, 'n_stocks': 5,
            ...     'stop_loss': 0.15, 'take_profit': 0.50,
            ...     'position_limit': 0.20, 'resample': 'M'
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 1.45
        """
        # Validate parameters before execution (Code Review Issue #4 fix)
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Create 6 contrarian reversal filtering conditions
            # This applies all contrarian filters: price high, revenue quality,
            # revenue bottom detection, momentum, and liquidity
            cond_all = self._create_contrarian_conditions(params)

            # Step 2: Apply volume weighting and select bottom N stocks (contrarian selection)
            # This weights conditions by trading volume and selects the N stocks with
            # LOWEST volume (contrarian approach - opposite of momentum strategies)
            final_selection = self._apply_volume_weighting(cond_all, params)

            # Step 3: Execute backtest with risk management parameters
            # Create descriptive strategy name for tracking
            strategy_name = f"Mastiff_{params['n_stocks']}n_{params['stop_loss']}sl"

            # Import backtest module (lazy import to avoid circular dependencies)
            from finlab import backtest

            # Run backtest simulation with all risk parameters
            # Note: Using trade_at_price='open' for realistic execution (from example/藏獒.py:36)
            report = backtest.sim(
                final_selection,
                resample=params['resample'],
                fee_ratio=1.425/1000/3,  # Taiwan stock transaction fee
                stop_loss=params['stop_loss'],
                take_profit=params['take_profit'],
                position_limit=params['position_limit'],
                trade_at_price='open',  # Trade at opening price (from example)
                upload=False,  # Disable upload for sandbox testing
                name=strategy_name
            )

            # Step 4: Extract performance metrics from backtest report
            # Calculate key metrics for strategy evaluation
            annual_return = report.metrics.annual_return()
            sharpe_ratio = report.metrics.sharpe_ratio()
            max_drawdown = report.metrics.max_drawdown()

            # Step 5: Validate against performance targets
            # Check if strategy meets all target thresholds
            expected_perf = self.expected_performance
            success = (
                sharpe_ratio >= expected_perf['sharpe_range'][0] and
                annual_return >= expected_perf['return_range'][0] and
                max_drawdown >= expected_perf['mdd_range'][0]
            )

            # Prepare metrics dictionary with all required fields
            metrics = {
                'annual_return': annual_return,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'success': success
            }

            return report, metrics

        except KeyError as e:
            # Parameter validation error - missing required key
            raise ValueError(
                f"Missing required parameter in params dictionary: {e}. "
                f"Required parameters: {list(self.PARAM_GRID.keys())}"
            ) from e

        except AttributeError as e:
            # Backtest or metrics calculation error
            raise RuntimeError(
                f"Failed to extract metrics from backtest report: {e}. "
                f"Ensure backtest.sim() completed successfully and report "
                f"object has valid metrics attribute."
            ) from e

        except Exception as e:
            # General error with context logging
            raise RuntimeError(
                f"Strategy generation failed for params {params}: {e}. "
                f"Check data availability, parameter validity, and filtering "
                f"conditions."
            ) from e
