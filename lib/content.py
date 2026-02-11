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

    # Truncate text fields to safe lengths for rendering
    _MAX_HEADLINE = 120
    _MAX_TITLE = 80
    _MAX_BODY = 500
    _MAX_METRIC_LEN = 60
    _MAX_METRICS = 10

    if data.get("headline") and len(data["headline"]) > _MAX_HEADLINE:
        data["headline"] = data["headline"][:_MAX_HEADLINE] + "..."
    if data.get("title") and len(data["title"]) > _MAX_TITLE:
        data["title"] = data["title"][:_MAX_TITLE] + "..."
    if data.get("body") and len(data["body"]) > _MAX_BODY:
        data["body"] = data["body"][:_MAX_BODY] + "..."
    if data.get("metrics"):
        metrics = data["metrics"][:_MAX_METRICS]
        data["metrics"] = [
            m[:_MAX_METRIC_LEN] + "..." if len(m) > _MAX_METRIC_LEN else m
            for m in metrics
            if isinstance(m, str)
        ]

    # Clamp numeric params to safe ranges
    duration = data.get("duration", 3.0)
    try:
        duration = float(duration)
    except (TypeError, ValueError):
        duration = 3.0
    duration = max(0.1, min(duration, 30.0))

    fps = data.get("fps", 15)
    try:
        fps = int(fps)
    except (TypeError, ValueError):
        fps = 15
    fps = max(1, min(fps, 60))

    variants = data.get("variants", 1)
    try:
        variants = int(variants)
    except (TypeError, ValueError):
        variants = 1
    variants = max(1, min(variants, 20))

    # Validate palette if provided
    palette = data.get("palette", None)
    if palette is not None:
        if isinstance(palette, list) and len(palette) >= 2:
            validated = []
            for color in palette:
                if isinstance(color, (list, tuple)) and len(color) == 3:
                    r, g, b = int(color[0]), int(color[1]), int(color[2])
                    validated.append((
                        max(0, min(255, r)),
                        max(0, min(255, g)),
                        max(0, min(255, b)),
                    ))
            palette = validated if len(validated) >= 2 else None
        else:
            palette = None

    # Validate output resolution if provided
    width = data.get("width", None)
    if width is not None:
        try:
            width = int(width)
            width = max(120, min(3840, width))
        except (TypeError, ValueError):
            width = None

    height = data.get("height", None)
    if height is not None:
        try:
            height = int(height)
            height = max(120, min(3840, height))
        except (TypeError, ValueError):
            height = None

    return {
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
        "mp4": data.get("mp4", False),
        "duration": duration,
        "fps": fps,
        "variants": variants,
        "title": data.get("title", None),
        # Director mode fields (Path A)
        "transforms": data.get("transforms", None),
        "postfx": data.get("postfx", None),
        "composition": data.get("composition", None),
        "mask": data.get("mask", None),
        "variant": data.get("variant", None),
        "color_scheme": data.get("color_scheme", None),
        # Custom palette and resolution
        "palette": palette,
        "width": width,
        "height": height,
    }


def content_has_data(content):
    """
    检查 content 是否包含实际数据 - Check if content has actual data

    Returns True if headline, metrics, or body is present.
    """
    return bool(
        content.get("headline") or content.get("metrics") or content.get("body")
    )
