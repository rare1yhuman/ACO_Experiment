# ACO-Optimized Drone Delivery Routing

Ant Colony Optimization for multi-point drone delivery routing in urban environments with No-Fly Zone constraints.

This repository contains the complete simulation code, experiment runner, and visualization pipeline for our research paper on applying Ant Colony System (ACS) to optimize drone delivery tours in NFZ-constrained grid environments.

## Key Results

| Metric | Value |
|--------|-------|
| Grid size | 100 × 100 (10 km × 10 km) |
| Delivery points | 15 |
| No-Fly Zones | 12 |
| Trials | 4 (seeds: 42, 7, 99, 42) |
| **Mean improvement over Dijkstra** | **8.63%** |
| Best improvement (Trial C) | 14.04% |
| ACO parameters | 50 ants, 200 iterations, α=1.0, β=2.0 |

## Architecture

```
.
├── generate_paper.py              # DOCX manuscript generator
├── requirements.txt               # Python dependencies
├── LICENSE                        # MIT License
│
└── drone_routing_experiment/
    ├── grid_gen.py                # Grid environment with NFZs + delivery points
    ├── graph_builder.py           # NetworkX graph from grid (4-connectivity)
    ├── dijkstra.py                # Baseline: nearest-neighbor + Dijkstra
    ├── aco.py                     # Ant Colony System optimizer
    ├── metrics.py                 # Metrics collection and aggregation
    ├── visualise.py               # Publication-quality figure generation
    ├── generate_city_map.py       # Cartographic route visualization
    ├── sensitivity_analysis.py    # ACO parameter sweep (α vs β)
    ├── run_experiment.py          # Main experiment orchestrator
    ├── regen_paper_figures.py     # Regenerate paper figures only
    │
    └── results/
        ├── summary_table.csv      # Aggregated trial results
        ├── fig_city_map.png       # Fig. 1: Route comparison map
        ├── fig_E_distance.png     # Fig. 2: Distance bar chart
        └── fig_convergence_paper.png  # Fig. 3: ACO convergence curve
```

## Installation

```bash
# Clone the repository
git clone https://github.com/rare1yhuman/ACO_Experiment.git
cd ACO_Experiment

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Full Experiment
```bash
cd drone_routing_experiment
python run_experiment.py
```
This runs all 4 trials (A–D) with Dijkstra baseline and ACO optimization, generates per-trial figures, and produces the summary table.

### Regenerate Paper Figures Only
```bash
cd drone_routing_experiment
python regen_paper_figures.py
```
Regenerates the 3 publication-quality figures used in the paper (city map, distance chart, convergence curve).

### Generate Paper (DOCX)
```bash
python generate_paper.py
```
Produces `ACO_Drone_Swarm_Paper.docx` with all figures embedded.

### Parameter Sensitivity Analysis
```bash
cd drone_routing_experiment
python sensitivity_analysis.py
```
Runs α × β parameter sweep and generates heatmap visualizations.

## Algorithm Overview

1. **Grid Generation**: 100×100 grid with randomly placed rectangular NFZs and delivery points
2. **Graph Construction**: 4-connected NetworkX graph (NFZ cells removed)
3. **Dijkstra Baseline**: Nearest-neighbor heuristic ordering + Dijkstra shortest paths
4. **ACO Optimization**: Ant Colony System with:
   - Two-level approach: high-level tour ordering + low-level Dijkstra navigation
   - ACS transition rule (exploitation probability Q₀ = 0.9)
   - Global + local pheromone updates
   - 50 ants × 200 iterations per trial

## GitHub Repository

🔗 **Repository:** [https://github.com/rare1yhuman/ACO_Experiment](https://github.com/rare1yhuman/ACO_Experiment)

## Citation

If you use this code or find our work useful in your research, please cite:

```bibtex
@article{aco2026drone,
  title   = {Ant Colony Optimization for Efficient Pathway Planning in Multi-Drone
             Delivery Systems with No-Fly Zone Constraints},

  note    = {Code available at \url{https://github.com/rare1yhuman/ACO_Experiment}}
}
```

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
