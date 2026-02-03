"""
Doom Flame 火焰效果 - Doom Flame Effect

实现经典 Doom 风格的火焰效果，通过热量传播和随机衰减产生动态火焰。

原理:
    1. 底部生成热量 (使用 ValueNoise)
    2. 热量向上传播 (带随机水平偏移)
    3. 随机衰减 (产生火焰的不规则边缘)
    4. 映射到字符密度和热力颜色

算法:
    # 底部生成
    heat = noise(x * 0.05, t) * 40 + random() * 10

    # 向上传播
    src_x = x + random.randint(-1, 1)
    src_heat = heat_map[src_x, y+1]
    heat_map[x, y] = max(0, src_heat - random()*2)

    # 映射到颜色
    黑 → 深红 → 红 → 橙 → 黄 → 白

参考:
    - play.core/src/programs/demos/doom_flame.js
    - viz/poc_playcore.py:260-343

用法::

    from procedural.effects import get_effect

    flame = get_effect('flame')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'intensity': 1.0}
    )

    state = flame.pre(ctx, buffer)
    cell = flame.main(80, 80, ctx, state)
"""

import math
from procedural.types import Context, Cell, Buffer
from procedural.core.noise import ValueNoise
from procedural.core.mathx import clamp, map_range
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["DoomFlameEffect"]


class DoomFlameEffect(BaseEffect):
    """
    Doom 风格火焰效果

    通过热量传播和随机衰减产生动态火焰。

    参数 (从 ctx.params 读取):
        intensity: 火焰强度 (默认 1.0, 范围 0.5-3.0)
        seed: 随机种子 (默认从 ctx.seed 读取)

    参数范围说明:
        - intensity: 0.5 (弱火焰) 到 3.0 (强烈火焰)

    示例::

        ctx.params = {
            'intensity': 1.2,  # 更强的火焰
        }
    """

    # 密度字符梯度 (从稀疏到密集)
    DENSITY = "  ..::░░▒▒▓▓██"

    def __init__(self):
        """
        初始化火焰效果

        注意: 不预先指定尺寸，在 pre() 中动态初始化
        """
        self.heat_map = None
        self.width = 0
        self.height = 0
        self.noise = None

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理 - 更新热量图状态

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典，包含:
                - intensity: 火焰强度
                - heat_map: 热量图 (list[float])
        """
        # 检测尺寸变化，初始化 heat_map
        if (
            self.heat_map is None
            or self.width != ctx.width
            or self.height != ctx.height
        ):
            self.width = ctx.width
            self.height = ctx.height
            self.heat_map = [0.0] * (self.width * self.height)
            self.noise = ValueNoise(seed=ctx.seed)

        # 提取参数
        intensity = ctx.params.get("intensity", 1.0)
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        # === 底部生成热量 ===
        last_row = self.width * (self.height - 1)
        t = ctx.time * 0.5  # 时间缩放

        for x in range(self.width):
            # 使用 ValueNoise 生成平滑的热量分布
            noise_val = self.noise(x * 0.05, t)
            heat = noise_val * 40 * intensity + ctx.rng.random() * 10 * intensity
            self.heat_map[last_row + x] = min(50, heat)

        # === 向上传播 + 随机衰减 ===
        for y in range(self.height - 2, -1, -1):
            for x in range(self.width):
                # 从下方取样 (带随机水平偏移)
                src_x = clamp(x + ctx.rng.randint(-1, 1), 0, self.width - 1)
                src_y = y + 1

                src_heat = self.heat_map[src_x + src_y * self.width]
                decay = ctx.rng.random() * 2 + 0.5

                self.heat_map[x + y * self.width] = max(0, src_heat - decay)

        return {
            "intensity": intensity,
            "heat_map": self.heat_map,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染 - 为每个像素生成火焰 Cell

        算法:
            1. 从 heat_map 读取热量值
            2. 映射到字符索引 (密度字符)
            3. 映射到颜色 (热力图)

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell (字符索引 + 颜色)
        """
        # 提取状态
        heat_map = state["heat_map"]

        # 读取热量值
        index = x + y * ctx.width
        heat = heat_map[index]

        # 低热量 → 空白
        if heat < 1:
            return Cell(char_idx=0, fg=(0, 0, 0), bg=None)

        # === 映射到字符索引 ===
        # 统一使用 0-9 范围 (与渲染器 char_idx/9.0 归一化兼容)
        char_idx = int(map_range(heat, 0, 50, 0, 9))
        char_idx = int(clamp(char_idx, 0, 9))

        # === 映射到颜色 ===
        heat_norm = clamp(heat / 50, 0.0, 1.0)
        if state.get("warmth") is not None:
            color = value_to_color_continuous(
                heat_norm,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(heat_norm, "heat")

        return Cell(
            char_idx=char_idx,
            fg=color,
            bg=None,
        )

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理 - Flame 不需要后处理

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass  # Flame 效果不需要后处理
