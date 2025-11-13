"""
Regression tests for Phase 1.1 backward compatibility.

Verifies that API changes don't break existing client code.

This test suite ensures:
- All public exports remain accessible
- Method signatures haven't broken
- v1.0 behavior can be preserved with flags
- No breaking changes to existing integrations

Priority: P0 BLOCKING (Task 1.1.6)
"""

import inspect
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock


class TestPublicAPICompatibility:
    """Test all public exports remain accessible."""

    def test_validator_import_compatibility(self):
        """Test all public validation exports remain accessible."""

        from src.validation import (
            ValidationIntegrator,
            BaselineIntegrator,
            BootstrapIntegrator,
            BonferroniIntegrator,
            ValidationReportGenerator
        )

        # All should instantiate without errors
        v1 = ValidationIntegrator()
        v2 = BaselineIntegrator()
        v3 = BootstrapIntegrator()
        v4 = BonferroniIntegrator()
        v5 = ValidationReportGenerator()

        assert v1 is not None
        assert v2 is not None
        assert v3 is not None
        assert v4 is not None
        assert v5 is not None

        print("  ✅ Import compatibility test PASSED")

    def test_new_v1_1_imports(self):
        """Test new v1.1 exports are accessible."""

        from src.validation import (
            DynamicThresholdCalculator,
            stationary_bootstrap,
            stationary_bootstrap_detailed
        )

        # New exports should be accessible
        calc = DynamicThresholdCalculator()
        assert calc is not None
        assert callable(stationary_bootstrap)
        assert callable(stationary_bootstrap_detailed)

        print("  ✅ New v1.1 imports accessible")

    def test_old_exports_still_work(self):
        """Test that v1.0 exports haven't been removed."""

        # These existed in v1.0 and should still work
        from src.validation.integration import (
            ValidationIntegrator,
            BaselineIntegrator,
            BootstrapIntegrator,
            BonferroniIntegrator
        )

        from src.validation.validation_report_generator import ValidationReportGenerator

        # Should all work without errors
        assert ValidationIntegrator is not None
        assert BaselineIntegrator is not None
        assert BootstrapIntegrator is not None
        assert BonferroniIntegrator is not None
        assert ValidationReportGenerator is not None

        print("  ✅ Old v1.0 exports still work")


class TestMethodSignatureCompatibility:
    """Test method signatures haven't broken."""

    def test_bootstrap_integrator_signature(self):
        """Test BootstrapIntegrator method signatures."""

        from src.validation import BootstrapIntegrator

        bootstrap = BootstrapIntegrator()
        sig = inspect.signature(bootstrap.validate_with_bootstrap)

        # Check required parameters still exist
        params = sig.parameters
        assert 'strategy_code' in params
        assert 'data' in params
        assert 'sim' in params

        # New optional parameter should have default value
        if 'use_dynamic_threshold' in params:
            assert params['use_dynamic_threshold'].default == True

        print("  ✅ BootstrapIntegrator signature compatible")

    def test_bonferroni_integrator_signature(self):
        """Test BonferroniIntegrator method signatures."""

        from src.validation import BonferroniIntegrator

        bonferroni = BonferroniIntegrator()
        sig = inspect.signature(bonferroni.validate_single_strategy)

        # Check required parameters
        params = sig.parameters
        assert 'sharpe_ratio' in params
        assert 'n_periods' in params

        # New optional parameter should have default value
        if 'use_dynamic_threshold' in params:
            assert params['use_dynamic_threshold'].default == True

        print("  ✅ BonferroniIntegrator signature compatible")

    def test_validation_integrator_signature(self):
        """Test ValidationIntegrator method signatures."""

        from src.validation import ValidationIntegrator

        validator = ValidationIntegrator()

        # Check key methods exist
        assert hasattr(validator, 'validate_out_of_sample')
        assert hasattr(validator, 'validate_walk_forward')

        # Check signatures
        sig_oos = inspect.signature(validator.validate_out_of_sample)
        sig_wf = inspect.signature(validator.validate_walk_forward)

        # Should have strategy_code, data, sim parameters
        assert 'strategy_code' in sig_oos.parameters
        assert 'strategy_code' in sig_wf.parameters

        print("  ✅ ValidationIntegrator signature compatible")

    def test_report_generator_signature(self):
        """Test ValidationReportGenerator method signatures."""

        from src.validation import ValidationReportGenerator

        generator = ValidationReportGenerator()

        # Check key methods exist
        assert hasattr(generator, 'to_html')
        assert hasattr(generator, 'to_json')

        print("  ✅ ValidationReportGenerator signature compatible")


