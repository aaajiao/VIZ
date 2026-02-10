"""
3D 投影与向量运算 - 3D Projection and Vector Operations

提供 Vec3 类和 3D 变换工具函数，用于 3D 效果的投影渲染。
纯 Python 实现，无 NumPy 依赖。

用法::

    from procedural.core.projection import Vec3, rotate_x, rotate_y, project_perspective

    v = Vec3(1, 2, 3)
    v = rotate_y(v, 0.5)
    sx, sy, depth = project_perspective(v, fov=60, aspect=1.0)
"""

import math

__all__ = [
    "Vec3",
    "vec3",
    "length3",
    "normalize3",
    "dot3",
    "cross3",
    "rotate_x",
    "rotate_y",
    "rotate_z",
    "project_perspective",
]


class Vec3:
    """3D 向量 - 3D Vector"""

    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    # --- 运算符重载 ---

    def __add__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
        return Vec3(self.x + other, self.y + other, self.z + other)

    def __radd__(self, other):
        return Vec3(self.x + other, self.y + other, self.z + other)

    def __sub__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
        return Vec3(self.x - other, self.y - other, self.z - other)

    def __rsub__(self, other):
        return Vec3(other - self.x, other - self.y, other - self.z)

    def __mul__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x * other.x, self.y * other.y, self.z * other.z)
        return Vec3(self.x * other, self.y * other, self.z * other)

    def __rmul__(self, other):
        return Vec3(self.x * other, self.y * other, self.z * other)

    def __truediv__(self, other):
        if isinstance(other, Vec3):
            return Vec3(self.x / other.x, self.y / other.y, self.z / other.z)
        return Vec3(self.x / other, self.y / other, self.z / other)

    def __neg__(self):
        return Vec3(-self.x, -self.y, -self.z)

    def __abs__(self):
        return Vec3(abs(self.x), abs(self.y), abs(self.z))

    def __eq__(self, other):
        if not isinstance(other, Vec3):
            return NotImplemented
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __repr__(self):
        return f"Vec3({self.x:.4g}, {self.y:.4g}, {self.z:.4g})"

    def __iter__(self):
        """支持解构: x, y, z = vec"""
        yield self.x
        yield self.y
        yield self.z

    def __hash__(self):
        return hash((self.x, self.y, self.z))


# --- 工厂函数 ---


def vec3(x=0.0, y=None, z=None):
    """
    创建 Vec3 的便捷函数 - Convenience factory for Vec3

    vec3(3, 4, 5)  -> Vec3(3, 4, 5)
    vec3(5)        -> Vec3(5, 5, 5)  # 标量广播
    vec3(1, 2)     -> Vec3(1, 2, 0)
    """
    if y is None and z is None:
        return Vec3(x, x, x)
    if z is None:
        return Vec3(x, y, 0.0)
    return Vec3(x, y, z)


# --- 向量运算函数 ---


def length3(v):
    """
    3D 向量长度 - 3D vector magnitude

    length3(Vec3(1, 2, 2))  -> 3.0
    """
    return math.sqrt(v.x * v.x + v.y * v.y + v.z * v.z)


def normalize3(v):
    """
    归一化 3D 向量 - Normalize 3D vector (safe for zero)

    normalize3(Vec3(3, 0, 0))  -> Vec3(1, 0, 0)
    normalize3(Vec3(0, 0, 0))  -> Vec3(0, 0, 0)
    """
    ln = length3(v)
    if ln < 1e-10:
        return Vec3(0.0, 0.0, 0.0)
    return Vec3(v.x / ln, v.y / ln, v.z / ln)


def dot3(a, b):
    """
    3D 点积 - 3D dot product

    dot3(Vec3(1,0,0), Vec3(0,1,0))  -> 0.0
    dot3(Vec3(1,0,0), Vec3(1,0,0))  -> 1.0
    """
    return a.x * b.x + a.y * b.y + a.z * b.z


def cross3(a, b):
    """
    3D 叉积 - 3D cross product

    cross3(Vec3(1,0,0), Vec3(0,1,0))  -> Vec3(0, 0, 1)
    """
    return Vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def rotate_x(v, angle):
    """
    绕 X 轴旋转 - Rotate around X axis

    参数:
        v: 输入向量
        angle: 旋转角度 (弧度)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(
        v.x,
        v.y * cos_a - v.z * sin_a,
        v.y * sin_a + v.z * cos_a,
    )


def rotate_y(v, angle):
    """
    绕 Y 轴旋转 - Rotate around Y axis

    参数:
        v: 输入向量
        angle: 旋转角度 (弧度)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(
        v.x * cos_a + v.z * sin_a,
        v.y,
        -v.x * sin_a + v.z * cos_a,
    )


def rotate_z(v, angle):
    """
    绕 Z 轴旋转 - Rotate around Z axis

    参数:
        v: 输入向量
        angle: 旋转角度 (弧度)
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return Vec3(
        v.x * cos_a - v.y * sin_a,
        v.x * sin_a + v.y * cos_a,
        v.z,
    )


def project_perspective(v, fov=60.0, aspect=1.0):
    """
    透视投影 - Perspective projection

    将 3D 点投影到 2D 屏幕空间。返回 (screen_x, screen_y, depth)。
    screen_x, screen_y 范围约 -1 到 1 (取决于 FOV 和点的位置)。
    depth 为正值表示在相机前方。

    参数:
        v: 3D 向量 (相机空间，相机看向 +Z)
        fov: 垂直视场角 (度)
        aspect: 宽高比 (width / height)

    返回:
        tuple: (screen_x, screen_y, depth)
    """
    # 将 FOV 转为焦距
    f = 1.0 / math.tan(math.radians(fov) * 0.5)
    # 避免除零
    z = v.z if abs(v.z) > 1e-10 else 1e-10
    sx = (f * v.x) / (z * aspect)
    sy = (f * v.y) / z
    return (sx, sy, v.z)
