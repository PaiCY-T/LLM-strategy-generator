"""
Innovation Lineage Tracker - Task 3.3

Tracks innovation ancestry to identify "golden lineages" and
visualize evolution tree.

Responsibilities:
- Build innovation ancestry graph
- Identify breakthrough lineages
- Trace innovation genealogy
- Visualize evolution tree
"""

from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, deque
import json
from datetime import datetime


class LineageNode:
    """Represents a single innovation in the lineage tree."""

    def __init__(
        self,
        innovation_id: str,
        code: str,
        performance: float,
        parent_id: Optional[str] = None,
        generation: int = 0,
        timestamp: Optional[str] = None
    ):
        self.innovation_id = innovation_id
        self.code = code
        self.performance = performance
        self.parent_id = parent_id
        self.generation = generation
        self.timestamp = timestamp or datetime.now().isoformat()
        self.children: List[str] = []


class LineageTracker:
    """
    Track innovation ancestry and identify golden lineages.

    Maintains a directed acyclic graph (DAG) of innovations,
    tracking parent-child relationships and identifying
    high-performing lineages.
    """

    def __init__(self):
        """Initialize lineage tracker."""
        self.nodes: Dict[str, LineageNode] = {}
        self.roots: Set[str] = set()  # Innovations with no parents
        self.generations: Dict[int, List[str]] = defaultdict(list)

    def add_innovation(
        self,
        innovation_id: str,
        code: str,
        performance: float,
        parent_id: Optional[str] = None,
        generation: int = 0
    ):
        """
        Add innovation to lineage tree.

        Args:
            innovation_id: Unique innovation ID
            code: Innovation code
            performance: Performance metric (e.g., Sharpe ratio)
            parent_id: ID of parent innovation (None for roots)
            generation: Generation number
        """
        node = LineageNode(
            innovation_id=innovation_id,
            code=code,
            performance=performance,
            parent_id=parent_id,
            generation=generation
        )

        self.nodes[innovation_id] = node
        self.generations[generation].append(innovation_id)

        if parent_id is None:
            self.roots.add(innovation_id)
        else:
            # Add to parent's children
            if parent_id in self.nodes:
                self.nodes[parent_id].children.append(innovation_id)

    def get_ancestors(
        self,
        innovation_id: str
    ) -> List[Tuple[str, LineageNode]]:
        """
        Get all ancestors of an innovation (parents, grandparents, ...).

        Args:
            innovation_id: Innovation ID

        Returns:
            List of (id, node) tuples in order from parent to root
        """
        ancestors = []
        current_id = innovation_id

        while current_id in self.nodes:
            node = self.nodes[current_id]
            if node.parent_id is None:
                break

            if node.parent_id not in self.nodes:
                break

            parent_node = self.nodes[node.parent_id]
            ancestors.append((node.parent_id, parent_node))
            current_id = node.parent_id

        return ancestors

    def get_descendants(
        self,
        innovation_id: str
    ) -> List[Tuple[str, LineageNode]]:
        """
        Get all descendants of an innovation (BFS traversal).

        Args:
            innovation_id: Innovation ID

        Returns:
            List of (id, node) tuples
        """
        if innovation_id not in self.nodes:
            return []

        descendants = []
        queue = deque([innovation_id])
        visited = set()

        while queue:
            current_id = queue.popleft()
            if current_id in visited:
                continue

            visited.add(current_id)
            node = self.nodes[current_id]

            # Add children to descendants
            for child_id in node.children:
                if child_id in self.nodes:
                    descendants.append((child_id, self.nodes[child_id]))
                    queue.append(child_id)

        return descendants

    def identify_golden_lineages(
        self,
        min_performance: float = 0.70,
        min_lineage_length: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Identify high-performing lineages ("golden lineages").

        A golden lineage is a path from root to leaf where all nodes
        have performance above threshold.

        Args:
            min_performance: Minimum performance for golden status
            min_lineage_length: Minimum lineage length to consider

        Returns:
            List of golden lineage dictionaries
        """
        golden_lineages = []

        # For each root, trace paths to leaves
        for root_id in self.roots:
            paths = self._find_all_paths_to_leaves(root_id)

            for path in paths:
                if len(path) < min_lineage_length:
                    continue

                # Check if all nodes meet performance threshold
                is_golden = all(
                    self.nodes[node_id].performance >= min_performance
                    for node_id in path
                )

                if is_golden:
                    avg_performance = sum(
                        self.nodes[node_id].performance
                        for node_id in path
                    ) / len(path)

                    golden_lineages.append({
                        'path': path,
                        'length': len(path),
                        'avg_performance': avg_performance,
                        'root_id': root_id,
                        'leaf_id': path[-1]
                    })

        # Sort by average performance
        return sorted(
            golden_lineages,
            key=lambda x: x['avg_performance'],
            reverse=True
        )

    def _find_all_paths_to_leaves(
        self,
        start_id: str
    ) -> List[List[str]]:
        """
        Find all paths from start node to leaf nodes.

        Args:
            start_id: Starting node ID

        Returns:
            List of paths (each path is a list of node IDs)
        """
        if start_id not in self.nodes:
            return []

        node = self.nodes[start_id]

        # Base case: leaf node (no children)
        if not node.children:
            return [[start_id]]

        # Recursive case: extend paths through children
        all_paths = []
        for child_id in node.children:
            child_paths = self._find_all_paths_to_leaves(child_id)
            for path in child_paths:
                all_paths.append([start_id] + path)

        return all_paths

    def get_lineage_depth(self, innovation_id: str) -> int:
        """
        Get depth of innovation in tree (distance from root).

        Args:
            innovation_id: Innovation ID

        Returns:
            Depth (0 for roots)
        """
        if innovation_id not in self.nodes:
            return -1

        ancestors = self.get_ancestors(innovation_id)
        return len(ancestors)

    def get_lineage_stats(self) -> Dict[str, Any]:
        """
        Get overall lineage statistics.

        Returns:
            Statistics dictionary
        """
        if not self.nodes:
            return {
                'total_innovations': 0,
                'total_roots': 0,
                'max_depth': 0,
                'avg_children': 0.0
            }

        # Calculate max depth
        max_depth = 0
        for node_id in self.nodes:
            depth = self.get_lineage_depth(node_id)
            max_depth = max(max_depth, depth)

        # Calculate average children per node
        total_children = sum(
            len(node.children)
            for node in self.nodes.values()
        )
        avg_children = total_children / len(self.nodes)

        return {
            'total_innovations': len(self.nodes),
            'total_roots': len(self.roots),
            'total_generations': len(self.generations),
            'max_depth': max_depth,
            'avg_children': avg_children,
            'nodes_per_generation': {
                gen: len(nodes)
                for gen, nodes in self.generations.items()
            }
        }

    def remove_innovation(self, innovation_id: str):
        """
        Remove an innovation node from the lineage tree.

        Used for memory management when innovations are cleaned up from repository.

        Args:
            innovation_id: ID of the innovation to remove
        """
        if innovation_id not in self.nodes:
            return

        node_to_remove = self.nodes[innovation_id]

        # Remove from parent's children list
        if node_to_remove.parent_id and node_to_remove.parent_id in self.nodes:
            parent_node = self.nodes[node_to_remove.parent_id]
            parent_node.children = [
                child_id for child_id in parent_node.children
                if child_id != innovation_id
            ]

        # Remove from roots if it was a root
        if innovation_id in self.roots:
            self.roots.remove(innovation_id)

        # Remove from generations dictionary
        if node_to_remove.generation in self.generations:
            self.generations[node_to_remove.generation] = [
                fid for fid in self.generations[node_to_remove.generation]
                if fid != innovation_id
            ]
            # Clean up empty generation lists
            if not self.generations[node_to_remove.generation]:
                del self.generations[node_to_remove.generation]

        # Finally, remove the node itself
        del self.nodes[innovation_id]

    def export_tree(self, filepath: str):
        """Export lineage tree to JSON."""
        export_data = {
            'nodes': {
                node_id: {
                    'code': node.code[:100],  # Truncate for readability
                    'performance': node.performance,
                    'parent_id': node.parent_id,
                    'generation': node.generation,
                    'children': node.children,
                    'timestamp': node.timestamp
                }
                for node_id, node in self.nodes.items()
            },
            'roots': list(self.roots),
            'stats': self.get_lineage_stats()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("TESTING LINEAGE TRACKER")
    print("=" * 70)

    tracker = LineageTracker()

    # Build example lineage tree
    print("\nBuilding Lineage Tree...")
    print("-" * 70)

    # Generation 0: Roots
    tracker.add_innovation("root1", "factor = data.get('ROE')", 0.65, None, 0)
    tracker.add_innovation("root2", "factor = data.get('P/E')", 0.70, None, 0)

    # Generation 1: Children of roots
    tracker.add_innovation("child1_1", "factor = data.get('ROE') * 2", 0.75, "root1", 1)
    tracker.add_innovation("child1_2", "factor = data.get('ROE') / data.get('P/B')", 0.85, "root1", 1)
    tracker.add_innovation("child2_1", "factor = data.get('P/E') + data.get('ROE')", 0.72, "root2", 1)

    # Generation 2: Grandchildren
    tracker.add_innovation("grand1", "factor = data.get('ROE') / data.get('P/B') * 1.5", 0.90, "child1_2", 2)

    print(f"✅ Built lineage tree with {len(tracker.nodes)} nodes")

    # Test 2: Get ancestors
    print("\nTest 2: Get Ancestors")
    print("-" * 70)

    ancestors = tracker.get_ancestors("grand1")
    print(f"✅ Ancestors of 'grand1': {len(ancestors)}")
    for ancestor_id, node in ancestors:
        print(f"   - {ancestor_id}: Sharpe {node.performance:.3f}")

    # Test 3: Identify golden lineages
    print("\nTest 3: Golden Lineages")
    print("-" * 70)

    golden = tracker.identify_golden_lineages(min_performance=0.70, min_lineage_length=2)
    print(f"✅ Found {len(golden)} golden lineages")
    for i, lineage in enumerate(golden[:3], 1):
        print(f"   {i}. Length: {lineage['length']}, Avg Sharpe: {lineage['avg_performance']:.3f}")
        print(f"      Path: {' → '.join(lineage['path'])}")

    # Test 4: Lineage statistics
    print("\nTest 4: Lineage Statistics")
    print("-" * 70)

    stats = tracker.get_lineage_stats()
    print(f"✅ Lineage stats:")
    print(f"   Total innovations: {stats['total_innovations']}")
    print(f"   Total roots: {stats['total_roots']}")
    print(f"   Max depth: {stats['max_depth']}")
    print(f"   Avg children: {stats['avg_children']:.2f}")

    print("\n" + "=" * 70)
    print("LINEAGE TRACKER TEST COMPLETE")
    print("=" * 70)
