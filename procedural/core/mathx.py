"""
GLSL 风格数学函数 - play.core/num.js 移植

提供 clamp, mix, smoothstep, map_range 等着色器常用数学工具。
纯 Python 实现，无 NumPy 依赖。

用法::

    from viz.procedural.core.mathx import clamp, mix, smoothstep, map_range, fract

    smoothstep(0, 1, 0.5)       # ~0.5 (平滑插值)
    map_range(50, 0, 100, 0, 1) # 0.5  (范围映射)
    fract(3.7)                  # 0.7  (小数部分)
"""

import math

__all__ = [
    "clamp",
    "mix",
    "smoothstep",
    "smootherstep",
    "map_range",
    "fract",
    "sign",
    "step",
    "pulse",
    "mod",
    "PI",
    "TAU",
    "HALF_PI",
]

# --- 常量 ---

PI = math.pi
"""圆周率 π ≈ 3.14159"""

TAU = math.pi * 2.0
"""2π ≈ 6.28318 (完整圆)"""

HALF_PI = math.pi * 0.5
"""π/2 ≈ 1.5708 (直角)"""


# --- 核心函数 ---


def clamp(value, min_val=0.0, max_val=1.0):
    """
    限制值在 [min_val, max_val] 范围内

    clamp(1.5, 0, 1)   → 1.0
    clamp(-0.3, 0, 1)  → 0.0
    clamp(0.5, 0, 1)   → 0.5

    参数:
        value: 输入值
        min_val: 下界 (默认 0.0)
        max_val: 上界 (默认 1.0)
    """
    return max(min_val, min(max_val, value))


def mix(a, b, t):
    """
    线性插值 (GLSL mix / lerp)

    mix(0, 10, 0.5)   → 5.0
    mix(0, 10, 0.0)   → 0.0
    mix(0, 10, 1.0)   → 10.0

    参数:
        a: 起始值
        b: 终止值
        t: 插值因子 (0.0 = a, 1.0 = b)
    """
    return a * (1.0 - t) + b * t


def smoothstep(edge0, edge1, x):
    """
    Hermite 平滑插值 (GLSL smoothstep)

    在 edge0 和 edge1 之间产生平滑的 S 曲线过渡。
    边缘处导数为 0，比线性插值更自然。

    smoothstep(0, 1, 0.0)  → 0.0
    smoothstep(0, 1, 0.5)  → 0.5
    smoothstep(0, 1, 1.0)  → 1.0
    smoothstep(0, 1, 0.25) → ~0.156 (非线性)

    参数:
        edge0: 下边缘
        edge1: 上边缘
        x: 输入值
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smootherstep(edge0, edge1, x):
    """
    Ken Perlin 改进版 smoothstep

    比 smoothstep 更平滑，一阶和二阶导数在边缘都为 0。
    适合高质量噪声生成。

    参数:
        edge0: 下边缘
        edge1: 上边缘
        x: 输入值
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def map_range(value, in_min, in_max, out_min, out_max):
    """
    范围映射 (play.core 的 map() 函数)

    将值从一个范围线性映射到另一个范围。

    map_range(50, 0, 100, 0, 1)      → 0.5
    map_range(0.5, 0, 1, -100, 100)  → 0.0
    map_range(75, 0, 100, 0, 255)    → 191.25

    参数:
        value: 输入值
        in_min: 输入范围下界
        in_max: 输入范围上界
        out_min: 输出范围下界
        out_max: 输出范围上界
    """
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)


def fract(x):
    """
    小数部分 (GLSL fract)

    fract(3.7)   → 0.7
    fract(-0.3)  → 0.7  (始终非负，等同于 x - floor(x))
    fract(1.0)   → 0.0
    """
    return x - math.floor(x)


def sign(x):
    """
    符号函数 (GLSL sign)

    sign(5)    → 1.0
    sign(-3)   → -1.0
    sign(0)    → 0.0
    """
    if x > 0:
        return 1.0
    elif x < 0:
        return -1.0
    return 0.0


def step(edge, x):
    """
    阶跃函数 (GLSL step)

    step(0.5, 0.3)  → 0.0  (x < edge)
    step(0.5, 0.7)  → 1.0  (x >= edge)
    step(0.5, 0.5)  → 1.0
    """
    return 1.0 if x >= edge else 0.0


def pulse(edge0, edge1, x):
    """
    脉冲函数 - 在 [edge0, edge1] 范围内为 1，其余为 0

    pulse(0.3, 0.7, 0.5)  → 1.0
    pulse(0.3, 0.7, 0.1)  → 0.0

    等价于 step(edge0, x) - step(edge1, x)
    """
    return step(edge0, x) - step(edge1, x)


def mod(x, y):
    """
    取模 (GLSL mod，行为与 Python % 一致)

    mod(5.5, 3.0)  → 2.5
    mod(-1.5, 3.0) → 1.5
    """
    return x - y * math.floor(x / y)
