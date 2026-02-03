"""test procedural/core/sdf.py - signed distance functions"""

import pytest
from procedural.core.vec import Vec2
from procedural.core.sdf import (
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


class TestSdCircle:
    def test_center_is_inside(self):
        d = sd_circle(Vec2(0, 0), Vec2(0, 0), 1.0)
        assert d == -1.0

    def test_on_boundary(self):
        d = sd_circle(Vec2(1, 0), Vec2(0, 0), 1.0)
        assert d == pytest.approx(0.0)

    def test_outside(self):
        d = sd_circle(Vec2(2, 0), Vec2(0, 0), 1.0)
        assert d == pytest.approx(1.0)

    def test_with_offset_center(self):
        d = sd_circle(Vec2(5, 5), Vec2(5, 5), 2.0)
        assert d == -2.0


class TestSdBox:
    def test_center_is_inside(self):
        d = sd_box(Vec2(0, 0), Vec2(0, 0), Vec2(1, 1))
        assert d < 0

    def test_outside(self):
        d = sd_box(Vec2(2, 0), Vec2(0, 0), Vec2(1, 1))
        assert d > 0

    def test_on_edge(self):
        d = sd_box(Vec2(1, 0), Vec2(0, 0), Vec2(1, 1))
        assert d == pytest.approx(0.0)


class TestSdLine:
    def test_perpendicular_distance(self):
        d = sd_line(Vec2(0, 1), Vec2(0, 0), Vec2(2, 0))
        assert d == pytest.approx(1.0)

    def test_point_on_line(self):
        d = sd_line(Vec2(1, 0), Vec2(0, 0), Vec2(2, 0))
        assert d == pytest.approx(0.0)

    def test_beyond_endpoint(self):
        d = sd_line(Vec2(3, 0), Vec2(0, 0), Vec2(2, 0))
        assert d == pytest.approx(1.0)

    def test_zero_length_line(self):
        d = sd_line(Vec2(1, 1), Vec2(0, 0), Vec2(0, 0))
        assert d == pytest.approx(1.4142, rel=0.01)


class TestSdRing:
    def test_on_ring_center(self):
        d = sd_ring(Vec2(1, 0), Vec2(0, 0), 1.0, 0.1)
        assert d == pytest.approx(-0.1)

    def test_inside_ring(self):
        d = sd_ring(Vec2(0.95, 0), Vec2(0, 0), 1.0, 0.1)
        assert d < 0

    def test_outside_ring(self):
        d = sd_ring(Vec2(1.2, 0), Vec2(0, 0), 1.0, 0.1)
        assert d > 0


class TestBooleanOps:
    def test_union(self):
        assert op_union(0.5, 0.3) == 0.3
        assert op_union(-0.5, 0.3) == -0.5

    def test_intersection(self):
        assert op_intersection(0.5, 0.3) == 0.5
        assert op_intersection(-0.5, 0.3) == 0.3

    def test_subtraction(self):
        assert op_subtraction(0.5, 0.3) == 0.5
        assert op_subtraction(-0.5, 0.3) == -0.3


class TestSmoothOps:
    def test_smooth_union_with_k_zero(self):
        result = op_smooth_union(0.5, 0.3, 0.0)
        assert result == pytest.approx(0.3)

    def test_smooth_union_produces_rounder_result(self):
        sharp = op_union(0.1, 0.1)
        smooth = op_smooth_union(0.1, 0.1, 0.2)
        assert smooth < sharp

    def test_smooth_subtraction_with_k_zero(self):
        result = op_smooth_subtraction(0.5, -0.3, 0.0)
        assert result == pytest.approx(0.5)

    def test_smooth_intersection_with_k_zero(self):
        result = op_smooth_intersection(0.5, 0.3, 0.0)
        assert result == pytest.approx(0.5)
