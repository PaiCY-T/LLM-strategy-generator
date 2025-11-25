# Design Document: Comprehensive Improvement Plan

## Overview

本設計文檔描述 LLM 策略生成器綜合改善計畫的技術架構，採用 **TDD (Test-Driven Development)** 方法論，遵循 Red-Green-Refactor 循環。

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     LLM Strategy Generator                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  Templates  │  │  Factors    │  │     Validation          │ │
│  │             │  │             │  │                         │ │
│  │ Momentum    │  │ RSI         │  │ LiquidityFilter         │ │
│  │ Template    │──│ RVOL        │──│ ExecutionCostModel      │ │
│  │ (Fixed)     │  │ Bollinger   │  │ ComprehensiveScorer     │ │
│  │             │  │ ER          │  │ TTPT Framework          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│         │                │                    │                 │
│         ▼                ▼                    ▼                 │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    FinLabDataFrame                          ││
│  │    Container with Matrix Operations (Dates × Symbols)       ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Finlab Data Layer                        ││
│  │    data.get('price:close'), data.get('price:成交金額')       ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
src/
├── templates/
│   └── momentum_template.py          # P0: 修復 _extract_metrics()
├── factor_library/
│   ├── __init__.py
│   ├── registry.py                   # 因子註冊中心
│   ├── mean_reversion_factors.py     # P1: RSI, RVOL, Bollinger
│   └── regime_factors.py             # P2: Efficiency Ratio
├── validation/
│   ├── __init__.py
│   ├── liquidity_filter.py           # P1: 40M TWD 流動性過濾
│   ├── execution_cost.py             # P1: Square Root Law 滑價
│   ├── comprehensive_scorer.py       # P1: 多目標評分
│   └── runtime_ttpt.py               # P2: Runtime TTPT 監控
│
tests/
├── templates/
│   └── test_momentum_template.py     # P0: Metrics 合約測試
├── factor_library/
│   ├── test_rsi_factor.py            # P1: RSI TDD 測試
│   ├── test_rvol_factor.py           # P1: RVOL TDD 測試
│   ├── test_bollinger_factor.py      # P2: Bollinger TDD 測試
│   ├── test_er_factor.py             # P2: ER TDD 測試
│   └── test_lookahead_bias.py        # P2: TTPT 框架
└── validation/
    ├── test_liquidity_filter.py      # P1: 流動性過濾測試
    ├── test_execution_cost.py        # P1: 滑價模型測試
    └── test_comprehensive_scorer.py  # P1: 評分器測試
```

## Detailed Design

### 1. P0: Metrics Contract Fix

**Location**: `src/templates/momentum_template.py`

**Current Issue**:
```python
# 當前實現 (line 127-132) - 缺失欄位
metrics = {
    'annual_return': report.metrics.annual_return(),
    'sharpe_ratio': report.metrics.sharpe_ratio(),
    'max_drawdown': report.metrics.max_drawdown()
    # ❌ 缺失 'execution_success': True
    # ❌ 缺失 'total_return': ...
}
```

**Fixed Design**:
```python
def _extract_metrics(self, report) -> Dict[str, Any]:
    """Extract standardized metrics following StrategyMetrics contract.

    Returns:
        Dict containing all required fields for StrategyMetrics.classify()
    """
    return {
        'execution_success': True,  # ✅ 必要欄位
        'annual_return': report.metrics.annual_return(),
        'total_return': report.metrics.annual_return(),  # ✅ 必要欄位
        'sharpe_ratio': report.metrics.sharpe_ratio(),
        'max_drawdown': report.metrics.max_drawdown(),
        'sortino_ratio': report.metrics.sortino_ratio(),
        'calmar_ratio': report.metrics.calmar_ratio()
    }
```

**TDD Test Design**:
```python
# tests/templates/test_momentum_template.py
class TestMetricsContract:
    """TDD tests for Metrics Contract - Write FIRST"""

    def test_metrics_has_execution_success(self):
        """RED: metrics must have execution_success"""
        metrics = template._extract_metrics(mock_report)
        assert 'execution_success' in metrics
        assert metrics['execution_success'] == True

    def test_metrics_has_total_return(self):
        """RED: metrics must have total_return"""
        metrics = template._extract_metrics(mock_report)
        assert 'total_return' in metrics

    def test_strategy_classification_works(self):
        """RED: classification should not be all LEVEL_0"""
        metrics = template._extract_metrics(mock_report)
        level = StrategyMetrics.classify(metrics)
        assert level != StrategyLevel.LEVEL_0
```

---

### 2. P1: RSI Factor (TA-Lib Integration)

**Location**: `src/factor_library/mean_reversion_factors.py`

**Interface Design**:
```python
def rsi_factor(
    container: FinLabDataFrame,
    parameters: Dict[str, Any]
) -> None:
    """RSI Mean Reversion Factor using TA-Lib.

    Parameters:
        rsi_period (int): RSI計算週期 (預設14)
        oversold_threshold (float): 超賣門檻 (預設30)
        overbought_threshold (float): 超買門檻 (預設70)

    Outputs (added to container):
        rsi (Dates×Symbols): RSI值 [0-100]
        signal (Dates×Symbols): 訊號強度 [-1.0, 1.0]
    """
