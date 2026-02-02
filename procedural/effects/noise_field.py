"""
噪声场效果 - Noise Field Effect

纯 Perlin/Value 噪声可视化，展示噪声的原始形态。

原理:
    直接可视化 ValueNoise 生成的噪声场，可选择使用 FBM (分形布朗运动)
    叠加多个八度 (octaves) 产生更丰富的细节。
    噪声值直接映射到字符密度和颜色。

算法:
    1. 对每个像素，计算归一化坐标
    2. 使用 ValueNoise 采样噪声值
    3. 可选：使用 FBM 叠加多个八度
    4. 噪声值 (0-1) 映射到字符和颜色

参考:
    - play.core/doom_flame.js - ValueNoise 实现
    - Perlin Noise 经典论文

用法::

    from procedural.effects import get_effect

    noise = get_effect('noise_field')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={
            'scale': 0.05,
            'octaves': 4,
            'lacunarity': 2.0,
            'gain': 0.5,
            'animate': True,
            'speed': 0.5,
        }
    )

    state = noise.pre(ctx, buffer)
    cell = noise.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.noise import ValueNoise
from procedural.core.mathx import clamp
from procedural.palette import value_to_color
from .base import BaseEffect

__all__ = ["NoiseFieldEffect"]


class NoiseFieldEffect(BaseEffect):
    """
    噪声场效果 - 纯噪声可视化

    直接展示 ValueNoise 生成的噪声场，支持 FBM 多八度叠加。

    参数 (从 ctx.params 读取):
        scale: 噪声缩放 (默认 0.05, 范围 0.01-0.2，越小越密集)
        octaves: FBM 八度数 (默认 4, 范围 1-8，1=基础噪声)
        lacunarity: 频率倍增因子 (默认 2.0, 范围 1.5-3.0)
        gain: 振幅衰减因子 (默认 0.5, 范围 0.3-0.8)
        animate: 是否动画 (默认 True)
        speed: 动画速度 (默认 0.5, 范围 0.1-5.0)
        turbulence: 是否使用湍流模式 (默认 False)

    参数范围说明:
        - scale: 0.01 (密集) 到 0.2 (稀疏)
        - octaves: 1 (简单) 到 8 (复杂细节)
        - lacunarity: 1.5 (平缓) 到 3.0 (快速频率增长)
        - gain: 0.3 (快速衰减) 到 0.8 (缓慢衰减)
        - speed: 0.1 (缓慢) 到 5.0 (快速)

    示例::

        # 基础噪声
        ctx.params = {
            'scale': 0.08,
            'octaves': 1,
            'animate': False,
        }

        # 丰富细节的 FBM
        ctx.params = {
            'scale': 0.05,
            'octaves': 6,
            'lacunarity': 2.0,
            'gain': 0.5,
            'animate': True,
        }

        # 湍流效果 (火焰/烟雾)
        ctx.params = {
            'scale': 0.05,
            'octaves': 4,
            'turbulence': True,
            'animate': True,
        }
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 初始化噪声生成器

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - noise: ValueNoise 实例
                - scale: 噪声缩放
                - octaves: 八度数
                - lacunarity: 频率倍增因子
                - gain: 振幅衰减因子
                - animate: 是否动画
                - speed: 动画速度
                - turbulence: 是否湍流模式
        """
        # 提取参数
        scale = ctx.params.get("scale", 0.05)
        octaves = ctx.params.get("octaves", 4)
        lacunarity = ctx.params.get("lacunarity", 2.0)
        gain = ctx.params.get("gain", 0.5)
        animate = ctx.params.get("animate", True)
        speed = ctx.params.get("speed", 0.5)
        turbulence = ctx.params.get("turbulence", False)

        # 初始化噪声生成器
        noise = ValueNoise(seed=ctx.seed)

        return {
            "noise": noise,
            "scale": scale,
            "octaves": octaves,
            "lacunarity": lacunarity,
            "gain": gain,
            "animate": animate,
            "speed": speed,
            "turbulence": turbulence,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 采样噪声值并映射到字符和颜色

        算法:
            1. 归一化坐标
            2. 应用缩放和时间偏移
            3. 采样噪声 (单次或 FBM)
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
        noise = state["noise"]
        scale = state["scale"]
        octaves = state["octaves"]
        lacunarity = state["lacunarity"]
        gain = state["gain"]
        animate = state["animate"]
        speed = state["speed"]
        turbulence = state["turbulence"]

        # 归一化坐标 (0-1)
        u = x / ctx.width
        v = y / ctx.height

        # 宽高比校正
        aspect = ctx.width / ctx.height if ctx.height > 0 else 1.0
        u *= aspect

        # 时间参数 (用于动画)
        t = ctx.time * speed if animate else 0.0

        # === 噪声采样 ===
        # 应用缩放和时间偏移
        nx = u / scale + t
        ny = v / scale

        # 根据八度数选择采样方式
        if octaves == 1:
            # 单次采样 (基础噪声)
            value = noise(nx, ny)
        elif turbulence:
            # 湍流模式 (适合火焰/烟雾)
            value = noise.turbulence(nx, ny, octaves, lacunarity, gain)
        else:
            # FBM 模式 (分形布朗运动)
            value = noise.fbm(nx, ny, octaves, lacunarity, gain)

        # 确保值在 [0, 1] 范围
        value = clamp(value, 0.0, 1.0)

        # === 映射到字符 ===
        # 使用 10 级字符梯度 (0-9)
        char_idx = int(value * 9)
        char_idx = clamp(char_idx, 0, 9)

        # === 映射到颜色 ===
        # 根据模式选择颜色方案
        if turbulence:
            # 湍流模式使用火焰色
            color_scheme = "fire"
        else:
            # 普通模式使用 plasma 色
            color_scheme = "plasma"

        # 添加时间相位偏移
        color_value = (value + t * 0.05) % 1.0
        color = value_to_color(color_value, color_scheme)

        # 返回 Cell
        return Cell(
            char_idx=char_idx,
            fg=color,
            bg=None,  # 透明背景
        )

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理 - 噪声场不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # 无需后处理
