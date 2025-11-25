# LLM策略生成器 - 綜合改善計畫

**文件版本**: v1.0
**創建日期**: 2025-11-25
**資本規模**: 4千萬新台幣 (40M TWD)
**優先級**: P0 (Critical) - 立即執行

---

## 執行摘要

本計畫整合資深量化交易員建議與深度技術分析，針對LLM策略生成器的5個關鍵問題提出系統性解決方案。**重點修正40M TWD資本規模的流動性成本計算**，並採用**Finlab TA-Lib整合**簡化技術指標實現。

### 關鍵發現

1. **P0級嚴重Bug**: `MomentumTemplate._extract_metrics()` 缺失必要欄位導致100%策略被誤判為失敗
2. **因子同質化**: 現有13個因子全為趨勢追蹤型，相關性>0.8
3. **單一指標陷阱**: Sharpe ratio優化忽略交易量、穩定性、週轉率
4. **流動性處理錯誤**: 應為過濾器+成本，而非評分指標
5. **Look-ahead Bias風險**: 缺乏時間旅行擾動測試

### 預期成果

- **Week 1**: Metrics bug修復 → 策略分類正確率 100%
- **Week 1**: 新增RSI、RVOL因子 → 因子多樣性提升 40%
- **Week 1**: 流動性過濾器 (40M TWD) → 零滑價風險策略
- **Week 2**: Bollinger、ER因子 → 市場狀態適應性提升
- **Week 2**: CI/CD look-ahead測試 → 100%新因子覆蓋

---

## 問題分析與解決方案

### P0: Metrics Contract Bug (2小時)

**問題**: `MomentumTemplate._extract_metrics()` 返回不完整metrics導致StrategyMetrics.classify()失敗

**症狀**:
```python
# 當前實現 (src/templates/momentum_template.py:127-132)
metrics = {
    'annual_return': report.metrics.annual_return(),
    'sharpe_ratio': report.metrics.sharpe_ratio(),
    'max_drawdown': report.metrics.max_drawdown()
    # ❌ 缺失 'execution_success': True
    # ❌ 缺失 'total_return': ...
}
```

**後果**: 所有策略被誤判為LEVEL_0 (失敗)，學習循環完全失效

**解決方案**:
```python
# src/templates/momentum_template.py:127-136
def _extract_metrics(self, report) -> Dict[str, Any]:
    """Extract standardized metrics following StrategyMetrics contract."""
    return {
        'execution_success': True,  # ✅ 新增
        'annual_return': report.metrics.annual_return(),
        'total_return': report.metrics.annual_return(),  # ✅ 新增 (使用annual_return作為代理)
        'sharpe_ratio': report.metrics.sharpe_ratio(),
        'max_drawdown': report.metrics.max_drawdown(),
        'sortino_ratio': report.metrics.sortino_ratio(),
        'calmar_ratio': report.metrics.calmar_ratio()
    }
```

**驗證**:
```bash
pytest tests/templates/test_momentum_template.py::test_metrics_contract -v
```

---

### P1: 因子多樣性不足 - RSI因子 (3小時，含TA-Lib整合)

**問題**: 現有13個因子全為趨勢追蹤型 (momentum, ma_filter, breakout等)

**解決方案**: 使用 **Finlab TA-Lib整合** 實現RSI反轉因子

#### 實現 (Matrix-Native V2 + TA-Lib)

```python
# src/factor_library/mean_reversion_factors.py (新檔案)
"""Mean Reversion Factors using Finlab TA-Lib Integration.

參考文件:
- Finlab TA-Lib: https://doc.finlab.tw/details/tech_ind/
- TA-Lib Python: https://ta-lib.github.io/ta-lib-python/
"""

from finlab.dataframe import FinLabDataFrame
from typing import Dict, Any
import talib  # Finlab已內建支援

def rsi_factor(
    container: FinLabDataFrame,
    parameters: Dict[str, Any]
) -> None:
    """RSI Mean Reversion Factor - 反轉訊號因子.

    使用Finlab內建TA-Lib計算RSI，簡化實現並提升準確性。

    策略邏輯:
    - RSI < oversold_threshold (預設30) → 超賣，做多訊號
    - RSI > overbought_threshold (預設70) → 超買，做空訊號 (台股不做空則過濾)

    Parameters:
        rsi_period (int): RSI計算週期 (預設14)
        oversold_threshold (float): 超賣門檻 (預設30)
        overbought_threshold (float): 超買門檻 (預設70)

    Outputs:
        rsi (Dates×Symbols): RSI值 [0-100]
        signal (Dates×Symbols): 訊號強度 [-1.0, 1.0]
    """
    # 參數提取
    rsi_period = parameters.get('rsi_period', 14)
    oversold = parameters.get('oversold_threshold', 30)
    overbought = parameters.get('overbought_threshold', 70)

    # 使用Finlab TA-Lib整合 (比手動pandas計算簡單且準確)
    close = container.get_matrix('close')

    # TA-Lib RSI計算 (自動處理NaN、矩陣廣播)
    rsi = close.apply(lambda x: talib.RSI(x, timeperiod=rsi_period))

    # 訊號生成: 線性映射到 [-1, 1]
    # RSI=0 → signal=1.0 (極度超賣，強烈做多)
    # RSI=50 → signal=0 (中性)
    # RSI=100 → signal=-1.0 (極度超買，強烈做空/過濾)
    signal = (50 - rsi) / 50  # 簡單線性映射

    # 存入container
    container.add_matrix('rsi', rsi)
    container.add_matrix('signal', signal)


# Factor Registration
MEAN_REVERSION_FACTORS = {
    'rsi_factor': {
        'name': 'RSI Mean Reversion',
        'category': 'mean_reversion',
        'function': rsi_factor,
        'description': 'RSI-based mean reversion signals (TA-Lib)',
        'parameters': {
            'rsi_period': {'type': int, 'default': 14, 'range': [5, 50]},
            'oversold_threshold': {'type': float, 'default': 30, 'range': [10, 40]},
            'overbought_threshold': {'type': float, 'default': 70, 'range': [60, 90]}
        },
        'inputs': ['close'],
        'outputs': ['rsi', 'signal'],
        'constraints': {
            'oversold_threshold': lambda p: p < p['overbought_threshold']
        }
    }
}
```

