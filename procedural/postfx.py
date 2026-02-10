"""
后处理特效链 - Post-Processing FX Chain

缓冲区级别的后处理效果，在 effect.post() 后、buffer_to_image() 前执行。
修改 160x160 Cell 网格，每个效果遍历缓冲区一次。

Buffer-level post-processing effects applied after effect.post()
but before buffer_to_image(). Operates on the 160x160 Cell grid.

用法::

    from procedural.postfx import postfx_invert, postfx_scanlines, POSTFX_REGISTRY

    # 直接调用
    postfx_invert(buffer)
    postfx_scanlines(buffer, spacing=4, darkness=0.3)

    # 通过注册表
    fx = POSTFX_REGISTRY['vignette']
    fx(buffer, strength=0.6)
"""

import math

try:
    from procedural.types import Cell
except ImportError:
    from viz.procedural.types import Cell

try:
    from procedural.core.mathx import clamp
except ImportError:
    from viz.procedural.core.mathx import clamp

__all__ = [
    "postfx_threshold",
    "postfx_invert",
    "postfx_edge_detect",
    "postfx_scanlines",
    "postfx_vignette",
    "postfx_pixelate",
    "postfx_color_shift",
    "POSTFX_REGISTRY",
]


# ==================== 后处理效果函数 ====================


def postfx_threshold(buffer, threshold=0.5):
    """二值化 - Binary threshold on char_idx"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    thresh_idx = int(threshold * 9)
    for y in range(h):
        for x in range(w):
            cell = buffer[y][x]
            new_idx = 9 if cell.char_idx >= thresh_idx else 0
            buffer[y][x] = Cell(char_idx=new_idx, fg=cell.fg, bg=cell.bg)


def postfx_invert(buffer):
    """反转 - Invert char_idx and colors"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    for y in range(h):
        for x in range(w):
            cell = buffer[y][x]
            new_idx = 9 - cell.char_idx
            inv_fg = (255 - cell.fg[0], 255 - cell.fg[1], 255 - cell.fg[2])
            inv_bg = None
            if cell.bg is not None:
                inv_bg = (255 - cell.bg[0], 255 - cell.bg[1], 255 - cell.bg[2])
            buffer[y][x] = Cell(char_idx=new_idx, fg=inv_fg, bg=inv_bg)


def postfx_edge_detect(buffer):
    """边缘检测 - Sobel on char_idx for edge outlines"""
    h = len(buffer)
    if h < 3:
        return
    w = len(buffer[0])
    if w < 3:
        return
    # Snapshot char_idx values before modification
    vals = [[buffer[y][x].char_idx for x in range(w)] for y in range(h)]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            # Sobel kernels
            gx = (vals[y - 1][x + 1] + 2 * vals[y][x + 1] + vals[y + 1][x + 1]) - \
                 (vals[y - 1][x - 1] + 2 * vals[y][x - 1] + vals[y + 1][x - 1])
            gy = (vals[y + 1][x - 1] + 2 * vals[y + 1][x] + vals[y + 1][x + 1]) - \
                 (vals[y - 1][x - 1] + 2 * vals[y - 1][x] + vals[y - 1][x + 1])
            mag = min(9, int(abs(gx) + abs(gy)))
            cell = buffer[y][x]
            buffer[y][x] = Cell(char_idx=mag, fg=cell.fg, bg=cell.bg)


def postfx_scanlines(buffer, spacing=4, darkness=0.3):
    """扫描线 - Horizontal scanline darkening"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    factor = 1.0 - darkness
    for y in range(h):
        if y % spacing == 0:
            for x in range(w):
                cell = buffer[y][x]
                dim_fg = (
                    int(cell.fg[0] * factor),
                    int(cell.fg[1] * factor),
                    int(cell.fg[2] * factor),
                )
                new_idx = max(0, int(cell.char_idx * factor))
                buffer[y][x] = Cell(char_idx=new_idx, fg=dim_fg, bg=cell.bg)


def postfx_vignette(buffer, strength=0.5):
    """暗角 - Darken edges"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    cx = w / 2.0
    cy = h / 2.0
    max_dist = math.sqrt(cx * cx + cy * cy)
    if max_dist == 0:
        return
    for y in range(h):
        for x in range(w):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            nd = dist / max_dist
            factor = max(0.0, 1.0 - strength * nd * nd)
            cell = buffer[y][x]
            dim_fg = (
                int(cell.fg[0] * factor),
                int(cell.fg[1] * factor),
                int(cell.fg[2] * factor),
            )
            new_idx = max(0, int(cell.char_idx * factor))
            buffer[y][x] = Cell(char_idx=new_idx, fg=dim_fg, bg=cell.bg)


def postfx_pixelate(buffer, block_size=4):
    """像素化 - Average blocks for lower resolution effect"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    for by in range(0, h, block_size):
        for bx in range(0, w, block_size):
            total_idx = 0
            total_r, total_g, total_b = 0, 0, 0
            count = 0
            for dy in range(min(block_size, h - by)):
                for dx in range(min(block_size, w - bx)):
                    cell = buffer[by + dy][bx + dx]
                    total_idx += cell.char_idx
                    total_r += cell.fg[0]
                    total_g += cell.fg[1]
                    total_b += cell.fg[2]
                    count += 1
            if count > 0:
                avg_idx = total_idx // count
                avg_fg = (total_r // count, total_g // count, total_b // count)
                avg_cell = Cell(char_idx=avg_idx, fg=avg_fg, bg=None)
                for dy in range(min(block_size, h - by)):
                    for dx in range(min(block_size, w - bx)):
                        buffer[by + dy][bx + dx] = avg_cell


def postfx_color_shift(buffer, hue_shift=0.1):
    """色相偏移 - Shift hue channel via YIQ-like rotation"""
    h = len(buffer)
    if h == 0:
        return
    w = len(buffer[0])
    if w == 0:
        return
    angle = hue_shift * 2 * math.pi
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    for y in range(h):
        for x in range(w):
            cell = buffer[y][x]
            r, g, b = cell.fg
            # Luminance-preserving hue rotation in RGB space
            nr = int(clamp(
                r * (0.299 + 0.701 * cos_a + 0.168 * sin_a) +
                g * (0.587 - 0.587 * cos_a + 0.330 * sin_a) +
                b * (0.114 - 0.114 * cos_a - 0.497 * sin_a),
                0, 255))
            ng = int(clamp(
                r * (0.299 - 0.299 * cos_a - 0.328 * sin_a) +
                g * (0.587 + 0.413 * cos_a + 0.035 * sin_a) +
                b * (0.114 - 0.114 * cos_a + 0.292 * sin_a),
                0, 255))
            nb = int(clamp(
                r * (0.299 - 0.300 * cos_a + 1.250 * sin_a) +
                g * (0.587 - 0.588 * cos_a - 1.050 * sin_a) +
                b * (0.114 + 0.886 * cos_a - 0.203 * sin_a),
                0, 255))
            buffer[y][x] = Cell(char_idx=cell.char_idx, fg=(nr, ng, nb), bg=cell.bg)


# ==================== 后处理注册表 ====================

POSTFX_REGISTRY = {
    "threshold": postfx_threshold,
    "invert": postfx_invert,
    "edge_detect": postfx_edge_detect,
    "scanlines": postfx_scanlines,
    "vignette": postfx_vignette,
    "pixelate": postfx_pixelate,
    "color_shift": postfx_color_shift,
}
"""
全局后处理注册表 - Global PostFX Registry

存储所有已注册的后处理效果函数。
"""
