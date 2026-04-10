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
        assert result["_warnings"] == []

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

    def test_meta_field_removed(self):
        result = make_content({"meta": {"key": "value"}})
        assert "meta" not in result


class TestContentWarnings:
    def test_no_warnings_for_valid_input(self):
        result = make_content({"emotion": "joy", "duration": 3.0, "fps": 15})
        assert result["_warnings"] == []

    def test_warnings_for_clamped_duration(self):
        result = make_content({"duration": 100})
        warnings = result["_warnings"]
        assert any("duration clamped" in w for w in warnings)

    def test_warnings_for_clamped_fps(self):
        result = make_content({"fps": 120})
        warnings = result["_warnings"]
        assert any("fps clamped" in w for w in warnings)

    def test_warnings_for_clamped_variants(self):
        result = make_content({"variants": 100})
        warnings = result["_warnings"]
        assert any("variants clamped" in w for w in warnings)

    def test_warnings_for_truncated_headline(self):
        result = make_content({"headline": "x" * 200})
        warnings = result["_warnings"]
        assert any("headline truncated" in w for w in warnings)

    def test_warnings_for_truncated_title(self):
        result = make_content({"title": "y" * 100})
        warnings = result["_warnings"]
        assert any("title truncated" in w for w in warnings)

    def test_warnings_for_truncated_body(self):
        result = make_content({"body": "z" * 600})
        warnings = result["_warnings"]
        assert any("body truncated" in w for w in warnings)

    def test_warnings_for_dropped_palette_bad_type(self):
        result = make_content({"palette": "bad"})
        warnings = result["_warnings"]
        assert any("palette dropped" in w for w in warnings)

    def test_warnings_for_dropped_palette_too_few(self):
        result = make_content({"palette": [[255, 0, 0]]})
        warnings = result["_warnings"]
        assert any("palette dropped" in w for w in warnings)

    def test_warnings_for_clamped_width(self):
        result = make_content({"width": 5})
        warnings = result["_warnings"]
        assert any("width clamped" in w for w in warnings)

    def test_warnings_for_clamped_height(self):
        result = make_content({"height": 5000})
        warnings = result["_warnings"]
        assert any("height clamped" in w for w in warnings)

    def test_warnings_for_invalid_duration_type(self):
        result = make_content({"duration": "bad"})
        warnings = result["_warnings"]
        assert any("duration" in w for w in warnings)

    def test_warnings_for_invalid_width_type(self):
        result = make_content({"width": "bad"})
        warnings = result["_warnings"]
        assert any("width ignored" in w for w in warnings)
        assert result["width"] is None

    def test_warnings_for_filtered_non_string_metric(self):
        result = make_content({"metrics": ["valid", 123]})
        warnings = result["_warnings"]
        assert any("non-string metric dropped" in w for w in warnings)

    def test_warnings_for_metrics_count_trimmed(self):
        metrics = [f"m{i}" for i in range(15)]
        result = make_content({"metrics": metrics})
        warnings = result["_warnings"]
        assert any("metrics trimmed" in w for w in warnings)

    def test_multiple_warnings_accumulate(self):
        result = make_content({"duration": 100, "fps": 120, "headline": "x" * 200})
        warnings = result["_warnings"]
        assert len(warnings) >= 3


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
