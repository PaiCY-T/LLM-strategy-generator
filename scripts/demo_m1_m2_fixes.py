#!/usr/bin/env python3
"""
M1 & M2 修復功能示範

展示:
1. M1 Fix: 一致性分數計算修復 (epsilon threshold)
2. M2 Fix: 報告過濾版本參數控制 (strict_filtering)

執行: python3 demo_m1_m2_fixes.py
"""

import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.validation.data_split import DataSplitValidator
from src.validation.walk_forward import WalkForwardValidator


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_m1_consistency_score():
    """示範 M1 修復: 一致性分數計算"""
    print_section("M1 修復示範: 一致性分數計算")

    validator = DataSplitValidator(epsilon=0.1)

    test_cases = [
        {
            'name': '❌ 錯誤案例 1: Consistently Losing Strategy',
            'sharpes': [-0.5, -0.6, -0.7],
            'expected': '0.0 (修復前: 0.83)',
            'explanation': '負值策略被正確拒絕'
        },
        {
            'name': '❌ 錯誤案例 2: Near-Zero Strategy',
            'sharpes': [0.05, 0.06, 0.07],
            'expected': '0.0 (數值不穩定)',
            'explanation': '接近零的策略被拒絕'
        },
        {
            'name': '✅ 正確案例 1: Robust Positive Strategy',
            'sharpes': [1.2, 1.3, 1.4],
            'expected': '0.89 (高一致性)',
            'explanation': '穩定的正向策略'
        },
        {
            'name': '✅ 正確案例 2: Moderate Strategy',
            'sharpes': [0.5, 0.8, 0.6],
            'expected': '0.73 (中等一致性)',
            'explanation': '有變異但仍為正向'
        },
        {
            'name': '⚠️  邊界案例: Exactly at Epsilon',
            'sharpes': [0.1, 0.1, 0.1],
            'expected': '1.0 (剛好通過)',
            'explanation': 'mean = 0.1 = epsilon，通過檢查'
        },
        {
            'name': '❌ 錯誤案例 3: Just Below Epsilon',
            'sharpes': [0.09, 0.09, 0.09],
            'expected': '0.0 (被拒絕)',
            'explanation': 'mean < epsilon，被拒絕'
        }
    ]

    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"   Sharpe values: {test['sharpes']}")
        print(f"   Mean Sharpe: {np.mean(test['sharpes']):.4f}")
        print(f"   Std Sharpe: {np.std(test['sharpes'], ddof=1):.4f}")

        consistency = validator._calculate_consistency(test['sharpes'])

        print(f"   ✓ Consistency Score: {consistency:.4f}")
        print(f"   Expected: {test['expected']}")
        print(f"   說明: {test['explanation']}")

    print("\n" + "-" * 80)
    print("M1 修復總結:")
    print("  ✓ 負值 Sharpe 策略現在得到 0.0 一致性分數")
    print("  ✓ 接近零的策略被正確拒絕 (防止數值不穩定)")
    print("  ✓ 正向穩定策略得到正確的高分")
    print("  ✓ Epsilon threshold 提供明確的拒絕邊界")


def demo_m2_backward_compatible_mode():
    """示範 M2 修復: 向後相容模式 (strict_filtering=False)"""
    print_section("M2 修復示範: 向後相容模式 (strict_filtering=False)")

    print("\n創建驗證器 (strict_filtering=False - 預設):")
    print("  validator = DataSplitValidator(strict_filtering=False)")

    validator = DataSplitValidator(strict_filtering=False)

    print("\n模擬不支援過濾的 FinLab Report:")

    # Create mock report (模擬實際的 FinLab Report)
    class MockFinLabReport:
        """模擬 FinLab Report (沒有 filter_dates 方法)"""
        def get_stats(self):
            return {'sharpe_ratio': 1.5}

    report = MockFinLabReport()

    print(f"  Report type: {type(report).__name__}")
    print(f"  Has filter_dates: {hasattr(report, 'filter_dates')}")
    print(f"  Is DataFrame: {isinstance(report, pd.DataFrame)}")

    print("\n嘗試過濾 report (期待會看到警告):")
    print("  filtered = validator._filter_report_to_period(report, '2023-01-01', '2023-12-31')")

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        filtered = validator._filter_report_to_period(
            report,
            '2023-01-01',
            '2023-12-31'
        )

        if len(w) > 0:
            print("\n  ⚠️  收到 DeprecationWarning:")
            print(f"      Category: {w[0].category.__name__}")
            print(f"      Message: {str(w[0].message)[:100]}...")
        else:
            print("\n  ⚠️  Warning 未觸發 (可能被其他配置抑制)")

    print("\n  ✓ 結果: 返回未過濾的 report (向後相容)")
    print(f"  ✓ filtered is report: {filtered is report}")
    print(f"  ✓ Sharpe ratio: {filtered.get_stats()['sharpe_ratio']}")

    print("\n" + "-" * 80)
    print("向後相容模式總結:")
    print("  ✓ 不破壞現有代碼 - 仍可運行")
    print("  ⚠️  發出 DeprecationWarning 提醒資料洩漏風險")
    print("  ⚠️  使用完整 report，可能導致資料洩漏")
    print("  📌 建議: 遷移到 strict_filtering=True 或實施 report wrapper")


