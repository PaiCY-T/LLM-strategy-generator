"""
Test Suite for Strategy Parameter Schemas (TDD RED Phase)

Tests for MomentumStrategyParams and StrategyParamRequest Pydantic schemas.
Following TDD methodology: these tests are written FIRST before implementation.

Requirements: F1.1, F1.2, AC1
"""

import pytest
from pydantic import ValidationError


class TestMomentumStrategyParams:
    """Test suite for MomentumStrategyParams Pydantic schema."""

    # ==========================================================================
    # Happy Path Tests - Valid Parameter Combinations
    # ==========================================================================

    def test_valid_params_all_minimum_values(self):
        """
        GIVEN minimum valid values for all parameters
        WHEN creating MomentumStrategyParams
        THEN schema validates successfully
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=5,
            ma_periods=20,
            catalyst_type="revenue",
            catalyst_lookback=2,
            n_stocks=5,
            stop_loss=0.08,
            resample="W",
            resample_offset=0
        )

        assert params.momentum_period == 5
        assert params.ma_periods == 20
        assert params.catalyst_type == "revenue"
        assert params.catalyst_lookback == 2
        assert params.n_stocks == 5
        assert params.stop_loss == 0.08
        assert params.resample == "W"
        assert params.resample_offset == 0

    def test_valid_params_all_maximum_values(self):
        """
        GIVEN maximum valid values for all parameters
        WHEN creating MomentumStrategyParams
        THEN schema validates successfully
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=30,
            ma_periods=120,
            catalyst_type="earnings",
            catalyst_lookback=6,
            n_stocks=20,
            stop_loss=0.15,
            resample="M",
            resample_offset=4
        )

        assert params.momentum_period == 30
        assert params.ma_periods == 120
        assert params.catalyst_type == "earnings"

    def test_valid_params_mixed_values(self):
        """
        GIVEN a mix of valid parameter values
        WHEN creating MomentumStrategyParams
        THEN schema validates successfully
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=20,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=2
        )

        assert params.momentum_period == 20
        assert params.n_stocks == 15

    # ==========================================================================
    # Invalid Value Tests - Literal Type Enforcement
    # ==========================================================================

    def test_invalid_momentum_period_value(self):
        """
        GIVEN momentum_period=25 (not in [5, 10, 20, 30])
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=25,  # Invalid: not in Literal
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        assert "momentum_period" in str(exc_info.value)

    def test_invalid_ma_periods_value(self):
        """
        GIVEN ma_periods=50 (not in [20, 60, 90, 120])
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10,
                ma_periods=50,  # Invalid: not in Literal
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        assert "ma_periods" in str(exc_info.value)

    def test_invalid_catalyst_type_value(self):
        """
        GIVEN catalyst_type="growth" (not in ["revenue", "earnings"])
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10,
                ma_periods=60,
                catalyst_type="growth",  # Invalid: not in Literal
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        assert "catalyst_type" in str(exc_info.value)

    def test_invalid_stop_loss_value(self):
        """
        GIVEN stop_loss=0.05 (not in [0.08, 0.10, 0.12, 0.15])
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.05,  # Invalid: not in Literal
                resample="W",
                resample_offset=0
            )

        assert "stop_loss" in str(exc_info.value)

    def test_invalid_resample_value(self):
        """
        GIVEN resample="D" (not in ["W", "M"])
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="D",  # Invalid: not in Literal
                resample_offset=0
            )

        assert "resample" in str(exc_info.value)

    # ==========================================================================
    # Type Error Tests
    # ==========================================================================

    def test_type_error_stop_loss_string(self):
        """
        GIVEN stop_loss="10%" (string instead of float)
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss="10%",  # Invalid: string instead of float
                resample="W",
                resample_offset=0
            )

        # Should reject type mismatch
        errors = exc_info.value.errors()
        assert len(errors) > 0

    def test_type_error_momentum_period_float(self):
        """
        GIVEN momentum_period=10.5 (float instead of int)
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised (not in Literal)
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=10.5,  # Invalid: float, not in Literal
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        assert "momentum_period" in str(exc_info.value)

    # ==========================================================================
    # Missing Field Tests
    # ==========================================================================

    def test_missing_required_field(self):
        """
        GIVEN momentum_period is missing
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                # momentum_period missing
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        assert "momentum_period" in str(exc_info.value)

    # ==========================================================================
    # Cross-Parameter Validation Tests (model_validator)
    # ==========================================================================

    def test_cross_validation_momentum_greater_than_ma(self):
        """
        GIVEN momentum_period=30 > ma_periods=20
        WHEN creating MomentumStrategyParams
        THEN ValidationError is raised (momentum should be <= ma for trend following)
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            MomentumStrategyParams(
                momentum_period=30,  # 30 > 20, invalid
                ma_periods=20,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )

        # Should mention the cross-validation failure
        error_str = str(exc_info.value)
        assert "momentum_period" in error_str or "ma_periods" in error_str

    def test_cross_validation_momentum_equal_ma_valid(self):
        """
        GIVEN momentum_period=20 == ma_periods=20
        WHEN creating MomentumStrategyParams
        THEN validation passes (equal is allowed)
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=20,
            ma_periods=20,  # Equal is allowed
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )

        assert params.momentum_period == params.ma_periods

    def test_cross_validation_momentum_less_than_ma_valid(self):
        """
        GIVEN momentum_period=5 < ma_periods=120
        WHEN creating MomentumStrategyParams
        THEN validation passes
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=5,
            ma_periods=120,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )

        assert params.momentum_period < params.ma_periods

    # ==========================================================================
    # JSON Schema Export Test
    # ==========================================================================

    def test_json_schema_export(self):
        """
        GIVEN MomentumStrategyParams class
        WHEN calling model_json_schema()
        THEN returns valid JSON schema with all field definitions
        """
        from src.schemas.strategy_params import MomentumStrategyParams

        schema = MomentumStrategyParams.model_json_schema()

        assert "properties" in schema
        assert "momentum_period" in schema["properties"]
        assert "ma_periods" in schema["properties"]
        assert "catalyst_type" in schema["properties"]
        assert "stop_loss" in schema["properties"]
        assert "resample" in schema["properties"]


