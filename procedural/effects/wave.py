"""
Wave 波纹效果 - Wave Effect

实现多层正弦波叠加效果，产生流动的波纹图案。

原理:
    通过多个不同频率和相位的正弦波在垂直方向叠加，
    产生类似水波、声波的干涉图案。

算法:
    value = sum(sin(y * freq[i] + t * speed[i]) for i in range(wave_count))
    value = (value / wave_count + 1) / 2  # 归一化到 0-1

参考:
    - play.core/src/programs/demos/sinsin_wave.js
    - 经典 demo scene 波纹效果

用法::

    from procedural.effects import get_effect

    wave = get_effect('wave')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'wave_count': 5, 'frequency': 0.1, 'amplitude': 1.0, 'speed': 1.0}
    )

    state = wave.pre(ctx, buffer)
    cell = wave.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.palette import value_to_color
from .base import BaseEffect

__all__ = ["WaveEffect"]


class WaveEffect(BaseEffect):
    """
    Wave 波纹效果

    通过多层正弦波叠加产生流动的波纹图案。

    参数 (从 ctx.params 读取):
        wave_count: 波的数量 (默认 5, 范围 1-10)
        frequency: 波的频率 (默认 0.1, 范围 0.01-0.2)
        amplitude: 波的振幅 (默认 1.0, 范围 0.5-3.0)
        speed: 动画速度 (默认 1.0, 范围 0.1-5.0)
        color_scheme: 颜色方案 (默认 'ocean')

    参数范围说明:
        - wave_count: 1 (单波) 到 10 (复杂干涉)
        - frequency: 0.01 (稀疏波纹) 到 0.2 (密集波纹)
        - amplitude: 0.5 (低对比) 到 3.0 (高对比)
        - speed: 0.1 (缓慢动画) 到 5.0 (快速动画)

    示例::

        ctx.params = {
            'wave_count': 7,     # 更多波 = 更复杂的干涉
            'frequency': 0.15,   # 更高频率 = 更密集的波纹
            'amplitude': 1.2,    # 更大振幅 = 更强对比
            'speed': 2.0,        # 更快的动画
            'color_scheme': 'ocean',
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 提取参数并预计算波的频率和速度

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - wave_count: 波的数量
                - base_frequency: 基础频率
                - amplitude: 振幅
                - base_speed: 基础速度
                - frequencies: 每个波的频率列表
                - speeds: 每个波的速度列表
                - color_scheme: 颜色方案
        """
        # 从参数中提取配置
        wave_count = ctx.params.get("wave_count", 5)
        base_frequency = ctx.params.get("frequency", 0.1)
        amplitude = ctx.params.get("amplitude", 1.0)
        base_speed = ctx.params.get("speed", 1.0)
        color_scheme = ctx.params.get("color_scheme", "ocean")

        # 预计算每个波的频率和速度 (使用不同的倍数产生丰富的干涉)
        frequencies = []
        speeds = []
        for i in range(wave_count):
            # 频率: 1.0, 1.3, 1.7, 2.1, ... (质数倍数避免周期性重复)
            freq_mult = 1.0 + i * 0.4
            frequencies.append(base_frequency * freq_mult)

            # 速度: 1.0, 0.7, 1.3, 0.5, ... (不同速度产生动态变化)
            speed_mult = 1.0 - (i % 2) * 0.3 + (i % 3) * 0.2
            speeds.append(base_speed * speed_mult)

        return {
            "wave_count": wave_count,
            "base_frequency": base_frequency,
            "amplitude": amplitude,
            "base_speed": base_speed,
            "frequencies": frequencies,
            "speeds": speeds,
            "color_scheme": color_scheme,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 为每个像素生成波纹值

        算法:
            1. 对每个波计算 sin(y * freq + t * speed)
            2. 叠加所有波并归一化
            3. 映射到字符和颜色

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell (字符索引 + 颜色)
        """
        # 提取状态
        wave_count = state["wave_count"]
        amplitude = state["amplitude"]
        frequencies = state["frequencies"]
        speeds = state["speeds"]
        color_scheme = state["color_scheme"]

        # 时间参数
        t = ctx.time

        # === Wave 核心算法 ===
        # 叠加多个正弦波
        wave_sum = 0.0
        for i in range(wave_count):
            # 每个波使用不同的频率和速度
            wave_value = math.sin(y * frequencies[i] + t * speeds[i])
            wave_sum += wave_value * amplitude

        # 归一化到 0-1 范围
        # wave_sum 范围: [-wave_count * amplitude, wave_count * amplitude]
        value = (wave_sum / (wave_count * amplitude) + 1.0) / 2.0
        value = clamp(value, 0.0, 1.0)

        # === 映射到字符 ===
        # 使用 10 级灰度字符
        char_idx = int(value * 9)
        char_idx = int(clamp(char_idx, 0, 9))

        # === 映射到颜色 ===
        # 使用指定颜色方案
        color = value_to_color(value, color_scheme)

        # 返回 Cell
        return Cell(
            char_idx=char_idx,
            fg=color,
            bg=None,  # 透明背景
        )

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理 - Wave 不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # Wave 效果不需要后处理
