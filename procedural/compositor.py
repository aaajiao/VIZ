"""
效果合成器 - Effect Compositor

用于混合两个效果的合成模块。支持多种混合模式（Add, Multiply, Screen, Overlay）。
限制：最多混合两个效果，不支持嵌套。

用法::

    from procedural.compositor import CompositeEffect, BlendMode
    from procedural.effects import get_effect

    effect_a = get_effect('plasma')
    effect_b = get_effect('wave')

    # 创建合成效果 (50% 混合，叠加模式)
    composite = CompositeEffect(effect_a, effect_b, BlendMode.OVERLAY, mix=0.5)
"""

from enum import Enum, auto
from typing import Tuple, Dict, Any
import math

from procedural.types import Effect, Context, Buffer, Cell


class BlendMode(Enum):
    ADD = auto()
    MULTIPLY = auto()
    SCREEN = auto()
    OVERLAY = auto()


def _clamp(v: int) -> int:
    return max(0, min(255, int(v)))


def _lerp(a: int, b: int, t: float) -> int:
    return int(a * (1 - t) + b * t)


def _blend_add(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    return (_clamp(c1[0] + c2[0]), _clamp(c1[1] + c2[1]), _clamp(c1[2] + c2[2]))


def _blend_multiply(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    return (
        _clamp(c1[0] * c2[0] // 255),
        _clamp(c1[1] * c2[1] // 255),
        _clamp(c1[2] * c2[2] // 255),
    )


def _blend_screen(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    def screen_channel(a, b):
        return 255 - ((255 - a) * (255 - b) // 255)

    return (
        _clamp(screen_channel(c1[0], c2[0])),
        _clamp(screen_channel(c1[1], c2[1])),
        _clamp(screen_channel(c1[2], c2[2])),
    )


def _blend_overlay(
    c1: Tuple[int, int, int], c2: Tuple[int, int, int]
) -> Tuple[int, int, int]:
    def overlay_channel(a, b):
        if a < 128:
            return (2 * a * b) // 255
        else:
            return 255 - (2 * (255 - a) * (255 - b) // 255)

    return (
        _clamp(overlay_channel(c1[0], c2[0])),
        _clamp(overlay_channel(c1[1], c2[1])),
        _clamp(overlay_channel(c1[2], c2[2])),
    )


class CompositeEffect:
    """
    合成效果 - Composite Effect

    将两个效果混合在一起。
    """

    def __init__(
        self, effect_a: Effect, effect_b: Effect, mode: BlendMode, mix: float = 0.5
    ):
        """
        初始化合成效果。

        Args:
            effect_a: 基础效果 (底层)
            effect_b: 混合效果 (顶层)
            mode: 混合模式
            mix: 混合强度 (0.0 - 1.0)，控制 effect_b 的不透明度

        Raises:
            ValueError: 如果尝试嵌套 CompositeEffect
        """
        if isinstance(effect_a, CompositeEffect) or isinstance(
            effect_b, CompositeEffect
        ):
            raise ValueError(
                "Nesting of CompositeEffect is not allowed. Maximum 2 effects."
            )

        self.effect_a = effect_a
        self.effect_b = effect_b
        self.mode = mode
        self.mix = max(0.0, min(1.0, mix))

    def pre(self, ctx: Context, buffer: Buffer) -> Dict[str, Any]:
        """
        预处理阶段：分别调用两个效果的 pre 方法。
        """
        state_a = self.effect_a.pre(ctx, buffer)
        state_b = self.effect_b.pre(ctx, buffer)
        return {"a": state_a, "b": state_b}

    def main(self, x: int, y: int, ctx: Context, state: Dict[str, Any]) -> Cell:
        """
        主渲染阶段：获取两个效果的 Cell 并混合。
        """
        cell_a = self.effect_a.main(x, y, ctx, state["a"])
        cell_b = self.effect_b.main(x, y, ctx, state["b"])

        # 混合颜色
        c1 = cell_a.fg
        c2 = cell_b.fg

        if self.mode == BlendMode.ADD:
            blended_fg = _blend_add(c1, c2)
        elif self.mode == BlendMode.MULTIPLY:
            blended_fg = _blend_multiply(c1, c2)
        elif self.mode == BlendMode.SCREEN:
            blended_fg = _blend_screen(c1, c2)
        elif self.mode == BlendMode.OVERLAY:
            blended_fg = _blend_overlay(c1, c2)
        else:
            blended_fg = c2  # Fallback

        # 应用混合强度 (Opacity)
        final_fg = (
            _lerp(c1[0], blended_fg[0], self.mix),
            _lerp(c1[1], blended_fg[1], self.mix),
            _lerp(c1[2], blended_fg[2], self.mix),
        )

        # 混合字符索引 (线性插值)
        final_char_idx = _lerp(cell_a.char_idx, cell_b.char_idx, self.mix)

        # 背景色处理 (优先使用非空的背景，如果都有则混合)
        bg_a = cell_a.bg
        bg_b = cell_b.bg
        final_bg = None

        if bg_a and bg_b:
            # 简单混合背景
            final_bg = (
                _lerp(bg_a[0], bg_b[0], self.mix),
                _lerp(bg_a[1], bg_b[1], self.mix),
                _lerp(bg_a[2], bg_b[2], self.mix),
            )
        elif bg_a:
            final_bg = bg_a
        elif bg_b:
            final_bg = bg_b

        return Cell(char_idx=final_char_idx, fg=final_fg, bg=final_bg)

    def post(self, ctx: Context, buffer: Buffer, state: Dict[str, Any]) -> None:
        """
        后处理阶段：按顺序调用两个效果的 post 方法。
        """
        self.effect_a.post(ctx, buffer, state["a"])
        self.effect_b.post(ctx, buffer, state["b"])
