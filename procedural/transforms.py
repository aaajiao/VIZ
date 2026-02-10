"""
域变换 - Domain Transforms

坐标变换函数和 TransformedEffect 包装器。
在效果的 main() 调用前应用坐标变换，N 个效果 x M 个变换 = N*M 视觉结构。

Pure coordinate transform functions + TransformedEffect wrapper.
Applied before an effect's main() call to remap coordinates.

用法::

    from procedural.transforms import TransformedEffect, kaleidoscope, tile

    # 包装任意效果
    transformed = TransformedEffect(
        inner_effect=PlasmaEffect(),
        transforms=[(kaleidoscope, {'segments': 6}), (tile, {'cols': 2, 'rows': 2})]
    )

    # 使用与普通效果完全相同
    state = transformed.pre(ctx, buffer)
    cell = transformed.main(x, y, ctx, state)
"""

import math

try:
    from procedural.core.mathx import clamp, fract, TAU, PI
except ImportError:
    from viz.procedural.core.mathx import clamp, fract, TAU, PI

__all__ = [
    "mirror_x",
    "mirror_y",
    "mirror_quad",
    "kaleidoscope",
    "tile",
    "rotate_uv",
    "zoom",
    "spiral_warp",
    "polar_remap",
    "TRANSFORM_REGISTRY",
    "TransformedEffect",
]


# ==================== 坐标变换函数 ====================
# Transform functions: (u, v) -> (u', v') where u,v in [0,1]


def mirror_x(u, v):
    """水平镜像 - Horizontal mirror symmetry"""
    return (1.0 - u if u > 0.5 else u) * 2.0, v


def mirror_y(u, v):
    """垂直镜像 - Vertical mirror symmetry"""
    return u, (1.0 - v if v > 0.5 else v) * 2.0


def mirror_quad(u, v):
    """四象限镜像 - Four-fold symmetry"""
    mu = (1.0 - u if u > 0.5 else u) * 2.0
    mv = (1.0 - v if v > 0.5 else v) * 2.0
    return mu, mv


def kaleidoscope(u, v, segments=6, cx=0.5, cy=0.5):
    """万花筒 - N-fold rotational symmetry"""
    dx = u - cx
    dy = v - cy
    r = math.sqrt(dx * dx + dy * dy)
    theta = math.atan2(dy, dx)

    seg_angle = TAU / segments
    # Which segment are we in (for mirror decision)
    seg_idx = int(math.floor(((theta % TAU) / seg_angle)))
    # Fold angle into one segment
    theta = (theta % TAU) % seg_angle
    # Mirror alternate segments for seamless joins
    if seg_idx % 2 == 1:
        theta = seg_angle - theta

    return cx + r * math.cos(theta), cy + r * math.sin(theta)


def tile(u, v, cols=2, rows=2):
    """平铺重复 - Repeat/tile coordinates"""
    return fract(u * cols), fract(v * rows)


def rotate_uv(u, v, angle=0.0, cx=0.5, cy=0.5):
    """旋转 - Rotate around center"""
    dx = u - cx
    dy = v - cy
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a


def zoom(u, v, factor=2.0, cx=0.5, cy=0.5):
    """缩放 - Zoom in/out from center"""
    if factor == 0:
        return cx, cy
    return cx + (u - cx) / factor, cy + (v - cy) / factor


def spiral_warp(u, v, twist=1.0, cx=0.5, cy=0.5):
    """螺旋扭曲 - Spiral domain warp"""
    dx = u - cx
    dy = v - cy
    r = math.sqrt(dx * dx + dy * dy)
    theta = math.atan2(dy, dx)
    theta += r * twist * TAU
    return cx + r * math.cos(theta), cy + r * math.sin(theta)


def polar_remap(u, v, cx=0.5, cy=0.5):
    """极坐标重映射 - Cartesian to polar domain"""
    dx = u - cx
    dy = v - cy
    r = math.sqrt(dx * dx + dy * dy) * 2.0
    theta = (math.atan2(dy, dx) / TAU + 0.5) % 1.0
    return theta, r


# ==================== 变换注册表 ====================

TRANSFORM_REGISTRY = {
    "mirror_x": mirror_x,
    "mirror_y": mirror_y,
    "mirror_quad": mirror_quad,
    "kaleidoscope": kaleidoscope,
    "tile": tile,
    "rotate": rotate_uv,
    "zoom": zoom,
    "spiral_warp": spiral_warp,
    "polar_remap": polar_remap,
}
"""
全局变换注册表 - Global Transform Registry

存储所有已注册的坐标变换函数。
"""


# ==================== TransformedEffect 包装器 ====================


class TransformedEffect:
    """
    变换效果包装器 - Transformed Effect Wrapper

    包装任意 Effect，在 main() 调用前应用坐标变换链。
    变换按列表顺序依次应用。

    示例::

        transformed = TransformedEffect(
            inner_effect=PlasmaEffect(),
            transforms=[
                (kaleidoscope, {'segments': 8}),
                (tile, {'cols': 3, 'rows': 3}),
            ]
        )
    """

    def __init__(self, inner_effect, transforms):
        """
        初始化变换包装器

        参数:
            inner_effect: 被包装的效果实例 (实现 Effect Protocol)
            transforms: 变换列表 [(fn, kwargs), ...]
                每项为 (变换函数, 关键字参数字典)
        """
        self.inner = inner_effect
        self.transforms = transforms

    def pre(self, ctx, buffer):
        """预处理阶段 - 委托给内部效果"""
        return self.inner.pre(ctx, buffer)

    def main(self, x, y, ctx, state):
        """主渲染阶段 - 应用变换链后委托给内部效果"""
        u = x / ctx.width if ctx.width > 0 else 0.0
        v = y / ctx.height if ctx.height > 0 else 0.0

        for fn, kwargs in self.transforms:
            u, v = fn(u, v, **kwargs)

        # Clamp and convert back to pixel coords
        tx = int(clamp(u * ctx.width, 0, ctx.width - 1))
        ty = int(clamp(v * ctx.height, 0, ctx.height - 1))
        return self.inner.main(tx, ty, ctx, state)

    def post(self, ctx, buffer, state):
        """后处理阶段 - 委托给内部效果"""
        self.inner.post(ctx, buffer, state)
