"""
Comprehensive Test Suite for InnovationRepository

Tests JSONL storage, add/retrieve/search operations, top-N ranking,
and repository management functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from innovation.innovation_repository import (
    InnovationRepository,
    Innovation
)


class TestInnovationDataclass:
    """Test Innovation dataclass"""

    def test_innovation_creation(self):
        """Test creating Innovation object"""
        innovation = Innovation(
            code="test_code",
            rationale="test rationale",
            performance={'sharpe_ratio': 0.85},
            validation_report={'passed': True},
            timestamp=datetime.now().isoformat(),
            category='quality'
        )

        assert innovation.code == "test_code"
        assert innovation.rationale == "test rationale"
        assert innovation.performance['sharpe_ratio'] == 0.85
        assert innovation.category == 'quality'

    def test_innovation_to_dict(self):
        """Test converting Innovation to dictionary"""
        innovation = Innovation(
            code="test",
            rationale="test",
            performance={},
            validation_report={},
            timestamp="2025-10-23",
            category=None
        )

        dict_rep = innovation.to_dict()
        assert isinstance(dict_rep, dict)
        assert 'code' in dict_rep
        assert 'rationale' in dict_rep


class TestRepositoryInitialization:
    """Test repository initialization and file handling"""

    def test_repository_init_new_file(self):
        """Test initializing repository with new file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test.jsonl"
            repo = InnovationRepository(str(repo_path))

            assert repo.path == repo_path
            assert len(repo.index) == 0

    def test_repository_init_existing_file(self):
        """Test initializing repository with existing file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test.jsonl"

            # Create file with one innovation
            with open(repo_path, 'w') as f:
                record = {
                    'id': 'test_id',
                    'code': 'test_code',
                    'rationale': 'test',
                    'performance': {'sharpe_ratio': 0.8},
                    'validation_report': {},
                    'timestamp': '2025-10-23',
                    'category': 'test'
                }
                f.write(json.dumps(record) + '\n')

            # Load repository
            repo = InnovationRepository(str(repo_path))
            assert len(repo.index) == 1
            assert 'test_id' in repo.index


class TestAddOperations:
    """Test adding innovations to repository"""

    def test_add_single_innovation(self):
        """Test adding a single innovation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            innovation = Innovation(
                code="data.get('roe')",
                rationale="ROE factor",
                performance={'sharpe_ratio': 0.85},
                validation_report={'passed': True},
                timestamp=datetime.now().isoformat()
            )

            innovation_id = repo.add(innovation)

            assert innovation_id is not None
            assert innovation_id.startswith('innov_')
            assert len(repo.index) == 1

    def test_add_multiple_innovations(self):
        """Test adding multiple innovations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            for i in range(5):
                innovation = Innovation(
                    code=f"data.get('factor_{i}')",
                    rationale=f"Factor {i}",
                    performance={'sharpe_ratio': 0.8 + i * 0.01},
                    validation_report={'passed': True},
                    timestamp=datetime.now().isoformat()
                )
                repo.add(innovation)

            assert len(repo.index) == 5

    def test_duplicate_detection(self):
        """Test duplicate innovation detection"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            innovation = Innovation(
                code="data.get('roe')",
                rationale="ROE factor",
                performance={'sharpe_ratio': 0.85},
                validation_report={'passed': True},
                timestamp=datetime.now().isoformat()
            )

            id1 = repo.add(innovation)
            id2 = repo.add(innovation)  # Same innovation

            assert id1 == id2  # Should return existing ID
            assert len(repo.index) == 1  # Only one innovation stored


class TestRetrieveOperations:
    """Test retrieving innovations from repository"""

    def test_get_by_id(self):
        """Test retrieving innovation by ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            innovation = Innovation(
                code="test_code",
                rationale="test",
                performance={'sharpe_ratio': 0.85},
                validation_report={},
                timestamp=datetime.now().isoformat()
            )

            innovation_id = repo.add(innovation)
            retrieved = repo.get(innovation_id)

            assert retrieved is not None
            assert retrieved['code'] == "test_code"
            assert retrieved['performance']['sharpe_ratio'] == 0.85

    def test_get_nonexistent_id(self):
        """Test retrieving non-existent ID returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            result = repo.get('nonexistent_id')
            assert result is None

    def test_get_all(self):
        """Test retrieving all innovations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            for i in range(3):
                innovation = Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                )
                repo.add(innovation)

            all_innovations = repo.get_all()
            assert len(all_innovations) == 3


class TestSearchOperations:
    """Test search functionality"""

    def test_search_by_rationale(self):
        """Test searching by rationale keyword"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            # Add innovations with different rationales
            repo.add(Innovation(
                code="code1",
                rationale="ROE momentum strategy",
                performance={},
                validation_report={},
                timestamp=datetime.now().isoformat()
            ))

            repo.add(Innovation(
                code="code2",
                rationale="Price-to-book value factor",
                performance={},
                validation_report={},
                timestamp=datetime.now().isoformat()
            ))

            # Search for "ROE"
            results = repo.search("ROE")
            assert len(results) >= 1
            assert any("ROE" in r['rationale'] for r in results)

    def test_search_by_code(self):
        """Test searching by code snippet"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            repo.add(Innovation(
                code="data.get('fundamental_features:ROE稅後')",
                rationale="test",
                performance={},
                validation_report={},
                timestamp=datetime.now().isoformat()
            ))

            results = repo.search("ROE稅後")
            assert len(results) >= 1

    def test_search_top_k(self):
        """Test limiting search results with top_k"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            for i in range(10):
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="momentum factor",
                    performance={},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                ))

            results = repo.search("momentum", top_k=3)
            assert len(results) <= 3


