# Requirements Document

## Introduction

This control specification orchestrates the parallel execution of **4 priority specs** to maximize development velocity and minimize context-switching overhead. Instead of sequential completion (9 days), parallel execution compresses delivery to **5 days** with 4-6 people working concurrently.

**Problem Statement**:
- Manual coordination of 28 remaining tasks across 4 specs is error-prone
- Repeated analysis in conversations wastes tokens (60K+ per session)
- Sequential execution creates artificial bottlenecks
- No single source of truth for dependencies and timeline

**Solution**:
- **Control Spec**: Central coordination document with dependency matrix
- **Parallel Tracks**: 4 independent execution streams
- **Token Efficiency**: Reusable task breakdown (saves ~40K tokens per session)
- **Timeline Compression**: 44% time savings (9 days → 5 days)

**Specs Under Management**:
1. **Exit Mutation Redesign** (5/8 complete, 62.5%)
2. **LLM Integration Activation** (5/14 complete, 35.7%)
3. **Structured Innovation MVP** (3/13 complete, 23%)
4. **YAML Normalizer Phase2 Complete Normalization** (0/6 complete, 0%)

**Current Status**: 13/41 tasks complete, 28 tasks remaining, 71.5h estimated effort

## Alignment with Product Vision

**避免過度工程化 (Avoid Over-Engineering)**:
- **No new framework**: Use existing spec-workflow for coordination
- **Simple dependency matrix**: Track what blocks what, nothing more
- **Reuse existing tasks.md**: No duplication, just orchestration
- **Control spec is metadata**: Doesn't change implementation details

**從數據中學習 (Learn from Data)**:
- **Evidence-based plan**: Analyzed actual tasks.md from all 4 specs
- **Verified dependencies**: Identified true blockers vs artificial sequencing
- **Historical performance**: Exit Mutation 5/8 proves parallel work succeeds
- **Measurement**: Track actual vs estimated completion for future planning

**漸進式改進 (Incremental Improvement)**:
- **Phase 1** (Current): 13/41 tasks complete via sequential approach
- **Phase 2** (This Spec): Parallel execution unlocks remaining 28 tasks
- **Phase 3** (Future): Lessons learned inform next multi-spec coordination

**自動化優先 (Automation First)**:
- **Automated dependency checking**: Script validates task prerequisites
- **Status aggregation**: Single command shows all 4 specs progress
- **Timeline tracking**: Automated alerts when tasks exceed estimates
- **Resource conflict detection**: Flag when same role needed on multiple tracks

**Product Impact**:
- **Time to Market**: 44% faster delivery (5 days vs 9 days)
- **Token Efficiency**: ~40K tokens saved per planning session
- **Developer Velocity**: 4-6 parallel streams vs 1 sequential
- **Risk Reduction**: Early completion of Exit Mutation + YAML Normalizer (Day 1-2)

## Requirements

### Requirement 1: Dependency Matrix and Parallel Track Definition

**User Story:** As a project coordinator, I want a clear dependency matrix showing which tasks can run in parallel, so that I can maximize concurrent work without introducing blockers.

#### Acceptance Criteria

1. WHEN analyzing task dependencies THEN system SHALL categorize into 4 parallel tracks
   - **Track 1**: Exit Mutation Redesign (Tasks 7-8, independent)
   - **Track 2**: LLM Integration Activation (Tasks 6-14, 2 sub-tracks)
   - **Track 3**: Structured Innovation MVP (Tasks 4-13, 3 sub-tracks)
   - **Track 4**: YAML Normalizer Phase2 (Tasks 1-6, independent)
   - **Validation**: No cross-track dependencies (each track is self-contained)

2. WHEN task has prerequisites THEN dependency SHALL be documented with blocking task reference
   - **Format**: `Dependency: Track 2A Task 6 (LLMConfig loading)`
   - **Intra-track**: Dependencies within same track (e.g., Task 7 → Task 6)
   - **Inter-track**: No dependencies between tracks (all tracks are parallel)
   - **Example**: LLM Task 12 (E2E testing) depends on Task 8+9 (prompts), both in Track 2A

3. WHEN estimating timeline THEN critical path SHALL be identified
   - **Longest Pole**: Track 3 (Structured Innovation) = 2 days
   - **Second**: Track 2 (LLM Integration) = 1.75 days
   - **Fastest**: Track 1 (Exit Mutation) = 0.5 days, Track 4 (YAML Normalizer) = 0.8 days
   - **Wall-Clock**: 5 days (determined by longest track)

4. WHEN tasks can overlap THEN parallel opportunities SHALL be flagged
   - **Example**: LLM Task 8 (modification prompts) + Task 9 (creation prompts) = different files
   - **Example**: Structured Task 7 (integration) + Task 8 (validation) = different modules
   - **Benefit**: Sub-tracks reduce serial bottlenecks by 30-40%

