"""test procedural/core/mathx.py - clamp, mix, smoothstep, fract, etc."""

import math
import pytest
from procedural.core.mathx import (
    clamp,
    mix,
    smoothstep,
    smootherstep,
    map_range,
    fract,
    sign,
    step,
    pulse,
    mod,
    PI,
    TAU,
    HALF_PI,
)


class TestConstants:
    def test_pi(self):
        assert abs(PI - math.pi) < 1e-10

    def test_tau(self):
        assert abs(TAU - 2 * math.pi) < 1e-10

    def test_half_pi(self):
        assert abs(HALF_PI - math.pi / 2) < 1e-10


class TestClamp:
    def test_value_within_range(self):
        assert clamp(0.5, 0.0, 1.0) == 0.5

    def test_value_below_min(self):
        assert clamp(-0.5, 0.0, 1.0) == 0.0

    def test_value_above_max(self):
        assert clamp(1.5, 0.0, 1.0) == 1.0

    def test_custom_range(self):
        assert clamp(50, 10, 100) == 50
        assert clamp(5, 10, 100) == 10
        assert clamp(150, 10, 100) == 100


class TestMix:
    def test_t_zero_returns_a(self):
        assert mix(10, 20, 0.0) == 10

    def test_t_one_returns_b(self):
        assert mix(10, 20, 1.0) == 20

    def test_t_half_returns_midpoint(self):
        assert mix(0, 10, 0.5) == 5.0

    def test_negative_values(self):
        assert mix(-10, 10, 0.5) == 0.0


class TestSmoothstep:
    def test_below_edge0(self):
        assert smoothstep(0, 1, -0.5) == 0.0

    def test_above_edge1(self):
        assert smoothstep(0, 1, 1.5) == 1.0

    def test_at_edge0(self):
        assert smoothstep(0, 1, 0.0) == 0.0

    def test_at_edge1(self):
        assert smoothstep(0, 1, 1.0) == 1.0

    def test_at_midpoint(self):
        assert smoothstep(0, 1, 0.5) == 0.5

    def test_nonlinear_interpolation(self):
        result = smoothstep(0, 1, 0.25)
        assert result != 0.25
        assert 0 < result < 0.5


class TestSmootherstep:
    def test_at_edges(self):
        assert smootherstep(0, 1, 0.0) == 0.0
        assert smootherstep(0, 1, 1.0) == 1.0

    def test_at_midpoint(self):
        assert smootherstep(0, 1, 0.5) == 0.5


class TestMapRange:
    def test_simple_mapping(self):
        assert map_range(50, 0, 100, 0, 1) == 0.5

    def test_inverse_mapping(self):
        assert map_range(0.5, 0, 1, 100, 0) == 50

    def test_offset_mapping(self):
        assert map_range(75, 0, 100, 0, 255) == pytest.approx(191.25)


class TestFract:
    def test_positive_value(self):
        assert fract(3.7) == pytest.approx(0.7)

    def test_negative_value(self):
        assert fract(-0.3) == pytest.approx(0.7)

    def test_whole_number(self):
        assert fract(5.0) == pytest.approx(0.0)


class TestSign:
    def test_positive(self):
        assert sign(5) == 1.0

    def test_negative(self):
        assert sign(-3) == -1.0

    def test_zero(self):
        assert sign(0) == 0.0


class TestStep:
    def test_below_edge(self):
        assert step(0.5, 0.3) == 0.0

    def test_above_edge(self):
        assert step(0.5, 0.7) == 1.0

    def test_at_edge(self):
        assert step(0.5, 0.5) == 1.0


class TestPulse:
    def test_inside_range(self):
        assert pulse(0.3, 0.7, 0.5) == 1.0

    def test_outside_range_low(self):
        assert pulse(0.3, 0.7, 0.1) == 0.0

    def test_outside_range_high(self):
        assert pulse(0.3, 0.7, 0.9) == 0.0


class TestMod:
    def test_positive(self):
        assert mod(5.5, 3.0) == pytest.approx(2.5)

    def test_negative(self):
        assert mod(-1.5, 3.0) == pytest.approx(1.5)