```

**Data Flow**:
```
close (Dates×Symbols)
    │
    ▼ talib.RSI()
RSI [0-100]
    │
    ▼ Linear mapping: (50-RSI)/50
signal [-1, 1]
    │
    ▼
container.add_matrix('signal', signal)
```

**TDD Test Design**:
```python
# tests/factor_library/test_rsi_factor.py
class TestRSIFactor:
    """TDD tests for RSI Factor - Write FIRST"""

    @pytest.fixture
    def sample_data(self):
        """Standard test fixture"""
        dates = pd.date_range('2023-01-01', periods=50, freq='D')
        close = pd.DataFrame(
            np.random.randn(50, 2).cumsum(axis=0) + 100,
            index=dates, columns=['2330', '2317']
        )
        return FinLabDataFrame({'close': close})

    def test_rsi_range_0_to_100(self, sample_data):
        """RED: RSI must be in [0, 100]"""
        rsi_factor(sample_data, {'rsi_period': 14})
        rsi = sample_data.get_matrix('rsi')
        assert (rsi >= 0).all().all()
        assert (rsi <= 100).all().all()

    def test_signal_range_neg1_to_1(self, sample_data):
        """RED: Signal must be in [-1, 1]"""
        rsi_factor(sample_data, {})
        signal = sample_data.get_matrix('signal')
        assert (signal >= -1.0).all().all()
        assert (signal <= 1.0).all().all()

    def test_no_lookahead_bias(self, sample_data):
        """RED: TTPT - T+1 perturbation must not affect T"""
        # Original calculation
        rsi_factor(sample_data, {})
        signal_orig = sample_data.get_matrix('signal').copy()

        # Perturb T+1
        close = sample_data.get_matrix('close')
        close.iloc[-1] += np.random.randn(2) * 10

        container_perturbed = FinLabDataFrame({'close': close})
        rsi_factor(container_perturbed, {})
        signal_perturbed = container_perturbed.get_matrix('signal')

        # T-1 and before must be identical
        pd.testing.assert_frame_equal(
            signal_orig.iloc[:-1],
            signal_perturbed.iloc[:-1]
        )
