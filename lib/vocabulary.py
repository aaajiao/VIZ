"""
视觉词汇覆盖 - Visual Vocabulary Overrides

AI 通过 JSON vocabulary 字段传入自定义视觉词汇（粒子字符、颜文字情绪、装饰符号）。
情感系统驱动所有默认视觉选择，vocabulary 仅用于覆盖。

AI passes custom visual vocabulary (particle chars, kaomoji moods, decoration symbols)
via the JSON vocabulary field. The emotion system drives all default visual choices;
vocabulary is override-only.
"""


def get_vocabulary(overrides=None):
    """
    获取词汇覆盖 - Get vocabulary overrides

    Args:
        overrides: dict of vocabulary fields to override (optional)

    Returns:
        copy of overrides dict, or empty dict if None
    """
    if overrides:
        return dict(overrides)
    return {}
