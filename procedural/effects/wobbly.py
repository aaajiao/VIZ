"""
域扭曲 - Domain Warping (Wobbly)

迭代噪声位移实现域扭曲效果。从初始坐标开始，
每次迭代用噪声采样偏移坐标，产生有机的流体扭曲。

Iterative noise-based domain warping. Starting from initial coords,
each iteration offsets position by noise-sampled displacement,
producing organic fluid-like distortion.

参考/Reference:
    - Inigo Quilez "warp" article (iquilezles.org/articles/warp)
    - Shadertoy domain warping examples

用法/Usage::

    from procedural.effects import get_effect

    wobbly = get_effect('wobbly')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'warp_amount': 0.4, 'warp_freq': 0.03, 'iterations': 2, 'speed': 0.5}
    )

    state = wobbly.pre(ctx, buffer)
    cell = wobbly.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, fract
from procedural.core.noise import ValueNoise
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["WobblyEffect"]


class WobblyEffect(BaseEffect):
    """
    域扭曲效果

    通过迭代噪声位移实现有机的流体扭曲。

    参数 (从 ctx.params 读取):
        warp_amount: 位移幅度 (默认 0.4, 范围 0.1-1.0)
        warp_freq: 扭曲噪声频率 (默认 0.03)
        iterations: 扭曲迭代次数 (默认 2, 范围 1-3)
        speed: 动画速度 (默认 0.5)

    示例::

        ctx.params = {
            'warp_amount': 0.6,
            'warp_freq': 0.05,
            'iterations': 3,
            'speed': 1.0,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """预处理 - 创建噪声实例并提取参数"""
        warp_amount = ctx.params.get("warp_amount", 0.4)
        warp_freq = ctx.params.get("warp_freq", 0.03)
        iterations = ctx.params.get("iterations", 2)
        speed = ctx.params.get("speed", 0.5)

        # Two separate noise instances for x and y displacement
        noise_x = ValueNoise(seed=ctx.seed)
        noise_y = ValueNoise(seed=ctx.seed + 137)
        # Final value noise
        noise_final = ValueNoise(seed=ctx.seed + 293)

        # Continuous color params
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        return {
            "warp_amount": warp_amount,
            "warp_freq": warp_freq,
            "iterations": max(1, min(3, int(iterations))),
            "speed": speed,
            "noise_x": noise_x,
            "noise_y": noise_y,
            "noise_final": noise_final,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """主渲染 - 为每个像素计算域扭曲后的噪声值"""
        warp_amount = state["warp_amount"]
        warp_freq = state["warp_freq"]
        iterations = state["iterations"]
        speed = state["speed"]
        noise_x = state["noise_x"]
        noise_y = state["noise_y"]
        noise_final = state["noise_final"]

        t = ctx.time * speed

        # Normalize coordinates to roughly 0-1 range scaled by frequency
        px = x * warp_freq
        py = y * warp_freq

        # Iterative domain warping
        for i in range(iterations):
            # Sample noise for x displacement with time offset
            # Different time offsets per iteration for variety
            t_offset_x = t * 0.7 + i * 1.7
            t_offset_y = t * 0.5 + i * 2.3

            dx = noise_x(px + t_offset_x, py + 10.0 * i) * 2.0 - 1.0
            dy = noise_y(px + 10.0 * i, py + t_offset_y) * 2.0 - 1.0

            # Offset coordinates by displacement
            px += dx * warp_amount
            py += dy * warp_amount

        # Sample final noise at warped coordinates
        value = noise_final.fbm(px + t * 0.1, py + t * 0.13, octaves=3)
        value = clamp(value, 0.0, 1.0)

        # Map to char_idx
        char_idx = int(clamp(value * 9, 0, 9))

        # Color mapping
        color_value = fract(value + t * 0.04)
        if state["warmth"] is not None:
            color = value_to_color_continuous(
                color_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(color_value, "ocean")

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - Wobbly 不需要后处理"""
        pass
