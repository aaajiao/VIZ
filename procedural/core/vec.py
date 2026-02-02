"""
2D 向量运算 - play.core/vec2.js 风格

提供 Vec2 类和常用向量操作函数。所有运算纯 Python，无 NumPy 依赖。

用法::

    from viz.procedural.core.vec import Vec2, length, normalize, rotate, dot

    v = Vec2(3, 4)
    print(length(v))       # 5.0
    print(normalize(v))    # Vec2(0.6, 0.8)
    print(rotate(v, 1.57)) # ~Vec2(-4, 3)
    print(dot(v, Vec2(1, 0)))  # 3.0
"""

import math

__all__ = [
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
]


class Vec2:
    """
    2D 向量

    支持基本算术运算符重载 (+, -, *, /, ==)。
    不可变风格使用：运算返回新 Vec2 实例。

    示例::

        a = Vec2(1, 2)
        b = Vec2(3, 4)
        c = a + b        # Vec2(4, 6)
        d = a * 2.0      # Vec2(2, 4)
        print(a.x, a.y)  # 1 2
    """

    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    # --- 运算符重载 ---

    def __add__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x + other.x, self.y + other.y)
        return Vec2(self.x + other, self.y + other)

    def __radd__(self, other):
        return Vec2(self.x + other, self.y + other)

    def __sub__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x - other.x, self.y - other.y)
        return Vec2(self.x - other, self.y - other)

    def __rsub__(self, other):
        return Vec2(other - self.x, other - self.y)

    def __mul__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x * other.x, self.y * other.y)
        return Vec2(self.x * other, self.y * other)

    def __rmul__(self, other):
        return Vec2(self.x * other, self.y * other)

    def __truediv__(self, other):
        if isinstance(other, Vec2):
            return Vec2(self.x / other.x, self.y / other.y)
        return Vec2(self.x / other, self.y / other)

    def __neg__(self):
        return Vec2(-self.x, -self.y)

    def __abs__(self):
        return Vec2(abs(self.x), abs(self.y))

    def __eq__(self, other):
        if not isinstance(other, Vec2):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Vec2({self.x:.4g}, {self.y:.4g})"

    def __iter__(self):
        """支持解构: x, y = vec"""
        yield self.x
        yield self.y

    def __hash__(self):
        return hash((self.x, self.y))


# --- 工厂函数 ---


def vec2(x=0.0, y=None):
    """
    创建 Vec2 的便捷函数

    vec2(3, 4)   → Vec2(3, 4)
    vec2(5)      → Vec2(5, 5)  # 标量广播
    """
    if y is None:
        return Vec2(x, x)
    return Vec2(x, y)


# --- 向量运算函数 ---


def add(a, b):
    """向量加法: a + b"""
    return a + b


def sub(a, b):
    """向量减法: a - b"""
    return a - b


def mul(a, s):
    """
    向量乘法

    mul(Vec2(1,2), 3)          → Vec2(3, 6)   # 标量乘
    mul(Vec2(1,2), Vec2(3,4))  → Vec2(3, 8)   # 分量乘
    """
    return a * s


def div(a, s):
    """向量除法"""
    return a / s


def length(v):
    """
    向量长度 (模)

    length(Vec2(3, 4))  → 5.0
    """
    return math.sqrt(v.x * v.x + v.y * v.y)


def length_sq(v):
    """
    向量长度的平方 (避免 sqrt，用于距离比较)

    length_sq(Vec2(3, 4))  → 25.0
    """
    return v.x * v.x + v.y * v.y


def normalize(v):
    """
    归一化向量 (长度变为 1)

    normalize(Vec2(3, 4))  → Vec2(0.6, 0.8)
    normalize(Vec2(0, 0))  → Vec2(0, 0)  # 零向量安全处理
    """
    ln = length(v)
    if ln < 1e-10:
        return Vec2(0.0, 0.0)
    return Vec2(v.x / ln, v.y / ln)


def rotate(v, angle):
    """
    绕原点旋转向量 (弧度)

    rotate(Vec2(1, 0), math.pi / 2)  → ~Vec2(0, 1)

    参数:
        v: 输入向量
        angle: 旋转角度 (弧度，逆时针为正)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec2(
        v.x * cos_a - v.y * sin_a,
        v.x * sin_a + v.y * cos_a,
    )


def dot(a, b):
    """
    点积

    dot(Vec2(1,0), Vec2(0,1))  → 0.0  # 正交
    dot(Vec2(1,0), Vec2(1,0))  → 1.0  # 平行
    """
    return a.x * b.x + a.y * b.y


def cross(a, b):
    """
    2D 叉积 (标量值，表示有符号面积)

    cross(Vec2(1,0), Vec2(0,1))  → 1.0   # 逆时针
    cross(Vec2(0,1), Vec2(1,0))  → -1.0  # 顺时针
    """
    return a.x * b.y - a.y * b.x


def dist(a, b):
    """
    两点间距离

    dist(Vec2(0,0), Vec2(3,4))  → 5.0
    """
    return length(a - b)


def reflect(v, n):
    """
    向量反射 (沿法线 n 反射)

    n 应为单位向量。

    reflect(Vec2(1,-1), Vec2(0,1))  → Vec2(1, 1)
    """
    d = dot(v, n)
    return Vec2(v.x - 2.0 * d * n.x, v.y - 2.0 * d * n.y)


def mix_vec(a, b, t):
    """
    向量线性插值

    mix_vec(Vec2(0,0), Vec2(10,10), 0.5)  → Vec2(5, 5)

    参数:
        a: 起点向量
        b: 终点向量
        t: 插值因子 (0.0 = a, 1.0 = b)
    """
    return Vec2(
        a.x * (1.0 - t) + b.x * t,
        a.y * (1.0 - t) + b.y * t,
    )