#### Registry整合

```python
# src/factor_library/registry.py (新增)
from .mean_reversion_factors import MEAN_REVERSION_FACTORS

# 在 FACTOR_REGISTRY 中新增
FACTOR_REGISTRY.update(MEAN_REVERSION_FACTORS)
```

#### 單元測試 (含Look-ahead驗證)

```python
# tests/factor_library/test_rsi_factor.py
import pytest
import pandas as pd
import numpy as np
from finlab.dataframe import FinLabDataFrame
from src.factor_library.mean_reversion_factors import rsi_factor

def test_rsi_basic_calculation():
    """Test RSI calculation produces values in [0, 100]."""
    # 構造測試數據
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    symbols = ['2330', '2317']
    close = pd.DataFrame(
        np.random.randn(50, 2).cumsum(axis=0) + 100,
        index=dates,
        columns=symbols
    )

    container = FinLabDataFrame({'close': close})
    rsi_factor(container, {'rsi_period': 14})

    rsi = container.get_matrix('rsi')
    assert (rsi >= 0).all().all()
    assert (rsi <= 100).all().all()

def test_rsi_signal_range():
    """Test signal values are in [-1, 1]."""
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    symbols = ['2330']
    close = pd.DataFrame(
        np.random.randn(50, 1).cumsum(axis=0) + 100,
        index=dates,
        columns=symbols
    )

    container = FinLabDataFrame({'close': close})
    rsi_factor(container, {})

    signal = container.get_matrix('signal')
    assert (signal >= -1.0).all().all()
    assert (signal <= 1.0).all().all()

def test_rsi_no_lookahead_bias():
    """Time Travel Perturbation Test - RSI Factor.

    驗證T時刻的RSI訊號不受T+1數據影響:
    1. 計算原始RSI(T)
    2. 擾動close(T+1) 100次
    3. 斷言RSI(T)保持不變
    """
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    close = pd.DataFrame(
        np.random.randn(50, 1).cumsum(axis=0) + 100,
        index=dates,
        columns=['2330']
    )

    # 原始計算
    container_original = FinLabDataFrame({'close': close.copy()})
    rsi_factor(container_original, {'rsi_period': 14})
    rsi_original = container_original.get_matrix('rsi')

    # 擾動T+1 (最後一天)
    for _ in range(100):
        close_perturbed = close.copy()
        close_perturbed.iloc[-1] = close.iloc[-1] + np.random.randn() * 10

        container_perturbed = FinLabDataFrame({'close': close_perturbed})
        rsi_factor(container_perturbed, {'rsi_period': 14})
        rsi_perturbed = container_perturbed.get_matrix('rsi')

        # 斷言T-1之前的RSI完全不變
        pd.testing.assert_frame_equal(
            rsi_original.iloc[:-1],
            rsi_perturbed.iloc[:-1],
            check_exact=True
        )
```

---

### P1: 因子多樣性不足 - RVOL因子 (3小時，含TA-Lib整合)

**問題**: 缺乏量價確認機制

**解決方案**: 使用Finlab `成交金額` 數據實現相對成交量因子

#### 實現 (TA-Lib OBV + Finlab數據)

```python
# src/factor_library/mean_reversion_factors.py (新增到同檔案)
def rvol_factor(
    container: FinLabDataFrame,
    parameters: Dict[str, Any]
) -> None:
    """Relative Volume Factor - 相對成交量確認因子.

    使用Finlab成交金額數據 + TA-Lib OBV計算量價確認。

    策略邏輯:
    - RVOL > threshold → 成交量放大，確認趨勢
    - OBV上升 + 價格上升 → 多頭確認

    Data Source:
        Finlab: data.get('price:成交金額') - 每日成交金額 (TWD)

    Parameters:
        lookback_period (int): RVOL計算窗口 (預設20天)
        volume_threshold (float): 放量門檻 (預設1.5倍均量)

    Outputs:
        rvol (Dates×Symbols): 相對成交量 [當日量/均量]
        obv (Dates×Symbols): On-Balance Volume
        signal (Dates×Symbols): 量價確認訊號 [0-1]
    """
    # 參數
    lookback = parameters.get('lookback_period', 20)
    threshold = parameters.get('volume_threshold', 1.5)

    # 從Finlab獲取成交金額數據
    try:
        volume_amount = container.get_matrix('成交金額')  # Finlab內建欄位
    except KeyError:
        # Fallback: 如果container沒有，使用finlab.data
        from finlab import data
        volume_amount = data.get('price:成交金額')

    close = container.get_matrix('close')

    # 計算RVOL (相對成交量)
    avg_volume = volume_amount.rolling(window=lookback).mean()
    rvol = volume_amount / avg_volume

    # 使用TA-Lib計算OBV (量價關係)
    obv = close.copy()
    for col in close.columns:
        obv[col] = talib.OBV(close[col].values, volume_amount[col].values)

    # 訊號生成: RVOL放量 + OBV上升
    obv_slope = obv.diff(5) / obv.shift(5)  # 5日OBV變化率
    signal = ((rvol > threshold).astype(float) +
              (obv_slope > 0).astype(float)) / 2  # 平均兩個條件

    container.add_matrix('rvol', rvol)
    container.add_matrix('obv', obv)
    container.add_matrix('signal', signal)


# Registration
MEAN_REVERSION_FACTORS['rvol_factor'] = {
    'name': 'Relative Volume Confirmation',
    'category': 'volume',
    'function': rvol_factor,
    'description': 'Volume-price confirmation using Finlab transaction amount + TA-Lib OBV',
    'parameters': {
        'lookback_period': {'type': int, 'default': 20, 'range': [10, 60]},
        'volume_threshold': {'type': float, 'default': 1.5, 'range': [1.2, 3.0]}
    },
    'inputs': ['close', '成交金額'],
    'outputs': ['rvol', 'obv', 'signal']
}
```

