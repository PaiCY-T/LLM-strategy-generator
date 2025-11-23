"""
Tests for Strategy Configuration Data Structures

Task: 18.3 - Define StrategyConfig Data Structure
Tests comprehensive validation of all strategy config dataclasses:
- FieldMapping: canonical name, alias, usage validation
- ParameterConfig: type validation, range checking, value validation
- LogicConfig: entry/exit logic and dependency validation
- ConstraintConfig: severity levels and constraint types
- StrategyConfig: complete configuration validation and integration

Integration:
    - Layer 1: FieldMetadata canonical names
    - YAML schema: src/config/strategy_schema.yaml patterns
"""

import pytest
from src.execution.strategy_config import (
    FieldMapping,
    ParameterConfig,
    LogicConfig,
    ConstraintConfig,
    StrategyConfig,
)


class TestFieldMapping:
    """Test suite for FieldMapping dataclass."""

    def test_valid_field_mapping(self):
        """Test creating valid FieldMapping."""
        field = FieldMapping(
            canonical_name="price:收盤價",
            alias="close",
            usage="Signal generation - momentum calculation"
        )

        assert field.canonical_name == "price:收盤價"
        assert field.alias == "close"
        assert field.usage == "Signal generation - momentum calculation"

    def test_field_mapping_with_volume(self):
        """Test FieldMapping with volume field (critical field)."""
        field = FieldMapping(
            canonical_name="price:成交金額",
            alias="volume",
            usage="Volume filtering - minimum liquidity requirement"
        )

        assert field.canonical_name == "price:成交金額"
        assert field.alias == "volume"

    def test_empty_canonical_name_raises(self):
        """Test that empty canonical_name raises ValueError."""
        with pytest.raises(ValueError, match="canonical_name must be a non-empty string"):
            FieldMapping(
                canonical_name="",
                alias="close",
                usage="Test usage"
            )

    def test_none_canonical_name_raises(self):
        """Test that None canonical_name raises ValueError."""
        with pytest.raises(ValueError, match="canonical_name must be a non-empty string"):
            FieldMapping(
                canonical_name=None,
                alias="close",
                usage="Test usage"
            )

    def test_empty_alias_raises(self):
        """Test that empty alias raises ValueError."""
        with pytest.raises(ValueError, match="alias must be a non-empty string"):
            FieldMapping(
                canonical_name="price:收盤價",
                alias="",
                usage="Test usage"
            )

    def test_empty_usage_raises(self):
        """Test that empty usage raises ValueError."""
        with pytest.raises(ValueError, match="usage must be a non-empty string"):
            FieldMapping(
                canonical_name="price:收盤價",
                alias="close",
                usage=""
            )


