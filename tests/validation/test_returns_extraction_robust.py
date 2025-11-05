"""
Test suite for robust returns extraction from finlab Report objects.

This tests the v1.1 implementation that removed returns synthesis and uses
only actual data extraction methods.

Task 1.1.1: Replace Returns Synthesis with Equity Curve Extraction
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock
from src.validation.integration import BootstrapIntegrator


class TestReturnsExtractionRobust:
    """Test the 4-layer extraction strategy."""

    def setup_method(self):
        """Setup test fixtures."""
        self.integrator = BootstrapIntegrator(executor=None)

    def test_method1_direct_returns_attribute(self):
        """Test extraction from report.returns (Method 1)."""
        # Create mock report with returns attribute
        mock_report = Mock()
        mock_report.returns = np.random.randn(300)  # 300 days

        # Extract returns
        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        # Verify
        assert returns is not None
        assert len(returns) == 300
        assert isinstance(returns, np.ndarray)

    def test_method1_insufficient_data_raises_error(self):
        """Test that <252 days raises ValueError (Method 1)."""
        mock_report = Mock()
        mock_report.returns = np.random.randn(100)  # Only 100 days

        with pytest.raises(ValueError, match="Insufficient data.*100 days < 252"):
            self.integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.5,
                total_return=0.20,
                n_days=252
            )

    def test_method2_daily_returns_attribute(self):
        """Test extraction from report.daily_returns (Method 2)."""
        mock_report = Mock()
        mock_report.returns = None  # Method 1 unavailable
        mock_report.daily_returns = np.random.randn(365)  # 365 days

        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        assert returns is not None
        assert len(returns) == 365

    def test_method3_equity_series_pct_change(self):
        """Test extraction from report.equity as Series (Method 3)."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None

        # Create equity curve as Series
        dates = pd.date_range('2020-01-01', periods=300, freq='D')
        equity_curve = pd.Series(
            100000 * (1 + 0.0005) ** np.arange(300),  # Growing equity
            index=dates
        )
        mock_report.equity = equity_curve

        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        # Verify extraction worked
        assert returns is not None
        assert len(returns) == 299  # pct_change() drops first row
        assert isinstance(returns, np.ndarray)

        # Verify returns are reasonable
        assert np.all(np.isfinite(returns))
        assert np.mean(returns) > 0  # Growing equity should have positive returns

    def test_method3_equity_dataframe_first_column(self):
        """Test extraction from report.equity as DataFrame (Method 3)."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None

        # Create equity curve as DataFrame with multiple columns
        dates = pd.date_range('2020-01-01', periods=300, freq='D')
        equity_df = pd.DataFrame({
            'equity': 100000 * (1 + 0.0005) ** np.arange(300),
            'other_column': np.random.randn(300)
        }, index=dates)
        mock_report.equity = equity_df

        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        assert returns is not None
        assert len(returns) == 299  # First column used

    def test_method3_equity_insufficient_data(self):
        """Test that equity with <252 days raises error (Method 3)."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None

        # Only 100 days
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        equity_curve = pd.Series(100000 * (1 + 0.001) ** np.arange(100), index=dates)
        mock_report.equity = equity_curve

        with pytest.raises(ValueError, match="Insufficient data.*99 days < 252"):
            self.integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.5,
                total_return=0.20,
                n_days=252
            )

    def test_method4_position_dataframe_sum(self):
        """Test extraction from report.position (Method 4)."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None
        mock_report.equity = None

        # Create position DataFrame (multiple positions)
        dates = pd.date_range('2020-01-01', periods=300, freq='D')
        position_df = pd.DataFrame({
            'stock_A': np.random.randn(300) * 1000 + 50000,
            'stock_B': np.random.randn(300) * 1000 + 30000,
            'stock_C': np.random.randn(300) * 1000 + 20000
        }, index=dates)
        mock_report.position = position_df

        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        assert returns is not None
        assert len(returns) == 299  # pct_change() drops first row

    def test_all_methods_fail_raises_detailed_error(self):
        """Test that all extraction failures produces detailed error message."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None
        mock_report.equity = None
        mock_report.position = None

        with pytest.raises(ValueError) as exc_info:
            self.integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.5,
                total_return=0.20,
                n_days=252
            )

        error_msg = str(exc_info.value)
        # Verify error message contains key information
        assert "Failed to extract returns" in error_msg
        assert "Tried methods: returns, daily_returns, equity, position" in error_msg
        assert "Available attributes" in error_msg
        assert "CRITICAL: Returns synthesis has been removed" in error_msg

    def test_no_synthesis_fallback_exists(self):
        """Verify that synthesis fallback has been completely removed."""
        # This is a meta-test to ensure no code path leads to synthesis
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None
        mock_report.equity = None
        mock_report.position = None

        # Should raise, not synthesize
        with pytest.raises(ValueError):
            self.integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.5,  # Would be used in synthesis
                total_return=0.20,  # Would be used in synthesis
                n_days=252
            )

    def test_extraction_preserves_actual_returns_properties(self):
        """Test that extracted returns preserve actual data properties."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None

        # Create realistic equity curve with known properties
        # - Trending upward
        # - Volatility clustering
        # - Fat tails (occasional large moves)
        np.random.seed(42)
        n = 500
        returns_true = []
        for i in range(n):
            if i % 50 == 0:  # Fat tail event every 50 days
                ret = np.random.normal(0, 0.05)
            else:
                ret = np.random.normal(0.0005, 0.01)
            returns_true.append(ret)

        returns_true = np.array(returns_true)
        equity_curve = pd.Series(100000 * np.cumprod(1 + returns_true))
        mock_report.equity = equity_curve
        mock_report.position = None

        # Extract returns
        extracted_returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.0,
            total_return=0.25,
            n_days=252
        )

        # Verify extracted returns match calculated returns
        calculated_returns = equity_curve.pct_change().dropna().values
        np.testing.assert_array_almost_equal(extracted_returns, calculated_returns)

        # Verify properties preserved
        assert len(extracted_returns) == n - 1  # pct_change drops first
        assert np.mean(extracted_returns) > 0  # Trending up
        assert np.std(extracted_returns) > 0  # Has volatility

    def test_sharpe_total_return_parameters_unused(self):
        """Test that sharpe_ratio and total_return are truly unused (backward compatibility)."""
        mock_report = Mock()
        mock_report.returns = np.random.randn(300)

        # These should have NO effect on extraction
        returns1 = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        returns2 = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=999.9,  # Absurd value
            total_return=-0.99,  # Absurd value
            n_days=252
        )

        # Should be identical (same report.returns)
        np.testing.assert_array_equal(returns1, returns2)

    def test_n_days_parameter_controls_minimum_requirement(self):
        """Test that n_days parameter correctly controls minimum data requirement."""
        mock_report = Mock()
        mock_report.returns = np.random.randn(150)  # 150 days

        # Should succeed with n_days=100
        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=100
        )
        assert len(returns) == 150

        # Should fail with n_days=252
        with pytest.raises(ValueError, match="150 days < 252"):
            self.integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.5,
                total_return=0.20,
                n_days=252
            )

    def test_extraction_handles_nan_in_equity_curve(self):
        """Test that pct_change().dropna() correctly handles NaN values."""
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None

        # Equity curve with some NaN values
        equity_values = np.random.randn(300).cumsum() + 100000
        equity_values[50] = np.nan  # Inject NaN
        equity_values[150] = np.nan

        equity_curve = pd.Series(equity_values)
        mock_report.equity = equity_curve
        mock_report.position = None

        returns = self.integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.5,
            total_return=0.20,
            n_days=252
        )

        # Verify NaN values removed
        assert np.all(np.isfinite(returns))
        assert len(returns) < 299  # Some values dropped due to NaN


class TestBootstrapIntegrationWithRobustExtraction:
    """Test that bootstrap validation uses the robust extraction."""

    def test_bootstrap_uses_actual_returns_not_synthesis(self):
        """Integration test: verify bootstrap receives actual returns."""
        # This would require mocking BacktestExecutor and verifying
        # that the bootstrap receives actual equity-derived returns
        # Detailed implementation deferred to E2E tests (Task 1.1.4)
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
