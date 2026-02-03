"""
VAD 连续情感空间 - Valence-Arousal-Dominance Emotion Space

用三维连续向量取代离散情绪分类 (bull/bear/neutral)，
实现无限粒度的情感表达。

维度说明::

    Valence   [-1, +1]  消极 ←→ 积极 (不愉快到愉快)
    Arousal   [-1, +1]  平静 ←→ 激动 (低唤醒到高唤醒)
    Dominance [-1, +1]  顺从 ←→ 支配 (无力到掌控)

用法::

    from procedural.flexible.emotion import EmotionVector, text_to_emotion

    # 从文本自动推断
    ev = text_to_emotion("市场暴跌 恐慌蔓延")
    # → EmotionVector(valence=-0.7, arousal=0.8, dominance=-0.3)

    # 直接构造
    ev = EmotionVector(valence=0.5, arousal=0.3, dominance=0.1)

    # 插值两种情绪
    ev3 = ev1.lerp(ev2, t=0.5)

    # 转换为视觉参数
    params = ev.to_visual_params()
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from procedural.core.mathx import clamp, mix, smoothstep


@dataclass
class EmotionVector:
    """
    VAD 情感向量 - 三维连续情感表示

    属性:
        valence: 效价 [-1, +1] (消极到积极)
        arousal: 唤醒度 [-1, +1] (平静到激动)
        dominance: 支配度 [-1, +1] (顺从到支配)
    """

    valence: float = 0.0
    arousal: float = 0.0
    dominance: float = 0.0

    def __post_init__(self):
        self.valence = clamp(self.valence, -1.0, 1.0)
        self.arousal = clamp(self.arousal, -1.0, 1.0)
        self.dominance = clamp(self.dominance, -1.0, 1.0)

    def as_tuple(self) -> tuple:
        return (self.valence, self.arousal, self.dominance)

    def magnitude(self) -> float:
        """向量长度 (情感强度)"""
        return math.sqrt(
            self.valence ** 2 + self.arousal ** 2 + self.dominance ** 2
        )

    def normalized(self) -> EmotionVector:
        """归一化到单位球面"""
        m = self.magnitude()
        if m < 1e-10:
            return EmotionVector(0.0, 0.0, 0.0)
        return EmotionVector(
            self.valence / m, self.arousal / m, self.dominance / m
        )

    def lerp(self, other: EmotionVector, t: float) -> EmotionVector:
        """线性插值"""
        return EmotionVector(
            valence=mix(self.valence, other.valence, t),
            arousal=mix(self.arousal, other.arousal, t),
            dominance=mix(self.dominance, other.dominance, t),
        )

    def slerp(self, other: EmotionVector, t: float) -> EmotionVector:
        """
        球面线性插值 (保持向量模长，更适合情感空间)
        """
        v0 = self.as_tuple()
        v1 = other.as_tuple()

        dot = sum(a * b for a, b in zip(v0, v1))
        dot = clamp(dot, -1.0, 1.0)

        omega = math.acos(dot)
        if abs(omega) < 1e-10:
            return self.lerp(other, t)

        so = math.sin(omega)
        s0 = math.sin((1 - t) * omega) / so
        s1 = math.sin(t * omega) / so

        return EmotionVector(
            valence=s0 * v0[0] + s1 * v1[0],
            arousal=s0 * v0[1] + s1 * v1[1],
            dominance=s0 * v0[2] + s1 * v1[2],
        )

    def distance(self, other: EmotionVector) -> float:
        """欧几里得距离"""
        return math.sqrt(
            (self.valence - other.valence) ** 2
            + (self.arousal - other.arousal) ** 2
            + (self.dominance - other.dominance) ** 2
        )

    def to_visual_params(self) -> dict:
        """
        将情感向量映射到连续视觉参数空间

        返回一个包含所有视觉维度的连续参数字典，
        每个参数都是 0-1 范围内的浮点数。

        映射逻辑:
            - valence  → 色温 (冷色到暖色), 字符密度方向
            - arousal  → 频率, 速度, 复杂度
            - dominance → 对比度, 锐度, 结构性
            - |valence| → 饱和度 (极端情绪更鲜艳)
            - 交叉项   → 湍流度, 动画幅度
        """
        v, a, d = self.valence, self.arousal, self.dominance

        # 基础映射 (全部映射到 0-1 范围)
        warmth = _remap(v, -1, 1, 0.0, 1.0)
        energy = _remap(a, -1, 1, 0.0, 1.0)
        structure = _remap(d, -1, 1, 0.0, 1.0)

        # 派生参数 (交叉项产生更丰富的变化)
        saturation = clamp(abs(v) * 0.7 + abs(a) * 0.3, 0.0, 1.0)
        turbulence = clamp(abs(v - 0.5) * 0.6 + a * 0.4, 0.0, 1.0)
        intensity = clamp(self.magnitude() / math.sqrt(3), 0.0, 1.0)

        # 具体视觉参数
        return {
            # 颜色空间
            "warmth": warmth,
            "saturation": saturation,
            "brightness": _remap(v * 0.5 + a * 0.3 + d * 0.2, -1, 1, 0.3, 1.0),

            # 效果参数
            "frequency": _remap(a, -1, 1, 0.01, 0.2),
            "speed": _remap(a, -1, 1, 0.2, 5.0),
            "complexity": _remap(d, -1, 1, 0.2, 0.9),
            "octaves": max(1, min(8, int(_remap(d, -1, 1, 1, 8)))),
            "turbulence": turbulence,

            # 动画参数
            "float_amp": _remap(a, -1, 1, 1.0, 8.0),
            "breath_amp": _remap(abs(a), 0, 1, 0.02, 0.15),
            "animation_speed": _remap(a, -1, 1, 0.5, 3.0),

            # 结构参数
            "density": _remap(d, -1, 1, 0.2, 0.6),
            "contrast": _remap(abs(d), 0, 1, 1.0, 1.5),
            "structure": structure,

            # 元参数 (用于文法选择)
            "energy": energy,
            "intensity": intensity,

            # 原始 VAD 值 (供下游使用)
            "valence": v,
            "arousal": a,
            "dominance": d,
        }


# === VAD 锚点 (基于心理学文献) ===

VAD_ANCHORS: dict[str, EmotionVector] = {
    # 基础情绪
    "joy":          EmotionVector(+0.76, +0.48, +0.35),
    "excitement":   EmotionVector(+0.62, +0.75, +0.38),
    "euphoria":     EmotionVector(+0.90, +0.85, +0.60),
    "calm":         EmotionVector(+0.30, -0.60, +0.20),
    "serenity":     EmotionVector(+0.50, -0.40, +0.30),
    "surprise":     EmotionVector(+0.40, +0.67, -0.13),
    "awe":          EmotionVector(+0.50, +0.55, -0.30),
    "hope":         EmotionVector(+0.55, +0.20, +0.15),
    "nostalgia":    EmotionVector(+0.20, -0.20, -0.10),
    "melancholy":   EmotionVector(-0.30, -0.30, -0.20),
    "anxiety":      EmotionVector(-0.51, +0.60, -0.33),
    "fear":         EmotionVector(-0.64, +0.60, -0.43),
    "panic":        EmotionVector(-0.80, +0.90, -0.60),
    "anger":        EmotionVector(-0.51, +0.59, +0.25),
    "sadness":      EmotionVector(-0.63, -0.27, -0.33),
    "despair":      EmotionVector(-0.80, -0.40, -0.70),
    "boredom":      EmotionVector(-0.20, -0.60, -0.20),
    "contempt":     EmotionVector(-0.40, +0.10, +0.50),
    "disgust":      EmotionVector(-0.60, +0.35, +0.20),
    "trust":        EmotionVector(+0.60, -0.10, +0.40),

    # 市场情绪 (兼容旧系统)
    "bull":         EmotionVector(+0.70, +0.50, +0.40),
    "bear":         EmotionVector(-0.60, +0.40, -0.30),
    "neutral":      EmotionVector(+0.00, -0.10, +0.00),
    "volatile":     EmotionVector(-0.10, +0.80, -0.20),
}


# === 文本关键词到 VAD 偏移量 ===

_WORD_VAD: dict[str, tuple[float, float, float]] = {
    # 积极高唤醒 (V+, A+)
    "surge": (+0.6, +0.7, +0.3), "rally": (+0.6, +0.6, +0.3),
    "soar": (+0.7, +0.8, +0.4), "boom": (+0.5, +0.8, +0.3),
    "rocket": (+0.7, +0.9, +0.4), "moon": (+0.6, +0.7, +0.3),
    "bull": (+0.5, +0.4, +0.3), "bullish": (+0.5, +0.4, +0.3),
    "gain": (+0.4, +0.3, +0.2), "rise": (+0.3, +0.3, +0.1),
    "up": (+0.3, +0.2, +0.1), "high": (+0.3, +0.3, +0.2),
    "record": (+0.5, +0.5, +0.3), "breakthrough": (+0.6, +0.6, +0.4),
    "positive": (+0.4, +0.1, +0.2),

    # 积极低唤醒 (V+, A-)
    "stable": (+0.3, -0.3, +0.3), "steady": (+0.3, -0.3, +0.3),
    "calm": (+0.3, -0.6, +0.2), "safe": (+0.4, -0.3, +0.3),
    "recover": (+0.3, -0.1, +0.2),

    # 消极高唤醒 (V-, A+)
    "crash": (-0.8, +0.9, -0.5), "panic": (-0.7, +0.9, -0.6),
    "plunge": (-0.7, +0.8, -0.4), "collapse": (-0.8, +0.7, -0.5),
    "crisis": (-0.6, +0.7, -0.4), "fear": (-0.6, +0.6, -0.4),
    "volatile": (-0.1, +0.8, -0.2), "chaos": (-0.5, +0.9, -0.3),
    "shock": (-0.5, +0.8, -0.3), "turmoil": (-0.5, +0.7, -0.3),
    "sell": (-0.3, +0.4, -0.1), "dump": (-0.5, +0.6, -0.2),
    "bear": (-0.5, +0.3, -0.2), "bearish": (-0.5, +0.3, -0.2),

    # 消极低唤醒 (V-, A-)
    "decline": (-0.4, -0.1, -0.2), "fall": (-0.3, +0.1, -0.1),
    "drop": (-0.3, +0.2, -0.1), "loss": (-0.4, -0.1, -0.2),
    "down": (-0.3, +0.1, -0.1), "low": (-0.2, -0.2, -0.1),
    "weak": (-0.3, -0.3, -0.3), "stagnant": (-0.2, -0.5, -0.2),
    "negative": (-0.4, +0.1, -0.2), "sad": (-0.6, -0.3, -0.3),

    # 中文关键词
    "暴涨": (+0.7, +0.9, +0.4), "暴跌": (-0.8, +0.9, -0.5),
    "上涨": (+0.4, +0.3, +0.2), "下跌": (-0.4, +0.2, -0.2),
    "恐慌": (-0.7, +0.9, -0.6), "稳定": (+0.3, -0.3, +0.3),
    "牛市": (+0.6, +0.5, +0.4), "熊市": (-0.5, +0.3, -0.3),
    "崩盘": (-0.9, +0.9, -0.6), "狂热": (+0.5, +0.9, +0.3),
    "焦虑": (-0.5, +0.6, -0.3), "平静": (+0.3, -0.6, +0.2),
    "喜悦": (+0.7, +0.5, +0.3), "悲伤": (-0.6, -0.3, -0.3),
    "愤怒": (-0.5, +0.6, +0.3), "惊喜": (+0.5, +0.7, -0.1),
    "绝望": (-0.8, -0.4, -0.7), "希望": (+0.5, +0.2, +0.2),
    "美丽": (+0.6, +0.2, +0.2), "创新": (+0.5, +0.4, +0.3),
    "突破": (+0.6, +0.6, +0.4), "震撼": (+0.3, +0.8, -0.2),
}


def text_to_emotion(text: str, base: EmotionVector | None = None) -> EmotionVector:
    """
    从文本推断 VAD 情感向量

    通过关键词匹配和加权平均计算文本的情感向量。
    支持中英文混合文本。

    算法:
        1. 分词 (空格 + 中文字符边界)
        2. 匹配关键词表，累加 VAD 偏移
        3. 归一化，使每个维度在 [-1, 1] 范围
        4. 与 base 向量混合 (如果提供)

    参数:
        text: 输入文本
        base: 基础情感向量 (可选，用于偏置结果)

    返回:
        EmotionVector
    """
    if base is None:
        base = EmotionVector(0.0, 0.0, 0.0)

    text_lower = text.lower()

    # 简单分词: 英文用空格，同时做中文子串匹配
    words = re.findall(r'[a-z]+', text_lower)

    total_v, total_a, total_d = 0.0, 0.0, 0.0
    weight_sum = 0.0

    # 英文词匹配
    for word in words:
        if word in _WORD_VAD:
            vad = _WORD_VAD[word]
            total_v += vad[0]
            total_a += vad[1]
            total_d += vad[2]
            weight_sum += 1.0

    # 中文子串匹配
    for keyword, vad in _WORD_VAD.items():
        if len(keyword) > 1 and keyword in text_lower:
            # 避免单个英文字母的重复匹配
            if not keyword.isascii():
                total_v += vad[0]
                total_a += vad[1]
                total_d += vad[2]
                weight_sum += 1.0

    if weight_sum > 0:
        # 使用 tanh 压缩，避免极端值，同时保留方向
        scale = 1.0 / math.sqrt(weight_sum)  # 词越多，每个词的影响越小
        v = math.tanh(total_v * scale)
        a = math.tanh(total_a * scale)
        d = math.tanh(total_d * scale)
        detected = EmotionVector(v, a, d)
    else:
        detected = EmotionVector(0.0, 0.0, 0.0)

    # 与 base 混合 (detected 权重更高)
    if base.magnitude() > 0.01:
        return detected.lerp(base, 0.3)
    return detected


def emotion_from_name(name: str) -> EmotionVector:
    """
    从预定义情绪名称获取 VAD 向量

    支持旧系统的情绪名称 (bull/bear/euphoria/etc.)
    和新增的细粒度情绪名称。

    参数:
        name: 情绪名称 (如 'joy', 'fear', 'bull')

    返回:
        EmotionVector (如果名称未知，返回 neutral)
    """
    return VAD_ANCHORS.get(name.lower(), VAD_ANCHORS["neutral"])


def blend_emotions(
    emotions: list[EmotionVector],
    weights: list[float] | None = None,
) -> EmotionVector:
    """
    多情感重心混合

    参数:
        emotions: 情感向量列表
        weights: 权重列表 (默认等权重)

    返回:
        混合后的 EmotionVector
    """
    if not emotions:
        return EmotionVector(0.0, 0.0, 0.0)

    if weights is None:
        weights = [1.0 / len(emotions)] * len(emotions)
    else:
        w_sum = sum(weights)
        if w_sum > 0:
            weights = [w / w_sum for w in weights]
        else:
            weights = [1.0 / len(emotions)] * len(emotions)

    v = sum(e.valence * w for e, w in zip(emotions, weights))
    a = sum(e.arousal * w for e, w in zip(emotions, weights))
    d = sum(e.dominance * w for e, w in zip(emotions, weights))

    return EmotionVector(v, a, d)


# === 内部工具 ===

def _remap(value: float, in_min: float, in_max: float,
           out_min: float, out_max: float) -> float:
    """线性范围映射"""
    t = (value - in_min) / (in_max - in_min)
    t = clamp(t, 0.0, 1.0)
    return out_min + t * (out_max - out_min)