class TestParameterConfig:
    """Test suite for ParameterConfig dataclass."""

    def test_valid_integer_parameter(self):
        """Test creating valid integer parameter."""
        param = ParameterConfig(
            name="momentum_period",
            type="integer",
            value=20,
            default=20,
            range=(10, 60),
            unit="trading_days"
        )

        assert param.name == "momentum_period"
        assert param.type == "integer"
        assert param.value == 20
        assert param.default == 20
        assert param.range == (10, 60)
        assert param.unit == "trading_days"
        assert param.is_in_range()

    def test_valid_float_parameter(self):
        """Test creating valid float parameter."""
        param = ParameterConfig(
            name="entry_threshold",
            type="float",
            value=0.02,
            default=0.02,
            range=(0.01, 0.10),
            unit="percentage"
        )

        assert param.type == "float"
        assert param.value == 0.02
        assert param.is_in_range()

    def test_valid_boolean_parameter(self):
        """Test creating valid boolean parameter."""
        param = ParameterConfig(
            name="regime_detection",
            type="boolean",
            value=True,
            default=True,
            range=None,
            unit=None
        )

        assert param.type == "boolean"
        assert param.value is True

    def test_valid_string_parameter(self):
        """Test creating valid string parameter."""
        param = ParameterConfig(
            name="strategy_mode",
            type="string",
            value="aggressive",
            default="balanced",
            range=None,
            unit=None
        )

        assert param.type == "string"
        assert param.value == "aggressive"

    def test_invalid_type_raises(self):
        """Test that invalid type raises ValueError."""
        with pytest.raises(ValueError, match="type must be one of"):
            ParameterConfig(
                name="test",
                type="invalid_type",
                value=10,
                default=10
            )

    def test_missing_range_for_integer_raises(self):
        """Test that missing range for integer type raises ValueError."""
        with pytest.raises(ValueError, match="range is required for numeric type"):
            ParameterConfig(
                name="test",
                type="integer",
                value=10,
                default=10,
                range=None
            )

    def test_missing_range_for_float_raises(self):
        """Test that missing range for float type raises ValueError."""
        with pytest.raises(ValueError, match="range is required for numeric type"):
            ParameterConfig(
                name="test",
                type="float",
                value=0.5,
                default=0.5,
                range=None
            )

    def test_invalid_range_format_raises(self):
        """Test that invalid range format raises ValueError."""
        with pytest.raises(ValueError, match="range must be a tuple"):
            ParameterConfig(
                name="test",
                type="integer",
                value=10,
                default=10,
                range=[1, 100]  # List instead of tuple
            )

    def test_range_min_greater_than_max_raises(self):
        """Test that min >= max in range raises ValueError."""
        with pytest.raises(ValueError, match="range min must be less than max"):
            ParameterConfig(
                name="test",
                type="integer",
                value=10,
                default=10,
                range=(100, 1)  # Reversed range
            )

    def test_value_out_of_range_raises(self):
        """Test that value outside range raises ValueError."""
        with pytest.raises(ValueError, match="value .* is not in valid range"):
            ParameterConfig(
                name="test",
                type="integer",
                value=150,  # Outside range
                default=10,
                range=(1, 100)
            )

    def test_value_type_mismatch_raises(self):
        """Test that value type mismatch raises ValueError."""
        with pytest.raises(ValueError, match="value .* does not match type"):
            ParameterConfig(
                name="test",
                type="integer",
                value=10.5,  # Float for integer type
                default=10,
                range=(1, 100)
            )

    def test_default_type_mismatch_raises(self):
        """Test that default type mismatch raises ValueError."""
        with pytest.raises(ValueError, match="default .* does not match type"):
            ParameterConfig(
                name="test",
                type="integer",
                value=10,
                default=10.5,  # Float for integer type
                range=(1, 100)
            )

    def test_validate_type_integer(self):
        """Test validate_type for integer parameters."""
        param = ParameterConfig(
            name="test",
            type="integer",
            value=10,
            default=10,
            range=(1, 100)
        )

        assert param.validate_type(20) is True
        assert param.validate_type(20.5) is False
        assert param.validate_type("20") is False
        assert param.validate_type(True) is False  # Boolean is not integer

    def test_validate_type_float(self):
        """Test validate_type for float parameters."""
        param = ParameterConfig(
            name="test",
            type="float",
            value=0.5,
            default=0.5,
            range=(0.0, 1.0)
        )

        assert param.validate_type(0.75) is True
        assert param.validate_type(10) is True  # Integer accepted for float
        assert param.validate_type("0.5") is False
        assert param.validate_type(True) is False

    def test_validate_type_boolean(self):
        """Test validate_type for boolean parameters."""
        param = ParameterConfig(
            name="test",
            type="boolean",
            value=True,
            default=False
        )

        assert param.validate_type(True) is True
        assert param.validate_type(False) is True
        assert param.validate_type(1) is False  # Integer not boolean
        assert param.validate_type("True") is False

    def test_is_in_range_within_bounds(self):
        """Test is_in_range for value within bounds."""
        param = ParameterConfig(
            name="test",
            type="integer",
            value=50,
            default=50,
            range=(1, 100)
        )

        assert param.is_in_range() is True

    def test_is_in_range_at_boundaries(self):
        """Test is_in_range at exact boundaries."""
        param_min = ParameterConfig(
            name="test",
            type="integer",
            value=1,
            default=1,
            range=(1, 100)
        )
        param_max = ParameterConfig(
            name="test",
            type="integer",
            value=100,
            default=100,
            range=(1, 100)
        )

        assert param_min.is_in_range() is True
        assert param_max.is_in_range() is True


