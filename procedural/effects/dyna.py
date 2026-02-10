"""
动态吸引子波干涉 - Dynamic Attractor Wave Interference

多个运动吸引子点产生正弦波，各波叠加形成干涉图案。
吸引子在画布内弹跳或环绕移动，产生不断变化的驻波效果。

算法:
    1. N 个吸引子各有位置 (x, y) 和速度 (vx, vy)
    2. 每帧更新吸引子位置（弹跳或环绕）
    3. 每像素: 计算到各吸引子距离，叠加 sin(distance * frequency * TAU)
    4. 归一化后映射到字符和颜色

用法/Usage::

    from procedural.effects import get_effect

    dyna = get_effect('dyna')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'attractor_count': 4, 'frequency': 0.5, 'speed': 1.0, 'bounce': True}
    )

    state = dyna.pre(ctx, buffer)
    cell = dyna.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, TAU
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["DynaEffect"]


class DynaEffect(BaseEffect):
    """
    动态吸引子波干涉效果 - Dynamic Attractor Wave Interference Effect

    多个运动吸引子产生波干涉图案。

    参数 (从 ctx.params 读取):
        attractor_count: 吸引子数量 (默认 4, 范围 2-8)
        frequency: 波频率 (默认 0.5, 范围 0.1-2.0)
        speed: 吸引子移动速度 (默认 1.0)
        bounce: 弹跳或环绕 (默认 True)
    """

    def __init__(self):
        self._attractors = None
        self._initialized = False

    def _init_state(self, ctx: Context) -> None:
        """初始化吸引子 - Initialize attractors"""
        attractor_count = ctx.params.get("attractor_count", 4)
        rng = ctx.rng
        w, h = ctx.width, ctx.height

        self._attractors = []
        for _ in range(attractor_count):
            ax = rng.random() * w
            ay = rng.random() * h
            vx = (rng.random() - 0.5) * 2.0
            vy = (rng.random() - 0.5) * 2.0
            self._attractors.append([ax, ay, vx, vy])

    def _update_attractors(self, ctx: Context, speed: float, bounce: bool) -> None:
        """更新吸引子位置 - Update attractor positions"""
        w, h = ctx.width, ctx.height

        for att in self._attractors:
            att[0] += att[2] * speed
            att[1] += att[3] * speed

            if bounce:
                if att[0] < 0:
                    att[0] = -att[0]
                    att[2] = -att[2]
                elif att[0] >= w:
                    att[0] = 2 * w - att[0] - 1
                    att[2] = -att[2]
                if att[1] < 0:
                    att[1] = -att[1]
                    att[3] = -att[3]
                elif att[1] >= h:
                    att[1] = 2 * h - att[1] - 1
                    att[3] = -att[3]
            else:
                att[0] = att[0] % w
                att[1] = att[1] % h

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 更新吸引子位置

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典
        """
        frequency = ctx.params.get("frequency", 0.5)
        speed = ctx.params.get("speed", 1.0)
        bounce = ctx.params.get("bounce", True)
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        if not self._initialized:
            self._init_state(ctx)
            self._initialized = True

        self._update_attractors(ctx, speed, bounce)

        return {
            "attractors": self._attractors,
            "frequency": frequency,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 计算波干涉并映射到 Cell

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell
        """
        attractors = state["attractors"]
        frequency = state["frequency"]

        # Sum sine waves from each attractor
        total = 0.0
        for att in attractors:
            dx = x - att[0]
            dy = y - att[1]
            dist = math.sqrt(dx * dx + dy * dy)
            total += math.sin(dist * frequency * TAU / ctx.width)

        # Normalize: divide by count, map from [-1,1] to [0,1]
        n = len(attractors)
        value = (total / n + 1.0) / 2.0
        value = clamp(value, 0.0, 1.0)

        char_idx = int(clamp(value * 9, 0, 9))

        if state["warmth"] is not None:
            color = value_to_color_continuous(
                value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(value, "plasma")

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - 波干涉效果不需要后处理"""
        pass
