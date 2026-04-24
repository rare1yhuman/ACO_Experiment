"""
Ant Colony Optimization (ACO) Module
Ant Colony System (ACS) for drone routing with two-level path score.

Two-level approach:
- High-level path score: Between delivery points (tour construction)
- Low-level navigation: Shortest paths on grid (Dijkstra)
"""

import networkx as nx
import numpy as np
import random
import time
from collections import defaultdict
from typing import List, Tuple, Dict, Set


# ACO Parameters
NUM_ANTS = 50
MAX_ITER = 200
ALPHA = 1.0         # Path score importance
BETA = 2.0          # Heuristic importance
RHO_GLOBAL = 0.1    # Global evaporation rate
RHO_LOCAL = 0.01    # Local evaporation rate
Q0 = 0.9            # Exploitation probability


def run_aco(G: nx.Graph, grid: np.ndarray, depot: Tuple[int, int],
            delivery_points: List[Tuple[int, int]],
            dijkstra_baseline: float,
            verbose: bool = False) -> Dict:
    """
    Run Ant Colony System.

    Uses two-level approach:
    1. Path score on delivery point pairs determines tour order
    2. Shortest paths used for actual navigation

    Args:
        G: NetworkX graph
        grid: N×N grid array (default 100×100)
        depot: Depot position
        delivery_points: List of delivery positions
        dijkstra_baseline: Baseline distance for path score initialization
        verbose: Print progress

    Returns:
        Dictionary with best tour and convergence data
    """
    start_time = time.perf_counter()

    # Pre-compute distances between all points
    all_points = [depot] + delivery_points
    precompute_start = time.perf_counter()
    distances = compute_distance_matrix(G, all_points)
    precompute_time = time.perf_counter() - precompute_start

    # Initialize path score on delivery point pairs
    tau_0 = 1.0 / ((len(delivery_points) + 1) * dijkstra_baseline)
    path_score = initialize_delivery_path_score(all_points, tau_0)

    if verbose:
        print(f"ACO initialized: tau_0={tau_0:.6e}, {len(all_points)} points")

    # Track best solution
    global_best_tour = None
    global_best_distance = float('inf')
    convergence_curve = []
    avg_distances = []

    # Main ACO loop
    optimization_start = time.perf_counter()
    for iteration in range(MAX_ITER):
        iteration_ants = []

        # Deploy ants
        for ant_id in range(NUM_ANTS):
            tour = construct_ant_tour(depot, delivery_points, distances,
                                     path_score, tau_0)

            if tour is not None:
                iteration_ants.append(tour)

        # Find best ant this iteration
        if iteration_ants:
            iteration_best = min(iteration_ants, key=lambda t: t['distance'])

            # Update global best
            if iteration_best['distance'] < global_best_distance:
                global_best_distance = iteration_best['distance']
                global_best_tour = iteration_best.copy()

            # Global path score update (only best ant)
            global_path_score_update(path_score, global_best_tour, tau_0)

            # Record convergence
            convergence_curve.append(global_best_distance)
            avg_dist = np.mean([ant['distance'] for ant in iteration_ants])
            avg_distances.append(avg_dist)

            if verbose and (iteration % 10 == 0 or iteration == MAX_ITER - 1):
                print(f"  Iter {iteration+1}/{MAX_ITER}: Best={global_best_distance:.1f}m, " +
                      f"Avg={avg_dist:.1f}m, Ants={len(iteration_ants)}/{NUM_ANTS}")

    optimization_time = time.perf_counter() - optimization_start
    compute_time = time.perf_counter() - start_time

    # Build full cell-by-cell path from best tour order
    full_path = []
    if global_best_tour:
        for i in range(len(global_best_tour['order']) - 1):
            source = global_best_tour['order'][i]
            target = global_best_tour['order'][i + 1]
            segment = nx.shortest_path(G, source, target, weight='weight')

            if i == 0:
                full_path.extend(segment)
            else:
                full_path.extend(segment[1:])

    # Find convergence iteration
    convergence_iter = 0
    for i in range(1, len(convergence_curve)):
        if convergence_curve[i] < convergence_curve[i-1]:
            convergence_iter = i

    # Compute path score heatmap for visualization
    path_score_matrix = compute_path_score_matrix(grid, path_score, all_points)

    return {
        'best_tour_path': full_path,
        'best_tour_distance': global_best_distance,
        'best_tour_order': global_best_tour['order'] if global_best_tour else [],
        'convergence_curve': convergence_curve,
        'avg_distances': avg_distances,
        'compute_time_s': compute_time,
        'precompute_time_s': precompute_time,
        'optimization_time_s': optimization_time,
        'convergence_iteration': convergence_iter,
        'path_score_matrix': path_score_matrix
    }


