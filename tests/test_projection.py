"""test procedural/core/projection - 3D vector and projection operations"""

import pytest
import math
from procedural.core.projection import (
    Vec3,
    vec3,
    length3,
    normalize3,
    dot3,
    cross3,
    rotate_x,
    rotate_y,
    rotate_z,
    project_perspective,
)


class TestVec3:
    """Vec3 创建与运算符 - Vec3 creation and operators"""

    def test_creation_default(self):
        v = Vec3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_creation_values(self):
        v = Vec3(1, 2, 3)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_add_vec(self):
        a = Vec3(1, 2, 3)
        b = Vec3(4, 5, 6)
        c = a + b
        assert c == Vec3(5, 7, 9)

    def test_add_scalar(self):
        v = Vec3(1, 2, 3)
        c = v + 10
        assert c == Vec3(11, 12, 13)

    def test_radd_scalar(self):
        v = Vec3(1, 2, 3)
        c = 10 + v
        assert c == Vec3(11, 12, 13)

    def test_sub_vec(self):
        a = Vec3(5, 7, 9)
        b = Vec3(1, 2, 3)
        c = a - b
        assert c == Vec3(4, 5, 6)

    def test_sub_scalar(self):
        v = Vec3(10, 20, 30)
        c = v - 5
        assert c == Vec3(5, 15, 25)

    def test_rsub_scalar(self):
        v = Vec3(1, 2, 3)
        c = 10 - v
        assert c == Vec3(9, 8, 7)

    def test_mul_scalar(self):
        v = Vec3(1, 2, 3)
        c = v * 2
        assert c == Vec3(2, 4, 6)

    def test_rmul_scalar(self):
        v = Vec3(1, 2, 3)
        c = 3 * v
        assert c == Vec3(3, 6, 9)

    def test_mul_vec(self):
        a = Vec3(2, 3, 4)
        b = Vec3(5, 6, 7)
        c = a * b
        assert c == Vec3(10, 18, 28)

    def test_truediv_scalar(self):
        v = Vec3(4, 6, 8)
        c = v / 2
        assert c == Vec3(2, 3, 4)

    def test_truediv_vec(self):
        a = Vec3(10, 20, 30)
        b = Vec3(2, 5, 10)
        c = a / b
        assert c == Vec3(5, 4, 3)

    def test_neg(self):
        v = Vec3(1, -2, 3)
        c = -v
        assert c == Vec3(-1, 2, -3)

    def test_abs(self):
        v = Vec3(-1, -2, 3)
        c = abs(v)
        assert c == Vec3(1, 2, 3)

    def test_eq(self):
        a = Vec3(1, 2, 3)
        b = Vec3(1, 2, 3)
        assert a == b

    def test_neq(self):
        a = Vec3(1, 2, 3)
        b = Vec3(1, 2, 4)
        assert a != b

    def test_eq_non_vec(self):
        v = Vec3(1, 2, 3)
        assert v.__eq__(42) is NotImplemented

    def test_repr(self):
        v = Vec3(1, 2, 3)
        assert repr(v) == "Vec3(1, 2, 3)"

    def test_iter(self):
        v = Vec3(1, 2, 3)
        x, y, z = v
        assert x == 1.0
        assert y == 2.0
        assert z == 3.0

    def test_hash_equal(self):
        a = Vec3(1, 2, 3)
        b = Vec3(1, 2, 3)
        assert hash(a) == hash(b)

    def test_hash_different(self):
        a = Vec3(1, 2, 3)
        b = Vec3(4, 5, 6)
        assert hash(a) != hash(b)

    def test_usable_in_set(self):
        s = {Vec3(1, 2, 3), Vec3(1, 2, 3), Vec3(4, 5, 6)}
        assert len(s) == 2


class TestVec3Factory:
    """vec3 工厂函数 - vec3 factory function"""

    def test_scalar_broadcast(self):
        v = vec3(5)
        assert v == Vec3(5, 5, 5)

    def test_two_args(self):
        v = vec3(1, 2)
        assert v == Vec3(1, 2, 0)

    def test_three_args(self):
        v = vec3(1, 2, 3)
        assert v == Vec3(1, 2, 3)


