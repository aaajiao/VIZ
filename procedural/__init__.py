"""
Procedural Visualization System - 程序化可视化系统

基于 play.core 数学原语的 ASCII 艺术生成框架。
提供类型系统、参数化、效果引擎和渲染管线。

Public API::

    from procedural import Context, Cell, Buffer, Effect
    from procedural import ParamSpec, resolve_params, create_rng
    from procedural.core import Vec2, noise2d, plasma, sdf_circle

核心概念:
- Context: 渲染上下文 (尺寸、时间、随机种子、参数)
- Cell: 单个字符单元 (字符索引、前景色、背景色)
- Buffer: 2D 字符缓冲区 (list[list[Cell]])
- Effect: 效果协议 (pre/main/post 三阶段渲染)
- ParamSpec: 参数规格 (名称、范围、分布)
"""

# 类型系统
from procedural.types import Context, Cell, Buffer, Effect

# 参数化框架
from procedural.params import ParamSpec, resolve_params, create_rng

# 引擎
from procedural.engine import Engine

__all__ = [
    # Types
    "Context",
    "Cell",
    "Buffer",
    "Effect",
    # Params
    "ParamSpec",
    "resolve_params",
    "create_rng",
    # Engine
    "Engine",
]

__version__ = "0.1.0"
