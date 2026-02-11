# Rendering Pipeline（渲染管线）

从 ASCII 网格到最终图像的完整渲染流程（默认 160×160 → 1080×1080，分辨率可配置）。

## 管线概览

```
1. Engine 创建 Context + Buffer
        │
        ▼
1b. [可选] TransformedEffect 包装效果（域变换）
        │
        ▼
2. Effect.pre(ctx, buffer) → state
        │
        ▼
3. 逐像素: buffer[y][x] = Effect.main(x, y, ctx, state)
        │
        ▼
4. Effect.post(ctx, buffer, state)
        │
        ▼
4b. [可选] PostFX 链（buffer 级后处理）
        │
        ▼
4c. Cell 去别名 + bg_fill 第二渲染通道（背景填充）
        │
        ▼
4d. 情感亮度缩放（brightness + saturation → dim_factor）
        │
        ▼
5. buffer_to_image(buffer) → 低分辨率 PIL Image
        │
        ▼
6. upscale_image(img, output_size) — NEAREST 插值
        │
        ▼
7. 精灵层渲染 (Kaomoji, Text, Decoration[frame/grid/circuit], Particle)
        │
        ▼
8. 后处理 (Sharpen + Contrast)
        │
        ▼
9. 最终 PIL Image (output_size)
```

**关键设计：** 精灵在上采样 **之后** 渲染，坐标空间为输出分辨率（默认 1080×1080，可配置）。

---

## 核心类型

`procedural/types.py`

### Context

渲染上下文，传递给所有效果方法：

```python
@dataclass
class Context:
    width: int          # 网格宽度 (160)
    height: int         # 网格高度 (160)
    time: float         # 时间（秒），用于动画
    frame: int          # 帧序号（0 起始）
    seed: int           # 随机种子
    rng: random.Random  # 种子化的 RNG 实例
    params: dict        # 效果参数（frequency, speed, warmth, ...）
```

### Cell

单个 ASCII 像素：

```python
@dataclass
class Cell:
    char_idx: int           # 字符梯度索引 (0-9)
    fg: tuple[int,int,int]  # 前景色 RGB (0-255)
    bg: tuple | None        # 背景色 RGB 或 None（透明）
```

### Buffer

二维 Cell 数组：

```python
Buffer = list[list[Cell]]   # buffer[y][x] → Cell
```

---

## Engine

`procedural/engine.py`

### 关键属性

| 属性 | 默认值 | 说明 |
|------|--------|------|
| `internal_size` | (160, 160) | 内部渲染分辨率（可配置，自动按输出 ÷ 6.75 计算） |
| `output_size` | (1080, 1080) | 最终输出分辨率（可配置，120-3840px） |
| `char_size` | 1 | 像素/字符 |
| `gradient_name` | — | ASCII 字符梯度选择 |
| `color_scheme` | `"heat"` | 颜色方案（传给 bg_fill + buffer_to_image） |
| `sharpen` | — | 是否锐化 |
| `contrast` | — | 对比度增强 |

### render_frame()

```python
def render_frame(self, effect, sprites, time, frame, seed, params) -> Image:
    # 1. 创建 Context
    ctx = Context(width=w, height=h, time=time, frame=frame,
                  seed=seed, rng=Random(seed), params=params)

    # 2. 初始化空 Buffer
    buffer = self._init_buffer(w, h)

    # 3. 预处理
    state = effect.pre(ctx, buffer)

    # 4. 逐像素渲染
    for y in range(h):
        for x in range(w):
            buffer[y][x] = effect.main(x, y, ctx, state)

    # 5. 后处理
    effect.post(ctx, buffer, state)

    # 5b. PostFX 链（注入 _time 实现动画）
    for fx in postfx_chain:
        fx_kwargs["_time"] = ctx.time
        POSTFX_REGISTRY[fx["type"]](buffer, **fx_kwargs)

    # 5c-pre. Cell 去别名（防止共享引用导致多次缩放）
    for y, x: buffer[y][x] = Cell(cell.char_idx, cell.fg, cell.bg)

    # 5c-fill. bg_fill 第二渲染通道
    #   在临时 buffer 上跑独立 effect（可带 transform/postfx/mask），
    #   提取 char_idx 强度 → color scheme 着色 → dim → 写入 cell.bg
    from procedural.bg_fill import bg_fill
    bg_fill(buffer, w, h, seed, bg_fill_spec)

    # 5c. 情感亮度缩放
    dim_factor = brightness * sat_adjust + jitter
    for cell in buffer: cell.fg *= dim_factor; cell.bg *= dim_factor

    # 6. Buffer → Image
    img = buffer_to_image(buffer, ...)

    # 7. 上采样（NEAREST 保持像素感）
    img = upscale_image(img, self.output_size)

    # 8. 渲染精灵（在输出分辨率上）
    for sprite in sprites:
        sprite.render(img, time=time)

    # 9. 后处理
    img = self._postprocess(img)

    return img
```

