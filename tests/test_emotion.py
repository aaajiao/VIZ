"""test procedural/flexible/emotion.py - EmotionVector, text_to_emotion, VAD_ANCHORS"""

import math
import pytest
from procedural.flexible.emotion import (
    EmotionVector,
    VAD_ANCHORS,
    text_to_emotion,
    emotion_from_name,
    blend_emotions,
)


class TestEmotionVector:
    def test_clamps_values(self):
        ev = EmotionVector(2.0, -2.0, 1.5)
        assert ev.valence == 1.0
        assert ev.arousal == -1.0
        assert ev.dominance == 1.0

    def test_as_tuple(self):
        ev = EmotionVector(0.5, -0.3, 0.7)
        assert ev.as_tuple() == (0.5, -0.3, 0.7)

    def test_magnitude(self):
        ev = EmotionVector(1.0, 0.0, 0.0)
        assert ev.magnitude() == 1.0

        ev2 = EmotionVector(0.0, 0.0, 0.0)
        assert ev2.magnitude() == 0.0

    def test_normalized(self):
        ev = EmotionVector(3.0, 4.0, 0.0)  # will be clamped to (1, 1, 0)
        norm = ev.normalized()
        assert abs(norm.magnitude() - 1.0) < 0.01

    def test_lerp(self):
        ev1 = EmotionVector(0.0, 0.0, 0.0)
        ev2 = EmotionVector(1.0, 1.0, 1.0)
        result = ev1.lerp(ev2, 0.5)
        assert result.valence == pytest.approx(0.5)
        assert result.arousal == pytest.approx(0.5)
        assert result.dominance == pytest.approx(0.5)

    def test_slerp(self):
        ev1 = EmotionVector(1.0, 0.0, 0.0)
        ev2 = EmotionVector(0.0, 1.0, 0.0)
        result = ev1.slerp(ev2, 0.5)
        assert result.valence > 0
        assert result.arousal > 0

    def test_distance(self):
        ev1 = EmotionVector(0.0, 0.0, 0.0)
        ev2 = EmotionVector(1.0, 0.0, 0.0)
        assert ev1.distance(ev2) == 1.0

    def test_to_visual_params(self):
        ev = EmotionVector(0.5, 0.5, 0.5)
        params = ev.to_visual_params()
        assert "warmth" in params
        assert "energy" in params
        assert "frequency" in params
        assert "valence" in params
        assert 0 <= params["warmth"] <= 1
        assert 0 <= params["energy"] <= 1


class TestVADAnchors:
    def test_basic_emotions_exist(self):
        required = ["joy", "fear", "sadness", "anger", "calm", "euphoria"]
        for name in required:
            assert name in VAD_ANCHORS

    def test_market_emotions_exist(self):
        assert "bull" in VAD_ANCHORS
        assert "bear" in VAD_ANCHORS
        assert "neutral" in VAD_ANCHORS

    def test_all_anchors_are_emotion_vectors(self):
        for name, ev in VAD_ANCHORS.items():
            assert isinstance(ev, EmotionVector)

    def test_bull_is_positive_valence(self):
        assert VAD_ANCHORS["bull"].valence > 0

    def test_bear_is_negative_valence(self):
        assert VAD_ANCHORS["bear"].valence < 0


class TestTextToEmotion:
    def test_positive_words(self):
        ev = text_to_emotion("surge rally gain rise")
        assert ev.valence > 0

    def test_negative_words(self):
        ev = text_to_emotion("crash panic fear collapse")
        assert ev.valence < 0
        assert ev.arousal > 0

    def test_empty_text(self):
        ev = text_to_emotion("")
        assert ev.valence == 0.0
        assert ev.arousal == 0.0
        assert ev.dominance == 0.0

    def test_chinese_keywords(self):
        ev = text_to_emotion("暴涨 牛市")
        assert ev.valence > 0

    def test_with_base_emotion(self):
        base = EmotionVector(0.5, 0.5, 0.5)
        ev = text_to_emotion("neutral text", base=base)
        assert ev.magnitude() > 0


class TestEmotionFromName:
    def test_known_emotion(self):
        ev = emotion_from_name("joy")
        assert ev == VAD_ANCHORS["joy"]

    def test_unknown_emotion_returns_neutral(self):
        ev = emotion_from_name("unknown_emotion_xyz")
        assert ev == VAD_ANCHORS["neutral"]

    def test_case_insensitive(self):
        ev = emotion_from_name("JOY")
        assert ev == VAD_ANCHORS["joy"]


class TestBlendEmotions:
    def test_empty_list(self):
        result = blend_emotions([])
        assert result.magnitude() == 0.0

    def test_single_emotion(self):
        ev = EmotionVector(0.5, 0.5, 0.5)
        result = blend_emotions([ev])
        assert result.valence == pytest.approx(0.5)

    def test_equal_weights(self):
        ev1 = EmotionVector(0.0, 0.0, 0.0)
        ev2 = EmotionVector(1.0, 1.0, 1.0)
        result = blend_emotions([ev1, ev2])
        assert result.valence == pytest.approx(0.5)

    def test_custom_weights(self):
        ev1 = EmotionVector(0.0, 0.0, 0.0)
        ev2 = EmotionVector(1.0, 1.0, 1.0)
        result = blend_emotions([ev1, ev2], weights=[0.25, 0.75])
        assert result.valence == pytest.approx(0.75)
