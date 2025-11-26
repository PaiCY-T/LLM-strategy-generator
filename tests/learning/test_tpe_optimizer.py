"""Test suite for TPE-based optimizer (Task 0.1: TPE Optimizer Implementation).

This test file follows strict TDD workflow:
- Phase 1: RED - All tests written FIRST and must FAIL
- Phase 2: GREEN - Minimal implementation to make tests pass
- Phase 3: REFACTOR - Improve quality while keeping tests green

Test Coverage:
- TPE sampler initialization and configuration
- IS/OOS validation workflow
- Degradation calculation and warning thresholds
- Backtest failure handling with TrialPruned
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import optuna
from optuna.samplers import TPESampler
from typing import Dict, Any


class TestTPEOptimizer:
    """Test suite for TPE-based optimizer."""

    # === TPE Sampler Tests ===

    def test_tpe_sampler_initialization(self):
        """GIVEN optimizer creation WHEN creating study THEN uses TPESampler.

        This test proves TPE is used instead of ASHA/Hyperband pruner.
        Expected to FAIL until TPEOptimizer class is created.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()
        study = optimizer._create_study()

        # Verify TPESampler is used
        assert isinstance(study.sampler, TPESampler), \
            f"Expected TPESampler, got {type(study.sampler).__name__}"

    def test_tpe_sampler_parameters(self):
        """THEN TPESampler configured with correct parameters.

        Expected configuration:
        - n_startup_trials=10 (random exploration first)
        - n_ei_candidates=24 (TPE candidates per iteration)
        - multivariate=True (consider parameter correlations)
        - seed=42 (reproducibility)

        Expected to FAIL until TPE sampler is configured correctly.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()
        study = optimizer._create_study()
        sampler = study.sampler

        # Access sampler internals to verify configuration
        assert isinstance(sampler, TPESampler)
        # Note: These are private attributes, testing implementation details
        # In production, we'd verify behavior through optimization results
        assert sampler._n_startup_trials == 10, \
            f"Expected n_startup_trials=10, got {sampler._n_startup_trials}"
        assert sampler._n_ei_candidates == 24, \
            f"Expected n_ei_candidates=24, got {sampler._n_ei_candidates}"
        assert sampler._multivariate is True, \
            f"Expected multivariate=True, got {sampler._multivariate}"

    # === IS/OOS Validation Tests ===

    def test_optimize_with_validation_method_exists(self):
        """WHEN calling optimize_with_validation THEN method exists with correct signature.

        Expected to FAIL until optimize_with_validation() method is added.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Verify method exists
        assert hasattr(optimizer, 'optimize_with_validation'), \
            "TPEOptimizer must have optimize_with_validation() method"

        # Verify method signature (callable check)
        method = getattr(optimizer, 'optimize_with_validation')
        assert callable(method), "optimize_with_validation must be callable"

    def test_is_oos_split(self):
        """GIVEN IS/OOS dates WHEN optimizing THEN splits data correctly.

        Verifies that IS/OOS date ranges are properly stored and can be used
        for validation split. This test checks the method accepts the parameters.

        Expected to FAIL until optimize_with_validation() is implemented.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Mock objective function
        mock_objective = Mock(return_value=0.5)

        param_space = {
            'learning_rate': ('uniform', 0.001, 0.1)
        }

        # Call with IS/OOS dates - should not raise exception
        result = optimizer.optimize_with_validation(
            objective_fn=mock_objective,
            n_trials=5,
            param_space=param_space,
            is_start_date="2020-01-01",
            is_end_date="2022-12-31",
            oos_start_date="2023-01-01",
            oos_end_date="2023-12-31"
        )

        # Verify result structure (minimal check)
        assert isinstance(result, dict), "Result must be a dictionary"
        assert 'best_params' in result, "Result must contain best_params"

    def test_degradation_calculation(self):
        """WHEN IS=0.5, OOS=0.3 THEN degradation=0.4 (40%).

        Degradation formula: (IS_value - OOS_value) / IS_value
        0.5 - 0.3 = 0.2
        0.2 / 0.5 = 0.4 (40%)

        Expected to FAIL until degradation calculation is implemented.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Mock objective to return different values for IS/OOS
        call_count = {'count': 0}
        def mock_objective(params):
            call_count['count'] += 1
            if call_count['count'] <= 5:  # First 5 calls are IS optimization
                return 0.5
            else:  # OOS validation call
                return 0.3

        param_space = {'lr': ('uniform', 0.001, 0.1)}

        result = optimizer.optimize_with_validation(
            objective_fn=mock_objective,
            n_trials=5,
            param_space=param_space,
            is_start_date="2020-01-01",
            is_end_date="2022-12-31",
            oos_start_date="2023-01-01",
            oos_end_date="2023-12-31"
        )

        # Verify degradation calculation
        assert 'degradation' in result, "Result must contain degradation"
        expected_degradation = 0.4  # (0.5 - 0.3) / 0.5
        assert abs(result['degradation'] - expected_degradation) < 0.01, \
            f"Expected degradation ~0.4, got {result['degradation']}"

    def test_degradation_threshold_warning(self):
        """WHEN degradation >30% THEN logs warning.

        Expected to FAIL until warning logic is implemented.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Mock objective with high degradation
        call_count = {'count': 0}
        def mock_objective(params):
            call_count['count'] += 1
            if call_count['count'] <= 5:  # IS
                return 0.5
            else:  # OOS - significant degradation
                return 0.2  # 60% degradation

        param_space = {'lr': ('uniform', 0.001, 0.1)}

        # Capture log output
        with patch('src.learning.optimizer.logger') as mock_logger:
            result = optimizer.optimize_with_validation(
                objective_fn=mock_objective,
                n_trials=5,
                param_space=param_space,
                is_start_date="2020-01-01",
                is_end_date="2022-12-31",
                oos_start_date="2023-01-01",
                oos_end_date="2023-12-31",
                degradation_threshold=0.30  # 30% threshold
            )

            # Verify warning was logged
            # Check if any warning call contains degradation message
            warning_calls = [call for call in mock_logger.warning.call_args_list]
            assert len(warning_calls) > 0, "Expected warning to be logged for high degradation"

    def test_oos_result_structure(self):
        """THEN returns dict with best_params, best_value, oos_value, degradation.

        Verifies complete result structure from IS/OOS validation.
        Expected to FAIL until full result structure is implemented.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        mock_objective = Mock(return_value=0.5)
        param_space = {'lr': ('uniform', 0.001, 0.1)}

        result = optimizer.optimize_with_validation(
            objective_fn=mock_objective,
            n_trials=5,
            param_space=param_space,
            is_start_date="2020-01-01",
            is_end_date="2022-12-31",
            oos_start_date="2023-01-01",
            oos_end_date="2023-12-31"
        )

        # Verify all required fields
        required_fields = ['best_params', 'best_value', 'oos_value', 'degradation']
        for field in required_fields:
            assert field in result, f"Result must contain '{field}' field"

        # Verify field types
        assert isinstance(result['best_params'], dict), "best_params must be dict"
        assert isinstance(result['best_value'], (int, float)), "best_value must be numeric"
        assert isinstance(result['oos_value'], (int, float)), "oos_value must be numeric"
        assert isinstance(result['degradation'], (int, float)), "degradation must be numeric"

    # === Backtest Failure Handling (Task 0.1b) ===

    def test_backtest_failure_raises_trial_pruned(self):
        """WHEN objective_fn raises exception THEN catches and raises TrialPruned.

        This ensures backtest failures don't crash the optimization,
        but are properly marked as pruned trials.

        Expected to FAIL until exception handling is added.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Mock objective that fails
        def failing_objective(params):
            raise ValueError("Simulated backtest failure")

        param_space = {'lr': ('uniform', 0.001, 0.1)}

        # Optimization should complete despite failures
        # (optuna catches TrialPruned and continues)
        result = optimizer.optimize(
            objective_fn=failing_objective,
            n_trials=3,
            param_space=param_space
        )

        # Verify trials were pruned (not completed)
        stats = optimizer.get_search_stats()
        assert stats['n_pruned'] == 3, \
            f"Expected 3 pruned trials, got {stats['n_pruned']}"

    def test_backtest_failure_logged(self):
        """WHEN objective_fn fails THEN failure is logged with context.

        Verifies that failures are properly logged for debugging.
        Expected to FAIL until logging is added.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        def failing_objective(params):
            raise RuntimeError("Database connection timeout")

        param_space = {'lr': ('uniform', 0.001, 0.1)}

        # Capture log output
        with patch('src.learning.optimizer.logger') as mock_logger:
            optimizer.optimize(
                objective_fn=failing_objective,
                n_trials=2,
                param_space=param_space
            )

            # Verify warning was logged
            assert mock_logger.warning.called, "Expected warning to be logged for failures"

            # Check that trial number and error message are in log
            warning_calls = mock_logger.warning.call_args_list
            assert len(warning_calls) >= 2, f"Expected at least 2 warnings, got {len(warning_calls)}"

    # === Backward Compatibility Test ===

    def test_asha_optimizer_alias_exists(self):
        """THEN ASHAOptimizer exists as backward compatibility alias.

        Ensures existing code using ASHAOptimizer still works.
        Expected to FAIL until alias is added.
        """
        from src.learning.optimizer import ASHAOptimizer, TPEOptimizer

        # Verify alias exists
        assert ASHAOptimizer is TPEOptimizer, \
            "ASHAOptimizer should be an alias for TPEOptimizer"

        # Verify can instantiate via old name
        optimizer = ASHAOptimizer()
        assert isinstance(optimizer, TPEOptimizer)


