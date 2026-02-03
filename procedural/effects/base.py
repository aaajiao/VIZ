"""
效果基类和辅助函数 - Effect Base Classes and Utilities

提供效果实现的通用工具和基类。

用法::

    from procedural.effects.base import BaseEffect

    class MyEffect(BaseEffect):
        def main(self, x, y, ctx, state):
            # 实现主渲染逻辑
            return Cell(...)
"""

from typing import Any

from procedural.types import Context, Cell, Buffer

__all__ = [
    "BaseEffect",
]


class BaseEffect:
    """
    效果基类 - Base Effect Class

    提供 pre() 和 post() 的默认实现，子类只需实现 main() 方法。

    适用于不需要预处理或后处理的简单效果。

    示例::

        class SimpleEffect(BaseEffect):
            def main(self, x, y, ctx, state):
                value = (x + y) / (ctx.width + ctx.height)
                char_idx = int(value * 9)
                return Cell(char_idx=char_idx, fg=(255, 255, 255), bg=None)
    """

    def pre(self, ctx: Context, buffer: Buffer) -> dict[str, Any]:
        """
        默认预处理 - 返回空状态字典

        子类可覆盖此方法以添加预处理逻辑。

        Args:
            ctx: 渲染上下文
            buffer: 当前缓冲区

        Returns:
            空字典 {}
        """
        return {}

    def main(self, x: int, y: int, ctx: Context, state: dict[str, Any]) -> Cell:
        """
        主渲染方法 - 必须由子类实现

        Args:
            x: 像素 X 坐标
            y: 像素 Y 坐标
            ctx: 渲染上下文
            state: pre() 返回的状态字典

        Returns:
            该位置的 Cell

        Raises:
            NotImplementedError: 如果子类未实现
        """
        raise NotImplementedError("Subclass must implement main() method")

    def post(self, ctx: Context, buffer: Buffer, state: dict[str, Any]) -> None:
        """
        默认后处理 - 无操作

        子类可覆盖此方法以添加后处理逻辑。

        Args:
            ctx: 渲染上下文
            buffer: 渲染后的缓冲区
            state: pre() 返回的状态字典
        """
        pass
