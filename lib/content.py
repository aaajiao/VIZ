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

    warnings = []

    # Truncate text fields to safe lengths for rendering
    _MAX_HEADLINE = 120
    _MAX_TITLE = 80
    _MAX_BODY = 500
    _MAX_METRIC_LEN = 60
    _MAX_METRICS = 10

    if data.get("headline") and len(data["headline"]) > _MAX_HEADLINE:
        orig_len = len(data["headline"])
        data["headline"] = data["headline"][:_MAX_HEADLINE] + "..."
        warnings.append(f"headline truncated from {orig_len} to {_MAX_HEADLINE} chars")
    if data.get("title") and len(data["title"]) > _MAX_TITLE:
        orig_len = len(data["title"])
        data["title"] = data["title"][:_MAX_TITLE] + "..."
        warnings.append(f"title truncated from {orig_len} to {_MAX_TITLE} chars")
    if data.get("body") and len(data["body"]) > _MAX_BODY:
        orig_len = len(data["body"])
        data["body"] = data["body"][:_MAX_BODY] + "..."
        warnings.append(f"body truncated from {orig_len} to {_MAX_BODY} chars")
    if data.get("metrics"):
        orig_count = len(data["metrics"])
        metrics = data["metrics"][:_MAX_METRICS]
        if orig_count > _MAX_METRICS:
            warnings.append(f"metrics trimmed from {orig_count} to {_MAX_METRICS} items")
        truncated_metrics = []
        for m in metrics:
            if not isinstance(m, str):
                warnings.append(f"non-string metric dropped: {m!r}")
                continue
            if len(m) > _MAX_METRIC_LEN:
                warnings.append(f"metric truncated from {len(m)} to {_MAX_METRIC_LEN} chars")
                truncated_metrics.append(m[:_MAX_METRIC_LEN] + "...")
            else:
                truncated_metrics.append(m)
        data["metrics"] = truncated_metrics

    # Clamp numeric params to safe ranges
    raw_duration = data.get("duration", 3.0)
    try:
        duration = float(raw_duration)
    except (TypeError, ValueError):
        warnings.append(f"duration ignored: invalid value {raw_duration!r}, using default 3.0")
        duration = 3.0
    if duration < 0.1 or duration > 30.0:
        clamped = max(0.1, min(duration, 30.0))
        warnings.append(f"duration clamped from {duration} to {clamped} (range 0.1-30.0)")
        duration = clamped

    raw_fps = data.get("fps", 15)
    try:
        fps = int(raw_fps)
    except (TypeError, ValueError):
        warnings.append(f"fps ignored: invalid value {raw_fps!r}, using default 15")
        fps = 15
    if fps < 1 or fps > 60:
        clamped = max(1, min(fps, 60))
        warnings.append(f"fps clamped from {fps} to {clamped} (range 1-60)")
        fps = clamped

    raw_variants = data.get("variants", 1)
    try:
        variants = int(raw_variants)
    except (TypeError, ValueError):
        warnings.append(f"variants ignored: invalid value {raw_variants!r}, using default 1")
        variants = 1
    if variants < 1 or variants > 20:
        clamped = max(1, min(variants, 20))
        warnings.append(f"variants clamped from {variants} to {clamped} (range 1-20)")
        variants = clamped

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
            if palette is None:
                warnings.append("palette dropped: fewer than 2 valid RGB triplets after validation")
        else:
            warnings.append("palette dropped: need list of 2+ RGB triplets")
            palette = None

    # Validate output resolution if provided
    width = data.get("width", None)
    if width is not None:
        try:
            raw_width = width
            width = int(width)
            if width < 120 or width > 3840:
                clamped = max(120, min(3840, width))
                warnings.append(f"width clamped from {width} to {clamped} (range 120-3840)")
                width = clamped
        except (TypeError, ValueError):
            warnings.append(f"width ignored: invalid value {raw_width!r}")
            width = None

    height = data.get("height", None)
    if height is not None:
        try:
            raw_height = height
            height = int(height)
            if height < 120 or height > 3840:
                clamped = max(120, min(3840, height))
                warnings.append(f"height clamped from {height} to {clamped} (range 120-3840)")
                height = clamped
        except (TypeError, ValueError):
            warnings.append(f"height ignored: invalid value {raw_height!r}")
            height = None

    return {
        "headline": data.get("headline", None),
        "metrics": data.get("metrics", []),
        "body": data.get("body", None),
        "emotion": data.get("emotion", None),
        "vad": data.get("vad", None),
        "timestamp": data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M")),
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
        # Sanitization metadata
        "_warnings": warnings,
    }


def content_has_data(content):
    """
    检查 content 是否包含实际数据 - Check if content has actual data

    Returns True if headline, metrics, or body is present.
    """
    return bool(
        content.get("headline") or content.get("metrics") or content.get("body")
    )
