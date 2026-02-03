"""
发光文字渲染 - Glow Text Rendering

统一的发光文字效果，支持多层外发光和可调缩放。
Unified glow text effect with multi-layer outer glow and adjustable scaling.
"""

from PIL import ImageDraw


def draw_glow_text(draw, x, y, text, color, glow_color=None, scale=1, glow_radius=None):
    """
    绘制发光文字效果 - Draw glowing text

    Args:
        draw: PIL ImageDraw object
        x: X position
        y: Y position
        text: text string
        color: main text color (hex string or RGB tuple)
        glow_color: outer glow color (defaults to color if None)
        scale: text boldness scale (1=normal, 12=large)
        glow_radius: glow spread radius (defaults to scale+3 if None)
    """
    if glow_color is None:
        glow_color = color
    if glow_radius is None:
        glow_radius = scale + 3

    # Outer glow (multi-layer)
    for offset in range(glow_radius, 0, -1):
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    for sx in range(min(scale, 3)):
                        for sy in range(min(scale, 3)):
                            draw.text((x + dx + sx, y + dy + sy), text, fill=glow_color)

    # Main text (bold via repeated draw)
    for dx in range(scale):
        for dy in range(scale):
            draw.text((x + dx, y + dy), text, fill=color)
