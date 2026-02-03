"""
随机视觉文法 - Stochastic Visual Grammar

用概率产生式规则组合视觉元素，实现组合爆炸式的输出多样性。

核心概念::

    - 每次渲染由文法展开一棵 "场景树"
    - Or 节点: 从多个候选中概率选择一个 (产生变化)
    - And 节点: 组合多个子元素 (产生复杂度)
    - 参数节点: 从连续分布采样 (产生微变)
    - 情感向量影响选择概率 (情绪驱动组合)

文法产生的变化维度::

    1. 背景效果选择 (6 种 + CPPN)
    2. 叠加效果选择 (可选第二层)
    3. 混合模式 (4 种)
    4. 布局算法 (scatter/grid/spiral/force/preset)
    5. 颜文字数量和分布
    6. 文字元素配置
    7. 动画组合
    8. 后处理管线

理论上限: 7 × 7 × 4 × 5 × 5 × 3 × 8 × 4 = 235,200 种离散组合
加上连续参数变化 → 无限

用法::

    from procedural.flexible.grammar import VisualGrammar

    grammar = VisualGrammar(seed=42)
    spec = grammar.generate(energy=0.7, warmth=0.3)
    # spec 是一个完整的渲染规格，可直接传给 FlexiblePipeline
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class SceneSpec:
    """
    场景规格 - 由文法生成的完整渲染规格

    描述一个可视化输出的所有组成部分，供 Pipeline 执行。
    """
    # 背景效果
    bg_effect: str = "plasma"
    bg_params: dict = field(default_factory=dict)

    # 叠加效果 (可选)
    overlay_effect: str | None = None
    overlay_params: dict = field(default_factory=dict)
    overlay_blend: str = "ADD"
    overlay_mix: float = 0.3

    # 布局
    layout_type: str = "random_scatter"
    layout_count: int = 6
    layout_params: dict = field(default_factory=dict)

    # 颜文字配置
    kaomoji_count: int = 6
    kaomoji_mood: str = "neutral"
    kaomoji_size_range: tuple = (80, 150)

    # 中心颜文字
    has_central_kaomoji: bool = True
    central_size: int = 200

    # 文字元素
    text_elements: list = field(default_factory=list)

    # 动画
    animations: list = field(default_factory=list)
    float_amp: float = 3.0
    breath_amp: float = 0.08

    # 装饰
    decoration_style: str = "corners"
    decoration_chars: list = field(default_factory=lambda: ["+", "+", "+", "+"])

    # 后处理
    sharpen: bool = True
    contrast: float = 1.2
    gradient_name: str = "classic"

    # 粒子字符
    particle_chars: str = "01·"

    # 颜色空间参数 (连续)
    warmth: float = 0.5
    saturation: float = 0.9
    brightness: float = 0.8


class VisualGrammar:
    """
    随机视觉文法

    基于概率产生式规则生成 SceneSpec。
    情感参数影响各规则的选择概率。
    """

    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def generate(
        self,
        energy: float = 0.5,
        warmth: float = 0.5,
        structure: float = 0.5,
        intensity: float = 0.5,
        valence: float = 0.0,
        arousal: float = 0.0,
    ) -> SceneSpec:
        """
        根据连续参数生成场景规格

        参数影响文法选择的概率分布:
            energy: 能量 (影响效果激烈程度)
            warmth: 色温 (影响颜色选择)
            structure: 结构性 (影响布局规则性)
            intensity: 强度 (影响装饰和后处理)
            valence: 效价 (正面/负面)
            arousal: 唤醒度

        返回:
            SceneSpec - 完整的渲染规格
        """
        spec = SceneSpec()

        # 设置颜色空间参数
        spec.warmth = warmth
        spec.saturation = _clamp(0.6 + intensity * 0.4, 0.0, 1.0)
        spec.brightness = _clamp(0.5 + valence * 0.3, 0.3, 1.0)

        # === 背景效果 ===
        spec.bg_effect = self._choose_bg_effect(energy, structure)
        spec.bg_params = self._generate_effect_params(
            spec.bg_effect, energy, structure
        )

        # === 叠加效果 (概率性) ===
        overlay_chance = 0.2 + energy * 0.4  # 高能量更可能叠加
        if self.rng.random() < overlay_chance:
            spec.overlay_effect = self._choose_overlay_effect(
                spec.bg_effect, energy
            )
            spec.overlay_params = self._generate_effect_params(
                spec.overlay_effect, energy * 0.7, structure
            )
            spec.overlay_blend = self._choose_blend_mode(energy)
            spec.overlay_mix = self.rng.uniform(0.15, 0.5)

        # === 布局 ===
        spec.layout_type = self._choose_layout(structure)
        spec.layout_count = self._choose_kaomoji_count(energy, structure)
        spec.kaomoji_count = spec.layout_count

        # === 颜文字大小范围 ===
        base_size = int(80 + intensity * 40)
        size_var = int(30 + energy * 40)
        spec.kaomoji_size_range = (
            max(60, base_size - size_var),
            min(200, base_size + size_var),
        )

        # === 中心颜文字 ===
        spec.has_central_kaomoji = self.rng.random() < (0.5 + structure * 0.3)
        spec.central_size = int(160 + intensity * 80)

        # === 动画 ===
        spec.float_amp = 1.0 + energy * 7.0
        spec.breath_amp = 0.02 + abs(arousal) * 0.13
        spec.animations = self._choose_animations(energy, arousal)

        # === 装饰 ===
        spec.decoration_style = self._choose_decoration_style(structure)
        spec.decoration_chars = self._choose_decoration_chars(energy, warmth)

        # === ASCII 梯度 ===
        spec.gradient_name = self._choose_gradient(energy, structure)

        # === 后处理 ===
        spec.sharpen = self.rng.random() < 0.7
        spec.contrast = 1.0 + intensity * 0.4

        # === 粒子字符 ===
        spec.particle_chars = self._choose_particle_chars(warmth, energy)

        # === 文字元素 ===
        spec.text_elements = self._choose_text_elements(
            valence, arousal, energy
        )

        # === 颜文字情绪 ===
        spec.kaomoji_mood = self._choose_kaomoji_mood(valence, arousal)

        return spec

    # === 产生式规则实现 ===

    def _choose_bg_effect(self, energy: float, structure: float) -> str:
        """
        选择背景效果

        高能量偏向 flame/plasma，高结构偏向 moire/sdf_shapes，
        低能量偏向 noise_field/wave。
        """
        weights = {
            "plasma":      0.5 + energy * 0.3,
            "wave":        0.5 + (1 - energy) * 0.3,
            "flame":       0.2 + energy * 0.6,
            "moire":       0.3 + structure * 0.4,
            "noise_field": 0.4 + (1 - energy) * 0.3,
            "sdf_shapes":  0.2 + structure * 0.4,
            "cppn":        0.3,  # CPPN 始终有机会
        }
        return self._weighted_choice(weights)

    def _choose_overlay_effect(self, bg_effect: str, energy: float) -> str:
        """
        选择叠加效果 (避免与背景相同)
        """
        candidates = {
            "plasma": 0.3,
            "wave": 0.3,
            "noise_field": 0.4,
            "moire": 0.2,
            "cppn": 0.3,
        }
        # 移除与背景相同的效果
        candidates.pop(bg_effect, None)
        return self._weighted_choice(candidates)

    def _choose_blend_mode(self, energy: float) -> str:
        """选择混合模式"""
        weights = {
            "ADD":      0.3 + energy * 0.3,
            "SCREEN":   0.3,
            "OVERLAY":  0.2 + energy * 0.2,
            "MULTIPLY": 0.2 + (1 - energy) * 0.2,
        }
        return self._weighted_choice(weights)

    def _choose_layout(self, structure: float) -> str:
        """
        选择布局算法

        高结构 → grid/preset, 低结构 → scatter/spiral
        """
        weights = {
            "random_scatter":   0.3 + (1 - structure) * 0.3,
            "grid_jitter":      0.2 + structure * 0.4,
            "spiral":           0.3,
            "force_directed":   0.2,
            "preset":           0.2 + structure * 0.3,
        }
        return self._weighted_choice(weights)

    def _choose_kaomoji_count(self, energy: float, structure: float) -> int:
        """选择颜文字数量"""
        base = 4 + int(energy * 4)
        variation = self.rng.randint(-2, 2)
        return max(2, min(12, base + variation))

    def _choose_animations(self, energy: float, arousal: float) -> list:
        """
        选择动画组合

        返回动画配置列表，高能量时动画更多、更强。
        """
        anims = []

        # 浮动动画 (几乎总是启用)
        if self.rng.random() < 0.85:
            anims.append({
                "type": "floating",
                "amp": 1.0 + energy * 7.0,
                "speed": 0.5 + energy * 2.0,
            })

        # 呼吸动画
        if self.rng.random() < 0.7:
            anims.append({
                "type": "breathing",
                "amp": 0.02 + abs(arousal) * 0.13,
                "speed": 1.0 + energy * 2.0,
            })

        # 颜色循环 (概率性)
        if self.rng.random() < 0.3 + energy * 0.3:
            anims.append({
                "type": "color_cycle",
                "speed": 0.1 + energy * 0.5,
                "saturation": 0.7 + energy * 0.3,
            })

        return anims

    def _choose_decoration_style(self, structure: float) -> str:
        """选择装饰风格 (含 box-drawing 边框/网格/电路风格)"""
        weights = {
            "corners":      0.20 + structure * 0.15,
            "edges":        0.12 + structure * 0.12,
            "scattered":    0.20 + (1 - structure) * 0.15,
            "minimal":      0.12,
            "none":         0.06,
            # 新增 box-drawing 装饰风格
            "frame":        0.10 + structure * 0.20,
            "grid_lines":   0.06 + structure * 0.15,
            "circuit":      0.08 + (1 - structure) * 0.08,
        }
        return self._weighted_choice(weights)

    def _choose_decoration_chars(
        self, energy: float, warmth: float
    ) -> list[str]:
        """选择装饰字符 (含 box-drawing 和 semigraphic 字符)"""
        # 经典 ASCII 装饰
        classic_sets = [
            ["+", "+", "+", "+"],
            [".", ".", ".", "."],
            ["x", "x", "x", "x"],
            ["|", "|", "|", "|"],
            ["/", "\\", "/", "\\"],
            ["*", "*", "*", "*"],
            ["#", "#", "#", "#"],
            ["~", "~", "~", "~"],
            ["{}", "[]", "<>", "()"],
            ["====", "====", "----", "----"],
            [">>", "<<", ">>", "<<"],
            [":::", ":::", ":::", ":::"],
        ]

        # Box-drawing 角落装饰
        box_corner_sets = [
            ["┌", "┐", "└", "┘"],
            ["╭", "╮", "╰", "╯"],
            ["┏", "┓", "┗", "┛"],
            ["╔", "╗", "╚", "╝"],
            ["┌─", "─┐", "└─", "─┘"],
            ["╔═", "═╗", "╚═", "═╝"],
            ["┏━", "━┓", "┗━", "━┛"],
            ["╭─", "─╮", "╰─", "─╯"],
        ]

        # Box-drawing 线条装饰
        box_line_sets = [
            ["─", "─", "│", "│"],
            ["━", "━", "┃", "┃"],
            ["═", "═", "║", "║"],
            ["┄", "┄", "┆", "┆"],
            ["┈", "┈", "┊", "┊"],
            ["├", "┤", "┬", "┴"],
            ["┣", "┫", "┳", "┻"],
            ["╠", "╣", "╦", "╩"],
        ]

        # 交叉/节点装饰
        cross_sets = [
            ["┼", "┼", "┼", "┼"],
            ["╋", "╋", "╋", "╋"],
            ["╬", "╬", "╬", "╬"],
            ["╳", "╳", "╳", "╳"],
        ]

        # 方块/几何装饰
        block_sets = [
            ["░", "░", "░", "░"],
            ["▪", "▫", "▪", "▫"],
            ["■", "□", "■", "□"],
            ["▛", "▜", "▙", "▟"],
            ["▀", "▄", "▌", "▐"],
            ["●", "○", "●", "○"],
            ["◆", "◇", "◆", "◇"],
            ["◉", "◎", "◉", "◎"],
        ]

        # 点阵装饰
        dot_sets = [
            ["·", "·", "·", "·"],
            ["∙", "∙", "∙", "∙"],
            ["•", "◦", "•", "◦"],
            ["○", "◎", "○", "◎"],
        ]

        # 根据 energy/warmth 权重选择类别
        if energy > 0.7:
            # 高能量: 偏向粗重和几何
            pool = box_corner_sets + cross_sets + block_sets
        elif energy > 0.4:
            # 中等能量: 混合
            pool = classic_sets + box_corner_sets + box_line_sets
        elif warmth > 0.6:
            # 暖色低能量: 圆润
            pool = dot_sets + [["╭", "╮", "╰", "╯"]] + classic_sets[:4]
        else:
            # 冷色低能量: 细线
            pool = dot_sets + box_line_sets[:3] + classic_sets[:4]

        return self.rng.choice(pool)

    def _choose_gradient(self, energy: float, structure: float) -> str:
        """选择 ASCII 梯度 (含 box-drawing 和几何梯度)"""
        weights = {
            # 经典
            "classic":          0.20,
            "smooth":           0.12,
            "matrix":           0.10 + energy * 0.10,
            "plasma":           0.10 + energy * 0.15,
            # 方块
            "blocks":           0.10 + structure * 0.15,
            "blocks_fine":      0.08 + structure * 0.10,
            "glitch":           0.05 + energy * 0.15,
            # Box-drawing
            "box_density":      0.06 + structure * 0.12,
            "box_cross":        0.04 + structure * 0.08 + energy * 0.08,
            "circuit":          0.04 + structure * 0.10 + energy * 0.06,
            # 几何/点阵
            "dots_density":     0.06 + (1 - energy) * 0.08,
            "geometric":        0.05 + structure * 0.08,
            "braille_density":  0.04 + (1 - structure) * 0.06,
            # 混合
            "tech":             0.06 + energy * 0.06,
            "cyber":            0.04 + energy * 0.08,
            "organic":          0.05 + (1 - structure) * 0.08,
        }
        return self._weighted_choice(weights)

    def _choose_particle_chars(self, warmth: float, energy: float) -> str:
        """选择粒子字符 (含 box-drawing 和 semigraphic 字符)"""
        # 经典
        classic = [
            "01·",
            "0123456789",
            "*o.:-",
            "$#@!",
            "+-×÷",
            "~≈≋",
        ]

        # 几何/圆点
        geometric = [
            "·•○◦",
            "·∙•◦○◎",
            "◦○◎◉●",
            "▪▫□■▮",
            "◆◇◈◉◎",
            "△▽○□◇",
        ]

        # Box-drawing 线段
        box_lines = [
            "─│┼┄┆",
            "━┃╋┅┇",
            "═║╬",
            "├┤┬┴┼",
            "┣┫┳┻╋",
            "╠╣╦╩╬",
            "╱╲╳",
        ]

        # 方块
        blocks = [
            "░▒▓",
            "░▒▓█",
            "▀▄▌▐█",
            "▖▗▘▙▚▛▜▝",
        ]

        # 盲文点阵
        braille = [
            "⠁⠂⠃⠄⠅⠆⠇",
            "⣀⣁⣂⣃⣄⣅⣆⣇",
        ]

        # 根据 energy/warmth 倾向选择
        if energy > 0.7:
            pool = box_lines + blocks + classic[:3]
        elif energy > 0.4:
            pool = classic + geometric + box_lines[:3]
        elif warmth > 0.6:
            pool = geometric + braille + classic[:2]
        else:
            pool = classic + geometric[:3] + braille

        return self.rng.choice(pool)

    def _generate_effect_params(
        self, effect_name: str, energy: float, structure: float
    ) -> dict:
        """
        为效果生成连续参数

        不同于旧系统的固定范围随机，这里参数受 energy/structure 影响。
        """
        rng = self.rng

        if effect_name == "plasma":
            return {
                "frequency": rng.uniform(0.02, 0.08 + energy * 0.12),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
                "color_phase": rng.uniform(0.0, 1.0),
            }
        elif effect_name == "wave":
            return {
                "wave_count": rng.randint(1, 3 + int(energy * 7)),
                "frequency": rng.uniform(0.02, 0.05 + energy * 0.15),
                "amplitude": rng.uniform(0.5, 1.0 + energy * 2.0),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
            }
        elif effect_name == "flame":
            return {
                "intensity": rng.uniform(0.5, 1.0 + energy * 2.0),
            }
        elif effect_name == "moire":
            base_freq = 2.0 + structure * 10.0
            return {
                "freq_a": rng.uniform(base_freq * 0.5, base_freq * 1.5),
                "freq_b": rng.uniform(base_freq * 0.5, base_freq * 1.5),
                "speed_a": rng.uniform(-2.0, 2.0) * (0.5 + energy),
                "speed_b": rng.uniform(-2.0, 2.0) * (0.5 + energy),
                "offset_a": rng.uniform(-0.5, 0.5),
                "offset_b": rng.uniform(-0.5, 0.5),
            }
        elif effect_name == "noise_field":
            return {
                "scale": rng.uniform(0.02, 0.05 + energy * 0.15),
                "octaves": rng.randint(2, 3 + int(structure * 5)),
                "lacunarity": rng.uniform(1.5, 2.0 + structure),
                "gain": rng.uniform(0.3, 0.5 + structure * 0.3),
                "animate": rng.random() < (0.5 + energy * 0.4),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
                "turbulence": rng.random() < (0.3 + energy * 0.4),
            }
        elif effect_name == "sdf_shapes":
            return {
                "shape_count": rng.randint(2, 3 + int(energy * 7)),
                "shape_type": rng.choice(["circle", "box"]),
                "radius_min": rng.uniform(0.02, 0.05 + structure * 0.05),
                "radius_max": rng.uniform(0.1, 0.15 + structure * 0.15),
                "smoothness": rng.uniform(0.05, 0.1 + structure * 0.2),
                "animate": rng.random() < (0.5 + energy * 0.4),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
            }
        elif effect_name == "cppn":
            return {
                "num_hidden": rng.randint(2, 5),
                "layer_size": rng.choice([4, 6, 8, 10, 12]),
                "seed": rng.randint(0, 100000),
            }
        else:
            return {}

    def _choose_text_elements(
        self, valence: float, arousal: float, energy: float
    ) -> list[dict]:
        """
        生成氛围文字元素

        根据情绪维度选择散布在画面中的氛围文字词汇。
        每个元素包含 text, position (相对), size, opacity。
        """
        # 根据能量决定数量 (0-3)
        count = 0
        if self.rng.random() < 0.3 + energy * 0.4:
            count = self.rng.randint(1, 3)
        if count == 0:
            return []

        # 根据情绪选择词池 (含 box-drawing/semigraphic 装饰符号)
        if valence > 0.5:
            if arousal > 0.3:
                pool = ["RISE", "UP", "BULL", "GO", "YES", "MAX", "TOP",
                        "涨", "牛", "冲", "↑", "▲",
                        "━━▶", "╱╲╱", "◉", "█▀█", "⣿"]
            else:
                pool = ["calm", "flow", "ease", "zen", "~",
                        "静", "和", "润", "◎", "○",
                        "╭─╮", "≈≈", "◌", "⠿", "·∙·"]
        elif valence > 0.0:
            pool = ["...", "---", "===", "~", "○", "△",
                    "等", "观", "守", "…",
                    "─┄─", "┈┈┈", "╌╌╌", "◦◦◦"]
        elif valence > -0.5:
            if arousal > 0.3:
                pool = ["?!", "WARN", "ALERT", "!!",
                        "慌", "急", "!", "⚠", "△",
                        "╳╳╳", "┃┃┃", "▓▓▓", "╋╋╋"]
            else:
                pool = ["...", "fade", "dim", "gray",
                        "淡", "沉", "暗", "—",
                        "┄┄┄", "░░░", "┆┆┆", "⠁⠂⠄"]
        else:
            if arousal > 0.3:
                pool = ["SELL", "DOWN", "BEAR", "RUN", "NO", "STOP",
                        "跌", "崩", "逃", "↓", "▼",
                        "█▄█", "━━╋", "▓█▓", "╬╬╬"]
            else:
                pool = ["...", "___", "void", "null",
                        "空", "无", "寂", "—",
                        "░░░", "┈┈┈", "⠀⠀⠀", "···"]

        elements = []
        for _ in range(count):
            text = self.rng.choice(pool)
            elements.append({
                "text": text,
                "position": (
                    self.rng.uniform(0.1, 0.9),
                    self.rng.uniform(0.1, 0.9),
                ),
                "size": self.rng.uniform(0.6, 1.5),
                "opacity": self.rng.uniform(0.3, 0.8),
            })

        return elements

    def _choose_kaomoji_mood(self, valence: float, arousal: float) -> str:
        """
        根据 valence + arousal 二维空间选择颜文字情绪类别

        作为 SceneSpec 的参考情绪，pipeline 可用作 fallback。
        """
        high_a = arousal > 0.3
        if valence > 0.5:
            return "euphoria" if high_a else "happy"
        elif valence > 0.0:
            return "excitement" if high_a else "relaxed"
        elif valence > -0.3:
            return "confused" if high_a else "bored"
        elif valence > -0.6:
            return "anxiety" if high_a else "sad"
        else:
            return "panic" if high_a else "lonely"

    # === 工具方法 ===

    def _weighted_choice(self, weights: dict[str, float]) -> str:
        """加权随机选择"""
        items = list(weights.items())
        total = sum(w for _, w in items)
        if total <= 0:
            return items[0][0]

        r = self.rng.random() * total
        cumulative = 0.0
        for name, w in items:
            cumulative += w
            if r <= cumulative:
                return name
        return items[-1][0]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
