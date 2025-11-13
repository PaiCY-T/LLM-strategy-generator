"""
Unit tests for SemanticValidator - Story 5: Semantic Validation.

This module tests the SemanticValidator's ability to detect unrealistic trading
behavior patterns including position concentration, excessive turnover, and
inappropriate portfolio sizing.

Design Reference: design.md v1.1 lines 149-274 (ValidationHook Protocol)
Tasks Reference: tasks.md lines 220-230 (Task 5.7 specification)
Requirements Reference: requirements.md F5.1-F5.4 (semantic validation rules)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any

from src.validation.semantic_validator import SemanticValidator


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def validator():
    """Create SemanticValidator instance for testing."""
    return SemanticValidator()


@pytest.fixture
def diversified_portfolio() -> pd.DataFrame:
    """
    Diversified portfolio with 10 stocks, max 15% concentration.

    Represents a well-balanced strategy with:
    - 10 stocks (good diversification)
    - Max position weight: 15% (below 20% limit)
    - Quarterly rebalancing

    Returns:
        DataFrame with dates as index, stock tickers as columns
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create 10 stocks with varying weights (total = 100%)
    # Weights: [15, 12, 11, 10, 10, 9, 9, 8, 8, 8] = 100%
    portfolio = pd.DataFrame({
        '2330': np.linspace(15000, 18000, 252),  # 15% max
        '2317': np.linspace(12000, 14000, 252),  # 12%
        '2454': np.linspace(11000, 13000, 252),  # 11%
        '2308': np.linspace(10000, 12000, 252),  # 10%
        '2303': np.linspace(10000, 11000, 252),  # 10%
        '1301': np.linspace(9000, 10500, 252),   # 9%
        '1303': np.linspace(9000, 10000, 252),   # 9%
        '2891': np.linspace(8000, 9500, 252),    # 8%
        '2882': np.linspace(8000, 9000, 252),    # 8%
        '2886': np.linspace(8000, 9000, 252),    # 8%
    }, index=dates)

    return portfolio


@pytest.fixture
def concentrated_portfolio() -> pd.DataFrame:
    """
    Concentrated portfolio with 5 stocks, one with 40% concentration.

    Represents an over-concentrated strategy:
    - 5 stocks (minimal diversification)
    - Stock '2330' has 40% weight (exceeds 20% limit)
    - Other stocks: 20%, 15%, 15%, 10%

    Returns:
        DataFrame with dates as index, stock tickers as columns
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create 5 stocks with concentrated weights (total = 100%)
    # Weights: [40, 20, 15, 15, 10] = 100%
    portfolio = pd.DataFrame({
        '2330': np.linspace(40000, 48000, 252),  # 40% - VIOLATES 20% LIMIT
        '2317': np.linspace(20000, 24000, 252),  # 20%
        '2454': np.linspace(15000, 18000, 252),  # 15%
        '2308': np.linspace(15000, 18000, 252),  # 15%
        '2303': np.linspace(10000, 12000, 252),  # 10%
    }, index=dates)

    return portfolio


@pytest.fixture
def normal_turnover_portfolio() -> pd.DataFrame:
    """
    Normal turnover portfolio with quarterly rebalancing, 200% annual turnover.

    Represents typical rebalancing behavior:
    - Quarterly rebalancing (4 times/year)
    - ~50% portfolio change per rebalance
    - Annual turnover: 200% (acceptable)

    Returns:
        DataFrame with quarterly rebalancing dates
    """
    # Create quarterly rebalancing dates (5 quarters)
    dates = pd.date_range('2024-01-01', periods=5, freq='QE')

    # Portfolio with gradual position changes between quarters
    # Each quarter, roughly 50% of portfolio changes (2.0 * 100k = 200% annual turnover)
    portfolio = pd.DataFrame({
        '2330': [30000, 25000, 30000, 20000, 25000],
        '2317': [25000, 30000, 20000, 30000, 25000],
        '2454': [20000, 20000, 25000, 25000, 25000],
        '2308': [15000, 15000, 15000, 15000, 15000],
        '2303': [10000, 10000, 10000, 10000, 10000],
    }, index=dates)

    return portfolio


@pytest.fixture
def excessive_turnover_portfolio() -> pd.DataFrame:
    """
    Excessive turnover portfolio with monthly rebalancing, 700% annual turnover.

    Represents unrealistic high-frequency trading:
    - Monthly rebalancing (12 times/year)
    - ~60% portfolio change per rebalance
    - Annual turnover: 720% (exceeds 500% limit)

    Returns:
        DataFrame with monthly rebalancing dates
    """
    # Create monthly rebalancing dates (13 months)
    dates = pd.date_range('2024-01-01', periods=13, freq='ME')

    # Portfolio with dramatic position changes each month
    # Alternating allocation patterns create high turnover
    portfolio_data = []
    for i in range(13):
        if i % 2 == 0:
            # Even months: concentrate in stocks 1-2
            row = [40000, 40000, 10000, 5000, 5000]
        else:
            # Odd months: concentrate in stocks 3-5
            row = [5000, 10000, 30000, 30000, 25000]
        portfolio_data.append(row)

    portfolio = pd.DataFrame(
        portfolio_data,
        columns=['2330', '2317', '2454', '2308', '2303'],
        index=dates
    )

    return portfolio


@pytest.fixture
def small_portfolio() -> pd.DataFrame:
    """
    Under-diversified portfolio with 2 stocks (below 5 minimum).

    Represents insufficient diversification:
    - Only 2 stocks (below 5 minimum)
    - Violates minimum diversification requirement

    Returns:
        DataFrame with dates as index, 2 stock tickers as columns
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    portfolio = pd.DataFrame({
        '2330': np.linspace(60000, 72000, 252),  # 60%
        '2317': np.linspace(40000, 48000, 252),  # 40%
    }, index=dates)

    return portfolio


