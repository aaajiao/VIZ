"""
生命游戏细胞自动机 - Conway's Game of Life Cellular Automaton

经典 B3/S23 规则的生命游戏，使用环形拓扑（边界环绕）。
通过 ValueNoise 生成有机分布的初始种子，追踪细胞存活年龄以映射颜色。

算法:
    1. 使用 ValueNoise 生成初始种子模式
    2. 每帧按 B3/S23 规则推进若干代:
       - 死亡细胞恰好有 3 个邻居时复活
       - 存活细胞有 2 或 3 个邻居时存活，否则死亡
    3. 存活细胞年龄递增，死亡细胞年龄归零
    4. 年龄映射到字符密度和颜色亮度

用法/Usage::

    from procedural.effects import get_effect

    gol = get_effect('game_of_life')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'density': 0.4, 'speed': 5.0, 'wrap': True}
    )

    state = gol.pre(ctx, buffer)
    cell = gol.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.core.noise import ValueNoise
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["GameOfLifeEffect"]


class GameOfLifeEffect(BaseEffect):
    """
    生命游戏效果 - Conway's Game of Life Effect

    B3/S23 规则细胞自动机，支持环形拓扑和细胞年龄追踪。

    参数 (从 ctx.params 读取):
        density: 初始填充比例 (默认 0.4, 范围 0.3-0.7)
        speed: 每秒代数 (默认 5.0)
        wrap: 是否使用环形拓扑 (默认 True)
    """

    def __init__(self):
        self._grid = None
        self._age = None
        self._initialized = False
        self._last_time = 0.0
        self._gen_accum = 0.0

    def _init_state(self, ctx: Context) -> None:
        """使用 ValueNoise 初始化网格 - Initialize grid with ValueNoise"""
        w, h = ctx.width, ctx.height
        density = ctx.params.get("density", 0.4)
        noise = ValueNoise(seed=ctx.seed)
        noise_scale = 0.08

        self._grid = []
        self._age = []
        for y in range(h):
            row = []
            age_row = []
            for x in range(w):
                val = noise(x * noise_scale, y * noise_scale)
                alive = 1 if val < density else 0
                row.append(alive)
                age_row.append(1 if alive else 0)
            self._grid.append(row)
            self._age.append(age_row)

        self._last_time = ctx.time

    def _count_neighbors(self, x: int, y: int, w: int, h: int, wrap: bool) -> int:
        """计算邻居数量 - Count live neighbors"""
        count = 0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if wrap:
                    nx = nx % w
                    ny = ny % h
                elif nx < 0 or nx >= w or ny < 0 or ny >= h:
                    continue
                count += self._grid[ny][nx]
        return count

    def _step(self, w: int, h: int, wrap: bool) -> None:
        """推进一代 - Advance one generation"""
        new_grid = []
        new_age = []
        for y in range(h):
            row = []
            age_row = []
            for x in range(w):
                neighbors = self._count_neighbors(x, y, w, h, wrap)
                alive = self._grid[y][x]
                if alive:
                    survives = 1 if neighbors in (2, 3) else 0
                else:
                    survives = 1 if neighbors == 3 else 0

                if survives:
                    age_row.append(self._age[y][x] + 1)
                else:
                    age_row.append(0)
                row.append(survives)
            new_grid.append(row)
            new_age.append(age_row)
        self._grid = new_grid
        self._age = new_age

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 推进生命游戏

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典
        """
        speed = ctx.params.get("speed", 5.0)
        wrap = ctx.params.get("wrap", True)
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        if not self._initialized:
            self._init_state(ctx)
            self._initialized = True

        # Calculate generations to advance this frame
        dt = ctx.time - self._last_time
        if dt < 0:
            dt = 0.0
        self._last_time = ctx.time
        self._gen_accum += dt * speed
        steps = int(self._gen_accum)
        self._gen_accum -= steps

        w, h = ctx.width, ctx.height
        for _ in range(min(steps, 10)):
            self._step(w, h, wrap)

        return {
            "grid": self._grid,
            "age": self._age,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 根据细胞状态和年龄生成 Cell

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell
        """
        grid = state["grid"]
        age = state["age"]

        alive = grid[y][x]
        cell_age = age[y][x]

        if alive:
            # Age-based brightness: older cells are brighter
            age_val = clamp(cell_age / 30.0, 0.0, 1.0)
            value = 0.4 + 0.6 * age_val
            char_idx = int(clamp(value * 9, 0, 9))

            if state["warmth"] is not None:
                color = value_to_color_continuous(
                    value,
                    warmth=state["warmth"],
                    saturation=state.get("saturation", 1.0),
                )
            else:
                color = value_to_color(value, "matrix")
        else:
            # Dead cell: dim glow based on nearby alive cells
            glow = 0
            w, h = ctx.width, ctx.height
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx = (x + dx) % w
                    ny = (y + dy) % h
                    glow += grid[ny][nx]

            if glow > 0:
                glow_val = clamp(glow / 8.0, 0.0, 0.15)
                char_idx = 0
                if state["warmth"] is not None:
                    color = value_to_color_continuous(
                        glow_val,
                        warmth=state["warmth"],
                        saturation=state.get("saturation", 1.0),
                    )
                else:
                    color = value_to_color(glow_val, "matrix")
            else:
                char_idx = 0
                color = (0, 0, 0)

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - 生命游戏不需要后处理"""
        pass
