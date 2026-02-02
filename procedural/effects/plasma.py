"""
Plasma 等离子体效果 - Plasma Effect

实现多正弦波叠加的经典 plasma 效果。

原理:
    通过多个不同频率和相位的正弦波叠加，产生复杂的干涉图案。
    每个波使用不同的空间函数（距离、坐标、对角线等）。

算法:
    v1 = sin(dot(coord, vec2(sin(t), cos(t))) * freq)
    v2 = cos(length(sub(st, center)) * 4.0)
    v3 = sin(x * freq + t) + sin(y * freq * 1.3 + t * 0.7)
    v4 = sin(sqrt(x*x + y*y) * freq + t)
    value = (v1 + v2 + v3 + v4) / 4  # -1 到 1
    value = (value + 1) / 2  # 0 到 1

参考:
    - play.core/src/programs/demos/plasma.js
    - Shadertoy plasma shaders

用法::

    from procedural.effects import get_effect

    plasma = get_effect('plasma')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'frequency': 0.05, 'speed': 1.0, 'color_phase': 0.0}
    )

    state = plasma.pre(ctx, buffer)
    cell = plasma.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.vec import Vec2, dot, length, sub
from procedural.core.mathx import clamp, map_range
from procedural.palette import char_at_value, value_to_color
from .base import BaseEffect

__all__ = ["PlasmaEffect"]


class PlasmaEffect(BaseEffect):
    """
    Plasma 等离子体效果

    通过多个正弦波叠加产生复杂的干涉图案。

    参数 (从 ctx.params 读取):
        frequency: 波的频率 (默认 0.05, 范围 0.01-0.2)
        speed: 动画速度 (默认 1.0, 范围 0.1-5.0)
        color_phase: 颜色相位偏移 (默认 0.0, 范围 0.0-1.0)
        seed: 随机种子 (默认 0)

    参数范围说明:
        - frequency: 0.01 (稀疏波纹) 到 0.2 (密集波纹)
        - speed: 0.1 (缓慢动画) 到 5.0 (快速动画)
        - color_phase: 0.0 到 1.0 (完整色环)

    示例::

        ctx.params = {
            'frequency': 0.08,  # 更高频率 = 更密集的波纹
            'speed': 2.0,       # 更快的动画
            'color_phase': 0.5, # 颜色偏移
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 提取参数并预计算常量

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - frequency: 波的频率
                - speed: 动画速度
                - color_phase: 颜色相位
                - center: 画布中心点 (Vec2)
                - aspect: 宽高比校正
        """
        # 从参数中提取配置
        frequency = ctx.params.get("frequency", 0.05)
        speed = ctx.params.get("speed", 1.0)
        color_phase = ctx.params.get("color_phase", 0.0)

        # 预计算中心点和宽高比
        center = Vec2(ctx.width / 2.0, ctx.height / 2.0)
        aspect = ctx.width / ctx.height if ctx.height > 0 else 1.0

        return {
            "frequency": frequency,
            "speed": speed,
            "color_phase": color_phase,
            "center": center,
            "aspect": aspect,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 为每个像素生成 plasma 值

        算法:
            1. 归一化坐标到 0-1 范围
            2. 计算 4 个不同的正弦波
            3. 叠加并归一化到 0-1
            4. 映射到字符和颜色

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell (字符索引 + 颜色)
        """
        # 提取状态
        freq = state["frequency"]
        speed = state["speed"]
        color_phase = state["color_phase"]
        center = state["center"]
        aspect = state["aspect"]

        # 时间参数
        t = ctx.time * speed

        # 归一化坐标 (0-1)
        u = x / ctx.width
        v = y / ctx.height

        # 宽高比校正
        u *= aspect

        # === Plasma 核心算法 ===
        # 4 层正弦波叠加

        # 波 1: 旋转方向波 (基于时间变化的方向向量)
        # 使用 dot 产品计算沿旋转方向的投影
        direction = Vec2(math.sin(t * 0.3), math.cos(t * 0.5))
        coord = Vec2(u, v)
        v1 = math.sin(dot(coord, direction) * 10.0 * freq + t)

        # 波 2: 径向波 (从中心向外扩散)
        # 使用距离函数产生圆形波纹
        center_norm = Vec2(center.x / ctx.width * aspect, center.y / ctx.height)
        dist_from_center = length(sub(coord, center_norm))
        v2 = math.cos(dist_from_center * 40.0 * freq + t * 0.7)

        # 波 3: 水平 + 垂直波 (网格状干涉)
        # 不同频率的 x 和 y 波叠加
        v3 = (math.sin(u * 10.0 * freq + t) + math.sin(v * 13.0 * freq + t * 0.7)) / 2.0

        # 波 4: 对角波 (sqrt 产生非线性扭曲)
        # 使用勾股定理计算到原点的距离
        diagonal_dist = math.sqrt(u * u + v * v)
        v4 = math.sin(diagonal_dist * 15.0 * freq + t * 1.2)

        # 合成所有波 (平均值)
        value = (v1 + v2 + v3 + v4) / 4.0  # -1 到 1
        value = (value + 1.0) / 2.0  # 归一化到 0-1

        # 确保值在有效范围内
        value = clamp(value, 0.0, 1.0)

        # === 映射到字符 ===
        # 使用 plasma 专用字符梯度
        char_idx = int(value * 9)  # 0-9 索引
        char_idx = int(clamp(char_idx, 0, 9))

        # === 映射到颜色 ===
        # 使用 plasma 颜色方案 + 时间相位偏移
        color_value = (value + t * 0.05 + color_phase) % 1.0
        color = value_to_color(color_value, "plasma")

        # 返回 Cell
        return Cell(
            char_idx=char_idx,
            fg=color,
            bg=None,  # 透明背景
        )

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理 - Plasma 不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # Plasma 效果不需要后处理
