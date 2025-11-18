# LLM Field Validation Fix - Three-Layered Defense - Design Document

## Overview

**Problem**: LLM strategy generation achieves 0% success rate due to 29.4% invalid field rate (5/17 fields), while Factor Graph achieves 100% success rate using validated field names.

**Solution**: Three-layered defense system mimicking Factor Graph's success pattern:
1. **Layer 1 (Days 3-4)**: Enhanced data field manifest with finlab API verification
2. **Layer 2 (Days 5-6)**: Pattern-based validator with auto-correction
3. **Layer 3 (Days 8-21)**: Configuration-based architecture (LLM generates YAML, not code)

**Design Philosophy**:
- **Test-Driven Development**: All features implemented test-first (90%+ coverage)
- **Evidence-Based**: GPT-5.1 expert validation with calibrated success expectations
- **Factor Graph-Inspired**: Mimic successful patterns (container abstraction → YAML configs)
- **Progressive Enhancement**: 0% → 25-45% (Layer 1) → 40-60% (Layer 2) → 70-85% (Layer 3)

**Key Insight from Factor Graph Analysis**:
```python
# Factor Graph (100% success) - Container abstraction
close = container.get_matrix('close')  # Pre-validated mapping

# LLM Generation (0% success) - Direct API calls
close = data.get('price:收盤價')   # ✅ Correct
volume = data.get('price:成交量')  # ❌ Wrong! Should be 'price:成交金額'
```

