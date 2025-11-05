# Factor Graph System - Architecture Overview

**Version**: 2.0+
**Last Updated**: 2025-10-23

---

## System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     Factor Graph System (Phase 2.0+)                │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │    Factor    │   │   Strategy   │   │   Mutation   │           │
│  │   Library    │──▶│  Composition │──▶│   Engine     │           │
│  └──────────────┘   └──────────────┘   └──────────────┘           │
│         │                    │                   │                  │
│         │                    ▼                   ▼                  │
│         │           ┌──────────────┐   ┌──────────────┐           │
│         │           │  DAG         │   │  Three-Tier  │           │
│         │           │  Validator   │   │  Mutations   │           │
│         │           └──────────────┘   └──────────────┘           │
│         │                                        │                  │
│         │                                        ▼                  │
│         │                                ┌──────────────┐           │
│         │                                │  Tier 1:     │           │
│         │                                │  YAML Config │           │
│         │                                ├──────────────┤           │
│         └───────────────────────────────▶│  Tier 2:     │           │
│                                          │  Factor Ops  │           │
│                                          ├──────────────┤           │
│                                          │  Tier 3:     │           │
│                                          │  AST Mutations│          │
│                                          └──────────────┘           │
│                                                   │                  │
│                                                   ▼                  │
│                                          ┌──────────────┐           │
│                                          │  Evaluation  │           │
│                                          │   Engine     │           │
│                                          └──────────────┘           │
└────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Factor (Atomic Component)
- **Purpose**: Atomic strategy building block
- **Interface**: inputs → logic → outputs
- **Location**: `src/factor_graph/factor.py`

### 2. Strategy (DAG Composition)
- **Purpose**: Compose factors into executable strategies
- **Structure**: NetworkX DiGraph
- **Location**: `src/factor_graph/strategy.py`

### 3. Factor Library
- **Purpose**: Reusable factor collection
- **Categories**: MOMENTUM, VALUE, QUALITY, RISK, EXIT, ENTRY, SIGNAL
- **Location**: `src/factor_library/`

### 4. Three-Tier Mutation System
- **Tier 1**: YAML Configuration (Safe, ~80% success)
- **Tier 2**: Factor Operations (Medium, ~60% success)
- **Tier 3**: AST Mutations (Advanced, ~50% success)
- **Location**: `src/mutation/`

### 5. Evaluation Engine
- **Purpose**: Multi-objective fitness evaluation
- **Metrics**: Sharpe, Calmar, drawdown, volatility, win rate, etc.
- **Location**: `src/evaluation/`

---

## Data Flow

```
1. Strategy Definition (YAML or Code)
         ↓
2. Factor Registry → Create Factors
         ↓
3. Strategy Composition → Build DAG
         ↓
4. DAG Validation → Check integrity
         ↓
5. Pipeline Compilation → Executable code
         ↓
6. Backtest Execution → Run on data
         ↓
7. Multi-Objective Evaluation → Calculate metrics
         ↓
8. Mutation → Evolve strategy
         ↓
     (Loop back to step 3)
```

---

## Key Technologies

- **NetworkX**: DAG manipulation and topological sorting
- **Python AST**: Code parsing and generation  
- **finlab**: Backtesting and evaluation
- **JSON Schema**: YAML validation
- **NSGA-II**: Multi-objective optimization
- **Pandas**: Data manipulation

---

## Design Principles

1. **Validation-First**: Prevent invalid strategies before backtest
2. **Compositional**: Build complex strategies from simple factors
3. **Immutable**: Original strategies never modified (copy-on-mutate)
4. **Progressive Risk**: Three tiers from safe to advanced
5. **Expert-Validated**: Architecture reviewed by domain experts

---

**Version**: 2.0+ (Production Ready)
**Last Updated**: 2025-10-23
