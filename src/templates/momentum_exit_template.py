"""
Momentum + Exit Strategy Template (Phase 0 Validation)
========================================================

PHASE 0 VALIDATION: Manual implementation of sophisticated exit strategies on Momentum template
to validate hypothesis before investing in mutation framework.

**Purpose**: Test whether adding exit strategies improves Momentum template performance
**Success Criteria**: Sharpe improvement ≥0.3 vs baseline Momentum template
**Timeline**: Phase 0, Task 0.1 (3 days)

Architecture:
-------------
Extends MomentumTemplate with 3 sophisticated exit mechanisms:
1. **ATR Trailing Stop-Loss**: 2× ATR below highest high since entry
2. **Fixed Profit Target**: 3× ATR above entry price
3. **Time-Based Exit**: Maximum 30 trading days holding period

These exit strategies implement the missing "exit half" identified in user insights:
- Stop-loss: Risk management through volatility-adjusted stops
- Take-profit: Systematic profit capture using risk-adjusted targets
- Time exit: Prevent stale positions and capital lock-up

Expected Impact (REQ-6 Estimates):
----------------------------------
- Sharpe Ratio: +0.3 to +0.8 improvement (20-60% increase)
- Max Drawdown: -15% to -40% reduction
- Win Rate: +5% to +15% increase
- Profit Factor: +0.2 to +0.5 improvement

Implementation Strategy:
------------------------
- Inherit from MomentumTemplate to preserve all entry logic
- Add ATR calculation helper function
- Implement exit logic post-processing on position signals
- Maintain backward compatibility (toggle exits via parameter)

Requirements Traceability:
--------------------------
- REQ-6: Exit Strategy Mutation (Phase 0 manual validation)
- User Insight: "止損、止盈的策略也都該加入演算法的範籌"
"""

from typing import Dict, List, Tuple
from src.templates.momentum_template import MomentumTemplate
import pandas as pd
import numpy as np


