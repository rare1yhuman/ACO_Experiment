"""
Generate City Map Style Visualization for Drone Routes
Creates publication-quality map similar to cartographic city maps.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, PathPatch
from matplotlib.path import Path
import matplotlib.patheffects as path_effects
import numpy as np
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grid_gen import generate_grid, DEPOT_POS, CELL_SIZE_M, GRID_ROWS, GRID_COLS
from graph_builder import build_graph
from dijkstra import build_dijkstra_tour
from aco import run_aco

# Map color palette (cartographic style)
COLORS = {
    'road': '#F5F5F0',           # Light cream for roads
    'road_outline': '#D4D4C8',   # Subtle road border
    'block': '#E8E4DB',          # Building blocks (tan/beige)
    'block_outline': '#C8C4BB',  # Block borders
    'park': '#C8E6C9',           # Green spaces
    'park_outline': '#A5D6A7',   # Park borders
    'nfz': '#FFCDD2',            # No-fly zone (light red)
    'nfz_outline': '#E57373',    # NFZ border
    'water': '#B3E5FC',          # Water features
    'route_dijkstra': '#1565C0', # Blue route
    'route_aco': '#2E7D32',      # Green route
    'depot': '#FF6F00',          # Orange depot
    'delivery': '#0097A7',       # Cyan delivery points
    'text': '#424242',           # Dark gray text
}


def generate_city_map(seed=42, output_dir='results'):
    """Generate city-map style visualization with drone routes."""
    print("Generating city map style visualization...")

    # Generate environment
    grid, delivery_points, nfz_blocks = generate_grid(seed=seed, has_nfz=True)
    G = build_graph(grid)

    # Run algorithms
    print("  Running Dijkstra baseline...")
    dijkstra_result = build_dijkstra_tour(G, DEPOT_POS, delivery_points)

    print("  Running ACO optimization...")
    aco_result = run_aco(G, grid, DEPOT_POS, delivery_points,
                         dijkstra_result['total_distance_m'], verbose=False)

    # Calculate improvement
    improvement = ((dijkstra_result['total_distance_m'] - aco_result['best_tour_distance'])
                   / dijkstra_result['total_distance_m'] * 100)

    # Create single map with both routes
    fig, ax = plt.subplots(figsize=(10, 10))

    _draw_city_base(ax, grid, nfz_blocks)
    _draw_routes(ax, dijkstra_result['full_path'], aco_result['best_tour_path'],
                 dijkstra_result['total_distance_m'], aco_result['best_tour_distance'])
    _draw_waypoints(ax, delivery_points, DEPOT_POS)
    _add_map_elements(ax, dijkstra_result['total_distance_m'],
                      aco_result['best_tour_distance'], improvement)

    plt.tight_layout()

    output_path = os.path.join(output_dir, 'fig_city_map.png')
    plt.savefig(output_path, dpi=600, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved city map to {output_path}")

    # Also create separate maps for each algorithm
    _create_single_route_map(grid, nfz_blocks, delivery_points,
                             dijkstra_result['full_path'],
                             dijkstra_result['total_distance_m'],
                             'Dijkstra Algorithm', COLORS['route_dijkstra'],
                             os.path.join(output_dir, 'fig_city_map_dijkstra.png'))

    _create_single_route_map(grid, nfz_blocks, delivery_points,
                             aco_result['best_tour_path'],
                             aco_result['best_tour_distance'],
                             f'ACO Algorithm ({improvement:.1f}% improvement)',
                             COLORS['route_aco'],
                             os.path.join(output_dir, 'fig_city_map_aco.png'))

    return dijkstra_result, aco_result


def _draw_city_base(ax, grid, nfz_blocks):
    """Draw the city map base layer (clean, no decorative blocks)."""
    rows, cols = grid.shape

    # Clean white background
    ax.set_facecolor(COLORS['road'])

    # Draw No-Fly Zones
    for block in nfz_blocks:
        # Main NFZ area
        rect = FancyBboxPatch(
            (block['col'], block['row']),
            block['width'], block['height'],
            boxstyle="round,pad=0.02,rounding_size=0.3",
            facecolor=COLORS['nfz'],
            edgecolor=COLORS['nfz_outline'],
            linewidth=2,
            zorder=2
        )
        ax.add_patch(rect)

        # Add diagonal stripes pattern for NFZ
        for offset in np.arange(-block['height'], block['width'], 1.5):
            x1 = block['col'] + max(0, offset)
            y1 = block['row'] + max(0, -offset)
            x2 = block['col'] + min(block['width'], offset + block['height'])
            y2 = block['row'] + min(block['height'], -offset + block['width'])

            if x1 < block['col'] + block['width'] and x2 > block['col']:
                ax.plot([x1, x2], [y1, y2], color=COLORS['nfz_outline'],
                       linewidth=0.5, alpha=0.4, zorder=2)

    # Draw main roads (grid lines)
    for i in range(0, rows + 1, 5):
        ax.axhline(y=i, color=COLORS['road_outline'], linewidth=0.8, zorder=0)
    for j in range(0, cols + 1, 5):
        ax.axvline(x=j, color=COLORS['road_outline'], linewidth=0.8, zorder=0)

    ax.set_xlim(-4, cols + 4)
    ax.set_ylim(rows + 4, -4)
    ax.set_aspect('equal')


def _draw_routes(ax, dijkstra_path, aco_path, dij_dist, aco_dist):
    """Draw drone flight routes on the map."""

    # Draw Dijkstra path (solid line with glow effect)
    if dijkstra_path and len(dijkstra_path) > 1:
        path_rows = [p[0] + 0.5 for p in dijkstra_path]
        path_cols = [p[1] + 0.5 for p in dijkstra_path]

        # Glow effect (wider, lighter line underneath)
        ax.plot(path_cols, path_rows, '-', color='white',
                linewidth=8.5, solid_capstyle='round', zorder=4, alpha=0.8)

        # Main line
        line1, = ax.plot(path_cols, path_rows, '-', color=COLORS['route_dijkstra'],
                linewidth=5.5, solid_capstyle='round', zorder=5,
                label=f'Dijkstra Path ({dij_dist/1000:.2f} km)')

    # Draw ACO path (dashed line with glow effect)
    if aco_path and len(aco_path) > 1:
        path_rows = [p[0] + 0.5 for p in aco_path]
        path_cols = [p[1] + 0.5 for p in aco_path]

        # Glow effect
        ax.plot(path_cols, path_rows, '--', color='white',
                linewidth=8.5, solid_capstyle='round', zorder=4, alpha=0.8)

        # Main line
        line2, = ax.plot(path_cols, path_rows, '--', color=COLORS['route_aco'],
                linewidth=5.5, solid_capstyle='round', zorder=5,
                label=f'ACO Path ({aco_dist/1000:.2f} km)')


def _draw_waypoints(ax, delivery_points, depot):
    """Draw delivery points and depot."""

    # Draw delivery points
    for i, point in enumerate(delivery_points):
        # Outer circle (white border)
        circle_bg = Circle((point[1] + 0.5, point[0] + 0.5), 3.0,
                          facecolor='white', edgecolor='white',
                          linewidth=0, zorder=7)
        ax.add_patch(circle_bg)

        # Main circle
        circle = Circle((point[1] + 0.5, point[0] + 0.5), 2.5,
                        facecolor=COLORS['delivery'], edgecolor='white',
                        linewidth=2, zorder=8)
        ax.add_patch(circle)

        # Number label
        txt = ax.text(point[1] + 0.5, point[0] + 0.5, f'{i+1}',
                     ha='center', va='center', fontsize=18, fontweight='bold',
                     color='white', zorder=9)
        txt.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground='black')])

    # Draw depot (star shape)
    depot_x, depot_y = depot[1] + 0.5, depot[0] + 0.5

    # White background circle
    circle_bg = Circle((depot_x, depot_y), 2.6,
                       facecolor='white', edgecolor='white',
                       linewidth=0, zorder=7)
    ax.add_patch(circle_bg)

    # Star marker
    ax.plot(depot_x, depot_y, '*', markersize=34,
            color=COLORS['depot'], markeredgecolor='white',
            markeredgewidth=2, zorder=9)

    # Depot label
    txt = ax.text(depot_x + 3, depot_y, 'DEPOT',
                 fontsize=14, fontweight='bold', color=COLORS['depot'],
                 va='center', zorder=9)
    txt.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')])


def _add_map_elements(ax, dij_dist, aco_dist, improvement):
    """Add legend, scale bar (no badge, no title)."""

    # Legend — moved to lower right to avoid overlapping delivery points
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color=COLORS['route_dijkstra'], linewidth=3,
               label=f'Dijkstra Path ({dij_dist/1000:.2f} km)'),
        Line2D([0], [0], color=COLORS['route_aco'], linewidth=3, linestyle='--',
               label=f'ACO Path ({aco_dist/1000:.2f} km)'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor=COLORS['depot'],
               markersize=15, markeredgecolor='white', label='Depot'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS['delivery'],
               markersize=12, markeredgecolor='white', label='Delivery Point'),
        patches.Patch(facecolor=COLORS['nfz'], edgecolor=COLORS['nfz_outline'],
                     linewidth=2, label='No-Fly Zone'),
    ]

    legend = ax.legend(handles=legend_elements, loc='lower right',
                      fontsize=13, framealpha=0.95, edgecolor='gray',
                      fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('white')

    # Scale bar (bottom left)
    scale_x, scale_y = 2, GRID_ROWS - 3
    scale_length = 10  # 10 cells = 1 km
    # Scale bar background
    scale_bg = FancyBboxPatch((scale_x - 1, scale_y - 2.5), scale_length + 4, 4,
                              boxstyle="round,pad=0.02,rounding_size=0.3",
                              facecolor='white', edgecolor='gray',
                              linewidth=1, alpha=0.9, zorder=10)
    ax.add_patch(scale_bg)

    # Scale bar
    ax.plot([scale_x, scale_x + scale_length], [scale_y, scale_y],
            color='black', linewidth=3.5, zorder=11)
    ax.plot([scale_x, scale_x], [scale_y - 0.3, scale_y + 0.3],
            color='black', linewidth=2.5, zorder=11)
    ax.plot([scale_x + scale_length, scale_x + scale_length], [scale_y - 0.3, scale_y + 0.3],
            color='black', linewidth=2.5, zorder=11)
    ax.text(scale_x + scale_length/2, scale_y - 1.5, '1 km',
            ha='center', va='center', fontsize=13, fontweight='bold', zorder=11)

    # Axis labels (larger for print)
    ax.set_xlabel('Distance (×100 m)', fontsize=17, color=COLORS['text'])
    ax.set_ylabel('Distance (×100 m)', fontsize=17, color=COLORS['text'])

    # Grid ticks
    ax.set_xticks(range(0, GRID_COLS + 1, 10))
    ax.set_yticks(range(0, GRID_ROWS + 1, 10))
    ax.tick_params(colors=COLORS['text'], direction='in', labelsize=15)


def _create_single_route_map(grid, nfz_blocks, delivery_points, path, distance,
                             title, color, output_path):
    """Create a map showing only one route."""
    fig, ax = plt.subplots(figsize=(10, 10))

    _draw_city_base(ax, grid, nfz_blocks)

    # Draw single route
    if path and len(path) > 1:
        path_rows = [p[0] + 0.5 for p in path]
        path_cols = [p[1] + 0.5 for p in path]

        # Glow effect
        ax.plot(path_cols, path_rows, '-', color='white',
                linewidth=8, solid_capstyle='round', zorder=4, alpha=0.8)

        # Main line
        ax.plot(path_cols, path_rows, '-', color=color,
                linewidth=4, solid_capstyle='round', zorder=5)

        # Add direction arrows
        arrow_interval = max(1, len(path) // 15)
        for i in range(0, len(path) - 1, arrow_interval):
            if i + 1 < len(path):
                dx = path_cols[i+1] - path_cols[i]
                dy = path_rows[i+1] - path_rows[i]
                length = np.sqrt(dx**2 + dy**2)
                if length > 0.5:
                    ax.annotate('',
                               xy=(path_cols[i] + dx*0.7, path_rows[i] + dy*0.7),
                               xytext=(path_cols[i] + dx*0.3, path_rows[i] + dy*0.3),
                               arrowprops=dict(arrowstyle='->', color=color, lw=2),
                               zorder=6)

    _draw_waypoints(ax, delivery_points, DEPOT_POS)

    # Title removed — rendered as document text in the paper

    # Scale bar
    scale_x, scale_y = 2, GRID_ROWS - 3
    ax.plot([scale_x, scale_x + 10], [scale_y, scale_y], color='black', linewidth=3)
    ax.text(scale_x + 5, scale_y + 1, '1 km', ha='center', fontsize=9, fontweight='bold')

    ax.set_xlabel('Distance (×100 m)', fontsize=11)
    ax.set_ylabel('Distance (×100 m)', fontsize=11)
    ax.set_xticks(range(0, GRID_COLS + 1, 10))
    ax.set_yticks(range(0, GRID_ROWS + 1, 10))

    plt.tight_layout()
    plt.savefig(output_path, dpi=600, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  Saved to {output_path}")


if __name__ == '__main__':
    generate_city_map(seed=99, output_dir='results')