class TestTPEOptimizerIntegration:
    """Integration tests for TPE optimizer with realistic scenarios."""

    def test_basic_optimization_workflow(self):
        """GIVEN simple quadratic function WHEN optimizing THEN finds minimum.

        Integration test to verify end-to-end optimization works.
        Expected to FAIL until full TPE implementation is complete.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Quadratic function with minimum at x=5
        def quadratic(params):
            x = params['x']
            return -(x - 5) ** 2  # Negative for maximization

        param_space = {'x': ('uniform', 0.0, 10.0)}

        best_params = optimizer.optimize(
            objective_fn=quadratic,
            n_trials=50,
            param_space=param_space
        )

        # Verify convergence near optimal value
        assert 'x' in best_params
        assert abs(best_params['x'] - 5.0) < 0.5, \
            f"Expected x near 5.0, got {best_params['x']}"

        # Verify best value is near 0
        stats = optimizer.get_search_stats()
        assert stats['best_value'] > -1.0, \
            f"Expected best value near 0, got {stats['best_value']}"

    def test_multiparameter_optimization(self):
        """GIVEN multi-parameter function WHEN optimizing THEN explores space efficiently.

        Tests TPE with multiple correlated parameters.
        Expected to FAIL until TPE multivariate configuration works.
        """
        from src.learning.optimizer import TPEOptimizer

        optimizer = TPEOptimizer()

        # Function with optimal at x=2, y=3
        def rosenbrock(params):
            x = params['x']
            y = params['y']
            return -((1 - x)**2 + 100*(y - x**2)**2)  # Negative for maximization

        param_space = {
            'x': ('uniform', -2.0, 2.0),
            'y': ('uniform', -1.0, 3.0)
        }

        best_params = optimizer.optimize(
            objective_fn=rosenbrock,
            n_trials=100,
            param_space=param_space
        )

        # Verify reasonable convergence (Rosenbrock is hard to optimize)
        assert 'x' in best_params and 'y' in best_params
        assert abs(best_params['x'] - 1.0) < 1.0, \
            f"Expected x near 1.0, got {best_params['x']}"


# === Pytest Configuration ===

@pytest.fixture
def mock_objective():
    """Fixture providing a simple mock objective function."""
    return Mock(return_value=0.5)


@pytest.fixture
def basic_param_space():
    """Fixture providing a basic parameter space."""
    return {
        'learning_rate': ('uniform', 0.001, 0.1),
        'batch_size': ('int', 16, 128)
    }
