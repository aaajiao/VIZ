"""test procedural/transforms.py - domain transforms and TransformedEffect"""

import math
import random
import pytest

from procedural.transforms import (
    mirror_x,
    mirror_y,
    mirror_quad,
    kaleidoscope,
    tile,
    rotate_uv,
    zoom,
    spiral_warp,
    polar_remap,
    TRANSFORM_REGISTRY,
    TransformedEffect,
)
from procedural.types import Context, Cell


# ==================== Helper ====================


class StubEffect:
    """Minimal effect that encodes coordinates into the Cell"""

    def pre(self, ctx, buffer):
        return {}

    def main(self, x, y, ctx, state):
        value = (x + y) / max(ctx.width + ctx.height, 1)
        idx = min(9, int(value * 9))
        return Cell(char_idx=idx, fg=(x % 256, y % 256, 0), bg=None)

    def post(self, ctx, buffer, state):
        pass


def make_ctx(w=160, h=160):
    return Context(
        width=w,
        height=h,
        time=0.0,
        frame=0,
        seed=42,
        rng=random.Random(42),
        params={},
    )


# ==================== Transform function tests ====================


class TestMirrorX:
    def test_left_half_maps_to_full_range(self):
        u, v = mirror_x(0.0, 0.5)
        assert abs(u - 0.0) < 1e-9
        assert abs(v - 0.5) < 1e-9

    def test_midpoint(self):
        u, v = mirror_x(0.5, 0.5)
        assert abs(u - 1.0) < 1e-9

    def test_right_half_mirrors(self):
        u_left, _ = mirror_x(0.25, 0.5)
        u_right, _ = mirror_x(0.75, 0.5)
        assert abs(u_left - u_right) < 1e-9

    def test_symmetry(self):
        """Points equidistant from center produce same output"""
        for d in [0.1, 0.2, 0.3, 0.4]:
            u_a, _ = mirror_x(0.5 - d, 0.3)
            u_b, _ = mirror_x(0.5 + d, 0.3)
            assert abs(u_a - u_b) < 1e-9


class TestMirrorY:
    def test_top_half_maps_to_full_range(self):
        u, v = mirror_y(0.5, 0.0)
        assert abs(v - 0.0) < 1e-9

    def test_bottom_half_mirrors(self):
        _, v_top = mirror_y(0.5, 0.25)
        _, v_bot = mirror_y(0.5, 0.75)
        assert abs(v_top - v_bot) < 1e-9


class TestMirrorQuad:
    def test_all_quadrants_same(self):
        """All four quadrants map to the same output"""
        results = [
            mirror_quad(0.25, 0.25),
            mirror_quad(0.75, 0.25),
            mirror_quad(0.25, 0.75),
            mirror_quad(0.75, 0.75),
        ]
        for r in results[1:]:
            assert abs(r[0] - results[0][0]) < 1e-9
            assert abs(r[1] - results[0][1]) < 1e-9


class TestKaleidoscope:
    def test_center_unchanged(self):
        u, v = kaleidoscope(0.5, 0.5, segments=6)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 0.5) < 1e-9

    def test_returns_tuple(self):
        result = kaleidoscope(0.3, 0.7, segments=8)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_different_segments(self):
        # Use a point that falls in different segment indices for 4 vs 8
        r4 = kaleidoscope(0.52, 0.9, segments=4)
        r8 = kaleidoscope(0.52, 0.9, segments=8)
        # Different segment counts should produce different folded coordinates
        diff = abs(r4[0] - r8[0]) + abs(r4[1] - r8[1])
        assert diff > 1e-6


class TestTile:
    def test_single_tile_identity(self):
        u, v = tile(0.3, 0.7, cols=1, rows=1)
        assert abs(u - 0.3) < 1e-9
        assert abs(v - 0.7) < 1e-9

    def test_2x2_wraps(self):
        u, v = tile(0.75, 0.75, cols=2, rows=2)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 0.5) < 1e-9

    def test_result_in_unit_range(self):
        for cols in [2, 3, 5]:
            for val in [0.0, 0.25, 0.5, 0.99]:
                u, v = tile(val, val, cols=cols, rows=cols)
                assert 0.0 <= u < 1.0
                assert 0.0 <= v < 1.0


class TestRotateUV:
    def test_zero_rotation_identity(self):
        u, v = rotate_uv(0.3, 0.7, angle=0.0)
        assert abs(u - 0.3) < 1e-9
        assert abs(v - 0.7) < 1e-9

    def test_full_rotation_identity(self):
        u, v = rotate_uv(0.3, 0.7, angle=2 * math.pi)
        assert abs(u - 0.3) < 1e-6
        assert abs(v - 0.7) < 1e-6

    def test_quarter_turn(self):
        # Rotate (1,0.5) by 90 degrees around (0.5,0.5) -> (0.5, 1)
        u, v = rotate_uv(1.0, 0.5, angle=math.pi / 2, cx=0.5, cy=0.5)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 1.0) < 1e-9


class TestZoom:
    def test_zoom_center_unchanged(self):
        u, v = zoom(0.5, 0.5, factor=3.0)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 0.5) < 1e-9

    def test_zoom_in(self):
        u, v = zoom(0.75, 0.5, factor=2.0)
        # (0.75 - 0.5) / 2 + 0.5 = 0.625
        assert abs(u - 0.625) < 1e-9

    def test_zoom_out(self):
        u, v = zoom(0.75, 0.5, factor=0.5)
        # (0.75 - 0.5) / 0.5 + 0.5 = 1.0
        assert abs(u - 1.0) < 1e-9

    def test_zero_factor_returns_center(self):
        u, v = zoom(0.8, 0.2, factor=0, cx=0.5, cy=0.5)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 0.5) < 1e-9


