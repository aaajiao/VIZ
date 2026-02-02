"""
viz.procedural.core - 数学原语模块

play.core 风格的数学工具：向量运算、噪声、距离场、插值函数。
纯 Python 实现，无外部依赖。

用法::

    # 向量
    from viz.procedural.core.vec import Vec2, length, normalize, rotate, dot

    # 数学
    from viz.procedural.core.mathx import clamp, mix, smoothstep, map_range

    # 噪声
    from viz.procedural.core.noise import ValueNoise

    # 距离场
    from viz.procedural.core.sdf import sd_circle, sd_box, op_smooth_union

    # 或者一次性导入全部
    from viz.procedural.core import *
"""

# vec.py - 2D 向量
from .vec import (
    Vec2,
    vec2,
    add,
    sub,
    mul,
    div,
    length,
    length_sq,
    normalize,
    rotate,
    dot,
    cross,
    dist,
    reflect,
    mix_vec,
)

# mathx.py - GLSL 风格数学
from .mathx import (
    clamp,
    mix,
    smoothstep,
    smootherstep,
    map_range,
    fract,
    sign,
    step,
    pulse,
    mod,
    PI,
    TAU,
    HALF_PI,
)

# noise.py - 值噪声
from .noise import ValueNoise

# sdf.py - 有符号距离场
from .sdf import (
    sd_circle,
    sd_box,
    sd_line,
    sd_ring,
    op_union,
    op_intersection,
    op_subtraction,
    op_smooth_union,
    op_smooth_subtraction,
    op_smooth_intersection,
)

__all__ = [
    # vec
    "Vec2",
    "vec2",
    "add",
    "sub",
    "mul",
    "div",
    "length",
    "length_sq",
    "normalize",
    "rotate",
    "dot",
    "cross",
    "dist",
    "reflect",
    "mix_vec",
    # mathx
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
    # noise
    "ValueNoise",
    # sdf
    "sd_circle",
    "sd_box",
    "sd_line",
    "sd_ring",
    "op_union",
    "op_intersection",
    "op_subtraction",
    "op_smooth_union",
    "op_smooth_subtraction",
    "op_smooth_intersection",
]
