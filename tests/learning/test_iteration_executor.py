"""
Tests for Phase 6 IterationExecutor (Task 5.3)

Tests the 10-step iteration execution process:
1. Load recent history
2. Generate feedback
3. Decide LLM or Factor Graph
4. Generate strategy
5. Execute strategy
6. Extract metrics
7. Classify success
8. Update champion if better
9. Create IterationRecord
10. Return record
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from src.backtest.executor import ExecutionResult
from src.learning.iteration_executor import IterationExecutor
from src.learning.iteration_history import IterationRecord


@pytest.fixture
def mock_components():
    """Create mock components for IterationExecutor."""
    return {
        'llm_client': Mock(),
        'feedback_generator': Mock(),
        'backtest_executor': Mock(),
        'champion_tracker': Mock(),
        'history': Mock(),
        'config': {
            'innovation_rate': 100,
            'history_window': 5,
            'timeout_seconds': 420,
            'start_date': '2018-01-01',
            'end_date': '2024-12-31',
            'fee_ratio': 0.001425,
            'tax_ratio': 0.003,
            'resample': 'M',
        }
    }


@pytest.fixture
def executor(mock_components):
    """Create IterationExecutor with mocked dependencies."""
    return IterationExecutor(**mock_components)


class TestIterationExecutorInitialization:
    """Test IterationExecutor initialization."""

    def test_initialization_success(self, mock_components):
        """Test successful initialization with all components."""
        executor = IterationExecutor(**mock_components)

        assert executor.llm_client == mock_components['llm_client']
        assert executor.feedback_generator == mock_components['feedback_generator']
        assert executor.backtest_executor == mock_components['backtest_executor']
        assert executor.champion_tracker == mock_components['champion_tracker']
        assert executor.history == mock_components['history']
        assert executor.config == mock_components['config']

    def test_metrics_extractor_initialized(self, executor):
        """Test MetricsExtractor is initialized."""
        assert hasattr(executor, 'metrics_extractor')
        assert executor.metrics_extractor is not None

    def test_error_classifier_initialized(self, executor):
        """Test ErrorClassifier is initialized."""
        assert hasattr(executor, 'error_classifier')
        assert executor.error_classifier is not None


class TestLoadRecentHistory:
    """Test Step 1: Load recent history."""

    def test_load_empty_history(self, executor):
        """Test loading history when no records exist."""
        executor.history.get_all.return_value = []

        recent = executor._load_recent_history(window=5)

        assert recent == []
        executor.history.get_all.assert_called_once()

    def test_load_recent_history_within_window(self, executor):
        """Test loading history with fewer records than window."""
        records = [
            Mock(iteration_num=0),
            Mock(iteration_num=1),
            Mock(iteration_num=2),
        ]
        executor.history.get_all.return_value = records

        recent = executor._load_recent_history(window=5)

        assert len(recent) == 3
        assert recent == records

    def test_load_recent_history_exceeds_window(self, executor):
        """Test loading history with more records than window."""
        records = [Mock(iteration_num=i) for i in range(10)]
        executor.history.get_all.return_value = records

        recent = executor._load_recent_history(window=5)

        assert len(recent) == 5
        assert recent == records[-5:]  # Last 5 records

    def test_load_history_handles_exception(self, executor):
        """Test loading history handles exceptions gracefully."""
        executor.history.get_all.side_effect = Exception("Database error")

        recent = executor._load_recent_history(window=5)

        assert recent == []  # Returns empty list on error


class TestGenerateFeedback:
    """Test Step 2: Generate feedback."""

    def test_generate_feedback_success(self, executor):
        """Test successful feedback generation."""
        records = [Mock()]
        executor.feedback_generator.generate.return_value = "Test feedback"

        feedback = executor._generate_feedback(records, iteration_num=5)

        assert feedback == "Test feedback"
        executor.feedback_generator.generate.assert_called_once_with(
            history=records,
            iteration_num=5
        )

    def test_generate_feedback_failure_returns_fallback(self, executor):
        """Test feedback generation failure returns fallback message."""
        executor.feedback_generator.generate.side_effect = Exception("LLM error")

        feedback = executor._generate_feedback([], iteration_num=0)

        assert "No feedback available" in feedback


class TestDecideGenerationMethod:
    """Test Step 3: Decide LLM or Factor Graph."""

    def test_innovation_rate_100_always_llm(self, executor):
        """Test innovation_rate=100 always chooses LLM."""
        executor.config['innovation_rate'] = 100

        results = [executor._decide_generation_method() for _ in range(10)]

        assert all(results), "All iterations should use LLM"

    def test_innovation_rate_0_always_factor_graph(self, executor):
        """Test innovation_rate=0 always chooses Factor Graph."""
        executor.config['innovation_rate'] = 0

        results = [executor._decide_generation_method() for _ in range(10)]

        assert not any(results), "All iterations should use Factor Graph"

    def test_innovation_rate_50_mixed(self, executor):
        """Test innovation_rate=50 produces mixed results."""
        executor.config['innovation_rate'] = 50

        results = [executor._decide_generation_method() for _ in range(100)]

        llm_count = sum(results)
        # Should be roughly 50%, allow 30-70% range for randomness
        assert 30 <= llm_count <= 70, f"Expected ~50 LLM calls, got {llm_count}"


class TestGenerateWithLLM:
    """Test Step 4: Generate strategy with LLM."""

    def test_llm_generation_success(self, executor):
        """Test successful LLM strategy generation."""
        engine = Mock()
        engine.generate_strategy.return_value = {"code": "# Strategy code"}
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = engine

        code, strategy_id, generation = executor._generate_with_llm("feedback", 0)

        assert code == "# Strategy code"
        assert strategy_id is None
        assert generation is None
        engine.generate_strategy.assert_called_once_with("feedback")

    def test_llm_disabled_fallback_to_factor_graph(self, executor):
        """Test LLM disabled falls back to Factor Graph."""
        executor.llm_client.is_enabled.return_value = False

        code, strategy_id, generation = executor._generate_with_llm("feedback", 0)

        # Should return Factor Graph placeholder
        assert code is None
        assert strategy_id is not None
        assert "fallback" in strategy_id

    def test_llm_engine_unavailable_fallback(self, executor):
        """Test LLM engine unavailable falls back to Factor Graph."""
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = None

        code, strategy_id, generation = executor._generate_with_llm("feedback", 0)

        assert code is None
        assert strategy_id is not None

    def test_llm_empty_response_fallback(self, executor):
        """Test LLM empty response falls back to Factor Graph."""
        engine = Mock()
        engine.generate_strategy.return_value = {}  # Empty response
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = engine

        code, strategy_id, generation = executor._generate_with_llm("feedback", 0)

        assert code is None
        assert strategy_id is not None

    def test_llm_exception_fallback(self, executor):
        """Test LLM exception falls back to Factor Graph."""
        engine = Mock()
        engine.generate_strategy.side_effect = Exception("API error")
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = engine

        code, strategy_id, generation = executor._generate_with_llm("feedback", 0)

        assert code is None
        assert strategy_id is not None


class TestGenerateWithFactorGraph:
    """Test Step 4: Generate strategy with Factor Graph."""

    def test_factor_graph_returns_placeholder(self, executor):
        """Test Factor Graph returns placeholder (not yet implemented)."""
        code, strategy_id, generation = executor._generate_with_factor_graph(5)

        assert code is None
        assert strategy_id is not None
        assert "fallback" in strategy_id
        assert generation == 0


class TestExecuteStrategy:
    """Test Step 5: Execute strategy."""

    def test_execute_llm_strategy_success(self, executor):
        """Test successful LLM strategy execution."""
        success_result = ExecutionResult(
            success=True,
            report={'sharpe_ratio': 1.5},
            execution_time=10.0
        )
        executor.backtest_executor.execute_code.return_value = success_result

        result = executor._execute_strategy(
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            generation_method="llm"
        )

        assert result.success is True
        executor.backtest_executor.execute_code.assert_called_once()

    def test_execute_factor_graph_not_implemented(self, executor):
        """Test Factor Graph execution returns not implemented error."""
        result = executor._execute_strategy(
            strategy_code=None,
            strategy_id="test_strategy",
            strategy_generation=1,
            generation_method="factor_graph"
        )

        assert result.success is False
        assert "NotImplementedError" in result.error_type

    def test_execute_invalid_method_returns_error(self, executor):
        """Test invalid generation method returns error."""
        result = executor._execute_strategy(
            strategy_code=None,
            strategy_id=None,
            strategy_generation=None,
            generation_method="invalid"
        )

        assert result.success is False
        assert "ValueError" in result.error_type

    def test_execute_exception_returns_error_result(self, executor):
        """Test execution exception returns error result."""
        executor.backtest_executor.execute_code.side_effect = Exception("Timeout")

        result = executor._execute_strategy(
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            generation_method="llm"
        )

        assert result.success is False
        assert result.error_type == "Exception"
        assert "Timeout" in result.error_message


class TestExtractMetrics:
    """Test Step 6: Extract metrics."""

    def test_extract_metrics_success(self, executor):
        """Test successful metrics extraction."""
        success_result = ExecutionResult(
            success=True,
            report={'returns': [0.01, 0.02, -0.01]},
            execution_time=10.0
        )
        executor.metrics_extractor.extract.return_value = {
            'sharpe_ratio': 1.5,
            'total_return': 0.15,
            'max_drawdown': -0.05
        }

        metrics = executor._extract_metrics(success_result)

        assert metrics['sharpe_ratio'] == 1.5
        assert metrics['total_return'] == 0.15
        assert metrics['max_drawdown'] == -0.05

    def test_extract_metrics_failure_returns_empty(self, executor):
        """Test failed execution returns empty metrics."""
        failure_result = ExecutionResult(
            success=False,
            error_type="SyntaxError",
            error_message="Invalid syntax",
            execution_time=0.0
        )

        metrics = executor._extract_metrics(failure_result)

        assert metrics == {}

    def test_extract_metrics_exception_returns_empty(self, executor):
        """Test metrics extraction exception returns empty dict."""
        success_result = ExecutionResult(success=True, report={}, execution_time=10.0)
        executor.metrics_extractor.extract.side_effect = Exception("Extract error")

        metrics = executor._extract_metrics(success_result)

        assert metrics == {}


class TestClassifyResult:
    """Test Step 7: Classify success."""

    def test_classify_level_3_success(self, executor):
        """Test LEVEL_3 classification for success."""
        result = ExecutionResult(success=True, report={}, execution_time=10.0)
        metrics = {'sharpe_ratio': 1.5}
        executor.error_classifier.classify.return_value = "LEVEL_3"

        level = executor._classify_result(result, metrics)

        assert level == "LEVEL_3"
        executor.error_classifier.classify.assert_called_once()

    def test_classify_level_0_failure(self, executor):
        """Test LEVEL_0 classification for failure."""
        result = ExecutionResult(success=False, error_type="SyntaxError", error_message="", execution_time=0)
        metrics = {}
        executor.error_classifier.classify.return_value = "LEVEL_0"

        level = executor._classify_result(result, metrics)

        assert level == "LEVEL_0"

    def test_classify_exception_returns_level_0(self, executor):
        """Test classification exception returns LEVEL_0."""
        result = ExecutionResult(success=True, report={}, execution_time=10.0)
        executor.error_classifier.classify.side_effect = Exception("Classify error")

        level = executor._classify_result(result, {})

        assert level == "LEVEL_0"


class TestUpdateChampionIfBetter:
    """Test Step 8: Update champion if better."""

    def test_update_champion_level_3_with_high_sharpe(self, executor):
        """Test champion updated for LEVEL_3 with high Sharpe."""
        executor.champion_tracker.update_champion.return_value = True

        updated = executor._update_champion_if_better(
            iteration_num=5,
            generation_method="llm",
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            metrics={'sharpe_ratio': 2.0},
            classification_level="LEVEL_3"
        )

        assert updated is True
        executor.champion_tracker.update_champion.assert_called_once()

    def test_no_update_for_level_0(self, executor):
        """Test champion not updated for LEVEL_0."""
        updated = executor._update_champion_if_better(
            iteration_num=5,
            generation_method="llm",
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            metrics={},
            classification_level="LEVEL_0"
        )

        assert updated is False
        executor.champion_tracker.update_champion.assert_not_called()

    def test_no_update_for_missing_sharpe(self, executor):
        """Test champion not updated when Sharpe missing."""
        updated = executor._update_champion_if_better(
            iteration_num=5,
            generation_method="llm",
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            metrics={'total_return': 0.5},  # No sharpe_ratio
            classification_level="LEVEL_3"
        )

        assert updated is False
        executor.champion_tracker.update_champion.assert_not_called()

    def test_update_champion_exception_returns_false(self, executor):
        """Test champion update exception returns False."""
        executor.champion_tracker.update_champion.side_effect = Exception("Update error")

        updated = executor._update_champion_if_better(
            iteration_num=5,
            generation_method="llm",
            strategy_code="# code",
            strategy_id=None,
            strategy_generation=None,
            metrics={'sharpe_ratio': 2.0},
            classification_level="LEVEL_3"
        )

        assert updated is False


class TestExecuteIterationFullFlow:
    """Test complete iteration execution (Steps 1-10)."""

    def test_full_iteration_llm_success(self, executor):
        """Test complete successful LLM iteration."""
        # Setup mocks for successful LLM flow
        executor.history.get_all.return_value = []
        executor.feedback_generator.generate.return_value = "feedback"

        # LLM generation
        engine = Mock()
        engine.generate_strategy.return_value = {"code": "# Strategy"}
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = engine

        # Execution
        executor.backtest_executor.execute_code.return_value = ExecutionResult(
            success=True,
            report={'returns': [0.01]},
            execution_time=10.0
        )

        # Metrics
        executor.metrics_extractor.extract.return_value = {'sharpe_ratio': 1.5}

        # Classification
        executor.error_classifier.classify.return_value = "LEVEL_3"

        # Champion
        executor.champion_tracker.update_champion.return_value = True

        # Execute iteration
        record = executor.execute_iteration(iteration_num=0)

        # Verify record
        assert isinstance(record, IterationRecord)
        assert record.iteration_num == 0
        assert record.generation_method == "llm"
        assert record.strategy_code == "# Strategy"
        assert record.classification_level == "LEVEL_3"
        assert record.champion_updated is True
        assert 'sharpe_ratio' in record.metrics

    def test_full_iteration_llm_failure(self, executor):
        """Test complete LLM iteration with execution failure."""
        executor.history.get_all.return_value = []
        executor.feedback_generator.generate.return_value = "feedback"

        # LLM generation
        engine = Mock()
        engine.generate_strategy.return_value = {"code": "# Bad code"}
        executor.llm_client.is_enabled.return_value = True
        executor.llm_client.get_engine.return_value = engine

        # Execution failure
        executor.backtest_executor.execute_code.return_value = ExecutionResult(
            success=False,
            error_type="SyntaxError",
            error_message="Invalid code",
            execution_time=0.0
        )

        # Classification
        executor.error_classifier.classify.return_value = "LEVEL_0"

        # Execute iteration
        record = executor.execute_iteration(iteration_num=1)

        # Verify record
        assert record.iteration_num == 1
        assert record.classification_level == "LEVEL_0"
        assert record.champion_updated is False
        assert record.metrics == {}

    def test_full_iteration_factor_graph_placeholder(self, executor):
        """Test complete Factor Graph iteration (placeholder)."""
        executor.config['innovation_rate'] = 0  # Force Factor Graph
        executor.history.get_all.return_value = []

        # Execute iteration
        record = executor.execute_iteration(iteration_num=2)

        # Verify record
        assert record.generation_method == "factor_graph"
        assert record.strategy_code is None
        assert record.strategy_id is not None
        # Note: Will fail execution (not implemented) but shouldn't crash


class TestCreateFailureRecord:
    """Test failure record creation."""

    def test_create_failure_record_structure(self, executor):
        """Test failure record has correct structure."""
        start_time = datetime.now()
        record = executor._create_failure_record(
            iteration_num=5,
            generation_method="llm",
            error_message="Test error",
            start_time=start_time
        )

        assert isinstance(record, IterationRecord)
        assert record.iteration_num == 5
        assert record.generation_method == "llm"
        assert record.classification_level == "LEVEL_0"
        assert record.champion_updated is False
        assert record.strategy_code is None
        assert "success" in record.execution_result
        assert record.execution_result["success"] is False
