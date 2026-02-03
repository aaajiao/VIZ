"""
Box-Drawing & Semigraphic Character Library
制图符号和半图形字符库

参考:
    - Unicode Box Drawing Block (U+2500–U+257F)
    - Unicode Block Elements (U+2580–U+259F)
    - Unicode Geometric Shapes (U+25A0–U+25FF)
    - play.ertdfgcvb.xyz character set philosophy
    - PETSCII / CP437 semigraphics tradition

设计原则:
    1. 按视觉语义分类，而非 Unicode 码位
    2. 每个分类提供 "密度梯度" (从稀疏到密集)
    3. 支持情感驱动的字符选择 (能量/结构/温度)
    4. 所有字符必须在 DejaVuSansMono 中有字形

用法::

    from lib.box_chars import (
        get_charset, get_gradient, get_border_set,
        get_chars_for_mood, CHARSETS,
    )

    # 获取某类字符
    chars = get_charset("box_light")  # "─│┌┐└┘├┤┬┴┼"

    # 获取密度梯度 (空→密)
    gradient = get_gradient("blocks_fine")  # " ░▒▓█"

    # 获取边框字符集
    border = get_border_set("double")
    # → {"h": "═", "v": "║", "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", ...}

    # 情绪驱动选择
    chars = get_chars_for_mood(energy=0.8, structure=0.3, warmth=0.6)
"""

from __future__ import annotations

import random

__all__ = [
    "CHARSETS",
    "GRADIENTS",
    "BORDER_SETS",
    "get_charset",
    "get_gradient",
    "get_border_set",
    "get_chars_for_mood",
    "get_decoration_set",
    "build_box_frame_chars",
]


# ═══════════════════════════════════════════════════════════════
# 1. Character Sets - 字符集分类
# ═══════════════════════════════════════════════════════════════

CHARSETS = {
    # --- Box Drawing: Light ---
    "box_light": "─│┌┐└┘├┤┬┴┼",
    "box_light_h": "─┄┈╌",          # horizontal variants
    "box_light_v": "│┆┊╎",          # vertical variants

    # --- Box Drawing: Heavy ---
    "box_heavy": "━┃┏┓┗┛┣┫┳┻╋",
    "box_heavy_h": "━┅┉╍",
    "box_heavy_v": "┃┇┋╏",

    # --- Box Drawing: Double ---
    "box_double": "═║╔╗╚╝╠╣╦╩╬",

    # --- Box Drawing: Rounded ---
    "box_round": "─│╭╮╰╯├┤┬┴┼",

    # --- Box Drawing: Mixed (light+heavy) ---
    "box_mixed": "┍┑┕┙┝┥┯┷┿╃╄╅╆╇╈╉╊",

    # --- Box Drawing: Dashes ---
    "box_dash_light": "┄┆┈┊",       # light dashes (triple, quadruple)
    "box_dash_heavy": "┅┇┉┋",       # heavy dashes

    # --- Box Drawing: Arc / Diagonal ---
    "box_arc": "╭╮╯╰",              # rounded corners
    "box_diagonal": "╱╲╳",          # diagonal lines

    # --- Block Elements ---
    "blocks_full": "░▒▓█",
    "blocks_half": "▀▄▌▐",          # half blocks
    "blocks_quarter": "▖▗▘▙▚▛▜▝",  # quadrant blocks
    "blocks_shade": "░▒▓",          # shade progression

    # --- Geometric Shapes ---
    "geometric_filled": "■▪▮●▲▼◆",
    "geometric_outline": "□▫▯○△▽◇",
    "geometric_small": "▪▫▸▹►◄▴▵▾▿",
    "geometric_circles": "●○◉◎◦◌◍◐◑",
    "geometric_triangles": "▲△▴▵▶▷▸▹►▻▼▽▾▿◀◁◂◃◄◅",

    # --- Mathematical & Technical ---
    "math_operators": "±×÷∓∞≈≠≤≥≡∝∑∏∫",
    "math_sets": "∈∉∪∩⊂⊃⊆⊇",
    "arrows": "←↑→↓↔↕↖↗↘↙⇐⇑⇒⇓",
    "arrows_thin": "↑↓←→↗↘↙↖",

    # --- Braille Patterns (density gradient) ---
    "braille": "⠀⠁⠂⠃⠄⠅⠆⠇⡀⡁⣀⣁⣂⣃⣄⣅⣆⣇⣈⣉⣊⣋⣌⣍⣎⣏⣿",

    # --- Miscellaneous Symbols ---
    "dots": "·∙•◦○◎◉●",
    "stars": "✦✧★☆✶✴✹✻✼✽",
    "sparkles": "⁺⁎∗✦✧✩✫✬✭✮✯✰",
    "lines_misc": "╱╲╳│─═║┃━",

    # --- Currency / Data ---
    "data": "0123456789ABCDEF",
    "hex_lower": "0123456789abcdef",
    "binary": "01",

    # --- CP437 / Retro ---
    "cp437_box": "┌┐└┘│─├┤┬┴┼═║╔╗╚╝╠╣╦╩╬",
    "cp437_shade": "░▒▓█",
    "cp437_misc": "♠♣♥♦•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼",
}


