"""
Test suite for UnifiedMutationOperator.

Tests unified interface for three-tier mutations including tier dispatch,
fallback logic, and statistics tracking.

Architecture: Structural Mutation Phase 2 - Phase D.5
Task: D.5 - Three-Tier Mutation System Integration
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.mutation.unified_mutation_operator import (
    UnifiedMutationOperator,
    MutationResult
)
from src.tier1.yaml_interpreter import YAMLInterpreter
from src.mutation.tier2.smart_mutation_engine import SmartMutationEngine
from src.mutation.tier3.ast_factor_mutator import ASTFactorMutator
from src.mutation.tier_selection.tier_selection_manager import (
    TierSelectionManager,
    MutationPlan,
    MutationTier
)
from src.factor_graph.strategy import Strategy
from src.factor_graph.factor import Factor, FactorCategory


@pytest.fixture
def mock_strategy():
    """Create mock strategy for testing."""
    strategy = Strategy(id="test_strategy", generation=0)

    # Add a simple factor
    factor = Factor(
        id="test_factor",
        name="Test Factor",
        category=FactorCategory.MOMENTUM,
        inputs=["close"],
        outputs=["signal"],
        logic=lambda data, params: data,
        parameters={"period": 20}
    )
    strategy.add_factor(factor)

    return strategy


@pytest.fixture
def mock_components():
    """Create mock components for unified operator."""
    yaml_interpreter = Mock(spec=YAMLInterpreter)

    # Mock tier2 engine
    tier2_engine = Mock(spec=SmartMutationEngine)
    tier2_operator = Mock()
    tier2_operator.mutate = Mock(return_value=Mock(spec=Strategy))
    tier2_engine.select_operator = Mock(return_value=("add_factor", tier2_operator))

    # Mock tier3 mutator
    tier3_mutator = Mock(spec=ASTFactorMutator)
    tier3_mutator.mutate = Mock(return_value=Mock(spec=Factor))

    # Mock tier selector
    tier_selector = Mock(spec=TierSelectionManager)

    return {
        "yaml_interpreter": yaml_interpreter,
        "tier2_engine": tier2_engine,
        "tier3_mutator": tier3_mutator,
        "tier_selector": tier_selector
    }


class TestUnifiedMutationOperator:
    """Test UnifiedMutationOperator functionality."""

    def test_initialization(self, mock_components):
        """Test operator initializes correctly."""
        operator = UnifiedMutationOperator(
            yaml_interpreter=mock_components["yaml_interpreter"],
            tier2_engine=mock_components["tier2_engine"],
            tier3_mutator=mock_components["tier3_mutator"],
            tier_selector=mock_components["tier_selector"]
        )

        assert operator is not None
        assert operator.enable_fallback is True
        assert operator.validate_mutations is True
        assert len(operator._mutation_history) == 0

    def test_tier2_mutation_success(self, mock_components, mock_strategy):
        """Test successful Tier 2 mutation."""
        # Setup tier selector to return Tier 2
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test Tier 2 mutation"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup tier2 engine to return mutated strategy
        mutated_strategy = Strategy(id="mutated_strategy", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        result = operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config={"intent": "add_factor"}
        )

        assert result.success is True
        assert result.tier_used == 2
        assert result.mutation_type == "add_factor"
        assert result.strategy is not None
        assert len(operator._mutation_history) == 1

    def test_tier3_mutation_with_fallback(self, mock_components, mock_strategy):
        """Test Tier 3 mutation with fallback to Tier 2."""
        # Setup tier selector to return Tier 3
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER3_AST,
            mutation_type="ast_mutation",
            config={},
            risk_score=0.8,
            rationale="Test Tier 3 mutation"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup tier3 to fail (will trigger fallback)
        mock_components["tier3_mutator"].mutate = Mock(
            side_effect=Exception("Tier 3 failed")
        )

        # Setup tier2 to succeed (fallback)
        mutated_strategy = Strategy(id="mutated_strategy", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        result = operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config={"intent": "ast_mutation"}
        )

        # Should succeed via fallback to Tier 2
        assert result.success is True
        assert result.tier_used == 2
        assert 3 in result.fallback_chain
        assert 2 in result.fallback_chain

    def test_all_tiers_fail(self, mock_components, mock_strategy):
        """Test when all tiers fail."""
        # Setup tier selector to return Tier 3
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER3_AST,
            mutation_type="ast_mutation",
            config={},
            risk_score=0.8,
            rationale="Test all tiers fail"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup all tiers to fail
        mock_components["tier3_mutator"].mutate = Mock(
            side_effect=Exception("Tier 3 failed")
        )

        tier2_operator = Mock()
        tier2_operator.mutate = Mock(side_effect=Exception("Tier 2 failed"))
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        result = operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config={"intent": "ast_mutation"}
        )

        assert result.success is False
        assert result.strategy is None
        assert len(result.fallback_chain) > 1
        assert "failed" in result.error.lower()

    def test_fallback_disabled(self, mock_components, mock_strategy):
        """Test mutation with fallback disabled."""
        # Setup tier selector to return Tier 3
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER3_AST,
            mutation_type="ast_mutation",
            config={},
            risk_score=0.8,
            rationale="Test no fallback"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup tier3 to fail
        mock_components["tier3_mutator"].mutate = Mock(
            side_effect=Exception("Tier 3 failed")
        )

        operator = UnifiedMutationOperator(
            **mock_components,
            enable_fallback=False,
            validate_mutations=False
        )

        result = operator.mutate_strategy(
            strategy=mock_strategy,
            mutation_config={"intent": "ast_mutation"}
        )

        # Should fail without attempting fallback
        assert result.success is False
        assert len(result.fallback_chain) == 1  # Only initial tier

    def test_get_tier_statistics(self, mock_components, mock_strategy):
        """Test getting tier statistics."""
        # Setup tier selector
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup tier2 engine
        mutated_strategy = Strategy(id="mutated", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        # Perform some mutations
        for i in range(5):
            operator.mutate_strategy(
                strategy=mock_strategy,
                mutation_config={"intent": "add_factor"}
            )

        stats = operator.get_tier_statistics()

        assert stats["total_mutations"] == 5
        assert stats["tier_attempts"][2] == 5
        assert stats["tier_successes"][2] == 5
        assert stats["tier_success_rates"][2] == 1.0

    def test_export_tier_analysis(self, mock_components, mock_strategy):
        """Test exporting tier analysis to file."""
        # Setup minimal mocks
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()
        mock_components["tier_selector"].export_state = Mock(return_value={})

        mutated_strategy = Strategy(id="mutated", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        # Perform a mutation
        operator.mutate_strategy(strategy=mock_strategy)

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / "tier_analysis.json"
            operator.export_tier_analysis(str(export_path))

            assert export_path.exists()

            with open(export_path, 'r') as f:
                data = json.load(f)

            assert "statistics" in data
            assert "tier_selector_state" in data
            assert "mutation_history" in data

    def test_reset_statistics(self, mock_components, mock_strategy):
        """Test resetting statistics."""
        # Setup mocks
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()
        mock_components["tier_selector"].reset_learning = Mock()

        mutated_strategy = Strategy(id="mutated", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        # Perform mutation
        operator.mutate_strategy(strategy=mock_strategy)

        assert len(operator._mutation_history) > 0

        # Reset
        operator.reset_statistics()

        assert len(operator._mutation_history) == 0
        assert all(operator._tier_attempts[tier] == 0 for tier in [1, 2, 3])

    def test_validation_failure(self, mock_components, mock_strategy):
        """Test mutation with validation failure."""
        # Setup tier selector
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        # Setup tier2 to return invalid strategy
        invalid_strategy = Mock(spec=Strategy)
        invalid_strategy.validate = Mock(side_effect=Exception("Validation failed"))
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=invalid_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(
            **mock_components,
            validate_mutations=True  # Enable validation
        )

        result = operator.mutate_strategy(strategy=mock_strategy)

        assert result.success is False
        # Validation failure triggers fallback, so error message is about fallback failure
        assert result.error is not None

    def test_mutation_result_structure(self, mock_components, mock_strategy):
        """Test mutation result structure is complete."""
        mutation_plan = MutationPlan(
            tier=MutationTier.TIER2_FACTOR,
            mutation_type="add_factor",
            config={},
            risk_score=0.5,
            rationale="Test"
        )
        mock_components["tier_selector"].select_mutation_tier = Mock(return_value=mutation_plan)
        mock_components["tier_selector"].record_mutation_result = Mock()

        mutated_strategy = Strategy(id="mutated", generation=1)
        tier2_operator = Mock()
        tier2_operator.mutate = Mock(return_value=mutated_strategy)
        mock_components["tier2_engine"].select_operator = Mock(
            return_value=("add_factor", tier2_operator)
        )

        operator = UnifiedMutationOperator(**mock_components, validate_mutations=False)

        result = operator.mutate_strategy(strategy=mock_strategy)

        # Check all required fields
        assert hasattr(result, 'success')
        assert hasattr(result, 'strategy')
        assert hasattr(result, 'tier_used')
        assert hasattr(result, 'mutation_type')
        assert hasattr(result, 'error')
        assert hasattr(result, 'fallback_chain')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'timestamp')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
