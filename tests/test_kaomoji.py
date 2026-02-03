"""test lib/kaomoji.py - kaomoji selection logic"""

import random
import pytest
from lib.kaomoji import _normalize_mood, get_moods_by_category, _hex_to_rgb
from lib.kaomoji_data import KAOMOJI_SINGLE, MOOD_CATEGORIES


class TestNormalizeMood:
    def test_exact_match_in_kaomoji_single(self):
        for mood in list(KAOMOJI_SINGLE.keys())[:5]:
            assert _normalize_mood(mood) == mood

    def test_bull_category_moods(self):
        if "bull" in MOOD_CATEGORIES:
            for mood in MOOD_CATEGORIES["bull"]:
                result = _normalize_mood(mood)
                assert result in KAOMOJI_SINGLE or result == "bull"

    def test_bear_category_moods(self):
        if "bear" in MOOD_CATEGORIES:
            for mood in MOOD_CATEGORIES["bear"]:
                result = _normalize_mood(mood)
                assert result in KAOMOJI_SINGLE or result == "bear"

    def test_unknown_mood_returns_neutral(self):
        result = _normalize_mood("completely_unknown_mood_xyz")
        assert result == "neutral"

    def test_case_insensitive(self):
        result1 = _normalize_mood("happy")
        result2 = _normalize_mood("HAPPY")
        assert result1 == result2


class TestGetMoodsByCategory:
    def test_bull_category(self):
        moods = get_moods_by_category("bull")
        assert isinstance(moods, list)

    def test_bear_category(self):
        moods = get_moods_by_category("bear")
        assert isinstance(moods, list)

    def test_neutral_category(self):
        moods = get_moods_by_category("neutral")
        assert isinstance(moods, list)

    def test_unknown_category_returns_neutral(self):
        moods = get_moods_by_category("unknown_category")
        assert moods == MOOD_CATEGORIES.get("neutral", [])


class TestHexToRgb:
    def test_red(self):
        assert _hex_to_rgb("#FF0000") == (255, 0, 0)

    def test_green(self):
        assert _hex_to_rgb("#00FF00") == (0, 255, 0)

    def test_blue(self):
        assert _hex_to_rgb("#0000FF") == (0, 0, 255)

    def test_without_hash(self):
        assert _hex_to_rgb("FF0000") == (255, 0, 0)

    def test_lowercase(self):
        assert _hex_to_rgb("#ff00ff") == (255, 0, 255)


class TestKaomojiData:
    def test_kaomoji_single_not_empty(self):
        assert len(KAOMOJI_SINGLE) > 0

    def test_each_mood_has_faces(self):
        for mood, faces in KAOMOJI_SINGLE.items():
            assert len(faces) > 0, f"{mood} has no faces"

    def test_mood_categories_cover_expected(self):
        expected = {"bull", "bear", "neutral"}
        actual = set(MOOD_CATEGORIES.keys())
        assert expected.issubset(actual)
