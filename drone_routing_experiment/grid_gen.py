"""
Grid Generation Module
Generates 100x100 grid with No-Fly Zones (NFZs) and delivery points.
"""

import numpy as np
from collections import deque
from typing import List, Dict, Tuple

# Environment parameters
GRID_ROWS = 100
GRID_COLS = 100
CELL_SIZE_M = 100  # metres per cell

# NFZ parameters
NFZ_COUNT = 12
NFZ_MIN_W = 6   # cells
NFZ_MAX_W = 14  # cells
NFZ_MIN_H = 6   # cells
NFZ_MAX_H = 14  # cells
BORDER_EXCLUSION = 5  # cells - NFZs cannot touch border

# Delivery parameters
DEPOT_POS = (10, 10)  # Fixed depot position
NUM_DELIVERIES = 15
MIN_POINT_SEP = 5  # Minimum separation between delivery points (cells)

# Grid cell types
CELL_FREE = 0
CELL_NFZ = 1
CELL_DELIVERY = 2
CELL_DEPOT = 3


def generate_grid(seed: int, has_nfz: bool = True) -> Tuple[np.ndarray, List[Tuple[int, int]], List[Dict]]:
    """
    Generate grid with NFZs and delivery points.

    Args:
        seed: Random seed for reproducibility
        has_nfz: Whether to place NFZ blocks

    Returns:
        grid: N×N numpy array (default 100×100)
        delivery_points: List of (row, col) tuples for delivery locations
        nfz_blocks: List of dicts with NFZ metadata
    """
    np.random.seed(seed)

    # Initialize empty grid
    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=np.uint8)

    # Mark depot
    grid[DEPOT_POS] = CELL_DEPOT

    # Place NFZ blocks if required
    nfz_blocks = []
    if has_nfz:
        nfz_blocks = place_nfz_blocks(grid, max_retries=1000)

    # Place delivery points
    delivery_points = place_delivery_points(grid, nfz_blocks)

    # Mark delivery points on grid
    for point in delivery_points:
        grid[point] = CELL_DELIVERY

    return grid, delivery_points, nfz_blocks


def place_nfz_blocks(grid: np.ndarray, max_retries: int = 1000) -> List[Dict]:
    """
    Place NFZ blocks with overlap and connectivity validation.

    Uses rejection sampling: retry if overlap or disconnection occurs.
    """
    nfz_blocks = []
    attempts = 0

    for block_id in range(NFZ_COUNT):
        placed = False
        block_attempts = 0

        while not placed and block_attempts < max_retries:
            attempts += 1
            block_attempts += 1

            # Random block dimensions
            width = np.random.randint(NFZ_MIN_W, NFZ_MAX_W + 1)
            height = np.random.randint(NFZ_MIN_H, NFZ_MAX_H + 1)

            # Random position (keep away from borders)
            max_row = GRID_ROWS - height - BORDER_EXCLUSION
            max_col = GRID_COLS - width - BORDER_EXCLUSION

            if max_row <= BORDER_EXCLUSION or max_col <= BORDER_EXCLUSION:
                continue

            row = np.random.randint(BORDER_EXCLUSION, max_row)
            col = np.random.randint(BORDER_EXCLUSION, max_col)

            # Check overlap with existing blocks
            if has_overlap(row, col, width, height, nfz_blocks):
                continue

            # Check depot not inside block
            if (DEPOT_POS[0] >= row and DEPOT_POS[0] < row + height and
                DEPOT_POS[1] >= col and DEPOT_POS[1] < col + width):
                continue

            # Tentatively place block
            temp_grid = grid.copy()
            temp_grid[row:row+height, col:col+width] = CELL_NFZ

            # Check connectivity
            if not is_connected(temp_grid, DEPOT_POS):
                continue

            # Block is valid - commit it
            grid[row:row+height, col:col+width] = CELL_NFZ
            nfz_blocks.append({
                'row': row,
                'col': col,
                'width': width,
                'height': height
            })
            placed = True

        if not placed:
            raise RuntimeError(f"Failed to place NFZ block {block_id} after {max_retries} attempts")

    print(f"Placed {len(nfz_blocks)} NFZ blocks in {attempts} total attempts")
    return nfz_blocks


def has_overlap(row: int, col: int, width: int, height: int, existing_blocks: List[Dict]) -> bool:
    """Check if proposed block overlaps with existing blocks."""
    for block in existing_blocks:
        # Check rectangle intersection
        if not (row + height <= block['row'] or
                row >= block['row'] + block['height'] or
                col + width <= block['col'] or
                col >= block['col'] + block['width']):
            return True
    return False


