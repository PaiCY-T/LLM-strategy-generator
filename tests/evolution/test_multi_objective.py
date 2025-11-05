"""
Unit tests for multi-objective optimization functions (NSGA-II implementation).

Tests cover:
- Pareto dominance relationships (pareto_dominates function)
- Crowding distance calculation
- Boundary solution handling
- Interior solution distance
- Edge cases and error handling
- Integration with Pareto ranking

References:
    - Deb, K., et al. (2002). "A Fast and Elitist Multiobjective Genetic Algorithm: NSGA-II"
    - IEEE Transactions on Evolutionary Computation, 6(2), 182-197
"""

import pytest
from src.evolution.types import Strategy, MultiObjectiveMetrics
from src.evolution.multi_objective import (
    pareto_dominates,
    calculate_crowding_distance,
    assign_pareto_ranks
)



class TestParetoDominates:
    """
    Comprehensive test suite for pareto_dominates function (Task 13).

    Tests Pareto dominance relationships across all objectives:
    - Maximization objectives: sharpe_ratio, calmar_ratio, total_return, win_rate, annual_return
    - Minimization objective: max_drawdown (less negative is better, e.g., -0.10 > -0.20)

    Coverage includes:
    - Clear dominance scenarios (all objectives better)
    - No dominance scenarios (mixed performance)
    - Equal metrics (tie cases)
    - Failed backtest scenarios
    - Edge cases (zero values, extreme values, negative values)
    - Mathematical properties (symmetry, transitivity)
    """

    def test_clear_dominance_all_objectives_better(self):
        """Test clear dominance when A is better in all objectives."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,  # Better: -10% vs -20%
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,
            calmar_ratio=1.8,
            max_drawdown=-0.20,  # Worse: -20% drawdown
            total_return=0.40,
            win_rate=0.55,
            annual_return=0.18,
            success=True
        )

        # A dominates B (better in all objectives)
        assert pareto_dominates(metrics_a, metrics_b) is True

        # B does not dominate A (worse in all objectives)
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_clear_dominance_single_objective_better(self):
        """Test dominance when A is better in one objective, equal in others."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,  # Better
            calmar_ratio=2.0,  # Equal
            max_drawdown=-0.15,  # Equal
            total_return=0.45,  # Equal
            win_rate=0.58,  # Equal
            annual_return=0.19,  # Equal
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,  # Worse
            calmar_ratio=2.0,  # Equal
            max_drawdown=-0.15,  # Equal
            total_return=0.45,  # Equal
            win_rate=0.58,  # Equal
            annual_return=0.19,  # Equal
            success=True
        )

        # A dominates B (better in sharpe_ratio, equal in rest)
        assert pareto_dominates(metrics_a, metrics_b) is True

        # B does not dominate A
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_no_dominance_mixed_performance(self):
        """Test non-dominated case where each has better and worse objectives."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.8,    # A better
            calmar_ratio=1.5,    # B better
            max_drawdown=-0.12,  # A better
            total_return=0.45,   # B better
            win_rate=0.58,       # A better
            annual_return=0.19,  # B better
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.4,    # A better
            calmar_ratio=2.2,    # B better
            max_drawdown=-0.11,  # B better (less negative)
            total_return=0.48,   # B better
            win_rate=0.59,       # B better
            annual_return=0.21,  # B better
            success=True
        )

        # Neither dominates the other (mixed performance)
        assert pareto_dominates(metrics_a, metrics_b) is False
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_equal_metrics_no_dominance(self):
        """Test that equal metrics result in no dominance (tie)."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.58,
            annual_return=0.19,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,  # All equal
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.58,
            annual_return=0.19,
            success=True
        )

        # Equal metrics → no dominance (requires strict improvement)
        assert pareto_dominates(metrics_a, metrics_b) is False
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_failed_backtest_never_dominates(self):
        """Test that failed backtests cannot dominate or be dominated."""
        metrics_success = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_failed = MultiObjectiveMetrics(
            sharpe_ratio=0.8,  # Worse metrics but failed
            calmar_ratio=1.0,
            max_drawdown=-0.30,
            total_return=0.20,
            win_rate=0.45,
            annual_return=0.10,
            success=False
        )

        # Success cannot dominate failure
        assert pareto_dominates(metrics_success, metrics_failed) is False

        # Failure cannot dominate success
        assert pareto_dominates(metrics_failed, metrics_success) is False

    def test_both_failed_no_dominance(self):
        """Test that two failed backtests have no dominance relationship."""
        metrics_failed_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=False
        )
        metrics_failed_b = MultiObjectiveMetrics(
            sharpe_ratio=1.2,
            calmar_ratio=1.8,
            max_drawdown=-0.20,
            total_return=0.40,
            win_rate=0.55,
            annual_return=0.18,
            success=False
        )

        # Failed backtests have no dominance relationship
        assert pareto_dominates(metrics_failed_a, metrics_failed_b) is False
        assert pareto_dominates(metrics_failed_b, metrics_failed_a) is False

    def test_max_drawdown_less_negative_is_better(self):
        """Test that max_drawdown is correctly treated as minimization (less negative is better)."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.10,  # Better: -10% drawdown
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.25,  # Worse: -25% drawdown
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # A dominates B (better max_drawdown: -0.10 > -0.25)
        assert pareto_dominates(metrics_a, metrics_b) is True

        # B does not dominate A
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_edge_case_zero_values(self):
        """Test dominance with zero values in some objectives."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=0.0,
            calmar_ratio=0.0,
            max_drawdown=0.0,  # No drawdown (best case)
            total_return=0.0,
            win_rate=0.5,
            annual_return=0.0,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=-0.5,  # Worse
            calmar_ratio=-0.2,  # Worse
            max_drawdown=-0.10,  # Worse
            total_return=-0.10,  # Worse
            win_rate=0.45,  # Worse
            annual_return=-0.05,  # Worse
            success=True
        )

        # A dominates B (better or equal in all objectives)
        assert pareto_dominates(metrics_a, metrics_b) is True
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_edge_case_extreme_values(self):
        """Test dominance with extreme values."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=10.0,   # Extremely high
            calmar_ratio=20.0,   # Extremely high
            max_drawdown=-0.01,  # Very small drawdown
            total_return=5.0,    # 500% return
            win_rate=0.95,       # 95% win rate
            annual_return=1.0,   # 100% annual return
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # A dominates B (extremely better in all objectives)
        assert pareto_dominates(metrics_a, metrics_b) is True
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_edge_case_negative_sharpe_ratio(self):
        """Test dominance with negative Sharpe ratios (losing strategies)."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=-0.5,  # Less negative (better)
            calmar_ratio=-0.3,
            max_drawdown=-0.20,
            total_return=-0.10,
            win_rate=0.40,
            annual_return=-0.05,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=-1.0,  # More negative (worse)
            calmar_ratio=-0.5,
            max_drawdown=-0.30,
            total_return=-0.20,
            win_rate=0.35,
            annual_return=-0.10,
            success=True
        )

        # A dominates B (less negative is better for negative values)
        assert pareto_dominates(metrics_a, metrics_b) is True
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_symmetry_property(self):
        """Test that dominance is not symmetric: if A dominates B, B does not dominate A."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=2.0,
            calmar_ratio=3.0,
            max_drawdown=-0.08,
            total_return=0.60,
            win_rate=0.65,
            annual_return=0.25,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.5,
            max_drawdown=-0.12,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )

        # Verify asymmetry
        a_dominates_b = pareto_dominates(metrics_a, metrics_b)
        b_dominates_a = pareto_dominates(metrics_b, metrics_a)

        assert a_dominates_b is True
        assert b_dominates_a is False
        assert a_dominates_b != b_dominates_a

    def test_transitivity_property(self):
        """Test transitivity: if A dominates B and B dominates C, then A dominates C."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=2.0,
            calmar_ratio=3.0,
            max_drawdown=-0.08,
            total_return=0.60,
            win_rate=0.65,
            annual_return=0.25,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5,
            calmar_ratio=2.5,
            max_drawdown=-0.12,
            total_return=0.50,
            win_rate=0.60,
            annual_return=0.20,
            success=True
        )
        metrics_c = MultiObjectiveMetrics(
            sharpe_ratio=1.0,
            calmar_ratio=2.0,
            max_drawdown=-0.18,
            total_return=0.40,
            win_rate=0.55,
            annual_return=0.15,
            success=True
        )

        # Check transitivity: A > B > C ⇒ A > C
        assert pareto_dominates(metrics_a, metrics_b) is True
        assert pareto_dominates(metrics_b, metrics_c) is True
        assert pareto_dominates(metrics_a, metrics_c) is True

    def test_single_objective_improvements(self):
        """Test that improvement in just one objective (with others equal) is sufficient for dominance."""
        base_data = {
            'calmar_ratio': 2.0,
            'max_drawdown': -0.15,
            'total_return': 0.45,
            'win_rate': 0.58,
            'annual_return': 0.19,
            'success': True
        }

        # Test each objective individually
        test_cases = [
            ('sharpe_ratio', 1.6, 1.5),
            ('calmar_ratio', 2.1, 2.0),
            ('max_drawdown', -0.14, -0.15),  # Less negative is better
            ('total_return', 0.46, 0.45),
            ('win_rate', 0.59, 0.58),
            ('annual_return', 0.20, 0.19),
        ]

        for objective_name, better_value, base_value in test_cases:
            # Create metrics with one objective better, sharpe_ratio as default
            metrics_a_data = base_data.copy()
            metrics_a_data['sharpe_ratio'] = better_value if objective_name == 'sharpe_ratio' else base_value
            if objective_name != 'sharpe_ratio':
                metrics_a_data[objective_name] = better_value

            metrics_b_data = base_data.copy()
            metrics_b_data['sharpe_ratio'] = base_value

            metrics_a = MultiObjectiveMetrics(**metrics_a_data)
            metrics_b = MultiObjectiveMetrics(**metrics_b_data)

            # A should dominate B (better in one objective, equal in rest)
            assert pareto_dominates(metrics_a, metrics_b) is True, \
                f"Failed for objective: {objective_name}"
            assert pareto_dominates(metrics_b, metrics_a) is False, \
                f"Symmetry failed for objective: {objective_name}"

    def test_comprehensive_non_dominated_scenarios(self):
        """Test various non-dominated scenarios (no clear winner)."""
        # Scenario 1: Each better in different objectives
        m1 = MultiObjectiveMetrics(1.8, 1.5, -0.12, 0.45, 0.58, 0.19, True)
        m2 = MultiObjectiveMetrics(1.4, 2.2, -0.11, 0.48, 0.59, 0.21, True)
        assert pareto_dominates(m1, m2) is False
        assert pareto_dominates(m2, m1) is False

        # Scenario 2: Trade-offs across objectives
        m3 = MultiObjectiveMetrics(2.0, 1.0, -0.20, 0.60, 0.50, 0.15, True)
        m4 = MultiObjectiveMetrics(1.0, 2.0, -0.10, 0.40, 0.70, 0.25, True)
        assert pareto_dominates(m3, m4) is False
        assert pareto_dominates(m4, m3) is False

        # Scenario 3: High variance in objectives
        m5 = MultiObjectiveMetrics(3.0, 0.5, -0.05, 0.80, 0.40, 0.10, True)
        m6 = MultiObjectiveMetrics(0.5, 3.0, -0.25, 0.30, 0.75, 0.30, True)
        assert pareto_dominates(m5, m6) is False
        assert pareto_dominates(m6, m5) is False

    def test_dominance_with_very_close_values(self):
        """Test dominance detection with very close but distinct values."""
        metrics_a = MultiObjectiveMetrics(
            sharpe_ratio=1.5001,  # Slightly better
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.58,
            annual_return=0.19,
            success=True
        )
        metrics_b = MultiObjectiveMetrics(
            sharpe_ratio=1.5000,  # Slightly worse
            calmar_ratio=2.0,
            max_drawdown=-0.15,
            total_return=0.45,
            win_rate=0.58,
            annual_return=0.19,
            success=True
        )

        # Even tiny improvement should result in dominance
        assert pareto_dominates(metrics_a, metrics_b) is True
        assert pareto_dominates(metrics_b, metrics_a) is False

    def test_all_objectives_matter(self):
        """Test that all 6 objectives are correctly considered in dominance."""
        # Base metrics
        base = MultiObjectiveMetrics(1.5, 2.0, -0.15, 0.45, 0.58, 0.19, True)

        # Test that each objective can prevent dominance
        test_objectives = [
            ('sharpe_ratio', 1.4),
            ('calmar_ratio', 1.9),
            ('max_drawdown', -0.16),  # More negative is worse
            ('total_return', 0.44),
            ('win_rate', 0.57),
            ('annual_return', 0.18),
        ]

        for obj_name, worse_value in test_objectives:
            # Create metrics where one objective is worse, others are equal or better
            worse_data = {
                'sharpe_ratio': 1.6,  # Better than base
                'calmar_ratio': 2.1,  # Better than base
                'max_drawdown': -0.14,  # Better than base
                'total_return': 0.46,  # Better than base
                'win_rate': 0.59,  # Better than base
                'annual_return': 0.20,  # Better than base
                'success': True
            }
            worse_data[obj_name] = worse_value  # Make one objective worse

            metrics_worse_one = MultiObjectiveMetrics(**worse_data)

            # Should not dominate base (one objective worse, others better)
            # This shows mutual non-dominance due to trade-offs
            assert pareto_dominates(metrics_worse_one, base) is False, \
                f"Should not dominate when {obj_name} is worse"