# ═══════════════════════════════════════════════════════════════
# 2. Density Gradients - 密度梯度
# ═══════════════════════════════════════════════════════════════
# 每个梯度从空/稀疏到密/实，可直接用于 char_at_value 映射

GRADIENTS = {
    # --- Classic ASCII ---
    "classic": " .:-=+*#%@",
    "smooth": " .':;!>+*%@#█",
    "matrix": " .:-=+*@#",
    "plasma": "$?01▄abc+-><:.",

    # --- Block-based ---
    "blocks": " ░▒▓█",
    "blocks_fine": " ·░▒▓█",
    "blocks_ultra": " ·⠁░▒▓▓█",

    # --- Box-drawing density ---
    "box_density": " ·┄─┈━░▒▓█",
    "box_vertical": " ·┆│┊┃░▒▓█",
    "box_cross": " ·+┼╋╬░▒▓█",

    # --- Geometric density ---
    "dots_density": " ·∙•◦○◎◉●█",
    "geometric": " ·▪□▫▮■▓█",

    # --- Braille density ---
    "braille_density": " ⠁⠃⠇⡇⣇⣧⣷⣿",

    # --- Mixed expressive ---
    "tech": " .·:;+*░▒▓█",
    "cyber": " ·-=≡░▒▓█",
    "organic": " ·∙•○◎●▒▓█",
    "noise": " ·⠁⠃░▒▓▓█",
    "circuit": " ·┄─├┼╋▒▓█",
    "glitch": " ·░▒▓█▀▄▌▐",
}


# ═══════════════════════════════════════════════════════════════
# 3. Border Sets - 边框字符集
# ═══════════════════════════════════════════════════════════════

BORDER_SETS = {
    "light": {
        "h": "─", "v": "│",
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "lt": "├", "rt": "┤", "tt": "┬", "bt": "┴",
        "cross": "┼",
    },
    "heavy": {
        "h": "━", "v": "┃",
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "lt": "┣", "rt": "┫", "tt": "┳", "bt": "┻",
        "cross": "╋",
    },
    "double": {
        "h": "═", "v": "║",
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "lt": "╠", "rt": "╣", "tt": "╦", "bt": "╩",
        "cross": "╬",
    },
    "round": {
        "h": "─", "v": "│",
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "lt": "├", "rt": "┤", "tt": "┬", "bt": "┴",
        "cross": "┼",
    },
    "dash_light": {
        "h": "┄", "v": "┆",
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "lt": "├", "rt": "┤", "tt": "┬", "bt": "┴",
        "cross": "┼",
    },
    "dash_heavy": {
        "h": "┅", "v": "┇",
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "lt": "┣", "rt": "┫", "tt": "┳", "bt": "┻",
        "cross": "╋",
    },
}


# ═══════════════════════════════════════════════════════════════
# 4. Mood-Driven Character Palettes - 情绪驱动的字符调色板
# ═══════════════════════════════════════════════════════════════

