"""
Common Visual Effects Library
公共视觉效果函数库

提供可视化系统中重复使用的效果函数：
- 发光文字效果
- 故障艺术效果
- 数据粒子背景
- 能量波纹

这些函数从 emotional_market_viz.py 和 market_viz_complete.py 中提取，
用于避免代码重复和统一效果实现。
"""

import random
import math
from PIL import ImageDraw


def draw_glow_text(draw, x, y, text, color, glow_color, size=1):
    """
    绘制发光文字效果
    Draw text with glow effect

    Args:
        draw: PIL ImageDraw object
        x: X coordinate
        y: Y coordinate
        text: Text string to draw
        color: Main text color (hex or RGB tuple)
        glow_color: Glow/outline color (hex or RGB tuple)
        size: Glow intensity (default 1)

    Returns:
        None (modifies draw object in-place)

    Example:
        draw_glow_text(draw, 100, 100, "BULL", "#00ff00", "#88ff88", size=2)
    """
    # 外发光（多层）- Outer glow (multiple layers)
    for offset in range(size + 3, 0, -1):
        alpha = int(100 - offset * 20)
        if alpha > 0:
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, fill=glow_color)

    # 主体文字（加粗）- Main text (bold via multiple draws)
    for dx in range(size):
        for dy in range(size):
            draw.text((x + dx, y + dy), text, fill=color)


def apply_glitch(img, intensity=150):
    """
    应用故障艺术效果
    Apply glitch art effect to image

    Args:
        img: PIL Image object
        intensity: Number of glitch iterations (default 150)

    Returns:
        Modified PIL Image object

    Example:
        img = apply_glitch(img, intensity=200)
    """
    WIDTH, HEIGHT = img.size
    pixels = img.load()

    for _ in range(intensity):
        x = random.randint(0, WIDTH - 80)
        y = random.randint(0, HEIGHT - 1)
        w = random.randint(20, 100)
        shift = random.randint(-12, 12)

        for i in range(w):
            if x + i < WIDTH and 0 <= (y + shift) < HEIGHT:
                try:
                    pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
                except:
                    pass

    return img


def create_data_particles(draw, width, height, color, density=50):
    """
    创建数据粒子背景（动态感）
    Create data particle background for dynamic effect

    Args:
        draw: PIL ImageDraw object
        width: Canvas width
        height: Canvas height
        color: Particle color (hex or RGB tuple)
        density: Number of particles (default 50)

    Returns:
        None (modifies draw object in-place)

    Example:
        create_data_particles(draw, 1080, 1080, "#00ff00", density=100)
    """
    chars = "0123456789.,:;-+*"
    for _ in range(density):
        x = random.randint(0, width)
        y = random.randint(0, height)
        char = random.choice(chars)
        size = random.randint(1, 3)

        for dx in range(size):
            for dy in range(size):
                draw.text((x + dx, y + dy), char, fill=color)


def create_energy_waves(draw, width, height, color, wave_count=5):
    """
    创建能量波纹（视觉动态）
    Create energy wave rings for visual dynamics

    Args:
        draw: PIL ImageDraw object
        width: Canvas width
        height: Canvas height
        color: Wave line color (hex or RGB tuple)
        wave_count: Number of concentric waves (default 5)

    Returns:
        None (modifies draw object in-place)

    Example:
        create_energy_waves(draw, 1080, 1080, "#00ff88", wave_count=5)
    """
    center_x, center_y = width // 2, height // 2

    for wave_idx in range(wave_count):
        radius = 100 + wave_idx * 80
        segments = 60

        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            x1 = center_x + int(math.cos(angle) * radius)
            y1 = center_y + int(math.sin(angle) * radius)

            angle2 = ((i + 1) / segments) * 2 * math.pi
            x2 = center_x + int(math.cos(angle2) * radius)
            y2 = center_y + int(math.sin(angle2) * radius)

            # 随机断续效果 - Random discontinuous effect
            if random.random() > 0.3:
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)
