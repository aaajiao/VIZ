"""test lib/vocabulary.py - get_vocabulary (override-only)"""

import pytest
from lib.vocabulary import get_vocabulary


class TestGetVocabulary:
    def test_returns_empty_dict_for_none(self):
        vocab = get_vocabulary(None)
        assert vocab == {}

    def test_returns_empty_dict_for_no_args(self):
        vocab = get_vocabulary()
        assert vocab == {}

    def test_returns_empty_dict_for_empty_overrides(self):
        vocab = get_vocabulary({})
        assert vocab == {}

    def test_returns_overrides(self):
        overrides = {"particles": "ABC123", "kaomoji_moods": ["joy", "fear"]}
        vocab = get_vocabulary(overrides)
        assert vocab["particles"] == "ABC123"
        assert vocab["kaomoji_moods"] == ["joy", "fear"]

    def test_returns_copy_not_reference(self):
        overrides = {"particles": "XYZ"}
        vocab = get_vocabulary(overrides)
        vocab["particles"] = "MODIFIED"
        assert overrides["particles"] == "XYZ"
