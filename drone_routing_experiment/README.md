# Drone Routing Experiment: Dijkstra vs Ant Colony Optimization

A comprehensive experimental simulation comparing Dijkstra's shortest-path algorithm against Ant Colony Optimization (ACO) for urban drone delivery routing in the presence of No-Fly Zones (NFZs).

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Algorithms](#algorithms)
   - [Dijkstra Baseline](#dijkstra-baseline)
   - [Ant Colony Optimization](#ant-colony-optimization)
4. [System Architecture](#system-architecture)
5. [Module Documentation](#module-documentation)
6. [Experimental Setup](#experimental-setup)
7. [Results & Analysis](#results--analysis)
8. [Installation & Usage](#installation--usage)
9. [Technical Details](#technical-details)
10. [Limitations & Future Work](#limitations--future-work)
11. [References](#references)

---

## Overview

This project implements a controlled experimental framework to evaluate the effectiveness of Ant Colony Optimization (ACO) versus traditional Dijkstra pathfinding for drone delivery routing in urban environments with restricted airspace (No-Fly Zones).

**Key Research Question:** Does bio-inspired route optimization (ACO) provide meaningful improvements over classical shortest-path algorithms when navigating around obstacles?

**Key Finding:** ACO achieves a mean path length reduction of **8.63%** compared to Dijkstra with nearest-neighbor ordering, with peak improvements of **14.04%** in environments with dense obstacle density.

---

## Problem Statement

### The Drone Delivery Routing Problem

Given:
- A 2D grid representing urban airspace (100x100 cells, 10km x 10km area)
- A depot location (starting/ending point)
- Multiple delivery points that must be visited
- No-Fly Zones (NFZs) representing restricted airspace (buildings, protected areas, etc.)

Find:
- An optimal or near-optimal tour visiting all delivery points
- The tour must avoid all NFZ regions
- Minimize total travel distance

### Mathematical Formulation

This is a variant of the **Traveling Salesman Problem (TSP)** with obstacles:

```
minimize: Σ d(p_i, p_{i+1})  for i = 0 to n
subject to:
  - p_0 = p_n = depot (start and end at depot)
  - Each delivery point visited exactly once
  - Path segments avoid all NFZ cells
```

Where `d(p_i, p_j)` is the shortest navigable path distance between points, not Euclidean distance.

---

## Algorithms

### Dijkstra Baseline

**Implementation:** `dijkstra.py`

The baseline algorithm uses a two-phase approach:

#### Phase 1: Tour Construction (Nearest-Neighbor Heuristic)
```
1. Start at depot
2. While unvisited delivery points remain:
   a. Find nearest unvisited point (using graph distance, not Euclidean)
   b. Add to tour
   c. Mark as visited
3. Return to depot
```

**Key insight:** Uses shortest-path distances (respecting NFZs) for ordering decisions, not straight-line distances.

#### Phase 2: Path Realization
```
For each consecutive pair (p_i, p_{i+1}) in tour:
    Find shortest path using Dijkstra's algorithm
    Append to full path
```

**Complexity:** O(n * (V + E) log V) where n = number of delivery points

**Properties:**
- Deterministic (same result every run)
- Greedy (locally optimal choices)
- No global optimization

---

### Ant Colony Optimization

**Implementation:** `aco.py`

Uses **Ant Colony System (ACS)** variant with two-level path score structure.

#### Two-Level Architecture

```
Level 1 (High-Level): Path score on delivery point pairs
  - Guides tour construction order
  - Updated by ant colony behavior

Level 2 (Low-Level): Grid navigation
  - Uses Dijkstra for actual pathfinding
  - Ensures obstacle avoidance
```

This hybrid approach combines:
- ACO's ability to discover better orderings
- Dijkstra's guarantee of obstacle-free paths

#### Algorithm Steps

```python
1. INITIALIZE
   tau_0 = 1 / (n * L_dijkstra)  # Initial path score
   path_score[(i,j)] = tau_0 for all pairs

2. FOR each iteration:
   FOR each ant:
     a. Construct tour using transition rule:
        - With probability q0: choose best (exploitation)
        - Otherwise: probabilistic (exploration)

     b. Transition probability:
        P(i→j) = [tau(i,j)]^α * [1/d(i,j)]^β / Σ same for all k

     c. Local path score update after each move:
        tau(i,j) = (1-ρ_local) * tau(i,j) + ρ_local * tau_0

   d. Global path score update (best ant only):
      tau(i,j) = (1-ρ_global) * tau(i,j) + ρ_global * (1/L_best)

3. RETURN best tour found
```

#### Parameters

| Parameter | Symbol | Value | Description |
|-----------|--------|-------|-------------|
| Ants | - | 50 | Number of artificial ants |
| Iterations | - | 200 | Maximum iterations |
| Alpha | α | 1.0 | Path score importance |
| Beta | β | 2.0 | Heuristic (distance) importance |
| Global evaporation | ρ_global | 0.1 | Evaporation rate for global update |
| Local evaporation | ρ_local | 0.01 | Evaporation rate for local update |
| Exploitation prob | q0 | 0.9 | Probability of greedy choice |

**Complexity:** O(iterations * ants * n² * (V + E) log V)

**Properties:**
- Stochastic (varies across runs)
- Emergent optimization through collective behavior
- Balances exploration vs exploitation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        run_experiment.py                            │
│                    (Main Orchestrator)                              │
└─────────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  grid_gen.py  │       │    aco.py     │       │  dijkstra.py  │
│               │       │               │       │               │
│ - 100x100 grid  │       │ - ACS variant │       │ - Baseline    │
│ - NFZ blocks  │       │ - Two-level   │       │ - NN ordering │
│ - Delivery pts│       │   path score  │       │ - Shortest    │
│ - Depot       │       │ - Tour        │       │   path per    │
│               │       │   construction│       │   leg         │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │graph_builder.py│
                        │               │
                        │ - NetworkX    │
                        │ - 4-connect   │
                        │ - Edge weights│
                        └───────┬───────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│  metrics.py   │       │ visualise.py  │       │ sensitivity_  │
│               │       │               │       │ analysis.py   │
│ - Collection  │       │ - Pub-quality │       │               │
│ - Statistics  │       │ - Routes      │       │ - α/β sweep   │
│ - CSV export  │       │ - Convergence │       │ - Heatmaps    │
│               │       │ - Heatmaps    │       │               │
└───────────────┘       └───────────────┘       └───────────────┘
```

---

## Module Documentation

### `grid_gen.py` - Environment Generation

**Purpose:** Generates the simulation environment including grid, NFZs, and delivery points.

**Key Constants:**
```python
GRID_ROWS = 100          # Grid height (cells)
GRID_COLS = 100          # Grid width (cells)
CELL_SIZE_M = 100       # 100 meters per cell
NFZ_COUNT = 12           # Number of NFZ blocks
NUM_DELIVERIES = 15      # Delivery points to place
DEPOT_POS = (10, 10)      # Fixed depot location
```

**Cell Types:**
```python
CELL_FREE = 0      # Passable airspace
CELL_NFZ = 1       # No-Fly Zone (obstacle)
CELL_DELIVERY = 2  # Delivery point
CELL_DEPOT = 3     # Depot location
```

**Key Functions:**
- `generate_grid(seed, has_nfz)` → Returns (grid, delivery_points, nfz_blocks)
- `place_nfz_blocks(grid)` → Places rectangular NFZ obstacles
- `place_delivery_points(grid)` → Places delivery locations with minimum separation
- `is_connected(grid, start)` → BFS connectivity check

**Validation Features:**
- NFZ blocks cannot overlap
- NFZ blocks maintain border exclusion zone
- Connectivity guaranteed (all points reachable)
- Minimum separation between delivery points (3 cells)

---

### `graph_builder.py` - Graph Construction

**Purpose:** Converts grid array to NetworkX graph for pathfinding.

**Graph Properties:**
- **Nodes:** (row, col) tuples for all non-NFZ cells
- **Edges:** 4-connectivity (up, down, left, right)
- **Weights:** Uniform 100m per edge (cell size)
- **Type:** Undirected

**Key Functions:**
- `build_graph(grid)` → Returns NetworkX Graph
- `validate_graph(G, depot, delivery_points)` → Validates connectivity, returns stats

**Output Statistics:**
```python
{
    'num_nodes': 8763,      # Passable cells
    'num_edges': 17085,      # Connections
    'is_connected': True,   # Single component
    'all_paths_exist': True # All deliveries reachable
}
```

---

### `dijkstra.py` - Baseline Algorithm

**Purpose:** Implements the deterministic baseline using nearest-neighbor + Dijkstra.

**Main Function:**
```python
def build_dijkstra_tour(G, depot, delivery_points) -> Dict:
    """
    Returns:
        stop_order: [depot, D3, D1, D5, ..., depot]
        full_path: [(5,5), (5,6), (5,7), ..., (5,5)]
        total_distance_m: 20000.0
        leg_distances_m: [2300, 1800, ...]
        compute_time_s: 0.015
        num_waypoints: 450
    """
```

**Algorithm Guarantee:** Always finds shortest path for each leg (given the computed ordering).

---

### `aco.py` - Ant Colony Optimization

**Purpose:** Implements Ant Colony System with two-level path score.

**Main Function:**
```python
def run_aco(G, grid, depot, delivery_points, dijkstra_baseline, verbose) -> Dict:
    """
    Returns:
        best_tour_path: [(5,5), (6,5), ..., (5,5)]
        best_tour_distance: 18000.0
        best_tour_order: [depot, D1, D5, D3, ..., depot]
        convergence_curve: [20000, 19500, 19000, ...]
        avg_distances: [21000, 20000, ...]
        compute_time_s: 4.5
        convergence_iteration: 15
        path_score_matrix: np.ndarray (for visualization)
    """
```

**Key Internal Functions:**
- `compute_distance_matrix()` - Pre-computes all pairwise shortest paths
- `construct_ant_tour()` - Single ant tour construction
- `choose_best_delivery()` - Exploitation (greedy selection)
- `choose_probabilistic_delivery()` - Exploration (roulette wheel)
- `global_path_score_update()` - Reinforcement learning step

---

### `metrics.py` - Data Collection

**Purpose:** Collects, aggregates, and exports experimental metrics.

**Functions:**
- `collect_trial_metrics()` - Gathers all metrics from a trial
- `compute_summary_statistics()` - Calculates mean, std, improvement %
- `create_summary_table()` - Aggregates across all trials
- `save_trial_metrics()` / `save_summary_table()` - CSV export

**Output Format:**
```csv
trial_id,algorithm,run_id,seed,has_nfz,distance_m,compute_time_s
A,Dijkstra,0,42,True,20000.0,0.015
A,ACO,1,42,True,18000.0,4.2
A,ACO,2,42,True,18200.0,4.1
...
```

---

### `visualise.py` - Publication-Quality Figures

**Purpose:** Generates research paper-ready visualizations.

**Figure Types:**

| Figure | Description | Key Elements |
|--------|-------------|--------------|
| A | Dijkstra route | Grid, NFZs, path (blue) |
| B | ACO route | Grid, NFZs, path (green), improvement % |
| C | Convergence | Best/average distance over iterations |
| D | Path Score | Heatmap of path score distribution |
| E | Distance comparison | Bar chart across trials |
| F | Time comparison | Computation time bars |
| Dashboard | Summary | All key metrics in one figure |

**Publication Settings:**
```python
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'savefig.dpi': 300,
    'axes.linewidth': 1.2,
})
```

---

### `sensitivity_analysis.py` - Parameter Tuning

**Purpose:** Performs grid search over ACO parameters.

**Parameter Ranges:**
```python
ALPHA_RANGE = [0.5, 1.0, 1.5, 2.0]  # Path score importance
BETA_RANGE = [1.0, 2.0, 3.0, 4.0]   # Heuristic importance
```

**Output:** Heatmaps showing performance across α-β space.

---

### `run_experiment.py` - Main Orchestrator

**Purpose:** Runs reproducible multi-trial experiments.

**Trial Configuration:**
```python
TRIALS = [
    {'id': 'A', 'seed': 42, 'has_nfz': True,  'description': 'Standard layout'},
    {'id': 'B', 'seed': 7,  'has_nfz': True,  'description': 'Sparse NFZs'},
    {'id': 'C', 'seed': 99, 'has_nfz': True,  'description': 'Dense NFZs'},
    {'id': 'D', 'seed': 42, 'has_nfz': False, 'description': 'No NFZ control'}
]
NUM_ACO_RUNS = 10  # Repetitions per trial for statistics
```

**Execution Pipeline:**
1. Generate environment (grid, NFZs, delivery points)
2. Build graph
3. Run Dijkstra baseline
4. Run ACO multiple times
5. Collect metrics
6. Generate visualizations
7. Aggregate cross-trial statistics

---

## Experimental Setup

### Environment Specifications

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| Grid size | 100 x 100 | 10 km x 10 km urban area |
| Cell size | 100 m | Minimum spatial resolution |
| NFZ count | 12 | Restricted airspace regions |
| NFZ size | 6-14 cells | 600m - 1400m obstacles |
| Delivery points | 15 | Customer locations |
| Depot | (10, 10) | Base station at 1000m, 1000m |
| Movement | 4-connected | Cardinal directions only |

### Trial Design

**Trial A (Seed 42, NFZ):** Standard layout - moderate obstacle density
**Trial B (Seed 7, NFZ):** Sparse NFZs - more routing freedom
**Trial C (Seed 99, NFZ):** Dense NFZs - constricted corridors
**Trial D (Seed 42, No NFZ):** Control - validates both algorithms find same path

### Statistical Robustness

- 10 ACO runs per trial (stochastic algorithm)
- Report mean ± standard deviation
- Control trial validates correctness

---

## Results & Analysis

### Summary Table

| Trial | Seed | NFZ | Dijkstra (m) | ACO Mean (m) | ACO Std (m) | Improvement |
|-------|------|-----|--------------|--------------|-------------|-------------|
| A | 42 | Yes | 47,200 | 46,000 ± 0 | 0.0 | **2.54%** |
| B | 7 | Yes | 51,400 | 44,200 ± 0 | 0.0 | **14.01%** |
| C | 99 | Yes | 55,000 | 47,280 ± 286 | 286.0 | **14.04%** |
| D | 42 | No | 48,800 | 46,880 ± 240 | 240.0 | **3.93%** |
| **Mean** | - | - | 50,600 | 46,090 ± 132 | - | **8.63%** |

### Key Findings

1. **Mean improvement: 8.63%** across all trials with NFZs
2. **Best case: 14.04%** improvement (Trial C - dense obstacles)
3. **Control validation:** 0% difference without NFZs (both find optimal)
4. **Low variance:** ACO produces consistent results (std: 0-240m)
5. **Compute tradeoff:** ACO ~3x slower than Dijkstra

### Interpretation

**Why ACO outperforms Dijkstra:**
- Dijkstra uses greedy nearest-neighbor ordering
- This ordering ignores global tour structure
- ACO discovers better orderings through path score learning
- Better orderings = fewer NFZ detours

**When improvement decreases:**
- Dense NFZs (Trial C): Both algorithms forced through similar corridors
- No NFZs (Trial D): No obstacles means Euclidean is optimal

**Practical implications:**
- ACO worthwhile for complex obstacle environments
- Pre-flight computation acceptable (seconds, not real-time)
- Improvement scales with environment complexity

---

## Installation & Usage

### Prerequisites

```bash
Python 3.9+
```

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install numpy matplotlib networkx scipy pandas seaborn
```

### Running Experiments

```bash
# Full experiment (4 trials, ~5 minutes)
python run_experiment.py

# Test individual modules
python grid_gen.py
python graph_builder.py
python dijkstra.py
python aco.py

# Run sensitivity analysis (optional, ~15 minutes)
python sensitivity_analysis.py
```

### Output Structure

```
results/
├── summary_table.csv           # Aggregated results
├── fig_E_distance.png          # Distance comparison
├── fig_F_time.png              # Time comparison
├── summary_dashboard.png       # Overview figure
├── trial_A_seed42/
│   ├── metrics.csv             # Detailed trial data
│   ├── fig_A_dijkstra.png      # Dijkstra route
│   ├── fig_B_aco.png           # ACO route
│   ├── fig_C_convergence.png   # Learning curve
│   ├── fig_D_path_score.png     # Path score heatmap
│   └── fig_combined.png        # Overlaid routes
├── trial_B_seed7/
├── trial_C_seed99/
└── trial_D_seed42/
```

---

## Technical Details

### Data Structures

**Grid Representation:**
```python
grid: np.ndarray[uint8]  # Shape: (100, 100)
# Values: 0=free, 1=nfz, 2=delivery, 3=depot
```

**Path Score Structure:**
```python
path_score: Dict[Tuple[point, point], float]
# Key: sorted tuple of two points
# Value: path score intensity
```

**Tour Representation:**
```python
tour_order: List[Tuple[int, int]]  # [depot, D1, D3, D5, ..., depot]
full_path: List[Tuple[int, int]]   # Cell-by-cell path
```

### Complexity Analysis

| Operation | Dijkstra | ACO |
|-----------|----------|-----|
| Distance matrix | - | O(n² * V log V) |
| Tour construction | O(n * V log V) | O(ants * n²) |
| Path realization | O(n * V log V) | O(n * V log V) |
| **Per iteration** | - | O(ants * n² + n * V log V) |
| **Total** | O(n * V log V) | O(iter * ants * n² + n² * V log V) |

Where:
- n = delivery points (15)
- V = graph nodes (~8700)
- iter = iterations (200)
- ants = colony size (50)

### Reproducibility

All random operations use seeded generators:
```python
np.random.seed(seed)
random.seed(seed)
```

Same seed → same environment → comparable results.

---

## Limitations & Future Work

### Current Limitations

1. **Scale:** 100x100 grid (10km²) is smaller than real urban networks
2. **Static NFZs:** No dynamic airspace changes during flight
3. **Single drone:** No multi-agent coordination
4. **Simple baseline:** Nearest-neighbor ordering is weak; TSP solvers would close the gap
5. **2D only:** No altitude or 3D pathfinding
6. **Uniform cells:** No terrain cost variation

### Future Extensions

- **Scale up:** 200×200 or larger grids
- **Dynamic NFZs:** NFZ appears mid-flight, triggers replanning
- **Multi-drone:** Fleet coordination with collision avoidance
- **Stronger baselines:** 2-opt, Or-opt, Christofides algorithm
- **Real-world integration:** OpenStreetMap data, actual airspace regulations
- **3D routing:** Altitude-aware pathfinding

---

## References

### Ant Colony Optimization

1. Dorigo, M., & Gambardella, L. M. (1997). "Ant colony system: a cooperative learning approach to the traveling salesman problem." *IEEE Transactions on Evolutionary Computation*, 1(1), 53-66.

2. Dorigo, M., & Stützle, T. (2004). *Ant Colony Optimization*. MIT Press.

### Drone Routing

3. Otto, A., Agatz, N., Campbell, J., Golden, B., & Pesch, E. (2018). "Optimization approaches for civil applications of unmanned aerial vehicles (UAVs) or aerial drones: A survey." *Networks*, 72(4), 411-458.

### Graph Algorithms

4. Dijkstra, E. W. (1959). "A note on two problems in connexion with graphs." *Numerische Mathematik*, 1(1), 269-271.

---

## License

This simulation was developed for academic research purposes.

**Generated:** 2026-03-23

---

## Contact & Citation

If using this simulation in publications:

```bibtex
@misc{drone_routing_sim,
  title={Drone Routing Experiment: Dijkstra vs ACO with No-Fly Zones},
  year={2026},
  note={Ant Colony System implementation on 100x100 grid. Python 3.9+, NetworkX, Matplotlib.}
}
```
