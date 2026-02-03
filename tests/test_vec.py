"""test procedural/core/vec.py - Vec2 operations"""

import math
import pytest
from procedural.core.vec import (
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


class TestVec2:
    def test_init_default(self):
        v = Vec2()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_init_with_values(self):
        v = Vec2(3, 4)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_add_vectors(self):
        a = Vec2(1, 2)
        b = Vec2(3, 4)
        c = a + b
        assert c.x == 4.0
        assert c.y == 6.0

    def test_add_scalar(self):
        a = Vec2(1, 2)
        c = a + 5
        assert c.x == 6.0
        assert c.y == 7.0

    def test_sub_vectors(self):
        a = Vec2(5, 7)
        b = Vec2(2, 3)
        c = a - b
        assert c.x == 3.0
        assert c.y == 4.0

    def test_mul_scalar(self):
        a = Vec2(2, 3)
        c = a * 2
        assert c.x == 4.0
        assert c.y == 6.0

    def test_mul_vectors(self):
        a = Vec2(2, 3)
        b = Vec2(4, 5)
        c = a * b
        assert c.x == 8.0
        assert c.y == 15.0

    def test_div_scalar(self):
        a = Vec2(4, 6)
        c = a / 2
        assert c.x == 2.0
        assert c.y == 3.0

    def test_neg(self):
        a = Vec2(3, -4)
        b = -a
        assert b.x == -3.0
        assert b.y == 4.0

    def test_abs(self):
        a = Vec2(-3, -4)
        b = abs(a)
        assert b.x == 3.0
        assert b.y == 4.0

    def test_eq(self):
        a = Vec2(1, 2)
        b = Vec2(1, 2)
        c = Vec2(1, 3)
        assert a == b
        assert a != c

    def test_iter(self):
        v = Vec2(3, 4)
        x, y = v
        assert x == 3.0
        assert y == 4.0

    def test_repr(self):
        v = Vec2(3.14159, 2.71828)
        s = repr(v)
        assert "Vec2" in s
        assert "3.14" in s

    def test_hash(self):
        v1 = Vec2(1, 2)
        v2 = Vec2(1, 2)
        assert hash(v1) == hash(v2)


class TestVec2Factory:
    def test_with_two_args(self):
        v = vec2(3, 4)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_with_one_arg_broadcasts(self):
        v = vec2(5)
        assert v.x == 5.0
        assert v.y == 5.0


class TestVectorFunctions:
    def test_add_func(self):
        a = Vec2(1, 2)
        b = Vec2(3, 4)
        c = add(a, b)
        assert c == Vec2(4, 6)

    def test_sub_func(self):
        a = Vec2(5, 7)
        b = Vec2(2, 3)
        c = sub(a, b)
        assert c == Vec2(3, 4)

    def test_mul_func(self):
        a = Vec2(2, 3)
        c = mul(a, 2)
        assert c == Vec2(4, 6)

    def test_div_func(self):
        a = Vec2(4, 6)
        c = div(a, 2)
        assert c == Vec2(2, 3)


class TestLength:
    def test_length_3_4(self):
        v = Vec2(3, 4)
        assert length(v) == 5.0

    def test_length_zero(self):
        v = Vec2(0, 0)
        assert length(v) == 0.0

    def test_length_sq(self):
        v = Vec2(3, 4)
        assert length_sq(v) == 25.0


class TestNormalize:
    def test_normalize_unit(self):
        v = Vec2(3, 4)
        n = normalize(v)
        assert n.x == pytest.approx(0.6)
        assert n.y == pytest.approx(0.8)

    def test_normalize_zero(self):
        v = Vec2(0, 0)
        n = normalize(v)
        assert n.x == 0.0
        assert n.y == 0.0


class TestRotate:
    def test_rotate_90_degrees(self):
        v = Vec2(1, 0)
        r = rotate(v, math.pi / 2)
        assert r.x == pytest.approx(0, abs=1e-10)
        assert r.y == pytest.approx(1)

    def test_rotate_180_degrees(self):
        v = Vec2(1, 0)
        r = rotate(v, math.pi)
        assert r.x == pytest.approx(-1)
        assert r.y == pytest.approx(0, abs=1e-10)


class TestDot:
    def test_perpendicular(self):
        a = Vec2(1, 0)
        b = Vec2(0, 1)
        assert dot(a, b) == 0.0

    def test_parallel(self):
        a = Vec2(1, 0)
        b = Vec2(2, 0)
        assert dot(a, b) == 2.0


class TestCross:
    def test_cross_ccw(self):
        a = Vec2(1, 0)
        b = Vec2(0, 1)
        assert cross(a, b) == 1.0

    def test_cross_cw(self):
        a = Vec2(0, 1)
        b = Vec2(1, 0)
        assert cross(a, b) == -1.0


class TestDist:
    def test_dist_3_4(self):
        a = Vec2(0, 0)
        b = Vec2(3, 4)
        assert dist(a, b) == 5.0


class TestReflect:
    def test_reflect_horizontal(self):
        v = Vec2(1, -1)
        n = Vec2(0, 1)
        r = reflect(v, n)
        assert r.x == pytest.approx(1)
        assert r.y == pytest.approx(1)


class TestMixVec:
    def test_mix_midpoint(self):
        a = Vec2(0, 0)
        b = Vec2(10, 10)
        m = mix_vec(a, b, 0.5)
        assert m.x == pytest.approx(5)
        assert m.y == pytest.approx(5)

    def test_mix_t_zero(self):
        a = Vec2(0, 0)
        b = Vec2(10, 10)
        m = mix_vec(a, b, 0.0)
        assert m == a

    def test_mix_t_one(self):
        a = Vec2(0, 0)
        b = Vec2(10, 10)
        m = mix_vec(a, b, 1.0)
        assert m == b