def compute_distance_matrix(G: nx.Graph, points: List[Tuple[int, int]]) -> Dict:
    """
    Pre-compute shortest path distances between all point pairs.

    Returns dict: {(point1, point2): distance}
    """
    distances = {}

    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i != j:
                try:
                    dist = nx.shortest_path_length(G, p1, p2, weight='weight')
                    distances[(p1, p2)] = dist
                except nx.NetworkXNoPath:
                    distances[(p1, p2)] = float('inf')

    return distances


def initialize_delivery_path_score(points: List[Tuple[int, int]], tau_0: float) -> Dict:
    """
    Initialize path score on delivery point pairs.

    Returns dict: {(point1, point2): tau_0}
    """
    path_score = defaultdict(lambda: tau_0)

    # Initialize all pairs
    for i, p1 in enumerate(points):
        for j, p2 in enumerate(points):
            if i != j:
                edge_key = tuple(sorted([p1, p2]))
                path_score[edge_key] = tau_0

    return path_score


def construct_ant_tour(depot: Tuple[int, int],
                      delivery_points: List[Tuple[int, int]],
                      distances: Dict,
                      path_score: Dict, tau_0: float) -> Dict:
    """
    Construct tour for one ant using ACS decision rule.

    Ant chooses next delivery point based on path score and distance.

    Returns:
        Dictionary with tour order and distance, or None if failed
    """
    current = depot
    unvisited = set(delivery_points)
    tour_order = [depot]
    total_distance = 0.0

    # Visit all delivery points
    while unvisited:
        # ACS transition rule: choose next delivery point
        if random.random() < Q0:
            # Exploitation: choose best
            next_point = choose_best_delivery(current, unvisited, distances,
                                             path_score, ALPHA, BETA)
        else:
            # Exploration: probabilistic
            next_point = choose_probabilistic_delivery(current, unvisited, distances,
                                                       path_score, ALPHA, BETA)

        # Add to tour
        tour_order.append(next_point)
        leg_distance = distances.get((current, next_point), float('inf'))

        if leg_distance == float('inf'):
            return None  # No path exists

        total_distance += leg_distance

        # Local path score update
        edge_key = tuple(sorted([current, next_point]))
        path_score[edge_key] = ((1 - RHO_LOCAL) * path_score[edge_key] +
                               RHO_LOCAL * tau_0)

        # Update state
        current = next_point
        unvisited.remove(next_point)

    # Return to depot
    tour_order.append(depot)
    return_distance = distances.get((current, depot), float('inf'))

    if return_distance == float('inf'):
        return None

    total_distance += return_distance

    return {
        'order': tour_order,
        'distance': total_distance
    }


def choose_best_delivery(current: Tuple[int, int],
                        unvisited: Set[Tuple[int, int]],
                        distances: Dict,
                        path_score: Dict,
                        alpha: float, beta: float) -> Tuple[int, int]:
    """
    Choose next delivery point with highest attractiveness.

    Attractiveness = tau^alpha * eta^beta
    where eta = 1 / distance
    """
    best_score = -1
    best_point = None

    for point in unvisited:
        tau = get_path_score(path_score, current, point)
        dist = distances.get((current, point), float('inf'))

        if dist == float('inf'):
            continue

        eta = 1.0 / dist
        score = (tau ** alpha) * (eta ** beta)

        if score > best_score:
            best_score = score
            best_point = point

    return best_point if best_point else list(unvisited)[0]


def choose_probabilistic_delivery(current: Tuple[int, int],
                                  unvisited: Set[Tuple[int, int]],
                                  distances: Dict,
                                  path_score: Dict,
                                  alpha: float, beta: float) -> Tuple[int, int]:
    """
    Choose next delivery point probabilistically.

    Probability proportional to tau^alpha * eta^beta.
    """
    candidates = []
    scores = []

    for point in unvisited:
        tau = get_path_score(path_score, current, point)
        dist = distances.get((current, point), float('inf'))

        if dist == float('inf'):
            continue

        eta = 1.0 / dist
        score = (tau ** alpha) * (eta ** beta)

        candidates.append(point)
        scores.append(score)

    if not candidates:
        return list(unvisited)[0]

    # Normalize to probabilities
    total = sum(scores)
    if total == 0:
        return random.choice(candidates)

    probabilities = [s / total for s in scores]

    # Roulette wheel selection
    r = random.random()
    cumulative = 0.0

    for i, prob in enumerate(probabilities):
        cumulative += prob
        if r <= cumulative:
            return candidates[i]

    return candidates[-1]


