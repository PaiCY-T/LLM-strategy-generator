# Implementation Plan

## Task Overview

Implementation follows a bottom-up approach: foundational infrastructure � core functionality � AI features � UI integration. Each task is atomic (15-30 min), touches 1-3 files, and has a single testable outcome.

## Steering Document Compliance

**Project Structure**: Following proposed structure from design.md
**Technical Standards**: Python 3.8+, PEP 8, Streamlit, SQLite, Finlab API integration

## Atomic Task Requirements

**Each task meets these criteria:**
- **File Scope**: Touches 1-3 related files maximum
- **Time Boxing**: Completable in 15-30 minutes
- **Single Purpose**: One testable outcome per task
- **Specific Files**: Exact file paths to create/modify
- **Agent-Friendly**: Clear input/output with minimal context switching

## Task Format Guidelines

- Checkbox format with numbered hierarchy
- **Specify files**: Exact file paths
- **Include implementation details** as bullet points
- Reference requirements: `_Requirements: X.Y_`
- Reference existing code: `_Leverage: finlab.data.get(), finlab.backtest.sim()_`

## Tasks

### Phase 1: Project Setup and Infrastructure (Foundation)

- [ ] 1. Create project directory structure
  - Files: Create directories as per design.md structure
  - Create `src/`, `src/data/`, `src/backtest/`, `src/analysis/`, `src/ui/`, `src/utils/`
  - Create `data/`, `storage/`, `config/`, `tests/`
  - Create `__init__.py` in each src subdirectory
  - Purpose: Establish project organization following design.md structure
  - _Requirements: Design structure, Maintainability NFR_
  - **QA Step 1**: Run code review on created `__init__.py` files with `mcp__zen__codereview`
  - **QA Step 2**: Validate directory structure correctness with `mcp__zen__challenge` using `gemini-2.5-pro`
  - **Evidence Required**:
    - Directory tree output (`tree -L 3` or `ls -R`)
    - Code review PASS status for all `__init__.py` files
    - Challenge validation confirming structure matches design.md

- [ ] 2. Create requirements.txt with dependencies
  - File: `requirements.txt`
  - Add: finlab>=0.4.0, streamlit>=1.28.0, pandas>=1.5.0, plotly>=5.14.0
  - Add: anthropic>=0.7.0, python-dotenv>=1.0.0, cryptography>=41.0.0
  - Add: pytest>=7.4.0, pytest-asyncio>=0.21.0, streamlit-ace>=0.1.1
  - Purpose: Define all project dependencies with pinned versions
  - _Requirements: Design - Technology Stack_

- [ ] 3. Create configuration file template
  - File: `config/app_config.yaml`
  - Define finlab, backtest, analysis, storage, ui sections per design.md
  - Set defaults: cache_retention_days=30, timeout_seconds=120, max_suggestions=5
  - Purpose: Centralize configuration with sensible defaults
  - _Leverage: Design.md Configuration Management section_
  - _Requirements: REQ-1, Design standards_

- [ ] 4. Create .env template file
  - File: `.env.example`
  - Add placeholders: FINLAB_API_TOKEN=your_token_here, CLAUDE_API_KEY=your_key_here
  - Add comments explaining where to get API keys
  - Purpose: Provide template for user credentials
  - _Requirements: Security NFR (token storage)_

- [ ] 5. Create configuration loader utility
  - File: `src/utils/config.py`
  - Implement `load_config()` to read app_config.yaml
  - Implement `load_env()` to read .env using python-dotenv
  - Return typed config objects (dataclass or dict)
  - Purpose: Centralize configuration loading with type safety
  - _Leverage: python-dotenv library, yaml library_
  - _Requirements: Maintainability NFR_

### Phase 2: Data Layer (REQ-1: Finlab API Integration)

- [ ] 6. Create data manager interface
  - File: `src/data/__init__.py`
  - Define DataManager class with method signatures from design.md
  - Add type hints: download_data, get_cached_data, check_data_freshness, list_available_datasets
  - Purpose: Establish data layer contract
  - _Requirements: REQ-1, Design Component 1_

- [ ] 7. Implement data download method
  - File: `src/data/manager.py` (continue from task 6)
  - Implement `download_data(dataset, force_refresh)` using finlab.data.get()
  - Configure finlab.data.set_storage() to use FileStorage with data/ directory
  - Add error handling for network failures with exponential backoff (5s, 10s, 20s, 40s)
  - Purpose: Enable data retrieval from Finlab API with resilience
  - _Leverage: finlab.data.get(), finlab.data.set_storage()_
  - _Requirements: AC-1.1, AC-1.2, AC-1.7, Reliability NFR_

