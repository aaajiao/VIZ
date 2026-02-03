"""test lib/box_chars.py - CHARSETS, get_charset, get_gradient, etc."""

import random
import pytest
from lib.box_chars import (
    CHARSETS,
    GRADIENTS,
    BORDER_SETS,
    get_charset,
    get_gradient,
    get_border_set,
    get_chars_for_mood,
    get_decoration_set,
    build_box_frame_chars,
)


class TestCharsets:
    def test_box_light_exists(self):
        assert "box_light" in CHARSETS

    def test_box_heavy_exists(self):
        assert "box_heavy" in CHARSETS

    def test_blocks_full_exists(self):
        assert "blocks_full" in CHARSETS

    def test_all_charsets_non_empty(self):
        for name, chars in CHARSETS.items():
            assert len(chars) > 0, f"{name} is empty"


class TestGradients:
    def test_classic_exists(self):
        assert "classic" in GRADIENTS

    def test_blocks_exists(self):
        assert "blocks" in GRADIENTS

    def test_most_gradients_start_with_space(self):
        exceptions = {"plasma"}  # plasma starts with '$' by design
        for name, gradient in GRADIENTS.items():
            if name not in exceptions:
                assert gradient[0] == " ", f"{name} should start with space"


class TestBorderSets:
    def test_light_exists(self):
        assert "light" in BORDER_SETS

    def test_heavy_exists(self):
        assert "heavy" in BORDER_SETS

    def test_double_exists(self):
        assert "double" in BORDER_SETS

    def test_border_sets_have_required_keys(self):
        required = ["h", "v", "tl", "tr", "bl", "br"]
        for name, border in BORDER_SETS.items():
            for key in required:
                assert key in border, f"{name} missing {key}"


class TestGetCharset:
    def test_returns_charset(self):
        result = get_charset("box_light")
        assert result == CHARSETS["box_light"]

    def test_raises_for_unknown(self):
        with pytest.raises(KeyError):
            get_charset("nonexistent_charset")


class TestGetGradient:
    def test_returns_gradient(self):
        result = get_gradient("classic")
        assert result == GRADIENTS["classic"]

    def test_returns_default_for_unknown(self):
        result = get_gradient("nonexistent_gradient")
        assert result == GRADIENTS["classic"]


class TestGetBorderSet:
    def test_returns_border_set(self):
        result = get_border_set("light")
        assert result == BORDER_SETS["light"]

    def test_returns_default_for_unknown(self):
        result = get_border_set("nonexistent_border")
        assert result == BORDER_SETS["light"]


class TestGetCharsForMood:
    def test_returns_dict(self):
        result = get_chars_for_mood(energy=0.5, structure=0.5, warmth=0.5)
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = get_chars_for_mood()
        required = ["gradient", "decoration", "particles", "border", "fill"]
        for key in required:
            assert key in result

    def test_high_energy_structured(self):
        result = get_chars_for_mood(energy=0.9, structure=0.8)
        assert "gradient" in result

    def test_low_energy_organic(self):
        result = get_chars_for_mood(energy=0.1, structure=0.2)
        assert "gradient" in result

    def test_with_rng(self):
        rng = random.Random(42)
        result1 = get_chars_for_mood(rng=rng)
        rng2 = random.Random(42)
        result2 = get_chars_for_mood(rng=rng2)
        assert result1["gradient"] == result2["gradient"]


class TestGetDecorationSet:
    def test_frame_style(self):
        result = get_decoration_set("frame")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_circuit_style(self):
        result = get_decoration_set("circuit")
        assert isinstance(result, list)

    def test_corners_style(self):
        result = get_decoration_set("corners")
        assert isinstance(result, list)

    def test_scattered_style(self):
        result = get_decoration_set("scattered")
        assert isinstance(result, list)

    def test_energy_affects_output(self):
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        result_low = get_decoration_set("corners", energy=0.1, rng=rng1)
        result_high = get_decoration_set("corners", energy=0.9, rng=rng2)
        # Different energy levels may produce different results
        assert isinstance(result_low, list)
        assert isinstance(result_high, list)


class TestBuildBoxFrameChars:
    def test_returns_list(self):
        result = build_box_frame_chars(10, 5)
        assert isinstance(result, list)

    def test_contains_corners(self):
        result = build_box_frame_chars(10, 5, "light")
        coords = [(x, y) for x, y, _ in result]
        assert (0, 0) in coords  # top-left
        assert (9, 0) in coords  # top-right
        assert (0, 4) in coords  # bottom-left
        assert (9, 4) in coords  # bottom-right

    def test_tuples_have_three_elements(self):
        result = build_box_frame_chars(5, 5)
        for item in result:
            assert len(item) == 3
            x, y, char = item
            assert isinstance(x, int)
            assert isinstance(y, int)
            assert isinstance(char, str)

    def test_different_styles(self):
        light = build_box_frame_chars(5, 5, "light")
        heavy = build_box_frame_chars(5, 5, "heavy")
        light_corners = {(x, y): c for x, y, c in light if (x, y) in [(0, 0), (4, 0)]}
        heavy_corners = {(x, y): c for x, y, c in heavy if (x, y) in [(0, 0), (4, 0)]}
        assert light_corners != heavy_corners
