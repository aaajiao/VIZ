"""
图像转 ASCII 艺术 - Image to ASCII art converter

逐像素将真实图像转换为彩色 ASCII 字符画。
Converts real images to colored ASCII art pixel by pixel.

从 stock_pixel_ascii.py 提取的核心功能。
"""

import math

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


# ========== 字符集（按密度从亮到暗）==========
CHAR_SETS = {
    "classic": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "simple": " .:-=+*#%@",
    "blocks": " ░▒▓█",
    "bull": " .+*$↑▲🚀",
    "bear": " .+*$↓▼📉",
    "numbers": " 0123456789",
    "money": " .,;:¥$€£₿",
}


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
    将图像转换为 ASCII 艺术 - Convert image to ASCII art

    Args:
        image_path_or_obj: 图像路径或 PIL Image 对象
        char_set: 字符集名称或自定义字符串
        scale: 缩放比例（越小越快）
        char_width/char_height: 每个字符的像素尺寸
        font_size: 字体大小
        rgb_limit: RGB 上限 (r, g, b)
        saturation: 饱和度
        brightness: 亮度
        bg_color: 背景色
        custom_font: 自定义字体路径
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
    在 ASCII 图像上叠加市场数据文字 - Overlay market data text on ASCII image

    Args:
        ascii_image: PIL Image 对象
        market_data: dict with 'headline', 'metrics', 'timestamp'
        font_size: 字体大小
    """
    draw = ImageDraw.Draw(ascii_image)
    width, height = ascii_image.size

    # 半透明黑色背景条
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle(
        [(0, height - 120), (width, height)], fill=(0, 0, 0, 180)
    )
    ascii_image.paste(
        Image.alpha_composite(ascii_image.convert("RGBA"), overlay).convert("RGB")
    )

    draw = ImageDraw.Draw(ascii_image)

    try:
        font_large = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", font_size
        )
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size // 2
        )
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 标题
    headline = market_data.get("headline", "")
    if headline:
        draw.text((20, height - 110), headline, font=font_large, fill=(255, 255, 255))

    # 指标
    metrics = market_data.get("metrics", [])
    x_offset = 20
    for metric in metrics:
        draw.text(
            (x_offset, height - 50), metric, font=font_small, fill=(200, 200, 200)
        )
        x_offset += len(metric) * font_size // 3 + 20

    # 时间戳
    timestamp = market_data.get("timestamp", "")
    if timestamp:
        draw.text(
            (width - 200, height - 50),
            timestamp,
            font=font_small,
            fill=(150, 150, 150),
        )

    return ascii_image
