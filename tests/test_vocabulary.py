"""test lib/vocabulary.py - get_vocabulary, VOCABULARIES"""

import pytest
from lib.vocabulary import get_vocabulary, VOCABULARIES, DEFAULT_VOCABULARY


class TestVocabularies:
    def test_market_vocabulary_exists(self):
        assert "market" in VOCABULARIES
        assert "particles" in VOCABULARIES["market"]
        assert "kaomoji_moods" in VOCABULARIES["market"]

    def test_art_vocabulary_exists(self):
        assert "art" in VOCABULARIES

    def test_news_vocabulary_exists(self):
        assert "news" in VOCABULARIES

    def test_mood_vocabulary_exists(self):
        assert "mood" in VOCABULARIES

    def test_all_vocabularies_have_required_keys(self):
        required_keys = [
            "particles",
            "kaomoji_moods",
            "symbols",
            "decoration_chars",
            "ambient_words",
        ]
        for source, vocab in VOCABULARIES.items():
            for key in required_keys:
                assert key in vocab, f"{source} missing {key}"


class TestGetVocabulary:
    def test_returns_market_vocabulary(self):
        vocab = get_vocabulary("market")
        assert vocab["particles"] == VOCABULARIES["market"]["particles"]

    def test_returns_default_for_none(self):
        vocab = get_vocabulary(None)
        assert vocab["particles"] == DEFAULT_VOCABULARY["particles"]

    def test_returns_default_for_unknown_source(self):
        vocab = get_vocabulary("unknown_source")
        assert vocab["particles"] == DEFAULT_VOCABULARY["particles"]

    def test_applies_overrides(self):
        overrides = {"particles": "ABC123"}
        vocab = get_vocabulary("market", overrides)
        assert vocab["particles"] == "ABC123"
        assert vocab["kaomoji_moods"] == VOCABULARIES["market"]["kaomoji_moods"]

    def test_override_does_not_modify_original(self):
        original_particles = VOCABULARIES["market"]["particles"]
        get_vocabulary("market", {"particles": "OVERRIDE"})
        assert VOCABULARIES["market"]["particles"] == original_particles

    def test_returns_copy_not_reference(self):
        vocab = get_vocabulary("market")
        vocab["particles"] = "MODIFIED"
        assert VOCABULARIES["market"]["particles"] != "MODIFIED"
