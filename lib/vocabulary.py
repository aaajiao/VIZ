"""
视觉词汇表 - Source Vocabulary

定义每种信息来源的视觉词汇（粒子字符、kaomoji 集合、装饰符号）。
AI 选择 source 时自动加载对应词汇，也可通过 JSON 覆盖任意字段。

Defines visual vocabulary per source type (particle chars, kaomoji sets, decoration symbols).
AI loads vocabulary when selecting source, can override any field via JSON.
"""


# Default vocabulary per source
VOCABULARIES = {
    "market": {
        "particles": "0123456789$#%↑↓±",
        "kaomoji_moods": ["euphoria", "excitement", "anxiety", "fear", "panic"],
        "symbols": ["↑", "↓", "$", "€", "¥", "₿", "%"],
        "decoration_chars": ["┃", "━", "╋", "║", "═", "╬"],
        "ambient_words": {
            "positive": ["BULL", "RISE", "UP", "GAIN", "涨", "牛"],
            "negative": ["BEAR", "DOWN", "SELL", "CRASH", "跌", "崩"],
            "neutral": ["HOLD", "WAIT", "---", "===", "观", "守"],
        },
    },
    "art": {
        "particles": "◆◇○●□■△▽✧✦",
        "kaomoji_moods": ["love", "surprised", "thinking", "happy", "proud"],
        "symbols": ["◆", "✧", "○", "□", "△", "◎"],
        "decoration_chars": ["╭", "╮", "╰", "╯", "─", "│"],
        "ambient_words": {
            "positive": ["ART", "CREATE", "美", "创", "VISION"],
            "negative": ["VOID", "FADE", "空", "寂", "NULL"],
            "neutral": ["FORM", "SHAPE", "形", "式", "..."],
        },
    },
    "news": {
        "particles": "ABCDEFG!?#@&",
        "kaomoji_moods": ["neutral", "surprised", "thinking", "confused", "anxiety"],
        "symbols": ["!", "?", "#", "@", "▶", "■"],
        "decoration_chars": ["┌", "┐", "└", "┘", "─", "│"],
        "ambient_words": {
            "positive": ["BREAKING", "UPDATE", "快讯", "关注"],
            "negative": ["ALERT", "WARN", "警告", "紧急"],
            "neutral": ["NEWS", "REPORT", "新闻", "报道"],
        },
    },
    "mood": {
        "particles": "·˚✧♪♫∞~○◦",
        "kaomoji_moods": ["happy", "sad", "thinking", "love", "relaxed", "lonely"],
        "symbols": ["♪", "✧", "~", "○", "∞", "·"],
        "decoration_chars": ["·", "˚", "✧", "○", "◦", "∙"],
        "ambient_words": {
            "positive": ["FEEL", "FLOW", "感", "润", "~"],
            "negative": ["EMPTY", "LOST", "空", "迷", "..."],
            "neutral": ["THINK", "DRIFT", "想", "漂", "—"],
        },
    },
}

# Default vocabulary when no source specified (pure visual)
DEFAULT_VOCABULARY = {
    "particles": "01·*.:+-",
    "kaomoji_moods": ["neutral", "happy", "thinking", "calm"],
    "symbols": ["+", "*", "·", "○", "□", "△"],
    "decoration_chars": ["+", "+", "+", "+"],
    "ambient_words": {
        "positive": ["YES", "GO", "UP"],
        "negative": ["NO", "STOP", "DOWN"],
        "neutral": ["...", "---", "==="],
    },
}


def get_vocabulary(source=None, overrides=None):
    """
    获取词汇表 - Get vocabulary for a source

    Args:
        source: source name ('market', 'art', 'news', 'mood', or None)
        overrides: dict to override specific vocabulary fields

    Returns:
        dict with vocabulary fields
    """
    if source and source in VOCABULARIES:
        vocab = dict(VOCABULARIES[source])
    else:
        vocab = dict(DEFAULT_VOCABULARY)

    # Apply overrides
    if overrides:
        for key, value in overrides.items():
            vocab[key] = value

    return vocab
