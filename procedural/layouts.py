import math
import random
from procedural.core.vec import Vec2, length, normalize, dist


def random_scatter(width, height, count, rng):
    """
    Randomly scatter points within the bounds.
    """
    positions = []
    margin = min(width, height) * 0.05
    for _ in range(count):
        x = rng.uniform(margin, width - margin)
        y = rng.uniform(margin, height - margin)
        positions.append((x, y))
    return positions


def grid_with_jitter(width, height, count, rng, jitter=20):
    """
    Place points in a grid with random jitter.
    """
    if count <= 0:
        return []

    cols = math.ceil(math.sqrt(count))
    rows = math.ceil(count / cols)

    cell_w = width / cols
    cell_h = height / rows

    positions = []
    for i in range(count):
        r = i // cols
        c = i % cols

        cx = c * cell_w + cell_w / 2
        cy = r * cell_h + cell_h / 2

        jx = rng.uniform(-jitter, jitter)
        jy = rng.uniform(-jitter, jitter)

        positions.append((cx + jx, cy + jy))

    return positions


def spiral_layout(width, height, count, rng, spacing=None):
    """
    Place points in a spiral pattern (Fermat's spiral).
    """
    positions = []
    cx, cy = width / 2, height / 2

    if spacing is None:
        # Auto-calculate spacing based on area
        area = width * height
        spacing = math.sqrt(area / (count * 3))  # Heuristic

    golden_angle = math.pi * (3 - math.sqrt(5))

    for i in range(count):
        theta = i * golden_angle
        r = spacing * math.sqrt(i)

        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)

        positions.append((x, y))

    return positions


def force_directed_layout(width, height, count, rng, iterations=50):
    """
    Simple force-directed layout to distribute points evenly.
    """
    # Initialize random positions
    nodes = [Vec2(rng.uniform(0, width), rng.uniform(0, height)) for _ in range(count)]

    area = width * height
    k = math.sqrt(area / count)

    center = Vec2(width / 2, height / 2)

    for _ in range(iterations):
        # Repulsive forces
        displacements = [Vec2(0, 0) for _ in range(count)]

        for i in range(count):
            for j in range(count):
                if i == j:
                    continue

                delta = nodes[i] - nodes[j]
                d = length(delta)
                if d < 0.01:
                    d = 0.01
                    delta = Vec2(rng.uniform(-1, 1), rng.uniform(-1, 1))

                # f_rep = k^2 / d
                force = (k * k) / d
                displacements[i] = displacements[i] + normalize(delta) * force

        # Attractive forces (gravity to center)
        for i in range(count):
            delta = nodes[i] - center
            d = length(delta)
            if d > 0:
                # f_att = d^2 / k
                force = (d * d) / k
                displacements[i] = (
                    displacements[i] - normalize(delta) * force * 0.1
                )  # Weak gravity

        # Apply displacement
        for i in range(count):
            disp = displacements[i]
            d = length(disp)
            # Limit max displacement (temperature)
            max_disp = k  # Simple temperature
            if d > max_disp:
                disp = normalize(disp) * max_disp

            nodes[i] = nodes[i] + disp

            # Bounds check
            nodes[i].x = min(width - 20, max(20, nodes[i].x))
            nodes[i].y = min(height - 20, max(20, nodes[i].y))

    return [(n.x, n.y) for n in nodes]


