"""
内容数据结构 - Content Data Structure

统一的内容结构，由 AI 通过 stdin JSON 传入，供渲染层使用。
Unified content structure passed by AI via stdin JSON for rendering layer.
"""

from datetime import datetime


def make_content(data=None):
    """
    创建标准化的 Content 字典 - Create standardized Content dict

    Args:
        data: raw dict from JSON input (optional)

    Returns:
        normalized Content dict with all fields populated
    """
    if data is None:
        data = {}

    return {
        "source": data.get("source", None),
        "headline": data.get("headline", None),
        "metrics": data.get("metrics", []),
        "body": data.get("body", None),
        "emotion": data.get("emotion", None),
        "vad": data.get("vad", None),
        "timestamp": data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "meta": data.get("meta", {}),
        "vocabulary": data.get("vocabulary", {}),
        "effect": data.get("effect", None),
        "seed": data.get("seed", None),
        "params": data.get("params", {}),
        "layout": data.get("layout", None),
        "decoration": data.get("decoration", None),
        "gradient": data.get("gradient", None),
        "overlay": data.get("overlay", None),
        "video": data.get("video", False),
        "duration": data.get("duration", 3.0),
        "fps": data.get("fps", 15),
        "variants": data.get("variants", 1),
        "title": data.get("title", None),
    }


def content_has_data(content):
    """
    检查 content 是否包含实际数据 - Check if content has actual data

    Returns True if headline, metrics, or body is present.
    """
    return bool(content.get("headline") or content.get("metrics") or content.get("body"))
