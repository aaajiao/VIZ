#!/usr/bin/env python3
"""
Complete Market Visualization System
完整的市场可视化系统

功能：
1. 获取市场新闻和数据
2. 情绪分析（涨/跌/震荡）
3. 生成 ASCII 艺术可视化（含清晰可辨识的颜文字）
4. 输出高质量图像

艺术 × 数据 × 新闻
"""

import argparse
import json
import math
import os
import random
import re
import subprocess
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

try:
    from lib.kaomoji import draw_kaomoji
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji

ASCII_GRADIENT = " .:-=+*#%@"

# ========== ASCII 颜文字（只用基础字符，保证可辨识）==========
ASCII_KAOMOJI = {
    "bull": [
        # 开心表情
        ["  ^___^  ", " (◠‿◠) ", "  \\___/  "],
        ["  *___*  ", " (^o^) ", "  <___>  "],
        ["  O___O  ", " (≧▽≦)", "  |___|  "],
        # 庆祝
        ["  \\o/   ", "   |    ", "  / \\   "],
        ["  ^_^   ", " <(^_^)>", "  (_)   "],
    ],
    "bear": [
        # 难过表情
        ["  T_T   ", " (;_;)  ", "  |_|   "],
        ["  -_-   ", " (x_x)  ", "  |_|   "],
        ["  >_<   ", " (╥﹏╥)", "  |_|   "],
    ],
    "neutral": [
        # 平静表情
        ["  -_-   ", " (._.)  ", "  |_|   "],
        ["  o_o   ", " (o.o)  ", "  |_|   "],
    ],
}

# ========== ASCII 大型装饰 ==========
ASCII_DECORATIONS = {
    "rocket": [
        "       /\\       ",
        "      /  \\      ",
        "     | ** |     ",
        "    /|    |\\    ",
        "   / |    | \\   ",
        "  /  |    |  \\  ",
        " |   ======   | ",
        " |    |  |    | ",
        " |    |  |    | ",
        " \\====|  |====/ ",
        "      |  |      ",
        "     /|  |\\     ",
        "    //|  |\\\\    ",
        "   ///|  |\\\\\\   ",
    ],
    "chart_up": [
        "                 ████",
        "            ████ ████",
        "       ████ ████ ████",
        "  ████ ████ ████ ████",
        "  ████ ████ ████ ████",
    ],
    "chart_down": [
        "  ████ ████ ████ ████",
        "  ████ ████ ████     ",
        "       ████           ",
        "            ████      ",
        "                 ████ ",
    ],
    "arrow_up": [
        "        ▲▲▲         ",
        "       ▲▲▲▲▲        ",
        "      ▲▲▲▲▲▲▲       ",
        "     ▲▲▲▲▲▲▲▲▲      ",
        "    ▲▲▲▲▲▲▲▲▲▲▲     ",
        "        ████         ",
        "        ████         ",
        "        ████         ",
        "        ████         ",
    ],
    "arrow_down": [
        "        ████         ",
        "        ████         ",
        "        ████         ",
        "        ████         ",
        "    ▼▼▼▼▼▼▼▼▼▼▼     ",
        "     ▼▼▼▼▼▼▼▼▼      ",
        "      ▼▼▼▼▼▼▼       ",
        "       ▼▼▼▼▼        ",
        "        ▼▼▼         ",
    ],
}

# ========== 配色方案 ==========
COLOR_PALETTES = {
    "bull": {
        "bg": "#001a00",
        "primary": "#00ff00",
        "secondary": "#00cc00",
        "accent": "#ffffff",
        "glow": "#88ff88",
    },
    "bear": {
        "bg": "#1a0000",
        "primary": "#ff0000",
        "secondary": "#cc0000",
        "accent": "#ffffff",
        "glow": "#ff8888",
    },
    "neutral": {
        "bg": "#0a0a1a",
        "primary": "#ffaa00",
        "secondary": "#cc8800",
        "accent": "#ffffff",
        "glow": "#ffcc88",
    },
}


