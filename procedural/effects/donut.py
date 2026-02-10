"""
旋转甜甜圈效果 - Rotating Donut (Torus) Effect

经典 donut.c 算法适配 ASCII 艺术缓冲区渲染。
通过预计算 z-buffer 和光照缓冲区实现高效逐像素输出。

算法:
    1. pre() 阶段遍历环面参数 (theta, phi)
    2. 计算 3D 表面点并施加旋转变换
    3. 投影到 2D 屏幕空间，维护 z-buffer
    4. 计算表面法线与光源方向的点积得到亮度
    5. main() 阶段查表输出字符和颜色

参数:
    R1: 小半径 (截面半径, 默认 1.0)
    R2: 大半径 (环心距, 默认 2.0)
    rotation_speed: 旋转速度 (默认 1.0)
    light_x, light_y, light_z: 光源方向 (默认 0, 1, -1)
    surface_noise: 表面噪声变形量 (默认 0.0, 范围 0.0-1.0)
    asymmetry_x, asymmetry_y: 非均匀缩放 (默认 1.0, 范围 0.3-2.0)
    twist: 沿环面扭曲截面 (默认 0.0, 范围 0.0-2.0)
    count: 环面数量 (默认 1, 范围 1-3)
    ring_offset: 多环面轨道偏移 (默认 0.3)

用法::

    from procedural.effects import get_effect

    donut = get_effect('donut')
    state = donut.pre(ctx, buffer)
    cell = donut.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.core.noise import ValueNoise
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

try:
    from procedural.core.projection import Vec3, rotate_x, rotate_y, rotate_z, dot3, normalize3
except ImportError:
    from viz.procedural.core.projection import Vec3, rotate_x, rotate_y, rotate_z, dot3, normalize3

__all__ = ["DonutEffect"]

# Torus surface sampling resolution
THETA_STEPS = 90
PHI_STEPS = 40


class DonutEffect(BaseEffect):
    """
    旋转甜甜圈效果 - Rotating Donut (Torus) Effect

    经典 donut.c 算法的 ASCII 缓冲区实现。

    参数 (从 ctx.params 读取):
        R1: 小半径 (默认 1.0, 范围 0.5-3.0)
        R2: 大半径 (默认 2.0, 范围 1.0-5.0)
        rotation_speed: 旋转速度 (默认 1.0, 范围 0.1-5.0)
        light_x, light_y, light_z: 光源方向分量
        surface_noise: 表面噪声量 (默认 0.0)
        asymmetry_x, asymmetry_y: 非均匀缩放 (默认 1.0)
        twist: 截面扭曲 (默认 0.0)
        count: 环面数量 (默认 1)
        ring_offset: 多环面轨道偏移 (默认 0.3)
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 预计算 z-buffer 和亮度缓冲区

        遍历环面参数空间，投影到屏幕并记录每个像素的深度和亮度。
        """
        R1 = ctx.params.get("R1", 1.0)
        R2 = ctx.params.get("R2", 2.0)
        speed = ctx.params.get("rotation_speed", 1.0)

        # 光源方向 (归一化)
        lx = ctx.params.get("light_x", 0.0)
        ly = ctx.params.get("light_y", 1.0)
        lz = ctx.params.get("light_z", -1.0)
        light_dir = normalize3(Vec3(lx, ly, lz))

        # 连续颜色参数
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        # 变形参数 - Deformation params
        surface_noise_amt = ctx.params.get("surface_noise", 0.0)
        asymmetry_x = ctx.params.get("asymmetry_x", 1.0)
        asymmetry_y = ctx.params.get("asymmetry_y", 1.0)
        twist = ctx.params.get("twist", 0.0)
        count = max(1, int(ctx.params.get("count", 1)))
        ring_offset = ctx.params.get("ring_offset", 0.3)

        # 噪声源 (用于表面变形)
        noise_fn = None
        if surface_noise_amt > 0:
            noise_fn = ValueNoise(seed=ctx.seed + 99)

        w = ctx.width
        h = ctx.height

        # 初始化缓冲区
        z_buffer = [[0.0] * w for _ in range(h)]
        lum_buffer = [[0.0] * w for _ in range(h)]

        # 旋转角度 (随时间变化)
        A = ctx.time * speed * 0.8
        B = ctx.time * speed * 0.6

        # 观察距离 (将环面放在合适的位置)
        K2 = 5.0
        # 屏幕缩放因子
        K1 = w * K2 * 3.0 / (8.0 * (R1 + R2))

        theta_step = 2.0 * math.pi / THETA_STEPS
        phi_step = 2.0 * math.pi / PHI_STEPS

        for torus_idx in range(count):
            # 多环面轨道偏移
            if torus_idx > 0:
                torus_angle = torus_idx * (2.0 * math.pi / count) + ctx.time * 0.3
                offset_x = ring_offset * math.cos(torus_angle)
                offset_y = ring_offset * math.sin(torus_angle)
            else:
                offset_x = 0.0
                offset_y = 0.0

            for j in range(THETA_STEPS):
                theta = j * theta_step
                cos_theta = math.cos(theta)
                sin_theta = math.sin(theta)

                for i in range(PHI_STEPS):
                    phi = i * phi_step
                    cos_phi = math.cos(phi)
                    sin_phi = math.sin(phi)

                    # 表面噪声变形
                    local_R1 = R1
                    if noise_fn is not None and surface_noise_amt > 0:
                        noise_val = noise_fn(theta * 3.0, phi * 3.0)
                        local_R1 = R1 + (noise_val - 0.5) * 2.0 * surface_noise_amt * R1

                    # 截面扭曲: 根据 phi 旋转截面
                    if twist > 0:
                        twist_angle = phi * twist
                        ct = math.cos(twist_angle)
                        st = math.sin(twist_angle)
                        deformed_cos = cos_theta * ct - sin_theta * st
                        deformed_sin = cos_theta * st + sin_theta * ct
                    else:
                        deformed_cos = cos_theta
                        deformed_sin = sin_theta

                    # 环面上的圆 (在 xz 平面)
                    circle_x = R2 + local_R1 * deformed_cos
                    circle_y = local_R1 * deformed_sin

                    # 绕 Y 轴旋转 phi 角得到 3D 环面点 + 非均匀缩放
                    px = circle_x * cos_phi * asymmetry_x + offset_x
                    py = circle_y * asymmetry_y + offset_y
                    pz = -circle_x * sin_phi

                    # 表面法线 (环面上的法线方向)
                    nx = deformed_cos * cos_phi
                    ny = deformed_sin
                    nz = -deformed_cos * sin_phi

                    # 施加旋转 A (绕 X), B (绕 Z)
                    p = Vec3(px, py, pz)
                    p = rotate_x(p, A)
                    p = rotate_z(p, B)

                    n = Vec3(nx, ny, nz)
                    n = rotate_x(n, A)
                    n = rotate_z(n, B)

                    # 平移到视点前方
                    p = Vec3(p.x, p.y, p.z + K2)

                    # 深度倒数 (用于 z-buffer)
                    ooz = 1.0 / p.z if p.z > 0.1 else 0.0

                    # 投影到屏幕
                    xp = int(w / 2.0 + K1 * ooz * p.x)
                    yp = int(h / 2.0 - K1 * ooz * p.y)

                    # 光照计算 (法线点积光源方向)
                    luminance = dot3(n, light_dir)

                    # 裁剪到屏幕范围
                    if 0 <= xp < w and 0 <= yp < h:
                        if ooz > z_buffer[yp][xp]:
                            z_buffer[yp][xp] = ooz
                            lum_buffer[yp][xp] = luminance

        return {
            "z_buffer": z_buffer,
            "lum_buffer": lum_buffer,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 查表输出每个像素的字符和颜色
        """
        z_val = state["z_buffer"][y][x]
        lum = state["lum_buffer"][y][x]

        if z_val <= 0.0:
            # 背景 (无环面覆盖)
            return Cell(char_idx=0, fg=(20, 20, 30), bg=None)

        # 亮度映射到 0-1
        value = clamp((lum + 1.0) * 0.5, 0.0, 1.0)

        # 字符索引
        char_idx = int(clamp(value * 9, 0, 9))

        # 颜色映射
        if state["warmth"] is not None:
            color = value_to_color_continuous(
                value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(value, "heat")

        return Cell(char_idx=char_idx, fg=color, bg=None)