# Extracted from universal_viz_system.py
# Note: positions in presets include size (x, y, size), but dynamic algos return (x, y).
# The consumer handles size assignment.
LAYOUT_PRESETS = [
    # Layout 1: Classic Grid-like
    {
        "positions": [
            (100, 100, 120),
            (300, 120, 100),
            (500, 100, 120),
            (700, 120, 100),
            (120, 300, 110),
            (320, 320, 130),
            (520, 300, 110),
            (720, 320, 130),
            (200, 500, 140),
            (600, 500, 140),
        ],
        "central": (540, 540),  # Center-ish
        "title_y": 40,
        "info_y": 900,
        "timestamp_y": 960,
        "decorations": [
            (40, 40, "+"),
            (1040, 40, "+"),
            (40, 1040, "+"),
            (1040, 1040, "+"),
        ],
    },
    # Layout 2: Circular
    {
        "positions": [
            (540, 150, 130),
            (800, 250, 110),
            (930, 540, 120),
            (800, 830, 110),
            (540, 930, 130),
            (280, 830, 110),
            (150, 540, 120),
            (280, 250, 110),
        ],
        "central": (540, 540),
        "title_y": 40,
        "info_y": 1000,
        "timestamp_y": 1040,
        "decorations": [
            (40, 40, "."),
            (1040, 40, "."),
            (40, 1040, "."),
            (1040, 1040, "."),
        ],
    },
    # Layout 3: Asymmetric Scatter
    {
        "positions": [
            (100, 150, 140),
            (250, 300, 100),
            (150, 500, 120),
            (300, 700, 110),
            (800, 150, 130),
            (900, 350, 100),
            (850, 600, 120),
            (950, 800, 110),
            (540, 850, 150),
        ],
        "central": (540, 450),
        "title_y": 40,
        "info_y": 980,
        "timestamp_y": 1020,
        "decorations": [
            (20, 540, "-"),
            (1060, 540, "-"),
            (540, 20, "|"),
            (540, 1060, "|"),
        ],
    },
    # Layout 4: Diagonal Flow
    {
        "positions": [
            (80, 120, 110),
            (240, 260, 120),
            (400, 420, 130),
            (560, 580, 120),
            (720, 740, 110),
            (820, 820, 130),  # width-260, height-260 approx
        ],
        "central": (400, 380),  # width//2 - 140, height//2 - 160
        "title_y": 40,
        "info_y": 940,
        "timestamp_y": 1010,
        "decorations": [
            (40, 100, "/"),
            (1000, 920, "\\"),
            (60, 960, "//"),
            (940, 80, "\\\\"),
        ],
    },
    # Layout 5: Top Banner
    {
        "positions": [
            (100, 220, 120),
            (320, 240, 110),
            (540, 260, 120),
            (760, 280, 110),
            (120, 840, 140),
            (780, 840, 140),
        ],
        "central": (430, 620),  # width//2 - 110, height//2 + 80
        "title_y": 20,
        "info_y": 960,
        "timestamp_y": 1020,
        "decorations": [
            (40, 40, "===="),
            (940, 40, "===="),
            (40, 140, "----"),
            (940, 140, "----"),
        ],
    },
    # Layout 6: Side Columns (New)
    {
        "positions": [
            (100, 200, 110),
            (100, 400, 110),
            (100, 600, 110),
            (100, 800, 110),
            (980, 200, 110),
            (980, 400, 110),
            (980, 600, 110),
            (980, 800, 110),
        ],
        "central": (540, 540),
        "title_y": 50,
        "info_y": 950,
        "timestamp_y": 1000,
        "decorations": [
            (200, 100, "|"),
            (880, 100, "|"),
            (200, 980, "|"),
            (880, 980, "|"),
        ],
    },
    # Layout 7: Cross (New)
    {
        "positions": [
            (540, 150, 120),
            (540, 300, 110),
            (540, 780, 110),
            (540, 930, 120),
            (150, 540, 120),
            (300, 540, 110),
            (780, 540, 110),
            (930, 540, 120),
        ],
        "central": (540, 540),
        "title_y": 40,
        "info_y": 1000,
        "timestamp_y": 1040,
        "decorations": [
            (40, 40, "x"),
            (1040, 40, "x"),
            (40, 1040, "x"),
            (1040, 1040, "x"),
        ],
    },
    # Layout 8: Random Cloud (New - Static version)
    {
        "positions": [
            (300, 300, 100),
            (400, 250, 110),
            (600, 280, 100),
            (700, 350, 110),
            (350, 600, 100),
            (450, 700, 110),
            (650, 650, 100),
            (750, 600, 110),
        ],
        "central": (540, 540),
        "title_y": 40,
        "info_y": 980,
        "timestamp_y": 1020,
        "decorations": [
            (540, 100, "^"),
            (540, 980, "v"),
        ],
    },
]


def get_preset_layout(name, width=1080, height=1080):
    """
    Get a preset layout by name or index.
    Currently returns a random one if name is not found or 'random'.
    """
    # In a real implementation, we might map names to indices
    # For now, we just return a random one as per original behavior
    # but we could extend this to support named retrieval

    # Note: The original code just did rng.choice(layouts)
    # We will return the list so the caller can choose, or implement logic here.
    # But to match the signature requested:

    # If name is an integer index
    if isinstance(name, int) and 0 <= name < len(LAYOUT_PRESETS):
        return LAYOUT_PRESETS[name]

    # Default fallback
    return LAYOUT_PRESETS[0]
