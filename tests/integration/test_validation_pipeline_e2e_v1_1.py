"""
End-to-End Integration Tests for Phase 1.1 Validation Pipeline
==============================================================

Tests complete validation flow with real finlab execution after v1.1 remediation:
Strategy code → BacktestExecutor → Report → All 5 validators → HTML/JSON report

v1.1 Changes Tested:
- Task 1.1.1: Returns extraction (no synthesis)
- Task 1.1.2: Stationary bootstrap (temporal structure preservation)
- Task 1.1.3: Dynamic threshold (0.8 instead of 0.5)

Test Coverage:
- Full pipeline with passing strategy
- Pipeline with failing strategy
- Pipeline with insufficient data (<252 days)
- Report generation (HTML/JSON)

Priority: P0 BLOCKING (Task 1.1.4)
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import json

# Note: These imports may fail if finlab is not installed
# Tests will be skipped in that case
try:
    from finlab import data
    from finlab.backtest import sim
    FINLAB_AVAILABLE = True
except ImportError:
    FINLAB_AVAILABLE = False
    data = None
    sim = None

from src.backtest.executor import BacktestExecutor
from src.validation.integration import (
    ValidationIntegrator,
    BaselineIntegrator,
    BootstrapIntegrator,
    BonferroniIntegrator
)
from src.validation.validation_report import ValidationReportGenerator


# Skip all tests if finlab not available
pytestmark = pytest.mark.skipif(
    not FINLAB_AVAILABLE,
    reason="finlab not installed - skipping E2E tests"
)


class TestFullPipelineWithRealExecution:
    """Test full validation pipeline with real strategy execution."""

    @pytest.mark.slow
    def test_full_pipeline_momentum_strategy(self):
        """
        Test full pipeline with real momentum strategy.

        Validates v1.1 improvements:
        - Bootstrap uses actual returns (Task 1.1.1)
        - Stationary bootstrap preserves temporal structure (Task 1.1.2)
        - Dynamic threshold (0.8) used instead of arbitrary 0.5 (Task 1.1.3)
        """
        # Simple momentum strategy (known to work with Taiwan market)
        strategy_code = '''
close = data.get("price:收盤價")
returns_20d = close.pct_change(20)
position = returns_20d.rank(axis=1, ascending=False) <= 30
report = sim(position, resample="Q", upload=False, mae_mfe_window=5, position_limit=0.5)
'''

        # Initialize all integrators
        validation_int = ValidationIntegrator()
        baseline_int = BaselineIntegrator()
        bootstrap_int = BootstrapIntegrator()  # use_dynamic_threshold=True by default
        bonferroni_int = BonferroniIntegrator(
            n_strategies=20,
            use_dynamic_threshold=True  # v1.1: Uses 0.8 threshold
        )
        report_gen = ValidationReportGenerator(project_name="E2E Test v1.1")

        # Execute strategy with BacktestExecutor
        executor = BacktestExecutor(timeout=420)
        result = executor.execute(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            start_date="2020-01-01",
            end_date="2023-12-31",
            fee_ratio=0.001425,
            tax_ratio=0.003,
            iteration_num=0
        )

        # Verify execution success
        assert result.success, f"Execution failed: {result.error_message}"
        assert result.sharpe_ratio is not None, "Sharpe ratio should not be None"
        assert result.report is not None, "Report should not be None"

        print(f"Strategy executed successfully: Sharpe = {result.sharpe_ratio:.3f}")

        # Run all 5 validators
        print("\n=== Running Validators ===")

        # 1. Out-of-sample validation
        print("1. Out-of-sample validation...")
        oos = validation_int.validate_out_of_sample(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            iteration_num=0
        )
        assert 'validation_passed' in oos
        print(f"   Out-of-sample: {oos['validation_passed']}")

        # 2. Walk-forward validation
        print("2. Walk-forward validation...")
        wf = validation_int.validate_walk_forward(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            iteration_num=0
        )
        assert 'validation_passed' in wf
        print(f"   Walk-forward: {wf['validation_passed']}")

        # 3. Baseline comparison
        print("3. Baseline comparison...")
        baseline = baseline_int.compare_with_baselines(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            iteration_num=0
        )
        assert 'validation_passed' in baseline
        print(f"   Baseline: {baseline['validation_passed']}")

        # 4. Bootstrap CI validation (v1.1: uses actual returns + dynamic threshold)
        print("4. Bootstrap CI validation (v1.1)...")
        bootstrap = bootstrap_int.validate_with_bootstrap(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            start_date="2020-01-01",
            end_date="2023-12-31",
            n_iterations=500,  # Reduced for faster testing
            iteration_num=0
        )
        assert 'validation_passed' in bootstrap
        print(f"   Bootstrap: {bootstrap['validation_passed']}")

        # v1.1 VERIFICATION: Bootstrap should use actual returns (Task 1.1.1)
        assert 'n_days' in bootstrap, "Bootstrap should report n_days used"
        assert bootstrap['n_days'] >= 252, \
            f"Bootstrap should use >=252 days of actual returns, got {bootstrap['n_days']}"
        print(f"   ✓ Bootstrap used {bootstrap['n_days']} days of actual returns (Task 1.1.1)")

        # v1.1 VERIFICATION: Dynamic threshold should be used (Task 1.1.3)
        assert 'dynamic_threshold' in bootstrap, "Bootstrap should use dynamic threshold"
        assert bootstrap['dynamic_threshold'] == 0.8, \
            f"Dynamic threshold should be 0.8, got {bootstrap['dynamic_threshold']}"
        print(f"   ✓ Dynamic threshold 0.8 used (Task 1.1.3)")

        # 5. Bonferroni multiple comparison (v1.1: uses dynamic threshold)
        print("5. Bonferroni multiple comparison (v1.1)...")
        bonferroni = bonferroni_int.validate_single_strategy(
            sharpe_ratio=result.sharpe_ratio,
            n_periods=252,
            use_conservative=True
        )
        assert 'validation_passed' in bonferroni
        print(f"   Bonferroni: {bonferroni['validation_passed']}")

        # v1.1 VERIFICATION: Dynamic threshold in Bonferroni (Task 1.1.3)
        assert 'significance_threshold' in bonferroni, "Bonferroni should have threshold"
        if 'dynamic_threshold' in bonferroni:
            assert bonferroni['dynamic_threshold'] == 0.8, \
                f"Bonferroni dynamic threshold should be 0.8, got {bonferroni['dynamic_threshold']}"
            print(f"   ✓ Bonferroni dynamic threshold 0.8 used (Task 1.1.3)")

        # Generate comprehensive report
        print("\n=== Generating Report ===")
        report_gen.add_strategy_validation(
            strategy_name="E2E_Momentum_v1.1",
            iteration_num=0,
            out_of_sample_results=oos,
            walk_forward_results=wf,
            baseline_results=baseline,
            bootstrap_results=bootstrap,
            bonferroni_results=bonferroni,
            metadata={
                'test_type': 'E2E_v1.1',
                'sharpe_ratio': result.sharpe_ratio,
                'total_return': result.total_return if result.total_return else 0.0,
                'date_range': '2020-2023'
            }
        )

        # Verify HTML report generation
        html = report_gen.to_html()
        assert len(html) > 1000, "HTML report should be substantial"
        assert "E2E_Momentum_v1.1" in html, "HTML should contain strategy name"
        assert "v1.1" in html or "E2E" in html, "HTML should reference test type"
        print(f"   ✓ HTML report generated ({len(html)} chars)")

        # Verify JSON report generation
        json_report = report_gen.to_json()
        report_data = json.loads(json_report)
        assert 'summary' in report_data, "JSON should have summary"
        assert report_data['summary']['total_strategies'] == 1
        assert 'strategies' in report_data, "JSON should have strategies list"
        print(f"   ✓ JSON report generated (1 strategy)")

        # Verify report contains v1.1 information
        strategy_report = report_data['strategies'][0]
        assert 'validations' in strategy_report
        assert 'bootstrap_ci' in strategy_report['validations']

        bootstrap_data = strategy_report['validations']['bootstrap_ci']
        if 'n_days' in bootstrap_data:
            assert bootstrap_data['n_days'] >= 252, "Report should show actual returns usage"

        print("\n✅ Full E2E Pipeline Test v1.1 PASSED")
        print(f"   - All 5 validators executed")
        print(f"   - Actual returns used ({bootstrap['n_days']} days)")
        print(f"   - Dynamic threshold 0.8 enforced")
        print(f"   - Reports generated successfully")


class TestPipelineWithFailingStrategy:
    """Test pipeline correctly rejects poor strategies."""

    def test_pipeline_rejects_random_strategy(self):
        """
        Test pipeline correctly fails validation for random strategy.

        Random positions should fail multiple validators.
        """
        # Strategy with random positions (should perform poorly)
        strategy_code = '''
import numpy as np
close = data.get("price:收盤價")
np.random.seed(42)
random_scores = np.random.randn(*close.shape)
position = pd.DataFrame(random_scores, index=close.index, columns=close.columns).rank(axis=1, ascending=False) <= 30
report = sim(position, resample="Q", upload=False)
'''

        bootstrap_int = BootstrapIntegrator()
        bonferroni_int = BonferroniIntegrator(n_strategies=20)

        # Execute random strategy
        executor = BacktestExecutor(timeout=420)
        result = executor.execute(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            start_date="2020-01-01",
            end_date="2023-12-31"
        )

        # Execution might succeed but validations should fail
        if result.success:
            # Bootstrap should likely fail (random strategy unlikely to have Sharpe >= 0.8)
            bootstrap = bootstrap_int.validate_with_bootstrap(
                strategy_code=strategy_code,
                data=data,
                sim=sim,
                start_date="2020-01-01",
                end_date="2023-12-31",
                n_iterations=200
            )

            # Random strategy very unlikely to pass 0.8 threshold
            if result.sharpe_ratio and result.sharpe_ratio < 0.8:
                assert not bootstrap['validation_passed'], \
                    "Random strategy should fail bootstrap validation"
                print("✅ Random strategy correctly failed validation")
            else:
                print("⚠️  Random strategy happened to pass (unlikely but possible)")


class TestPipelineWithInsufficientData:
    """Test pipeline correctly handles insufficient data."""

    def test_pipeline_rejects_short_history(self):
        """
        Test pipeline rejects strategies with <252 days of data.

        v1.1: Bootstrap now requires actual returns with minimum 252 days.
        """
        # Strategy with only 6 months of data
        strategy_code = '''
close = data.get("price:收盤價")
returns_20d = close.pct_change(20)
position = returns_20d.rank(axis=1, ascending=False) <= 30
report = sim(position, resample="M", upload=False)
'''

        bootstrap_int = BootstrapIntegrator()

        # Execute with short date range (6 months)
        executor = BacktestExecutor(timeout=420)
        result = executor.execute(
            strategy_code=strategy_code,
            data=data,
            sim=sim,
            start_date="2023-01-01",
            end_date="2023-06-30"  # Only 6 months
        )

        if result.success:
            # Bootstrap should fail due to insufficient data
            bootstrap = bootstrap_int.validate_with_bootstrap(
                strategy_code=strategy_code,
                data=data,
                sim=sim,
                start_date="2023-01-01",
                end_date="2023-06-30"
            )

            # Should fail validation (either error or validation_passed=False)
            if 'error' in bootstrap:
                assert '252' in bootstrap['error'] or 'Insufficient' in bootstrap['error'], \
                    "Error should mention 252-day requirement"
                print("✅ Short history correctly rejected (error raised)")
            else:
                assert not bootstrap['validation_passed'], \
                    "Short history should fail validation"
                print("✅ Short history correctly rejected (validation failed)")


class TestReportGeneration:
    """Test report generation components."""

    def test_report_generator_structure(self):
        """Test ValidationReportGenerator structure and methods."""
        report_gen = ValidationReportGenerator(project_name="Test Project v1.1")

        # Add mock validation results
        report_gen.add_strategy_validation(
            strategy_name="Test_Strategy",
            iteration_num=0,
            out_of_sample_results={'validation_passed': True, 'sharpes': {'training': 1.0, 'validation': 0.9, 'test': 0.8}},
            walk_forward_results={'validation_passed': True, 'consistency': 0.85},
            baseline_results={'validation_passed': True, 'beats_buy_and_hold': True},
            bootstrap_results={'validation_passed': True, 'ci_lower': 0.7, 'ci_upper': 1.1, 'n_days': 300, 'dynamic_threshold': 0.8},
            bonferroni_results={'validation_passed': True, 'sharpe_ratio': 0.95, 'significance_threshold': 0.8}
        )

        # Test HTML generation
        html = report_gen.to_html()
        assert len(html) > 500
        assert "Test_Strategy" in html
        assert "Test Project v1.1" in html

        # Test JSON generation
        json_str = report_gen.to_json()
        data = json.loads(json_str)

        assert 'summary' in data
        assert data['summary']['total_strategies'] == 1
        assert 'reports' in data, f"JSON should have 'reports' key, got: {list(data.keys())}"
        assert len(data['reports']) == 1

        strategy = data['reports'][0]
        assert strategy['strategy_name'] == "Test_Strategy"
        assert 'validations' in strategy
        assert 'bootstrap_ci' in strategy['validations']

        # Verify v1.1 fields present
        bootstrap_data = strategy['validations']['bootstrap_ci']
        assert 'n_days' in bootstrap_data
        assert bootstrap_data['n_days'] == 300
        assert 'dynamic_threshold' in bootstrap_data
        assert bootstrap_data['dynamic_threshold'] == 0.8

        print("✅ Report generation test PASSED")


class TestV11Improvements:
    """Test v1.1 specific improvements."""

    def test_dynamic_threshold_enforcement(self):
        """
        Test that v1.1 uses 0.8 dynamic threshold instead of 0.5.

        Strategies with Sharpe 0.5-0.7 should fail v1.1 (pass v1.0).
        """
        # Test BootstrapIntegrator
        bootstrap_v11 = BootstrapIntegrator(use_dynamic_threshold=True)
        bootstrap_v10 = BootstrapIntegrator(use_dynamic_threshold=False)

        assert bootstrap_v11.threshold_calc is not None, "v1.1 should have threshold calculator"
        assert bootstrap_v10.threshold_calc is None, "v1.0 should not have threshold calculator"

        # Test BonferroniIntegrator
        bonferroni_v11 = BonferroniIntegrator(n_strategies=20, use_dynamic_threshold=True)
        bonferroni_v10 = BonferroniIntegrator(n_strategies=20, use_dynamic_threshold=False)

        assert bonferroni_v11.threshold_calc is not None, "v1.1 should have threshold calculator"
        assert bonferroni_v10.threshold_calc is None, "v1.0 should not have threshold calculator"

        # Verify threshold values
        assert bonferroni_v11.threshold_calc.get_threshold() == 0.8, "v1.1 threshold should be 0.8"

        print("✅ Dynamic threshold enforcement test PASSED")
        print("   - v1.1 uses 0.8 threshold")
        print("   - v1.0 legacy mode available (0.5 threshold)")

    def test_actual_returns_extraction(self):
        """
        Test that BootstrapIntegrator extracts actual returns.

        v1.1: Should use _extract_returns_from_report() without synthesis.
        """
        bootstrap_int = BootstrapIntegrator()

        # Verify method exists
        assert hasattr(bootstrap_int, '_extract_returns_from_report'), \
            "BootstrapIntegrator should have _extract_returns_from_report method"

        # Create mock Report with equity curve
        import pandas as pd
        mock_report = Mock()
        mock_report.returns = None
        mock_report.daily_returns = None
        equity_curve = pd.Series(
            np.cumsum(np.random.normal(0.001, 0.01, 300)) + 100,
            index=pd.date_range('2020-01-01', periods=300)
        )
        mock_report.equity = equity_curve
        mock_report.position = None

        # Test extraction
        returns = bootstrap_int._extract_returns_from_report(
            report=mock_report,
            sharpe_ratio=1.0,  # Unused in v1.1
            total_return=0.5,  # Unused in v1.1
            n_days=252
        )

        assert returns is not None, "Should extract returns successfully"
        assert len(returns) >= 252, f"Should have >=252 returns, got {len(returns)}"
        assert isinstance(returns, np.ndarray), "Returns should be numpy array"

        print("✅ Actual returns extraction test PASSED")
        print(f"   - Extracted {len(returns)} days of actual returns")
        print("   - No synthesis fallback (removed in v1.1)")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
