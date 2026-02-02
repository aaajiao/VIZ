"""
有符号距离场 (Signed Distance Functions) - play.core/sdf.js 风格

SDF 是程序化图形的核心技术：每个函数返回点到形状的最短距离。
正值 = 形状外部，负值 = 形状内部，0 = 恰好在边界上。

可通过布尔运算组合多个 SDF 产生复杂形状。

用法::

    from viz.procedural.core.vec import Vec2
    from viz.procedural.core.sdf import sd_circle, sd_box, op_smooth_union

    # 基本形状
    d1 = sd_circle(Vec2(0.5, 0.5), Vec2(0, 0), 1.0)  # 圆
    d2 = sd_box(Vec2(0.5, 0.5), Vec2(2, 0), Vec2(1, 1))  # 矩形

    # 平滑合并
    d = op_smooth_union(d1, d2, 0.3)
"""

import math

from .vec import Vec2, length

__all__ = [
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


# --- 基本形状 ---


def sd_circle(p, center, radius):
    """
    圆形 SDF

    返回点 p 到圆心 center、半径 radius 的圆的有符号距离。

    sd_circle(Vec2(2, 0), Vec2(0, 0), 1.0)  → 1.0  (外部)
    sd_circle(Vec2(0, 0), Vec2(0, 0), 1.0)  → -1.0 (内部)
    sd_circle(Vec2(1, 0), Vec2(0, 0), 1.0)  → 0.0  (边界)

    参数:
        p: 采样点 (Vec2)
        center: 圆心 (Vec2)
        radius: 半径 (float)

    返回:
        有符号距离 (float): 负值=内部, 正值=外部
    """
    return length(p - center) - radius


def sd_box(p, center, half_size):
    """
    矩形 SDF (轴对齐)

    返回点 p 到中心 center、半宽高 half_size 的矩形的有符号距离。

    sd_box(Vec2(2, 0), Vec2(0, 0), Vec2(1, 1))  → 1.0
    sd_box(Vec2(0, 0), Vec2(0, 0), Vec2(1, 1))  → -1.0

    参数:
        p: 采样点 (Vec2)
        center: 矩形中心 (Vec2)
        half_size: 半宽高 (Vec2)

    返回:
        有符号距离 (float)
    """
    d = abs(p - center) - half_size
    # 外部距离: max(d, 0) 的长度
    outside = length(Vec2(max(d.x, 0.0), max(d.y, 0.0)))
    # 内部距离: max 分量 (负值)
    inside = min(max(d.x, d.y), 0.0)
    return outside + inside


def sd_line(p, a, b):
    """
    线段 SDF

    返回点 p 到线段 a→b 的最短距离。

    sd_line(Vec2(0, 1), Vec2(0, 0), Vec2(2, 0))  → 1.0

    参数:
        p: 采样点 (Vec2)
        a: 线段起点 (Vec2)
        b: 线段终点 (Vec2)

    返回:
        无符号距离 (float, 始终 >= 0)
    """
    pa = p - a
    ba = b - a
    # 投影比例，限制在 [0, 1]
    ba_len_sq = ba.x * ba.x + ba.y * ba.y
    if ba_len_sq < 1e-10:
        return length(pa)
    t = max(0.0, min(1.0, (pa.x * ba.x + pa.y * ba.y) / ba_len_sq))
    # 最近点
    closest = Vec2(a.x + t * ba.x, a.y + t * ba.y)
    return length(p - closest)


def sd_ring(p, center, radius, thickness):
    """
    圆环 SDF

    sd_ring(Vec2(1.5, 0), Vec2(0, 0), 1.0, 0.2)

    参数:
        p: 采样点 (Vec2)
        center: 圆心 (Vec2)
        radius: 中心半径 (float)
        thickness: 环宽度 (float)

    返回:
        有符号距离 (float)
    """
    return abs(length(p - center) - radius) - thickness


# --- 布尔运算 ---


def op_union(d1, d2):
    """
    并集 (取最小值)

    op_union(0.5, 0.3)  → 0.3
    """
    return min(d1, d2)


def op_intersection(d1, d2):
    """
    交集 (取最大值)

    op_intersection(0.5, 0.3)  → 0.5
    """
    return max(d1, d2)


def op_subtraction(d1, d2):
    """
    差集 (从 d1 中减去 d2)

    结果是 d1 内部但不在 d2 内部的区域。
    """
    return max(d1, -d2)


# --- 平滑布尔运算 ---


def op_smooth_union(d1, d2, k):
    """
    平滑并集

    在两个形状交界处产生圆滑过渡，而非锐利边缘。
    k 控制平滑程度 (k=0 等同于普通 union)。

    op_smooth_union(0.5, 0.3, 0.1)  # 带圆角的合并

    参数:
        d1: 第一个距离值
        d2: 第二个距离值
        k: 平滑系数 (越大越圆滑，推荐 0.1 ~ 0.5)

    返回:
        平滑合并后的距离值
    """
    if k <= 0.0:
        return min(d1, d2)
    h = max(0.0, min(1.0, 0.5 + 0.5 * (d2 - d1) / k))
    return d2 * (1.0 - h) + d1 * h - k * h * (1.0 - h)


def op_smooth_subtraction(d1, d2, k):
    """
    平滑差集

    从 d1 中平滑地减去 d2，交界处产生圆滑凹陷。

    参数:
        d1: 被减形状的距离
        d2: 减去形状的距离
        k: 平滑系数

    返回:
        平滑差集后的距离值
    """
    if k <= 0.0:
        return max(d1, -d2)
    h = max(0.0, min(1.0, 0.5 - 0.5 * (d1 + d2) / k))
    return d1 * (1.0 - h) + (-d2) * h + k * h * (1.0 - h)


def op_smooth_intersection(d1, d2, k):
    """
    平滑交集

    参数:
        d1: 第一个距离值
        d2: 第二个距离值
        k: 平滑系数

    返回:
        平滑交集后的距离值
    """
    if k <= 0.0:
        return max(d1, d2)
    h = max(0.0, min(1.0, 0.5 - 0.5 * (d2 - d1) / k))
    return d2 * (1.0 - h) + d1 * h + k * h * (1.0 - h)
