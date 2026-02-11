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
    "flame": [
        {"name": "classic", "weight": 0.25, "params": {}},
        {"name": "intense", "weight": 0.25, "params": {
            "intensity": (2.0, 3.0),
        }},
        {"name": "faint", "weight": 0.25, "params": {
            "intensity": (0.3, 0.6),
        }},
        {"name": "turbulent", "weight": 0.25, "params": {
            "intensity": (1.5, 2.5),
        }},
    ],
    "noise_field": [
        {"name": "classic", "weight": 0.17, "params": {}},
        {"name": "dense", "weight": 0.17, "params": {
            "scale": (0.02, 0.04), "octaves": (6, 8),
        }},
        {"name": "coarse", "weight": 0.17, "params": {
            "scale": (0.1, 0.2), "octaves": (1, 2),
        }},
        {"name": "turbulent", "weight": 0.17, "params": {
            "turbulence": True, "octaves": (4, 6), "speed": (0.3, 0.7),
        }},
        {"name": "smooth_flow", "weight": 0.16, "params": {
            "lacunarity": (1.5, 1.8), "gain": (0.6, 0.8), "speed": (1.0, 3.0),
        }},
        {"name": "sharp", "weight": 0.16, "params": {
            "lacunarity": (2.5, 3.0), "gain": (0.3, 0.4), "octaves": (5, 7),
        }},
    ],
    "ten_print": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "compact", "weight": 0.2, "params": {
            "cell_size": (4, 5),
        }},
        {"name": "spacious", "weight": 0.2, "params": {
            "cell_size": (10, 12),
        }},
        {"name": "biased", "weight": 0.2, "params": {
            "probability": (0.65, 0.80),
        }},
        {"name": "dynamic", "weight": 0.2, "params": {
            "speed": (2.0, 4.0), "cell_size": (7, 9),
        }},
    ],
    "wobbly": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "gentle", "weight": 0.2, "params": {
            "warp_amount": (0.1, 0.2), "iterations": 1,
        }},
        {"name": "violent", "weight": 0.2, "params": {
            "warp_amount": (0.7, 1.0), "iterations": 3,
        }},
        {"name": "fine_ripple", "weight": 0.2, "params": {
            "warp_freq": (0.08, 0.15), "warp_amount": (0.3, 0.5),
        }},
        {"name": "coarse_warp", "weight": 0.2, "params": {
            "warp_freq": (0.01, 0.02), "warp_amount": (0.5, 0.8),
        }},
    ],
    "sdf_shapes": [
        {"name": "classic", "weight": 0.17, "params": {}},
        {"name": "single", "weight": 0.17, "params": {
            "shape_count": 1, "radius_max": (0.2, 0.3),
        }},
        {"name": "swarm", "weight": 0.17, "params": {
            "shape_count": (8, 10), "radius_min": (0.02, 0.05),
        }},
        {"name": "boxes", "weight": 0.17, "params": {
            "shape_type": "box", "shape_count": (3, 5), "smoothness": (0.08, 0.15),
        }},
        {"name": "sharp", "weight": 0.16, "params": {
            "smoothness": (0.02, 0.06), "shape_count": (4, 7),
        }},
        {"name": "fuzzy", "weight": 0.16, "params": {
            "smoothness": (0.2, 0.3), "shape_count": (5, 8),
        }},
    ],
    "game_of_life": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "sparse", "weight": 0.2, "params": {
            "density": (0.2, 0.35),
        }},
        {"name": "dense", "weight": 0.2, "params": {
            "density": (0.55, 0.7),
        }},
        {"name": "fast_evolution", "weight": 0.2, "params": {
            "speed": (8.0, 15.0),
        }},
        {"name": "bounded", "weight": 0.2, "params": {
            "wrap": False, "density": (0.4, 0.5),
        }},
    ],
    "sand_game": [
        {"name": "classic", "weight": 0.2, "params": {}},
        {"name": "rain", "weight": 0.2, "params": {
            "spawn_rate": (0.6, 0.8), "gravity_speed": (3, 4),
        }},
        {"name": "drizzle", "weight": 0.2, "params": {
            "spawn_rate": (0.05, 0.15), "gravity_speed": 1,
        }},
        {"name": "avalanche", "weight": 0.2, "params": {
            "spawn_rate": (0.3, 0.5), "gravity_speed": (4, 5),
        }},
        {"name": "rainbow", "weight": 0.2, "params": {
            "particle_types": 3, "spawn_rate": (0.2, 0.4),
        }},
    ],
    "slime_dish": [
        {"name": "classic", "weight": 0.17, "params": {}},
        {"name": "sparse", "weight": 0.17, "params": {
            "agent_count": (500, 1000), "decay_rate": (0.92, 0.95),
        }},
        {"name": "dense", "weight": 0.17, "params": {
            "agent_count": (3500, 5000), "decay_rate": (0.96, 0.99),
        }},
        {"name": "explorer", "weight": 0.17, "params": {
            "sensor_angle": (0.8, 1.0), "sensor_distance": (12, 15),
        }},
        {"name": "focused", "weight": 0.16, "params": {
            "sensor_angle": (0.2, 0.35), "sensor_distance": (3, 6),
        }},
        {"name": "persistent", "weight": 0.16, "params": {
            "decay_rate": (0.97, 0.99), "agent_count": (2000, 3000),
        }},
    ],
    "dyna": [
        {"name": "classic", "weight": 0.17, "params": {}},
        {"name": "single", "weight": 0.17, "params": {
            "attractor_count": 1, "frequency": (0.5, 0.8),
        }},
        {"name": "many", "weight": 0.17, "params": {
            "attractor_count": (6, 8), "frequency": (0.3, 0.6),
        }},
        {"name": "long_waves", "weight": 0.17, "params": {
            "frequency": (0.08, 0.15), "attractor_count": (3, 4),
        }},
        {"name": "short_ripples", "weight": 0.16, "params": {
            "frequency": (1.5, 2.0), "attractor_count": (4, 6),
        }},
        {"name": "chaotic", "weight": 0.16, "params": {
            "speed": (0.3, 0.6), "frequency": (1.2, 1.8), "bounce": False,
        }},
    ],
    "cppn": [
        {"name": "classic", "weight": 0.17, "params": {}},
        {"name": "delicate", "weight": 0.17, "params": {
            "num_hidden": 2, "layer_size": 4,
        }},
        {"name": "intricate", "weight": 0.17, "params": {
            "num_hidden": 4, "layer_size": 12,
        }},
        {"name": "radiant", "weight": 0.17, "params": {
            "num_hidden": 3, "use_radial": True, "use_time": False,
        }},
        {"name": "chaotic", "weight": 0.16, "params": {
            "num_hidden": 5, "layer_size": 16, "use_radial": False,
            "color_mode": "rgb",
        }},
        {"name": "linear", "weight": 0.16, "params": {
            "num_hidden": 2, "layer_size": 6, "use_radial": False,
        }},
    ],
}
