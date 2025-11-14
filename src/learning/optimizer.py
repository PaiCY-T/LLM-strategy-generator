"""ASHA-based hyperparameter optimizer for strategy evolution.

This module implements Asynchronous Successive Halving Algorithm (ASHA)
for efficient hyperparameter search using Optuna backend.

P0.2 Implementation Target: Week 2-3
Expected Improvement: 50-70% reduction in search time
"""

from typing import Dict, Any, Callable, Optional
import optuna
from optuna.pruners import HyperbandPruner
import time


class ASHAOptimizer:
    """ASHA-based hyperparameter optimizer for strategy evolution.

    Uses multi-fidelity optimization with early stopping to efficiently
    search high-dimensional parameter spaces. Integrates with Optuna for
    robust trial management and pruning logic.

    Attributes:
        n_iterations: Maximum iterations per trial
        min_resource: Minimum backtest iterations before pruning
        reduction_factor: Factor for successive halving (default: 3)
        grace_period: Number of iterations before pruning starts

    Examples:
        >>> optimizer = ASHAOptimizer(n_iterations=100, min_resource=3)
        >>> param_space = {
        ...     'learning_rate': ('uniform', 0.001, 0.1),
        ...     'max_depth': ('int', 3, 10)
        ... }
        >>> best_params = optimizer.optimize(objective_fn, param_space, n_trials=50)
        >>> print(best_params)
        {'learning_rate': 0.023, 'max_depth': 7}
    """

    def __init__(
        self,
        reduction_factor: int = 4,
        min_resource: int = 1,
        max_resource: int = 81
    ):
        """Initialize ASHA optimizer with Optuna backend.

        Args:
            reduction_factor: Factor for successive halving (default: 4)
            min_resource: Minimum resource allocation before pruning (default: 1)
            max_resource: Maximum resource allocation (default: 81)

        Raises:
            ValueError: If reduction_factor < 2 or min_resource <= 0
        """
        if reduction_factor < 2:
            raise ValueError(f"reduction_factor must be >= 2, got {reduction_factor}")
        if min_resource <= 0:
            raise ValueError(f"min_resource must be > 0, got {min_resource}")

        self.reduction_factor = reduction_factor
        self.min_resource = min_resource
        self.max_resource = max_resource
        self.study: Optional[optuna.Study] = None
        self._search_stats: Dict[str, Any] = {}

    def _create_study(self) -> optuna.Study:
        """Create Optuna study with ASHA (Hyperband) pruner.

        Returns:
            Configured Optuna study with HyperbandPruner

        Examples:
            >>> optimizer = ASHAOptimizer()
            >>> optimizer._create_study()
            >>> print(optimizer.study.direction)
            StudyDirection.MAXIMIZE
        """
        pruner = HyperbandPruner(
            min_resource=self.min_resource,
            max_resource=self.max_resource,
            reduction_factor=self.reduction_factor
        )

        self.study = optuna.create_study(
            direction='maximize',  # Maximize Sharpe ratio
            pruner=pruner
        )
        return self.study

    def optimize(
        self,
        objective_fn: Callable[[Dict[str, Any]], float],
        n_trials: int,
        param_space: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run ASHA optimization and return best parameters.

        Args:
            objective_fn: Function that takes parameters dict and returns score
            n_trials: Number of trials to run
            param_space: Dictionary defining parameter search space
                Format: {param_name: (type, *args)}
                Types: 'uniform' (min, max), 'int' (min, max),
                       'categorical' (choices,), 'log_uniform' (min, max)

        Returns:
            Dictionary containing best parameters found

        Raises:
            ValueError: If n_trials <= 0

        Examples:
            >>> def objective(params):
            ...     # Simulate backtest with params
            ...     return sharpe_ratio
            >>> optimizer = ASHAOptimizer()
            >>> param_space = {'lr': ('uniform', 0.001, 0.1)}
            >>> best = optimizer.optimize(objective, n_trials=20, param_space=param_space)
        """
        # Validation
        if n_trials <= 0:
            raise ValueError(f"n_trials must be > 0, got {n_trials}")

        # Create study if not exists
        if self.study is None:
            self._create_study()

        # Track start time
        start_time = time.time()

        # Define objective wrapper for Optuna
        def objective_wrapper(trial: optuna.Trial) -> float:
            # Suggest parameters based on param_space
            params = {}
            for param_name, param_config in param_space.items():
                param_type = param_config[0]

                if param_type == 'uniform':
                    params[param_name] = trial.suggest_float(
                        param_name, param_config[1], param_config[2]
                    )
                elif param_type == 'int':
                    params[param_name] = trial.suggest_int(
                        param_name, param_config[1], param_config[2]
                    )
                elif param_type == 'categorical':
                    params[param_name] = trial.suggest_categorical(
                        param_name, param_config[1]
                    )
                elif param_type == 'log_uniform':
                    params[param_name] = trial.suggest_float(
                        param_name, param_config[1], param_config[2], log=True
                    )
                else:
                    raise ValueError(f"Unknown parameter type: {param_type}")

            # Call user's objective function
            value = objective_fn(params)

            # Report intermediate value for pruning
            # ASHA uses resource allocation, report at max_resource
            trial.report(value, step=self.max_resource)

            # Check if trial should be pruned
            if trial.should_prune():
                raise optuna.TrialPruned()

            return value

        # Run optimization
        self.study.optimize(objective_wrapper, n_trials=n_trials, catch=(optuna.TrialPruned,))

        # Collect statistics
        search_time = time.time() - start_time
        n_complete = len([t for t in self.study.trials if t.state == optuna.trial.TrialState.COMPLETE])
        n_pruned = len([t for t in self.study.trials if t.state == optuna.trial.TrialState.PRUNED])
        pruning_rate = n_pruned / n_trials if n_trials > 0 else 0.0

        self._search_stats = {
            'n_trials': n_trials,
            'n_pruned': n_pruned,
            'pruning_rate': pruning_rate,
            'best_value': self.study.best_value,
            'best_params': self.study.best_params,
            'search_time': search_time
        }

        return self.study.best_params

    def early_stop_callback(
        self,
        study: optuna.Study,
        trial: optuna.Trial
    ) -> None:
        """Callback for early stopping logic.

        Args:
            study: Current Optuna study
            trial: Current trial being evaluated

        Examples:
            >>> study = optimizer.create_study()
            >>> trial = study.ask()
            >>> optimizer.early_stop_callback(study, trial)
        """
        # TODO: Implement callback logic
        # 1. Check if within grace period
        # 2. Compare current performance to threshold
        # 3. Prune if underperforming
        raise NotImplementedError("P0.2: To be implemented in Week 2-3")

    def get_search_stats(self) -> Dict[str, Any]:
        """Return optimization statistics.

        Returns:
            Dictionary containing:
                - n_trials: Total trials run
                - n_pruned: Number of pruned trials
                - pruning_rate: Fraction of trials pruned (0.0-1.0)
                - best_value: Best score achieved
                - best_params: Best parameters found
                - search_time: Total search time in seconds

        Raises:
            RuntimeError: If optimize() has not been called yet

        Examples:
            >>> optimizer.optimize(objective_fn, n_trials=50, param_space=param_space)
            >>> stats = optimizer.get_search_stats()
            >>> print(f"Pruned {stats['n_pruned']} trials")
        """
        if not self._search_stats:
            raise RuntimeError("optimize() must be called before get_search_stats()")

        return self._search_stats