---

### P1: 流動性處理 - 40M TWD資本規模 (4+4=8小時)

**關鍵用戶反饋**:
> "多目標評分公式中的權重 必須加入交易量的權重，我看過太多策略但完全沒有交易量"

**專家建議**: 流動性應為 **過濾器 + 成本懲罰**，而非評分指標

#### 40M TWD資本規模分析

**資本配置假設**:
- 總資本: 4,000萬 TWD
- 單策略配置: 5-10% = 200-400萬 TWD
- 單股票倉位: 2-5% = 80-200萬 TWD (假設20-40檔分散)

**流動性門檻計算**:
```
單日最大交易量 = 單股票倉位 × 換手率
                = 200萬 × 0.2 (假設20%月週轉率 → 1%日週轉率)
                = 4萬 TWD/日

安全流動性門檻 = 單日最大交易量 × 10 (避免衝擊成本)
                = 40萬 TWD/日 ADV (Average Daily Volume)

保守門檻 (推薦) = 100萬 TWD/日 ADV (25倍安全邊際)
```

**Finlab數據應用**:
```python
# 使用Finlab成交金額計算20日平均日成交量 (ADV)
volume_amount = data.get('price:成交金額')  # TWD
adv_20d = volume_amount.rolling(20).mean()

# 流動性分級
liquidity_tier = pd.cut(
    adv_20d,
    bins=[0, 40萬, 100萬, 500萬, float('inf')],
    labels=['禁止', '警告', '安全', '優質']
)
```

#### LiquidityFilter實現

```python
# src/validation/liquidity_filter.py (新檔案)
"""Liquidity Filter for 40M TWD Capital Size.

基於Finlab成交金額數據的流動性過濾器，針對4千萬資本規模優化。
"""

from finlab import data
from finlab.dataframe import FinLabDataFrame
import pandas as pd
from typing import Dict, Any

class LiquidityFilter:
    """流動性過濾器 - 40M TWD資本規模.

    流動性分級 (基於20日平均成交金額):
    - 禁止 (Forbidden): ADV < 40萬 TWD → 完全排除
    - 警告 (Warning): 40萬 <= ADV < 100萬 → 小倉位 (最多1%)
    - 安全 (Safe): 100萬 <= ADV < 500萬 → 正常倉位 (最多5%)
    - 優質 (Premium): ADV >= 500萬 → 無限制 (最多10%)

    資本配置邏輯:
    - 總資本: 4,000萬 TWD
    - 策略配置: 5-10% = 200-400萬
    - 單股倉位: 2-10% (依流動性分級)
    """

    def __init__(
        self,
        capital: float = 40_000_000,  # 4千萬 TWD
        position_pct: float = 0.05,   # 單策略5%配置
        turnover_rate: float = 0.01,  # 1%日週轉率
        safety_multiple: float = 10.0 # 10倍安全邊際
    ):
        self.capital = capital
        self.position_pct = position_pct
        self.turnover_rate = turnover_rate
        self.safety_multiple = safety_multiple

        # 計算流動性門檻
        single_position = capital * position_pct  # 200萬 (假設5%配置)
        daily_trade = single_position * turnover_rate  # 2萬 (1%日週轉)
        self.min_adv = daily_trade * safety_multiple  # 20萬 (10倍安全)

        # 實際使用更保守的門檻
        self.thresholds = {
            'forbidden': 400_000,   # 40萬 (最低門檻)
            'warning': 1_000_000,   # 100萬 (建議門檻)
            'safe': 5_000_000,      # 500萬 (安全門檻)
        }

    def calculate_adv(
        self,
        volume_amount: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        """計算平均日成交量 (ADV).

        Args:
            volume_amount: 成交金額 (Dates×Symbols, TWD)
            window: 計算窗口 (預設20日)

        Returns:
            adv: 平均日成交量 (Dates×Symbols, TWD)
        """
        return volume_amount.rolling(window=window).mean()

    def classify_liquidity(
        self,
        adv: pd.DataFrame
    ) -> pd.DataFrame:
        """流動性分級.

        Returns:
            liquidity_tier: 流動性等級 (Dates×Symbols)
                0 = Forbidden (禁止)
                1 = Warning (警告)
                2 = Safe (安全)
                3 = Premium (優質)
        """
        tier = pd.DataFrame(0, index=adv.index, columns=adv.columns)
        tier[adv >= self.thresholds['forbidden']] = 1
        tier[adv >= self.thresholds['warning']] = 2
        tier[adv >= self.thresholds['safe']] = 3
        return tier

    def apply_filter(
        self,
        container: FinLabDataFrame,
        strict_mode: bool = True
    ) -> FinLabDataFrame:
        """應用流動性過濾.

        Args:
            container: 策略container
            strict_mode: True=禁止tier<2, False=允許tier>=1

        Returns:
            filtered_container: 過濾後的container (低流動性股票訊號=0)
        """
        # 獲取成交金額
        try:
            volume_amount = container.get_matrix('成交金額')
        except KeyError:
            volume_amount = data.get('price:成交金額')

        # 計算ADV和分級
        adv = self.calculate_adv(volume_amount)
        tier = self.classify_liquidity(adv)

        # 構造流動性mask
        if strict_mode:
            liquidity_mask = (tier >= 2)  # 僅保留Safe/Premium
        else:
            liquidity_mask = (tier >= 1)  # 允許Warning以上

        # 過濾訊號
        signal = container.get_matrix('signal')
        filtered_signal = signal * liquidity_mask  # 低流動性→訊號歸零

        # 更新container
        container.add_matrix('liquidity_tier', tier)
        container.add_matrix('liquidity_mask', liquidity_mask.astype(float))
        container.add_matrix('signal', filtered_signal)

        return container
```