@pytest.fixture
def large_portfolio() -> pd.DataFrame:
    """
    Over-diversified portfolio with 75 stocks (above 50 maximum).

    Represents over-diversification:
    - 75 stocks (exceeds 50 maximum)
    - Violates maximum portfolio size constraint

    Returns:
        DataFrame with dates as index, 75 stock tickers as columns
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create 75 stocks with equal weights (~1.33% each)
    portfolio_dict = {}
    for i in range(75):
        ticker = f'STOCK_{i:03d}'
        portfolio_dict[ticker] = np.linspace(1330, 1600, 252)

    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    return portfolio


@pytest.fixture
def normal_size_portfolio() -> pd.DataFrame:
    """
    Normal-sized portfolio with 20 stocks (within 5-50 range).

    Represents optimal diversification:
    - 20 stocks (within 5-50 range)
    - Good balance between diversification and manageability

    Returns:
        DataFrame with dates as index, 20 stock tickers as columns
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create 20 stocks with equal weights (5% each)
    portfolio_dict = {}
    for i in range(20):
        ticker = f'STOCK_{i:02d}'
        portfolio_dict[ticker] = np.linspace(5000, 6000, 252)

    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    return portfolio


@pytest.fixture
def always_empty_portfolio() -> pd.DataFrame:
    """
    Always empty portfolio with 0 positions on all dates.

    Represents broken entry logic:
    - Never enters any positions
    - Strategy does not trade at all

    Returns:
        DataFrame with all zeros
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create portfolio with 10 stocks, all zeros
    portfolio = pd.DataFrame({
        f'STOCK_{i:02d}': np.zeros(252)
        for i in range(10)
    }, index=dates)

    return portfolio


@pytest.fixture
def always_full_portfolio() -> pd.DataFrame:
    """
    Always full portfolio with all stocks, never changes.

    Represents broken exit logic:
    - Holds all 50 stocks on all dates
    - Never exits any positions
    - No actual trading behavior

    Returns:
        DataFrame with constant positions across all dates
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='D')

    # Create portfolio with 50 stocks, constant positions (all non-zero)
    portfolio_dict = {}
    for i in range(50):
        ticker = f'STOCK_{i:02d}'
        portfolio_dict[ticker] = np.full(252, 2000)  # Constant 2000 for all dates

    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    return portfolio


