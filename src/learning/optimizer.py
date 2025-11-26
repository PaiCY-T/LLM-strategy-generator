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

    def __init__(self) -> None:
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
        # Suppress experimental warning for multivariate TPE
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)

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

    def optimize_with_template(
        self,
        template_name: str,
        objective_fn: Callable[[str, Dict], float],
        n_trials: int,
        asset_universe: list[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Optimize template parameters with data caching.

        Integrates TPE Optimizer with Template Library to:
        1. Cache market data once (70% speedup)
        2. Optimize template parameters across n_trials
        3. Return best parameters and strategy code

        Args:
            template_name: Template to optimize (e.g., 'Momentum')
            objective_fn: Function(strategy_code: str, cached_data: Dict) -> float
            n_trials: Number of TPE optimization trials
            asset_universe: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary containing:
                - best_params: Best parameters found by TPE
                - best_value: Best Sharpe ratio achieved
                - template: Template name used
                - n_trials: Number of trials run
                - best_strategy_code: Generated strategy code with best params

        Example:
            >>> optimizer = TPEOptimizer()
            >>> def backtest_objective(strategy_code: str, cached_data: Dict) -> float:
            ...     result = backtester.run(strategy_code, cached_data)
            ...     return result.sharpe_ratio
            >>> result = optimizer.optimize_with_template(
            ...     template_name='Momentum',
            ...     objective_fn=backtest_objective,
            ...     n_trials=50,
            ...     asset_universe=['2330.TW', '2317.TW'],
            ...     start_date='2023-01-01',
            ...     end_date='2023-12-31'
            ... )
            >>> print(f"Best Sharpe: {result['best_value']:.3f}")
            Best Sharpe: 1.234
        """
        from src.templates.template_library import TemplateLibrary
        from src.templates.template_registry import TEMPLATE_SEARCH_SPACES

        # Initialize library and cache data ONCE
        library = TemplateLibrary(cache_data=True)
        cached_data = library.cache_market_data(
            template_name=template_name,
            asset_universe=asset_universe,
            start_date=start_date,
            end_date=end_date
        )

        logger.info(f"Cached market data for {template_name}: {len(asset_universe)} assets, {start_date} to {end_date}")

        # Get template search space function
        if template_name not in TEMPLATE_SEARCH_SPACES:
            raise KeyError(
                f"Template '{template_name}' not found. "
                f"Available: {list(TEMPLATE_SEARCH_SPACES.keys())}"
            )
        template_fn = TEMPLATE_SEARCH_SPACES[template_name]

        # Create study if not exists
        if self.study is None:
            self._create_study()

        # Assert study exists for type checker
        assert self.study is not None, "Study should exist after _create_study()"

        # Track start time
        start_time = time.time()

        # Define objective wrapper for Optuna
        def objective_wrapper(trial: optuna.Trial) -> float:
            # Get parameters from template search space
            params = template_fn(trial)

            # Generate strategy with cached data (FAST - no data loading)
            strategy_result = library.generate_strategy(
                template_name=template_name,
                params=params,
                cached_data=cached_data
            )

            # Call objective function with strategy code and cached data
            try:
                value = objective_fn(strategy_result['code'], cached_data)
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

        self._search_stats = {
            'n_trials': n_trials,
            'n_pruned': n_pruned,
            'pruning_rate': n_pruned / n_trials if n_trials > 0 else 0.0,
            'best_value': self.study.best_value,
            'best_params': self.study.best_params,
            'search_time': search_time,
            'template': template_name
        }

        # Generate best strategy code
        best_strategy_result = library.generate_strategy(
            template_name=template_name,
            params=self.study.best_params,
            cached_data=cached_data
        )

        logger.info(
            f"Optimization complete: {template_name} | "
            f"Best Sharpe: {self.study.best_value:.3f} | "
            f"Trials: {n_complete}/{n_trials} | "
            f"Time: {search_time:.1f}s"
        )

        return {
            'best_params': self.study.best_params,
            'best_value': self.study.best_value,
            'template': template_name,
            'n_trials': n_trials,
            'best_strategy_code': best_strategy_result['code']
        }

    def optimize_with_validation(
        self,
        template_name: str,
        objective_fn: Callable[[str, Dict], float],
        n_trials: int,
        # IS period
        is_asset_universe: list[str],
        is_start_date: str,
        is_end_date: str,
        # OOS period
        oos_start_date: str,
        oos_end_date: str,
        degradation_threshold: float = 0.30
    ) -> Dict[str, Any]:
        """Optimize with IS/OOS validation to detect overfitting.

        Process:
        1. Optimize on in-sample (IS) data using TPE
        2. Validate on out-of-sample (OOS) data
        3. Calculate degradation
        4. Warn if degradation > threshold

        Args:
            template_name: Template to optimize
            objective_fn: Function(strategy_code: str, cached_data: Dict) -> float
            n_trials: Number of optimization trials
            is_asset_universe: Assets for in-sample optimization
            is_start_date: In-sample start date (YYYY-MM-DD)
            is_end_date: In-sample end date (YYYY-MM-DD)
            oos_start_date: Out-of-sample start date (YYYY-MM-DD)
            oos_end_date: Out-of-sample end date (YYYY-MM-DD)
            degradation_threshold: Warn if degradation exceeds this (default 0.30 = 30%)

        Returns:
            Dictionary containing:
                - best_params: Best parameters found
                - is_value: Best in-sample Sharpe ratio
                - oos_value: Out-of-sample Sharpe ratio
                - degradation: Performance degradation ratio (0.0-1.0)
                - overfitting_detected: Boolean flag
                - template: Template name

        Examples:
            >>> optimizer = TPEOptimizer()
            >>> result = optimizer.optimize_with_validation(
            ...     template_name='Momentum',
            ...     objective_fn=backtest_objective,
            ...     n_trials=50,
            ...     is_asset_universe=['2330.TW', '2317.TW'],
            ...     is_start_date="2020-01-01",
            ...     is_end_date="2022-12-31",
            ...     oos_start_date="2023-01-01",
            ...     oos_end_date="2023-12-31"
            ... )
            >>> print(f"Degradation: {result['degradation']:.1%}")
            Degradation: 23.5%
        """
        from src.templates.template_library import TemplateLibrary

        # Run optimization on IS data
        is_result = self.optimize_with_template(
            template_name=template_name,
            objective_fn=objective_fn,
            n_trials=n_trials,
            asset_universe=is_asset_universe,
            start_date=is_start_date,
            end_date=is_end_date
        )

        is_value = is_result['best_value']
        best_params = is_result['best_params']

        logger.info(f"IS optimization complete: Sharpe={is_value:.3f}")

        # Validate on OOS data
        library = TemplateLibrary(cache_data=True)
        oos_cached_data = library.cache_market_data(
            template_name=template_name,
            asset_universe=is_asset_universe,  # Same assets
            start_date=oos_start_date,
            end_date=oos_end_date
        )

        strategy_result = library.generate_strategy(
            template_name=template_name,
            params=best_params,
            cached_data=oos_cached_data
        )

        oos_value = objective_fn(strategy_result['code'], oos_cached_data)

        logger.info(f"OOS validation complete: Sharpe={oos_value:.3f}")

        # Calculate degradation
        degradation = (is_value - oos_value) / is_value if is_value != 0 else 0.0

        # Warn if overfitting detected
        if degradation > degradation_threshold:
            logger.warning(
                f"Overfitting detected: IS={is_value:.3f}, OOS={oos_value:.3f}, "
                f"Degradation={degradation:.1%} (threshold={degradation_threshold:.1%})"
            )
        else:
            logger.info(
                f"No overfitting: IS={is_value:.3f}, OOS={oos_value:.3f}, "
                f"Degradation={degradation:.1%}"
            )

        return {
            'best_params': best_params,
            'is_value': is_value,
            'oos_value': oos_value,
            'degradation': degradation,
            'overfitting_detected': degradation > degradation_threshold,
            'template': template_name
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

    def optimize_with_runtime_ttpt(
        self,
        objective_fn: Callable,
        strategy_fn: Callable,
        data: Dict[str, Any],
        n_trials: int,
        param_space: Dict[str, Any],
        checkpoint_interval: int = 10,
        ttpt_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize with runtime TTPT monitoring.

        Integrates Time-Travel Perturbation Testing into optimization loop,
        validating strategies at checkpoints for look-ahead bias.

        Args:
            objective_fn: Objective function to maximize (takes params dict)
            strategy_fn: Strategy function for TTPT validation (takes data_dict, params)
            data: Market data for TTPT validation
            n_trials: Number of optimization trials
            param_space: Parameter search space
            checkpoint_interval: Validate every N trials
            ttpt_config: Configuration for TTPT framework

        Returns:
            {
                'best_params': Dict,
                'best_value': float,
                'ttpt_summary': Dict  # Violation summary
            }

        Example:
            >>> def objective(params):
            ...     return backtest_sharpe(params)
            >>> def strategy(data_dict, params):
            ...     return generate_signals(data_dict, params)
            >>> result = optimizer.optimize_with_runtime_ttpt(
            ...     objective_fn=objective,
            ...     strategy_fn=strategy,
            ...     data={'close': df},
            ...     n_trials=50,
            ...     param_space={'lookback': (10, 50)},
            ...     checkpoint_interval=10
            ... )
        """
        from src.validation.runtime_ttpt_monitor import RuntimeTTPTMonitor

        # Initialize TTPT monitor
        monitor = RuntimeTTPTMonitor(
            ttpt_config=ttpt_config,
            checkpoint_interval=checkpoint_interval,
            alert_on_violation=True
        )

        # Wrapper to add TTPT validation
        trial_counter = [0]  # Mutable counter for closure

        def objective_with_ttpt(params):
            trial_counter[0] += 1
            current_trial = trial_counter[0]

            # Run objective function
            value = objective_fn(params)

            # Validate at checkpoints
            validation_result = monitor.validate_checkpoint(
                trial_number=current_trial,
                strategy_fn=strategy_fn,
                data=data,
                params=params
            )

            # Log validation result
            if not validation_result.get('skipped'):
                if validation_result['passed']:
                    logger.info(f"Trial {current_trial}: TTPT validation PASSED")
                else:
                    logger.warning(
                        f"Trial {current_trial}: TTPT validation FAILED - "
                        f"{len(validation_result.get('violations', []))} violations"
                    )

            return value

        # Run optimization (let optimize() handle param_space)
        self.optimize(
            objective_fn=objective_with_ttpt,
            n_trials=n_trials,
            param_space=param_space
        )

        # Get TTPT summary
        ttpt_summary = monitor.get_violation_summary()

        return {
            'best_params': self.study.best_params,
            'best_value': self.study.best_value,
            'ttpt_summary': ttpt_summary
        }


# Backward compatibility alias
ASHAOptimizer = TPEOptimizer
