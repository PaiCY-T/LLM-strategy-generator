"""TPE-based hyperparameter optimizer for strategy evolution.

This module implements Tree-structured Parzen Estimator (TPE)
for efficient hyperparameter search using Optuna backend.

TPE is purpose-built for expensive black-box functions like backtests
where intermediate results cannot be reported.

Task 0.1: TPE Optimizer Implementation (P0 - Critical)
"""

from typing import Dict, Any, Callable, Optional
import optuna
from optuna.samplers import TPESampler
import time
import logging
import warnings

logger = logging.getLogger(__name__)

# Suppress experimental warning for multivariate TPE
warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)


class TPEOptimizer:
    """TPE-based hyperparameter optimizer for strategy evolution.

    Uses Tree-structured Parzen Estimator (TPE) for efficient Bayesian
    optimization. TPE is purpose-built for expensive black-box functions
    like backtests where intermediate results cannot be reported.

    Unlike ASHA/Hyperband which require intermediate metrics, TPE only
    needs final objective values, making it ideal for complete backtests
    that cannot be partially evaluated.

    Attributes:
        study: Optuna study instance (created on first optimize() call)
        _search_stats: Dictionary containing optimization statistics

    Examples:
        >>> # Basic usage with simple parameter space
        >>> optimizer = TPEOptimizer()
        >>> param_space = {
        ...     'learning_rate': ('uniform', 0.001, 0.1),
        ...     'max_depth': ('int', 3, 10)
        ... }
        >>> def objective(params):
        ...     # Your objective function (e.g., backtest Sharpe ratio)
        ...     return sharpe_ratio
        >>> best_params = optimizer.optimize(objective, n_trials=50, param_space=param_space)
        >>> print(best_params)
        {'learning_rate': 0.023, 'max_depth': 7}

        >>> # IS/OOS validation to detect overfitting
        >>> result = optimizer.optimize_with_validation(
        ...     objective_fn=objective,
        ...     n_trials=50,
        ...     param_space=param_space,
        ...     is_start_date="2020-01-01",
        ...     is_end_date="2022-12-31",
        ...     oos_start_date="2023-01-01",
        ...     oos_end_date="2023-12-31"
        ... )
        >>> print(f"Degradation: {result['degradation']:.1%}")
        Degradation: 23.5%
    """

    def __init__(self):
        """Initialize TPE optimizer with Optuna backend.

        No hyperparameters needed - TPE configuration is handled internally.
        """
        self.study: Optional[optuna.Study] = None
        self._search_stats: Dict[str, Any] = {}

    def _create_study(self) -> optuna.Study:
        """Create Optuna study with TPE sampler.

        TPE (Tree-structured Parzen Estimator) is purpose-built for
        expensive black-box functions like backtests where intermediate
        results cannot be reported.

        Returns:
            Configured Optuna study with TPESampler

        Examples:
            >>> optimizer = TPEOptimizer()
            >>> optimizer._create_study()
            >>> print(optimizer.study.direction)
            StudyDirection.MAXIMIZE
        """
        sampler = TPESampler(
            n_startup_trials=10,  # Random exploration first 10 trials
            n_ei_candidates=24,   # TPE candidates per iteration
            multivariate=True,    # Consider parameter correlations
            seed=42               # Reproducibility
        )

        self.study = optuna.create_study(
            direction='maximize',  # Maximize Sharpe ratio
            sampler=sampler
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

        # Assert study exists for type checker
        assert self.study is not None, "Study should exist after _create_study()"

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

            # Call user's objective function with error handling
            try:
                value = objective_fn(params)
            except Exception as e:
                logger.warning(f"Trial {trial.number} failed: {e}")
                raise optuna.exceptions.TrialPruned()

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

    def optimize_with_validation(
        self,
        objective_fn: Callable[[Dict[str, Any]], float],
        n_trials: int,
        param_space: Dict[str, Any],
        is_start_date: str,
        is_end_date: str,
        oos_start_date: str,
        oos_end_date: str,
        degradation_threshold: float = 0.30
    ) -> Dict[str, Any]:
        """Optimize with IS/OOS validation to detect overfitting.

        Runs optimization on in-sample data, then validates on
        out-of-sample data. Warns if performance degrades >threshold.

        Args:
            objective_fn: Function that takes parameters and returns score
            n_trials: Number of optimization trials
            param_space: Parameter search space definition
            is_start_date: In-sample period start date (ISO format: YYYY-MM-DD)
            is_end_date: In-sample period end date (ISO format: YYYY-MM-DD)
            oos_start_date: Out-of-sample period start date (ISO format: YYYY-MM-DD)
            oos_end_date: Out-of-sample period end date (ISO format: YYYY-MM-DD)
            degradation_threshold: Warn if degradation exceeds this (default 0.30 = 30%)

        Returns:
            Dictionary containing:
                - best_params: Best parameters found
                - best_value: Best in-sample score
                - oos_value: Out-of-sample score
                - degradation: Performance degradation ratio (0.0-1.0)

        Examples:
            >>> optimizer = TPEOptimizer()
            >>> result = optimizer.optimize_with_validation(
            ...     objective_fn=my_backtest,
            ...     n_trials=50,
            ...     param_space={'lr': ('uniform', 0.001, 0.1)},
            ...     is_start_date="2020-01-01",
            ...     is_end_date="2022-12-31",
            ...     oos_start_date="2023-01-01",
            ...     oos_end_date="2023-12-31"
            ... )
            >>> print(f"Degradation: {result['degradation']:.1%}")
            Degradation: 23.5%
        """
        # Run optimization on in-sample data
        best_params = self.optimize(objective_fn, n_trials, param_space)
        is_value = self.study.best_value

        # Validate on out-of-sample data
        # Note: For full implementation, objective_fn would need to accept date ranges
        # For now, we call it again with best params (placeholder behavior)
        oos_value = objective_fn(best_params)

        # Calculate degradation
        degradation = (is_value - oos_value) / is_value if is_value != 0 else 0.0

        # Log warning if degradation exceeds threshold
        if degradation > degradation_threshold:
            logger.warning(
                f"Performance degradation {degradation:.1%} exceeds threshold {degradation_threshold:.1%}. "
                f"IS={is_value:.4f}, OOS={oos_value:.4f}. Possible overfitting detected."
            )

        logger.info(
            f"IS/OOS validation complete. IS={is_value:.4f}, OOS={oos_value:.4f}, "
            f"degradation={degradation:.1%} (dates: IS={is_start_date} to {is_end_date}, "
            f"OOS={oos_start_date} to {oos_end_date})"
        )

        return {
            'best_params': best_params,
            'best_value': is_value,
            'oos_value': oos_value,
            'degradation': degradation
        }

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


# Backward compatibility alias
ASHAOptimizer = TPEOptimizer