def get_path_score(path_score: Dict, node1: Tuple[int, int],
                 node2: Tuple[int, int]) -> float:
    """Get path score value for edge (direction-independent)."""
    edge_key = tuple(sorted([node1, node2]))
    return path_score[edge_key]


def global_path_score_update(path_score: Dict, best_tour: Dict, tau_0: float):
    """
    Update path score on edges of best tour (ACS global update).

    tau(edge) = (1 - rho_global) * tau(edge) + rho_global * (1 / L_best)
    """
    if best_tour is None:
        return

    order = best_tour['order']
    delta_tau = 1.0 / best_tour['distance']

    # Update all edges in tour
    for i in range(len(order) - 1):
        edge_key = tuple(sorted([order[i], order[i+1]]))
        path_score[edge_key] = ((1 - RHO_GLOBAL) * path_score[edge_key] +
                               RHO_GLOBAL * delta_tau)


def compute_path_score_matrix(grid: np.ndarray, path_score: Dict,
                            points: List[Tuple[int, int]]) -> np.ndarray:
    """
    Compute path score heatmap for visualization.

    Maps delivery-point-level path score to grid cells.
    """
    rows, cols = grid.shape
    heatmap = np.zeros((rows, cols))

    # For each cell, sum path score on edges passing through it
    # Approximate: cells near high path score delivery point pairs get high values
    for (p1, p2), tau in path_score.items():
        # Linear interpolation between points
        r1, c1 = p1
        r2, c2 = p2

        # Parametric line
        steps = max(abs(r2 - r1), abs(c2 - c1))
        if steps == 0:
            continue

        for t in np.linspace(0, 1, steps * 2):
            r = int(r1 + t * (r2 - r1))
            c = int(c1 + t * (c2 - c1))

            if 0 <= r < rows and 0 <= c < cols:
                heatmap[r, c] += tau

    return heatmap


if __name__ == '__main__':
    """Test ACO implementation."""
    from grid_gen import generate_grid, DEPOT_POS
    from graph_builder import build_graph
    from dijkstra import build_dijkstra_tour

    print("Testing ACO implementation...\n")

    # Generate environment
    grid, delivery_points, nfz_blocks = generate_grid(seed=42, has_nfz=True)
    print(f"Grid: {len(nfz_blocks)} NFZ blocks, {len(delivery_points)} delivery points")

    G = build_graph(grid)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Run Dijkstra for baseline
    print("\nRunning Dijkstra baseline...")
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)
    print(f"Dijkstra: {dijkstra_result['total_distance_m']:.1f}m in {dijkstra_result['compute_time_s']*1000:.1f}ms")

    # Run ACO
    print(f"\nRunning ACO ({NUM_ANTS} ants, {MAX_ITER} iterations)...")
    aco_result = run_aco(G, grid, DEPOT_POS, delivery_points,
                        dijkstra_result['total_distance_m'],
                        verbose=True)

    print(f"\nACO Results:")
    print(f"  Best distance: {aco_result['best_tour_distance']:.1f}m")
    print(f"  Compute time: {aco_result['compute_time_s']:.2f}s")
    print(f"  Converged at iteration: {aco_result['convergence_iteration']}")

    print(f"\nComparison:")
    print(f"  Dijkstra: {dijkstra_result['total_distance_m']:.1f}m")
    print(f"  ACO:      {aco_result['best_tour_distance']:.1f}m")

    improvement = (dijkstra_result['total_distance_m'] - aco_result['best_tour_distance']) / dijkstra_result['total_distance_m'] * 100

    if improvement > 0:
        print(f"  ACO is {improvement:.2f}% BETTER (shorter path)")
    else:
        print(f"  ACO is {-improvement:.2f}% WORSE (longer path)")

    print(f"\n  Compute time ratio: ACO is {aco_result['compute_time_s'] / dijkstra_result['compute_time_s']:.1f}x slower")

    # Show tour orders
    print(f"\n  Dijkstra tour order:")
    for i, stop in enumerate(dijkstra_result['stop_order'][:3]):
        if stop == DEPOT_POS:
            print(f"    {i}: Depot")
        else:
            idx = delivery_points.index(stop)
            print(f"    {i}: D{idx+1}")
    print(f"    ...")

    print(f"\n  ACO best tour order:")
    for i, stop in enumerate(aco_result['best_tour_order'][:3]):
        if stop == DEPOT_POS:
            print(f"    {i}: Depot")
        else:
            idx = delivery_points.index(stop)
            print(f"    {i}: D{idx+1}")
    print(f"    ...")
