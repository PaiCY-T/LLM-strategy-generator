"""
Unit tests for liquidity calculator module.

Tests cover basic calculations, edge cases, validation logic,
and error handling for the dynamic liquidity calculator.
"""

import pytest

from src.liquidity_calculator import (
    calculate_min_liquidity,
    recommend_threshold,
    validate_liquidity_threshold,
)


@pytest.mark.unit
class TestCalculateMinLiquidity:
    """Tests for calculate_min_liquidity function."""

    def test_basic_calculation_default_params(self) -> None:
        """Test basic calculation with default parameters."""
        result = calculate_min_liquidity()

        # Verify all required fields exist
        assert "portfolio_value" in result
        assert "stock_count" in result
        assert "position_size" in result
        assert "theoretical_min" in result
        assert "recommended_threshold" in result
        assert "market_impact_pct" in result
        assert "safety_multiplier" in result
        assert "safety_margin" in result

        # Verify default values
        assert result["portfolio_value"] == 20_000_000
        assert result["stock_count"] == 8
        assert result["safety_multiplier"] == 50.0
        assert result["safety_margin"] == 0.1

        # Verify calculations
        expected_position_size = 20_000_000 / 8
        assert result["position_size"] == expected_position_size

        expected_theoretical_min = expected_position_size * 50.0
        assert result["theoretical_min"] == expected_theoretical_min

        expected_recommended = expected_theoretical_min / 0.9
        assert abs(result["recommended_threshold"] - expected_recommended) < 0.01

        expected_impact = (expected_position_size / expected_recommended) * 100
        assert abs(result["market_impact_pct"] - expected_impact) < 0.01

    def test_6_stocks_worst_case(self) -> None:
        """Test calculation with 6 stocks (worst case concentration)."""
        result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=6,
            safety_multiplier=50.0,
            safety_margin=0.1,
        )

        # With 6 stocks, position size is larger
        assert result["stock_count"] == 6
        expected_position_size = 20_000_000 / 6
        assert abs(result["position_size"] - expected_position_size) < 0.01

        # Theoretical minimum should be 50x position
        expected_theoretical = expected_position_size * 50.0
        assert abs(result["theoretical_min"] - expected_theoretical) < 0.01

        # Recommended should be theoretical / 0.9
        expected_recommended = expected_theoretical / 0.9
        assert abs(result["recommended_threshold"] - expected_recommended) < 0.01

        # Market impact should be around 1.8%
        assert abs(result["market_impact_pct"] - 1.8) < 0.01

    def test_12_stocks_best_case(self) -> None:
        """Test calculation with 12 stocks (best case diversification)."""
        result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=12,
            safety_multiplier=50.0,
            safety_margin=0.1,
        )

        # With 12 stocks, position size is smaller
        assert result["stock_count"] == 12
        expected_position_size = 20_000_000 / 12
        assert abs(result["position_size"] - expected_position_size) < 0.01

        # Should have lower liquidity requirement
        assert result["recommended_threshold"] < 100_000_000

        # Market impact should still be around 1.8%
        assert abs(result["market_impact_pct"] - 1.8) < 0.01

    def test_custom_safety_multiplier(self) -> None:
        """Test calculation with custom safety multiplier."""
        result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=8,
            safety_multiplier=100.0,  # 1% market impact
            safety_margin=0.1,
        )

        # Higher multiplier should result in higher threshold
        assert result["safety_multiplier"] == 100.0
        assert result["recommended_threshold"] > 200_000_000

        # Market impact should be lower (around 0.9%)
        assert result["market_impact_pct"] < 1.0

    def test_zero_safety_margin(self) -> None:
        """Test calculation with zero safety margin."""
        result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=8,
            safety_multiplier=50.0,
            safety_margin=0.0,
        )

        # With zero margin, recommended equals theoretical
        assert result["safety_margin"] == 0.0
        assert abs(
            result["recommended_threshold"] - result["theoretical_min"]
        ) < 0.01

        # Market impact should be exactly 2%
        assert abs(result["market_impact_pct"] - 2.0) < 0.01

    def test_high_safety_margin(self) -> None:
        """Test calculation with high safety margin."""
        result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=8,
            safety_multiplier=50.0,
            safety_margin=0.5,  # 50% margin
        )

        # High margin should double the threshold
        assert result["safety_margin"] == 0.5
        expected_recommended = result["theoretical_min"] / 0.5
        assert abs(result["recommended_threshold"] - expected_recommended) < 0.01

        # Market impact should be 1%
        assert abs(result["market_impact_pct"] - 1.0) < 0.01

    def test_small_portfolio(self) -> None:
        """Test calculation with small portfolio value."""
        result = calculate_min_liquidity(
            portfolio_value=1_000_000,  # 1M TWD
            stock_count=5,
            safety_multiplier=50.0,
            safety_margin=0.1,
        )

        assert result["portfolio_value"] == 1_000_000
        expected_position_size = 1_000_000 / 5
        assert result["position_size"] == expected_position_size

        # Should have much lower liquidity requirement
        assert result["recommended_threshold"] < 15_000_000

    def test_large_portfolio(self) -> None:
        """Test calculation with large portfolio value."""
        result = calculate_min_liquidity(
            portfolio_value=100_000_000,  # 100M TWD
            stock_count=10,
            safety_multiplier=50.0,
            safety_margin=0.1,
        )

        assert result["portfolio_value"] == 100_000_000
        expected_position_size = 100_000_000 / 10
        assert result["position_size"] == expected_position_size

        # Should have higher liquidity requirement
        assert result["recommended_threshold"] > 500_000_000

    def test_negative_portfolio_value_raises_error(self) -> None:
        """Test that negative portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            calculate_min_liquidity(portfolio_value=-1000)

    def test_zero_portfolio_value_raises_error(self) -> None:
        """Test that zero portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            calculate_min_liquidity(portfolio_value=0)

    def test_negative_stock_count_raises_error(self) -> None:
        """Test that negative stock count raises ValueError."""
        with pytest.raises(ValueError, match="stock_count must be positive"):
            calculate_min_liquidity(stock_count=-5)

    def test_zero_stock_count_raises_error(self) -> None:
        """Test that zero stock count raises ValueError."""
        with pytest.raises(ValueError, match="stock_count must be positive"):
            calculate_min_liquidity(stock_count=0)

    def test_negative_safety_multiplier_raises_error(self) -> None:
        """Test that negative safety multiplier raises ValueError."""
        with pytest.raises(ValueError, match="safety_multiplier must be positive"):
            calculate_min_liquidity(safety_multiplier=-10)

    def test_zero_safety_multiplier_raises_error(self) -> None:
        """Test that zero safety multiplier raises ValueError."""
        with pytest.raises(ValueError, match="safety_multiplier must be positive"):
            calculate_min_liquidity(safety_multiplier=0)

    def test_negative_safety_margin_raises_error(self) -> None:
        """Test that negative safety margin raises ValueError."""
        with pytest.raises(ValueError, match="safety_margin must be in"):
            calculate_min_liquidity(safety_margin=-0.1)

    def test_safety_margin_greater_than_one_raises_error(self) -> None:
        """Test that safety margin ≥1 raises ValueError."""
        with pytest.raises(ValueError, match="safety_margin must be in"):
            calculate_min_liquidity(safety_margin=1.0)

        with pytest.raises(ValueError, match="safety_margin must be in"):
            calculate_min_liquidity(safety_margin=1.5)


