"""
ASCII 梯度和颜色映射 - play.core/palette.js 移植

提供多种 ASCII 字符密度梯度和颜色方案，用于将数值映射到字符和颜色。

用法::

    from viz.procedural.palette import char_at_value, value_to_color

    # 获取 ASCII 字符
    char = char_at_value(0.5, 'classic')  # 返回中等密度字符

    # 获取 RGB 颜色
    color = value_to_color(0.5, 'heat')   # 返回 (r, g, b) 元组
"""

import math
from .core.mathx import clamp

__all__ = [
    "ASCII_GRADIENTS",
    "COLOR_SCHEMES",
    "char_at_value",
    "value_to_color",
]

# ==================== ASCII 梯度定义 ====================

ASCII_GRADIENTS = {
    "classic": " .:-=+*#%@",
    "blocks": " ░▒▓█",
    "smooth": " .':;!>+*%@#█",
    "matrix": " .:-=+*@#",
    "plasma": "$?01▄abc+-><:.",
    "default": " .:-=+*#%@",  # 别名
}

# ==================== 颜色方案定义 ====================

COLOR_SCHEMES = {
    "heat": "heat",
    "rainbow": "rainbow",
    "cool": "cool",
    "matrix": "matrix",
    "plasma": "plasma",
}


# ==================== 核心函数 ====================


def char_at_value(value, gradient_name="default"):
    """
    将 0-1 范围的值映射到 ASCII 字符

    Args:
        value: 0.0 到 1.0 之间的浮点数
        gradient_name: 梯度名称 ('classic', 'blocks', 'smooth', 'matrix', 'plasma', 'default')

    Returns:
        str: 单个 ASCII 字符

    示例::

        char_at_value(0.0, 'classic')   # ' ' (最稀疏)
        char_at_value(0.5, 'classic')   # '*' (中等)
        char_at_value(1.0, 'classic')   # '@' (最密集)
    """
    # 获取梯度字符串
    gradient = ASCII_GRADIENTS.get(gradient_name, ASCII_GRADIENTS["default"])

    # 将值限制在 0-1 范围内
    value = clamp(value, 0.0, 1.0)

    # 映射到字符索引
    char_idx = int(value * (len(gradient) - 1))
    char_idx = int(clamp(char_idx, 0, len(gradient) - 1))

    return gradient[char_idx]


def value_to_color(value, color_scheme="heat"):
    """
    将 0-1 范围的值映射到 RGB 颜色元组

    Args:
        value: 0.0 到 1.0 之间的浮点数
        color_scheme: 颜色方案名称 ('heat', 'rainbow', 'cool', 'matrix', 'plasma')

    Returns:
        tuple: (r, g, b) 元组，每个分量 0-255

    示例::

        value_to_color(0.0, 'heat')     # (0, 0, 0) 黑色
        value_to_color(0.5, 'heat')     # (255, 128, 0) 橙色
        value_to_color(1.0, 'heat')     # (255, 255, 255) 白色
    """
    value = clamp(value, 0.0, 1.0)

    if color_scheme == "heat":
        return _heat_to_color(value)
    elif color_scheme == "rainbow":
        return _rainbow_to_color(value)
    elif color_scheme == "cool":
        return _cool_to_color(value)
    elif color_scheme == "matrix":
        return _matrix_to_color(value)
    elif color_scheme == "plasma":
        return _plasma_to_color(value)
    else:
        return _heat_to_color(value)  # 默认热力图


# ==================== 颜色映射实现 ====================


def _heat_to_color(t):
    """
    热力图颜色映射：黑 → 深红 → 红 → 橙 → 黄 → 白

    Args:
        t: 0.0 到 1.0 的值

    Returns:
        tuple: (r, g, b)
    """
    if t < 0.25:
        # 黑 → 深红
        r = int(t * 4 * 180)
        return (r, 0, 0)
    elif t < 0.5:
        # 深红 → 红
        r = 180 + int((t - 0.25) * 4 * 75)
        return (r, 0, 0)
    elif t < 0.75:
        # 红 → 橙
        g = int((t - 0.5) * 4 * 165)
        return (255, g, 0)
    else:
        # 橙 → 黄 → 白
        b = int((t - 0.75) * 4 * 255)
        return (255, 255, b)


def _rainbow_to_color(t):
    """
    彩虹色映射：HSV 色相循环 (S=1, V=1)

    Args:
        t: 0.0 到 1.0 的值

    Returns:
        tuple: (r, g, b)
    """
    h = t % 1.0
    i = int(h * 6)
    f = h * 6 - i

    r, g, b = 0, 0, 0

    if i == 0:
        r, g, b = 1, f, 0
    elif i == 1:
        r, g, b = 1 - f, 1, 0
    elif i == 2:
        r, g, b = 0, 1, f
    elif i == 3:
        r, g, b = 0, 1 - f, 1
    elif i == 4:
        r, g, b = f, 0, 1
    else:
        r, g, b = 1, 0, 1 - f

    return (int(r * 255), int(g * 255), int(b * 255))


def _cool_to_color(t):
    """
    冷色映射：蓝 → 青 → 白

    Args:
        t: 0.0 到 1.0 的值

    Returns:
        tuple: (r, g, b)
    """
    if t < 0.5:
        # 蓝 → 青
        g = int(t * 2 * 255)
        return (0, g, 255)
    else:
        # 青 → 白
        r = int((t - 0.5) * 2 * 255)
        return (r, 255, 255)


def _matrix_to_color(t):
    """
    矩阵绿色映射：黑 → 深绿 → 亮绿

    Args:
        t: 0.0 到 1.0 的值

    Returns:
        tuple: (r, g, b)
    """
    if t < 0.5:
        # 黑 → 深绿
        g = int(t * 2 * 128)
        return (0, g, 0)
    else:
        # 深绿 → 亮绿
        g = 128 + int((t - 0.5) * 2 * 127)
        return (0, g, 0)


def _plasma_to_color(t):
    """
    等离子体彩虹映射：多彩渐变

    结合热力图和彩虹色的混合效果

    Args:
        t: 0.0 到 1.0 的值

    Returns:
        tuple: (r, g, b)
    """
    # 使用 HSV 色相但增加饱和度变化
    h = t % 1.0
    s = 1.0
    v = 0.5 + 0.5 * math.sin(t * math.pi)  # 亮度脉动

    i = int(h * 6)
    f = h * 6 - i

    p = v * (1 - s)
    q = v * (1 - f * s)
    t_hsv = v * (1 - (1 - f) * s)

    if i == 0:
        r, g, b = v, t_hsv, p
    elif i == 1:
        r, g, b = q, v, p
    elif i == 2:
        r, g, b = p, v, t_hsv
    elif i == 3:
        r, g, b = p, q, v
    elif i == 4:
        r, g, b = t_hsv, p, v
    else:
        r, g, b = v, p, q

    return (int(r * 255), int(g * 255), int(b * 255))
