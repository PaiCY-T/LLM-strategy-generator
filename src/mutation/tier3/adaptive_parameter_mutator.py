"""
Adaptive Parameter Mutator - Create factors with dynamic parameters.

Enables creation of factors where parameters adapt to market conditions
(volatility, regime, performance) for more robust trading strategies.

Part of Tier 3 AST Mutation Framework.
Task: D.3 - AST-Based Factor Logic Mutation
"""

from typing import Dict, Any, Callable
import pandas as pd
import copy

from src.factor_graph.factor import Factor


class AdaptiveParameterMutator:
    """
    Create factors with adaptive parameters.

    Adaptive Parameter Types:
    ------------------------
    1. Volatility-Adaptive: Parameters scale with market volatility
       Example: threshold = base * (current_volatility / avg_volatility)

    2. Regime-Adaptive: Parameters adjust to market regime (bull/bear/sideways)
       Example: aggressive_threshold in bull, conservative in bear

    3. Performance-Adaptive: Parameters adjust based on recent performance
       Example: increase threshold after losses, decrease after wins

    Example Usage:
    -------------
    ```python
    mutator = AdaptiveParameterMutator()

    # Make threshold volatility-adaptive
    adaptive_factor = mutator.create_volatility_adaptive(
        base_factor=rsi_factor,
        param_name="overbought_threshold",
        volatility_period=20
    )

    # Make strategy regime-adaptive
    adaptive_factor = mutator.create_regime_adaptive(
        base_factor=momentum_factor,
        param_name="period",
        bull_value=14,
        bear_value=30
    )
    ```

    Design Notes:
    ------------
    - Adaptive parameters calculated at runtime based on market data
    - Original factor logic preserved, parameters modified dynamically
    - Adds required inputs (volatility, regime indicators)
    - Maintains same outputs as original factor
    """

    def create_volatility_adaptive(
        self,
        base_factor: Factor,
        param_name: str = None,
        volatility_period: int = 20,
        scale_factor: float = 1.0
    ) -> Factor:
        """
        Make factor parameters adapt to volatility.

        Creates a new factor where specified parameter scales with
        market volatility:
        adapted_param = base_param * (current_vol / avg_vol) * scale_factor

        Args:
            base_factor: Original factor to make adaptive
            param_name: Parameter name to adapt (if None, adapts first numeric param)
            volatility_period: Period for volatility calculation (default: 20)
            scale_factor: Scaling factor for adaptation strength (default: 1.0)

        Returns:
            New Factor with volatility-adaptive parameter

        Example:
            >>> # Adapt RSI overbought threshold to volatility
            >>> adaptive = mutator.create_volatility_adaptive(
            ...     base_factor=rsi_factor,
            ...     param_name="overbought_threshold",
            ...     volatility_period=20
            ... )
        """
        # Determine which parameter to adapt
        if param_name is None:
            # Find first numeric parameter
            for name, value in base_factor.parameters.items():
                if isinstance(value, (int, float)):
                    param_name = name
                    break

        if param_name is None or param_name not in base_factor.parameters:
            raise ValueError(
                f"Parameter '{param_name}' not found in factor. "
                f"Available parameters: {list(base_factor.parameters.keys())}"
            )

        base_param_value = base_factor.parameters[param_name]

        # Create adaptive logic
        def adaptive_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            # Calculate volatility ratio
            returns = data['close'].pct_change()
            current_vol = returns.rolling(window=volatility_period).std()
            avg_vol = returns.std()

            # Calculate volatility ratio (avoid division by zero)
            vol_ratio = current_vol / avg_vol if avg_vol != 0 else 1.0

            # Create adaptive parameter column
            adapted_param = base_param_value * vol_ratio * scale_factor

            # Store in data for reference (optional)
            data[f'{param_name}_adaptive'] = adapted_param

            # Create modified params with adaptive value
            # Use median adaptive value for the entire period
            if isinstance(adapted_param, pd.Series):
                median_adaptive = adapted_param.median()
            else:
                median_adaptive = adapted_param  # Scalar value
            modified_params = params.copy()
            modified_params[param_name] = median_adaptive

            # Execute base factor logic with adaptive parameter
            result = base_factor.logic(data, modified_params)

            return result

        # Add 'close' to inputs if not present (needed for volatility)
        adaptive_inputs = base_factor.inputs.copy()
        if 'close' not in adaptive_inputs:
            adaptive_inputs.append('close')

        # Add volatility-adaptive parameter output
        adaptive_outputs = base_factor.outputs.copy()
        adaptive_outputs.append(f'{param_name}_adaptive')

        # Create adaptive factor
        adaptive_factor = Factor(
            id=f"{base_factor.id}_vol_adaptive",
            name=f"{base_factor.name} (Vol-Adaptive)",
            category=base_factor.category,
            inputs=adaptive_inputs,
            outputs=adaptive_outputs,
            logic=adaptive_logic,
            parameters={
                **copy.deepcopy(base_factor.parameters),
                'volatility_period': volatility_period,
                'scale_factor': scale_factor,
                'adaptive_param': param_name,
            },
            description=f"{base_factor.description} [Volatility-adaptive {param_name}]"
        )

        return adaptive_factor

    def create_regime_adaptive(
        self,
        base_factor: Factor,
        param_name: str = None,
        bull_value: float = None,
        bear_value: float = None,
        regime_period: int = 50
    ) -> Factor:
        """
        Make factor parameters adapt to market regime.

        Creates a new factor where specified parameter changes based on
        market regime (bull/bear/sideways):
        - Bull market: Use bull_value
        - Bear market: Use bear_value
        - Sideways: Use base value

        Args:
            base_factor: Original factor to make adaptive
            param_name: Parameter name to adapt (if None, adapts first numeric param)
            bull_value: Parameter value in bull market (if None, uses base * 0.8)
            bear_value: Parameter value in bear market (if None, uses base * 1.2)
            regime_period: Period for regime detection (default: 50)

        Returns:
            New Factor with regime-adaptive parameter

        Example:
            >>> # Use shorter period in bull, longer in bear
            >>> adaptive = mutator.create_regime_adaptive(
            ...     base_factor=momentum_factor,
            ...     param_name="period",
            ...     bull_value=14,
            ...     bear_value=30
            ... )
        """
        # Determine which parameter to adapt
        if param_name is None:
            # Find first numeric parameter
            for name, value in base_factor.parameters.items():
                if isinstance(value, (int, float)):
                    param_name = name
                    break

        if param_name is None or param_name not in base_factor.parameters:
            raise ValueError(
                f"Parameter '{param_name}' not found in factor. "
                f"Available parameters: {list(base_factor.parameters.keys())}"
            )

        base_param_value = base_factor.parameters[param_name]

        # Set default bull/bear values
        if bull_value is None:
            bull_value = base_param_value * 0.8  # More aggressive
        if bear_value is None:
            bear_value = base_param_value * 1.2  # More conservative

        # Create adaptive logic
        def adaptive_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            # Detect market regime using SMA
            sma = data['close'].rolling(window=regime_period).mean()
            price = data['close']

            # Simple regime detection
            # Bull: price > SMA by >5%
            # Bear: price < SMA by >5%
            # Sideways: within 5% of SMA
            regime = pd.Series('sideways', index=data.index)
            regime[price > sma * 1.05] = 'bull'
            regime[price < sma * 0.95] = 'bear'

            # Map regime to parameter value
            param_values = pd.Series(base_param_value, index=data.index)
            param_values[regime == 'bull'] = bull_value
            param_values[regime == 'bear'] = bear_value

            # Store regime for reference
            data['regime'] = regime
            data[f'{param_name}_adaptive'] = param_values

            # Use median regime-specific value
            if isinstance(param_values, pd.Series):
                median_adaptive = param_values.median()
            else:
                median_adaptive = param_values

            # Ensure integer if base param was integer
            if isinstance(base_param_value, int):
                median_adaptive = int(round(median_adaptive))

            modified_params = params.copy()
            modified_params[param_name] = median_adaptive

            # Execute base factor logic with adaptive parameter
            result = base_factor.logic(data, modified_params)

            return result

        # Add 'close' to inputs if not present (needed for regime detection)
        adaptive_inputs = base_factor.inputs.copy()
        if 'close' not in adaptive_inputs:
            adaptive_inputs.append('close')

        # Add regime outputs
        adaptive_outputs = base_factor.outputs.copy()
        adaptive_outputs.extend(['regime', f'{param_name}_adaptive'])

        # Create adaptive factor
        adaptive_factor = Factor(
            id=f"{base_factor.id}_regime_adaptive",
            name=f"{base_factor.name} (Regime-Adaptive)",
            category=base_factor.category,
            inputs=adaptive_inputs,
            outputs=adaptive_outputs,
            logic=adaptive_logic,
            parameters={
                **copy.deepcopy(base_factor.parameters),
                'regime_period': regime_period,
                'bull_value': bull_value,
                'bear_value': bear_value,
                'adaptive_param': param_name,
            },
            description=f"{base_factor.description} [Regime-adaptive {param_name}]"
        )

        return adaptive_factor

    def create_bounded_adaptive(
        self,
        base_factor: Factor,
        param_name: str,
        min_value: float,
        max_value: float,
        adaptation_rate: float = 0.1
    ) -> Factor:
        """
        Create factor with bounded adaptive parameter.

        Parameter adapts gradually within bounds, useful for preventing
        extreme parameter values while allowing adaptation.

        Args:
            base_factor: Original factor
            param_name: Parameter to adapt
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            adaptation_rate: Rate of adaptation (0-1, default: 0.1)

        Returns:
            New Factor with bounded adaptive parameter

        Example:
            >>> # Keep RSI period between 10 and 30
            >>> adaptive = mutator.create_bounded_adaptive(
            ...     base_factor=rsi_factor,
            ...     param_name="period",
            ...     min_value=10,
            ...     max_value=30
            ... )
        """
        if param_name not in base_factor.parameters:
            raise ValueError(
                f"Parameter '{param_name}' not found in factor. "
                f"Available parameters: {list(base_factor.parameters.keys())}"
            )

        base_param_value = base_factor.parameters[param_name]

        # Ensure bounds are valid
        if min_value >= max_value:
            raise ValueError(f"min_value ({min_value}) must be less than max_value ({max_value})")

        if not (min_value <= base_param_value <= max_value):
            raise ValueError(
                f"Base parameter value ({base_param_value}) must be within bounds "
                f"[{min_value}, {max_value}]"
            )

        def adaptive_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            # Calculate volatility as adaptation signal
            returns = data['close'].pct_change()
            volatility = returns.rolling(window=20).std()

            # Normalize volatility to [0, 1]
            vol_min = volatility.min()
            vol_max = volatility.max()
            if vol_max > vol_min:
                norm_vol = (volatility - vol_min) / (vol_max - vol_min)
            else:
                norm_vol = pd.Series(0.5, index=data.index)

            # Adapt parameter based on normalized volatility
            # Higher volatility → move towards max_value
            # Lower volatility → move towards min_value
            adapted_param = min_value + norm_vol * (max_value - min_value)

            # Apply adaptation rate (smoothing)
            adapted_param = (
                base_param_value * (1 - adaptation_rate) +
                adapted_param * adaptation_rate
            )

            # Store adaptive parameter
            data[f'{param_name}_adaptive'] = adapted_param

            # Use median adaptive value
            if isinstance(adapted_param, pd.Series):
                median_adaptive = adapted_param.median()
            else:
                median_adaptive = adapted_param

            median_adaptive = max(min_value, min(max_value, median_adaptive))

            # Ensure integer if base param was integer
            if isinstance(base_param_value, int):
                median_adaptive = int(round(median_adaptive))

            modified_params = params.copy()
            modified_params[param_name] = median_adaptive

            # Execute base factor logic
            result = base_factor.logic(data, modified_params)

            return result

        # Add 'close' to inputs if not present
        adaptive_inputs = base_factor.inputs.copy()
        if 'close' not in adaptive_inputs:
            adaptive_inputs.append('close')

        # Add adaptive parameter output
        adaptive_outputs = base_factor.outputs.copy()
        adaptive_outputs.append(f'{param_name}_adaptive')

        # Create adaptive factor
        adaptive_factor = Factor(
            id=f"{base_factor.id}_bounded_adaptive",
            name=f"{base_factor.name} (Bounded-Adaptive)",
            category=base_factor.category,
            inputs=adaptive_inputs,
            outputs=adaptive_outputs,
            logic=adaptive_logic,
            parameters={
                **copy.deepcopy(base_factor.parameters),
                'min_value': min_value,
                'max_value': max_value,
                'adaptation_rate': adaptation_rate,
                'adaptive_param': param_name,
            },
            description=f"{base_factor.description} [Bounded-adaptive {param_name}]"
        )

        return adaptive_factor