5. IF dependency cycle detected THEN error SHALL be raised with cycle details
   - **Validation**: Topological sort on task graph
   - **Error Message**: "Circular dependency: Task A → Task B → Task A"
   - **Resolution**: Manual review to break cycle

### Requirement 2: Resource Allocation and Role Assignment

**User Story:** As a development lead, I want task assignments organized by role, so that I can allocate the right people to the right tracks without conflicts.

#### Acceptance Criteria

1. WHEN allocating resources THEN tasks SHALL be grouped by specialized role
   - **Backend Dev 1**: Track 2A (LLM Core, 13h)
   - **Backend Dev 2**: Track 3A (Structured Core, 10h) + Track 3B (Integration, 9h)
   - **Backend Dev 3**: Track 4 (YAML Normalizer, 6.5h)
   - **QA Engineer**: Track 2B (LLM Testing, 15h) + Track 3C (Structured Testing, 14h)
   - **Technical Writer**: Track 1 (Exit Docs, 2h) + Track 2/3 Documentation (5h)
   - **DevOps**: Track 1 (Metrics, 2h) + Track 2B (Cost Metrics, 2h) + Track 3 (Benchmarks, 3h)

2. WHEN resource conflicts occur THEN system SHALL flag overlapping assignments
   - **Conflict Detection**: Same role assigned to parallel tasks in same time window
   - **Example**: Backend Dev 2 cannot work on Task 7 and Task 8 simultaneously
   - **Resolution**: Reschedule or assign to different role

3. WHEN estimating capacity THEN person-hours SHALL be compared to wall-clock time
   - **Total Person-Hours**: 81.5h (sum of all task estimates)
   - **Wall-Clock Time**: 5 days × 8h = 40h (longest track)
   - **Parallelism Factor**: 81.5h / 40h = 2.04 (requires 2+ people minimum)
   - **Actual**: 4-6 people for optimal parallelism

4. IF role unavailable THEN alternative assignment SHALL be suggested
   - **Example**: No dedicated QA → Backend Dev runs integration tests
   - **Trade-off**: Slower completion but no external dependency
   - **Documentation**: Backup assignments in tasks.md

5. WHEN track completes THEN resources SHALL be reallocated to remaining tracks
   - **Example**: Backend Dev 3 finishes Track 4 (Day 2) → helps Track 3C testing
   - **Dynamic Reallocation**: Update assignments based on actual progress
   - **Buffer Management**: Use freed resources for at-risk tasks

### Requirement 3: Timeline Tracking and Progress Monitoring

**User Story:** As a project manager, I want real-time visibility into progress across all 4 specs, so that I can identify delays and adjust plans proactively.

#### Acceptance Criteria

1. WHEN tracking progress THEN aggregated status SHALL be available for all specs
   - **Command**: `python scripts/check_priority_specs_status.py`
   - **Output**: Table showing completed/total tasks per spec
   - **Example**:
     ```
     Exit Mutation:     7/8  (87.5%) - Track 1 complete
     LLM Integration:   9/14 (64.3%) - Track 2A complete, 2B in-progress
     Structured Innov:  8/13 (61.5%) - Track 3B complete, 3C in-progress
     YAML Normalizer:   6/6  (100%)  - Track 4 complete
     TOTAL:            30/41 (73.2%)
     ```

2. WHEN task exceeds estimate THEN alert SHALL be triggered
   - **Threshold**: Actual time > 1.5× estimated time
   - **Alert**: WARNING log + optional notification
   - **Message**: "LLM Task 12 exceeded estimate: 6h actual vs 4h estimated"
   - **Action**: Review task complexity, update estimates for similar tasks

3. WHEN critical path task is delayed THEN impact analysis SHALL be provided
   - **Critical Path**: Track 3 (Structured Innovation) determines overall timeline
   - **Impact**: 1 day delay in Track 3 Task 11 → 1 day delay in overall completion
   - **Mitigation**: Shift resources from completed tracks to critical path
   - **Example**: Backend Dev 3 finished Track 4 → helps with Track 3C testing

4. IF spec blocked by external dependency THEN tracking SHALL note blocker
   - **Example**: "LLM Integration blocked: API key not configured"
   - **Status**: `blocked` (different from `in-progress` or `pending`)
   - **Resolution**: Document blocker, update ETA when resolved

5. WHEN all tasks complete THEN final metrics SHALL be generated
   - **Metrics**:
     - Total time: 5 days (actual) vs 5 days (estimated)
     - Person-hours: 81.5h (actual) vs 81.5h (estimated)
     - Task overruns: X tasks exceeded estimate by Y%
     - Parallelism efficiency: (person-hours / wall-clock) = Z
   - **Report**: Feed into future multi-spec planning

### Requirement 4: Quick Wins Identification and Prioritization

