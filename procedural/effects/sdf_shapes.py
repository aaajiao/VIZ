"""
SDF 形状效果 - SDF Shapes Effect

实现多个 SDF 形状的平滑混合，类似 play.core/balls.js 的效果。

原理:
    使用有符号距离场 (Signed Distance Functions) 定义多个几何形状，
    通过 smooth union 操作将它们平滑混合，产生有机的融合效果。
    距离值映射到字符密度和颜色，形成视觉层次。

算法:
    1. 预计算多个形状的位置和半径
    2. 对每个像素，计算到所有形状的 SDF 距离
    3. 使用 op_smooth_union 平滑合并所有距离
    4. 将距离值映射到 0-1 范围
    5. 根据距离值选择字符和颜色

参考:
    - play.core/sdf.js - SDF 基础函数
    - play.core/balls.js - 多球体融合效果

用法::

    from procedural.effects import get_effect

    sdf = get_effect('sdf_shapes')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={
            'shape_count': 5,
            'shape_type': 'circle',  # 'circle' or 'box'
            'radius_min': 0.05,
            'radius_max': 0.15,
            'smoothness': 0.1,
            'animate': True,
        }
    )

    state = sdf.pre(ctx, buffer)
    cell = sdf.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.vec import Vec2
from procedural.core.sdf import sd_circle, sd_box, op_smooth_union
from procedural.core.mathx import clamp, map_range
from procedural.palette import value_to_color
from .base import BaseEffect

__all__ = ["SDFShapesEffect"]


class SDFShapesEffect(BaseEffect):
    """
    SDF 形状效果 - 多个 SDF 形状平滑混合

    通过有符号距离场实现多个形状的有机融合。

    参数 (从 ctx.params 读取):
        shape_count: 形状数量 (默认 5)
        shape_type: 形状类型 'circle' 或 'box' (默认 'circle')
        radius_min: 最小半径 (默认 0.05)
        radius_max: 最大半径 (默认 0.15)
        smoothness: 平滑系数 (默认 0.1，越大越圆滑)
        animate: 是否动画 (默认 True)
        speed: 动画速度 (默认 1.0)

    示例::

        ctx.params = {
            'shape_count': 8,
            'shape_type': 'circle',
            'radius_min': 0.08,
            'radius_max': 0.2,
            'smoothness': 0.15,
            'animate': True,
            'speed': 0.5,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 生成形状位置和属性

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - shapes: 形状列表 [{'center': Vec2, 'radius': float, 'phase': float}, ...]
                - shape_type: 形状类型
                - smoothness: 平滑系数
                - animate: 是否动画
                - speed: 动画速度
        """
        # 提取参数
        shape_count = ctx.params.get("shape_count", 5)
        shape_type = ctx.params.get("shape_type", "circle")
        radius_min = ctx.params.get("radius_min", 0.05)
        radius_max = ctx.params.get("radius_max", 0.15)
        smoothness = ctx.params.get("smoothness", 0.1)
        animate = ctx.params.get("animate", True)
        speed = ctx.params.get("speed", 1.0)

        # 生成形状
        shapes = []
        for i in range(shape_count):
            # 使用 RNG 生成随机位置和半径
            x = ctx.rng.uniform(0.2, 0.8)
            y = ctx.rng.uniform(0.2, 0.8)
            radius = ctx.rng.uniform(radius_min, radius_max)
            # 每个形状有独立的相位偏移（用于动画）
            phase = ctx.rng.uniform(0, math.pi * 2)

            shapes.append(
                {
                    "center": Vec2(x, y),
                    "radius": radius,
                    "phase": phase,
                }
            )

        return {
            "shapes": shapes,
            "shape_type": shape_type,
            "smoothness": smoothness,
            "animate": animate,
            "speed": speed,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 计算 SDF 距离并映射到字符和颜色

        算法:
            1. 归一化坐标到 0-1
            2. 对每个形状计算 SDF 距离
            3. 使用 smooth union 合并所有距离
            4. 距离值映射到 0-1 (负值=内部, 正值=外部)
            5. 根据值选择字符和颜色

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell (字符索引 + 颜色)
        """
        # 提取状态
        shapes = state["shapes"]
        shape_type = state["shape_type"]
        smoothness = state["smoothness"]
        animate = state["animate"]
        speed = state["speed"]

        # 归一化坐标 (0-1)
        u = x / ctx.width
        v = y / ctx.height

        # 宽高比校正
        aspect = ctx.width / ctx.height if ctx.height > 0 else 1.0
        u *= aspect

        # 当前采样点
        p = Vec2(u, v)

        # 时间参数
        t = ctx.time * speed if animate else 0.0

        # === SDF 核心算法 ===
        # 初始化距离为无穷大
        d = float("inf")

        # 遍历所有形状，计算 smooth union
        for shape in shapes:
            # 动画：形状中心随时间移动
            if animate:
                # 使用正弦波产生循环运动
                offset_x = math.sin(t + shape["phase"]) * 0.1
                offset_y = math.cos(t * 0.7 + shape["phase"]) * 0.1
                center = Vec2(
                    shape["center"].x + offset_x, shape["center"].y + offset_y
                )
            else:
                center = shape["center"]

            # 计算形状的 SDF 距离
            if shape_type == "circle":
                d_shape = sd_circle(p, center, shape["radius"])
            elif shape_type == "box":
                # 矩形使用半宽高
                half_size = Vec2(shape["radius"], shape["radius"])
                d_shape = sd_box(p, center, half_size)
            else:
                # 默认使用圆形
                d_shape = sd_circle(p, center, shape["radius"])

            # 平滑合并
            d = op_smooth_union(d, d_shape, smoothness)

        # === 距离值映射 ===
        # 将距离映射到 0-1 范围
        # 负值 (内部) → 1.0, 正值 (外部) → 0.0
        # 使用缩放因子控制过渡区域宽度
        scale_factor = 5.0
        value = clamp(1.0 - d * scale_factor, 0.0, 1.0)

        # === 映射到字符 ===
        # 使用 10 级字符梯度 (0-9)
        char_idx = int(value * 9)
        char_idx = clamp(char_idx, 0, 9)

        # === 映射到颜色 ===
        # 使用 plasma 颜色方案 + 时间相位
        color_value = (value + t * 0.05) % 1.0
        color = value_to_color(color_value, "plasma")

        # 返回 Cell
        return Cell(
            char_idx=char_idx,
            fg=color,
            bg=None,  # 透明背景
        )

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理 - SDF 形状不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # 无需后处理
