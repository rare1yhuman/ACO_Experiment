"""
Regenerate all 3 paper figures with UI/UX improvements.
Fig 1: City map (cleaned up)
Fig 2: Distance comparison (y-axis break, hatching)
Fig 3: ACO convergence curve (Trial C, replaces dashboard)
"""
import os
import sys
import random
import numpy as np
import pandas as pd

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grid_gen import generate_grid, DEPOT_POS
from graph_builder import build_graph
from dijkstra import build_dijkstra_tour
from aco import run_aco
from generate_city_map import generate_city_map
from visualise import plot_distance_comparison, plot_convergence_paper

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')

def main():
    print("=" * 60)
    print("REGENERATING ALL PAPER FIGURES")
    print("=" * 60)

    # --- Fig 1: City Map ---
    print("\n[1/3] Regenerating city map (fig_city_map.png)...")
    generate_city_map(seed=99, output_dir=RESULTS_DIR)

    # --- Fig 2: Distance Comparison Bar Chart ---
    print("\n[2/3] Regenerating distance comparison (fig_E_distance.png)...")
    summary_csv = os.path.join(RESULTS_DIR, 'summary_table.csv')
    summary_df = pd.read_csv(summary_csv)
    plot_distance_comparison(summary_df, os.path.join(RESULTS_DIR, 'fig_E_distance.png'))

    # --- Fig 3: ACO Convergence Curve (Trial C) ---
    print("\n[3/3] Generating convergence curve (fig_convergence_paper.png)...")
    print("  Re-running ACO for Trial C (seed=99) to capture convergence data...")
    
    seed = 99
    np.random.seed(seed)
    random.seed(seed)
    
    grid, delivery_points, nfz_blocks = generate_grid(seed=seed, has_nfz=True)
    G = build_graph(grid)
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)
    
    aco_result = run_aco(G, grid, DEPOT_POS, delivery_points,
                         dijkstra_result['total_distance_m'], verbose=True)
    
    plot_convergence_paper(
        convergence_curve=aco_result['convergence_curve'],
        avg_distances=aco_result['avg_distances'],
        dijkstra_baseline=dijkstra_result['total_distance_m'],
        output_path=os.path.join(RESULTS_DIR, 'fig_convergence_paper.png')
    )

    print("\n" + "=" * 60)
    print("ALL 3 FIGURES REGENERATED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Fig 1: {os.path.join(RESULTS_DIR, 'fig_city_map.png')}")
    print(f"  Fig 2: {os.path.join(RESULTS_DIR, 'fig_E_distance.png')}")
    print(f"  Fig 3: {os.path.join(RESULTS_DIR, 'fig_convergence_paper.png')}")


if __name__ == '__main__':
    main()