- [ ] 8. Implement cache freshness checking
  - File: `src/data/manager.py` (continue)
  - Implement `check_data_freshness(dataset)` returning (is_fresh: bool, timestamp: datetime)
  - Check file modification time against 7-day threshold
  - Use ISO 8601 timestamp format for cache file naming
  - Purpose: Prevent using stale data
  - _Leverage: pathlib for file operations, datetime for timestamps_
  - _Requirements: AC-1.6, AC-1.8_

- [ ] 9. Implement cached data retrieval
  - File: `src/data/manager.py` (continue)
  - Implement `get_cached_data(dataset)` returning DataFrame or None
  - Check cache directory for existing data files
  - Return None if not cached, triggering download
  - Purpose: Minimize API calls by reusing cached data
  - _Leverage: finlab FileStorage, pandas read methods_
  - _Requirements: AC-1.3_

- [ ] 10. Add rate limit handling to data manager
  - File: `src/data/manager.py` (continue)
  - Wrap finlab.data.get() calls in try/except for rate limit errors
  - Implement request queue with exponential backoff
  - Log retry attempts and wait times
  - Purpose: Handle Finlab API rate limits gracefully
  - _Requirements: AC-1.7, Design Error Handling #1_

- [ ] 11. Create data manager unit tests
  - File: `tests/data/test_manager.py`
  - Mock finlab.data.get() responses
  - Test download_data, get_cached_data, check_data_freshness methods
  - Test exponential backoff timing
  - Purpose: Ensure data manager reliability
  - _Leverage: pytest, unittest.mock_
  - _Requirements: Design Testing Strategy_

### Phase 3: Storage Layer (REQ-8: Version Management, REQ-4: Iteration History)

- [ ] 12. Create database schema initialization script
  - File: `src/utils/init_db.py`
  - Implement `initialize_database()` creating SQLite database at storage/iterations.db
  - Create tables: strategies, iterations, metrics, suggestions, trades
  - Create all indexes from design.md schema
  - Purpose: Initialize persistent storage structure
  - _Leverage: sqlite3 module_
  - _Requirements: Design Database Schema, REQ-8, REQ-4_

- [ ] 13. Create storage manager interface
  - File: `src/storage/__init__.py`
  - Define StorageManager class with method signatures from design.md
  - Add type hints for all methods: save_iteration, load_iteration, save_strategy_version, etc.
  - Purpose: Establish storage layer contract
  - _Requirements: Design Component 6_

- [ ] 14. Implement strategy version saving
  - File: `src/storage/manager.py` (continue from task 13)
  - Implement `save_strategy_version(strategy)` with parameterized INSERT query
  - Generate UUID for strategy ID, timestamp for version
  - Return strategy_id on success
  - Purpose: Enable strategy versioning with lineage tracking
  - _Leverage: sqlite3, uuid, datetime_
  - _Requirements: AC-8.1, Design Component 6_

- [ ] 15. Implement iteration saving with connection pooling
  - File: `src/storage/manager.py` (continue)
  - Implement connection pool (queue with 5 connections) per design.md
  - Implement `save_iteration(iteration)` with atomic write operation
  - Save to iterations, metrics, trades tables in transaction
  - Return iteration_id on success
  - Purpose: Store iteration results with data integrity
  - _Leverage: queue.Queue for connection pool, sqlite3 transactions_
  - _Requirements: AC-4.1, Design Component 6 (concurrency handling)_

- [ ] 16. Implement iteration loading
  - File: `src/storage/manager.py` (continue)
  - Implement `load_iteration(iteration_id)` with JOIN queries
  - Reconstruct Iteration object from database rows
  - Include metrics, suggestions, trades
  - Purpose: Retrieve complete iteration data
  - _Leverage: sqlite3, dataclasses_
  - _Requirements: AC-8.3, Design Component 6_

- [ ] 17. Implement strategy export to JSON
  - File: `src/storage/manager.py` (continue)
  - Implement `export_results(iteration_ids, format="json")`
  - Serialize iteration data including code, metrics, trades
  - Save to user-specified file path
  - Purpose: Enable strategy sharing and backup
  - _Leverage: json module_
  - _Requirements: AC-8.4_

- [ ] 18. Add automatic backup scheduler
  - File: `src/storage/backup.py`
  - Implement `BackupScheduler` class with daily backup logic
  - Copy storage/iterations.db to storage/backups/ with timestamp
  - Cleanup backups older than 30 days
  - Purpose: Protect against data loss
  - _Leverage: shutil for file copy, schedule or APScheduler library_
  - _Requirements: Design Component 6 (backup automation), Reliability NFR_

