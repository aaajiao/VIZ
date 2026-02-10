"""
落沙游戏粒子模拟 - Falling Sand Particle Simulation

模拟沙粒在重力作用下的下落和堆积行为。
粒子从顶部随机生成，向下掉落并在底部或其他粒子上堆积。

算法:
    1. 每帧在顶部随机生成新粒子
    2. 物理更新（从底部向上扫描）:
       - 下方为空 → 直接下落
       - 下方被占 → 尝试左下或右下滑落
       - 全部被占 → 静止
    3. 粒子类型决定颜色方案

用法/Usage::

    from procedural.effects import get_effect

    sand = get_effect('sand_game')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'spawn_rate': 0.3, 'gravity_speed': 2, 'particle_types': 2}
    )

    state = sand.pre(ctx, buffer)
    cell = sand.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["SandGameEffect"]

# Color palettes per particle type
_SAND_COLORS = [
    # Type 1: warm sand
    [(194, 178, 128), (210, 190, 140), (220, 200, 150)],
    # Type 2: reddish sand
    [(180, 100, 60), (200, 120, 70), (220, 140, 80)],
    # Type 3: blue-grey
    [(100, 120, 160), (120, 140, 180), (140, 160, 200)],
]


class SandGameEffect(BaseEffect):
    """
    落沙游戏效果 - Falling Sand Game Effect

    粒子下落与堆积模拟，支持多种粒子类型。

    参数 (从 ctx.params 读取):
        spawn_rate: 每行每帧生成粒子概率 (默认 0.3, 范围 0.1-0.8)
        gravity_speed: 每帧物理更新步数 (默认 2)
        particle_types: 颜色类型数量 (默认 2, 范围 1-3)
    """

    def __init__(self):
        self._grid = None
        self._initialized = False

    def _init_state(self, ctx: Context) -> None:
        """初始化空网格 - Initialize empty grid"""
        w, h = ctx.width, ctx.height
        self._grid = [[0] * w for _ in range(h)]

    def _spawn_particles(self, ctx: Context, spawn_rate: float, particle_types: int) -> None:
        """在顶部生成粒子 - Spawn particles at top row"""
        w = ctx.width
        rng = ctx.rng
        for x in range(w):
            if rng.random() < spawn_rate:
                if self._grid[0][x] == 0:
                    self._grid[0][x] = rng.randint(1, particle_types)

    def _physics_step(self, ctx: Context) -> None:
        """物理更新（从底向上扫描）- Physics update bottom-to-top"""
        w, h = ctx.width, ctx.height
        rng = ctx.rng

        # Scan bottom-to-top, randomize horizontal order
        for y in range(h - 2, -1, -1):
            # Randomize x scan order to avoid directional bias
            xs = list(range(w))
            rng.shuffle(xs)
            for x in xs:
                if self._grid[y][x] == 0:
                    continue

                particle = self._grid[y][x]

                # Try falling straight down
                if self._grid[y + 1][x] == 0:
                    self._grid[y + 1][x] = particle
                    self._grid[y][x] = 0
                else:
                    # Try diagonal: randomly choose left or right first
                    if rng.random() < 0.5:
                        dirs = [(-1, 1), (1, 1)]
                    else:
                        dirs = [(1, 1), (-1, 1)]

                    moved = False
                    for dx, dy in dirs:
                        nx = x + dx
                        ny = y + dy
                        if 0 <= nx < w and ny < h and self._grid[ny][nx] == 0:
                            self._grid[ny][nx] = particle
                            self._grid[y][x] = 0
                            moved = True
                            break

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 生成粒子并更新物理

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典
        """
        spawn_rate = ctx.params.get("spawn_rate", 0.3)
        gravity_speed = ctx.params.get("gravity_speed", 2)
        particle_types = ctx.params.get("particle_types", 2)
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        if not self._initialized:
            self._init_state(ctx)
            self._initialized = True

        # Spawn new particles
        self._spawn_particles(ctx, spawn_rate, particle_types)

        # Physics steps
        for _ in range(gravity_speed):
            self._physics_step(ctx)

        return {
            "grid": self._grid,
            "warmth": warmth,
            "saturation": saturation,
            "height": ctx.height,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 根据粒子类型和位置生成 Cell

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell
        """
        grid = state["grid"]
        particle = grid[y][x]

        if particle == 0:
            # Empty cell
            return Cell(char_idx=0, fg=(10, 10, 15), bg=None)

        # Particle present: map type and height to visual
        height_ratio = y / state["height"]
        value = 0.5 + 0.5 * height_ratio

        char_idx = int(clamp(value * 9, 0, 9))

        if state["warmth"] is not None:
            # Use continuous color with type-based hue shift
            shifted_value = (value + (particle - 1) * 0.3) % 1.0
            color = value_to_color_continuous(
                shifted_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            # Use predefined sand colors
            type_idx = (particle - 1) % len(_SAND_COLORS)
            palette = _SAND_COLORS[type_idx]
            brightness_idx = int(clamp(height_ratio * (len(palette) - 1), 0, len(palette) - 1))
            color = palette[brightness_idx]

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - 落沙游戏不需要后处理"""
        pass
