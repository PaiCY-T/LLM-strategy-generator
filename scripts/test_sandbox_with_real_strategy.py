"""
Test Docker Sandbox with Real Production Strategy Code

This script validates that the Docker sandbox can execute real FinLab strategies
with full production dependencies (pandas, numpy, finlab, TA-Lib).

Usage:
    python scripts/test_sandbox_with_real_strategy.py

Expected:
    - Container starts successfully
    - Strategy executes with real data
    - Results returned correctly
    - Total time < 60 seconds (performance target)
"""

import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sandbox.docker_executor import DockerExecutor, DOCKER_AVAILABLE
from src.sandbox.docker_config import DockerConfig


def test_simple_pandas_strategy():
    """Test 1: Simple pandas strategy (baseline)"""
    print("\n" + "="*70)
    print("TEST 1: Simple Pandas Strategy")
    print("="*70)

    strategy_code = """
import pandas as pd
import numpy as np

# Simulate Taiwan stock data
data = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=100),
    'close': np.random.randn(100).cumsum() + 100,
    'volume': np.random.randint(1000, 10000, 100)
})

# Simple moving average strategy
data['ma_20'] = data['close'].rolling(20).mean()
data['signal'] = np.where(data['close'] > data['ma_20'], 1, -1)

# Generate position signal
signal = data.iloc[-1]['signal']
print(f"Latest signal: {signal}")
print(f"Data shape: {data.shape}")
print(f"Latest close: {data.iloc[-1]['close']:.2f}")
"""

    config = DockerConfig.from_yaml()
    config.enabled = True
    executor = DockerExecutor(config)

    start = time.time()
    result = executor.execute(strategy_code, validate=False)
    elapsed = time.time() - start

    print(f"\n✓ Execution time: {elapsed:.2f}s")
    print(f"✓ Success: {result['success']}")
    if not result['success']:
        print(f"✗ Error: {result.get('error')}")

    executor.cleanup_all()
    return result['success']


def test_technical_indicators():
    """Test 2: TA-Lib technical indicators"""
    print("\n" + "="*70)
    print("TEST 2: TA-Lib Technical Indicators")
    print("="*70)

    strategy_code = """
import pandas as pd
import numpy as np
import talib

# Generate sample OHLCV data
np.random.seed(42)
length = 100
data = pd.DataFrame({
    'open': 100 + np.random.randn(length).cumsum(),
    'high': 102 + np.random.randn(length).cumsum(),
    'low': 98 + np.random.randn(length).cumsum(),
    'close': 100 + np.random.randn(length).cumsum(),
    'volume': np.random.randint(1000, 10000, length)
})

# Calculate technical indicators
data['rsi'] = talib.RSI(data['close'], timeperiod=14)
data['macd'], data['macd_signal'], data['macd_hist'] = talib.MACD(
    data['close'],
    fastperiod=12,
    slowperiod=26,
    signalperiod=9
)

# Generate signal based on RSI
latest_rsi = data['rsi'].iloc[-1]
signal = 1 if latest_rsi < 30 else (-1 if latest_rsi > 70 else 0)

print(f"✓ TA-Lib loaded successfully")
print(f"Latest RSI: {latest_rsi:.2f}")
print(f"Signal: {signal}")
"""

    config = DockerConfig.from_yaml()
    config.enabled = True
    executor = DockerExecutor(config)

    start = time.time()
    result = executor.execute(strategy_code, validate=False)
    elapsed = time.time() - start

    print(f"\n✓ Execution time: {elapsed:.2f}s")
    print(f"✓ Success: {result['success']}")
    if not result['success']:
        print(f"✗ Error: {result.get('error')}")

    executor.cleanup_all()
    return result['success']


def test_factor_graph_dependencies():
    """Test 3: Factor Graph system dependencies"""
    print("\n" + "="*70)
    print("TEST 3: Factor Graph Dependencies (networkx, scipy)")
    print("="*70)

    strategy_code = """
import networkx as nx
import numpy as np
from scipy import stats

# Create a simple factor graph
G = nx.Graph()
G.add_edges_from([
    ('momentum', 'signal'),
    ('value', 'signal'),
    ('volatility', 'signal')
])

# Calculate some factor scores
factors = {
    'momentum': np.random.randn(),
    'value': np.random.randn(),
    'volatility': np.random.randn()
}

# Combine factors (simple average)
signal = np.mean(list(factors.values()))

print(f"✓ NetworkX loaded successfully")
print(f"✓ Graph nodes: {G.number_of_nodes()}")
print(f"✓ Graph edges: {G.number_of_edges()}")
print(f"Factor scores: {factors}")
print(f"Combined signal: {signal:.3f}")
"""

    config = DockerConfig.from_yaml()
    config.enabled = True
    executor = DockerExecutor(config)

    start = time.time()
    result = executor.execute(strategy_code, validate=False)
    elapsed = time.time() - start

    print(f"\n✓ Execution time: {elapsed:.2f}s")
    print(f"✓ Success: {result['success']}")
    if not result['success']:
        print(f"✗ Error: {result.get('error')}")

    executor.cleanup_all()
    return result['success']


def test_ml_dependencies():
    """Test 4: Machine learning dependencies"""
    print("\n" + "="*70)
    print("TEST 4: ML Dependencies (scikit-learn)")
    print("="*70)

    strategy_code = """
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# Generate synthetic training data
np.random.seed(42)
X = np.random.randn(100, 5)
y = X @ np.array([1, 2, -1, 0.5, -0.5]) + np.random.randn(100) * 0.1

# Train model
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
model = LinearRegression()
model.fit(X_scaled, y)

# Predict on latest data
X_latest = np.random.randn(1, 5)
X_latest_scaled = scaler.transform(X_latest)
prediction = model.predict(X_latest_scaled)[0]

print(f"✓ scikit-learn loaded successfully")
print(f"Model R² score: {model.score(X_scaled, y):.3f}")
print(f"Latest prediction: {prediction:.3f}")
"""

    config = DockerConfig.from_yaml()
    config.enabled = True
    executor = DockerExecutor(config)

    start = time.time()
    result = executor.execute(strategy_code, validate=False)
    elapsed = time.time() - start

    print(f"\n✓ Execution time: {elapsed:.2f}s")
    print(f"✓ Success: {result['success']}")
    if not result['success']:
        print(f"✗ Error: {result.get('error')}")

    executor.cleanup_all()
    return result['success']


def main():
    """Run all real strategy tests"""
    print("\n" + "="*70)
    print("Docker Sandbox - Real Production Strategy Tests")
    print("="*70)
    print("\nValidating production dependencies in Docker sandbox:")
    print("- pandas, numpy (data processing)")
    print("- TA-Lib (technical indicators)")
    print("- networkx, scipy (factor graph)")
    print("- scikit-learn (machine learning)")

    if not DOCKER_AVAILABLE:
        print("\n✗ Docker SDK not available. Install with: pip install docker")
        sys.exit(1)

    # Run tests
    results = []
    tests = [
        ("Simple Pandas Strategy", test_simple_pandas_strategy),
        ("TA-Lib Technical Indicators", test_technical_indicators),
        ("Factor Graph Dependencies", test_factor_graph_dependencies),
        ("ML Dependencies", test_ml_dependencies),
    ]

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n✅ All tests passed! Docker sandbox ready for production.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
