"""
参数化框架 - Parameterization Framework

提供可复现的参数生成和随机数管理。

核心功能::

    ParamSpec      - 参数规格 (名称、范围、分布)
    resolve_params - 从规格列表生成参数字典
    create_rng     - 创建可复现的随机数生成器

用法示例::

    from procedural.params import ParamSpec, resolve_params, create_rng

    # 定义参数规格
    specs = [
        ParamSpec('speed', min_val=0.5, max_val=2.0, distribution='uniform'),
        ParamSpec('intensity', min_val=0.1, max_val=1.0, distribution='log'),
        ParamSpec('noise_scale', min_val=0.01, max_val=0.1, distribution='normal'),
    ]

    # 生成参数 (可复现)
    params = resolve_params(specs, seed=42)
    # → {'speed': 1.23, 'intensity': 0.45, 'noise_scale': 0.067}

    # 创建可复现的 RNG
    rng = create_rng(42)
    value = rng.random()  # 始终相同 (给定相同种子)
"""

from dataclasses import dataclass
import random
import math

__all__ = [
    "ParamSpec",
    "resolve_params",
    "create_rng",
    "generate_random_params",
]


@dataclass
class ParamSpec:
    """
    参数规格 - Parameter Specification

    定义单个参数的名称、范围和分布类型。
    用于自动生成可复现的参数值。

    属性:
        name: 参数名称 (如 'speed', 'intensity')
        min_val: 最小值
        max_val: 最大值
        distribution: 分布类型 ('uniform' | 'log' | 'normal')

    分布类型说明:
        - 'uniform': 均匀分布 (线性，所有值概率相等)
        - 'log': 对数分布 (适合跨数量级的参数，如 0.01 到 10.0)
        - 'normal': 正态分布 (中心值概率高，边缘值概率低)

    示例::

        # 线性速度参数 (0.5 到 2.0)
        speed_spec = ParamSpec('speed', min_val=0.5, max_val=2.0, distribution='uniform')

        # 对数尺度参数 (0.001 到 1.0，适合噪声频率)
        scale_spec = ParamSpec('scale', min_val=0.001, max_val=1.0, distribution='log')

        # 正态分布参数 (0.0 到 1.0，中心值 0.5 概率最高)
        intensity_spec = ParamSpec('intensity', min_val=0.0, max_val=1.0, distribution='normal')
    """

    name: str
    min_val: float
    max_val: float
    distribution: str = "uniform"  # 'uniform' | 'log' | 'normal'

    def __post_init__(self):
        """验证参数规格"""
        if self.min_val >= self.max_val:
            raise ValueError(
                f"ParamSpec '{self.name}': min_val ({self.min_val}) must be < max_val ({self.max_val})"
            )

        if self.distribution not in ("uniform", "log", "normal"):
            raise ValueError(
                f"ParamSpec '{self.name}': distribution must be 'uniform', 'log', or 'normal', got '{self.distribution}'"
            )

        if self.distribution == "log" and self.min_val <= 0:
            raise ValueError(
                f"ParamSpec '{self.name}': log distribution requires min_val > 0, got {self.min_val}"
            )


def resolve_params(specs: list[ParamSpec], seed: int) -> dict:
    """
    从参数规格列表生成参数字典 - Resolve Parameters from Specs

    根据每个 ParamSpec 的分布类型，使用给定种子生成可复现的参数值。

    参数:
        specs: ParamSpec 列表
        seed: 随机种子 (相同种子 → 相同参数)

    返回:
        参数字典 {name: value}

    示例::

        specs = [
            ParamSpec('speed', 0.5, 2.0, 'uniform'),
            ParamSpec('scale', 0.01, 0.1, 'log'),
            ParamSpec('intensity', 0.0, 1.0, 'normal'),
        ]

        params = resolve_params(specs, seed=42)
        # → {'speed': 1.234, 'scale': 0.0456, 'intensity': 0.678}

        # 相同种子 → 相同结果
        params2 = resolve_params(specs, seed=42)
        assert params == params2
    """
    rng = random.Random(seed)
    params = {}

    for spec in specs:
        if spec.distribution == "uniform":
            # 均匀分布: 线性插值
            value = rng.uniform(spec.min_val, spec.max_val)

        elif spec.distribution == "log":
            # 对数分布: 在 log 空间均匀采样
            log_min = math.log(spec.min_val)
            log_max = math.log(spec.max_val)
            log_value = rng.uniform(log_min, log_max)
            value = math.exp(log_value)

        elif spec.distribution == "normal":
            # 正态分布: 中心值为均值，范围的 1/6 为标准差
            mean = (spec.min_val + spec.max_val) / 2.0
            stddev = (spec.max_val - spec.min_val) / 6.0

            # 生成正态分布值，裁剪到范围内
            value = rng.gauss(mean, stddev)
            value = max(spec.min_val, min(spec.max_val, value))

        else:
            # 不应到达 (已在 __post_init__ 验证)
            raise ValueError(f"Unknown distribution: {spec.distribution}")

        params[spec.name] = value

    return params