### render_video(), save_gif() & save_mp4()

```python
def render_video(self, effect, duration, fps, sprites, seed):
    frames = []
    for i in range(int(duration * fps)):
        t = i / fps
        frame = self.render_frame(effect, sprites, time=t, frame=i, seed=seed)
        frames.append(frame)
    return frames

def save_gif(self, frames, output_path, fps):
    frames[0].save(output_path, save_all=True, append_images=frames[1:],
                   duration=1000/fps, loop=0, optimize=True)

def save_mp4(self, frames, output_path, fps):
    """Convert frames to MP4 via FFmpeg subprocess. Returns False if FFmpeg unavailable."""
    # 1. Save frames as temp GIF
    # 2. Run: ffmpeg -y -i temp.gif -movflags faststart -pix_fmt yuv420p output.mp4
    # 3. Gracefully degrades to GIF-only if FFmpeg not installed
```

---

## Renderer

`procedural/renderer.py`

### buffer_to_image()

将 ASCII 网格转换为 PIL Image：

1. 创建黑色 RGB 画布 (`width * char_size`, `height * char_size`)
2. 对每个 Cell：
   - 绘制背景矩形（如果 `bg` 不为 None）
   - `char_idx / 9.0` 归一化 → `palette.char_at_value()` 获取字符
   - 用前景色渲染字符
3. 字体：DejaVuSansMono（等宽，覆盖 Box Drawing / Block Elements / Braille 等 Unicode 区块）