@pytest.mark.unit
class TestValidateLiquidityThreshold:
    """Tests for validate_liquidity_threshold function."""

    def test_validate_150m_threshold_default_params(self) -> None:
        """Test validation of 150M TWD threshold (current standard)."""
        result = validate_liquidity_threshold(
            threshold=150_000_000,
            portfolio_value=20_000_000,
            stock_count_range=(6, 12),
        )

        # Verify all required fields exist
        assert "threshold" in result
        assert "portfolio_value" in result
        assert "stock_count_range" in result
        assert "results" in result
        assert "worst_case" in result
        assert "is_valid" in result
        assert "max_acceptable_impact" in result

        # Verify inputs
        assert result["threshold"] == 150_000_000
        assert result["portfolio_value"] == 20_000_000
        assert result["stock_count_range"] == (6, 12)
        assert result["max_acceptable_impact"] == 2.0

        # Should have results for 7 stock counts (6-12)
        assert len(result["results"]) == 7

        # Worst case should be 6 stocks
        assert result["worst_case"]["stock_count"] == 6

        # 150M threshold should be valid (all impacts ≤2%)
        # At 6 stocks: 20M/6 = 3.33M position, 3.33M/150M = 2.22% impact
        # This is slightly above 2%, so should be invalid
        assert result["is_valid"] is False

    def test_validate_200m_threshold_is_valid(self) -> None:
        """Test validation of 200M TWD threshold (should be valid)."""
        result = validate_liquidity_threshold(
            threshold=200_000_000,
            portfolio_value=20_000_000,
            stock_count_range=(6, 12),
        )

        # 200M should be valid for all stock counts
        assert result["is_valid"] is True

        # All individual results should be acceptable
        for stock_result in result["results"]:
            assert stock_result["is_acceptable"] is True
            assert stock_result["market_impact_pct"] <= 2.0

        # Worst case should still be 6 stocks but under 2%
        assert result["worst_case"]["stock_count"] == 6
        assert result["worst_case"]["market_impact_pct"] <= 2.0

    def test_validate_100m_threshold_is_invalid(self) -> None:
        """Test validation of 100M TWD threshold (should be invalid)."""
        result = validate_liquidity_threshold(
            threshold=100_000_000,
            portfolio_value=20_000_000,
            stock_count_range=(6, 12),
        )

        # 100M should be invalid (too low)
        assert result["is_valid"] is False

        # Should have some unacceptable results
        unacceptable_count = sum(
            1 for r in result["results"] if not r["is_acceptable"]
        )
        assert unacceptable_count > 0

        # Worst case impact should be above 2%
        assert result["worst_case"]["market_impact_pct"] > 2.0

    def test_validate_narrow_stock_range(self) -> None:
        """Test validation with narrow stock count range."""
        result = validate_liquidity_threshold(
            threshold=150_000_000,
            portfolio_value=20_000_000,
            stock_count_range=(8, 10),
        )

        # Should have results for 3 stock counts (8, 9, 10)
        assert len(result["results"]) == 3

        # All stock counts should be in range
        stock_counts = [r["stock_count"] for r in result["results"]]
        assert stock_counts == [8, 9, 10]

    def test_validate_single_stock_count(self) -> None:
        """Test validation with single stock count (min=max)."""
        result = validate_liquidity_threshold(
            threshold=150_000_000,
            portfolio_value=20_000_000,
            stock_count_range=(8, 8),
        )

        # Should have exactly 1 result
        assert len(result["results"]) == 1
        assert result["results"][0]["stock_count"] == 8

        # Worst case should be the only case
        assert result["worst_case"]["stock_count"] == 8

    def test_validate_results_structure(self) -> None:
        """Test that result entries have correct structure."""
        result = validate_liquidity_threshold(150_000_000)

        # Each result should have required fields
        for stock_result in result["results"]:
            assert "stock_count" in stock_result
            assert "position_size" in stock_result
            assert "market_impact_pct" in stock_result
            assert "is_acceptable" in stock_result

            # Verify types
            assert isinstance(stock_result["stock_count"], int)
            assert isinstance(stock_result["position_size"], float)
            assert isinstance(stock_result["market_impact_pct"], float)
            assert isinstance(stock_result["is_acceptable"], bool)

    def test_negative_threshold_raises_error(self) -> None:
        """Test that negative threshold raises ValueError."""
        with pytest.raises(ValueError, match="threshold must be positive"):
            validate_liquidity_threshold(threshold=-1000)

    def test_zero_threshold_raises_error(self) -> None:
        """Test that zero threshold raises ValueError."""
        with pytest.raises(ValueError, match="threshold must be positive"):
            validate_liquidity_threshold(threshold=0)

    def test_negative_portfolio_value_raises_error(self) -> None:
        """Test that negative portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            validate_liquidity_threshold(150_000_000, portfolio_value=-1000)

    def test_invalid_stock_range_tuple_raises_error(self) -> None:
        """Test that invalid stock range tuple raises ValueError."""
        with pytest.raises(ValueError, match="stock_count_range must be tuple"):
            validate_liquidity_threshold(
                150_000_000, stock_count_range=(6, 8, 10)  # type: ignore
            )

    def test_negative_stock_range_raises_error(self) -> None:
        """Test that negative stock range values raise ValueError."""
        with pytest.raises(ValueError, match="stock count range values must be positive"):
            validate_liquidity_threshold(150_000_000, stock_count_range=(-1, 10))

    def test_reversed_stock_range_raises_error(self) -> None:
        """Test that reversed stock range (min > max) raises ValueError."""
        with pytest.raises(ValueError, match="stock_count_range min must be"):
            validate_liquidity_threshold(150_000_000, stock_count_range=(12, 6))


@pytest.mark.unit
class TestRecommendThreshold:
    """Tests for recommend_threshold function."""

    def test_recommend_for_8_stocks_2pct_impact(self) -> None:
        """Test recommendation for 8 stocks with 2% max impact."""
        result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=8,
            max_impact=2.0,
        )

        # Verify all required fields exist
        assert "portfolio_value" in result
        assert "target_stock_count" in result
        assert "max_impact" in result
        assert "position_size" in result
        assert "recommended_threshold" in result
        assert "actual_impact" in result
        assert "safety_multiplier" in result
        assert "justification" in result

        # Verify inputs
        assert result["portfolio_value"] == 20_000_000
        assert result["target_stock_count"] == 8
        assert result["max_impact"] == 2.0

        # Verify calculations
        expected_position_size = 20_000_000 / 8
        assert result["position_size"] == expected_position_size

        expected_threshold = (expected_position_size / 2.0) * 100
        assert abs(result["recommended_threshold"] - expected_threshold) < 0.01

        # Actual impact should equal max_impact
        assert abs(result["actual_impact"] - 2.0) < 0.01

        # Safety multiplier should be 50x for 2% impact
        assert abs(result["safety_multiplier"] - 50.0) < 0.01

    def test_recommend_for_6_stocks_1_5pct_impact(self) -> None:
        """Test recommendation for 6 stocks with 1.5% max impact."""
        result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=6,
            max_impact=1.5,
        )

        assert result["target_stock_count"] == 6
        assert result["max_impact"] == 1.5

        # With stricter impact limit, threshold should be higher
        expected_position_size = 20_000_000 / 6
        expected_threshold = (expected_position_size / 1.5) * 100
        assert abs(result["recommended_threshold"] - expected_threshold) < 0.01

        # Actual impact should equal max_impact
        assert abs(result["actual_impact"] - 1.5) < 0.01

        # Safety multiplier should be ~66.67x for 1.5% impact
        assert abs(result["safety_multiplier"] - 66.67) < 0.1

    def test_recommend_for_12_stocks_2pct_impact(self) -> None:
        """Test recommendation for 12 stocks with 2% max impact."""
        result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=12,
            max_impact=2.0,
        )

        assert result["target_stock_count"] == 12

        # With more stocks, position size is smaller
        expected_position_size = 20_000_000 / 12
        assert abs(result["position_size"] - expected_position_size) < 0.01

        # Threshold should be lower than 8-stock case
        assert result["recommended_threshold"] < 125_000_000

        # Actual impact should equal max_impact
        assert abs(result["actual_impact"] - 2.0) < 0.01

    def test_recommend_with_1pct_max_impact(self) -> None:
        """Test recommendation with very conservative 1% max impact."""
        result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=8,
            max_impact=1.0,
        )

        assert result["max_impact"] == 1.0

        # Threshold should be double the 2% case
        expected_position_size = 20_000_000 / 8
        expected_threshold = (expected_position_size / 1.0) * 100
        assert abs(result["recommended_threshold"] - expected_threshold) < 0.01

        # Actual impact should equal max_impact
        assert abs(result["actual_impact"] - 1.0) < 0.01

        # Safety multiplier should be 100x for 1% impact
        assert abs(result["safety_multiplier"] - 100.0) < 0.01

    def test_recommend_justification_text(self) -> None:
        """Test that justification text is generated correctly."""
        result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=8,
            max_impact=2.0,
        )

        justification = result["justification"]

        # Should contain key information
        assert "20,000,000" in justification
        assert "8 stocks" in justification
        assert "2500000" in justification or "2,500,000" in justification  # position size
        assert "2.0%" in justification or "2%" in justification
        assert "50" in justification  # safety multiplier

    def test_recommend_for_large_portfolio(self) -> None:
        """Test recommendation for large portfolio."""
        result = recommend_threshold(
            portfolio_value=100_000_000,
            target_stock_count=10,
            max_impact=2.0,
        )

        assert result["portfolio_value"] == 100_000_000

        # Should have much higher threshold
        assert result["recommended_threshold"] > 400_000_000

        # Actual impact should still equal max_impact
        assert abs(result["actual_impact"] - 2.0) < 0.01

    def test_negative_portfolio_value_raises_error(self) -> None:
        """Test that negative portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            recommend_threshold(
                portfolio_value=-1000, target_stock_count=8, max_impact=2.0
            )

    def test_zero_portfolio_value_raises_error(self) -> None:
        """Test that zero portfolio value raises ValueError."""
        with pytest.raises(ValueError, match="portfolio_value must be positive"):
            recommend_threshold(portfolio_value=0, target_stock_count=8, max_impact=2.0)

    def test_negative_stock_count_raises_error(self) -> None:
        """Test that negative stock count raises ValueError."""
        with pytest.raises(ValueError, match="target_stock_count must be positive"):
            recommend_threshold(
                portfolio_value=20_000_000, target_stock_count=-5, max_impact=2.0
            )

    def test_zero_stock_count_raises_error(self) -> None:
        """Test that zero stock count raises ValueError."""
        with pytest.raises(ValueError, match="target_stock_count must be positive"):
            recommend_threshold(
                portfolio_value=20_000_000, target_stock_count=0, max_impact=2.0
            )

    def test_negative_max_impact_raises_error(self) -> None:
        """Test that negative max impact raises ValueError."""
        with pytest.raises(ValueError, match="max_impact must be in"):
            recommend_threshold(
                portfolio_value=20_000_000, target_stock_count=8, max_impact=-1.0
            )

    def test_zero_max_impact_raises_error(self) -> None:
        """Test that zero max impact raises ValueError."""
        with pytest.raises(ValueError, match="max_impact must be in"):
            recommend_threshold(
                portfolio_value=20_000_000, target_stock_count=8, max_impact=0
            )

    def test_max_impact_over_100_raises_error(self) -> None:
        """Test that max impact >100% raises ValueError."""
        with pytest.raises(ValueError, match="max_impact must be in"):
            recommend_threshold(
                portfolio_value=20_000_000, target_stock_count=8, max_impact=150.0
            )


