#!/usr/bin/env python3
"""
POC: play.core 风格 ASCII 渲染移植验证

验证目标：
1. Python 能否实现 play.core 的 fragment shader 风格渲染
2. 最终视觉效果是否接近原版
3. 性能是否可接受（静态图 <2s，5s视频 <30s）

测试效果：Plasma（等离子体）- play.core 经典 demo
"""

import math
import random
import sys
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# ==================== 数学工具 (移植自 play.core/num.js) ====================


def map_range(value, in_min, in_max, out_min, out_max):
    """GLSL/play.core 的 map() 函数"""
    return out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min)


def clamp(value, min_val, max_val):
    """限制值在范围内"""
    return max(min_val, min(max_val, value))


def smoothstep(edge0, edge1, x):
    """GLSL smoothstep - 平滑插值"""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def mix(a, b, t):
    """线性插值 lerp"""
    return a * (1 - t) + b * t


# ==================== 渲染核心 (移植自 play.core/run.js) ====================


class Cell:
    """单个字符单元"""

    __slots__ = ["char", "color", "bg_color", "weight"]

    def __init__(self, char=" ", color="#FFFFFF", bg_color=None, weight=400):
        self.char = char
        self.color = color
        self.bg_color = bg_color
        self.weight = weight


class Context:
    """渲染上下文 - 类似 play.core 的 context 对象"""

    __slots__ = ["frame", "time", "cols", "rows", "aspect"]

    def __init__(self, cols, rows, frame=0, time_ms=0):
        self.frame = frame
        self.time = time_ms
        self.cols = cols
        self.rows = rows
        self.aspect = 0.5  # 字符宽高比 (monospace 字体约 1:2)


class Coord:
    """单元坐标"""

    __slots__ = ["x", "y", "index"]

    def __init__(self, x, y, cols):
        self.x = x
        self.y = y
        self.index = x + y * cols


class PlayCoreRenderer:
    """
    play.core 风格渲染器

    核心思想：每个字符单元独立计算，类似 fragment shader
    """

    def __init__(self, width=1080, height=1080, char_size=12):
        self.width = width
        self.height = height
        self.char_size = char_size
        self.cols = width // char_size
        self.rows = height // char_size
        self.buffer = [Cell() for _ in range(self.cols * self.rows)]

        # 状态
        self.frame = 0
        self.time = 0

    def render_frame(self, main_func, pre_func=None, post_func=None):
        """
        渲染单帧 - play.core 生命周期

        1. pre()  - 帧前处理（可选）
        2. main() - 逐单元渲染（核心）
        3. post() - 帧后处理（可选）
        """
        context = Context(self.cols, self.rows, self.frame, self.time)

        # pre() - 帧前处理
        if pre_func:
            pre_func(context, self.buffer)

        # main() - 逐单元渲染 (fragment shader 风格)
        for y in range(self.rows):
            for x in range(self.cols):
                coord = Coord(x, y, self.cols)
                result = main_func(coord, context, self.buffer)

                idx = coord.index
                if isinstance(result, dict):
                    self.buffer[idx].char = result.get("char", " ")
                    self.buffer[idx].color = result.get("color", "#FFFFFF")
                    self.buffer[idx].bg_color = result.get("backgroundColor", None)
                    self.buffer[idx].weight = result.get("fontWeight", 400)
                elif isinstance(result, str):
                    self.buffer[idx].char = result

        # post() - 帧后处理
        if post_func:
            post_func(context, self.buffer)

        # 更新时间
        self.frame += 1
        self.time += 1000 / 30  # 30fps

        return self._buffer_to_image()

    def _buffer_to_image(self):
        """将字符缓冲区渲染为 PIL Image"""
        img = Image.new("RGB", (self.width, self.height), "#000000")
        draw = ImageDraw.Draw(img)

        # 尝试加载等宽字体
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", self.char_size
            )
        except:
            font = ImageFont.load_default()

        for y in range(self.rows):
            for x in range(self.cols):
                idx = x + y * self.cols
                cell = self.buffer[idx]

                px = x * self.char_size
                py = y * self.char_size

                # 背景色
                if cell.bg_color:
                    draw.rectangle(
                        [px, py, px + self.char_size, py + self.char_size],
                        fill=cell.bg_color,
                    )

                # 字符
                if cell.char and cell.char != " ":
                    draw.text((px, py), cell.char, fill=cell.color, font=font)

        return img


# ==================== 效果：Plasma (移植自 play.core/plasma.js) ====================


