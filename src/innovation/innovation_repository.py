"""
InnovationRepository - JSONL-based knowledge base for validated innovations

Stores validated innovations with performance metrics, rationale, and search capabilities.
Supports top-N ranking, similarity search, and automatic cleanup of low performers.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher


@dataclass
class Innovation:
    """Validated innovation with metadata."""
    code: str
    rationale: str
    performance: Dict[str, float]
    validation_report: Dict[str, Any]
    timestamp: str
    category: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return asdict(self)


class InnovationRepository:
    """JSONL-based repository for validated innovations."""

    def __init__(self, path: str = "artifacts/data/innovations.jsonl"):
        """
        Initialize repository.

        Args:
            path: Path to JSONL storage file
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory index for fast queries
        self.index: Dict[str, Dict] = {}
        self._load_index()

    def _load_index(self):
        """Load existing innovations into in-memory index."""
        if not self.path.exists():
            return

        with open(self.path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                if line.strip():
                    try:
                        record = json.loads(line)

                        # Validate required keys
                        if 'id' not in record or 'code' not in record:
                            print(f"⚠️  Skipping line {line_num}: Missing required keys ('id', 'code')")
                            continue

                        self.index[record['id']] = record
                    except json.JSONDecodeError as e:
                        print(f"⚠️  Skipping line {line_num}: Invalid JSON ({e})")
                        continue
                    except Exception as e:
                        print(f"⚠️  Skipping line {line_num}: Unexpected error ({type(e).__name__})")
                        continue

    def _generate_id(self, innovation: Innovation) -> str:
        """Generate unique ID for innovation based on code hash."""
        code_hash = hashlib.sha256(innovation.code.encode()).hexdigest()[:12]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"innov_{timestamp}_{code_hash}"

    def add(self, innovation: Innovation) -> str:
        """
        Add validated innovation to repository.

        Args:
            innovation: Validated innovation with metrics

        Returns:
            innovation_id: Unique ID for the innovation
        """
        innovation_id = self._generate_id(innovation)

        # Check if already exists (based on code similarity)
        if self._is_duplicate(innovation.code):
            existing_id = self._find_similar_id(innovation.code)
            print(f"⚠️  Innovation already exists: {existing_id}")
            return existing_id

        record = {
            'id': innovation_id,
            'code': innovation.code,
            'rationale': innovation.rationale,
            'performance': innovation.performance,
            'validation_report': innovation.validation_report,
            'timestamp': innovation.timestamp,
            'category': innovation.category
        }

        # Append to JSONL file
        with open(self.path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')

        # Update in-memory index
        self.index[innovation_id] = record

        return innovation_id

    def get(self, innovation_id: str) -> Optional[Dict]:
        """
        Retrieve innovation by ID.

        Args:
            innovation_id: Unique innovation ID

        Returns:
            Innovation record or None if not found
        """
        return self.index.get(innovation_id)

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search repository by semantic similarity to query.

        Args:
            query: Search query (rationale or code snippet)
            top_k: Number of results to return

        Returns:
            List of matching innovations sorted by relevance
        """
        results = []

        for record in self.index.values():
            # Search in both rationale and code
            rationale_similarity = self._calculate_similarity(
                query.lower(),
                record['rationale'].lower()
            )
            code_similarity = self._calculate_similarity(
                query.lower(),
                record['code'].lower()
            )

            # Use maximum similarity
            max_similarity = max(rationale_similarity, code_similarity)

            if max_similarity > 0.3:  # Minimum threshold
                results.append({
                    **record,
                    'similarity': max_similarity
                })

        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)

        return results[:top_k]

    def get_top_n(self, n: int, metric: str = 'sharpe_ratio') -> List[Dict]:
        """
        Get top N innovations by performance metric.

        Args:
            n: Number of top innovations to return
            metric: Performance metric to rank by (sharpe_ratio, calmar_ratio, etc.)

        Returns:
            List of top N innovations sorted by metric
        """
        # Filter innovations that have the metric
        valid_innovations = [
            record for record in self.index.values()
            if metric in record.get('performance', {})
        ]

        # Sort by metric (descending)
        sorted_innovations = sorted(
            valid_innovations,
            key=lambda x: x['performance'][metric],
            reverse=True
        )

        return sorted_innovations[:n]

    def get_by_category(self, category: str) -> List[Dict]:
        """
        Get all innovations in a specific category.

        Args:
            category: Innovation category (value, quality, growth, momentum, mixed)

        Returns:
            List of innovations in the category
        """
        return [
            record for record in self.index.values()
            if record.get('category') == category
        ]

    def get_all(self) -> List[Dict]:
        """Get all innovations in the repository."""
        return list(self.index.values())

    def count(self) -> int:
        """Get total number of innovations."""
        return len(self.index)

    def cleanup_low_performers(self, metric: str = 'sharpe_ratio', threshold: float = 0.5, keep_top_n: int = 100):
        """
        Remove low-performing innovations from repository.

        Args:
            metric: Performance metric to evaluate
            threshold: Minimum threshold to keep
            keep_top_n: Always keep top N innovations regardless of threshold
        """
        # Get top N to preserve
        top_n = self.get_top_n(keep_top_n, metric)
        top_n_ids = {record['id'] for record in top_n}

        # Identify innovations to remove
        to_remove = []
        for innovation_id, record in self.index.items():
            if innovation_id in top_n_ids:
                continue  # Always keep top N

            perf_value = record.get('performance', {}).get(metric, 0)
            if perf_value < threshold:
                to_remove.append(innovation_id)

        # Remove from index
        for innovation_id in to_remove:
            del self.index[innovation_id]

        # Rewrite JSONL file (only kept innovations)
        with open(self.path, 'w', encoding='utf-8') as f:
            for record in self.index.values():
                f.write(json.dumps(record) + '\n')

        return len(to_remove)

    def _is_duplicate(self, code: str, threshold: float = 0.85) -> bool:
        """Check if code is duplicate of existing innovation."""
        for record in self.index.values():
            similarity = self._calculate_similarity(code, record['code'])
            if similarity >= threshold:
                return True
        return False

    def _find_similar_id(self, code: str) -> Optional[str]:
        """Find ID of most similar existing innovation."""
        max_similarity = 0
        similar_id = None

        for record in self.index.values():
            similarity = self._calculate_similarity(code, record['code'])
            if similarity > max_similarity:
                max_similarity = similarity
                similar_id = record['id']

        return similar_id

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher."""
        return SequenceMatcher(None, text1, text2).ratio()

    def get_statistics(self) -> Dict[str, Any]:
        """Get repository statistics."""
        if not self.index:
            return {
                'total_innovations': 0,
                'categories': {},
                'performance_stats': {}
            }

        # Category distribution
        categories = {}
        for record in self.index.values():
            cat = record.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1

        # Performance statistics
        sharpe_values = [
            record['performance'].get('sharpe_ratio', 0)
            for record in self.index.values()
            if 'sharpe_ratio' in record.get('performance', {})
        ]

        calmar_values = [
            record['performance'].get('calmar_ratio', 0)
            for record in self.index.values()
            if 'calmar_ratio' in record.get('performance', {})
        ]

        performance_stats = {}
        if sharpe_values:
            performance_stats['sharpe'] = {
                'mean': sum(sharpe_values) / len(sharpe_values),
                'max': max(sharpe_values),
                'min': min(sharpe_values)
            }

        if calmar_values:
            performance_stats['calmar'] = {
                'mean': sum(calmar_values) / len(calmar_values),
                'max': max(calmar_values),
                'min': min(calmar_values)
            }

        return {
            'total_innovations': len(self.index),
            'categories': categories,
            'performance_stats': performance_stats
        }


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING INNOVATION REPOSITORY")
    print("=" * 70)

    # Create repository
    repo = InnovationRepository("test_innovations.jsonl")

    # Test 1: Add innovations
    print("\nTest 1: Adding innovations...")

    innovation1 = Innovation(
        code="data.get('fundamental_features:ROE稅後') * data.get('fundamental_features:營收成長率')",
        rationale="Combines profitability (ROE) with growth momentum to identify high-quality growth stocks",
        performance={'sharpe_ratio': 0.85, 'calmar_ratio': 2.8, 'max_drawdown': 0.18},
        validation_report={'layers_passed': [1, 2, 3, 4, 5, 6, 7], 'novelty_score': 0.87},
        timestamp=datetime.now().isoformat(),
        category='quality'
    )

    innovation2 = Innovation(
        code="data.get('price:收盤價').rolling(20).mean() / data.get('price:收盤價').rolling(50).mean()",
        rationale="Moving average crossover strategy for momentum detection",
        performance={'sharpe_ratio': 0.72, 'calmar_ratio': 2.1, 'max_drawdown': 0.22},
        validation_report={'layers_passed': [1, 2, 3, 4, 5, 6, 7], 'novelty_score': 0.75},
        timestamp=datetime.now().isoformat(),
        category='momentum'
    )

    innovation3 = Innovation(
        code="data.get('fundamental_features:本益比') / data.get('fundamental_features:淨值比')",
        rationale="PE/PB ratio identifies undervalued stocks with strong fundamentals",
        performance={'sharpe_ratio': 0.91, 'calmar_ratio': 3.2, 'max_drawdown': 0.15},
        validation_report={'layers_passed': [1, 2, 3, 4, 5, 6, 7], 'novelty_score': 0.82},
        timestamp=datetime.now().isoformat(),
        category='value'
    )

    id1 = repo.add(innovation1)
    id2 = repo.add(innovation2)
    id3 = repo.add(innovation3)

    print(f"✅ Added 3 innovations: {id1}, {id2}, {id3}")

    # Test 2: Retrieve by ID
    print("\nTest 2: Retrieving by ID...")
    retrieved = repo.get(id1)
    print(f"✅ Retrieved innovation {id1[:20]}...")
    print(f"   Sharpe: {retrieved['performance']['sharpe_ratio']:.3f}")

    # Test 3: Top N ranking
    print("\nTest 3: Top N ranking by Sharpe ratio...")
    top_2 = repo.get_top_n(2, metric='sharpe_ratio')
    print(f"✅ Top 2 innovations:")
    for i, innov in enumerate(top_2, 1):
        print(f"   {i}. Sharpe {innov['performance']['sharpe_ratio']:.3f} - {innov['rationale'][:50]}...")

    # Test 4: Search
    print("\nTest 4: Searching for 'ROE'...")
    results = repo.search("ROE", top_k=5)
    print(f"✅ Found {len(results)} results")
    for result in results:
        print(f"   Similarity: {result['similarity']:.2f} - {result['rationale'][:50]}...")

    # Test 5: Category filter
    print("\nTest 5: Get innovations by category...")
    quality_innov = repo.get_by_category('quality')
    print(f"✅ Found {len(quality_innov)} 'quality' innovations")

    # Test 6: Statistics
    print("\nTest 6: Repository statistics...")
    stats = repo.get_statistics()
    print(f"✅ Total innovations: {stats['total_innovations']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   Performance stats: {stats['performance_stats']}")

    # Test 7: Duplicate detection
    print("\nTest 7: Testing duplicate detection...")
    duplicate_id = repo.add(innovation1)  # Try to add same innovation
    print(f"✅ Duplicate detection: {duplicate_id == id1}")

    print("\n" + "=" * 70)
    print("REPOSITORY TEST COMPLETE")
    print("=" * 70)
