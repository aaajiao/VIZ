"""
渲染器 - ASCII Buffer to PIL Image Renderer

将 ASCII 字符缓冲区转换为 PIL 图像，支持字符绘制、颜色映射和图像上采样。

核心功能::

    buffer_to_image()  - 将 Buffer 渲染为 PIL Image
    upscale_image()    - 上采样图像到目标分辨率

用法示例::

    from procedural.types import Cell, Buffer
    from procedural.renderer import buffer_to_image, upscale_image
    from procedural.palette import char_at_value, value_to_color

    # 创建测试 buffer
    buffer: Buffer = []
    for y in range(10):
        row = []
        for x in range(10):
            value = (x + y) / 18.0
            char_idx = int(value * 9)
            fg = value_to_color(value, 'heat')
            row.append(Cell(char_idx, fg, None))
        buffer.append(row)

    # 渲染为 PIL Image
    img = buffer_to_image(
        buffer,
        char_size=10,
        gradient_name='classic',
        color_scheme='heat'
    )
    print(img.size)  # (100, 100)

    # 上采样到 Instagram 尺寸
    img_large = upscale_image(img, (1080, 1080))
    img_large.save('/workspace/media/test.png')
"""

from PIL import Image, ImageDraw, ImageFont
from .types import Buffer, Cell
from .palette import char_at_value

__all__ = [
    "buffer_to_image",
    "upscale_image",
]


def buffer_to_image(
    buffer: Buffer,
    char_size: int = 10,
    gradient_name: str = "default",
    color_scheme: str = "heat",
) -> Image.Image:
    """
    将 ASCII 字符缓冲区渲染为 PIL 图像

    Args:
        buffer: 2D 字符缓冲区 (list[list[Cell]])
        char_size: 每个字符的像素尺寸 (宽高相等)
        gradient_name: ASCII 梯度名称 (用于 char_idx → char 映射)
        color_scheme: 颜色方案名称 (当前未使用，颜色由 Cell.fg/bg 提供)

    Returns:
        PIL.Image.Image: 渲染后的图像

    示例::

        buffer = [[Cell(5, (255, 255, 255), (0, 0, 0)) for _ in range(10)] for _ in range(10)]
        img = buffer_to_image(buffer, char_size=10, gradient_name='classic')
        img.save('output.png')

    注意:
        - Cell.char_idx 通过 palette.char_at_value() 映射到实际字符
        - Cell.bg 为 None 时背景透明 (保持黑色)
        - 使用 DejaVuSansMono 等宽字体，失败则使用默认字体
    """
    if not buffer or not buffer[0]:
        raise ValueError("Buffer is empty")

    # 计算图像尺寸
    rows = len(buffer)
    cols = len(buffer[0])
    width = cols * char_size
    height = rows * char_size

    # 创建黑色背景图像
    img = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 尝试加载等宽字体
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", char_size
        )
    except (IOError, OSError):
        font = ImageFont.load_default()

    # 逐字符渲染
    for y in range(rows):
        for x in range(cols):
            cell = buffer[y][x]

            px = x * char_size
            py = y * char_size

            # 绘制背景色 (如果有)
            if cell.bg is not None:
                draw.rectangle(
                    [px, py, px + char_size, py + char_size],
                    fill=cell.bg,
                )

            # 将 char_idx 映射到实际字符
            # char_idx 是梯度索引 (0-9)，需要通过 gradient 转换
            # 使用归一化值 (char_idx / 9.0) 调用 char_at_value
            normalized_value = cell.char_idx / 9.0
            char = char_at_value(normalized_value, gradient_name)

            # 绘制字符 (跳过空格以提高性能)
            if char and char != " ":
                draw.text((px, py), char, fill=cell.fg, font=font)

    return img


def upscale_image(image: Image.Image, target_size: tuple[int, int]) -> Image.Image:
    """
    上采样图像到目标分辨率 (保持像素化效果)

    Args:
        image: 源 PIL 图像
        target_size: 目标尺寸 (width, height)

    Returns:
        PIL.Image.Image: 上采样后的图像

    示例::

        small_img = Image.new('RGB', (100, 100), (0, 0, 0))
        large_img = upscale_image(small_img, (1080, 1080))
        print(large_img.size)  # (1080, 1080)

    注意:
        - 使用 NEAREST 插值保持像素化/ASCII 艺术风格
        - 不使用 LANCZOS/BILINEAR 以避免模糊
    """
    return image.resize(target_size, Image.Resampling.NEAREST)