- [ ] 19. Create storage manager unit tests
  - File: `tests/storage/test_manager.py`
  - Use in-memory SQLite (:memory:) for testing
  - Test save/load iteration cycle, strategy versioning, export/import
  - Test connection pooling with concurrent access
  - Purpose: Ensure storage reliability and data integrity
  - _Leverage: pytest, sqlite3 in-memory database_
  - _Requirements: Design Testing Strategy_

### Phase 4: Backtest Engine (REQ-2: Core Backtesting)

- [ ] 20. Create backtest engine interface
  - File: `src/backtest/__init__.py`
  - Define BacktestEngine class with async method signatures from design.md
  - Define BacktestResult and PerformanceMetrics dataclasses
  - Purpose: Establish backtest layer contract
  - _Requirements: REQ-2, Design Component 2_

- [ ] 21. Implement strategy code validation
  - File: `src/backtest/engine.py` (continue from task 20)
  - Implement `validate_strategy_code(code)` using AST parsing
  - Check for syntax errors, restricted imports, forbidden builtins
  - Return (is_valid, error_message) tuple
  - Purpose: Prevent execution of invalid or malicious code
  - _Leverage: ast module, Design Security (code sandboxing)_
  - _Requirements: AC-5.1, Security NFR_

- [ ] 22. Implement code execution sandbox with resource limits
  - File: `src/backtest/sandbox.py`
  - Implement `execute_with_limits(code, timeout=120)` per design.md Security section
  - Set memory limit (500MB), CPU time limit, timeout alarm
  - Use restricted builtins dict for safe execution
  - Purpose: Execute user code safely with resource constraints
  - _Leverage: resource, signal modules_
  - _Requirements: Security NFR, Design Security #2_

- [ ] 23. Implement async backtest execution
  - File: `src/backtest/engine.py` (continue)
  - Implement `async run_backtest(strategy_code, data_config, backtest_params)`
  - Wrap finlab.backtest.sim() in ThreadPoolExecutor for async execution
  - Execute strategy code in sandbox, capture results
  - Return BacktestResult with portfolio positions, trade records, equity curve
  - Purpose: Execute backtests without blocking UI
  - _Leverage: asyncio.get_event_loop().run_in_executor(), finlab.backtest.sim()_
  - _Requirements: AC-2.1, AC-6.1, Design Component 2_

- [ ] 24. Implement performance metrics calculation
  - File: `src/backtest/metrics.py`
  - Implement `calculate_metrics(backtest_result)` returning PerformanceMetrics
  - Calculate annualized return using finlab report.metrics.annual_return()
  - Calculate Sharpe ratio using report.metrics.sharpe_ratio()
  - Calculate max drawdown using report.metrics.max_drawdown()
  - Calculate win rate, profit factor, total trades from trade records
  - Purpose: Extract standard performance metrics from backtest results
  - _Leverage: finlab report.metrics methods, pandas operations_
  - _Requirements: AC-2.2, AC-2.3, AC-2.4, AC-2.5_

- [ ] 25. Implement zero trades detection
  - File: `src/backtest/engine.py` (continue)
  - Add check after backtest execution: if total_trades == 0
  - Return error result with suggestion to review entry/exit conditions
  - Log warning with strategy code summary
  - Purpose: Detect and handle strategies with no signals
  - _Requirements: AC-2.8, Design Error Handling #3_

- [ ] 26. Create backtest visualization generator
  - File: `src/backtest/visualizer.py`
  - Implement `generate_visualizations(backtest_result)` returning dict of Plotly figures
  - Create equity curve chart (cumulative returns over time)
  - Create drawdown chart (underwater equity chart)
  - Create trade distribution chart (profit/loss histogram)
  - Purpose: Provide visual analysis of backtest results
  - _Leverage: plotly.graph_objects_
  - _Requirements: AC-2.7, REQ-7 (visualizations)_

- [ ] 27. Create backtest engine unit tests
  - File: `tests/backtest/test_engine.py`
  - Mock finlab.backtest.sim() with sample return data
  - Test valid/invalid code validation
  - Test async execution completes
  - Test metrics calculation accuracy
  - Test zero trades detection
  - Purpose: Ensure backtest engine reliability
  - _Leverage: pytest, pytest-asyncio, unittest.mock_
  - _Requirements: Design Testing Strategy_

### Phase 5: Input Handler (REQ-5: Code and NL Input)

- [ ] 28. Create input handler interface
  - File: `src/input/__init__.py`
  - Define InputHandler class with async method signatures from design.md
  - Define ProcessedStrategy and ValidationResult dataclasses
  - Purpose: Establish input processing contract
  - _Requirements: REQ-5, Design Component 3_

