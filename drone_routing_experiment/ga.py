"""
Genetic Algorithm (GA) Module
GA for drone routing with two-level architecture (same as ACO).

Two-level approach:
- High-level GA: Evolves delivery point visit order (permutation)
- Low-level navigation: Shortest paths on grid (Dijkstra)

Matched evaluation budget: 100 population × 100 generations = 10,000 evaluations
(Same as ACO's 50 ants × 200 iterations = 10,000 evaluations)
"""

import networkx as nx
import numpy as np
import random
import time
from typing import List, Tuple, Dict

# Import distance matrix computation from ACO module
from aco import compute_distance_matrix


# GA Parameters
POPULATION_SIZE = 100
MAX_GENERATIONS = 100
CROSSOVER_RATE = 0.8
MUTATION_RATE = 0.1
TOURNAMENT_SIZE = 5
ELITISM_COUNT = 2  # Top individuals preserved unchanged


def run_ga(G: nx.Graph, grid: np.ndarray, depot: Tuple[int, int],
           delivery_points: List[Tuple[int, int]],
           dijkstra_baseline: float,
           verbose: bool = False) -> Dict:
    """
    Run Genetic Algorithm for drone routing.

    Uses same two-level approach as ACO:
    1. GA evolves delivery point visit order (permutation encoding)
    2. Dijkstra shortest paths used for actual navigation

    Args:
        G: NetworkX graph
        grid: N×N grid array (default 100×100)
        depot: Depot position
        delivery_points: List of delivery positions
        dijkstra_baseline: Baseline distance (for reference)
        verbose: Print progress

    Returns:
        Dictionary with best tour and convergence data (same format as run_aco)
    """
    start_time = time.perf_counter()

    # Pre-compute distances between all points (same as ACO)
    all_points = [depot] + delivery_points
    precompute_start = time.perf_counter()
    distances = compute_distance_matrix(G, all_points)
    precompute_time = time.perf_counter() - precompute_start

    n = len(delivery_points)

    if verbose:
        print(f"GA initialized: {POPULATION_SIZE} pop, {MAX_GENERATIONS} gen, {n} delivery points")

    # Initialize population (random permutations of delivery points)
    population = []
    for _ in range(POPULATION_SIZE):
        perm = list(delivery_points)
        random.shuffle(perm)
        population.append(perm)

    # Evaluate initial population
    fitness = [evaluate_tour(ind, depot, distances) for ind in population]

    # Track best solution
    global_best_idx = np.argmin(fitness)
    global_best_tour = population[global_best_idx][:]
    global_best_distance = fitness[global_best_idx]
    convergence_curve = []
    avg_distances = []

    # Main GA loop
    optimization_start = time.perf_counter()
    for generation in range(MAX_GENERATIONS):
        # Selection + Crossover + Mutation → new population
        new_population = []

        # Elitism: keep top individuals
        sorted_indices = np.argsort(fitness)
        for i in range(ELITISM_COUNT):
            new_population.append(population[sorted_indices[i]][:])

        # Fill rest of population
        while len(new_population) < POPULATION_SIZE:
            # Tournament selection
            parent1 = tournament_select(population, fitness, TOURNAMENT_SIZE)
            parent2 = tournament_select(population, fitness, TOURNAMENT_SIZE)

            # Crossover
            if random.random() < CROSSOVER_RATE:
                child1, child2 = order_crossover(parent1, parent2)
            else:
                child1, child2 = parent1[:], parent2[:]

            # Mutation
            if random.random() < MUTATION_RATE:
                child1 = swap_mutation(child1)
            if random.random() < MUTATION_RATE:
                child2 = swap_mutation(child2)

            # 2-opt local search (applied with low probability for efficiency)
            if random.random() < 0.1:
                child1 = two_opt_improve(child1, depot, distances)
            if random.random() < 0.1:
                child2 = two_opt_improve(child2, depot, distances)

            new_population.append(child1)
            if len(new_population) < POPULATION_SIZE:
                new_population.append(child2)

        population = new_population
        fitness = [evaluate_tour(ind, depot, distances) for ind in population]

        # Update global best
        gen_best_idx = np.argmin(fitness)
        gen_best_distance = fitness[gen_best_idx]

        if gen_best_distance < global_best_distance:
            global_best_distance = gen_best_distance
            global_best_tour = population[gen_best_idx][:]

        # Record convergence
        convergence_curve.append(global_best_distance)
        avg_dist = np.mean(fitness)
        avg_distances.append(avg_dist)

        if verbose and (generation % 10 == 0 or generation == MAX_GENERATIONS - 1):
            print(f"  Gen {generation+1}/{MAX_GENERATIONS}: Best={global_best_distance:.1f}m, "
                  f"Avg={avg_dist:.1f}m")

    optimization_time = time.perf_counter() - optimization_start
    compute_time = time.perf_counter() - start_time

    # Build full cell-by-cell path from best tour order
    best_order = [depot] + global_best_tour + [depot]
    full_path = []

    for i in range(len(best_order) - 1):
        source = best_order[i]
        target = best_order[i + 1]
        segment = nx.shortest_path(G, source, target, weight='weight')

        if i == 0:
            full_path.extend(segment)
        else:
            full_path.extend(segment[1:])

    # Find convergence generation (last time best improved)
    convergence_gen = 0
    for i in range(1, len(convergence_curve)):
        if convergence_curve[i] < convergence_curve[i-1]:
            convergence_gen = i

    return {
        'best_tour_path': full_path,
        'best_tour_distance': global_best_distance,
        'best_tour_order': best_order,
        'convergence_curve': convergence_curve,
        'avg_distances': avg_distances,
        'compute_time_s': compute_time,
        'precompute_time_s': precompute_time,
        'optimization_time_s': optimization_time,
        'convergence_generation': convergence_gen,
        'convergence_iteration': convergence_gen,  # Alias for compatibility
    }


