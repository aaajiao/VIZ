#!/usr/bin/env python3
"""
Universal Visualization System
通用可视化系统

支持内容类型：
1. 市场与经济 (market)
2. 艺术与文化 (art)
3. 个人心情 (mood)
4. 通用新闻 (news)
"""

import argparse
import random
import re
import subprocess
import sys
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

try:
    from lib.kaomoji import draw_kaomoji, get_moods_by_category
except ImportError:
    from viz.lib.kaomoji import draw_kaomoji, get_moods_by_category

# ========== 内容类型配置 ==========
CONTENT_TYPES = {
    "market": {
        "name": "市场与经济",
        "search_keywords": [
            "stock market",
            "economy",
            "financial",
            "trading",
            "dow",
            "nasdaq",
        ],
        "colors_bull": {
            "bg": "#001a00",
            "primary": "#00ff00",
            "secondary": "#00cc00",
            "accent": "#ffffff",
            "glow": "#88ff88",
        },
        "colors_bear": {
            "bg": "#1a0000",
            "primary": "#ff0000",
            "secondary": "#cc0000",
            "accent": "#ffffff",
            "glow": "#ff8888",
        },
        "colors_neutral": {
            "bg": "#0a0a1a",
            "primary": "#ffaa00",
            "secondary": "#cc8800",
            "accent": "#ffffff",
            "glow": "#ffcc88",
        },
        "moods": {
            "bull": ["^_^", "excited", "\\o/", "happy"],
            "bear": ["T_T", "sad", "(_)", "cry"],
            "neutral": ["o_o", "-_-", "thinking", "calm"],
        },
    },
    "art": {
        "name": "艺术与文化",
        "search_keywords": [
            "art exhibition",
            "gallery",
            "artist",
            "museum",
            "contemporary art",
            "media art",
        ],
        "colors": {
            "bg": "#1a0a1a",
            "primary": "#ff00ff",
            "secondary": "#cc00cc",
            "accent": "#ffffff",
            "glow": "#ff88ff",
        },
        "moods": ["*_*", "love", "♥", "excited", "thinking", "?", "surprised"],
    },
    "mood": {
        "name": "个人心情",
        "colors": {
            "bg": "#0a0a1a",
            "primary": "#88aaff",
            "secondary": "#5577cc",
            "accent": "#aaccff",
            "glow": "#aaccff",
            "outline": "#334466",
            "dim": "#223344",
        },
        "moods": ["^_^", "-_-", "*_*", "T_T", "o_o", "\\o/", "thinking", "working"],
    },
    "news": {
        "name": "通用新闻",
        "colors": {
            "bg": "#0a1a0a",
            "primary": "#00ffaa",
            "secondary": "#00cc88",
            "accent": "#ffffff",
            "glow": "#88ffcc",
        },
        "moods": ["o_o", "thinking", "?", "surprised", "O_O", "calm"],
    },
}


