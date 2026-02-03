"""
ASCII 纹理与粒子 - ASCII Texture and Particles

共享的 ASCII 纹理绘制和颜文字散布功能。
Shared ASCII texture drawing and kaomoji scattering functions.
"""

from PIL import ImageDraw

try:
    from lib.kaomoji import draw_kaomoji
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji  # pyright: ignore[reportMissingImports]

ASCII_GRADIENT = " .:-=+*#%@"
ASCII_GRADIENT_FINE = " .':;!>+*%@#█"


def draw_ascii_texture(
    draw, rng, width, height, color, density=0.35, gradient=None, cell_sizes=None
):
    """
    绘制 ASCII 纹理层 - Draw ASCII texture layer

    Args:
        draw: PIL ImageDraw
        rng: random.Random instance
        width: canvas width
        height: canvas height
        color: text fill color
        density: character density (0.0-1.0)
        gradient: character gradient string (default ASCII_GRADIENT)
        cell_sizes: list of cell size options (default [18, 22, 26, 30])
    """
    if gradient is None:
        gradient = ASCII_GRADIENT
    if cell_sizes is None:
        cell_sizes = [18, 22, 26, 30]

    cell = rng.choice(cell_sizes)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if rng.random() < density:
                char = gradient[int(rng.random() * (len(gradient) - 1))]
                draw.text((x, y), char, fill=color)


def scatter_kaomoji(
    draw,
    rng,
    width,
    height,
    mood,
    color,
    outline_color=None,
    count=None,
    exclude_rect=None,
    avoid_center=False,
):
    """
    散布小型颜文字 - Scatter small kaomoji

    Args:
        draw: PIL ImageDraw
        rng: random.Random instance
        width: canvas width
        height: canvas height
        mood: kaomoji mood string or list of moods
        color: kaomoji fill color
        outline_color: kaomoji outline color
        count: number to scatter (default random 6-14)
        exclude_rect: (x, y, w, h) rectangle to avoid (optional)
        avoid_center: if True, avoid center 440x440 area
    """
    if outline_color is None:
        outline_color = color
    if count is None:
        count = rng.randint(6, 14)

    for _ in range(count):
        x = rng.randint(40, width - 200)
        y = rng.randint(40, height - 200)

        # Exclude rectangle check
        if exclude_rect:
            bx, by, bw, bh = exclude_rect
            if bx - 60 <= x <= bx + bw + 60 and by - 60 <= y <= by + bh + 60:
                continue

        # Avoid center check
        if avoid_center:
            if abs(x - width // 2) < 220 and abs(y - height // 2) < 220:
                continue

        # Resolve mood
        if isinstance(mood, (list, tuple)):
            m = rng.choice(mood)
        else:
            m = mood

        size = rng.randint(2, 5)
        draw_kaomoji(
            draw,
            x,
            y,
            m,
            color=color,
            outline_color=outline_color,
            size=size,
            rng=rng,
        )


def draw_data_particles(
    draw, rng, width, height, color, chars="0123456789", count=None, bold=False
):
    """
    绘制数据粒子背景 - Draw data particle background

    Args:
        draw: PIL ImageDraw
        rng: random.Random instance
        width: canvas width
        height: canvas height
        color: particle color
        chars: character string to sample from
        count: particle count (default random 60-140)
        bold: if True, draw characters at multi-pixel scale
    """
    if count is None:
        count = rng.randint(60, 140)

    for _ in range(count):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        char = rng.choice(chars)

        if bold:
            size = rng.randint(1, 3)
            for dx in range(size):
                for dy in range(size):
                    draw.text((x + dx, y + dy), char, fill=color)
        else:
            draw.text((x, y), char, fill=color)
