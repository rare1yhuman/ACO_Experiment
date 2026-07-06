# ACO-Optimized Drone Delivery Routing

[![Conference](https://img.shields.io/badge/Conference-INFINITYS_2026-blue)](#)
[![Status](https://img.shields.io/badge/Status-Completed-success)](#)

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
