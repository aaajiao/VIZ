# Rendering Pipeline（渲染管线）

从 160×160 ASCII 网格到 1080×1080 最终图像的完整渲染流程。

## 管线概览

```
1. Engine 创建 Context + Buffer
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
5. buffer_to_image(buffer) → 低分辨率 PIL Image
        │
        ▼
6. upscale_image(img, 1080×1080) — NEAREST 插值
        │
        ▼
7. 精灵层渲染 (Kaomoji, Text, Decoration, Particle)
        │
        ▼
8. 后处理 (Sharpen + Contrast)
        │
        ▼
9. 最终 PIL Image (1080×1080)
```

**关键设计：** 精灵在上采样 **之后** 渲染，坐标空间为输出分辨率（1080×1080）。

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
| `internal_size` | (160, 160) | 内部渲染分辨率 |
| `output_size` | (1080, 1080) | 最终输出分辨率 |
| `char_size` | 1 | 像素/字符 |
| `gradient_name` | — | ASCII 字符梯度选择 |
| `color_scheme` | — | 颜色映射方案 |
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

### render_video() & save_gif()

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
3. 字体：DejaVuSansMono（等宽）

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
| 内部网格 | 160 × 160 | Effect 的 (x, y) 参数 |
| Buffer | 160 × 160 | Cell 二维数组 |
| 低分辨率图像 | 160 × 160 | buffer_to_image 输出 |
| 输出分辨率 | 1080 × 1080 | upscale 后、精灵坐标、最终输出 |

精灵的 `(x, y)` 始终在输出分辨率空间（1080×1080）。
