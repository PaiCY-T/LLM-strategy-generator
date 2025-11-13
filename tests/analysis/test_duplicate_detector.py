"""
Unit Tests for DuplicateDetector (Task 2.3)
============================================

Comprehensive tests for duplicate strategy detection using Sharpe ratio matching
and AST similarity analysis.

Test Coverage:
- Test 1: Identical Sharpe ratio grouping
- Test 2: High AST similarity (99% similar strategies)
- Test 3: Low AST similarity (different strategies)
- Test 4: AST normalization (variable name handling)
- Test 5: Duplicate report generation (DuplicateGroup dataclass)
- Test 6: Known duplicate pair (strategies 9 and 13)
"""

import ast
import json
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any

from src.analysis.duplicate_detector import (
    DuplicateDetector,
    DuplicateGroup,
    StrategyInfo
)


class TestDuplicateDetector:
    """Test suite for DuplicateDetector class."""

    @pytest.fixture
    def detector(self):
        """Create DuplicateDetector with default settings."""
        return DuplicateDetector()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_strategy_identical(self):
        """Sample strategy code (template for creating identical strategies)."""
        return '''
def create_strategy(data):
    """Sample trading strategy."""
    close = data['close']
    volume = data['volume']

    # Calculate indicators
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()

    # Entry signal
    entry = (close > sma_20) & (close > sma_50) & (volume > 1000000)

    return entry
'''

    @pytest.fixture
    def sample_strategy_different(self):
        """Different strategy with different logic."""
        return '''
def create_strategy(data):
    """Momentum strategy."""
    close = data['close']
    high = data['high']
    low = data['low']

    # Calculate RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # Entry on oversold
    entry = rsi < 30

    return entry
'''

    # ========================================================================
    # Test 1: Identical Sharpe Ratio Grouping
    # ========================================================================

    def test_identical_sharpe_grouping(self, detector, temp_dir, sample_strategy_identical):
        """
        Test 1: Verify Sharpe ratio matching with tolerance 1e-8.

        Creates mock strategies with identical Sharpe ratios and verifies
        they are grouped together for AST comparison.
        """
        # Create three strategies with identical Sharpe ratio
        sharpe_value = 0.9443348034803672
        strategies = []

        for i in range(3):
            strategy = StrategyInfo(
                index=i,
                file_path=f"strategy_{i}.py",
                sharpe_ratio=sharpe_value,
                validation_passed=True,
                code=sample_strategy_identical,
                ast_tree=ast.parse(sample_strategy_identical)
            )
            strategies.append(strategy)

        # Group by Sharpe ratio
        groups = detector._group_by_sharpe(strategies)

        # Verify all strategies are in the same group
        assert len(groups) == 1, "All strategies with identical Sharpe should be in one group"

        sharpe_key = list(groups.keys())[0]
        assert abs(sharpe_key - sharpe_value) <= 1e-8, "Sharpe key should match input"
        assert len(groups[sharpe_key]) == 3, "Group should contain all 3 strategies"

        # Verify tolerance works
        # Add strategy with slightly different Sharpe (within tolerance)
        close_sharpe_strategy = StrategyInfo(
            index=3,
            file_path="strategy_3.py",
            sharpe_ratio=sharpe_value + 1e-9,  # Within tolerance 1e-8
            validation_passed=True,
            code=sample_strategy_identical,
            ast_tree=ast.parse(sample_strategy_identical)
        )
        strategies.append(close_sharpe_strategy)

        groups = detector._group_by_sharpe(strategies)
        assert len(groups) == 1, "Strategy with Sharpe within tolerance should be in same group"
        assert len(groups[sharpe_key]) == 4, "Group should contain all 4 strategies"

    # ========================================================================
    # Test 2: High AST Similarity
    # ========================================================================

    def test_ast_similarity_high(self, detector, temp_dir):
        """
        Test 2: Test 99% similar strategies (only variable names differ).

        Creates two strategies programmatically with same logic but different
        variable names and verifies similarity score >95%.
        """
        # Strategy A: Uses variables x, y, z
        strategy_a = '''
def create_strategy(data):
    """Strategy with variables x, y, z."""
    x = data['close']
    y = data['volume']

    # Calculate moving averages
    z = x.rolling(20).mean()
    w = x.rolling(50).mean()

    # Entry signal
    entry = (x > z) & (x > w) & (y > 1000000)

    return entry
'''

        # Strategy B: Same logic, different variable names (a, b, c)
        strategy_b = '''
def create_strategy(data):
    """Strategy with variables a, b, c."""
    a = data['close']
    b = data['volume']

    # Calculate moving averages
    c = a.rolling(20).mean()
    d = a.rolling(50).mean()

    # Entry signal
    entry = (a > c) & (a > d) & (b > 1000000)

    return entry
'''

        # Create temporary files
        file_a = temp_dir / "strategy_a.py"
        file_b = temp_dir / "strategy_b.py"

        file_a.write_text(strategy_a)
        file_b.write_text(strategy_b)

        # Compare strategies
        similarity = detector.compare_strategies(str(file_a), str(file_b))

        # Verify high similarity
        assert similarity > 0.95, f"Expected similarity >0.95, got {similarity:.2%}"
        print(f"✓ High similarity detected: {similarity:.2%}")

    # ========================================================================
    # Test 3: Low AST Similarity
    # ========================================================================

    def test_ast_similarity_low(self, detector, temp_dir):
        """
        Test 3: Test completely different strategies (<50% similar).

        Creates two strategies with different logic and verifies
        similarity score <50%.
        """
        # Strategy A: Moving average crossover
        strategy_a = '''
def create_strategy(data):
    """Moving average crossover strategy."""
    close = data['close']
    volume = data['volume']

    # Calculate indicators
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()

    # Entry signal
    entry = (close > sma_20) & (close > sma_50) & (volume > 1000000)

    return entry
'''

        # Strategy B: RSI momentum strategy (completely different logic)
        strategy_b = '''
def create_strategy(data):
    """RSI momentum strategy with different structure."""
    prices = data['close']
    highs = data['high']
    lows = data['low']

    # Calculate RSI
    price_changes = prices.diff()
    gains = price_changes.where(price_changes > 0, 0)
    losses = -price_changes.where(price_changes < 0, 0)

    avg_gains = gains.rolling(14).mean()
    avg_losses = losses.rolling(14).mean()

    relative_strength = avg_gains / avg_losses
    rsi = 100 - (100 / (1 + relative_strength))

    # Bollinger bands
    bb_middle = prices.rolling(20).mean()
    bb_std = prices.rolling(20).std()
    bb_upper = bb_middle + (2 * bb_std)
    bb_lower = bb_middle - (2 * bb_std)

    # Complex entry condition
    oversold = rsi < 30
    near_lower_band = prices < bb_lower
    high_volatility = (highs - lows) / prices > 0.05

    entry = oversold & near_lower_band & high_volatility

    return entry
'''

        # Create temporary files
        file_a = temp_dir / "strategy_diff_a.py"
        file_b = temp_dir / "strategy_diff_b.py"

        file_a.write_text(strategy_a)
        file_b.write_text(strategy_b)

        # Compare strategies
        similarity = detector.compare_strategies(str(file_a), str(file_b))

        # Verify low similarity
        assert similarity < 0.50, f"Expected similarity <0.50, got {similarity:.2%}"
        print(f"✓ Low similarity detected: {similarity:.2%}")

    # ========================================================================
    # Test 4: AST Normalization
    # ========================================================================

    def test_normalize_ast(self, detector):
        """
        Test 4: Verify variable name normalization.

        Tests that identical logic with different variable names produces
        identical normalized AST.
        """
        # Code A: x = data.get('revenue')
        code_a = '''
x = data.get('revenue')
y = x * 2
result = y + 10
'''

        # Code B: y = data.get('revenue') - same logic, different variable name
        code_b = '''
y = data.get('revenue')
z = y * 2
result = z + 10
'''

        # Parse AST
        tree_a = ast.parse(code_a)
        tree_b = ast.parse(code_b)

        # Normalize AST
        norm_a = detector.normalize_ast(tree_a)
        norm_b = detector.normalize_ast(tree_b)

        print(f"Normalized A:\n{norm_a}\n")
        print(f"Normalized B:\n{norm_b}\n")

        # Verify normalized versions are identical
        assert norm_a == norm_b, "Normalized AST should be identical for same logic"

        # Verify variable names are replaced
        assert "VAR_" in norm_a, "Variables should be replaced with VAR_N placeholders"
        assert "x" not in norm_a or "VAR_" in norm_a, "Original variable names should be normalized"

        print("✓ AST normalization successful")

    # ========================================================================
    # Test 5: Duplicate Report Generation
    # ========================================================================

    def test_duplicate_report_generation(self, detector, sample_strategy_identical):
        """
        Test 5: Verify DuplicateGroup dataclass structure.

        Checks JSON serialization and required fields.
        """
        # Create duplicate strategies
        strategy_1 = StrategyInfo(
            index=1,
            file_path="strategy_1.py",
            sharpe_ratio=0.95,
            validation_passed=True,
            code=sample_strategy_identical,
            ast_tree=ast.parse(sample_strategy_identical)
        )

        strategy_2 = StrategyInfo(
            index=2,
            file_path="strategy_2.py",
            sharpe_ratio=0.95,
            validation_passed=True,
            code=sample_strategy_identical,
            ast_tree=ast.parse(sample_strategy_identical)
        )

        # Create duplicate group
        group = DuplicateGroup(
            sharpe_ratio=0.95,
            strategies=[strategy_1, strategy_2],
            similarity_score=0.99,
            diff="--- strategy_a\n+++ strategy_b\nNo differences"
        )

        # Verify dataclass structure
        assert group.sharpe_ratio == 0.95, "Sharpe ratio should be set"
        assert len(group.strategies) == 2, "Should contain 2 strategies"
        assert group.similarity_score == 0.99, "Similarity score should be set"
        assert group.diff is not None, "Diff should be present"
        assert group.recommendation == "KEEP_FIRST", "Should recommend keeping first"

        # Test recommendation logic
        strategy_3 = StrategyInfo(
            index=3,
            file_path="strategy_3.py",
            sharpe_ratio=0.95,
            validation_passed=False,
            code=sample_strategy_identical,
            ast_tree=ast.parse(sample_strategy_identical)
        )

        strategy_4 = StrategyInfo(
            index=4,
            file_path="strategy_4.py",
            sharpe_ratio=0.95,
            validation_passed=False,
            code=sample_strategy_identical,
            ast_tree=ast.parse(sample_strategy_identical)
        )

        group_no_validation = DuplicateGroup(
            sharpe_ratio=0.95,
            strategies=[strategy_3, strategy_4],
            similarity_score=0.99
        )

        assert group_no_validation.recommendation == "REVIEW", \
            "Should recommend review when no strategies passed validation"

        # Test JSON serialization of strategy info (excluding ast_tree)
        strategy_dict = {
            'index': strategy_1.index,
            'file_path': strategy_1.file_path,
            'sharpe_ratio': strategy_1.sharpe_ratio,
            'validation_passed': strategy_1.validation_passed
        }

        # Verify JSON serialization works
        json_str = json.dumps(strategy_dict)
        assert json_str is not None, "Should be JSON serializable"

        # Verify can deserialize
        deserialized = json.loads(json_str)
        assert deserialized['index'] == 1, "Index should be preserved"
        assert deserialized['sharpe_ratio'] == 0.95, "Sharpe ratio should be preserved"

        print("✓ DuplicateGroup structure and serialization verified")

    # ========================================================================
    # Test 6: Known Duplicate Pair (Strategies 9 and 13)
    # ========================================================================

    def test_strategies_9_13_duplicates(self, detector, temp_dir):
        """
        Test 6: Specific test for known duplicate pair (strategies 9 and 13).

        Uses mock strategies with same logic to simulate the known duplicate case.
        Sharpe ratio: 0.9443348034803672 (identical)
        Expected: similarity >95%
        """
        # Create strategy 9 - Base momentum strategy
        strategy_9 = '''
def create_strategy(data):
    """Momentum strategy iteration 9."""
    close_price = data['close']
    trading_volume = data['volume']

    # Technical indicators
    short_ma = close_price.rolling(window=20).mean()
    long_ma = close_price.rolling(window=50).mean()

    # Volume filter
    avg_volume = trading_volume.rolling(window=20).mean()
    volume_condition = trading_volume > avg_volume * 1.5

    # Entry conditions
    price_above_short = close_price > short_ma
    price_above_long = close_price > long_ma

    entry_signal = price_above_short & price_above_long & volume_condition

    return entry_signal
'''

        # Create strategy 13 - Same logic with different variable names
        strategy_13 = '''
def create_strategy(data):
    """Momentum strategy iteration 13."""
    price = data['close']
    vol = data['volume']

    # Technical indicators
    sma_20 = price.rolling(window=20).mean()
    sma_50 = price.rolling(window=50).mean()

    # Volume filter
    volume_ma = vol.rolling(window=20).mean()
    volume_check = vol > volume_ma * 1.5

    # Entry conditions
    above_short_ma = price > sma_20
    above_long_ma = price > sma_50

    entry_signal = above_short_ma & above_long_ma & volume_check

    return entry_signal
'''

        # Create strategy files
        file_9 = temp_dir / "generated_strategy_loop_iter9.py"
        file_13 = temp_dir / "generated_strategy_loop_iter13.py"

        file_9.write_text(strategy_9)
        file_13.write_text(strategy_13)

        # Create validation results
        sharpe_value = 0.9443348034803672
        validation_results = {
            'strategies_validation': [
                {
                    'strategy_index': 9,
                    'sharpe_ratio': sharpe_value,
                    'validation_passed': True
                },
                {
                    'strategy_index': 13,
                    'sharpe_ratio': sharpe_value,
                    'validation_passed': True
                }
            ]
        }

        # Find duplicates
        strategy_files = [str(file_9), str(file_13)]
        duplicates = detector.find_duplicates(strategy_files, validation_results)

        # Verify duplicates were found
        assert len(duplicates) > 0, "Should find duplicate pair"

        duplicate_group = duplicates[0]
        assert len(duplicate_group.strategies) == 2, "Should contain both strategies"
        assert abs(duplicate_group.sharpe_ratio - sharpe_value) < 1e-8, \
            f"Sharpe ratio should match {sharpe_value}"

        # Verify both strategies are in the group
        indices = [s.index for s in duplicate_group.strategies]
        assert 9 in indices, "Strategy 9 should be in duplicate group"
        assert 13 in indices, "Strategy 13 should be in duplicate group"

        # Verify similarity score
        similarity = detector.compare_strategies(str(file_9), str(file_13))
        assert similarity > 0.95, \
            f"Strategies 9 and 13 should have >95% similarity, got {similarity:.2%}"

        # Verify recommendation
        assert duplicate_group.recommendation == "KEEP_FIRST", \
            "Should recommend keeping first strategy"

        print(f"✓ Successfully identified strategies 9 and 13 as duplicates")
        print(f"  Sharpe ratio: {duplicate_group.sharpe_ratio}")
        print(f"  Similarity: {similarity:.2%}")
        print(f"  Recommendation: {duplicate_group.recommendation}")

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_file_handling(self, detector, temp_dir):
        """Test graceful handling of empty strategy files."""
        # Create empty file
        empty_file = temp_dir / "generated_strategy_loop_iter99.py"
        empty_file.write_text("")

        validation_results = {
            'strategies_validation': [
                {
                    'strategy_index': 99,
                    'sharpe_ratio': 0.5,
                    'validation_passed': True
                }
            ]
        }

        # Should handle gracefully (parse error)
        duplicates = detector.find_duplicates([str(empty_file)], validation_results)
        assert isinstance(duplicates, list), "Should return list even with errors"

    def test_syntax_error_handling(self, detector, temp_dir):
        """Test graceful handling of syntax errors in strategy files."""
        # Create file with syntax error
        bad_file = temp_dir / "generated_strategy_loop_iter98.py"
        bad_file.write_text("def bad_syntax(\n    return invalid")

        validation_results = {
            'strategies_validation': [
                {
                    'strategy_index': 98,
                    'sharpe_ratio': 0.5,
                    'validation_passed': True
                }
            ]
        }

        # Should handle gracefully
        duplicates = detector.find_duplicates([str(bad_file)], validation_results)
        assert isinstance(duplicates, list), "Should return list even with syntax errors"

    def test_zero_sharpe_ratio(self, detector):
        """Test handling of strategies with zero Sharpe ratio."""
        strategies = [
            StrategyInfo(
                index=1,
                file_path="strategy_1.py",
                sharpe_ratio=0.0,
                validation_passed=True,
                code="pass",
                ast_tree=ast.parse("pass")
            ),
            StrategyInfo(
                index=2,
                file_path="strategy_2.py",
                sharpe_ratio=0.0,
                validation_passed=True,
                code="pass",
                ast_tree=ast.parse("pass")
            )
        ]

        groups = detector._group_by_sharpe(strategies)

        # Should group strategies with zero Sharpe
        assert len(groups) == 1, "Strategies with zero Sharpe should be grouped"
        assert 0.0 in groups, "Zero Sharpe key should exist"
        assert len(groups[0.0]) == 2, "Both strategies should be in zero Sharpe group"

    def test_single_strategy(self, detector, temp_dir, sample_strategy_identical):
        """Test behavior with single strategy (no duplicates possible)."""
        file_1 = temp_dir / "generated_strategy_loop_iter1.py"
        file_1.write_text(sample_strategy_identical)

        validation_results = {
            'strategies_validation': [
                {
                    'strategy_index': 1,
                    'sharpe_ratio': 0.85,
                    'validation_passed': True
                }
            ]
        }

        duplicates = detector.find_duplicates([str(file_1)], validation_results)

        # Should return empty list (no duplicates)
        assert len(duplicates) == 0, "Single strategy should have no duplicates"

    def test_no_validation_results(self, detector, temp_dir, sample_strategy_identical):
        """Test behavior with empty validation results."""
        file_1 = temp_dir / "generated_strategy_loop_iter1.py"
        file_1.write_text(sample_strategy_identical)

        validation_results = {
            'strategies_validation': []
        }

        duplicates = detector.find_duplicates([str(file_1)], validation_results)

        # Should return empty list
        assert len(duplicates) == 0, "No validation results should yield no duplicates"

    def test_custom_thresholds(self, temp_dir, sample_strategy_identical):
        """Test detector with custom Sharpe tolerance and similarity threshold."""
        # Create detector with looser thresholds
        loose_detector = DuplicateDetector(
            sharpe_tolerance=0.01,  # Much larger tolerance
            similarity_threshold=0.80  # Lower similarity requirement
        )

        strategies = [
            StrategyInfo(
                index=1,
                file_path="strategy_1.py",
                sharpe_ratio=0.90,
                validation_passed=True,
                code=sample_strategy_identical,
                ast_tree=ast.parse(sample_strategy_identical)
            ),
            StrategyInfo(
                index=2,
                file_path="strategy_2.py",
                sharpe_ratio=0.905,  # Within 0.01 tolerance
                validation_passed=True,
                code=sample_strategy_identical,
                ast_tree=ast.parse(sample_strategy_identical)
            )
        ]

        groups = loose_detector._group_by_sharpe(strategies)

        # Should group with looser tolerance
        assert len(groups) == 1, "Looser tolerance should group more strategies"
