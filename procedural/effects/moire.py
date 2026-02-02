"""
Moiré 干涉图案效果 - Moiré Pattern Effect

实现两个振荡场的乘法干涉，产生经典的莫尔纹图案。

原理:
    通过两个不同频率的径向波场相乘，产生复杂的干涉图案。
    使用 atan2 计算角度，产生从中心向外辐射的波纹。

算法:
    angle_a = atan2(y - cy_a, x - cx_a)
    angle_b = atan2(y - cy_b, x - cx_b)
    wave_a = cos(angle_a * freq_a + t * speed_a)
    wave_b = cos(angle_b * freq_b + t * speed_b)
    value = (wave_a * wave_b + 1) / 2  # 乘法干涉，归一化到 0-1

参考:
    - play.core/src/programs/demos/moire_explorer.js
    - 经典光学莫尔纹效应

用法::

    from procedural.effects import get_effect

    moire = get_effect('moire')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'freq_a': 8.0, 'freq_b': 13.0, 'speed': 1.0}
    )

    state = moire.pre(ctx, buffer)
    cell = moire.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.palette import value_to_color
from .base import BaseEffect

__all__ = ["MoireEffect"]


class MoireEffect(BaseEffect):
    """
    Moiré 干涉图案效果

    通过两个不同频率的径向波场相乘产生莫尔纹。

    参数 (从 ctx.params 读取):
        freq_a: 第一个波场的频率 (默认 8.0)
        freq_b: 第二个波场的频率 (默认 13.0)
        speed_a: 第一个波场的旋转速度 (默认 0.5)
        speed_b: 第二个波场的旋转速度 (默认 -0.3)
        offset_a: 第一个波场中心偏移 (默认 0.0)
        offset_b: 第二个波场中心偏移 (默认 0.0)
        color_scheme: 颜色方案 (默认 'rainbow')

    示例::

        ctx.params = {
            'freq_a': 12.0,      # 更高频率 = 更密集的辐射线
            'freq_b': 19.0,      # 使用质数避免周期性重复
            'speed_a': 1.0,      # 顺时针旋转
            'speed_b': -0.7,     # 逆时针旋转
            'offset_a': 0.2,     # 中心偏移产生不对称图案
            'offset_b': -0.15,
            'color_scheme': 'rainbow',
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 提取参数并预计算中心点

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - freq_a: 第一个波场频率
                - freq_b: 第二个波场频率
                - speed_a: 第一个波场速度
                - speed_b: 第二个波场速度
                - center_a: 第一个波场中心点 (归一化坐标)
                - center_b: 第二个波场中心点 (归一化坐标)
                - color_scheme: 颜色方案
        """
        # 从参数中提取配置
        freq_a = ctx.params.get("freq_a", 8.0)
        freq_b = ctx.params.get("freq_b", 13.0)
        speed_a = ctx.params.get("speed_a", 0.5)
        speed_b = ctx.params.get("speed_b", -0.3)
        offset_a = ctx.params.get("offset_a", 0.0)
        offset_b = ctx.params.get("offset_b", 0.0)
        color_scheme = ctx.params.get("color_scheme", "rainbow")

        # 预计算中心点 (归一化到 0-1 范围)
        # 默认在画布中心，可通过 offset 参数偏移
        center_a_x = 0.5 + offset_a
        center_a_y = 0.5
        center_b_x = 0.5 + offset_b
        center_b_y = 0.5

        return {
            "freq_a": freq_a,
            "freq_b": freq_b,
            "speed_a": speed_a,
            "speed_b": speed_b,
            "center_a": (center_a_x, center_a_y),
            "center_b": (center_b_x, center_b_y),
            "color_scheme": color_scheme,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 为每个像素生成莫尔纹值

        算法:
            1. 归一化坐标到 0-1 范围
            2. 计算两个波场中心的角度 (atan2)
            3. 使用角度和频率生成径向波
            4. 两个波相乘产生干涉图案
            5. 映射到字符和颜色

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell (字符索引 + 颜色)
        """
        # 提取状态
        freq_a = state["freq_a"]
        freq_b = state["freq_b"]
        speed_a = state["speed_a"]
        speed_b = state["speed_b"]
        center_a = state["center_a"]
        center_b = state["center_b"]
        color_scheme = state["color_scheme"]

        # 时间参数
        t = ctx.time

        # 归一化坐标 (0-1)
        u = x / ctx.width
        v = y / ctx.height

        # === Moiré 核心算法 ===

        # 波场 A: 计算相对于中心 A 的角度
        dx_a = u - center_a[0]
        dy_a = v - center_a[1]
        angle_a = math.atan2(dy_a, dx_a)
        # 使用角度和频率生成径向波 (加上时间旋转)
        wave_a = math.cos(angle_a * freq_a + t * speed_a)

        # 波场 B: 计算相对于中心 B 的角度
        dx_b = u - center_b[0]
        dy_b = v - center_b[1]
        angle_b = math.atan2(dy_b, dx_b)
        # 使用不同频率和速度生成第二个径向波
        wave_b = math.cos(angle_b * freq_b + t * speed_b)

        # 乘法干涉: 两个波相乘产生莫尔纹
        # wave_a 和 wave_b 范围: [-1, 1]
        # 乘积范围: [-1, 1]
        interference = wave_a * wave_b

        # 归一化到 0-1 范围
        value = (interference + 1.0) / 2.0
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
        后处理 - Moiré 不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # Moiré 效果不需要后处理
