"""
噪声调制器 - Noise Modulator

用噪声函数让参数随时间和空间平滑漂移，
使每一帧都产生微妙变化，避免静态重复。

核心概念::

    - 每个参数被一个 NoiseModulator 包裹
    - 调制器输出 = base_value + amplitude * noise(t * frequency)
    - 支持时间调制 (参数随时间变化) 和空间调制 (参数随位置变化)
    - 支持 domain warping (用噪声扭曲噪声坐标，产生有机变形)

用法::

    from procedural.flexible.modulator import NoiseModulator, ModulatedParams

    # 单参数调制
    mod = NoiseModulator(base=0.5, amplitude=0.2, frequency=0.1, seed=42)
    value = mod.sample(t=1.5)
    # value 在 0.3 ~ 0.7 之间平滑变化

    # 批量参数调制
    mp = ModulatedParams(seed=42)
    mp.add("frequency", base=0.05, amplitude=0.03, speed=0.2)
    mp.add("speed", base=1.0, amplitude=0.5, speed=0.1)
    params = mp.sample(t=1.5)
    # → {"frequency": 0.062, "speed": 1.23}
"""

from __future__ import annotations

import math
import random

from procedural.core.noise import ValueNoise
from procedural.core.mathx import clamp


class NoiseModulator:
    """
    单参数噪声调制器

    将一个基础值用噪声函数调制，产生平滑的时间变化。

    属性:
        base: 基础值 (中心值)
        amplitude: 调制幅度 (最大偏移量)
        frequency: 噪声频率 (变化速率)
        min_val: 输出下限 (可选)
        max_val: 输出上限 (可选)
    """

    def __init__(
        self,
        base: float = 0.5,
        amplitude: float = 0.1,
        frequency: float = 0.1,
        seed: int = 42,
        min_val: float | None = None,
        max_val: float | None = None,
    ):
        self.base = base
        self.amplitude = amplitude
        self.frequency = frequency
        self.min_val = min_val
        self.max_val = max_val
        self._noise = ValueNoise(seed=seed)
        self._offset = random.Random(seed).random() * 1000.0

    def sample(self, t: float) -> float:
        """
        在时间 t 采样调制后的值

        使用 fbm 获得更丰富的噪声层次。

        参数:
            t: 时间 (秒)

        返回:
            调制后的值
        """
        n = self._noise.fbm(
            (t + self._offset) * self.frequency,
            self._offset,
            octaves=3,
        )
        # n 在 [0, 1] 范围，映射到 [-1, 1]
        deviation = (n * 2.0 - 1.0) * self.amplitude
        result = self.base + deviation

        if self.min_val is not None:
            result = max(self.min_val, result)
        if self.max_val is not None:
            result = min(self.max_val, result)

        return result

    def sample_2d(self, x: float, y: float, t: float) -> float:
        """
        空间 + 时间调制 (用于每像素调制)

        包含 domain warping: 用一层噪声扭曲采样坐标，
        产生有机的空间变形效果。

        参数:
            x: X 坐标 (归一化 0-1)
            y: Y 坐标 (归一化 0-1)
            t: 时间

        返回:
            调制后的值
        """
        freq = self.frequency
        offset = self._offset

        # Domain warping: 用噪声扭曲坐标
        warp_x = self._noise(x * 0.3 + offset, t * 0.05) * 2.0
        warp_y = self._noise(y * 0.3 + offset + 100, t * 0.05) * 2.0

        n = self._noise.fbm(
            (x + warp_x) * freq,
            (y + warp_y) * freq + t * 0.1,
            octaves=4,
        )

        deviation = (n * 2.0 - 1.0) * self.amplitude
        result = self.base + deviation

        if self.min_val is not None:
            result = max(self.min_val, result)
        if self.max_val is not None:
            result = min(self.max_val, result)

        return result


class ModulatedParams:
    """
    批量参数调制器

    管理多个参数的噪声调制，一次调用获取所有调制后的参数值。

    用法::

        mp = ModulatedParams(seed=42)
        mp.add("frequency", base=0.05, amplitude=0.03, speed=0.2)
        mp.add("speed", base=1.0, amplitude=0.5, speed=0.1)

        # 获取 t=1.5 时的所有参数
        params = mp.sample(t=1.5)
        # → {"frequency": 0.062, "speed": 1.23}
    """

    def __init__(self, seed: int = 42):
        self._modulators: dict[str, NoiseModulator] = {}
        self._seed = seed
        self._next_seed = seed

    def add(
        self,
        name: str,
        base: float,
        amplitude: float = 0.0,
        speed: float = 0.1,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> ModulatedParams:
        """
        添加一个被调制的参数

        参数:
            name: 参数名
            base: 基础值
            amplitude: 调制幅度 (0=不调制)
            speed: 变化速率
            min_val: 下限
            max_val: 上限

        返回:
            self (链式调用)
        """
        self._next_seed += 1
        self._modulators[name] = NoiseModulator(
            base=base,
            amplitude=amplitude,
            frequency=speed,
            seed=self._next_seed,
            min_val=min_val,
            max_val=max_val,
        )
        return self

    def sample(self, t: float) -> dict[str, float]:
        """
        采样所有参数在时间 t 的调制值

        参数:
            t: 时间 (秒)

        返回:
            {name: modulated_value} 字典
        """
        return {name: mod.sample(t) for name, mod in self._modulators.items()}

    def sample_static(self) -> dict[str, float]:
        """
        获取所有参数的基础值 (不调制)

        用于需要固定参数的场景。

        返回:
            {name: base_value} 字典
        """
        return {name: mod.base for name, mod in self._modulators.items()}


def modulate_visual_params(
    params: dict,
    t: float,
    drift_amount: float = 0.3,
    seed: int = 42,
) -> dict:
    """
    对视觉参数字典进行噪声调制

    对 EmotionVector.to_visual_params() 的输出进行时间调制，
    使参数随时间缓慢漂移。

    参数:
        params: 原始参数字典
        t: 时间
        drift_amount: 漂移强度 (0=无漂移, 1=最大漂移)
        seed: 种子

    返回:
        调制后的参数字典
    """
    noise = ValueNoise(seed=seed)
    result = {}
    offset = 0

    for key, value in params.items():
        if isinstance(value, (int, float)):
            offset += 1
            n = noise.fbm(t * 0.1 + offset * 7.3, offset * 13.7, octaves=2)
            deviation = (n * 2.0 - 1.0) * drift_amount

            if isinstance(value, int):
                # 整数参数: 小幅波动后取整
                modulated = value + deviation * max(1, abs(value) * 0.3)
                result[key] = max(1, int(round(modulated)))
            else:
                # 浮点参数: 按比例调制
                modulated = value + deviation * abs(value) * 0.5
                # 保持合理范围
                if 0.0 <= value <= 1.0:
                    modulated = clamp(modulated, 0.0, 1.0)
                elif value >= 0:
                    modulated = max(0.0, modulated)
                result[key] = modulated
        else:
            result[key] = value

    return result