_MOOD_CHAR_PALETTES = {
    # (energy_range, structure_range, warmth_range) → charset config
    "calm_structured": {
        "gradient": "dots_density",
        "decoration": ["·", "○", "◎", "─", "│"],
        "particles": "·∙•◦○",
        "border": "round",
        "fill": "braille_density",
    },
    "calm_organic": {
        "gradient": "organic",
        "decoration": ["~", "≈", "◦", "○", "·"],
        "particles": "~≈≋·∙",
        "border": "dash_light",
        "fill": "noise",
    },
    "energetic_structured": {
        "gradient": "circuit",
        "decoration": ["╋", "┼", "═", "║", "╬"],
        "particles": "┼╋╬╳+",
        "border": "heavy",
        "fill": "box_cross",
    },
    "energetic_chaotic": {
        "gradient": "glitch",
        "decoration": ["█", "▀", "▄", "▌", "▐"],
        "particles": "░▒▓█▀▄",
        "border": "double",
        "fill": "blocks_ultra",
    },
    "warm_gentle": {
        "gradient": "blocks_fine",
        "decoration": ["◉", "●", "◎", "○", "◦"],
        "particles": "·•○◎◉",
        "border": "round",
        "fill": "dots_density",
    },
    "cold_sharp": {
        "gradient": "cyber",
        "decoration": ["┃", "━", "╋", "╳", "┼"],
        "particles": "─│┼╋╳",
        "border": "heavy",
        "fill": "tech",
    },
    "data_dense": {
        "gradient": "tech",
        "decoration": ["░", "▒", "▓", "█", "┼"],
        "particles": "0123456789ABCDEF",
        "border": "double",
        "fill": "box_density",
    },
    "minimal": {
        "gradient": "blocks",
        "decoration": ["·", "─", "│", "+"],
        "particles": "·∙·.",
        "border": "light",
        "fill": "classic",
    },
}


# ═══════════════════════════════════════════════════════════════
# 5. Public API
# ═══════════════════════════════════════════════════════════════

def get_charset(name: str) -> str:
    """
    获取指定名称的字符集

    Args:
        name: 字符集名称 (见 CHARSETS 键)

    Returns:
        str: 字符集字符串

    Raises:
        KeyError: 如果名称不存在
    """
    return CHARSETS[name]


def get_gradient(name: str) -> str:
    """
    获取指定名称的密度梯度

    Args:
        name: 梯度名称 (见 GRADIENTS 键)

    Returns:
        str: 梯度字符串 (空→密)
    """
    return GRADIENTS.get(name, GRADIENTS["classic"])


def get_border_set(name: str) -> dict[str, str]:
    """
    获取边框字符集

    Args:
        name: 边框风格名称

    Returns:
        dict: 包含 h, v, tl, tr, bl, br, lt, rt, tt, bt, cross 键的字典
    """
    return BORDER_SETS.get(name, BORDER_SETS["light"])


def get_chars_for_mood(
    energy: float = 0.5,
    structure: float = 0.5,
    warmth: float = 0.5,
    rng: random.Random | None = None,
) -> dict:
    """
    根据情绪参数选择字符调色板

    Args:
        energy: 能量 (0=平静, 1=激烈)
        structure: 结构性 (0=有机/混乱, 1=有序/几何)
        warmth: 色温 (0=冷, 1=暖)
        rng: 可选随机数生成器

    Returns:
        dict: 包含 gradient, decoration, particles, border, fill 键
    """
    if rng is None:
        rng = random.Random()

    # 根据三维参数空间匹配最近的调色板
    high_energy = energy > 0.6
    high_structure = structure > 0.5
    warm = warmth > 0.55

    if high_energy:
        if high_structure:
            palette_name = "energetic_structured"
        else:
            palette_name = "energetic_chaotic"
    elif energy < 0.3:
        if high_structure:
            palette_name = "calm_structured"
        else:
            palette_name = "calm_organic"
    else:
        if warm:
            palette_name = "warm_gentle"
        elif warmth < 0.35:
            palette_name = "cold_sharp"
        elif high_structure:
            palette_name = "data_dense"
        else:
            palette_name = "minimal"

    # 偶尔变异到相邻调色板
    all_palettes = list(_MOOD_CHAR_PALETTES.keys())
    if rng.random() < 0.15:
        palette_name = rng.choice(all_palettes)

    return dict(_MOOD_CHAR_PALETTES[palette_name])