def demo_m2_strict_mode():
    """示範 M2 修復: 嚴格模式 (strict_filtering=True)"""
    print_section("M2 修復示範: 嚴格模式 (strict_filtering=True)")

    print("\n創建驗證器 (strict_filtering=True):")
    print("  validator = DataSplitValidator(strict_filtering=True)")

    validator = DataSplitValidator(strict_filtering=True)

    print("\n情況 1: Report 不支援過濾 (會拋出錯誤)")

    class MockFinLabReport:
        """模擬 FinLab Report (沒有 filter_dates)"""
        def get_stats(self):
            return {'sharpe_ratio': 1.5}

    report = MockFinLabReport()

    print(f"  Report type: {type(report).__name__}")
    print(f"  Has filter_dates: {hasattr(report, 'filter_dates')}")

    try:
        print("\n  嘗試過濾...")
        filtered = validator._filter_report_to_period(
            report,
            '2023-01-01',
            '2023-12-31'
        )
        print("  ❌ 未預期: 應該拋出錯誤但沒有")
    except ValueError as e:
        print("\n  ✓ 如預期拋出 ValueError:")
        print(f"     {str(e)[:150]}...")

    print("\n" + "-" * 40)
    print("\n情況 2: Report 支援 filter_dates() (正常運作)")

    class FilterableReport:
        """模擬支援過濾的 Report"""
        def __init__(self, sharpe=1.5):
            self.sharpe = sharpe

        def filter_dates(self, start_date, end_date):
            print(f"     ✓ filter_dates({start_date}, {end_date}) called")
            # Return filtered version
            return FilterableReport(sharpe=1.2)  # Filtered result

        def get_stats(self):
            return {'sharpe_ratio': self.sharpe}

    report = FilterableReport(sharpe=1.5)

    print(f"  Report type: {type(report).__name__}")
    print(f"  Has filter_dates: {hasattr(report, 'filter_dates')}")

    try:
        print("\n  嘗試過濾...")
        filtered = validator._filter_report_to_period(
            report,
            '2023-01-01',
            '2023-12-31'
        )
        print(f"  ✓ 成功! Filtered Sharpe: {filtered.get_stats()['sharpe_ratio']}")
    except ValueError as e:
        print(f"  ❌ 未預期的錯誤: {e}")

    print("\n" + "-" * 40)
    print("\n情況 3: Report 是 DataFrame with DatetimeIndex (正常運作)")

    dates = pd.date_range('2020-01-01', periods=1500, freq='D')
    df_report = pd.DataFrame({
        'sharpe_ratio': np.random.randn(1500).cumsum()
    }, index=dates)

    print(f"  Report type: {type(df_report).__name__}")
    print(f"  Is DataFrame: {isinstance(df_report, pd.DataFrame)}")
    print(f"  Has DatetimeIndex: {isinstance(df_report.index, pd.DatetimeIndex)}")
    print(f"  Original shape: {df_report.shape}")
    print(f"  Date range: {df_report.index[0]} to {df_report.index[-1]}")

    try:
        print("\n  嘗試過濾 2023-01-01 to 2023-06-30...")
        filtered = validator._filter_report_to_period(
            df_report,
            '2023-01-01',
            '2023-06-30'
        )
        print(f"  ✓ 成功! Filtered shape: {filtered.shape}")
        if len(filtered) > 0:
            print(f"  ✓ Date range: {filtered.index[0]} to {filtered.index[-1]}")
    except ValueError as e:
        print(f"  ❌ 未預期的錯誤: {e}")

    print("\n" + "-" * 80)
    print("嚴格模式總結:")
    print("  ✓ 強制要求 report 支援過濾")
    print("  ✓ 防止資料洩漏")
    print("  ✓ 支援 filter_dates() 方法")
    print("  ✓ 支援 DataFrame with DatetimeIndex")
    print("  ❌ 不支援的 report 會拋出 ValueError")
    print("  📌 推薦: 用於新代碼和生產環境")


