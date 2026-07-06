# ACO-Optimized Drone Delivery Routing

[![Conference](https://img.shields.io/badge/Conference-INFINITYS_2026-blue)](#)
[![Status](https://img.shields.io/badge/Status-Completed-success)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the complete simulation code, experiment runner, and visualization pipeline for the research paper **"Pathway Planning Using Ant Colony Optimization"**, presented at the International Conference on Instrumentation, Networks, Future Sustainability, Information Theory, Transportation, and Systems (INFINITYS 2026).

## 👨‍💻 Primary Developer & Contributor

**Rishi Mandal** (@rare1yhuman)
* **Role:** Lead Developer, Algorithm Architect, & Primary Researcher
* **Contributions:**
  * Independently designed and implemented the Ant Colony System (ACS) optimizer in Python.
  * Engineered the grid environment, No-Fly Zone (NFZ) constraints, and evaluation metrics.
  * Conducted all computational experiments, data processing, parameter sensitivity analysis (α vs β), and figure generation.
  * Authored the core technical manuscript, methodology, and structural framework for the publication.

## 📄 Publication Details
* **Paper Title:** Pathway Planning Using Ant Colony Optimization
* **Authors:** Shilpi Khanna, Rishi Mandal, Santripti Bajpai
* **Conference:** INFINITYS 2026 (Solo, Indonesia - Hybrid)
* **Presentation Date:** July 9, 2026

---

## 📊 Key Results

| Metric | Value |
|--------|-------|
| Grid size | 100 × 100 (10 km × 10 km) |
| Delivery points | 15 |
| No-Fly Zones | 12 |
| Trials | 4 (seeds: 42, 7, 99, 42) |
| **Mean improvement over Dijkstra** | **8.63%** |
| Best improvement (Trial C) | 14.04% |
| ACO parameters | 50 ants, 200 iterations, α=1.0, β=2.0 |

## 🏗️ Architecture

```text
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

## 🚀 Installation

Ensure you have Python 3.8+ installed. It is highly recommended to run this inside a virtual environment to prevent dependency conflicts.

```bash
# 1. Clone the repository
git clone https://github.com/rare1yhuman/ACO_Experiment.git
cd ACO_Experiment

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install required dependencies
pip install -r requirements.txt
```

## 💻 Running the Experiments

This repository is designed to be highly reproducible. You can rerun the exact simulations used in our paper with a few simple commands.

### 1. Run the Main Simulation Pipeline

This script executes the core experiment. It runs 4 distinct trials (Trials A–D) using specific random seeds to generate different grid environments, NFZ placements, and delivery points.

```bash
cd drone_routing_experiment
python run_experiment.py
```

### 2. Parameter Sensitivity Analysis (Heatmaps)

To understand how the ACO's heuristic parameters affect route optimization, run the sensitivity analysis.

```bash
cd drone_routing_experiment
python sensitivity_analysis.py
```

### 3. Regenerate Visualizations Only

If you have already run the experiments and just want to tweak or regenerate the Matplotlib figures for a presentation or paper without re-running the heavy computational simulations:

```bash
cd drone_routing_experiment
python regen_paper_figures.py
```

### 4. Compile the Research Paper (DOCX)

Once all experiments have run and figures are generated in the `results/` folder, you can auto-generate a formatted draft of the paper:

```bash
python generate_paper.py
```

## 📂 Interpreting the Results

After running `run_experiment.py`, check the `results/` folder:

* **`summary_table.csv`**: A direct numerical comparison showing the total distance traveled by the baseline (Dijkstra) vs. the ACO algorithm across all trials.
* **`fig_city_map.png`**: A 2D cartographic plot showing the 100×100 grid. Red blocks represent No-Fly Zones. Blue paths show the Dijkstra baseline, and green paths show the optimized ACO route.
* **`fig_convergence_paper.png`**: A line graph demonstrating how quickly the Ant Colony "learned" (X-axis: iterations, Y-axis: shortest route found).

## 🧠 Algorithm Overview

1. **Grid Generation**: A 100×100 grid map is constructed to simulate urban airspace. Rectangular No-Fly Zones (NFZs) and 15 target delivery nodes are randomly placed.
2. **Graph Construction**: The grid is converted into a 4-connected NetworkX graph. Nodes falling within NFZ boundaries are systematically removed to represent strict flight constraints.
3. **Baseline (Dijkstra + Nearest-Neighbor)**: A greedy approach that simply travels to the closest unvisited node using Dijkstra's shortest path.
4. **ACO Optimization**: An Ant Colony System (ACS) utilizing:
   * **Two-level approach**: High-level tour node ordering combined with low-level Dijkstra navigation between nodes.
   * **ACS transition rule**: Features an exploitation probability (Q₀ = 0.9) to favor known good paths while allowing exploration.
   * **Pheromone Updates**: Implements both global updates (rewarding the best ant) and local updates (evaporating pheromones to prevent premature convergence).

## 🔗 Citation

If you use this codebase, methodology, or find our work useful in your research, please cite the official conference proceedings:

```bibtex
@inproceedings{mandal2026aco,
  author    = {Khanna, Shilpi and Mandal, Rishi and Bajpai, Santripti},
  title     = {Pathway Planning Using Ant Colony Optimization},
  booktitle = {Proceedings of the International Conference on Instrumentation, Networks, Future Sustainability, Information Theory, Transportation, and Systems (INFINITYS)},
  year      = {2026},
  month     = {July},
  address   = {Solo, Indonesia},
  note      = {Source code available at \url{https://github.com/rare1yhuman/ACO_Experiment}}
}
```

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.
