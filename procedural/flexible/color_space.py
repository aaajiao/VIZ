"""
连续颜色空间 - Continuous Color Space

用连续参数 (warmth, saturation, brightness) 生成颜色，
取代固定的 5 种调色板映射。

特性::

    - 任意色温 (0=冷蓝 → 1=暖红)
    - 任意饱和度 (0=灰色 → 1=纯色)
    - 多锚点插值 (在已知色板之间平滑过渡)
    - 支持 palette 生成 (从连续参数生成完整调色板)

用法::

    from procedural.flexible.color_space import ContinuousColorSpace

    cs = ContinuousColorSpace()

    # 从连续参数生成单色
    color = cs.sample(value=0.5, warmth=0.7, saturation=0.8)
    # → (r, g, b)

    # 生成完整调色板 (bg, primary, secondary, accent, glow)
    palette = cs.generate_palette(warmth=0.3, saturation=0.9, brightness=0.8)
"""

from __future__ import annotations

import colorsys
import math

from procedural.core.mathx import clamp, mix


class ContinuousColorSpace:
    """
    连续颜色空间

    通过 warmth/saturation/brightness 三个连续参数生成颜色，
    实现从冷色到暖色的无级过渡。
    """

    # 色温锚点: warmth → 基础色相 (HSV)
    # 0.0=冷(蓝) → 0.5=中性(绿) → 1.0=暖(红)
    _WARMTH_HUE_CURVE = [
        (0.0, 0.75),   # 紫罗兰 violet
        (0.10, 0.65),  # 蓝紫 blue-violet
        (0.20, 0.58),  # 蓝 blue
        (0.30, 0.50),  # 青蓝 cyan-blue
        (0.40, 0.40),  # 青 cyan
        (0.50, 0.30),  # 绿 green
        (0.60, 0.18),  # 黄绿 yellow-green
        (0.70, 0.12),  # 黄 yellow
        (0.80, 0.05),  # 橙 orange
        (0.90, 0.00),  # 红 red
        (1.0, 0.92),   # 洋红/粉 magenta/pink
    ]

    def warmth_to_hue(self, warmth: float) -> float:
        """
        将色温参数映射到 HSV 色相

        使用分段线性插值在锚点之间过渡。

        参数:
            warmth: 0.0 (冷蓝) 到 1.0 (暖红)

        返回:
            HSV 色相 (0.0-1.0)
        """
        warmth = clamp(warmth, 0.0, 1.0)
        curve = self._WARMTH_HUE_CURVE

        # 找到 warmth 所在的区间
        for i in range(len(curve) - 1):
            w0, h0 = curve[i]
            w1, h1 = curve[i + 1]
            if warmth <= w1:
                t = (warmth - w0) / (w1 - w0) if w1 > w0 else 0.0
                return mix(h0, h1, t)

        return curve[-1][1]

    def sample(
        self,
        value: float,
        warmth: float = 0.5,
        saturation: float = 1.0,
        brightness: float = 1.0,
        hue_spread: float = 0.1,
    ) -> tuple[int, int, int]:
        """
        从连续参数空间采样颜色

        参数:
            value: 明暗值 (0=暗, 1=亮) - 类似灰度梯度
            warmth: 色温 (0=冷蓝, 1=暖红)
            saturation: 饱和度 (0=灰, 1=纯色)
            brightness: 亮度缩放
            hue_spread: 色相在 value 上的扩展范围

        返回:
            (r, g, b) 元组，0-255 范围
        """
        value = clamp(value, 0.0, 1.0)

        base_hue = self.warmth_to_hue(warmth)
        # value 越高，色相略偏移 (模拟真实色彩变化)
        hue = (base_hue + value * hue_spread) % 1.0

        # 饱和度随 value 的极端值降低 (纯黑和纯白趋于无彩)
        value_sat_factor = 1.0 - (2.0 * value - 1.0) ** 4
        effective_sat = clamp(saturation * value_sat_factor, 0.0, 1.0)

        # HSV → RGB
        effective_val = clamp(value * brightness, 0.0, 1.0)
        r, g, b = colorsys.hsv_to_rgb(hue, effective_sat, effective_val)

        return (int(r * 255), int(g * 255), int(b * 255))

    def generate_palette(
        self,
        warmth: float = 0.5,
        saturation: float = 0.9,
        brightness: float = 0.8,
        contrast: float = 0.7,
    ) -> dict[str, tuple[int, int, int]]:
        """
        从连续参数生成完整调色板

        兼容旧系统的 palette 格式 (bg, primary, secondary, accent, glow)，
        但参数是连续的而非离散选择。

        参数:
            warmth: 色温 (0=冷, 1=暖)
            saturation: 饱和度
            brightness: 整体亮度
            contrast: 明暗对比度 (0=flat, 1=高对比)

        返回:
            dict with keys: bg, primary, secondary, accent, glow, outline, dim
        """
        base_hue = self.warmth_to_hue(warmth)

        # 背景: 极暗，带有色温倾向
        bg_v = mix(0.02, 0.08 + brightness * 0.15, 1.0 - contrast)
        bg_s = saturation * 0.3
        br, bg, bb = colorsys.hsv_to_rgb(base_hue, bg_s, bg_v)
        bg_color = (int(br * 255), int(bg * 255), int(bb * 255))

        # 主色: 高饱和高亮度
        p_v = mix(0.7, 1.0, brightness)
        pr, pg, pb = colorsys.hsv_to_rgb(base_hue, saturation, p_v)
        primary = (int(pr * 255), int(pg * 255), int(pb * 255))

        # 副色: 色相偏移，稍暗
        sec_hue = (base_hue + 0.08 + 0.07 * (1.0 - warmth)) % 1.0
        s_v = mix(0.5, 0.85, brightness)
        sr, sg, sb = colorsys.hsv_to_rgb(sec_hue, saturation * 0.9, s_v)
        secondary = (int(sr * 255), int(sg * 255), int(sb * 255))

        # 强调色: 互补色方向偏移或高亮白色
        if saturation > 0.5:
            acc_hue = (base_hue + 0.4 + 0.2 * (1.0 - warmth)) % 1.0
            ar, ag, ab = colorsys.hsv_to_rgb(acc_hue, saturation * 0.5, 0.95)
            accent = (int(ar * 255), int(ag * 255), int(ab * 255))
        else:
            accent = (240, 240, 240)

        # 发光色: 主色的淡化版本
        glow_s = saturation * 0.4
        glow_v = min(1.0, brightness + 0.2)
        gr, gg, gb = colorsys.hsv_to_rgb(base_hue, glow_s, glow_v)
        glow = (int(gr * 255), int(gg * 255), int(gb * 255))

        # 轮廓色: 主色的暗化版本
        or_, og, ob = colorsys.hsv_to_rgb(base_hue, saturation * 0.6, 0.3)
        outline = (int(or_ * 255), int(og * 255), int(ob * 255))

        # 暗色: 极暗参考色
        dr, dg, db = colorsys.hsv_to_rgb(base_hue, saturation * 0.4, 0.15)
        dim = (int(dr * 255), int(dg * 255), int(db * 255))

        return {
            "bg": bg_color,
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "glow": glow,
            "outline": outline,
            "dim": dim,
        }

    def value_to_color(
        self,
        value: float,
        warmth: float = 0.5,
        saturation: float = 1.0,
    ) -> tuple[int, int, int]:
        """
        类似旧系统的 value_to_color，但参数可连续调节

        用于 effect main() 中将像素值映射到颜色。
        替代固定的 heat/rainbow/cool/matrix/plasma 五选一。

        参数:
            value: 0.0-1.0 像素值
            warmth: 色温 (连续)
            saturation: 饱和度 (连续)

        返回:
            (r, g, b)
        """
        return self.sample(value, warmth=warmth, saturation=saturation)


def interpolate_palettes(
    palette_a: dict,
    palette_b: dict,
    t: float,
) -> dict:
    """
    在两个调色板之间插值

    参数:
        palette_a: 调色板 A
        palette_b: 调色板 B
        t: 插值因子 (0.0=A, 1.0=B)

    返回:
        插值后的调色板
    """
    result = {}
    for key in palette_a:
        if key in palette_b:
            ca = palette_a[key]
            cb = palette_b[key]
            result[key] = (
                int(mix(ca[0], cb[0], t)),
                int(mix(ca[1], cb[1], t)),
                int(mix(ca[2], cb[2], t)),
            )
        else:
            result[key] = palette_a[key]
    return result
