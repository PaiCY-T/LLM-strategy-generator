"""
Template Registry - Centralized singleton for template management.

Provides lazy initialization and caching for strategy templates,
enabling multi-template evolution while maintaining performance.
"""

from typing import Dict, Type, List, Any, Optional
import threading


class TemplateRegistry:
    """
    Singleton registry for strategy templates with lazy initialization.

    Manages template class mapping, instantiation, and caching to support
    multi-template evolution. Provides O(1) template lookup and ensures
    single instance per template class per process.

    Thread Safety:
        Single-threaded usage only (matches genetic algorithm execution model).
        If multi-threading is needed in future, use threading.Lock for
        _template_instances access.

    Attributes:
        AVAILABLE_TEMPLATES: Dict mapping template names to template classes
        _instance: Singleton instance (class attribute)
        _template_instances: Cache of instantiated templates

    Example:
        >>> registry = TemplateRegistry.get_instance()
        >>> template = registry.get_template('Turtle')
        >>> param_grid = registry.get_param_grid('Momentum')
    """

    # Singleton instance (class attribute)
    _instance: Optional['TemplateRegistry'] = None
    _lock = threading.Lock()

    # Template class registry - maps template names to classes
    AVAILABLE_TEMPLATES: Dict[str, Type] = {
        'Momentum': None,  # Lazy import to avoid circular dependencies
        'MomentumExit': None,  # Phase 0 validation - Momentum with exit strategies
        'Turtle': None,
        'Factor': None,
        'Mastiff': None,
        'Combination': None
    }

    def __init__(self):
        """
        Initialize template registry (private - use get_instance()).

        Raises:
            RuntimeError: If called directly instead of via get_instance()
        """
        if TemplateRegistry._instance is not None:
            raise RuntimeError(
                "TemplateRegistry is a singleton. Use get_instance() instead."
            )

        # Cache for instantiated templates (lazy initialization)
        self._template_instances: Dict[str, Any] = {}

        # Lazy import template classes to avoid circular dependencies
        self._initialize_template_classes()

    @classmethod
    def get_instance(cls) -> 'TemplateRegistry':
        """
        Get singleton instance of TemplateRegistry.

        Thread-safe singleton implementation with double-checked locking.

        Returns:
            TemplateRegistry: The singleton instance

        Example:
            >>> registry1 = TemplateRegistry.get_instance()
            >>> registry2 = TemplateRegistry.get_instance()
            >>> assert registry1 is registry2  # Same instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def _initialize_template_classes(self) -> None:
        """
        Lazy import template classes to avoid circular dependencies.

        Imports template classes only when registry is first instantiated,
        preventing import-time circular dependency issues.

        Raises:
            ImportError: If template classes cannot be imported
        """
        try:
            from src.templates.momentum_template import MomentumTemplate
            from src.templates.momentum_exit_template import MomentumExitTemplate
            from src.templates.turtle_template import TurtleTemplate
            from src.templates.factor_template import FactorTemplate
            from src.templates.mastiff_template import MastiffTemplate
            from src.templates.combination_template import CombinationTemplate

            TemplateRegistry.AVAILABLE_TEMPLATES = {
                'Momentum': MomentumTemplate,
                'MomentumExit': MomentumExitTemplate,
                'Turtle': TurtleTemplate,
                'Factor': FactorTemplate,
                'Mastiff': MastiffTemplate,
                'Combination': CombinationTemplate
            }
        except ImportError as e:
            raise ImportError(
                f"Failed to import template classes: {str(e)}. "
                "Ensure all template classes are implemented in src/templates/."
            ) from e

    def get_template(self, template_type: str):
        """
        Get template instance with caching (lazy initialization).

        Retrieves template instance from cache, or instantiates and caches
        if not yet created. Each template class has exactly one instance
        per registry (singleton pattern per template type).

        Args:
            template_type: Template name ('Momentum', 'Turtle', 'Factor', 'Mastiff', 'Combination')

        Returns:
            Template instance (MomentumTemplate, TurtleTemplate, CombinationTemplate, etc.)

        Raises:
            ValueError: If template_type is not in AVAILABLE_TEMPLATES
            RuntimeError: If template instantiation fails

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> turtle = registry.get_template('Turtle')
            >>> turtle2 = registry.get_template('Turtle')
            >>> assert turtle is turtle2  # Cached instance
        """
        if template_type not in self.AVAILABLE_TEMPLATES:
            available = list(self.AVAILABLE_TEMPLATES.keys())
            raise ValueError(
                f"Unknown template type '{template_type}'. "
                f"Available templates: {available}"
            )

        # Check cache first (lazy initialization)
        if template_type in self._template_instances:
            return self._template_instances[template_type]

        # Instantiate and cache template
        try:
            template_class = self.AVAILABLE_TEMPLATES[template_type]
            template_instance = template_class()
            self._template_instances[template_type] = template_instance
            return template_instance
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate template '{template_type}': {str(e)}"
            ) from e

    def get_param_grid(self, template_type: str) -> Dict[str, List[Any]]:
        """
        Get parameter grid for template type.

        Retrieves PARAM_GRID from template instance, defining allowed
        parameter values for the specified template.

        Args:
            template_type: Template name ('Momentum', 'Turtle', 'Factor', 'Mastiff', 'Combination')

        Returns:
            Dict[str, List[Any]]: Parameter grid with allowed values

        Raises:
            ValueError: If template_type is invalid
            RuntimeError: If template has no PARAM_GRID attribute

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> grid = registry.get_param_grid('Momentum')
            >>> print(grid['n_stocks'])  # [10, 20, 30, 50]
        """
        template = self.get_template(template_type)

        if not hasattr(template, 'PARAM_GRID'):
            raise RuntimeError(
                f"Template '{template_type}' has no PARAM_GRID attribute. "
                "All templates must define PARAM_GRID."
            )

        return template.PARAM_GRID

    def get_available_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List[str]: Template names ['Momentum', 'Turtle', 'Factor', 'Mastiff', 'Combination']

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> templates = registry.get_available_templates()
            >>> print(templates)  # ['Momentum', 'Turtle', 'Factor', 'Mastiff', 'Combination']
        """
        return list(self.AVAILABLE_TEMPLATES.keys())

    def get_template_class(self, template_type: str) -> Type:
        """
        Get template class (not instance) for advanced use cases.

        Returns the class reference itself, useful for type checking
        or reflection. For normal template operations, use get_template().

        Args:
            template_type: Template name ('Momentum', 'Turtle', 'Factor', 'Mastiff', 'Combination')

        Returns:
            Type: Template class (MomentumTemplate, TurtleTemplate, CombinationTemplate, etc.)

        Raises:
            ValueError: If template_type is invalid

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> cls = registry.get_template_class('Turtle')
            >>> print(cls.__name__)  # 'TurtleTemplate'
        """
        if template_type not in self.AVAILABLE_TEMPLATES:
            available = list(self.AVAILABLE_TEMPLATES.keys())
            raise ValueError(
                f"Unknown template type '{template_type}'. "
                f"Available templates: {available}"
            )

        return self.AVAILABLE_TEMPLATES[template_type]

    def validate_template_type(self, template_type: str) -> bool:
        """
        Validate that template_type is available.

        Args:
            template_type: Template name to validate

        Returns:
            bool: True if template_type is valid, False otherwise

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> registry.validate_template_type('Turtle')  # True
            >>> registry.validate_template_type('Invalid')  # False
        """
        return template_type in self.AVAILABLE_TEMPLATES

    def clear_cache(self) -> None:
        """
        Clear template instance cache (for testing/memory management).

        Forces re-instantiation of all templates on next get_template() call.
        Useful for testing or when template classes are modified dynamically.

        Warning:
            Only use for testing. In production, template instances should
            be cached for the lifetime of the process.

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> registry.clear_cache()
            >>> # Next get_template() will create new instance
        """
        self._template_instances.clear()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset singleton instance (for testing only).

        Forces creation of new TemplateRegistry instance on next get_instance().

        Warning:
            Only use for testing. In production, singleton should persist
            for entire process lifetime.

        Example:
            >>> TemplateRegistry.reset_instance()
            >>> registry = TemplateRegistry.get_instance()  # New instance
        """
        with cls._lock:
            cls._instance = None

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with keys:
                - 'cached_templates': List of cached template names
                - 'cache_size': Number of cached templates
                - 'available_templates': List of all available template names

        Example:
            >>> registry = TemplateRegistry.get_instance()
            >>> registry.get_template('Momentum')
            >>> stats = registry.get_cache_stats()
            >>> print(stats['cached_templates'])  # ['Momentum']
        """
        return {
            'cached_templates': list(self._template_instances.keys()),
            'cache_size': len(self._template_instances),
            'available_templates': self.get_available_templates()
        }

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation
        """
        cached = list(self._template_instances.keys())
        available = list(self.AVAILABLE_TEMPLATES.keys())
        return (
            f"TemplateRegistry("
            f"available={available}, "
            f"cached={cached})"
        )
