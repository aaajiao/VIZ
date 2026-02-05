"""
Kaomoji Rendering Module
颜文字渲染模块

提供 ASCII 颜文字绘制和分类功能。
数据统一从 kaomoji_data.py 导入，不再硬编码。

渲染策略::

    1. 精确匹配: mood 在 KAOMOJI_SINGLE 中有直接 key → 用单行渲染
    2. 多行匹配: mood 在 KAOMOJI_MULTILINE 中有直接 key → 用多行渲染
    3. 父类兜底: 通过 MOOD_CATEGORIES 解析到 bull/bear/neutral
"""

from PIL import ImageDraw
import random

from lib.kaomoji_data import (
    KAOMOJI_SINGLE,
    KAOMOJI_MULTILINE,
    MOOD_CATEGORIES,
)
from lib.fonts import get_font

ASCII_KAOMOJI = KAOMOJI_MULTILINE


def draw_kaomoji(draw, x, y, mood, color, outline_color, size=1, rng=None):
    """
    绘制颜文字（支持单行和多行格式）

    渲染策略:
        - 优先从 KAOMOJI_SINGLE 精确匹配 mood，用单行渲染（品种最丰富）
        - 如果 mood 不在 KAOMOJI_SINGLE 中，尝试 KAOMOJI_MULTILINE
        - 最终 fallback 到父类

    参数:
        draw: PIL ImageDraw 对象
        x: 左上角 X 坐标
        y: 左上角 Y 坐标
        mood: 情绪类型 ('happy', 'love', 'sad', 'angry', 'bull', 'bear', ...)
        color: 主颜色 (RGB 元组或十六进制字符串)
        outline_color: 轮廓颜色 (RGB 元组或十六进制字符串)
        size: 缩放大小 (默认 1)
        rng: random.Random 对象 (可选，用于可复现性)
    """
    _rng = rng or random

    # 转换颜色格式（如果是十六进制字符串）
    if isinstance(color, str):
        color = _hex_to_rgb(color)
    if isinstance(outline_color, str):
        outline_color = _hex_to_rgb(outline_color)

    font_size = min(200, max(1, 10 * size))
    font = get_font(font_size)

    # === 选择颜文字 ===
    mood_lower = str(mood).lower()

    # 策略 1: 精确匹配 KAOMOJI_SINGLE（最丰富）
    if mood_lower in KAOMOJI_SINGLE:
        face_text = _rng.choice(KAOMOJI_SINGLE[mood_lower])
        _draw_single_line(draw, x, y, face_text, color, outline_color, font, size)
        return

    # 策略 2: 精确匹配 KAOMOJI_MULTILINE
    if mood_lower in KAOMOJI_MULTILINE:
        kaomoji = _rng.choice(KAOMOJI_MULTILINE[mood_lower])
        _draw_multiline(draw, x, y, kaomoji, color, outline_color, font, size)
        return

    # 策略 3: 父类兜底
    parent = _normalize_mood(mood_lower)
    if parent in KAOMOJI_SINGLE:
        face_text = _rng.choice(KAOMOJI_SINGLE[parent])
        _draw_single_line(draw, x, y, face_text, color, outline_color, font, size)
    elif parent in KAOMOJI_MULTILINE:
        kaomoji = _rng.choice(KAOMOJI_MULTILINE[parent])
        _draw_multiline(draw, x, y, kaomoji, color, outline_color, font, size)


def _draw_single_line(draw, x, y, text, color, outline_color, font, size):
    """渲染单行颜文字"""
    outline_offset = max(1, min(4, 2 * size))
    for offset_x in range(-outline_offset, outline_offset + 1):
        for offset_y in range(-outline_offset, outline_offset + 1):
            if offset_x != 0 or offset_y != 0:
                draw.text(
                    (x + offset_x, y + offset_y),
                    text,
                    fill=outline_color,
                    font=font,
                )

    bold_range = min(size, 4)
    for dx in range(bold_range):
        for dy in range(bold_range):
            draw.text((x + dx, y + dy), text, fill=color, font=font)


def _draw_multiline(draw, x, y, kaomoji_lines, color, outline_color, font, size):
    """渲染多行颜文字"""
    line_height = max(12, int(10 * size * 1.2))
    outline_offset = max(1, min(4, 2 * size))

    for line_idx, line_text in enumerate(kaomoji_lines):
        current_y = y + line_idx * line_height

        for offset_x in range(-outline_offset, outline_offset + 1):
            for offset_y in range(-outline_offset, outline_offset + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (x + offset_x, current_y + offset_y),
                        line_text,
                        fill=outline_color,
                        font=font,
                    )

        bold_range = min(size, 4)
        for dx in range(bold_range):
            for dy in range(bold_range):
                draw.text((x + dx, current_y + dy), line_text, fill=color, font=font)


def get_moods_by_category(category):
    """
    获取指定分类下的所有情绪

    参数:
        category: 分类名称 ('bull', 'bear', 'neutral')

    返回:
        情绪列表
    """
    if category in MOOD_CATEGORIES:
        return MOOD_CATEGORIES[category]
    return MOOD_CATEGORIES.get("neutral", [])


def _normalize_mood(mood):
    """
    将任意情绪名称规范化为标准父类

    精确匹配优先：如果 mood 本身就是 KAOMOJI_SINGLE 的 key，
    直接返回该 mood（不压缩到父类）。

    参数:
        mood: 情绪名称

    返回:
        标准情绪类别 ('bull', 'bear', 'neutral') 或精确 mood 名
    """
    mood_lower = str(mood).lower()

    # 精确匹配：mood 自身就是数据 key
    if mood_lower in KAOMOJI_SINGLE:
        return mood_lower

    # 父类映射
    for category, moods in MOOD_CATEGORIES.items():
        if mood_lower in moods:
            return category

    return "neutral"


def _hex_to_rgb(hex_color):
    """
    将十六进制颜色转换为 RGB 元组

    参数:
        hex_color: 十六进制颜色字符串 (如 '#FF0000')

    返回:
        RGB 元组 (如 (255, 0, 0))
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