def fetch_content(content_type, query=None):
    """获取内容（新闻/数据）"""
    if content_type == "mood":
        # 个人心情不需要获取新闻
        return None

    if not query:
        # 使用默认搜索词
        keywords = CONTENT_TYPES[content_type].get("search_keywords", [content_type])
        query = " ".join(keywords[:3])

    result = subprocess.run(
        ["/workspace/scripts/perplexity-search.sh", query],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.stdout if result.returncode == 0 else None


def analyze_sentiment(text, content_type):
    """分析情绪/趋势"""
    if not text:
        return "neutral"

    text_lower = text.lower()

    if content_type == "market":
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

        bull_count = sum(1 for word in bull_words if word in text_lower)
        bear_count = sum(1 for word in bear_words if word in text_lower)

        if bull_count > bear_count + 2:
            return "bull"
        elif bear_count > bull_count + 2:
            return "bear"
        else:
            return "neutral"

    elif content_type == "art":
        positive_words = [
            "amazing",
            "beautiful",
            "stunning",
            "innovative",
            "groundbreaking",
            "celebrated",
        ]
        if any(word in text_lower for word in positive_words):
            return "positive"
        return "neutral"

    else:
        return "neutral"


def extract_key_info(text, content_type):
    """提取关键信息"""
    if not text:
        return []

    info = []

    if content_type == "market":
        # 提取百分比
        percentages = re.findall(r"[+-]?\d+\.?\d*%", text)
        info.extend(percentages[:2])

        # 提取指数名称
        indices = re.findall(r"\b(DOW|Dow|NASDAQ|Nasdaq|S&P ?500|SPX|VIX)\b", text)
        info.extend(list(set(indices))[:2])

    elif content_type == "art":
        # 提取艺术家名字（简单正则）
        artists = re.findall(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", text)
        info.extend(list(set(artists))[:2])

        # 提取展览/博物馆
        venues = re.findall(r"\b(Museum|Gallery|Center|Institute|Foundation)\b", text)
        info.extend(list(set(venues))[:2])

    # 如果信息不足，添加默认
    if len(info) < 3:
        info.extend([datetime.now().strftime("%b %d"), content_type.upper()])

    return info[:4]


def generate_visualization(content_type, content_data, output_path):
    """
    生成可视化

    content_data = {
        'sentiment': 'bull/bear/neutral/positive/...',
        'key_info': ['信息1', '信息2', ...],
        'title': '标题',
        'custom_moods': [...] (可选，自定义表情)
    }
    """
    WIDTH, HEIGHT = 1080, 1080

    # 获取配置
    config = CONTENT_TYPES[content_type]
    sentiment = content_data.get("sentiment", "neutral")

    # 选择配色
    if content_type == "market":
        colors = config[f"colors_{sentiment}"]
        moods_list = config["moods"][sentiment]
    else:
        colors = config["colors"]
        moods_list = config.get("moods", ["o_o", "^_^", "thinking"])

    # 自定义表情覆盖
    if "custom_moods" in content_data:
        moods_list = content_data["custom_moods"]

    # 创建画布
    img = Image.new("RGB", (WIDTH, HEIGHT), colors["bg"])
    draw = ImageDraw.Draw(img)

    # === 背景网格 ===
    grid_color = colors.get("glow", colors["secondary"])
    for y in range(0, HEIGHT, 80):
        draw.line([(0, y), (WIDTH, y)], fill=grid_color, width=1)
    for x in range(0, WIDTH, 80):
        draw.line([(x, 0), (x, HEIGHT)], fill=grid_color, width=1)

    # === 数据粒子 ===
    particle_chars = "01·" if content_type == "mood" else "0123456789$#"
    for _ in range(80):
        x = random.randint(0, WIDTH)
        y = random.randint(0, HEIGHT)
        draw.text(
            (x, y),
            random.choice(particle_chars),
            fill=colors.get("dim", colors["secondary"]),
        )

    # === 颜文字布局 ===
    # 6个位置 + 1个中央
    positions = [
        (120, 100, 120),
        (680, 80, 130),
        (180, 420, 110),
        (720, 480, 115),
        (320, 750, 140),
        (WIDTH - 280, HEIGHT - 280, 125),
    ]

    for idx, (x, y, size) in enumerate(positions):
        mood = moods_list[idx % len(moods_list)]
        draw_kaomoji(
            draw,
            x,
            y,
            mood,
            color=colors["primary"],
            outline_color=colors.get("outline", colors["secondary"]),
            size=size,
        )

    # 中央大表情
    central_mood = moods_list[0] if moods_list else "happy"
    draw_kaomoji(
        draw,
        WIDTH // 2 - 100,
        HEIGHT // 2 - 100,
        central_mood,
        color=colors["accent"],
        outline_color=colors.get("outline", colors["secondary"]),
        size=200,
    )

    # === 文字信息（顶部和底部，不用大方框）===
    # 顶部标题
    title = content_data.get("title", config["name"])
    for dx in range(6):
        for dy in range(6):
            draw.text(
                (WIDTH // 2 - len(title) * 10 + dx * 2, 30 + dy * 2),
                title,
                fill=colors["primary"],
            )

    # 底部关键信息（横排）
    key_info = content_data.get("key_info", [])
    if key_info:
        info_text = " | ".join(key_info[:3])
        for dx in range(4):
            for dy in range(4):
                draw.text(
                    (WIDTH // 2 - len(info_text) * 3 + dx, HEIGHT - 100 + dy),
                    info_text,
                    fill=colors["primary"],
                )

    # 时间戳
    timestamp = datetime.now().strftime("%b %d, %Y")
    for dx in range(3):
        for dy in range(3):
            draw.text(
                (WIDTH // 2 - 100 + dx, HEIGHT - 50 + dy),
                timestamp,
                fill=colors.get("dim", colors["secondary"]),
            )

    # === 角落装饰 ===
    decorations = [
        (40, 40, "{ }"),
        (WIDTH - 100, 40, "[ ]"),
        (40, HEIGHT - 70, "< >"),
        (WIDTH - 100, HEIGHT - 70, "( )"),
    ]
    for x, y, symbol in decorations:
        for dx in range(5):
            for dy in range(5):
                draw.text((x + dx * 2, y + dy * 2), symbol, fill=colors["primary"])

    # === 后期处理 ===
    img = img.filter(ImageFilter.SHARPEN)
    img = ImageEnhance.Contrast(img).enhance(1.4)

    # 轻微故障（只在极端情绪时）
    if sentiment in ["bull", "bear", "positive"]:
        pixels = img.load()
        glitch_count = 100
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

    img.save(output_path, "PNG", quality=95)
    return output_path


def _generate_video(static_path, args):
    """使用 procedural engine 生成 GIF 视频"""
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
    """构建 argparse 解析器"""
    parser = argparse.ArgumentParser(
        description="Universal Visualization System - 通用可视化系统",
    )
    parser.add_argument(
        "type",
        choices=["market", "art", "mood", "news"],
        help="内容类型: market(市场), art(艺术), mood(心情), news(新闻)",
    )
    parser.add_argument("query", nargs="*", help="搜索查询 (可选)")
    parser.add_argument("--video", action="store_true", help="输出 GIF 视频")
    parser.add_argument(
        "--duration", type=float, default=5.0, help="视频时长 (秒，默认 5)"
    )
    parser.add_argument("--fps", type=int, default=30, help="视频帧率 (默认 30)")
    parser.add_argument("--effect", default="plasma", help="视频效果 (默认 plasma)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (默认自动)")
    return parser


def main():
    """主流程"""
    parser = build_parser()
    args = parser.parse_args()

    content_type = args.type
    query = " ".join(args.query) if args.query else None

    print("=" * 60)
    print("  Universal Visualization System")
    print("  通用可视化系统")
    print("=" * 60)
    print()

    print(f"📊 类型: {CONTENT_TYPES[content_type]['name']}")

    # 获取内容
    if content_type != "mood":
        print(f"🔍 查询: {query or '默认'}")
        print("获取内容...")
        content_text = fetch_content(content_type, query)

        if content_text:
            print(f"✓ 获取到 {len(content_text)} 字符")
        else:
            print("⚠️  获取失败，使用模拟数据")
            content_text = "Sample content for visualization"

        # 分析
        sentiment = analyze_sentiment(content_text, content_type)
        key_info = extract_key_info(content_text, content_type)
        title = CONTENT_TYPES[content_type]["name"].upper()
    else:
        sentiment = "neutral"
        key_info = ["TODAY", "MOOD CHECK"]
        title = "MY MOOD"

    print(f"📈 情绪: {sentiment}")
    print(f"📌 关键信息: {', '.join(key_info)}")
    print()

    # 生成
    print("🎨 生成可视化...")
    content_data = {
        "sentiment": sentiment,
        "key_info": key_info,
        "title": title,
    }

    output_path = (
        f"media/{content_type}_viz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    generate_visualization(content_type, content_data, output_path)

    # 视频模式
    if args.video:
        print("🎬 生成视频...")
        output_path = _generate_video(output_path, args)

    print()
    print("=" * 60)
    print("✅ 生成完成！")
    print("=" * 60)
    print(f"📁 文件: {output_path}")
    print(f"📊 类型: {content_type}")
    print(f"📈 情绪: {sentiment}")
    print("=" * 60)


if __name__ == "__main__":
    main()
