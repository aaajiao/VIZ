"""
结构变体注册表 - Structural Variant Registry

每个效果的命名结构变体，提供参数范围预设。
文法系统根据权重选择变体，然后在范围内均匀采样参数。

Named structural variants for effects with parameter range presets.
Grammar selects variants by weight, then samples uniformly within ranges.
"""

__all__ = ["VARIANT_REGISTRY"]

VARIANT_REGISTRY = {
    "donut": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "alien", "weight": 0.2, "params": {
            "surface_noise": (0.3, 0.8),
            "asymmetry_x": (0.5, 1.5),
            "asymmetry_y": (0.5, 1.5),
            "twist": (0.3, 1.5),
        }},
        {"name": "thin_ring", "weight": 0.15, "params": {
            "R1": (0.1, 0.3), "R2": (2.0, 4.0),
        }},
        {"name": "fat_blob", "weight": 0.15, "params": {
            "R1": (1.5, 3.0), "R2": (0.05, 0.5),
            "surface_noise": (0.1, 0.5),
        }},
        {"name": "multi", "weight": 0.15, "params": {
            "count": (2, 3), "ring_offset": (0.2, 0.5),
        }},
        {"name": "twisted", "weight": 0.15, "params": {
            "twist": (0.8, 2.0), "surface_noise": (0.1, 0.4),
        }},
    ],
    "wireframe_cube": [
        {"name": "classic", "weight": 0.25, "params": {}},
        {"name": "irregular", "weight": 0.25, "params": {
            "vertex_noise": (0.1, 0.6),
        }},
        {"name": "morphing", "weight": 0.25, "params": {
            "morph": (0.2, 1.0),
        }},
        {"name": "deformed", "weight": 0.25, "params": {
            "vertex_noise": (0.2, 0.5), "morph": (0.1, 0.5),
            "scale": (0.2, 0.7),
        }},
    ],
    "plasma": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "warped", "weight": 0.2, "params": {
            "self_warp": (0.2, 0.8),
        }},
        {"name": "noisy", "weight": 0.2, "params": {
            "noise_injection": (0.2, 0.7),
        }},
        {"name": "turbulent", "weight": 0.2, "params": {
            "self_warp": (0.1, 0.4), "noise_injection": (0.1, 0.4),
            "frequency": (0.08, 0.2),
        }},
        {"name": "slow_morph", "weight": 0.2, "params": {
            "frequency": (0.01, 0.03), "speed": (0.1, 0.5),
            "noise_injection": (0.3, 0.6),
        }},
    ],
    "wave": [
        {"name": "classic", "weight": 0.25, "params": {}},
        {"name": "warped", "weight": 0.25, "params": {
            "self_warp": (0.2, 0.7),
        }},
        {"name": "chaotic", "weight": 0.25, "params": {
            "noise_injection": (0.3, 0.8),
            "wave_count": (5, 10),
        }},
        {"name": "minimal", "weight": 0.25, "params": {
            "wave_count": (1, 2), "amplitude": (1.5, 3.0),
        }},
    ],
    "moire": [
        {"name": "classic", "weight": 0.25, "params": {}},
        {"name": "distorted", "weight": 0.25, "params": {
            "distortion": (0.2, 0.7),
        }},
        {"name": "multi_center", "weight": 0.25, "params": {
            "multi_center": (2, 3),
        }},
        {"name": "dense", "weight": 0.25, "params": {
            "freq_a": (12.0, 20.0), "freq_b": (12.0, 20.0),
            "distortion": (0.1, 0.3),
        }},
    ],
    "chroma_spiral": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "warped", "weight": 0.2, "params": {
            "distortion": (0.2, 0.6),
        }},
        {"name": "multi", "weight": 0.2, "params": {
            "multi_center": (2, 4),
        }},
        {"name": "tight", "weight": 0.2, "params": {
            "arms": (5, 8), "tightness": (1.0, 2.0),
        }},
        {"name": "loose", "weight": 0.2, "params": {
            "arms": (1, 2), "tightness": (0.1, 0.3),
            "chroma_offset": (0.15, 0.3),
        }},
    ],
    "mod_xor": [
        {"name": "classic", "weight": 0.25, "params": {}},
        {"name": "distorted", "weight": 0.25, "params": {
            "distortion": (0.2, 0.6),
        }},
        {"name": "fine", "weight": 0.25, "params": {
            "modulus": (4, 8), "zoom": (0.5, 0.8),
        }},
        {"name": "layered", "weight": 0.25, "params": {
            "modulus": (16, 64), "layers": (2, 3),
        }},
    ],
}