- [ ] 29. Implement Finlab API compatibility checker
  - File: `src/input/validator.py`
  - Implement `validate_finlab_compatibility(code)` checking for:
    - finlab.data.get() calls, finlab.backtest.sim() usage
    - Position DataFrame generation (is_largest, is_smallest patterns)
    - Common errors: missing imports, incorrect parameter names
  - Return ValidationResult with errors and warnings
  - Purpose: Catch Finlab-specific usage errors before execution
  - _Leverage: ast module, regex for pattern matching_
  - _Requirements: AC-5.5, Design Component 3_

- [ ] 30. Implement code input processing
  - File: `src/input/handler.py` (continue from task 28)
  - Implement `async process_code_input(code)` method
  - Validate syntax using AST
  - Check Finlab compatibility using validator
  - Extract strategy parameters (resample, stop_loss, etc.) using regex
  - Return ProcessedStrategy with code, explanation, parameters, validation status
  - Purpose: Process and validate user-provided strategy code
  - _Leverage: ast, re modules, validator from task 29_
  - _Requirements: AC-5.1, Design Component 3_

- [ ] 31. Create clarification handler
  - File: `src/input/clarification.py`
  - Implement ClarificationHandler with `generate_clarifying_questions(missing_elements)`
  - Define question templates for missing entry conditions, exit conditions, timeframe
  - Return list of specific questions to ask user
  - Purpose: Enable multi-turn conversation for incomplete NL prompts
  - _Requirements: AC-5.3, Design Component 8_

- [ ] 32. Implement natural language to code conversion
  - File: `src/input/handler.py` (continue)
  - Implement `async process_nl_input(prompt)` using Claude API
  - Check prompt completeness, use ClarificationHandler if needed
  - Construct Claude API request with Finlab documentation context
  - Parse Claude response to extract strategy code
  - Validate generated code using validator
  - Return ProcessedStrategy with generated code and explanation
  - Purpose: Convert natural language strategy descriptions to executable Finlab code
  - _Leverage: anthropic library, ClarificationHandler_
  - _Requirements: AC-5.2, AC-5.3, AC-5.4, Design Component 3_

- [ ] 33. Add syntax highlighting for code display
  - File: `src/input/formatter.py`
  - Implement `highlight_code(code, language="python")` using Pygments
  - Return syntax-highlighted HTML or formatted string
  - Purpose: Improve code readability in UI
  - _Leverage: pygments library_
  - _Requirements: AC-5.6, Design Component 3_

- [ ] 34. Create input handler unit tests
  - File: `tests/input/test_handler.py`
  - Test code validation with valid/invalid Finlab code
  - Mock Claude API for NL processing tests
  - Test clarifying questions generation
  - Test parameter extraction from strategy code
  - Purpose: Ensure input processing reliability
  - _Leverage: pytest, pytest-asyncio, unittest.mock for Claude API_
  - _Requirements: Design Testing Strategy_

### Phase 6: Learning Engine (REQ-4: Iterative Learning)

- [ ] 35. Create learning engine interface
  - File: `src/learning/__init__.py`
  - Define LearningEngine class with method signatures from design.md
  - Define LearningContext, Pattern, ConvergenceReport dataclasses
  - Purpose: Establish learning layer contract
  - _Requirements: REQ-4, Design Component 5_

- [ ] 36. Implement iteration history analysis
  - File: `src/learning/engine.py` (continue from task 35)
  - Implement `analyze_iteration_history(min_iterations=5)` method
  - Load all iterations from storage
  - Calculate metric deltas between consecutive iterations
  - Build LearningContext with trends
  - Purpose: Extract insights from historical iterations
  - _Leverage: storage manager, pandas for trend analysis_
  - _Requirements: AC-4.2, Design Component 5_

- [ ] 37. Implement successful pattern identification
  - File: `src/learning/patterns.py`
  - Implement `identify_successful_patterns()` using simple heuristics
  - Pattern = successful if: Sharpe improvement > 10% OR return improvement > 15%
  - Categorize patterns: risk_management, entry_condition, position_sizing
  - Store pattern type, description, metric impact, confidence
  - Purpose: Identify what works for learning
  - _Requirements: AC-4.3, Design Component 5 (pattern recognition)_

- [ ] 38. Implement failed pattern identification
  - File: `src/learning/patterns.py` (continue)
  - Implement `identify_failed_patterns()` using heuristics
  - Pattern = failed if: any metric degraded > 5%
  - Store pattern type, description, metric impact
  - Purpose: Identify what doesn't work to avoid in future
  - _Requirements: AC-4.4, Design Component 5_

- [ ] 39. Implement convergence detection
  - File: `src/learning/convergence.py`
  - Implement `detect_convergence()` checking last 3 iterations
  - Convergence detected if: metric improvements all < 2%
  - Return ConvergenceReport with status and recommended actions
  - Purpose: Inform user when further optimization yields diminishing returns
  - _Requirements: AC-4.6, Design Component 5_

