"""
装饰风格生成器 - Decoration Style Builders

将装饰风格生成逻辑从 pipeline.py 中解耦，每种风格独立函数，
通过 dispatcher 统一调用。

支持的风格::

    - corners: 四角装饰
    - edges: 边缘装饰
    - scattered: 随机散布
    - minimal: 极简对角
    - frame: Box-drawing 边框
    - grid_lines: 网格线
    - circuit: 电路板风格
    - none: 无装饰

添加新风格::

    1. 定义 def deco_xxx(ctx: DecoContext) -> list[TextSprite]: ...
    2. 注册到 DECO_BUILDERS["xxx"] = deco_xxx
    3. 在 grammar.py 的 _DECORATION_OPTIONS 中添加 "xxx"

用法::

    from procedural.flexible.decorations import build_decoration_sprites

    sprites = build_decoration_sprites(
        style="frame",
        spec=scene_spec,
        palette=palette_dict,
        width=1080,
        height=1080,
        rng=random.Random(42),
    )
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from procedural.layers import TextSprite

if TYPE_CHECKING:
    from .grammar import SceneSpec


@dataclass
class DecoContext:
    """
    装饰生成上下文 - Decoration Builder Context

    封装所有装饰生成器需要的输入参数，避免长参数列表。
    """

    spec: SceneSpec
    palette: dict[str, Any]
    width: int
    height: int
    rng: random.Random
    margin: int = 40

    @property
    def chars(self) -> list[str]:
        """装饰字符列表"""
        return list(self.spec.decoration_chars)

    @property
    def color(self) -> tuple[int, int, int]:
        """装饰颜色"""
        c = self.palette.get("dim", self.palette.get("outline", (80, 80, 80)))
        return tuple(c)  # type: ignore[return-value]

    @property
    def w(self) -> int:
        return self.width

    @property
    def h(self) -> int:
        return self.height


def deco_none(ctx: DecoContext) -> list[TextSprite]:
    """无装饰 - No decoration"""
    return []


def deco_corners(ctx: DecoContext) -> list[TextSprite]:
    """
    四角装饰 - Corner decorations

    在画面四个角落放置装饰字符，带呼吸动画。
    """
    decos: list[TextSprite] = []
    m = ctx.margin

    positions = [
        (m, m),
        (ctx.w - m, m),
        (m, ctx.h - m),
        (ctx.w - m, ctx.h - m),
    ]

    for i, (x, y) in enumerate(positions):
        ch = ctx.chars[i % len(ctx.chars)]
        decos.append(
            TextSprite(
                text=ch,
                x=x,
                y=y,
                color=ctx.color,
                scale=1.0,
                animations=[{"type": "breathing", "amp": 0.02, "speed": 0.5}],
            )
        )

    return decos


def deco_edges(ctx: DecoContext) -> list[TextSprite]:
    """
    边缘装饰 - Edge decorations

    在画面四条边上等距放置装饰字符。
    """
    decos: list[TextSprite] = []
    m = ctx.margin

    for i in range(4):
        ch = ctx.chars[i % len(ctx.chars)]
        for j in range(3):
            t = (j + 1) / 4
            if i == 0:
                x, y = int(t * ctx.w), m
            elif i == 1:
                x, y = int(t * ctx.w), ctx.h - m
            elif i == 2:
                x, y = m, int(t * ctx.h)
            else:
                x, y = ctx.w - m, int(t * ctx.h)
            decos.append(
                TextSprite(
                    text=ch,
                    x=x,
                    y=y,
                    color=ctx.color,
                    scale=1.0,
                )
            )

    return decos


def deco_scattered(ctx: DecoContext) -> list[TextSprite]:
    """
    随机散布 - Scattered decorations

    在画面随机位置散布装饰字符，带浮动动画。
    """
    decos: list[TextSprite] = []
    m = ctx.margin
    count = ctx.rng.randint(8, 16)

    for _ in range(count):
        ch = ctx.rng.choice(ctx.chars)
        x = ctx.rng.randint(m, ctx.w - m)
        y = ctx.rng.randint(m, ctx.h - m)
        decos.append(
            TextSprite(
                text=ch,
                x=x,
                y=y,
                color=ctx.color,
                scale=1.0,
                animations=[
                    {
                        "type": "floating",
                        "amp": ctx.rng.uniform(1, 4),
                        "speed": ctx.rng.uniform(0.3, 1.0),
                        "phase": ctx.rng.uniform(0, 6.28),
                    }
                ],
            )
        )

    return decos


def deco_minimal(ctx: DecoContext) -> list[TextSprite]:
    """
    极简装饰 - Minimal decorations

    只在左上和右下对角放置装饰字符。
    """
    m = ctx.margin
    return [
        TextSprite(
            text=ctx.chars[0],
            x=m,
            y=m,
            color=ctx.color,
            scale=1.0,
        ),
        TextSprite(
            text=ctx.chars[-1],
            x=ctx.w - m,
            y=ctx.h - m,
            color=ctx.color,
            scale=1.0,
        ),
    ]


def deco_frame(ctx: DecoContext) -> list[TextSprite]:
    """
    边框装饰 - Box-drawing frame

    使用 box-drawing 字符绘制矩形边框，根据 energy 选择粗细。
    """
    from lib.box_chars import get_border_set

    decos: list[TextSprite] = []
    inset = ctx.margin
    color = ctx.color
    rng = ctx.rng

    energy = ctx.spec.warmth
    if energy > 0.6:
        bs = get_border_set("heavy")
    elif energy > 0.3:
        bs = get_border_set(rng.choice(["light", "round"]))
    else:
        bs = get_border_set(rng.choice(["dash_light", "round"]))

    corner_anim = [{"type": "breathing", "amp": 0.02, "speed": 0.4}]
    decos.extend(
        [
            TextSprite(
                text=bs["tl"],
                x=inset,
                y=inset,
                color=color,
                scale=1.0,
                animations=corner_anim,
            ),
            TextSprite(
                text=bs["tr"],
                x=ctx.w - inset,
                y=inset,
                color=color,
                scale=1.0,
                animations=corner_anim,
            ),
            TextSprite(
                text=bs["bl"],
                x=inset,
                y=ctx.h - inset,
                color=color,
                scale=1.0,
                animations=corner_anim,
            ),
            TextSprite(
                text=bs["br"],
                x=ctx.w - inset,
                y=ctx.h - inset,
                color=color,
                scale=1.0,
                animations=corner_anim,
            ),
        ]
    )

    h_count = rng.randint(5, 12)
    for i in range(h_count):
        t = (i + 1) / (h_count + 1)
        px = int(inset + t * (ctx.w - 2 * inset))
        decos.append(TextSprite(text=bs["h"], x=px, y=inset, color=color, scale=1.0))
        decos.append(
            TextSprite(text=bs["h"], x=px, y=ctx.h - inset, color=color, scale=1.0)
        )

    v_count = rng.randint(4, 10)
    for i in range(v_count):
        t = (i + 1) / (v_count + 1)
        py = int(inset + t * (ctx.h - 2 * inset))
        decos.append(TextSprite(text=bs["v"], x=inset, y=py, color=color, scale=1.0))
        decos.append(
            TextSprite(text=bs["v"], x=ctx.w - inset, y=py, color=color, scale=1.0)
        )

    if rng.random() < 0.5:
        for _ in range(rng.randint(1, 3)):
            side = rng.randint(0, 3)
            t = rng.uniform(0.2, 0.8)
            if side == 0:
                px, py = int(inset + t * (ctx.w - 2 * inset)), inset
                ch = bs["tt"]
            elif side == 1:
                px, py = int(inset + t * (ctx.w - 2 * inset)), ctx.h - inset
                ch = bs["bt"]
            elif side == 2:
                px, py = inset, int(inset + t * (ctx.h - 2 * inset))
                ch = bs["lt"]
            else:
                px, py = ctx.w - inset, int(inset + t * (ctx.h - 2 * inset))
                ch = bs["rt"]
            decos.append(TextSprite(text=ch, x=px, y=py, color=color, scale=1.0))

    return decos


def deco_grid_lines(ctx: DecoContext) -> list[TextSprite]:
    """
    网格线装饰 - Grid line decorations

    在画面中绘制交叉网格。
    """
    from lib.box_chars import get_border_set

    decos: list[TextSprite] = []
    m = ctx.margin
    rng = ctx.rng
    color = ctx.color

    bs = get_border_set(rng.choice(["light", "heavy", "dash_light"]))

    grid_cols = rng.randint(2, 5)
    grid_rows = rng.randint(2, 5)

    dim_color = tuple(max(0, int(c) - 40) for c in color)

    for c in range(grid_cols):
        t = (c + 1) / (grid_cols + 1)
        px = int(t * ctx.w)
        for _ in range(rng.randint(3, 8)):
            py = rng.randint(m, ctx.h - m)
            decos.append(
                TextSprite(text=bs["v"], x=px, y=py, color=dim_color, scale=1.0)
            )

    for r in range(grid_rows):
        t = (r + 1) / (grid_rows + 1)
        py = int(t * ctx.h)
        for _ in range(rng.randint(3, 8)):
            px = rng.randint(m, ctx.w - m)
            decos.append(
                TextSprite(text=bs["h"], x=px, y=py, color=dim_color, scale=1.0)
            )

    for c in range(grid_cols):
        for r in range(grid_rows):
            if rng.random() < 0.6:
                px = int((c + 1) / (grid_cols + 1) * ctx.w)
                py = int((r + 1) / (grid_rows + 1) * ctx.h)
                decos.append(
                    TextSprite(
                        text=bs["cross"],
                        x=px,
                        y=py,
                        color=color,
                        scale=1.0,
                        animations=[{"type": "breathing", "amp": 0.03, "speed": 0.3}],
                    )
                )

    return decos


def deco_circuit(ctx: DecoContext) -> list[TextSprite]:
    """
    电路板装饰 - Circuit board style

    随机生成节点和延伸的线路。
    """
    from lib.box_chars import get_border_set

    decos: list[TextSprite] = []
    m = ctx.margin
    rng = ctx.rng
    color = ctx.color

    bs = get_border_set(rng.choice(["light", "heavy"]))

    node_count = rng.randint(4, 10)
    trace_color = tuple(max(0, int(c) - 20) for c in color)

    for _ in range(node_count):
        nx = rng.randint(m * 2, ctx.w - m * 2)
        ny = rng.randint(m * 2, ctx.h - m * 2)

        node_char = rng.choice([bs["cross"], bs["lt"], bs["rt"], bs["tt"], bs["bt"]])
        decos.append(
            TextSprite(
                text=node_char,
                x=nx,
                y=ny,
                color=color,
                scale=1.0,
                animations=[{"type": "breathing", "amp": 0.02, "speed": 0.6}],
            )
        )

        trace_len = rng.randint(2, 6)
        direction = rng.choice(["h", "v"])
        sign = 1

        for t in range(1, trace_len + 1):
            if direction == "h":
                sign = rng.choice([-1, 1])
                px = nx + sign * t * 20
                py = ny
                ch = bs["h"]
            else:
                sign = rng.choice([-1, 1])
                px = nx
                py = ny + sign * t * 20
                ch = bs["v"]

            if m < px < ctx.w - m and m < py < ctx.h - m:
                decos.append(
                    TextSprite(text=ch, x=px, y=py, color=trace_color, scale=1.0)
                )

        if direction == "h":
            end_x = nx + sign * (trace_len + 1) * 20
            end_y = ny
        else:
            end_x = nx
            end_y = ny + sign * (trace_len + 1) * 20

        if m < end_x < ctx.w - m and m < end_y < ctx.h - m:
            end_char = rng.choice(
                ["·", "•", "◦", "○", bs["tl"], bs["tr"], bs["bl"], bs["br"]]
            )
            decos.append(
                TextSprite(
                    text=end_char, x=end_x, y=end_y, color=trace_color, scale=1.0
                )
            )

    return decos


DECO_BUILDERS: dict[str, Callable[[DecoContext], list[TextSprite]]] = {
    "none": deco_none,
    "corners": deco_corners,
    "edges": deco_edges,
    "scattered": deco_scattered,
    "minimal": deco_minimal,
    "frame": deco_frame,
    "grid_lines": deco_grid_lines,
    "circuit": deco_circuit,
}


def build_decoration_sprites(
    style: str,
    spec: SceneSpec,
    palette: dict[str, Any],
    width: int,
    height: int,
    rng: random.Random,
    margin: int = 40,
) -> list[TextSprite]:
    """
    构建装饰精灵 - Build decoration sprites

    根据指定的装饰风格生成对应的精灵列表。

    Args:
        style: 装饰风格名称 (corners, edges, scattered, minimal, frame, grid_lines, circuit, none)
        spec: 场景规格
        palette: 调色板
        width: 画面宽度
        height: 画面高度
        rng: 随机数生成器
        margin: 边距 (默认 40)

    Returns:
        TextSprite 列表

    Raises:
        ValueError: 如果风格名称未知

    示例::

        sprites = build_decoration_sprites(
            style="frame",
            spec=scene_spec,
            palette={"dim": (80, 80, 80)},
            width=1080,
            height=1080,
            rng=random.Random(42),
        )
    """
    builder = DECO_BUILDERS.get(style)
    if builder is None:
        raise ValueError(
            f"Unknown decoration style '{style}'. "
            f"Available: {sorted(DECO_BUILDERS.keys())}"
        )

    ctx = DecoContext(
        spec=spec,
        palette=palette,
        width=width,
        height=height,
        rng=rng,
        margin=margin,
    )

    return builder(ctx)


DECORATION_STYLES = list(DECO_BUILDERS.keys())
