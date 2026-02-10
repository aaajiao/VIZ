"""
10 PRINT 迷宫图案 - 10 PRINT Maze Pattern

经典 Commodore 64 的 10 PRINT CHR$(205.5+RND(1)); : GOTO 10 迷宫效果。
将屏幕分割为网格单元，每个单元随机选择 / 或 \ 对角线，
通过时间偏移实现动画效果。

Classic Commodore 64 maze pattern. Divides screen into grid cells,
each randomly assigned a / or \ diagonal. Animated via column shifting.

参考/Reference:
    - 10print.org
    - Commodore 64 BASIC one-liner

用法/Usage::

    from procedural.effects import get_effect

    ten_print = get_effect('ten_print')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'cell_size': 6, 'probability': 0.5, 'speed': 1.0}
    )

    state = ten_print.pre(ctx, buffer)
    cell = ten_print.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, fract
from procedural.core.noise import ValueNoise
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["TenPrintEffect"]


class TenPrintEffect(BaseEffect):
    """
    10 PRINT 迷宫效果

    经典 Commodore 64 单行程序产生的随机迷宫图案。

    参数 (从 ctx.params 读取):
        cell_size: 网格单元大小 (默认 6, 范围 4-12)
        probability: 选择 \\ 的概率 (默认 0.5, 范围 0.3-0.7)
        speed: 动画速度 (默认 1.0)

    示例::

        ctx.params = {
            'cell_size': 8,
            'probability': 0.6,
            'speed': 1.5,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """预处理 - 提取参数并创建噪声实例"""
        cell_size = ctx.params.get("cell_size", 6)
        probability = ctx.params.get("probability", 0.5)
        speed = ctx.params.get("speed", 1.0)

        # Noise for smooth probability variation across the grid
        noise = ValueNoise(seed=ctx.seed)

        # Grid dimensions
        grid_w = max(1, ctx.width // cell_size + 2)
        grid_h = max(1, ctx.height // cell_size + 2)

        # Continuous color params
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        return {
            "cell_size": cell_size,
            "probability": probability,
            "speed": speed,
            "noise": noise,
            "grid_w": grid_w,
            "grid_h": grid_h,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """主渲染 - 为每个像素生成迷宫图案"""
        cell_size = state["cell_size"]
        probability = state["probability"]
        speed = state["speed"]
        noise = state["noise"]

        t = ctx.time * speed

        # Determine which grid cell this pixel belongs to
        # Apply time-based column shift for animation
        shift = t * cell_size * 0.5
        cx = int(math.floor((x + shift) / cell_size))
        cy = int(math.floor(y / cell_size))

        # Local coordinates within the cell (0 to 1)
        lx = fract((x + shift) / cell_size)
        ly = fract(y / cell_size)

        # Determine / or \ using noise-based hash for this cell
        # Noise gives smooth spatial variation; add probability bias
        noise_val = noise(cx * 0.73, cy * 0.91)
        is_backslash = noise_val < probability

        # Compute distance from the chosen diagonal within the cell
        # For \: diagonal goes from (0,0) to (1,1), distance = |lx - ly| / sqrt(2)
        # For /: diagonal goes from (1,0) to (0,1), distance = |lx + ly - 1| / sqrt(2)
        if is_backslash:
            dist = abs(lx - ly)
        else:
            dist = abs(lx + ly - 1.0)

        # Normalize distance (max possible is ~0.707 for sqrt(2)/2)
        # Map to 0-1 where 0 = on the line, 1 = far from line
        dist = dist * 1.414  # multiply by sqrt(2) to normalize
        dist = clamp(dist, 0.0, 1.0)

        # Invert so line is bright, edges are dark
        value = 1.0 - dist

        # Apply a sharpening curve to make lines more defined
        value = value * value * value

        # Map to char_idx
        char_idx = int(clamp(value * 9, 0, 9))

        # Color mapping - use cell position for color variation
        color_value = fract(value * 0.8 + (cx + cy) * 0.05 + t * 0.02)
        if state["warmth"] is not None:
            color = value_to_color_continuous(
                color_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(color_value, "matrix")

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - 10 PRINT 不需要后处理"""
        pass
