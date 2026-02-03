"""
CPPN 效果 - Compositional Pattern Producing Network

用随机权重的小型神经网络将 (x, y) 映射到 (char_idx, r, g, b)，
每个不同的种子 (权重初始化) 产生完全不同的视觉图案。

特性::

    - 无需训练: 随机权重即可产生丰富的抽象图案
    - 无限分辨率: 函数式，可在任意分辨率采样
    - 极高多样性: 每个种子产生独特的视觉
    - 可插值: 两组权重之间可 SLERP 平滑过渡
    - 多种激活函数: sin/cos/tanh/abs/gaussian 产生不同美学

算法::

    inputs = [x_norm, y_norm, radius, bias, time_sin, time_cos]
    for layer in hidden_layers:
        outputs = [activation(dot(weights, inputs)) for each neuron]
        inputs = outputs
    [char, r, g, b] = tanh(dot(output_weights, inputs))

参考:
    - Stanley (2007): "Compositional Pattern Producing Networks"
    - hardmaru/cppn-tensorflow
    - neale/CPPN (PyTorch)

用法::

    from procedural.flexible.cppn import CPPNEffect

    effect = CPPNEffect(seed=42, num_hidden=3, layer_size=8)
    # 直接作为 Effect Protocol 使用
    state = effect.pre(ctx, buffer)
    cell = effect.main(x, y, ctx, state)
"""

from __future__ import annotations

import math
import random

from procedural.types import Context, Cell, Buffer
from procedural.effects.base import BaseEffect
from procedural.core.mathx import clamp


# === 激活函数库 ===

def _sin(x: float) -> float:
    return math.sin(x)

def _cos(x: float) -> float:
    return math.cos(x)

def _tanh(x: float) -> float:
    return math.tanh(x)

def _abs(x: float) -> float:
    return abs(x)

def _identity(x: float) -> float:
    return x

def _gaussian(x: float) -> float:
    return math.exp(-x * x)

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-clamp(x, -10.0, 10.0)))

def _softplus(x: float) -> float:
    return math.log(1.0 + math.exp(clamp(x, -10.0, 10.0)))

def _sin_abs(x: float) -> float:
    """sin(|x|) - 产生对称的波纹"""
    return math.sin(abs(x))

ACTIVATIONS = [_sin, _cos, _tanh, _abs, _identity, _gaussian, _sigmoid, _sin_abs]


