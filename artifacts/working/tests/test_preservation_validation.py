"""Test preservation validation functionality.

This script demonstrates the _validate_preservation() method detecting
violations when LLM-generated code deviates from champion patterns.
"""

from autonomous_loop import AutonomousLoop, ChampionStrategy
from datetime import datetime


def test_preservation_validation():
    """Test that preservation validation detects pattern violations."""

    # Create autonomous loop instance
    loop = AutonomousLoop(model="google/gemini-2.5-flash", max_iterations=5)

    # Create a mock champion with smoothed ROE and liquidity filter
    champion = ChampionStrategy(
        iteration_num=2,
        code="# Mock champion code",
        parameters={
            'roe_type': 'smoothed',
            'roe_smoothing_window': 4,
            'liquidity_threshold': 500000000
        },
        metrics={'sharpe_ratio': 1.2},
        success_patterns=['smoothed_roe', 'liquidity_filter'],
        timestamp=datetime.now().isoformat()
    )
    loop.champion = champion

    print("="*60)
    print("TESTING PRESERVATION VALIDATION")
    print("="*60)
    print(f"\nChampion Parameters:")
    print(f"  ROE Type: {champion.parameters['roe_type']}")
    print(f"  ROE Window: {champion.parameters['roe_smoothing_window']}")
    print(f"  Liquidity Threshold: {champion.parameters['liquidity_threshold']:,}")

    # Test Case 1: Valid preservation (within tolerance)
    print("\n" + "-"*60)
    print("Test Case 1: Valid Preservation (ROE window 4→5, +25% exceeds ±20%)")
    print("-"*60)

    valid_code = """
def strategy(data):
    roe = data.get('roe')
    trading_value = data.get('trading_value')

    # Smoothed ROE with window=5 (was 4, +25% change)
    roe_smoothed = roe.rolling(window=5).mean()

    # Liquidity filter maintained
    liquid_stocks = data[trading_value > 500000000]

    return liquid_stocks[roe_smoothed > 0.15]
"""

    result = loop._validate_preservation(valid_code)
    print(f"\nResult: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Expected: ❌ FAILED (window deviation 25% > 20% tolerance)")

    # Test Case 2: ROE type violation
    print("\n" + "-"*60)
    print("Test Case 2: ROE Type Violation (smoothed → raw)")
    print("-"*60)

    roe_violation_code = """
def strategy(data):
    roe = data.get('roe')
    trading_value = data.get('trading_value')

    # Using raw ROE with shift instead of smoothed
    roe_lagged = roe.shift(1)

    # Liquidity filter maintained
    liquid_stocks = data[trading_value > 500000000]

    return liquid_stocks[roe_lagged > 0.15]
"""

    result = loop._validate_preservation(roe_violation_code)
    print(f"\nResult: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Expected: ❌ FAILED (ROE type changed from smoothed to raw)")

    # Test Case 3: Liquidity threshold violation
    print("\n" + "-"*60)
    print("Test Case 3: Liquidity Threshold Violation (500M → 300M)")
    print("-"*60)

    liquidity_violation_code = """
def strategy(data):
    roe = data.get('roe')
    trading_value = data.get('trading_value')

    # Smoothed ROE maintained
    roe_smoothed = roe.rolling(window=4).mean()

    # Liquidity threshold relaxed by 40% (500M → 300M)
    liquid_stocks = data[trading_value > 300000000]

    return liquid_stocks[roe_smoothed > 0.15]
"""

    result = loop._validate_preservation(liquidity_violation_code)
    print(f"\nResult: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Expected: ❌ FAILED (threshold relaxed by 40%, allowed max 20%)")

    # Test Case 4: Liquidity filter removal
    print("\n" + "-"*60)
    print("Test Case 4: Liquidity Filter Removal")
    print("-"*60)

    removal_code = """
def strategy(data):
    roe = data.get('roe')

    # Smoothed ROE maintained
    roe_smoothed = roe.rolling(window=4).mean()

    # No liquidity filter
    return data[roe_smoothed > 0.15]
"""

    result = loop._validate_preservation(removal_code)
    print(f"\nResult: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Expected: ❌ FAILED (critical liquidity filter removed)")

    # Test Case 5: Valid incremental improvement
    print("\n" + "-"*60)
    print("Test Case 5: Valid Incremental Improvement (all patterns preserved)")
    print("-"*60)

    valid_improvement_code = """
def strategy(data):
    # Get ROE data
    roe = data.get('roe')

    # Smoothed ROE maintained with window=4
    roe_smoothed = roe.rolling(window=4).mean()

    # Get trading value
    trading_value = data.get('trading_value')

    # Liquidity filter maintained at 500M
    liquid_stocks = data[trading_value > 500000000]

    # Added new quality filter (incremental improvement)
    roa = data.get('roa')
    quality_stocks = liquid_stocks[roa > 0.05]

    return quality_stocks[roe_smoothed > 0.15]
"""

    result = loop._validate_preservation(valid_improvement_code)
    print(f"\nResult: {'✅ PASSED' if result else '❌ FAILED'}")
    print(f"Expected: ✅ PASSED (all critical patterns preserved)")

    print("\n" + "="*60)
    print("PRESERVATION VALIDATION TEST COMPLETE")
    print("="*60)


if __name__ == '__main__':
    test_preservation_validation()