def get_decoration_set(
    style: str,
    energy: float = 0.5,
    rng: random.Random | None = None,
) -> list[str]:
    """
    获取装饰字符组合

    根据风格和能量级别返回一组装饰字符。

    Args:
        style: 装饰风格 (corners, edges, frame, scattered, circuit, grid_lines)
        energy: 能量级别
        rng: 可选随机数生成器

    Returns:
        list[str]: 装饰字符列表
    """
    if rng is None:
        rng = random.Random()

    if style == "frame":
        # 边框装饰: 使用完整边框字符
        if energy > 0.6:
            sets = [
                ["╔", "═", "╗", "║", "╚", "═", "╝", "║"],
                ["┏", "━", "┓", "┃", "┗", "━", "┛", "┃"],
                ["╔", "═══", "╗", "║", "╚", "═══", "╝", "║"],
            ]
        else:
            sets = [
                ["┌", "─", "┐", "│", "└", "─", "┘", "│"],
                ["╭", "─", "╮", "│", "╰", "─", "╯", "│"],
                ["┌", "┄", "┐", "┆", "└", "┄", "┘", "┆"],
            ]
        return rng.choice(sets)

    elif style == "circuit":
        # 电路板风格
        return rng.choice([
            ["├", "┤", "┬", "┴", "┼", "─", "│"],
            ["┣", "┫", "┳", "┻", "╋", "━", "┃"],
            ["╠", "╣", "╦", "╩", "╬", "═", "║"],
            ["├─┼", "┤─┼", "┬│┴", "┼─┼"],
        ])

    elif style == "grid_lines":
        # 网格线风格
        return rng.choice([
            ["┼", "─", "│", "┼"],
            ["╋", "━", "┃", "╋"],
            ["╬", "═", "║", "╬"],
            ["┼", "┄", "┆", "┼"],
        ])

    elif style == "corners":
        # 增强的角落装饰
        if energy > 0.7:
            sets = [
                ["╔═", "═╗", "╚═", "═╝"],
                ["┏━", "━┓", "┗━", "━┛"],
                ["╔══", "══╗", "╚══", "══╝"],
                ["▛", "▜", "▙", "▟"],
            ]
        elif energy > 0.4:
            sets = [
                ["┌─", "─┐", "└─", "─┘"],
                ["╭─", "─╮", "╰─", "─╯"],
                ["┌┄", "┄┐", "└┄", "┄┘"],
                ["┌", "┐", "└", "┘"],
            ]
        else:
            sets = [
                ["·", "·", "·", "·"],
                ["╭", "╮", "╰", "╯"],
                ["◦", "◦", "◦", "◦"],
                ["○", "○", "○", "○"],
            ]
        return rng.choice(sets)

    elif style == "scattered":
        # 散布装饰
        if energy > 0.6:
            return rng.choice([
                ["╳", "╋", "┼", "╬", "━", "┃"],
                ["▪", "▫", "■", "□", "▮", "▯"],
                ["░", "▒", "▓", "█", "▀", "▄"],
                ["◆", "◇", "◉", "◎", "●", "○"],
            ])
        else:
            return rng.choice([
                ["·", "∙", "•", "◦", "○"],
                ["─", "│", "·", "┄", "┆"],
                ["╱", "╲", "╳", "·", "·"],
                ["⠁", "⠃", "⠇", "·", "·"],
            ])

    else:  # edges, minimal, etc.
        return rng.choice([
            ["─", "─", "│", "│"],
            ["━", "━", "┃", "┃"],
            ["═", "═", "║", "║"],
            ["·", "·", "·", "·"],
        ])


def build_box_frame_chars(
    width: int,
    height: int,
    border_style: str = "light",
) -> list[tuple[int, int, str]]:
    """
    生成矩形边框的字符坐标列表

    用于在指定区域绘制一个完整的 box-drawing 边框。
    返回 (x, y, char) 元组列表，可直接传递给精灵系统。

    Args:
        width: 边框宽度 (字符数)
        height: 边框高度 (字符数)
        border_style: 边框风格名称

    Returns:
        list[tuple[int, int, str]]: (x, y, char) 坐标字符列表
    """
    bs = get_border_set(border_style)
    chars = []

    # 四个角
    chars.append((0, 0, bs["tl"]))
    chars.append((width - 1, 0, bs["tr"]))
    chars.append((0, height - 1, bs["bl"]))
    chars.append((width - 1, height - 1, bs["br"]))

    # 水平边
    for x in range(1, width - 1):
        chars.append((x, 0, bs["h"]))
        chars.append((x, height - 1, bs["h"]))

    # 垂直边
    for y in range(1, height - 1):
        chars.append((0, y, bs["v"]))
        chars.append((width - 1, y, bs["v"]))

    return chars
