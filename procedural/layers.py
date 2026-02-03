"""
Sprite Layer Animation System - 精灵层动画系统

提供文字和颜文字的精灵层，支持呼吸、浮动、颜色循环等动画效果。
每个精灵 (Sprite) 封装位置、缩放、颜色、旋转等属性，
可通过动画函数随时间变化产生动态视觉效果。

核心类型::

    Sprite         - 精灵基类 (position, scale, color, rotation)
    TextSprite     - 文字精灵 (使用 draw_glow_text 渲染)
    KaomojiSprite  - 颜文字精灵 (使用 draw_kaomoji 渲染)

动画函数::

    breathing(time, amp, speed)    - 呼吸缩放效果
    floating(time, amp, speed)     - 上下浮动效果
    color_cycle(time, base_hue, speed) - HSV 色相循环

用法示例::

    from procedural.layers import TextSprite, KaomojiSprite

    # 文字精灵
    text = TextSprite('MARKET', x=100, y=100, color='#00ff00')
    text.render(image, time=1.5)

    # 颜文字精灵
    face = KaomojiSprite('bull', x=200, y=200)
    face.render(image, time=2.0)

    # 批量渲染到图像
    from procedural.layers import render_to_image
    sprites = [text, face]
    img = render_to_image(sprites, width=1080, height=1080, time=1.5)
"""

import colorsys
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

from PIL import Image, ImageDraw

# === 动画函数 (Animation Functions) ===


def breathing(time, amp=0.05, speed=2.0):
    """
    呼吸缩放动画 - Breathing Scale Animation

    返回随时间正弦变化的缩放系数，模拟呼吸节奏。
    以 1.0 为中心，在 [1-amp, 1+amp] 范围内振荡。

    参数:
        time: 当前时间 (秒)
        amp: 缩放幅度 (默认 0.05，即 ±5%)
        speed: 速度因子 (默认 2.0)

    返回:
        float - 缩放值，如 1.03

    公式::

        scale = 1.0 + amp * sin(time * speed)

    示例::

        breathing(0.0)  # → 1.0  (起始)
        breathing(0.785, amp=0.1, speed=2.0)  # → ~1.1  (峰值附近)
    """
    return 1.0 + amp * math.sin(time * speed)


def floating(time, amp=20.0, speed=1.0, phase=0.0):
    """
    浮动位移动画 - Floating Y-Offset Animation

    返回随时间正弦变化的 Y 轴偏移量，模拟上下浮动。

    参数:
        time: 当前时间 (秒)
        amp: 浮动幅度，像素 (默认 20.0)
        speed: 速度因子 (默认 1.0)
        phase: 相位偏移，弧度 (默认 0.0，可为不同精灵错开相位)

    返回:
        float - Y 轴偏移量 (像素)

    公式::

        y_offset = amp * sin(time * speed + phase)

    示例::

        floating(0.0)  # → 0.0
        floating(1.57)  # → ~20.0 (向下偏移最大)
    """
    return amp * math.sin(time * speed + phase)


def color_cycle(time, base_hue=0.0, speed=1.0, saturation=1.0, value=1.0):
    """
    颜色循环动画 - HSV Hue Cycle Animation

    返回随时间循环变化的 RGB 颜色，通过 HSV 色相旋转实现。

    参数:
        time: 当前时间 (秒)
        base_hue: 基础色相 (0.0-1.0，默认 0.0 = 红色)
        speed: 循环速度 (默认 1.0，每秒旋转一圈为 1.0)
        saturation: 饱和度 (0.0-1.0，默认 1.0)
        value: 明度 (0.0-1.0，默认 1.0)

    返回:
        tuple - (r, g, b)，范围 0-255

    公式::

        hue = (base_hue + time * speed) % 1.0
        rgb = hsv_to_rgb(hue, saturation, value)

    示例::

        color_cycle(0.0, base_hue=0.0)    # → (255, 0, 0)   红色
        color_cycle(0.33, base_hue=0.0)   # → 色相偏移后的颜色
    """
    hue = (base_hue + time * speed) % 1.0
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))


# === 颜色工具 (Color Utilities) ===


