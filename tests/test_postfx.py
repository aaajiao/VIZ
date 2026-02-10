"""test procedural/postfx.py - post-processing FX chain"""

import pytest

from procedural.postfx import (
    postfx_threshold,
    postfx_invert,
    postfx_edge_detect,
    postfx_scanlines,
    postfx_vignette,
    postfx_pixelate,
    postfx_color_shift,
    POSTFX_REGISTRY,
)
from procedural.types import Cell


# ==================== Helpers ====================


def make_buffer(w, h, char_idx=5, fg=(128, 128, 128), bg=None):
    """Create a uniform buffer for testing"""
    return [[Cell(char_idx=char_idx, fg=fg, bg=bg) for _ in range(w)] for _ in range(h)]


def make_gradient_buffer(w, h):
    """Create a buffer with gradient char_idx values (0-9)"""
    return [
        [Cell(char_idx=min(9, int(9 * x / max(w - 1, 1))),
              fg=(int(255 * x / max(w - 1, 1)), int(255 * y / max(h - 1, 1)), 128),
              bg=None)
         for x in range(w)]
        for y in range(h)
    ]


# ==================== Registry tests ====================


class TestPostfxRegistry:
    def test_all_effects_registered(self):
        expected = [
            "threshold", "invert", "edge_detect", "scanlines",
            "vignette", "pixelate", "color_shift",
        ]
        for name in expected:
            assert name in POSTFX_REGISTRY

    def test_registry_values_callable(self):
        for name, fn in POSTFX_REGISTRY.items():
            assert callable(fn)


# ==================== Empty/edge case tests ====================


class TestEdgeCases:
    def test_all_effects_handle_empty_buffer(self):
        """No effect should crash on an empty buffer"""
        empty = []
        for name, fn in POSTFX_REGISTRY.items():
            fn(empty)  # should not raise

    def test_all_effects_handle_empty_rows(self):
        """Buffer with zero-width rows"""
        buf = [[], []]
        for name, fn in POSTFX_REGISTRY.items():
            fn(buf)

    def test_all_effects_handle_single_cell(self):
        """1x1 buffer"""
        for name, fn in POSTFX_REGISTRY.items():
            buf = make_buffer(1, 1, char_idx=5, fg=(100, 150, 200))
            fn(buf)
            assert isinstance(buf[0][0], Cell)


# ==================== Threshold tests ====================


class TestThreshold:
    def test_low_values_become_zero(self):
        buf = make_buffer(4, 4, char_idx=2)
        postfx_threshold(buf, threshold=0.5)
        for row in buf:
            for cell in row:
                assert cell.char_idx == 0

    def test_high_values_become_nine(self):
        buf = make_buffer(4, 4, char_idx=8)
        postfx_threshold(buf, threshold=0.5)
        for row in buf:
            for cell in row:
                assert cell.char_idx == 9

    def test_preserves_colors(self):
        buf = make_buffer(2, 2, char_idx=7, fg=(100, 200, 50))
        postfx_threshold(buf, threshold=0.5)
        assert buf[0][0].fg == (100, 200, 50)

    def test_threshold_at_boundary(self):
        """char_idx exactly at threshold should go to 9"""
        buf = make_buffer(2, 2, char_idx=4)
        postfx_threshold(buf, threshold=0.5)  # thresh_idx = 4
        assert buf[0][0].char_idx == 9


# ==================== Invert tests ====================


class TestInvert:
    def test_char_idx_inverted(self):
        buf = make_buffer(2, 2, char_idx=3)
        postfx_invert(buf)
        assert buf[0][0].char_idx == 6

    def test_fg_inverted(self):
        buf = make_buffer(2, 2, fg=(100, 150, 200))
        postfx_invert(buf)
        assert buf[0][0].fg == (155, 105, 55)

    def test_bg_inverted_when_present(self):
        buf = make_buffer(2, 2, fg=(0, 0, 0), bg=(100, 100, 100))
        postfx_invert(buf)
        assert buf[0][0].bg == (155, 155, 155)

    def test_bg_stays_none(self):
        buf = make_buffer(2, 2, fg=(0, 0, 0), bg=None)
        postfx_invert(buf)
        assert buf[0][0].bg is None

    def test_double_invert_restores(self):
        buf = make_buffer(4, 4, char_idx=7, fg=(50, 100, 200))
        postfx_invert(buf)
        postfx_invert(buf)
        assert buf[0][0].char_idx == 7
        assert buf[0][0].fg == (50, 100, 200)


# ==================== Edge detect tests ====================


class TestEdgeDetect:
    def test_uniform_buffer_zero_edges(self):
        """Uniform buffer should have zero gradients in interior"""
        buf = make_buffer(8, 8, char_idx=5)
        postfx_edge_detect(buf)
        # Interior pixels should be 0 (no gradient)
        assert buf[4][4].char_idx == 0

    def test_gradient_buffer_detects_edges(self):
        """Buffer with gradient should have non-zero edge values"""
        buf = make_gradient_buffer(16, 16)
        postfx_edge_detect(buf)
        # Some interior pixels should have non-zero edge magnitude
        has_edge = any(
            buf[y][x].char_idx > 0
            for y in range(1, 15)
            for x in range(1, 15)
        )
        assert has_edge

    def test_preserves_border(self):
        """Border pixels should not be modified"""
        buf = make_gradient_buffer(8, 8)
        border_before = buf[0][0].char_idx
        postfx_edge_detect(buf)
        assert buf[0][0].char_idx == border_before

    def test_too_small_buffer_no_crash(self):
        """Buffer smaller than 3x3 should be handled gracefully"""
        buf = make_buffer(2, 2, char_idx=5)
        postfx_edge_detect(buf)  # should not raise
        assert buf[0][0].char_idx == 5  # unchanged


