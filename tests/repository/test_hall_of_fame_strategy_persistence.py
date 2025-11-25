"""
Unit tests for HallOfFameRepository Strategy persistence.

Tests Factor Graph Strategy serialization using Strategy.to_dict()/from_dict().
Verifies DAG structure preservation, metadata retention, and error handling.

Test Coverage:
- Roundtrip serialization (save → load → verify)
- DAG structure preservation (nodes, edges, topology)
- Metadata preservation (strategy_id, generation, parent_ids)
- Error handling (corrupted JSON, missing fields)
- Tier-based storage (Champions/Contenders/Archive)
"""

import pytest
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.repository.hall_of_fame import HallOfFameRepository
from src.evolution.types import Strategy, MultiObjectiveMetrics


@pytest.fixture
def temp_repo():
    """Create temporary HallOfFameRepository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = HallOfFameRepository(base_path=tmpdir, test_mode=True)
        yield repo


@pytest.fixture
def sample_strategy():
    """Create a sample Strategy object for testing."""
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
        id='test-strategy-001',
        generation=5,
        parent_ids=['parent-001', 'parent-002'],
        code='def strategy(): pass',
        parameters={'n_stocks': 20, 'lookback': 60},
        metrics=metrics,
        novelty_score=0.85,
        pareto_rank=1,
        crowding_distance=0.75,
        timestamp='2025-01-19T10:30:00',
        template_type='FactorGraph',
        metadata={'author': 'test', 'version': '1.0'}
    )

    return strategy


def test_save_and_load_strategy_roundtrip(temp_repo, sample_strategy):
    """Test Strategy save and load roundtrip preserves all data."""
    # Save strategy to champions tier
    temp_repo.save_strategy(sample_strategy, tier='champions')

    # Load strategy back
    loaded_strategy = temp_repo.load_strategy(tier='champions')

    # Verify loaded strategy is not None
    assert loaded_strategy is not None, "Failed to load saved strategy"

    # Verify all fields preserved
    assert loaded_strategy.id == sample_strategy.id
    assert loaded_strategy.generation == sample_strategy.generation
    assert loaded_strategy.parent_ids == sample_strategy.parent_ids
    assert loaded_strategy.code == sample_strategy.code
    assert loaded_strategy.parameters == sample_strategy.parameters
    assert loaded_strategy.novelty_score == sample_strategy.novelty_score
    assert loaded_strategy.pareto_rank == sample_strategy.pareto_rank
    assert loaded_strategy.crowding_distance == sample_strategy.crowding_distance
    assert loaded_strategy.timestamp == sample_strategy.timestamp
    assert loaded_strategy.template_type == sample_strategy.template_type
    assert loaded_strategy.metadata == sample_strategy.metadata

    # Verify metrics preserved
    assert loaded_strategy.metrics is not None
    assert loaded_strategy.metrics.sharpe_ratio == sample_strategy.metrics.sharpe_ratio
    assert loaded_strategy.metrics.calmar_ratio == sample_strategy.metrics.calmar_ratio
    assert loaded_strategy.metrics.max_drawdown == sample_strategy.metrics.max_drawdown
    assert loaded_strategy.metrics.total_return == sample_strategy.metrics.total_return
    assert loaded_strategy.metrics.win_rate == sample_strategy.metrics.win_rate
    assert loaded_strategy.metrics.annual_return == sample_strategy.metrics.annual_return
    assert loaded_strategy.metrics.success == sample_strategy.metrics.success


def test_dag_structure_preservation(temp_repo):
    """Test DAG structure (nodes, edges, topology) is preserved."""
    # Create strategy with complex DAG structure
    metrics = MultiObjectiveMetrics(
        sharpe_ratio=2.2,
        calmar_ratio=1.5,
        max_drawdown=-0.18,
        total_return=0.35,
        win_rate=0.58,
        annual_return=0.22,
        success=True
    )

    strategy = Strategy(
        id='dag-strategy-001',
        generation=3,
        parent_ids=['parent-a', 'parent-b', 'parent-c'],
        code='# Complex DAG\nnode1 = Selection()\nnode2 = Filter()\nedge = node1 -> node2',
        parameters={
            'dag_nodes': ['Selection', 'Filter', 'Strategy'],
            'dag_edges': [('Selection', 'Filter'), ('Filter', 'Strategy')],
            'node_params': {
                'Selection': {'top_n': 50, 'method': 'momentum'},
                'Filter': {'threshold': 0.05, 'lookback': 20}
            }
        },
        metrics=metrics,
        novelty_score=0.92,
        pareto_rank=0,
        crowding_distance=1.0,
        timestamp='2025-01-19T11:00:00',
        template_type='FactorGraph',
        metadata={'dag_depth': 3, 'total_nodes': 5}
    )

    # Save and load
    temp_repo.save_strategy(strategy, tier='champions')
    loaded = temp_repo.load_strategy(tier='champions')

    # Verify DAG structure preserved
    assert loaded is not None
    assert loaded.parameters['dag_nodes'] == strategy.parameters['dag_nodes']

    # Note: JSON serialization converts tuples to lists, so we compare content not types
    assert len(loaded.parameters['dag_edges']) == len(strategy.parameters['dag_edges'])
    for i, edge in enumerate(loaded.parameters['dag_edges']):
        # Compare edge content (both tuples and lists are acceptable)
        assert list(edge) == list(strategy.parameters['dag_edges'][i])

    assert loaded.parameters['node_params'] == strategy.parameters['node_params']
    assert loaded.metadata['dag_depth'] == strategy.metadata['dag_depth']
    assert loaded.metadata['total_nodes'] == strategy.metadata['total_nodes']


def test_metadata_preservation(temp_repo, sample_strategy):
    """Test metadata (strategy_id, generation, parent_ids) is preserved."""
    # Save strategy
    temp_repo.save_strategy(sample_strategy, tier='contenders')

    # Load strategy
    loaded = temp_repo.load_strategy(tier='contenders')

    # Verify metadata preserved
    assert loaded is not None
    assert loaded.id == sample_strategy.id, "Strategy ID not preserved"
    assert loaded.generation == sample_strategy.generation, "Generation not preserved"
    assert loaded.parent_ids == sample_strategy.parent_ids, "Parent IDs not preserved"
    assert len(loaded.parent_ids) == 2, "Parent IDs list length incorrect"


def test_save_to_different_tiers(temp_repo, sample_strategy):
    """Test saving strategies to different tiers (champions/contenders/archive)."""
    # Save to champions
    temp_repo.save_strategy(sample_strategy, tier='champions')
    loaded_champ = temp_repo.load_strategy(tier='champions')
    assert loaded_champ is not None
    assert loaded_champ.id == sample_strategy.id

    # Save to contenders (different strategy)
    sample_strategy.id = 'test-strategy-002'
    sample_strategy.metrics.sharpe_ratio = 1.8
    temp_repo.save_strategy(sample_strategy, tier='contenders')
    loaded_cont = temp_repo.load_strategy(tier='contenders')
    assert loaded_cont is not None
    assert loaded_cont.id == 'test-strategy-002'

    # Save to archive (different strategy)
    sample_strategy.id = 'test-strategy-003'
    sample_strategy.metrics.sharpe_ratio = 1.2
    temp_repo.save_strategy(sample_strategy, tier='archive')
    loaded_arch = temp_repo.load_strategy(tier='archive')
    assert loaded_arch is not None
    assert loaded_arch.id == 'test-strategy-003'


def test_error_handling_corrupted_json(temp_repo):
    """Test error handling for corrupted JSON files."""
    # Create corrupted JSON file
    champions_dir = temp_repo.champions_dir
    corrupted_file = champions_dir / 'corrupted_strategy.json'

    with open(corrupted_file, 'w') as f:
        f.write('{ invalid json content :::')

    # Attempt to load should return None (graceful failure)
    loaded = temp_repo.load_strategy(tier='champions')
    assert loaded is None, "Should return None for corrupted JSON"


def test_error_handling_missing_fields(temp_repo):
    """Test error handling for JSON with missing required fields."""
    # Create JSON with missing 'code' field
    champions_dir = temp_repo.champions_dir
    incomplete_file = champions_dir / 'incomplete_strategy.json'

    incomplete_data = {
        'id': 'incomplete-001',
        'generation': 1,
        # Missing 'code' field
        'parameters': {},
        'parent_ids': []
    }

    with open(incomplete_file, 'w') as f:
        json.dump(incomplete_data, f)

    # Attempt to load should return None (validation failure)
    loaded = temp_repo.load_strategy(tier='champions')
    assert loaded is None, "Should return None for incomplete JSON"


def test_invalid_tier_raises_error(temp_repo, sample_strategy):
    """Test that invalid tier name raises ValueError."""
    with pytest.raises(ValueError, match="Invalid tier"):
        temp_repo.save_strategy(sample_strategy, tier='invalid_tier')


def test_load_from_empty_tier(temp_repo):
    """Test loading from empty tier returns None."""
    loaded = temp_repo.load_strategy(tier='champions')
    assert loaded is None, "Should return None when no strategies in tier"


def test_strategy_with_no_metrics(temp_repo):
    """Test Strategy with None metrics can be saved and loaded."""
    strategy = Strategy(
        id='no-metrics-001',
        generation=1,
        parent_ids=[],
        code='def strategy(): pass',
        parameters={'test': 123},
        metrics=None,  # No metrics
        novelty_score=0.5,
        pareto_rank=0,
        crowding_distance=0.0,
        timestamp='2025-01-19T12:00:00',
        template_type='FactorGraph',
        metadata={}
    )

    # Save and load
    temp_repo.save_strategy(strategy, tier='archive')
    loaded = temp_repo.load_strategy(tier='archive')

    # Verify
    assert loaded is not None
    assert loaded.id == strategy.id
    assert loaded.metrics is None, "Metrics should remain None"


def test_strategy_with_empty_parent_ids(temp_repo):
    """Test Strategy with empty parent_ids list (first generation)."""
    metrics = MultiObjectiveMetrics(
        sharpe_ratio=2.0,
        calmar_ratio=1.4,
        max_drawdown=-0.20,
        total_return=0.30,
        win_rate=0.55,
        annual_return=0.20,
        success=True
    )

    strategy = Strategy(
        id='first-gen-001',
        generation=0,
        parent_ids=[],  # Empty for first generation
        code='def strategy(): pass',
        parameters={'initial': True},
        metrics=metrics,
        novelty_score=1.0,
        pareto_rank=0,
        crowding_distance=0.0,
        timestamp='2025-01-19T12:30:00',
        template_type='FactorGraph',
        metadata={'first_generation': True}
    )

    # Save and load
    temp_repo.save_strategy(strategy, tier='champions')
    loaded = temp_repo.load_strategy(tier='champions')

    # Verify
    assert loaded is not None
    assert loaded.parent_ids == []
    assert loaded.generation == 0


def test_multiple_saves_overwrite(temp_repo, sample_strategy):
    """Test that saving to same tier multiple times overwrites previous."""
    # Save first strategy
    temp_repo.save_strategy(sample_strategy, tier='champions')
    loaded1 = temp_repo.load_strategy(tier='champions')
    assert loaded1.id == sample_strategy.id

    # Save different strategy to same tier
    sample_strategy.id = 'test-strategy-new'
    sample_strategy.generation = 10
    temp_repo.save_strategy(sample_strategy, tier='champions')
    loaded2 = temp_repo.load_strategy(tier='champions')

    # Verify new strategy loaded (overwritten)
    assert loaded2.id == 'test-strategy-new'
    assert loaded2.generation == 10
