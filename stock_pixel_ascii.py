#!/usr/bin/env python3
"""
Stock Market Pixel-to-ASCII Converter
基于 Ascify-Art 的方法，用真实图像转 ASCII

特点：
1. 真实的逐像素 ASCII 转换
2. 保留原图色彩
3. 可自定义字符集（情绪化）
4. 叠加市场数据文字
"""

import argparse
import math
import sys
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

# ========== 字符集（按密度从亮到暗）==========
CHAR_SETS = {
    "classic": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "simple": " .:-=+*#%@",
    "blocks": " ░▒▓█",
    "bull": " .+*$↑▲🚀",  # 上涨主题
    "bear": " .+*$↓▼📉",  # 下跌主题
    "numbers": " 0123456789",
    "money": " .,;:¥$€£₿",
}


def download_chart_image(symbol="SPY", width=400, height=300):
    """
    下载股票图表（示例：用占位图）
    实际可以接 TradingView / Yahoo Finance 等 API
    """
    # 暂时用占位图
    url = f"https://via.placeholder.com/{width}x{height}/00ff00/000000?text={symbol}+CHART"
    response = requests.get(url)
    return Image.open(BytesIO(response.content))


def image_to_ascii_art(
    image_path_or_obj,
    char_set="classic",
    scale=0.25,
    char_width=8,
    char_height=16,
    font_size=10,
    rgb_limit=(255, 255, 255),
    saturation=1.0,
    brightness=1.0,
    bg_color="black",
    custom_font=None,
):
    """
    将图像转换为 ASCII 艺术

    参数：
    - image_path_or_obj: 图像路径或 PIL Image 对象
    - char_set: 字符集名称或自定义字符串
    - scale: 缩放比例（越小越快）
    - char_width/char_height: 每个字符的像素尺寸
    - font_size: 字体大小
    - rgb_limit: RGB 上限 (r, g, b)
    - saturation: 饱和度
    - brightness: 亮度
    - bg_color: 背景色
    - custom_font: 自定义字体路径
    """
    # 加载图像
    if isinstance(image_path_or_obj, str):
        im = Image.open(image_path_or_obj).convert("RGB")
    else:
        im = image_path_or_obj.convert("RGB")

    # 获取字符集
    if char_set in CHAR_SETS:
        chars = CHAR_SETS[char_set]
    else:
        chars = char_set

    char_array = list(chars[::-1])  # 反转（最亮到最暗）
    char_length = len(char_array)
    interval = char_length / 256

    # 缩放图像
    width, height = im.size
    im = im.resize(
        (int(scale * width), int(scale * height * (char_width / char_height))),
        Image.Resampling.NEAREST,
    )
    width, height = im.size
    pix = im.load()

    # 创建输出图像
    output_image = Image.new(
        "RGB", (char_width * width, char_height * height), color=bg_color
    )
    draw = ImageDraw.Draw(output_image)

    # 加载字体
    try:
        if custom_font:
            font = ImageFont.truetype(custom_font, font_size)
        else:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    # RGB 限制
    max_r, max_g, max_b = rgb_limit

    # 逐像素转换
    ascii_string = ""
    for i in range(height):
        for j in range(width):
            r, g, b = pix[j, i]

            # 限制 RGB
            r = min(r, max_r)
            g = min(g, max_g)
            b = min(b, max_b)

            # 计算灰度
            gray = int(r / 3 + g / 3 + b / 3)

            # 映射到字符
            char_index = math.floor(gray * interval)
            char_index = min(char_index, char_length - 1)
            char = char_array[char_index]

            # 绘制字符（保留原色）
            draw.text(
                (j * char_width, i * char_height), char, font=font, fill=(r, g, b)
            )

            ascii_string += char
        ascii_string += "\n"

    # 后期增强
    output_image = ImageEnhance.Color(output_image).enhance(saturation)
    output_image = ImageEnhance.Brightness(output_image).enhance(brightness)

    return output_image, ascii_string


