"""
3D 线框立方体效果 - 3D Wireframe Cube Effect

通过距离场渲染旋转线框立方体。8 个顶点 12 条棱，
投影到 2D 后用 sd_line 计算每个像素到最近棱边的距离。

算法:
    1. pre() 阶段旋转 8 个顶点并投影到 2D
    2. 为每个像素计算到 12 条投影棱的最小距离
    3. 存储距离场缓冲区
    4. main() 阶段查表映射距离到字符和颜色

参数:
    rotation_speed_x: X 轴旋转速度 (默认 0.7)
    rotation_speed_y: Y 轴旋转速度 (默认 1.0)
    rotation_speed_z: Z 轴旋转速度 (默认 0.3)
    scale: 立方体缩放 (默认 0.3)
    edge_thickness: 边线粗细 (默认 0.015)
    vertex_noise: 顶点噪声位移 (默认 0.0, 范围 0.0-1.0)
    morph: 立方体-球体变形 (默认 0.0, 范围 0.0-1.0)

用法::

    from procedural.effects import get_effect

    cube = get_effect('wireframe_cube')
    state = cube.pre(ctx, buffer)
    cell = cube.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.core.noise import ValueNoise
from procedural.core.vec import Vec2
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

try:
    from procedural.core.sdf import sd_line
except ImportError:
    from viz.procedural.core.sdf import sd_line

try:
    from procedural.core.projection import Vec3, rotate_x, rotate_y, rotate_z, project_perspective
except ImportError:
    from viz.procedural.core.projection import Vec3, rotate_x, rotate_y, rotate_z, project_perspective

__all__ = ["WireframeCubeEffect"]

# 立方体 8 个顶点 (+-0.5, +-0.5, +-0.5)
_CUBE_VERTICES = [
    Vec3(-0.5, -0.5, -0.5),
    Vec3(+0.5, -0.5, -0.5),
    Vec3(+0.5, +0.5, -0.5),
    Vec3(-0.5, +0.5, -0.5),
    Vec3(-0.5, -0.5, +0.5),
    Vec3(+0.5, -0.5, +0.5),
    Vec3(+0.5, +0.5, +0.5),
    Vec3(-0.5, +0.5, +0.5),
]

# 12 条棱 (顶点索引对)
_CUBE_EDGES = [
    # 底面
    (0, 1), (1, 2), (2, 3), (3, 0),
    # 顶面
    (4, 5), (5, 6), (6, 7), (7, 4),
    # 竖棱
    (0, 4), (1, 5), (2, 6), (3, 7),
]


class WireframeCubeEffect(BaseEffect):
    """
    3D 线框立方体效果 - 3D Wireframe Cube Effect

    通过距离场渲染旋转的线框立方体。

    参数 (从 ctx.params 读取):
        rotation_speed_x: X 轴旋转速度 (默认 0.7)
        rotation_speed_y: Y 轴旋转速度 (默认 1.0)
        rotation_speed_z: Z 轴旋转速度 (默认 0.3)
        scale: 立方体缩放 (默认 0.3)
        edge_thickness: 边线粗细 (默认 0.015)
        vertex_noise: 顶点噪声位移 (默认 0.0)
        morph: 立方体-球体变形 (默认 0.0)
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 旋转顶点、投影、构建距离场缓冲区
        """
        speed_x = ctx.params.get("rotation_speed_x", 0.7)
        speed_y = ctx.params.get("rotation_speed_y", 1.0)
        speed_z = ctx.params.get("rotation_speed_z", 0.3)
        scale = ctx.params.get("scale", 0.3)
        thickness = ctx.params.get("edge_thickness", 0.015)

        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        # 变形参数 - Deformation params
        vertex_noise_amt = ctx.params.get("vertex_noise", 0.0)
        morph = ctx.params.get("morph", 0.0)

        # 噪声源 (用于顶点变形)
        noise_fn = None
        if vertex_noise_amt > 0:
            noise_fn = ValueNoise(seed=ctx.seed + 55)

        t = ctx.time
        w = ctx.width
        h = ctx.height

        # 旋转角度
        ax = t * speed_x
        ay = t * speed_y
        az = t * speed_z

        # 旋转并投影顶点到归一化屏幕空间
        projected = []
        for vi, v in enumerate(_CUBE_VERTICES):
            mv = v

            # 立方体-球体变形
            if morph > 0:
                vlen = math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)
                if vlen > 0.001:
                    sphere_v = Vec3(v.x / vlen * 0.5, v.y / vlen * 0.5, v.z / vlen * 0.5)
                    mv = Vec3(
                        v.x * (1.0 - morph) + sphere_v.x * morph,
                        v.y * (1.0 - morph) + sphere_v.y * morph,
                        v.z * (1.0 - morph) + sphere_v.z * morph,
                    )

            # 顶点噪声位移
            if noise_fn is not None and vertex_noise_amt > 0:
                nx = (noise_fn(vi * 7.1, t * 0.5) - 0.5) * vertex_noise_amt * 0.5
                ny = (noise_fn(t * 0.5, vi * 7.1) - 0.5) * vertex_noise_amt * 0.5
                nz = (noise_fn(vi * 3.7, vi * 5.3 + t * 0.3) - 0.5) * vertex_noise_amt * 0.5
                mv = Vec3(mv.x + nx, mv.y + ny, mv.z + nz)

            # 缩放
            sv = Vec3(mv.x * scale, mv.y * scale, mv.z * scale)
            # 旋转
            sv = rotate_x(sv, ax)
            sv = rotate_y(sv, ay)
            sv = rotate_z(sv, az)
            # 平移到相机前方
            sv = Vec3(sv.x, sv.y, sv.z + 1.5)
            # 投影到屏幕空间 (-1 to 1 range)
            sx, sy, _ = project_perspective(sv, fov=60.0, aspect=1.0)
            # 转为归一化坐标 (0 to 1)
            px = sx * 0.5 + 0.5
            py = -sy * 0.5 + 0.5
            projected.append(Vec2(px, py))

        # 构建距离场缓冲区
        dist_buffer = [[0.0] * w for _ in range(h)]

        for y_px in range(h):
            ny = y_px / h
            for x_px in range(w):
                nx = x_px / w
                p = Vec2(nx, ny)

                # 计算到所有 12 条棱的最小距离
                min_dist = 1e10
                for i0, i1 in _CUBE_EDGES:
                    d = sd_line(p, projected[i0], projected[i1])
                    if d < min_dist:
                        min_dist = d

                dist_buffer[y_px][x_px] = min_dist

        return {
            "dist_buffer": dist_buffer,
            "thickness": thickness,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 查表距离场，映射到字符和颜色
        """
        dist = state["dist_buffer"][y][x]
        thickness = state["thickness"]

        # 距离归一化：边线内部亮，外部衰减
        # thickness 以内为全亮，之外按距离衰减
        if dist < thickness:
            value = 1.0
        else:
            # 衰减区域 (从 thickness 到 thickness * 4)
            falloff = thickness * 3.0
            value = 1.0 - clamp((dist - thickness) / falloff, 0.0, 1.0)

        # 低亮度区域为背景
        if value < 0.02:
            return Cell(char_idx=0, fg=(15, 15, 25), bg=None)

        char_idx = int(clamp(value * 9, 0, 9))

        # 颜色映射
        color_value = clamp(value, 0.0, 1.0)
        if state["warmth"] is not None:
            color = value_to_color_continuous(
                color_value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(color_value, "cool")

        return Cell(char_idx=char_idx, fg=color, bg=None)