@pytest.mark.unit
class TestMarketImpactCalculations:
    """Tests for market impact calculation accuracy."""

    def test_market_impact_consistency_across_functions(self) -> None:
        """Test that market impact is calculated consistently across functions."""
        # Calculate using calculate_min_liquidity
        calc_result = calculate_min_liquidity(
            portfolio_value=20_000_000,
            stock_count=8,
            safety_multiplier=50.0,
            safety_margin=0.1,
        )

        # Calculate using recommend_threshold
        rec_result = recommend_threshold(
            portfolio_value=20_000_000,
            target_stock_count=8,
            max_impact=calc_result["market_impact_pct"],
        )

        # Thresholds should match (within rounding)
        assert abs(
            calc_result["recommended_threshold"] - rec_result["recommended_threshold"]
        ) < 1.0

        # Impacts should match
        assert abs(
            calc_result["market_impact_pct"] - rec_result["actual_impact"]
        ) < 0.01

    def test_validation_uses_same_impact_calculation(self) -> None:
        """Test that validation uses same impact calculation as other functions."""
        threshold = 125_000_000
        portfolio_value = 20_000_000

        # Validate the threshold
        val_result = validate_liquidity_threshold(
            threshold=threshold,
            portfolio_value=portfolio_value,
            stock_count_range=(8, 8),
        )

        # Calculate expected impact manually
        position_size = portfolio_value / 8
        expected_impact = (position_size / threshold) * 100

        # Should match validation result
        assert abs(
            val_result["results"][0]["market_impact_pct"] - expected_impact
        ) < 0.01

    def test_market_impact_inverse_relationship_with_threshold(self) -> None:
        """Test that market impact has inverse relationship with threshold."""
        portfolio_value = 20_000_000
        stock_count = 8

        # Calculate with different thresholds
        low_threshold = calculate_min_liquidity(
            portfolio_value, stock_count, safety_multiplier=25.0, safety_margin=0.0
        )

        high_threshold = calculate_min_liquidity(
            portfolio_value, stock_count, safety_multiplier=100.0, safety_margin=0.0
        )

        # Higher threshold should have lower impact
        assert high_threshold["market_impact_pct"] < low_threshold["market_impact_pct"]

        # Verify specific values
        assert abs(low_threshold["market_impact_pct"] - 4.0) < 0.01  # 1/25 = 4%
        assert abs(high_threshold["market_impact_pct"] - 1.0) < 0.01  # 1/100 = 1%
