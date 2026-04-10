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
from typing import Any

try:
    from lib.box_chars import CHARSETS, BORDER_SETS
except ImportError:
    from viz.lib.box_chars import CHARSETS, BORDER_SETS


@dataclass
class SceneSpec:
    """
    场景规格 - 由文法生成的完整渲染规格

    描述一个可视化输出的所有组成部分，供 Pipeline 执行。
    """

    # 背景效果
    bg_effect: str = "plasma"
    bg_params: dict[str, Any] = field(default_factory=dict)

    # 叠加效果 (可选)
    overlay_effect: str | None = None
    overlay_params: dict[str, Any] = field(default_factory=dict)
    overlay_blend: str = "ADD"
    overlay_mix: float = 0.3

    # 布局
    layout_type: str = "random_scatter"
    layout_count: int = 6
    layout_params: dict[str, Any] = field(default_factory=dict)

    # 颜文字配置
    kaomoji_count: int = 6
    kaomoji_mood: str = "neutral"
    kaomoji_size_range: tuple[int, int] = (100, 200)

    # 中心颜文字
    has_central_kaomoji: bool = True
    central_size: int = 250

    # 文字元素
    text_elements: list[dict[str, Any]] = field(default_factory=list)

    # 动画
    animations: list[dict[str, Any]] = field(default_factory=list)
    float_amp: float = 3.0
    breath_amp: float = 0.08

    # 装饰
    decoration_style: str = "corners"
    decoration_chars: list[str] = field(default_factory=lambda: ["+", "+", "+", "+"])

    # 后处理
    sharpen: bool = True
    contrast: float = 1.2
    gradient_name: str = "classic"
    postprocess_spec: dict[str, Any] = field(default_factory=dict)
    brightness_floor: float = 0.20

    # 粒子字符
    particle_chars: str = "01·"

    # 颜色空间参数 (连续)
    warmth: float = 0.5
    saturation: float = 0.9
    brightness: float = 0.8

    # Content placement (from AI input)
    content_headline: str | None = None
    content_metrics: list[str] = field(default_factory=list)
    content_timestamp: str | None = None
    content_body: str | None = None
    kaomoji_mood_overrides: list[str] | None = None

    # 域变换 (Domain transforms)
    domain_transforms: list[dict[str, Any]] = field(default_factory=list)

    # 后处理链 (Post-FX chain)
    postfx_chain: list[dict[str, Any]] = field(default_factory=list)

    # 合成模式 (Composition mode)
    composition_mode: str = "blend"
    mask_type: str | None = None
    mask_params: dict[str, Any] = field(default_factory=dict)

    # 背景填充规格 (第二渲染通道)
    bg_fill_spec: dict[str, Any] = field(default_factory=dict)
    # 颜色方案
    color_scheme: str = "heat"
    # 自定义调色盘 (覆盖 color_scheme)
    palette: list[tuple[int, int, int]] | None = None


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
        dominance: float = 0.0,
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
        spec.bg_params = self._generate_effect_params(spec.bg_effect, energy, structure)

        # === 叠加效果 (概率性) ===
        overlay_chance = 0.45 + energy * 0.35  # 高能量更可能叠加
        if self.rng.random() < overlay_chance:
            spec.overlay_effect = self._choose_overlay_effect(spec.bg_effect, energy)
            spec.overlay_params = self._generate_effect_params(
                spec.overlay_effect, energy * 0.7, structure
            )
            spec.overlay_blend = self._choose_blend_mode(energy)
            spec.overlay_mix = self.rng.uniform(0.05, 0.95)

        # === 域变换 ===
        spec.domain_transforms = self._choose_domain_transforms(energy, structure)

        # === 合成模式 (当有叠加效果时) ===
        if spec.overlay_effect is not None:
            comp = self._choose_composition_mode(energy, structure)
            spec.composition_mode = comp["mode"]
            spec.mask_type = comp.get("mask_type")
            spec.mask_params = comp.get("mask_params", {})

        # === 后处理链 ===
        spec.postfx_chain = self._choose_postfx_chain(energy, structure, intensity)

        # === 布局 ===
        spec.layout_type = self._choose_layout(structure)
        spec.layout_count = self._choose_kaomoji_count(energy, structure)
        spec.kaomoji_count = spec.layout_count

        # === 颜文字大小范围 ===
        base_size = int(100 + intensity * 50)
        size_var = int(30 + energy * 50)
        spec.kaomoji_size_range = (
            max(90, base_size - size_var),
            min(250, base_size + size_var),
        )

        # === 中心颜文字 ===
        spec.has_central_kaomoji = self.rng.random() < (0.5 + structure * 0.3)
        spec.central_size = int(200 + intensity * 100)

        # === 动画 ===
        spec.float_amp = 1.0 + energy * 7.0
        spec.breath_amp = 0.02 + abs(arousal) * 0.13
        spec.animations = self._choose_animations(energy, arousal)

        # === 装饰 ===
        spec.decoration_style = self._choose_decoration_style(structure)
        spec.decoration_chars = self._choose_decoration_chars(energy, warmth)

        # === ASCII 梯度 ===
        spec.gradient_name = self._choose_gradient(energy, structure)

        # === 后处理 — 随机选择滤镜模式，拓宽对比度范围 ===
        filter_mode = self.rng.choice(["sharpen", "sharpen", "none", "blur", "detail"])
        spec.sharpen = (filter_mode == "sharpen")
        spec.contrast = _clamp(0.7 + self.rng.uniform(0, 1.1), 0.7, 1.8)
        spec.postprocess_spec = {"filter_mode": filter_mode, "contrast": spec.contrast}
        if filter_mode == "blur":
            spec.postprocess_spec["blur_radius"] = self.rng.uniform(0.5, 2.0)
        # 极端情绪微调亮度
        if valence < -0.5 and arousal < -0.3:
            spec.postprocess_spec["brightness_adjust"] = self.rng.uniform(0.75, 0.92)
        elif valence > 0.7 and arousal > 0.5:
            spec.postprocess_spec["brightness_adjust"] = self.rng.uniform(1.03, 1.15)

        # === 亮度地板 (emotion 驱动动态范围) ===
        if valence < -0.3:
            floor_base = 0.10 + (1 + valence) * 0.12
        else:
            floor_base = 0.18 + valence * 0.08
        spec.brightness_floor = _clamp(
            floor_base + self.rng.uniform(-0.05, 0.05), 0.08, 0.40
        )

        # === 粒子字符 ===
        spec.particle_chars = self._choose_particle_chars(warmth, energy)

        # === 文字元素 ===
        spec.text_elements = self._choose_text_elements(valence, arousal, energy)

        # === 颜文字情绪 ===
        spec.kaomoji_mood = self._choose_kaomoji_mood(valence, arousal, dominance)

        # === 程序化调色板 (每个 seed 独特配色) ===
        try:
            from procedural.palette import generate_palette
        except ImportError:
            from viz.procedural.palette import generate_palette
        palette_seed = self.rng.randint(0, 0xFFFFFF)
        spec.palette = generate_palette(palette_seed, warmth, energy, spec.saturation)
        spec.color_scheme = "heat"  # 回退默认，仅 Director Mode 显式指定时使用

        # === 背景填充 (第二渲染通道，独立调色板) ===
        spec.bg_fill_spec = self._choose_bg_fill_spec(
            energy, structure, warmth, spec.bg_effect
        )
        # bg_fill 用独立的程序化调色板
        bg_palette_seed = self.rng.randint(0, 0xFFFFFF)
        spec.bg_fill_spec["palette"] = generate_palette(
            bg_palette_seed, warmth, energy * 0.7, spec.saturation * 0.8
        )
        spec.bg_fill_spec["color_scheme"] = spec.color_scheme

        return spec

    # === 产生式规则实现 ===

    def _choose_bg_effect(self, energy: float, structure: float) -> str:
        """
        选择背景效果 — 近均匀随机，情绪仅微偏

        17 种效果接近等概率。energy/structure 只提供 ≤20% 的轻微倾向。
        """
        try:
            from procedural.effects import EFFECT_REGISTRY
        except ImportError:
            from viz.procedural.effects import EFFECT_REGISTRY
        effects = sorted(EFFECT_REGISTRY.keys())
        boost: dict[str, float] = {}
        if energy > 0.6:
            for e in ["flame", "chroma_spiral", "dyna", "game_of_life"]:
                boost[e] = 0.15
        elif energy < 0.4:
            for e in ["noise_field", "wave", "wobbly", "sand_game", "slime_dish"]:
                boost[e] = 0.15
        if structure > 0.6:
            for e in ["sdf_shapes", "wireframe_cube", "mod_xor", "ten_print", "moire"]:
                boost[e] = 0.12
        elif structure < 0.4:
            for e in ["wobbly", "noise_field", "cppn", "plasma"]:
                boost[e] = 0.12
        return self._biased_choice(effects, boost)

    def _choose_overlay_effect(self, bg_effect: str, energy: float) -> str:
        """
        选择叠加效果 — 从全部效果中均匀选择 (排除与背景相同的)
        """
        try:
            from procedural.effects import EFFECT_REGISTRY
        except ImportError:
            from viz.procedural.effects import EFFECT_REGISTRY
        candidates = [e for e in sorted(EFFECT_REGISTRY.keys()) if e != bg_effect]
        return self.rng.choice(candidates)

    def _choose_blend_mode(self, energy: float) -> str:
        """选择混合模式 — 均匀随机"""
        return self.rng.choice(["ADD", "SCREEN", "OVERLAY", "MULTIPLY"])

    def _choose_layout(self, structure: float) -> str:
        """选择布局算法 — 均匀随机"""
        return self.rng.choice(["random_scatter", "grid_jitter", "spiral",
                                "force_directed", "preset"])

    def _choose_kaomoji_count(self, energy: float, structure: float) -> int:
        """选择颜文字数量"""
        base = 4 + int(energy * 4)
        variation = self.rng.randint(-3, 3)
        return max(2, min(12, base + variation))

    def _choose_animations(self, energy: float, arousal: float) -> list[dict[str, Any]]:
        """
        选择动画组合

        返回动画配置列表，高能量时动画更多、更强。
        """
        anims = []

        # 浮动动画 (几乎总是启用)
        if self.rng.random() < 0.85:
            anims.append(
                {
                    "type": "floating",
                    "amp": 1.0 + energy * 7.0,
                    "speed": 0.5 + energy * 2.0,
                }
            )

        # 呼吸动画
        if self.rng.random() < 0.7:
            anims.append(
                {
                    "type": "breathing",
                    "amp": 0.02 + abs(arousal) * 0.13,
                    "speed": 1.0 + energy * 2.0,
                }
            )

        # 颜色循环 (概率性)
        if self.rng.random() < 0.3 + energy * 0.3:
            anims.append(
                {
                    "type": "color_cycle",
                    "speed": 0.1 + energy * 0.5,
                    "saturation": 0.7 + energy * 0.3,
                }
            )

        return anims

    def _choose_decoration_style(self, structure: float) -> str:
        """选择装饰风格 — 均匀随机"""
        return self.rng.choice(["corners", "edges", "scattered", "minimal",
                                "none", "frame", "grid_lines", "circuit"])

    def _choose_decoration_chars(self, energy: float, warmth: float) -> list[str]:
        """选择装饰字符 (含 box-drawing 和 semigraphic 字符)"""
        # 经典 ASCII 装饰 (纯 ASCII，保持内联)
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

        # Box-drawing 角落装饰 (from BORDER_SETS)
        _bs_light = BORDER_SETS["light"]
        _bs_round = BORDER_SETS["round"]
        _bs_heavy = BORDER_SETS["heavy"]
        _bs_double = BORDER_SETS["double"]
        box_corner_sets = [
            [_bs_light["tl"], _bs_light["tr"], _bs_light["bl"], _bs_light["br"]],
            [_bs_round["tl"], _bs_round["tr"], _bs_round["bl"], _bs_round["br"]],
            [_bs_heavy["tl"], _bs_heavy["tr"], _bs_heavy["bl"], _bs_heavy["br"]],
            [_bs_double["tl"], _bs_double["tr"], _bs_double["bl"], _bs_double["br"]],
            [_bs_light["tl"] + _bs_light["h"], _bs_light["h"] + _bs_light["tr"],
             _bs_light["bl"] + _bs_light["h"], _bs_light["h"] + _bs_light["br"]],
            [_bs_double["tl"] + _bs_double["h"], _bs_double["h"] + _bs_double["tr"],
             _bs_double["bl"] + _bs_double["h"], _bs_double["h"] + _bs_double["br"]],
            [_bs_heavy["tl"] + _bs_heavy["h"], _bs_heavy["h"] + _bs_heavy["tr"],
             _bs_heavy["bl"] + _bs_heavy["h"], _bs_heavy["h"] + _bs_heavy["br"]],
            [_bs_round["tl"] + _bs_round["h"], _bs_round["h"] + _bs_round["tr"],
             _bs_round["bl"] + _bs_round["h"], _bs_round["h"] + _bs_round["br"]],
        ]

        # Box-drawing 线条装饰 (from BORDER_SETS)
        _bs_dl = BORDER_SETS["dash_light"]
        _bs_dh = BORDER_SETS["dash_heavy"]
        box_line_sets = [
            [_bs_light["h"], _bs_light["h"], _bs_light["v"], _bs_light["v"]],
            [_bs_heavy["h"], _bs_heavy["h"], _bs_heavy["v"], _bs_heavy["v"]],
            [_bs_double["h"], _bs_double["h"], _bs_double["v"], _bs_double["v"]],
            [_bs_dl["h"], _bs_dl["h"], _bs_dl["v"], _bs_dl["v"]],
            [_bs_dh["h"], _bs_dh["h"], _bs_dh["v"], _bs_dh["v"]],
            [_bs_light["lt"], _bs_light["rt"], _bs_light["tt"], _bs_light["bt"]],
            [_bs_heavy["lt"], _bs_heavy["rt"], _bs_heavy["tt"], _bs_heavy["bt"]],
            [_bs_double["lt"], _bs_double["rt"], _bs_double["tt"], _bs_double["bt"]],
        ]

        # 交叉/节点装饰 (from BORDER_SETS cross keys)
        cross_sets = [
            [_bs_light["cross"]] * 4,
            [_bs_heavy["cross"]] * 4,
            [_bs_double["cross"]] * 4,
            ["╳", "╳", "╳", "╳"],
        ]

        # 方块/几何装饰 (from CHARSETS)
        _blk_full = CHARSETS["blocks_full"]
        _blk_half = CHARSETS["blocks_half"]
        _blk_quarter = CHARSETS["blocks_quarter"]
        _geo_filled = CHARSETS["geometric_filled"]
        block_sets = [
            [_blk_full[0]] * 4,                              # ░░░░
            [_geo_filled[1], _geo_filled[1], _geo_filled[1], _geo_filled[1]],  # ▪▪▪▪
            [_geo_filled[0], _geo_filled[0], _geo_filled[0], _geo_filled[0]],  # ■■■■
            list(_blk_quarter[:4]),                           # ▖▗▘▙
            list(_blk_half[:4]),                              # ▀▄▌▐
            [_geo_filled[3], _geo_filled[3], _geo_filled[3], _geo_filled[3]],  # ●●●●
            [_geo_filled[5], _geo_filled[5], _geo_filled[5], _geo_filled[5]],  # ◆◆◆◆
        ]

        # 点阵装饰 (from CHARSETS)
        _dots = CHARSETS["dots"]
        _circles = CHARSETS["geometric_circles"]
        dot_sets = [
            [_dots[0]] * 4,                          # ····
            [_dots[1]] * 4,                          # ∙∙∙∙
            [_dots[2], _dots[3], _dots[2], _dots[3]],  # •◦•◦
            [_circles[1], _circles[2], _circles[1], _circles[2]],  # ○◉○◉
        ]

        # 星星装饰 (from CHARSETS - 新增)
        _stars = CHARSETS["stars"]
        _sparkles = CHARSETS["sparkles"]
        star_sets = [
            [_stars[0], _stars[1], _stars[0], _stars[1]],     # ✦✧✦✧
            [_stars[2], _stars[3], _stars[2], _stars[3]],     # ★☆★☆
            [_sparkles[0], _sparkles[1], _sparkles[0], _sparkles[1]],
            [_stars[4], _sparkles[2], _stars[4], _sparkles[2]],
        ]

        # 箭头装饰 (from CHARSETS - 新增)
        _arrows = CHARSETS["arrows"]
        _arrows_t = CHARSETS["arrows_thin"]
        arrow_sets = [
            [_arrows[0], _arrows[2], _arrows[1], _arrows[3]],  # ←→↑↓
            [_arrows_t[0], _arrows_t[1], _arrows_t[2], _arrows_t[3]],
            [_arrows[4], _arrows[5], _arrows[4], _arrows[5]],  # ↔↕↔↕
            [_arrows[6], _arrows[7], _arrows[8], _arrows[9]],
        ]

        # Probability-weighted pool (all categories always available)
        pool_weights = [
            (classic_sets, 0.18),
            (box_corner_sets, 0.13 + energy * 0.13),
            (box_line_sets, 0.10 + (1 - energy) * 0.08),
            (cross_sets, 0.07 + energy * 0.10),
            (block_sets, 0.09 + energy * 0.09),
            (dot_sets, 0.09 + (1 - energy) * 0.08 + warmth * 0.04),
            (star_sets, 0.06 + warmth * 0.08),
            (arrow_sets, 0.06 + energy * 0.08),
        ]

        # Weighted category selection
        total = sum(w for _, w in pool_weights)
        r = self.rng.random() * total
        cumulative = 0.0
        selected_pool = classic_sets
        for pool, w in pool_weights:
            cumulative += w
            if r <= cumulative:
                selected_pool = pool
                break

        return self.rng.choice(selected_pool)

    def _choose_gradient(self, energy: float, structure: float) -> str:
        """选择 ASCII 梯度 — 从全部 73 种中均匀随机"""
        try:
            from procedural.palette import ASCII_GRADIENTS
        except ImportError:
            from viz.procedural.palette import ASCII_GRADIENTS
        return self.rng.choice(sorted(ASCII_GRADIENTS.keys()))

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

        # 几何/圆点 (from CHARSETS)
        _dots = CHARSETS["dots"]
        _circles = CHARSETS["geometric_circles"]
        _geo_f = CHARSETS["geometric_filled"]
        geometric = [
            _dots[:4],                   # ·∙•◦
            _dots[:6],                   # ·∙•◦○◎
            _circles[:5],                # ●○◉◎◦
            _geo_f[:4],                  # ■▪▮●
            _geo_f[4:7],                 # ▲▼◆
        ]

        # Box-drawing 线段 (from CHARSETS)
        _box_l = CHARSETS["box_light"]
        _box_h = CHARSETS["box_heavy"]
        _box_d = CHARSETS["box_double"]
        box_lines = [
            _box_l[:5],                  # ─│┌┐└
            _box_h[:5],                  # ━┃┏┓┗
            _box_d[:5],                  # ═║╔╗╚
            _box_l[6:],                  # ┤┬┴┼
            _box_h[6:],                  # ┫┳┻╋
            _box_d[6:],                  # ╣╦╩╬
            CHARSETS["box_diagonal"],    # ╱╲╳
        ]

        # 方块 (from CHARSETS)
        _blk_full = CHARSETS["blocks_full"]
        _blk_half = CHARSETS["blocks_half"]
        _blk_quarter = CHARSETS["blocks_quarter"]
        blocks = [
            _blk_full[:3],               # ░▒▓
            _blk_full,                   # ░▒▓█
            _blk_half + "█",             # ▀▄▌▐█
            _blk_quarter,                # ▖▗▘▙▚▛▜▝
        ]

        # 盲文点阵 (from CHARSETS)
        _braille = CHARSETS["braille"]
        braille = [
            _braille[1:8],               # ⠁⠂⠃⠄⠅⠆⠇
            _braille[10:18],             # ⣀⣁⣂⣃⣄⣅⣆⣇
        ]

        # 星星/闪烁 (from CHARSETS - 新增)
        _stars = CHARSETS["stars"]
        _sparkles = CHARSETS["sparkles"]
        stars_sparkles = [
            _stars[:5],                  # ✦✧★☆✶
            _sparkles[:5],               # ⁺⁎∗✦✧
            _stars[:3] + _sparkles[:3],  # ✦✧★⁺⁎∗
        ]

        # 箭头/数学 (from CHARSETS - 新增)
        _arrows = CHARSETS["arrows"]
        _math_ops = CHARSETS["math_operators"]
        arrows_math = [
            _arrows[:6],                 # ←↑→↓↔↕
            _math_ops[:6],               # ±×÷∓∞≈
            _arrows[:4] + _math_ops[:2], # ←↑→↓±×
        ]

        # Probability-weighted pool (all categories always available)
        pool_weights = [
            (classic, 0.18),
            (geometric, 0.13 + (1 - energy) * 0.08),
            (box_lines, 0.10 + energy * 0.13),
            (blocks, 0.09 + energy * 0.10),
            (braille, 0.07 + (1 - energy) * 0.07 + warmth * 0.04),
            (stars_sparkles, 0.06 + warmth * 0.08),
            (arrows_math, 0.06 + energy * 0.08),
        ]

        total = sum(w for _, w in pool_weights)
        r = self.rng.random() * total
        cumulative = 0.0
        selected_pool = classic
        for pool, w in pool_weights:
            cumulative += w
            if r <= cumulative:
                selected_pool = pool
                break

        return self.rng.choice(selected_pool)

    def _generate_effect_params(
        self, effect_name: str, energy: float, structure: float
    ) -> dict[str, Any]:
        """
        为效果生成连续参数

        不同于旧系统的固定范围随机，这里参数受 energy/structure 影响。
        变体注册表提供结构变化，抖动提供微观变化。
        """
        rng = self.rng

        if effect_name == "plasma":
            params = {
                "frequency": self._jitter(
                    rng.uniform(0.02, 0.08 + energy * 0.12), 0.03, 0.005, 0.3),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
                "color_phase": rng.uniform(0.0, 1.0),
            }
        elif effect_name == "wave":
            params = {
                "wave_count": rng.randint(1, 3 + int(energy * 7)),
                "frequency": self._jitter(
                    rng.uniform(0.02, 0.05 + energy * 0.15), 0.02, 0.005, 0.3),
                "amplitude": rng.uniform(0.5, 1.0 + energy * 2.0),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
            }
        elif effect_name == "flame":
            params = {
                "intensity": rng.uniform(0.5, 1.0 + energy * 2.0),
            }
        elif effect_name == "moire":
            base_freq = 2.0 + structure * 10.0
            params = {
                "freq_a": self._jitter(
                    rng.uniform(base_freq * 0.5, base_freq * 1.5), 2.0, 1.0, 25.0),
                "freq_b": self._jitter(
                    rng.uniform(base_freq * 0.5, base_freq * 1.5), 2.0, 1.0, 25.0),
                "speed_a": rng.uniform(-2.0, 2.0) * (0.5 + energy),
                "speed_b": rng.uniform(-2.0, 2.0) * (0.5 + energy),
                "offset_a": rng.uniform(-0.5, 0.5),
                "offset_b": rng.uniform(-0.5, 0.5),
            }
        elif effect_name == "noise_field":
            params = {
                "scale": rng.uniform(0.02, 0.05 + energy * 0.15),
                "octaves": rng.randint(2, 3 + int(structure * 5)),
                "lacunarity": rng.uniform(1.5, 2.0 + structure),
                "gain": rng.uniform(0.3, 0.5 + structure * 0.3),
                "animate": rng.random() < (0.5 + energy * 0.4),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
                "turbulence": rng.random() < (0.3 + energy * 0.4),
            }
        elif effect_name == "sdf_shapes":
            params = {
                "shape_count": rng.randint(2, 3 + int(energy * 7)),
                "shape_type": rng.choice(["circle", "box", "ring", "cross"]),
                "radius_min": rng.uniform(0.02, 0.05 + structure * 0.05),
                "radius_max": rng.uniform(0.1, 0.15 + structure * 0.15),
                "smoothness": rng.uniform(0.05, 0.1 + structure * 0.2),
                "animate": rng.random() < (0.5 + energy * 0.4),
                "speed": rng.uniform(0.3, 1.0 + energy * 4.0),
            }
        elif effect_name == "cppn":
            params = {
                "num_hidden": rng.randint(2, 5),
                "layer_size": rng.choice([4, 6, 8, 10, 12]),
                "seed": rng.randint(0, 100000),
            }
        elif effect_name == "ten_print":
            params = {
                "cell_size": rng.randint(4, 8 + int(structure * 4)),
                "probability": rng.uniform(0.3, 0.7),
                "speed": rng.uniform(0.3, 1.0 + energy * 3.0),
            }
        elif effect_name == "game_of_life":
            params = {
                "density": rng.uniform(0.3, 0.5 + energy * 0.2),
                "speed": rng.uniform(2.0, 5.0 + energy * 10.0),
                "wrap": True,
            }
        elif effect_name == "donut":
            params = {
                "R1": self._jitter(
                    rng.uniform(0.15, 0.6 + energy * 0.4), 0.2, 0.1, 3.0),
                "R2": self._jitter(
                    rng.uniform(0.05, 0.3 + structure * 0.3), 0.15, 0.05, 4.0),
                "rotation_speed": rng.uniform(0.3, 1.0 + energy * 2.0),
            }
        elif effect_name == "mod_xor":
            params = {
                "modulus": rng.choice([8, 16, 32, 64]),
                "operation": rng.choice(["xor", "and", "or"]),
                "layers": rng.randint(1, 2 + int(energy)),
                "speed": rng.uniform(0.2, 0.5 + energy * 1.5),
                "zoom": rng.uniform(0.5, 1.5 + structure * 0.5),
            }
        elif effect_name == "wireframe_cube":
            params = {
                "rotation_speed_x": rng.uniform(0.2, 0.5 + energy * 1.0),
                "rotation_speed_y": rng.uniform(0.3, 0.6 + energy * 1.0),
                "rotation_speed_z": rng.uniform(0.1, 0.4 + energy * 0.8),
                "scale": self._jitter(
                    rng.uniform(0.2, 0.5 + structure * 0.2), 0.1, 0.1, 0.8),
                "edge_thickness": rng.uniform(0.01, 0.03 + structure * 0.02),
            }
        elif effect_name == "chroma_spiral":
            params = {
                "arms": rng.randint(1, 4 + int(energy * 4)),
                "tightness": rng.uniform(0.1, 1.0 + structure * 1.0),
                "speed": rng.uniform(0.3, 1.0 + energy * 3.0),
                "chroma_offset": rng.uniform(0.0, 0.1 + energy * 0.2),
            }
        elif effect_name == "wobbly":
            params = {
                "warp_amount": rng.uniform(0.1, 0.4 + energy * 0.6),
                "warp_freq": rng.uniform(0.02, 0.04 + structure * 0.02),
                "iterations": rng.randint(1, 2 + int(energy)),
                "speed": rng.uniform(0.2, 0.5 + energy * 1.5),
            }
        elif effect_name == "sand_game":
            params = {
                "spawn_rate": rng.uniform(0.1, 0.3 + energy * 0.5),
                "gravity_speed": rng.randint(1, 2 + int(energy * 2)),
                "particle_types": rng.randint(1, 2 + int(structure)),
            }
        elif effect_name == "slime_dish":
            params = {
                "agent_count": rng.randint(500, 2000 + int(energy * 3000)),
                "sensor_distance": rng.randint(3, 9 + int(structure * 6)),
                "sensor_angle": rng.uniform(0.2, 0.6 + structure * 0.4),
                "decay_rate": rng.uniform(0.9, 0.95 + (1 - energy) * 0.04),
                "speed": rng.randint(1, 3 + int(energy * 3)),
            }
        elif effect_name == "dyna":
            params = {
                "attractor_count": rng.randint(2, 4 + int(energy * 4)),
                "frequency": rng.uniform(0.1, 0.5 + energy * 1.5),
                "speed": rng.uniform(0.3, 1.0 + energy * 3.0),
                "bounce": rng.random() < 0.7,
            }
        else:
            params = {}

        # Merge variant params (overrides base where specified)
        variant_params = self._sample_variant_params(effect_name)
        params.update(variant_params)

        return params

    def _choose_text_elements(
        self, valence: float, arousal: float, energy: float
    ) -> list[dict[str, Any]]:
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
                pool = [
                    "RISE",
                    "UP",
                    "BULL",
                    "GO",
                    "YES",
                    "MAX",
                    "TOP",
                    "涨",
                    "牛",
                    "冲",
                    "↑",
                    "▲",
                    "━━▶",
                    "╱╲╱",
                    "◉",
                    "█▀█",
                    "⣿",
                ]
            else:
                pool = [
                    "calm",
                    "flow",
                    "ease",
                    "zen",
                    "~",
                    "静",
                    "和",
                    "润",
                    "◎",
                    "○",
                    "╭─╮",
                    "≈≈",
                    "◌",
                    "⠿",
                    "·∙·",
                ]
        elif valence > 0.0:
            pool = [
                "...",
                "---",
                "===",
                "~",
                "○",
                "△",
                "等",
                "观",
                "守",
                "…",
                "─┄─",
                "┈┈┈",
                "╌╌╌",
                "◦◦◦",
            ]
        elif valence > -0.5:
            if arousal > 0.3:
                pool = [
                    "?!",
                    "WARN",
                    "ALERT",
                    "!!",
                    "慌",
                    "急",
                    "!",
                    "⚠",
                    "△",
                    "╳╳╳",
                    "┃┃┃",
                    "▓▓▓",
                    "╋╋╋",
                ]
            else:
                pool = [
                    "...",
                    "fade",
                    "dim",
                    "gray",
                    "淡",
                    "沉",
                    "暗",
                    "—",
                    "┄┄┄",
                    "░░░",
                    "┆┆┆",
                    "⠁⠂⠄",
                ]
        else:
            if arousal > 0.3:
                pool = [
                    "SELL",
                    "DOWN",
                    "BEAR",
                    "RUN",
                    "NO",
                    "STOP",
                    "跌",
                    "崩",
                    "逃",
                    "↓",
                    "▼",
                    "█▄█",
                    "━━╋",
                    "▓█▓",
                    "╬╬╬",
                ]
            else:
                pool = [
                    "...",
                    "___",
                    "void",
                    "null",
                    "空",
                    "无",
                    "寂",
                    "—",
                    "░░░",
                    "┈┈┈",
                    "⠀⠀⠀",
                    "···",
                ]

        elements = []
        for _ in range(count):
            text = self.rng.choice(pool)
            elements.append(
                {
                    "text": text,
                    "position": (
                        self.rng.uniform(0.1, 0.9),
                        self.rng.uniform(0.1, 0.9),
                    ),
                    "size": self.rng.uniform(0.6, 1.5),
                    "opacity": self.rng.uniform(0.3, 0.8),
                }
            )

        return elements

    def _choose_kaomoji_mood(self, valence: float, arousal: float, dominance: float = 0.0) -> str:
        """
        根据 VAD 三维空间最近质心选择颜文字情绪类别

        使用欧氏距离匹配最近情绪锚点，覆盖 20 种情绪。
        """
        centroids = {
            "euphoria":      ( 0.8,  0.8,  0.5),
            "happy":         ( 0.6,  0.0,  0.3),
            "excitement":    ( 0.5,  0.7,  0.4),
            "love":          ( 0.7,  0.2, -0.3),
            "proud":         ( 0.5,  0.3,  0.8),
            "relaxed":       ( 0.4, -0.6,  0.1),
            "angry":         (-0.6,  0.7,  0.7),
            "anxiety":       (-0.4,  0.6, -0.4),
            "fear":          (-0.7,  0.7, -0.7),
            "panic":         (-0.8,  0.9, -0.3),
            "sad":           (-0.5, -0.4, -0.3),
            "lonely":        (-0.6, -0.5, -0.6),
            "disappointed":  (-0.4, -0.3,  0.0),
            "confused":      ( 0.0,  0.3, -0.3),
            "surprised":     ( 0.1,  0.9, -0.2),
            "thinking":      ( 0.0, -0.3,  0.4),
            "embarrassed":   (-0.2,  0.3, -0.6),
            "bored":         (-0.1, -0.7,  0.0),
            "sleepy":        ( 0.1, -0.8, -0.3),
            "neutral":       ( 0.0,  0.0,  0.0),
        }
        best_mood = "neutral"
        best_dist = float("inf")
        for mood, (cv, ca, cd) in centroids.items():
            dist = (valence - cv) ** 2 + (arousal - ca) ** 2 + (dominance - cd) ** 2
            if dist < best_dist:
                best_dist = dist
                best_mood = mood
        return best_mood

    def place_content(self, spec, content, visual_params):
        """
        在场景中放置内容数据 - Place content data in scene

        根据视觉参数和概率规则决定 headline/metrics/timestamp 的放置方式。
        不使用固定模板，位置和大小由文法规则概率决定。

        Args:
            spec: SceneSpec to modify in-place
            content: Content dict from AI
            visual_params: visual parameter dict
        """
        if not content:
            return

        spec.content_headline = content.get("headline")
        spec.content_metrics = content.get("metrics", [])
        spec.content_timestamp = content.get("timestamp")
        spec.content_body = content.get("body")
        # Override from vocabulary if present
        vocab = content.get("vocabulary", {})
        if vocab.get("kaomoji_moods"):
            spec.kaomoji_mood_overrides = list(vocab["kaomoji_moods"])
        if vocab.get("particles"):
            spec.particle_chars = vocab["particles"]

        # Override decoration chars from vocabulary if present
        if vocab.get("decoration_chars"):
            spec.decoration_chars = list(vocab["decoration_chars"])

        # Add content text elements through the grammar system
        energy = visual_params.get("energy", 0.5)
        warmth = visual_params.get("warmth", 0.5)

        # Headline placement (probabilistic position)
        if spec.content_headline:
            headline_positions = [
                (0.5, 0.08),  # top center
                (0.5, 0.92),  # bottom center
                (0.5, 0.5),  # dead center
                (0.15, 0.15),  # top-left area
                (0.85, 0.85),  # bottom-right area
            ]
            pos = self.rng.choice(headline_positions)
            spec.text_elements.append(
                {
                    "text": spec.content_headline,
                    "position": pos,
                    "size": 1.5 + energy * 0.5,
                    "opacity": 0.9,
                    "role": "headline",
                }
            )

        # Metrics placement
        if spec.content_metrics:
            # Choose between clustered and scattered placement
            clustered = self.rng.random() < (
                0.4 + visual_params.get("structure", 0.5) * 0.4
            )

            if clustered:
                # Stack metrics vertically
                base_y = self.rng.uniform(0.3, 0.7)
                base_x = self.rng.uniform(0.15, 0.85)
                for i, metric in enumerate(spec.content_metrics[:4]):
                    spec.text_elements.append(
                        {
                            "text": metric,
                            "position": (base_x, base_y + i * 0.08),
                            "size": 1.0 + energy * 0.3,
                            "opacity": 0.85,
                            "role": "metric",
                        }
                    )
            else:
                # Scatter metrics around canvas
                for metric in spec.content_metrics[:4]:
                    pos = (self.rng.uniform(0.1, 0.9), self.rng.uniform(0.1, 0.9))
                    spec.text_elements.append(
                        {
                            "text": metric,
                            "position": pos,
                            "size": 0.8 + energy * 0.4,
                            "opacity": 0.75,
                            "role": "metric",
                        }
                    )

        # Timestamp placement (always subtle)
        if spec.content_timestamp:
            ts_positions = [
                (0.85, 0.95),  # bottom-right
                (0.15, 0.95),  # bottom-left
                (0.5, 0.97),  # bottom-center
                (0.85, 0.05),  # top-right
            ]
            pos = self.rng.choice(ts_positions)
            spec.text_elements.append(
                {
                    "text": spec.content_timestamp,
                    "position": pos,
                    "size": 0.6,
                    "opacity": 0.5,
                    "role": "timestamp",
                }
            )

        # Source ambient words (from vocabulary)
        if vocab.get("ambient_words"):
            valence = visual_params.get("valence", 0.0)
            if valence > 0.2:
                word_pool = vocab["ambient_words"].get("positive", [])
            elif valence < -0.2:
                word_pool = vocab["ambient_words"].get("negative", [])
            else:
                word_pool = vocab["ambient_words"].get("neutral", [])

            # Add 0-2 ambient words
            ambient_count = self.rng.randint(0, min(2, len(word_pool)))
            for _ in range(ambient_count):
                word = self.rng.choice(word_pool)
                spec.text_elements.append(
                    {
                        "text": word,
                        "position": (
                            self.rng.uniform(0.1, 0.9),
                            self.rng.uniform(0.1, 0.9),
                        ),
                        "size": self.rng.uniform(0.5, 1.0),
                        "opacity": self.rng.uniform(0.3, 0.6),
                        "role": "ambient",
                    }
                )

    # === 域变换 / 后处理 / 合成模式 产生式规则 ===

    def _choose_domain_transforms(
        self, energy: float, structure: float
    ) -> list[dict[str, Any]]:
        """选择域变换 — 自由叠加，从全部 9 种中均匀选取

        变换数量 0-3 随机，每种变换的参数从连续空间生成。
        """
        all_types = ["mirror_x", "mirror_y", "mirror_quad", "kaleidoscope",
                     "tile", "spiral_warp", "rotate", "zoom", "polar_remap"]
        # 变换数量: 0-3
        max_count = self.rng.choices([0, 1, 2, 3], weights=[20, 35, 30, 15])[0]
        self.rng.shuffle(all_types)
        transforms: list[dict[str, Any]] = []
        for t_type in all_types[:max_count]:
            transforms.append(self._generate_transform_params(t_type, energy))
        return transforms

    def _generate_transform_params(self, t_type: str, energy: float) -> dict[str, Any]:
        """为单个域变换生成随机参数"""
        if t_type == "kaleidoscope":
            return {
                "type": "kaleidoscope",
                "segments": self.rng.choice([3, 4, 5, 6, 8, 10, 12]),
            }
        elif t_type == "tile":
            return {
                "type": "tile",
                "cols": self.rng.choice([2, 3, 4]),
                "rows": self.rng.choice([2, 3, 4]),
            }
        elif t_type == "spiral_warp":
            twist_base = self.rng.uniform(0.2, 2.0)
            twist_val: Any = twist_base
            if energy > 0.3 and self.rng.random() < 0.6:
                twist_val = {
                    "base": twist_base, "speed": 0.1 + energy * 0.3,
                    "mode": "linear",
                }
            return {"type": "spiral_warp", "twist": twist_val}
        elif t_type == "rotate":
            angle_base = self.rng.uniform(-1.0, 1.0)
            angle_val: Any = angle_base
            if energy > 0.2 and self.rng.random() < 0.65:
                angle_val = {
                    "base": angle_base, "speed": 0.15 + energy * 0.4,
                    "mode": "linear",
                }
            return {"type": "rotate", "angle": angle_val}
        elif t_type == "zoom":
            factor_base = self.rng.uniform(1.1, 4.0)
            factor_val: Any = factor_base
            if self.rng.random() < 0.5:
                factor_val = {
                    "base": factor_base,
                    "speed": 0.3 + energy * 0.7,
                    "amp": self.rng.uniform(0.2, 0.6),
                    "mode": "oscillate",
                }
            return {"type": "zoom", "factor": factor_val}
        elif t_type == "polar_remap":
            return {"type": "polar_remap"}
        else:
            # mirror_x, mirror_y, mirror_quad
            return {"type": t_type}

    def _choose_postfx_chain(
        self, energy: float, structure: float, intensity: float
    ) -> list[dict[str, Any]]:
        """选择后处理链 — 自由组合，均匀随机选择类型

        链长度 0-3 随机，从全部 7 种 postfx 中均匀选取（不重复）。
        允许空链 — 没有后处理也是一种风格。
        """
        all_types = ["vignette", "scanlines", "threshold", "edge_detect",
                     "invert", "color_shift", "pixelate"]
        # 链长度: 0-3
        max_count = self.rng.choices([0, 1, 2, 3], weights=[15, 35, 30, 20])[0]
        self.rng.shuffle(all_types)
        chain: list[dict[str, Any]] = []
        for fx_type in all_types[:max_count]:
            chain.append(self._generate_postfx_params(fx_type, energy))
        return chain

    def _generate_postfx_params(self, fx_type: str, energy: float) -> dict[str, Any]:
        """为单个 postfx 生成随机参数"""
        if fx_type == "vignette":
            params: dict[str, Any] = {
                "type": "vignette",
                "strength": self.rng.uniform(0.2, 0.8),
            }
            if energy > 0.3 and self.rng.random() < 0.5:
                params["pulse_speed"] = 0.3 + energy * 0.7
                params["pulse_amp"] = self.rng.uniform(0.1, 0.25)
            return params
        elif fx_type == "scanlines":
            params = {
                "type": "scanlines",
                "spacing": self.rng.choice([3, 4, 5, 6]),
                "darkness": self.rng.uniform(0.15, 0.45),
            }
            if energy > 0.25 and self.rng.random() < 0.55:
                params["scroll_speed"] = 0.5 + energy * 2.0
            return params
        elif fx_type == "threshold":
            return {"type": "threshold", "threshold": self.rng.uniform(0.25, 0.75)}
        elif fx_type == "edge_detect":
            return {"type": "edge_detect"}
        elif fx_type == "invert":
            return {"type": "invert"}
        elif fx_type == "color_shift":
            params = {
                "type": "color_shift",
                "hue_shift": self.rng.uniform(0.05, 0.3),
            }
            if energy > 0.3 and self.rng.random() < 0.5:
                params["drift_speed"] = self.rng.uniform(0.02, 0.2)
            return params
        else:  # pixelate
            params = {
                "type": "pixelate",
                "block_size": self.rng.choice([3, 4, 5, 6]),
            }
            if energy > 0.4 and self.rng.random() < 0.4:
                params["pulse_speed"] = 0.3 + energy * 0.5
                params["pulse_amp"] = self.rng.uniform(1.0, 2.0)
            return params

    def _choose_composition_mode(
        self, energy: float, structure: float
    ) -> dict[str, Any]:
        """选择合成模式 — 均匀随机"""
        mode = self.rng.choice(["blend", "masked_split", "radial_masked",
                                "noise_masked", "sdf_masked"])

        result: dict[str, Any] = {"mode": mode}

        # Mask animation speed: driven by energy
        anim_speed = 0.0
        if energy > 0.25 and self.rng.random() < 0.55:
            anim_speed = self.rng.uniform(0.3, 0.8 + energy * 1.2)

        if mode == "masked_split":
            mask_type = self.rng.choice(["horizontal_split", "vertical_split", "diagonal"])
            result["mask_type"] = mask_type
            result["mask_params"] = {
                "mask_split": self.rng.uniform(0.3, 0.7),
                "mask_softness": self.rng.uniform(0.05, 0.25),
                "mask_anim_speed": anim_speed,
            }
            if mask_type == "diagonal":
                result["mask_params"]["mask_angle"] = self.rng.uniform(-0.5, 0.5)

        elif mode == "radial_masked":
            result["mask_type"] = "radial"
            result["mask_params"] = {
                "mask_center_x": self.rng.uniform(0.3, 0.7),
                "mask_center_y": self.rng.uniform(0.3, 0.7),
                "mask_radius": self.rng.uniform(0.2, 0.5),
                "mask_softness": self.rng.uniform(0.1, 0.3),
                "mask_invert": self.rng.random() < 0.3,
                "mask_anim_speed": anim_speed,
            }

        elif mode == "noise_masked":
            result["mask_type"] = "noise"
            result["mask_params"] = {
                "mask_noise_scale": self.rng.uniform(0.03, 0.1),
                "mask_noise_octaves": self.rng.randint(2, 4),
                "mask_threshold": self.rng.uniform(0.3, 0.7),
                "mask_softness": self.rng.uniform(0.1, 0.25),
                "mask_anim_speed": anim_speed,
            }

        elif mode == "sdf_masked":
            sdf_shape = self.rng.choice(["circle", "box", "ring"])
            result["mask_type"] = "sdf"
            sdf_params: dict[str, Any] = {
                "sdf_shape": sdf_shape,
                "sdf_size": self.rng.uniform(0.2, 0.5),
                "mask_softness": self.rng.uniform(0.05, 0.2),
                "mask_anim_speed": anim_speed,
            }
            if sdf_shape == "ring":
                sdf_params["sdf_thickness"] = self.rng.uniform(0.05, 0.15)
            result["mask_params"] = sdf_params

        return result

    # === 背景填充 / 颜色方案 产生式规则 ===

    def _choose_color_scheme(self, warmth: float, energy: float) -> str:
        """选择颜色方案 - Choose color scheme based on warmth"""
        if warmth > 0.7:
            weights = {
                "fire": 0.35, "heat": 0.30, "plasma": 0.20, "rainbow": 0.15,
            }
        elif warmth > 0.3:
            weights = {
                "plasma": 0.28, "rainbow": 0.25, "heat": 0.20,
                "ocean": 0.15, "cool": 0.12,
            }
        else:
            weights = {
                "cool": 0.30, "ocean": 0.28, "matrix": 0.22,
                "plasma": 0.15, "rainbow": 0.05,
            }
        return self._weighted_choice(weights)

    def _choose_bg_fill_spec(
        self, energy: float, structure: float, warmth: float,
        main_effect: str,
    ) -> dict[str, Any]:
        """
        选择背景填充规格 — 均匀随机生成

        各层独立掷骰子，从全部可用空间自由生成。
        """
        rng = self.rng

        # 1. 效果 — 均匀选择 (排除主 effect 和重量级模拟效果)
        bg_pool = ["plasma", "wave", "noise_field", "moire", "mod_xor",
                    "chroma_spiral", "wobbly", "ten_print", "sdf_shapes",
                    "cppn", "flame", "donut", "wireframe_cube"]
        bg_pool = [e for e in bg_pool if e != main_effect]
        bg_effect_name = rng.choice(bg_pool)

        # 2. 效果参数
        effect_params = self._generate_effect_params(bg_effect_name, energy, structure)

        # 3. 变换 (0-2 个，均匀选取)
        all_types = ["mirror_x", "mirror_y", "mirror_quad", "kaleidoscope",
                     "tile", "spiral_warp", "rotate", "zoom", "polar_remap"]
        t_count = rng.choices([0, 1, 2], weights=[30, 40, 30])[0]
        rng.shuffle(all_types)
        transforms: list[dict[str, Any]] = []
        for t_type in all_types[:t_count]:
            transforms.append(self._generate_transform_params(t_type, energy))

        # 4. 后处理 (0-1 个，均匀选取)
        postfx: list[dict[str, Any]] = []
        if rng.random() < 0.45:
            fx_type = rng.choice(["vignette", "color_shift", "scanlines",
                                  "threshold", "invert", "edge_detect", "pixelate"])
            postfx.append(self._generate_postfx_params(fx_type, energy))

        # 5. 蒙版 (0-1 个，均匀选取)
        mask: dict[str, Any] | None = None
        if rng.random() < 0.40:
            mask_type = rng.choice(["radial", "noise", "diagonal",
                                    "horizontal_split", "vertical_split", "sdf"])
            if mask_type == "radial":
                mask = {"type": "radial", "radius": rng.uniform(0.2, 0.7),
                        "softness": rng.uniform(0.1, 0.4)}
            elif mask_type == "noise":
                mask = {"type": "noise", "noise_scale": rng.uniform(0.02, 0.1),
                        "noise_octaves": rng.randint(2, 5),
                        "softness": rng.uniform(0.1, 0.3)}
            elif mask_type == "diagonal":
                mask = {"type": "diagonal", "softness": rng.uniform(0.05, 0.3),
                        "angle": rng.uniform(-1.0, 1.0)}
            elif mask_type in ("horizontal_split", "vertical_split"):
                mask = {"type": mask_type, "split": rng.uniform(0.2, 0.8),
                        "softness": rng.uniform(0.05, 0.3)}
            else:
                sdf_shape = rng.choice(["circle", "box", "ring"])
                mask = {"type": "sdf", "sdf_shape": sdf_shape,
                        "sdf_size": rng.uniform(0.15, 0.6),
                        "softness": rng.uniform(0.05, 0.25)}
                if sdf_shape == "ring":
                    mask["sdf_thickness"] = rng.uniform(0.03, 0.2)

        # 6. dim 系数 — 更宽范围
        dim_val = rng.uniform(0.10, 0.55)

        spec: dict[str, Any] = {
            "effect": bg_effect_name,
            "effect_params": effect_params,
            "transforms": transforms,
            "postfx": postfx,
            "color_mode": "continuous",
            "warmth": warmth,
            "saturation": _clamp(0.4 + rng.uniform(0, 0.6), 0.0, 1.0),
            "dim": _clamp(dim_val, 0.08, 0.55),
        }
        if mask is not None:
            spec["mask"] = mask

        return spec

    # === 工具方法 ===

    def _jitter(
        self, base: float, amount: float,
        lo: float | None = None, hi: float | None = None,
    ) -> float:
        """添加高斯抖动 - Add Gaussian jitter to a base value"""
        offset = self.rng.gauss(0, amount * 0.6)
        result = base + offset
        if lo is not None:
            result = max(lo, result)
        if hi is not None:
            result = min(hi, result)
        return result

    def _sample_variant_params(self, effect_name: str) -> dict[str, Any]:
        """从变体注册表采样参数 - Sample parameters from variant registry"""
        try:
            from procedural.effects.variants import VARIANT_REGISTRY
        except ImportError:
            return {}

        variants = VARIANT_REGISTRY.get(effect_name)
        if not variants:
            return {}

        # Weighted selection
        total = sum(v["weight"] for v in variants)
        r = self.rng.random() * total
        cumulative = 0.0
        selected = variants[0]
        for v in variants:
            cumulative += v["weight"]
            if r <= cumulative:
                selected = v
                break

        # Sample params from ranges
        params: dict[str, Any] = {}
        for key, val in selected["params"].items():
            if isinstance(val, tuple) and len(val) == 2:
                lo, hi = val
                if isinstance(lo, int) and isinstance(hi, int):
                    params[key] = self.rng.randint(lo, hi)
                else:
                    params[key] = self.rng.uniform(float(lo), float(hi))
            else:
                params[key] = val

        return params

    def _weighted_choice(self, weights: dict[str, float]) -> str:
        """加权随机选择 (保留用于内部参数选择) - Weighted choice for internal params"""
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

    def _biased_choice(self, items: list[str], boost: dict[str, float] | None = None) -> str:
        """均匀为主的随机选择，情绪只提供微偏 - Uniform random with slight emotion bias

        base 权重为 1.0，boost 值不超过 ±0.2，使任何选项最多比基准概率高 20%。
        """
        if not boost or not items:
            return self.rng.choice(items)
        weights = [(name, 1.0 + boost.get(name, 0.0)) for name in items]
        total = sum(w for _, w in weights)
        r = self.rng.random() * total
        cumulative = 0.0
        for name, w in weights:
            cumulative += w
            if r <= cumulative:
                return name
        return items[-1]


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))
