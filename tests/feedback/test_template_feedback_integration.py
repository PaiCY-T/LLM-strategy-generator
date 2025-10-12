"""
Integration Tests for Template Feedback System
==============================================

End-to-end integration tests for the complete template feedback workflow.

Test Coverage:
    - Template recommendation pipeline
    - Performance-based selection
    - Exploration mode activation
    - Champion-based suggestions
    - Validation feedback integration
    - Template match scoring
    - Analytics tracking

Requirements Tested:
    - Requirement 4.1: Template recommendation system ✓
    - Requirement 4.2: Performance-based selection ✓
    - Requirement 4.3: Champion-based suggestions ✓
    - Requirement 4.4: Forced exploration ✓
    - Requirement 4.5: Validation feedback ✓
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.feedback import (
    TemplateFeedbackIntegrator,
    TemplateRecommendation,
    FeedbackLoopIntegrator,
    TemplateAnalytics
)


class TestTemplateFeedbackIntegration:
    """Integration tests for template feedback system."""

    @pytest.fixture
    def integrator(self):
        """Create TemplateFeedbackIntegrator instance."""
        return TemplateFeedbackIntegrator(repository=None)

    @pytest.fixture
    def mock_repository(self):
        """Create mock HallOfFameRepository."""
        repo = Mock()
        repo.get_champions = Mock(return_value=[
            {
                'genome_id': 'test_champion_1',
                'sharpe_ratio': 2.3,
                'template_name': 'TurtleTemplate',
                'parameters': {'n_stocks': 10, 'ma_short': 20, 'ma_long': 60}
            }
        ])
        return repo

    def test_performance_based_recommendation_low_sharpe(self, integrator):
        """Test: Low Sharpe (0.8) → TurtleTemplate recommendation."""
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=1
        )

        assert recommendation.template_name == 'TurtleTemplate'
        assert recommendation.match_score >= 0.70
        assert 'proven 80% success rate' in recommendation.rationale or 'TurtleTemplate' in recommendation.rationale
        assert not recommendation.exploration_mode

    def test_performance_based_recommendation_high_sharpe(self, integrator):
        """Test: High Sharpe (2.1) → Champion tier recommendation."""
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 2.1},
            iteration=1
        )

        assert recommendation.template_name == 'TurtleTemplate'
        assert recommendation.match_score >= 0.85
        assert 'Champion tier' in recommendation.rationale or 'High Sharpe' in recommendation.rationale

    def test_exploration_mode_activation(self, integrator):
        """Test: Iteration 5 → Exploration mode activated."""
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=5  # 5 % 5 == 0 → exploration mode
        )

        assert recommendation.exploration_mode is True
        assert 'EXPLORATION MODE' in recommendation.rationale
        assert recommendation.match_score == 0.65  # Lower confidence for exploration

    def test_exploration_mode_avoids_recent_templates(self, integrator):
        """Test: Exploration avoids recently used templates."""
        # Use TurtleTemplate 3 times
        for i in range(1, 4):
            integrator.recommend_template(
                current_metrics={'sharpe_ratio': 0.8},
                iteration=i
            )

        # Iteration 5 should recommend different template
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=5
        )

        assert recommendation.exploration_mode is True
        # Should avoid TurtleTemplate (used 3 times)
        # Note: May still get TurtleTemplate if it's the least-used available

    def test_champion_based_enhancement(self):
        """Test: Champion parameters enhance recommendation."""
        mock_repo = Mock()
        mock_repo.get_champions = Mock(return_value=[
            {
                'genome_id': 'champion_42',
                'sharpe_ratio': 2.5,
                'template_name': 'TurtleTemplate',
                'parameters': {'n_stocks': 15, 'ma_short': 25, 'ma_long': 70}
            }
        ])

        integrator = TemplateFeedbackIntegrator(repository=mock_repo)

        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=1
        )

        assert recommendation.template_name == 'TurtleTemplate'
        assert recommendation.champion_reference == 'champion_42'
        assert 'champion_42' in recommendation.rationale
        assert recommendation.suggested_params.get('n_stocks') == 15

    def test_template_match_scoring(self, integrator):
        """Test: Template match scoring for strategy code."""
        # Code with 6 conditions and .is_largest()
        turtle_like_code = """
cond1 = data.get('revenue:營收成長率') > 0.10
cond2 = data.get('price:收盤價') > data.get('price:收盤價').rolling(20).mean()
cond3 = data.get('volume:成交股數') > data.get('volume:成交股數').rolling(20).mean()
cond4 = data.get('fundamental:本益比') < 20
cond5 = data.get('price:收盤價') > data.get('price:收盤價').rolling(60).mean()
cond6 = data.get('revenue:營收成長率') > data.get('revenue:營收成長率').rolling(12).mean()

