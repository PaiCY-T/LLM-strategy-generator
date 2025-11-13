"""
Pydantic Models for Strategy YAML Validation

Auto-generated from schemas/strategy_schema_v1.json with manual field validators.
Provides type-safe validation with detailed error messages.

Task 3 of yaml-normalizer-implementation spec.
Requirements: 2.1, 2.2, 2.3, 2.4
"""

from typing import Any, List, Optional, Union, Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


# ============================================================================
# ENUMS (Requirement 2.1)
# ============================================================================

StrategyType = Literal["momentum", "mean_reversion", "factor_combination"]
RebalancingFrequency = Literal["M", "W-FRI", "W-MON", "W-TUE", "W-WED", "W-THU", "Q"]
RiskLevel = Literal["low", "medium", "high", "very_high"]
IndicatorType = Literal[
    "RSI", "MACD", "BB", "SMA", "EMA", "ATR", "ADX",
    "Stochastic", "CCI", "Williams_R", "MFI", "OBV",
    "VWAP", "Momentum", "ROC", "TSI"
]
FundamentalField = Literal[
    "ROE", "ROA", "PB_ratio", "PE_ratio", "PS_ratio",
    "revenue_growth", "earnings_growth", "margin",
    "operating_margin", "net_margin", "debt_ratio",
    "debt_to_equity", "current_ratio", "quick_ratio",
    "cash_flow_to_debt", "dividend_yield", "payout_ratio",
    "asset_turnover", "inventory_turnover", "receivables_turnover"
]
RankingMethod = Literal["top_percent", "bottom_percent", "top_n", "bottom_n", "percentile_range"]
LogicalOperator = Literal["AND", "OR"]
PositionSizingMethod = Literal[
    "equal_weight", "factor_weighted", "risk_parity",
    "volatility_weighted", "custom_formula"
]


# ============================================================================
# INDICATOR MODELS
# ============================================================================

class TechnicalIndicator(BaseModel):
    """Technical analysis indicator configuration."""
    name: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    type: IndicatorType
    period: Optional[int] = Field(None, ge=1, le=250)
    source: Optional[str] = Field(None, pattern=r"^data\.get\(['\"].*['\"]\)$")
    fast_period: Optional[int] = Field(None, ge=1, le=100)
    slow_period: Optional[int] = Field(None, ge=1, le=250)
    signal_period: Optional[int] = Field(None, ge=1, le=100)
    std_dev: Optional[float] = Field(None, ge=0.1, le=5.0)

    class Config:
        extra = "allow"  # Allow additional fields

    @field_validator('type', mode='before')
    @classmethod
    def uppercase_type(cls, v: Any) -> str:
        """Double-insurance type conversion (requirement 2.2)."""
        if isinstance(v, str):
            return v.upper()
        return v


class FundamentalFactor(BaseModel):
    """Fundamental analysis factor configuration."""
    name: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    field: FundamentalField
    source: Optional[str] = Field(None, pattern=r"^data\.get\(['\"].*['\"]\)$")
    transformation: Optional[Literal["none", "log", "sqrt", "rank", "zscore", "winsorize"]] = "none"

    class Config:
        extra = "allow"


class CustomCalculation(BaseModel):
    """Custom calculated indicator configuration."""
    name: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    expression: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None

    class Config:
        extra = "allow"


class VolumeFilter(BaseModel):
    """Liquidity and volume-based filter configuration."""
    name: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    metric: Literal["average_volume", "dollar_volume", "turnover_ratio", "bid_ask_spread"]
    period: Optional[int] = Field(None, ge=1, le=250)
    threshold: Optional[float] = None

    class Config:
        extra = "allow"


class IndicatorsObject(BaseModel):
    """Indicators in structured object format."""
    technical_indicators: Optional[List[TechnicalIndicator]] = Field(default_factory=list, max_length=20)
    fundamental_factors: Optional[List[FundamentalFactor]] = Field(default_factory=list, max_length=15)
    custom_calculations: Optional[List[CustomCalculation]] = Field(default_factory=list, max_length=10)
    volume_filters: Optional[List[VolumeFilter]] = Field(default_factory=list)

    class Config:
        extra = "allow"