**Solution**: LLM generates YAML configs (like Factor Graph's factory pattern), not Python code with field names.

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Strategy Generator                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                Layer 3: Configuration Engine                │ │
│  │                                                             │ │
│  │  LLM Prompt → YAML Config → StrategyFactory → Execution   │ │
│  │      ↓             ↓              ↓              ↓          │ │
│  │  Two-Stage   Schema Valid   Parse Config   Run Strategy    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓ (uses)                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │          Layer 2: Pattern-Based Validator                  │ │
│  │                                                             │ │
│  │  Code Scan → Pattern Match → Auto-Correct → Suggestions   │ │
│  │      ↓            ↓              ↓              ↓           │ │
│  │  AST Parse   Detect Errors   Fix Common     Provide        │ │
│  │              (data.get)      Mistakes       Feedback        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓ (uses)                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │       Layer 1: Enhanced Data Field Manifest                │ │
│  │                                                             │ │
│  │  finlab API → Field Registry → Alias Resolver → Metadata  │ │
│  │      ↓             ↓                ↓              ↓        │ │
│  │  Discover    Store Fields    close→price:     category/    │ │
│  │  All Fields  (17+ fields)    收盤價            frequency   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                            ↓ (verifies against)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    finlab.data API                          │ │
│  │                                                             │ │
│  │  price:收盤價 | price:成交金額 | fundamental_features:ROE  │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Layer 1 Foundation (Days 3-4)**:
```
finlab API Discovery → Field Metadata Creation → Alias Mapping → Cache Storage
                                                        ↓
                                          tests/fixtures/finlab_fields.json
```

**Layer 2 Validation (Days 5-6)**:
```
LLM Generated Code → AST Parser → Pattern Detector → Field Validator (uses Layer 1)
                                                              ↓
                                              Auto-Correction or Error Feedback
```

**Layer 3 Configuration (Days 8-21)**:
```
LLM Prompt (Two-Stage) → YAML Generation → Schema Validation → StrategyFactory
                                                                        ↓
                                               Execution (uses Layer 2 validator)
```

### Three-Layered Defense Integration

**Decision Gates**:
- **Day 7 (Gate 1)**: Layer 1+2 success rate ≥25% required to proceed to Layer 3
- **Day 18 (Gate 2)**: Layer 3 success rate ≥40% required for iterative expansion

**Rollback Strategy**:
- If Layer 3 fails: Fallback to Layer 1+2 with improved prompts
- If Layer 2 fails: Add AST validator or regex-based field extraction
- If Layer 1 fails: Use Factor Graph field list as backup

## Components and Interfaces

### Layer 1: Enhanced Data Field Manifest

#### Component: `src/config/data_fields.py`

**Purpose**: Centralized field registry with alias resolution and metadata management.

**Interface**:
```python
class DataFieldManifest:
    """
    Enhanced data field manifest with finlab API verification.

    Attributes:
        fields: Dict[str, FieldMetadata]  # Canonical field name → metadata
        aliases: Dict[str, str]           # Alias → canonical name
    """

    def get_field(self, field_or_alias: str) -> Optional[FieldMetadata]:
        """
        Resolve field name or alias to metadata.

        Args:
            field_or_alias: Field name or alias (e.g., 'close' or 'price:收盤價')

        Returns:
            FieldMetadata if valid, None otherwise
        """

    def validate_field(self, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate field against finlab API.

        Args:
            field_name: Field name to validate

        Returns:
            (is_valid: bool, suggestion: Optional[str])

        Example:
            >>> manifest.validate_field('price:成交量')
            (False, 'Did you mean "price:成交金額"?')
        """

    def get_aliases(self, canonical_name: str) -> List[str]:
        """Get all aliases for a canonical field name."""

    def get_fields_by_category(self, category: str) -> List[str]:
        """Get all fields in a category (price/fundamental/technical)."""
```

**Data Structure**:
```python
@dataclass
class FieldMetadata:
    """Metadata for a finlab API field."""
    canonical_name: str       # e.g., 'price:收盤價'
    category: str            # 'price', 'fundamental', 'technical'
    frequency: str           # 'daily', 'weekly', 'monthly'
    dtype: str               # 'float', 'int', 'str'
    description_zh: str      # Chinese description
    description_en: str      # English description
    aliases: List[str]       # ['close', '收盤價', 'closing_price']
    example_values: Optional[List[Any]] = None
    valid_range: Optional[Tuple[float, float]] = None
```

**Implementation Details**:
```python
# Example manifest entry
FIELD_MANIFEST = {
    'price:收盤價': FieldMetadata(
        canonical_name='price:收盤價',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日收盤價格',
        description_en='Daily closing price',
        aliases=['close', '收盤價', 'closing_price', 'close_price'],
        valid_range=(0.0, 10000.0)
    ),
    'price:成交金額': FieldMetadata(
        canonical_name='price:成交金額',
        category='price',
        frequency='daily',
        dtype='float',
        description_zh='每日成交金額（單位：千元）',
        description_en='Daily trading value (unit: thousand TWD)',
        aliases=['amount', 'value', '成交金額', 'trading_value', 'volume'],  # ⚠️ 'volume' → amount
        valid_range=(0.0, 1e12)
    ),
    # ... 17+ fields
}

# Alias resolution
ALIAS_MAP = {
    'close': 'price:收盤價',
    '收盤價': 'price:收盤價',
    'volume': 'price:成交金額',  # ⚠️ Common mistake: volume → amount (not shares)
    '成交量': 'price:成交金額',   # ⚠️ Common mistake
    # ... more aliases
}
```

**Testing**:
```python
# tests/test_data_field_manifest.py

def test_alias_resolution():
    """Test alias resolution to canonical names."""
    manifest = DataFieldManifest()
    assert manifest.get_field('close').canonical_name == 'price:收盤價'
    assert manifest.get_field('volume').canonical_name == 'price:成交金額'
    assert manifest.get_field('price:收盤價').canonical_name == 'price:收盤價'

def test_field_validation():
    """Test field validation against finlab API."""
    manifest = DataFieldManifest()

    # Valid field
    is_valid, suggestion = manifest.validate_field('price:收盤價')
    assert is_valid
    assert suggestion is None

    # Invalid field with suggestion
    is_valid, suggestion = manifest.validate_field('price:成交量')
    assert not is_valid
    assert 'price:成交金額' in suggestion

def test_metadata_access():
    """Test metadata retrieval."""
    manifest = DataFieldManifest()
    field = manifest.get_field('close')
    assert field.category == 'price'
    assert field.frequency == 'daily'
    assert field.dtype == 'float'
    assert 'close' in field.aliases
```

#### Component: `scripts/discover_finlab_fields.py`

**Purpose**: Discover all available fields from finlab API and generate field manifest.

**Interface**:
```python
def discover_finlab_fields() -> Dict[str, FieldMetadata]:
    """
    Discover all available fields from finlab API.

    Returns:
        Dictionary mapping canonical field names to metadata

    Raises:
        finlab.APIError: If finlab API is unavailable
    """

def save_field_cache(fields: Dict[str, FieldMetadata], path: str):
    """Save discovered fields to JSON cache."""

def load_field_cache(path: str) -> Dict[str, FieldMetadata]:
    """Load fields from JSON cache."""
```

**Testing**:
```python
# tests/test_finlab_field_discovery.py

def test_finlab_api_field_availability():
    """Test that all discovered fields exist in finlab API."""
    fields = discover_finlab_fields()

    # Verify minimum field count
    assert len(fields) >= 17, "Should discover at least 17 fields"

    # Verify critical fields exist
    assert 'price:收盤價' in fields
    assert 'price:成交金額' in fields
    assert 'fundamental_features:ROE' in fields

    # Verify field metadata completeness
    for field_name, metadata in fields.items():
        assert metadata.canonical_name == field_name
        assert metadata.category in ['price', 'fundamental', 'technical']
        assert metadata.frequency in ['daily', 'weekly', 'monthly']
        assert len(metadata.aliases) > 0
```

### Layer 2: Pattern-Based Validator

#### Component: `src/validation/field_validator.py`

**Purpose**: AST-based code validator with auto-correction for common field errors.

**Interface**:
```python
class FieldValidator:
    """
    Pattern-based validator for LLM-generated code.

    Validates data.get() calls and auto-corrects common mistakes.
    """

    def __init__(self, manifest: DataFieldManifest):
        """Initialize with field manifest."""
        self.manifest = manifest

    def validate_code(self, code: str) -> ValidationResult:
        """
        Validate Python code for field errors.

        Args:
            code: Python code string to validate

        Returns:
            ValidationResult with errors and suggestions
        """

    def auto_correct(self, code: str) -> Tuple[str, List[Correction]]:
        """
        Auto-correct common field mistakes.

        Args:
            code: Python code with potential errors

        Returns:
            (corrected_code: str, corrections: List[Correction])

        Example:
            >>> code = "close = data.get('price:成交量')"
            >>> corrected, fixes = validator.auto_correct(code)
            >>> print(corrected)
            "close = data.get('price:成交金額')"
            >>> print(fixes[0].message)
            "Auto-corrected 'price:成交量' → 'price:成交金額'"
        """
```

**Data Structures**:
```python
@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    errors: List[FieldError]
    warnings: List[FieldWarning]
    suggestions: List[str]

@dataclass
class FieldError:
    """Field validation error."""
    line: int
    column: int
    field_name: str
    error_type: str  # 'invalid_field', 'unknown_field', 'deprecated_field'
    message: str
    suggestion: Optional[str] = None

@dataclass
class Correction:
    """Auto-correction record."""
    line: int
    original: str
    corrected: str
    confidence: float  # 0.0-1.0
    message: str
```

**Implementation Details**:
```python
# AST-based pattern detection
def _extract_data_get_calls(self, code: str) -> List[DataGetCall]:
    """
    Extract all data.get() calls from code using AST.

    Returns:
        List of DataGetCall with line, field_name, context
    """
    tree = ast.parse(code)
    calls = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check if it's data.get('field_name')
            if (isinstance(node.func, ast.Attribute) and
                node.func.attr == 'get' and
                isinstance(node.func.value, ast.Name) and
                node.func.value.id == 'data'):

                if node.args and isinstance(node.args[0], ast.Constant):
                    field_name = node.args[0].value
                    calls.append(DataGetCall(
                        line=node.lineno,
                        field_name=field_name,
                        context=ast.get_source_segment(code, node)
                    ))

    return calls

# Auto-correction for top 20 common mistakes
COMMON_CORRECTIONS = {
    'price:成交量': 'price:成交金額',  # 94% of errors
    'close': 'price:收盤價',           # 6% of errors
    'volume': 'price:成交金額',
    '成交量': 'price:成交金額',
    # ... more common mistakes
}
```

**Testing**:
```python
# tests/test_field_validator.py

def test_invalid_field_detection():
    """Test detection of invalid field names."""
    validator = FieldValidator(DataFieldManifest())

    code = """
    close = data.get('price:成交量')  # Wrong!
    roe = data.get('fundamental_features:本益比')  # Doesn't exist
    """

    result = validator.validate_code(code)
    assert not result.is_valid
    assert len(result.errors) == 2
    assert 'price:成交金額' in result.errors[0].suggestion

def test_common_mistake_autocorrection():
    """Test auto-correction of common mistakes."""
    validator = FieldValidator(DataFieldManifest())

    code = "close = data.get('price:成交量')"
    corrected, corrections = validator.auto_correct(code)

    assert "price:成交金額" in corrected
    assert len(corrections) == 1
    assert corrections[0].confidence >= 0.9  # High confidence

def test_integration_with_manifest():
    """Test validator uses manifest for validation."""
    manifest = DataFieldManifest()
    validator = FieldValidator(manifest)

    code = "close = data.get('close')"  # Alias usage
    result = validator.validate_code(code)

    # Should suggest canonical name
    assert 'price:收盤價' in result.suggestions[0]
```

### Layer 3: Configuration-Based Architecture

#### Component: `src/config/strategy_schema.yaml`

**Purpose**: YAML schema definitions for top 5 strategy patterns.

**Schema Structure**:
```yaml
# SMA Crossover Pattern
sma_crossover:
  type: "momentum"
  description: "Simple Moving Average Crossover Strategy"
  required_fields:
    - field: "price:收盤價"
      alias: "close"
      usage: "Calculate short/long moving averages"
  parameters:
    short_window:
      type: int
      default: 5
      range: [3, 50]
      description: "Short-term MA period"
    long_window:
      type: int
      default: 20
      range: [10, 200]
      description: "Long-term MA period"
  logic:
    entry: "short_ma > long_ma"
    exit: "short_ma < long_ma"
  constraints:
    min_holding_days: 1
    max_position_size: 0.1

# Momentum + Value Pattern
momentum_value:
  type: "mixed"
  description: "Combined Momentum and Value Strategy"
  required_fields:
    - field: "price:收盤價"
      alias: "close"
    - field: "fundamental_features:ROE"
      alias: "roe"
    - field: "fundamental_features:本益比"
      alias: "pe_ratio"
  parameters:
    momentum_period:
      type: int
      default: 20
      range: [5, 60]
    roe_threshold:
      type: float
      default: 0.15
      range: [0.0, 1.0]
    pe_max:
      type: float
      default: 20.0
      range: [5.0, 50.0]
  logic:
    entry: "(momentum > 0) AND (roe > roe_threshold) AND (pe_ratio < pe_max)"
    exit: "momentum < 0"

# ... 3 more patterns (Quality Score, Reversal, Breakout)
```

#### Component: `src/execution/config_executor.py`

**Purpose**: StrategyFactory that parses YAML configs and executes strategies.

**Interface**:
```python
class StrategyFactory:
    """
    Factory for creating strategies from YAML configs.

    Mimics Factor Graph's factory pattern:
    - Factor Graph: FactorMetadata.factory(parameters)
    - Config Mode: StrategyFactory.create(yaml_config)
    """

    def __init__(self, validator: FieldValidator):
        """Initialize with field validator."""
        self.validator = validator

    def parse_config(self, yaml_str: str) -> StrategyConfig:
        """
        Parse YAML config into StrategyConfig object.

        Args:
            yaml_str: YAML configuration string

        Returns:
            StrategyConfig object

        Raises:
            ConfigParseError: If YAML is invalid
            FieldValidationError: If fields don't exist in manifest
        """

    def create_strategy(self, config: StrategyConfig) -> Strategy:
        """
        Create executable strategy from config.

        Args:
            config: Parsed StrategyConfig

        Returns:
            Strategy object ready for backtest
        """

    def execute(self, config: StrategyConfig, data: FinLabData) -> BacktestResult:
        """
        Execute strategy on data.

        Args:
            config: Strategy configuration
            data: finlab.data instance

        Returns:
            BacktestResult with performance metrics
        """
```

**Data Structures**:
```python
@dataclass
class StrategyConfig:
    """Parsed strategy configuration."""
    name: str
    type: str  # 'momentum', 'value', 'quality', 'mixed'
    description: str
    fields: List[FieldMapping]
    parameters: Dict[str, Any]
    entry_logic: str
    exit_logic: str
    constraints: Dict[str, Any]

@dataclass
class FieldMapping:
    """Field mapping in config."""
    canonical_name: str  # 'price:收盤價'
    alias: str           # 'close'
    usage: str          # Description of how field is used
```

**Implementation Details**:
```python
def parse_config(self, yaml_str: str) -> StrategyConfig:
    """Parse YAML config with field validation."""
    config_dict = yaml.safe_load(yaml_str)

    # Extract fields and validate
    fields = []
    for field_spec in config_dict['required_fields']:
        canonical = field_spec['field']

        # Validate field exists in manifest
        is_valid, suggestion = self.validator.manifest.validate_field(canonical)
        if not is_valid:
            raise FieldValidationError(
                f"Invalid field '{canonical}'. {suggestion}"
            )

        fields.append(FieldMapping(
            canonical_name=canonical,
            alias=field_spec['alias'],
            usage=field_spec.get('usage', '')
        ))

    return StrategyConfig(
        name=config_dict['name'],
        type=config_dict['type'],
        fields=fields,
        parameters=config_dict['parameters'],
        entry_logic=config_dict['logic']['entry'],
        exit_logic=config_dict['logic']['exit'],
        constraints=config_dict.get('constraints', {})
    )
```

**Testing**:
```python
# tests/test_config_executor.py

def test_yaml_config_parsing():
    """Test YAML config parsing."""
    factory = StrategyFactory(FieldValidator(DataFieldManifest()))

    yaml_config = """
    name: "SMA Crossover"
    type: "momentum"
    required_fields:
      - field: "price:收盤價"
        alias: "close"
    parameters:
      short_window: 5
      long_window: 20
    logic:
      entry: "short_ma > long_ma"
      exit: "short_ma < long_ma"
    """

    config = factory.parse_config(yaml_config)
    assert config.name == "SMA Crossover"
    assert len(config.fields) == 1
    assert config.fields[0].canonical_name == "price:收盤價"

def test_factory_execution():
    """Test StrategyFactory creates executable strategies."""
    factory = StrategyFactory(FieldValidator(DataFieldManifest()))
    config = factory.parse_config(VALID_SMA_CONFIG)

    strategy = factory.create_strategy(config)
    assert strategy is not None
    assert hasattr(strategy, 'backtest')

def test_invalid_field_rejection():
    """Test configs with invalid fields are rejected."""
    factory = StrategyFactory(FieldValidator(DataFieldManifest()))

    invalid_config = """
    name: "Bad Strategy"
    required_fields:
      - field: "price:成交量"  # Wrong!
        alias: "volume"
    """

    with pytest.raises(FieldValidationError) as exc:
        factory.parse_config(invalid_config)

    assert "price:成交金額" in str(exc.value)
```

#### Component: `src/innovation/two_stage_prompts.py`

**Purpose**: Two-stage LLM prompting system (GPT-5.1 recommendation).

**Interface**:
```python
def generate_field_selection_prompt(
    available_fields: List[str],
    strategy_type: str
) -> str:
    """
    Stage 1: Prompt LLM to select fields for strategy.

    Args:
        available_fields: List from Layer 1 manifest
        strategy_type: 'momentum', 'value', 'quality', 'mixed'

    Returns:
        Prompt string for LLM
    """

def generate_config_creation_prompt(
    selected_fields: List[str],
    strategy_type: str
) -> str:
    """
    Stage 2: Prompt LLM to generate YAML config using selected fields.

    Args:
        selected_fields: Fields chosen in Stage 1
        strategy_type: Strategy type

    Returns:
        Prompt string for LLM
    """
```

**Prompt Templates**:
```python
STAGE1_PROMPT_TEMPLATE = """
## Task: Select Fields for {strategy_type} Strategy

Choose 2-5 fields from the following validated list for a {strategy_type} strategy.

## Available Fields (All Validated):
{field_list_with_descriptions}

## Guidelines:
1. Choose fields relevant to {strategy_type} strategies
2. All fields are guaranteed to exist in finlab API
3. Use canonical names (e.g., 'price:收盤價', not 'close')
4. Return ONLY a JSON list of field names

## Output Format:
```json
{
  "selected_fields": ["price:收盤價", "fundamental_features:ROE"],
  "rationale": "Brief explanation of why these fields work together"
}
```
"""

STAGE2_PROMPT_TEMPLATE = """
## Task: Generate Strategy Configuration YAML

Create a YAML config for a {strategy_type} strategy using these validated fields:
{selected_fields}

## YAML Schema:
```yaml
name: "<strategy_name>"
type: "{strategy_type}"
required_fields:
  - field: "<canonical_field_name>"
    alias: "<short_alias>"
    usage: "<how_field_is_used>"
parameters:
  <param_name>:
    type: int|float|str
    default: <value>
    range: [min, max]
logic:
  entry: "<entry_condition>"
  exit: "<exit_condition>"
```

## Return ONLY valid YAML. No explanation.
"""
```

## Data Models

### Field Manifest Data Model

**Storage Format**: JSON cache in `tests/fixtures/finlab_fields.json`

```json
{
  "fields": {
    "price:收盤價": {
      "canonical_name": "price:收盤價",
      "category": "price",
      "frequency": "daily",
      "dtype": "float",
      "description_zh": "每日收盤價格",
      "description_en": "Daily closing price",
      "aliases": ["close", "收盤價", "closing_price"],
      "valid_range": [0.0, 10000.0],
      "example_values": [100.5, 125.0, 98.3]
    },
    "price:成交金額": {
      "canonical_name": "price:成交金額",
      "category": "price",
      "frequency": "daily",
      "dtype": "float",
      "description_zh": "每日成交金額（千元）",
      "description_en": "Daily trading value (thousand TWD)",
      "aliases": ["amount", "value", "volume", "成交金額"],
      "valid_range": [0.0, 1e12],
      "example_values": [1000000.0, 5000000.0, 3500000.0]
    }
  },
  "alias_map": {
    "close": "price:收盤價",
    "volume": "price:成交金額",
    "roe": "fundamental_features:ROE"
  },
  "categories": {
    "price": ["price:收盤價", "price:成交金額", "price:開盤價"],
    "fundamental": ["fundamental_features:ROE", "fundamental_features:EPS"],
    "technical": ["technical:RSI", "technical:MACD"]
  },
  "metadata": {
    "discovery_date": "2025-11-17",
    "total_fields": 17,
    "finlab_api_version": "0.3.2"
  }
}
```

### Validation Result Data Model

```python
# Validation result for Day 7 checkpoint
{
    "test_id": "20iteration_llm_improvement",
    "timestamp": "2025-11-24T10:30:00",
    "layer": "1+2",
    "results": {
        "total_iterations": 20,
        "successful": 9,           # 45% success rate
        "failed": 11,
        "success_rate": 0.45,
        "field_error_rate": 0.0,   # ✅ 0% field errors
        "avg_execution_time": 28.5
    },
    "field_validation": {
        "total_fields_used": 34,
        "invalid_fields": 0,       # ✅ All valid
        "auto_corrected": 6,       # 6 common mistakes fixed
        "manual_intervention": 0
    },
    "decision": "PASS - Proceed to Layer 3"
}
```

### YAML Config Data Model

```yaml
# Example: SMA Crossover Strategy Config
name: "SMA_Crossover_5_20"
type: "momentum"
description: "5-day and 20-day moving average crossover strategy"

required_fields:
  - field: "price:收盤價"
    alias: "close"
    usage: "Calculate short and long moving averages"

parameters:
  short_window:
    type: int
    default: 5
    range: [3, 50]
    description: "短期均線週期"
  long_window:
    type: int
    default: 20
    range: [10, 200]
    description: "長期均線週期"

logic:
  entry: "short_ma > long_ma"
  exit: "short_ma < long_ma"

constraints:
  min_holding_days: 1
  max_position_size: 0.1
  stop_loss: 0.05

metadata:
  created_by: "LLM"
  creation_date: "2025-11-25"
  tested: true
  success_rate: 0.65
```

## Error Handling

### Layer 1: Manifest Errors

**Error Type**: finlab API Discovery Failure

**Handling**:
```python
def discover_finlab_fields() -> Dict[str, FieldMetadata]:
    """Discover fields with fallback to Factor Graph list."""
    try:
        # Primary: Discover from finlab API
        fields = _query_finlab_api()
        return fields
    except finlab.APIError as e:
        logger.warning(f"finlab API unavailable: {e}")

        # Fallback: Use Factor Graph field list
        logger.info("Using Factor Graph field list as backup")
        return _load_factor_graph_fields()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise FieldDiscoveryError(
            "Failed to discover fields. Check finlab API connection."
        )
```

**Recovery Strategy**:
1. Retry with exponential backoff (3 attempts)
2. Fallback to cached field list from previous run
3. Fallback to Factor Graph field list (last resort)

### Layer 2: Validation Errors

**Error Type**: Invalid Field in Generated Code

**Handling**:
```python
def validate_code(self, code: str) -> ValidationResult:
    """Validate with structured error reporting."""
    errors = []

    for call in self._extract_data_get_calls(code):
        field_name = call.field_name

        # Check if field exists
        is_valid, suggestion = self.manifest.validate_field(field_name)

        if not is_valid:
            errors.append(FieldError(
                line=call.line,
                field_name=field_name,
                error_type='invalid_field',
                message=f"Field '{field_name}' does not exist",
                suggestion=suggestion  # "Did you mean 'price:成交金額'?"
            ))

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        suggestions=self._generate_suggestions(errors)
    )
```

**Auto-Correction Flow**:
```
Invalid Field Detected → Check Common Mistakes → High Confidence (>0.9)?
                                                        ↓ Yes
                                                  Auto-Correct
                                                        ↓
                                            Add to Corrections Log

                                                  ↓ No (Confidence <0.9)
                                              Report Error
                                                        ↓
                                          Provide Top 3 Suggestions
```

### Layer 3: Configuration Errors

**Error Type**: Invalid YAML Config

**Handling**:
```python
def parse_config(self, yaml_str: str) -> StrategyConfig:
    """Parse with comprehensive error handling."""
    try:
        config_dict = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise ConfigParseError(
            f"Invalid YAML syntax: {e}",
            suggestion="Check YAML indentation and structure"
        )

    # Validate schema
    try:
        self._validate_schema(config_dict)
    except SchemaValidationError as e:
        raise ConfigParseError(
            f"Schema validation failed: {e}",
            suggestion="Compare against examples/configs/sma_crossover.yaml"
        )

    # Validate fields (Layer 1 integration)
    for field_spec in config_dict['required_fields']:
        is_valid, suggestion = self.validator.manifest.validate_field(
            field_spec['field']
        )
        if not is_valid:
            raise FieldValidationError(
                f"Invalid field '{field_spec['field']}'. {suggestion}"
            )

    return self._create_config(config_dict)
```

**Recovery Strategy**:
1. **Syntax Error**: Provide line number and YAML syntax guide
2. **Schema Error**: Show expected vs. actual structure
3. **Field Error**: Auto-suggest correct field name (Layer 2 integration)

### Decision Gate Failures

**Day 7 Gate**: Layer 1+2 Success Rate <25%

**Handling**:
```python
def evaluate_checkpoint_day7(results: Dict) -> Decision:
    """Evaluate Day 7 checkpoint results."""
    success_rate = results['success_rate']
    field_error_rate = results['field_error_rate']

    if field_error_rate > 0:
        # CRITICAL: Field errors should be 0%
        return Decision(
            status='FAIL',
            action='ROLLBACK',
            reason=f"Field error rate {field_error_rate:.1%} > 0%",
            next_steps=[
                "Investigate invalid fields in Layer 1 manifest",
                "Check Layer 2 auto-correction logic",
                "Re-run finlab API field discovery"
            ]
        )

    if success_rate < 0.25:
        # Low success rate: Debug Layer 1+2
        return Decision(
            status='FAIL',
            action='DEBUG',
            reason=f"Success rate {success_rate:.1%} < 25%",
            next_steps=[
                "Analyze failure patterns in 20-iteration test",
                "Check if prompts guide LLM to use manifest fields",
                "Consider adding regex/AST validator (Layer 2 enhancement)"
            ]
        )

    # Success: Proceed to Layer 3
    return Decision(
        status='PASS',
        action='PROCEED',
        reason=f"Success rate {success_rate:.1%} ≥ 25%",
        next_steps=["Begin Layer 3 implementation (Days 8-10)"]
    )
```

## Testing Strategy

### TDD Methodology

**Red-Green-Refactor Cycle**:
```
1. RED: Write failing test
2. GREEN: Implement minimal code to pass
3. REFACTOR: Improve code quality
4. COMMIT: Save working state
```

**Coverage Requirements**:
- Unit Tests: ≥90% code coverage
- Integration Tests: ≥70% coverage
- E2E Tests: All decision gates validated

### Layer 1 Testing (Days 3-4)

**Unit Tests**:
```python
# tests/test_data_field_manifest.py

class TestDataFieldManifest:
    """Layer 1 unit tests."""

    def test_alias_resolution(self):
        """Test alias → canonical name resolution."""
        manifest = DataFieldManifest()
        assert manifest.get_field('close').canonical_name == 'price:收盤價'
        assert manifest.get_field('volume').canonical_name == 'price:成交金額'

    def test_field_metadata_access(self):
        """Test metadata retrieval."""
        manifest = DataFieldManifest()
        field = manifest.get_field('price:收盤價')
        assert field.category == 'price'
        assert field.frequency == 'daily'
        assert 'close' in field.aliases

    def test_category_filtering(self):
        """Test get_fields_by_category."""
        manifest = DataFieldManifest()
        price_fields = manifest.get_fields_by_category('price')
        assert 'price:收盤價' in price_fields
        assert 'price:成交金額' in price_fields
```

**Integration Tests**:
```python
# tests/test_finlab_integration.py

def test_finlab_api_field_availability():
    """Test all manifest fields exist in finlab API."""
    manifest = DataFieldManifest()

    for field_name in manifest.fields.keys():
        # Verify field can be queried from finlab
        assert finlab.data.get(field_name) is not None, \
            f"Field '{field_name}' not available in finlab API"
```

### Layer 2 Testing (Days 5-6)

**Unit Tests**:
```python
# tests/test_field_validator.py

class TestFieldValidator:
    """Layer 2 unit tests."""

    def test_invalid_field_detection(self):
        """Test AST-based field error detection."""
        validator = FieldValidator(DataFieldManifest())
        code = "close = data.get('price:成交量')"  # Wrong!

        result = validator.validate_code(code)
        assert not result.is_valid
        assert len(result.errors) == 1
        assert 'price:成交金額' in result.errors[0].suggestion

    def test_common_mistake_autocorrection(self):
        """Test auto-correction of top 20 common mistakes."""
        validator = FieldValidator(DataFieldManifest())

        test_cases = [
            ("data.get('price:成交量')", "data.get('price:成交金額')"),
            ("data.get('close')", "data.get('price:收盤價')"),
            ("data.get('volume')", "data.get('price:成交金額')"),
        ]

        for original, expected in test_cases:
            corrected, _ = validator.auto_correct(original)
            assert expected in corrected

    def test_integration_with_manifest(self):
        """Test validator uses Layer 1 manifest."""
        manifest = DataFieldManifest()
        validator = FieldValidator(manifest)

        # Should accept valid canonical names
        assert validator.validate_code("data.get('price:收盤價')").is_valid

        # Should reject invalid fields
        assert not validator.validate_code("data.get('invalid_field')").is_valid
```

### Layer 3 Testing (Days 11-14)

**Unit Tests**:
```python
# tests/test_config_executor.py

class TestStrategyFactory:
    """Layer 3 unit tests."""

    def test_yaml_config_parsing(self):
        """Test YAML → StrategyConfig parsing."""
        factory = StrategyFactory(FieldValidator(DataFieldManifest()))

        config = factory.parse_config(VALID_SMA_CONFIG)
        assert config.name == "SMA_Crossover_5_20"
        assert config.type == "momentum"
        assert len(config.fields) == 1

    def test_factory_execution(self):
        """Test config → executable strategy."""
        factory = StrategyFactory(FieldValidator(DataFieldManifest()))
        config = factory.parse_config(VALID_SMA_CONFIG)

        strategy = factory.create_strategy(config)
        assert strategy is not None

    def test_invalid_field_rejection(self):
        """Test configs with invalid fields are rejected."""
        factory = StrategyFactory(FieldValidator(DataFieldManifest()))

        invalid_config = """
        name: "Bad Strategy"
        required_fields:
          - field: "price:成交量"  # Invalid!
        """

        with pytest.raises(FieldValidationError):
            factory.parse_config(invalid_config)
```

**Integration Tests**:
```python
# tests/test_config_integration.py

def test_20iteration_config_mode():
    """Test 20-iteration validation in config mode (Day 18)."""
    factory = StrategyFactory(FieldValidator(DataFieldManifest()))

    # Run 20 iterations with LLM generating configs
    results = []
    for i in range(20):
        yaml_config = llm_generate_config(strategy_type='momentum')

        try:
            config = factory.parse_config(yaml_config)
            strategy = factory.create_strategy(config)
            result = strategy.backtest()
            results.append({'iteration': i, 'success': True, 'result': result})
        except Exception as e:
            results.append({'iteration': i, 'success': False, 'error': str(e)})

    success_rate = sum(1 for r in results if r['success']) / 20

    # Day 18 Decision Gate
    assert success_rate >= 0.40, \
        f"Config mode success rate {success_rate:.1%} < 40%"

    # All configs should parse successfully (0% parse errors)
    parse_errors = sum(1 for r in results if not r['success'])
    assert parse_errors == 0, \
        f"{parse_errors} configs failed to parse"
```

### Decision Gate Validation Tests

**Day 7 Checkpoint**:
```python
# tests/test_checkpoint_day7.py

def test_20iteration_llm_improvement():
    """Test Layer 1+2 achieves 25-45% success rate."""
    # Run 20 iterations with Layer 1+2 enabled
    results = run_20iteration_test(
        mode='llm_only',
        enable_manifest=True,
        enable_validator=True
    )

    # Validate success rate
    assert 0.25 <= results.success_rate <= 0.45, \
        f"Success rate {results.success_rate:.1%} outside [25%, 45%]"

    # Validate 0% field errors
    assert results.field_error_rate == 0.0, \
        f"Field error rate {results.field_error_rate:.1%} > 0%"

    # Validate performance
    assert results.avg_execution_time < 30, \
        f"Avg execution time {results.avg_execution_time}s > 30s"
```

**Day 18 Checkpoint**:
```python
# tests/test_checkpoint_day18.py

def test_20iteration_config_mode():
    """Test Layer 3 achieves 40-60% success rate."""
    results = run_20iteration_test(
        mode='config',
        enable_all_layers=True
    )

    # Validate success rate improvement
    assert 0.40 <= results.success_rate <= 0.60, \
        f"Success rate {results.success_rate:.1%} outside [40%, 60%]"

    # Validate YAML validity (100% parsing success)
    assert results.yaml_parse_success_rate == 1.0, \
        f"YAML parse success {results.yaml_parse_success_rate:.1%} < 100%"
```

### Test Execution Timeline

**Days 1-2**: Field discovery tests
- `test_finlab_api_field_availability()`
- `test_field_cache_creation()`

**Days 3-4**: Layer 1 tests
- `test_alias_resolution()`
- `test_field_metadata_access()`
- `test_integration_with_finlab()`

**Days 5-6**: Layer 2 tests
- `test_invalid_field_detection()`
- `test_common_mistake_autocorrection()`
- `test_integration_with_manifest()`

**Day 7**: Decision Gate 1
- `test_20iteration_llm_improvement()` → PASS/FAIL decision

**Days 11-14**: Layer 3 tests
- `test_yaml_config_parsing()`
- `test_factory_execution()`
- `test_invalid_field_rejection()`

**Day 18**: Decision Gate 2
- `test_20iteration_config_mode()` → PASS/FAIL decision

**Day 21**: Final validation
- `test_final_success_rate()` → Target 70-85%

### Continuous Testing

**Pre-commit Hooks**:
```bash
# .git/hooks/pre-commit
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90
mypy src/
black --check src/
```

**CI/CD Integration** (Optional):
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Design Validation

**Expert Review**: GPT-5.1 architectural feedback integrated
- ✅ Conservative success expectations (25-45% → 40-60% → 70-85%)
- ✅ Parallel Week 1 implementation (Day 1-2 discovery + Day 3-6 Layer 1+2 parallel)
- ✅ Enhanced manifest schema with alias resolution
- ✅ Two-stage prompting (field selection → config generation)

**Factor Graph Pattern Alignment**:
- ✅ Layer 3 YAML configs mimic FactorMetadata factory pattern
- ✅ StrategyFactory mimics Factor Graph's pre-validated execution
- ✅ Container abstraction pattern applied to config-based architecture

**Risk Mitigation**:
- ✅ Decision gates at Day 7 and Day 18
- ✅ Fallback strategies for all layers
- ✅ Field error rate monitored continuously (target: 0%)

**Timeline Feasibility**: 21 days
- Week 1 (Days 1-7): Foundation + Layer 1+2 + Checkpoint 1
- Week 2 (Days 8-14): Layer 3 YAML schema + Factory
- Week 3 (Days 15-21): LLM config generation + Iterative expansion

---

**Design Document Status**: ✅ Complete

**Next Steps**:
1. Obtain user approval for design
2. Create tasks.md with detailed implementation tasks
3. Begin Day 1 implementation (finlab field discovery)