def evaluate_tour(individual: List[Tuple[int, int]],
                  depot: Tuple[int, int],
                  distances: Dict) -> float:
    """
    Evaluate total tour distance for a permutation.

    Tour: depot → individual[0] → individual[1] → ... → depot
    """
    total = 0.0
    current = depot

    for point in individual:
        dist = distances.get((current, point), float('inf'))
        if dist == float('inf'):
            return float('inf')
        total += dist
        current = point

    # Return to depot
    dist = distances.get((current, depot), float('inf'))
    if dist == float('inf'):
        return float('inf')
    total += dist

    return total


def tournament_select(population: List, fitness: List[float],
                      tournament_size: int) -> List:
    """
    Tournament selection: pick best from random subset.
    """
    indices = random.sample(range(len(population)), tournament_size)
    best_idx = min(indices, key=lambda i: fitness[i])
    return population[best_idx][:]


def order_crossover(parent1: List, parent2: List) -> Tuple[List, List]:
    """
    Order Crossover (OX) — standard for TSP permutations.

    1. Select random segment from parent1
    2. Fill remaining positions with order from parent2
    """
    n = len(parent1)
    if n < 2:
        return parent1[:], parent2[:]

    # Select crossover segment
    start = random.randint(0, n - 2)
    end = random.randint(start + 1, n - 1)

    # Child 1: segment from parent1, rest from parent2
    child1 = [None] * n
    child1[start:end+1] = parent1[start:end+1]

    # Fill from parent2 in order, skipping already-placed elements
    segment_set = set(parent1[start:end+1])
    fill_pos = (end + 1) % n
    for gene in parent2:
        if gene not in segment_set:
            child1[fill_pos] = gene
            fill_pos = (fill_pos + 1) % n

    # Child 2: segment from parent2, rest from parent1
    child2 = [None] * n
    child2[start:end+1] = parent2[start:end+1]

    segment_set = set(parent2[start:end+1])
    fill_pos = (end + 1) % n
    for gene in parent1:
        if gene not in segment_set:
            child2[fill_pos] = gene
            fill_pos = (fill_pos + 1) % n

    return child1, child2


def swap_mutation(individual: List) -> List:
    """
    Swap mutation: exchange two random positions.
    """
    result = individual[:]
    if len(result) < 2:
        return result

    i, j = random.sample(range(len(result)), 2)
    result[i], result[j] = result[j], result[i]
    return result


def two_opt_improve(individual: List[Tuple[int, int]],
                    depot: Tuple[int, int],
                    distances: Dict) -> List:
    """
    2-opt local search: try reversing segments to reduce tour distance.

    Limited to a fixed number of iterations for efficiency.
    """
    best = individual[:]
    best_dist = evaluate_tour(best, depot, distances)
    improved = True
    max_iterations = 50  # Cap iterations for efficiency

    iteration = 0
    while improved and iteration < max_iterations:
        improved = False
        iteration += 1

        for i in range(len(best) - 1):
            for j in range(i + 2, len(best)):
                # Try reversing segment [i+1, j]
                candidate = best[:i+1] + best[i+1:j+1][::-1] + best[j+1:]
                candidate_dist = evaluate_tour(candidate, depot, distances)

                if candidate_dist < best_dist:
                    best = candidate
                    best_dist = candidate_dist
                    improved = True
                    break
            if improved:
                break

    return best


if __name__ == '__main__':
    """Test GA implementation."""
    from grid_gen import generate_grid, DEPOT_POS
    from graph_builder import build_graph
    from dijkstra import build_dijkstra_tour

    print("Testing GA implementation...\n")

    # Generate environment
    grid, delivery_points, nfz_blocks = generate_grid(seed=42, has_nfz=True)
    print(f"Grid: {len(nfz_blocks)} NFZ blocks, {len(delivery_points)} delivery points")

    G = build_graph(grid)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Run Dijkstra for baseline
    print("\nRunning Dijkstra baseline...")
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)
    print(f"Dijkstra: {dijkstra_result['total_distance_m']:.1f}m in {dijkstra_result['compute_time_s']*1000:.1f}ms")

    # Run GA
    print(f"\nRunning GA ({POPULATION_SIZE} pop, {MAX_GENERATIONS} gen)...")
    ga_result = run_ga(G, grid, DEPOT_POS, delivery_points,
                       dijkstra_result['total_distance_m'],
                       verbose=True)

    print(f"\nGA Results:")
    print(f"  Best distance: {ga_result['best_tour_distance']:.1f}m")
    print(f"  Compute time: {ga_result['compute_time_s']:.2f}s")
    print(f"    Precompute: {ga_result['precompute_time_s']:.2f}s")
    print(f"    Optimization: {ga_result['optimization_time_s']:.2f}s")
    print(f"  Converged at generation: {ga_result['convergence_generation']}")

    print(f"\nComparison:")
    print(f"  Dijkstra: {dijkstra_result['total_distance_m']:.1f}m")
    print(f"  GA:       {ga_result['best_tour_distance']:.1f}m")

    improvement = (dijkstra_result['total_distance_m'] - ga_result['best_tour_distance']) / dijkstra_result['total_distance_m'] * 100

    if improvement > 0:
        print(f"  GA is {improvement:.2f}% BETTER (shorter path)")
    else:
        print(f"  GA is {-improvement:.2f}% WORSE (longer path)")
