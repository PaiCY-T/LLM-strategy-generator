"""
Strategy Parameter Schemas for JSON Parameter Output Architecture

Pydantic schemas for validating LLM-generated strategy parameters.
These schemas enforce Literal types for constrained parameter values
and provide cross-parameter validation via model_validator.

Requirements: F1.1, F1.2, AC1
"""

from pydantic import BaseModel, Field, model_validator
from typing import Literal


class MomentumStrategyParams(BaseModel):
    """
    Pydantic schema for Momentum strategy parameters.

    All parameters use Literal types to constrain values to the exact
    options defined in MomentumTemplate.PARAM_GRID. This ensures the LLM
    can only select from valid parameter combinations.

    Attributes:
        momentum_period: Momentum lookback period in days (5, 10, 20, 30)
        ma_periods: Moving average period for trend confirmation (20, 60, 90, 120)
        catalyst_type: Fundamental catalyst type ('revenue' or 'earnings')
        catalyst_lookback: Catalyst lookback window in months (2, 3, 4, 6)
        n_stocks: Number of stocks in portfolio (5, 10, 15, 20)
        stop_loss: Stop loss percentage (0.08, 0.10, 0.12, 0.15)
        resample: Rebalancing frequency ('W' for Weekly, 'M' for Monthly)
        resample_offset: Rebalancing day offset (0, 1, 2, 3, 4)
    """

    # Momentum calculation
    momentum_period: Literal[5, 10, 20, 30] = Field(
        description="Momentum lookback period in days"
    )

    # Trend confirmation
    ma_periods: Literal[20, 60, 90, 120] = Field(
        description="Moving average period for trend confirmation"
    )

    # Catalyst type
    catalyst_type: Literal["revenue", "earnings"] = Field(
        description="Fundamental catalyst type"
    )

    # Catalyst detection
    catalyst_lookback: Literal[2, 3, 4, 6] = Field(
        description="Catalyst lookback window in months"
    )

    # Portfolio construction
    n_stocks: Literal[5, 10, 15, 20] = Field(
        description="Number of stocks in portfolio"
    )

    # Risk management
    stop_loss: Literal[0.08, 0.10, 0.12, 0.15] = Field(
        description="Stop loss percentage"
    )

    # Rebalancing
    resample: Literal["W", "M"] = Field(
        description="Rebalancing frequency (Weekly/Monthly)"
    )

    resample_offset: Literal[0, 1, 2, 3, 4] = Field(
        description="Rebalancing day offset"
    )

    @model_validator(mode='after')
    def validate_parameter_consistency(self) -> 'MomentumStrategyParams':
        """
        Cross-parameter validation for logical consistency.

        Validation Rules:
        1. momentum_period should be <= ma_periods for proper trend following
           (momentum calculation window should not exceed trend confirmation window)

        Returns:
            MomentumStrategyParams: The validated instance

        Raises:
            ValueError: If cross-parameter validation fails
        """
        # momentum_period should be shorter than or equal to ma_periods for trend following
        if self.momentum_period > self.ma_periods:
            raise ValueError(
                f"momentum_period ({self.momentum_period}) should be <= ma_periods ({self.ma_periods}) "
                "for proper trend confirmation"
            )
        return self


class StrategyParamRequest(BaseModel):
    """
    Schema for LLM JSON output format.

    This schema defines the complete structure expected from the LLM,
    including reasoning for parameter choices and the parameters themselves.

    Attributes:
        reasoning: Explanation for parameter choices (50-500 chars)
        params: The strategy parameters (validated MomentumStrategyParams)
    """

    reasoning: str = Field(
        min_length=50,
        max_length=500,
        description="Explanation for parameter choices"
    )

    params: MomentumStrategyParams = Field(
        description="Strategy parameters"
    )