class TestLogicConfig:
    """Test suite for LogicConfig dataclass."""

    def test_valid_logic_config(self):
        """Test creating valid LogicConfig."""
        logic = LogicConfig(
            entry="(price.pct_change(20) > 0.02) & (volume > 1000000)",
            exit="price < peak_price * 0.9",
            dependencies=["price:收盤價", "price:成交金額"]
        )

        assert logic.entry == "(price.pct_change(20) > 0.02) & (volume > 1000000)"
        assert logic.exit == "price < peak_price * 0.9"
        assert len(logic.dependencies) == 2
        assert "price:收盤價" in logic.dependencies

    def test_logic_config_with_no_exit(self):
        """Test LogicConfig with no exit logic."""
        logic = LogicConfig(
            entry="close > sma",
            exit="None",
            dependencies=["price:收盤價"]
        )

        assert logic.exit == "None"

    def test_logic_config_with_empty_exit(self):
        """Test LogicConfig with empty exit string."""
        logic = LogicConfig(
            entry="close > sma",
            exit="",
            dependencies=["price:收盤價"]
        )

        assert logic.exit == ""

    def test_empty_entry_raises(self):
        """Test that empty entry raises ValueError."""
        with pytest.raises(ValueError, match="entry must be a non-empty string"):
            LogicConfig(
                entry="",
                exit="None",
                dependencies=[]
            )

    def test_none_entry_raises(self):
        """Test that None entry raises ValueError."""
        with pytest.raises(ValueError, match="entry must be a non-empty string"):
            LogicConfig(
                entry=None,
                exit="None",
                dependencies=[]
            )

    def test_invalid_exit_type_raises(self):
        """Test that non-string exit raises ValueError."""
        with pytest.raises(ValueError, match="exit must be a string"):
            LogicConfig(
                entry="close > sma",
                exit=None,
                dependencies=[]
            )

    def test_invalid_dependencies_type_raises(self):
        """Test that non-list dependencies raises ValueError."""
        with pytest.raises(ValueError, match="dependencies must be a list"):
            LogicConfig(
                entry="close > sma",
                exit="None",
                dependencies="price:收盤價"  # String instead of list
            )

    def test_non_string_dependency_raises(self):
        """Test that non-string dependency items raise ValueError."""
        with pytest.raises(ValueError, match="all dependencies must be strings"):
            LogicConfig(
                entry="close > sma",
                exit="None",
                dependencies=["price:收盤價", 123]  # Number in list
            )

    def test_empty_dependency_string_raises(self):
        """Test that empty dependency strings raise ValueError."""
        with pytest.raises(ValueError, match="dependencies cannot contain empty strings"):
            LogicConfig(
                entry="close > sma",
                exit="None",
                dependencies=["price:收盤價", ""]  # Empty string
            )


class TestConstraintConfig:
    """Test suite for ConstraintConfig dataclass."""

    def test_valid_constraint_config(self):
        """Test creating valid ConstraintConfig."""
        constraint = ConstraintConfig(
            type="parameter",
            condition="momentum_period > 0",
            severity="critical",
            message="Momentum period must be positive"
        )

        assert constraint.type == "parameter"
        assert constraint.condition == "momentum_period > 0"
        assert constraint.severity == "critical"
        assert constraint.message == "Momentum period must be positive"
        assert constraint.tolerance == 0.0

    def test_constraint_with_tolerance(self):
        """Test ConstraintConfig with tolerance."""
        constraint = ConstraintConfig(
            type="parameter",
            condition="weight_sum == 1.0",
            severity="critical",
            tolerance=0.01
        )

        assert constraint.tolerance == 0.01

    def test_constraint_with_max_nan_pct(self):
        """Test ConstraintConfig with max_nan_pct."""
        constraint = ConstraintConfig(
            type="data_quality",
            condition="NaN check",
            severity="critical",
            max_nan_pct=0.05
        )

        assert constraint.max_nan_pct == 0.05

    def test_invalid_constraint_type_raises(self):
        """Test that invalid constraint type raises ValueError."""
        with pytest.raises(ValueError, match="type must be one of"):
            ConstraintConfig(
                type="invalid_type",
                condition="test",
                severity="critical"
            )

    def test_invalid_severity_raises(self):
        """Test that invalid severity raises ValueError."""
        with pytest.raises(ValueError, match="severity must be one of"):
            ConstraintConfig(
                type="parameter",
                condition="test",
                severity="invalid_severity"
            )

    def test_empty_condition_raises(self):
        """Test that empty condition raises ValueError."""
        with pytest.raises(ValueError, match="condition must be a non-empty string"):
            ConstraintConfig(
                type="parameter",
                condition="",
                severity="critical"
            )

    def test_negative_tolerance_raises(self):
        """Test that negative tolerance raises ValueError."""
        with pytest.raises(ValueError, match="tolerance must be non-negative"):
            ConstraintConfig(
                type="parameter",
                condition="test",
                severity="critical",
                tolerance=-0.01
            )

    def test_invalid_max_nan_pct_raises(self):
        """Test that invalid max_nan_pct raises ValueError."""
        with pytest.raises(ValueError, match="max_nan_pct must be in"):
            ConstraintConfig(
                type="data_quality",
                condition="test",
                severity="critical",
                max_nan_pct=1.5  # > 1.0
            )

    def test_negative_max_nan_pct_raises(self):
        """Test that negative max_nan_pct raises ValueError."""
        with pytest.raises(ValueError, match="max_nan_pct must be in"):
            ConstraintConfig(
                type="data_quality",
                condition="test",
                severity="critical",
                max_nan_pct=-0.1
            )