def is_connected(grid: np.ndarray, start: Tuple[int, int]) -> bool:
    """
    Check if all free cells are reachable from start position using BFS.

    Uses 4-connectivity (no diagonals).
    """
    rows, cols = grid.shape
    visited = np.zeros((rows, cols), dtype=bool)
    queue = deque([start])
    visited[start] = True
    reachable_count = 1

    # Count free cells (including depot and future delivery cells)
    free_cells = np.sum((grid == CELL_FREE) | (grid == CELL_DEPOT) | (grid == CELL_DELIVERY))

    while queue:
        r, c = queue.popleft()

        # Check 4 neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc

            if (0 <= nr < rows and 0 <= nc < cols and
                not visited[nr, nc] and
                grid[nr, nc] != CELL_NFZ):

                visited[nr, nc] = True
                queue.append((nr, nc))
                reachable_count += 1

    # Grid is connected if all free cells are reachable
    return reachable_count >= free_cells


def place_delivery_points(grid: np.ndarray, nfz_blocks: List[Dict]) -> List[Tuple[int, int]]:
    """
    Place delivery points with minimum separation constraint.
    """
    delivery_points = []
    max_attempts = 10000
    attempts = 0

    while len(delivery_points) < NUM_DELIVERIES and attempts < max_attempts:
        attempts += 1

        # Random position
        row = np.random.randint(0, GRID_ROWS)
        col = np.random.randint(0, GRID_COLS)

        # Check if cell is free
        if grid[row, col] != CELL_FREE:
            continue

        # Check minimum separation from depot
        if euclidean_distance((row, col), DEPOT_POS) < MIN_POINT_SEP:
            continue

        # Check minimum separation from existing delivery points
        too_close = False
        for point in delivery_points:
            if euclidean_distance((row, col), point) < MIN_POINT_SEP:
                too_close = True
                break

        if too_close:
            continue

        # Valid delivery point
        delivery_points.append((row, col))

    if len(delivery_points) < NUM_DELIVERIES:
        raise RuntimeError(f"Could only place {len(delivery_points)} delivery points (needed {NUM_DELIVERIES})")

    print(f"Placed {len(delivery_points)} delivery points in {attempts} attempts")
    return delivery_points


def euclidean_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    """Calculate Euclidean distance between two points."""
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def get_grid_info(grid: np.ndarray, delivery_points: List[Tuple[int, int]],
                  nfz_blocks: List[Dict]) -> Dict:
    """Get summary information about the grid."""
    return {
        'grid_size': f"{GRID_ROWS}x{GRID_COLS}",
        'cell_size_m': CELL_SIZE_M,
        'total_area_km2': (GRID_ROWS * CELL_SIZE_M / 1000) * (GRID_COLS * CELL_SIZE_M / 1000),
        'depot': DEPOT_POS,
        'num_deliveries': len(delivery_points),
        'delivery_points': delivery_points,
        'num_nfz': len(nfz_blocks),
        'nfz_blocks': nfz_blocks,
        'free_cells': int(np.sum(grid == CELL_FREE)),
        'nfz_cells': int(np.sum(grid == CELL_NFZ))
    }


if __name__ == '__main__':
    """Test grid generation."""
    import matplotlib.pyplot as plt

    # Test with NFZ
    print("Generating grid with NFZ (seed 42)...")
    grid, delivery_points, nfz_blocks = generate_grid(seed=42, has_nfz=True)
    info = get_grid_info(grid, delivery_points, nfz_blocks)

    print("\nGrid Info:")
    for key, value in info.items():
        if key not in ['delivery_points', 'nfz_blocks']:
            print(f"  {key}: {value}")

    # Visualize
    fig, ax = plt.subplots(figsize=(10, 10))

    # Show grid (white=free, red=NFZ)
    display_grid = np.ones((GRID_ROWS, GRID_COLS, 3))
    display_grid[grid == CELL_NFZ] = [1, 0.8, 0.8]  # Light red for NFZ

    ax.imshow(display_grid, origin='upper')

    # Draw NFZ outlines
    for block in nfz_blocks:
        rect = plt.Rectangle((block['col']-0.5, block['row']-0.5),
                             block['width'], block['height'],
                             fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(rect)

    # Plot depot
    ax.plot(DEPOT_POS[1], DEPOT_POS[0], 'g*', markersize=20, label='Depot')

    # Plot delivery points
    for i, point in enumerate(delivery_points):
        ax.plot(point[1], point[0], 'bo', markersize=10)
        ax.text(point[1]+0.5, point[0]+0.5, f'D{i+1}', fontsize=8)

    ax.set_title(f'Grid Generation Test (Seed 42)\n{len(nfz_blocks)} NFZ blocks, {len(delivery_points)} delivery points')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.savefig('grid_test.png', dpi=150, bbox_inches='tight')
    print("\nVisualization saved to grid_test.png")

    # Test without NFZ
    print("\n\nGenerating grid without NFZ (seed 42)...")
    grid_no_nfz, delivery_points_no_nfz, nfz_blocks_no_nfz = generate_grid(seed=42, has_nfz=False)
    print(f"No-NFZ grid: {len(delivery_points_no_nfz)} delivery points")