def _hex_to_rgb(hex_color):
    """
    将十六进制颜色转换为 RGB 元组

    参数:
        hex_color: 十六进制颜色字符串 (如 '#FF0000')

    返回:
        RGB 元组 (如 (255, 0, 0))
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _resolve_color(color):
    """
    统一颜色格式为 RGB 元组

    接受十六进制字符串或 RGB 元组，返回 (r, g, b) 元组。

    参数:
        color: '#FF0000' 或 (255, 0, 0)

    返回:
        (r, g, b) 元组
    """
    if isinstance(color, str):
        return _hex_to_rgb(color)
    return tuple(color)


# === 精灵基类 (Sprite Base) ===


@dataclass
class Sprite:
    """
    精灵基类 - Sprite Base Class

    所有可渲染精灵的基础，封装位置、缩放、颜色、旋转属性。
    支持通过 animations 列表挂载动画效果。

    属性:
        x: X 坐标 (像素)
        y: Y 坐标 (像素)
        scale: 缩放系数 (1.0 = 原始大小)
        color: 颜色 (十六进制字符串或 RGB 元组)
        rotation: 旋转角度 (弧度，当前保留，渲染时未使用)
        visible: 是否可见 (False 时跳过渲染)
        animations: 动画效果配置列表

    animations 格式::

        [
            {'type': 'breathing', 'amp': 0.1, 'speed': 2.0},
            {'type': 'floating', 'amp': 15, 'speed': 1.5, 'phase': 0.0},
            {'type': 'color_cycle', 'base_hue': 0.3, 'speed': 0.5},
        ]

    示例::

        sprite = Sprite(x=100, y=200, color='#00ff00')
        sprite.animations = [{'type': 'breathing', 'amp': 0.1}]
    """

    x: float = 0.0
    y: float = 0.0
    scale: float = 1.0
    color: object = (255, 255, 255)  # hex str or RGB tuple
    rotation: float = 0.0
    visible: bool = True
    animations: list = field(default_factory=list)

    @property
    def position(self):
        """返回 (x, y) 元组"""
        return (self.x, self.y)

    @position.setter
    def position(self, pos):
        """设置 (x, y) 位置"""
        self.x, self.y = pos

    def apply_animations(self, time):
        """
        应用所有挂载的动画效果 - Apply Animations

        根据 self.animations 列表，计算当前时间下的动画变换值。
        返回一个包含变换结果的字典。

        参数:
            time: 当前时间 (秒)

        返回:
            dict - 动画变换结果::

                {
                    'scale': float,       # 缩放系数 (所有呼吸效果叠乘)
                    'y_offset': float,     # Y 偏移 (所有浮动效果叠加)
                    'color': tuple | None, # RGB 颜色 (最后一个颜色循环的值)
                }
        """
        result = {
            "scale": self.scale,
            "y_offset": 0.0,
            "color": None,
        }

        for anim in self.animations:
            anim_type = anim.get("type", "")

            if anim_type == "breathing":
                breath_scale = breathing(
                    time,
                    amp=anim.get("amp", 0.05),
                    speed=anim.get("speed", 2.0),
                )
                result["scale"] *= breath_scale

            elif anim_type == "floating":
                y_off = floating(
                    time,
                    amp=anim.get("amp", 20.0),
                    speed=anim.get("speed", 1.0),
                    phase=anim.get("phase", 0.0),
                )
                result["y_offset"] += y_off

            elif anim_type == "color_cycle":
                rgb = color_cycle(
                    time,
                    base_hue=anim.get("base_hue", 0.0),
                    speed=anim.get("speed", 1.0),
                    saturation=anim.get("saturation", 1.0),
                    value=anim.get("value", 1.0),
                )
                result["color"] = rgb

        return result

    def render(self, image, time=0.0):
        """
        将精灵渲染到 PIL Image - Render Sprite to Image

        子类必须重写此方法以实现具体的绘制逻辑。

        参数:
            image: PIL Image 对象
            time: 当前时间 (秒)
        """
        raise NotImplementedError("Subclass must implement render()")


# === 文字精灵 (Text Sprite) ===


class TextSprite(Sprite):
    """
    文字精灵 - Text Sprite

    在图像上绘制带发光效果的文字，支持呼吸/浮动/颜色循环动画。
    使用 viz.lib.effects.draw_glow_text() 进行渲染。

    属性 (继承自 Sprite):
        x, y, scale, color, rotation, visible, animations

    附加属性:
        text: 要显示的文字字符串
        glow_color: 发光颜色 (十六进制或 RGB 元组)
        glow_size: 发光强度 (传递给 draw_glow_text 的 size 参数)

    示例::

        sprite = TextSprite('BULL MARKET', x=100, y=100, color='#00ff00')
        sprite.animations = [
            {'type': 'breathing', 'amp': 0.08, 'speed': 3.0},
            {'type': 'floating', 'amp': 10, 'speed': 1.2},
        ]
        sprite.render(image, time=2.5)
    """

    def __init__(
        self,
        text,
        x=0.0,
        y=0.0,
        color="#ffffff",
        glow_color=None,
        glow_size=1,
        scale=1.0,
        rotation=0.0,
        visible=True,
        animations=None,
    ):
        super().__init__(
            x=x,
            y=y,
            scale=scale,
            color=color,
            rotation=rotation,
            visible=visible,
            animations=animations or [],
        )
        self.text = text
        self.glow_color = glow_color
        self.glow_size = glow_size

    def render(self, image, time=0.0):
        """
        将文字精灵渲染到图像 - Render Text to Image

        应用动画效果后，使用 draw_glow_text 绘制文字。
        如果没有 glow_color，使用普通 ImageDraw.text 绘制。

        参数:
            image: PIL Image 对象
            time: 当前时间 (秒)
        """
        if not self.visible:
            return

        # === 应用动画 ===
        anim = self.apply_animations(time)

        # 计算最终位置
        draw_x = self.x
        draw_y = self.y + anim["y_offset"]

        # 计算最终颜色
        if anim["color"] is not None:
            final_color = anim["color"]
        else:
            final_color = _resolve_color(self.color)

        # 计算 glow size (基于动画缩放)
        effective_glow_size = max(1, int(self.glow_size * anim["scale"]))

        draw = ImageDraw.Draw(image)

        # === 绘制文字 ===
        if self.glow_color is not None:
            glow_rgb = _resolve_color(self.glow_color)
            _draw_glow_text(
                draw,
                int(draw_x),
                int(draw_y),
                self.text,
                final_color,
                glow_rgb,
                size=effective_glow_size,
            )
        else:
            # 简单绘制 (无发光)，使用缩放的粗细模拟
            for dx in range(max(1, effective_glow_size)):
                for dy in range(max(1, effective_glow_size)):
                    draw.text(
                        (int(draw_x) + dx, int(draw_y) + dy),
                        self.text,
                        fill=final_color,
                    )


# === 颜文字精灵 (Kaomoji Sprite) ===


class KaomojiSprite(Sprite):
    """
    颜文字精灵 - Kaomoji Sprite

    在图像上绘制 ASCII 颜文字，支持呼吸/浮动/颜色循环动画。
    使用 viz.lib.kaomoji.draw_kaomoji() 进行渲染。

    属性 (继承自 Sprite):
        x, y, scale, color, rotation, visible, animations

    附加属性:
        mood: 情绪类型 ('bull', 'bear', 'neutral', 'euphoria', 'panic' 等)
        outline_color: 轮廓颜色 (十六进制或 RGB 元组)

    示例::

        sprite = KaomojiSprite('bull', x=200, y=200, color='#00ff00')
        sprite.animations = [
            {'type': 'floating', 'amp': 15, 'speed': 0.8},
            {'type': 'color_cycle', 'base_hue': 0.3, 'speed': 0.2},
        ]
        sprite.render(image, time=3.0)
    """

    def __init__(
        self,
        mood="neutral",
        x=0.0,
        y=0.0,
        color="#ffffff",
        outline_color=None,
        scale=1.0,
        rotation=0.0,
        visible=True,
        animations=None,
    ):
        super().__init__(
            x=x,
            y=y,
            scale=scale,
            color=color,
            rotation=rotation,
            visible=visible,
            animations=animations or [],
        )
        self.mood = mood
        self.outline_color = outline_color

    def render(self, image, time=0.0):
        """
        将颜文字精灵渲染到图像 - Render Kaomoji to Image

        应用动画效果后，使用 draw_kaomoji 绘制颜文字。
        如果 draw_kaomoji 不可用，回退到直接 ImageDraw 文字绘制。

        参数:
            image: PIL Image 对象
            time: 当前时间 (秒)
        """
        if not self.visible:
            return

        # === 应用动画 ===
        anim = self.apply_animations(time)

        # 计算最终位置
        draw_x = self.x
        draw_y = self.y + anim["y_offset"]

        # 计算最终颜色
        if anim["color"] is not None:
            final_color = anim["color"]
        else:
            final_color = _resolve_color(self.color)

        # 计算最终缩放
        effective_scale = max(1, int(anim["scale"]))

        # 轮廓颜色 (默认为主颜色的暗色版本)
        if self.outline_color is not None:
            outline_rgb = _resolve_color(self.outline_color)
        else:
            outline_rgb = tuple(max(0, c // 3) for c in final_color)

        # === 尝试使用 lib.kaomoji ===
        try:
            from lib.kaomoji import draw_kaomoji

            draw = ImageDraw.Draw(image)
            draw_kaomoji(
                draw,
                int(draw_x),
                int(draw_y),
                self.mood,
                final_color,
                outline_rgb,
                size=effective_scale,
            )
        except ImportError:
            # 回退: 使用简单文字绘制
            _draw_kaomoji_fallback(
                image,
                int(draw_x),
                int(draw_y),
                self.mood,
                final_color,
                outline_rgb,
                effective_scale,
            )


# === 批量渲染 (Batch Rendering) ===


def render_to_image(sprites, width=1080, height=1080, time=0.0, bg_color=(0, 0, 0)):
    """
    将精灵列表渲染到新的 PIL Image - Render Sprites to Image

    创建指定尺寸的画布，按顺序将所有精灵绘制上去。
    精灵列表的顺序决定了渲染层级 (后面的精灵覆盖前面的)。

    参数:
        sprites: Sprite 列表 (TextSprite, KaomojiSprite 等)
        width: 图像宽度 (默认 1080)
        height: 图像高度 (默认 1080)
        time: 当前时间 (秒)
        bg_color: 背景色 RGB 元组 (默认黑色)

    返回:
        PIL Image 对象

    示例::

        sprites = [
            TextSprite('HELLO', x=100, y=100, color='#ff0000'),
            KaomojiSprite('bull', x=200, y=200, color='#00ff00'),
        ]
        img = render_to_image(sprites, width=1080, height=1080, time=1.5)
        img.save('output.png')
    """
    image = Image.new("RGB", (width, height), bg_color)

    for sprite in sprites:
        sprite.render(image, time=time)

    return image


# === 内部绘制函数 (Internal Drawing Functions) ===


def _draw_glow_text(draw, x, y, text, color, glow_color, size=1):
    """
    发光文字效果 (内联版本)

    与 viz.lib.effects.draw_glow_text 相同的算法，
    内联以避免对 lib 模块的强依赖。

    参数:
        draw: PIL ImageDraw 对象
        x: X 坐标
        y: Y 坐标
        text: 文字字符串
        color: 主颜色 (RGB 元组)
        glow_color: 发光颜色 (RGB 元组)
        size: 发光强度 (默认 1)
    """
    # 尝试使用 lib.effects 中的实现
    try:
        from lib.effects import draw_glow_text as _lib_glow

        _lib_glow(draw, x, y, text, color, glow_color, size=size)
        return
    except ImportError:
        pass

    # 回退: 内联发光算法
    # 外发光 (多层偏移)
    for offset in range(size + 3, 0, -1):
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), text, fill=glow_color)

    # 主体文字 (加粗)
    for dx in range(size):
        for dy in range(size):
            draw.text((x + dx, y + dy), text, fill=color)


def _draw_kaomoji_fallback(image, x, y, mood, color, outline_color, scale):
    """
    颜文字回退绘制 (不依赖 lib.kaomoji)

    当 lib.kaomoji 不可用时，使用内置的简单颜文字绘制。

    参数:
        image: PIL Image 对象
        x: X 坐标
        y: Y 坐标
        mood: 情绪类型
        color: 主颜色 (RGB 元组)
        outline_color: 轮廓颜色 (RGB 元组)
        scale: 缩放大小
    """
    # 简单颜文字映射 — 每个情绪分类一个代表性 fallback
    FALLBACK_KAOMOJI = {
        # 正面
        "bull": "(^o^)",
        "happy": "(◠‿◠)",
        "euphoria": "\\(≧▽≦)/",
        "excitement": "(*^_^*)",
        "love": "(♡˙︶˙♡)",
        "proud": "(•̀ᴗ•́)و",
        "relaxed": "(´ー`)",
        # 负面
        "bear": "(;_;)",
        "sad": "(ಥ_ಥ)",
        "angry": "(╬ Ò﹏Ó)",
        "anxiety": "(´；ω；`)",
        "fear": "Σ(°△°|||)",
        "panic": "(×_×;）",
        "disappointed": "(ー_ー)!!",
        "lonely": "(◞‸◟)",
        # 中性
        "neutral": "(._.) ",
        "confused": "(？_？)",
        "surprised": "Σ(ﾟДﾟ)",
        "sleepy": "(=_=) zzZ",
        "thinking": "(˘_˘ )",
        "embarrassed": "(〃▽〃)",
        "bored": "(￢_￢)",
    }

    text = FALLBACK_KAOMOJI.get(mood, FALLBACK_KAOMOJI.get("neutral", "(._.) "))
    draw = ImageDraw.Draw(image)

    # 轮廓
    for dx in [-2, -1, 0, 1, 2]:
        for dy in [-2, -1, 0, 1, 2]:
            if dx != 0 or dy != 0:
                draw.text(
                    (x + dx * scale, y + dy * scale),
                    text,
                    fill=outline_color,
                )

    # 主体
    for i in range(scale):
        draw.text((x + i, y + i), text, fill=color)


# === 导出 ===

__all__ = [
    # Animation functions
    "breathing",
    "floating",
    "color_cycle",
    # Sprite classes
    "Sprite",
    "TextSprite",
    "KaomojiSprite",
    # Rendering
    "render_to_image",
]
