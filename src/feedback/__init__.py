"""
Template Feedback Integration System
====================================

Intelligent template recommendation and feedback system for strategy generation.
Provides template selection based on performance, champion strategies, and exploration.

Components:
    - TemplateFeedbackIntegrator: Core recommendation engine
    - TemplateRecommendation: Recommendation data model
    - Template match scoring and performance-based selection
    - Champion-based parameter suggestions
    - Forced exploration mode for diversity

Usage:
    from src.feedback import TemplateFeedbackIntegrator, TemplateRecommendation
    from src.repository import HallOfFameRepository

    repository = HallOfFameRepository(base_path='hall_of_fame')
    integrator = TemplateFeedbackIntegrator(repository)

    # Get template recommendation
    recommendation = integrator.recommend_template(
        current_metrics={'sharpe_ratio': 0.8},
        iteration=5,
        validation_result=None
    )

    print(f"Recommended: {recommendation.template_name}")
    print(f"Rationale: {recommendation.rationale}")
    print(f"Suggested params: {recommendation.suggested_params}")

Features:
    - Performance-based template selection
    - Champion strategy analysis
    - Exploration mode (every 5th iteration)
    - Validation-aware feedback
    - Template match scoring (0.0-1.0)
    - Parameter suggestion from champions

Requirements:
    - Requirement 4.1: Template recommendation system
    - Requirement 4.2: Performance-based selection
    - Requirement 4.3: Champion-based suggestions
    - Requirement 4.4: Forced exploration
    - Requirement 4.5: Validation feedback
"""

from .template_feedback import TemplateFeedbackIntegrator, TemplateRecommendation
from .rationale_generator import RationaleGenerator
from .loop_integration import FeedbackLoopIntegrator, IterationFeedback
from .template_analytics import TemplateAnalytics, TemplateUsageRecord
from .template_feedback_integrator import TemplateStatsTracker, TemplateStats

__all__ = [
    'TemplateFeedbackIntegrator',
    'TemplateRecommendation',
    'RationaleGenerator',
    'FeedbackLoopIntegrator',
    'IterationFeedback',
    'TemplateAnalytics',
    'TemplateUsageRecord',
    'TemplateStatsTracker',
    'TemplateStats'
]
