"""test lib/content.py - make_content, content_has_data"""

import pytest
from lib.content import make_content, content_has_data


class TestMakeContent:
    def test_empty_input_returns_defaults(self):
        result = make_content()
        assert result["headline"] is None
        assert result["metrics"] == []
        assert result["duration"] == 3.0
        assert result["fps"] == 15
        assert result["variants"] == 1

    def test_preserves_provided_values(self):
        data = {
            "headline": "Test Headline",
            "emotion": "bull",
        }
        result = make_content(data)
        assert result["headline"] == "Test Headline"
        assert result["emotion"] == "bull"

    def test_truncates_long_headline(self):
        long_headline = "x" * 200
        result = make_content({"headline": long_headline})
        assert len(result["headline"]) == 123  # 120 + "..."
        assert result["headline"].endswith("...")

    def test_truncates_long_title(self):
        long_title = "y" * 100
        result = make_content({"title": long_title})
        assert len(result["title"]) == 83  # 80 + "..."

    def test_truncates_long_body(self):
        long_body = "z" * 600
        result = make_content({"body": long_body})
        assert len(result["body"]) == 503  # 500 + "..."

    def test_limits_metrics_count(self):
        metrics = [f"metric_{i}" for i in range(20)]
        result = make_content({"metrics": metrics})
        assert len(result["metrics"]) == 10

    def test_truncates_long_metric(self):
        metrics = ["x" * 100]
        result = make_content({"metrics": metrics})
        assert len(result["metrics"][0]) == 63  # 60 + "..."

    def test_clamps_duration_min(self):
        result = make_content({"duration": 0.01})
        assert result["duration"] == 0.1

    def test_clamps_duration_max(self):
        result = make_content({"duration": 100})
        assert result["duration"] == 30.0

    def test_clamps_fps_min(self):
        result = make_content({"fps": 0})
        assert result["fps"] == 1

    def test_clamps_fps_max(self):
        result = make_content({"fps": 120})
        assert result["fps"] == 60

    def test_clamps_variants_min(self):
        result = make_content({"variants": -5})
        assert result["variants"] == 1

    def test_clamps_variants_max(self):
        result = make_content({"variants": 100})
        assert result["variants"] == 20

    def test_handles_invalid_duration_type(self):
        result = make_content({"duration": "invalid"})
        assert result["duration"] == 3.0

    def test_handles_invalid_fps_type(self):
        result = make_content({"fps": "invalid"})
        assert result["fps"] == 15

    def test_filters_non_string_metrics(self):
        metrics = ["valid", 123, "also_valid", None]
        result = make_content({"metrics": metrics})
        assert result["metrics"] == ["valid", "also_valid"]


class TestContentHasData:
    def test_returns_false_for_empty_content(self):
        content = make_content()
        assert content_has_data(content) is False

    def test_returns_true_with_headline(self):
        content = make_content({"headline": "Test"})
        assert content_has_data(content) is True

    def test_returns_true_with_metrics(self):
        content = make_content({"metrics": ["metric1"]})
        assert content_has_data(content) is True

    def test_returns_true_with_body(self):
        content = make_content({"body": "Some body text"})
        assert content_has_data(content) is True

    def test_returns_false_with_only_emotion(self):
        content = make_content({"emotion": "bull"})
        assert content_has_data(content) is False
