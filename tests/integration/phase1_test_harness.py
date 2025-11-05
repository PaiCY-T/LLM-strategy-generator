"""Phase 1 Test Harness for Population-Based Evolutionary Learning.

Extends Phase0TestHarness to implement genetic algorithm-based parameter optimization:
- Population-based learning with evolutionary operators
- Tournament selection with elitism
- Adaptive mutation rates
- IS/OOS data split for robust fitness evaluation
- Convergence detection and automatic restart
- Population state checkpointing

Target Metrics (Revised from Expert Review):
- Champion update rate: ≥10% (target)
- Best In-Sample Sharpe: >2.5 (target, beat Phase 0 champion)
- Champion Out-of-Sample Sharpe: >1.0 (target, validate robustness)
- Parameter diversity: ≥50% unique at gen 1-3 (target)

Decision Matrix:
- SUCCESS (≥10% update rate AND IS Sharpe >2.5 AND OOS Sharpe >1.0): Phase 1 validated
- PARTIAL (≥5% update rate AND IS Sharpe >2.0 AND OOS Sharpe 0.6-1.0): Tune hyperparameters
- FAILURE (<5% update rate OR IS Sharpe <2.0 OR OOS Sharpe <0.6): Investigate root cause
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys
import os
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import population components
from src.population.individual import Individual
from src.population.population_manager import PopulationManager
from src.population.genetic_operators import GeneticOperators
from src.population.fitness_evaluator import FitnessEvaluator
from src.population.evolution_monitor import EvolutionMonitor
from src.templates.momentum_template import MomentumTemplate

# Import base harness
from tests.integration.phase0_test_harness import Phase0TestHarness


class Phase1TestHarness(Phase0TestHarness):
    """Test harness for population-based evolutionary learning.

    Extends Phase0TestHarness with genetic algorithm components:
    - PopulationManager for population operations
    - GeneticOperators for mutation and crossover
    - FitnessEvaluator with IS/OOS split
    - EvolutionMonitor for tracking evolution progress

    Attributes:
        num_generations: Total number of generations to run
        population_size: Number of individuals in population
        elite_size: Number of elites to preserve each generation
        mutation_rate: Base mutation rate (adaptive)
        tournament_size: Tournament selection size
        max_restarts: Maximum convergence restarts allowed
        population_manager: PopulationManager instance
        genetic_operators: GeneticOperators instance
        fitness_evaluator: FitnessEvaluator instance
        evolution_monitor: EvolutionMonitor instance
        template: MomentumTemplate instance for strategy generation
        is_period: In-sample period for fitness optimization
        oos_period: Out-of-sample period for validation
    """

    def __init__(
        self,
        test_name: str = "phase1_evolution_test",
        num_generations: int = 50,
        population_size: int = 50,  # Increased from 30 per expert review
        elite_size: int = 5,  # 10% of population
        mutation_rate: float = 0.15,
        tournament_size: int = 2,  # Reduced from 3 per expert review
        max_restarts: int = 3,  # Maximum convergence restarts
        is_period: str = '2015:2020',  # In-sample period
        oos_period: str = '2021:2024',  # Out-of-sample period
        checkpoint_interval: int = 10,
        checkpoint_dir: str = "checkpoints"
    ):
        """Initialize Phase 1 Test Harness for evolutionary learning.

        Args:
            test_name: Test identifier (used in checkpoint filenames)
            num_generations: Number of generations to evolve (50 for full test)
            population_size: Population size (default: 50, increased from 30)
            elite_size: Number of elites to preserve (default: 5, 10%)
            mutation_rate: Base mutation rate (default: 0.15)
            tournament_size: Tournament selection size (default: 2, reduced from 3)
            max_restarts: Maximum convergence restarts (default: 3)
            is_period: In-sample period 'start:end' (default: '2015:2020')
            oos_period: Out-of-sample period 'start:end' (default: '2021:2024')
            checkpoint_interval: Save checkpoint every N generations (default: 10)
            checkpoint_dir: Directory path for checkpoint files
        """
        # Initialize base class (Phase0TestHarness)
        # Note: max_iterations maps to num_generations for Phase 1
        super().__init__(
            test_name=test_name,
            max_iterations=num_generations,
            model="N/A",  # Not used in Phase 1 (no LLM)
            checkpoint_interval=checkpoint_interval,
            checkpoint_dir=checkpoint_dir
        )

        # Phase 1 specific configuration
        self.num_generations = num_generations
        self.population_size = population_size
        self.elite_size = elite_size
        self.mutation_rate = mutation_rate
        self.tournament_size = tournament_size
        self.max_restarts = max_restarts
        self.is_period = is_period
        self.oos_period = oos_period

        # Parse IS/OOS periods
        self.is_start, self.is_end = is_period.split(':')
        self.oos_start, self.oos_end = oos_period.split(':')

        # Initialize population components (will be set in run())
        self.population_manager: Optional[PopulationManager] = None
        self.genetic_operators: Optional[GeneticOperators] = None
        self.fitness_evaluator: Optional[FitnessEvaluator] = None
        self.evolution_monitor: Optional[EvolutionMonitor] = None
        self.template: Optional[MomentumTemplate] = None

        # Evolution state tracking
        self.current_population: List[Individual] = []
        self.restart_count: int = 0

        # Override base class logger messages
        self.logger.info("=" * 70)
        self.logger.info("PHASE 1 TEST HARNESS INITIALIZED")
        self.logger.info("=" * 70)
        self.logger.info(f"Population-Based Evolutionary Learning Configuration:")
        self.logger.info(f"  Test name: {self.test_name}")
        self.logger.info(f"  Generations: {self.num_generations}")
        self.logger.info(f"  Population size: {self.population_size}")
        self.logger.info(f"  Elite size: {self.elite_size} ({self.elite_size/self.population_size*100:.0f}%)")
        self.logger.info(f"  Mutation rate: {self.mutation_rate} (adaptive 0.05-0.30)")
        self.logger.info(f"  Tournament size: {self.tournament_size}")
        self.logger.info(f"  Max restarts: {self.max_restarts}")
        self.logger.info(f"  IS period: {self.is_period} (fitness optimization)")
        self.logger.info(f"  OOS period: {self.oos_period} (validation)")
        self.logger.info(f"  Checkpoint interval: {self.checkpoint_interval}")
        self.logger.info("=" * 70)

    def run(
        self,
        data: Any,
        resume_from_checkpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute population-based evolutionary learning test.

        Main evolution loop that implements:
        - Population initialization with diversity guarantee
        - Generation loop with selection, crossover, mutation, evaluation
        - Elitism to preserve best individuals
        - Convergence detection and automatic restart
        - IS/OOS fitness evaluation
        - Progress monitoring and checkpointing

        Args:
            data: Finlab data object for strategy backtesting
            resume_from_checkpoint: Optional checkpoint file to resume from

        Returns:
            Dict[str, Any]: Comprehensive results containing:
                - test_completed: True if test finished
                - total_generations: Number of generations executed
                - champion_update_count: Number of champion updates
                - champion_update_rate: Percentage of generations with updates
                - best_is_sharpe: Best in-sample Sharpe ratio
                - champion_oos_sharpe: Champion out-of-sample Sharpe ratio
                - avg_is_sharpe: Average in-sample Sharpe
                - population_diversity_final: Final population diversity
                - restart_count: Number of convergence restarts
                - cache_hit_rate: Average cache hit rate
                - success_rate: Percentage of successful evaluations
                - final_champion: Champion individual state

        Raises:
            Exception: Critical failures that prevent test completion
        """
        # Initialize components
        self._initialize_components(data)

        # Initialize test state
        start_generation = 0

        # Resume from checkpoint if provided
        if resume_from_checkpoint:
            self.logger.info("=" * 70)
            self.logger.info("RESUMING FROM CHECKPOINT")
            self.logger.info("=" * 70)
            try:
                start_generation = self._load_checkpoint(resume_from_checkpoint)
                self.logger.info(f"✅ Checkpoint restored successfully")
                self.logger.info(f"   Resuming from generation: {start_generation}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load checkpoint: {e}")
                self.logger.error("Starting fresh evolution instead")
                start_generation = 0
        else:
            self.logger.info("=" * 70)
            self.logger.info("STARTING PHASE 1 EVOLUTIONARY LEARNING")
            self.logger.info("=" * 70)

        # Log test configuration
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Population size: {self.population_size}")
        self.logger.info(f"  Generations: {self.num_generations}")
        self.logger.info(f"  Start generation: {start_generation}")
        self.logger.info(f"  IS period: {self.is_period}")
        self.logger.info(f"  OOS period: {self.oos_period}")
        self.logger.info("")

        # Initialize population if starting fresh
        if start_generation == 0:
            self.logger.info("🧬 Initializing population...")
            self.current_population = self.population_manager.initialize_population(
                param_grid=self.template.PARAM_GRID
            )
            initial_diversity = self.population_manager.calculate_diversity(self.current_population)
            self.logger.info(f"✅ Population initialized")
            self.logger.info(f"   Population size: {len(self.current_population)}")
            self.logger.info(f"   Initial diversity: {initial_diversity:.1%}")

            # Evaluate initial population (IS data only)
            self.logger.info("📊 Evaluating initial population on IS data...")
            self.current_population = self.fitness_evaluator.evaluate_population(
                self.current_population,
                use_oos=False
            )
            self.logger.info(f"✅ Initial population evaluated")

        # Track test-level statistics
        test_start_time = time.time()

        # Main evolution loop
        for generation in range(start_generation, self.num_generations):
            self.logger.info("")
            self.logger.info("=" * 70)
            self.logger.info(f"GENERATION {generation}/{self.num_generations - 1}")
            self.logger.info("=" * 70)

            generation_start_time = time.time()

            # Calculate current diversity
            diversity = self.population_manager.calculate_diversity(self.current_population)

            # Get cache statistics
            cache_stats = self.fitness_evaluator.get_cache_stats()

            # Record generation statistics
            self.evolution_monitor.record_generation(
                generation_num=generation,
                population=self.current_population,
                diversity=diversity,
                cache_stats=cache_stats
            )

            # Update champion
            best_individual = max(self.current_population, key=lambda ind: ind.fitness)
            champion_updated = self.evolution_monitor.update_champion(best_individual)

            # Log generation summary
            avg_fitness = sum(ind.fitness for ind in self.current_population) / len(self.current_population)
            self.logger.info(f"Generation {generation} Summary:")
            self.logger.info(f"  Best fitness: {best_individual.fitness:.4f}")
            self.logger.info(f"  Avg fitness: {avg_fitness:.4f}")
            self.logger.info(f"  Diversity: {diversity:.1%}")
            self.logger.info(f"  Cache hit rate: {cache_stats['hit_rate']:.1%}")
            if champion_updated:
                self.logger.info(f"  🏆 NEW CHAMPION!")

            # Check for convergence
            if self.population_manager.check_convergence(self.current_population):
                self.logger.info("")
                self.logger.info("⚠️  CONVERGENCE DETECTED")

                # Check if we can restart
                if self.restart_count < self.max_restarts:
                    self.restart_count += 1
                    self.logger.info(f"🔄 RESTART {self.restart_count}/{self.max_restarts}")

                    # Preserve current champion
                    champion = self.evolution_monitor.get_champion()
                    self.logger.info(f"   Preserved champion: {champion.id} (fitness {champion.fitness:.4f})")

                    # Reinitialize population with champion seeded
                    self.logger.info("   Reinitializing population...")
                    self.current_population = self.population_manager.initialize_population(
                        param_grid=self.template.PARAM_GRID,
                        seed_parameters=[champion.parameters]
                    )

                    # Evaluate new population (IS data only)
                    self.logger.info("   Evaluating new population...")
                    self.current_population = self.fitness_evaluator.evaluate_population(
                        self.current_population,
                        use_oos=False
                    )

                    # Reset convergence tracking
                    self.population_manager.reset_convergence_tracking()
                    self.logger.info("   ✅ Restart complete")

                    # Continue to next generation
                    continue
                else:
                    self.logger.warning(f"⚠️  Maximum restarts ({self.max_restarts}) reached")
                    self.logger.warning("   Continuing evolution without restart")

            # Generate offspring via selection, crossover, mutation
            offspring = []
            while len(offspring) < self.population_size:
                # Tournament selection
                parent1 = self.population_manager.select_parent(self.current_population)
                parent2 = self.population_manager.select_parent(self.current_population)

                # Crossover
                child1, child2 = self.genetic_operators.crossover(parent1, parent2, generation)

                # Mutation
                child1 = self.genetic_operators.mutate(child1, generation)
                child2 = self.genetic_operators.mutate(child2, generation)

                offspring.extend([child1, child2])

            # Trim to population size
            offspring = offspring[:self.population_size]

            # Evaluate offspring (IS data only)
            offspring = self.fitness_evaluator.evaluate_population(offspring, use_oos=False)

            # Apply elitism: combine elites from current + top offspring
            self.current_population = self.population_manager.apply_elitism(
                self.current_population,
                offspring
            )

            # Update adaptive mutation rate based on diversity
            self.genetic_operators.update_mutation_rate(diversity)
            current_mutation_rate = self.genetic_operators.current_mutation_rate
            self.logger.info(f"  Mutation rate: {current_mutation_rate:.3f}")

            # Track generation metrics
            generation_duration = time.time() - generation_start_time
            self.durations.append(generation_duration)
            self.champion_updates.append(champion_updated)
            self.sharpes.append(best_individual.fitness)

            # Log timing
            self.logger.info(f"  Generation time: {generation_duration:.1f}s")

            # Update progress
            self._update_progress_phase1(generation)

            # Save checkpoint at intervals
            if (generation + 1) % self.checkpoint_interval == 0:
                self.logger.info(f"\n📁 Saving checkpoint at generation {generation}...")
                checkpoint_path = self._save_checkpoint_phase1(generation)
                if checkpoint_path:
                    self.logger.info(f"✅ Checkpoint saved: {checkpoint_path}")

        # Evolution completed
        test_duration = time.time() - test_start_time

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("PHASE 1 EVOLUTIONARY LEARNING - COMPLETE")
        self.logger.info("=" * 70)
        self.logger.info(f"Total duration: {test_duration:.1f}s ({test_duration/60:.1f}m)")
        self.logger.info(f"Total generations: {self.num_generations}")
        self.logger.info(f"Restarts: {self.restart_count}")

        # Evaluate final champion on OOS data
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("FINAL CHAMPION OOS VALIDATION")
        self.logger.info("=" * 70)
        final_champion = self.evolution_monitor.get_champion()
        self.logger.info(f"Champion ID: {final_champion.id}")
        self.logger.info(f"Champion IS fitness: {final_champion.fitness:.4f}")

        # Evaluate on OOS data
        champion_oos = self.fitness_evaluator.evaluate(final_champion, use_oos=True)
        self.logger.info(f"Champion OOS fitness: {champion_oos.fitness:.4f}")

        # Save final checkpoint
        self.logger.info("")
        self.logger.info("📁 Saving final checkpoint...")
        final_checkpoint = self._save_checkpoint_phase1(self.num_generations - 1)
        if final_checkpoint:
            self.logger.info(f"✅ Final checkpoint saved: {final_checkpoint}")

        # Compile and return results
        return self._compile_results_phase1(test_duration, champion_oos)

    def _initialize_components(self, data: Any) -> None:
        """Initialize all population-based learning components.

        Args:
            data: Finlab data object for backtesting
        """
        self.logger.info("Initializing components...")

        # Initialize template
        self.template = MomentumTemplate()
        self.logger.info("  ✅ MomentumTemplate initialized")

        # Initialize PopulationManager
        self.population_manager = PopulationManager(
            population_size=self.population_size,
            elite_size=self.elite_size,
            tournament_size=self.tournament_size
        )
        self.logger.info(f"  ✅ PopulationManager initialized (size={self.population_size}, elites={self.elite_size})")

        # Initialize GeneticOperators
        self.genetic_operators = GeneticOperators(
            base_mutation_rate=self.mutation_rate
        )
        self.logger.info(f"  ✅ GeneticOperators initialized (mutation_rate={self.mutation_rate})")

        # Initialize FitnessEvaluator with IS/OOS split
        self.fitness_evaluator = FitnessEvaluator(
            template=self.template,
            data=data,
            is_start=self.is_start,
            is_end=self.is_end,
            oos_start=self.oos_start,
            oos_end=self.oos_end
        )
        self.logger.info(f"  ✅ FitnessEvaluator initialized (IS: {self.is_period}, OOS: {self.oos_period})")

        # Initialize EvolutionMonitor
        self.evolution_monitor = EvolutionMonitor()
        self.logger.info("  ✅ EvolutionMonitor initialized")

        self.logger.info("All components initialized successfully")

    def _update_progress_phase1(self, generation: int) -> None:
        """Display progress for Phase 1 evolution.

        Args:
            generation: Current generation number
        """
        # Calculate progress percentage
        progress_pct = ((generation + 1) / self.num_generations * 100)

        # Get evolution summary
        summary = self.evolution_monitor.get_summary()

        # Calculate ETA
        avg_duration = sum(self.durations) / len(self.durations) if self.durations else 0.0
        generations_remaining = self.num_generations - (generation + 1)
        eta_seconds = avg_duration * generations_remaining
        eta_minutes = eta_seconds / 60

        # Display progress
        self.logger.info("")
        self.logger.info("─" * 70)
        self.logger.info("PROGRESS UPDATE")
        self.logger.info("─" * 70)
        self.logger.info(f"Generation: {generation + 1}/{self.num_generations} ({progress_pct:.1f}%)")
        self.logger.info(f"Champion updates: {summary['champion_updates_count']} ({summary['champion_update_rate']:.1f}%)")
        self.logger.info(f"Best IS Sharpe: {summary['best_fitness']:.4f}")
        self.logger.info(f"Avg IS Sharpe: {summary['avg_fitness']:.4f}")
        self.logger.info(f"Final diversity: {summary['final_diversity']:.1%}")
        self.logger.info(f"Avg cache hit rate: {summary['avg_cache_hit_rate']:.1%}")
        self.logger.info(f"Restarts: {self.restart_count}/{self.max_restarts}")
        self.logger.info(f"Avg generation time: {avg_duration:.1f}s")
        self.logger.info(f"ETA: {eta_minutes:.1f} minutes ({eta_seconds:.0f}s)")
        self.logger.info("─" * 70)

    def _save_checkpoint_phase1(self, generation: int) -> str:
        """Save Phase 1 checkpoint including population state.

        Args:
            generation: Current generation number

        Returns:
            str: Path to checkpoint file
        """
        try:
            # Get evolution summary
            summary = self.evolution_monitor.get_summary()

            # Build checkpoint data
            checkpoint_data = {
                "test_name": self.test_name,
                "phase": "phase1",
                "generation_number": generation,
                "timestamp": datetime.now().isoformat(),
                "durations": self.durations,
                "champion_updates": self.champion_updates,
                "sharpes": self.sharpes,
                "restart_count": self.restart_count,
                "evolution_summary": summary,
                "population": [ind.to_dict() for ind in self.current_population],
                "config": {
                    "population_size": self.population_size,
                    "elite_size": self.elite_size,
                    "mutation_rate": self.mutation_rate,
                    "tournament_size": self.tournament_size,
                    "is_period": self.is_period,
                    "oos_period": self.oos_period
                }
            }

            # Create checkpoint filename
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{self.test_name}_gen_{generation}.json"

            # Save to JSON
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)

            return str(checkpoint_file)

        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")
            return ""

    def _compile_results_phase1(self, test_duration: float, champion_oos: Individual) -> Dict[str, Any]:
        """Compile Phase 1 evolutionary learning results.

        Args:
            test_duration: Total test duration in seconds
            champion_oos: Champion evaluated on OOS data

        Returns:
            Dict[str, Any]: Comprehensive results dictionary
        """
        # Get evolution summary
        summary = self.evolution_monitor.get_summary()

        # Calculate metrics
        champion_update_rate = summary['champion_update_rate']
        best_is_sharpe = summary['best_fitness']
        avg_is_sharpe = summary['avg_fitness']
        champion_oos_sharpe = champion_oos.fitness
        final_diversity = summary['final_diversity']
        avg_cache_hit_rate = summary['avg_cache_hit_rate']

        # Build results
        results = {
            # Test completion
            'test_completed': True,
            'total_generations': self.num_generations,
            'test_duration_seconds': test_duration,

            # Primary decision metrics
            'champion_update_count': summary['champion_updates_count'],
            'champion_update_rate': champion_update_rate,
            'best_is_sharpe': best_is_sharpe,
            'champion_oos_sharpe': champion_oos_sharpe,
            'avg_is_sharpe': avg_is_sharpe,

            # Secondary metrics
            'population_diversity_final': final_diversity,
            'restart_count': self.restart_count,
            'cache_hit_rate': avg_cache_hit_rate,

            # Champion details
            'final_champion': champion_oos.to_dict(),

            # Evolution summary
            'evolution_summary': summary
        }

        # Log results
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("RESULTS SUMMARY")
        self.logger.info("=" * 70)
        self.logger.info(f"Total generations: {self.num_generations}")
        self.logger.info(f"Champion updates: {summary['champion_updates_count']} ({champion_update_rate:.1f}%)")
        self.logger.info(f"Best IS Sharpe: {best_is_sharpe:.4f}")
        self.logger.info(f"Champion OOS Sharpe: {champion_oos_sharpe:.4f}")
        self.logger.info(f"Avg IS Sharpe: {avg_is_sharpe:.4f}")
        self.logger.info(f"Final diversity: {final_diversity:.1%}")
        self.logger.info(f"Restarts: {self.restart_count}")
        self.logger.info(f"Cache hit rate: {avg_cache_hit_rate:.1%}")
        self.logger.info("")

        # Decision analysis
        self.logger.info("=" * 70)
        self.logger.info("DECISION ANALYSIS")
        self.logger.info("=" * 70)

        success_criteria = (
            champion_update_rate >= 10.0 and
            best_is_sharpe > 2.5 and
            champion_oos_sharpe > 1.0
        )

        partial_criteria = (
            champion_update_rate >= 5.0 and
            best_is_sharpe > 2.0 and
            champion_oos_sharpe > 0.6
        )

        if success_criteria:
            self.logger.info("✅ SUCCESS - Phase 1 validated!")
            self.logger.info("   Proceed to production with population-based learning")
            results['decision'] = 'SUCCESS'
        elif partial_criteria:
            self.logger.info("⚠️  PARTIAL - Promising results, needs tuning")
            self.logger.info("   Re-test with adjusted hyperparameters")
            results['decision'] = 'PARTIAL'
        else:
            self.logger.info("❌ FAILURE - Did not meet targets")
            self.logger.info("   Investigate root cause and revise approach")
            results['decision'] = 'FAILURE'

        self.logger.info("=" * 70)

        return results