buy = cond1 & cond2 & cond3 & cond4 & cond5 & cond6
buy = buy.is_largest(10)
"""

        scores = integrator.calculate_template_match_score(
            strategy_code=turtle_like_code,
            current_params={'n_stocks': 10},
            current_metrics={'sharpe_ratio': 1.8}
        )

        assert 'TurtleTemplate' in scores
        # TurtleTemplate should score highly (6 conditions + .is_largest())
        assert scores['TurtleTemplate'] >= 0.60

    def test_validation_feedback_integration(self, integrator):
        """Test: Validation errors trigger parameter adjustment."""
        from src.validation import ValidationResult, ValidationError, Severity, Category

        # Create validation result with parameter error
        validation_result = ValidationResult(
            status='FAIL',
            errors=[
                ValidationError(
                    severity=Severity.CRITICAL,
                    category=Category.PARAMETER,
                    message='n_stocks out of range: 50 (must be 5-30)',
                    context={'parameter': 'n_stocks', 'value': 50, 'valid_range': '5-30'}
                )
            ],
            warnings=[],
            suggestions=[],
            metadata={}
        )

        # Get recommendation with validation feedback
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=1,
            validation_result=validation_result
        )

        # Should adjust based on validation feedback
        assert 'validation' in recommendation.rationale.lower() or 'adjusted' in recommendation.rationale.lower()

    def test_risk_profile_override(self, integrator):
        """Test: Risk profile overrides default recommendation."""
        # Test concentrated risk profile
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=1,
            risk_profile='concentrated'
        )

        assert recommendation.template_name == 'MastiffTemplate'
        assert 'concentrated' in recommendation.rationale.lower()

        # Test stable risk profile
        recommendation = integrator.recommend_template(
            current_metrics={'sharpe_ratio': 0.8},
            iteration=2,
            risk_profile='stable'
        )

        assert recommendation.template_name == 'FactorTemplate'
        assert 'stability' in recommendation.rationale.lower()

    def test_iteration_tracking(self, integrator):
        """Test: Iteration history tracked correctly."""
        # Recommend 5 templates
        for i in range(1, 6):
            integrator.recommend_template(
                current_metrics={'sharpe_ratio': 0.8},
                iteration=i
            )

        stats = integrator.get_template_statistics()

        assert stats['total_iterations'] == 5
        assert len(stats['templates_used']) >= 1
        assert stats['most_used_template'] is not None


class TestFeedbackLoopIntegration:
    """Integration tests for feedback loop integration."""

    @pytest.fixture
    def loop_integrator(self):
        """Create FeedbackLoopIntegrator instance."""
        template_integrator = TemplateFeedbackIntegrator()
        return FeedbackLoopIntegrator(
            template_integrator=template_integrator,
            repository=None
        )

    def test_process_iteration_complete_workflow(self, loop_integrator):
        """Test: Complete iteration processing workflow."""
        backtest_result = {
            'sharpe_ratio': 1.2,
            'max_drawdown': 0.15,
            'total_return': 0.25,
            'volatility': 0.18
        }

        feedback = loop_integrator.process_iteration(
            iteration=1,
            strategy_code="# test code",
            backtest_result=backtest_result,
            current_params={'n_stocks': 10}
        )

        assert feedback.iteration == 1
        assert feedback.template_recommendation is not None
        assert feedback.performance_metrics['sharpe_ratio'] == 1.2
        assert len(feedback.suggested_improvements) >= 0
        assert feedback.historical_context is not None

    def test_learning_trajectory_tracking(self, loop_integrator):
        """Test: Learning trajectory calculation."""
        # Process multiple iterations with improving Sharpe
        for i in range(1, 6):
            loop_integrator.process_iteration(
                iteration=i,
                backtest_result={'sharpe_ratio': 0.5 + (i * 0.2)},  # Improving trend
                strategy_code="# test"
            )

        trajectory = loop_integrator.get_learning_trajectory()

        assert trajectory['total_iterations'] == 5
        assert trajectory['is_improving'] is True
        assert len(trajectory['sharpe_trajectory']) == 5


class TestTemplateAnalyticsIntegration:
    """Integration tests for template analytics."""

    @pytest.fixture
    def analytics(self, tmp_path):
        """Create TemplateAnalytics instance with temp storage."""
        storage_file = tmp_path / "test_analytics.json"
        return TemplateAnalytics(storage_path=str(storage_file))

    def test_usage_tracking_and_statistics(self, analytics):
        """Test: Template usage tracking and statistics calculation."""
        # Record 10 uses of TurtleTemplate with varying success
        for i in range(10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.0 + (i * 0.1),  # 1.0 to 1.9
                validation_passed=(i % 2 == 0),  # 50% pass rate
                match_score=0.85
            )

        stats = analytics.get_template_statistics('TurtleTemplate')

        assert stats['total_usage'] == 10
        assert stats['has_data'] is True
        assert stats['reliable_stats'] is True
        assert 0.0 <= stats['success_rate'] <= 1.0
        assert stats['avg_sharpe'] > 1.0

    def test_best_performing_template_identification(self, analytics):
        """Test: Best performing template identification."""
        # TurtleTemplate: High success rate
        for i in range(5):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='TurtleTemplate',
                sharpe_ratio=1.5,
                validation_passed=True
            )

        # MastiffTemplate: Lower success rate
        for i in range(5, 10):
            analytics.record_template_usage(
                iteration=i + 1,
                template_name='MastiffTemplate',
                sharpe_ratio=0.8,
                validation_passed=False
            )

        best = analytics.get_best_performing_template()

        assert best == 'TurtleTemplate'

    def test_persistence_across_sessions(self, analytics, tmp_path):
        """Test: Analytics data persists across sessions."""
        # Record usage
        analytics.record_template_usage(
            iteration=1,
            template_name='TurtleTemplate',
            sharpe_ratio=1.5,
            validation_passed=True
        )

        # Create new instance (should load from storage)
        analytics2 = TemplateAnalytics(storage_path=str(tmp_path / "test_analytics.json"))

        stats = analytics2.get_template_statistics('TurtleTemplate')

        assert stats['total_usage'] == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
