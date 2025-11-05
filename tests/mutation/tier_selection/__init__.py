"""
Test suite for Tier Selection System.

Tests adaptive mutation tier routing across three tiers:
- Tier 1 (Safe): YAML configuration mutations
- Tier 2 (Domain): Factor-level mutations
- Tier 3 (Advanced): AST code mutations

Test modules:
- test_risk_assessor: Risk assessment logic
- test_tier_router: Tier routing and selection
- test_adaptive_learner: Adaptive learning and threshold adjustment
- test_tier_selection_integration: End-to-end integration tests

Architecture: Phase 2.0+ Factor Graph System
Task: D.4 - Adaptive Mutation Tier Selection
"""