- [ ] 40. Create learning engine unit tests
  - File: `tests/learning/test_engine.py`
  - Create synthetic iteration data with known patterns
  - Test pattern identification (successful and failed)
  - Test convergence detection with various scenarios
  - Purpose: Ensure learning logic reliability
  - _Leverage: pytest_
  - _Requirements: Design Testing Strategy_

### Phase 7: Analysis Engine (REQ-3: AI-Driven Suggestions)

- [ ] 41. Create analysis engine interface
  - File: `src/analysis/__init__.py`
  - Define AnalysisEngine class with async method signatures from design.md
  - Define AnalysisReport and Suggestion dataclasses (with learning_references field)
  - Purpose: Establish analysis layer contract
  - _Requirements: REQ-3, Design Component 4_

- [ ] 42. Implement rule-based suggestion templates
  - File: `src/analysis/rules.py`
  - Implement RULE_BASED_TEMPLATES dict from design.md
  - Define conditions and suggestions for: low_sharpe, high_drawdown, low_win_rate, few_trades
  - Include specific code changes, expected impact ranges, priorities
  - Purpose: Provide fallback suggestions when Claude API unavailable
  - _Leverage: Design Component 4 (Rule-Based Suggestion Templates)_
  - _Requirements: AC-3.9, Design Component 4_

- [ ] 43. Implement rule-based suggestion generator
  - File: `src/analysis/rules.py` (continue)
  - Implement `generate_rule_based_suggestions(metrics)` evaluating all rule conditions
  - Return 3-5 suggestions matching triggered rules
  - Rank by priority (high > medium > low)
  - Purpose: Generate suggestions without AI when needed
  - _Requirements: AC-3.9, Design Component 4_

- [ ] 44. Implement backtest results analysis
  - File: `src/analysis/analyzer.py`
  - Implement `async analyze_results(backtest_result, metrics, iteration_history)`
  - Identify weaknesses: Sharpe < 1.0, MDD > 20%, win rate < 50%
  - Identify strengths: consistent profitability, low drawdown periods
  - Identify risk factors and opportunity areas
  - Return AnalysisReport
  - Purpose: Systematically analyze backtest performance
  - _Leverage: pandas for data analysis_
  - _Requirements: AC-3.1, Design Component 4_

- [ ] 45. Implement Claude API suggestion generation
  - File: `src/analysis/ai_analyzer.py`
  - Implement `async generate_ai_suggestions(analysis_report, learning_context)` using Claude API
  - Construct structured prompt with current metrics, weaknesses, historical patterns
  - Parse Claude response to extract suggestions with all required fields
  - Add learning_references to each suggestion linking to historical patterns
  - Return List[Suggestion]
  - Purpose: Generate intelligent suggestions using AI
  - _Leverage: anthropic library, learning context_
  - _Requirements: AC-3.6, AC-3.7, AC-4.5, Design Component 4_

- [ ] 46. Implement suggestion ranking
  - File: `src/analysis/ranker.py`
  - Implement `rank_suggestions(suggestions, learning_context)` method
  - Boost priority if similar suggestion succeeded in past (from learning context)
  - Lower priority if similar suggestion failed
  - Sort by: priority weight * expected_impact * confidence
  - Purpose: Prioritize most promising suggestions
  - _Leverage: learning context with successful/failed patterns_
  - _Requirements: AC-3.8, AC-4.3, AC-4.4, Design Component 4_

- [ ] 47. Implement main analysis workflow
  - File: `src/analysis/engine.py` (continue from task 41)
  - Implement `async analyze_and_suggest()` orchestrating analyzer, AI, rules, ranker
  - Try AI suggestions first, fallback to rules if API fails
  - Limit output to 3-5 suggestions
  - Ensure all suggestions have learning_references populated
  - Purpose: Complete analysis workflow with fallback
  - _Requirements: AC-3.2, AC-3.9, REQ-3, Design Component 4_

- [ ] 48. Create analysis engine unit tests
  - File: `tests/analysis/test_engine.py`
  - Mock Claude API responses
  - Test rule-based suggestion generation with various metrics
  - Test AI suggestion parsing and validation
  - Test suggestion ranking logic
  - Test learning_references are properly added
  - Purpose: Ensure analysis reliability
  - _Leverage: pytest, pytest-asyncio, unittest.mock_
  - _Requirements: Design Testing Strategy_

### Phase 8: Comparison Engine (REQ-9: Multi-Strategy Comparison)

