"""
Unit tests for TemplateRegistry singleton.

Tests cover:
- Singleton pattern enforcement
- Template instance caching
- Template validation
- Parameter grid retrieval
- Available templates listing
"""

import pytest
from src.utils.template_registry import TemplateRegistry


class TestTemplateRegistrySingleton:
    """Test singleton pattern enforcement."""

    def setup_method(self):
        """Reset singleton before each test."""
        TemplateRegistry.reset_instance()

    def test_singleton_pattern(self):
        """Test only one TemplateRegistry instance exists."""
        registry1 = TemplateRegistry.get_instance()
        registry2 = TemplateRegistry.get_instance()

        # Same instance returned
        assert registry1 is registry2

        # Same id in memory
        assert id(registry1) == id(registry2)

    def test_singleton_direct_instantiation_fails(self):
        """Test direct instantiation raises RuntimeError."""
        # First instance succeeds
        _ = TemplateRegistry.get_instance()

        # Direct instantiation should fail
        with pytest.raises(RuntimeError, match="singleton"):
            TemplateRegistry()

    def test_reset_instance(self):
        """Test reset_instance creates new singleton."""
        registry1 = TemplateRegistry.get_instance()

        TemplateRegistry.reset_instance()

        registry2 = TemplateRegistry.get_instance()

        # Different instances after reset
        assert registry1 is not registry2


class TestTemplateInstanceCaching:
    """Test template instance caching behavior."""

    def setup_method(self):
        """Reset registry and clear cache before each test."""
        TemplateRegistry.reset_instance()
        registry = TemplateRegistry.get_instance()
        registry.clear_cache()

    def test_template_caching(self):
        """Test same template instance returned on multiple calls."""
        registry = TemplateRegistry.get_instance()

        # Get template twice
        template1 = registry.get_template('Momentum')
        template2 = registry.get_template('Momentum')

        # Same instance returned (cached)
        assert template1 is template2
        assert id(template1) == id(template2)

    def test_different_templates_different_instances(self):
        """Test different templates return different instances."""
        registry = TemplateRegistry.get_instance()

        momentum = registry.get_template('Momentum')
        turtle = registry.get_template('Turtle')

        # Different instances
        assert momentum is not turtle
        assert type(momentum).__name__ == 'MomentumTemplate'
        assert type(turtle).__name__ == 'TurtleTemplate'

    def test_cache_stats(self):
        """Test cache statistics tracking."""
        registry = TemplateRegistry.get_instance()

        # Initially empty cache
        stats = registry.get_cache_stats()
        assert stats['cache_size'] == 0
        assert len(stats['cached_templates']) == 0

        # Cache one template
        registry.get_template('Momentum')
        stats = registry.get_cache_stats()
        assert stats['cache_size'] == 1
        assert 'Momentum' in stats['cached_templates']

        # Cache another template
        registry.get_template('Turtle')
        stats = registry.get_cache_stats()
        assert stats['cache_size'] == 2
        assert set(stats['cached_templates']) == {'Momentum', 'Turtle'}

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        registry = TemplateRegistry.get_instance()

        # Cache templates
        template1 = registry.get_template('Momentum')
        assert registry.get_cache_stats()['cache_size'] == 1

        # Clear cache
        registry.clear_cache()
        assert registry.get_cache_stats()['cache_size'] == 0

        # New instance after cache clear
        template2 = registry.get_template('Momentum')
        assert template1 is not template2


class TestTemplateValidation:
    """Test template validation and error handling."""

    def setup_method(self):
        """Reset registry before each test."""
        TemplateRegistry.reset_instance()

    def test_validate_template_type_valid(self):
        """Test validation accepts valid template types."""
        registry = TemplateRegistry.get_instance()

        assert registry.validate_template_type('Momentum') is True
        assert registry.validate_template_type('Turtle') is True
        assert registry.validate_template_type('Factor') is True
        assert registry.validate_template_type('Mastiff') is True

    def test_validate_template_type_invalid(self):
        """Test validation rejects invalid template types."""
        registry = TemplateRegistry.get_instance()

        assert registry.validate_template_type('Invalid') is False
        assert registry.validate_template_type('') is False
        assert registry.validate_template_type('momentum') is False  # Case sensitive

    def test_get_template_invalid_raises_error(self):
        """Test get_template raises ValueError for invalid template_type."""
        registry = TemplateRegistry.get_instance()

        with pytest.raises(ValueError, match="Unknown template type 'Invalid'"):
            registry.get_template('Invalid')

    def test_get_template_error_message_includes_available(self):
        """Test error message includes available templates."""
        registry = TemplateRegistry.get_instance()

        try:
            registry.get_template('Invalid')
            pytest.fail("Expected ValueError")
        except ValueError as e:
            error_msg = str(e)
            assert 'Momentum' in error_msg
            assert 'Turtle' in error_msg
            assert 'Factor' in error_msg
            assert 'Mastiff' in error_msg


