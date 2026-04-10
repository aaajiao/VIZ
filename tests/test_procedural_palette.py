"""test procedural palette - tests for generate_palette and resolve_color"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procedural.palette import generate_palette, resolve_color, value_to_color

class TestGeneratePalette:
    def test_returns_16_colors(self):
        p = generate_palette(42)
        assert len(p) == 16

    def test_colors_are_rgb_tuples(self):
        p = generate_palette(42)
        for r, g, b in p:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_lightness_monotonically_increasing(self):
        """Palette should go from dark to light"""
        p = generate_palette(42)
        lumas = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in p]
        for i in range(1, len(lumas)):
            assert lumas[i] >= lumas[i-1] - 5, f"Lightness decreased at index {i}: {lumas[i-1]:.1f} -> {lumas[i]:.1f}"

    def test_deterministic_same_seed(self):
        assert generate_palette(42) == generate_palette(42)
        assert generate_palette(100) == generate_palette(100)

    def test_different_seeds_different_palettes(self):
        p1 = generate_palette(1)
        p2 = generate_palette(2)
        p3 = generate_palette(3)
        # At least 2 of 3 should differ
        assert p1 != p2 or p2 != p3

    def test_warmth_affects_hue(self):
        """Warm palettes should have more red/orange, cool more blue"""
        warm = generate_palette(42, warmth=0.9)
        cool = generate_palette(42, warmth=0.1)
        # Check mid-palette color (index 8)
        # Warm should have more red, cool should have more blue
        assert warm[8][0] > cool[8][0] or cool[8][2] > warm[8][2], \
            f"Warmth didn't affect hues: warm={warm[8]}, cool={cool[8]}"

    def test_many_seeds_all_unique(self):
        """100 seeds should produce 100 unique palettes"""
        palettes = [tuple(tuple(c) for c in generate_palette(s)) for s in range(100)]
        unique = len(set(palettes))
        assert unique >= 95, f"Only {unique} unique palettes out of 100"


class TestResolveColor:
    def test_palette_takes_priority(self):
        palette = [(0,0,0)] * 8 + [(255,255,255)] * 8
        c = resolve_color(0.0, palette=palette)
        assert c == (0, 0, 0)

    def test_warmth_fallback(self):
        c = resolve_color(0.5, warmth=0.8, saturation=0.9)
        assert isinstance(c, tuple) and len(c) == 3

    def test_scheme_fallback(self):
        c = resolve_color(0.5, color_scheme="fire")
        expected = value_to_color(0.5, "fire")
        assert c == expected

    def test_default_fallback(self):
        c = resolve_color(0.5)
        expected = value_to_color(0.5, "heat")
        assert c == expected

    def test_clamps_value(self):
        c_lo = resolve_color(-0.5, color_scheme="heat")
        c_zero = resolve_color(0.0, color_scheme="heat")
        assert c_lo == c_zero
        c_hi = resolve_color(1.5, color_scheme="heat")
        c_one = resolve_color(1.0, color_scheme="heat")
        assert c_hi == c_one