- [ ] 49. Create comparison engine interface
  - File: `src/comparison/__init__.py`
  - Define ComparisonEngine class with method signatures from design.md
  - Define ComparisonResult, HighlightedComparison, CodeDiff dataclasses
  - Purpose: Establish comparison layer contract
  - _Requirements: REQ-9, Design Component 7_

- [ ] 50. Implement strategy comparison
  - File: `src/comparison/engine.py` (continue from task 49)
  - Implement `compare_strategies(strategy_ids)` loading multiple strategies from storage
  - Build comparison DataFrame with all metrics as columns
  - Identify best_per_metric using max/min as appropriate
  - Return ComparisonResult
  - Purpose: Enable side-by-side strategy comparison
  - _Leverage: storage manager, pandas DataFrame_
  - _Requirements: AC-9.1, AC-9.2, Design Component 7_

- [ ] 51. Implement best metric highlighting
  - File: `src/comparison/highlighter.py`
  - Implement `highlight_best_metrics(comparison_result)` generating HTML table
  - Highlight best values in each column with CSS class
  - Calculate best_overall using weighted score: 0.4*sharpe + 0.3*return + 0.3*(1-drawdown)
  - Return HighlightedComparison with HTML
  - Purpose: Visual comparison with best values highlighted
  - _Leverage: pandas.DataFrame.style for HTML generation_
  - _Requirements: AC-9.2, Design Component 7_

- [ ] 52. Implement overlay chart generation
  - File: `src/comparison/charts.py`
  - Implement `generate_overlay_chart(strategy_ids)` creating Plotly multi-line chart
  - Load equity curves for all strategies
  - Normalize to percentage returns if different time periods
  - Use distinct colors for up to 5 strategies
  - Purpose: Visual comparison of returns over time
  - _Leverage: plotly.graph_objects, pandas_
  - _Requirements: AC-9.3, Design Component 7_

- [ ] 53. Implement code diff generation
  - File: `src/comparison/diff.py`
  - Implement `generate_code_diff(strategy_id_1, strategy_id_2)` using difflib
  - Generate unified diff format
  - Apply syntax highlighting to diff using Pygments
  - Count additions, deletions, modifications
  - Return CodeDiff with diff_html and changes_summary
  - Purpose: Show code changes between strategy versions
  - _Leverage: difflib.unified_diff, pygments_
  - _Requirements: AC-9.4, Design Component 7_

- [ ] 54. Create comparison engine unit tests
  - File: `tests/comparison/test_engine.py`
  - Create mock strategies with different metrics
  - Test comparison table generation
  - Test best metric identification
  - Test overlay chart with multiple strategies
  - Test code diff with known changes
  - Purpose: Ensure comparison accuracy
  - _Leverage: pytest_
  - _Requirements: Design Testing Strategy_

### Phase 9: Notification & UI Support (REQ-6, REQ-7, Usability NFR)

- [ ] 55. Create notification handler
  - File: `src/ui/notifications.py`
  - Implement NotificationHandler with methods from design.md Component 8
  - Implement `notify_backtest_complete()` using Streamlit st.toast()
  - Implement `notify_error()` using st.error()
  - Implement `play_sound(sound_type)` using playsound library (optional)
  - Purpose: Provide user feedback for async operations
  - _Leverage: streamlit, playsound library_
  - _Requirements: AC-6.3, Design Component 8_

- [ ] 56. Create tutorial manager
  - File: `src/ui/tutorial.py`
  - Implement TutorialManager with methods from design.md Component 8
  - Load tooltip definitions from JSON i18n files (zh-TW, en-US)
  - Implement `show_onboarding_tour()` using Streamlit components
  - Track tutorial completion in session state
  - Purpose: Help first-time users learn the system
  - _Leverage: streamlit session_state, JSON for i18n_
  - _Requirements: Usability NFR (onboarding tutorial), AC-7.4_

- [ ] 57. Create i18n translation files
  - Files: `config/i18n/zh-TW.json`, `config/i18n/en-US.json`
  - Define translations for all UI labels, tooltips, error messages
  - Structure by screen: dashboard, input, backtest, analysis, suggestions, history, comparison
  - Purpose: Support bilingual interface
  - _Requirements: AC-7.8, Design Component 9_

- [ ] 58. Create i18n utility
  - File: `src/ui/i18n.py`
  - Implement `load_translations(language)` loading JSON translation file
  - Implement `get_text(key, language)` for translation lookup
  - Cache loaded translations in memory
  - Purpose: Simplify bilingual UI development
  - _Leverage: json module, caching_
  - _Requirements: AC-7.8, Design Component 9_

### Phase 10: Streamlit UI Implementation (REQ-7: User Interface)

