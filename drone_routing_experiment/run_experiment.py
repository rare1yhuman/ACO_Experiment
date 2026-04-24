"""
Main Experiment Runner
Orchestrates all 4 trials with proper seed control and reproducibility.
"""

import os
import sys
import time
import random
import numpy as np
import pandas as pd
from typing import Dict

from grid_gen import generate_grid, DEPOT_POS
from graph_builder import build_graph, validate_graph
from dijkstra import build_dijkstra_tour
from aco import run_aco
from metrics import (collect_trial_metrics, compute_summary_statistics,
                    create_summary_table, save_trial_metrics,
                    save_summary_table, print_summary)
from visualise import (plot_dijkstra_route, plot_aco_route,
                      plot_grid_routes_overlaid,
                      plot_convergence, plot_path_score_heatmap,
                      plot_distance_comparison, plot_time_comparison,
                      plot_summary_dashboard)


# Experiment configuration
TRIALS = [
    {'id': 'A', 'seed': 42, 'has_nfz': True, 'description': 'Standard layout (100x100)'},
    {'id': 'B', 'seed': 7, 'has_nfz': True, 'description': 'Sparse NFZs (100x100)'},
    {'id': 'C', 'seed': 99, 'has_nfz': True, 'description': 'Dense NFZs (100x100)'},
    {'id': 'D', 'seed': 42, 'has_nfz': False, 'description': 'No NFZ control (100x100)'}
]

NUM_ACO_RUNS = 10  # Number of ACO repetitions per trial for statistics


def run_single_trial(trial_config: Dict, results_base_dir: str) -> Dict:
    """
    Run a single experimental trial.

    Args:
        trial_config: Trial configuration dict
        results_base_dir: Base directory for results

    Returns:
        Summary statistics dict
    """
    trial_id = trial_config['id']
    seed = trial_config['seed']
    has_nfz = trial_config['has_nfz']
    description = trial_config['description']

    print(f"\n{'='*70}")
    print(f"TRIAL {trial_id}: {description} (Seed {seed}, NFZ={has_nfz})")
    print(f"{'='*70}")

    # Set seeds for reproducibility
    np.random.seed(seed)
    random.seed(seed)

    # Create trial output directory
    trial_dir = os.path.join(results_base_dir, f"trial_{trial_id}_seed{seed}")
    os.makedirs(trial_dir, exist_ok=True)

    # Step 1: Generate environment
    print(f"\nStep 1: Generating grid...")
    grid, delivery_points, nfz_blocks = generate_grid(seed=seed, has_nfz=has_nfz)
    print(f"  Grid: {len(nfz_blocks)} NFZ blocks, {len(delivery_points)} delivery points")

    # Step 2: Build graph
    print(f"\nStep 2: Building graph...")
    G = build_graph(grid)
    validation = validate_graph(G, DEPOT_POS, delivery_points)
    print(f"  Graph: {validation['num_nodes']} nodes, {validation['num_edges']} edges")
    print(f"  Connected: {validation['is_connected']}, All paths exist: {validation['all_paths_exist']}")

    if not validation['all_paths_exist']:
        raise RuntimeError(f"Graph validation failed for trial {trial_id}")

    # Step 3: Run Dijkstra
    print(f"\nStep 3: Running Dijkstra...")
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)
    print(f"  Distance: {dijkstra_result['total_distance_m']:.1f}m")
    print(f"  Compute time: {dijkstra_result['compute_time_s']*1000:.1f}ms")

    # Step 4: Run ACO multiple times
    print(f"\nStep 4: Running ACO ({NUM_ACO_RUNS} runs)...")
    aco_results = []

    for run_id in range(NUM_ACO_RUNS):
        # Set run-specific seed for stochastic variation
        run_seed = seed + run_id * 1000
        random.seed(run_seed)

        print(f"  Run {run_id+1}/{NUM_ACO_RUNS}...", end='', flush=True)
        aco_result = run_aco(G, grid, DEPOT_POS, delivery_points,
                            dijkstra_result['total_distance_m'],
                            verbose=False)
        aco_results.append(aco_result)
        print(f" {aco_result['best_tour_distance']:.1f}m")

    # Use first ACO run for visualizations
    aco_representative = aco_results[0]

    # Step 5: Collect metrics
    print(f"\nStep 5: Collecting metrics...")
    trial_data = collect_trial_metrics(trial_id, seed, has_nfz,
                                      dijkstra_result, aco_results)
    save_trial_metrics(trial_data, trial_dir)

    summary = compute_summary_statistics(trial_data)
    print_summary(summary)

    # Step 6: Generate visualizations
    print(f"\nStep 6: Generating visualizations...")

    # Figure A: Dijkstra route only
    plot_dijkstra_route(grid, nfz_blocks, DEPOT_POS, delivery_points,
                       dijkstra_result['full_path'], dijkstra_result['total_distance_m'],
                       trial_id, seed,
                       os.path.join(trial_dir, 'fig_A_dijkstra.png'))

    # Figure B: ACO route only
    improvement = (dijkstra_result['total_distance_m'] - aco_representative['best_tour_distance']) / dijkstra_result['total_distance_m'] * 100
    plot_aco_route(grid, nfz_blocks, DEPOT_POS, delivery_points,
                  aco_representative['best_tour_path'], aco_representative['best_tour_distance'],
                  improvement, trial_id, seed,
                  os.path.join(trial_dir, 'fig_B_aco.png'))

    # Figure C: Convergence curve
    plot_convergence(aco_representative, dijkstra_result['total_distance_m'],
                    trial_id, os.path.join(trial_dir, 'fig_C_convergence.png'))

    # Figure D: Path score heatmap
    plot_path_score_heatmap(aco_representative['path_score_matrix'], grid, nfz_blocks,
                          trial_id, os.path.join(trial_dir, 'fig_D_path_score.png'))

    # Combined view (optional)
    plot_grid_routes_overlaid(grid, nfz_blocks, DEPOT_POS, delivery_points,
                             dijkstra_result['full_path'], aco_representative['best_tour_path'],
                             dijkstra_result['total_distance_m'], aco_representative['best_tour_distance'],
                             trial_id, seed,
                             os.path.join(trial_dir, 'fig_combined.png'))

    return summary