class TestCrowdingDistance:
    """Test suite for NSGA-II crowding distance calculation."""

    def test_boundary_solutions_infinite_distance(self):
        """
        Test that boundary solutions (extreme values) get infinite crowding distance.

        NSGA-II algorithm assigns infinite distance to boundary solutions to ensure
        they are always preserved. This maintains diversity at the edges of the
        Pareto front.
        """
        # Create 3 strategies with varying metrics
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,  # Worst Sharpe
                    calmar_ratio=1.5,
                    max_drawdown=-0.20,
                    total_return=0.30,
                    win_rate=0.50,
                    annual_return=0.15,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Middle Sharpe
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,  # Best Sharpe
                    calmar_ratio=2.5,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        distances = calculate_crowding_distance(strategies)

        # Boundary solutions should have infinite distance
        # At least 2 strategies should have infinite distance (boundaries in different objectives)
        infinite_count = sum(1 for d in distances.values() if d == float('inf'))
        assert infinite_count >= 2, "At least 2 boundary solutions should have infinite distance"

        # All distances should be non-negative
        assert all(d >= 0.0 for d in distances.values()), "All distances should be non-negative"

    def test_interior_solutions_finite_distance(self):
        """
        Test that interior solutions get finite (non-infinite) crowding distance.

        Interior solutions have neighbors on both sides in objective space, so their
        distance is calculated as the sum of normalized gaps to neighbors across all
        objectives.
        """
        # Create 5 strategies where middle ones are clearly interior
        strategies = [
            Strategy(
                id=f's{i}',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0 + i * 0.2,  # Evenly spaced: 1.0, 1.2, 1.4, 1.6, 1.8
                    calmar_ratio=1.5 + i * 0.2,
                    max_drawdown=-0.20 + i * 0.02,
                    total_return=0.30 + i * 0.05,
                    win_rate=0.50 + i * 0.04,
                    annual_return=0.15 + i * 0.02,
                    success=True
                )
            )
            for i in range(5)
        ]

        distances = calculate_crowding_distance(strategies)

        # Middle strategies (s1, s2, s3) should have finite distance
        for sid in ['s1', 's2', 's3']:
            assert distances[sid] != float('inf'), f"Interior solution {sid} should have finite distance"
            assert distances[sid] > 0.0, f"Interior solution {sid} should have positive distance"

        # All distances should be non-negative
        assert all(d >= 0.0 for d in distances.values()), "All distances should be non-negative"

    def test_distance_increases_with_spread(self):
        """
        Test crowding distance with unevenly spaced strategies.

        The crowding distance is normalized by the range of each objective, so
        evenly-spaced strategies get similar normalized distances regardless of
        absolute spread. This test verifies that unevenly spaced strategies have
        different crowding distances reflecting their relative positions.
        """
        # Scenario 1: Evenly spaced strategies
        even_strategies = [
            Strategy(
                id='e1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='e2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.25,  # Even spacing
                    calmar_ratio=2.25,
                    max_drawdown=-0.1375,
                    total_return=0.45,
                    win_rate=0.65,
                    annual_return=0.19,
                    success=True
                )
            ),
            Strategy(
                id='e3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Even spacing
                    calmar_ratio=2.5,
                    max_drawdown=-0.125,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='e4',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.75,  # Even spacing
                    calmar_ratio=2.75,
                    max_drawdown=-0.1125,
                    total_return=0.55,
                    win_rate=0.75,
                    annual_return=0.21,
                    success=True
                )
            ),
            Strategy(
                id='e5',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=3.0,
                    max_drawdown=-0.10,
                    total_return=0.60,
                    win_rate=0.80,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        # Scenario 2: Unevenly spaced (one strategy clustered with neighbors)
        uneven_strategies = [
            Strategy(
                id='u1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='u2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.2,  # Closer to u1
                    calmar_ratio=2.1,
                    max_drawdown=-0.14,
                    total_return=0.42,
                    win_rate=0.62,
                    annual_return=0.185,
                    success=True
                )
            ),
            Strategy(
                id='u3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.3,  # Close to u2 (clustered)
                    calmar_ratio=2.15,
                    max_drawdown=-0.135,
                    total_return=0.43,
                    win_rate=0.64,
                    annual_return=0.187,
                    success=True
                )
            ),
            Strategy(
                id='u4',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.7,  # Large gap from u3
                    calmar_ratio=2.7,
                    max_drawdown=-0.115,
                    total_return=0.53,
                    win_rate=0.74,
                    annual_return=0.208,
                    success=True
                )
            ),
            Strategy(
                id='u5',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=3.0,
                    max_drawdown=-0.10,
                    total_return=0.60,
                    win_rate=0.80,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        even_distances = calculate_crowding_distance(even_strategies)
        uneven_distances = calculate_crowding_distance(uneven_strategies)

        # In evenly spaced strategies, middle ones have similar distances
        even_middle = [even_distances[f'e{i}'] for i in range(2, 5)]
        even_finite = [d for d in even_middle if d != float('inf')]

        # In unevenly spaced, u3 (clustered) should have smaller distance than u4 (isolated)
        # u3 is close to neighbors, u4 has large gaps on both sides
        if uneven_distances['u3'] != float('inf') and uneven_distances['u4'] != float('inf'):
            assert uneven_distances['u4'] > uneven_distances['u3'], \
                f"Isolated strategy (u4) should have larger distance than clustered (u3): " \
                f"{uneven_distances['u4']} > {uneven_distances['u3']}"

    def test_two_strategies_both_infinite(self):
        """
        Test edge case with only 2 strategies - both should get infinite distance.

        With only 2 strategies, both are boundary solutions (extremes) in the
        objective space, so both should receive infinite crowding distance.
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.5,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        distances = calculate_crowding_distance(strategies)

        # Both strategies are boundaries, so both should have infinite distance
        assert distances['s1'] == float('inf'), "First strategy should have infinite distance"
        assert distances['s2'] == float('inf'), "Second strategy should have infinite distance"

    def test_all_same_metrics_handling(self):
        """
        Test edge case where all strategies have identical metrics.

        When all strategies have the same metrics, there's no diversity in the
        objective space. The algorithm should handle this gracefully by skipping
        objectives with no range (obj_range == 0). All strategies will get
        distance 0.0 since there's no spread to measure.
        """
        # All strategies have identical metrics
        strategies = [
            Strategy(
                id=f's{i}',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            )
            for i in range(4)
        ]

        distances = calculate_crowding_distance(strategies)

        # All strategies should get distance values (all will be 0.0 due to no diversity)
        assert len(distances) == 4, "Should have distances for all 4 strategies"

        # When all metrics are identical, the algorithm skips objectives (obj_range == 0)
        # This results in all distances remaining at 0.0 (initial value)
        # This is the correct behavior - no diversity means no crowding distance
        assert all(d == 0.0 for d in distances.values()), \
            "All strategies should have 0.0 distance when metrics are identical"

    def test_empty_list_raises_error(self):
        """Test that empty strategy list raises ValueError."""
        with pytest.raises(ValueError, match="strategies list is empty"):
            calculate_crowding_distance([])

    def test_single_strategy_raises_error(self):
        """Test that single strategy raises ValueError (need at least 2)."""
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            )
        ]

        with pytest.raises(ValueError, match="need at least 2 strategies"):
            calculate_crowding_distance(strategies)

    def test_strategies_without_metrics_raises_error(self):
        """Test that strategies without metrics raise ValueError."""
        strategies = [
            Strategy(id='s1', metrics=None),
            Strategy(id='s2', metrics=None)
        ]

        with pytest.raises(ValueError, match="no strategies with successful evaluations"):
            calculate_crowding_distance(strategies)

    def test_failed_evaluations_excluded(self):
        """Test that strategies with failed evaluations are excluded."""
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=False  # Failed evaluation
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.5,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.22,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=3.0,
                    max_drawdown=-0.08,
                    total_return=0.60,
                    win_rate=0.75,
                    annual_return=0.25,
                    success=True
                )
            )
        ]

        distances = calculate_crowding_distance(strategies)

        # Only successful strategies should be in results
        assert 's1' not in distances, "Failed strategy should not have distance calculated"
        assert 's2' in distances, "Successful strategy should have distance"
        assert 's3' in distances, "Successful strategy should have distance"

    def test_mixed_metrics_and_none(self):
        """Test that strategies with None metrics are filtered out."""
        strategies = [
            Strategy(id='s1', metrics=None),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=2.5,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        distances = calculate_crowding_distance(strategies)

        # Only strategies with metrics should be in results
        assert 's1' not in distances, "Strategy without metrics should not have distance"
        assert 's2' in distances, "Strategy with metrics should have distance"
        assert 's3' in distances, "Strategy with metrics should have distance"

    def test_distance_values_properties(self):
        """
        Test mathematical properties of crowding distance values.

        Verifies that:
        - All distances are non-negative
        - Boundary solutions have infinite distance
        - Interior solutions have finite positive distance
        - Sum across all objectives makes sense
        """
        strategies = [
            Strategy(
                id=f's{i}',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0 + i * 0.3,
                    calmar_ratio=1.5 + i * 0.3,
                    max_drawdown=-0.20 + i * 0.03,
                    total_return=0.30 + i * 0.08,
                    win_rate=0.50 + i * 0.06,
                    annual_return=0.15 + i * 0.03,
                    success=True
                )
            )
            for i in range(4)
        ]

        distances = calculate_crowding_distance(strategies)

        # Property 1: All distances are non-negative
        assert all(d >= 0.0 for d in distances.values()), "All distances must be non-negative"

        # Property 2: At least 2 boundary solutions with infinite distance
        infinite_count = sum(1 for d in distances.values() if d == float('inf'))
        assert infinite_count >= 2, "Should have at least 2 boundary solutions"

        # Property 3: Non-infinite distances are positive
        finite_distances = [d for d in distances.values() if d != float('inf')]
        if finite_distances:
            assert all(d > 0.0 for d in finite_distances), \
                "All finite distances should be positive"

        # Property 4: All strategies have a distance value
        assert len(distances) == 4, "Should have distance for all 4 strategies"


class TestCrowdingDistanceIntegration:
    """Test integration of crowding distance with Pareto ranking."""

    def test_crowding_distance_on_pareto_front(self):
        """
        Test crowding distance calculation on strategies from same Pareto front.

        This is the typical use case: calculating crowding distance for all
        non-dominated strategies to maintain diversity in selection.
        """
        # Create non-dominated strategies (Pareto front)
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,  # Best Sharpe
                    calmar_ratio=1.5,  # Worst Calmar
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.60,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Middle Sharpe
                    calmar_ratio=2.0,  # Middle Calmar
                    max_drawdown=-0.12,
                    total_return=0.45,
                    win_rate=0.65,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,  # Worst Sharpe
                    calmar_ratio=2.5,  # Best Calmar
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.70,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        # These strategies are designed to be non-dominated (trade-offs)
        # Verify they form a Pareto front
        ranks = assign_pareto_ranks(strategies)
        assert all(ranks[s.id] == 1 for s in strategies), \
            "All strategies should be on Pareto front (rank 1)"

        # Calculate crowding distances
        distances = calculate_crowding_distance(strategies)

        # All strategies should have distances
        assert len(distances) == 3, "Should have distances for all 3 strategies"

        # Boundary solutions should have infinite distance
        infinite_count = sum(1 for d in distances.values() if d == float('inf'))
        assert infinite_count >= 2, "Should have at least 2 boundary solutions"

    def test_crowding_distance_on_dominated_strategies(self):
        """
        Test crowding distance on dominated strategies (not typical use case).

        While crowding distance is usually calculated for Pareto front only,
        it should still work correctly on any set of strategies with metrics.
        """
        # Create dominated strategies (not on Pareto front)
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=0.8,
                    calmar_ratio=1.2,
                    max_drawdown=-0.25,
                    total_return=0.25,
                    win_rate=0.50,
                    annual_return=0.12,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=0.9,
                    calmar_ratio=1.3,
                    max_drawdown=-0.23,
                    total_return=0.28,
                    win_rate=0.52,
                    annual_return=0.14,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=-0.20,
                    total_return=0.32,
                    win_rate=0.55,
                    annual_return=0.16,
                    success=True
                )
            )
        ]

        # Calculate crowding distances
        distances = calculate_crowding_distance(strategies)

        # Should still work correctly
        assert len(distances) == 3, "Should have distances for all strategies"
        assert all(d >= 0.0 for d in distances.values()), \
            "All distances should be non-negative"

        # Boundary solutions should have infinite distance
        infinite_count = sum(1 for d in distances.values() if d == float('inf'))
        assert infinite_count >= 2, "Should have at least 2 boundary solutions"

    def test_nsga_ii_selection_scenario(self):
        """
        Test crowding distance in NSGA-II tournament selection scenario.

        Simulates the typical use case where crowding distance is used to break
        ties between strategies of the same Pareto rank during selection.
        """
        # Create a Pareto front with varying crowding
        strategies = [
            Strategy(
                id=f's{i}',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0 + i * 0.25,
                    calmar_ratio=1.5 + i * 0.25,
                    max_drawdown=-0.20 + i * 0.025,
                    total_return=0.30 + i * 0.06,
                    win_rate=0.50 + i * 0.05,
                    annual_return=0.15 + i * 0.025,
                    success=True
                )
            )
            for i in range(5)
        ]

        # Assign Pareto ranks
        ranks = assign_pareto_ranks(strategies)

        # Calculate crowding distances
        distances = calculate_crowding_distance(strategies)

        # Verify integration: all strategies should have both rank and distance
        for strategy in strategies:
            assert strategy.id in ranks, f"Strategy {strategy.id} should have Pareto rank"
            assert strategy.id in distances, f"Strategy {strategy.id} should have crowding distance"

        # In NSGA-II selection, prefer:
        # 1. Lower Pareto rank (better)
        # 2. Higher crowding distance (less crowded, more diverse)

        # Identify boundary solutions (infinite distance)
        boundary_ids = [sid for sid, d in distances.items() if d == float('inf')]
        assert len(boundary_ids) >= 2, "Should have at least 2 boundary solutions"

        # Boundary solutions should be preferred over interior solutions
        # (when Pareto ranks are equal)
        for bid in boundary_ids:
            assert distances[bid] == float('inf'), \
                f"Boundary solution {bid} should have infinite distance"


class TestAssignParetoRanks:
    """Test suite for NSGA-II Pareto ranking (fast non-dominated sorting)."""

    def test_simple_pareto_ranking(self):
        """
        Test simple Pareto ranking with clear dominance hierarchy.

        Creates 3 strategies where:
        - s1 dominates s2 (better in all objectives) → rank 1
        - s2 dominates s3 (better in all objectives) → rank 2
        - s3 is dominated by both s1 and s2 → rank 3
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,  # Best
                    calmar_ratio=3.0,  # Best
                    max_drawdown=-0.08,  # Best (least negative)
                    total_return=0.60,  # Best
                    win_rate=0.70,  # Best
                    annual_return=0.25,  # Best
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Middle
                    calmar_ratio=2.0,  # Middle
                    max_drawdown=-0.15,  # Middle
                    total_return=0.45,  # Middle
                    win_rate=0.60,  # Middle
                    annual_return=0.20,  # Middle
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,  # Worst
                    calmar_ratio=1.5,  # Worst
                    max_drawdown=-0.25,  # Worst (most negative)
                    total_return=0.30,  # Worst
                    win_rate=0.50,  # Worst
                    annual_return=0.15,  # Worst
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # s1 should be rank 1 (Pareto front, dominates all)
        assert ranks['s1'] == 1, f"s1 should have rank 1, got {ranks['s1']}"

        # s2 should be rank 2 (dominated only by s1)
        assert ranks['s2'] == 2, f"s2 should have rank 2, got {ranks['s2']}"

        # s3 should be rank 3 (dominated by both s1 and s2)
        assert ranks['s3'] == 3, f"s3 should have rank 3, got {ranks['s3']}"

    def test_all_non_dominated(self):
        """
        Test ranking when all strategies are non-dominated (on Pareto front).

        Creates strategies with trade-offs where none dominates others:
        - s1: High Sharpe, Low Calmar
        - s2: Middle Sharpe, Middle Calmar
        - s3: Low Sharpe, High Calmar
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,  # Best Sharpe
                    calmar_ratio=1.5,  # Worst Calmar
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.55,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Middle Sharpe
                    calmar_ratio=2.0,  # Middle Calmar
                    max_drawdown=-0.12,
                    total_return=0.45,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,  # Worst Sharpe
                    calmar_ratio=2.5,  # Best Calmar
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.65,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # All strategies should be rank 1 (all on Pareto front)
        assert ranks['s1'] == 1, f"s1 should have rank 1, got {ranks['s1']}"
        assert ranks['s2'] == 1, f"s2 should have rank 1, got {ranks['s2']}"
        assert ranks['s3'] == 1, f"s3 should have rank 1, got {ranks['s3']}"

    def test_single_dominant_strategy(self):
        """
        Test ranking with one dominant strategy and multiple equal lower-ranked strategies.

        s1 dominates all others, s2/s3/s4 are non-dominated among themselves.
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.5,  # Dominates all
                    calmar_ratio=3.0,
                    max_drawdown=-0.05,
                    total_return=0.70,
                    win_rate=0.75,
                    annual_return=0.28,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # High Sharpe, Low Calmar
                    calmar_ratio=1.8,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.55,
                    annual_return=0.18,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.2,  # Middle
                    calmar_ratio=2.0,
                    max_drawdown=-0.12,
                    total_return=0.45,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='s4',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,  # Low Sharpe, High Calmar
                    calmar_ratio=2.2,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.65,
                    annual_return=0.22,
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # s1 should be rank 1 (dominates all others)
        assert ranks['s1'] == 1, f"s1 should have rank 1, got {ranks['s1']}"

        # s2, s3, s4 should all be rank 2 (dominated only by s1, non-dominated among themselves)
        assert ranks['s2'] == 2, f"s2 should have rank 2, got {ranks['s2']}"
        assert ranks['s3'] == 2, f"s3 should have rank 2, got {ranks['s3']}"
        assert ranks['s4'] == 2, f"s4 should have rank 2, got {ranks['s4']}"

    def test_failed_strategies_rank_zero(self):
        """
        Test that failed/unevaluated strategies are assigned rank 0.

        Strategies with metrics.success=False or metrics=None should get rank 0.
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True  # Valid strategy
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.2,
                    calmar_ratio=1.8,
                    max_drawdown=-0.15,
                    total_return=0.40,
                    win_rate=0.55,
                    annual_return=0.18,
                    success=False  # Failed evaluation
                )
            ),
            Strategy(
                id='s3',
                metrics=None  # No metrics (unevaluated)
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # s1 should be rank 1 (only valid strategy, on Pareto front)
        assert ranks['s1'] == 1, f"s1 should have rank 1, got {ranks['s1']}"

        # s2 should be rank 0 (failed evaluation)
        assert ranks['s2'] == 0, f"s2 should have rank 0 (failed), got {ranks['s2']}"

        # s3 should be rank 0 (no metrics)
        assert ranks['s3'] == 0, f"s3 should have rank 0 (no metrics), got {ranks['s3']}"

    def test_empty_population(self):
        """Test that empty population returns empty dictionary."""
        strategies = []
        ranks = assign_pareto_ranks(strategies)
        assert ranks == {}, "Empty population should return empty rank dictionary"

    def test_single_strategy(self):
        """Test that single strategy gets rank 1 (Pareto front)."""
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # Single valid strategy should be rank 1
        assert ranks['s1'] == 1, f"Single strategy should have rank 1, got {ranks['s1']}"

    def test_all_strategies_failed(self):
        """Test that all failed strategies get rank 0."""
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=False  # Failed
                )
            ),
            Strategy(
                id='s2',
                metrics=None  # Unevaluated
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # All strategies should be rank 0
        assert ranks['s1'] == 0, f"Failed strategy should have rank 0, got {ranks['s1']}"
        assert ranks['s2'] == 0, f"Unevaluated strategy should have rank 0, got {ranks['s2']}"

    def test_complex_dominance_hierarchy(self):
        """
        Test complex dominance hierarchy with multiple ranks.

        Creates 5 strategies with dominance chain:
        - s1: Rank 1 (dominates s2, s3, s4, s5)
        - s2: Rank 2 (dominated by s1, dominates s3, s4, s5)
        - s3, s4: Rank 3 (dominated by s1, s2, but non-dominated among themselves)
        - s5: Rank 4 (dominated by all)
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.5,
                    calmar_ratio=3.0,
                    max_drawdown=-0.05,
                    total_return=0.70,
                    win_rate=0.75,
                    annual_return=0.28,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=2.5,
                    max_drawdown=-0.08,
                    total_return=0.60,
                    win_rate=0.70,
                    annual_return=0.25,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,  # Better Sharpe than s4
                    calmar_ratio=1.8,  # Worse Calmar than s4
                    max_drawdown=-0.12,
                    total_return=0.45,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='s4',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.3,  # Worse Sharpe than s3
                    calmar_ratio=2.0,  # Better Calmar than s3
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.65,
                    annual_return=0.22,
                    success=True
                )
            ),
            Strategy(
                id='s5',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=0.8,
                    calmar_ratio=1.2,
                    max_drawdown=-0.30,
                    total_return=0.20,
                    win_rate=0.45,
                    annual_return=0.10,
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # Verify rank assignments
        assert ranks['s1'] == 1, f"s1 should have rank 1, got {ranks['s1']}"
        assert ranks['s2'] == 2, f"s2 should have rank 2, got {ranks['s2']}"
        assert ranks['s3'] == 3, f"s3 should have rank 3, got {ranks['s3']}"
        assert ranks['s4'] == 3, f"s4 should have rank 3, got {ranks['s4']}"
        assert ranks['s5'] == 4, f"s5 should have rank 4, got {ranks['s5']}"

    def test_identical_metrics(self):
        """
        Test ranking with identical metrics.

        All strategies with identical metrics are non-dominated, should all get rank 1.
        """
        strategies = [
            Strategy(
                id=f's{i}',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.10,
                    total_return=0.50,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            )
            for i in range(4)
        ]

        ranks = assign_pareto_ranks(strategies)

        # All strategies should be rank 1 (all non-dominated with identical metrics)
        for i in range(4):
            assert ranks[f's{i}'] == 1, f"s{i} should have rank 1, got {ranks[f's{i}']}"

    def test_rank_consistency_with_dominance(self):
        """
        Test that rank assignments are consistent with dominance relationships.

        If strategy A dominates strategy B, then rank(A) < rank(B).
        """
        strategies = [
            Strategy(
                id='s1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=2.5,
                    max_drawdown=-0.08,
                    total_return=0.60,
                    win_rate=0.70,
                    annual_return=0.25,
                    success=True
                )
            ),
            Strategy(
                id='s2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.12,
                    total_return=0.50,
                    win_rate=0.65,
                    annual_return=0.22,
                    success=True
                )
            ),
            Strategy(
                id='s3',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.0,
                    calmar_ratio=1.5,
                    max_drawdown=-0.18,
                    total_return=0.40,
                    win_rate=0.55,
                    annual_return=0.18,
                    success=True
                )
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # Check dominance relationships
        assert strategies[0].dominates(strategies[1]), "s1 should dominate s2"
        assert strategies[1].dominates(strategies[2]), "s2 should dominate s3"
        assert strategies[0].dominates(strategies[2]), "s1 should dominate s3"

        # Verify rank consistency: dominating strategy has lower rank
        assert ranks['s1'] < ranks['s2'], f"rank(s1)={ranks['s1']} should be < rank(s2)={ranks['s2']}"
        assert ranks['s2'] < ranks['s3'], f"rank(s2)={ranks['s2']} should be < rank(s3)={ranks['s3']}"
        assert ranks['s1'] < ranks['s3'], f"rank(s1)={ranks['s1']} should be < rank(s3)={ranks['s3']}"

    def test_mixed_valid_and_invalid_strategies(self):
        """
        Test ranking with mix of valid, failed, and unevaluated strategies.

        Only valid strategies should be ranked normally, others get rank 0.
        """
        strategies = [
            Strategy(
                id='valid1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=2.0,
                    calmar_ratio=2.5,
                    max_drawdown=-0.08,
                    total_return=0.60,
                    win_rate=0.70,
                    annual_return=0.25,
                    success=True
                )
            ),
            Strategy(
                id='failed1',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.8,
                    calmar_ratio=2.2,
                    max_drawdown=-0.10,
                    total_return=0.55,
                    win_rate=0.65,
                    annual_return=0.23,
                    success=False  # Failed
                )
            ),
            Strategy(
                id='valid2',
                metrics=MultiObjectiveMetrics(
                    sharpe_ratio=1.5,
                    calmar_ratio=2.0,
                    max_drawdown=-0.12,
                    total_return=0.50,
                    win_rate=0.60,
                    annual_return=0.20,
                    success=True
                )
            ),
            Strategy(
                id='unevaluated',
                metrics=None
            )
        ]

        ranks = assign_pareto_ranks(strategies)

        # Valid strategies should be ranked normally
        assert ranks['valid1'] == 1, f"valid1 should have rank 1, got {ranks['valid1']}"
        assert ranks['valid2'] == 2, f"valid2 should have rank 2, got {ranks['valid2']}"

        # Invalid strategies should be rank 0
        assert ranks['failed1'] == 0, f"failed1 should have rank 0, got {ranks['failed1']}"
        assert ranks['unevaluated'] == 0, f"unevaluated should have rank 0, got {ranks['unevaluated']}"
