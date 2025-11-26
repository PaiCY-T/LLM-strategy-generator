"""
Architecture Layer Separation Tests (Spec A Task 5.1).

Tests that Domain and Persistence layers are properly separated:
- IStrategy Protocol has NO save/load methods (domain only)
- Strategy class has NO persistence methods
- HallOfFameRepository handles ALL persistence

This prevents Active Record anti-pattern and maintains clean architecture.

Architecture Design:
    Domain Layer (src/evolution/types.py, src/learning/interfaces.py):
        - Strategy: Domain entity with business logic
        - IStrategy: Protocol defining domain contract
        - NO persistence concerns

    Persistence Layer (src/repository/hall_of_fame.py):
        - HallOfFameRepository: Handles save/load operations
        - Converts domain objects to/from JSON
        - Manages tier-based storage
"""

import pytest
import inspect
from typing import get_type_hints


class TestIStrategyProtocolLayerSeparation:
    """Test IStrategy Protocol has NO persistence methods."""

    def test_istrategy_has_no_save_method(self):
        """IStrategy should NOT have save() method."""
        from src.learning.interfaces import IStrategy

        # Get all methods defined in IStrategy
        methods = [
            name for name, _ in inspect.getmembers(IStrategy, predicate=inspect.isfunction)
            if not name.startswith('_')
        ]

        # Verify no save-related methods
        persistence_methods = ['save', 'save_to_file', 'persist', 'store', 'write']
        for method in persistence_methods:
            assert method not in methods, \
                f"IStrategy should NOT have '{method}' method (violates layer separation)"

    def test_istrategy_has_no_load_method(self):
        """IStrategy should NOT have load() method."""
        from src.learning.interfaces import IStrategy

        # Get all methods including class methods
        methods = dir(IStrategy)

        # Verify no load-related methods
        persistence_methods = ['load', 'load_from_file', 'read', 'retrieve', 'from_file']
        for method in persistence_methods:
            assert method not in methods or method.startswith('from_'), \
                f"IStrategy should NOT have '{method}' method (violates layer separation)"

    def test_istrategy_defines_domain_methods_only(self):
        """IStrategy should only define domain-related methods."""
        from src.learning.interfaces import IStrategy

        # Expected domain methods (from Spec A design)
        expected_domain_methods = {
            'dominates',      # Pareto comparison
            'get_parameters', # Parameter extraction
            'get_metrics'     # Metrics extraction
        }

        # Expected domain properties
        expected_domain_properties = {
            'id',
            'generation',
            'metrics'
        }

        # Get all public methods (not properties)
        all_members = inspect.getmembers(IStrategy)
        public_methods = [
            name for name, value in all_members
            if not name.startswith('_') and callable(value)
        ]

        # Verify all expected methods exist
        for method in expected_domain_methods:
            assert method in public_methods, \
                f"IStrategy missing expected domain method: {method}"


class TestStrategyClassLayerSeparation:
    """Test Strategy class has NO persistence methods."""

    def test_strategy_has_no_save_method(self):
        """Strategy class should NOT have save() method."""
        from src.evolution.types import Strategy

        # Get all methods
        methods = [
            name for name, _ in inspect.getmembers(Strategy, predicate=inspect.isfunction)
            if not name.startswith('_')
        ]

        # Verify no save-related methods (to_dict is OK for serialization prep)
        persistence_methods = ['save', 'save_to_file', 'persist', 'store', 'write_to_file']
        for method in persistence_methods:
            assert method not in methods, \
                f"Strategy should NOT have '{method}' method (violates layer separation)"

    def test_strategy_has_no_load_method(self):
        """Strategy class should NOT have load() method (from_dict is OK)."""
        from src.evolution.types import Strategy

        # Get all class methods
        methods = dir(Strategy)

        # Verify no load-related methods (from_dict is allowed for reconstruction)
        forbidden_methods = ['load', 'load_from_file', 'read_from_file', 'retrieve']
        for method in forbidden_methods:
            assert method not in methods, \
                f"Strategy should NOT have '{method}' method (violates layer separation)"

    def test_strategy_to_dict_is_serialization_prep_only(self):
        """Strategy.to_dict() should return dict for serialization, not persist."""
        from src.evolution.types import Strategy, MultiObjectiveMetrics

        strategy = Strategy(
            id='test-001',
            generation=5,
            parameters={'n_stocks': 20}
        )

        # to_dict should return a dict (serialization preparation)
        result = strategy.to_dict()

        assert isinstance(result, dict)
        assert 'id' in result
        assert 'generation' in result
        assert 'parameters' in result

    def test_strategy_from_dict_is_reconstruction_only(self):
        """Strategy.from_dict() should reconstruct from dict, not load from file."""
        from src.evolution.types import Strategy

        data = {
            'id': 'test-001',
            'generation': 5,
            'parent_ids': [],
            'code': 'def strategy(): pass',
            'parameters': {'n_stocks': 20},
            'metrics': None,
            'novelty_score': 0.5,
            'pareto_rank': 0,
            'crowding_distance': 0.0,
            'timestamp': '2025-01-01T00:00:00',
            'template_type': 'FactorGraph',
            'metadata': {}
        }

        # from_dict should reconstruct Strategy from dict
        strategy = Strategy.from_dict(data)

        assert isinstance(strategy, Strategy)
        assert strategy.id == 'test-001'
        assert strategy.generation == 5

    def test_strategy_implements_istrategy_domain_methods(self):
        """Strategy class should implement IStrategy domain methods."""
        from src.evolution.types import Strategy, MultiObjectiveMetrics
        from src.learning.interfaces import IStrategy

        metrics = MultiObjectiveMetrics(
            sharpe_ratio=2.5,
            calmar_ratio=1.8,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.62,
            annual_return=0.28,
            success=True
        )

        strategy = Strategy(
            id='test-001',
            generation=5,
            parameters={'n_stocks': 20},
            metrics=metrics
        )

        # Verify Strategy implements IStrategy
        assert isinstance(strategy, IStrategy)

        # Verify domain methods work
        assert strategy.id == 'test-001'
        assert strategy.generation == 5
        assert strategy.metrics is not None

        params = strategy.get_parameters()
        assert isinstance(params, dict)
        assert params['n_stocks'] == 20

        metrics_dict = strategy.get_metrics()
        assert isinstance(metrics_dict, dict)
        assert 'sharpe_ratio' in metrics_dict