#### ExecutionCostModel實現

```python
# src/validation/execution_cost.py (新檔案)
"""Execution Cost Model with Slippage Penalty.

基於Square Root Law的滑價模型，針對40M TWD資本規模。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

class ExecutionCostModel:
    """執行成本模型 - 滑價懲罰.

    滑價公式 (Square Root Law):
        Slippage (bps) = Base_Cost + Impact_Cost
        Impact_Cost = α × sqrt(Trade_Size / ADV) × Volatility

    參數校準 (40M TWD):
        - Base_Cost: 10 bps (手續費+稅)
        - α: 50 (衝擊係數，台股經驗值)
        - Trade_Size: 單次交易金額 (TWD)
        - ADV: 20日平均成交金額 (TWD)
        - Volatility: 20日報酬率標準差 (年化)
    """

    def __init__(
        self,
        base_cost_bps: float = 10.0,     # 基礎成本 (手續費+稅)
        impact_coeff: float = 50.0,      # 衝擊係數
        volatility_window: int = 20,     # 波動率窗口
        adv_window: int = 20              # ADV計算窗口
    ):
        self.base_cost_bps = base_cost_bps
        self.impact_coeff = impact_coeff
        self.vol_window = volatility_window
        self.adv_window = adv_window

    def calculate_slippage(
        self,
        trade_size: pd.DataFrame,   # 交易金額 (Dates×Symbols, TWD)
        adv: pd.DataFrame,          # 平均日成交量 (Dates×Symbols, TWD)
        returns: pd.DataFrame       # 日報酬率 (Dates×Symbols)
    ) -> pd.DataFrame:
        """計算滑價 (bps).

        Returns:
            slippage: 滑價 (Dates×Symbols, basis points)
        """
        # 計算波動率 (年化)
        volatility = returns.rolling(self.vol_window).std() * np.sqrt(252)

        # Square Root Law
        participation_rate = trade_size / adv  # 參與率
        impact_cost = (
            self.impact_coeff *
            np.sqrt(participation_rate) *
            volatility
        )

        # 總滑價 (bps)
        slippage = self.base_cost_bps + impact_cost

        # 限制最大滑價 (避免異常值)
        slippage = slippage.clip(upper=500)  # 最大5%

        return slippage

    def calculate_liquidity_penalty(
        self,
        strategy_return: float,      # 策略年化報酬 (%)
        avg_slippage_bps: float      # 平均滑價 (bps)
    ) -> float:
        """計算流動性懲罰分數.

        懲罰邏輯:
        - 滑價 < 20 bps → 無懲罰
        - 滑價 20-50 bps → 輕度懲罰
        - 滑價 > 50 bps → 重度懲罰

        Returns:
            penalty: 懲罰分數 (越大越差，用於評分公式減項)
        """
        if avg_slippage_bps < 20:
            return 0.0
        elif avg_slippage_bps < 50:
            # 線性懲罰: 20-50 bps → 0-0.5分
            return (avg_slippage_bps - 20) / 60
        else:
            # 二次懲罰: >50 bps → 快速增長
            return 0.5 + (avg_slippage_bps - 50) ** 2 / 10000
```

---

### P1: 多目標評分公式 (6小時)

**用戶要求**: 必須加入交易量權重

**專家建議**: Calmar + Sortino + Stability - Turnover_Cost - Liquidity_Penalty

#### ComprehensiveScorer實現