**ASCII 梯度选择：** 系统提供 73 种梯度（含 box-drawing、block fill、geometric、typography、stars/sparkles、arrows、cp437 等，覆盖 450+ 个 Unicode 字符），全部由 grammar 的 `_choose_gradient()` 自动选择。数据源统一在 `lib/box_chars.py`，`palette.py` 通过导入获取。详见 [box_chars.md](box_chars.md#2-密度梯度gradients)。

### upscale_image()

```python
def upscale_image(image, target_size):
    return image.resize(target_size, Image.NEAREST)
```

使用 `NEAREST` 插值保持像素化 ASCII 美学，不使用 LANCZOS/BILINEAR。

---

## Compositor（效果组合）

`procedural/compositor.py`

将两个效果叠加为一个 `CompositeEffect`：

```python
composite = CompositeEffect(effect_a, effect_b, mode, mix)
```

### BlendMode

| 模式 | 公式 | 视觉效果 |
|------|------|----------|
| `ADD` | `min(255, c1 + c2)` | 叠亮（光效） |
| `MULTIPLY` | `c1 * c2 / 255` | 叠暗（阴影） |
| `SCREEN` | `255 - (255-c1)(255-c2)/255` | 明亮混合 |
| `OVERLAY` | 按通道条件混合 | 对比增强 |

### 工作原理

```python
def pre(ctx, buffer):
    return {"a": effect_a.pre(ctx, buffer),
            "b": effect_b.pre(ctx, buffer)}

def main(x, y, ctx, state):
    cell_a = effect_a.main(x, y, ctx, state["a"])
    cell_b = effect_b.main(x, y, ctx, state["b"])
    # 混合 char_idx 和 fg 颜色
    blended_fg = blend(cell_a.fg, cell_b.fg, mode, mix)
    blended_idx = int(mix_func(cell_a.char_idx, cell_b.char_idx, mix))
    return Cell(blended_idx, blended_fg, None)
```

### MaskedCompositeEffect（遮罩合成）

`procedural/compositor.py`

在传统混合之外，支持基于空间遮罩的区域性合成：

```python
from procedural.compositor import MaskedCompositeEffect
from procedural.masks import RadialMask

masked = MaskedCompositeEffect(
    effect_a=PlasmaEffect(),
    effect_b=WaveEffect(),
    mask=RadialMask(),
    threshold=0.5,
    softness=0.2,
)
```

遮罩的 `char_idx` 值 (0-9) 控制混合权重：0 = 完全 effect_a，9 = 完全 effect_b。

6 种遮罩类型：`horizontal_split`, `vertical_split`, `diagonal`, `radial`, `noise`, `sdf`。

详见 [composition.md](composition.md) 获取完整的合成系统参考。

---

### Composition Layer（合成层）

渲染管线在基础效果之上增加了四层可选合成：

1. **合成/遮罩** — `CompositeEffect` 或 `MaskedCompositeEffect` 混合两个效果
2. **域变换** — `TransformedEffect` 包装效果，在 `main()` 调用前变换坐标（支持动画 kwargs）
3. **PostFX 链** — 7 种 buffer 级后处理效果，在 `effect.post()` 后执行（注入 `_time` 实现帧间动画）
4. **bg_fill 第二渲染通道** — 在独立临时 buffer 上运行另一个 effect（含 variant/transform/postfx/mask/color scheme），填充 `bg=None` 的 cell 背景色（~750k 种纹理组合）

```
Effect → [Composite/Masked] → [TransformedEffect] → PostFX chain(_time) → bg_fill → brightness → buffer_to_image
```

所有合成参数由文法系统（`VisualGrammar`）自动选择。三层合成均支持时间驱动动画：transforms 使用动画 kwargs、PostFX 接收 `_time`、masks 读取 `mask_anim_speed`。bg_fill 规格由 `_choose_bg_fill_spec()` 独立产生。详见 [composition.md](composition.md)。

---

## Sprite System（精灵系统）

`procedural/layers.py`

### 基类 Sprite

```python
@dataclass
class Sprite:
    x: float                # X 坐标（输出分辨率空间）
    y: float                # Y 坐标
    scale: float = 1.0      # 缩放
    color: str | tuple      # 颜色
    rotation: float = 0.0   # 保留字段
    visible: bool = True
    animations: list        # 动画配置列表
```

### TextSprite

文本精灵，支持光晕效果：

```python
TextSprite(x=540, y=100, text="BULL", color=(0, 255, 0),
           glow_color=(0, 128, 0), glow_size=4)
```

渲染流程：
1. 多偏移绘制光晕层（`glow_color`，在 `[-glow_size, +glow_size]` 范围）
2. 居中绘制主文本（`color`）

### KaomojiSprite

颜文字精灵，详见 [kaomoji.md](kaomoji.md)。

### 动画函数

| 函数 | 公式 | 返回值 |
|------|------|--------|
| `breathing(t, amp, speed)` | `1 + amp * sin(t * speed)` | 缩放因子 |
| `floating(t, amp, speed, phase)` | `amp * sin(t * speed + phase)` | Y 偏移（像素） |
| `color_cycle(t, base_hue, speed)` | HSV 色相旋转 | RGB 元组 |

---

## 核心工具库

### ValueNoise (`procedural/core/noise.py`)

```python
noise = ValueNoise(seed=42, size=256)

value = noise(x, y)                        # 2D 噪声 [0, 1]
value = noise.fbm(x, y, octaves=4)         # 分形布朗运动
value = noise.turbulence(x, y, octaves=4)  # 湍流噪声
```

- 排列表 + 平滑插值（smoothstep）
- FBM：多层叠加，频率递增 × lacunarity，振幅递减 × gain
- 湍流：FBM 但取绝对值（锐利边缘）

### mathx (`procedural/core/mathx.py`)

GLSL 风格数学工具：

| 函数 | 说明 |
|------|------|
| `clamp(v, lo, hi)` | 截断到范围 |
| `mix(a, b, t)` | 线性插值 `a*(1-t) + b*t` |
| `smoothstep(e0, e1, x)` | Hermite S 曲线 |
| `smootherstep(e0, e1, x)` | Perlin 改进版 |
| `map_range(v, in_lo, in_hi, out_lo, out_hi)` | 线性范围映射 |
| `fract(x)` | 小数部分 |
| `step(edge, x)` | 阶跃函数 |
| `pulse(e0, e1, x)` | 脉冲函数 |

常量：`PI`, `TAU` (2π), `HALF_PI` (π/2)

---

## 坐标空间

| 空间 | 分辨率 | 用于 |
|------|--------|------|
| 内部网格 | 默认 160 × 160（可配置） | Effect 的 (x, y) 参数 |
| Buffer | 同内部网格 | Cell 二维数组 |
| 低分辨率图像 | 同内部网格 | buffer_to_image 输出 |
| 输出分辨率 | 默认 1080 × 1080（可配置） | upscale 后、精灵坐标、最终输出 |

精灵的 `(x, y)` 始终在输出分辨率空间。