```

---

### 3. P1: Liquidity Filter (40M TWD)

**Location**: `src/validation/liquidity_filter.py`

**Class Design**:
```python
class LiquidityFilter:
    """Liquidity Filter for 40M TWD Capital Size.

    Liquidity Tiers (based on 20-day ADV):
        - Forbidden (0): ADV < 40萬 TWD → 完全排除
        - Warning (1): 40萬 <= ADV < 100萬 → 小倉位 (1%)
        - Safe (2): 100萬 <= ADV < 500萬 → 正常倉位 (5%)
        - Premium (3): ADV >= 500萬 → 無限制 (10%)

    Attributes:
        capital (float): Total capital in TWD (default: 40M)
        thresholds (dict): ADV thresholds for each tier
    """

    def __init__(
        self,
        capital: float = 40_000_000,
        position_pct: float = 0.05,
        turnover_rate: float = 0.01,
        safety_multiple: float = 10.0
    ): ...

    def calculate_adv(
        self,
        volume_amount: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame: ...

    def classify_liquidity(
        self,
        adv: pd.DataFrame
    ) -> pd.DataFrame: ...

    def apply_filter(
        self,
        container: FinLabDataFrame,
        strict_mode: bool = True
    ) -> FinLabDataFrame: ...
```

**Tier Classification Logic**:
```
ADV (TWD)          Tier    Max Position    Signal Multiplier
─────────────────────────────────────────────────────────────
< 400,000          0       0%              0.0 (Forbidden)
400,000-1,000,000  1       1%              0.5 (Warning)
1,000,000-5,000,000 2      5%              1.0 (Safe)
>= 5,000,000       3       10%             1.0 (Premium)
```

**TDD Test Design**:
```python
# tests/validation/test_liquidity_filter.py
class TestLiquidityFilter:
    """TDD tests for Liquidity Filter - Write FIRST"""

    @pytest.fixture
    def filter(self):
        return LiquidityFilter(capital=40_000_000)

    def test_tier_forbidden_below_400k(self, filter):
        """RED: ADV < 400k → Tier 0 (Forbidden)"""
        adv = pd.DataFrame({'2330': [300_000]})
        tier = filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 0

    def test_tier_warning_400k_to_1m(self, filter):
        """RED: 400k <= ADV < 1M → Tier 1 (Warning)"""
        adv = pd.DataFrame({'2330': [600_000]})
        tier = filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 1

    def test_tier_safe_1m_to_5m(self, filter):
        """RED: 1M <= ADV < 5M → Tier 2 (Safe)"""
        adv = pd.DataFrame({'2330': [2_000_000]})
        tier = filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 2

    def test_tier_premium_above_5m(self, filter):
        """RED: ADV >= 5M → Tier 3 (Premium)"""
        adv = pd.DataFrame({'2330': [10_000_000]})
        tier = filter.classify_liquidity(adv)
        assert tier.iloc[0, 0] == 3

    def test_strict_mode_filters_warning(self, filter):
        """RED: strict_mode=True filters out Tier 1"""
        # Create container with mixed liquidity
        # After filter, Warning tier signals should be 0
```

---

### 4. P1: Execution Cost Model

**Location**: `src/validation/execution_cost.py`

**Class Design**:
```python
class ExecutionCostModel:
    """Execution Cost Model with Square Root Law Slippage.

    Slippage Formula:
        Slippage (bps) = Base_Cost + α × sqrt(Trade_Size/ADV) × Volatility

    Parameters:
        base_cost_bps (float): 基礎成本 (default: 10 bps)
        impact_coeff (float): 衝擊係數 α (default: 50)
        volatility_window (int): 波動率計算窗口 (default: 20)
    """

    def calculate_slippage(
        self,
        trade_size: pd.DataFrame,
        adv: pd.DataFrame,
        returns: pd.DataFrame
    ) -> pd.DataFrame: ...

    def calculate_liquidity_penalty(
        self,
        strategy_return: float,
        avg_slippage_bps: float
    ) -> float: ...
```

**Penalty Tiers**:
```
Slippage (bps)    Penalty Formula
─────────────────────────────────
< 20              0.0
20-50             (slippage - 20) / 60
> 50              0.5 + (slippage - 50)² / 10000
```

---

### 5. P1: Comprehensive Scorer

**Location**: `src/validation/comprehensive_scorer.py`

**Class Design**:
```python
class ComprehensiveScorer:
    """Multi-Objective Comprehensive Scorer.

    Score Formula:
        Score = w1×Calmar + w2×Sortino + w3×Stability
                - w4×Turnover_Cost - w5×Liquidity_Penalty

    Default Weights (40M TWD):
        - Calmar: 30%
        - Sortino: 25%
        - Stability: 20%
        - Turnover_Cost: 15%
        - Liquidity_Penalty: 10%
    """

    def __init__(
        self,
        weights: Dict[str, float] = None,
        capital: float = 40_000_000
    ): ...

    def calculate_stability(
        self,
        monthly_returns: np.ndarray
    ) -> float: ...

    def calculate_turnover_cost(
        self,
        annual_turnover: float,
        commission_bps: float = 10
    ) -> float: ...

    def compute_score(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, float]: ...
```

---

### 6. P2: TTPT Framework

**Location**: `tests/factor_library/test_lookahead_bias.py`

**Framework Design**:
```python
NEW_FACTORS = [
    ('rsi_factor', 'src.factor_library.mean_reversion_factors'),
    ('rvol_factor', 'src.factor_library.mean_reversion_factors'),
    ('bollinger_percentb_factor', 'src.factor_library.mean_reversion_factors'),
    ('efficiency_ratio_factor', 'src.factor_library.regime_factors')
]

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_single_perturbation(factor_name, module_path):
    """TTPT - Single perturbation test"""

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_100_perturbations(factor_name, module_path):
    """TTPT - 100 random perturbations"""

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_multi_day(factor_name, module_path):
    """TTPT - T+1, T+2, T+3 perturbations"""
```

---

## Data Models

### Factor Registry Entry
```python
FACTOR_ENTRY = {
    'name': str,           # Display name
    'category': str,       # momentum|mean_reversion|volume|regime
    'function': Callable,  # Factor function
    'description': str,    # Documentation
    'parameters': {
        'param_name': {
            'type': type,
            'default': Any,
            'range': [min, max]
        }
    },
    'inputs': List[str],   # Required matrix inputs
    'outputs': List[str],  # Output matrix names
    'constraints': dict    # Parameter constraints
}
```

### Liquidity Tier Enum
```python
class LiquidityTier(IntEnum):
    FORBIDDEN = 0   # ADV < 400k
    WARNING = 1     # 400k <= ADV < 1M
    SAFE = 2        # 1M <= ADV < 5M
    PREMIUM = 3     # ADV >= 5M
```

---

## Error Handling

### Factor Calculation Errors
```python
try:
    rsi = close.apply(lambda x: talib.RSI(x, timeperiod=period))
except Exception as e:
    logger.warning(f"RSI calculation failed: {e}")
    rsi = pd.DataFrame(50, index=close.index, columns=close.columns)
```

### Liquidity Data Fallback
```python
try:
    volume_amount = container.get_matrix('成交金額')
except KeyError:
    from finlab import data
    volume_amount = data.get('price:成交金額')
```

---

## Testing Strategy

### TDD Cycle (Red-Green-Refactor)
```
1. RED: Write failing test first
   └─ Define expected behavior

2. GREEN: Write minimal code to pass
   └─ Implementation just enough to pass

3. REFACTOR: Clean up code
   └─ Maintain test passing
```

### Test Categories
1. **Unit Tests**: Individual function/class tests
2. **Integration Tests**: Component interaction tests
3. **TTPT Tests**: Look-ahead bias verification
4. **E2E Tests**: Full workflow tests

### Coverage Targets
- Unit Tests: ≥ 80%
- TTPT Coverage: 100% for new factors
- Integration: ≥ 70%