```python
# src/validation/comprehensive_scorer.py (新檔案)
"""Comprehensive Multi-Objective Scorer.

整合風險調整報酬、穩定性、週轉率成本、流動性懲罰的綜合評分。
"""

from typing import Dict, Any
import numpy as np

class ComprehensiveScorer:
    """綜合評分器 - 多目標優化.

    評分公式:
        Score = w1×Calmar + w2×Sortino + w3×Stability
                - w4×Turnover_Cost - w5×Liquidity_Penalty

    預設權重 (40M TWD資本):
        - Calmar: 30% (風險調整報酬，避免極端drawdown)
        - Sortino: 25% (下行風險，符合台股特性)
        - Stability: 20% (報酬穩定性，避免單月暴賺暴賠)
        - Turnover_Cost: 15% (週轉率成本，控制交易頻率)
        - Liquidity_Penalty: 10% (流動性懲罰，確保可執行性)

    用戶關注重點:
        「必須加入交易量的權重」→ Liquidity_Penalty (10%權重)
    """

    def __init__(
        self,
        weights: Dict[str, float] = None,
        capital: float = 40_000_000
    ):
        self.weights = weights or {
            'calmar': 0.30,
            'sortino': 0.25,
            'stability': 0.20,
            'turnover_cost': 0.15,
            'liquidity_penalty': 0.10
        }
        self.capital = capital

        # 權重總和應為1.0
        assert abs(sum(self.weights.values()) - 1.0) < 1e-6

    def calculate_stability(
        self,
        monthly_returns: np.ndarray
    ) -> float:
        """穩定性指標.

        Stability = 1 - CV(monthly_returns)
        CV = Coefficient of Variation = std / mean

        範圍: [0, 1]，越高越穩定
        """
        if len(monthly_returns) < 3:
            return 0.0

        mean_ret = np.mean(monthly_returns)
        std_ret = np.std(monthly_returns)

        if mean_ret <= 0:
            return 0.0

        cv = std_ret / mean_ret
        stability = 1 / (1 + cv)  # 歸一化到[0,1]

        return stability

    def calculate_turnover_cost(
        self,
        annual_turnover: float,      # 年化週轉率 (%)
        commission_bps: float = 10   # 手續費+稅 (bps)
    ) -> float:
        """週轉率成本.

        Turnover_Cost = Annual_Turnover × Commission × 2
        × 2 是因為買賣都要付手續費

        Returns:
            cost: 年化成本 (%)
        """
        return annual_turnover * (commission_bps / 10000) * 2

    def compute_score(
        self,
        metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """計算綜合評分.

        Args:
            metrics: 策略指標字典
                - calmar_ratio: Calmar比率
                - sortino_ratio: Sortino比率
                - monthly_returns: 月度報酬序列
                - annual_turnover: 年化週轉率 (%)
                - avg_slippage_bps: 平均滑價 (bps)

        Returns:
            scores: 評分結果
                - calmar_score: Calmar分數
                - sortino_score: Sortino分數
                - stability_score: 穩定性分數
                - turnover_penalty: 週轉率懲罰
                - liquidity_penalty: 流動性懲罰
                - total_score: 總分
        """
        from .execution_cost import ExecutionCostModel

        # 1. Calmar分數 (歸一化)
        calmar = metrics.get('calmar_ratio', 0)
        calmar_score = min(calmar / 3.0, 1.0)  # Calmar=3視為滿分

        # 2. Sortino分數 (歸一化)
        sortino = metrics.get('sortino_ratio', 0)
        sortino_score = min(sortino / 2.0, 1.0)  # Sortino=2視為滿分

        # 3. 穩定性分數
        monthly_returns = metrics.get('monthly_returns', [])
        stability_score = self.calculate_stability(monthly_returns)

        # 4. 週轉率懲罰
        annual_turnover = metrics.get('annual_turnover', 0)
        turnover_cost = self.calculate_turnover_cost(annual_turnover)
        turnover_penalty = min(turnover_cost / 0.5, 1.0)  # 50%週轉成本=滿分懲罰

        # 5. 流動性懲罰
        avg_slippage = metrics.get('avg_slippage_bps', 0)
        cost_model = ExecutionCostModel()
        liquidity_penalty = cost_model.calculate_liquidity_penalty(
            strategy_return=metrics.get('annual_return', 0),
            avg_slippage_bps=avg_slippage
        )

        # 6. 綜合評分
        total_score = (
            self.weights['calmar'] * calmar_score +
            self.weights['sortino'] * sortino_score +
            self.weights['stability'] * stability_score -
            self.weights['turnover_cost'] * turnover_penalty -
            self.weights['liquidity_penalty'] * liquidity_penalty
        )

        return {
            'calmar_score': calmar_score,
            'sortino_score': sortino_score,
            'stability_score': stability_score,
            'turnover_penalty': turnover_penalty,
            'liquidity_penalty': liquidity_penalty,
            'total_score': total_score
        }
```

---

### P2: Bollinger %B因子 (2小時，TA-Lib)

**目的**: 波動率均值回歸

#### 實現

```python
# src/factor_library/mean_reversion_factors.py (新增)
def bollinger_percentb_factor(
    container: FinLabDataFrame,
    parameters: Dict[str, Any]
) -> None:
    """Bollinger %B Factor - 波動率均值回歸.

    使用TA-Lib BBANDS計算布林帶，%B判斷相對位置。

    %B公式:
        %B = (Close - Lower_Band) / (Upper_Band - Lower_Band)

    訊號邏輯:
        - %B < 0 → 價格低於下軌，超賣訊號
        - %B > 1 → 價格高於上軌，超買訊號
        - %B ∈ [0.4, 0.6] → 中性區間

    Parameters:
        period (int): BB週期 (預設20)
        std_dev (float): 標準差倍數 (預設2.0)
    """
    import talib

    period = parameters.get('period', 20)
    std_dev = parameters.get('std_dev', 2.0)

    close = container.get_matrix('close')

    # TA-Lib Bollinger Bands
    upper = close.copy()
    middle = close.copy()
    lower = close.copy()

    for col in close.columns:
        u, m, l = talib.BBANDS(
            close[col].values,
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev,
            matype=0  # SMA
        )
        upper[col] = u
        middle[col] = m
        lower[col] = l

    # 計算%B
    percentb = (close - lower) / (upper - lower)

    # 訊號生成: 線性映射
    # %B=0 → signal=1 (超賣)
    # %B=0.5 → signal=0 (中性)
    # %B=1 → signal=-1 (超買)
    signal = (0.5 - percentb) * 2

    container.add_matrix('bb_upper', upper)
    container.add_matrix('bb_middle', middle)
    container.add_matrix('bb_lower', lower)
    container.add_matrix('bb_percentb', percentb)
    container.add_matrix('signal', signal)


# Registration
MEAN_REVERSION_FACTORS['bollinger_percentb_factor'] = {
    'name': 'Bollinger %B',
    'category': 'volatility',
    'function': bollinger_percentb_factor,
    'description': 'Bollinger Bands %B mean reversion (TA-Lib)',
    'parameters': {
        'period': {'type': int, 'default': 20, 'range': [10, 50]},
        'std_dev': {'type': float, 'default': 2.0, 'range': [1.5, 3.0]}
    },
    'inputs': ['close'],
    'outputs': ['bb_upper', 'bb_middle', 'bb_lower', 'bb_percentb', 'signal']
}
```

---

### P2: Efficiency Ratio因子 (3小時)

**目的**: 市場狀態識別 (趨勢 vs 震盪)

#### 實現