def create_rng(seed: int) -> random.Random:
    """
    创建可复现的随机数生成器 - Create Reproducible RNG

    返回一个独立的 random.Random 实例，不影响全局随机状态。
    相同种子 → 相同随机序列。

    参数:
        seed: 随机种子 (整数)

    返回:
        random.Random 实例

    示例::

        # 创建两个独立的 RNG
        rng1 = create_rng(42)
        rng2 = create_rng(42)

        # 相同种子 → 相同序列
        assert rng1.random() == rng2.random()
        assert rng1.randint(0, 100) == rng2.randint(0, 100)

        # 不同种子 → 不同序列
        rng3 = create_rng(123)
        assert rng1.random() != rng3.random()

    用法 (在 Effect 中)::

        class MyEffect:
            def pre(self, ctx: Context, buffer: Buffer) -> dict:
                # 使用 ctx.rng 进行可复现的随机操作
                offset_x = ctx.rng.uniform(-10, 10)
                offset_y = ctx.rng.uniform(-10, 10)
                return {'offset_x': offset_x, 'offset_y': offset_y}
    """
    return random.Random(seed)


# --- 辅助函数 (内部使用) ---


def _clamp(value: float, min_val: float, max_val: float) -> float:
    """限制值在范围内"""
    return max(min_val, min(max_val, value))


def _validate_seed(seed: int) -> None:
    """验证种子值"""
    if not isinstance(seed, int):
        raise TypeError(f"Seed must be int, got {type(seed).__name__}")
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")


def generate_random_params(effect_name: str, rng: random.Random) -> dict:
    """
    为指定效果生成随机参数 - Generate Random Parameters for Effect

    根据效果名称和随机数生成器，生成该效果的随机参数字典。
    参数范围基于效果的设计特性，确保生成的参数在合理范围内。

    参数:
        effect_name: 效果名称 ('plasma', 'wave', 'flame', 'moire', 'noise_field', 'sdf_shapes')
        rng: random.Random 实例 (用于可复现性)

    返回:
        参数字典 {param_name: value}

    示例::

        import random
        from procedural.params import generate_random_params

        # 使用固定种子生成可复现的参数
        rng = random.Random(42)
        params = generate_random_params('plasma', rng)
        # → {'frequency': 0.087, 'speed': 2.34, 'color_phase': 0.56}

        # 不同种子 → 不同参数
        rng2 = random.Random(99)
        params2 = generate_random_params('plasma', rng2)
        # → {'frequency': 0.042, 'speed': 1.23, 'color_phase': 0.89}
    """
    if effect_name == "plasma":
        return {
            "frequency": rng.uniform(0.01, 0.2),
            "speed": rng.uniform(0.1, 5.0),
            "color_phase": rng.uniform(0.0, 1.0),
        }

    elif effect_name == "wave":
        return {
            "wave_count": rng.randint(1, 10),
            "frequency": rng.uniform(0.01, 0.2),
            "amplitude": rng.uniform(0.5, 3.0),
            "speed": rng.uniform(0.1, 5.0),
            "color_scheme": rng.choice(["ocean", "heat", "cool", "matrix", "rainbow"]),
        }

    elif effect_name == "flame":
        return {
            "intensity": rng.uniform(0.5, 3.0),
        }

    elif effect_name == "moire":
        return {
            "freq_a": rng.uniform(1.0, 20.0),
            "freq_b": rng.uniform(1.0, 20.0),
            "speed_a": rng.uniform(-5.0, 5.0),
            "speed_b": rng.uniform(-5.0, 5.0),
            "offset_a": rng.uniform(-0.5, 0.5),
            "offset_b": rng.uniform(-0.5, 0.5),
            "color_scheme": rng.choice(["rainbow", "heat", "cool", "matrix"]),
        }

    elif effect_name == "noise_field":
        return {
            "scale": rng.uniform(0.01, 0.2),
            "octaves": rng.randint(1, 8),
            "lacunarity": rng.uniform(1.5, 3.0),
            "gain": rng.uniform(0.3, 0.8),
            "animate": rng.choice([True, False]),
            "speed": rng.uniform(0.1, 5.0),
            "turbulence": rng.choice([True, False]),
        }

    elif effect_name == "sdf_shapes":
        return {
            "shape_count": rng.randint(1, 10),
            "shape_type": rng.choice(["circle", "box"]),
            "radius_min": rng.uniform(0.02, 0.1),
            "radius_max": rng.uniform(0.1, 0.3),
            "smoothness": rng.uniform(0.05, 0.3),
            "animate": rng.choice([True, False]),
            "speed": rng.uniform(0.1, 5.0),
        }

    else:
        raise ValueError(
            f"Unknown effect: {effect_name}. "
            f"Supported effects: plasma, wave, flame, moire, noise_field, sdf_shapes"
        )