class IndicatorArrayItem(BaseModel):
    """Single indicator in simplified array format."""
    name: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    type: Optional[str] = None
    field: Optional[str] = None
    period: Optional[int] = Field(None, ge=1, le=250)
    source: Optional[str] = None
    expression: Optional[str] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


# ============================================================================
# CONDITION MODELS (Requirement 2.4 - Discriminated Unions)
# ============================================================================

class ThresholdRule(BaseModel):
    """Simple threshold-based rule."""
    condition: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None

    class Config:
        extra = "allow"


class RankingRule(BaseModel):
    """Ranking-based selection rule."""
    field: str = Field(..., pattern=r"^[a-z_][a-z0-9_]*$")
    method: RankingMethod
    value: Optional[float] = None
    ascending: bool = False
    percentile_min: Optional[float] = Field(None, ge=0, le=100)
    percentile_max: Optional[float] = Field(None, ge=0, le=100)

    class Config:
        extra = "allow"


class MinLiquidity(BaseModel):
    """Minimum liquidity requirements."""
    average_volume_20d: Optional[float] = Field(None, ge=0)
    dollar_volume: Optional[float] = Field(None, ge=0)


class EntryConditionsObject(BaseModel):
    """Entry conditions in object format."""
    threshold_rules: Optional[List[ThresholdRule]] = Field(default_factory=list, max_length=15)
    ranking_rules: Optional[List[RankingRule]] = Field(default_factory=list, max_length=5)
    logical_operator: LogicalOperator = "AND"
    min_liquidity: Optional[MinLiquidity] = None

    class Config:
        extra = "allow"


class EntryConditionArrayItem(BaseModel):
    """Single entry condition in array format."""
    condition: Optional[str] = None
    field: Optional[str] = Field(None, pattern=r"^[a-z_][a-z0-9_]*$")
    method: Optional[RankingMethod] = None
    value: Optional[float] = None
    description: Optional[str] = None

    class Config:
        extra = "allow"


class TrailingStop(BaseModel):
    """Trailing stop configuration."""
    trail_percent: float = Field(..., ge=0.01, le=0.30)
    activation_profit: Optional[float] = Field(None, ge=0, le=0.50)

    class Config:
        extra = "allow"


class ConditionalExit(BaseModel):
    """Indicator-based exit condition."""
    condition: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None

    class Config:
        extra = "allow"


class ExitConditionsObject(BaseModel):
    """Exit conditions in object format."""
    stop_loss_pct: Optional[float] = Field(None, gt=0.01, le=0.50)
    take_profit_pct: Optional[float] = Field(None, ge=0.05, le=2.0)
    trailing_stop: Optional[TrailingStop] = None
    holding_period_days: Optional[int] = Field(None, ge=1, le=365)
    conditional_exits: Optional[List[ConditionalExit]] = Field(default_factory=list, max_length=10)
    exit_operator: LogicalOperator = "OR"

    class Config:
        extra = "allow"


class ExitConditionArrayItem(BaseModel):
    """Single exit condition in array format."""
    condition: Optional[str] = None
    stop_loss_pct: Optional[float] = Field(None, ge=0.01, le=0.50)
    take_profit_pct: Optional[float] = Field(None, ge=0.05, le=2.0)
    description: Optional[str] = None

    class Config:
        extra = "allow"


# ============================================================================
# METADATA AND OTHER MODELS
# ============================================================================

class Metadata(BaseModel):
    """Strategy metadata and identification."""
    name: str = Field(..., min_length=5, max_length=100, pattern=r"^[A-Za-z0-9 _-]+$")
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    strategy_type: StrategyType
    rebalancing_frequency: RebalancingFrequency
    version: str = Field(default="1.0.0", pattern=r"^\d+\.\d+\.\d+$")
    author: str = "FinLab LLM System"
    tags: List[str] = Field(default_factory=list, max_length=10)
    risk_level: RiskLevel = "medium"

    class Config:
        extra = "allow"


