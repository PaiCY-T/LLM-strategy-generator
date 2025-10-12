"""
Unit Tests for RationaleGenerator
==================================

Unit tests for the template rationale generation system.

Test Coverage:
    - Performance-based rationale generation
    - Exploration mode rationale generation
    - Champion-based rationale generation
    - Validation feedback rationale generation
    - Risk profile rationale generation
    - Template descriptions

Components Tested:
    - RationaleGenerator.generate_performance_rationale()
    - RationaleGenerator.generate_exploration_rationale()
    - RationaleGenerator.generate_champion_rationale()
    - RationaleGenerator.generate_validation_rationale()
    - RationaleGenerator.generate_risk_profile_rationale()
    - RationaleGenerator._get_performance_tier()
"""

import pytest
from src.feedback.rationale_generator import RationaleGenerator


class TestRationaleGenerator:
    """Unit tests for RationaleGenerator."""

    @pytest.fixture
    def generator(self):
        """Create RationaleGenerator instance."""
        return RationaleGenerator()

    # Performance Tier Tests
    def test_get_performance_tier_poor(self, generator):
        """Test: Sharpe <0.5 → Poor performance tier."""
        tier = generator._get_performance_tier(0.3)
        assert tier['label'] == 'Poor performance'
        assert tier['min_sharpe'] == 0.0

    def test_get_performance_tier_archive(self, generator):
        """Test: Sharpe 0.5-1.0 → Archive tier."""
        tier = generator._get_performance_tier(0.8)
        assert tier['label'] == 'Archive tier'
        assert tier['min_sharpe'] == 0.5

    def test_get_performance_tier_solid(self, generator):
        """Test: Sharpe 1.0-1.5 → Solid performance."""
        tier = generator._get_performance_tier(1.2)
        assert tier['label'] == 'Solid performance'
        assert tier['min_sharpe'] == 1.0

    def test_get_performance_tier_contender(self, generator):
        """Test: Sharpe 1.5-2.0 → Contender tier."""
        tier = generator._get_performance_tier(1.7)
        assert tier['label'] == 'Contender tier'
        assert tier['min_sharpe'] == 1.5

    def test_get_performance_tier_champion(self, generator):
        """Test: Sharpe ≥2.0 → Champion tier."""
        tier = generator._get_performance_tier(2.5)
        assert tier['label'] == 'Champion tier'
        assert tier['min_sharpe'] == 2.0

    # Performance Rationale Generation Tests
    def test_generate_performance_rationale_basic(self, generator):
        """Test: Basic performance rationale generation."""
        rationale = generator.generate_performance_rationale(
            template_name='TurtleTemplate',
            sharpe=1.2,
            success_rate=0.80
        )

        assert 'TurtleTemplate' in rationale
        assert '1.2' in rationale or '1.20' in rationale
        assert '80%' in rationale

    def test_generate_performance_rationale_high_sharpe(self, generator):
        """Test: Performance rationale for high Sharpe (≥2.0)."""
        rationale = generator.generate_performance_rationale(
            template_name='TurtleTemplate',
            sharpe=2.3,
            success_rate=0.85
        )

        assert 'TurtleTemplate' in rationale
        assert 'Champion tier' in rationale
        assert '2.3' in rationale or '2.30' in rationale

    def test_generate_performance_rationale_low_sharpe(self, generator):
        """Test: Performance rationale for low Sharpe (<0.5)."""
        rationale = generator.generate_performance_rationale(
            template_name='TurtleTemplate',
            sharpe=0.3,
            success_rate=0.60
        )

        assert 'TurtleTemplate' in rationale
        assert 'Poor performance' in rationale
        assert 'rapid iteration' in rationale.lower()

    def test_generate_performance_rationale_with_drawdown(self, generator):
        """Test: Performance rationale with low drawdown."""
        rationale = generator.generate_performance_rationale(
            template_name='TurtleTemplate',
            sharpe=1.1,
            success_rate=0.75,
            drawdown=0.08
        )

        assert 'TurtleTemplate' in rationale
        assert 'drawdown' in rationale.lower() or '8%' in rationale

    # Exploration Rationale Generation Tests
    def test_generate_exploration_rationale_basic(self, generator):
        """Test: Basic exploration rationale generation."""
        rationale = generator.generate_exploration_rationale(
            template_name='FactorTemplate',
            iteration=5,
            recent_templates=['TurtleTemplate', 'TurtleTemplate'],
            success_rate=0.70
        )

        assert 'EXPLORATION MODE' in rationale
        assert 'FactorTemplate' in rationale
        assert '5' in rationale
        assert '70%' in rationale

    def test_generate_exploration_rationale_shows_avoided_templates(self, generator):
        """Test: Exploration rationale shows avoided templates."""
        rationale = generator.generate_exploration_rationale(
            template_name='MomentumTemplate',
            iteration=10,
            recent_templates=['TurtleTemplate', 'MastiffTemplate', 'TurtleTemplate'],
            success_rate=0.65
        )

        assert 'Avoiding recently used templates' in rationale
        assert 'TurtleTemplate' in rationale
        assert 'MastiffTemplate' in rationale

    # Champion Rationale Generation Tests
    def test_generate_champion_rationale_basic(self, generator):
        """Test: Basic champion rationale generation."""
        rationale = generator.generate_champion_rationale(
            template_name='TurtleTemplate',
            champion_id='champion_42',
            champion_sharpe=2.5,
            champion_params={'n_stocks': 15, 'ma_short': 25, 'ma_long': 70}
        )

        assert 'champion_42' in rationale
        assert 'TurtleTemplate' in rationale
        assert '2.5' in rationale or '2.50' in rationale
        assert 'n_stocks=15' in rationale

    def test_generate_champion_rationale_high_sharpe(self, generator):
        """Test: Champion rationale for very high Sharpe (>3.0)."""
        rationale = generator.generate_champion_rationale(
            template_name='MastiffTemplate',
            champion_id='champion_elite',
            champion_sharpe=3.5,
            champion_params={'n_stocks': 5, 'contrarian_threshold': 0.2}
        )

        assert 'champion_elite' in rationale
        assert '3.5' in rationale or '3.50' in rationale

    # Validation Rationale Generation Tests
    def test_generate_validation_rationale_parameter_errors(self, generator):
        """Test: Validation rationale for parameter errors."""
        rationale = generator.generate_validation_rationale(
            template_name='TurtleTemplate',
            num_param_errors=2
        )

        assert 'TurtleTemplate' in rationale or 'parameter' in rationale.lower()
        assert '2' in rationale

    def test_generate_validation_rationale_complexity_errors(self, generator):
        """Test: Validation rationale for complexity errors."""
        rationale = generator.generate_validation_rationale(
            template_name='MastiffTemplate',
            num_complexity_errors=1
        )

        assert 'complexity' in rationale.lower()
        assert '1' in rationale

    def test_generate_validation_rationale_simplified_template(self, generator):
        """Test: Validation rationale when template simplified."""
        rationale = generator.generate_validation_rationale(
            template_name='FactorTemplate',
            num_complexity_errors=2,
            simplified_from='TurtleTemplate'
        )

        assert 'FactorTemplate' in rationale
        assert 'TurtleTemplate' in rationale
        assert 'simpler architecture' in rationale.lower()

    # Risk Profile Rationale Generation Tests
    def test_generate_risk_profile_rationale_concentrated(self, generator):
        """Test: Risk profile rationale for concentrated strategy."""
        rationale = generator.generate_risk_profile_rationale(
            template_name='MastiffTemplate',
            risk_profile='concentrated',
            success_rate=0.65
        )

        assert 'MastiffTemplate' in rationale
        assert 'concentrated' in rationale.lower()
        assert '65%' in rationale

    def test_generate_risk_profile_rationale_stable(self, generator):
        """Test: Risk profile rationale for stable strategy."""
        rationale = generator.generate_risk_profile_rationale(
            template_name='FactorTemplate',
            risk_profile='stable',
            success_rate=0.75
        )

        assert 'FactorTemplate' in rationale
        assert 'stable' in rationale.lower() or 'stability' in rationale.lower()

    def test_generate_risk_profile_rationale_fast(self, generator):
        """Test: Risk profile rationale for fast iteration."""
        rationale = generator.generate_risk_profile_rationale(
            template_name='MomentumTemplate',
            risk_profile='fast',
            success_rate=0.68
        )

        assert 'MomentumTemplate' in rationale
        assert 'fast' in rationale.lower() or 'rapid' in rationale.lower()

    # Template Description Tests
    def test_template_descriptions_exist(self, generator):
        """Test: All templates have descriptions."""
        templates = ['TurtleTemplate', 'MastiffTemplate', 'FactorTemplate', 'MomentumTemplate']

        for template in templates:
            assert template in generator.TEMPLATE_DESCRIPTIONS
            desc = generator.TEMPLATE_DESCRIPTIONS[template]

            assert 'architecture' in desc
            assert 'selection' in desc
            assert 'characteristics' in desc
            assert 'expected_sharpe' in desc
            assert 'risk_profile' in desc

    def test_template_descriptions_sharpe_ranges(self, generator):
        """Test: Template descriptions have valid Sharpe ranges."""
        for template, desc in generator.TEMPLATE_DESCRIPTIONS.items():
            sharpe_range = desc['expected_sharpe']

            assert isinstance(sharpe_range, tuple)
            assert len(sharpe_range) == 2
            assert sharpe_range[0] < sharpe_range[1]
            assert sharpe_range[0] >= 0.0

    def test_performance_tier_definitions(self, generator):
        """Test: Performance tier definitions are valid."""
        tiers = ['champion', 'contender', 'solid', 'archive', 'poor']

        for tier_name in tiers:
            assert tier_name in generator.PERFORMANCE_TIERS
            tier = generator.PERFORMANCE_TIERS[tier_name]

            assert 'min_sharpe' in tier
            assert 'label' in tier
            assert tier['min_sharpe'] >= 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