class TestStrategyConfig:
    """Test suite for StrategyConfig dataclass."""

    def test_valid_strategy_config(self):
        """Test creating valid complete StrategyConfig."""
        config = StrategyConfig(
            name="Pure Momentum",
            type="momentum",
            description="Fast breakout strategy using price momentum",
            fields=[
                FieldMapping(
                    canonical_name="price:收盤價",
                    alias="close",
                    usage="Signal generation - momentum calculation"
                ),
                FieldMapping(
                    canonical_name="price:成交金額",
                    alias="volume",
                    usage="Volume filtering - minimum liquidity"
                )
            ],
            parameters=[
                ParameterConfig(
                    name="momentum_period",
                    type="integer",
                    value=20,
                    default=20,
                    range=(10, 60),
                    unit="trading_days"
                ),
                ParameterConfig(
                    name="entry_threshold",
                    type="float",
                    value=0.02,
                    default=0.02,
                    range=(0.01, 0.10),
                    unit="percentage"
                )
            ],
            logic=LogicConfig(
                entry="(price.pct_change(momentum_period) > entry_threshold) & (volume > min_volume)",
                exit="None",
                dependencies=["price:收盤價", "price:成交金額"]
            ),
            constraints=[
                ConstraintConfig(
                    type="data_quality",
                    condition="No NaN values in price field",
                    severity="critical"
                ),
                ConstraintConfig(
                    type="parameter",
                    condition="momentum_period < total_backtest_days",
                    severity="critical"
                )
            ],
            coverage=0.18
        )

        assert config.name == "Pure Momentum"
        assert config.type == "momentum"
        assert len(config.fields) == 2
        assert len(config.parameters) == 2
        assert len(config.constraints) == 2
        assert config.coverage == 0.18

    def test_empty_name_raises(self):
        """Test that empty name raises ValueError."""
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            StrategyConfig(
                name="",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[]
            )

    def test_empty_type_raises(self):
        """Test that empty type raises ValueError."""
        with pytest.raises(ValueError, match="type must be a non-empty string"):
            StrategyConfig(
                name="Test Strategy",
                type="",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[]
            )

    def test_empty_fields_raises(self):
        """Test that empty fields list raises ValueError."""
        with pytest.raises(ValueError, match="fields must be a non-empty list"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[],  # Empty list
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[]
            )

    def test_invalid_field_type_raises(self):
        """Test that non-FieldMapping in fields raises ValueError."""
        with pytest.raises(ValueError, match="all fields must be FieldMapping objects"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=["invalid"],  # String instead of FieldMapping
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[]
            )

    def test_invalid_parameter_type_raises(self):
        """Test that non-ParameterConfig in parameters raises ValueError."""
        with pytest.raises(ValueError, match="all parameters must be ParameterConfig objects"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=["invalid"],  # String instead of ParameterConfig
                logic=LogicConfig("test", "None", []),
                constraints=[]
            )

    def test_invalid_logic_type_raises(self):
        """Test that non-LogicConfig for logic raises ValueError."""
        with pytest.raises(ValueError, match="logic must be a LogicConfig object"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic="invalid",  # String instead of LogicConfig
                constraints=[]
            )

    def test_invalid_constraint_type_raises(self):
        """Test that non-ConstraintConfig in constraints raises ValueError."""
        with pytest.raises(ValueError, match="all constraints must be ConstraintConfig objects"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=["invalid"]  # String instead of ConstraintConfig
            )

    def test_invalid_coverage_raises(self):
        """Test that coverage outside [0, 1] raises ValueError."""
        with pytest.raises(ValueError, match="coverage must be in"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[],
                coverage=1.5  # > 1.0
            )

    def test_get_required_fields(self):
        """Test get_required_fields method."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[
                FieldMapping("price:收盤價", "close", "test"),
                FieldMapping("price:成交金額", "volume", "test"),
                FieldMapping("fundamental_features:ROE", "roe", "test")
            ],
            parameters=[],
            logic=LogicConfig("test", "None", []),
            constraints=[]
        )

        required = config.get_required_fields()
        assert len(required) == 3
        assert "price:收盤價" in required
        assert "price:成交金額" in required
        assert "fundamental_features:ROE" in required

    def test_get_parameter_by_name(self):
        """Test get_parameter_by_name method."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[FieldMapping("price:收盤價", "close", "test")],
            parameters=[
                ParameterConfig("momentum_period", "integer", 20, 20, (10, 60)),
                ParameterConfig("threshold", "float", 0.02, 0.02, (0.01, 0.1))
            ],
            logic=LogicConfig("test", "None", []),
            constraints=[]
        )

        param = config.get_parameter_by_name("momentum_period")
        assert param is not None
        assert param.value == 20

        param_none = config.get_parameter_by_name("nonexistent")
        assert param_none is None

    def test_get_critical_constraints(self):
        """Test get_critical_constraints method."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[FieldMapping("price:收盤價", "close", "test")],
            parameters=[],
            logic=LogicConfig("test", "None", []),
            constraints=[
                ConstraintConfig("parameter", "test1", "critical"),
                ConstraintConfig("data_quality", "test2", "warning"),
                ConstraintConfig("logic", "test3", "critical")
            ]
        )

        critical = config.get_critical_constraints()
        assert len(critical) == 2
        assert all(c.severity == "critical" for c in critical)

    def test_validate_dependencies_satisfied(self):
        """Test validate_dependencies when all deps satisfied."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[
                FieldMapping("price:收盤價", "close", "test"),
                FieldMapping("price:成交金額", "volume", "test")
            ],
            parameters=[],
            logic=LogicConfig(
                entry="test",
                exit="None",
                dependencies=["price:收盤價", "price:成交金額"]
            ),
            constraints=[]
        )

        assert config.validate_dependencies() is True

    def test_validate_dependencies_missing(self):
        """Test validate_dependencies when deps missing."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[
                FieldMapping("price:收盤價", "close", "test")
            ],
            parameters=[],
            logic=LogicConfig(
                entry="test",
                exit="None",
                dependencies=["price:收盤價", "price:成交金額"]  # volume missing
            ),
            constraints=[]
        )

        assert config.validate_dependencies() is False

    def test_strategy_with_metadata(self):
        """Test StrategyConfig with optional metadata."""
        config = StrategyConfig(
            name="Test Strategy",
            type="momentum",
            description="Test",
            fields=[FieldMapping("price:收盤價", "close", "test")],
            parameters=[],
            logic=LogicConfig("test", "None", []),
            constraints=[],
            metadata={
                "author": "FinLab LLM System",
                "version": "1.0.0",
                "tags": ["momentum", "technical"]
            }
        )

        assert config.metadata is not None
        assert config.metadata["author"] == "FinLab LLM System"
        assert "momentum" in config.metadata["tags"]

    def test_invalid_metadata_type_raises(self):
        """Test that non-dict metadata raises ValueError."""
        with pytest.raises(ValueError, match="metadata must be a dictionary"):
            StrategyConfig(
                name="Test Strategy",
                type="momentum",
                description="Test",
                fields=[FieldMapping("price:收盤價", "close", "test")],
                parameters=[],
                logic=LogicConfig("test", "None", []),
                constraints=[],
                metadata="invalid"  # String instead of dict
            )


class TestIntegrationWithLayer1:
    """Integration tests with Layer 1 field manifest."""

    def test_pure_momentum_pattern_config(self):
        """Test complete Pure Momentum pattern from schema."""
        config = StrategyConfig(
            name="Pure Momentum",
            type="momentum",
            description="Fast breakout strategy using price momentum with rolling mean returns",
            fields=[
                FieldMapping(
                    canonical_name="price:收盤價",
                    alias="close",
                    usage="Signal generation - momentum calculation"
                ),
                FieldMapping(
                    canonical_name="price:成交金額",
                    alias="volume",
                    usage="Volume filtering - minimum liquidity requirement"
                )
            ],
            parameters=[
                ParameterConfig(
                    name="momentum_period",
                    type="integer",
                    value=20,
                    default=20,
                    range=(10, 60),
                    unit="trading_days"
                ),
                ParameterConfig(
                    name="entry_threshold",
                    type="float",
                    value=0.02,
                    default=0.02,
                    range=(0.01, 0.10),
                    unit="percentage"
                ),
                ParameterConfig(
                    name="min_volume",
                    type="float",
                    value=1000000.0,
                    default=1000000.0,
                    range=(100000.0, 10000000.0),
                    unit="currency"
                )
            ],
            logic=LogicConfig(
                entry="(price.pct_change(momentum_period).rolling(5).mean() > entry_threshold) & (volume > min_volume)",
                exit="None",
                dependencies=["price:收盤價", "price:成交金額"]
            ),
            constraints=[
                ConstraintConfig(
                    type="data_quality",
                    condition="No NaN values in price field",
                    severity="critical"
                ),
                ConstraintConfig(
                    type="parameter",
                    condition="momentum_period < total_backtest_days",
                    severity="critical"
                ),
                ConstraintConfig(
                    type="performance",
                    condition="min_volume filter must exclude <5% of universe",
                    severity="warning"
                )
            ],
            coverage=0.18
        )

        # Validate structure
        assert config.name == "Pure Momentum"
        assert config.type == "momentum"
        assert len(config.fields) == 2
        assert len(config.parameters) == 3
        assert len(config.constraints) == 3

        # Validate methods
        assert config.validate_dependencies() is True
        required_fields = config.get_required_fields()
        assert "price:收盤價" in required_fields
        assert "price:成交金額" in required_fields

        # Validate parameters
        momentum_param = config.get_parameter_by_name("momentum_period")
        assert momentum_param is not None
        assert momentum_param.value == 20
        assert momentum_param.is_in_range()

        # Validate critical constraints
        critical = config.get_critical_constraints()
        assert len(critical) == 2

    def test_multi_factor_scoring_pattern_config(self):
        """Test complete Multi-Factor Scoring pattern from schema."""
        config = StrategyConfig(
            name="Multi-Factor Scoring",
            type="factor_scoring",
            description="Combines multiple factors (momentum, value, quality) with weighted scoring",
            fields=[
                FieldMapping("price:收盤價", "close", "Momentum factor calculation"),
                FieldMapping("fundamental_features:本益比", "pe_ratio", "Value factor - inverse PE scoring"),
                FieldMapping("fundamental_features:ROE", "roe", "Quality factor - profitability screening"),
                FieldMapping("price:成交金額", "volume", "Liquidity screening")
            ],
            parameters=[
                ParameterConfig("momentum_weight", "float", 0.4, 0.4, (0.0, 1.0), "weight"),
                ParameterConfig("value_weight", "float", 0.3, 0.3, (0.0, 1.0), "weight"),
                ParameterConfig("quality_weight", "float", 0.3, 0.3, (0.0, 1.0), "weight"),
                ParameterConfig("momentum_period", "integer", 20, 20, (10, 60), "trading_days"),
                ParameterConfig("top_n_pct", "float", 0.10, 0.10, (0.05, 0.30), "percentage"),
                ParameterConfig("min_roe", "float", 0.10, 0.10, (0.05, 0.30), "percentage")
            ],
            logic=LogicConfig(
                entry="Rank stocks by weighted composite score, select top N%",
                exit="Exit positions falling out of top N% on rebalance",
                dependencies=["price:收盤價", "fundamental_features:本益比", "fundamental_features:ROE"]
            ),
            constraints=[
                ConstraintConfig(
                    type="parameter",
                    condition="momentum_weight + value_weight + quality_weight == 1.0",
                    severity="critical",
                    tolerance=0.01
                ),
                ConstraintConfig(
                    type="data_quality",
                    condition="PE ratio > 0 for value scoring",
                    severity="critical"
                ),
                ConstraintConfig(
                    type="data_quality",
                    condition="ROE values available and valid",
                    severity="critical"
                )
            ],
            coverage=0.16
        )

        # Validate structure
        assert len(config.fields) == 4
        assert len(config.parameters) == 6
        assert config.validate_dependencies() is True

        # Validate weight parameters sum to 1.0
        momentum_w = config.get_parameter_by_name("momentum_weight")
        value_w = config.get_parameter_by_name("value_weight")
        quality_w = config.get_parameter_by_name("quality_weight")

        total_weight = momentum_w.value + value_w.value + quality_w.value
        assert abs(total_weight - 1.0) < 0.01  # Within tolerance
