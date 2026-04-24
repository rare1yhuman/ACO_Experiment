"""
Sensitivity Analysis Module
ACO parameter sweep for alpha and beta values.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import random
import os
from itertools import product

from grid_gen import generate_grid, DEPOT_POS
from graph_builder import build_graph
from dijkstra import build_dijkstra_tour
from aco import run_aco


# Parameter ranges
ALPHA_RANGE = [0.5, 1.0, 1.5, 2.0]
BETA_RANGE = [1.0, 2.0, 3.0, 4.0]
NUM_RUNS_PER_CONFIG = 5  # Reduced for speed


def run_sensitivity_analysis(output_dir: str = 'results/sensitivity'):
    """
    Run parameter sweep for ACO alpha and beta values.

    Tests all combinations of alpha and beta to find optimal region.

    Args:
        output_dir: Directory to save results
    """
    print("="*70)
    print("ACO SENSITIVITY ANALYSIS: Alpha vs Beta Parameter Sweep")
    print("="*70)
    print(f"\nConfiguration:")
    print(f"  Alpha values: {ALPHA_RANGE}")
    print(f"  Beta values: {BETA_RANGE}")
    print(f"  Combinations: {len(ALPHA_RANGE) * len(BETA_RANGE)}")
    print(f"  Runs per combination: {NUM_RUNS_PER_CONFIG}")
    print(f"  Total ACO runs: {len(ALPHA_RANGE) * len(BETA_RANGE) * NUM_RUNS_PER_CONFIG}")

    # Use Trial A configuration (seed 42, with NFZ)
    seed = 42
    np.random.seed(seed)
    random.seed(seed)

    print(f"\nUsing Trial A configuration (seed {seed}, with NFZ)...")
    grid, delivery_points, nfz_blocks = generate_grid(seed=seed, has_nfz=True)
    G = build_graph(grid)

    # Run Dijkstra baseline
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)
    dijkstra_distance = dijkstra_result['total_distance_m']
    print(f"Dijkstra baseline: {dijkstra_distance:.1f}m")

    # Parameter sweep
    results = []
    total_configs = len(ALPHA_RANGE) * len(BETA_RANGE)
    config_count = 0

    print(f"\nRunning parameter sweep...")

    for alpha in ALPHA_RANGE:
        for beta in BETA_RANGE:
            config_count += 1
            print(f"  [{config_count}/{total_configs}] Alpha={alpha:.1f}, Beta={beta:.1f}...", end='', flush=True)

            # Temporarily modify ACO parameters
            import aco
            original_alpha = aco.ALPHA
            original_beta = aco.BETA

            aco.ALPHA = alpha
            aco.BETA = beta

            # Run multiple times
            distances = []
            for run_id in range(NUM_RUNS_PER_CONFIG):
                run_seed = seed + run_id * 1000
                random.seed(run_seed)

                aco_result = run_aco(G, grid, DEPOT_POS, delivery_points,
                                    dijkstra_distance, verbose=False)
                distances.append(aco_result['best_tour_distance'])

            # Restore original parameters
            aco.ALPHA = original_alpha
            aco.BETA = original_beta

            mean_dist = np.mean(distances)
            std_dist = np.std(distances)
            improvement = (dijkstra_distance - mean_dist) / dijkstra_distance * 100

            results.append({
                'alpha': alpha,
                'beta': beta,
                'mean_distance': mean_dist,
                'std_distance': std_dist,
                'improvement_pct': improvement
            })

            print(f" {mean_dist:.1f}m ({improvement:+.2f}%)")

    # Create results DataFrame
    results_df = pd.DataFrame(results)

    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'sensitivity_results.csv')
    results_df.to_csv(csv_path, index=False)
    print(f"\nResults saved to {csv_path}")

    # Create pivot tables for heatmaps
    heatmap_distance = results_df.pivot(index='beta', columns='alpha', values='mean_distance')
    heatmap_improvement = results_df.pivot(index='beta', columns='alpha', values='improvement_pct')

    # Plot heatmaps
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Heatmap 1: Mean distance
    sns.heatmap(heatmap_distance, annot=True, fmt='.0f', cmap='YlOrRd_r',
                ax=axes[0], cbar_kws={'label': 'Mean Distance (m)'})
    axes[0].set_title('ACO Mean Distance by Alpha & Beta\n(Lower is Better)', fontsize=14)
    axes[0].set_xlabel('Alpha (Path Score Importance)', fontsize=12)
    axes[0].set_ylabel('Beta (Heuristic Importance)', fontsize=12)

    # Heatmap 2: Improvement percentage
    sns.heatmap(heatmap_improvement, annot=True, fmt='.2f', cmap='RdYlGn',
                ax=axes[1], cbar_kws={'label': 'Improvement (%)'}, center=0)
    axes[1].set_title('ACO Improvement vs Dijkstra\n(Positive = Better)', fontsize=14)
    axes[1].set_xlabel('Alpha (Path Score Importance)', fontsize=12)
    axes[1].set_ylabel('Beta (Heuristic Importance)', fontsize=12)

    # Add reference to baseline
    fig.suptitle(f'ACO Parameter Sensitivity Analysis (Dijkstra Baseline: {dijkstra_distance:.0f}m)',
                 fontsize=16, y=1.02)

    plt.tight_layout()
    heatmap_path = os.path.join(output_dir, 'sensitivity_heatmap.png')
    plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {heatmap_path}")

    # Find optimal parameters
    best_config = results_df.loc[results_df['improvement_pct'].idxmax()]
    print(f"\nOptimal Configuration:")
    print(f"  Alpha: {best_config['alpha']:.1f}")
    print(f"  Beta: {best_config['beta']:.1f}")
    print(f"  Mean distance: {best_config['mean_distance']:.1f}m")
    print(f"  Improvement: {best_config['improvement_pct']:.2f}%")

    # Validate default parameters
    default_result = results_df[(results_df['alpha'] == 1.0) & (results_df['beta'] == 2.0)]
    if not default_result.empty:
        default = default_result.iloc[0]
        print(f"\nDefault Configuration (α=1.0, β=2.0):")
        print(f"  Mean distance: {default['mean_distance']:.1f}m")
        print(f"  Improvement: {default['improvement_pct']:.2f}%")
        print(f"  Ranking: {results_df['improvement_pct'].rank(ascending=False).loc[default_result.index[0]]:.0f}/" +
              f"{len(results_df)}")

    print(f"\n{'='*70}")
    print("SENSITIVITY ANALYSIS COMPLETE")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    run_sensitivity_analysis()
