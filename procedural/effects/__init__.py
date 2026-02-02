"""
效果注册系统 - Effect Registry System

提供效果注册表和查找机制，用于动态加载和管理程序化效果。

用法::

    from procedural.effects import EFFECT_REGISTRY, get_effect

    # 获取效果实例
    plasma = get_effect('plasma')

    # 列出所有可用效果
    print(EFFECT_REGISTRY.keys())
"""

__all__ = [
    "EFFECT_REGISTRY",
    "get_effect",
]

# ==================== 效果注册表 ====================

EFFECT_REGISTRY = {}
"""
全局效果注册表 - Global Effect Registry

存储所有已注册的效果类/函数。

结构::

    {
        'plasma': PlasmaEffect,
        'flame': FlameEffect,
        'wave': WaveEffect,
        ...
    }
"""


# ==================== 核心函数 ====================


def get_effect(name):
    """
    获取效果实例

    Args:
        name: 效果名称 (如 'plasma', 'flame', 'wave')

    Returns:
        效果实例 (实现 Effect Protocol)

    Raises:
        KeyError: 如果效果未注册

    示例::

        plasma = get_effect('plasma')
        state = plasma.pre(ctx, buffer)
        cell = plasma.main(x, y, ctx, state)
    """
    if name not in EFFECT_REGISTRY:
        available = ", ".join(EFFECT_REGISTRY.keys())
        raise KeyError(f"Effect '{name}' not found. Available effects: {available}")

    effect_class = EFFECT_REGISTRY[name]
    return effect_class()


# ==================== 自动导入已注册效果 ====================

# 导入所有效果模块以触发注册
try:
    from .plasma import PlasmaEffect

    EFFECT_REGISTRY["plasma"] = PlasmaEffect
except ImportError:
    pass

try:
    from .flame import DoomFlameEffect

    EFFECT_REGISTRY["flame"] = DoomFlameEffect
except ImportError:
    pass

try:
    from .sdf_shapes import SDFShapesEffect

    EFFECT_REGISTRY["sdf_shapes"] = SDFShapesEffect
except ImportError:
    pass

try:
    from .noise_field import NoiseFieldEffect

    EFFECT_REGISTRY["noise_field"] = NoiseFieldEffect
except ImportError:
    pass

try:
    from .wave import WaveEffect

    EFFECT_REGISTRY["wave"] = WaveEffect
except ImportError:
    pass

try:
    from .moire import MoireEffect

    EFFECT_REGISTRY["moire"] = MoireEffect
except ImportError:
    pass
