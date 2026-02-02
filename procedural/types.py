"""
类型系统 - Type System

定义程序化可视化系统的核心数据结构和协议。

核心类型::

    Context  - 渲染上下文 (尺寸、时间、随机种子、参数)
    Cell     - 单个字符单元 (字符索引、前景色、背景色)
    Buffer   - 2D 字符缓冲区 (list[list[Cell]])
    Effect   - 效果协议 (pre/main/post 三阶段渲染)

用法示例::

    from procedural.types import Context, Cell, Buffer, Effect
    import random

    # 创建渲染上下文
    ctx = Context(
        width=160,
        height=160,
        time=0.0,
        frame=0,
        seed=42,
        rng=random.Random(42),
        params={'intensity': 0.8}
    )

    # 创建字符单元
    cell = Cell(
        char_idx=5,           # ASCII 梯度索引
        fg=(255, 100, 0),     # 橙色前景
        bg=(0, 0, 0)          # 黑色背景
    )

    # 创建缓冲区
    buffer: Buffer = [[Cell(0, (0,0,0), None) for _ in range(160)] for _ in range(160)]

    # 实现效果
    class MyEffect:
        def pre(self, ctx: Context, buffer: Buffer) -> dict:
            return {'state': 'initialized'}

        def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
            return Cell(char_idx=x % 10, fg=(255, 255, 255), bg=None)

        def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
            pass
"""

from dataclasses import dataclass
from typing import Protocol
import random

__all__ = [
    "Context",
    "Cell",
    "Buffer",
    "Effect",
]


@dataclass
class Context:
    """
    渲染上下文 - Rendering Context

    包含渲染一帧所需的所有全局信息。

    属性:
        width: 内部网格宽度 (如 160)
        height: 内部网格高度 (如 160)
        time: 当前时间 (秒，用于动画)
        frame: 当前帧号 (从 0 开始)
        seed: 随机种子 (用于可复现生成)
        rng: 可复现的随机数生成器 (random.Random 实例)
        params: 效果特定参数 (dict，由 ParamSpec 生成)

    示例::

        ctx = Context(
            width=160,
            height=160,
            time=1.5,
            frame=90,
            seed=42,
            rng=random.Random(42),
            params={'speed': 2.0, 'intensity': 0.8}
        )
    """

    width: int
    height: int
    time: float
    frame: int
    seed: int
    rng: random.Random
    params: dict


@dataclass
class Cell:
    """
    字符单元 - Character Cell

    表示 ASCII 艺术中的单个字符及其颜色。

    属性:
        char_idx: ASCII 梯度索引 (0-9 或更大，映射到字符集如 " .:-=+*#%@")
        fg: 前景色 RGB 元组 (r, g, b)，范围 0-255
        bg: 背景色 RGB 元组 (r, g, b) 或 None (透明背景)

    示例::

        # 白色 '#' 字符，黑色背景
        cell = Cell(char_idx=8, fg=(255, 255, 255), bg=(0, 0, 0))

        # 绿色 ':' 字符，透明背景
        cell = Cell(char_idx=2, fg=(0, 255, 0), bg=None)
    """

    char_idx: int
    fg: tuple  # (r, g, b)
    bg: tuple | None  # (r, g, b) or None


# 类型别名
Buffer = list[list[Cell]]
"""
2D 字符缓冲区 - 2D Character Buffer

表示整个 ASCII 艺术画布的二维数组。

结构: buffer[y][x] → Cell

示例::

    # 创建 160x160 的空白缓冲区
    buffer: Buffer = [
        [Cell(0, (0, 0, 0), None) for x in range(160)]
        for y in range(160)
    ]
    
    # 访问特定位置
    cell = buffer[80][80]  # 中心点
    
    # 修改特定位置
    buffer[10][20] = Cell(char_idx=5, fg=(255, 0, 0), bg=None)
"""


class Effect(Protocol):
    """
    效果协议 - Effect Protocol

    定义程序化效果的三阶段渲染接口。
    所有效果必须实现 pre(), main(), post() 三个方法。

    渲染流程:
        1. pre()  - 预处理阶段 (初始化状态、计算全局参数)
        2. main() - 主渲染阶段 (逐像素调用，生成 Cell)
        3. post() - 后处理阶段 (全局效果、模糊、锐化等)

    方法:
        pre(ctx, buffer) -> dict:
            预处理阶段，返回状态字典供 main() 使用。

            参数:
                ctx: 渲染上下文
                buffer: 当前缓冲区 (可读写)

            返回:
                状态字典 (任意键值对，传递给 main() 和 post())

        main(x, y, ctx, state) -> Cell:
            主渲染阶段，为每个像素生成 Cell。

            参数:
                x: 像素 X 坐标 (0 到 width-1)
                y: 像素 Y 坐标 (0 到 height-1)
                ctx: 渲染上下文
                state: pre() 返回的状态字典

            返回:
                该位置的 Cell (字符索引 + 颜色)

        post(ctx, buffer, state) -> None:
            后处理阶段，可修改整个缓冲区。

            参数:
                ctx: 渲染上下文
                buffer: 渲染后的缓冲区 (可修改)
                state: pre() 返回的状态字典

    示例实现::

        class PlasmaEffect:
            def pre(self, ctx: Context, buffer: Buffer) -> dict:
                # 预计算全局参数
                return {
                    'scale': ctx.params.get('scale', 0.05),
                    'speed': ctx.params.get('speed', 1.0)
                }

            def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
                from procedural.core import plasma

                # 生成 plasma 值
                value = plasma(x, y, ctx.time, state['scale'], state['speed'])

                # 映射到字符索引和颜色
                char_idx = int(value * 9)
                color = (int(value * 255), 0, int((1 - value) * 255))

                return Cell(char_idx=char_idx, fg=color, bg=None)

            def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
                # 可选: 添加后处理效果 (如模糊、锐化)
                pass
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict:
        """
        预处理阶段 - Preprocessing Phase

        在主渲染前调用一次，用于:
        - 初始化效果状态
        - 预计算全局参数
        - 设置随机种子
        - 准备查找表

        参数:
            ctx: 渲染上下文
            buffer: 当前缓冲区 (通常为空，可预填充)

        返回:
            状态字典 (传递给 main() 和 post())
        """
        ...

    def main(self, x: int, y: int, ctx: Context, state: dict) -> Cell:
        """
        主渲染阶段 - Main Rendering Phase

        为每个像素调用一次，生成该位置的 Cell。

        参数:
            x: 像素 X 坐标 (0 到 width-1)
            y: 像素 Y 坐标 (0 到 height-1)
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        返回:
            该位置的 Cell (字符索引 + 颜色)
        """
        ...

    def post(self, ctx: Context, buffer: Buffer, state: dict) -> None:
        """
        后处理阶段 - Postprocessing Phase

        在主渲染后调用一次，用于:
        - 全局模糊/锐化
        - 色彩校正
        - 添加噪点/故障效果
        - 边缘检测

        参数:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区 (可直接修改)
            state: pre() 返回的状态字典
        """
        ...