```python
# src/factor_library/regime_factors.py (新檔案)
def efficiency_ratio_factor(
    container: FinLabDataFrame,
    parameters: Dict[str, Any]
) -> None:
    """Efficiency Ratio (ER) - 市場效率比率.

    ER = Direction / Volatility
       = abs(Close[t] - Close[t-n]) / sum(abs(Close[i] - Close[i-1]))

    範圍: [0, 1]
    - ER → 1: 強趨勢市場 (單向移動)
    - ER → 0: 震盪市場 (來回波動)

    策略應用:
    - ER > 0.5 → 趨勢策略 (momentum, breakout)
    - ER < 0.3 → 均值回歸策略 (RSI, Bollinger)

    Parameters:
        period (int): ER計算週期 (預設10)
        trend_threshold (float): 趨勢門檻 (預設0.5)
    """
    period = parameters.get('period', 10)
    trend_threshold = parameters.get('trend_threshold', 0.5)

    close = container.get_matrix('close')

    # 計算Direction (淨移動)
    direction = (close - close.shift(period)).abs()

    # 計算Volatility (累積波動)
    daily_change = close.diff().abs()
    volatility = daily_change.rolling(window=period).sum()

    # ER = Direction / Volatility
    er = direction / volatility
    er = er.fillna(0).clip(0, 1)

    # 市場狀態分類
    regime = pd.DataFrame(0, index=er.index, columns=er.columns)
    regime[er > trend_threshold] = 1  # 趨勢市場
    regime[er < (1 - trend_threshold)] = -1  # 震盪市場

    # 訊號: ER本身作為趨勢強度
    signal = er * 2 - 1  # 映射到[-1, 1]

    container.add_matrix('efficiency_ratio', er)
    container.add_matrix('market_regime', regime)
    container.add_matrix('signal', signal)


# Registration
REGIME_FACTORS = {
    'efficiency_ratio_factor': {
        'name': 'Efficiency Ratio',
        'category': 'regime',
        'function': efficiency_ratio_factor,
        'description': 'Market regime identification (trend vs range)',
        'parameters': {
            'period': {'type': int, 'default': 10, 'range': [5, 30]},
            'trend_threshold': {'type': float, 'default': 0.5, 'range': [0.3, 0.7]}
        },
        'inputs': ['close'],
        'outputs': ['efficiency_ratio', 'market_regime', 'signal']
    }
}
```

---

### P2: Look-ahead Bias驗證 (6+4=10小時)

**專家建議**: Time Travel Perturbation Test (TTPT)

#### 三層防護體系

**Layer 1: 單元測試** (6小時)
```python
# tests/factor_library/test_lookahead_bias.py
"""Time Travel Perturbation Test Framework.

對所有新因子執行TTPT驗證:
1. 計算原始訊號 signal(T)
2. 擾動未來數據 data(T+k), k=1,2,3
3. 重新計算訊號 signal'(T)
4. 斷言 signal(T) == signal'(T)
"""

import pytest
import pandas as pd
import numpy as np
from finlab.dataframe import FinLabDataFrame

# 新因子列表 (需要TTPT驗證)
NEW_FACTORS = [
    ('rsi_factor', 'src.factor_library.mean_reversion_factors'),
    ('rvol_factor', 'src.factor_library.mean_reversion_factors'),
    ('bollinger_percentb_factor', 'src.factor_library.mean_reversion_factors'),
    ('efficiency_ratio_factor', 'src.factor_library.regime_factors')
]

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_single_perturbation(factor_name, module_path):
    """TTPT - 單次擾動測試."""
    # 動態導入
    import importlib
    module = importlib.import_module(module_path)
    factor_func = getattr(module, factor_name)

    # 構造測試數據 (50天)
    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    symbols = ['2330', '2317']
    close = pd.DataFrame(
        np.random.randn(50, 2).cumsum(axis=0) + 100,
        index=dates,
        columns=symbols
    )

    # 原始計算
    container_original = FinLabDataFrame({'close': close.copy()})
    factor_func(container_original, {})
    signal_original = container_original.get_matrix('signal')

    # 擾動T+1
    close_perturbed = close.copy()
    close_perturbed.iloc[-1] += np.random.randn(2) * 10  # 擾動最後一天

    container_perturbed = FinLabDataFrame({'close': close_perturbed})
    factor_func(container_perturbed, {})
    signal_perturbed = container_perturbed.get_matrix('signal')

    # 斷言T-1之前完全不變
    pd.testing.assert_frame_equal(
        signal_original.iloc[:-1],
        signal_perturbed.iloc[:-1],
        check_exact=False,
        rtol=1e-10
    )

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_multiple_perturbations(factor_name, module_path):
    """TTPT - 多次擾動測試 (100次)."""
    import importlib
    module = importlib.import_module(module_path)
    factor_func = getattr(module, factor_name)

    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    close = pd.DataFrame(
        np.random.randn(50, 1).cumsum(axis=0) + 100,
        index=dates,
        columns=['2330']
    )

    # 原始訊號
    container_original = FinLabDataFrame({'close': close.copy()})
    factor_func(container_original, {})
    signal_original = container_original.get_matrix('signal')

    # 100次擾動
    for i in range(100):
        close_perturbed = close.copy()
        close_perturbed.iloc[-1] += np.random.randn() * 20

        container_perturbed = FinLabDataFrame({'close': close_perturbed})
        factor_func(container_perturbed, {})
        signal_perturbed = container_perturbed.get_matrix('signal')

        # 必須完全相同
        pd.testing.assert_frame_equal(
            signal_original.iloc[:-1],
            signal_perturbed.iloc[:-1],
            check_exact=False,
            rtol=1e-10,
            err_msg=f"Perturbation {i+1}/100 failed for {factor_name}"
        )

@pytest.mark.parametrize("factor_name,module_path", NEW_FACTORS)
def test_ttpt_multi_day_perturbation(factor_name, module_path):
    """TTPT - 多日擾動測試 (T+1, T+2, T+3)."""
    import importlib
    module = importlib.import_module(module_path)
    factor_func = getattr(module, factor_name)

    dates = pd.date_range('2023-01-01', periods=50, freq='D')
    close = pd.DataFrame(
        np.random.randn(50, 1).cumsum(axis=0) + 100,
        index=dates,
        columns=['2330']
    )

    container_original = FinLabDataFrame({'close': close.copy()})
    factor_func(container_original, {})
    signal_original = container_original.get_matrix('signal')

    # 擾動T+1, T+2, T+3
    for days_ahead in [1, 2, 3]:
        close_perturbed = close.copy()
        close_perturbed.iloc[-days_ahead:] += np.random.randn(days_ahead, 1) * 15

        container_perturbed = FinLabDataFrame({'close': close_perturbed})
        factor_func(container_perturbed, {})
        signal_perturbed = container_perturbed.get_matrix('signal')

        # T-days_ahead之前不變
        pd.testing.assert_frame_equal(
            signal_original.iloc[:-days_ahead],
            signal_perturbed.iloc[:-days_ahead],
            check_exact=False,
            rtol=1e-10,
            err_msg=f"T+{days_ahead} perturbation failed"
        )
```