def add_market_overlay(ascii_image, market_data, font_size=48):
    """
    在 ASCII 图像上叠加市场数据文字
    """
    draw = ImageDraw.Draw(ascii_image)
    width, height = ascii_image.size

    # 半透明黑色背景条
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # 顶部条
    overlay_draw.rectangle([(0, 0), (width, 120)], fill=(0, 0, 0, 180))

    # 底部条
    overlay_draw.rectangle([(0, height - 100), (width, height)], fill=(0, 0, 0, 180))

    # 合成
    ascii_image = Image.alpha_composite(ascii_image.convert("RGBA"), overlay).convert(
        "RGB"
    )

    draw = ImageDraw.Draw(ascii_image)

    # 绘制文字
    headline = market_data.get("headline", "")
    metrics = market_data.get("metrics", [])
    timestamp = market_data.get("timestamp", "")

    # 顶部标题
    for dx in range(8):
        for dy in range(8):
            draw.text((30 + dx, 30 + dy), headline, fill="#ffffff")

    # 底部指标
    metric_text = " | ".join(metrics)
    for dx in range(4):
        for dy in range(4):
            draw.text((30 + dx, height - 70 + dy), metric_text, fill="#00ff00")

    # 时间戳
    for dx in range(2):
        for dy in range(2):
            draw.text((width - 200 + dx, height - 35 + dy), timestamp, fill="#888888")

    return ascii_image


def generate_stock_ascii_viz(source_image, market_data, output_path, emotion="bull"):
    """
    生成股票 ASCII 可视化

    source_image: 图像路径或 PIL Image
    market_data: {
        'headline': '主标题',
        'metrics': ['指标1', '指标2'],
        'timestamp': '时间'
    }
    emotion: 'bull' | 'bear' | 'neutral'
    """
    # 根据情绪选择参数
    if emotion == "bull":
        char_set = "bull"
        rgb_limit = (100, 255, 100)  # 增强绿色
        saturation = 1.5
        brightness = 1.2
        bg_color = "#001a00"
    elif emotion == "bear":
        char_set = "bear"
        rgb_limit = (255, 100, 100)  # 增强红色
        saturation = 1.5
        brightness = 1.1
        bg_color = "#1a0000"
    else:
        char_set = "classic"
        rgb_limit = (255, 255, 255)
        saturation = 1.0
        brightness = 1.0
        bg_color = "#0a0a0a"

    # 转换为 ASCII
    ascii_image, ascii_text = image_to_ascii_art(
        source_image,
        char_set=char_set,
        scale=0.3,
        char_width=6,
        char_height=12,
        font_size=8,
        rgb_limit=rgb_limit,
        saturation=saturation,
        brightness=brightness,
        bg_color=bg_color,
    )

    # 叠加市场数据
    final_image = add_market_overlay(ascii_image, market_data)

    # 保存
    final_image.save(output_path, "PNG", quality=95)
    print(f"✓ 生成完成: {output_path}")
    print(f"  尺寸: {final_image.size}")
    print(f"  情绪: {emotion}")

    return output_path, ascii_text


import random as _random


def _generate_video(static_path, args):
    from procedural.engine import Engine
    from procedural.effects import get_effect

    seed = args.seed if args.seed is not None else _random.randint(0, 999999)
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
        description="Stock Pixel-to-ASCII Converter - 像素转ASCII转换器",
    )
    parser.add_argument(
        "emotion",
        nargs="?",
        default="bull",
        choices=["bull", "bear"],
        help="情绪/趋势 (默认 bull)",
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

    test_img = Image.new("RGB", (800, 600), "#000000")
    draw = ImageDraw.Draw(test_img)

    if emotion == "bull":
        for y in range(600):
            ratio = y / 600
            green = int(100 + 155 * ratio)
            draw.line([(0, y), (800, y)], fill=(0, green, 0), width=1)

        for i in range(10):
            x = i * 80
            y_start = 500 - i * 40
            y_end = 500 - (i + 1) * 40
            draw.line([(x, y_start), (x + 80, y_end)], fill="#00ff00", width=5)
    else:
        for y in range(600):
            ratio = y / 600
            red = int(100 + 155 * ratio)
            draw.line([(0, y), (800, y)], fill=(red, 0, 0), width=1)

        for i in range(10):
            x = i * 80
            y_start = 100 + i * 40
            y_end = 100 + (i + 1) * 40
            draw.line([(x, y_start), (x + 80, y_end)], fill="#ff0000", width=5)

    market_data = {
        "headline": "US STOCKS" if emotion == "bull" else "MARKET DOWN",
        "metrics": ["DOW +0.6%", "PMI 52.6", "FEB 2 2026"]
        if emotion == "bull"
        else ["DOW -2.1%", "VIX +18%", "FEB 2 2026"],
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }

    output = f"media/stock_pixel_ascii_{emotion}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    generate_stock_ascii_viz(test_img, market_data, output, emotion=emotion)

    if args.video:
        print("🎬 生成视频...")
        output = _generate_video(output, args)
        print(f"📁 视频: {output}")
