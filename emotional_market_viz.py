#!/usr/bin/env python3
"""
Emotional Market Visualization
情绪化的市场数据可视化生成器

设计原则：
1. 强烈的色彩对比 - 传达紧迫感或喜悦感
2. 大胆的排版 - 层次分明的信息架构
3. 动态感 - 通过重复、渐变、故障效果
4. 符号语言 - ASCII 艺术与数据结合
5. 空间留白 - 突出核心信息

参考：Affective Visualization Design + ASCII Art Best Practices
"""

import argparse
import math
import random
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

try:
    from lib.kaomoji import draw_kaomoji
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji

from procedural.engine import Engine
from procedural.effects import get_effect
from procedural.layers import KaomojiSprite, TextSprite

# ========== 配色方案（基于情绪心理学）==========
COLOR_SCHEMES = {
    "euphoria": {  # 狂喜 - 强劲上涨
        "bg": ["#000000", "#0a0000"],
        "primary": "#00ff00",  # 纯绿 - 生命力
        "secondary": "#00ff88",  # 青绿 - 希望
        "accent": "#ffff00",  # 黄色 - 兴奋
        "glow": "#88ff88",  # 发光效果
        "emotion": "BULLISH 🚀",
    },
    "excitement": {  # 兴奋 - 温和上涨
        "bg": ["#001a00", "#002000"],
        "primary": "#00ff41",
        "secondary": "#00cc33",
        "accent": "#ffffff",
        "glow": "#00ff88",
        "emotion": "UP ↑",
    },
    "anxiety": {  # 焦虑 - 震荡
        "bg": ["#1a1a00", "#1a1200"],
        "primary": "#ffaa00",
        "secondary": "#ff8800",
        "accent": "#ffffff",
        "glow": "#ffcc66",
        "emotion": "VOLATILE ⚡",
    },
    "fear": {  # 恐惧 - 下跌
        "bg": ["#1a0000", "#2a0000"],
        "primary": "#ff0000",
        "secondary": "#cc0000",
        "accent": "#ffffff",
        "glow": "#ff6666",
        "emotion": "DOWN ↓",
    },
    "panic": {  # 恐慌 - 暴跌
        "bg": ["#000000", "#100000"],
        "primary": "#ff0033",
        "secondary": "#ff0066",
        "accent": "#ff99aa",
        "glow": "#ff3366",
        "emotion": "CRASH ⚠️",
    },
}

# ========== ASCII 密度字符（优化对比度）==========
ASCII_GRADIENT = " .':;!>+*%@#█"  # 稀疏到密集

# ========== ASCII 大型符号（情绪化）==========
ASCII_SYMBOLS = {
    "rocket": [
        "    /\\    ",
        "   /  \\   ",
        "  | ** |  ",
        "  |/**\\|  ",
        " /______\\ ",
        "  |    |  ",
        "  |    |  ",
        " /|    |\\ ",
        " |      | ",
        " \\______/ ",
    ],
    "arrow_up": [
        "      ╱╲      ",
        "     ╱  ╲     ",
        "    ╱    ╲    ",
        "   ╱  UP  ╲   ",
        "  ╱        ╲  ",
        " ╱__________╲ ",
        "     ║║║║     ",
        "     ║║║║     ",
        "     ████     ",
    ],
    "arrow_down": [
        "     ████     ",
        "     ║║║║     ",
        "     ║║║║     ",
        " \\‾‾‾‾‾‾‾‾‾‾/ ",
        "  \\  DOWN  /  ",
        "   \\      /   ",
        "    \\    /    ",
        "     \\  /     ",
        "      \\/      ",
    ],
    "chart_rise": [
        "         ██   ",
        "      ██ ██   ",
        "   ██ ██ ██   ",
        "██ ██ ██ ██   ",
    ],
    "chart_fall": [
        "██             ",
        "██ ██          ",
        "██ ██ ██       ",
        "██ ██ ██ ██    ",
    ],
    "happy_face": [
        "  ########  ",
        " ##  ##  ## ",
        "##  ####  ##",
        "##        ##",
        "##  ####  ##",
        " ##  ##  ## ",
        "  ########  ",
    ],
    "sad_face": [
        "  ########  ",
        " ##  ##  ## ",
        "##  ####  ##",
        "##        ##",
        "##  ####  ##",
        " ##      ## ",
        "  ########  ",
    ],
}