**Layer 2: CI/CD整合** (2小時)
```yaml
# .github/workflows/ttpt_validation.yml
name: Time Travel Perturbation Test

on:
  pull_request:
    paths:
      - 'src/factor_library/**'
      - 'tests/factor_library/**'

jobs:
  ttpt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run TTPT Tests
        run: |
          pytest tests/factor_library/test_lookahead_bias.py -v --tb=short
      - name: TTPT Coverage Report
        run: |
          pytest tests/factor_library/test_lookahead_bias.py --cov=src/factor_library --cov-report=html
```

**Layer 3: Runtime監控** (2小時)
```python
# src/validation/runtime_ttpt.py
"""Runtime TTPT Monitoring.

生產環境中對新因子進行採樣TTPT驗證 (1%機率)。
"""

import random
from typing import Callable

def runtime_ttpt_check(
    factor_func: Callable,
    container_original,
    parameters: dict,
    sample_rate: float = 0.01
) -> bool:
    """Runtime TTPT檢查 (採樣).

    Args:
        factor_func: 因子函數
        container_original: 原始container
        parameters: 因子參數
        sample_rate: 採樣率 (預設1%)

    Returns:
        passed: True=通過, False=檢測到look-ahead bias
    """
    if random.random() > sample_rate:
        return True  # 跳過採樣

    # 執行TTPT
    signal_original = container_original.get_matrix('signal')

    # 擾動T+1
    close = container_original.get_matrix('close')
    close_perturbed = close.copy()
    close_perturbed.iloc[-1] += np.random.randn(len(close.columns)) * 10

    container_perturbed = FinLabDataFrame({'close': close_perturbed})
    factor_func(container_perturbed, parameters)
    signal_perturbed = container_perturbed.get_matrix('signal')

    # 比較
    try:
        pd.testing.assert_frame_equal(
            signal_original.iloc[:-1],
            signal_perturbed.iloc[:-1],
            rtol=1e-8
        )
        return True
    except AssertionError:
        # 檢測到look-ahead bias!
        logger.error(f"Runtime TTPT failed for {factor_func.__name__}")
        return False
```

---

## 實施時間表

### Week 1: 關鍵修復與基礎因子 (30小時)

**Day 1-2** (16小時):
1. ✅ P0: Metrics Contract Bug修復 (2小時)
   - 修改 `momentum_template.py`
   - 單元測試驗證
   - 回測驗證 (策略分類正確率應100%)

2. ✅ P1: LiquidityFilter實現 (4小時)
   - 40M TWD資本規模計算
   - Finlab `成交金額` 數據整合
   - 流動性分級系統 (Forbidden/Warning/Safe/Premium)
   - 單元測試

3. ✅ P1: ExecutionCostModel實現 (4小時)
   - Square Root Law滑價模型
   - 40M TWD參數校準
   - 流動性懲罰計算
   - 單元測試

4. ✅ P1: ComprehensiveScorer實現 (6小時)
   - 多目標評分公式
   - 權重配置 (Calmar 30%, Sortino 25%, Stability 20%, Turnover 15%, Liquidity 10%)
   - 整合測試

**Day 3** (14小時):
5. ✅ P1: RSI Factor實現 (3小時，TA-Lib)
   - `mean_reversion_factors.py` 新檔案
   - TA-Lib RSI整合
   - Registry註冊
   - 基礎單元測試

6. ✅ P1: RVOL Factor實現 (3小時，TA-Lib)
   - Finlab成交金額數據
   - TA-Lib OBV整合
   - 量價確認邏輯
   - 基礎單元測試

7. ✅ P2: TTPT Framework (6小時)
   - `test_lookahead_bias.py` 框架
   - RSI、RVOL的TTPT測試
   - 100次擾動驗證

8. ⏸️ 整合測試 (2小時)
   - 端到端測試 (LiquidityFilter + Scorer + New Factors)

### Week 2: 市場狀態因子與CI/CD (28小時)

**Day 4** (8小時):
9. ✅ P2: Bollinger %B Factor (2小時，TA-Lib)
   - TA-Lib BBANDS整合
   - %B計算邏輯
   - 基礎測試

10. ✅ P2: Efficiency Ratio Factor (3小時)
    - `regime_factors.py` 新檔案
    - ER計算邏輯
    - 市場狀態分類
    - 基礎測試

11. ⏸️ TTPT擴展測試 (3小時)
    - Bollinger、ER的TTPT測試
    - 多日擾動測試 (T+1, T+2, T+3)

**Day 5** (10小時):
12. ⏸️ CI/CD整合 (2小時)
    - GitHub Actions配置
    - TTPT自動化

13. ⏸️ Runtime TTPT監控 (2小時)
    - 採樣監控系統 (1%)
    - 日誌告警

14. ⏸️ 文檔與示例 (6小時)
    - 新因子使用指南
    - 流動性處理文檔
    - 評分公式說明
    - 完整示例代碼