def main():
    """
    Run all experimental trials.
    """
    print("="*70)
    print("SIMULATION: Dijkstra vs ACO for Drone Routing with NFZs")
    print("="*70)
    print(f"\nExperiment Configuration:")
    print(f"  Total trials: {len(TRIALS)}")
    print(f"  ACO runs per trial: {NUM_ACO_RUNS}")
    print(f"  Total ACO runs: {len(TRIALS) * NUM_ACO_RUNS}")

    # Create results directory
    results_dir = 'results'
    os.makedirs(results_dir, exist_ok=True)

    # Run all trials
    start_time = time.time()
    all_summaries = []

    for trial_config in TRIALS:
        summary = run_single_trial(trial_config, results_dir)
        all_summaries.append(summary)

    # Create summary table
    print(f"\n\n{'='*70}")
    print("CREATING SUMMARY TABLE")
    print(f"{'='*70}")

    summary_df = create_summary_table(all_summaries)
    save_summary_table(summary_df, results_dir)

    # Generate cross-trial comparison figures
    print(f"\nGenerating cross-trial visualizations...")
    plot_distance_comparison(summary_df, os.path.join(results_dir, 'fig_E_distance.png'))
    plot_time_comparison(summary_df, os.path.join(results_dir, 'fig_F_time.png'))
    plot_summary_dashboard(summary_df, os.path.join(results_dir, 'summary_dashboard.png'))

    # Print final summary
    total_time = time.time() - start_time

    print(f"\n\n{'='*70}")
    print("EXPERIMENT COMPLETED")
    print(f"{'='*70}")
    print(f"\nTotal experiment time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")

    print(f"\nSummary Table:")
    print(summary_df.to_string(index=False))

    print(f"\nKey Findings:")
    overall = summary_df[summary_df['trial_id'] == 'Overall'].iloc[0]
    print(f"  Mean improvement: {overall['improvement_pct']:.2f}%")
    print(f"  Mean Dijkstra distance: {overall['dijkstra_distance_m']:.1f}m")
    print(f"  Mean ACO distance: {overall['aco_mean_distance_m']:.1f}m")

    print(f"\nOutputs:")
    print(f"  Results directory: {results_dir}/")
    print(f"  Trial directories: {len(TRIALS)}")

    print(f"\nExperiment complete! Results saved to '{results_dir}/' directory.\n")


if __name__ == '__main__':
    main()
