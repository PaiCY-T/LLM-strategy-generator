# Requirements Document - Template Evolution System

## Introduction

The Template Evolution System enables the genetic algorithm to evolve not just strategy parameters, but also the choice of strategy template itself. Currently, Phase 1 genetic algorithm is constrained to a single template (MomentumTemplate with 0.8-1.5 Sharpe ceiling), while Phase 0 achieved 2.48 Sharpe using a custom multi-factor hybrid strategy. This feature will enable the system to discover the optimal template type and parameters for different market regimes, addressing the 67% performance gap through architectural enhancement rather than parameter tuning.

This system implements the expert-validated Solution D from consensus analysis, providing long-term strategic value by automating template discovery and enabling regime-adaptive performance.

## Alignment with Product Vision

This feature directly supports the core product goals:
- **Autonomous Strategy Discovery**: Extends evolution from parameters to template selection, enabling true autonomous discovery
- **Performance Maximization**: Removes architectural constraints limiting performance to single-template ceilings
- **Market Adaptability**: Enables system to adapt template selection based on market regime changes
- **Reduces Manual Intervention**: Eliminates need to manually switch templates for different market conditions

## Requirements

### Requirement 1: Template Gene in Individual Class

**User Story:** As a genetic algorithm, I want individuals to carry a template_type gene, so that the population can explore different strategy architectures simultaneously.

#### Acceptance Criteria

1. WHEN an Individual is created THEN the system SHALL include a `template_type` string attribute
2. WHEN template_type is set THEN the system SHALL validate it against available templates ['Momentum', 'Turtle', 'Factor', 'Mastiff']
3. WHEN parameters are validated THEN the system SHALL use the template-specific PARAM_GRID for validation
4. WHEN an Individual ID is generated THEN the system SHALL include template_type in the hash to ensure uniqueness across templates
5. IF template_type is not provided THEN the system SHALL default to 'Momentum' for backward compatibility

### Requirement 2: Template-Aware Genetic Operators

**User Story:** As a genetic algorithm operator, I want crossover to work within same template types, so that offspring maintain valid parameter combinations.

#### Acceptance Criteria

1. WHEN crossover is performed THEN the system SHALL only cross individuals with identical template_type
2. IF parents have different template_types THEN the system SHALL skip crossover and return two mutated copies
3. WHEN mutation is performed THEN the system SHALL have 5% probability of template_type mutation
4. WHEN template_type mutates THEN the system SHALL re-initialize parameters from new template's PARAM_GRID default values
5. WHEN parameters are mutated THEN the system SHALL use the Individual's current template_type PARAM_GRID

### Requirement 3: Population Diversity Across Templates

**User Story:** As a population manager, I want initial population distributed across templates, so that evolution explores the full template space.

#### Acceptance Criteria

1. WHEN initial population is created THEN the system SHALL distribute individuals across all 4 templates
2. WHEN distribution is configured THEN the system SHALL support equal distribution or weighted distribution
3. WHEN population size is N THEN the system SHALL create N/4 individuals per template (equal distribution)
4. IF weighted distribution is used THEN the system SHALL support custom proportions per template
5. WHEN diversity is measured THEN the system SHALL track template distribution in evolution metrics

### Requirement 4: Template-Specific Fitness Evaluation

**User Story:** As a fitness evaluator, I want to route strategy generation to the correct template, so that each individual is evaluated with its proper strategy architecture.

#### Acceptance Criteria

1. WHEN fitness is evaluated THEN the system SHALL retrieve template instance based on individual's template_type
2. WHEN template is retrieved THEN the system SHALL use cached template instances to avoid re-instantiation
3. WHEN strategy is generated THEN the system SHALL call template.generate_strategy() with individual's parameters
4. WHEN metrics are extracted THEN the system SHALL use template-specific expected_performance threshold (Sharpe ratio ≥ lower bound of sharpe_range) for success validation
5. IF template instantiation fails THEN the system SHALL log error and assign fitness of 0.0

### Requirement 5: Template Performance Tracking

**User Story:** As a researcher, I want to track which templates perform best, so that I can understand template effectiveness across market regimes.

#### Acceptance Criteria

1. WHEN evolution completes a generation THEN the system SHALL record best fitness per template type
2. WHEN champion is updated THEN the system SHALL record the template_type of the new champion
3. WHEN diversity metrics are calculated THEN the system SHALL include template distribution statistics
4. WHEN evolution completes THEN the system SHALL report final champion template and performance by template
5. WHEN analytics are generated THEN the system SHALL include template_type in all strategy records

### Requirement 6: Backward Compatibility

**User Story:** As an existing user, I want single-template mode to continue working, so that my current workflows are not disrupted.

#### Acceptance Criteria

1. WHEN template_type is not specified THEN the system SHALL default to 'Momentum' template
2. WHEN FitnessEvaluator is initialized with a template instance THEN the system SHALL use that template exclusively
3. IF population is created without template distribution config THEN the system SHALL create all individuals with default template
4. WHEN legacy test harnesses run THEN the system SHALL produce results within 0.01% variance of pre-evolution baseline performance
5. WHEN migration is needed THEN the system SHALL provide conversion utility for existing strategies

## Non-Functional Requirements

### Performance

- Template lookup and instantiation: <50ms per individual evaluation
- Template-aware crossover decision: <10ms per operation
- Population initialization with 4 templates: <2 seconds for 100 individuals
- No more than 10% performance overhead vs single-template approach
- Template instance caching: Single instance per template class per process with lazy initialization
- Memory overhead: <10MB for all 4 template instances

### Reliability

- Template validation SHALL catch invalid template_type values before fitness evaluation
- Template mutation SHALL never create invalid parameter combinations
- Crossover between different templates SHALL never produce corrupted individuals
- System SHALL gracefully handle missing template classes with clear error messages

### Maintainability

- Adding new templates SHALL require only: (1) implement BaseTemplate, (2) add to template registry
- Template registry SHALL be centralized in a single configuration module
- All template-specific logic SHALL be encapsulated in template classes
- Template evolution code SHALL be isolated from core genetic algorithm logic

### Usability

- Template distribution in population SHALL be configurable via simple dict: {'Momentum': 0.25, 'Turtle': 0.25, 'Factor': 0.25, 'Mastiff': 0.25}
- Evolution monitor SHALL display template breakdown in real-time progress
- Final reports SHALL clearly indicate best template and comparative performance
- Error messages SHALL specify which template caused failures for debugging

## Success Criteria

The Template Evolution System will be considered successful when:

1.  Individual class supports template_type gene with validation
2.  Genetic operators respect template boundaries (same-template crossover, template mutation)
3.  Population can be initialized with configurable template distribution
4.  Fitness evaluation routes to correct template based on individual's template_type
5.  Evolution metrics track template performance separately
6.  Backward compatibility maintained for single-template workflows
7.  10-generation test achieves >1.0 Sharpe when TurtleTemplate individuals are present
8.  Template diversity maintained throughout evolution (each template ≥5% of final population)
9.  Performance overhead <10% compared to single-template baseline
10.  All existing Phase 1 tests pass without modification