# ==================== Scanlines tests ====================


class TestScanlines:
    def test_darkens_scanline_rows(self):
        buf = make_buffer(4, 8, char_idx=9, fg=(200, 200, 200))
        postfx_scanlines(buf, spacing=4, darkness=0.5)
        # Row 0 and 4 should be darkened
        assert buf[0][0].fg[0] < 200
        # Row 1 should be unchanged
        assert buf[1][0].fg == (200, 200, 200)

    def test_spacing_controls_frequency(self):
        buf = make_buffer(4, 12, char_idx=9, fg=(200, 200, 200))
        postfx_scanlines(buf, spacing=3, darkness=0.5)
        # Rows 0, 3, 6, 9 should be darkened
        assert buf[3][0].fg[0] < 200
        assert buf[6][0].fg[0] < 200
        # Row 1 unchanged
        assert buf[1][0].fg == (200, 200, 200)

    def test_zero_darkness_no_change(self):
        buf = make_buffer(4, 4, char_idx=5, fg=(100, 100, 100))
        postfx_scanlines(buf, spacing=2, darkness=0.0)
        assert buf[0][0].fg == (100, 100, 100)


# ==================== Vignette tests ====================


class TestVignette:
    def test_center_brighter_than_corners(self):
        buf = make_buffer(16, 16, char_idx=9, fg=(200, 200, 200))
        postfx_vignette(buf, strength=1.0)
        center = buf[8][8]
        corner = buf[0][0]
        assert center.fg[0] > corner.fg[0]

    def test_zero_strength_no_change(self):
        buf = make_buffer(8, 8, char_idx=5, fg=(100, 100, 100))
        postfx_vignette(buf, strength=0.0)
        assert buf[0][0].fg == (100, 100, 100)
        assert buf[4][4].fg == (100, 100, 100)

    def test_high_strength_darkens_corners(self):
        buf = make_buffer(16, 16, char_idx=9, fg=(255, 255, 255))
        postfx_vignette(buf, strength=2.0)
        corner = buf[0][0]
        assert corner.fg[0] < 255


# ==================== Pixelate tests ====================


class TestPixelate:
    def test_block_averaging(self):
        """After pixelation, all cells in a block should be identical"""
        buf = make_gradient_buffer(8, 8)
        postfx_pixelate(buf, block_size=4)
        # All cells in the first 4x4 block should be the same
        ref = buf[0][0]
        for dy in range(4):
            for dx in range(4):
                assert buf[dy][dx].char_idx == ref.char_idx
                assert buf[dy][dx].fg == ref.fg

    def test_block_size_1_preserves_original(self):
        """Block size 1 should effectively be a no-op on values"""
        buf = make_gradient_buffer(4, 4)
        original = [[buf[y][x].char_idx for x in range(4)] for y in range(4)]
        postfx_pixelate(buf, block_size=1)
        for y in range(4):
            for x in range(4):
                assert buf[y][x].char_idx == original[y][x]

    def test_non_divisible_size(self):
        """Buffer size not divisible by block_size should not crash"""
        buf = make_gradient_buffer(7, 5)
        postfx_pixelate(buf, block_size=3)
        # Just verify no crash and cells are valid
        for row in buf:
            for cell in row:
                assert isinstance(cell, Cell)


# ==================== Color shift tests ====================


class TestColorShift:
    def test_zero_shift_preserves_colors(self):
        buf = make_buffer(4, 4, fg=(100, 150, 200))
        postfx_color_shift(buf, hue_shift=0.0)
        r, g, b = buf[0][0].fg
        # Allow rounding tolerance of 1 due to float->int conversion
        assert abs(r - 100) <= 1
        assert abs(g - 150) <= 1
        assert abs(b - 200) <= 1

    def test_full_rotation_preserves_colors(self):
        """Full 360-degree hue rotation should return to original"""
        buf = make_buffer(4, 4, fg=(100, 150, 200))
        postfx_color_shift(buf, hue_shift=1.0)
        # Should be very close to original (within rounding)
        r, g, b = buf[0][0].fg
        assert abs(r - 100) <= 1
        assert abs(g - 150) <= 1
        assert abs(b - 200) <= 1

    def test_shift_changes_colors(self):
        buf = make_buffer(4, 4, fg=(200, 50, 50))
        postfx_color_shift(buf, hue_shift=0.33)
        # Colors should be different after significant hue shift
        assert buf[0][0].fg != (200, 50, 50)

    def test_preserves_char_idx(self):
        buf = make_buffer(4, 4, char_idx=7, fg=(100, 100, 100))
        postfx_color_shift(buf, hue_shift=0.25)
        assert buf[0][0].char_idx == 7

    def test_colors_stay_in_range(self):
        """All color values should remain in 0-255"""
        buf = make_buffer(4, 4, fg=(255, 0, 128))
        for shift in [0.1, 0.25, 0.5, 0.75]:
            b = make_buffer(4, 4, fg=(255, 0, 128))
            postfx_color_shift(b, hue_shift=shift)
            r, g, bl = b[0][0].fg
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= bl <= 255
