"""TDD Test Suite for ASHA Hyperparameter Optimizer.

This test suite follows Test-Driven Development principles:
1. All tests written BEFORE implementation (RED phase)
2. Tests define the desired behavior of ASHAOptimizer
3. Implementation should make these tests pass (GREEN phase)

Tests cover ASHA (Asynchronous Successive Halving Algorithm) optimization
using Optuna's HyperbandPruner for efficient hyperparameter search.

Test Structure:
- Phase 1: Initialization and Study Creation (8 tests)
- Phase 2: Optimization Behavior (10 tests)
Total: 18 tests ensuring robust ASHA implementation
"""

import pytest
import optuna
from typing import Dict, Any
import time


# ============================================================================
# PHASE 1: Initialization and Study Creation Tests (8 tests)
# ============================================================================

class TestASHAInitialization:
    """RED Phase 1: Test suite for ASHAOptimizer initialization."""

    def test_init_with_valid_parameters(self):
        """RED: ASHAOptimizer should initialize with valid parameters."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer(reduction_factor=4, min_resource=1, max_resource=81)

        assert optimizer.reduction_factor == 4
        assert optimizer.min_resource == 1
        assert optimizer.max_resource == 81
        assert optimizer.study is None  # Study not created yet

    def test_init_with_default_parameters(self):
        """RED: ASHAOptimizer should use default parameters."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()

        # Defaults from spec: reduction_factor=4, min_resource=1, max_resource=81
        assert optimizer.reduction_factor == 4
        assert optimizer.min_resource == 1
        assert optimizer.max_resource == 81

    def test_init_raises_on_invalid_reduction_factor(self):
        """RED: reduction_factor < 2 should raise ValueError."""
        from src.learning.optimizer import ASHAOptimizer

        with pytest.raises(ValueError, match="reduction_factor must be >= 2"):
            ASHAOptimizer(reduction_factor=1)

        with pytest.raises(ValueError, match="reduction_factor must be >= 2"):
            ASHAOptimizer(reduction_factor=0)

    def test_init_raises_on_invalid_min_resource(self):
        """RED: min_resource <= 0 should raise ValueError."""
        from src.learning.optimizer import ASHAOptimizer

        with pytest.raises(ValueError, match="min_resource must be > 0"):
            ASHAOptimizer(min_resource=0)

        with pytest.raises(ValueError, match="min_resource must be > 0"):
            ASHAOptimizer(min_resource=-1)


class TestASHAStudyCreation:
    """RED Phase 1: Test suite for Optuna study creation."""

    def test_create_study_returns_optuna_study(self):
        """RED: _create_study() should return optuna.Study instance."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()
        optimizer._create_study()

        assert isinstance(optimizer.study, optuna.Study)

    def test_create_study_configures_pruner_correctly(self):
        """RED: Study should use HyperbandPruner with correct parameters."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer(reduction_factor=3, min_resource=2, max_resource=27)
        optimizer._create_study()

        # Verify pruner type
        assert isinstance(optimizer.study.pruner, optuna.pruners.HyperbandPruner)

        # Verify pruner parameters
        pruner = optimizer.study.pruner
        assert pruner._reduction_factor == 3
        assert pruner._min_resource == 2
        assert pruner._max_resource == 27

    def test_create_study_sets_maximize_direction(self):
        """RED: Study direction should be MAXIMIZE."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()
        optimizer._create_study()

        assert optimizer.study.direction == optuna.study.StudyDirection.MAXIMIZE

    def test_create_study_stores_in_instance(self):
        """RED: Study should be stored in self.study attribute."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()

        # Initially None
        assert optimizer.study is None

        # After creation
        optimizer._create_study()
        assert optimizer.study is not None
        assert isinstance(optimizer.study, optuna.Study)


# ============================================================================
# PHASE 2: Optimization Behavior Tests (10 tests)
# ============================================================================