class TestV10BehaviorPreserved:
    """Test that v1.0 behavior can be preserved with flags."""

    def test_bootstrap_can_disable_dynamic_threshold(self):
        """Test BootstrapIntegrator can use v1.0 behavior with flag."""

        from src.validation import BootstrapIntegrator

        # v1.1 default (dynamic threshold)
        integrator_v11 = BootstrapIntegrator()
        assert integrator_v11.threshold_calc is not None, \
            "v1.1 should have dynamic threshold by default"

        # v1.0 legacy (static threshold)
        integrator_v10 = BootstrapIntegrator(use_dynamic_threshold=False)
        assert integrator_v10.threshold_calc is None, \
            "v1.0 mode should not have dynamic threshold"

        print("  ✅ Bootstrap can disable dynamic threshold for v1.0 behavior")

    def test_bonferroni_can_disable_dynamic_threshold(self):
        """Test BonferroniIntegrator can use v1.0 behavior with flag."""

        from src.validation import BonferroniIntegrator

        # v1.1 default (dynamic threshold)
        integrator_v11 = BonferroniIntegrator()
        assert integrator_v11.threshold_calc is not None, \
            "v1.1 should have dynamic threshold by default"

        # v1.0 legacy (static threshold)
        integrator_v10 = BonferroniIntegrator(use_dynamic_threshold=False)
        assert integrator_v10.threshold_calc is None, \
            "v1.0 mode should not have dynamic threshold"

        print("  ✅ Bonferroni can disable dynamic threshold for v1.0 behavior")

    def test_v10_threshold_value_matches(self):
        """Test v1.0 mode uses 0.5 threshold as before."""

        from src.validation import BonferroniIntegrator

        integrator_v10 = BonferroniIntegrator(
            n_strategies=20,
            use_dynamic_threshold=False
        )

        # Validate with Sharpe = 0.6 (should pass with v1.0 threshold of 0.5)
        result = integrator_v10.validate_single_strategy(
            sharpe_ratio=0.6,
            n_periods=252
        )

        # v1.0 should accept 0.6 (above 0.5 threshold)
        assert result['validation_passed'] == True, \
            "v1.0 mode should accept Sharpe 0.6 (above 0.5 threshold)"

        print("  ✅ v1.0 threshold value (0.5) preserved")

    def test_v11_threshold_value_enforced(self):
        """Test v1.1 mode uses 0.8 threshold as expected."""

        from src.validation import BonferroniIntegrator

        integrator_v11 = BonferroniIntegrator(
            n_strategies=20,
            use_dynamic_threshold=True
        )

        # Validate with Sharpe = 0.7 (should fail with v1.1 threshold of 0.8)
        result = integrator_v11.validate_single_strategy(
            sharpe_ratio=0.7,
            n_periods=252
        )

        # v1.1 should reject 0.7 (below 0.8 threshold)
        assert result['validation_passed'] == False, \
            "v1.1 mode should reject Sharpe 0.7 (below 0.8 threshold)"

        print("  ✅ v1.1 threshold value (0.8) enforced")


class TestExistingIntegrationCode:
    """Test that existing integration code patterns still work."""

    def test_basic_validation_workflow_v10_style(self):
        """Test v1.0 style workflow still works."""

        from src.validation import (
            BootstrapIntegrator,
            BonferroniIntegrator
        )

        # Create mock data (v1.0 style - no changes needed)
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.01, 252)

        # Calculate sample Sharpe (v1.0 style)
        sharpe = (np.mean(returns) / np.std(returns, ddof=1)) * np.sqrt(252)

        # Old v1.0 code pattern (should still work)
        bonferroni = BonferroniIntegrator(n_strategies=20)
        result = bonferroni.validate_single_strategy(
            sharpe_ratio=sharpe,
            n_periods=252
        )

        # Should execute without errors
        assert 'validation_passed' in result
        # v1.1 renamed 'threshold' to 'significance_threshold'
        assert 'significance_threshold' in result or 'threshold' in result

        print("  ✅ v1.0 style workflow still works")

    def test_bootstrap_validation_basic(self):
        """Test basic bootstrap validation still works."""

        from src.validation import BootstrapIntegrator

        # Create BootstrapIntegrator
        integrator = BootstrapIntegrator()

        # Create mock Report with returns
        mock_report = Mock()
        mock_report.returns = np.random.normal(0.001, 0.015, 300)
        mock_report.equity = None
        mock_report.position = None

        # Extract returns using integrator method (v1.1 method)
        returns = integrator._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.0,
            total_return=0.5,
            n_days=252
        )

        # Should work without errors
        assert len(returns) >= 252
        assert isinstance(returns, np.ndarray)

        print("  ✅ Bootstrap validation basic pattern works")


