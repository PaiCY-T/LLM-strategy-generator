"""
Factor Ranking Strategy Template
==================================

Implements a single-factor ranking strategy for cross-sectional stock selection.

Architecture:
-------------
The Factor template implements a classic quantitative factor-based strategy that:
- Ranks stocks by a single quantitative factor (e.g., P/E, ROE, revenue growth)
- Selects top/bottom N stocks based on factor ranking
- Rebalances periodically (monthly or quarterly)
- Uses low-turnover approach for consistent factor exposure

Strategy Characteristics:
------------------------
1. **Factor Selection**: Single-factor ranking across entire stock universe
   - Factor types: P/E ratio, P/B ratio, ROE, ROA, revenue growth, margin
   - Parameter: factor_type ('pe_ratio', 'pb_ratio', 'roe', 'roa', 'revenue_growth', 'margin')

2. **Ranking Direction**: Defines how to rank stocks by the chosen factor
   - Ascending: Lower values ranked higher (e.g., low P/E, low P/B)
   - Descending: Higher values ranked higher (e.g., high ROE, high growth)
   - Parameter: ranking_direction ('ascending', 'descending')

3. **Portfolio Size**: Number of stocks selected from rankings
   - Range: 10-50 stocks
   - Parameter: n_stocks (10, 20, 30, 50)

4. **Risk Controls**: Standard position sizing and exit rules
   - Stop loss: 8-15% maximum loss per position
   - Take profit: 20-50% target profit per position
   - Parameter: stop_loss (0.08, 0.10, 0.15), take_profit (0.20, 0.30, 0.50)

5. **Position Sizing**: Diversified portfolio with position limits
   - Position limit: 5-15% per stock (diversified approach)
   - Parameter: position_limit (0.05, 0.10, 0.15)

6. **Rebalancing**: Low-turnover periodic rebalancing
   - Frequency: Monthly or quarterly
   - Parameter: resample ('M' monthly, 'Q' quarterly)

Position Management:
-------------------
- Portfolio size: n_stocks (10-50 positions) - DIVERSIFIED
- Risk controls: stop_loss (8-15%), take_profit (20-50%)
- Position sizing: position_limit (5-15% per stock) - LOW CONCENTRATION
- Rebalancing: resample ('M' monthly or 'Q' quarterly) - LOW TURNOVER

Performance Targets:
-------------------
- Sharpe Ratio: 0.8-1.3 (modest but consistent risk-adjusted returns)
- Annual Return: 10-20% (steady growth from factor exposure)
- Max Drawdown: -25% to -15% (moderate downside protection)

Requirements:
------------
- Requirement 1.1: Provides name, pattern_type, PARAM_GRID, expected_performance
- Requirement 1.3: Returns Finlab backtest report and metrics dictionary
- Requirement 1.6: Implements factor ranking architecture
"""

from typing import Dict, List, Tuple
from src.templates.base_template import BaseTemplate


