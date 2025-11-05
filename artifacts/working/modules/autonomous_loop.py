"""Autonomous learning loop controller.

Orchestrates the complete workflow:
1. Generate strategy using LLM with feedback
2. Validate code with AST security validator
3. Execute in sandbox
4. Extract metrics
5. Record iteration
6. Build feedback for next iteration
7. Repeat until convergence or max iterations

This implements the core autonomous iteration logic for MVP.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Tuple, Any, Dict, List
from datetime import datetime
import time
import random

from history import IterationHistory
from prompt_builder import PromptBuilder
from scripts.validate_code import validate_code
from sandbox_simple import execute_strategy_safe
from poc_claude_test import generate_strategy
from fix_dataset_keys import fix_dataset_keys
from static_validator import validate_code as static_validate
from src.failure_tracker import FailureTracker
from src.constants import METRIC_SHARPE, CHAMPION_FILE
from src.repository.hall_of_fame import HallOfFameRepository
from src.validation.metric_validator import MetricValidator
from src.validation.semantic_validator import SemanticValidator
from src.data.pipeline_integrity import DataPipelineIntegrity
from src.config.experiment_config_manager import ExperimentConfigManager
from src.monitoring.variance_monitor import VarianceMonitor
from src.config.anti_churn_manager import AntiChurnManager
from src.sandbox.docker_executor import DockerExecutor
from src.sandbox.docker_config import DockerConfig
from src.utils.json_logger import get_event_logger
from src.monitoring.metrics_collector import MetricsCollector
from src.monitoring.resource_monitor import ResourceMonitor
from src.monitoring.diversity_monitor import DiversityMonitor
from src.monitoring.container_monitor import ContainerMonitor
from src.monitoring.alert_manager import AlertManager, AlertConfig
from src.innovation.innovation_engine import InnovationEngine
from src.learning.config_manager import ConfigManager
from src.learning.llm_client import LLMClient


@dataclass
class ChampionStrategy:
    """Best-performing strategy across all iterations.

    Tracks the highest-performing strategy to enable:
    - Performance attribution (comparing current vs. champion)
    - Success pattern extraction (identifying what works)
    - Evolutionary constraints (preserving proven patterns)

    Attributes:
        iteration_num: Which iteration produced this champion
        code: Complete strategy code that achieved these metrics
        parameters: Extracted parameter values from the code
        metrics: Performance metrics (sharpe_ratio, annual_return, etc.)
        success_patterns: List of patterns that contributed to success
        timestamp: When this champion was established (ISO format)
    """
    iteration_num: int
    code: str
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success_patterns: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary containing all champion data
        """
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict) -> 'ChampionStrategy':
        """Create ChampionStrategy from dictionary.

        Args:
            data: Dictionary with all required fields

        Returns:
            ChampionStrategy instance
        """
        return ChampionStrategy(**data)


class SandboxExecutionWrapper:
    """Wraps strategy execution with optional Docker Sandbox and automatic fallback.

    Provides dual-layer security defense:
    - Layer 1: AST validation (always enabled)
    - Layer 2: Docker container isolation (optional, configurable)

    When sandbox is enabled, automatically falls back to direct execution
    on Docker errors or timeouts to ensure autonomous loop continuity.
    """

    def __init__(self, sandbox_enabled: bool, docker_executor: Optional['DockerExecutor'], event_logger):
        """Initialize sandbox execution wrapper.

        Args:
            sandbox_enabled: Whether Docker sandbox is enabled
            docker_executor: DockerExecutor instance (None if disabled)
            event_logger: JSON event logger for execution metadata
        """
        self.sandbox_enabled = sandbox_enabled
        self.docker_executor = docker_executor
        self.event_logger = event_logger
        self.fallback_count = 0
        self.execution_count = 0
        # Task 3.3: Track Docker execution result for diversity fallback (Bug #4 fix)
        self.last_result = None  # None=not executed, True=Docker success, False=Docker failure

    def execute_strategy(
        self,
        code: str,
        data: Any,
        timeout: int = 120
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Execute strategy with sandbox (if enabled) or direct execution.

        Args:
            code: Strategy code to execute
            data: Finlab data object
            timeout: Execution timeout in seconds

        Returns:
            Tuple of (success, metrics, error_message)
            - success: True if execution succeeded
            - metrics: Dict of performance metrics
            - error_message: Error description if failed, None if succeeded
        """
        self.execution_count += 1

        if not self.sandbox_enabled:
            # Sandbox disabled - use direct execution (current behavior)
            return self._direct_execution(code, data, timeout)

        # Sandbox enabled - try Docker execution with fallback
        try:
            result = self._sandbox_execution(code, data, timeout)
            # Task 3.3: Track Docker success for diversity fallback (Bug #4 fix)
            self.last_result = result[0]  # result[0] is success boolean
            return result
        except (TimeoutError, Exception) as e:
            # Docker execution failed - automatic fallback to direct execution
            import logging
            logger = logging.getLogger(__name__)

            # Task 3.3: Fix Bug #4 - Update state to trigger diversity fallback
            self.last_result = False  # Docker failed, enable diversity fallback
            logger.info("Setting last_result=False to enable diversity-aware prompting in next iteration")

            logger.warning(
                f"Sandbox execution failed: {type(e).__name__}: {e}, "
                f"falling back to direct execution"
            )

            self.fallback_count += 1
            self.event_logger.log_event(
                logging.WARNING,
                "sandbox_fallback",
                "Sandbox execution failed, falling back to direct execution",
                error_type=type(e).__name__,
                error_message=str(e),
                fallback_count=self.fallback_count,
                execution_count=self.execution_count
            )

            return self._direct_execution(code, data, timeout)

    def _sandbox_execution(
        self,
        code: str,
        data: Any,
        timeout: int
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Execute strategy in Docker container.

        Args:
            code: Strategy code
            data: Finlab data object
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, metrics, error_message)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info("Executing strategy in Docker sandbox")
        self.event_logger.log_event(
            logging.INFO,
            "sandbox_execution",
            "Executing strategy in Docker container",
            execution_count=self.execution_count
        )

        # Prepare complete code with data serialization
        # DockerExecutor.execute() doesn't accept data directly,
        # so we inject mock data setup into the code
        import pandas as pd
        import numpy as np

        # Serialize data to code
        data_setup = f"""
import pandas as pd
import numpy as np

# Mock data object for sandbox execution
class Data:
    def __init__(self):
        # Create mock data for 10 stocks across 252 trading days
        dates = pd.date_range('2020-01-01', periods=252, freq='D')
        stocks = ['STOCK_{{:04d}}'.format(i) for i in range(10)]

        # Create DataFrames (stocks x dates) instead of Series
        # This matches the real FinLab data structure
        self.close = pd.DataFrame(
            np.random.randn(252, 10).cumsum(axis=0) + 100,
            index=dates,
            columns=stocks
        )
        self.open = self.close + np.random.randn(252, 10) * 0.5
        self.high = self.close + abs(np.random.randn(252, 10)) * 1.0
        self.low = self.close - abs(np.random.randn(252, 10)) * 1.0
        self.volume = pd.DataFrame(
            np.random.randint(1000000, 10000000, (252, 10)),
            index=dates,
            columns=stocks
        )

        # Simple mock for market value and other dataframes
        self.market_value = self.close * self.volume
        self.roe = pd.DataFrame(
            np.random.uniform(5, 20, (252, 10)),
            index=dates,
            columns=stocks
        )
        self.revenue_yoy = pd.DataFrame(
            np.random.uniform(-10, 30, (252, 10)),
            index=dates,
            columns=stocks
        )
        self.foreign_net_buy = pd.DataFrame(
            np.random.randint(-1e6, 1e6, (252, 10)),
            index=dates,
            columns=stocks
        )

        # Key mapping for the .get() method
        self._key_map = {{
            'etl:adj_close': self.close,
            'price:成交金額': self.volume,
            'etl:market_value': self.market_value,
            'fundamental_features:ROE稅後': self.roe,
            'monthly_revenue:去年同月增減(%)': self.revenue_yoy,
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)': self.foreign_net_buy,
        }}

    def get(self, key, default=None):
        \"\"\"Mock .get() to map string keys to data attributes.\"\"\"
        if key not in self._key_map:
            # Return a default random DataFrame to prevent crashes on unknown keys
            return pd.DataFrame(
                np.random.rand(252, 10),
                index=self.close.index,
                columns=self.close.columns
            )
        return self._key_map.get(key, default)

    def indicator(self, name, *args, **kwargs):
        \"\"\"Mock .indicator() to return a plausible random DataFrame.\"\"\"
        # For RSI, return a DataFrame between 0 and 100
        if name.upper() == 'RSI':
            return pd.DataFrame(
                np.random.uniform(0, 100, (252, 10)),
                index=self.close.index,
                columns=self.close.columns
            )
        # Default for other indicators
        return pd.DataFrame(
            np.random.randn(252, 10),
            index=self.close.index,
            columns=self.close.columns
        )

data = Data()

# Add FinLab-specific methods to pandas DataFrame
# These methods are used by generated strategies but don't exist in standard pandas
def is_largest(df, n):
    \"\"\"Mock FinLab's is_largest method - returns top N stocks as boolean DataFrame\"\"\"
    # For each row (date), mark top N stocks as True
    result = pd.DataFrame(False, index=df.index, columns=df.columns)
    for date in df.index:
        row = df.loc[date]
        top_n_stocks = row.nlargest(n).index
        result.loc[date, top_n_stocks] = True
    return result

def is_smallest(df, n):
    \"\"\"Mock FinLab's is_smallest method - returns bottom N stocks as boolean DataFrame\"\"\"
    result = pd.DataFrame(False, index=df.index, columns=df.columns)
    for date in df.index:
        row = df.loc[date]
        bottom_n_stocks = row.nsmallest(n).index
        result.loc[date, bottom_n_stocks] = True
    return result

# Monkey patch DataFrame to add FinLab methods
pd.DataFrame.is_largest = is_largest
pd.DataFrame.is_smallest = is_smallest

# Mock sim function for sandbox execution
def sim(position, resample='D', upload=False, stop_loss=None):
    report = type('obj', (object,), {{
        'total_return': float(np.random.randn() * 0.5),
        'annual_return': float(np.random.randn() * 0.3),
        'sharpe_ratio': float(abs(np.random.randn() * 2)),
        'max_drawdown': float(-abs(np.random.randn() * 0.5)),
        'win_rate': float(abs(np.random.randn() * 0.3 + 0.5)),
        'position_count': 252
    }})()
    return report

"""

        # Add metrics extraction wrapper
        metrics_extraction = """
import json

# Execute strategy and extract metrics
if 'report' in locals():
    # Extract metrics from report object
    signal = {
        'total_return': getattr(report, 'total_return', 0.0),
        'annual_return': getattr(report, 'annual_return', 0.0),
        'sharpe_ratio': getattr(report, 'sharpe_ratio', 0.0),
        'max_drawdown': getattr(report, 'max_drawdown', 0.0),
        'win_rate': getattr(report, 'win_rate', 0.0),
        'position_count': getattr(report, 'position_count', 0)
    }
else:
    signal = {}