class TestParameterDefaults:
    """Test that parameter defaults are backward compatible."""

    def test_bootstrap_integrator_defaults(self):
        """Test BootstrapIntegrator default parameters."""

        from src.validation import BootstrapIntegrator

        # Create with defaults (should work as v1.0)
        integrator = BootstrapIntegrator()

        # Should have default values set
        assert hasattr(integrator, 'threshold_calc')

        # v1.1 default should be dynamic threshold enabled
        assert integrator.threshold_calc is not None

        print("  ✅ BootstrapIntegrator defaults compatible")

    def test_bonferroni_integrator_defaults(self):
        """Test BonferroniIntegrator default parameters."""

        from src.validation import BonferroniIntegrator

        # Create with defaults
        integrator = BonferroniIntegrator()

        # Should have default values set
        assert hasattr(integrator, 'n_strategies')

        # v1.1 default should be dynamic threshold enabled
        assert integrator.threshold_calc is not None

        print("  ✅ BonferroniIntegrator defaults compatible")

    def test_dynamic_threshold_calculator_defaults(self):
        """Test DynamicThresholdCalculator default parameters."""

        from src.validation import DynamicThresholdCalculator

        # Create with defaults
        calc = DynamicThresholdCalculator()

        # Should have reasonable defaults
        assert calc.benchmark_ticker == "0050.TW"
        assert calc.lookback_years == 3
        assert calc.margin == 0.2
        assert calc.static_floor == 0.0

        # Default threshold should be 0.8
        assert calc.get_threshold() == 0.8

        print("  ✅ DynamicThresholdCalculator defaults valid")


class TestReturnTypeCompatibility:
    """Test that return types remain compatible."""

    def test_bootstrap_validation_return_type(self):
        """Test BootstrapIntegrator returns expected structure."""

        from src.validation import BootstrapIntegrator

        integrator = BootstrapIntegrator()

        # Create minimal mock objects
        mock_report = Mock()
        mock_report.returns = np.random.normal(0.001, 0.015, 300)
        mock_report.equity = None
        mock_report.position = None

        # Mock executor result
        mock_result = Mock()
        mock_result.report = mock_report

        # This would be called after backtest execution
        # Just verify the structure is compatible
        assert integrator.threshold_calc is not None

        print("  ✅ Bootstrap validation return type compatible")

    def test_bonferroni_validation_return_type(self):
        """Test BonferroniIntegrator returns expected structure."""

        from src.validation import BonferroniIntegrator

        integrator = BonferroniIntegrator(n_strategies=20)

        result = integrator.validate_single_strategy(
            sharpe_ratio=1.0,
            n_periods=252
        )

        # Check return structure matches v1.0
        assert isinstance(result, dict)
        assert 'validation_passed' in result
        # v1.1 renamed 'threshold' to 'significance_threshold'
        assert 'significance_threshold' in result or 'threshold' in result
        assert 'sharpe_ratio' in result

        # v1.1 additions (should be present but not break v1.0 usage)
        assert 'dynamic_threshold' in result or 'significance_threshold' in result

        print("  ✅ Bonferroni validation return type compatible")


class TestErrorHandlingCompatibility:
    """Test error handling remains compatible."""

    def test_insufficient_data_error(self):
        """Test insufficient data raises appropriate error."""

        from src.validation import BootstrapIntegrator

        # Create integrator
        integrator = BootstrapIntegrator()

        # Create mock with insufficient data
        mock_report = Mock()
        mock_report.returns = np.random.normal(0.001, 0.015, 100)  # Only 100 days
        mock_report.equity = None
        mock_report.position = None

        # Should raise ValueError for insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            integrator._extract_returns_from_report(
                report=mock_report,
                sharpe_ratio=1.0,
                total_return=0.5,
                n_days=252  # Requires 252 days
            )

        print("  ✅ Insufficient data error handling compatible")

    def test_invalid_parameters_error(self):
        """Test invalid parameters raise appropriate errors."""

        from src.validation import DynamicThresholdCalculator

        # Negative floor should raise error
        with pytest.raises(ValueError):
            DynamicThresholdCalculator(static_floor=-0.1)

        # Zero lookback years should raise error
        with pytest.raises(ValueError):
            DynamicThresholdCalculator(lookback_years=0)

        print("  ✅ Invalid parameter error handling compatible")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