- [ ] 59. Create main Streamlit app entry point
  - File: `src/ui/main.py`
  - Initialize Streamlit page config with title, icon, layout
  - Load configuration and translations
  - Set up session state for workflow persistence
  - Route to appropriate screen based on session state
  - Purpose: Main application entry point and routing
  - _Leverage: streamlit, session_state_
  - _Requirements: AC-7.1, Design Component 9_

- [ ] 60. Implement dashboard screen (Screen 1)
  - File: `src/ui/screens/dashboard.py`
  - Display workflow progress indicator (Input � Backtest � Analysis � Suggestions)
  - Show quick stats: total iterations, best Sharpe ratio, current strategy name
  - Display recent iterations table with key metrics
  - Add navigation buttons to other screens
  - Purpose: Main entry screen with overview
  - _Leverage: streamlit components, storage manager for data_
  - _Requirements: AC-7.1, AC-7.2, Design Component 9 Screen 1_

- [ ] 61. Implement strategy input screen (Screen 2)
  - File: `src/ui/screens/input.py`
  - Add code editor using streamlit-ace with Python syntax highlighting
  - Add natural language input text area
  - Add "Validate & Preview" button calling InputHandler
  - Display validation status (errors, warnings)
  - Show clarifying questions dialog if NL prompt incomplete
  - Purpose: Strategy input and validation
  - _Leverage: streamlit-ace, InputHandler, ClarificationHandler_
  - _Requirements: AC-5.1, AC-5.2, AC-5.3, AC-5.6, Design Component 9 Screen 2_

- [ ] 62. Implement backtest configuration screen (Screen 3)
  - File: `src/ui/screens/backtest_config.py`
  - Add dataset selection dropdown (populated from DataManager.list_available_datasets())
  - Add date range picker for backtest period
  - Add parameter inputs: resample period, fee_ratio, tax_ratio, stop_loss
  - Add "Run Backtest" button triggering async execution
  - Display progress indicator during execution
  - Purpose: Configure and execute backtests
  - _Leverage: streamlit form components, BacktestEngine_
  - _Requirements: AC-6.1, AC-6.2, Design Component 9 Screen 3_

- [ ] 63. Implement results display screen (Screen 4)
  - File: `src/ui/screens/results.py`
  - Display performance metrics in cards: annualized return, Sharpe ratio, max drawdown
  - Show interactive Plotly charts: equity curve, drawdown, trade distribution
  - Display trade records table with sorting and filtering
  - Add "View Suggestions" button to navigate to suggestions screen
  - Purpose: Display backtest results with visualizations
  - _Leverage: plotly charts, streamlit dataframe, BacktestResult_
  - _Requirements: AC-2.2, AC-2.3, AC-2.4, AC-2.7, AC-7.3, Design Component 9 Screen 4_

- [ ] 64. Implement suggestions screen (Screen 5)
  - File: `src/ui/screens/suggestions.py`
  - Display suggestion cards with priority badges (high/medium/low)
  - Show expandable details: description, specific changes, expected impact, rationale, learning_references
  - Add "Apply Suggestion" button for each suggestion
  - Add checkbox selection for "Apply Multiple" suggestions
  - Purpose: Display and apply AI-generated suggestions
  - _Leverage: streamlit expanders, AnalysisEngine, learning_references from suggestions_
  - _Requirements: AC-3.6, AC-3.7, AC-3.8, AC-4.5, AC-7.7, Design Component 9 Screen 5_

- [ ] 65. Implement iteration history screen (Screen 6)
  - File: `src/ui/screens/history.py`
  - Display timeline visualization of metric progression (line chart)
  - Show iteration list table with sortable columns
  - Add "Compare Selected" button with checkbox selection
  - Add "Export" button for JSON/PDF export
  - Purpose: Review iteration history and trends
  - _Leverage: plotly timeline, streamlit dataframe, StorageManager_
  - _Requirements: AC-4.7, AC-8.2, AC-8.4, AC-8.5, Design Component 9 Screen 6_

- [ ] 66. Implement strategy comparison screen (Screen 7)
  - File: `src/ui/screens/comparison.py`
  - Add multi-select strategy picker
  - Display side-by-side metrics comparison table with highlighted best values
  - Show overlay chart with cumulative returns for all selected strategies
  - Add code diff viewer for two-strategy comparison
  - Add "Export Comparison" button
  - Purpose: Compare multiple strategies side-by-side
  - _Leverage: ComparisonEngine, HighlightedComparison, CodeDiff_
  - _Requirements: AC-9.1, AC-9.2, AC-9.3, AC-9.4, Design Component 9 Screen 7_