def draw_glow_text(draw, x, y, text, color, glow_color, size=1):
    """绘制发光文字效果"""
    # 外发光（多层）
    for offset in range(size + 3, 0, -1):
        alpha = int(100 - offset * 20)
        if alpha > 0:
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, fill=glow_color)

    # 主体文字（加粗）
    for dx in range(size):
        for dy in range(size):
            draw.text((x + dx, y + dy), text, fill=color)


def draw_ascii_symbol(draw, x, y, symbol_lines, color, scale=1):
    """绘制 ASCII 符号"""
    for i, line in enumerate(symbol_lines):
        line_y = y + i * 16 * scale
        for dx in range(scale):
            for dy in range(scale):
                draw.text((x + dx, line_y + dy), line, fill=color)


def create_data_particles(draw, width, height, color, density=50, chars=None, rng=None):
    """创建数据粒子背景（动态感）"""
    if chars is None:
        chars = "0123456789.,:;-+*"
    if rng is None:
        rng = random
    for _ in range(density):
        x = rng.randint(0, width)
        y = rng.randint(0, height)
        char = rng.choice(chars)
        size = rng.randint(1, 3)

        for dx in range(size):
            for dy in range(size):
                draw.text((x + dx, y + dy), char, fill=color)


def create_energy_waves(
    draw, width, height, color, wave_count=5, center=None, radius_step=80, rng=None
):
    """创建能量波纹（视觉动态）"""
    if rng is None:
        rng = random
    if center is None:
        center_x, center_y = width // 2, height // 2
    else:
        center_x, center_y = center

    for wave_idx in range(wave_count):
        radius = 100 + wave_idx * radius_step
        segments = 60

        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            x1 = center_x + int(math.cos(angle) * radius)
            y1 = center_y + int(math.sin(angle) * radius)

            angle2 = ((i + 1) / segments) * 2 * math.pi
            x2 = center_x + int(math.cos(angle2) * radius)
            y2 = center_y + int(math.sin(angle2) * radius)

            # 随机断续效果
            if rng.random() > 0.3:
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)


def _draw_ascii_texture(draw, rng, width, height, colors, density=0.35):
    """绘制 ASCII 纹理层"""
    cell = rng.choice([18, 22, 26, 30])
    text_color = colors.get("secondary", colors["primary"])
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if rng.random() < density:
                char = ASCII_GRADIENT[int(rng.random() * (len(ASCII_GRADIENT) - 1))]
                draw.text((x, y), char, fill=text_color)


def _scatter_kaomoji(draw, rng, width, height, colors, mood, exclude_box=None):
    """散布小型颜文字以强化 ASCII 属性"""
    count = rng.randint(6, 14)
    for _ in range(count):
        x = rng.randint(40, width - 200)
        y = rng.randint(40, height - 200)
        if exclude_box:
            box_x, box_y, box_w, box_h = exclude_box
            if (
                box_x - 60 <= x <= box_x + box_w + 60
                and box_y - 60 <= y <= box_y + box_h + 60
            ):
                continue
        size = rng.randint(2, 5)
        draw_kaomoji(
            draw,
            x,
            y,
            mood,
            color=colors["secondary"],
            outline_color=colors.get("glow", colors["primary"]),
            size=size,
            rng=rng,
        )


def _render_procedural_background(effect_name, seed, size, blend_color):
    """渲染 procedural 背景 (静态)"""
    if not effect_name:
        return None

    from procedural.engine import Engine
    from procedural.effects import get_effect

    rng = random.Random(seed)
    engine = Engine(internal_size=(160, 160), output_size=size, contrast=1.2)
    effect = get_effect(effect_name)
    frame = engine.render_frame(effect, time=rng.random() * 6.0, seed=seed)

    overlay = Image.new("RGB", size, blend_color)
    frame = Image.blend(frame, overlay, 0.4)

    return frame