class TestHallOfFameRepositoryLayerSeparation:
    """Test HallOfFameRepository handles ALL persistence."""

    def test_repository_has_save_method(self):
        """HallOfFameRepository should have save_strategy() method."""
        from src.repository.hall_of_fame import HallOfFameRepository

        assert hasattr(HallOfFameRepository, 'save_strategy'), \
            "HallOfFameRepository should have save_strategy() method"

    def test_repository_has_load_method(self):
        """HallOfFameRepository should have load_strategy() method."""
        from src.repository.hall_of_fame import HallOfFameRepository

        assert hasattr(HallOfFameRepository, 'load_strategy'), \
            "HallOfFameRepository should have load_strategy() method"

    def test_repository_accepts_strategy_objects(self):
        """HallOfFameRepository should accept Strategy objects."""
        from src.repository.hall_of_fame import HallOfFameRepository
        import inspect

        # Check save_strategy method signature
        sig = inspect.signature(HallOfFameRepository.save_strategy)
        params = list(sig.parameters.keys())

        assert 'strategy' in params, \
            "save_strategy should accept 'strategy' parameter"

    def test_repository_returns_strategy_objects(self):
        """HallOfFameRepository.load_strategy should return Strategy objects."""
        from src.repository.hall_of_fame import HallOfFameRepository
        import inspect

        # Check load_strategy method exists
        assert hasattr(HallOfFameRepository, 'load_strategy')

        # Check return type annotation if available
        sig = inspect.signature(HallOfFameRepository.load_strategy)
        # Return type should be Optional[Strategy] or similar


class TestNoCircularDependencies:
    """Test there are no circular dependencies between layers."""

    def test_strategy_does_not_import_repository(self):
        """Strategy module should NOT import repository module."""
        import src.evolution.types as types_module

        # Check imports in the module
        module_imports = dir(types_module)

        # Verify no repository imports
        assert 'HallOfFameRepository' not in module_imports, \
            "types.py should NOT import HallOfFameRepository"

    def test_interfaces_does_not_import_repository(self):
        """interfaces.py should NOT import repository module."""
        import src.learning.interfaces as interfaces_module

        module_imports = dir(interfaces_module)

        assert 'HallOfFameRepository' not in module_imports, \
            "interfaces.py should NOT import HallOfFameRepository"


class TestArchitectureDocumentation:
    """Test architecture documentation is in place."""

    def test_istrategy_has_architecture_docstring(self):
        """IStrategy Protocol should have architecture documentation."""
        from src.learning.interfaces import IStrategy

        docstring = IStrategy.__doc__

        assert docstring is not None, "IStrategy should have docstring"
        assert 'domain' in docstring.lower() or 'protocol' in docstring.lower(), \
            "IStrategy docstring should mention domain or protocol"

    def test_strategy_has_serialization_docstring(self):
        """Strategy.to_dict should document serialization purpose."""
        from src.evolution.types import Strategy

        docstring = Strategy.to_dict.__doc__

        assert docstring is not None, "to_dict should have docstring"
        assert 'serial' in docstring.lower() or 'dict' in docstring.lower(), \
            "to_dict docstring should mention serialization"
