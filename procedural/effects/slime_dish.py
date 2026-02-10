"""
黏菌模拟 - Physarum Slime Mold Simulation

基于代理的黏菌（多头绒泡菌）模拟。
每个代理沿朝向移动，感知前方的化学轨迹浓度并转向信号最强方向，
同时在路径上沉积化学物质。轨迹地图每帧扩散并衰减。

算法:
    1. N 个代理各有位置 (x, y) 和朝向角度
    2. 每步每个代理:
       a. 感知: 在前方三个方向（前、左前、右前）采样轨迹地图
       b. 转向: 向信号最强方向旋转
       c. 移动: 沿朝向前进一步
       d. 沉积: 在新位置增加轨迹浓度
    3. 轨迹地图: 扩散（简单均值模糊）+ 衰减

用法/Usage::

    from procedural.effects import get_effect

    slime = get_effect('slime_dish')
    ctx = Context(
        width=160, height=160, time=1.5, frame=90,
        seed=42, rng=random.Random(42),
        params={'agent_count': 2000, 'sensor_distance': 9,
                'sensor_angle': 0.4, 'decay_rate': 0.95, 'speed': 3}
    )

    state = slime.pre(ctx, buffer)
    cell = slime.main(80, 80, ctx, state)
"""

import math
from typing import Any

from procedural.types import Context, Cell, Buffer
from procedural.core.mathx import clamp
from procedural.palette import value_to_color, value_to_color_continuous
from .base import BaseEffect

__all__ = ["SlimeDishEffect"]


class SlimeDishEffect(BaseEffect):
    """
    黏菌模拟效果 - Physarum Slime Mold Effect

    基于代理的化学轨迹模拟，产生有机分支网络图案。

    参数 (从 ctx.params 读取):
        agent_count: 代理数量 (默认 2000, 范围 500-5000)
        sensor_distance: 感知距离 (默认 9, 范围 3-15)
        sensor_angle: 感知器张角弧度 (默认 0.4, 范围 0.2-1.0)
        decay_rate: 轨迹衰减率 (默认 0.95, 范围 0.9-0.99)
        speed: 每帧模拟步数 (默认 3)
    """

    def __init__(self):
        self._trail_map = None
        self._agents = None
        self._initialized = False

    def _init_state(self, ctx: Context) -> None:
        """初始化轨迹地图和代理 - Initialize trail map and agents"""
        w, h = ctx.width, ctx.height
        agent_count = ctx.params.get("agent_count", 2000)
        rng = ctx.rng

        # Empty trail map
        self._trail_map = [[0.0] * w for _ in range(h)]

        # Spawn agents at random positions with random headings
        self._agents = []
        for _ in range(agent_count):
            ax = rng.random() * w
            ay = rng.random() * h
            angle = rng.random() * math.pi * 2.0
            self._agents.append([ax, ay, angle])

    def _sense(self, agent, offset_angle: float, sensor_dist: float, w: int, h: int) -> float:
        """在指定方向采样轨迹浓度 - Sample trail at given direction"""
        ax, ay, angle = agent
        sense_angle = angle + offset_angle
        sx = int(ax + math.cos(sense_angle) * sensor_dist) % w
        sy = int(ay + math.sin(sense_angle) * sensor_dist) % h
        return self._trail_map[sy][sx]

    def _step_agents(self, ctx: Context, sensor_dist: float, sensor_angle: float) -> None:
        """更新所有代理 - Update all agents"""
        w, h = ctx.width, ctx.height
        rng = ctx.rng
        turn_speed = 0.3

        for agent in self._agents:
            # Sense in three directions
            f = self._sense(agent, 0.0, sensor_dist, w, h)
            fl = self._sense(agent, -sensor_angle, sensor_dist, w, h)
            fr = self._sense(agent, sensor_angle, sensor_dist, w, h)

            # Turn toward strongest signal
            if f >= fl and f >= fr:
                pass  # Keep heading
            elif fl > fr:
                agent[2] -= turn_speed
            elif fr > fl:
                agent[2] += turn_speed
            else:
                # Equal: random jitter
                agent[2] += (rng.random() - 0.5) * turn_speed

            # Move forward
            agent[0] = (agent[0] + math.cos(agent[2])) % w
            agent[1] = (agent[1] + math.sin(agent[2])) % h

            # Deposit trail
            ix = int(agent[0]) % w
            iy = int(agent[1]) % h
            self._trail_map[iy][ix] = min(self._trail_map[iy][ix] + 1.0, 5.0)

    def _diffuse_and_decay(self, w: int, h: int, decay_rate: float) -> None:
        """扩散并衰减轨迹地图 - Diffuse and decay trail map"""
        old = self._trail_map
        new_map = [[0.0] * w for _ in range(h)]

        for y in range(h):
            ym = (y - 1) % h
            yp = (y + 1) % h
            for x in range(w):
                xm = (x - 1) % w
                xp = (x + 1) % w
                # Simple 3x3 box blur
                avg = (
                    old[ym][xm] + old[ym][x] + old[ym][xp]
                    + old[y][xm] + old[y][x] + old[y][xp]
                    + old[yp][xm] + old[yp][x] + old[yp][xp]
                ) / 9.0
                new_map[y][x] = avg * decay_rate

        self._trail_map = new_map

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        预处理 - 推进黏菌模拟

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            状态字典
        """
        sensor_distance = ctx.params.get("sensor_distance", 9)
        sensor_angle = ctx.params.get("sensor_angle", 0.4)
        decay_rate = ctx.params.get("decay_rate", 0.95)
        speed = ctx.params.get("speed", 3)
        warmth = ctx.params.get("warmth", None)
        saturation = ctx.params.get("saturation", None)

        if not self._initialized:
            self._init_state(ctx)
            self._initialized = True

        w, h = ctx.width, ctx.height

        # Simulation steps
        for _ in range(speed):
            self._step_agents(ctx, sensor_distance, sensor_angle)
            self._diffuse_and_decay(w, h, decay_rate)

        return {
            "trail_map": self._trail_map,
            "warmth": warmth,
            "saturation": saturation,
        }

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染 - 根据轨迹浓度生成 Cell

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell
        """
        trail = state["trail_map"]
        intensity = trail[y][x]

        # Normalize intensity to 0-1 (max expected ~3.0 after diffusion)
        value = clamp(intensity / 2.5, 0.0, 1.0)

        char_idx = int(clamp(value * 9, 0, 9))

        if state["warmth"] is not None:
            color = value_to_color_continuous(
                value,
                warmth=state["warmth"],
                saturation=state.get("saturation", 1.0),
            )
        else:
            color = value_to_color(value, "cool")

        return Cell(char_idx=char_idx, fg=color, bg=None)

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """后处理 - 黏菌模拟不需要后处理"""
        pass
