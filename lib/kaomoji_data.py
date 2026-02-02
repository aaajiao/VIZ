"""
Kaomoji Data Module
颜文字数据模块

Provides single-line and multiline kaomoji formats with mood categories.
提供单行和多行颜文字格式及情绪分类。
"""

# ========== 单行颜文字格式 ==========
# Single-line format: all faces are strings without newlines
KAOMOJI_SINGLE = {
    "bull": [
        "(^o^)",
        "(≧▽≦)",
        "\\(^o^)/",
        "(◠‿◠)",
        "(^_^)",
    ],
    "bear": [
        "(;_;)",
        "(x_x)",
        "(╥﹏╥)",
        "(T_T)",
        "(>_<)",
    ],
    "neutral": [
        "(._.) ",
        "(o.o)",
        "(-_-)",
        "(o_o)",
        "(・_・)",
    ],
    "euphoria": [
        "\\(^o^)/",
        "(≧▽≦)",
        "(*^_^*)",
        "(๑•́ ω •̀๑)",
        "\\(^▽^)/",
    ],
    "excitement": [
        "(*^_^*)",
        "(๑•́ ω •̀๑)",
        "(^_^)v",
        "\\(^o^)/",
        "(๑´ڡ`๑)",
    ],
    "anxiety": [
        "(o_o)",
        "(´；ω；`)",
        "(´・_・`)",
        "(´；ω；`)",
        "(´；ω；`)",
    ],
    "fear": [
        "(>_<)",
        "(´；ω；`)",
        "(´・_・`)",
        "(´；ω；`)",
        "(´；ω；`)",
    ],
    "panic": [
        "(x_x)",
        "(´；ω；`)",
        "(´・_・`)",
        "(´；ω；`)",
        "(´；ω；`)",
    ],
}

# ========== 多行颜文字格式（向后兼容）==========
# Multiline format: preserved from original kaomoji.py for backward compatibility
KAOMOJI_MULTILINE = {
    "bull": [
        ["  ^___^  ", " (◠‿◠) ", "  \\___/  "],
        ["  *___*  ", " (^o^) ", "  <___>  "],
        ["  O___O  ", " (≧▽≦)", "  |___|  "],
        ["  \\o/   ", "   |    ", "  / \\   "],
        ["  ^_^   ", " <(^_^)>", "  (_)   "],
    ],
    "bear": [
        ["  T_T   ", " (;_;)  ", "  |_|   "],
        ["  -_-   ", " (x_x)  ", "  |_|   "],
        ["  >_<   ", " (╥﹏╥)", "  |_|   "],
    ],
    "neutral": [
        ["  -_-   ", " (._.)  ", "  |_|   "],
        ["  o_o   ", " (o.o)  ", "  |_|   "],
    ],
    "euphoria": [
        ["  \\o/   ", "   |    ", "  / \\   "],
        ["  ^_^   ", " <(^_^)>", "  (_)   "],
    ],
    "excitement": [
        ["  *___*  ", " (^o^) ", "  <___>  "],
        ["  O___O  ", " (≧▽≦)", "  |___|  "],
    ],
    "anxiety": [
        ["  o_o   ", " (o.o)  ", "  |_|   "],
        ["  -_-   ", " (._.)  ", "  |_|   "],
    ],
    "fear": [
        ["  >_<   ", " (╥﹏╥)", "  |_|   "],
        ["  T_T   ", " (;_;)  ", "  |_|   "],
    ],
    "panic": [
        ["  -_-   ", " (x_x)  ", "  |_|   "],
        ["  >_<   ", " (╥﹏╥)", "  |_|   "],
    ],
}

# ========== 情绪分类映射 ==========
# Mood category mappings for sentiment analysis
MOOD_CATEGORIES = {
    "bull": ["bull", "happy", "excited", "euphoria", "excitement"],
    "bear": ["bear", "sad", "anxious", "fear", "panic"],
    "neutral": ["neutral", "calm", "uncertain", "anxiety"],
}


def get_kaomoji(mood, format="single"):
    """
    获取颜文字 - Get kaomoji face(s) for a mood

    参数 / Parameters:
        mood (str): 情绪类型 - Mood type (bull, bear, neutral, euphoria, panic, etc.)
        format (str): 格式 - Format ('single' or 'multiline')

    返回 / Returns:
        list: 颜文字列表 - List of kaomoji faces

    示例 / Example:
        >>> get_kaomoji('bull', format='single')
        ['(^o^)', '(≧▽≦)', '\\(^o^)/', ...]

        >>> get_kaomoji('bull', format='multiline')
        [['  ^___^  ', ' (◠‿◠) ', '  \\___/  '], ...]
    """
    if format == "single":
        return KAOMOJI_SINGLE.get(mood, KAOMOJI_SINGLE.get("neutral", []))
    elif format == "multiline":
        return KAOMOJI_MULTILINE.get(mood, KAOMOJI_MULTILINE.get("neutral", []))
    else:
        raise ValueError(f"Invalid format: {format}. Use 'single' or 'multiline'")


def convert_multiline_to_single(multiline_faces):
    """
    将多行颜文字转换为单行 - Convert multiline kaomoji to single-line

    参数 / Parameters:
        multiline_faces (list): 多行颜文字列表 - List of 3-line kaomoji

    返回 / Returns:
        list: 单行颜文字列表 - List of single-line kaomoji

    示例 / Example:
        >>> convert_multiline_to_single([["  ^___^  ", " (◠‿◠) ", "  \\___/  "]])
        ['(◠‿◠)']
    """
    single_faces = []
    for face in multiline_faces:
        if isinstance(face, list) and len(face) >= 3:
            # Extract middle line (the actual face)
            middle_line = face[1].strip()
            if middle_line:
                single_faces.append(middle_line)
    return single_faces


def migrate_kaomoji_format():
    """
    迁移颜文字格式 - Migrate from multiline to single-line format

    返回 / Returns:
        dict: 转换后的单行颜文字字典 - Converted single-line kaomoji dict

    说明 / Note:
        This function demonstrates how to convert existing multiline data
        to single-line format. Useful for gradual migration.
    """
    migrated = {}
    for mood, faces in KAOMOJI_MULTILINE.items():
        migrated[mood] = convert_multiline_to_single(faces)
    return migrated