def generate_emotional_viz(market_data, output_path):
    """
    生成情绪化市场可视化

    market_data = {
        'emotion': 'euphoria' | 'excitement' | 'anxiety' | 'fear' | 'panic',
        'headline': '主标题',
        'metrics': ['指标1', '指标2', '指标3'],
        'timestamp': '时间',
        'change_pct': +2.5 (百分比变化)
    }
    """
    WIDTH, HEIGHT = 1080, 1080

    emotion = market_data.get("emotion", "excitement")
    colors = COLOR_SCHEMES[emotion]

    seed = market_data.get("seed")
    if seed is None:
        seed = random.randint(0, 999999)
    rng = random.Random(seed)

    effect_map = {
        "euphoria": "plasma",
        "excitement": "moire",
        "anxiety": "noise_field",
        "fear": "wave",
        "panic": "flame",
    }
    effect_name = market_data.get("effect") or effect_map.get(emotion, "plasma")

    layouts = [
        {
            "box_w": 800,
            "box_h": 500,
            "box_x": (WIDTH - 800) // 2,
            "box_y": (HEIGHT - 500) // 2,
            "badge": (WIDTH - 250, 50),
            "symbol_a": (80, 80),
            "symbol_b": (WIDTH - 300, HEIGHT - 300),
        },
        {
            "box_w": 720,
            "box_h": 460,
            "box_x": 120,
            "box_y": 220,
            "badge": (WIDTH - 260, 80),
            "symbol_a": (WIDTH - 320, 80),
            "symbol_b": (80, HEIGHT - 320),
        },
        {
            "box_w": 760,
            "box_h": 520,
            "box_x": (WIDTH - 760) // 2,
            "box_y": 160,
            "badge": (WIDTH - 240, 70),
            "symbol_a": (60, 120),
            "symbol_b": (WIDTH - 360, HEIGHT - 260),
        },
        # New Layout 1: Bottom Heavy
        {
            "box_w": 900,
            "box_h": 400,
            "box_x": (WIDTH - 900) // 2,
            "box_y": HEIGHT - 450,
            "badge": (WIDTH - 200, 50),
            "symbol_a": (100, 100),
            "symbol_b": (WIDTH - 250, 150),
        },
        # New Layout 2: Top Heavy
        {
            "box_w": 850,
            "box_h": 450,
            "box_x": (WIDTH - 850) // 2,
            "box_y": 100,
            "badge": (WIDTH - 200, HEIGHT - 200),
            "symbol_a": (100, HEIGHT - 250),
            "symbol_b": (WIDTH - 300, HEIGHT - 300),
        },
        # New Layout 3: Asymmetric Left
        {
            "box_w": 600,
            "box_h": 800,
            "box_x": 50,
            "box_y": (HEIGHT - 800) // 2,
            "badge": (WIDTH - 250, 100),
            "symbol_a": (WIDTH - 300, 300),
            "symbol_b": (WIDTH - 300, 600),
        },
        # New Layout 4: Left Column
        {
            "box_w": 520,
            "box_h": 900,
            "box_x": 80,
            "box_y": 90,
            "badge": (WIDTH - 220, HEIGHT - 220),
            "symbol_a": (WIDTH - 320, 120),
            "symbol_b": (WIDTH - 320, HEIGHT - 260),
        },
        # New Layout 5: Right Column
        {
            "box_w": 520,
            "box_h": 900,
            "box_x": WIDTH - 600,
            "box_y": 90,
            "badge": (120, HEIGHT - 220),
            "symbol_a": (120, 120),
            "symbol_b": (120, HEIGHT - 260),
        },
    ]
    layout = rng.choice(layouts)

    # 创建基础图像 (procedural 背景 + 叠色)
    bg_gradient = colors["bg"]
    img = _render_procedural_background(
        effect_name, seed, (WIDTH, HEIGHT), bg_gradient[0]
    )
    if img is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), bg_gradient[0])

    draw = ImageDraw.Draw(img)

    # === 1. 背景渐变 ===
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        # 简单的垂直渐变
        if rng.random() > 0.95:  # 5% 噪点
            color = colors["primary"]
            draw.point((rng.randint(0, WIDTH), y), fill=color)

    # === 2. 能量波纹（根据情绪强度）===
    wave_center = (
        WIDTH // 2 + rng.randint(-120, 120),
        HEIGHT // 2 + rng.randint(-120, 120),
    )
    wave_count = rng.randint(4, 9)
    wave_step = rng.choice([60, 80, 100])
    if emotion in ["euphoria", "panic"]:
        create_energy_waves(
            draw,
            WIDTH,
            HEIGHT,
            colors["glow"],
            wave_count=wave_count,
            center=wave_center,
            radius_step=wave_step,
            rng=rng,
        )
    elif emotion in ["excitement", "fear"]:
        create_energy_waves(
            draw,
            WIDTH,
            HEIGHT,
            colors["secondary"],
            wave_count=wave_count,
            center=wave_center,
            radius_step=wave_step,
            rng=rng,
        )

    # === 3. 数据粒子背景 ===
    particle_chars = rng.choice(["0123456789", ".:;*", "<>/\\", "[]{}"])
    particle_density = rng.randint(60, 120)
    create_data_particles(
        draw,
        WIDTH,
        HEIGHT,
        colors["secondary"],
        density=particle_density,
        chars=particle_chars,
        rng=rng,
    )

    # === 4. ASCII 纹理层 ===
    _draw_ascii_texture(
        draw, rng, WIDTH, HEIGHT, colors, density=rng.uniform(0.25, 0.45)
    )

    # === 3.5. Kaomoji Particles (Richer Expression) ===
    kaomoji_count = rng.randint(3, 6)
    for _ in range(kaomoji_count):
        kx = rng.randint(50, WIDTH - 100)
        ky = rng.randint(50, HEIGHT - 100)

        # Avoid center box area roughly
        if (
            layout["box_x"] - 100 < kx < layout["box_x"] + layout["box_w"] + 100
            and layout["box_y"] - 100 < ky < layout["box_y"] + layout["box_h"] + 100
        ):
            continue

        k_size = rng.randint(1, 3)
        k_mood = emotion
        if rng.random() > 0.7:
            k_mood = "neutral"

        draw_kaomoji(
            draw,
            kx,
            ky,
            k_mood,
            color=colors["secondary"],
            outline_color=colors["dim"] if "dim" in colors else colors["bg"][0],
            size=k_size,
            rng=rng,
        )

    # === 4. 主视觉符号（左上右下对角）===
    if emotion in ["euphoria", "excitement"]:
        symbol = "rocket" if emotion == "euphoria" else "arrow_up"
        draw_ascii_symbol(
            draw,
            layout["symbol_a"][0],
            layout["symbol_a"][1],
            ASCII_SYMBOLS[symbol],
            colors["primary"],
            scale=2,
        )
        draw_ascii_symbol(
            draw,
            layout["symbol_b"][0],
            layout["symbol_b"][1],
            ASCII_SYMBOLS["chart_rise"],
            colors["accent"],
            scale=3,
        )
    elif emotion in ["fear", "panic"]:
        symbol = "arrow_down"
        draw_ascii_symbol(
            draw,
            layout["symbol_a"][0],
            layout["symbol_a"][1],
            ASCII_SYMBOLS[symbol],
            colors["primary"],
            scale=2,
        )
        draw_ascii_symbol(
            draw,
            layout["symbol_b"][0],
            layout["symbol_b"][1],
            ASCII_SYMBOLS["chart_fall"],
            colors["accent"],
            scale=3,
        )

    # === 5. 中央信息区（极简黑盒）===
    box_w, box_h = layout["box_w"], layout["box_h"]
    box_x, box_y = layout["box_x"], layout["box_y"]

    # === 4.5 背景颜文字散布 ===
    _scatter_kaomoji(
        draw,
        rng,
        WIDTH,
        HEIGHT,
        colors,
        emotion,
        exclude_box=(box_x, box_y, box_w, box_h),
    )

    # 黑色背景 + 发光边框
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill="#000000")

    for i in range(5):
        draw.rectangle(
            [box_x - i, box_y - i, box_x + box_w + i, box_y + box_h + i],
            outline=colors["glow"] if i < 2 else colors["primary"],
            width=2,
        )

    # ASCII 边框增强
    for x in range(box_x + 10, box_x + box_w - 10, 20):
        draw.text((x, box_y - 18), "-", fill=colors["secondary"])
        draw.text((x, box_y + box_h + 4), "-", fill=colors["secondary"])
    for y in range(box_y + 10, box_y + box_h - 10, 20):
        draw.text((box_x - 18, y), "|", fill=colors["secondary"])
        draw.text((box_x + box_w + 6, y), "|", fill=colors["secondary"])

    # === 6. 核心信息排版 ===
    text_x = box_x + 50
    text_y = box_y + 40

    # 顶部标签（情绪标识）
    emotion_label = colors["emotion"]
    draw_glow_text(
        draw, text_x, text_y, emotion_label, colors["accent"], colors["glow"], size=4
    )

    # 分隔线
    text_y += 60
    for i in range(70):
        draw.text((text_x + i * 10, text_y), "═", fill=colors["secondary"])

    # 关键指标（大字）
    text_y += 40
    metrics = market_data.get("metrics", [])
    for idx, metric in enumerate(metrics[:3]):
        y_pos = text_y + idx * 90
        draw_glow_text(
            draw, text_x, y_pos, metric, colors["primary"], colors["glow"], size=12
        )

    # 主标题（超大）
    headline = market_data.get("headline", "MARKET")
    title_y = text_y + 320
    draw_glow_text(
        draw, text_x, title_y, headline, colors["accent"], colors["glow"], size=18
    )

    # 时间戳
    timestamp = market_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M"))
    ts_y = title_y + 70
    for dx in range(3):
        for dy in range(3):
            draw.text((text_x + dx, ts_y + dy), timestamp, fill=colors["secondary"])

    # === 7. 变化百分比（角标）===
    change_pct = market_data.get("change_pct", 0)
    change_text = f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%"
    badge_x, badge_y = layout["badge"]

    # 徽章背景
    draw.ellipse(
        [badge_x, badge_y, badge_x + 180, badge_y + 180],
        fill=colors["primary"],
        outline=colors["glow"],
        width=5,
    )

    # 徽章文字
    for dx in range(10):
        for dy in range(10):
            draw.text(
                (badge_x + 30 + dx, badge_y + 70 + dy), change_text, fill="#000000"
            )

    # === 8. 后期处理：对比度增强 + 锐化 ===
    img = img.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)

    # === 9. 故障效果（情绪张力）===
    if emotion in ["euphoria", "panic"]:
        pixels = img.load()
        glitch_intensity = 200 if emotion == "panic" else 150

        for _ in range(glitch_intensity):
            x = rng.randint(0, WIDTH - 80)
            y = rng.randint(0, HEIGHT - 1)
            w = rng.randint(20, 100)
            shift = rng.randint(-12, 12)

            for i in range(w):
                if x + i < WIDTH and 0 <= (y + shift) < HEIGHT:
                    try:
                        pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
                    except:
                        pass

    # 保存
    img.save(output_path, "PNG", quality=95)
    print(f"✓ 生成完成: {output_path}")
    print(f"  情绪: {emotion} ({colors['emotion']})")
    print(f"  主题色: {colors['primary']}")
    print(f"  变化: {change_pct:+.2f}%")

    return output_path


