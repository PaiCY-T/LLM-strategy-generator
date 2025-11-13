"""
Signal Combiner - Create composite factors by combining signals.

Enables creation of complex trading signals by combining multiple
factors using logical operations (AND, OR) or weighted combinations.

Part of Tier 3 AST Mutation Framework.
Task: D.3 - AST-Based Factor Logic Mutation
"""

from typing import Dict, Any, List, Callable
import pandas as pd
import copy

from src.factor_graph.factor import Factor
from src.factor_graph.factor_category import FactorCategory


class SignalCombiner:
    """
    Create composite factors by combining signals.

    Combination Types:
    -----------------
    1. AND Combination: signal1 & signal2 (both must be true)
    2. OR Combination: signal1 | signal2 (either must be true)
    3. Weighted Combination: w1*signal1 + w2*signal2 (linear combination)
    4. Conditional: signal1 if condition else signal2

    Example Usage:
    -------------
    ```python
    combiner = SignalCombiner()

    # AND combination (RSI and MACD both bullish)
    composite = combiner.combine_and(rsi_factor, macd_factor)

    # OR combination (RSI or MACD bullish)
    composite = combiner.combine_or(rsi_factor, macd_factor)

    # Weighted combination (60% RSI, 40% MACD)
    composite = combiner.combine_weighted(
        [rsi_factor, macd_factor],
        [0.6, 0.4]
    )
    ```

    Design Notes:
    ------------
    - Input factors must have compatible outputs (signals)
    - Output signals are combined using specified logic
    - Dependencies are merged (union of inputs)
    - New factor inherits highest category priority (SIGNAL > EXIT > ...)
    """

    def combine_and(self, factor1: Factor, factor2: Factor) -> Factor:
        """
        Create AND combination factor.

        Combines two factors using logical AND: output is True only if
        both factors produce True signals.

        Args:
            factor1: First factor
            factor2: Second factor

        Returns:
            New Factor with AND combination logic

        Raises:
            ValueError: If factors have incompatible outputs

        Example:
            >>> # Require both RSI and MACD to be bullish
            >>> composite = combiner.combine_and(rsi_factor, macd_factor)
        """
        # Validate factors have compatible outputs
        self._validate_combination(factor1, factor2)

        # Create combined logic
        def combined_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            # Execute first factor
            result = factor1.execute(data)

            # Execute second factor
            result = factor2.execute(result)

            # Combine outputs using AND
            # Assume last output of each factor is the signal
            signal1_col = factor1.outputs[-1]
            signal2_col = factor2.outputs[-1]

            # Create combined signal column
            combined_col = f"{signal1_col}_and_{signal2_col}"
            result[combined_col] = result[signal1_col] & result[signal2_col]

            return result

        # Merge inputs (union)
        combined_inputs = list(set(factor1.inputs + factor2.inputs))

        # Merge outputs
        combined_outputs = factor1.outputs + factor2.outputs
        combined_signal = f"{factor1.outputs[-1]}_and_{factor2.outputs[-1]}"
        combined_outputs.append(combined_signal)

        # Create composite factor
        composite = Factor(
            id=f"{factor1.id}_and_{factor2.id}",
            name=f"{factor1.name} AND {factor2.name}",
            category=self._select_category(factor1.category, factor2.category),
            inputs=combined_inputs,
            outputs=combined_outputs,
            logic=combined_logic,
            parameters={
                "factor1_params": copy.deepcopy(factor1.parameters),
                "factor2_params": copy.deepcopy(factor2.parameters),
            },
            description=f"AND combination of {factor1.name} and {factor2.name}"
        )

        return composite

    def combine_or(self, factor1: Factor, factor2: Factor) -> Factor:
        """
        Create OR combination factor.

        Combines two factors using logical OR: output is True if
        either factor produces True signal.

        Args:
            factor1: First factor
            factor2: Second factor

        Returns:
            New Factor with OR combination logic

        Raises:
            ValueError: If factors have incompatible outputs

        Example:
            >>> # Trigger if either RSI or MACD is bullish
            >>> composite = combiner.combine_or(rsi_factor, macd_factor)
        """
        # Validate factors have compatible outputs
        self._validate_combination(factor1, factor2)

        # Create combined logic
        def combined_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            # Execute first factor
            result = factor1.execute(data)

            # Execute second factor
            result = factor2.execute(result)

            # Combine outputs using OR
            signal1_col = factor1.outputs[-1]
            signal2_col = factor2.outputs[-1]

            # Create combined signal column
            combined_col = f"{signal1_col}_or_{signal2_col}"
            result[combined_col] = result[signal1_col] | result[signal2_col]

            return result

        # Merge inputs (union)
        combined_inputs = list(set(factor1.inputs + factor2.inputs))

        # Merge outputs
        combined_outputs = factor1.outputs + factor2.outputs
        combined_signal = f"{factor1.outputs[-1]}_or_{factor2.outputs[-1]}"
        combined_outputs.append(combined_signal)

        # Create composite factor
        composite = Factor(
            id=f"{factor1.id}_or_{factor2.id}",
            name=f"{factor1.name} OR {factor2.name}",
            category=self._select_category(factor1.category, factor2.category),
            inputs=combined_inputs,
            outputs=combined_outputs,
            logic=combined_logic,
            parameters={
                "factor1_params": copy.deepcopy(factor1.parameters),
                "factor2_params": copy.deepcopy(factor2.parameters),
            },
            description=f"OR combination of {factor1.name} and {factor2.name}"
        )

        return composite

    def combine_weighted(
        self,
        factors: List[Factor],
        weights: List[float]
    ) -> Factor:
        """
        Create weighted combination factor.

        Combines multiple factors using weighted sum:
        output = w1*signal1 + w2*signal2 + ... + wn*signaln

        Useful for creating ensemble signals.

        Args:
            factors: List of factors to combine
            weights: Corresponding weights (should sum to 1.0)

        Returns:
            New Factor with weighted combination logic

        Raises:
            ValueError: If factors and weights have different lengths
            ValueError: If weights don't sum to approximately 1.0
            ValueError: If factors have incompatible outputs

        Example:
            >>> # 60% RSI, 40% MACD
            >>> composite = combiner.combine_weighted(
            ...     [rsi_factor, macd_factor],
            ...     [0.6, 0.4]
            ... )
        """
        # Validate inputs
        if len(factors) != len(weights):
            raise ValueError(
                f"Number of factors ({len(factors)}) must match "
                f"number of weights ({len(weights)})"
            )

        if len(factors) < 2:
            raise ValueError("Need at least 2 factors for weighted combination")

        # Validate weights sum to ~1.0
        weight_sum = sum(weights)
        if not (0.99 <= weight_sum <= 1.01):
            raise ValueError(
                f"Weights should sum to 1.0, got {weight_sum}. "
                "Tip: Normalize weights before passing."
            )

        # Validate all factors have compatible outputs
        for i in range(len(factors) - 1):
            self._validate_combination(factors[i], factors[i + 1])

        # Create combined logic
        def combined_logic(data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
            result = data.copy()

            # Execute all factors
            signal_columns = []
            for factor in factors:
                result = factor.execute(result)
                signal_columns.append(factor.outputs[-1])

            # Create weighted combination
            combined_col = "_weighted_".join([f.id for f in factors])
            result[combined_col] = 0.0

            for signal_col, weight in zip(signal_columns, weights):
                result[combined_col] += weight * result[signal_col]

            return result

        # Merge inputs (union)
        all_inputs = []
        for factor in factors:
            all_inputs.extend(factor.inputs)
        combined_inputs = list(set(all_inputs))

        # Merge outputs
        combined_outputs = []
        for factor in factors:
            combined_outputs.extend(factor.outputs)
        weighted_signal = "_weighted_".join([f.id for f in factors])
        combined_outputs.append(weighted_signal)

        # Create composite factor
        factor_names = " + ".join(
            [f"{w:.2f}*{f.name}" for f, w in zip(factors, weights)]
        )

        composite = Factor(
            id="_".join([f.id for f in factors]),
            name=f"Weighted: {factor_names}",
            category=self._select_category(*[f.category for f in factors]),
            inputs=combined_inputs,
            outputs=combined_outputs,
            logic=combined_logic,
            parameters={
                f"factor{i}_params": copy.deepcopy(f.parameters)
                for i, f in enumerate(factors)
            },
            description=f"Weighted combination: {factor_names}"
        )

        return composite

    def _validate_combination(self, factor1: Factor, factor2: Factor) -> None:
        """
        Validate that two factors can be combined.

        Args:
            factor1: First factor
            factor2: Second factor

        Raises:
            ValueError: If factors have incompatible outputs
        """
        # Check if factors produce outputs (required for combination)
        if not factor1.outputs or not factor2.outputs:
            raise ValueError(
                f"Both factors must produce outputs for combination. "
                f"Factor1 outputs: {factor1.outputs}, "
                f"Factor2 outputs: {factor2.outputs}"
            )

        # Note: We don't enforce output type compatibility here
        # because factors can produce different types of signals
        # (boolean, float, etc.). The combination logic handles this.

    def _select_category(self, *categories: FactorCategory) -> FactorCategory:
        """
        Select category for composite factor.

        Priority order: SIGNAL > EXIT > ENTRY > MOMENTUM > VALUE > QUALITY > RISK

        Args:
            categories: Factor categories to choose from

        Returns:
            Highest priority category
        """
        priority_order = [
            FactorCategory.SIGNAL,
            FactorCategory.EXIT,
            FactorCategory.ENTRY,
            FactorCategory.MOMENTUM,
            FactorCategory.VALUE,
            FactorCategory.QUALITY,
            FactorCategory.RISK,
        ]

        for priority_cat in priority_order:
            if priority_cat in categories:
                return priority_cat

        # Fallback to first category
        return categories[0]
