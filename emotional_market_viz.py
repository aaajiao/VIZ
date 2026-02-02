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


def create_data_particles(draw, width, height, color, density=50):
    """创建数据粒子背景（动态感）"""
    chars = "0123456789.,:;-+*"
    for _ in range(density):
        x = random.randint(0, width)
        y = random.randint(0, height)
        char = random.choice(chars)
        size = random.randint(1, 3)

        for dx in range(size):
            for dy in range(size):
                draw.text((x + dx, y + dy), char, fill=color)


def create_energy_waves(draw, width, height, color, wave_count=5):
    """创建能量波纹（视觉动态）"""
    center_x, center_y = width // 2, height // 2

    for wave_idx in range(wave_count):
        radius = 100 + wave_idx * 80
        segments = 60

        for i in range(segments):
            angle = (i / segments) * 2 * math.pi
            x1 = center_x + int(math.cos(angle) * radius)
            y1 = center_y + int(math.sin(angle) * radius)

            angle2 = ((i + 1) / segments) * 2 * math.pi
            x2 = center_x + int(math.cos(angle2) * radius)
            y2 = center_y + int(math.sin(angle2) * radius)

            # 随机断续效果
            if random.random() > 0.3:
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)


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

    # 创建基础图像
    bg_gradient = colors["bg"]
    img = Image.new("RGB", (WIDTH, HEIGHT), bg_gradient[0])
    draw = ImageDraw.Draw(img)

    # === 1. 背景渐变 ===
    for y in range(HEIGHT):
        ratio = y / HEIGHT
        # 简单的垂直渐变
        if random.random() > 0.95:  # 5% 噪点
            color = colors["primary"]
            draw.point((random.randint(0, WIDTH), y), fill=color)

    # === 2. 能量波纹（根据情绪强度）===
    if emotion in ["euphoria", "panic"]:
        create_energy_waves(draw, WIDTH, HEIGHT, colors["glow"], wave_count=8)
    elif emotion in ["excitement", "fear"]:
        create_energy_waves(draw, WIDTH, HEIGHT, colors["secondary"], wave_count=5)

    # === 3. 数据粒子背景 ===
    create_data_particles(draw, WIDTH, HEIGHT, colors["secondary"], density=80)

    # === 4. 主视觉符号（左上右下对角）===
    if emotion in ["euphoria", "excitement"]:
        symbol = "rocket" if emotion == "euphoria" else "arrow_up"
        draw_ascii_symbol(
            draw, 80, 80, ASCII_SYMBOLS[symbol], colors["primary"], scale=2
        )
        draw_ascii_symbol(
            draw,
            WIDTH - 300,
            HEIGHT - 300,
            ASCII_SYMBOLS["chart_rise"],
            colors["accent"],
            scale=3,
        )
    elif emotion in ["fear", "panic"]:
        symbol = "arrow_down"
        draw_ascii_symbol(
            draw, 80, 80, ASCII_SYMBOLS[symbol], colors["primary"], scale=2
        )
        draw_ascii_symbol(
            draw,
            WIDTH - 400,
            HEIGHT - 200,
            ASCII_SYMBOLS["chart_fall"],
            colors["accent"],
            scale=3,
        )

    # === 5. 中央信息区（极简黑盒）===
    box_w, box_h = 800, 500
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2

    # 黑色背景 + 发光边框
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill="#000000")

    for i in range(5):
        draw.rectangle(
            [box_x - i, box_y - i, box_x + box_w + i, box_y + box_h + i],
            outline=colors["glow"] if i < 2 else colors["primary"],
            width=2,
        )

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
    badge_x, badge_y = WIDTH - 250, 50

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
            x = random.randint(0, WIDTH - 80)
            y = random.randint(0, HEIGHT - 1)
            w = random.randint(20, 100)
            shift = random.randint(-12, 12)

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


def _generate_video(static_path, args):
    from procedural.engine import Engine
    from procedural.effects import get_effect

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    engine = Engine(internal_size=(160, 160), output_size=(1080, 1080))
    effect = get_effect(args.effect)
    frames = engine.render_video(
        effect, duration=args.duration, fps=args.fps, seed=seed
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
    }

    output = (
        f"media/emotional_viz_{emotion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    generate_emotional_viz(market_data, output)

    if args.video:
        print("🎬 生成视频...")
        output = _generate_video(output, args)
        print(f"📁 视频: {output}")