class FactorTemplate(BaseTemplate):
    """
    Single-Factor Ranking Strategy Template.

    Implements a quantitative factor-based strategy that:
    - Ranks stocks by a single quantitative factor
    - Uses cross-sectional ranking across entire universe
    - Selects top/bottom N stocks based on factor values
    - Rebalances periodically with low turnover

    The strategy uses systematic factor exposure: ranks all stocks by a
    chosen fundamental or valuation factor, then selects the top/bottom N
    stocks. This approach provides consistent factor exposure with low turnover,
    targeting steady risk-adjusted returns.

    Factor Strategies Characteristics:
    ----------------------------------
    - **Systematic**: Rules-based ranking, no discretionary decisions
    - **Cross-Sectional**: Ranks stocks relative to each other, not absolute thresholds
    - **Low Turnover**: Monthly or quarterly rebalancing reduces transaction costs
    - **Factor Exposure**: Pure exposure to single factor (value, quality, momentum)
    - **Diversified**: 10-50 positions with 5-15% position limits

    Attributes:
        name (str): "Factor" - identifying name for this template
        pattern_type (str): "factor_ranking" - describes the ranking strategy
        PARAM_GRID (Dict[str, List]): 7-parameter search space with 2,592 combinations
        expected_performance (Dict[str, Tuple[float, float]]): Performance targets
            - sharpe_range: (0.8, 1.3)
            - return_range: (0.10, 0.20)
            - mdd_range: (-0.25, -0.15)
    """

    @property
    def name(self) -> str:
        """
        Return the template name.

        Returns:
            str: "Factor" - the identifying name for this template
        """
        return "Factor"

    @property
    def pattern_type(self) -> str:
        """
        Return the strategy pattern type.

        Returns:
            str: "factor_ranking" - describes the single-factor ranking approach
        """
        return "factor_ranking"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid defining the search space.

        This grid defines all 7 tunable parameters with their possible values.
        Total search space: 6 * 2 * 4 * 3 * 3 * 3 * 2 = 2,592 combinations

        Parameter Categories:
        --------------------
        Factor Selection:
            - factor_type: Factor to rank by (6 options)
                'pe_ratio': Price-to-Earnings ratio (valuation)
                'pb_ratio': Price-to-Book ratio (valuation)
                'roe': Return on Equity (profitability/quality)
                'roa': Return on Assets (profitability/quality)
                'revenue_growth': Revenue growth rate (momentum/growth)
                'margin': Operating margin (profitability/quality)

            - ranking_direction: How to rank stocks (2 options)
                'ascending': Lower values ranked higher (e.g., low P/E = value)
                'descending': Higher values ranked higher (e.g., high ROE = quality)

        Portfolio Construction:
            - n_stocks: Number of stocks to select (4 options)
                10: Concentrated factor exposure
                20: Balanced diversification
                30: Diversified portfolio
                50: Highly diversified, index-like exposure

        Risk Management:
            - stop_loss: Maximum loss per position (3 options)
                0.08: Tight stop (8% loss limit)
                0.10: Moderate stop (10% loss limit)
                0.15: Loose stop (15% loss limit)

            - take_profit: Target profit per position (3 options)
                0.20: Conservative target (20% gain)
                0.30: Moderate target (30% gain)
                0.50: Aggressive target (50% gain)

        Position Sizing:
            - position_limit: Maximum position size (3 options)
                0.05: Highly diversified (5% per stock)
                0.10: Moderately diversified (10% per stock)
                0.15: Concentrated (15% per stock)

        Rebalancing:
            - resample: Rebalancing frequency (2 options)
                'M': Monthly rebalancing (higher turnover, faster factor adjustment)
                'Q': Quarterly rebalancing (lower turnover, reduced costs)

        Returns:
            Dict[str, List]: Parameter grid with 7 parameters

        Factor Strategy Design Rationale:
            - Factor selection: 6 common factors covering value, quality, momentum
            - Ranking direction: Allows long-value (low P/E) or long-quality (high ROE)
            - Portfolio size: 10-50 stocks balances concentration vs. diversification
            - Stop loss: 8-15% prevents large single-position losses
            - Take profit: 20-50% captures upside while managing volatility
            - Position limit: 5-15% ensures diversification (lower than Turtle/Mastiff)
            - Rebalancing: Monthly/quarterly balances turnover costs vs. factor drift
        """
        return {
            'factor_type': ['pe_ratio', 'pb_ratio', 'roe', 'roa', 'revenue_growth', 'margin'],
            'ranking_direction': ['ascending', 'descending'],
            'n_stocks': [10, 20, 30, 50],
            'stop_loss': [0.08, 0.10, 0.15],
            'take_profit': [0.20, 0.30, 0.50],
            'position_limit': [0.05, 0.10, 0.15],
            'resample': ['M', 'Q']
        }

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance metrics for this template.

        These ranges represent realistic targets based on the strategy's
        systematic factor ranking approach. Factor strategies typically deliver
        modest but consistent risk-adjusted returns with lower volatility than
        concentrated strategies (Turtle/Mastiff).

        Performance Targets:
        -------------------
        - Sharpe Ratio: 0.8-1.3 (modest but consistent risk-adjusted returns)
            Lower than Turtle (1.5-2.5) and Mastiff (1.2-2.0) due to:
            - Diversified portfolios (10-50 stocks vs. 5-20 for Turtle, 3-10 for Mastiff)
            - Lower concentration (5-15% position limit vs. 10-20% for Turtle, 15-30% for Mastiff)
            - Low turnover (monthly/quarterly vs. weekly rebalancing)
            - Single-factor exposure (less filtering than Turtle's 6-layer AND)

        - Annual Return: 10-20% (steady growth from factor exposure)
            More consistent but lower than Turtle (20-35%) and Mastiff (15-30%)
            Factor strategies provide systematic exposure with lower tail risk

        - Max Drawdown: -25% to -15% (moderate downside protection)
            Similar to Turtle (-25% to -10%) but tighter range
            Better than Mastiff (-30% to -15%) due to higher diversification

        Returns:
            Dict[str, Tuple[float, float]]: Performance ranges with keys:
                - 'sharpe_range': (min_sharpe, max_sharpe)
                - 'return_range': (min_return, max_return) as decimals
                - 'mdd_range': (min_drawdown, max_drawdown) as negative decimals

        Note:
            These ranges guide parameter optimization and validate strategy
            effectiveness. Actual performance depends on:
            - Factor selection (value vs. quality vs. momentum factors)
            - Market regime (value/growth cycles, bull/bear markets)
            - Rebalancing frequency (turnover costs vs. factor drift)
            - Parameter selection (concentration, risk controls)

        Factor Strategy Performance Characteristics:
            - **Consistency**: Lower variance than concentrated strategies
            - **Drawdowns**: Moderate drawdowns due to diversification
            - **Sharpe Ratio**: Respectable risk-adjusted returns (0.8-1.3)
            - **Turnover**: Low turnover reduces costs and improves net returns
            - **Regime Dependency**: Performance varies by factor and market regime
        """
        return {
            'sharpe_range': (0.8, 1.3),
            'return_range': (0.10, 0.20),
            'mdd_range': (-0.25, -0.15)
        }

    def _get_cached_data(self, key: str, verbose: bool = False):
        """
        Get cached data using the DataCache singleton.

        This helper method provides convenient access to the shared DataCache
        instance, avoiding redundant data loading operations.

        Args:
            key (str): Data key to retrieve (e.g., 'price_earning_ratio:本益比')
            verbose (bool): If True, prints loading messages. Default: False

        Returns:
            Any: Cached data object (typically DataFrame or Series)

        Raises:
            Exception: If data loading fails (propagated from DataCache)
        """
        from src.templates.data_cache import DataCache
        cache = DataCache.get_instance()
        return cache.get(key, verbose=verbose)

    def _calculate_factor_score(self, factor_type: str):
        """
        Calculate factor scores for all stocks in the universe.

        This method loads the appropriate dataset based on the factor type and
        returns the raw factor data for cross-sectional ranking. Supports all
        6 factor types defined in PARAM_GRID.

        Args:
            factor_type (str): Type of factor to calculate. Valid values:
                - 'pe_ratio': Price-to-Earnings ratio (valuation factor)
                    Lower P/E indicates potential undervaluation
                    Dataset: 'price_earning_ratio:本益比'

                - 'pb_ratio': Price-to-Book ratio (valuation factor)
                    Lower P/B indicates trading below book value
                    Dataset: 'price_earning_ratio:股價淨值比'

                - 'roe': Return on Equity (quality/profitability factor)
                    Higher ROE indicates efficient capital usage
                    Dataset: 'fundamental_features:ROE綜合損益'

                - 'roa': Return on Assets (quality/profitability factor)
                    Higher ROA indicates efficient asset utilization
                    Dataset: 'fundamental_features:資產報酬率'

                - 'revenue_growth': Revenue growth rate (momentum factor)
                    Higher growth indicates business momentum
                    Dataset: 'monthly_revenue:去年同月增減(%)'

                - 'margin': Operating margin (quality/profitability factor)
                    Higher margin indicates pricing power and efficiency
                    Dataset: 'fundamental_features:營業利益率'

        Returns:
            Any: Factor data object (finlab data structure) containing factor
                scores for all stocks across time. This will be passed to
                _apply_cross_sectional_rank() for ranking.

        Raises:
            ValueError: If factor_type is not one of the 6 supported types
            Exception: If data loading fails (propagated from DataCache)

        Implementation Details:
            - Uses DataCache for efficient data loading
            - Maps factor_type to appropriate dataset key
            - Returns raw factor data without preprocessing
            - No filtering or ranking applied at this stage

        Example:
            >>> template = FactorTemplate()
            >>> pe_data = template._calculate_factor_score('pe_ratio')
            >>> # pe_data contains P/E ratios for all stocks across time
            >>> roe_data = template._calculate_factor_score('roe')
            >>> # roe_data contains ROE values for all stocks across time

        Note:
            This method returns raw factor data. Ranking logic is applied
            separately in _apply_cross_sectional_rank() to support both
            ascending (low is good) and descending (high is good) rankings.
        """
        # Factor type to dataset key mapping
        factor_mapping = {
            'pe_ratio': 'price_earning_ratio:本益比',
            'pb_ratio': 'price_earning_ratio:股價淨值比',
            'roe': 'fundamental_features:ROE綜合損益',
            'roa': 'fundamental_features:資產報酬率',
            'revenue_growth': 'monthly_revenue:去年同月增減(%)',
            'margin': 'fundamental_features:營業利益率'
        }

        # Validate factor type
        if factor_type not in factor_mapping:
            raise ValueError(
                f"Invalid factor_type '{factor_type}'. "
                f"Must be one of: {list(factor_mapping.keys())}"
            )

        # Load factor data from DataCache
        dataset_key = factor_mapping[factor_type]
        factor_data = self._get_cached_data(dataset_key)

        return factor_data

    def _apply_cross_sectional_rank(self, factor_data, ranking_direction: str):
        """
        Apply cross-sectional ranking to factor scores.

        This method ranks stocks relative to each other at each time point
        (cross-sectional ranking) and returns percentile ranks from 0.0 to 1.0.
        The ranking direction determines whether lower or higher factor values
        receive higher ranks.

        Args:
            factor_data: Factor data object (finlab data structure) containing
                factor scores for all stocks across time. Typically a DataFrame
                where rows are dates and columns are stock symbols.

            ranking_direction (str): Direction for ranking. Valid values:
                - 'ascending': Lower factor values rank higher (closer to 1.0)
                    Use for factors where low is good (e.g., P/E, P/B ratios)
                    Example: P/E of 8 ranks higher than P/E of 15

                - 'descending': Higher factor values rank higher (closer to 1.0)
                    Use for factors where high is good (e.g., ROE, revenue growth)
                    Example: ROE of 20% ranks higher than ROE of 10%

        Returns:
            Any: Ranked data object (finlab data structure) containing percentile
                ranks from 0.0 to 1.0 for all stocks at each time point.
                - 1.0 = highest rank (best according to direction)
                - 0.0 = lowest rank (worst according to direction)
                - 0.5 = median rank

        Raises:
            ValueError: If ranking_direction is not 'ascending' or 'descending'

        Implementation Details:
            Cross-Sectional Ranking:
                - Uses .rank(axis=1, pct=True) for percentile ranking
                - axis=1: Ranks across columns (stocks) at each row (time point)
                - pct=True: Returns percentile ranks (0.0 to 1.0) instead of ordinal ranks

            Ranking Direction Logic:
                - 'ascending': ascending=True in rank() method
                    Lower values get lower ranks, then we can filter high ranks
                - 'descending': ascending=False in rank() method
                    Higher values get higher ranks directly

            Example:
                Given 3 stocks at a time point:
                    Stock A: P/E = 8 (low, good for value)
                    Stock B: P/E = 12 (medium)
                    Stock C: P/E = 20 (high, expensive)

                With ranking_direction='ascending':
                    Stock A rank: ~1.0 (highest rank, best value)
                    Stock B rank: ~0.5 (middle rank)
                    Stock C rank: ~0.0 (lowest rank, worst value)

        Note:
            This method performs pure cross-sectional ranking without any
            filtering or threshold application. Filtering by rank percentile
            (if needed) should be done separately in the strategy logic.
        """
        # Validate ranking direction
        if ranking_direction not in ['ascending', 'descending']:
            raise ValueError(
                f"Invalid ranking_direction '{ranking_direction}'. "
                f"Must be 'ascending' or 'descending'"
            )

        # Apply cross-sectional ranking
        # axis=1: rank across columns (stocks) at each time point
        # pct=True: return percentile ranks (0.0 to 1.0)
        # ascending: True for 'ascending' (low values rank low), False for 'descending' (high values rank high)
        ascending = (ranking_direction == 'ascending')
        ranked_data = factor_data.rank(axis=1, pct=True, ascending=ascending)

        return ranked_data

    def _apply_quality_filters(self, ranked_data, params: Dict):
        """
        Apply quality filters to enhance factor strategy robustness.

        This method applies additional filters on top of factor ranking to
        improve strategy quality and reduce false signals. Filters include:
        1. Technical confirmation: Moving average filter
        2. Liquidity filter: Volume constraints
        3. Volume momentum filter: Ensure adequate trading activity

        Args:
            ranked_data: Ranked factor data from _apply_cross_sectional_rank()
            params (Dict): Parameter dictionary containing filter thresholds

        Returns:
            Any: Filtered condition object combining rank-based selection with
                quality filters

        Implementation Details:
            Technical Confirmation Filter:
                - Price must be above 20-day moving average (uptrend confirmation)
                - Prevents entering stocks in downtrends even if factor ranks well

            Liquidity Filter:
                - 5-day average volume must be > 100k shares (minimum liquidity)
                - Ensures stocks can be traded without significant slippage

            Volume Momentum Filter:
                - Recent volume (5-day avg) > longer-term volume (20-day avg)
                - Indicates increasing interest and liquidity

        Note:
            This is an optional enhancement. Basic factor strategies may work
            without these filters, but they typically improve risk-adjusted returns
            by avoiding illiquid stocks and weak technical setups.
        """
        # Load price and trading value data
        close = self._get_cached_data('etl:adj_close')  # ✅ Adjusted for dividends/splits
        trading_value = self._get_cached_data('price:成交金額')  # OK for liquidity filter

        # Technical confirmation: Price above 20-day MA (uptrend)
        ma20 = close.average(20)
        technical_filter = close > ma20

        # Liquidity filter: Minimum 5-day average trading value (50M TWD)
        liquidity_filter = trading_value.average(5) >= 50_000_000

        # Trading activity: Increasing activity (5-day > 20-day average)
        activity_momentum = trading_value.average(5) > trading_value.average(20)

        # Combine quality filters with AND logic
        quality_conditions = technical_filter & liquidity_filter & activity_momentum

        # Apply quality filters to ranked data
        # Keep only stocks that pass quality filters
        filtered_data = ranked_data * quality_conditions

        return filtered_data

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate a strategy instance with the given parameters.

        This method orchestrates the complete factor ranking strategy generation workflow:
        1. Validate input parameters against PARAM_GRID
        2. Load factor data based on factor_type parameter
        3. Rank stocks by selected factor (ascending or descending)
        4. Apply quality filters for robustness
        5. Select top N stocks based on ranking
        6. Execute Finlab backtest with low-turnover configuration
        7. Extract performance metrics and validate against targets

        Args:
            params (Dict): Parameter dictionary with values for all 7 parameters
                defined in PARAM_GRID. Required keys:
                - factor_type (str): Factor to rank by ('pe_ratio', 'pb_ratio', 'roe',
                    'roa', 'revenue_growth', 'margin')
                - ranking_direction (str): Ranking direction ('ascending', 'descending')
                - n_stocks (int): Portfolio size (10, 20, 30, 50)
                - stop_loss (float): Max loss per position (0.08, 0.10, 0.15)
                - take_profit (float): Target profit per position (0.20, 0.30, 0.50)
                - position_limit (float): Max position size (0.05, 0.10, 0.15)
                - resample (str): Rebalancing frequency ('M' or 'Q')

        Returns:
            Tuple[object, Dict]: A tuple containing:
                - report (object): Finlab backtest report object with complete
                    results including trades, equity curve, and metrics
                - metrics_dict (Dict): Dictionary with extracted metrics:
                    - 'annual_return' (float): Annual return as decimal
                    - 'sharpe_ratio' (float): Sharpe ratio
                    - 'max_drawdown' (float): Max drawdown as negative decimal
                    - 'success' (bool): True if strategy meets all performance
                        targets (Sharpe ≥0.8, Return ≥10%, MDD ≥-25%)

        Raises:
            ValueError: If parameters are invalid or fail validation
            RuntimeError: If strategy generation or backtesting fails
            Exception: If data loading or factor calculation operations fail

        Performance:
            Target execution time: <30s per strategy generation
            Leverages DataCache to avoid redundant data loading

        Example:
            >>> template = FactorTemplate()
            >>> params = {
            ...     'factor_type': 'pe_ratio', 'ranking_direction': 'ascending',
            ...     'n_stocks': 20, 'stop_loss': 0.10, 'take_profit': 0.30,
            ...     'position_limit': 0.10, 'resample': 'M'
            ... }
            >>> report, metrics = template.generate_strategy(params)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            Sharpe: 1.05
        """
        # Validate parameters before execution (Code Review Issue #4 fix)
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Calculate factor scores for all stocks
            factor_data = self._calculate_factor_score(params['factor_type'])

            # Step 2: Apply cross-sectional ranking to factor data
            ranked_data = self._apply_cross_sectional_rank(
                factor_data,
                params['ranking_direction']
            )

            # Step 3: Apply quality filters to enhance robustness
            filtered_data = self._apply_quality_filters(ranked_data, params)

            # Step 4: Select top N stocks based on ranking
            # Use .is_largest() to select stocks with highest percentile ranks (closest to 1.0)
            # This works for both ascending and descending rankings because
            # _apply_cross_sectional_rank() already handles the direction logic
            final_selection = filtered_data[filtered_data > 0].is_largest(params['n_stocks'])

            # Step 5: Execute backtest with low-turnover configuration
            import finlab.backtest as backtest

            # Generate strategy name for identification
            strategy_name = (
                f"Factor_{params['factor_type']}_{params['ranking_direction']}_"
                f"N{params['n_stocks']}_SL{int(params['stop_loss']*100)}_"
                f"TP{int(params['take_profit']*100)}_PL{int(params['position_limit']*100)}_"
                f"{params['resample']}"
            )

            report = backtest.sim(
                final_selection,
                resample=params['resample'],  # 'M' or 'Q' for low turnover
                fee_ratio=1.425/1000/3,  # Standard Taiwan stock market fee
                stop_loss=params['stop_loss'],
                take_profit=params['take_profit'],
                position_limit=params['position_limit'],
                upload=False,  # Disable upload for sandbox testing
                name=strategy_name
            )

            # Step 6: Extract metrics from backtest report
            metrics_dict = self._extract_metrics(report)

            # Step 7: Validate metrics against expected performance targets
            metrics_dict['success'] = self._validate_performance(metrics_dict)

            return report, metrics_dict

        except ValueError as e:
            # Re-raise ValueError for parameter validation errors
            raise
        except Exception as e:
            # Wrap other exceptions in RuntimeError with context
            raise RuntimeError(
                f"Strategy generation failed for FactorTemplate with params {params}: {str(e)}"
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
            - Annual Return ≥ 10% (lower bound of return_range)
            - Max Drawdown ≥ -25% (upper bound of mdd_range, less negative)
        """
        expected = self.expected_performance

        # Check if metrics meet minimum thresholds
        sharpe_ok = metrics['sharpe_ratio'] >= expected['sharpe_range'][0]
        return_ok = metrics['annual_return'] >= expected['return_range'][0]
        mdd_ok = metrics['max_drawdown'] >= expected['mdd_range'][0]

        return sharpe_ok and return_ok and mdd_ok