class TestSpiralWarp:
    def test_center_unchanged(self):
        u, v = spiral_warp(0.5, 0.5, twist=5.0)
        assert abs(u - 0.5) < 1e-9
        assert abs(v - 0.5) < 1e-9

    def test_zero_twist_identity(self):
        u, v = spiral_warp(0.8, 0.3, twist=0.0)
        assert abs(u - 0.8) < 1e-6
        assert abs(v - 0.3) < 1e-6


class TestPolarRemap:
    def test_center_maps_to_zero_radius(self):
        theta, r = polar_remap(0.5, 0.5)
        assert abs(r) < 1e-9

    def test_returns_tuple(self):
        result = polar_remap(0.8, 0.3)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_theta_in_unit_range(self):
        for u in [0.0, 0.25, 0.5, 0.75, 1.0]:
            for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
                if u == 0.5 and v == 0.5:
                    continue  # center is degenerate
                theta, r = polar_remap(u, v)
                assert 0.0 <= theta <= 1.0


# ==================== Registry tests ====================


class TestTransformRegistry:
    def test_all_transforms_registered(self):
        expected = [
            "mirror_x", "mirror_y", "mirror_quad", "kaleidoscope",
            "tile", "rotate", "zoom", "spiral_warp", "polar_remap",
        ]
        for name in expected:
            assert name in TRANSFORM_REGISTRY

    def test_registry_values_callable(self):
        for name, fn in TRANSFORM_REGISTRY.items():
            assert callable(fn)


# ==================== TransformedEffect tests ====================


class TestTransformedEffect:
    def test_delegates_pre(self):
        stub = StubEffect()
        ctx = make_ctx()
        transformed = TransformedEffect(stub, [])
        state = transformed.pre(ctx, [])
        assert isinstance(state, dict)

    def test_delegates_post(self):
        stub = StubEffect()
        ctx = make_ctx()
        transformed = TransformedEffect(stub, [])
        # Should not raise
        transformed.post(ctx, [], {})

    def test_identity_chain_returns_same_cell(self):
        """Empty transform chain should produce same result as inner effect"""
        stub = StubEffect()
        ctx = make_ctx(w=32, h=32)
        transformed = TransformedEffect(stub, [])

        state_direct = stub.pre(ctx, [])
        state_wrapped = transformed.pre(ctx, [])

        for x in [0, 8, 16, 31]:
            for y in [0, 8, 16, 31]:
                cell_direct = stub.main(x, y, ctx, state_direct)
                cell_wrapped = transformed.main(x, y, ctx, state_wrapped)
                assert cell_direct.char_idx == cell_wrapped.char_idx
                assert cell_direct.fg == cell_wrapped.fg

    def test_mirror_x_produces_symmetry(self):
        """mirror_x transform should make left and right halves symmetric"""
        stub = StubEffect()
        ctx = make_ctx(w=32, h=32)
        transformed = TransformedEffect(stub, [(mirror_x, {})])
        state = transformed.pre(ctx, [])

        for y in [4, 8, 16]:
            cell_left = transformed.main(4, y, ctx, state)
            cell_right = transformed.main(27, y, ctx, state)
            assert cell_left.char_idx == cell_right.char_idx

    def test_tile_transform(self):
        """Tiling should repeat the pattern"""
        stub = StubEffect()
        ctx = make_ctx(w=32, h=32)
        transformed = TransformedEffect(stub, [(tile, {'cols': 2, 'rows': 2})])
        state = transformed.pre(ctx, [])

        # Point in first tile and corresponding point in second tile
        cell_a = transformed.main(4, 4, ctx, state)
        cell_b = transformed.main(20, 4, ctx, state)
        # With 2x tiling, x=4/32=0.125 maps to 0.25 and x=20/32=0.625 maps to 0.25
        assert cell_a.char_idx == cell_b.char_idx

    def test_chained_transforms(self):
        """Multiple transforms applied in sequence"""
        stub = StubEffect()
        ctx = make_ctx(w=32, h=32)
        chain = [
            (mirror_x, {}),
            (tile, {'cols': 2, 'rows': 1}),
        ]
        transformed = TransformedEffect(stub, chain)
        state = transformed.pre(ctx, [])
        # Should not raise
        cell = transformed.main(10, 10, ctx, state)
        assert isinstance(cell, Cell)

    def test_with_zero_size_context(self):
        """Edge case: zero-size context should not crash"""
        stub = StubEffect()
        ctx = make_ctx(w=0, h=0)
        transformed = TransformedEffect(stub, [(mirror_x, {})])
        state = transformed.pre(ctx, [])
        # main with x=0, y=0 on a 0x0 context: u=0, v=0
        cell = transformed.main(0, 0, ctx, state)
        assert isinstance(cell, Cell)

    def test_with_kaleidoscope(self):
        """Kaleidoscope transform should produce valid cells"""
        stub = StubEffect()
        ctx = make_ctx(w=64, h=64)
        transformed = TransformedEffect(stub, [(kaleidoscope, {'segments': 6})])
        state = transformed.pre(ctx, [])

        for x in range(0, 64, 8):
            for y in range(0, 64, 8):
                cell = transformed.main(x, y, ctx, state)
                assert isinstance(cell, Cell)
                assert 0 <= cell.char_idx <= 9