class TestASHAOptimization:
    """RED Phase 2: Test suite for ASHA optimization behavior."""

    def test_optimize_returns_best_parameters(self):
        """RED: optimize() should return dict with best parameters."""
        from src.learning.optimizer import ASHAOptimizer

        def simple_objective(params: Dict[str, Any]) -> float:
            """Simple quadratic objective: maximize -(x^2)."""
            return -(params['x'] ** 2)

        optimizer = ASHAOptimizer()
        param_space = {
            'x': ('uniform', -5.0, 5.0)
        }

        best_params = optimizer.optimize(simple_objective, n_trials=10, param_space=param_space)

        assert isinstance(best_params, dict)
        assert 'x' in best_params
        # Best x should be close to 0 (maximum of -(x^2))
        assert abs(best_params['x']) < 1.0

    def test_optimize_calls_objective_correct_times(self):
        """RED: optimize() should call objective_fn n_trials times (accounting for pruning)."""
        from src.learning.optimizer import ASHAOptimizer

        call_count = {'n': 0}

        def counting_objective(params: Dict[str, Any]) -> float:
            call_count['n'] += 1
            return params['x'] ** 2

        optimizer = ASHAOptimizer()
        param_space = {'x': ('uniform', -5.0, 5.0)}

        optimizer.optimize(counting_objective, n_trials=20, param_space=param_space)

        # Should call objective approximately n_trials times
        # Some trials may be pruned early, so total calls might be less
        assert call_count['n'] <= 20

    def test_optimize_prunes_underperforming_trials(self):
        """RED: optimize() should prune 50-70% of trials (ASHA behavior)."""
        from src.learning.optimizer import ASHAOptimizer

        def simple_objective(params: Dict[str, Any]) -> float:
            return params['x'] ** 2

        optimizer = ASHAOptimizer()
        param_space = {'x': ('uniform', -5.0, 5.0)}

        optimizer.optimize(simple_objective, n_trials=30, param_space=param_space)
        stats = optimizer.get_search_stats()

        # ASHA should prune 50-70% of trials
        assert 0.5 <= stats['pruning_rate'] <= 0.7

    def test_optimize_handles_trial_pruned_exception(self):
        """RED: optimize() should catch TrialPruned gracefully."""
        from src.learning.optimizer import ASHAOptimizer

        def pruning_objective(params: Dict[str, Any]) -> float:
            # Some trials will be pruned by ASHA
            return params['x'] ** 2

        optimizer = ASHAOptimizer()
        param_space = {'x': ('uniform', -5.0, 5.0)}

        # Should not raise exception even though some trials are pruned
        best_params = optimizer.optimize(pruning_objective, n_trials=20, param_space=param_space)

        assert isinstance(best_params, dict)

    def test_optimize_validates_n_trials_positive(self):
        """RED: n_trials <= 0 should raise ValueError."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()
        param_space = {'x': ('uniform', -5.0, 5.0)}

        def dummy_objective(params: Dict[str, Any]) -> float:
            return 0.0

        with pytest.raises(ValueError, match="n_trials must be > 0"):
            optimizer.optimize(dummy_objective, n_trials=0, param_space=param_space)

        with pytest.raises(ValueError, match="n_trials must be > 0"):
            optimizer.optimize(dummy_objective, n_trials=-5, param_space=param_space)


class TestASHASearchStats:
    """RED Phase 2: Test suite for search statistics."""

    def test_get_search_stats_returns_complete_dict(self):
        """RED: get_search_stats() should return all required keys."""
        from src.learning.optimizer import ASHAOptimizer

        def simple_objective(params: Dict[str, Any]) -> float:
            return params['x'] ** 2

        optimizer = ASHAOptimizer()
        param_space = {'x': ('uniform', -5.0, 5.0)}

        optimizer.optimize(simple_objective, n_trials=10, param_space=param_space)
        stats = optimizer.get_search_stats()

        # Required keys from spec
        assert 'n_trials' in stats
        assert 'n_pruned' in stats
        assert 'pruning_rate' in stats
        assert 'best_value' in stats
        assert 'best_params' in stats
        assert 'search_time' in stats

    def test_get_search_stats_raises_before_optimize(self):
        """RED: get_search_stats() should raise RuntimeError if optimize() not called."""
        from src.learning.optimizer import ASHAOptimizer

        optimizer = ASHAOptimizer()

        with pytest.raises(RuntimeError, match="optimize\\(\\) must be called before"):
            optimizer.get_search_stats()

    def test_pruning_rate_within_expected_range(self):
        """RED: Pruning rate should be 50-70% for ASHA."""
        from src.learning.optimizer import ASHAOptimizer

        def simple_objective(params: Dict[str, Any]) -> float:
            return params['x'] ** 2 + params['y'] ** 2

        optimizer = ASHAOptimizer()
        param_space = {
            'x': ('uniform', -5.0, 5.0),
            'y': ('uniform', -5.0, 5.0)
        }

        optimizer.optimize(simple_objective, n_trials=50, param_space=param_space)
        stats = optimizer.get_search_stats()

        # ASHA should prune 50-70% of trials
        assert 0.5 <= stats['pruning_rate'] <= 0.7
        assert stats['n_pruned'] == stats['n_trials'] * stats['pruning_rate']


class TestASHAParameterTypes:
    """RED Phase 2: Test suite for different parameter types."""

    def test_optimize_with_multiple_parameter_types(self):
        """RED: optimize() should handle uniform, int, categorical parameters."""
        from src.learning.optimizer import ASHAOptimizer

        def multi_param_objective(params: Dict[str, Any]) -> float:
            # Combine different parameter types
            x_contrib = params['x'] ** 2
            n_contrib = params['n'] * 0.1
            category_contrib = 1.0 if params['method'] == 'best' else 0.5
            return -(x_contrib + n_contrib + category_contrib)

        optimizer = ASHAOptimizer()
        param_space = {
            'x': ('uniform', -5.0, 5.0),
            'n': ('int', 1, 10),
            'method': ('categorical', ['best', 'good', 'bad'])
        }

        best_params = optimizer.optimize(multi_param_objective, n_trials=20, param_space=param_space)

        # Verify all parameter types present
        assert 'x' in best_params
        assert 'n' in best_params
        assert 'method' in best_params

        # Verify types
        assert isinstance(best_params['x'], float)
        assert isinstance(best_params['n'], int)
        assert best_params['method'] in ['best', 'good', 'bad']

    def test_convergence_within_max_trials(self):
        """RED: optimize() should find near-optimal solution within max_trials."""
        from src.learning.optimizer import ASHAOptimizer

        def convex_objective(params: Dict[str, Any]) -> float:
            # Simple convex function: maximize -(x^2 + y^2)
            # Optimal at x=0, y=0
            return -(params['x'] ** 2 + params['y'] ** 2)

        optimizer = ASHAOptimizer()
        param_space = {
            'x': ('uniform', -10.0, 10.0),
            'y': ('uniform', -10.0, 10.0)
        }

        best_params = optimizer.optimize(convex_objective, n_trials=50, param_space=param_space)
        stats = optimizer.get_search_stats()

        # Should find solution close to optimal (x=0, y=0)
        assert abs(best_params['x']) < 2.0
        assert abs(best_params['y']) < 2.0

        # Best value should be close to 0 (maximum)
        assert stats['best_value'] > -5.0  # Within reasonable tolerance
