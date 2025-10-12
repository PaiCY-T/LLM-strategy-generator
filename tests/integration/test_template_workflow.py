"""
Integration Tests for Template System Workflow

Test Coverage:
    - End-to-end workflow for each template
    - Template → Strategy Generation → Backtest → Hall of Fame
    - Multiple templates with Hall of Fame integration
    - Full system integration validation

Fixtures Used:
    - mock_data_cache: Mocked DataCache with synthetic data
    - mock_finlab_sim: Mocked backtest with predictable metrics
    - tmp_path: Temporary directory for Hall of Fame storage

Markers:
    - @pytest.mark.integration: Integration test marker
"""

import pytest
from pathlib import Path
from src.templates.turtle_template import TurtleTemplate
from src.templates.mastiff_template import MastiffTemplate
from src.templates.factor_template import FactorTemplate
from src.templates.momentum_template import MomentumTemplate
from src.repository.hall_of_fame import HallOfFameRepository


@pytest.mark.integration
class TestTurtleTemplateWorkflow:
    """Test complete Turtle template workflow."""

    def test_turtle_end_to_end(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test complete Turtle template workflow from generation to Hall of Fame."""
        # Step 1: Generate strategy
        template = TurtleTemplate()
        params = template.get_default_params()
        report, metrics = template.generate_strategy(params)

        assert report is not None

        # Step 2: Validate generated strategy metrics
        assert 'sharpe_ratio' in metrics
        assert 'annual_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'success' in metrics

        # Step 3: Add to Hall of Fame
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Create strategy code (placeholder for actual generated code)
        strategy_code = '''
def initialize(context):
    pass

def handle_data(context, data):
    pass

def before_trading_start(context, data):
    pass
'''

        success, message = hof.add_strategy(
            template_name='TurtleTemplate',
            parameters=params,
            metrics=metrics,
            strategy_code=strategy_code
        )

        assert success is True

        # Step 4: Verify retrieval
        champions = hof.get_champions()
        assert len(champions) == 1
        assert champions[0].template_name == 'TurtleTemplate'


@pytest.mark.integration
class TestMastiffTemplateWorkflow:
    """Test complete Mastiff template workflow."""

    def test_mastiff_end_to_end(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test complete Mastiff template workflow."""
        # Step 1: Generate strategy
        template = MastiffTemplate()
        params = template.get_default_params()
        report, metrics = template.generate_strategy(params)

        assert report is not None
        assert 'sharpe_ratio' in metrics

        # Step 2: Add to Hall of Fame
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        strategy_code = '''
def initialize(context):
    pass

def handle_data(context, data):
    pass
'''

        success, message = hof.add_strategy(
            template_name='MastiffTemplate',
            parameters=params,
            metrics=metrics,
            strategy_code=strategy_code
        )

        assert success is True

        # Step 3: Verify retrieval
        champions = hof.get_champions()
        assert len(champions) >= 1


@pytest.mark.integration
class TestFactorTemplateWorkflow:
    """Test complete Factor template workflow."""

    def test_factor_end_to_end(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test complete Factor template workflow."""
        template = FactorTemplate()
        params = template.get_default_params()
        report, metrics = template.generate_strategy(params)

        assert report is not None

        # Add to Hall of Fame
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        strategy_code = 'def initialize(context): pass'

        success, message = hof.add_strategy(
            template_name='FactorTemplate',
            parameters=params,
            metrics=metrics,
            strategy_code=strategy_code
        )

        assert success is True


@pytest.mark.integration
class TestMomentumTemplateWorkflow:
    """Test complete Momentum template workflow."""

    def test_momentum_end_to_end(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test complete Momentum template workflow."""
        template = MomentumTemplate()
        params = template.get_default_params()
        report, metrics = template.generate_strategy(params)

        assert report is not None

        # Add to Hall of Fame
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        strategy_code = 'def initialize(context): pass'

        success, message = hof.add_strategy(
            template_name='MomentumTemplate',
            parameters=params,
            metrics=metrics,
            strategy_code=strategy_code
        )

        assert success is True


@pytest.mark.integration
class TestMultiTemplateIntegration:
    """Test integration across multiple templates with Hall of Fame."""

    def test_multiple_templates_hall_of_fame(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test Hall of Fame with strategies from multiple templates."""
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        templates = [
            (TurtleTemplate, 'TurtleTemplate'),
            (MastiffTemplate, 'MastiffTemplate'),
            (FactorTemplate, 'FactorTemplate'),
            (MomentumTemplate, 'MomentumTemplate')
        ]

        # Generate from each template
        for template_class, template_name in templates:
            template = template_class()
            params = template.get_default_params()
            report, metrics = template.generate_strategy(params)

            # Add to Hall of Fame
            strategy_code = f'# Generated by {template_name}\ndef initialize(context): pass'

            success, message = hof.add_strategy(
                template_name=template_name,
                parameters=params,
                metrics=metrics,
                strategy_code=strategy_code
            )

            assert success is True, f"Failed to add {template_name}: {message}"

        # Verify all 4 strategies in Hall of Fame
        stats = hof.get_statistics()
        assert stats['total'] == 4

        # Verify template distribution
        assert 'TurtleTemplate' in stats['templates']
        assert 'MastiffTemplate' in stats['templates']
        assert 'FactorTemplate' in stats['templates']
        assert 'MomentumTemplate' in stats['templates']

    def test_best_strategy_selection(self, mock_data_cache, mock_finlab_sim, tmp_path):
        """Test selecting best strategy across templates."""
        hof = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Add strategies with varying performance
        templates_sharpe = [
            (TurtleTemplate, 'TurtleTemplate', 2.8),
            (MastiffTemplate, 'MastiffTemplate', 2.3),
            (FactorTemplate, 'FactorTemplate', 1.5),
            (MomentumTemplate, 'MomentumTemplate', 2.0)
        ]

        for template_class, template_name, sharpe in templates_sharpe:
            template = template_class()
            params = template.get_default_params()
            report, metrics = template.generate_strategy(params)

            # Override Sharpe for testing
            metrics['sharpe_ratio'] = sharpe

            strategy_code = f'# {template_name}'

            hof.add_strategy(
                template_name=template_name,
                parameters=params,
                metrics=metrics,
                strategy_code=strategy_code
            )

        # Get current champion (highest Sharpe)
        champion = hof.get_current_champion()

        assert champion is not None
        assert champion.template_name == 'TurtleTemplate'
        assert champion.metrics['sharpe_ratio'] == 2.8