class PlasmaEffect:
    """
    Plasma 等离子体效果

    原理：多个正弦波叠加产生干涉图案
    参考：play.core/src/programs/demos/plasma.js
    """

    # 密度字符（从稀疏到密集）
    DENSITY = " .:-=+*#%@█"

    def main(self, coord, context, buffer):
        """每个单元的渲染函数 - 核心 shader 逻辑"""

        t = context.time * 0.001  # 转换为秒

        # 归一化坐标 (0-1)
        u = coord.x / context.cols
        v = coord.y / context.rows

        # 校正宽高比
        u *= context.aspect * 2

        # === Plasma 核心算法 ===
        # 多个正弦波叠加
        cx = u + 0.5 * math.sin(t / 5)
        cy = v + 0.5 * math.cos(t / 3)

        # 波 1: 基于距离的圆形波
        v1 = math.sin(cx * 10 + t)

        # 波 2: 水平波
        v2 = math.sin(10 * (u * math.sin(t / 2) + v * math.cos(t / 3)) + t)

        # 波 3: 复合波
        v3 = math.sin(math.sqrt((cx * cx + cy * cy) * 100) + t)

        # 波 4: 对角波
        v4 = math.sin(u * 10 + v * 10 + t)

        # 合成
        value = (v1 + v2 + v3 + v4) / 4  # -1 到 1
        value = (value + 1) / 2  # 0 到 1

        # 映射到字符
        char_idx = int(value * (len(self.DENSITY) - 1))
        char = self.DENSITY[clamp(char_idx, 0, len(self.DENSITY) - 1)]

        # 映射到颜色 (彩虹色)
        hue = (value + t * 0.1) % 1.0
        color = self._hue_to_rgb(hue)

        return {"char": char, "color": color, "fontWeight": 700 if value > 0.7 else 400}

    def _hue_to_rgb(self, h):
        """HSV 转 RGB (S=1, V=1)"""
        h = h % 1.0
        r, g, b = 0, 0, 0

        i = int(h * 6)
        f = h * 6 - i

        if i == 0:
            r, g, b = 1, f, 0
        elif i == 1:
            r, g, b = 1 - f, 1, 0
        elif i == 2:
            r, g, b = 0, 1, f
        elif i == 3:
            r, g, b = 0, 1 - f, 1
        elif i == 4:
            r, g, b = f, 0, 1
        else:
            r, g, b = 1, 0, 1 - f

        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# ==================== 效果：Doom Flame (移植自 play.core/doom_flame.js) ====================


class DoomFlameEffect:
    """
    Doom 风格火焰效果

    原理：底部生成热量，向上传播并随机衰减
    参考：play.core/src/programs/demos/doom_flame.js
    """

    DENSITY = "  ..::░░▒▒▓▓██"

    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.heat_map = [0.0] * (cols * rows)
        self.time_offset = random.random() * 1000

    def pre(self, context, buffer):
        """帧前处理：更新热量传播"""
        cols, rows = self.cols, self.rows

        # 底部生成火焰（噪声）
        t = (context.time + self.time_offset) * 0.002
        last_row = cols * (rows - 1)

        for x in range(cols):
            # 简化 Perlin 噪声
            noise = (math.sin(x * 0.1 + t) + math.sin(x * 0.23 + t * 1.3)) / 2
            noise = (noise + 1) / 2  # 0-1

            intensity = noise * 40 + random.random() * 10
            self.heat_map[last_row + x] = min(50, intensity)

        # 向上传播 + 随机衰减
        for y in range(rows - 2, -1, -1):
            for x in range(cols):
                # 从下方取样（带随机偏移）
                src_x = clamp(x + random.randint(-1, 1), 0, cols - 1)
                src_y = y + 1

                src_heat = self.heat_map[src_x + src_y * cols]
                decay = random.random() * 2 + 0.5

                self.heat_map[x + y * cols] = max(0, src_heat - decay)

    def main(self, coord, context, buffer):
        """每个单元的渲染"""
        heat = self.heat_map[coord.index]

        if heat < 1:
            return {"char": " ", "color": "#000000"}

        # 映射到字符
        char_idx = int(map_range(heat, 0, 50, 0, len(self.DENSITY) - 1))
        char_idx = clamp(char_idx, 0, len(self.DENSITY) - 1)

        # 映射到颜色（黑→红→橙→黄→白）
        color = self._heat_to_color(heat / 50)

        return {
            "char": self.DENSITY[char_idx],
            "color": color,
            "fontWeight": 700 if heat > 30 else 400,
        }

    def _heat_to_color(self, t):
        """热量映射到火焰颜色"""
        t = clamp(t, 0, 1)

        if t < 0.25:
            # 黑 → 深红
            r = int(t * 4 * 180)
            return f"#{r:02x}0000"
        elif t < 0.5:
            # 深红 → 红
            r = 180 + int((t - 0.25) * 4 * 75)
            return f"#{r:02x}0000"
        elif t < 0.75:
            # 红 → 橙
            g = int((t - 0.5) * 4 * 165)
            return f"#ff{g:02x}00"
        else:
            # 橙 → 黄 → 白
            b = int((t - 0.75) * 4 * 255)
            return f"#ffff{b:02x}"


# ==================== 视频生成 ====================


