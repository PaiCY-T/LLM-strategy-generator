"""
Individual class for population-based evolutionary learning.

Represents a single strategy (parameter combination) in the population.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import hashlib
import json


@dataclass
class Individual:
    """
    Single parameter combination in population with fitness tracking.

    Attributes:
        parameters: Dictionary of strategy parameters
        template_type: Strategy template name (default: 'Momentum')
        fitness: Fitness score (None if not evaluated)
        metrics: Full backtest metrics dictionary
        generation: Generation number when created
        parent_ids: List of parent individual IDs (for lineage tracking)
        id: Unique hash-based identifier (auto-generated)
    """
    parameters: Dict[str, Any]
    template_type: str = 'Momentum'
    fitness: Optional[float] = None
    metrics: Optional[Dict] = None
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    id: str = field(default="", init=False)

    def __post_init__(self):
        """
        Generate unique ID and validate template_type after initialization.

        Raises:
            ValueError: If template_type is not a valid template name
        """
        # Validate template_type
        from src.utils.template_registry import TemplateRegistry
        registry = TemplateRegistry.get_instance()

        if not registry.validate_template_type(self.template_type):
            available = registry.get_available_templates()
            raise ValueError(
                f"Invalid template_type '{self.template_type}'. "
                f"Available templates: {available}"
            )

        # Generate unique ID
        if not self.id:
            self.id = self._hash_parameters()

    def _hash_parameters(self) -> str:
        """
        Generate unique 8-character hash from template_type and parameters.

        Includes template_type in hash to ensure individuals with same parameters
        but different templates have different IDs.

        Returns:
            str: 8-character hexadecimal hash
        """
        hash_data = {
            'template_type': self.template_type,
            'parameters': self.parameters
        }
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.md5(hash_str.encode()).hexdigest()[:8]

    def is_evaluated(self) -> bool:
        """
        Check if individual has been evaluated.

        Returns:
            bool: True if fitness is not None
        """
        return self.fitness is not None

    def is_valid(self) -> bool:
        """
        Validate individual has required fields.

        Returns:
            bool: True if parameters exist and ID is set
        """
        return (
            self.parameters is not None and
            len(self.parameters) > 0 and
            self.id != ""
        )

    def validate_parameters(self) -> bool:
        """
        Validate parameters against template-specific parameter grid.

        Uses the template's validate_params() method to check parameters
        against the PARAM_GRID for this individual's template_type.

        Returns:
            bool: True if all parameters are valid for the template

        Example:
            >>> ind = Individual(parameters={'n_stocks': 10}, template_type='Momentum')
            >>> ind.validate_parameters()  # Checks against MomentumTemplate.PARAM_GRID
            True
        """
        from src.utils.template_registry import TemplateRegistry
        registry = TemplateRegistry.get_instance()

        # Get template instance for this individual's template_type
        template = registry.get_template(self.template_type)

        # Use template's validate_params() method (returns tuple: is_valid, errors)
        is_valid, _ = template.validate_params(self.parameters)
        return is_valid

    def get_fitness_or_default(self, default: float = 0.0) -> float:
        """
        Get fitness value with fallback.

        Args:
            default: Default value if fitness is None

        Returns:
            float: Fitness value or default
        """
        return self.fitness if self.fitness is not None else default

    def clone(self) -> 'Individual':
        """
        Create a deep copy of this individual.

        Returns:
            Individual: New individual with copied data

        Note:
            Creates a new Individual with the same parameters, template_type,
            fitness, metrics, generation, and parent_ids. The ID will be
            regenerated automatically based on the parameters and template.
        """
        import copy
        return Individual(
            parameters=copy.deepcopy(self.parameters),
            template_type=self.template_type,
            fitness=self.fitness,
            metrics=copy.deepcopy(self.metrics) if self.metrics else None,
            generation=self.generation,
            parent_ids=self.parent_ids.copy()
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert individual to dictionary for serialization.

        Returns:
            Dict: Dictionary representation including template_type
        """
        return {
            'id': self.id,
            'template_type': self.template_type,
            'parameters': self.parameters,
            'fitness': self.fitness,
            'metrics': self.metrics,
            'generation': self.generation,
            'parent_ids': self.parent_ids
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Individual':
        """
        Create individual from dictionary.

        Args:
            data: Dictionary with individual data

        Returns:
            Individual: New individual instance

        Note:
            Defaults to template_type='Momentum' for backward compatibility
            with serialized individuals from before template evolution.
        """
        return cls(
            parameters=data['parameters'],
            template_type=data.get('template_type', 'Momentum'),
            fitness=data.get('fitness'),
            metrics=data.get('metrics'),
            generation=data.get('generation', 0),
            parent_ids=data.get('parent_ids', [])
        )

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Human-readable representation including template_type
        """
        fitness_str = f"{self.fitness:.4f}" if self.fitness is not None else "None"
        return (
            f"Individual(id={self.id}, template={self.template_type}, "
            f"gen={self.generation}, fitness={fitness_str})"
        )

    def __eq__(self, other: object) -> bool:
        """
        Equality comparison based on ID.

        Args:
            other: Another Individual or object

        Returns:
            bool: True if IDs match
        """
        if not isinstance(other, Individual):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        Hash method for set/dict usage.

        Returns:
            int: Hash of ID
        """
        return hash(self.id)