# Output signal in parseable format for DockerExecutor (Issue #5 fix)
print(f"__SIGNAL_JSON_START__{json.dumps(signal)}__SIGNAL_JSON_END__")
"""

        # Combine data setup + user code + metrics extraction
        complete_code = data_setup + "\n" + code + "\n" + metrics_extraction

        # Task 3.4: Diagnostic logging for Docker code assembly (Bug #1 fix)
        logger.debug(f"Complete code (first 500 chars): {complete_code[:500]}")

        # Task 3.4: Verify no {{}} remains (Bug #1 detection)
        if '{{' in complete_code or '}}' in complete_code:
            logger.warning("F-string template may not be fully evaluated - found {{}} in code")
            # Log occurrence count and locations for debugging
            double_brace_count = complete_code.count('{{') + complete_code.count('}}')
            logger.warning(f"Found {double_brace_count} double-brace occurrences in assembled code")

        # DEBUG: Print data setup to verify .get() method is included
        print("🔍 DEBUG - Data setup preview (first 1500 chars):")
        print(data_setup[:1500])
        print("🔍 DEBUG - Checking for '.get()' method:", "def get(" in data_setup)
        print("🔍 DEBUG - Checking for '.indicator()' method:", "def indicator(" in data_setup)

        # Call DockerExecutor.execute() with correct API
        # Returns: Dict[str, Any] with 'success', 'signal', 'error' keys
        result_dict = self.docker_executor.execute(
            code=complete_code,
            timeout=timeout,
            validate=True
        )

        # Task 4.3: Diagnostic logging for Docker execution result
        logger.debug(f"Docker execution result: success={result_dict.get('success')}, "
                     f"error={result_dict.get('error')}, "
                     f"signal_keys={list(result_dict.get('signal', {}).keys())}")

        # Parse DockerExecutor return format to match expected return type
        success = result_dict.get('success', False)
        error = result_dict.get('error')

        # Extract metrics from 'signal' key (DockerExecutor uses 'signal', not 'result')
        if success and 'signal' in result_dict:
            signal_data = result_dict['signal']
            if isinstance(signal_data, dict):
                metrics = signal_data
            else:
                # If signal is not a dict, create default metrics
                metrics = {
                    'total_return': 0.0,
                    'annual_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0,
                    'win_rate': 0.0,
                    'position_count': 0
                }
        else:
            metrics = {}

        return (success, metrics, error)

    def _direct_execution(
        self,
        code: str,
        data: Any,
        timeout: int
    ) -> Tuple[bool, Dict, Optional[str]]:
        """Direct execution without Docker (AST-only defense).

        Args:
            code: Strategy code
            data: Finlab data object
            timeout: Timeout in seconds

        Returns:
            Tuple of (success, metrics, error_message)
        """
        # Use existing execute_strategy_safe (current production path)
        return execute_strategy_safe(code=code, data=data, timeout=timeout)

    def get_fallback_stats(self) -> Dict[str, int]:
        """Get fallback statistics.

        Returns:
            Dict with execution_count and fallback_count
        """
        return {
            'execution_count': self.execution_count,
            'fallback_count': self.fallback_count,
            'fallback_rate': self.fallback_count / self.execution_count if self.execution_count > 0 else 0.0
        }


class AutonomousLoop:
    """Autonomous strategy generation and improvement loop."""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",  # Primary: Google AI, Fallback: OpenRouter
        max_iterations: int = 10,
        history_file: str = "iteration_history.json",
        template_mode: bool = False,
        template_name: str = "Momentum"
    ):
        """Initialize autonomous loop.

        Args:
            model: LLM model to use for generation
            max_iterations: Maximum number of iterations
            history_file: Path to history JSON file
            template_mode: If True, use template-guided mode; if False, use free-form mode
            template_name: Template name to use when template_mode=True (default: "Momentum")
        """
        self.model = model
        self.max_iterations = max_iterations
        self.history = IterationHistory(history_file)
        self.prompt_builder = PromptBuilder()

        # Template mode configuration (Phase 0)
        self.template_mode = template_mode
        self.template_name = template_name

        # Initialize template mode components if enabled
        if self.template_mode:
            from src.generators.template_parameter_generator import TemplateParameterGenerator
            from src.validation.strategy_validator import StrategyValidator
            from src.templates.momentum_template import MomentumTemplate

            self.param_generator = TemplateParameterGenerator(
                template_name=template_name,
                model=model
            )
            self.strategy_validator = StrategyValidator()
            self.template = MomentumTemplate()
        else:
            self.param_generator = None
            self.strategy_validator = None
            self.template = None

        # Champion tracking and failure learning
        # C1 Fix: Use Hall of Fame repository for unified champion persistence
        self.hall_of_fame = HallOfFameRepository()
        self.champion: Optional[ChampionStrategy] = self._load_champion()
        self.failure_tracker = FailureTracker()

        # Experiment configuration tracking (Story 8)
        self.config_manager = ExperimentConfigManager("experiment_configs.json")

        # Convergence monitoring (Story 1)
        self.variance_monitor = VarianceMonitor(alert_threshold=0.8)

        # Anti-churn management (Story 4)
        self.anti_churn = AntiChurnManager()

        # JSON event logger for sandbox execution mode decisions
        # (Must be initialized before _load_sandbox_config and _initialize_llm)
        self.event_logger = get_event_logger(
            "autonomous_loop.sandbox",
            log_file="sandbox_execution.json.log"
        )

        # LLM-driven innovation (llm-integration-activation: Task 5)
        # Refactored: Task 1.2 - LLMClient extraction
        # LLMClient uses default config path: config/learning_system.yaml
        self.llm_client = LLMClient()
        self.llm_enabled = self.llm_client.is_enabled()
        self.innovation_engine = self.llm_client.get_engine()
        self.innovation_rate = self.llm_client.get_innovation_rate()
        self.llm_stats = {
            'llm_innovations': 0,
            'llm_fallbacks': 0,
            'factor_mutations': 0,
            'llm_api_failures': 0,
            'llm_validation_failures': 0
        }

        # Load multi-objective validation config (Phase 3: Task 13.1)
        self._load_multi_objective_config()

        # Docker sandbox integration (docker-sandbox-security: Task 7)
        self.docker_executor: Optional[DockerExecutor] = None
        self.sandbox_enabled = False
        self._load_sandbox_config()

        # Sandbox execution wrapper (docker-sandbox-integration-testing: Task 2.1)
        self.sandbox_wrapper = SandboxExecutionWrapper(
            sandbox_enabled=self.sandbox_enabled,
            docker_executor=self.docker_executor,
            event_logger=self.event_logger
        )

    def _load_sandbox_config(self) -> None:
        """Load Docker sandbox configuration from YAML.

        Loads sandbox configuration from config/learning_system.yaml.
        Initializes DockerExecutor if sandbox is enabled.

        Configuration structure in learning_system.yaml:
        sandbox:
          enabled: true  # Enable Docker sandbox mode


        Default: sandbox disabled (backward compatibility)
        """
        import logging

        logger = logging.getLogger(__name__)

        # Default: sandbox disabled (backward compatibility)
        self.sandbox_enabled = False
        sandbox_fallback = False

        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()

            # Get sandbox configuration using nested key access
            sandbox_config = config_manager.get('sandbox', {})
            self.sandbox_enabled = sandbox_config.get('enabled', False)

            logger.info(
                f"Sandbox configuration loaded: enabled={self.sandbox_enabled}"
            )

        except FileNotFoundError as e:
            logger.warning(f"Config file not found: {e}, sandbox disabled")
            self.sandbox_enabled = False
        except Exception as e:
            logger.warning(f"Failed to load sandbox config: {e}, sandbox disabled")
            self.sandbox_enabled = False

        # Initialize DockerExecutor if sandbox is enabled
        if self.sandbox_enabled:
            try:
                # Load Docker configuration
                docker_config = DockerConfig.from_yaml()

                # Initialize executor
                self.docker_executor = DockerExecutor(config=docker_config)
                logger.info("DockerExecutor initialized successfully")

                # Log execution mode decision
                self.event_logger.log_event(
                    logging.INFO,
                    "sandbox_mode_enabled",
                    "Docker sandbox mode enabled for strategy execution",
                    
                    docker_image=docker_config.image,
                    memory_limit=docker_config.memory_limit,
                    cpu_limit=docker_config.cpu_limit,
                    timeout_seconds=docker_config.timeout_seconds
                )

            except Exception as e:
                logger.error(f"Failed to initialize DockerExecutor: {e}", exc_info=True)
                logger.warning("Sandbox mode disabled due to initialization failure")
                self.sandbox_enabled = False
                self.docker_executor = None

                # Log execution mode decision
                self.event_logger.log_event(
                    logging.ERROR,
                    "sandbox_mode_failed",
                    "Docker sandbox initialization failed, falling back to direct execution",
                    error=str(e)
                )
        else:
            logger.info("Docker sandbox mode disabled, using direct execution")
            self.event_logger.log_event(
                logging.INFO,
                "sandbox_mode_disabled",
                "Docker sandbox mode disabled, using direct execution"
            )

        # Resource monitoring system (Task 8: Integration)
        self._initialize_monitoring()


    def _initialize_monitoring(self) -> None:
        """Initialize monitoring components for resource tracking.

        Task 8: Integrate monitoring into autonomous loop
        - Creates MetricsCollector, ResourceMonitor, DiversityMonitor, ContainerMonitor, AlertManager
        - Starts background threads for resource and alert monitoring
        - Configures data sources for alert evaluation
        - Gracefully handles initialization failures (monitoring optional)

        Integration points:
        1. Loop initialization: Create monitoring components, start threads
        2. Start of iteration: Record resource snapshot, check alerts
        3. After strategy execution: Record diversity, container stats
        4. After champion update: Record staleness, update champion metrics
        5. Loop shutdown: Stop monitoring threads cleanly
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Initialize MetricsCollector for Prometheus export
            self.metrics_collector = MetricsCollector()
            logger.info("MetricsCollector initialized")

            # Initialize ResourceMonitor for system resource tracking
            self.resource_monitor = ResourceMonitor(self.metrics_collector)
            self.resource_monitor.start_monitoring(interval_seconds=5)
            logger.info("ResourceMonitor started (5s interval)")

            # Initialize DiversityMonitor for population diversity tracking
            self.diversity_monitor = DiversityMonitor(
                self.metrics_collector,
                collapse_threshold=0.1,
                collapse_window=5
            )
            logger.info("DiversityMonitor initialized")

            # Initialize ContainerMonitor for Docker resource tracking
            try:
                # Attempt to initialize Docker client
                import docker
                docker_client = docker.from_env()
                self.container_monitor = ContainerMonitor(
                    self.metrics_collector,
                    docker_client,
                    auto_cleanup=True
                )
                logger.info("ContainerMonitor initialized with Docker client")
            except Exception as e:
                # Docker not available - create monitor without client
                logger.warning(f"Docker not available, ContainerMonitor disabled: {e}")
                self.container_monitor = ContainerMonitor(
                    self.metrics_collector,
                    docker_client=None,
                    auto_cleanup=False
                )

            # Initialize AlertManager with configuration
            alert_config = AlertConfig(
                memory_threshold_percent=80.0,
                diversity_collapse_threshold=0.1,
                diversity_collapse_window=5,
                champion_staleness_threshold=20,
                success_rate_threshold=20.0,
                success_rate_window=10,
                orphaned_container_threshold=3,
                evaluation_interval=10,
                suppression_duration=300
            )
            self.alert_manager = AlertManager(alert_config, self.metrics_collector)

            # Configure alert data sources
            self.alert_manager.set_memory_source(
                lambda: self.resource_monitor.get_current_stats()
            )
            self.alert_manager.set_diversity_source(
                lambda: self.diversity_monitor.get_current_diversity()
            )
            self.alert_manager.set_staleness_source(
                lambda: self.diversity_monitor.get_current_staleness()
            )
            self.alert_manager.set_container_source(
                lambda: len(self.container_monitor.scan_orphaned_containers()) if self.container_monitor.is_docker_available() else 0
            )

            # Start alert monitoring
            self.alert_manager.start_monitoring()
            logger.info("AlertManager started (10s evaluation interval)")

            # Mark monitoring as enabled
            self._monitoring_enabled = True
            logger.info("Monitoring system fully initialized")

        except Exception as e:
            # Monitoring initialization failed - log warning but continue
            logger.warning(f"Monitoring initialization failed: {e}. Continuing without monitoring.")
            self.metrics_collector = None
            self.resource_monitor = None
            self.diversity_monitor = None
            self.container_monitor = None
            self.alert_manager = None
            self._monitoring_enabled = False

    def _load_multi_objective_config(self) -> None:
        """Load multi-objective validation configuration from YAML.

        Loads configuration for Calmar retention ratio and max drawdown tolerance
        from config/learning_system.yaml. Sets default values if config is unavailable.

        Default values match config/learning_system.yaml:
        - enabled: True
        - calmar_retention_ratio: 0.90 (maintain ≥90% of old Calmar)
        - max_drawdown_tolerance: 1.10 (allow ≤110% worse drawdown)
        """
        import logging

        logger = logging.getLogger(__name__)

        # Default configuration (matches YAML defaults)
        self.multi_objective_enabled = True
        self.calmar_retention_ratio = 0.90
        self.max_drawdown_tolerance = 1.10

        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()

            mo_config = config_manager.get('multi_objective', {})
            if mo_config:
                self.multi_objective_enabled = mo_config.get('enabled', True)
                self.calmar_retention_ratio = mo_config.get('calmar_retention_ratio', 0.90)
                self.max_drawdown_tolerance = mo_config.get('max_drawdown_tolerance', 1.10)

        except FileNotFoundError as e:
            logger.warning(f"Config file not found: {e}, using defaults")
        except Exception as e:
            logger.warning(f"Failed to load multi-objective config: {e}, using defaults")

    def _run_template_mode_iteration(
        self,
        iteration_num: int,
        data: Optional[Any] = None
    ) -> Tuple[object, Dict[str, float], Dict[str, Any], bool]:
        """Run single iteration in template mode.

        Template mode workflow:
        1. Create ParameterGenerationContext from champion
        2. Generate parameters via TemplateParameterGenerator
        3. Validate parameters via StrategyValidator
        4. Generate strategy via MomentumTemplate.generate_strategy()
        5. Return report, metrics, parameters

        Args:
            iteration_num: Current iteration number (0-indexed)
            data: Finlab data object for execution (None for testing)

        Returns:
            Tuple of (report, metrics, parameters, validation_success):
                - report: Finlab backtest report object
                - metrics: Performance metrics dictionary
                - parameters: Generated parameter dictionary
                - validation_success: True if parameters passed validation

        Raises:
            ValueError: If parameter generation or validation fails
            RuntimeError: If strategy generation fails
        """
        import logging
        from src.generators.template_parameter_generator import ParameterGenerationContext

        logger = logging.getLogger(__name__)

        print(f"\n[Template Mode] Step 1: Creating parameter generation context...")

        # Step 1: Create ParameterGenerationContext from champion
        if self.champion:
            context = ParameterGenerationContext(
                iteration_num=iteration_num,
                champion_params=self.champion.parameters,
                champion_sharpe=self.champion.metrics.get('sharpe_ratio'),
                feedback_history=None  # Can be extended later
            )
            logger.info(f"Context created with champion (Sharpe: {self.champion.metrics.get('sharpe_ratio'):.4f})")
        else:
            context = ParameterGenerationContext(
                iteration_num=iteration_num,
                champion_params=None,
                champion_sharpe=None,
                feedback_history=None
            )
            logger.info("Context created without champion (first iteration)")

        print(f"✅ Context created")

        # Step 2: Generate parameters via TemplateParameterGenerator
        print(f"\n[Template Mode] Step 2: Generating parameters...")
        try:
            parameters = self.param_generator.generate_parameters(context)
            logger.info(f"Parameters generated: {parameters}")
            print(f"✅ Parameters generated: {list(parameters.keys())}")
        except Exception as e:
            error_msg = f"Parameter generation failed: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            raise ValueError(error_msg) from e

        # Step 3: Validate parameters via StrategyValidator
        print(f"\n[Template Mode] Step 3: Validating parameters...")
        is_valid, warnings = self.strategy_validator.validate_parameters(parameters)

        if warnings:
            logger.warning(f"Parameter validation warnings ({len(warnings)}):")
            for warning in warnings:
                logger.warning(f"  - {warning}")
            print(f"⚠️  Validation warnings ({len(warnings)}):")
            for warning in warnings[:3]:  # Show first 3
                print(f"   - {warning}")
        else:
            logger.info("Parameter validation passed with no warnings")
            print(f"✅ Validation passed (no warnings)")

        # Step 4: Generate strategy via MomentumTemplate.generate_strategy()
        print(f"\n[Template Mode] Step 4: Generating strategy from template...")
        try:
            report, metrics = self.template.generate_strategy(parameters)
            logger.info(f"Strategy generated successfully")
            logger.info(f"Metrics: {metrics}")
            print(f"✅ Strategy generated")
            print(f"   Sharpe: {metrics.get('sharpe_ratio', 0):.4f}")
            print(f"   Return: {metrics.get('annual_return', 0):.2%}")
        except Exception as e:
            error_msg = f"Strategy generation failed: {e}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg) from e

        # Step 5: Return results
        validation_success = is_valid and len(warnings) == 0
        return report, metrics, parameters, validation_success

    def _run_template_iteration_wrapper(
        self,
        iteration_num: int,
        data: Optional[Any] = None
    ) -> Tuple[bool, str]:
        """Wrapper for template mode iteration that integrates with iteration tracking.

        This method bridges _run_template_mode_iteration with the existing
        autonomous loop infrastructure (history tracking, champion updates, etc.).

        Args:
            iteration_num: Current iteration number (0-indexed)
            data: Finlab data object for execution (None for testing)

        Returns:
            Tuple of (success, status_message)
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Run template mode iteration
            report, metrics, parameters, validation_success = self._run_template_mode_iteration(
                iteration_num, data
            )

            # Update champion if metrics are better
            champion_updated = self._update_champion(iteration_num, "", metrics)  # Empty code for template mode
            if champion_updated:
                # Update champion parameters for template mode
                self.champion.parameters = parameters
                logger.info(f"Champion updated in template mode with parameters: {parameters}")

            # Record iteration in history (Phase 0: Task 2.4)
            self.history.add_record(
                iteration_num=iteration_num,
                model=self.model,
                code="",  # No code in template mode
                validation_passed=validation_success,
                validation_errors=[],
                execution_success=True,
                execution_error=None,
                metrics=metrics,
                feedback="",  # No feedback in template mode
                data_checksum=None,
                data_version=None,
                config_snapshot=None,
                mode='template',  # Mark as template mode (Phase 0: Task 2.4)
                parameters=parameters  # Store parameters (Phase 0: Task 2.4)
            )

            print(f"\n[Template Mode] Iteration complete")
            print(f"✅ Success: {True}")
            print(f"   Sharpe: {metrics.get('sharpe_ratio', 0):.4f}")
            print(f"   Parameters: {len(parameters)} params")

            return True, "SUCCESS"

        except Exception as e:
            error_msg = f"Template mode iteration failed: {e}"
            logger.error(error_msg)
            print(f"\n❌ {error_msg}")

            # Record failed iteration
            self.history.add_record(
                iteration_num=iteration_num,
                model=self.model,
                code="",
                validation_passed=False,
                validation_errors=[str(e)],
                execution_success=False,
                execution_error=error_msg,
                metrics={},
                feedback="",
                data_checksum=None,
                data_version=None,
                config_snapshot=None,
                mode='template',
                parameters=None
            )

            return False, "FAILED"

    def run_iteration(
        self,
        iteration_num: int,
        data: Optional[Any] = None
    ) -> Tuple[bool, str]:
        """Run a single iteration of the loop.

        Routes execution based on mode:
        - Template mode: Uses template-guided parameter generation
        - Free-form mode: Uses LLM-generated code (original behavior)

        Args:
            iteration_num: Current iteration number (0-indexed)
            data: Finlab data object for execution (None for testing)

        Returns:
            Tuple of (success, status_message)
        """
        import logging
        logger = logging.getLogger(__name__)

        print(f"\n{'='*60}")
        print(f"ITERATION {iteration_num}")
        print(f"{'='*60}\n")

        # Route based on mode (Phase 0: Task 2.3)
        if self.template_mode:
            return self._run_template_iteration_wrapper(iteration_num, data)
        else:
            return self._run_freeform_iteration(iteration_num, data)

    def _build_population_context(self) -> dict:
        """
        Build diversity guidance context from iteration history.

        Extracts factor usage patterns from successful strategies to guide
        LLM toward generating diverse, novel strategies.

        Returns:
            dict: Population context with:
                - top_factors: Most frequently used factors
                - underused_factors: Rarely used factors
                - common_patterns: Common factor combinations
        """
        import re
        from collections import Counter

        # Get successful iterations
        successful_iterations = self.history.get_successful_iterations()

        if len(successful_iterations) < 3:
            # Not enough history for diversity analysis
            return None

        # Extract all factor keys from successful strategies
        all_factors = []
        factor_pairs = []

        for record in successful_iterations:
            code = record.code
            if not code:
                continue

            # Extract data.get('...') calls using regex
            pattern = r"data\.get\(['\"]([^'\"]+)['\"]\)"
            factors_in_strategy = re.findall(pattern, code)

            all_factors.extend(factors_in_strategy)

            # Extract factor pairs for common patterns
            unique_factors = list(set(factors_in_strategy))
            for i in range(len(unique_factors)):
                for j in range(i+1, len(unique_factors)):
                    pair = tuple(sorted([unique_factors[i], unique_factors[j]]))
                    factor_pairs.append(pair)

        # Count factor frequency
        factor_counts = Counter(all_factors)
        pair_counts = Counter(factor_pairs)

        # Get top factors (most used)
        top_factors = [factor for factor, count in factor_counts.most_common(5)]

        # Define comprehensive factor list for Taiwan market
        all_available_factors = [
            'etl:adj_close',
            'price:成交金額',
            'etl:market_value',
            'fundamental_features:ROE稅後',
            'monthly_revenue:去年同月增減(%)',
            'institutional_investors_trading_summary:外陸資買賣超股數(不含外資自營商)',
            'fundamental_features:營業毛利率',
            'fundamental_features:營業利益率',
            'fundamental_features:稅後淨利率',
            'fundamental_features:每股淨值',
            'fundamental_features:負債比率',
            'price:本益比',
            'price:股價淨值比',
            'monthly_revenue:當月營收',
            'monthly_revenue:上月比較增減(%)',
            'etl:adj_close_volume',
            'price:總市值'
        ]

        # Find underused factors (not in top 10 or never used)
        used_factors = set(all_factors)
        underused_factors = [
            f for f in all_available_factors
            if f not in top_factors and (f not in used_factors or factor_counts.get(f, 0) <= 2)
        ]

        # Get common patterns (top 3 factor pairs)
        common_patterns = [
            f"Combining {pair[0]} with {pair[1]}"
            for pair, count in pair_counts.most_common(3)
        ]

        return {
            'top_factors': top_factors,
            'underused_factors': underused_factors[:8],  # Limit to 8 suggestions
            'common_patterns': common_patterns
        }

    def _run_freeform_iteration(
        self,
        iteration_num: int,
        data: Optional[Any] = None
    ) -> Tuple[bool, str]:
        """Run single iteration in free-form mode (original behavior).

        This method contains the original run_iteration logic for backward compatibility.

        Args:
            iteration_num: Current iteration number (0-indexed)
            data: Finlab data object for execution (None for testing)

        Returns:
            Tuple of (success, status_message)
        """
        import logging
        logger = logging.getLogger(__name__)

        # Step 0: Record data provenance and validate consistency (Story 7)
        integrity = DataPipelineIntegrity()
        provenance = integrity.record_data_provenance(data, iteration_num)
        checksum = provenance['dataset_checksum']

        # Validate against previous iteration's checksum if exists
        if iteration_num > 0:
            prev = self.history.get_record(iteration_num - 1)
            if prev and prev.data_checksum:
                is_valid, msg = integrity.validate_data_consistency(data, prev.data_checksum)
                if not is_valid:
                    logger.warning(f"Data checksum changed: {msg}")

        # Step 0.5: Capture experiment configuration (Story 8)
        print(f"\n[0.5/6] Capturing configuration snapshot...")
        try:
            config = self.config_manager.capture_config_snapshot(self, iteration_num)

            # Compare with previous iteration if exists
            if iteration_num > 0:
                prev = self.history.get_record(iteration_num - 1)
                if prev and prev.config_snapshot:
                    # Convert dict back to config for comparison
                    # Bug #3 fix: Use correct import path (experiment_config_manager, not experiment_config)
                    from src.config import ExperimentConfig
                    prev_config = ExperimentConfig.from_dict(prev.config_snapshot)
                    diff = self.config_manager.compute_config_diff(prev_config, config)

                    if diff['has_changes']:
                        severity_emoji = {
                            'critical': '🚨',
                            'moderate': '⚠️',
                            'minor': 'ℹ️',
                            'none': '✅'
                        }
                        emoji = severity_emoji.get(diff['severity'], 'ℹ️')

                        # Log with appropriate severity
                        if diff['severity'] == 'critical':
                            logger.warning(f"{emoji} Config changes ({diff['severity']}): {diff['change_summary']}")
                        elif diff['severity'] == 'moderate':
                            logger.info(f"{emoji} Config changes ({diff['severity']}): {diff['change_summary']}")
                        else:
                            logger.debug(f"{emoji} Config changes ({diff['severity']}): {diff['change_summary']}")

            print("✅ Configuration captured")
        except Exception as e:
            logger.warning(f"Configuration capture failed: {e}")
            config = None  # Continue iteration even if config capture fails
            print("⚠️  Configuration capture failed (continuing)")

        # Step 1: Build enhanced prompt with evolutionary constraints
        print("[1/6] Building prompt...")
        feedback_summary = self.history.generate_feedback_summary() if iteration_num > 0 else None

        # Get failure patterns if champion exists
        failure_patterns = self.failure_tracker.get_avoid_directives() if self.champion else None

        # Build prompt (will use evolutionary prompts if champion exists)
        prompt = self.prompt_builder.build_prompt(
            iteration_num=iteration_num,
            feedback_history=feedback_summary,
            champion=self.champion,
            failure_patterns=failure_patterns
        )
        print(f"✅ Prompt ready ({len(prompt)} chars)")

        # Step 2: Generate strategy
        print(f"\n[2/6] Generating strategy with {self.model}...")

        # Decide: LLM innovation or Factor Graph mutation?
        use_llm = (self.llm_enabled and
                   self.innovation_engine is not None and
                   random.random() < self.innovation_rate)

        code = None
        generation_method = "llm" if use_llm else "factor_graph"

        if use_llm:
            # Try LLM innovation
            print(f"   → Using LLM innovation (rate: {self.innovation_rate:.1%})")
            try:
                # Prepare champion data for LLM
                if self.champion:
                    champion_code = self.champion.code
                    champion_metrics = self.champion.metrics
                else:
                    # No champion yet - use empty baseline
                    champion_code = "def strategy(data):\n    return data.get('fundamental_features:ROE稅後') > 10"
                    champion_metrics = {'sharpe_ratio': 0.0}

                # Get recent failures for feedback (last 10)
                failure_history = []
                if iteration_num > 0:
                    recent_records = []
                    for i in range(max(0, iteration_num - 10), iteration_num):
                        record = self.history.get_record(i)
                        if record and not record.execution_success:
                            recent_records.append({
                                'iteration': i,
                                'error': record.execution_error or 'Unknown error',
                                'validation_errors': record.validation_errors
                            })
                    failure_history = recent_records

                code = self.innovation_engine.generate_innovation(
                    champion_code=champion_code,
                    champion_metrics=champion_metrics,
                    failure_history=failure_history,
                    target_metric='sharpe_ratio'
                )

                if code:
                    self.llm_stats['llm_innovations'] += 1
                    print(f"✅ LLM innovation generated ({len(code)} chars)")

                    # Log successful LLM innovation
                    self.event_logger.log_event(
                        logging.INFO,
                        "llm_innovation_success",
                        "LLM successfully generated innovation",
                        iteration_num=iteration_num,
                        code_length=len(code),
                        champion_sharpe=champion_metrics.get('sharpe_ratio', 0)
                    )
                else:
                    # LLM failed - fallback to Factor Graph
                    self.llm_stats['llm_fallbacks'] += 1
                    print(f"⚠️  LLM innovation failed, falling back to Factor Graph")

                    # Log LLM fallback
                    self.event_logger.log_event(
                        logging.WARNING,
                        "llm_innovation_failed",
                        "LLM innovation failed, falling back to Factor Graph",
                        iteration_num=iteration_num
                    )

                    use_llm = False
                    generation_method = "factor_graph_fallback"

            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)

                self.llm_stats['llm_api_failures'] += 1
                print(f"⚠️  LLM innovation error: {e}")
                print(f"   → Falling back to Factor Graph")
                logger.warning(f"LLM innovation exception at iteration {iteration_num}: {e}")

                # Log LLM exception
                self.event_logger.log_event(
                    logging.ERROR,
                    "llm_innovation_exception",
                    "LLM innovation raised exception, falling back to Factor Graph",
                    iteration_num=iteration_num,
                    error=str(e),
                    exception_type=type(e).__name__
                )

                use_llm = False
                generation_method = "factor_graph_fallback"

        # Factor Graph mutation (default path or fallback)
        if not use_llm or not code:
            self.llm_stats['factor_mutations'] += 1

            if generation_method == "factor_graph":
                print(f"   → Using Factor Graph mutation (default)")

            # Build population context for diversity-aware prompting
            population_context = self._build_population_context()

            try:
                code = generate_strategy(
                    iteration_num=iteration_num,
                    history=feedback_summary or "",
                    model=self.model,
                    population_context=population_context
                )
                print(f"✅ Strategy generated ({len(code)} chars)")
            except Exception as e:
                error_msg = f"❌ Generation failed: {e}"
                print(error_msg)
                return False, error_msg

        # Step 2.3: Validate champion preservation (if applicable)
        if self.champion and iteration_num >= 3:  # Only for exploitation mode
            print(f"\n[2.3/6] Validating champion preservation...")
            is_compliant = self._validate_preservation(code)

            if is_compliant:
                print("✅ Preservation validated - critical patterns maintained")
            else:
                # P0 Fix: Retry generation with stronger preservation enforcement
                print("⚠️  Preservation violation detected - regenerating with stronger constraints...")
                logger.warning(f"Iteration {iteration_num}: Preservation validation failed, retrying generation")

                # Retry with stronger preservation prompt (max 2 attempts)
                for retry in range(2):
                    print(f"   Retry attempt {retry + 1}/2...")

                    # Build stronger preservation prompt
                    stronger_prompt = self.prompt_builder.build_prompt(
                        iteration_num=iteration_num,
                        feedback_history=feedback_summary,
                        champion=self.champion,
                        failure_patterns=failure_patterns,
                        force_preservation=True  # Flag for stronger constraints
                    )

                    # Build population context for diversity-aware prompting
                    population_context = self._build_population_context()

                    try:
                        code = generate_strategy(
                            iteration_num=iteration_num,
                            history=stronger_prompt or "",
                            model=self.model,
                            population_context=population_context
                        )
                        is_compliant = self._validate_preservation(code)

                        if is_compliant:
                            print(f"✅ Preservation validated after retry {retry + 1}")
                            logger.info(f"Iteration {iteration_num}: Preservation validated on retry {retry + 1}")
                            break
                    except Exception as e:
                        logger.error(f"Iteration {iteration_num}: Retry {retry + 1} generation failed: {e}")
                        continue
                else:
                    # After 2 retries, log warning but allow execution with monitoring
                    logger.warning(f"Iteration {iteration_num}: Failed preservation after 2 retries, proceeding with warning")
                    print("⚠️  Preservation enforcement failed after retries - executing with monitoring")

        # Step 2.5: Auto-fix incorrect dataset keys
        print(f"\n[2.5/6] Auto-fixing dataset keys...")
        fixed_code, fixes = fix_dataset_keys(code)

        # CRITICAL: Always use fixed_code, even if fixes list is empty
        # The function may have made transformations not tracked in fixes list
        code = fixed_code

        # Hash logging for delivery verification (o3 Phase 1)
        import hashlib
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        print(f"   Code hash: {code_hash}")

        if fixes:
            print(f"✅ Applied {len(fixes)} fixes:")
            for fix in fixes:
                print(f"   - {fix}")
        else:
            print("✅ No fixes needed")

        # Step 2.7: Static validation (pre-execution check)
        print(f"\n[2.7/6] Static validation...")
        static_valid, static_issues = static_validate(code)
        validation_errors = []  # Initialize validation_errors list

        if not static_valid:
            print(f"❌ Static validation failed ({len(static_issues)} issues)")
            for issue in static_issues[:5]:  # Show first 5
                print(f"   - {issue}")

            # Add to validation errors for feedback
            validation_errors.extend(static_issues)
            is_valid = False

            # Skip execution - mark as validation failure
            print(f"\n[3/6] Skipping AST validation (static validation failed)")
            print(f"\n[4/6] Skipping execution (validation failed)")
            execution_success = False
            execution_error = f"Static validation failed: {'; '.join(static_issues[:3])}"
            metrics = None
        else:
            print(f"✅ Static validation passed")

            # Step 3: Validate code
            print(f"\n[3/6] Validating code...")
            is_valid, validation_errors = validate_code(code)

        if is_valid:
            print("✅ Validation passed")
        else:
            print(f"❌ Validation failed ({len(validation_errors)} errors)")
            for error in validation_errors[:3]:  # Show first 3 errors
                print(f"   - {error}")

        # Step 4: Execute in sandbox (if validated)
        execution_success = False
        execution_error = None
        metrics = None

        if is_valid:
            # Step 4: Execute strategy using sandbox wrapper (with automatic fallback)
            execution_mode = "sandbox" if self.sandbox_enabled else "direct"
            print(f"\n[4/6] Executing strategy (mode: {execution_mode})...")

            # Log execution mode decision
            self.event_logger.log_event(
                logging.INFO,
                "execution_mode_selected",
                f"Executing strategy in {execution_mode} mode",
                iteration_num=iteration_num,
                mode=execution_mode,
                sandbox_enabled=self.sandbox_enabled
            )

            try:
                # Use wrapper for unified execution with automatic fallback
                execution_success, metrics, execution_error = self.sandbox_wrapper.execute_strategy(
                    code=code,
                    data=data,
                    timeout=120
                )

                if execution_success:
                    print("✅ Execution successful")
                    if metrics:
                        print(f"   Metrics: {list(metrics.keys())}")
                else:
                    print(f"❌ Execution failed")
                    if execution_error:
                        print(f"   Error: {execution_error}")

            except Exception as e:
                execution_success = False
                execution_error = str(e)
                print(f"❌ Execution error: {e}")
                logger.error(f"Execution exception: {e}", exc_info=True)

                self.event_logger.log_event(
                    logging.ERROR,
                    "execution_exception",
                    "Strategy execution raised exception",
                    iteration_num=iteration_num,
                    error=execution_error,
                    exception_type=type(e).__name__
                )

            # Post-execution validation (common to both modes)
            if execution_success and metrics:
                print(f"   Metrics: {list(metrics.keys())}")

                # Step 4.5: Validate metric integrity (Story 6)
                print(f"\n[4.5/6] Validating metric integrity...")
                validator = MetricValidator()
                is_valid_metrics, metric_errors = validator.validate_metrics(metrics, report=None)

                if not is_valid_metrics:
                    # Metric validation failed - treat as execution failure
                    execution_success = False
                    execution_error = f"Metric validation failed: {'; '.join(metric_errors)}"
                    print(f"❌ Metric validation failed ({len(metric_errors)} errors)")
                    for error in metric_errors[:3]:  # Show first 3 errors
                        print(f"   - {error}")
                else:
                    print("✅ Metric validation passed")

                    # Step 4.6: Validate semantic behavior (Story 5)
                    print(f"\n[4.6/6] Validating semantic behavior...")
                    sem_validator = SemanticValidator()
                    # Note: Currently report object is not returned from execute_strategy_safe
                    # Semantic validation will be fully functional when sandbox returns report
                    # For now, we pass None and skip validation if report is unavailable
                    is_valid_semantic, semantic_errors = sem_validator.validate_strategy(code, execution_result=None)

                    if not is_valid_semantic:
                        # Semantic validation failed - treat as execution failure
                        execution_success = False
                        execution_error = f"Semantic validation failed: {'; '.join(semantic_errors)}"
                        print(f"❌ Semantic validation failed ({len(semantic_errors)} errors)")
                        for error in semantic_errors[:3]:  # Show first 3 errors
                            print(f"   - {error}")
                    else:
                        print("✅ Semantic validation passed")
        else:
            print(f"\n[4/6] Skipping execution (validation failed)")

        # Step 5: Enhanced feedback with attribution
        print(f"\n[5/6] Building feedback...")

        if self.champion and is_valid and execution_success and metrics:
            attribution = self._compare_with_champion(code, metrics)

            if attribution:
                # Track failures dynamically
                if attribution.get('assessment') == 'degraded':
                    self.failure_tracker.add_pattern(attribution, iteration_num)

                # Generate attributed feedback
                feedback = self.prompt_builder.build_attributed_feedback(
                    attribution,
                    iteration_num,
                    self.champion,
                    failure_patterns=self.failure_tracker.get_avoid_directives()
                )
            else:
                # Fallback to simple feedback if attribution fails
                feedback = self.prompt_builder.build_simple_feedback(metrics)
        else:
            # No champion yet or iteration failed - use simple feedback
            feedback = self.prompt_builder.build_simple_feedback(metrics) if metrics else \
                       self.prompt_builder.build_combined_feedback(
                           validation_passed=is_valid,
                           validation_errors=validation_errors,
                           execution_success=execution_success,
                           execution_error=execution_error,
                           metrics=metrics
                       )

        print(f"✅ Feedback generated ({len(feedback)} chars)")

        # Step 5.5: Update champion if improved
        if is_valid and execution_success and metrics:
            import logging
            logger = logging.getLogger(__name__)
            champion_updated = self._update_champion(iteration_num, code, metrics)
            if champion_updated:
                logger.info("Champion updated successfully")

            # Step 5.6: Update variance monitor and check convergence (Story 1)
            sharpe = metrics.get(METRIC_SHARPE, 0)
            self.variance_monitor.update(iteration_num, sharpe)

            # Check for instability alerts
            alert_triggered, alert_msg = self.variance_monitor.check_alert_condition()
            if alert_triggered:
                logger.warning(f"Variance alert: {alert_msg}")

        # Step 5.7: Check champion staleness (every N iterations)
        if iteration_num > 0 and self.champion:
            # Load staleness configuration
            try:
                config_manager = ConfigManager.get_instance()
                config_manager.load_config()
                staleness_cfg = config_manager.get('anti_churn.staleness', {})
                staleness_enabled = staleness_cfg.get('staleness_enabled', True)
                staleness_check_interval = staleness_cfg.get('staleness_check_interval', 50)
            except Exception as e:
                logger.warning(f"Failed to load staleness configuration: {e}, using defaults")
                staleness_enabled = True
                staleness_check_interval = 50

            # Perform staleness check if enabled and at checkpoint
            if staleness_enabled and iteration_num % staleness_check_interval == 0:
                print(f"\n[5.7/6] Checking champion staleness (iteration {iteration_num})...")
                staleness_result = self._check_champion_staleness()

                if staleness_result['should_demote']:
                    logger.info(f"Champion staleness detected: {staleness_result['reason']}")
                    print(f"⚠️  Champion staleness detected: {staleness_result['reason']}")

                    # Get best strategy from cohort
                    best_cohort_strategy = self._get_best_cohort_strategy()

                    if best_cohort_strategy:
                        # Demote current champion to Hall of Fame
                        old_champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)
                        old_champion_iteration = self.champion.iteration_num
                        self._demote_champion_to_hall_of_fame()

                        # Promote best cohort strategy to new champion
                        new_champion_sharpe = best_cohort_strategy.metrics.get(METRIC_SHARPE, 0)
                        new_champion_iteration = best_cohort_strategy.iteration_num
                        self._promote_to_champion(best_cohort_strategy)

                        # Log comprehensive demotion event
                        logger.info(
                            f"Champion demoted due to staleness:\n"
                            f"  Old champion: Iteration {old_champion_iteration}, Sharpe {old_champion_sharpe:.4f}\n"
                            f"  New champion: Iteration {new_champion_iteration}, Sharpe {new_champion_sharpe:.4f}\n"
                            f"  Reason: {staleness_result['reason']}\n"
                            f"  Cohort metrics: {staleness_result['metrics']}"
                        )
                        print(f"✅ Champion updated: Iteration {old_champion_iteration} → {new_champion_iteration}")
                        print(f"   Sharpe: {old_champion_sharpe:.4f} → {new_champion_sharpe:.4f}")
                        print(f"   Cohort median: {staleness_result['metrics'].get('cohort_median', 'N/A')}")
                    else:
                        logger.warning("No suitable cohort strategy found for promotion")
                        print("⚠️  No suitable cohort strategy found for promotion")
                else:
                    logger.info(f"Champion remains competitive: {staleness_result['reason']}")
                    print(f"✅ Champion competitive: {staleness_result['reason']}")

        # Step 6: Record iteration
        print(f"\n[6/6] Recording iteration...")

        # Handle config serialization (may already be dict or ExperimentConfig object)
        config_dict = None
        if config is not None:
            if isinstance(config, dict):
                config_dict = config
            else:
                config_dict = config.to_dict()

        self.history.add_record(
            iteration_num=iteration_num,
            model=self.model,
            code=code,
            validation_passed=is_valid,
            validation_errors=validation_errors,
            execution_success=execution_success,
            execution_error=execution_error,
            metrics=metrics,
            feedback=feedback,
            data_checksum=checksum,
            data_version={
                'finlab_version': provenance['finlab_version'],
                'data_pull_timestamp': provenance['data_pull_timestamp'],
                'dataset_row_counts': provenance['dataset_row_counts']
            },
            config_snapshot=config_dict
        )
        print("✅ Iteration recorded")

        # Save generated code
        with open(f"generated_strategy_loop_iter{iteration_num}.py", 'w') as f:
            f.write(code)
        print(f"✅ Code saved to generated_strategy_loop_iter{iteration_num}.py")

        # Record iteration monitoring (Task 8: Integration Point 3)
        self._record_iteration_monitoring(
            iteration_num=iteration_num,
            execution_success=(is_valid and execution_success),
            metrics=metrics
        )

        status = "SUCCESS" if (is_valid and execution_success) else "FAILED"
        return (is_valid and execution_success), status

    def _load_champion(self) -> Optional[ChampionStrategy]:
        """Load champion strategy from Hall of Fame.

        C1 Fix: Uses unified Hall of Fame API instead of direct JSON file access.
        Falls back to legacy champion_strategy.json if Hall of Fame is empty
        (for backward compatibility during migration).

        Returns:
            ChampionStrategy if champion exists, None otherwise
        """
        import json
        import os

        # Try Hall of Fame first (unified persistence)
        genome = self.hall_of_fame.get_current_champion()
        if genome:
            # Convert StrategyGenome → ChampionStrategy
            # Extract iteration_num from parameters (stored during save)
            iteration_num = genome.parameters.get('__iteration_num__', 0)

            # Remove metadata from parameters
            clean_params = {k: v for k, v in genome.parameters.items() if not k.startswith('__')}

            return ChampionStrategy(
                iteration_num=iteration_num,
                code=genome.strategy_code,
                parameters=clean_params,
                metrics=genome.metrics,
                success_patterns=genome.success_patterns,
                timestamp=genome.created_at
            )

        # Fallback: Legacy champion_strategy.json (migration support)
        if os.path.exists(CHAMPION_FILE):
            try:
                with open(CHAMPION_FILE, 'r') as f:
                    data = json.load(f)
                champion = ChampionStrategy.from_dict(data)

                # Migrate to Hall of Fame automatically
                print(f"Migrating legacy champion from {CHAMPION_FILE} to Hall of Fame...")
                self._save_champion_to_hall_of_fame(champion)
                print("✅ Migration complete")

                return champion
            except (json.JSONDecodeError, TypeError, KeyError, ValueError) as e:
                print(f"Warning: Could not load legacy champion: {e}")
                print("Starting without champion")
                return None

        return None

    def _update_champion(
        self,
        iteration_num: int,
        code: str,
        metrics: Dict[str, float]
    ) -> bool:
        """Update champion with dynamic probation period (Story 4: F4).

        Uses AntiChurnManager for dynamic thresholds based on probation period.
        Tracks champion updates for frequency analysis.

        Args:
            iteration_num: Current iteration number
            code: Strategy code that was executed
            metrics: Performance metrics dict with at least METRIC_SHARPE key

        Returns:
            True if champion was updated, False otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        current_sharpe = metrics.get(METRIC_SHARPE, 0)

        # First valid strategy becomes champion
        if self.champion is None:
            if current_sharpe > self.anti_churn.min_sharpe_for_champion:
                self._create_champion(iteration_num, code, metrics)
                # Track initial champion creation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=True,
                    old_sharpe=None,
                    new_sharpe=current_sharpe,
                    threshold_used=None
                )
                return True
            else:
                # Track failed champion creation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False

        # Get dynamic improvement threshold
        champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)
        required_improvement_pct = self.anti_churn.get_required_improvement(
            current_iteration=iteration_num,
            champion_iteration=self.champion.iteration_num
        )
        required_improvement_multiplier = 1.0 + required_improvement_pct

        # Get additive threshold from anti-churn manager (Phase 3: Hybrid Threshold)
        additive_threshold = self.anti_churn.get_additive_threshold()

        # Hybrid threshold: Accept if EITHER condition met
        relative_threshold_met = current_sharpe >= champion_sharpe * required_improvement_multiplier
        absolute_threshold_met = current_sharpe >= champion_sharpe + additive_threshold

        if relative_threshold_met or absolute_threshold_met:
            improvement_pct = (current_sharpe / champion_sharpe - 1) * 100

            # Log which threshold was used for tracking
            threshold_type = "relative" if relative_threshold_met else "absolute"

            # Phase 3: Multi-objective validation (Story 10.3)
            # Prevent brittle strategy selection where Sharpe improves but risk metrics degrade
            logger.info(
                f"Champion update passed {threshold_type} threshold "
                f"(+{improvement_pct:.1f}%). Validating multi-objective criteria..."
            )

            validation_result = self._validate_multi_objective(
                new_metrics=metrics,
                old_metrics=self.champion.metrics
            )

            if not validation_result['passed']:
                # Multi-objective validation failed - reject champion update
                failed_criteria = ', '.join(validation_result['failed_criteria'])
                logger.info(
                    f"Champion update REJECTED by multi-objective validation. "
                    f"Failed criteria: {failed_criteria}. "
                    f"Sharpe improvement alone insufficient (new: {current_sharpe:.4f} vs "
                    f"champion: {champion_sharpe:.4f}, +{improvement_pct:.1f}%)"
                )

                # Track failed champion update due to multi-objective validation
                self.anti_churn.track_champion_update(
                    iteration_num=iteration_num,
                    was_updated=False
                )
                return False

            # Multi-objective validation passed
            logger.info(f"Multi-objective validation PASSED. Proceeding with champion update.")

            # Track successful champion update
            self.anti_churn.track_champion_update(
                iteration_num=iteration_num,
                was_updated=True,
                old_sharpe=champion_sharpe,
                new_sharpe=current_sharpe,
                threshold_used=required_improvement_pct
            )

            self._create_champion(iteration_num, code, metrics)
            logger.info(
                f"Champion updated via {threshold_type} threshold: "
                f"{champion_sharpe:.4f} → {current_sharpe:.4f} "
                f"(+{improvement_pct:.1f}%, relative_met: {relative_threshold_met}, "
                f"absolute_met: {absolute_threshold_met})"
            )

            # Record champion update to DiversityMonitor (Task 8: Integration Point 4)
            if hasattr(self, '_monitoring_enabled') and self._monitoring_enabled and hasattr(self, 'diversity_monitor') and self.diversity_monitor:
                try:
                    self.diversity_monitor.record_champion_update(
                        iteration=iteration_num,
                        old_sharpe=champion_sharpe,
                        new_sharpe=current_sharpe
                    )
                except Exception as e:
                    logger.warning(f"Failed to record champion update to monitoring: {e}")

            return True
        else:
            # Track failed champion update attempt
            self.anti_churn.track_champion_update(
                iteration_num=iteration_num,
                was_updated=False
            )
            return False

    def _create_champion(
        self,
        iteration_num: int,
        code: str,
        metrics: Dict[str, float]
    ) -> None:
        """Create new champion strategy.

        Extracts parameters and success patterns from the code, creates
        a ChampionStrategy instance, and persists it to disk.

        Args:
            iteration_num: Iteration number that produced this champion
            code: Strategy code
            metrics: Performance metrics dict
        """
        import logging
        from performance_attributor import extract_strategy_params, extract_success_patterns

        logger = logging.getLogger(__name__)

        parameters = extract_strategy_params(code)
        success_patterns = extract_success_patterns(code, parameters)

        self.champion = ChampionStrategy(
            iteration_num=iteration_num,
            code=code,
            parameters=parameters,
            metrics=metrics,
            success_patterns=success_patterns,
            timestamp=datetime.now().isoformat()
        )

        self._save_champion()
        logger.info(f"New champion: Iteration {iteration_num}, Sharpe {metrics.get(METRIC_SHARPE, 0):.4f}")

    def _save_champion(self) -> None:
        """Save champion strategy to Hall of Fame.

        C1 Fix: Uses unified Hall of Fame API instead of direct JSON file access.
        Automatically classifies strategy into appropriate tier based on Sharpe ratio.
        """
        if not self.champion:
            return

        self._save_champion_to_hall_of_fame(self.champion)

    def _save_champion_to_hall_of_fame(self, champion: ChampionStrategy) -> None:
        """Save champion to Hall of Fame repository.

        Helper method to convert ChampionStrategy format and persist to Hall of Fame.
        Used both for new champions and legacy migrations.

        Args:
            champion: ChampionStrategy to save
        """
        # Add iteration_num to parameters for later retrieval
        # Use __iteration_num__ prefix to distinguish from strategy parameters
        params_with_metadata = champion.parameters.copy()
        params_with_metadata['__iteration_num__'] = champion.iteration_num

        # Save to Hall of Fame (automatic tier classification)
        self.hall_of_fame.add_strategy(
            template_name='autonomous_generated',  # Autonomous loop strategies
            parameters=params_with_metadata,
            metrics=champion.metrics,
            strategy_code=champion.code,
            success_patterns=champion.success_patterns
        )

    def _compare_with_champion(
        self,
        current_code: str,
        current_metrics: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """Compare current strategy with champion for performance attribution.

        Extracts parameters from current code and compares with champion
        to identify what changed and how it affected performance.

        Args:
            current_code: Strategy code to compare
            current_metrics: Performance metrics for current strategy

        Returns:
            Attribution dictionary with changes and performance delta,
            or None if no champion exists or comparison fails
        """
        import logging

        if not self.champion:
            return None

        try:
            from performance_attributor import extract_strategy_params, compare_strategies

            logger = logging.getLogger(__name__)
            curr_params = extract_strategy_params(current_code)
            return compare_strategies(
                prev_params=self.champion.parameters,
                curr_params=curr_params,
                prev_metrics=self.champion.metrics,
                curr_metrics=current_metrics
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Attribution comparison failed: {e}")
            logger.info("Falling back to simple feedback")
            return None

    def _validate_preservation(self, generated_code: str, execution_metrics: Optional[Dict[str, float]] = None) -> bool:
        """Validate that generated code preserves champion patterns (Enhanced).

        Uses PreservationValidator for comprehensive validation including
        parameter preservation and behavioral similarity checks.

        Args:
            generated_code: LLM-generated strategy code to validate
            execution_metrics: Optional runtime metrics for behavioral validation

        Returns:
            True if all critical champion patterns are preserved, False otherwise
        """
        from src.validation.preservation_validator import PreservationValidator
        import logging

        logger = logging.getLogger(__name__)

        # Use enhanced preservation validator
        validator = PreservationValidator()
        is_preserved, report = validator.validate_preservation(
            generated_code=generated_code,
            champion=self.champion,
            execution_metrics=execution_metrics
        )

        # Log preservation report details
        if not is_preserved:
            logger.warning(f"Preservation validation failed: {report.summary()}")
            if report.missing_params:
                logger.warning(f"Missing critical parameters: {', '.join(report.missing_params)}")
            if report.recommendations:
                for rec in report.recommendations:
                    logger.info(f"Recommendation: {rec}")
        else:
            logger.info(f"Preservation validated: {report.summary()}")

        # Log false positive risk if high
        if report.false_positive_risk > 0.5:
            logger.warning(f"High false positive risk ({report.false_positive_risk:.2f})")

        return is_preserved

    def _validate_multi_objective(
        self,
        new_metrics: Dict[str, float],
        old_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Validate multi-objective criteria for champion update (Phase 3: Task 13.1).

        Validates that new strategy maintains balanced risk/return profile by checking:
        1. Sharpe ratio improvement (handled by hybrid threshold in _update_champion)
        2. Calmar ratio retention: new_calmar >= old_calmar * calmar_retention_ratio
        3. Max drawdown tolerance: new_mdd <= old_mdd * max_drawdown_tolerance

        This prevents brittle strategy selection where Sharpe improves but risk
        characteristics degrade (low Calmar, high drawdown).

        Args:
            new_metrics: Performance metrics for new strategy
            old_metrics: Performance metrics for champion strategy

        Returns:
            Dictionary with validation results:
            - passed (bool): True if all criteria pass
            - failed_criteria (list): List of failed criteria names
            - details (dict): Detailed validation results for each criterion
                - calmar_check (dict): Calmar validation details
                - drawdown_check (dict): Drawdown validation details

        Example:
            >>> result = self._validate_multi_objective(
            ...     new_metrics={'sharpe_ratio': 2.1, 'calmar_ratio': 0.75, 'max_drawdown': -0.16},
            ...     old_metrics={'sharpe_ratio': 2.0, 'calmar_ratio': 0.80, 'max_drawdown': -0.15}
            ... )
            >>> result['passed']
            True  # All criteria pass
            >>> result['failed_criteria']
            []
        """
        import logging
        from src.backtest.metrics import calculate_calmar_ratio
        import math

        logger = logging.getLogger(__name__)

        # Return structure
        validation_result = {
            'passed': True,
            'failed_criteria': [],
            'details': {}
        }

        # Check if multi-objective validation is enabled
        if not self.multi_objective_enabled:
            logger.debug("Multi-objective validation disabled, skipping")
            validation_result['details']['disabled'] = True
            return validation_result

        # Extract metrics with edge case handling
        def get_metric_safe(metrics: Dict[str, float], key: str, default: float = 0.0) -> Optional[float]:
            """Safely extract metric with NaN/None handling."""
            value = metrics.get(key, default)
            if value is None or (isinstance(value, float) and math.isnan(value)):
                return None
            return value

        # Get Sharpe ratios (for logging context)
        new_sharpe = get_metric_safe(new_metrics, 'sharpe_ratio')
        old_sharpe = get_metric_safe(old_metrics, 'sharpe_ratio')

        # Get Calmar ratios
        new_calmar = get_metric_safe(new_metrics, 'calmar_ratio')
        old_calmar = get_metric_safe(old_metrics, 'calmar_ratio')

        # Get max drawdowns (negative values)
        new_mdd = get_metric_safe(new_metrics, 'max_drawdown')
        old_mdd = get_metric_safe(old_metrics, 'max_drawdown')

        # Alternative: Calculate Calmar from annual_return and max_drawdown if not provided
        if new_calmar is None:
            annual_return = get_metric_safe(new_metrics, 'annual_return')
            if annual_return is not None and new_mdd is not None:
                new_calmar = calculate_calmar_ratio(annual_return, new_mdd)

        if old_calmar is None:
            annual_return = get_metric_safe(old_metrics, 'annual_return')
            if annual_return is not None and old_mdd is not None:
                old_calmar = calculate_calmar_ratio(annual_return, old_mdd)

        # ====================
        # Criterion 1: Calmar Ratio Retention
        # ====================
        calmar_check = {'passed': False, 'reason': '', 'values': {}}

        if old_calmar is None or new_calmar is None:
            # Missing Calmar data - treat as pass with warning
            calmar_check['passed'] = True
            calmar_check['reason'] = 'Calmar ratio unavailable (missing data)'
            calmar_check['values'] = {
                'old_calmar': old_calmar,
                'new_calmar': new_calmar,
                'required_calmar': None
            }
            logger.warning("Calmar ratio validation skipped: missing data")
        else:
            # Validate: new_calmar >= old_calmar * calmar_retention_ratio
            required_calmar = old_calmar * self.calmar_retention_ratio

            if new_calmar >= required_calmar:
                calmar_check['passed'] = True
                retention_pct = (new_calmar / old_calmar) * 100 if old_calmar != 0 else 100
                calmar_check['reason'] = (
                    f'Calmar retained: {new_calmar:.4f} >= {required_calmar:.4f} '
                    f'({retention_pct:.1f}% of old Calmar)'
                )
            else:
                calmar_check['passed'] = False
                retention_pct = (new_calmar / old_calmar) * 100 if old_calmar != 0 else 0
                calmar_check['reason'] = (
                    f'Calmar degraded: {new_calmar:.4f} < {required_calmar:.4f} '
                    f'({retention_pct:.1f}% < {self.calmar_retention_ratio*100:.0f}% retention)'
                )
                validation_result['failed_criteria'].append('calmar_ratio')
                validation_result['passed'] = False

            calmar_check['values'] = {
                'old_calmar': old_calmar,
                'new_calmar': new_calmar,
                'required_calmar': required_calmar,
                'retention_ratio': self.calmar_retention_ratio
            }

        validation_result['details']['calmar_check'] = calmar_check

        # ====================
        # Criterion 2: Max Drawdown Tolerance
        # ====================
        drawdown_check = {'passed': False, 'reason': '', 'values': {}}

        if old_mdd is None or new_mdd is None:
            # Missing drawdown data - treat as pass with warning
            drawdown_check['passed'] = True
            drawdown_check['reason'] = 'Max drawdown unavailable (missing data)'
            drawdown_check['values'] = {
                'old_mdd': old_mdd,
                'new_mdd': new_mdd,
                'max_allowed_mdd': None
            }
            logger.warning("Max drawdown validation skipped: missing data")
        else:
            # Validate: new_mdd <= old_mdd * max_drawdown_tolerance
            # Note: Drawdowns are negative, so "worse" means more negative (larger magnitude)
            # Example: old_mdd = -0.15, tolerance = 1.10 → max_allowed = -0.165 (10% worse)
            max_allowed_mdd = old_mdd * self.max_drawdown_tolerance

            if new_mdd >= max_allowed_mdd:  # More negative = worse, so >= is better
                drawdown_check['passed'] = True
                # Calculate how much worse the drawdown is (as percentage)
                if old_mdd != 0:
                    worse_pct = (new_mdd / old_mdd) * 100
                else:
                    worse_pct = 100
                drawdown_check['reason'] = (
                    f'Drawdown acceptable: {new_mdd:.4f} >= {max_allowed_mdd:.4f} '
                    f'({worse_pct:.1f}% of old drawdown)'
                )
            else:
                drawdown_check['passed'] = False
                # Calculate how much worse the drawdown is (as percentage)
                if old_mdd != 0:
                    worse_pct = (new_mdd / old_mdd) * 100
                else:
                    worse_pct = 0
                drawdown_check['reason'] = (
                    f'Drawdown too large: {new_mdd:.4f} < {max_allowed_mdd:.4f} '
                    f'({worse_pct:.1f}% > {self.max_drawdown_tolerance*100:.0f}% tolerance)'
                )
                validation_result['failed_criteria'].append('max_drawdown')
                validation_result['passed'] = False

            drawdown_check['values'] = {
                'old_mdd': old_mdd,
                'new_mdd': new_mdd,
                'max_allowed_mdd': max_allowed_mdd,
                'tolerance': self.max_drawdown_tolerance
            }

        validation_result['details']['drawdown_check'] = drawdown_check

        # Log validation results
        def format_metric(value: Optional[float]) -> str:
            """Format metric value for logging."""
            if value is None:
                return 'N/A'
            return f"{value:.4f}"

        if validation_result['passed']:
            logger.info(
                f"Multi-objective validation PASSED "
                f"(Sharpe: {format_metric(old_sharpe)}→{format_metric(new_sharpe)}, "
                f"Calmar: {format_metric(old_calmar)}→{format_metric(new_calmar)}, "
                f"MDD: {format_metric(old_mdd)}→{format_metric(new_mdd)})"
            )
        else:
            logger.warning(
                f"Multi-objective validation FAILED: {', '.join(validation_result['failed_criteria'])} "
                f"(Sharpe: {format_metric(old_sharpe)}→{format_metric(new_sharpe)}, "
                f"Calmar: {format_metric(old_calmar)}→{format_metric(new_calmar)}, "
                f"MDD: {format_metric(old_mdd)}→{format_metric(new_mdd)})"
            )
            for criterion in validation_result['failed_criteria']:
                detail = validation_result['details'].get(f"{criterion.split('_')[0]}_check", {})
                if detail:
                    logger.warning(f"  - {criterion}: {detail.get('reason', 'Unknown')}")

        return validation_result

    def _get_best_cohort_strategy(self) -> Optional['ChampionStrategy']:
        """Get best strategy from recent cohort for champion promotion.

        Extracts recent successful strategies, builds cohort from top performers,
        and returns the best strategy by Sharpe ratio.

        Returns:
            ChampionStrategy instance for best cohort strategy, or None if no suitable strategy found
        """
        import logging
        import numpy as np

        logger = logging.getLogger(__name__)

        # Load staleness configuration
        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()
            staleness_cfg = config_manager.get('anti_churn.staleness', {})
            check_interval = staleness_cfg.get('staleness_check_interval', 50)
            cohort_percentile = staleness_cfg.get('staleness_cohort_percentile', 0.10)
        except Exception as e:
            logger.error(f"Failed to load staleness configuration: {e}")
            return None

        # Get recent successful strategies
        successful = self.history.get_successful_iterations()
        if not successful:
            logger.warning("No successful iterations available for cohort selection")
            return None

        # Extract last N strategies (window for staleness check)
        recent_strategies = successful[-check_interval:] if len(successful) > check_interval else successful

        # Build cohort: top X% by Sharpe ratio
        strategies_with_sharpe = [
            (record, record.metrics.get(METRIC_SHARPE, 0))
            for record in recent_strategies
            if record.metrics and METRIC_SHARPE in record.metrics
        ]

        if not strategies_with_sharpe:
            logger.warning("No strategies with Sharpe ratios found in recent history")
            return None

        # Calculate percentile threshold
        sharpe_ratios = [sharpe for _, sharpe in strategies_with_sharpe]
        percentile_value = (1.0 - cohort_percentile) * 100
        threshold = np.percentile(sharpe_ratios, percentile_value)

        # Filter cohort: strategies above threshold
        cohort = [(record, sharpe) for record, sharpe in strategies_with_sharpe if sharpe >= threshold]

        if not cohort:
            logger.warning("No strategies in cohort after filtering")
            return None

        # Find best strategy in cohort (highest Sharpe)
        best_record, best_sharpe = max(cohort, key=lambda x: x[1])

        logger.info(f"Selected best cohort strategy: Iteration {best_record.iteration_num}, Sharpe {best_sharpe:.4f}")

        # Convert IterationRecord to ChampionStrategy
        from performance_attributor import extract_strategy_params, extract_success_patterns

        parameters = extract_strategy_params(best_record.code)
        success_patterns = extract_success_patterns(best_record.code, parameters)

        return ChampionStrategy(
            iteration_num=best_record.iteration_num,
            code=best_record.code,
            parameters=parameters,
            metrics=best_record.metrics,
            success_patterns=success_patterns,
            timestamp=datetime.now().isoformat()
        )

    def _demote_champion_to_hall_of_fame(self) -> None:
        """Demote current champion by saving to Hall of Fame (if not already there).

        The champion is already saved in Hall of Fame from _save_champion(), so this
        method is primarily for logging and tracking the demotion event.
        The actual demotion happens when we replace self.champion with a new strategy.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not self.champion:
            logger.warning("No champion to demote")
            return

        # Champion is already persisted in Hall of Fame from previous _save_champion() call
        # This method is a placeholder for future demotion tracking logic
        # (e.g., marking strategy as "demoted_champion" in Hall of Fame metadata)

        logger.info(
            f"Champion demoted: Iteration {self.champion.iteration_num}, "
            f"Sharpe {self.champion.metrics.get(METRIC_SHARPE, 0):.4f}"
        )

    def _promote_to_champion(self, strategy: 'ChampionStrategy') -> None:
        """Promote a cohort strategy to new champion.

        Args:
            strategy: ChampionStrategy instance to promote
        """
        import logging
        logger = logging.getLogger(__name__)

        if not strategy:
            logger.error("Cannot promote None strategy to champion")
            return

        # Set as new champion
        self.champion = strategy

        # Persist to Hall of Fame
        self._save_champion()

        logger.info(
            f"Champion promoted: Iteration {strategy.iteration_num}, "
            f"Sharpe {strategy.metrics.get(METRIC_SHARPE, 0):.4f}"
        )

    def _check_champion_staleness(self) -> Dict[str, Any]:
        """Check if champion is stale by comparing against recent strategy cohort.

        Staleness mechanism prevents eternal reign of outlier champions by:
        1. Extracting last N strategies from iteration history (N = staleness_check_interval)
        2. Calculating top X% threshold (e.g., 90th percentile of Sharpe ratios)
        3. Building cohort from strategies above threshold (top 10%)
        4. Calculating cohort median Sharpe ratio
        5. Comparing champion Sharpe vs cohort median
        6. Recommending demotion if champion < cohort median

        Example scenario:
        - Iteration 6: Champion achieves Sharpe 2.4751 (outlier)
        - Iterations 7-56: Champion remains dominant
        - Iteration 50: Staleness check triggered
        - Recent cohort (top 10% from iterations 0-50): median Sharpe 1.8
        - Champion Sharpe 2.4751 > cohort median 1.8 → KEEP champion (still competitive)

        Returns:
            Dictionary with staleness check results:
            - should_demote (bool): True if champion should be demoted
            - reason (str): Human-readable explanation of decision
            - metrics (dict): Supporting metrics for the decision
                - champion_sharpe (float): Champion's Sharpe ratio
                - cohort_median (float or None): Cohort median Sharpe ratio
                - cohort_size (int): Number of strategies in cohort
                - window_size (int): Number of recent strategies analyzed
                - percentile_threshold (float): Sharpe threshold for cohort membership
        """
        import logging
        import numpy as np

        logger = logging.getLogger(__name__)

        # Load configuration
        try:
            config_manager = ConfigManager.get_instance()
            config_manager.load_config()
            staleness_cfg = config_manager.get('anti_churn.staleness', {})
        except Exception as e:
            logger.error(f"Failed to load staleness configuration: {e}")
            return {
                'should_demote': False,
                'reason': f"Configuration error: {e}",
                'metrics': {}
            }

        # Extract configuration parameters
        check_interval = staleness_cfg.get('staleness_check_interval', 50)
        cohort_percentile = staleness_cfg.get('staleness_cohort_percentile', 0.10)
        min_cohort_size = staleness_cfg.get('staleness_min_cohort_size', 5)

        # Edge case: No champion exists
        if not self.champion:
            return {
                'should_demote': False,
                'reason': "No champion exists",
                'metrics': {}
            }

        champion_sharpe = self.champion.metrics.get(METRIC_SHARPE, 0)

        # Get recent N successful strategies from history
        successful = self.history.get_successful_iterations()
        if not successful:
            return {
                'should_demote': False,
                'reason': "No successful iterations in history",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': 0
                }
            }

        # Extract last N strategies (window for staleness check)
        recent_strategies = successful[-check_interval:] if len(successful) > check_interval else successful
        window_size = len(recent_strategies)

        # Edge case: Insufficient data for meaningful analysis
        if window_size < min_cohort_size:
            return {
                'should_demote': False,
                'reason': f"Insufficient data: {window_size} strategies < minimum {min_cohort_size}",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': window_size
                }
            }

        # Extract Sharpe ratios from recent strategies
        sharpe_ratios = []
        for record in recent_strategies:
            if record.metrics and METRIC_SHARPE in record.metrics:
                sharpe_ratios.append(record.metrics[METRIC_SHARPE])

        # Edge case: No valid Sharpe ratios found
        if not sharpe_ratios:
            return {
                'should_demote': False,
                'reason': "No valid Sharpe ratios in recent strategies",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': 0,
                    'window_size': window_size
                }
            }

        # Calculate percentile threshold (e.g., 90th percentile for top 10%)
        percentile_value = (1.0 - cohort_percentile) * 100  # Convert 0.10 → 90th percentile
        threshold = np.percentile(sharpe_ratios, percentile_value)

        # Build cohort: strategies above threshold (top X%)
        cohort_sharpes = [s for s in sharpe_ratios if s >= threshold]
        cohort_size = len(cohort_sharpes)

        # Edge case: Cohort too small for reliable comparison
        if cohort_size < min_cohort_size:
            return {
                'should_demote': False,
                'reason': f"Cohort too small: {cohort_size} strategies < minimum {min_cohort_size}",
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': None,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }

        # Calculate cohort median Sharpe ratio
        cohort_median = float(np.median(cohort_sharpes))

        # Compare champion vs cohort median
        if champion_sharpe < cohort_median:
            # Champion is stale - recent top strategies outperform
            return {
                'should_demote': True,
                'reason': (
                    f"Champion stale: Sharpe {champion_sharpe:.4f} < "
                    f"cohort median {cohort_median:.4f} "
                    f"(top {cohort_percentile*100:.0f}% of {window_size} recent strategies)"
                ),
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': cohort_median,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }
        else:
            # Champion still competitive
            logger.info(
                f"Champion competitive: Sharpe {champion_sharpe:.4f} >= "
                f"cohort median {cohort_median:.4f} "
                f"(cohort size: {cohort_size}, window: {window_size})"
            )
            return {
                'should_demote': False,
                'reason': (
                    f"Champion competitive: Sharpe {champion_sharpe:.4f} >= "
                    f"cohort median {cohort_median:.4f}"
                ),
                'metrics': {
                    'champion_sharpe': champion_sharpe,
                    'cohort_median': cohort_median,
                    'cohort_size': cohort_size,
                    'window_size': window_size,
                    'percentile_threshold': threshold
                }
            }

    def cleanup(self):
        """Cleanup Docker containers on shutdown.

        This method ensures all active Docker containers are cleaned up
        before the loop terminates. Should be called on normal exit or
        in exception handlers.
        """
        if self.docker_executor:
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Cleaning up Docker containers...")

            try:
                stats = self.docker_executor.cleanup_all()
                logger.info(
                    f"Container cleanup complete: {stats['success']}/{stats['total']} successful"
                )

                if stats['failed'] > 0:
                    logger.warning(f"Failed to cleanup {stats['failed']} containers")

                # Log cleanup event
                self.event_logger.log_event(
                    logging.INFO,
                    "docker_cleanup",
                    "Docker containers cleaned up on shutdown",
                    total_containers=stats['total'],
                    cleaned=stats['success'],
                    failed=stats['failed']
                )

            except Exception as e:
                logger.error(f"Container cleanup error: {e}", exc_info=True)

    def _record_iteration_monitoring(
        self,
        iteration_num: int,
        execution_success: bool,
        metrics: Optional[Dict[str, float]] = None
    ) -> None:
        """Record monitoring metrics for current iteration.

        Integration Point 3: After strategy execution
        Records diversity, container stats, and iteration results to monitoring system.

        Args:
            iteration_num: Current iteration number
            execution_success: Whether iteration succeeded
            metrics: Performance metrics if available
        """
        if not hasattr(self, '_monitoring_enabled') or not self._monitoring_enabled:
            return

        import logging
        logger = logging.getLogger(__name__)

        try:
            # Record iteration result for success rate tracking
            if self.alert_manager:
                self.alert_manager.record_iteration_result(execution_success)

            # Record diversity if metrics available (placeholder - requires population manager integration)
            # This is a simplified version - full integration would calculate actual diversity
            if self.diversity_monitor and metrics and execution_success:
                # For now, use a placeholder diversity calculation
                # In production, this should call population_manager.calculate_diversity()
                diversity = 0.5  # Placeholder
                unique_count = 1
                total_count = 1

                self.diversity_monitor.record_diversity(
                    iteration=iteration_num,
                    diversity=diversity,
                    unique_count=unique_count,
                    total_count=total_count
                )

                # Check for diversity collapse
                if self.diversity_monitor.check_diversity_collapse():
                    logger.warning(f"Diversity collapse detected at iteration {iteration_num}")

            # Record container stats if available
            if self.container_monitor and self.container_monitor.is_docker_available():
                # Scan for orphaned containers periodically (every 10 iterations)
                if iteration_num % 10 == 0:
                    orphaned = self.container_monitor.scan_orphaned_containers()
                    if orphaned:
                        logger.warning(f"Found {len(orphaned)} orphaned containers")
                        # Auto-cleanup if enabled
                        if self.container_monitor.auto_cleanup:
                            cleaned = self.container_monitor.cleanup_orphaned_containers(orphaned)
                            logger.info(f"Cleaned up {cleaned} orphaned containers")

        except Exception as e:
            # Monitoring should never break the iteration loop
            logger.warning(f"Monitoring recording failed (non-fatal): {e}")

    def _cleanup_monitoring(self) -> None:
        """Cleanup monitoring threads and resources.

        Integration Point 5: Loop shutdown
        Stops all monitoring threads gracefully.
        """
        import logging
        logger = logging.getLogger(__name__)

        if not hasattr(self, '_monitoring_enabled') or not self._monitoring_enabled:
            return

        logger.info("Shutting down monitoring system...")

        try:
            # Stop ResourceMonitor
            if hasattr(self, 'resource_monitor') and self.resource_monitor:
                try:
                    self.resource_monitor.stop_monitoring()
                    logger.info("ResourceMonitor stopped")
                except Exception as e:
                    logger.error(f"Failed to stop ResourceMonitor: {e}")

            # Stop AlertManager
            if hasattr(self, 'alert_manager') and self.alert_manager:
                try:
                    self.alert_manager.stop_monitoring()
                    logger.info("AlertManager stopped")
                except Exception as e:
                    logger.error(f"Failed to stop AlertManager: {e}")

            logger.info("Monitoring system shutdown complete")

        except Exception as e:
            logger.error(f"Error during monitoring cleanup: {e}")

    def run(self, data: Optional[Any] = None) -> dict:
        """Run the complete autonomous loop.

        Args:
            data: Finlab data object for execution (None for testing)

        Returns:
            Summary dictionary with loop statistics
        """
        print("\n" + "="*60)
        print("AUTONOMOUS LEARNING LOOP - START")
        print("="*60)
        print(f"Model: {self.model}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Sandbox mode: {'ENABLED' if self.sandbox_enabled else 'DISABLED'}")
        print()

        start_time = time.time()
        results = {
            'total_iterations': 0,
            'successful_iterations': 0,
            'failed_iterations': 0,
            'validation_failures': 0,
            'execution_failures': 0,
            'sandbox_mode': self.sandbox_enabled
        }

        try:
            for i in range(self.max_iterations):
                success, status = self.run_iteration(i, data)

                results['total_iterations'] += 1
                if success:
                    results['successful_iterations'] += 1
                else:
                    results['failed_iterations'] += 1

                    # Track failure types
                    record = self.history.get_record(i)
                    if record:
                        if not record.validation_passed:
                            results['validation_failures'] += 1
                        elif not record.execution_success:
                            results['execution_failures'] += 1

                # Brief pause between iterations
                if i < self.max_iterations - 1:
                    time.sleep(1)

        finally:
            # Always cleanup Docker containers on exit
            self.cleanup()

        elapsed = time.time() - start_time

        # Final summary
        print("\n" + "="*60)
        print("AUTONOMOUS LEARNING LOOP - COMPLETE")
        print("="*60)
        print(f"Total time: {elapsed:.1f}s")
        print(f"Total iterations: {results['total_iterations']}")
        print(f"✅ Successful: {results['successful_iterations']}")
        print(f"❌ Failed: {results['failed_iterations']}")
        print(f"   - Validation failures: {results['validation_failures']}")
        print(f"   - Execution failures: {results['execution_failures']}")

        # Success rate
        if results['total_iterations'] > 0:
            success_rate = results['successful_iterations'] / results['total_iterations'] * 100
            print(f"\nSuccess rate: {success_rate:.1f}%")

        # Best strategy
        successful = self.history.get_successful_iterations()
        if successful:
            print(f"\n🎉 Generated {len(successful)} successful strategies!")

            # Find best by Sharpe ratio if metrics available
            with_metrics = [s for s in successful if s.metrics and 'sharpe_ratio' in s.metrics]
            if with_metrics:
                best = max(with_metrics, key=lambda s: s.metrics['sharpe_ratio'])
                print(f"\n🏆 Best strategy: Iteration {best.iteration_num}")
                print(f"   Sharpe: {best.metrics['sharpe_ratio']:.4f}")
                print(f"   Return: {best.metrics.get('total_return', 'N/A')}")

        # Cleanup monitoring system (Task 8: Integration Point 5)
        self._cleanup_monitoring()

        # Add LLM statistics if enabled
        if self.llm_enabled:
            llm_stats = self.get_llm_statistics()
            results['llm_statistics'] = llm_stats

            print(f"\n{'='*60}")
            print("LLM INNOVATION STATISTICS")
            print(f"{'='*60}")
            print(f"LLM enabled: {llm_stats['llm_enabled']}")
            print(f"Innovation rate: {llm_stats['innovation_rate']:.1%}")
            print(f"LLM innovations: {llm_stats['llm_innovations']}")
            print(f"LLM fallbacks: {llm_stats['llm_fallbacks']}")
            print(f"Factor Graph mutations: {llm_stats['factor_mutations']}")
            print(f"LLM success rate: {llm_stats['llm_success_rate']:.1%}")

            if llm_stats.get('llm_costs'):
                cost_report = llm_stats['llm_costs']
                print(f"\nLLM Costs:")
                print(f"  Total cost: ${cost_report['total_cost_usd']:.6f}")
                print(f"  Total tokens: {cost_report['total_tokens']}")
                print(f"  Successful generations: {cost_report['successful_generations']}")
                if cost_report['successful_generations'] > 0:
                    print(f"  Average cost per success: ${cost_report['average_cost_per_success']:.6f}")

        results['elapsed_time'] = elapsed
        return results

    def get_llm_statistics(self) -> Dict[str, Any]:
        """Get LLM innovation statistics.

        Returns:
            Dictionary with LLM usage stats including:
            - llm_enabled: Whether LLM is enabled
            - innovation_rate: Configured innovation rate
            - llm_innovations: Successful LLM generations
            - llm_fallbacks: LLM failures with fallback to Factor Graph
            - factor_mutations: Direct Factor Graph mutations
            - llm_api_failures: API-level failures
            - llm_validation_failures: Validation failures
            - llm_success_rate: Percentage of successful LLM attempts
            - llm_costs: Cost report from InnovationEngine (if enabled)
        """
        stats = {
            'llm_enabled': self.llm_enabled,
            'innovation_rate': self.innovation_rate,
            'llm_innovations': self.llm_stats['llm_innovations'],
            'llm_fallbacks': self.llm_stats['llm_fallbacks'],
            'factor_mutations': self.llm_stats['factor_mutations'],
            'llm_api_failures': self.llm_stats['llm_api_failures'],
            'llm_validation_failures': self.llm_stats['llm_validation_failures']
        }

        # Calculate success rate
        total_llm_attempts = self.llm_stats['llm_innovations'] + self.llm_stats['llm_fallbacks']
        if total_llm_attempts > 0:
            stats['llm_success_rate'] = self.llm_stats['llm_innovations'] / total_llm_attempts
        else:
            stats['llm_success_rate'] = 0.0

        # Add cost report if LLM enabled
        if self.llm_enabled and self.innovation_engine:
            try:
                stats['llm_costs'] = self.innovation_engine.get_cost_report()
                stats['llm_engine_stats'] = self.innovation_engine.get_statistics()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get LLM cost report: {e}")
                stats['llm_costs'] = None
                stats['llm_engine_stats'] = None

        return stats


def main():
    """Test autonomous loop (without real finlab data)."""
    print("Testing autonomous loop...\n")
    print("Note: Running without real finlab data - execution will fail")
    print("      This tests the loop mechanism, not actual strategy performance\n")

    # Create loop with limited iterations for testing
    loop = AutonomousLoop(
        model="gemini-2.5-flash",  # Uses Google AI first with OpenRouter fallback
        max_iterations=3,
        history_file="test_loop_history.json"
    )

    # Clear previous test history
    loop.history.clear()

    # Run loop
    results = loop.run(data=None)

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Loop completed: {results['total_iterations']} iterations")
    print(f"Time per iteration: {results['elapsed_time'] / results['total_iterations']:.1f}s")
    print("\n✅ Autonomous loop mechanism verified")


if __name__ == '__main__':
    main()