def fetch_market_news(query="US stock market today"):
    """获取市场新闻（使用 Perplexity）"""
    try:
        result = subprocess.run(
            ["/workspace/scripts/perplexity-search.sh", query],
            capture_output=True,
            text=True,
        )
        return result.stdout
    except FileNotFoundError:
        return None


def analyze_sentiment(news_text):
    """
    简单的情绪分析
    返回：'bull', 'bear', 'neutral'
    """
    news_lower = news_text.lower()

    # 关键词计数
    bull_words = [
        "up",
        "gain",
        "rise",
        "rally",
        "surge",
        "high",
        "bull",
        "positive",
        "record",
    ]
    bear_words = [
        "down",
        "fall",
        "drop",
        "decline",
        "crash",
        "bear",
        "negative",
        "loss",
    ]

    bull_count = sum(1 for word in bull_words if word in news_lower)
    bear_count = sum(1 for word in bear_words if word in news_lower)

    if bull_count > bear_count + 2:
        return "bull"
    elif bear_count > bull_count + 2:
        return "bear"
    else:
        return "neutral"


def extract_metrics(news_text):
    """提取关键指标（百分比、指数名称）"""
    metrics = []

    # 提取百分比
    percentages = re.findall(r"[+-]?\d+\.?\d*%", news_text)
    metrics.extend(percentages[:3])

    # 提取指数名称
    indices = re.findall(r"\b(DOW|Dow|NASDAQ|Nasdaq|S&P ?500|SPX|VIX)\b", news_text)
    metrics.extend(list(set(indices))[:2])

    # 如果没找到足够的，添加默认
    if len(metrics) < 3:
        metrics.extend(["MARKET UPDATE", datetime.now().strftime("%b %d")])

    return metrics[:4]


def draw_ascii_block(draw, x, y, lines, color, char_scale=4):
    """绘制 ASCII 块（颜文字或装饰），放大且清晰"""
    line_height = 20 * char_scale
    char_width = 12 * char_scale

    for i, line in enumerate(lines):
        line_y = y + i * line_height

        # 每个字符放大绘制
        for j, char in enumerate(line):
            char_x = x + j * char_width

            # 多次绘制加粗
            for dx in range(char_scale):
                for dy in range(char_scale):
                    draw.text((char_x + dx * 2, line_y + dy * 2), char, fill=color)


def draw_glow_text_large(draw, x, y, text, color, glow_color, scale=15):
    """绘制大型发光文字"""
    # 外发光
    for offset in [5, 4, 3, 2, 1]:
        for dx in [-offset, 0, offset]:
            for dy in [-offset, 0, offset]:
                if dx != 0 or dy != 0:
                    for sx in range(scale):
                        for sy in range(scale):
                            draw.text((x + dx + sx, y + dy + sy), text, fill=glow_color)

    # 主体
    for dx in range(scale):
        for dy in range(scale):
            draw.text((x + dx, y + dy), text, fill=color)


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
    engine = Engine(internal_size=(160, 160), output_size=size, contrast=1.1)
    effect = get_effect(effect_name)
    frame = engine.render_frame(effect, time=rng.random() * 6.0, seed=seed)

    overlay = Image.new("RGB", size, blend_color)
    frame = Image.blend(frame, overlay, 0.35)

    return frame


