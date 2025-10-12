"""
Tests for HallOfFameRepository - Strategy Genome Storage

Test Coverage:
    - Tier classification (champions, contenders, archive)
    - Adding strategies with novelty checking
    - Duplicate detection
    - Retrieval methods (champions, contenders, archive, best strategy)
    - Persistence (save/load)
    - Query methods
    - Statistics

Fixtures Used:
    - tmp_path: pytest built-in temporary directory
    - sample_strategy_genome: Sample genome dictionary
"""

import pytest
import copy
from pathlib import Path
from src.repository.hall_of_fame import HallOfFameRepository, StrategyGenome


class TestHallOfFameRepository:
    """Test suite for HallOfFameRepository."""

    def test_initialization(self, tmp_path):
        """Test repository initialization creates required directories."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Check all tier directories exist
        assert (tmp_path / "hof" / "champions").exists()
        assert (tmp_path / "hof" / "contenders").exists()
        assert (tmp_path / "hof" / "archive").exists()
        assert (tmp_path / "hof" / "backup").exists()

    def test_classify_tier_champions(self, tmp_path):
        """Test tier classification for champions (Sharpe >= 2.0)."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Test champion classification
        assert repo._classify_tier(2.5) == 'champions'
        assert repo._classify_tier(2.0) == 'champions'

    def test_classify_tier_contenders(self, tmp_path):
        """Test tier classification for contenders (1.5 <= Sharpe < 2.0)."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        assert repo._classify_tier(1.9) == 'contenders'
        assert repo._classify_tier(1.5) == 'contenders'

    def test_classify_tier_archive(self, tmp_path):
        """Test tier classification for archive (Sharpe < 1.5)."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        assert repo._classify_tier(1.4) == 'archive'
        assert repo._classify_tier(1.0) == 'archive'
        assert repo._classify_tier(0.5) == 'archive'

    def test_add_strategy_champions_tier(self, tmp_path, sample_strategy_genome):
        """Test adding high-performing strategy to champions tier."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        genome_dict = sample_strategy_genome.copy()
        genome_dict['metrics']['sharpe_ratio'] = 2.5  # High performance

        success, message = repo.add_strategy(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            strategy_code=genome_dict['code']
        )

        assert success is True
        assert 'champions' in message

        # Verify it's in champions tier
        champions = repo.get_champions()
        assert len(champions) == 1
        assert champions[0].metrics['sharpe_ratio'] == 2.5

    def test_add_strategy_contenders_tier(self, tmp_path, sample_strategy_genome):
        """Test adding medium-performing strategy to contenders tier."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        genome_dict = sample_strategy_genome.copy()
        genome_dict['metrics']['sharpe_ratio'] = 1.8  # Medium performance

        success, message = repo.add_strategy(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            strategy_code=genome_dict['code']
        )

        assert success is True
        assert 'contenders' in message

        # Verify it's in contenders tier
        contenders = repo.get_contenders()
        assert len(contenders) == 1

    def test_add_strategy_archive_tier(self, tmp_path, sample_strategy_genome):
        """Test adding low-performing strategy to archive tier."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        genome_dict = sample_strategy_genome.copy()
        genome_dict['metrics']['sharpe_ratio'] = 1.2  # Low performance

        success, message = repo.add_strategy(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            strategy_code=genome_dict['code']
        )

        assert success is True
        assert 'archive' in message

    def test_add_strategy_missing_sharpe_ratio(self, tmp_path, sample_strategy_genome):
        """Test adding strategy without sharpe_ratio fails."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        genome_dict = sample_strategy_genome.copy()
        del genome_dict['metrics']['sharpe_ratio']  # Remove required metric

        success, message = repo.add_strategy(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            strategy_code=genome_dict['code']
        )

        assert success is False
        assert 'sharpe_ratio' in message

    def test_get_champions_sorted(self, tmp_path, sample_strategy_genome):
        """Test get_champions returns sorted by Sharpe ratio."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Add 3 champions with different Sharpe ratios
        for i, sharpe in enumerate([2.3, 2.8, 2.5]):
            genome_dict = copy.deepcopy(sample_strategy_genome)  # Use deepcopy to avoid shared mutable objects
            genome_dict['strategy_id'] = f'strategy_{i}'
            genome_dict['metrics']['sharpe_ratio'] = sharpe

            repo.add_strategy(
                template_name=genome_dict['template'],
                parameters=genome_dict['params'],
                metrics=genome_dict['metrics'],
                strategy_code=genome_dict['code']
            )

        champions = repo.get_champions(limit=3)

        # Should be sorted by Sharpe (descending)
        assert len(champions) == 3
        assert champions[0].metrics['sharpe_ratio'] == 2.8
        assert champions[1].metrics['sharpe_ratio'] == 2.5
        assert champions[2].metrics['sharpe_ratio'] == 2.3

    def test_get_current_champion(self, tmp_path, sample_strategy_genome):
        """Test get_current_champion returns highest Sharpe champion."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Add champions
        for i, sharpe in enumerate([2.3, 2.8, 2.5]):
            genome_dict = copy.deepcopy(sample_strategy_genome)  # Use deepcopy to avoid shared mutable objects
            genome_dict['strategy_id'] = f'strategy_{i}'
            genome_dict['metrics']['sharpe_ratio'] = sharpe

            repo.add_strategy(
                template_name=genome_dict['template'],
                parameters=genome_dict['params'],
                metrics=genome_dict['metrics'],
                strategy_code=genome_dict['code']
            )

        champion = repo.get_current_champion()

        # Should be the highest Sharpe
        assert champion is not None
        assert champion.metrics['sharpe_ratio'] == 2.8

    def test_get_current_champion_no_champions(self, tmp_path):
        """Test get_current_champion returns None when no champions exist."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        champion = repo.get_current_champion()

        assert champion is None

    def test_persistence_save_load(self, tmp_path, sample_strategy_genome):
        """Test saving and loading Hall of Fame state."""
        hof_path = tmp_path / "hof"
        repo1 = HallOfFameRepository(base_path=str(hof_path), test_mode=True)

        genome_dict = sample_strategy_genome.copy()
        genome_dict['metrics']['sharpe_ratio'] = 2.5

        # Add strategy
        repo1.add_strategy(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            strategy_code=genome_dict['code']
        )

        # Create new repo instance (simulates restart)
        repo2 = HallOfFameRepository(base_path=str(hof_path), test_mode=True)

        # Should load existing strategy from file
        champions = repo2.get_champions()
        assert len(champions) == 1
        assert champions[0].metrics['sharpe_ratio'] == 2.5

    def test_get_statistics(self, tmp_path, sample_strategy_genome):
        """Test repository statistics generation."""
        repo = HallOfFameRepository(base_path=str(tmp_path / "hof"), test_mode=True)

        # Add strategies to different tiers
        for i, sharpe in enumerate([2.5, 1.8, 1.2]):
            genome_dict = copy.deepcopy(sample_strategy_genome)  # Use deepcopy to avoid shared mutable objects
            genome_dict['strategy_id'] = f'strategy_{i}'
            genome_dict['metrics']['sharpe_ratio'] = sharpe

            repo.add_strategy(
                template_name=genome_dict['template'],
                parameters=genome_dict['params'],
                metrics=genome_dict['metrics'],
                strategy_code=genome_dict['code']
            )

        stats = repo.get_statistics()

        # Check statistics
        assert stats['champions'] == 1
        assert stats['contenders'] == 1
        assert stats['archive'] == 1
        assert stats['total'] == 3


class TestStrategyGenome:
    """Test suite for StrategyGenome dataclass."""

    def test_genome_initialization(self, sample_strategy_genome):
        """Test StrategyGenome initialization."""
        genome_dict = sample_strategy_genome.copy()

        genome = StrategyGenome(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            created_at=genome_dict['timestamp'],
            strategy_code=genome_dict['code']
        )

        assert genome.template_name == 'turtle'
        assert genome.metrics['sharpe_ratio'] == 2.5
        assert genome.genome_id is not None

    def test_genome_to_dict(self, sample_strategy_genome):
        """Test genome to_dict conversion."""
        genome_dict = sample_strategy_genome.copy()

        genome = StrategyGenome(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            created_at=genome_dict['timestamp'],
            strategy_code=genome_dict['code']
        )

        data = genome.to_dict()

        assert isinstance(data, dict)
        assert 'template_name' in data
        assert 'parameters' in data
        assert 'metrics' in data
        assert 'genome_id' in data

    def test_genome_to_json(self, sample_strategy_genome):
        """Test genome to_json serialization."""
        genome_dict = sample_strategy_genome.copy()

        genome = StrategyGenome(
            template_name=genome_dict['template'],
            parameters=genome_dict['params'],
            metrics=genome_dict['metrics'],
            created_at=genome_dict['timestamp'],
            strategy_code=genome_dict['code']
        )

        json_str = genome.to_json()

        assert isinstance(json_str, str)
        assert 'template_name' in json_str
        assert 'turtle' in json_str

    def test_genome_from_json(self):
        """Test genome from_json deserialization."""
        json_str = '''
        {
            "genome_id": "turtle_test_001",
            "template_name": "turtle",
            "parameters": {"n_stocks": 10},
            "metrics": {"sharpe_ratio": 2.5},
            "created_at": "2025-10-12T10:00:00"
        }
        '''

        genome = StrategyGenome.from_json(json_str)

        assert genome.template_name == 'turtle'
        assert genome.metrics['sharpe_ratio'] == 2.5
        assert genome.genome_id == 'turtle_test_001'