def _generate_video(static_path, args, market_data=None):
    """
    使用 procedural Engine + sprites 生成 GIF 视频
    Use procedural Engine with KaomojiSprite/TextSprite for animated GIF
    """
    if market_data is None:
        market_data = {}

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    rng = random.Random(seed)

    # === 配置 ===
    emotion = market_data.get("emotion", "excitement")
    colors = COLOR_SCHEMES.get(emotion, COLOR_SCHEMES["excitement"])

    effect_map = {
        "euphoria": "plasma",
        "excitement": "moire",
        "anxiety": "noise_field",
        "fear": "wave",
        "panic": "flame",
    }
    effect_name = market_data.get("effect") or effect_map.get(emotion, "plasma")

    # === 坐标缩放 (1080 → 160) ===
    INTERNAL = 160
    OUTPUT = 1080
    scale_factor = INTERNAL / OUTPUT

    # === 选择布局 ===
    layouts = [
        {
            "box_w": 800,
            "box_h": 500,
            "box_x": (OUTPUT - 800) // 2,
            "box_y": (OUTPUT - 500) // 2,
            "badge": (OUTPUT - 250, 50),
            "symbol_a": (80, 80),
            "symbol_b": (OUTPUT - 300, OUTPUT - 300),
        },
        {
            "box_w": 720,
            "box_h": 460,
            "box_x": 120,
            "box_y": 220,
            "badge": (OUTPUT - 260, 80),
            "symbol_a": (OUTPUT - 320, 80),
            "symbol_b": (80, OUTPUT - 320),
        },
        {
            "box_w": 760,
            "box_h": 520,
            "box_x": (OUTPUT - 760) // 2,
            "box_y": 160,
            "badge": (OUTPUT - 240, 70),
            "symbol_a": (60, 120),
            "symbol_b": (OUTPUT - 360, OUTPUT - 260),
        },
    ]
    layout = rng.choice(layouts)

    # === 情绪到心情映射 ===
    emotion_moods = {
        "euphoria": ["^_^", "excited", "\\o/", "happy", "*_*"],
        "excitement": ["^_^", "excited", "happy", "love"],
        "anxiety": ["o_o", "-_-", "thinking", "?"],
        "fear": ["T_T", "sad", "cry", ">_<"],
        "panic": ["x_x", "T_T", "cry", "sad", ">_<"],
    }
    moods_list = emotion_moods.get(emotion, ["o_o", "^_^"])

    # === 创建 KaomojiSprite 列表 ===
    sprites = []

    # 散布情绪颜文字 (带浮动动画)
    kaomoji_positions = [
        layout["symbol_a"],
        layout["symbol_b"],
        (layout["badge"][0] - 100, layout["badge"][1] + 200),
        (rng.randint(60, 300), rng.randint(600, 900)),
        (rng.randint(700, 950), rng.randint(100, 400)),
        (rng.randint(400, 700), rng.randint(50, 200)),
    ]

    for idx, (x, y) in enumerate(kaomoji_positions):
        mood = moods_list[idx % len(moods_list)]
        phase = idx * 0.8
        k_size = rng.randint(80, 140)
        # 极端情绪用更强动画
        float_amp = 5.0 if emotion in ["euphoria", "panic"] else 3.0
        breath_amp = 0.15 if emotion in ["euphoria", "panic"] else 0.08

        sprite = KaomojiSprite(
            mood,
            x=x * scale_factor,
            y=y * scale_factor,
            color=colors["primary"],
            outline_color=colors.get("glow", colors["secondary"]),
            scale=max(1, int(k_size * scale_factor)),
            animations=[
                {
                    "type": "floating",
                    "amp": float_amp,
                    "speed": 0.8 + idx * 0.1,
                    "phase": phase,
                },
                {"type": "breathing", "amp": breath_amp, "speed": 1.5},
            ],
        )
        sprites.append(sprite)

    # 散布小颜文字 (背景装饰)
    scatter_count = rng.randint(4, 8)
    for i in range(scatter_count):
        sx = rng.randint(40, OUTPUT - 200)
        sy = rng.randint(40, OUTPUT - 200)
        # 避开中央信息区
        bx, by, bw, bh = (
            layout["box_x"],
            layout["box_y"],
            layout["box_w"],
            layout["box_h"],
        )
        if bx - 60 <= sx <= bx + bw + 60 and by - 60 <= sy <= by + bh + 60:
            continue
        mood = rng.choice(moods_list)
        sprites.append(
            KaomojiSprite(
                mood,
                x=sx * scale_factor,
                y=sy * scale_factor,
                color=colors["secondary"],
                outline_color=colors.get("glow", colors["primary"]),
                scale=max(1, int(rng.randint(2, 5) * scale_factor)),
                animations=[
                    {"type": "floating", "amp": 2.0, "speed": 0.5, "phase": i * 1.2},
                ],
            )
        )

    # === 文字精灵 ===
    # 情绪标签
    emotion_label = colors["emotion"]
    sprites.append(
        TextSprite(
            emotion_label,
            x=(layout["box_x"] + 50) * scale_factor,
            y=(layout["box_y"] + 40) * scale_factor,
            color=colors["accent"],
            glow_color=colors["glow"],
            glow_size=2,
            animations=[
                {"type": "breathing", "amp": 0.06, "speed": 1.0},
            ],
        )
    )

    # 标题
    headline = market_data.get("headline", "MARKET")
    sprites.append(
        TextSprite(
            headline,
            x=(layout["box_x"] + 50) * scale_factor,
            y=(layout["box_y"] + 360) * scale_factor,
            color=colors["accent"],
            glow_color=colors["glow"],
            glow_size=3,
            animations=[
                {"type": "breathing", "amp": 0.05, "speed": 1.2},
            ],
        )
    )

    # 关键指标
    metrics = market_data.get("metrics", [])
    for idx, metric in enumerate(metrics[:3]):
        sprites.append(
            TextSprite(
                metric,
                x=(layout["box_x"] + 50) * scale_factor,
                y=(layout["box_y"] + 140 + idx * 70) * scale_factor,
                color=colors["primary"],
                glow_color=colors["glow"],
                glow_size=2,
            )
        )

    # 时间戳
    timestamp = market_data.get("timestamp", datetime.now().strftime("%b %d, %Y"))
    sprites.append(
        TextSprite(
            timestamp,
            x=(layout["box_x"] + 50) * scale_factor,
            y=(layout["box_y"] + 430) * scale_factor,
            color=colors["secondary"],
            glow_size=1,
        )
    )

    # 百分比变化
    change_pct = market_data.get("change_pct", 0)
    change_text = f"{'+' if change_pct > 0 else ''}{change_pct:.2f}%"
    sprites.append(
        TextSprite(
            change_text,
            x=layout["badge"][0] * scale_factor,
            y=layout["badge"][1] * scale_factor,
            color=colors["primary"],
            glow_color=colors["glow"],
            glow_size=2,
            animations=[
                {"type": "breathing", "amp": 0.10, "speed": 2.0},
            ],
        )
    )

    # === 渲染 ===
    engine = Engine(internal_size=(INTERNAL, INTERNAL), output_size=(OUTPUT, OUTPUT))
    effect = get_effect(effect_name)
    frames = engine.render_video(
        effect, duration=args.duration, fps=args.fps, sprites=sprites, seed=seed
    )

    gif_path = static_path.replace(".png", ".gif")
    engine.save_gif(frames, gif_path, fps=args.fps)
    return gif_path


def build_parser():
    parser = argparse.ArgumentParser(
        description="Emotional Market Visualization - 情绪化市场可视化",
    )
    parser.add_argument(
        "emotion",
        nargs="?",
        default="excitement",
        choices=["euphoria", "excitement", "anxiety", "fear", "panic"],
        help="情绪状态 (默认 excitement)",
    )
    parser.add_argument("--video", action="store_true", help="输出 GIF 视频")
    parser.add_argument("--duration", type=float, default=5.0, help="视频时长 (秒)")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--effect", default="plasma", help="视频效果 (默认 plasma)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()

    emotion = args.emotion

    market_data = {
        "emotion": emotion,
        "headline": "REBOUND",
        "metrics": ["DOW +0.6%", "PMI 52.6", "NASDAQ HIGH"],
        "timestamp": datetime.now().strftime("%b %d, %Y"),
        "change_pct": 0.6,
        "seed": args.seed,
        "effect": args.effect,
    }

    output = (
        f"media/emotional_viz_{emotion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    generate_emotional_viz(market_data, output)

    if args.video:
        print("🎬 生成视频...")
        output = _generate_video(output, args, market_data)
        print(f"📁 视频: {output}")