class CPPNEffect(BaseEffect):
    """
    CPPN 程序化图案效果

    每个实例 (不同种子) 产生独特的视觉图案。
    实现 Effect Protocol (pre/main/post)。

    参数 (构造时):
        seed: 随机种子 (决定网络权重 → 决定视觉图案)
        num_hidden: 隐藏层数 (2-5, 更多=更复杂)
        layer_size: 每层神经元数 (4-16, 更多=更精细)
        use_radial: 是否包含径向对称输入 (True 产生更多圆形图案)
        use_time: 是否包含时间输入 (True 产生动画)
        color_mode: 颜色模式 ('rgb'=直接RGB, 'hsv'=HSV空间)

    参数 (从 ctx.params):
        warmth: 色温调制 (0-1)
        saturation: 饱和度调制 (0-1)
    """

    def __init__(
        self,
        seed: int = 42,
        num_hidden: int = 3,
        layer_size: int = 8,
        use_radial: bool = True,
        use_time: bool = True,
        color_mode: str = "hsv",
    ):
        self.seed = seed
        self.num_hidden = num_hidden
        self.layer_size = layer_size
        self.use_radial = use_radial
        self.use_time = use_time
        self.color_mode = color_mode

        self._build_network(seed)

    def _build_network(self, seed: int):
        """构建随机权重网络"""
        rng = random.Random(seed)

        # 输入维度: x, y, [radius], bias, [time_sin, time_cos]
        in_size = 2 + int(self.use_radial) + 1 + 2 * int(self.use_time)

        self.layers: list[tuple[list[list[float]], callable]] = []

        for _ in range(self.num_hidden):
            out_size = self.layer_size
            # Xavier 初始化
            scale = math.sqrt(2.0 / (in_size + out_size))
            weights = [
                [rng.gauss(0, scale) for _ in range(in_size)]
                for _ in range(out_size)
            ]
            activation = rng.choice(ACTIVATIONS)
            self.layers.append((weights, activation))
            in_size = out_size

        # 输出层: 4 个输出 (char_value, color1, color2, color3)
        scale = math.sqrt(2.0 / (in_size + 4))
        self.output_weights = [
            [rng.gauss(0, scale) for _ in range(in_size)]
            for _ in range(4)
        ]

    def _forward(self, inputs: list[float]) -> list[float]:
        """前向传播"""
        x = inputs
        for weights, activation in self.layers:
            x = [
                activation(sum(w * v for w, v in zip(row, x)))
                for row in weights
            ]

        # 输出层用 tanh 限制范围到 [-1, 1]
        out = [
            math.tanh(sum(w * v for w, v in zip(row, x)))
            for row in self.output_weights
        ]
        return out

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """预处理: 提取色温/饱和度参数"""
        return {
            "warmth": ctx.params.get("warmth", 0.5),
            "saturation": ctx.params.get("saturation", 1.0),
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染: 对每个像素执行 CPPN 前向传播
        """
        # 归一化坐标到 [-1, 1]
        nx = (x / ctx.width) * 2.0 - 1.0
        ny = (y / ctx.height) * 2.0 - 1.0

        # 构造输入
        inputs = [nx, ny]

        if self.use_radial:
            inputs.append(math.sqrt(nx * nx + ny * ny))

        inputs.append(1.0)  # bias

        if self.use_time:
            inputs.append(math.sin(ctx.time * 0.5))
            inputs.append(math.cos(ctx.time * 0.3))

        # 前向传播
        out = self._forward(inputs)

        # 解码输出
        char_raw = out[0]   # [-1, 1]
        c1_raw = out[1]     # [-1, 1]
        c2_raw = out[2]     # [-1, 1]
        c3_raw = out[3]     # [-1, 1]

        # 字符索引: [-1, 1] → [0, 9]
        char_idx = int((char_raw + 1.0) * 0.5 * 9)
        char_idx = max(0, min(9, char_idx))

        # 颜色
        warmth = state.get("warmth", 0.5)
        saturation = state.get("saturation", 1.0)

        if self.color_mode == "hsv":
            # HSV 模式: c1=hue, c2=sat_mod, c3=value
            hue = (c1_raw + 1.0) * 0.5  # [0, 1]
            # 色温偏移: warmth 高时色相偏红/黄, 低时偏蓝
            hue = (hue * 0.6 + warmth * 0.4) % 1.0

            sat = clamp((c2_raw + 1.0) * 0.5 * saturation, 0.0, 1.0)
            val = clamp((c3_raw + 1.0) * 0.5, 0.1, 1.0)

            import colorsys
            r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
            color = (int(r * 255), int(g * 255), int(b * 255))
        else:
            # RGB 模式: 直接映射
            color = (
                max(0, min(255, int((c1_raw + 1.0) * 0.5 * 255))),
                max(0, min(255, int((c2_raw + 1.0) * 0.5 * 255))),
                max(0, min(255, int((c3_raw + 1.0) * 0.5 * 255))),
            )

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """CPPN 不需要后处理"""
        pass


def interpolate_cppns(
    cppn_a: CPPNEffect,
    cppn_b: CPPNEffect,
    t: float,
) -> CPPNEffect:
    """
    在两个 CPPN 之间插值权重，产生过渡效果

    参数:
        cppn_a: 起始 CPPN
        cppn_b: 目标 CPPN
        t: 插值因子 (0=A, 1=B)

    返回:
        权重被插值的新 CPPNEffect

    注意:
        两个 CPPN 必须有相同的架构 (num_hidden, layer_size)
    """
    if len(cppn_a.layers) != len(cppn_b.layers):
        raise ValueError("CPPNs must have same architecture for interpolation")

    # 创建一个新的 CPPN (复制 A 的结构)
    result = CPPNEffect(
        seed=cppn_a.seed,
        num_hidden=cppn_a.num_hidden,
        layer_size=cppn_a.layer_size,
        use_radial=cppn_a.use_radial,
        use_time=cppn_a.use_time,
        color_mode=cppn_a.color_mode,
    )

    # 插值隐藏层权重
    new_layers = []
    for (wa, act_a), (wb, act_b) in zip(cppn_a.layers, cppn_b.layers):
        new_weights = [
            [wa[i][j] * (1 - t) + wb[i][j] * t
             for j in range(len(wa[i]))]
            for i in range(len(wa))
        ]
        # 选择激活函数: t < 0.5 用 A 的, 否则用 B 的
        act = act_a if t < 0.5 else act_b
        new_layers.append((new_weights, act))

    result.layers = new_layers

    # 插值输出层权重
    result.output_weights = [
        [cppn_a.output_weights[i][j] * (1 - t) + cppn_b.output_weights[i][j] * t
         for j in range(len(cppn_a.output_weights[i]))]
        for i in range(len(cppn_a.output_weights))
    ]

    return result
