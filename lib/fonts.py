"""
Font loading utilities with fallback chain
字体加载工具（带回退链）
"""

import os
from pathlib import Path

from PIL import ImageFont

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PACKAGED_FONT = _PROJECT_ROOT / "lib" / "assets" / "unifont_jp.otf"
_REPO_FONT = _PROJECT_ROOT / "assets" / "fonts" / "unifont_jp.otf"

FONT_FALLBACK_CHAIN = [
    str(_PACKAGED_FONT),
    str(_REPO_FONT),
    "/usr/share/fonts/opentype/unifont/unifont_jp.otf",
    "/usr/share/fonts/opentype/unifont/unifont.otf",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "C:/Windows/Fonts/msgothic.ttc",
    "C:/Windows/Fonts/YuGothM.ttc",
    "C:/Windows/Fonts/seguisym.ttf",
]

_font_cache = {}


def get_font(size):
    """
    获取指定大小的字体，按优先级尝试回退链
    """
    if size in _font_cache:
        return _font_cache[size]

    for font_path in FONT_FALLBACK_CHAIN:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                _font_cache[size] = font
                return font
        except Exception:
            continue

    font = ImageFont.load_default()
    _font_cache[size] = font
    return font
