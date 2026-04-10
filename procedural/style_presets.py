"""
风格预设系统 - Style Presets

emotion-only 和 Director Mode 之间的中间层。
每个 style 映射到一组策划好的 Director Mode 组合。
"""

import random

STYLE_PRESETS = {
    "geometric": {
        "effects": ["sdf_shapes", "wireframe_cube", "mod_xor", "ten_print"],
        "transforms": [
            [{"type": "mirror_quad"}],
            [{"type": "kaleidoscope", "segments": 6}],
            [{"type": "kaleidoscope", "segments": 8}],
            [{"type": "mirror_x"}],
        ],
        "postfx": [
            [{"type": "edge_detect"}],
            [{"type": "threshold", "threshold": 0.5}],
            [{"type": "vignette", "strength": 0.4}],
        ],
        "gradients": ["box_density", "geometric", "squares", "box_cross", "circuit"],
    },
    "organic": {
        "effects": ["noise_field", "wobbly", "slime_dish", "wave"],
        "transforms": [
            [{"type": "spiral_warp", "twist": 0.5}],
            [{"type": "spiral_warp", "twist": 0.8}],
            [],
        ],
        "postfx": [
            [{"type": "vignette", "strength": 0.5}],
            [{"type": "color_shift", "hue_shift": 0.1}],
            [],
        ],
        "gradients": ["organic", "circles", "braille_density", "dots_density", "smooth"],
    },
    "retro": {
        "effects": ["ten_print", "mod_xor", "game_of_life", "plasma"],
        "transforms": [
            [{"type": "tile", "cols": 2, "rows": 2}],
            [{"type": "tile", "cols": 3, "rows": 3}],
            [],
        ],
        "postfx": [
            [{"type": "scanlines", "spacing": 4, "darkness": 0.3}],
            [{"type": "scanlines", "spacing": 3, "darkness": 0.4}, {"type": "vignette", "strength": 0.3}],
            [{"type": "pixelate", "block_size": 4}],
        ],
        "gradients": ["cp437_retro", "classic", "blocks", "blocks_fine", "digits"],
    },
    "psychedelic": {
        "effects": ["chroma_spiral", "moire", "plasma", "cppn"],
        "transforms": [
            [{"type": "kaleidoscope", "segments": 8}],
            [{"type": "kaleidoscope", "segments": 12}],
            [{"type": "polar_remap"}],
            [{"type": "spiral_warp", "twist": 1.5}],
        ],
        "postfx": [
            [{"type": "color_shift", "hue_shift": 0.2}],
            [{"type": "color_shift", "hue_shift": 0.15}, {"type": "vignette", "strength": 0.3}],
            [{"type": "invert"}],
        ],
        "gradients": ["sparkles", "glitch", "cyber", "noise", "tech"],
    },
    "minimal": {
        "effects": ["noise_field", "wave", "sdf_shapes", "plasma"],
        "transforms": [
            [],
            [],
            [{"type": "mirror_x"}],
        ],
        "postfx": [
            [{"type": "threshold", "threshold": 0.5}],
            [],
            [{"type": "vignette", "strength": 0.3}],
        ],
        "gradients": ["dots_density", "smooth", "box_thin", "classic", "default"],
    },
    "brutal": {
        "effects": ["flame", "plasma", "dyna", "mod_xor"],
        "transforms": [
            [{"type": "mirror_x"}],
            [{"type": "mirror_y"}],
            [{"type": "zoom", "factor": 2.0}],
        ],
        "postfx": [
            [{"type": "scanlines", "spacing": 3, "darkness": 0.4}, {"type": "threshold", "threshold": 0.45}],
            [{"type": "threshold", "threshold": 0.5}],
            [{"type": "edge_detect"}, {"type": "invert"}],
        ],
        "gradients": ["blocks_ultra", "blocks", "tech", "box_thick", "box_heavy"],
    },
    "ethereal": {
        "effects": ["wobbly", "wave", "sand_game", "noise_field"],
        "transforms": [
            [{"type": "spiral_warp", "twist": 0.3}],
            [{"type": "rotate", "angle": 0.2}],
            [],
        ],
        "postfx": [
            [{"type": "vignette", "strength": 0.5}, {"type": "color_shift", "hue_shift": 0.08}],
            [{"type": "color_shift", "hue_shift": 0.12}],
            [],
        ],
        "gradients": ["circles_arc", "organic", "smooth", "sparkles", "stars_density"],
    },
    "glitch": {
        "effects": ["cppn", "mod_xor", "plasma", "moire"],
        "transforms": [
            [{"type": "tile", "cols": 3, "rows": 3}, {"type": "mirror_quad"}],
            [{"type": "mirror_quad"}, {"type": "zoom", "factor": 1.5}],
            [{"type": "tile", "cols": 2, "rows": 2}],
        ],
        "postfx": [
            [{"type": "pixelate", "block_size": 5}, {"type": "invert"}],
            [{"type": "pixelate", "block_size": 3}, {"type": "scanlines", "spacing": 4, "darkness": 0.3}],
            [{"type": "invert"}, {"type": "edge_detect"}],
        ],
        "gradients": ["glitch", "cyber", "noise", "cp437_retro", "tech"],
    },
}

VALID_STYLES = sorted(STYLE_PRESETS.keys())


def resolve_style(style_name, seed, existing_overrides=None):
    """解析风格预设为 Director Mode 覆盖 - Resolve style preset to overrides

    从风格预设的各池中用 seed 随机选取，不覆盖已有的显式 overrides。

    Args:
        style_name: 风格名称
        seed: 随机种子
        existing_overrides: 已有的显式覆盖 (不被 style 覆盖)

    Returns:
        dict: Director Mode 覆盖字典
    """
    if style_name not in STYLE_PRESETS:
        return {}

    preset = STYLE_PRESETS[style_name]
    rng = random.Random(seed ^ 0x5771E)
    overrides = {}

    if existing_overrides is None:
        existing_overrides = {}

    # Effect
    if "effect" not in existing_overrides:
        overrides["effect"] = rng.choice(preset["effects"])

    # Transforms
    if "domain_transforms" not in existing_overrides:
        transforms = rng.choice(preset["transforms"])
        if transforms:
            overrides["domain_transforms"] = transforms

    # PostFX
    if "postfx_chain" not in existing_overrides:
        postfx = rng.choice(preset["postfx"])
        if postfx:
            overrides["postfx_chain"] = postfx

    # Gradient
    if "gradient" not in existing_overrides:
        overrides["gradient"] = rng.choice(preset["gradients"])

    return overrides