- [ ] 67. Add session state management
  - File: `src/ui/state_manager.py`
  - Implement `save_session_state()` persisting to disk every 5 minutes
  - Implement `load_session_state()` restoring on app startup
  - Track: current_screen, current_strategy_code, backtest_results, selected_suggestions
  - Purpose: Preserve user work across sessions
  - _Leverage: streamlit session_state, json for persistence_
  - _Requirements: AC-7.5, Design Component 9_

- [ ] 68. Implement responsive layout
  - File: `src/ui/layout.py`
  - Define consistent column layouts for all screens
  - Implement sidebar navigation
  - Apply consistent styling: colors, fonts, spacing
  - Purpose: Professional, consistent UI across all screens
  - _Leverage: streamlit columns, CSS injection_
  - _Requirements: Usability NFR (consistent design patterns), Design Component 9_

### Phase 11: Integration & Testing

- [ ] 69. Create integration test for complete workflow
  - File: `tests/integration/test_workflow.py`
  - Test end-to-end: NL input � code generation � backtest � suggestions � apply suggestion � re-backtest
  - Use real Finlab API and Claude API (with rate limiting)
  - Verify iteration history is saved correctly
  - Verify learning_references appear in suggestions
  - Purpose: Validate complete system integration
  - _Leverage: pytest, real APIs with credentials from .env_
  - _Requirements: Design Testing Strategy (Integration Testing)_

- [ ] 70. Create E2E test for UI workflow
  - File: `tests/e2e/test_ui_workflow.py`
  - Simulate user journey: open app � input strategy � run backtest � view suggestions � compare strategies
  - Use Selenium or Streamlit testing framework
  - Capture screenshots at each step
  - Purpose: Validate UI functionality and user experience
  - _Leverage: selenium or streamlit testing, pytest_
  - _Requirements: Design Testing Strategy (E2E Testing)_

- [ ] 71. Add performance benchmarking
  - File: `tests/performance/test_benchmarks.py`
  - Benchmark backtest execution time with 2 years of daily data
  - Benchmark suggestion generation time
  - Benchmark UI response time for key interactions
  - Assert performance targets from design.md are met
  - Purpose: Ensure performance requirements are satisfied
  - _Leverage: pytest-benchmark_
  - _Requirements: Performance NFR, Design Performance Targets_

- [ ] 72. Create deployment startup script
  - File: `run.sh` (Linux/macOS) and `run.bat` (Windows)
  - Initialize database if not exists (call init_db.py)
  - Check .env file exists, warn if missing
  - Start Streamlit application on port 8501
  - Purpose: Simplify application startup for users
  - _Requirements: Design Deployment Architecture_

- [ ] 73. Create comprehensive README.md
  - File: `README.md`
  - Document installation steps (Python 3.8+, pip install -r requirements.txt)
  - Document .env setup with API keys
  - Document usage: running the app, basic workflow
  - Include screenshots of main screens
  - Link to design.md and requirements.md for details
  - Purpose: Enable user self-service setup and usage
  - _Requirements: Maintainability NFR, Usability NFR_

- [ ] 74. Create developer documentation
  - File: `DEVELOPER.md`
  - Document project structure and architecture
  - Document how to run tests (pytest)
  - Document how to add new features (extending components)
  - Document code style guidelines (PEP 8, type hints)
  - Purpose: Enable future development and maintenance
  - _Requirements: Maintainability NFR, Design standards_

- [ ] 75. Final integration verification
  - Run all unit tests: `pytest tests/`
  - Run integration tests with real APIs
  - Run E2E tests with UI
  - Verify performance benchmarks pass
  - Verify all 9 requirements have corresponding implemented features
  - Purpose: Confirm system is ready for use
  - _Requirements: All REQ-1 through REQ-9_

---

## Summary

**Total Tasks**: 75 atomic tasks organized into 11 phases
**Estimated Total Time**: 19-38 hours (assuming 15-30 min per task)

**Phase Breakdown**:
1. Project Setup (5 tasks)
2. Data Layer (6 tasks)
3. Storage Layer (8 tasks)
4. Backtest Engine (8 tasks)
5. Input Handler (7 tasks)
6. Learning Engine (6 tasks)
7. Analysis Engine (8 tasks)
8. Comparison Engine (6 tasks)
9. Notification & UI Support (4 tasks)
10. Streamlit UI (10 tasks)
11. Integration & Testing (7 tasks)

**Key Achievements**:
-  All 9 requirements fully covered
-  All 9 design components implemented
-  Comprehensive testing at unit, integration, and E2E levels
-  Complete UI with 7 screens
-  Learning engine with pattern recognition
-  AI suggestions with fallback rules
-  Multi-strategy comparison
-  Bilingual support (zh-TW, en-US)
-  Performance benchmarking
-  Production-ready documentation