class PositionSizing(BaseModel):
    """Position sizing and portfolio construction rules."""
    method: PositionSizingMethod
    max_positions: Optional[int] = Field(None, ge=1, le=100)
    max_position_pct: Optional[float] = Field(None, ge=0.01, le=1.0)
    min_position_pct: Optional[float] = Field(None, ge=0.001, le=0.50)
    weighting_field: Optional[str] = Field(None, pattern=r"^[a-z_][a-z0-9_]*$")
    custom_formula: Optional[str] = Field(None, min_length=3, max_length=500)

    class Config:
        extra = "allow"


class RiskManagement(BaseModel):
    """Portfolio-level risk management rules."""
    max_portfolio_volatility: Optional[float] = Field(None, ge=0.01, le=1.0)
    max_sector_exposure: Optional[float] = Field(None, ge=0.05, le=1.0)
    max_correlation: Optional[float] = Field(None, ge=-1.0, le=1.0)
    rebalance_threshold: Optional[float] = Field(None, ge=0.01, le=0.50)
    max_drawdown_limit: Optional[float] = Field(None, ge=0.05, le=0.50)
    cash_reserve_pct: float = Field(default=0, ge=0, le=0.50)

    class Config:
        extra = "allow"


class BacktestConfig(BaseModel):
    """Backtesting configuration parameters."""
    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    initial_capital: float = Field(default=1000000, ge=1000)
    transaction_cost: float = Field(default=0.001425, ge=0, le=0.10)
    slippage: float = Field(default=0.001, ge=0, le=0.05)

    class Config:
        extra = "allow"


# ============================================================================
# MAIN STRATEGY MODEL
# ============================================================================

class StrategySpecification(BaseModel):
    """
    Complete trading strategy specification.

    Validates LLM-generated YAML against schema with detailed error messages.
    """
    metadata: Metadata
    indicators: Union[IndicatorsObject, List[IndicatorArrayItem]]
    entry_conditions: Union[EntryConditionsObject, List[EntryConditionArrayItem]]
    exit_conditions: Optional[Union[ExitConditionsObject, List[ExitConditionArrayItem]]] = None
    position_sizing: Optional[PositionSizing] = None
    risk_management: Optional[RiskManagement] = None
    backtest_config: Optional[BacktestConfig] = None

    class Config:
        extra = "allow"

    @model_validator(mode='after')
    def validate_indicator_references(self) -> 'StrategySpecification':
        """Validate that ranking fields reference defined indicators (requirement 2.3)."""
        # Collect all defined indicator names
        defined_indicators = set()

        if isinstance(self.indicators, IndicatorsObject):
            for ind in self.indicators.technical_indicators or []:
                defined_indicators.add(ind.name)
            for fac in self.indicators.fundamental_factors or []:
                defined_indicators.add(fac.name)
            for calc in self.indicators.custom_calculations or []:
                defined_indicators.add(calc.name)
        elif isinstance(self.indicators, list):
            for ind in self.indicators:
                defined_indicators.add(ind.name)

        # Check entry conditions ranking rules
        if isinstance(self.entry_conditions, EntryConditionsObject):
            for rule in self.entry_conditions.ranking_rules or []:
                if rule.field not in defined_indicators:
                    raise ValueError(
                        f"entry_conditions.ranking_rules: Field '{rule.field}' not found in indicators. "
                        f"Available indicators: {sorted(defined_indicators)}"
                    )

        # Check position sizing weighting field
        if self.position_sizing and self.position_sizing.method == "factor_weighted":
            if self.position_sizing.weighting_field:
                if self.position_sizing.weighting_field not in defined_indicators:
                    raise ValueError(
                        f"position_sizing.weighting_field: Field '{self.position_sizing.weighting_field}' "
                        f"not found in indicators. Available indicators: {sorted(defined_indicators)}"
                    )

        return self
