# Factor Graph System - Documentation Index

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23

---

## Getting Started

1. **[User Guide](./FACTOR_GRAPH_USER_GUIDE.md)** - Complete introduction and tutorial
   - Core concepts (Factor, Strategy, DAG)
   - Quick start examples
   - Best practices and patterns

2. **[Architecture Overview](./FACTOR_GRAPH_ARCHITECTURE.md)** - System design and data flow
   - System architecture diagram
   - Core components
   - Design principles

---

## Reference Documentation

3. **[API Reference](./FACTOR_GRAPH_API_REFERENCE.md)** - Complete API documentation
   - Factor API
   - Strategy API
   - Mutation Operators API
   - Registry API
   - Examples and type definitions

4. **[YAML Configuration Guide](./YAML_CONFIGURATION_GUIDE.md)** - Tier 1 configuration
   - YAML schema and syntax
   - Configuration examples
   - Validation and error handling

5. **[Mutation Operator Reference](./MUTATION_OPERATOR_REFERENCE.md)** - Three-tier mutations
   - Tier 1: YAML (Safe, ~80% success)
   - Tier 2: Factor Ops (Medium, ~60% success)
   - Tier 3: AST (Advanced, ~50% success)

---

## Operational Guides

6. **[Performance Tuning Guide](./PERFORMANCE_TUNING_GUIDE.md)** - Optimization strategies
   - Performance targets
   - Optimization techniques
   - Profiling tools

7. **[Troubleshooting Guide](./TROUBLESHOOTING_GUIDE.md)** - Common errors and solutions
   - Error diagnosis
   - Debug mode
   - Getting help

---

## Quick Links

- **Phase Completion Status**: [structural-mutation-phase2/STATUS.md](../.spec-workflow/specs/structural-mutation-phase2/STATUS.md)
- **Implementation Tasks**: [structural-mutation-phase2/tasks.md](../.spec-workflow/specs/structural-mutation-phase2/tasks.md)
- **Requirements**: [structural-mutation-phase2/requirements.md](../.spec-workflow/specs/structural-mutation-phase2/requirements.md)
- **Design Document**: [structural-mutation-phase2/design.md](../.spec-workflow/specs/structural-mutation-phase2/design.md)

---

## Test Examples

- **Factor Tests**: `tests/factor_graph/test_factor.py`
- **Strategy Tests**: `tests/factor_graph/test_strategy.py`
- **Mutation Tests**: `tests/factor_graph/test_mutations_*.py`
- **Integration Tests**: `tests/integration/test_three_tier_*.py`

---

## Version History

- **2.0+**: Production release (2025-10-23)
  - Complete three-tier mutation system
  - Comprehensive documentation
  - Production validation complete

---

**Spec**: structural-mutation-phase2
**Status**: ✅ Production Ready