**User Story:** As a developer, I want to see which tasks provide maximum impact with minimum effort, so that I can demonstrate early progress and unblock downstream work.

#### Acceptance Criteria

1. WHEN identifying quick wins THEN tasks SHALL be ranked by effort and impact
   - **Quick Win Criteria**:
     - Effort: <4h
     - Impact: Unblocks multiple downstream tasks OR completes entire spec
     - Independence: No prerequisites
   - **Example Quick Wins (Day 1)**:
     - Exit Mutation Task 7 (2h) → Completes entire spec to 87.5%
     - YAML Normalizer Task 1-3 (2.25h) → Unblocks Tasks 4-6
     - LLM Integration Task 6 (3h) → Unblocks Tasks 7-14
     - Structured Innovation Task 4 (4h) → Unblocks Track 3B and 3C

2. WHEN Day 1 is planned THEN quick wins SHALL be prioritized
   - **Day 1 Target**: Complete 4 quick wins = 13.25h of work
   - **Impact**:
     - 1 spec fully complete (Exit Mutation)
     - 2 specs 50%+ unblocked (LLM, Structured)
     - 1 spec core foundation complete (YAML Normalizer)
   - **Psychological Benefit**: Early momentum, visible progress

3. WHEN task unblocks multiple downstream tasks THEN priority SHALL be elevated
   - **Example**: LLM Task 6 (config loading) unblocks 8 downstream tasks
   - **Multiplier Effect**: 3h investment → 25h of parallelizable work
   - **Priority Formula**: `impact_score = downstream_hours × (1 / effort_hours)`

4. IF quick win has high risk THEN mitigation plan SHALL be documented
   - **Example**: YAML Normalizer Task 6 (integration testing) might reveal <85% success rate
   - **Mitigation**: Allocate 4h buffer on Day 4 for schema refinement
   - **Decision Tree**: If success rate <85% → iterate on normalization logic

5. WHEN quick wins are exhausted THEN focus SHALL shift to critical path
   - **Transition**: After Day 1 quick wins, prioritize Track 3 (longest pole)
   - **Reasoning**: Completing Track 3 determines overall timeline
   - **Resource Shift**: Freed resources from Track 1+4 → Track 3C testing

### Requirement 5: Token Efficiency and Reusable Context

**User Story:** As a system maintainer, I want task breakdowns and dependencies stored in a reusable format, so that each conversation doesn't require 40K+ tokens to re-analyze the same information.

#### Acceptance Criteria

1. WHEN starting new conversation THEN control spec SHALL provide complete context
   - **Single File**: `.spec-workflow/specs/priority-specs-parallel-execution/tasks.md`
   - **Content**: All 4 specs' task breakdowns, dependencies, timeline
   - **Token Count**: ~8K tokens (vs 40K+ for re-analysis)
   - **Savings**: 80% reduction in context overhead

2. WHEN task status changes THEN control spec SHALL be updated
   - **Update Mechanism**: Edit tasks.md to change [ ] → [-] → [x]
   - **Propagation**: Control spec aggregates status from all 4 individual specs
   - **Command**: `python scripts/update_control_spec_status.py`
   - **Frequency**: After each task completion

3. WHEN dependencies change THEN control spec SHALL reflect updates
   - **Example**: New blocker discovered (e.g., LLM Task 12 now depends on Task 11)
   - **Update**: Edit dependency matrix in tasks.md
   - **Validation**: Re-run topological sort to detect cycles
   - **Communication**: Update timeline if critical path affected

4. IF control spec becomes stale THEN validation SHALL fail with clear message
   - **Staleness Detection**: Individual spec tasks.md updated but control spec not
   - **Error**: "Control spec out of sync: LLM Integration shows 6/14 tasks but control spec shows 5/14"
   - **Resolution**: Run sync script to reconcile discrepancies

5. WHEN generating reports THEN control spec SHALL be single source of truth
   - **Reports**:
     - Daily standup status (completed tasks, blockers, ETA)
     - Weekly summary (overall progress, trends, risks)
     - Final retrospective (actuals vs estimates, lessons learned)
   - **Data Source**: All data pulled from control spec tasks.md
   - **No Re-analysis**: Never regenerate dependency matrix from scratch

## Non-Functional Requirements

### Code Architecture and Modularity

**Single Responsibility Principle**:
- **Control Spec (this)**: Orchestration and dependency management only
- **Individual Specs**: Implementation details remain in their own tasks.md
- **Scripts**: Automation for status checking and synchronization
- **Separation**: Control spec never duplicates implementation tasks

**Modular Design**:
- **Dependency Matrix**: Standalone data structure (JSON or YAML)
- **Timeline Calculator**: Pure function (dependencies + estimates → schedule)
- **Status Aggregator**: Queries all 4 specs, no hardcoded paths
- **Reporting**: Pluggable output formats (CLI table, JSON, Grafana)

