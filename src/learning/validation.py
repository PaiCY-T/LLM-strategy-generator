"""Runtime Protocol Validation - TDD GREEN Phase.

This module provides runtime validation for Protocol compliance with
diagnostic error messages.

**TDD Phase: GREEN (Minimal Implementation)**

Functions:
    - validate_protocol_compliance(): Runtime validation with isinstance()
    - _get_missing_attrs(): Helper for diagnostic messages (REFACTOR phase)

Design Principles:
    1. Use isinstance() with @runtime_checkable Protocols
    2. Raise TypeError for non-compliant objects
    3. Provide helpful diagnostic messages

Usage Example:
    >>> from src.learning.validation import validate_protocol_compliance
    >>> from src.learning.interfaces import IChampionTracker
    >>> from src.learning.champion_tracker import ChampionTracker
    >>>
    >>> tracker = ChampionTracker(...)
    >>> validate_protocol_compliance(tracker, IChampionTracker, context="LearningLoop")
    >>> # No exception - validation passed

Design Reference:
    See .spec-workflow/specs/api-mismatch-prevention-system/DESIGN_IMPROVEMENTS.md
    Section 1.3: Runtime Validation Function

Next Steps (REFACTOR Phase):
    - Add _get_missing_attrs() helper for detailed error messages
    - Enhance error messages with missing attribute lists
"""

from typing import Any, Type, List


def _get_missing_attrs(obj: Any, protocol: Type[Any]) -> List[str]:
    """Get list of missing attributes preventing Protocol compliance.

    **TDD Phase: REFACTOR - Helper Function**

    Introspects the Protocol to find required attributes and checks
    which ones are missing from the object.

    Args:
        obj: Object being validated
        protocol: Protocol class to check against

    Returns:
        List of missing attribute names (methods/properties)
    """
    missing = []

    # Get all attributes defined in Protocol (annotations and methods)
    protocol_attrs = set(dir(protocol))

    # Filter to only user-defined attributes (exclude dunder methods)
    protocol_attrs = {
        attr for attr in protocol_attrs
        if not attr.startswith('_') and attr != 'mro'
    }

    # Check which attributes are missing from object
    for attr in protocol_attrs:
        if not hasattr(obj, attr):
            missing.append(attr)

    return missing


def validate_protocol_compliance(
    obj: Any,
    protocol: Type[Any],
    context: str = "unknown"
) -> None:
    """Validate that object implements Protocol interface at runtime.

    **TDD Phase: REFACTOR - Enhanced with Diagnostic Messages**

    Uses isinstance() with @runtime_checkable Protocol to verify that
    an object implements the required interface at runtime.

    Behavioral Contract:
        - Raises TypeError if object doesn't implement Protocol
        - No-op (silent success) if object implements Protocol
        - Handles None gracefully with TypeError
        - Provides diagnostic messages listing missing attributes

    Pre-conditions:
        - protocol MUST be a @runtime_checkable Protocol
        - obj can be any type (including None)

    Post-conditions:
        - If no exception raised, obj implements protocol
        - If TypeError raised, obj missing required methods/properties
        - Error message includes list of missing attributes

    Args:
        obj: Object to validate (any type)
        protocol: Protocol class to validate against
        context: Description of where validation occurs (for error messages)

    Raises:
        TypeError: If obj doesn't implement protocol or is None
            Error message includes missing attribute details

    Example:
        >>> from src.learning.interfaces import IChampionTracker
        >>> from src.learning.champion_tracker import ChampionTracker
        >>>
        >>> tracker = ChampionTracker(...)
        >>> validate_protocol_compliance(
        ...     tracker,
        ...     IChampionTracker,
        ...     context="LearningLoop.__init__"
        ... )
        >>> # No exception raised - validation passed
        >>>
        >>> # Invalid object example:
        >>> class FakeTracker:
        ...     champion = None
        >>> validate_protocol_compliance(
        ...     FakeTracker(),
        ...     IChampionTracker,
        ...     context="test"
        ... )
        >>> # Raises: TypeError: test: Object FakeTracker does not implement
        >>> #         IChampionTracker Protocol
        >>> #         Missing attributes: ['update_champion']
    """
    # Handle None explicitly
    if obj is None:
        raise TypeError(
            f"{context}: Object is None, cannot implement {protocol.__name__} Protocol"
        )

    # Use isinstance() with @runtime_checkable Protocol
    if not isinstance(obj, protocol):
        # Enhanced error message with diagnostic details
        missing_attrs = _get_missing_attrs(obj, protocol)

        error_msg = (
            f"{context}: Object {type(obj).__name__} does not implement "
            f"{protocol.__name__} Protocol"
        )

        if missing_attrs:
            error_msg += f"\nMissing attributes: {missing_attrs}"

        raise TypeError(error_msg)

    # Validation passed - no exception raised
