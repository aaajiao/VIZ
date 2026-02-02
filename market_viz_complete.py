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
import random
import re
import subprocess
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

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
    result = subprocess.run(
        ["/workspace/scripts/perplexity-search.sh", query],
        capture_output=True,
        text=True,
    )
    return result.stdout


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


def create_complete_visualization(news_text, output_path):
    """
    创建完整的市场可视化
    """
    WIDTH, HEIGHT = 1080, 1080

    # 1. 分析情绪
    sentiment = analyze_sentiment(news_text)
    colors = COLOR_PALETTES[sentiment]

    # 2. 提取指标
    metrics = extract_metrics(news_text)

    # 3. 创建画布
    img = Image.new("RGB", (WIDTH, HEIGHT), colors["bg"])
    draw = ImageDraw.Draw(img)

    # === 背景层：网格 + 粒子 ===
    # 网格
    for y in range(0, HEIGHT, 50):
        draw.line([(0, y), (WIDTH, y)], fill=colors["glow"], width=1)
    for x in range(0, WIDTH, 50):
        draw.line([(x, 0), (x, HEIGHT)], fill=colors["glow"], width=1)

    # 数据粒子
    for _ in range(100):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        char = random.choice("0123456789$#@")
        size = random.randint(2, 4)
        for dx in range(size):
            for dy in range(size):
                draw.text((x + dx, y + dy), char, fill=colors["secondary"])

    # === 装饰层：大型 ASCII 艺术 ===
    # 左侧装饰
    if sentiment == "bull":
        decoration = "rocket"
    elif sentiment == "bear":
        decoration = "arrow_down"
    else:
        decoration = "chart_up"

    draw_ascii_block(
        draw, 50, 150, ASCII_DECORATIONS[decoration], colors["primary"], char_scale=3
    )

    # 右侧图表
    chart = "chart_up" if sentiment == "bull" else "chart_down"
    draw_ascii_block(
        draw,
        WIDTH - 500,
        HEIGHT - 400,
        ASCII_DECORATIONS[chart],
        colors["accent"],
        char_scale=4,
    )

    # === 颜文字层：清晰可辨识 ===
    kaomoji_set = ASCII_KAOMOJI[sentiment]

    # 四个位置放置颜文字
    positions = [
        (150, 50, "top-left"),
        (WIDTH - 300, 50, "top-right"),
        (100, HEIGHT - 250, "bottom-left"),
        (WIDTH - 350, HEIGHT - 250, "bottom-right"),
    ]

    for idx, (x, y, pos) in enumerate(positions[:3]):
        kao = random.choice(kaomoji_set)
        draw_ascii_block(
            draw,
            x,
            y,
            kao,
            colors["accent"],
            char_scale=5,  # 足够大，能看清
        )

    # === 中央信息框 ===
    box_w, box_h = 800, 450
    box_x = (WIDTH - box_w) // 2
    box_y = (HEIGHT - box_h) // 2

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
            x = random.randint(0, WIDTH - 60)
            y = random.randint(0, HEIGHT - 1)
            w = random.randint(20, 80)
            shift = random.randint(-8, 8)

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

    output_path = (
        f"media/market_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    result = create_complete_visualization(news, output_path)

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
