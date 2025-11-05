"""
Turtle Strategy Template
========================

Implements the High Dividend Turtle Strategy using 6-layer AND filtering.

Architecture:
-------------
The Turtle template implements a comprehensive multi-layer AND filtering strategy
with the following 6 layers:

1. **Yield Layer**: Filters stocks by dividend yield threshold (基本面選股)
   - Uses monthly dividend data to identify high-yield opportunities
   - Parameter: yield_threshold (4.0-8.0%)

2. **Technical Layer**: Moving average crossover signals (技術面選股)
   - Combines short-term and long-term moving averages
   - Parameters: ma_short (10-30 days), ma_long (40-80 days)

3. **Revenue Layer**: Revenue growth momentum (營收面選股)
   - Analyzes short-term and long-term revenue growth trends
   - Parameters: rev_short (3-6 months), rev_long (12-18 months)

4. **Quality Layer**: Operational efficiency metrics (品質面選股)
   - Filters by operating margin threshold
   - Parameter: op_margin_threshold (0-5%)

5. **Insider Layer**: Director shareholding changes (內部人持股)
   - Tracks insider buying as a confidence signal
   - Parameter: director_threshold (5-15% change)

6. **Liquidity Layer**: Trading volume constraints (流動性篩選)
   - Ensures adequate liquidity for entry/exit
   - Parameters: vol_min (30-100k), vol_max (5M-15M shares)

Position Management:
-------------------
- Portfolio size: n_stocks (5-20 positions)
- Risk controls: stop_loss (6-10%), take_profit (30-70%)
- Position sizing: position_limit (10-20% per stock)
- Rebalancing: resample ('M' monthly or 'W-FRI' weekly)

Performance Targets:
-------------------
- Sharpe Ratio: 1.5-2.5
- Annual Return: 20-35%
- Max Drawdown: -25% to -10%

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Requirement 1.4: Implements 6-layer AND filtering architecture
"""

from typing import Dict, List, Tuple
from src.templates.base_template import BaseTemplate