class TestVec3Operations:
    """向量运算函数 - Vector operation functions"""

    def test_length3_unit(self):
        assert length3(Vec3(1, 0, 0)) == pytest.approx(1.0)

    def test_length3_diagonal(self):
        assert length3(Vec3(1, 2, 2)) == pytest.approx(3.0)

    def test_length3_zero(self):
        assert length3(Vec3(0, 0, 0)) == pytest.approx(0.0)

    def test_normalize3_unit(self):
        n = normalize3(Vec3(3, 0, 0))
        assert n.x == pytest.approx(1.0)
        assert n.y == pytest.approx(0.0)
        assert n.z == pytest.approx(0.0)

    def test_normalize3_diagonal(self):
        n = normalize3(Vec3(1, 1, 1))
        expected = 1.0 / math.sqrt(3)
        assert n.x == pytest.approx(expected)
        assert n.y == pytest.approx(expected)
        assert n.z == pytest.approx(expected)

    def test_normalize3_zero_safe(self):
        n = normalize3(Vec3(0, 0, 0))
        assert n == Vec3(0, 0, 0)

    def test_normalize3_length_is_one(self):
        n = normalize3(Vec3(3, 4, 5))
        assert length3(n) == pytest.approx(1.0)

    def test_dot3_orthogonal(self):
        assert dot3(Vec3(1, 0, 0), Vec3(0, 1, 0)) == pytest.approx(0.0)

    def test_dot3_parallel(self):
        assert dot3(Vec3(1, 0, 0), Vec3(1, 0, 0)) == pytest.approx(1.0)

    def test_dot3_antiparallel(self):
        assert dot3(Vec3(1, 0, 0), Vec3(-1, 0, 0)) == pytest.approx(-1.0)

    def test_dot3_general(self):
        assert dot3(Vec3(1, 2, 3), Vec3(4, 5, 6)) == pytest.approx(32.0)

    def test_cross3_x_cross_y(self):
        c = cross3(Vec3(1, 0, 0), Vec3(0, 1, 0))
        assert c.x == pytest.approx(0.0)
        assert c.y == pytest.approx(0.0)
        assert c.z == pytest.approx(1.0)

    def test_cross3_y_cross_x(self):
        c = cross3(Vec3(0, 1, 0), Vec3(1, 0, 0))
        assert c.x == pytest.approx(0.0)
        assert c.y == pytest.approx(0.0)
        assert c.z == pytest.approx(-1.0)

    def test_cross3_self_is_zero(self):
        v = Vec3(1, 2, 3)
        c = cross3(v, v)
        assert c.x == pytest.approx(0.0)
        assert c.y == pytest.approx(0.0)
        assert c.z == pytest.approx(0.0)

    def test_cross3_perpendicular_to_inputs(self):
        a = Vec3(1, 2, 3)
        b = Vec3(4, 5, 6)
        c = cross3(a, b)
        assert dot3(c, a) == pytest.approx(0.0)
        assert dot3(c, b) == pytest.approx(0.0)