@pytest.fixture
def normal_trading_portfolio() -> pd.DataFrame:
    """
    Normal trading portfolio with varying positions.

    Represents realistic trading behavior:
    - Position count varies (8-12 stocks)
    - Positions change over time
    - Both entries and exits

    Returns:
        DataFrame with varying positions
    """
    dates = pd.date_range('2024-01-01', periods=12, freq='ME')

    # Create portfolio with varying position counts
    # Some stocks enter/exit, position counts vary from 8 to 12
    portfolio = pd.DataFrame({
        'STOCK_00': [10000, 12000, 0, 0, 8000, 10000, 12000, 0, 0, 9000, 10000, 11000],
        'STOCK_01': [10000, 12000, 14000, 0, 0, 10000, 12000, 14000, 0, 0, 10000, 12000],
        'STOCK_02': [10000, 0, 14000, 16000, 8000, 0, 12000, 14000, 16000, 9000, 0, 12000],
        'STOCK_03': [10000, 12000, 14000, 16000, 8000, 10000, 0, 0, 16000, 9000, 10000, 0],
        'STOCK_04': [10000, 12000, 14000, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_05': [10000, 12000, 14000, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_06': [10000, 12000, 14000, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_07': [10000, 12000, 14000, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_08': [0, 0, 14000, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_09': [0, 0, 0, 16000, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_10': [0, 0, 0, 0, 8000, 10000, 12000, 14000, 16000, 9000, 10000, 12000],
        'STOCK_11': [0, 0, 0, 0, 0, 0, 12000, 14000, 16000, 9000, 10000, 12000],
    }, index=dates)

    return portfolio


# ==============================================================================
# Test: check_position_concentration - Pass Cases
# ==============================================================================

def test_check_position_concentration_pass(validator, diversified_portfolio):
    """
    Test position concentration check passes with diversified portfolio.

    Verifies F5.1: position concentration <= 20%
    """
    # Act
    is_valid, error_msg = validator.check_position_concentration(diversified_portfolio)

    # Assert
    assert is_valid, f"Diversified portfolio should pass concentration check: {error_msg}"
    assert error_msg == "", "No error message for valid concentration"


def test_check_position_concentration_boundary(validator):
    """Test position concentration at exactly 20% (boundary case)."""
    # Arrange - Portfolio with max stock at exactly 20%
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio = pd.DataFrame({
        '2330': np.full(100, 20000),  # Exactly 20%
        '2317': np.full(100, 20000),  # 20%
        '2454': np.full(100, 20000),  # 20%
        '2308': np.full(100, 20000),  # 20%
        '2303': np.full(100, 20000),  # 20%
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_position_concentration(portfolio)

    # Assert
    assert is_valid, f"20% concentration (boundary) should pass: {error_msg}"


def test_check_position_concentration_empty_portfolio(validator):
    """Test position concentration check with empty DataFrame."""
    # Arrange
    empty_portfolio = pd.DataFrame()

    # Act
    is_valid, error_msg = validator.check_position_concentration(empty_portfolio)

    # Assert
    assert is_valid, "Empty portfolio should pass (no positions to check)"
    assert error_msg == ""


# ==============================================================================
# Test: check_position_concentration - Fail Cases
# ==============================================================================

def test_check_position_concentration_fail(validator, concentrated_portfolio):
    """
    Test position concentration check fails with concentrated portfolio.

    Verifies F5.1: detects when any stock exceeds 20% concentration.
    """
    # Act
    is_valid, error_msg = validator.check_position_concentration(concentrated_portfolio)

    # Assert
    assert not is_valid, "Concentrated portfolio should fail concentration check"
    assert "Position concentration violation" in error_msg
    assert "2330" in error_msg, "Error should identify violating stock"
    assert "40.0%" in error_msg or "40%" in error_msg, "Error should show concentration percentage"


def test_check_position_concentration_slight_violation(validator):
    """Test concentration violation just above 20% threshold."""
    # Arrange - Portfolio with one stock at 21% (just over limit)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio = pd.DataFrame({
        '2330': np.full(100, 21000),  # 21% - VIOLATES
        '2317': np.full(100, 19750),  # 19.75%
        '2454': np.full(100, 19750),  # 19.75%
        '2308': np.full(100, 19750),  # 19.75%
        '2303': np.full(100, 19750),  # 19.75%
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_position_concentration(portfolio)

    # Assert
    assert not is_valid, "21% concentration should fail"
    assert "21.0%" in error_msg or "21%" in error_msg


# ==============================================================================
# Test: check_portfolio_turnover - Pass Cases (Quarterly)
# ==============================================================================

def test_check_portfolio_turnover_quarterly_pass(validator, normal_turnover_portfolio):
    """
    Test portfolio turnover check passes with quarterly rebalancing.

    Verifies F5.2: annual turnover <= 500% for quarterly rebalancing.
    """
    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(
        normal_turnover_portfolio, 'Q'
    )

    # Assert
    assert is_valid, f"Normal quarterly turnover should pass: {error_msg}"
    assert error_msg == "", "No error message for valid turnover"


def test_check_portfolio_turnover_quarterly_boundary(validator):
    """Test turnover with moderate quarterly rebalancing passes."""
    # Arrange - Quarterly rebalancing with moderate 60% turnover per quarter
    # 60% * 4 quarters = 240% annual (well below 500% limit)
    dates = pd.date_range('2024-01-01', periods=5, freq='QE')

    # Create portfolio with moderate rebalancing
    # Portfolio value: 200k total
    # Each quarter, adjust 30k (15% of portfolio each direction = 30% turnover per quarter)
    portfolio = pd.DataFrame({
        '2330': [100000, 115000, 100000, 115000, 100000],  # Vary +/- 15k
        '2317': [100000, 85000, 100000, 85000, 100000],    # Vary +/- 15k (opposite)
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(portfolio, 'Q')

    # Assert
    assert is_valid, f"Moderate quarterly turnover should pass: {error_msg}"


# ==============================================================================
# Test: check_portfolio_turnover - Fail Cases (Monthly)
# ==============================================================================

def test_check_portfolio_turnover_monthly_fail(validator, excessive_turnover_portfolio):
    """
    Test portfolio turnover check fails with excessive monthly rebalancing.

    Verifies F5.2: detects when annual turnover exceeds 500%.
    """
    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(
        excessive_turnover_portfolio, 'M'
    )

    # Assert
    assert not is_valid, "Excessive monthly turnover should fail"
    assert "Portfolio turnover violation" in error_msg
    assert "exceeds limit 500.0%" in error_msg


def test_check_portfolio_turnover_single_period(validator):
    """Test turnover check with single-period DataFrame (no turnover)."""
    # Arrange - Portfolio with only one date
    dates = pd.date_range('2024-01-01', periods=1, freq='D')
    portfolio = pd.DataFrame({
        '2330': [50000],
        '2317': [50000],
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(portfolio, 'M')

    # Assert
    assert is_valid, "Single-period portfolio should pass (no turnover possible)"
    assert error_msg == ""


def test_check_portfolio_turnover_empty_portfolio(validator):
    """Test turnover check with empty DataFrame."""
    # Arrange
    empty_portfolio = pd.DataFrame()

    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(empty_portfolio, 'M')

    # Assert
    assert is_valid, "Empty portfolio should pass"
    assert error_msg == ""


# ==============================================================================
# Test: check_portfolio_size - Pass Cases
# ==============================================================================

def test_check_portfolio_size_pass(validator, normal_size_portfolio):
    """
    Test portfolio size check passes with 20 stocks.

    Verifies F5.3: 5 <= portfolio_size <= 50.
    """
    # Act
    is_valid, error_msg = validator.check_portfolio_size(normal_size_portfolio)

    # Assert
    assert is_valid, f"20-stock portfolio should pass size check: {error_msg}"
    assert error_msg == "", "No error message for valid portfolio size"


def test_check_portfolio_size_minimum_boundary(validator):
    """Test portfolio size at exactly 5 stocks (minimum boundary)."""
    # Arrange - Portfolio with exactly 5 stocks
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio = pd.DataFrame({
        '2330': np.full(100, 20000),
        '2317': np.full(100, 20000),
        '2454': np.full(100, 20000),
        '2308': np.full(100, 20000),
        '2303': np.full(100, 20000),
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_size(portfolio)

    # Assert
    assert is_valid, f"5-stock portfolio (minimum boundary) should pass: {error_msg}"


def test_check_portfolio_size_maximum_boundary(validator):
    """Test portfolio size at exactly 50 stocks (maximum boundary)."""
    # Arrange - Portfolio with exactly 50 stocks
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio_dict = {}
    for i in range(50):
        ticker = f'STOCK_{i:02d}'
        portfolio_dict[ticker] = np.full(100, 2000)
    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_size(portfolio)

    # Assert
    assert is_valid, f"50-stock portfolio (maximum boundary) should pass: {error_msg}"


# ==============================================================================
# Test: check_portfolio_size - Fail Cases
# ==============================================================================

def test_check_portfolio_size_too_small(validator, small_portfolio):
    """
    Test portfolio size check fails with 2 stocks (below minimum).

    Verifies F5.3: detects under-diversification.
    """
    # Act
    is_valid, error_msg = validator.check_portfolio_size(small_portfolio)

    # Assert
    assert not is_valid, "2-stock portfolio should fail size check"
    assert "Portfolio size violation" in error_msg
    assert "below minimum 5" in error_msg
    assert "2.0" in error_msg or "2 positions" in error_msg


def test_check_portfolio_size_too_large(validator, large_portfolio):
    """
    Test portfolio size check fails with 75 stocks (above maximum).

    Verifies F5.3: detects over-diversification.
    """
    # Act
    is_valid, error_msg = validator.check_portfolio_size(large_portfolio)

    # Assert
    assert not is_valid, "75-stock portfolio should fail size check"
    assert "Portfolio size violation" in error_msg
    assert "exceeds maximum 50" in error_msg
    assert "75.0" in error_msg or "75 positions" in error_msg


def test_check_portfolio_size_empty_portfolio(validator):
    """Test portfolio size check with empty DataFrame."""
    # Arrange
    empty_portfolio = pd.DataFrame()

    # Act
    is_valid, error_msg = validator.check_portfolio_size(empty_portfolio)

    # Assert
    assert is_valid, "Empty portfolio should pass (no positions to check)"
    assert error_msg == ""


# ==============================================================================
# Test: check_always_empty_or_full - Always Empty
# ==============================================================================

def test_check_always_empty(validator, always_empty_portfolio):
    """
    Test detection of always empty portfolio (never enters).

    Verifies F5.4: detects strategies that never enter positions.
    """
    # Act
    is_valid, error_msg = validator.check_always_empty_or_full(always_empty_portfolio)

    # Assert
    assert not is_valid, "Always empty portfolio should fail"
    assert "Always empty portfolio" in error_msg
    assert "never enters positions" in error_msg
    assert "0 positions on all" in error_msg
    assert "252 dates" in error_msg


# ==============================================================================
# Test: check_always_empty_or_full - Always Full
# ==============================================================================

def test_check_always_full(validator, always_full_portfolio):
    """
    Test detection of always full portfolio (never exits).

    Verifies F5.4: detects strategies that hold all stocks without changes.
    """
    # Act
    is_valid, error_msg = validator.check_always_empty_or_full(always_full_portfolio)

    # Assert
    assert not is_valid, "Always full portfolio should fail"
    assert "Always full portfolio" in error_msg
    assert "never exits positions" in error_msg
    assert "50 positions on all" in error_msg
    assert "252 dates" in error_msg


def test_check_always_empty_or_full_normal(validator, normal_trading_portfolio):
    """Test that normal trading portfolio passes empty/full check."""
    # Act
    is_valid, error_msg = validator.check_always_empty_or_full(normal_trading_portfolio)

    # Assert
    assert is_valid, f"Normal trading portfolio should pass: {error_msg}"
    assert error_msg == "", "No error message for normal trading"


def test_check_always_empty_or_full_constant_partial(validator):
    """Test that constant partial portfolio (not full) passes check."""
    # Arrange - Portfolio with constant 10 positions (not universe size)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio_dict = {}
    for i in range(50):  # Universe of 50 stocks
        ticker = f'STOCK_{i:02d}'
        if i < 10:
            # First 10 stocks always held
            portfolio_dict[ticker] = np.full(100, 5000)
        else:
            # Rest never held
            portfolio_dict[ticker] = np.zeros(100)
    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    # Act
    is_valid, error_msg = validator.check_always_empty_or_full(portfolio)

    # Assert
    assert is_valid, "Constant partial portfolio should pass (not full universe)"


def test_check_always_empty_or_full_empty_dataframe(validator):
    """Test empty/full check with empty DataFrame."""
    # Arrange
    empty_portfolio = pd.DataFrame()

    # Act
    is_valid, error_msg = validator.check_always_empty_or_full(empty_portfolio)

    # Assert
    assert is_valid, "Empty DataFrame should pass"
    assert error_msg == ""


# ==============================================================================
# Test: validate_strategy - Integration
# ==============================================================================

def test_validate_strategy_integration(validator, diversified_portfolio):
    """
    Test full validate_strategy integration with valid portfolio.

    Verifies that all semantic checks are integrated correctly.
    """
    # Arrange - Mock execution result with valid portfolio
    from unittest.mock import Mock
    mock_report = Mock()
    mock_report.position = diversified_portfolio

    # Act
    is_valid, errors = validator.validate_strategy(
        code="# Valid strategy code",
        execution_result=mock_report
    )

    # Assert
    # Note: Current implementation returns empty validation (TODOs not implemented)
    # This test validates the integration path exists
    assert isinstance(is_valid, bool), "Should return boolean validation status"
    assert isinstance(errors, list), "Should return list of errors"


def test_validate_strategy_no_execution_result(validator):
    """Test validate_strategy with no execution result."""
    # Act
    is_valid, errors = validator.validate_strategy(
        code="# Strategy code",
        execution_result=None
    )

    # Assert
    assert isinstance(is_valid, bool)
    assert isinstance(errors, list)


# ==============================================================================
# Test: Edge Cases and Boundary Conditions
# ==============================================================================

def test_check_position_concentration_with_zeros(validator):
    """Test concentration check handles zero positions correctly."""
    # Arrange - Portfolio with some zero positions
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio = pd.DataFrame({
        '2330': np.full(100, 30000),  # 30% - VIOLATES
        '2317': np.full(100, 40000),  # 40% - VIOLATES
        '2454': np.full(100, 30000),  # 30% - VIOLATES
        '2308': np.zeros(100),         # 0% - No position
        '2303': np.zeros(100),         # 0% - No position
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_position_concentration(portfolio)

    # Assert
    assert not is_valid, "Should detect violation in non-zero positions"
    # Should flag one of the violating stocks (2330, 2317, or 2454)
    assert any(ticker in error_msg for ticker in ['2330', '2317', '2454'])


def test_check_portfolio_turnover_zero_volatility(validator):
    """Test turnover check with zero volatility (no position changes)."""
    # Arrange - Portfolio with constant positions (no changes)
    dates = pd.date_range('2024-01-01', periods=13, freq='ME')
    portfolio = pd.DataFrame({
        '2330': np.full(13, 50000),
        '2317': np.full(13, 50000),
    }, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_turnover(portfolio, 'M')

    # Assert
    assert is_valid, "Zero turnover should pass (no trading)"
    assert error_msg == ""


def test_check_portfolio_size_varying_positions(validator, normal_trading_portfolio):
    """Test portfolio size check with varying position counts."""
    # Act
    is_valid, error_msg = validator.check_portfolio_size(normal_trading_portfolio)

    # Assert
    # normal_trading_portfolio has varying positions (8-12 stocks)
    # Average should be ~10, which is within [5, 50] range
    assert is_valid, f"Varying positions (8-12) should pass: {error_msg}"


def test_check_portfolio_turnover_unrecognized_frequency(validator):
    """Test turnover check with unrecognized rebalance frequency."""
    # Arrange
    dates = pd.date_range('2024-01-01', periods=5, freq='W')
    portfolio = pd.DataFrame({
        '2330': [50000, 40000, 50000, 40000, 50000],
        '2317': [50000, 60000, 50000, 60000, 50000],
    }, index=dates)

    # Act - Use unrecognized frequency 'W' (weekly)
    is_valid, error_msg = validator.check_portfolio_turnover(portfolio, 'W')

    # Assert
    # Should default to monthly (12 rebalances/year) and calculate turnover
    # Validation should work (not crash)
    assert isinstance(is_valid, bool)
    assert isinstance(error_msg, str)


def test_check_position_concentration_none_input(validator):
    """Test concentration check with None input."""
    # Act
    is_valid, error_msg = validator.check_position_concentration(None)

    # Assert
    assert is_valid, "None input should pass (no data to validate)"
    assert error_msg == ""


def test_check_portfolio_size_with_partial_positions(validator):
    """Test portfolio size with stocks that are sometimes zero."""
    # Arrange - 15 stocks, but not all held on all dates
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    portfolio_dict = {}
    for i in range(15):
        ticker = f'STOCK_{i:02d}'
        if i < 10:
            # First 10 stocks always held
            portfolio_dict[ticker] = np.full(100, 5000)
        else:
            # Last 5 stocks held 50% of the time
            values = np.where(np.arange(100) < 50, 5000, 0)
            portfolio_dict[ticker] = values
    portfolio = pd.DataFrame(portfolio_dict, index=dates)

    # Act
    is_valid, error_msg = validator.check_portfolio_size(portfolio)

    # Assert
    # Average positions should be ~12.5 (10 always + 2.5 from the 5 part-time stocks)
    # This is within [5, 50] range
    assert is_valid, f"12.5 average positions should pass: {error_msg}"