**Dependency Management**:
- **No Circular Dependencies**: Enforced by topological sort validation
- **Minimal Inter-track Dependencies**: Only where absolutely necessary
- **Explicit Prerequisites**: All dependencies documented in tasks.md
- **Testable**: Dependency graph can be validated without running code

**Clear Interfaces**:
```python
# Dependency Matrix
dependencies = {
    "track-2a-task-7": ["track-2a-task-6"],
    "track-2a-task-8": ["track-2a-task-7"],
    # ...
}

# Status Query
def get_spec_status(spec_name: str) -> Dict[str, Any]:
    """Returns {completed: int, total: int, percentage: float}"""

# Timeline Calculation
def calculate_timeline(dependencies, estimates) -> List[Day]:
    """Returns [{day: 1, tracks: [{track: "2A", tasks: [...]}, ...]}]"""
```

### Performance

**Status Checking Speed**:
- **Target**: <2s to aggregate status from all 4 specs
- **Method**: Parallel file reads (4 concurrent reads)
- **Caching**: Cache parsed tasks.md for 5 minutes

**Timeline Calculation Speed**:
- **Target**: <100ms for dependency graph + timeline generation
- **Algorithm**: Topological sort (O(V+E) where V=41 tasks, E~=60 dependencies)
- **Acceptable**: Negligible overhead for 41 tasks

**Token Efficiency**:
- **Baseline**: 60K tokens per planning session (historical)
- **Target**: 8K tokens with control spec (87% reduction)
- **Measurement**: Track token usage in conversation metadata

### Security

**Data Integrity**:
- **Immutable History**: Git tracks all changes to control spec
- **Validation**: Schema validation for dependency matrix format
- **No Code Execution**: Control spec is pure data (JSON/YAML + Markdown)

**Access Control**:
- **File Permissions**: Standard git repository permissions
- **No External APIs**: All data local to repository
- **Audit Trail**: Git log shows who updated what when

### Reliability

**Error Handling**:
- **Missing Spec**: Clear error if individual spec tasks.md not found
- **Circular Dependencies**: Detected and reported with cycle details
- **Stale Data**: Validation checks timestamp mismatches
- **Graceful Degradation**: If one spec unavailable, show status for others

**Backward Compatibility**:
- **No Breaking Changes**: Control spec is additive (doesn't modify existing specs)
- **Optional**: Individual specs work independently of control spec
- **Migration**: Can add/remove specs from control without disrupting others

**Monitoring**:
- **Health Check**: Daily validation that control spec matches individual specs
- **Drift Detection**: Alert if discrepancies exceed threshold (e.g., >2 tasks out of sync)
- **Automated Sync**: Optional cron job to reconcile status daily

### Usability

**Developer Experience**:
- **Single Command**: `check-priority-specs-status` shows everything
- **Clear Output**: Color-coded progress (green=complete, yellow=in-progress, red=blocked)
- **Actionable Insights**: "Next recommended tasks: LLM Task 6, Structured Task 4"

**Documentation**:
- **README**: How to use control spec, interpret output, update status
- **Examples**: Sample commands with expected output
- **Troubleshooting**: Common issues (staleness, dependency cycles, etc.)

**Integration**:
- **CI/CD**: Status check runs on every commit to verify progress
- **Dashboard**: Optional Grafana integration for visual timeline
- **Slack/Email**: Daily digest of progress and blockers

### Maintainability

**Code Quality**:
- **Type Hints**: All Python scripts fully typed
- **PEP 8**: Linting with flake8
- **Test Coverage**: >80% for dependency calculation and status aggregation

**Configuration Management**:
- **YAML Config**: Specify which specs are part of control group
- **Example**:
  ```yaml
  control_spec:
    name: priority-specs-parallel-execution
    specs:
      - exit-mutation-redesign
      - llm-integration-activation
      - structured-innovation-mvp
      - yaml-normalizer-phase2-complete-normalization
  ```

**Future-Proofing**:
- **Extensible**: Easy to add 5th spec to control group
- **Pluggable**: Different dependency solvers (manual, automatic)
- **Scalable**: Works for 4 specs or 40 specs (algorithm is O(V+E))

---

**Document Version**: 1.0
**Created**: 2025-10-27
**Status**: Draft - Pending Approval
**Owner**: Personal Project (週/月交易系統)
**Dependencies**:
- Exit Mutation Redesign (5/8 complete)
- LLM Integration Activation (5/14 complete)
- Structured Innovation MVP (3/13 complete)
- YAML Normalizer Phase2 Complete Normalization (0/6 complete)

**Estimated Effort**: 3-4 hours
- Control spec tasks.md creation: 1h
- Status aggregation script: 1h
- Dependency validation script: 0.5h
- Documentation and testing: 1h