class TestRotation:
    """旋转变换 - Rotation transforms"""

    def test_rotate_x_zero(self):
        v = Vec3(1, 2, 3)
        r = rotate_x(v, 0.0)
        assert r.x == pytest.approx(v.x)
        assert r.y == pytest.approx(v.y)
        assert r.z == pytest.approx(v.z)

    def test_rotate_y_zero(self):
        v = Vec3(1, 2, 3)
        r = rotate_y(v, 0.0)
        assert r.x == pytest.approx(v.x)
        assert r.y == pytest.approx(v.y)
        assert r.z == pytest.approx(v.z)

    def test_rotate_z_zero(self):
        v = Vec3(1, 2, 3)
        r = rotate_z(v, 0.0)
        assert r.x == pytest.approx(v.x)
        assert r.y == pytest.approx(v.y)
        assert r.z == pytest.approx(v.z)

    def test_rotate_x_90(self):
        """绕 X 轴旋转 90 度: Y -> Z, Z -> -Y"""
        v = Vec3(0, 1, 0)
        r = rotate_x(v, math.pi / 2)
        assert r.x == pytest.approx(0.0, abs=1e-10)
        assert r.y == pytest.approx(0.0, abs=1e-10)
        assert r.z == pytest.approx(1.0)

    def test_rotate_y_90(self):
        """绕 Y 轴旋转 90 度: Z -> X, X -> -Z"""
        v = Vec3(0, 0, 1)
        r = rotate_y(v, math.pi / 2)
        assert r.x == pytest.approx(1.0)
        assert r.y == pytest.approx(0.0, abs=1e-10)
        assert r.z == pytest.approx(0.0, abs=1e-10)

    def test_rotate_z_90(self):
        """绕 Z 轴旋转 90 度: X -> Y, Y -> -X"""
        v = Vec3(1, 0, 0)
        r = rotate_z(v, math.pi / 2)
        assert r.x == pytest.approx(0.0, abs=1e-10)
        assert r.y == pytest.approx(1.0)
        assert r.z == pytest.approx(0.0, abs=1e-10)

    def test_rotation_preserves_length(self):
        v = Vec3(1, 2, 3)
        original_len = length3(v)
        r = rotate_x(rotate_y(rotate_z(v, 0.7), 1.3), 2.1)
        assert length3(r) == pytest.approx(original_len)

    def test_rotation_composition_360(self):
        """完整旋转 360 度回到原点"""
        v = Vec3(1, 2, 3)
        r = rotate_y(v, 2 * math.pi)
        assert r.x == pytest.approx(v.x, abs=1e-10)
        assert r.y == pytest.approx(v.y, abs=1e-10)
        assert r.z == pytest.approx(v.z, abs=1e-10)

    def test_rotate_x_orthogonality(self):
        """旋转后两个基向量仍然正交"""
        vy = rotate_x(Vec3(0, 1, 0), 0.5)
        vz = rotate_x(Vec3(0, 0, 1), 0.5)
        assert dot3(vy, vz) == pytest.approx(0.0, abs=1e-10)


class TestPerspectiveProjection:
    """透视投影 - Perspective projection"""

    def test_center_projects_to_origin(self):
        """原点 (x=0, y=0) 投影到屏幕中心 (0, 0)"""
        sx, sy, depth = project_perspective(Vec3(0, 0, 1))
        assert sx == pytest.approx(0.0)
        assert sy == pytest.approx(0.0)

    def test_depth_ordering(self):
        """近处的点 depth 更小"""
        _, _, d1 = project_perspective(Vec3(0, 0, 1))
        _, _, d2 = project_perspective(Vec3(0, 0, 5))
        assert d1 < d2

    def test_positive_x_projects_right(self):
        """正 X 投影到屏幕右侧 (正 sx)"""
        sx, _, _ = project_perspective(Vec3(1, 0, 5))
        assert sx > 0

    def test_positive_y_projects_up(self):
        """正 Y 投影到屏幕上方 (正 sy)"""
        _, sy, _ = project_perspective(Vec3(0, 1, 5))
        assert sy > 0

    def test_perspective_foreshortening(self):
        """远处的点投影更小 (透视缩短)"""
        sx_near, _, _ = project_perspective(Vec3(1, 0, 2))
        sx_far, _, _ = project_perspective(Vec3(1, 0, 10))
        assert abs(sx_near) > abs(sx_far)

    def test_fov_affects_projection(self):
        """更大 FOV 产生更小的投影"""
        sx_narrow, _, _ = project_perspective(Vec3(1, 0, 5), fov=30.0)
        sx_wide, _, _ = project_perspective(Vec3(1, 0, 5), fov=90.0)
        assert abs(sx_narrow) > abs(sx_wide)

    def test_aspect_ratio(self):
        """宽高比影响 X 投影"""
        sx_square, _, _ = project_perspective(Vec3(1, 0, 5), aspect=1.0)
        sx_wide, _, _ = project_perspective(Vec3(1, 0, 5), aspect=2.0)
        assert abs(sx_wide) < abs(sx_square)

    def test_near_zero_z_safe(self):
        """接近零 Z 值不会崩溃"""
        sx, sy, depth = project_perspective(Vec3(1, 1, 0.0))
        # Should not raise, values will be large but finite
        assert math.isfinite(sx)
        assert math.isfinite(sy)
