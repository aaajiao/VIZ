"""
模运算/异或分形 - Modular Arithmetic / XOR Fractal Patterns

基于整数位运算 (XOR, AND, OR) 和模运算生成分形图案。
多层叠加不同模数可产生复杂干涉纹理。

Integer bitwise operations (XOR, AND, OR) combined with modular
arithmetic produce self-similar fractal patterns. Multiple layers
with different moduli create complex interference textures.

参考/Reference:
    - XOR fractal / Sierpinski triangle
    - Modular arithmetic art

用法/Usage::

    from procedural.effects import get_effect

    mod_xor = get_effect('mod_xor')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'modulus': 16, 'operation': 'xor', 'layers': 1, 'speed': 0.5}
    )

    state = mod_xor.pre(ctx, buffer)
    cell = mod_xor.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp, fract
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["ModXorEffect"]


# Bitwise operation functions
def _op_xor(a: int, b: int) -> int:
    return a ^ b


def _op_and(a: int, b: int) -> int:
    return a & b


def _op_or(a: int, b: int) -> int:
    return a | b


_OPERATIONS = {
    "xor": _op_xor,
    "and": _op_and,
    "or": _op_or,
}


class ModXorEffect(BaseEffect):
    """
    模运算/异或分形效果

    使用整数位运算和模运算生成自相似分形图案。

    参数 (从 ctx.params 读取):
        modulus: 模数 (默认 16, 范围 2-64)
        operation: 位运算类型 "xor" / "and" / "or" (默认 "xor")
        layers: 叠加层数 (默认 1, 范围 1-3)
        speed: 动画速度 (默认 0.5)
        zoom: 缩放级别 (默认 1.0)

    示例::

        ctx.params = {
            'modulus': 32,
            'operation': 'xor',
            'layers': 2,
            'speed': 1.0,
            'zoom': 1.5,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """预处理 - 提取参数"""
        modulus = ctx.params.get("modulus", 16)
        operation = ctx.params.get("operation", "xor")
        layers = ctx.params.get("layers", 1)
        speed = ctx.params.get("speed", 0.5)
        zoom = ctx.params.get("zoom", 1.0)

        op_func = _OPERATIONS.get(operation, _op_xor)

        # Continuous color params
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        return {
            "modulus": max(2, int(modulus)),
            "op_func": op_func,
            "layers": max(1, min(3, int(layers))),
            "speed": speed,
            "zoom": zoom,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """主渲染 - 为每个像素计算位运算分形值"""
        modulus = state["modulus"]
        op_func = state["op_func"]
        layers = state["layers"]
        speed = state["speed"]
        zoom = state["zoom"]

        t = ctx.time * speed

        # Scale and offset coordinates with time
        # Zoom from center
        cx = ctx.width / 2.0
        cy = ctx.height / 2.0
        sx = int((x - cx) / zoom + cx + t * 5.0)
        sy = int((y - cy) / zoom + cy + t * 3.0)

        # Accumulate across layers
        total = 0.0
        for layer in range(layers):
            # Each layer uses a different modulus offset
            layer_mod = max(2, modulus + layer * 7)

            # Apply coordinate offset per layer for variety
            lx = abs(sx + layer * 17)
            ly = abs(sy + layer * 13)

            # Core operation: (x op y) % modulus
            result = op_func(lx, ly) % layer_mod

            # Normalize to 0-1
            total += result / (layer_mod - 1) if layer_mod > 1 else 0.0

        # Average across layers
        value = total / layers
        value = clamp(value, 0.0, 1.0)

        # Map to char_idx
        char_idx = int(clamp(value * 9, 0, 9))

        # Color mapping - use value with time-based phase shift
        color_value = fract(value + t * 0.03)
        if state["warmth"] is not None:
            color = value_to_color_continuous(
                color_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(color_value, "rainbow")

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - ModXor 不需要后处理"""
        pass