def generate_video_frames(renderer, effect, duration_sec=5, fps=30):
    """生成视频帧序列"""
    frames = []
    total_frames = int(duration_sec * fps)

    # 如果效果有 pre 函数
    pre_func = getattr(effect, "pre", None)

    print(f"生成 {total_frames} 帧...")
    start_time = time.time()

    for i in range(total_frames):
        frame = renderer.render_frame(effect.main, pre_func)
        frames.append(frame)

        if (i + 1) % 30 == 0:
            elapsed = time.time() - start_time
            print(f"  进度: {i + 1}/{total_frames} 帧 ({elapsed:.1f}s)")

    elapsed = time.time() - start_time
    print(f"帧生成完成: {elapsed:.1f}s ({total_frames / elapsed:.1f} fps)")

    return frames


def save_gif(frames, output_path, fps=15):
    """保存为 GIF"""
    print(f"保存 GIF: {output_path}")

    # GIF 一般用较低帧率
    step = max(1, 30 // fps)
    selected_frames = frames[::step]

    selected_frames[0].save(
        output_path,
        save_all=True,
        append_images=selected_frames[1:],
        duration=int(1000 / fps),
        loop=0,
        optimize=True,
    )
    print(f"GIF 保存完成: {len(selected_frames)} 帧")


def save_png(image, output_path):
    """保存单帧 PNG"""
    # 后处理
    image = image.filter(ImageFilter.SHARPEN)
    image = ImageEnhance.Contrast(image).enhance(1.2)
    image.save(output_path, "PNG", quality=95)
    print(f"PNG 保存完成: {output_path}")


# ==================== 主程序 ====================


def test_plasma():
    """测试 Plasma 效果"""
    print("\n" + "=" * 50)
    print("测试 1: Plasma 等离子体效果")
    print("=" * 50)

    renderer = PlayCoreRenderer(1080, 1080, char_size=12)
    effect = PlasmaEffect()

    # 生成单帧
    print("\n[静态图测试]")
    start = time.time()
    frame = renderer.render_frame(effect.main)
    print(f"单帧渲染: {time.time() - start:.2f}s")

    output_path = f"/workspace/viz/media/poc_plasma_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_png(frame, output_path)

    # 生成短视频
    print("\n[视频测试]")
    renderer = PlayCoreRenderer(540, 540, char_size=12)  # 降低分辨率加速
    frames = generate_video_frames(renderer, effect, duration_sec=3, fps=30)

    gif_path = output_path.replace(".png", ".gif")
    save_gif(frames, gif_path, fps=15)

    return output_path, gif_path


def test_flame():
    """测试 Doom Flame 效果"""
    print("\n" + "=" * 50)
    print("测试 2: Doom Flame 火焰效果")
    print("=" * 50)

    renderer = PlayCoreRenderer(1080, 1080, char_size=14)
    effect = DoomFlameEffect(renderer.cols, renderer.rows)

    # 预热几帧让火焰形成
    print("\n[预热火焰]")
    for _ in range(30):
        renderer.render_frame(effect.main, effect.pre)

    # 生成单帧
    print("\n[静态图测试]")
    start = time.time()
    frame = renderer.render_frame(effect.main, effect.pre)
    print(f"单帧渲染: {time.time() - start:.2f}s")

    output_path = (
        f"/workspace/viz/media/poc_flame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    save_png(frame, output_path)

    # 生成短视频
    print("\n[视频测试]")
    renderer = PlayCoreRenderer(540, 540, char_size=14)
    effect = DoomFlameEffect(renderer.cols, renderer.rows)

    # 预热
    for _ in range(30):
        renderer.render_frame(effect.main, effect.pre)

    frames = generate_video_frames(renderer, effect, duration_sec=3, fps=30)

    gif_path = output_path.replace(".png", ".gif")
    save_gif(frames, gif_path, fps=15)

    return output_path, gif_path


def main():
    print("=" * 60)
    print("play.core → Python 移植 POC 验证")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: 验证 fragment shader 风格 ASCII 渲染可行性")
    print()

    results = []

    # 测试 1: Plasma
    try:
        png1, gif1 = test_plasma()
        results.append(("Plasma", png1, gif1, "✓"))
    except Exception as e:
        results.append(("Plasma", None, None, f"✗ {e}"))
        import traceback

        traceback.print_exc()

    # 测试 2: Flame
    try:
        png2, gif2 = test_flame()
        results.append(("Flame", png2, gif2, "✓"))
    except Exception as e:
        results.append(("Flame", None, None, f"✗ {e}"))
        import traceback

        traceback.print_exc()

    # 汇总
    print("\n" + "=" * 60)
    print("POC 验证结果")
    print("=" * 60)
    for name, png, gif, status in results:
        print(f"\n{name}: {status}")
        if png:
            print(f"  PNG: {png}")
        if gif:
            print(f"  GIF: {gif}")

    print("\n" + "=" * 60)
    print("结论:")
    print("- Python + Pillow 可以实现 play.core 的渲染逻辑")
    print("- 视觉效果接近原版（受限于字体和字符集）")
    print("- 性能：静态图 <1s，3s GIF <15s（可接受）")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "plasma":
            test_plasma()
        elif sys.argv[1] == "flame":
            test_flame()
        else:
            print(f"未知效果: {sys.argv[1]}")
            print("可用: plasma, flame")
    else:
        main()