class MomentumExitTemplate(MomentumTemplate):
    """
    Momentum + Sophisticated Exit Strategies Template (Phase 0 Validation).

    Extends MomentumTemplate with three exit mechanisms to validate the hypothesis
    that sophisticated exits significantly improve strategy performance.

    **Exit Mechanisms**:
    1. **ATR Trailing Stop-Loss**: Exits when price falls 2× ATR below highest high
    2. **Fixed Profit Target**: Exits when profit reaches 3× ATR above entry
    3. **Time-Based Exit**: Forces exit after 30 trading days

    **Toggle Control**:
    - use_exits=True: Apply exit strategies (default for validation)
    - use_exits=False: Baseline Momentum template behavior

    Attributes:
        name (str): "MomentumExit" - identifying name
        pattern_type (str): "momentum_catalyst_exit" - momentum + catalyst + exits
        PARAM_GRID (Dict[str, List]): Extends parent with exit parameters
        expected_performance (Dict[str, Tuple[float, float]]): Improved targets
    """

    @property
    def name(self) -> str:
        """Return the template name."""
        return "MomentumExit"

    @property
    def pattern_type(self) -> str:
        """Return the strategy pattern type."""
        return "momentum_catalyst_exit"

    @property
    def PARAM_GRID(self) -> Dict[str, List]:
        """
        Return the parameter grid with exit strategy controls.

        Extends parent PARAM_GRID with:
        - use_exits: Toggle exit strategies on/off
        - atr_period: Period for ATR calculation (14 standard)
        - stop_atr_mult: ATR multiplier for trailing stop (2.0 standard)
        - profit_atr_mult: ATR multiplier for profit target (3.0 for 1.5:1 risk:reward)
        - max_hold_days: Maximum holding period (30 days standard)

        Total search space: 4 × 4 × 2 × 4 × 4 × 4 × 2 × 5 × 2 = 20,480 combinations
        (Double the Momentum template due to use_exits toggle)
        """
        # Get base Momentum parameters
        base_grid = super().PARAM_GRID

        # Add exit strategy parameters
        exit_grid = {
            **base_grid,
            'use_exits': [True, False],  # Toggle for A/B testing
            'atr_period': [14],  # Standard ATR period (fixed for Phase 0)
            'stop_atr_mult': [2.0],  # 2× ATR trailing stop (fixed for Phase 0)
            'profit_atr_mult': [3.0],  # 3× ATR profit target (fixed for Phase 0)
            'max_hold_days': [30]  # 30-day maximum hold (fixed for Phase 0)
        }

        return exit_grid

    @property
    def expected_performance(self) -> Dict[str, Tuple[float, float]]:
        """
        Return expected performance with exit strategies.

        Based on REQ-6 conservative estimates:
        - Baseline Momentum: Sharpe 0.8-1.5, Return 12-25%, MDD -30% to -18%
        - With Exits: Sharpe 1.1-2.3 (+0.3 to +0.8), Return 14-30%, MDD -25% to -12%

        Performance Improvements:
        -------------------------
        - Sharpe Ratio: 1.1-2.3 (37.5% to 53% improvement)
            - Lower bound: 0.8 + 0.3 = 1.1 (minimum success criteria)
            - Upper bound: 1.5 + 0.8 = 2.3 (maximum expected improvement)

        - Annual Return: 14-30% (16.7% to 20% improvement)
            - Improved profit capture through systematic take-profit
            - Reduced whipsaw losses through trailing stops

        - Max Drawdown: -25% to -12% (16.7% to 33.3% improvement)
            - ATR-based stops cut losing trades faster
            - Time exits prevent deep drawdowns in stale positions

        Returns:
            Dict[str, Tuple[float, float]]: Improved performance ranges
        """
        return {
            'sharpe_range': (1.1, 2.3),  # Baseline + 0.3 to 0.8 improvement
            'return_range': (0.14, 0.30),  # Baseline + improved profit capture
            'mdd_range': (-0.25, -0.12)  # Baseline + reduced drawdowns
        }

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calculate Average True Range (ATR) - volatility measure.

        ATR is the exponential moving average of true range, where true range is
        the greatest of:
        1. Current high - current low
        2. Absolute value of current high - previous close
        3. Absolute value of current low - previous close

        Args:
            data: DataFrame with 'high', 'low', 'close' columns (finlab data format)
            period: ATR calculation period (default 14 days, standard)

        Returns:
            pd.Series: ATR values for each stock and date

        Implementation Details:
            - True Range captures both intraday volatility and gap volatility
            - EMA smoothing reduces noise while staying responsive
            - ATR is absolute (not percentage), so scales with price level

        Example:
            Stock at $100:
            - High = 102, Low = 98, PrevClose = 99
            - TR1 = 102 - 98 = 4
            - TR2 = |102 - 99| = 3
            - TR3 = |98 - 99| = 1
            - True Range = max(4, 3, 1) = 4
            - ATR = EMA(True Range, 14)
        """
        # Get price data from finlab format
        high = data.get('high', data.get('最高價', None))
        low = data.get('low', data.get('最低價', None))
        close = data.get('close', data.get('收盤價', None))

        if high is None or low is None or close is None:
            raise ValueError("Data must contain 'high', 'low', 'close' columns")

        # Calculate three components of True Range
        tr1 = high - low  # Intraday range
        tr2 = abs(high - close.shift(1))  # High to previous close
        tr3 = abs(low - close.shift(1))  # Low to previous close

        # True Range is the maximum of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # ATR is the exponential moving average of True Range
        atr = true_range.ewm(span=period, adjust=False).mean()

        return atr

    def _apply_exit_strategies(
        self,
        positions: pd.DataFrame,
        data: Dict,
        params: Dict
    ) -> pd.DataFrame:
        """
        Apply sophisticated exit strategies to position signals.

        Implements three exit mechanisms in order of priority:
        1. **Time Exit**: Force exit after max_hold_days (highest priority)
        2. **Stop-Loss**: Exit when price falls stop_atr_mult × ATR below highest high
        3. **Profit Target**: Exit when profit reaches profit_atr_mult × ATR above entry

        Args:
            positions: Boolean DataFrame of entry signals (from Momentum logic)
            data: Dictionary of price data ('close', 'high', 'low', etc.)
            params: Parameter dictionary with exit configuration

        Returns:
            pd.DataFrame: Modified position signals with exits applied

        Exit Logic Flow:
        ----------------
        1. Calculate ATR for volatility-adjusted stops/targets
        2. Track entry prices (when position first goes True)
        3. Track highest high since entry (for trailing stop)
        4. Track holding period (days since entry)
        5. Apply exits in priority order (time → stop → profit)
        6. Clear exit signals (set position to False)

        Example:
            Entry at $100, ATR = $5:
            - Stop-loss level: highest_high - (2.0 × $5) = highest_high - $10
            - Profit target: $100 + (3.0 × $5) = $115
            - Time exit: After 30 trading days

            If price rises to $120 (new highest high):
            - Stop-loss adjusts: $120 - $10 = $110 (trailing)
            - Profit target stays: $115 (hit, exit triggered)

        Performance Impact:
            - Stop-loss: Cuts losing trades at -10% typical (2× $5 ATR on $100)
            - Profit target: Captures +15% typical (3× $5 ATR on $100)
            - Time exit: Prevents capital lock-up in dead positions
        """
        # If use_exits is False, return original positions (baseline)
        if not params.get('use_exits', True):
            return positions

        # Get price data
        close = data.get('close', data.get('收盤價', None))
        high = data.get('high', data.get('最高價', None))

        if close is None or high is None:
            # Cannot apply exits without price data, return original
            return positions

        # Calculate ATR for volatility-adjusted exits
        atr_period = params.get('atr_period', 14)
        atr = self._calculate_atr(data, period=atr_period)

        # Ensure all DataFrames have the same columns (align to positions columns)
        positions = positions.fillna(False)

        # Handle both Series and DataFrame for price data
        if isinstance(close, pd.Series):
            # If Series, convert to DataFrame matching positions structure
            close = pd.DataFrame({col: close for col in positions.columns}, index=close.index)
        else:
            close = close.reindex(columns=positions.columns)

        if isinstance(high, pd.Series):
            high = pd.DataFrame({col: high for col in positions.columns}, index=high.index)
        else:
            high = high.reindex(columns=positions.columns)

        if isinstance(atr, pd.Series):
            atr = pd.DataFrame({col: atr for col in positions.columns}, index=atr.index)
        else:
            atr = atr.reindex(columns=positions.columns)

        # Initialize tracking variables with proper dtype and alignment
        entry_price = pd.DataFrame(np.nan, index=positions.index, columns=positions.columns)
        highest_high = pd.DataFrame(np.nan, index=positions.index, columns=positions.columns)
        holding_days = pd.DataFrame(0, index=positions.index, columns=positions.columns, dtype=int)

        # Modified positions (will apply exits)
        modified_positions = positions.copy()

        # Get date index for proper loc-based access
        dates = positions.index

        # Process each row (date) sequentially to track state
        for i, date in enumerate(dates):
            if i == 0:
                # First row: Initialize entry prices for positions that are True
                mask = positions.loc[date].fillna(False)
                entry_price.loc[date] = close.loc[date].where(mask, np.nan)
                highest_high.loc[date] = high.loc[date].where(mask, np.nan)
                holding_days.loc[date] = mask.astype(int)
            else:
                prev_date = dates[i-1]
                prev_positions = modified_positions.loc[prev_date].fillna(False)
                curr_positions = positions.loc[date].fillna(False)

                # Carry forward existing positions (not yet exited)
                continuing = prev_positions.copy()

                # New entries (signal is True AND was not in position yesterday)
                new_entries = curr_positions & ~prev_positions

                # Update entry prices
                # Keep existing entry price for continuing positions, set new for new entries
                entry_price.loc[date] = entry_price.loc[prev_date].where(continuing, np.nan)
                entry_price.loc[date] = close.loc[date].where(new_entries, entry_price.loc[date])

                # Update highest high since entry
                # For continuing: max of previous highest and current high
                # For new entries: current high
                highest_high.loc[date] = highest_high.loc[prev_date].where(continuing, np.nan)
                highest_high.loc[date] = pd.DataFrame([
                    highest_high.loc[date],
                    high.loc[date]
                ]).max().where(continuing, highest_high.loc[date])
                highest_high.loc[date] = high.loc[date].where(new_entries, highest_high.loc[date])

                # Update holding days
                holding_days.loc[date] = (holding_days.loc[prev_date] + 1).where(continuing, 0)
                holding_days.loc[date] = holding_days.loc[date].where(~new_entries, 1)

                # Apply exit strategies (in priority order)

                # 1. TIME EXIT: Force exit after max holding period
                max_hold = params.get('max_hold_days', 30)
                time_exit = holding_days.loc[date] >= max_hold

                # 2. STOP-LOSS: Exit when price falls below trailing stop
                stop_multiplier = params.get('stop_atr_mult', 2.0)
                stop_level = highest_high.loc[date] - (atr.loc[date] * stop_multiplier)
                stop_exit = close.loc[date] < stop_level

                # 3. PROFIT TARGET: Exit when profit target reached
                profit_multiplier = params.get('profit_atr_mult', 3.0)
                profit_target = entry_price.loc[date] + (atr.loc[date] * profit_multiplier)
                profit_exit = close.loc[date] >= profit_target

                # Combine all exit signals (handle NaN values)
                any_exit = (time_exit.fillna(False) |
                           stop_exit.fillna(False) |
                           profit_exit.fillna(False))

                # Apply exits: Clear position if any exit triggered
                # Keep position if no exit AND (continuing OR new entry)
                modified_positions.loc[date] = (continuing | new_entries) & ~any_exit

        return modified_positions

    def generate_strategy(self, params: Dict) -> Tuple[object, Dict]:
        """
        Generate strategy with exit strategies applied.

        Extends parent generate_strategy to add exit logic:
        1. Call parent to generate momentum + catalyst entry signals
        2. Apply exit strategies to modify position signals
        3. Re-run backtest with modified signals
        4. Return results for comparison

        Args:
            params: Parameter dictionary (includes both Momentum and Exit params)

        Returns:
            Tuple[object, Dict]: Backtest report and metrics dictionary

        Implementation Notes:
            - Parent generate_strategy creates positions based on momentum + catalyst
            - We intercept those positions and apply exit logic
            - Then run finlab backtest on modified positions
            - This allows clean A/B comparison (use_exits=True vs False)

        Performance:
            Target execution: <30s per strategy (same as parent)
            Exit logic adds ~1-2s overhead (position tracking)
        """
        # Validate parameters
        is_valid, errors = self.validate_params(params)
        if not is_valid:
            raise ValueError(
                f"Parameter validation failed: {'; '.join(errors)}"
            )

        try:
            # Step 1: Calculate momentum and catalyst (from parent)
            momentum = self._calculate_momentum(params)

            close = self._get_cached_data('price:收盤價')
            ma_filter = close > close.average(params['ma_periods'])

            if params['catalyst_type'] == 'revenue':
                catalyst = self._apply_revenue_catalyst(params)
            elif params['catalyst_type'] == 'earnings':
                catalyst = self._apply_earnings_catalyst(params)
            else:
                raise ValueError(
                    f"Invalid catalyst_type '{params['catalyst_type']}'. "
                    f"Must be 'revenue' or 'earnings'"
                )

            # Step 2: Combine conditions (entry logic)
            all_conditions = ma_filter & catalyst

            # Step 3: Select top N by momentum
            positions = momentum[all_conditions].is_largest(params['n_stocks'])

            # Step 4: Apply exit strategies (if enabled)
            # Prepare data dictionary for exit logic
            data_dict = {
                'close': close,
                'high': self._get_cached_data('price:最高價'),
                'low': self._get_cached_data('price:最低價')
            }

            positions = self._apply_exit_strategies(positions, data_dict, params)

            # Step 5: Execute backtest with modified positions
            import finlab.backtest as backtest

            strategy_name = (
                f"MomentumExit_MW{params['momentum_period']}_MA{params['ma_periods']}_"
                f"{params['catalyst_type'][:3]}{params['catalyst_lookback']}_"
                f"N{params['n_stocks']}_"
                f"{'EXIT' if params.get('use_exits', True) else 'BASE'}_"
                f"{params['resample']}{params['resample_offset']}"
            )

            # Build resample string
            if params['resample'] == 'W':
                if params['resample_offset'] == 0:
                    resample_str = 'W-MON'
                elif params['resample_offset'] == 1:
                    resample_str = 'W-TUE'
                elif params['resample_offset'] == 2:
                    resample_str = 'W-WED'
                elif params['resample_offset'] == 3:
                    resample_str = 'W-THU'
                else:
                    resample_str = 'W-FRI'
            else:  # 'M'
                if params['resample_offset'] == 0:
                    resample_str = 'M'
                else:
                    resample_str = f"MS+{params['resample_offset']}D"

            # Run backtest (exits already applied in position signals)
            # Note: stop_loss/take_profit parameters ignored since exits handled manually
            report = backtest.sim(
                positions,
                resample=resample_str,
                fee_ratio=1.425/1000/3,
                stop_loss=None,  # Disabled - using manual exit logic
                take_profit=None,  # Disabled - using manual exit logic
                position_limit=0.20,
                upload=False,
                name=strategy_name
            )

            # Extract metrics
            metrics_dict = self._extract_metrics(report)

            # Validate against expected performance
            metrics_dict['success'] = self._validate_performance(metrics_dict)

            return report, metrics_dict

        except ValueError as e:
            raise
        except Exception as e:
            raise RuntimeError(
                f"Strategy generation failed for MomentumExitTemplate: {str(e)}"
            ) from e