class TestParameterGridRetrieval:
    """Test parameter grid retrieval functionality."""

    def setup_method(self):
        """Reset registry before each test."""
        TemplateRegistry.reset_instance()

    def test_get_param_grid_momentum(self):
        """Test get_param_grid returns MomentumTemplate grid."""
        registry = TemplateRegistry.get_instance()

        grid = registry.get_param_grid('Momentum')

        # Check it's a dictionary
        assert isinstance(grid, dict)

        # Check expected parameters exist
        assert 'n_stocks' in grid
        assert isinstance(grid['n_stocks'], list)
        assert len(grid['n_stocks']) > 0

    def test_get_param_grid_different_templates(self):
        """Test different templates return different param grids."""
        registry = TemplateRegistry.get_instance()

        momentum_grid = registry.get_param_grid('Momentum')
        turtle_grid = registry.get_param_grid('Turtle')

        # Different grids for different templates
        assert set(momentum_grid.keys()) != set(turtle_grid.keys())

    def test_get_param_grid_invalid_template(self):
        """Test get_param_grid raises error for invalid template."""
        registry = TemplateRegistry.get_instance()

        with pytest.raises(ValueError, match="Unknown template type"):
            registry.get_param_grid('Invalid')


class TestAvailableTemplates:
    """Test available templates listing."""

    def setup_method(self):
        """Reset registry before each test."""
        TemplateRegistry.reset_instance()

    def test_get_available_templates_returns_four(self):
        """Test get_available_templates returns 4 templates."""
        registry = TemplateRegistry.get_instance()

        templates = registry.get_available_templates()

        assert len(templates) == 4
        assert isinstance(templates, list)

    def test_get_available_templates_correct_names(self):
        """Test get_available_templates returns correct template names."""
        registry = TemplateRegistry.get_instance()

        templates = registry.get_available_templates()

        expected = {'Momentum', 'Turtle', 'Factor', 'Mastiff'}
        assert set(templates) == expected

    def test_get_template_class(self):
        """Test get_template_class returns class reference."""
        registry = TemplateRegistry.get_instance()

        momentum_class = registry.get_template_class('Momentum')

        # It's a class, not an instance
        assert hasattr(momentum_class, '__call__')
        assert momentum_class.__name__ == 'MomentumTemplate'

    def test_get_template_class_invalid(self):
        """Test get_template_class raises error for invalid template."""
        registry = TemplateRegistry.get_instance()

        with pytest.raises(ValueError, match="Unknown template type"):
            registry.get_template_class('Invalid')


class TestTemplateRegistryRepr:
    """Test string representation for debugging."""

    def setup_method(self):
        """Reset registry before each test."""
        TemplateRegistry.reset_instance()

    def test_repr_shows_cached_templates(self):
        """Test __repr__ shows cached templates."""
        registry = TemplateRegistry.get_instance()

        # Cache one template
        registry.get_template('Momentum')

        repr_str = repr(registry)

        assert 'TemplateRegistry' in repr_str
        assert 'Momentum' in repr_str
        assert 'cached' in repr_str

    def test_repr_shows_all_available(self):
        """Test __repr__ shows all available templates."""
        registry = TemplateRegistry.get_instance()

        repr_str = repr(registry)

        assert 'Momentum' in repr_str
        assert 'Turtle' in repr_str
        assert 'Factor' in repr_str
        assert 'Mastiff' in repr_str


class TestTemplateRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Reset registry before each test."""
        TemplateRegistry.reset_instance()

    def test_multiple_template_retrievals_performance(self):
        """Test performance of multiple template retrievals."""
        registry = TemplateRegistry.get_instance()

        # First retrieval (cache miss)
        template1 = registry.get_template('Momentum')

        # Subsequent retrievals should be fast (cache hits)
        for _ in range(100):
            template = registry.get_template('Momentum')
            assert template is template1

    def test_all_templates_instantiable(self):
        """Test all 4 templates can be instantiated."""
        registry = TemplateRegistry.get_instance()

        templates = ['Momentum', 'Turtle', 'Factor', 'Mastiff']

        for template_name in templates:
            template = registry.get_template(template_name)
            assert template is not None
            assert hasattr(template, 'PARAM_GRID')
            assert hasattr(template, 'generate_strategy')