class TestStrategyParamRequest:
    """Test suite for StrategyParamRequest Pydantic schema (LLM output format)."""

    # ==========================================================================
    # Happy Path Tests
    # ==========================================================================

    def test_valid_request_with_reasoning(self):
        """
        GIVEN valid reasoning and params
        WHEN creating StrategyParamRequest
        THEN validation passes
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        request = StrategyParamRequest(
            reasoning="選擇 20 天動量週期配合 60 天均線，因為中期趨勢更穩定。收入催化劑在台股較可靠。15 支股票平衡分散與集中。10% 停損適合動量策略波動性。",
            params=MomentumStrategyParams(
                momentum_period=20,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )
        )

        assert len(request.reasoning) >= 50
        assert request.params.momentum_period == 20

    # ==========================================================================
    # Reasoning Field Constraint Tests
    # ==========================================================================

    def test_reasoning_too_short(self):
        """
        GIVEN reasoning with < 50 characters
        WHEN creating StrategyParamRequest
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            StrategyParamRequest(
                reasoning="Too short",  # < 50 chars
                params=MomentumStrategyParams(
                    momentum_period=20,
                    ma_periods=60,
                    catalyst_type="revenue",
                    catalyst_lookback=3,
                    n_stocks=15,
                    stop_loss=0.10,
                    resample="W",
                    resample_offset=0
                )
            )

        assert "reasoning" in str(exc_info.value)

    def test_reasoning_too_long(self):
        """
        GIVEN reasoning with > 500 characters
        WHEN creating StrategyParamRequest
        THEN ValidationError is raised
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            StrategyParamRequest(
                reasoning="x" * 501,  # > 500 chars
                params=MomentumStrategyParams(
                    momentum_period=20,
                    ma_periods=60,
                    catalyst_type="revenue",
                    catalyst_lookback=3,
                    n_stocks=15,
                    stop_loss=0.10,
                    resample="W",
                    resample_offset=0
                )
            )

        assert "reasoning" in str(exc_info.value)

    def test_reasoning_at_minimum_boundary(self):
        """
        GIVEN reasoning with exactly 50 characters
        WHEN creating StrategyParamRequest
        THEN validation passes
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        request = StrategyParamRequest(
            reasoning="x" * 50,  # Exactly 50 chars
            params=MomentumStrategyParams(
                momentum_period=20,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )
        )

        assert len(request.reasoning) == 50

    def test_reasoning_at_maximum_boundary(self):
        """
        GIVEN reasoning with exactly 500 characters
        WHEN creating StrategyParamRequest
        THEN validation passes
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        request = StrategyParamRequest(
            reasoning="x" * 500,  # Exactly 500 chars
            params=MomentumStrategyParams(
                momentum_period=20,
                ma_periods=60,
                catalyst_type="revenue",
                catalyst_lookback=3,
                n_stocks=15,
                stop_loss=0.10,
                resample="W",
                resample_offset=0
            )
        )

        assert len(request.reasoning) == 500

    # ==========================================================================
    # Nested Params Validation
    # ==========================================================================

    def test_nested_params_validation_propagates(self):
        """
        GIVEN valid reasoning but invalid params
        WHEN creating StrategyParamRequest
        THEN ValidationError is raised for nested params
        """
        from src.schemas.strategy_params import StrategyParamRequest, MomentumStrategyParams

        with pytest.raises(ValidationError) as exc_info:
            StrategyParamRequest(
                reasoning="x" * 50,
                params=MomentumStrategyParams(
                    momentum_period=25,  # Invalid
                    ma_periods=60,
                    catalyst_type="revenue",
                    catalyst_lookback=3,
                    n_stocks=15,
                    stop_loss=0.10,
                    resample="W",
                    resample_offset=0
                )
            )

        assert "momentum_period" in str(exc_info.value)

    # ==========================================================================
    # JSON Schema Export Test
    # ==========================================================================

    def test_request_json_schema_export(self):
        """
        GIVEN StrategyParamRequest class
        WHEN calling model_json_schema()
        THEN returns valid JSON schema with reasoning and params
        """
        from src.schemas.strategy_params import StrategyParamRequest

        schema = StrategyParamRequest.model_json_schema()

        assert "properties" in schema
        assert "reasoning" in schema["properties"]
        assert "params" in schema["properties"]


# ==========================================================================
# Parametrized Tests for All Valid Literal Combinations
# ==========================================================================

class TestMomentumStrategyParamsLiteralValues:
    """Parametrized tests for all valid Literal values."""

    @pytest.mark.parametrize("momentum_period", [5, 10, 20, 30])
    def test_all_valid_momentum_periods(self, momentum_period):
        """Test all valid momentum_period values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=momentum_period,
            ma_periods=120,  # Use max to allow all momentum values
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )
        assert params.momentum_period == momentum_period

    @pytest.mark.parametrize("ma_periods", [20, 60, 90, 120])
    def test_all_valid_ma_periods(self, ma_periods):
        """Test all valid ma_periods values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=5,  # Use min to allow all ma values
            ma_periods=ma_periods,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )
        assert params.ma_periods == ma_periods

    @pytest.mark.parametrize("catalyst_type", ["revenue", "earnings"])
    def test_all_valid_catalyst_types(self, catalyst_type):
        """Test all valid catalyst_type values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=10,
            ma_periods=60,
            catalyst_type=catalyst_type,
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=0
        )
        assert params.catalyst_type == catalyst_type

    @pytest.mark.parametrize("stop_loss", [0.08, 0.10, 0.12, 0.15])
    def test_all_valid_stop_loss_values(self, stop_loss):
        """Test all valid stop_loss values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=10,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=stop_loss,
            resample="W",
            resample_offset=0
        )
        assert params.stop_loss == stop_loss

    @pytest.mark.parametrize("resample", ["W", "M"])
    def test_all_valid_resample_values(self, resample):
        """Test all valid resample values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=10,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample=resample,
            resample_offset=0
        )
        assert params.resample == resample

    @pytest.mark.parametrize("resample_offset", [0, 1, 2, 3, 4])
    def test_all_valid_resample_offset_values(self, resample_offset):
        """Test all valid resample_offset values."""
        from src.schemas.strategy_params import MomentumStrategyParams

        params = MomentumStrategyParams(
            momentum_period=10,
            ma_periods=60,
            catalyst_type="revenue",
            catalyst_lookback=3,
            n_stocks=15,
            stop_loss=0.10,
            resample="W",
            resample_offset=resample_offset
        )
        assert params.resample_offset == resample_offset
