"""
Kaomoji Rendering Module
颜文字渲染模块

提供 ASCII 颜文字绘制和分类功能。
"""

from PIL import ImageDraw, ImageFont
import random

# ========== ASCII 颜文字数据 ==========
ASCII_KAOMOJI = {
    "bull": [
        # 开心表情
        ["  ^___^  ", " (◠‿◠) ", "  \\___/  "],
        ["  *___*  ", " (^o^) ", "  <___>  "],
        ["  O___O  ", " (≧▽≦)", "  |___|  "],
        # 庆祝
        ["  \\o/   ", "   |    ", "  / \\   "],
        ["  ^_^   ", " <(^_^)>", "  (_)   "],
    ],
    "bear": [
        # 难过表情
        ["  T_T   ", " (;_;)  ", "  |_|   "],
        ["  -_-   ", " (x_x)  ", "  |_|   "],
        ["  >_<   ", " (╥﹏╥)", "  |_|   "],
    ],
    "neutral": [
        # 平静表情
        ["  -_-   ", " (._.)  ", "  |_|   "],
        ["  o_o   ", " (o.o)  ", "  |_|   "],
    ],
}

# ========== 情绪分类 ==========
MOOD_CATEGORIES = {
    "bull": ["bull", "happy", "excited", "euphoria", "excitement"],
    "bear": ["bear", "sad", "anxious", "fear", "panic"],
    "neutral": ["neutral", "calm", "uncertain", "anxiety"],
}


def draw_kaomoji(draw, x, y, mood, color, outline_color, size=1, rng=None):
    """
    绘制 ASCII 颜文字

    参数:
        draw: PIL ImageDraw 对象
        x: 左上角 X 坐标
        y: 左上角 Y 坐标
        mood: 情绪类型 ('bull', 'bear', 'neutral')
        color: 主颜色 (RGB 元组或十六进制字符串)
        outline_color: 轮廓颜色 (RGB 元组或十六进制字符串)
        size: 缩放大小 (默认 1)
        rng: random.Random 对象 (可选，用于可复现性)
    """
    # 规范化 mood 到标准类别
    normalized_mood = _normalize_mood(mood)

    # 获取颜文字列表
    if normalized_mood not in ASCII_KAOMOJI:
        normalized_mood = "neutral"

    kaomoji_list = ASCII_KAOMOJI[normalized_mood]

    if rng:
        kaomoji = rng.choice(kaomoji_list)
    else:
        kaomoji = random.choice(kaomoji_list)

    # 转换颜色格式（如果是十六进制字符串）
    if isinstance(color, str):
        color = _hex_to_rgb(color)
    if isinstance(outline_color, str):
        outline_color = _hex_to_rgb(outline_color)

    # 加载字体 - Load font with fallback
    font = None
    try:
        font_size = min(200, max(1, 10 * size))
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size
        )
    except:
        font = ImageFont.load_default()

    # 绘制颜文字（每行）
    line_height = max(12, int(10 * size * 1.2))
    for line_idx, line_text in enumerate(kaomoji):
        current_y = y + line_idx * line_height

        # 绘制轮廓（2D网格偏移）- Outline with 2D grid offset
        outline_offset = max(1, 2 * size)
        for offset_x in range(-outline_offset, outline_offset + 1):
            for offset_y in range(-outline_offset, outline_offset + 1):
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (x + offset_x, current_y + offset_y),
                        line_text,
                        fill=outline_color,
                        font=font,
                    )

        # 绘制主文字（2D网格）- Main text with 2D grid
        for dx in range(size):
            for dy in range(size):
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
    将任意情绪名称规范化为标准类别

    参数:
        mood: 情绪名称

    返回:
        标准情绪类别 ('bull', 'bear', 'neutral')
    """
    mood_lower = str(mood).lower()

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