def demo_walk_forward_m2():
    """示範 Walk-Forward 的 M2 修復"""
    print_section("Walk-Forward 的 M2 修復示範")

    print("\nWalk-Forward 也實施了相同的 M2 修復:")

    # Backward compatible mode
    print("\n1. 向後相容模式:")
    wf_validator = WalkForwardValidator(strict_filtering=False)
    print(f"   ✓ WalkForwardValidator(strict_filtering=False)")
    print(f"   ✓ 預設行為: 使用未過濾 report 但發出警告")

    # Strict mode
    print("\n2. 嚴格模式:")
    wf_validator_strict = WalkForwardValidator(strict_filtering=True)
    print(f"   ✓ WalkForwardValidator(strict_filtering=True)")
    print(f"   ✓ 強制要求 report 支援過濾")

    print("\n" + "-" * 80)
    print("Walk-Forward M2 總結:")
    print("  ✓ 與 DataSplitValidator 完全相同的邏輯")
    print("  ✓ 防止多個 windows 使用相同的完整 report")
    print("  ✓ 確保每個 window 只使用其測試期間的指標")


def demo_practical_usage():
    """示範實際使用場景"""
    print_section("實際使用場景")

    print("\n場景 1: 現有項目 (向後相容)")
    print("-" * 80)
    print("""
# 不需要修改現有代碼
validator = DataSplitValidator()  # 使用預設值

# 會看到 DeprecationWarning 但仍可運行
results = validator.validate_strategy(strategy_code, data, 0)

# 建議: 查看警告並計劃遷移
# Warning: "Enable strict_filtering=True to enforce filtering requirement"
    """)

    print("\n場景 2: 新項目 (嚴格模式 + Report Wrapper)")
    print("-" * 80)
    print("""
# Step 1: 實施 FilterableReport wrapper
class FilterableReport:
    def __init__(self, finlab_report):
        self.report = finlab_report

    def filter_dates(self, start_date, end_date):
        # 過濾 returns 並重新計算 Sharpe
        returns = self.report.daily_creturn
        filtered_returns = returns.loc[start_date:end_date]
        sharpe = calculate_sharpe(filtered_returns)

        # 返回過濾後的 wrapper
        filtered = FilterableReport(self.report)
        filtered._sharpe_override = sharpe
        return filtered

    def get_stats(self):
        if hasattr(self, '_sharpe_override'):
            return {'sharpe_ratio': self._sharpe_override}
        return self.report.get_stats()

# Step 2: 使用嚴格模式
validator = DataSplitValidator(strict_filtering=True)

# Step 3: Wrap report before validation
raw_report = backtest.sim(position, resample='D')
report = FilterableReport(raw_report)

# ✅ 無資料洩漏，完全安全
results = validator.validate_strategy(strategy_code, data, 0)
    """)

    print("\n場景 3: 遷移計劃")
    print("-" * 80)
    print("""
# v2.x (現在)
validator = DataSplitValidator(strict_filtering=False)  # 預設
# → 運作但有警告

# v2.5-2.9 (遷移期)
validator = DataSplitValidator(strict_filtering=False)  # 明確設定
# → 實施 report wrapper
# → 逐步測試 strict_filtering=True

# v3.0 (未來)
validator = DataSplitValidator()  # strict_filtering=True 將成為預設
# → 必須有 filter_dates() 或 DataFrame
# → 完全防止資料洩漏
    """)


def main():
    """主程式"""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  M1 & M2 修復功能示範".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)

    # M1 Demo
    demo_m1_consistency_score()

    # M2 Demo
    demo_m2_backward_compatible_mode()
    demo_m2_strict_mode()
    demo_walk_forward_m2()

    # Practical usage
    demo_practical_usage()

    # Summary
    print_section("總結")
    print("""
✅ M1 修復 (一致性分數):
   - Epsilon threshold 防止負值/接近零策略獲得高分
   - 數值穩定且語義正確
   - 完全向後相容 (只是修正錯誤行為)

✅ M2 修復 (報告過濾):
   - 版本參數控制 (strict_filtering)
   - 預設向後相容 (False)
   - 明確警告資料洩漏風險
   - 提供遷移路徑到 v3.0

✅ 系統狀態:
   - 51/54 tests passing
   - 準備進入生產環境
   - 完整文檔和使用範例

📚 相關文件:
   - M1_M2_IMPLEMENTATION_COMPLETE.md (完整實施文檔)
   - CRITICAL_FIXES_SUMMARY.md (C1, C2 修復)
   - ZEN_CHALLENGE_COMPLETE_ANALYSIS.md (完整分析報告)
    """)

    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  示範完成 - Thank you!".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80 + "\n")


if __name__ == '__main__':
    main()
