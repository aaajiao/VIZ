"""
值噪声 (Value Noise) - play.core/doom_flame.js 风格

基于置换表 (permutation table) 和双线性插值的 2D 值噪声。
用于火焰、云、地形等程序化纹理生成。

用法::

    from viz.procedural.core.noise import ValueNoise

    noise = ValueNoise(seed=42)
    v = noise(1.5, 2.3)    # 返回 0.0 ~ 1.0
    v = noise.fbm(1.5, 2.3, octaves=4)  # 分形布朗运动
"""

import math
import random

from .mathx import smoothstep, mix

__all__ = ["ValueNoise"]


class ValueNoise:
    """
    2D 值噪声生成器

    使用置换表将整数坐标映射到随机值，
    通过 smoothstep 插值在格点之间产生平滑过渡。

    参数:
        seed: 随机种子 (默认 42)
        size: 置换表大小 (默认 256，必须为 2 的幂)

    示例::

        noise = ValueNoise(seed=42)

        # 单次采样
        v = noise(3.5, 7.2)  # 0.0 ~ 1.0

        # 分形噪声 (多八度叠加)
        v = noise.fbm(3.5, 7.2, octaves=4)

        # 湍流 (绝对值折叠)
        v = noise.turbulence(3.5, 7.2, octaves=4)
    """

    def __init__(self, seed=42, size=256):
        self._size = size
        self._mask = size - 1

        # 生成置换表 (0..255 的随机排列)
        rng = random.Random(seed)
        self._perm = list(range(size))
        rng.shuffle(self._perm)
        # 复制一份避免边界问题
        self._perm = self._perm + self._perm

        # 随机值表 (每个格点的值)
        self._values = [rng.random() for _ in range(size)]

    def _hash(self, ix, iy):
        """将 2D 整数坐标哈希到值表索引"""
        return self._perm[(self._perm[ix & self._mask] + iy) & self._mask] & self._mask

    def __call__(self, x, y):
        """
        采样 2D 值噪声

        返回 [0.0, 1.0] 范围的平滑噪声值。

        参数:
            x: x 坐标 (浮点数)
            y: y 坐标 (浮点数)
        """
        # 整数部分 (格点坐标)
        ix = int(math.floor(x))
        iy = int(math.floor(y))

        # 小数部分 (格点内偏移)
        fx = x - ix
        fy = y - iy

        # smoothstep 插值权重 (比线性插值更平滑)
        sx = smoothstep(0.0, 1.0, fx)
        sy = smoothstep(0.0, 1.0, fy)

        # 四个格点的值
        v00 = self._values[self._hash(ix, iy)]
        v10 = self._values[self._hash(ix + 1, iy)]
        v01 = self._values[self._hash(ix, iy + 1)]
        v11 = self._values[self._hash(ix + 1, iy + 1)]

        # 双线性插值
        top = mix(v00, v10, sx)
        bottom = mix(v01, v11, sx)
        return mix(top, bottom, sy)

    def fbm(self, x, y, octaves=4, lacunarity=2.0, gain=0.5):
        """
        分形布朗运动 (Fractal Brownian Motion)

        多个不同频率和振幅的噪声叠加，产生更自然的纹理。

        fbm(x, y, octaves=1)  → 基础噪声
        fbm(x, y, octaves=6)  → 丰富细节的噪声

        参数:
            x, y: 采样坐标
            octaves: 八度数 (层数，默认 4)
            lacunarity: 频率倍增因子 (默认 2.0)
            gain: 振幅衰减因子 (默认 0.5)

        返回:
            [0.0, 1.0] 范围的噪声值 (归一化后)
        """
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_amplitude = 0.0

        for _ in range(octaves):
            value += amplitude * self(x * frequency, y * frequency)
            max_amplitude += amplitude
            amplitude *= gain
            frequency *= lacunarity

        # 归一化到 [0, 1]
        return value / max_amplitude if max_amplitude > 0 else 0.0

    def turbulence(self, x, y, octaves=4, lacunarity=2.0, gain=0.5):
        """
        湍流噪声

        类似 FBM，但对每个八度取绝对值后再叠加，
        产生更尖锐的边缘 (适合火焰、烟雾效果)。

        参数:
            x, y: 采样坐标
            octaves: 八度数 (默认 4)
            lacunarity: 频率倍增因子 (默认 2.0)
            gain: 振幅衰减因子 (默认 0.5)

        返回:
            [0.0, 1.0] 范围的噪声值
        """
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_amplitude = 0.0

        for _ in range(octaves):
            # 将噪声映射到 [-1, 1] 后取绝对值
            n = self(x * frequency, y * frequency) * 2.0 - 1.0
            value += amplitude * abs(n)
            max_amplitude += amplitude
            amplitude *= gain
            frequency *= lacunarity

        return value / max_amplitude if max_amplitude > 0 else 0.0
