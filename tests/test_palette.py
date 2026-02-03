"""test procedural/palette.py - ASCII gradients and color schemes"""

import pytest
from procedural.palette import (
    ASCII_GRADIENTS,
    COLOR_SCHEMES,
    char_at_value,
    value_to_color,
    value_to_color_continuous,
)


class TestASCIIGradients:
    def test_classic_exists(self):
        assert "classic" in ASCII_GRADIENTS

    def test_blocks_exists(self):
        assert "blocks" in ASCII_GRADIENTS

    def test_default_exists(self):
        assert "default" in ASCII_GRADIENTS

    def test_gradients_non_empty(self):
        for name, gradient in ASCII_GRADIENTS.items():
            assert len(gradient) > 0


class TestColorSchemes:
    def test_heat_exists(self):
        assert "heat" in COLOR_SCHEMES

    def test_rainbow_exists(self):
        assert "rainbow" in COLOR_SCHEMES


class TestCharAtValue:
    def test_zero_returns_first_char(self):
        char = char_at_value(0.0, "classic")
        assert char == " "

    def test_one_returns_last_char(self):
        char = char_at_value(1.0, "classic")
        assert char == ASCII_GRADIENTS["classic"][-1]

    def test_mid_value(self):
        char = char_at_value(0.5, "classic")
        gradient = ASCII_GRADIENTS["classic"]
        mid_idx = len(gradient) // 2
        assert char in gradient

    def test_clamps_negative(self):
        char = char_at_value(-0.5, "classic")
        assert char == " "

    def test_clamps_above_one(self):
        char = char_at_value(1.5, "classic")
        assert char == ASCII_GRADIENTS["classic"][-1]

    def test_unknown_gradient_uses_default(self):
        char = char_at_value(0.5, "nonexistent")
        char_default = char_at_value(0.5, "default")
        assert char == char_default

    def test_blocks_gradient(self):
        for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
            char = char_at_value(v, "blocks")
            assert char in ASCII_GRADIENTS["blocks"]


class TestValueToColor:
    def test_returns_rgb_tuple(self):
        color = value_to_color(0.5, "heat")
        assert isinstance(color, tuple)
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)

    def test_heat_black_at_zero(self):
        color = value_to_color(0.0, "heat")
        assert color == (0, 0, 0)

    def test_heat_white_at_one(self):
        color = value_to_color(1.0, "heat")
        r, g, b = color
        assert r == 255
        assert g == 255
        assert b == 255

    def test_rainbow_varies_hue(self):
        colors = [value_to_color(v, "rainbow") for v in [0.0, 0.33, 0.66, 1.0]]
        assert len(set(colors)) > 1

    def test_cool_blue_dominant_at_start(self):
        color = value_to_color(0.0, "cool")
        r, g, b = color
        assert b >= r and b >= g

    def test_matrix_green_only(self):
        for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
            color = value_to_color(v, "matrix")
            r, g, b = color
            assert r == 0
            assert b == 0

    def test_unknown_scheme_uses_heat(self):
        color = value_to_color(0.5, "nonexistent")
        expected = value_to_color(0.5, "heat")
        assert color == expected

    def test_clamps_input(self):
        color_neg = value_to_color(-0.5, "heat")
        color_zero = value_to_color(0.0, "heat")
        assert color_neg == color_zero

        color_high = value_to_color(1.5, "heat")
        color_one = value_to_color(1.0, "heat")
        assert color_high == color_one


class TestValueToColorContinuous:
    def test_returns_rgb_tuple(self):
        color = value_to_color_continuous(0.5, warmth=0.5, saturation=1.0)
        assert isinstance(color, tuple)
        assert len(color) == 3

    def test_components_in_range(self):
        for v in [0.0, 0.25, 0.5, 0.75, 1.0]:
            for w in [0.0, 0.5, 1.0]:
                color = value_to_color_continuous(v, warmth=w)
                assert all(0 <= c <= 255 for c in color)

    def test_warmth_affects_hue(self):
        cold = value_to_color_continuous(0.5, warmth=0.0)
        warm = value_to_color_continuous(0.5, warmth=1.0)
        assert cold != warm

    def test_saturation_zero_approaches_gray(self):
        color = value_to_color_continuous(0.5, warmth=0.5, saturation=0.0)
        r, g, b = color
        diff = max(abs(r - g), abs(g - b), abs(r - b))
        assert diff < 50
