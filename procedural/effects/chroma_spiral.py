"""
色差螺旋 - Chromatic Spiral

极坐标螺旋加色差分离效果。将坐标转换为极坐标后，
为 RGB 三通道分别施加不同的半径/角度偏移，产生色差效果。

Polar coordinate spiral with chromatic aberration. Converts to polar
coords, then offsets each RGB channel by different radius/angle amounts
to produce chromatic aberration.

参考/Reference:
    - Shadertoy chromatic aberration spirals
    - Polar coordinate art

用法/Usage::

    from procedural.effects import get_effect

    spiral = get_effect('chroma_spiral')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'arms': 3, 'tightness': 0.5, 'speed': 1.0, 'chroma_offset': 0.1}
    )

    state = spiral.pre(ctx, buffer)
    cell = spiral.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, fract, TAU
from procedural.core.noise import ValueNoise
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["ChromaSpiralEffect"]


class ChromaSpiralEffect(BaseEffect):
    """
    色差螺旋效果

    极坐标螺旋加 RGB 通道色差分离。

    参数 (从 ctx.params 读取):
        arms: 螺旋臂数 (默认 3, 范围 1-8)
        tightness: 螺旋紧密度 (默认 0.5, 范围 0.1-2.0)
        speed: 动画速度 (默认 1.0)
        chroma_offset: 色差偏移量 (默认 0.1, 范围 0.0-0.3)
        distortion: 极坐标噪声扭曲 (默认 0.0, 范围 0.0-1.0)
        multi_center: 多中心点数量 (默认 1, 范围 1-4)

    示例::

        ctx.params = {
            'arms': 5,
            'tightness': 0.8,
            'speed': 1.5,
            'chroma_offset': 0.15,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """预处理 - 提取参数并计算中心"""
        arms = ctx.params.get("arms", 3)
        tightness = ctx.params.get("tightness", 0.5)
        speed = ctx.params.get("speed", 1.0)
        chroma_offset = ctx.params.get("chroma_offset", 0.1)

        center_x = ctx.width / 2.0
        center_y = ctx.height / 2.0

        # Continuous color params
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        # 变形参数 - Deformation params
        distortion = ctx.params.get("distortion", 0.0)
        multi_center = max(1, int(ctx.params.get("multi_center", 1)))

        # 噪声源 (用于极坐标扭曲)
        noise_fn = None
        if distortion > 0:
            noise_fn = ValueNoise(seed=ctx.seed + 88)

        # 多中心点: 围绕画布中心均匀分布
        centers = [(center_x, center_y)]
        if multi_center > 1:
            centers = []
            for ci in range(multi_center):
                angle = ci * (TAU / multi_center)
                cx = center_x + ctx.width * 0.15 * math.cos(angle)
                cy = center_y + ctx.height * 0.15 * math.sin(angle)
                centers.append((cx, cy))

        return {
            "arms": max(1, int(arms)),
            "tightness": tightness,
            "speed": speed,
            "chroma_offset": chroma_offset,
            "center_x": center_x,
            "center_y": center_y,
            "warmth": warmth,
            "saturation": saturation,
            "distortion": distortion,
            "noise_fn": noise_fn,
            "multi_center": multi_center,
            "centers": centers,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """主渲染 - 为每个像素计算色差螺旋值"""
        arms = state["arms"]
        tightness = state["tightness"]
        speed = state["speed"]
        chroma_offset = state["chroma_offset"]
        distortion = state["distortion"]
        noise_fn = state["noise_fn"]
        multi_center = state["multi_center"]
        centers = state["centers"]

        t = ctx.time * speed

        if multi_center > 1:
            # 多中心模式: 叠加多个螺旋中心
            r_total = 0.0
            g_total = 0.0
            b_total = 0.0
            for ci, (cx, cy) in enumerate(centers):
                dx = x - cx
                dy = y - cy
                radius = math.sqrt(dx * dx + dy * dy)
                angle = math.atan2(dy, dx)

                max_radius = min(ctx.width, ctx.height) / 2.0
                norm_radius = radius / max_radius if max_radius > 0 else 0.0

                # 噪声扭曲
                if noise_fn is not None and distortion > 0:
                    u = x / ctx.width
                    v = y / ctx.height
                    angle += (noise_fn(u * 4.0 + ci * 10.0, v * 4.0) - 0.5) * distortion * 2.0
                    norm_radius += (noise_fn(u * 4.0 + ci * 10.0 + 50.0, v * 4.0 + 50.0) - 0.5) * distortion * 0.3

                def spiral_value(r_off, a_off):
                    r = norm_radius + r_off
                    a = angle + a_off
                    return fract(a / TAU * arms + r * tightness * 10.0 + t + ci * 0.7)

                r_val = spiral_value(chroma_offset, chroma_offset * 0.5)
                g_val = spiral_value(0.0, 0.0)
                b_val = spiral_value(-chroma_offset, -chroma_offset * 0.5)

                r_total += r_val * r_val * (3.0 - 2.0 * r_val)
                g_total += g_val * g_val * (3.0 - 2.0 * g_val)
                b_total += b_val * b_val * (3.0 - 2.0 * b_val)

            r_val = r_total / multi_center
            g_val = g_total / multi_center
            b_val = b_total / multi_center
        else:
            # 标准单中心模式
            center_x = state["center_x"]
            center_y = state["center_y"]

            # Compute polar coordinates from center
            dx = x - center_x
            dy = y - center_y
            radius = math.sqrt(dx * dx + dy * dy)
            angle = math.atan2(dy, dx)

            # Normalize radius by half the smaller dimension
            max_radius = min(ctx.width, ctx.height) / 2.0
            norm_radius = radius / max_radius if max_radius > 0 else 0.0

            # 噪声扭曲极坐标
            if noise_fn is not None and distortion > 0:
                u = x / ctx.width
                v = y / ctx.height
                angle += (noise_fn(u * 4.0, v * 4.0) - 0.5) * distortion * 2.0
                norm_radius += (noise_fn(u * 4.0 + 50.0, v * 4.0 + 50.0) - 0.5) * distortion * 0.3

            # Spiral value for each RGB channel with chromatic offset
            # Base spiral: fract(angle/TAU * arms + radius * tightness + t)
            def spiral_value(r_offset: float, a_offset: float) -> float:
                r = norm_radius + r_offset
                a = angle + a_offset
                return fract(a / TAU * arms + r * tightness * 10.0 + t)

            # Red channel - slight outward offset
            r_val = spiral_value(chroma_offset, chroma_offset * 0.5)
            # Green channel - no offset (reference)
            g_val = spiral_value(0.0, 0.0)
            # Blue channel - slight inward offset
            b_val = spiral_value(-chroma_offset, -chroma_offset * 0.5)

            # Apply smoothing curve to each channel
            r_val = r_val * r_val * (3.0 - 2.0 * r_val)
            g_val = g_val * g_val * (3.0 - 2.0 * g_val)
            b_val = b_val * b_val * (3.0 - 2.0 * b_val)

        # Average for char_idx
        avg_value = (r_val + g_val + b_val) / 3.0
        char_idx = int(clamp(avg_value * 9, 0, 9))

        # Build color from the three channel values
        if state["warmth"] is not None:
            # Use continuous color with average value
            color_value = fract(avg_value + t * 0.05)
            color = value_to_color_continuous(
                color_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            # Direct RGB from spiral channels for chromatic effect
            r = int(clamp(r_val * 255, 0, 255))
            g = int(clamp(g_val * 255, 0, 255))
            b = int(clamp(b_val * 255, 0, 255))
            color = (r, g, b)

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - ChromaSpiral 不需要后处理"""
        pass