**Day 6** (10小時):
15. ⏸️ 端到端驗證 (6小時)
    - 100-iteration完整測試
    - 因子多樣性驗證 (相關性矩陣)
    - 流動性過濾效果
    - 評分公式合理性

16. ⏸️ 性能優化 (2小時)
    - TA-Lib計算優化
    - 快取策略

17. ⏸️ 最終審查 (2小時)
    - Code review
    - 文檔完整性
    - 測試覆蓋率 (目標≥80%)

---

## 成功指標

### Phase 1 (Week 1結束):
- ✅ **Metrics Bug**: 策略分類正確率 100% (當前0%)
- ✅ **因子多樣性**: 新增2個反轉因子 (RSI, RVOL)
- ✅ **流動性處理**: LiquidityFilter過濾低流動性股票 (ADV < 100萬)
- ✅ **評分公式**: ComprehensiveScorer整合5個指標
- ✅ **Look-ahead測試**: RSI、RVOL通過100次TTPT

### Phase 2 (Week 2結束):
- ⏸️ **市場狀態因子**: Bollinger %B, Efficiency Ratio上線
- ⏸️ **CI/CD**: TTPT自動化 (100%新因子覆蓋)
- ⏸️ **Runtime監控**: 1%採樣TTPT (零look-ahead檢測)
- ⏸️ **文檔完整性**: 使用指南、API文檔、範例代碼
- ⏸️ **測試覆蓋率**: ≥80% (unit + integration)

### 長期指標 (3個月):
- 策略Sharpe ratio分佈: 中位數 > 1.5 (當前未知)
- 策略多樣性: 因子相關性 < 0.6 (當前>0.8)
- 流動性合規率: 100% (ADV > 100萬)
- Look-ahead Bias: 零檢測 (Runtime TTPT)

---

## 風險與緩解

### 風險1: TA-Lib整合複雜度
- **機率**: 中
- **影響**: RSI、RVOL、Bollinger實現延遲
- **緩解**: Finlab已內建TA-Lib支援，降低整合難度

### 風險2: 流動性數據品質
- **機率**: 低-中
- **影響**: LiquidityFilter誤判
- **緩解**: 使用Finlab `成交金額` 官方數據，品質有保證

### 風險3: TTPT誤報
- **機率**: 低
- **影響**: 正常因子被誤判為look-ahead
- **緩解**: 使用相對容差 (rtol=1e-10)，允許浮點誤差

### 風險4: 評分公式權重爭議
- **機率**: 中
- **影響**: 用戶不滿意權重配置
- **緩解**: 提供可配置權重，文檔說明校準邏輯

---

## 附錄

### A. Finlab數據欄位

**成交金額**:
```python
volume_amount = data.get('price:成交金額')  # TWD, Dates×Symbols
```

**其他可用欄位**:
- `adj_close`, `adj_high`, `adj_low`, `adj_open` (復權價格)
- `buy`, `sell` (前15大券商買賣超)

### B. TA-Lib函數參考

**趨勢指標**:
- `RSI(close, timeperiod)` - 相對強弱指標
- `BBANDS(close, timeperiod, nbdevup, nbdevdn)` - 布林帶
- `OBV(close, volume)` - 能量潮
- `MACD(close, fastperiod, slowperiod, signalperiod)` - MACD

**波動率指標**:
- `ATR(high, low, close, timeperiod)` - 真實波幅
- `NATR(high, low, close, timeperiod)` - 歸一化ATR

**動量指標**:
- `MOM(close, timeperiod)` - 動量
- `ROC(close, timeperiod)` - 變化率

### C. 40M TWD資本流動性分析

**資本配置模型**:
```
總資本: 4,000萬 TWD
├── 策略配置: 5-10% = 200-400萬
│   ├── 單股倉位 (20-40檔): 2-10% = 80-400萬
│   ├── 月週轉率: 20% (假設)
│   └── 日週轉率: 1% (20% / 20交易日)
│
└── 流動性需求:
    ├── 單日交易量: 200萬 × 1% = 2萬 TWD
    ├── 安全門檻 (10倍): 20萬 TWD ADV
    └── 建議門檻 (50倍): 100萬 TWD ADV
```

**實際門檻**:
- Forbidden: ADV < 40萬 (完全排除)
- Warning: 40萬 ≤ ADV < 100萬 (小倉位1%)
- Safe: 100萬 ≤ ADV < 500萬 (正常倉位5%)
- Premium: ADV ≥ 500萬 (無限制10%)

### D. Look-ahead Bias案例

**正確實現** (No Look-ahead):
```python
# T時刻只使用T及之前的數據
rsi_t = talib.RSI(close[:t+1], timeperiod=14)[-1]
```

**錯誤實現** (Look-ahead):
```python
# ❌ 使用了T+1的數據
rsi_t = talib.RSI(close[:t+2], timeperiod=14)[-2]  # 包含T+1!
```

**TTPT檢測邏輯**:
```python
# 如果修改close[T+1]導致signal[T]改變 → Look-ahead!
assert signal_original[T] == signal_perturbed[T]
```

---

## 聯絡與支援

**技術負責人**: Claude (AI Assistant)
**用戶**: jnpi
**專案**: LLM Strategy Generator
**文檔版本**: v1.0 (2025-11-25)

**下一步行動**:
1. ✅ 修復Metrics Contract Bug → 立即執行 (2小時)
2. ✅ 實現LiquidityFilter (40M TWD) → 4小時
3. ✅ 實現RSI + RVOL (TA-Lib) → 6小時
4. ⏸️ TTPT Framework → 6小時
5. ⏸️ ComprehensiveScorer → 6小時

**總計Week 1**: 30小時 (5個工作日，每日6小時)

---

**文檔狀態**: ✅ 完成
**最後更新**: 2025-11-25
**審核狀態**: 待用戶確認