def create_complete_visualization(news_text, output_path, seed=None, effect=None):
    """
    创建完整的市场可视化
    """
    WIDTH, HEIGHT = 1080, 1080

    # 1. 分析情绪
    sentiment = analyze_sentiment(news_text)
    colors = COLOR_PALETTES[sentiment]

    if seed is None:
        seed = random.randint(0, 999999)
    rng = random.Random(seed)

    effect_map = {
        "bull": "plasma",
        "bear": "flame",
        "neutral": "wave",
    }
    effect_name = effect or effect_map.get(sentiment, "plasma")

    layouts = [
        {
            "box_w": 800,
            "box_h": 450,
            "box_x": (WIDTH - 800) // 2,
            "box_y": (HEIGHT - 450) // 2,
            "left": (50, 150),
            "right": (WIDTH - 500, HEIGHT - 400),
            "kao": [
                (150, 50),
                (WIDTH - 300, 50),
                (100, HEIGHT - 250),
                (WIDTH - 350, HEIGHT - 250),
            ],
        },
        {
            "box_w": 740,
            "box_h": 460,
            "box_x": 120,
            "box_y": 220,
            "left": (WIDTH - 420, 140),
            "right": (80, HEIGHT - 420),
            "kao": [
                (120, 80),
                (WIDTH - 320, 120),
                (140, HEIGHT - 260),
                (WIDTH - 360, HEIGHT - 260),
            ],
        },
        {
            "box_w": 780,
            "box_h": 500,
            "box_x": (WIDTH - 780) // 2,
            "box_y": 160,
            "left": (60, 140),
            "right": (WIDTH - 520, HEIGHT - 320),
            "kao": [
                (180, 80),
                (WIDTH - 360, 100),
                (140, HEIGHT - 260),
                (WIDTH - 320, HEIGHT - 260),
            ],
        },
        # New Layout 1: Vertical Split
        {
            "box_w": 500,
            "box_h": 800,
            "box_x": 50,
            "box_y": (HEIGHT - 800) // 2,
            "left": (WIDTH - 400, 100),
            "right": (WIDTH - 400, HEIGHT - 300),
            "kao": [
                (WIDTH - 300, 300),
                (WIDTH - 300, 500),
                (WIDTH - 300, 700),
                (WIDTH - 300, 900),
            ],
        },
        # New Layout 2: Horizontal Split
        {
            "box_w": 900,
            "box_h": 400,
            "box_x": (WIDTH - 900) // 2,
            "box_y": 50,
            "left": (100, HEIGHT - 300),
            "right": (WIDTH - 500, HEIGHT - 300),
            "kao": [
                (100, 500),
                (300, 500),
                (WIDTH - 300, 500),
                (WIDTH - 100, 500),
            ],
        },
        # New Layout 3: Corner Focus
        {
            "box_w": 600,
            "box_h": 600,
            "box_x": (WIDTH - 600) // 2,
            "box_y": (HEIGHT - 600) // 2,
            "left": (50, 50),
            "right": (WIDTH - 450, HEIGHT - 250),
            "kao": [
                (WIDTH - 200, 50),
                (50, HEIGHT - 200),
                (WIDTH // 2 - 100, 100),
                (WIDTH // 2 - 100, HEIGHT - 150),
            ],
        },
        # New Layout 4: Edge Frame
        {
            "box_w": 700,
            "box_h": 500,
            "box_x": (WIDTH - 700) // 2,
            "box_y": (HEIGHT - 500) // 2,
            "left": (60, 100),
            "right": (WIDTH - 520, HEIGHT - 340),
            "kao": [
                (60, 60),
                (WIDTH - 260, 60),
                (60, HEIGHT - 220),
                (WIDTH - 260, HEIGHT - 220),
            ],
        },
        # New Layout 5: Diagonal Strip
        {
            "box_w": 820,
            "box_h": 420,
            "box_x": 140,
            "box_y": 120,
            "left": (80, HEIGHT - 300),
            "right": (WIDTH - 520, HEIGHT - 360),
            "kao": [
                (120, 80),
                (WIDTH - 320, 140),
                (220, HEIGHT - 220),
                (WIDTH - 420, HEIGHT - 160),
            ],
        },
    ]
    layout = rng.choice(layouts)

    # 2. 提取指标
    metrics = extract_metrics(news_text)

    # 3. 创建画布 (procedural 背景 + 叠色)
    img = _render_procedural_background(
        effect_name, seed, (WIDTH, HEIGHT), colors["bg"]
    )
    if img is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), colors["bg"])
    draw = ImageDraw.Draw(img)

    # === 背景层：网格 + 粒子 ===
    # 网格
    grid_step = rng.choice([40, 50, 60, 80])
    grid_offset = rng.randint(0, grid_step // 2)
    for y in range(grid_offset, HEIGHT, grid_step):
        draw.line([(0, y), (WIDTH, y)], fill=colors["glow"], width=1)
    for x in range(grid_offset, WIDTH, grid_step):
        draw.line([(x, 0), (x, HEIGHT)], fill=colors["glow"], width=1)

    # 数据粒子
    particle_count = rng.randint(80, 150)
    particle_chars = rng.choice(["0123456789$#@", "%*+=", "<>/\\", "[]{}"])
    for _ in range(particle_count):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        char = rng.choice(particle_chars)
        size = rng.randint(2, 4)
        for dx in range(size):
            for dy in range(size):
                draw.text((x + dx, y + dy), char, fill=colors["secondary"])

    # ASCII 纹理层
    _draw_ascii_texture(
        draw, rng, WIDTH, HEIGHT, colors, density=rng.uniform(0.25, 0.45)
    )

    # === 装饰层：大型 ASCII 艺术 ===
    # 左侧装饰
    if sentiment == "bull":
        decoration = "rocket"
    elif sentiment == "bear":
        decoration = "arrow_down"
    else:
        decoration = "chart_up"

    draw_ascii_block(
        draw,
        layout["left"][0],
        layout["left"][1],
        ASCII_DECORATIONS[decoration],
        colors["primary"],
        char_scale=3,
    )

    # 右侧图表
    chart = "chart_up" if sentiment == "bull" else "chart_down"
    draw_ascii_block(
        draw,
        layout["right"][0],
        layout["right"][1],
        ASCII_DECORATIONS[chart],
        colors["accent"],
        char_scale=4,
    )

    # === 颜文字层：清晰可辨识 ===
    kaomoji_set = ASCII_KAOMOJI[sentiment]

    # Background Kaomoji Texture (New)
    bg_kao_count = rng.randint(5, 10)
    for _ in range(bg_kao_count):
        bx = rng.randint(0, WIDTH)
        by = rng.randint(0, HEIGHT)
        # Avoid center box roughly
        if (
            layout["box_x"] - 50 < bx < layout["box_x"] + layout["box_w"] + 50
            and layout["box_y"] - 50 < by < layout["box_y"] + layout["box_h"] + 50
        ):
            continue

        draw_kaomoji(
            draw,
            bx,
            by,
            sentiment,
            color=colors["secondary"],
            outline_color=colors["bg"],
            size=rng.randint(1, 2),
            rng=rng,
        )

    # 四个位置放置颜文字
    positions = layout["kao"]

    for idx, (x, y) in enumerate(positions[:3]):
        kao = rng.choice(kaomoji_set)
        draw_ascii_block(
            draw,
            x,
            y,
            kao,
            colors["accent"],
            char_scale=5,  # 足够大，能看清
        )

    # === 中央信息框 ===
    box_w, box_h = layout["box_w"], layout["box_h"]
    box_x, box_y = layout["box_x"], layout["box_y"]

    # 背景颜文字散布
    _scatter_kaomoji(
        draw,
        rng,
        WIDTH,
        HEIGHT,
        colors,
        sentiment,
        exclude_box=(box_x, box_y, box_w, box_h),
    )

    # 黑色背景 + 多层边框
    draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill="#000000")

    for i in range(6):
        draw.rectangle(
            [
                box_x - i * 2,
                box_y - i * 2,
                box_x + box_w + i * 2,
                box_y + box_h + i * 2,
            ],
            outline=colors["primary"] if i < 3 else colors["glow"],
            width=2,
        )

    # ASCII 边框增强
    for x in range(box_x + 10, box_x + box_w - 10, 20):
        draw.text((x, box_y - 18), "-", fill=colors["secondary"])
        draw.text((x, box_y + box_h + 4), "-", fill=colors["secondary"])
    for y in range(box_y + 10, box_y + box_h - 10, 20):
        draw.text((box_x - 18, y), "|", fill=colors["secondary"])
        draw.text((box_x + box_w + 6, y), "|", fill=colors["secondary"])

    # === 文字信息 ===
    text_x = box_x + 50
    text_y = box_y + 50

    # 顶部标签
    sentiment_label = {
        "bull": "BULLISH MARKET",
        "bear": "BEARISH MARKET",
        "neutral": "MIXED SIGNALS",
    }[sentiment]

    draw_glow_text_large(
        draw, text_x, text_y, sentiment_label, colors["accent"], colors["glow"], scale=8
    )

    # 分隔线
    text_y += 80
    for i in range(60):
        for dx in range(3):
            for dy in range(3):
                draw.text(
                    (text_x + i * 12 + dx, text_y + dy), "═", fill=colors["secondary"]
                )

    # 指标数据（超大）
    text_y += 50
    for idx, metric in enumerate(metrics[:3]):
        y_pos = text_y + idx * 90
        draw_glow_text_large(
            draw, text_x, y_pos, metric, colors["primary"], colors["glow"], scale=14
        )

    # 时间戳
    timestamp = datetime.now().strftime("%b %d, %Y %H:%M")
    ts_y = text_y + 300
    for dx in range(5):
        for dy in range(5):
            draw.text((text_x + dx, ts_y + dy), timestamp, fill=colors["secondary"])

    # === 底部标识 ===
    # 绘制大颜文字在底部中央
    big_kao = random.choice(kaomoji_set)
    kao_x = WIDTH // 2 - 150
    kao_y = HEIGHT - 200
    draw_ascii_block(
        draw,
        kao_x,
        kao_y,
        big_kao,
        colors["accent"],
        char_scale=6,  # 巨大，非常清晰
    )

    # === 后期处理 ===
    # 锐化
    img = img.filter(ImageFilter.SHARPEN)

    # 增强对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.4)

    # 轻微故障效果（只在极端情绪时）
    if sentiment in ["bull", "bear"]:
        pixels = img.load()
        glitch_count = 80 if sentiment == "bull" else 120

        for _ in range(glitch_count):
            x = rng.randint(0, WIDTH - 60)
            y = rng.randint(0, HEIGHT - 1)
            w = rng.randint(20, 80)
            shift = rng.randint(-8, 8)

            for i in range(w):
                if x + i < WIDTH and 0 <= (y + shift) < HEIGHT:
                    try:
                        pixels[x + i, y] = pixels[x + i, (y + shift) % HEIGHT]
                    except:
                        pass

    # 保存
    img.save(output_path, "PNG", quality=95)

    return {
        "path": output_path,
        "sentiment": sentiment,
        "metrics": metrics,
        "timestamp": timestamp,
    }


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
        description="Market Visualization Generator - 市场可视化生成器",
    )
    parser.add_argument("query", nargs="*", help="搜索查询 (默认: US stock market)")
    parser.add_argument("--video", action="store_true", help="输出 GIF 视频")
    parser.add_argument("--duration", type=float, default=5.0, help="视频时长 (秒)")
    parser.add_argument("--fps", type=int, default=30, help="视频帧率")
    parser.add_argument("--effect", default="plasma", help="视频效果 (默认 plasma)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    query = (
        " ".join(args.query)
        if args.query
        else "US stock market today major indices performance"
    )

    print("=" * 60)
    print("  Market Visualization Generator")
    print("  艺术 × 数据 × 新闻")
    print("=" * 60)
    print()

    print(f"📊 查询: {query}")
    print("🔍 获取市场新闻...")

    news = fetch_market_news(query)

    if not news or len(news) < 50:
        print("⚠️  无法获取新闻，使用模拟数据")
        news = "US stocks rise today. Dow Jones +0.6%, Nasdaq gains, S&P 500 near record highs. Manufacturing PMI 52.6 beats expectations."

    print(f"✓ 获取到 {len(news)} 字符的新闻")
    print()
    print("📈 分析情绪...")

    sentiment = analyze_sentiment(news)
    print(f"✓ 市场情绪: {sentiment.upper()}")
    print()

    print("🎨 生成可视化...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(
        script_dir,
        f"media/market_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
    )
    result = create_complete_visualization(
        news, output_path, seed=args.seed, effect=args.effect
    )

    if args.video:
        print("🎬 生成视频...")
        result["path"] = _generate_video(output_path, args)

    print()
    print("=" * 60)
    print("✅ 生成完成！")
    print("=" * 60)
    print(f"📁 文件: {result['path']}")
    print(f"📊 情绪: {result['sentiment'].upper()}")
    print(f"📌 指标: {', '.join(result['metrics'][:3])}")
    print(f"🕐 时间: {result['timestamp']}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    main()