class TurtleTemplate(BaseTemplate):
    """
    High Dividend Turtle Strategy Template.

    Implements a 6-layer AND filtering strategy that combines:
    - Fundamental analysis (yield, quality)
    - Technical analysis (moving averages)
    - Revenue momentum (short and long-term)
    - Insider confidence signals
    - Liquidity constraints

    The strategy uses strict AND logic: stocks must pass ALL 6 layers to be
    included in the portfolio. This conservative approach aims for high-quality,
    high-conviction positions with strong risk-adjusted returns.

    Attributes:
        name (str): "Turtle" - identifying name for this template
        pattern_type (str): "multi_layer_and" - describes the filtering strategy
        PARAM_GRID (Dict[str, List]): 14-parameter search space with 5,184,000 combinations
        expected_performance (Dict[str, Tuple[float, float]]): Performance targets
            - sharpe_range: (1.5, 2.5)
            - return_range: (0.20, 0.35)
            - mdd_range: (-0.25, -0.10)
    """

    @property
    def name(self) -> str:
        """
        Return the template name.

        Returns:
            str: "Turtle" - the identifying name for this template
        """
        return "Turtle"

    @property
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: "multi_layer_and" - describes the 6-layer AND filtering approach
        """
        return "multi_layer_and"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 14 tunable parameters with their possible values.
        Total search space: 5 * 3 * 3 * 2 * 2 * 3 * 3 * 3 * 3 * 4 * 3 * 3 * 4 * 2
        = 5,184,000 combinations

        Parameter Categories:
        --------------------
        Yield Layer:
            - yield_threshold: Minimum dividend yield (4-8%)

        Technical Layer:
            - ma_short: Short-term moving average period (10-30 days)
            - ma_long: Long-term moving average period (40-80 days)

        Revenue Layer:
            - rev_short: Short-term revenue growth window (3-6 months)
            - rev_long: Long-term revenue growth window (12-18 months)

        Quality Layer:
            - op_margin_threshold: Minimum operating margin (0-5%)

        Insider Layer:
            - director_threshold: Minimum director shareholding change (5-15%)

        Liquidity Layer:
            - vol_min: Minimum daily volume (30k-100k shares)
            - vol_max: Maximum daily volume (5M-15M shares)

        Position Management:
            - n_stocks: Portfolio size (5-20 positions)
            - stop_loss: Maximum loss per position (6-10%)
            - take_profit: Target profit per position (30-70%)
            - position_limit: Maximum position size (10-20% of portfolio)
            - resample: Rebalancing frequency ('M' monthly, 'W-FRI' weekly)

        Returns:
            Dict[str, List]: Parameter grid with 14 parameters

        Source:
            Leveraged from turtle_strategy_generator.py:29-61 (PARAM_GRID)
        """
        return {
            'yield_threshold': [4.0, 5.0, 6.0, 7.0, 8.0],
            'ma_short': [10, 20, 30],
            'ma_long': [40, 60, 80],
            'rev_short': [3, 6],
            'rev_long': [12, 18],
            'op_margin_threshold': [0, 3, 5],
            'director_threshold': [5, 10, 15],
            'vol_min': [30, 50, 100],
            'vol_max': [5000, 10000, 15000],
            'n_stocks': [5, 10, 15, 20],
            'stop_loss': [0.06, 0.08, 0.10],
            'take_profit': [0.3, 0.5, 0.7],
            'position_limit': [0.10, 0.125, 0.15, 0.20],
            'resample': ['M', 'W-FRI']
        }

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These ranges represent realistic targets based on the strategy's
        conservative AND filtering approach. The strategy prioritizes
        capital preservation and consistent risk-adjusted returns over
        aggressive growth.

        Performance Targets:
        -------------------
        - Sharpe Ratio: 1.5-2.5 (good risk-adjusted returns)
        - Annual Return: 20-35% (consistent growth)
        - Max Drawdown: -25% to -10% (controlled downside)

        Returns:
            Dict[str, Tuple[float, float]]: Performance ranges with keys:
                - 'sharpe_range': (min_sharpe, max_sharpe)
                - 'return_range': (min_return, max_return) as decimals
                - 'mdd_range': (min_drawdown, max_drawdown) as negative decimals

        Note:
            These ranges guide parameter optimization and validate strategy
            effectiveness. Actual performance depends on market conditions
            and parameter selection.
        """
        return {
            'sharpe_range': (1.5, 2.5),
            'return_range': (0.20, 0.35),
            'mdd_range': (-0.25, -0.10)
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

    def _create_6_layer_filter(self, params: Dict):
        """
        Create 6-layer AND filtering conditions for stock selection.

        Implements the comprehensive multi-layer filtering strategy that combines:
        - Layer 1: Dividend Yield (基本面選股)
        - Layer 2: Technical Confirmation (技術面選股)
        - Layer 3: Revenue Acceleration (營收面選股)
        - Layer 4: Operating Margin Quality (品質面選股)
        - Layer 5: Director Confidence (內部人持股)
        - Layer 6: Liquidity (流動性篩選)

        All conditions are combined with AND logic: stocks must pass ALL 6 layers
        to be included in the portfolio.

        Args:
            params (Dict): Parameter dictionary containing:
                - yield_threshold (float): Minimum dividend yield (4-8%)
                - ma_short (int): Short-term MA period (10-30 days)
                - ma_long (int): Long-term MA period (40-80 days)
                - rev_short (int): Short-term revenue window (3-6 months)
                - rev_long (int): Long-term revenue window (12-18 months)
                - op_margin_threshold (float): Minimum operating margin (0-5%)
                - director_threshold (float): Minimum director holding change (5-15%)
                - vol_min (int): Minimum daily volume (30k-100k shares)
                - vol_max (int): Maximum daily volume (5M-15M shares)

        Returns:
            Any: Combined condition object (finlab data structure) representing
                stocks that pass all 6 filtering layers

        Source:
            Leveraged from turtle_strategy_generator.py:93-128 (6-layer filtering logic)

        Implementation Details:
            Layer 1 - Dividend Yield:
                Filters stocks with yield >= threshold
                Uses: 'price_earning_ratio:殖利率(%)'

            Layer 2 - Technical Confirmation:
                Price must be above both short and long-term moving averages
                Uses: 'price:收盤價' with SMA calculations

            Layer 3 - Revenue Acceleration:
                Short-term revenue growth > long-term revenue growth
                Uses: 'monthly_revenue:當月營收'

            Layer 4 - Operating Margin Quality:
                Operating margin must exceed minimum threshold
                Uses: 'fundamental_features:營業利益率'

            Layer 5 - Director Confidence:
                Director shareholding must exceed minimum threshold
                Uses: 'internal_equity_changes:董監持有股數占比'

            Layer 6 - Liquidity:
                5-day average volume must be within min/max bounds
                Uses: 'price:成交股數' (converted to thousands)
        """
        # Load all required datasets using DataCache
        close = self._get_cached_data('price:收盤價')
        vol = self._get_cached_data('price:成交股數')
        rev = self._get_cached_data('monthly_revenue:當月營收')
        ope_earn = self._get_cached_data('fundamental_features:營業利益率')
        yield_ratio = self._get_cached_data('price_earning_ratio:殖利率(%)')
        boss_hold = self._get_cached_data('internal_equity_changes:董監持有股數占比')

        # Calculate technical indicators
        sma_short = close.average(params['ma_short'])
        sma_long = close.average(params['ma_long'])

        # Layer 1: Dividend Yield
        cond1 = yield_ratio >= params['yield_threshold']

        # Layer 2: Technical Confirmation
        cond2 = (close > sma_short) & (close > sma_long)

        # Layer 3: Revenue Acceleration
        cond3 = rev.average(params['rev_short']) > rev.average(params['rev_long'])

        # Layer 4: Operating Margin Quality
        cond4 = ope_earn >= params['op_margin_threshold']

        # Layer 5: Director Confidence
        cond5 = boss_hold >= params['director_threshold']

        # Layer 6: Liquidity
        cond6 = (
            (vol.average(5) >= params['vol_min'] * 1000) &
            (vol.average(5) <= params['vol_max'] * 1000)
        )

        # Combine all conditions with AND operator
        cond_all = cond1 & cond2 & cond3 & cond4 & cond5 & cond6

        return cond_all

    def _apply_revenue_weighting(self, conditions, params: Dict):
        """
        Apply revenue growth weighting and select top N stocks.

        This method implements the final stage of stock selection by:
        1. Weighting conditions by year-over-year revenue growth rate
        2. Filtering out stocks with non-positive weighted scores
        3. Selecting the top N stocks with highest weighted scores

        The revenue growth weighting gives preference to stocks showing strong
        momentum in revenue growth, which is a key indicator of business health
        and competitive advantage.

        Args:
            conditions: Combined condition object from 6-layer filtering
            params (Dict): Parameter dictionary containing:
                - n_stocks (int): Number of stocks to select for portfolio (5-20)

        Returns:
            Any: Final selection condition object representing the top N stocks
                ranked by revenue-weighted scores

        Source:
            Leveraged from:
            - turtle_strategy_generator.py:131-132 (weighting and selection logic)
            - example/高殖利率烏龜.py:30-32 (reference implementation)

        Implementation Details:
            Step 1: Load revenue growth rate data
                Uses: 'monthly_revenue:去年同月增減(%)' (YoY revenue growth)

            Step 2: Apply weighting
                Multiply filter conditions by revenue growth rate to favor
                stocks with accelerating revenue

            Step 3: Filter positive values
                Remove stocks with negative or zero weighted scores

            Step 4: Select top N
                Use .is_largest(n_stocks) to select highest-ranked stocks
                for final portfolio composition

        Example:
            If conditions represent 50 stocks passing all 6 filters:
            - Weight each by its YoY revenue growth (e.g., 15%, 8%, -2%, ...)
            - Keep only positive scores (removes declining revenue stocks)
            - Select top 10 (n_stocks=10) by weighted score
        """
        # Load revenue growth rate data (year-over-year growth percentage)
        rev_growth_rate = self._get_cached_data('monthly_revenue:去年同月增減(%)')

        # Apply revenue growth weighting to prioritize high-growth stocks
        weighted_conditions = conditions * rev_growth_rate

        # Filter out non-positive weighted scores (removes declining revenue stocks)
        # and select top N stocks with highest revenue-weighted scores
        final_selection = weighted_conditions[weighted_conditions > 0].is_largest(params['n_stocks'])

        return final_selection

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete strategy generation workflow:
        1. Validates input parameters against PARAM_GRID
        2. Creates 6-layer AND filtering conditions
        3. Applies revenue growth weighting and selects top N stocks
        4. Executes Finlab backtest with risk management parameters
        5. Extracts performance metrics and validates against targets

        Args:
            params (Dict): Parameter dictionary with values for all 14 parameters
                defined in PARAM_GRID. Required keys:
                - yield_threshold (float): Dividend yield filter (4-8%)
                - ma_short (int): Short-term MA period (10-30 days)
                - ma_long (int): Long-term MA period (40-80 days)
                - rev_short (int): Short-term revenue window (3-6 months)
                - rev_long (int): Long-term revenue window (12-18 months)
                - op_margin_threshold (float): Operating margin filter (0-5%)
                - director_threshold (float): Director holding change (5-15%)
                - vol_min (int): Minimum daily volume (30k-100k shares)
                - vol_max (int): Maximum daily volume (5M-15M shares)
                - n_stocks (int): Portfolio size (5-20 positions)
                - stop_loss (float): Max loss per position (6-10%)
                - take_profit (float): Target profit per position (30-70%)
                - position_limit (float): Max position size (10-20%)
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
                        targets (Sharpe ≥1.5, Return ≥20%, MDD ≥-25%)

        Raises:
            ValueError: If parameters are invalid or fail validation
            RuntimeError: If strategy generation or backtesting fails
            Exception: If data loading or filtering operations fail

        Performance:
            Target execution time: <30s per strategy generation
            Leverages DataCache to avoid redundant data loading

        Source:
            Leveraged from turtle_strategy_generator.py:83-159
            (generate_turtle_strategy function)

        Example:
            >>> template = TurtleTemplate()
            >>> params = {
            ...     'yield_threshold': 6.0, 'ma_short': 20, 'ma_long': 60,
            ...     'rev_short': 3, 'rev_long': 12, 'op_margin_threshold': 3,
            ...     'director_threshold': 10, 'vol_min': 50, 'vol_max': 10000,
            ...     'n_stocks': 10, 'stop_loss': 0.06, 'take_profit': 0.5,
            ...     'position_limit': 0.125, 'resample': 'M'
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 2.09
        """
        # Validate parameters before execution (Code Review Issue #4 fix)
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Create 6-layer AND filtering conditions
            # This applies all filtering layers: yield, technical, revenue,
            # quality, insider, and liquidity
            cond_all = self._create_6_layer_filter(params)

            # Step 2: Apply revenue growth weighting and select top N stocks
            # This weights conditions by YoY revenue growth and selects the
            # top N stocks for the final portfolio
            final_selection = self._apply_revenue_weighting(cond_all, params)

            # Step 3: Execute backtest with risk management parameters
            # Create descriptive strategy name for tracking
            strategy_name = f"Turtle_{params['yield_threshold']}y_{params['n_stocks']}n"

            # Import backtest module (lazy import to avoid circular dependencies)
            from finlab import backtest

            # Run backtest simulation with all risk parameters
            report = backtest.sim(
                final_selection,
                resample=params['resample'],
                fee_ratio=1.425/1000/3,  # Taiwan stock transaction fee
                stop_loss=params['stop_loss'],
                take_profit=params['take_profit'],
                position_limit=params['position_limit'],
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