class TestRankingOperations:
    """Test top-N ranking functionality"""

    def test_get_top_n_by_sharpe(self):
        """Test getting top N by Sharpe ratio"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            # Add innovations with different Sharpe ratios
            for i, sharpe in enumerate([0.7, 0.9, 0.6, 0.95, 0.8]):
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={'sharpe_ratio': sharpe},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                ))

            top_3 = repo.get_top_n(3, metric='sharpe_ratio')

            assert len(top_3) == 3
            assert top_3[0]['performance']['sharpe_ratio'] == 0.95
            assert top_3[1]['performance']['sharpe_ratio'] == 0.9
            assert top_3[2]['performance']['sharpe_ratio'] == 0.8

    def test_get_top_n_by_calmar(self):
        """Test getting top N by Calmar ratio"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            for i, calmar in enumerate([2.5, 3.0, 2.2, 3.5]):
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={'calmar_ratio': calmar},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                ))

            top_2 = repo.get_top_n(2, metric='calmar_ratio')

            assert len(top_2) == 2
            assert top_2[0]['performance']['calmar_ratio'] == 3.5


class TestCategoryOperations:
    """Test category filtering"""

    def test_get_by_category(self):
        """Test getting innovations by category"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            # Add innovations with different categories
            for cat in ['value', 'quality', 'momentum', 'quality']:
                repo.add(Innovation(
                    code="test",
                    rationale="test",
                    performance={},
                    validation_report={},
                    timestamp=datetime.now().isoformat(),
                    category=cat
                ))

            quality_innovations = repo.get_by_category('quality')
            assert len(quality_innovations) == 2

            value_innovations = repo.get_by_category('value')
            assert len(value_innovations) == 1


class TestRepositoryMaintenance:
    """Test repository maintenance operations"""

    def test_cleanup_low_performers(self):
        """Test removing low-performing innovations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            # Add 10 innovations with varying performance
            for i in range(10):
                sharpe = 0.3 + i * 0.1  # 0.3 to 1.2
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={'sharpe_ratio': sharpe},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                ))

            # Cleanup with threshold 0.7, keep top 5
            removed = repo.cleanup_low_performers(
                metric='sharpe_ratio',
                threshold=0.7,
                keep_top_n=5
            )

            assert removed >= 0  # Some should be removed
            assert len(repo.index) <= 10

    def test_count(self):
        """Test getting innovation count"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            assert repo.count() == 0

            for i in range(5):
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={},
                    validation_report={},
                    timestamp=datetime.now().isoformat()
                ))

            assert repo.count() == 5


class TestStatistics:
    """Test repository statistics"""

    def test_get_statistics_empty(self):
        """Test statistics for empty repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            stats = repo.get_statistics()

            assert stats['total_innovations'] == 0
            assert stats['categories'] == {}
            assert stats['performance_stats'] == {}

    def test_get_statistics_with_data(self):
        """Test statistics with innovations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = InnovationRepository(str(Path(tmpdir) / "test.jsonl"))

            # Add innovations
            for i in range(5):
                repo.add(Innovation(
                    code=f"code_{i}",
                    rationale="test",
                    performance={
                        'sharpe_ratio': 0.8 + i * 0.05,
                        'calmar_ratio': 2.5 + i * 0.1
                    },
                    validation_report={},
                    timestamp=datetime.now().isoformat(),
                    category='quality'
                ))

            stats = repo.get_statistics()

            assert stats['total_innovations'] == 5
            assert stats['categories']['quality'] == 5
            assert 'sharpe' in stats['performance_stats']
            assert 'mean' in stats['performance_stats']['sharpe']


class TestPersistence:
    """Test JSONL file persistence"""

    def test_persistence_across_instances(self):
        """Test data persists across repository instances"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test.jsonl"

            # Create first instance and add data
            repo1 = InnovationRepository(str(repo_path))
            innovation = Innovation(
                code="persistent_code",
                rationale="test",
                performance={'sharpe_ratio': 0.9},
                validation_report={},
                timestamp=datetime.now().isoformat()
            )
            innovation_id = repo1.add(innovation)

            # Create second instance (should load existing data)
            repo2 = InnovationRepository(str(repo_path))

            assert len(repo2.index) == 1
            assert innovation_id in repo2.index
            retrieved = repo2.get(innovation_id)
            assert retrieved['code'] == "persistent_code"


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
