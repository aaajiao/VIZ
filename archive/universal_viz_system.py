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
import os
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

from procedural.engine import Engine
from procedural.effects import get_effect
from procedural.layers import KaomojiSprite, TextSprite

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

ASCII_GRADIENT = " .:-=+*#%@"


def _render_procedural_background(effect_name, seed, size, blend_color=None):
    """渲染 procedural 背景 (静态)"""
    if not effect_name:
        return None

    from procedural.engine import Engine
    from procedural.effects import get_effect

    rng = random.Random(seed)
    engine = Engine(internal_size=(160, 160), output_size=size, contrast=1.1)
    effect = get_effect(effect_name)
    frame = engine.render_frame(effect, time=rng.random() * 6.0, seed=seed)

    if blend_color:
        overlay = Image.new("RGB", size, blend_color)
        frame = Image.blend(frame, overlay, 0.35)

    return frame


def _select_layout(rng, width, height):
    """选择布局模板 (位置 + 文本区域)"""
    layouts = [
        {
            "positions": [
                (120, 100, 120),
                (680, 80, 130),
                (180, 420, 110),
                (720, 480, 115),
                (320, 750, 140),
                (width - 280, height - 280, 125),
            ],
            "central": (width // 2 - 100, height // 2 - 100),
            "title_y": 30,
            "info_y": height - 100,
            "timestamp_y": height - 50,
            "decorations": [
                (40, 40, "{ }"),
                (width - 100, 40, "[ ]"),
                (40, height - 70, "< >"),
                (width - 100, height - 70, "( )"),
            ],
        },
        {
            "positions": [
                (80, 140, 120),
                (width - 360, 120, 130),
                (120, 520, 110),
                (width - 420, 560, 115),
                (240, 780, 140),
                (width - 260, height - 260, 125),
            ],
            "central": (width // 2 - 140, height // 2 - 140),
            "title_y": 60,
            "info_y": height - 140,
            "timestamp_y": height - 80,
            "decorations": [
                (60, 60, "//"),
                (width - 120, 60, "\\\\"),
                (60, height - 90, "::"),
                (width - 120, height - 90, "##"),
            ],
        },
        {
            "positions": [
                (140, 80, 110),
                (width - 320, 100, 120),
                (220, 460, 120),
                (width - 360, 420, 110),
                (360, 780, 150),
                (width - 300, height - 320, 120),
            ],
            "central": (width // 2 - 90, height // 2 - 120),
            "title_y": 80,
            "info_y": height - 120,
            "timestamp_y": height - 60,
            "decorations": [
                (50, 30, "<>"),
                (width - 120, 30, "[]"),
                (50, height - 80, "()"),
                (width - 120, height - 80, "{}"),
            ],
        },
        # New Layout 1: Asymmetric Corner
        {
            "positions": [
                (80, 80, 100),
                (200, 180, 110),
                (350, 300, 120),
                (width - 200, height - 200, 130),
                (width - 350, height - 350, 110),
                (width - 100, height - 100, 100),
            ],
            "central": (width // 2, height // 2),
            "title_y": 40,
            "info_y": height - 160,
            "timestamp_y": height - 40,
            "decorations": [
                (20, 20, "+"),
                (width - 40, 20, "+"),
                (20, height - 40, "+"),
                (width - 40, height - 40, "+"),
            ],
        },
        # New Layout 2: Sidebar
        {
            "positions": [
                (width - 150, 100, 110),
                (width - 150, 300, 110),
                (width - 150, 500, 110),
                (width - 150, 700, 110),
                (width - 150, 900, 110),
                (100, height - 100, 120),
            ],
            "central": (width // 2 - 100, height // 2),
            "title_y": 50,
            "info_y": height - 100,
            "timestamp_y": height - 50,
            "decorations": [
                (20, 100, "|"),
                (20, 300, "|"),
                (20, 500, "|"),
                (20, 700, "|"),
            ],
        },
        # New Layout 3: Orbit
        {
            "positions": [
                (width // 2, 150, 100),
                (width // 2 + 200, 250, 100),
                (width // 2 + 200, height - 250, 100),
                (width // 2, height - 150, 100),
                (width // 2 - 200, height - 250, 100),
                (width // 2 - 200, 250, 100),
            ],
            "central": (width // 2 - 120, height // 2 - 120),
            "title_y": 20,
            "info_y": height - 80,
            "timestamp_y": height - 40,
            "decorations": [
                (width // 2 - 300, height // 2, "("),
                (width // 2 + 300, height // 2, ")"),
                (width // 2, height // 2 - 300, "^"),
                (width // 2, height // 2 + 300, "v"),
            ],
        },
        # New Layout 4: Diagonal Flow
        {
            "positions": [
                (80, 120, 110),
                (240, 260, 120),
                (400, 420, 130),
                (560, 580, 120),
                (720, 740, 110),
                (width - 260, height - 260, 130),
            ],
            "central": (width // 2 - 140, height // 2 - 160),
            "title_y": 40,
            "info_y": height - 140,
            "timestamp_y": height - 70,
            "decorations": [
                (40, 100, "/"),
                (width - 80, height - 160, "\\"),
                (60, height - 120, "//"),
                (width - 140, 80, "\\\\"),
            ],
        },
        # New Layout 5: Top Banner
        {
            "positions": [
                (100, 220, 120),
                (320, 240, 110),
                (540, 260, 120),
                (760, 280, 110),
                (120, height - 240, 140),
                (width - 300, height - 240, 140),
            ],
            "central": (width // 2 - 110, height // 2 + 80),
            "title_y": 20,
            "info_y": height - 120,
            "timestamp_y": height - 60,
            "decorations": [
                (40, 40, "===="),
                (width - 140, 40, "===="),
                (40, 140, "----"),
                (width - 140, 140, "----"),
            ],
        },
    ]

    return rng.choice(layouts)


def _draw_ascii_texture(draw, rng, width, height, colors, density=0.35):
    """绘制 ASCII 纹理层"""
    cell = rng.choice([18, 20, 24, 28])
    text_color = colors.get("dim", colors["secondary"])
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if rng.random() < density:
                char = ASCII_GRADIENT[int(rng.random() * (len(ASCII_GRADIENT) - 1))]
                draw.text((x, y), char, fill=text_color)


def _scatter_kaomoji(draw, rng, width, height, moods_list, colors, avoid_center=True):
    """散布小型颜文字以强化 ASCII 属性"""
    count = rng.randint(6, 14)
    for _ in range(count):
        x = rng.randint(40, width - 200)
        y = rng.randint(40, height - 200)
        if avoid_center:
            if abs(x - width // 2) < 220 and abs(y - height // 2) < 220:
                continue
        mood = rng.choice(moods_list)
        size = rng.randint(2, 5)
        draw_kaomoji(
            draw,
            x,
            y,
            mood,
            color=colors["primary"],
            outline_color=colors.get("outline", colors["secondary"]),
            size=size,
            rng=rng,
        )


def fetch_content(content_type, query=None):
    """获取内容（新闻/数据）"""
    if content_type == "mood":
        # 个人心情不需要获取新闻
        return None

    if not query:
        # 使用默认搜索词
        keywords = CONTENT_TYPES[content_type].get("search_keywords", [content_type])
        query = " ".join(keywords[:3])

    try:
        result = subprocess.run(
            ["/workspace/scripts/perplexity-search.sh", query],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout if result.returncode == 0 else None
    except FileNotFoundError:
        return None


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

    seed = content_data.get("seed")
    if seed is None:
        seed = random.randint(0, 999999)
    rng = random.Random(seed)

    layout = _select_layout(rng, WIDTH, HEIGHT)
    effect_name = content_data.get("effect")

    # 创建画布 (可选 procedural 背景)
    img = _render_procedural_background(
        effect_name, seed, (WIDTH, HEIGHT), colors["bg"]
    )
    if img is None:
        img = Image.new("RGB", (WIDTH, HEIGHT), colors["bg"])

    draw = ImageDraw.Draw(img)

    # === 背景网格 ===
    grid_color = colors.get("glow", colors["secondary"])
    grid_step = rng.choice([60, 80, 100, 120])
    grid_offset = rng.randint(0, grid_step // 2)
    for y in range(grid_offset, HEIGHT, grid_step):
        draw.line([(0, y), (WIDTH, y)], fill=grid_color, width=1)
    for x in range(grid_offset, WIDTH, grid_step):
        draw.line([(x, 0), (x, HEIGHT)], fill=grid_color, width=1)

    # === 数据粒子 ===
    if content_type == "mood":
        particle_chars = "01·"
    elif content_type == "art":
        particle_chars = "*o.:-"
    else:
        particle_chars = "0123456789$#"

    particle_count = rng.randint(60, 140)
    for _ in range(particle_count):
        x = rng.randint(0, WIDTH)
        y = rng.randint(0, HEIGHT)
        draw.text(
            (x, y),
            rng.choice(particle_chars),
            fill=colors.get("dim", colors["secondary"]),
        )

    # === ASCII 纹理层 ===
    _draw_ascii_texture(
        draw, rng, WIDTH, HEIGHT, colors, density=rng.uniform(0.25, 0.45)
    )

    # === 背景颜文字散布 ===
    _scatter_kaomoji(draw, rng, WIDTH, HEIGHT, moods_list, colors)

    # === 颜文字布局 ===
    # 6个位置 + 1个中央
    positions = layout["positions"]

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
            rng=rng,
        )

    # 中央大表情
    central_mood = moods_list[0] if moods_list else "happy"
    center_x, center_y = layout["central"]
    central_size = rng.randint(180, 220)
    draw_kaomoji(
        draw,
        center_x,
        center_y,
        central_mood,
        color=colors["accent"],
        outline_color=colors.get("outline", colors["secondary"]),
        size=central_size,
        rng=rng,
    )

    # === 文字信息（顶部和底部，不用大方框）===
    # 顶部标题
    title = content_data.get("title", config["name"])
    title_y = layout["title_y"]
    for dx in range(6):
        for dy in range(6):
            draw.text(
                (WIDTH // 2 - len(title) * 10 + dx * 2, title_y + dy * 2),
                title,
                fill=colors["primary"],
            )

    # 底部关键信息（横排）
    key_info = content_data.get("key_info", [])
    if key_info:
        info_text = " | ".join(key_info[:3])
        info_y = layout["info_y"]
        for dx in range(4):
            for dy in range(4):
                draw.text(
                    (WIDTH // 2 - len(info_text) * 3 + dx, info_y + dy),
                    info_text,
                    fill=colors["primary"],
                )

    # 时间戳
    timestamp = datetime.now().strftime("%b %d, %Y")
    timestamp_y = layout["timestamp_y"]
    for dx in range(3):
        for dy in range(3):
            draw.text(
                (WIDTH // 2 - 100 + dx, timestamp_y + dy),
                timestamp,
                fill=colors.get("dim", colors["secondary"]),
            )

    # === 角落装饰 ===
    decorations = layout["decorations"]
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

    img.save(output_path, "PNG", quality=95)
    return output_path


def _generate_video(static_path, args, content_type="mood", content_data=None):
    """
    使用 procedural engine + sprites 生成 GIF 视频
    Use procedural Engine with KaomojiSprite/TextSprite for animated GIF

    content_data = {
        'sentiment', 'key_info', 'title', 'seed', 'effect',
    }
    """
    if content_data is None:
        content_data = {}

    seed = args.seed if args.seed is not None else random.randint(0, 999999)
    rng = random.Random(seed)

    # === 配置 ===
    config = CONTENT_TYPES[content_type]
    sentiment = content_data.get("sentiment", "neutral")

    if content_type == "market":
        colors = config[f"colors_{sentiment}"]
        moods_list = config["moods"][sentiment]
    else:
        colors = config["colors"]
        moods_list = config.get("moods", ["o_o", "^_^", "thinking"])

    if "custom_moods" in content_data:
        moods_list = content_data["custom_moods"]

    # === 精灵坐标直接使用输出分辨率 (引擎先上采样再渲染精灵) ===
    INTERNAL = 160
    OUTPUT = 1080

    # === 布局 ===
    layout = _select_layout(rng, OUTPUT, OUTPUT)
    positions = layout["positions"]

    # === 创建 KaomojiSprite 列表 ===
    sprites = []

    # 6 个位置颜文字 (带浮动动画)
    for idx, (x, y, size) in enumerate(positions):
        mood = moods_list[idx % len(moods_list)]
        phase = idx * 0.8  # 错开相位
        sprite = KaomojiSprite(
            mood,
            x=x,
            y=y,
            color=colors["primary"],
            outline_color=colors.get("outline", colors["secondary"]),
            scale=max(1, size // 100),
            animations=[
                {
                    "type": "floating",
                    "amp": 3.0,
                    "speed": 0.8 + idx * 0.1,
                    "phase": phase,
                },
                {"type": "breathing", "amp": 0.08, "speed": 1.5},
            ],
        )
        sprites.append(sprite)

    # 中央大表情 (呼吸动画)
    central_mood = moods_list[0] if moods_list else "happy"
    center_x, center_y = layout["central"]
    central_size = rng.randint(180, 220)
    sprites.append(
        KaomojiSprite(
            central_mood,
            x=center_x,
            y=center_y,
            color=colors["accent"],
            outline_color=colors.get("outline", colors["secondary"]),
            scale=max(1, central_size // 100),
            animations=[
                {"type": "breathing", "amp": 0.12, "speed": 2.0},
                {"type": "floating", "amp": 2.0, "speed": 0.6},
            ],
        )
    )

    # === 文字精灵 ===
    title = content_data.get("title", config["name"])
    title_y = layout["title_y"]
    sprites.append(
        TextSprite(
            title,
            x=OUTPUT // 2 - len(title) * 10,
            y=title_y,
            color=colors["primary"],
            glow_color=colors.get("glow", colors["secondary"]),
            glow_size=2,
            animations=[
                {"type": "breathing", "amp": 0.05, "speed": 1.0},
            ],
        )
    )

    # 底部信息文字
    key_info = content_data.get("key_info", [])
    if key_info:
        info_text = " | ".join(key_info[:3])
        info_y = layout["info_y"]
        sprites.append(
            TextSprite(
                info_text,
                x=OUTPUT // 2 - len(info_text) * 3,
                y=info_y,
                color=colors["primary"],
                glow_size=1,
            )
        )

    # 时间戳
    timestamp = datetime.now().strftime("%b %d, %Y")
    timestamp_y = layout["timestamp_y"]
    sprites.append(
        TextSprite(
            timestamp,
            x=OUTPUT // 2 - 100,
            y=timestamp_y,
            color=colors.get("dim", colors["secondary"]),
            glow_size=1,
        )
    )

    # === 散布小颜文字 (背景装饰，轻微浮动) ===
    scatter_count = rng.randint(4, 8)
    for i in range(scatter_count):
        sx = rng.randint(40, OUTPUT - 200)
        sy = rng.randint(40, OUTPUT - 200)
        # 避开中心区域
        if abs(sx - OUTPUT // 2) < 220 and abs(sy - OUTPUT // 2) < 220:
            continue
        mood = rng.choice(moods_list)
        sprites.append(
            KaomojiSprite(
                mood,
                x=sx,
                y=sy,
                color=colors["primary"],
                outline_color=colors.get("outline", colors["secondary"]),
                scale=max(1, rng.randint(2, 5)),
                animations=[
                    {"type": "floating", "amp": 2.0, "speed": 0.5, "phase": i * 1.2},
                ],
            )
        )

    # === 渲染 ===
    engine = Engine(internal_size=(INTERNAL, INTERNAL), output_size=(OUTPUT, OUTPUT))
    effect = get_effect(args.effect)
    frames = engine.render_video(
        effect, duration=args.duration, fps=args.fps, sprites=sprites, seed=seed
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
        "seed": args.seed,
        "effect": args.effect,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(
        script_dir,
        f"media/{content_type}_viz_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
    )
    generate_visualization(content_type, content_data, output_path)

    # 视频模式
    if args.video:
        print("🎬 生成视频...")
        output_path = _generate_video(output_path, args, content_type, content_data)

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
