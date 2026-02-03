"""
Flexible Output System - 千变万化的输出系统

打破刚性的一一对应映射，实现连续、可插值、可组合的视觉生成。

核心模块::

    emotion   - VAD 连续情感空间 (取代离散情绪分类)
    color     - 连续颜色空间 (取代固定调色板)
    modulator - 噪声调制器 (参数随时间漂移)
    grammar   - 随机文法 (组合爆炸式的视觉结构)
    cppn      - CPPN 效果 (无限图案变化)
    pipeline  - 柔性管线 (编排所有模块)

设计理念::

    旧系统: text -> 离散类别 -> 固定效果 -> 固定参数 -> 单一输出
    新系统: text -> VAD向量 -> 连续参数空间 -> 文法组合 -> 噪声调制 -> 千变万化

用法::

    from procedural.flexible import FlexiblePipeline

    pipe = FlexiblePipeline(seed=42)
    img = pipe.generate(
        text="market crash fears rising",
        output_size=(1080, 1080),
    )
    img.save('output.png')
"""

from .emotion import EmotionVector, VAD_ANCHORS, text_to_emotion
from .color_space import ContinuousColorSpace
from .modulator import NoiseModulator
from .grammar import VisualGrammar
from .cppn import CPPNEffect
from .pipeline import FlexiblePipeline

__all__ = [
    "EmotionVector",
    "VAD_ANCHORS",
    "text_to_emotion",
    "ContinuousColorSpace",
    "NoiseModulator",
    "VisualGrammar",
    "CPPNEffect",
    "FlexiblePipeline",
]
