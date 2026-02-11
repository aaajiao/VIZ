# Effect Composition System（效果合成系统）

效果合成系统为视觉输出提供四层可组合的结构变换，将基础效果从有限集合扩展到无限连续的视觉空间。本文档是合成子系统的权威参考。

The composition system provides four composable layers of structural transformation, expanding the base effect set from a finite collection into an infinite continuous visual space. This document is the authoritative reference for the composition subsystem.

```
                        ┌─────────────────────────┐
                        │   Base Effect (17 种)    │
                        │   procedural/effects/    │
                        └────────────┬────────────┘
                                     │
                   ┌─────────────────┼─────────────────┐
                   ▼                 ▼                   ▼
          ┌────────────────┐ ┌──────────────┐ ┌──────────────────┐
          │ Structural     │ │ Composition  │ │ Domain           │
          │ Variants       │ │ (Blend/Mask) │ │ Transforms       │
          │ variants.py    │ │ compositor.py│ │ transforms.py    │
          └────────────────┘ │ masks.py     │ └──────────────────┘
                             └──────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │   PostFX Chain           │
                        │   postfx.py              │
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │   bg_fill 第二渲染通道    │
                        │   procedural/bg_fill.py  │
                        │   (~750k 纹理组合)       │
                        └────────────┬────────────┘
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │   160x160 Buffer         │
                        │   → buffer_to_image()    │
                        └─────────────────────────┘
```

**五层架构 — Five-Layer Architecture:**

1. **Structural Variants** — 基础效果的命名参数预设，提供离散结构变化
2. **Composition** — 双效果混合（BlendMode）或空间遮罩合成（MaskedCompositeEffect）
3. **Domain Transforms** — UV 坐标变换链（镜像、平铺、万花筒等）
4. **PostFX Chain** — 缓冲区级后处理（暗角、扫描线、边缘检测等）
5. **Background Fill** — 第二渲染通道，在临时 buffer 上运行独立 effect + color scheme 着色 → 填充 `bg=None` cell

每层独立概率启用，层间可自由组合。详见 [rendering.md](rendering.md) 管线概览和 [effects.md](effects.md) 基础效果列表。

---

## 1. Domain Transforms（域变换）

`procedural/transforms.py`

坐标变换函数将像素坐标归一化为 UV `[0,1]` 后做几何变换，再转回像素坐标传给内部效果的 `main()` 方法。变换按列表顺序依次链式应用。

### 变换注册表 — TRANSFORM_REGISTRY

| 名称 | 说明 | 参数 |
|------|------|------|
| `mirror_x` | 水平镜像对称 — Horizontal mirror symmetry | 无 |
| `mirror_y` | 垂直镜像对称 — Vertical mirror symmetry | 无 |
| `mirror_quad` | 四象限对称 — Four-fold symmetry | 无 |
| `kaleidoscope` | N 折旋转对称 — N-fold rotational symmetry | `segments=6`, `cx=0.5`, `cy=0.5` |
| `tile` | 平铺重复 — Repeat/tile coordinates | `cols=2`, `rows=2` |
| `rotate` | 绕中心旋转 — Rotate around center | `angle=0.0`, `cx=0.5`, `cy=0.5` |
| `zoom` | 中心缩放 — Zoom in/out from center | `factor=2.0`, `cx=0.5`, `cy=0.5` |
| `spiral_warp` | 螺旋域扭曲 — Spiral domain warp | `twist=1.0`, `cx=0.5`, `cy=0.5` |
| `polar_remap` | 笛卡尔转极坐标 — Cartesian to polar domain | `cx=0.5`, `cy=0.5` |

共 9 种变换，其中 6 种带连续参数。

### TransformedEffect 包装器

`TransformedEffect` 包装任意 Effect 实例，在 `main()` 调用前应用变换链：

```python
from procedural.transforms import TransformedEffect, TRANSFORM_REGISTRY

# 包装任意效果，应用变换链
transformed = TransformedEffect(
    inner_effect=PlasmaEffect(),
    transforms=[
        (kaleidoscope, {'segments': 6}),
        (tile, {'cols': 2, 'rows': 2}),
    ]
)

# TransformedEffect 实现 Effect Protocol，可直接用于渲染
state = transformed.pre(ctx, buffer)
cell = transformed.main(x, y, ctx, state)
```

**执行流程：**

1. 像素坐标 `(x, y)` 归一化为 `u = x / width`, `v = y / height`
2. 按列表顺序依次应用变换函数：`u, v = fn(u, v, **resolved_kwargs)`
3. 结果钳位到 `[0, width-1]` / `[0, height-1]` 并转回整数坐标
4. 用变换后的坐标调用内部效果的 `main(tx, ty, ctx, state)`

`pre()` 和 `post()` 直接委托给内部效果，不做变换。

### 动画 Kwargs — Animated Kwargs

变换参数支持**时间驱动动画**，使 GIF/视频输出中的变换随时间变化。普通标量值（int/float）原样传递；动画规格 dict 在每帧根据 `ctx.time` 求值。

**动画规格格式：**

```python
# 静态 kwargs（传统方式）
{"angle": 0.5}

# 动画 kwargs（GIF 模式下随时间变化）
{"angle": {"base": 0.0, "speed": 0.5, "mode": "linear"}}
```

**三种动画模式：**

| 模式 | 公式 | 用途 |
|------|------|------|
| `linear` | `base + time * speed` | 持续旋转/平移 |
| `oscillate`（默认）| `base + amp * sin(time * speed * TAU)` | 呼吸/脉动 |
| `ping_pong` | `base + amp * triangle(time * speed)` | 来回运动 |

**规格字段：**

| 字段 | 必填 | 默认 | 说明 |
|------|------|------|------|
| `base` | 是 | — | 基础值 |
| `speed` | 是 | — | 速度乘数 |
| `mode` | 否 | `oscillate` | 动画模式 |
| `amp` | 否 | 1.0 | 振幅（oscillate/ping_pong） |

`_resolve_animated_kwargs(kwargs, time)` 在 `TransformedEffect.main()` 中每像素调用，保证 time=0.0（静态 PNG）时输出与传统方式完全一致。

**Grammar 自动生成动画 kwargs：** `_choose_domain_transforms()` 根据 `energy` 参数概率性地将 `rotate`（angle）、`zoom`（factor）、`spiral_warp`（twist）的固定值替换为动画规格。高能量情绪 → 更快动画速度。

---

## 2. Spatial Masks（空间遮罩）

`procedural/masks.py`

空间遮罩为双效果合成提供逐像素的混合权重。每个遮罩实现 Effect Protocol（`pre`/`main`/`post`），其 `main()` 返回的 Cell 的 `char_idx` 值 (0-9) 编码混合权重：

- `char_idx = 0` → 完全使用 effect_a
- `char_idx = 9` → 完全使用 effect_b
- 中间值 → 平滑插值

### 遮罩注册表 — MASK_REGISTRY

| 名称 | 说明 | 专用参数 |
|------|------|----------|
| `horizontal_split` | 上下分割 — Top vs bottom split | — |
| `vertical_split` | 左右分割 — Left vs right split | — |
| `diagonal` | 对角分割 — Diagonal split | `mask_angle` |
| `radial` | 径向渐变 — Center vs edges radial gradient | `mask_center_x`, `mask_center_y`, `mask_radius`, `mask_invert` |
| `noise` | 噪声有机斑块 — Organic blobs via ValueNoise fbm | `mask_noise_scale`, `mask_noise_octaves`, `mask_threshold`, `mask_seed_offset` |
| `sdf` | SDF 几何形状 — Circle/box/ring geometric shapes | `mask_sdf_shape`, `mask_sdf_size`, `mask_sdf_thickness`, `mask_invert` |

共 6 种遮罩。

**通用参数（所有遮罩共享）：**

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `mask_split` | 0.5 | 分割位置 (用于 split/diagonal 类型) |
| `mask_softness` | 0.05-0.15 | 过渡柔和度（smoothstep 宽度） |
| `mask_anim_speed` | 0.0 | 动画速度（0 = 静态，>0 = 随时间变化） |

所有遮罩在边界区域使用 `smoothstep()` 实现平滑过渡，`mask_softness` 控制过渡宽度。

### 遮罩动画 — Mask Animation

当 `mask_anim_speed > 0` 且 `ctx.time > 0` 时，各遮罩在 GIF/视频输出中产生帧间变化：

| 遮罩 | 动画效果 | 公式 |
|------|---------|------|
| `horizontal_split` | 分割线上下扫动 | `split += 0.15 * sin(t * speed * 2π)` |
| `vertical_split` | 分割线左右扫动 | `split += 0.15 * sin(t * speed * 2π)` |
| `diagonal` | 对角线旋转 | `angle += t * speed * 0.5` |
| `radial` | 径向边界脉动 | `radius += 0.1 * sin(t * speed * 2π)` |
| `noise` | 有机形态漂移 | 噪声坐标加 `t * speed * 10.0` 偏移 |
| `sdf` | 几何形状脉动 | `size += 0.08 * sin(t * speed * 2π)` |

`mask_anim_speed=0`（默认）保持完全静态，向后兼容。Split 值自动钳位到 `[0.1, 0.9]`，radius/size 钳位到安全范围。

### MaskedCompositeEffect

`procedural/compositor.py`

使用空间遮罩控制两个效果的逐像素混合：

```python
from procedural.compositor import MaskedCompositeEffect
from procedural.masks import MASK_REGISTRY

mask = MASK_REGISTRY['radial']()
composite = MaskedCompositeEffect(
    effect_a=PlasmaEffect(),
    effect_b=WaveEffect(),
    mask=mask,
    threshold=0.5,
    softness=0.2,
)
```

**逐像素执行流程：**

```python
def main(x, y, ctx, state):
    cell_a = effect_a.main(x, y, ctx, state["a"])
    cell_b = effect_b.main(x, y, ctx, state["b"])
    mask_cell = mask.main(x, y, ctx, state["mask"])

    # 遮罩值归一化
    mask_val = mask_cell.char_idx / 9.0

    # Smoothstep 过渡
    t = smoothstep(threshold - softness, threshold + softness, mask_val)

    # 插值：fg 颜色、char_idx、bg 颜色
    final_fg = lerp(cell_a.fg, cell_b.fg, t)
    final_char_idx = lerp(cell_a.char_idx, cell_b.char_idx, t)
    return Cell(final_char_idx, final_fg, final_bg)
```

每帧渲染三个子效果（effect_a、effect_b、mask），计算量约为单效果的 3 倍。

---

## 3. PostFX Chain（后处理特效链）

`procedural/postfx.py`

缓冲区级别的后处理效果，在 `effect.post()` 之后、`buffer_to_image()` 之前执行。操作 160x160 的 Cell 网格（不是像素图像），每个效果遍历缓冲区一次。

### 管线位置 — Pipeline Position

```
effect.pre(ctx, buffer) → state
    ↓
effect.main(x, y, ctx, state) → buffer[y][x]   (逐像素)
    ↓
effect.post(ctx, buffer, state)
    ↓
★ PostFX Chain ★   ← params["_postfx_chain"]
    ↓
buffer_to_image(buffer) → 低分辨率 PIL Image
    ↓
upscale → sprites → sharpen + contrast → 最终输出
```

PostFX 链通过 `params["_postfx_chain"]` 传递给 Engine，Engine 在 `render_frame()` 中按列表顺序逐个执行。参见 [rendering.md](rendering.md) 完整管线。

### 后处理注册表 — POSTFX_REGISTRY

| 名称 | 说明 | 参数 | 动画参数 |
|------|------|------|----------|
| `threshold` | 二值化 — Binary threshold on char_idx | `threshold=0.5` | — |
| `invert` | 反转 — Invert char_idx and colors | 无 | — |
| `edge_detect` | Sobel 边缘检测 — Edge outlines via Sobel operator | 无 | — |
| `scanlines` | 水平扫描线 — Horizontal scanline darkening | `spacing=4`, `darkness=0.3` | `scroll_speed` |
| `vignette` | 暗角 — Darken edges | `strength=0.5` | `pulse_speed`, `pulse_amp` |
| `pixelate` | 像素化 — Average blocks for lower resolution | `block_size=4` | `pulse_speed`, `pulse_amp` |
| `color_shift` | 色相偏移 — Hue rotation via YIQ-like transform | `hue_shift=0.1` | `drift_speed` |

共 7 种后处理效果，其中 4 种支持时间动画。

**关键特征：**

- 操作 Cell 网格（char_idx + fg RGB + bg RGB），不是像素图像
- 分辨率固定为 160x160（内部渲染分辨率）
- 链内顺序有意义：先 `threshold` 再 `edge_detect` 与反序结果不同
- 每个效果独立概率启用（参见 Grammar Integration 节），7 种效果理论上有 2^7 = 128 种开关组合

### PostFX 动画参数 — Animation Parameters

4 种 PostFX 支持时间驱动动画（GIF/视频模式下帧间变化）：

| PostFX | 动画参数 | 默认 | 效果 |
|--------|---------|------|------|
| `scanlines` | `scroll_speed` | 0.0 | 扫描线随时间滚动（offset = time × speed × spacing） |
| `vignette` | `pulse_speed`, `pulse_amp` | 0.0, 0.0 | 暗角强度正弦脉动 |
| `pixelate` | `pulse_speed`, `pulse_amp` | 0.0, 0.0 | 块大小正弦脉动 |
| `color_shift` | `drift_speed` | 0.0 | 色相随时间线性漂移 |

动画参数默认为 0（静态），Grammar 根据 `energy` 参数概率性地注入动画值。所有函数通过 `**_kw` 容错未知 kwargs，`_time=None` 默认确保向后兼容。

### Engine 集成

```python
# engine.py render_frame() 中的执行逻辑
postfx_chain = params.get("_postfx_chain", [])
if postfx_chain:
    from procedural.postfx import POSTFX_REGISTRY
    for fx in postfx_chain:
        fx_type = fx.get("type", "")
        fx_fn = POSTFX_REGISTRY.get(fx_type)
        if fx_fn:
            kwargs = {k: v for k, v in fx.items() if k != "type"}
            kwargs["_time"] = ctx.time  # 注入当前时间
            fx_fn(buffer, **kwargs)
```

---

## 4. Structural Variants（结构变体）

`procedural/effects/variants.py`

为基础效果提供命名参数预设（"变体"），每个变体定义一组参数范围。文法系统按权重选择变体，然后在范围内均匀采样具体参数值。

### VARIANT_REGISTRY 格式

```python
VARIANT_REGISTRY = {
    "effect_name": [
        {
            "name": "variant_name",
            "weight": 0.2,           # 选择权重（在同效果变体中）
            "params": {
                "param_a": (min, max),   # 连续范围 → uniform 采样
                "param_b": (int_min, int_max),  # 整数范围 → randint 采样
            },
        },
        # ...
    ],
}
```

### 86 个命名变体总览

| 效果 | 变体数 | 变体名称 |
|------|--------|----------|
| `donut` | 6 | classic, alien, thin_ring, fat_blob, multi, twisted |
| `wireframe_cube` | 4 | classic, irregular, morphing, deformed |
| `plasma` | 5 | classic, warped, noisy, turbulent, slow_morph |
| `wave` | 4 | classic, warped, chaotic, minimal |
| `moire` | 4 | classic, distorted, multi_center, dense |
| `chroma_spiral` | 5 | classic, warped, multi, tight, loose |
| `mod_xor` | 4 | classic, distorted, fine, layered |
| `flame` | 4 | classic, intense, faint, turbulent |
| `noise_field` | 6 | classic, dense, coarse, turbulent, smooth_flow, sharp |
| `ten_print` | 5 | classic, compact, spacious, biased, dynamic |
| `wobbly` | 5 | classic, gentle, violent, fine_ripple, coarse_warp |
| `sdf_shapes` | 6 | classic, single, swarm, boxes, sharp, fuzzy |
| `game_of_life` | 5 | classic, sparse, dense, fast_evolution, bounded |
| `sand_game` | 5 | classic, rain, drizzle, avalanche, rainbow |
| `slime_dish` | 6 | classic, sparse, dense, explorer, focused, persistent |
| `dyna` | 6 | classic, single, many, long_waves, short_ripples, chaotic |
| `cppn` | 6 | classic, delicate, intricate, radiant, chaotic, linear |

共 17 个效果 x 86 个命名变体。

### 变体参数详情

**donut 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.20 | 默认参数 |
| alien | 0.20 | `surface_noise` (0.3-0.8), `asymmetry_x/y` (0.5-1.5), `twist` (0.3-1.5) |
| thin_ring | 0.15 | `R1` (0.1-0.3), `R2` (2.0-4.0) |
| fat_blob | 0.15 | `R1` (1.5-3.0), `R2` (0.05-0.5), `surface_noise` (0.1-0.5) |
| multi | 0.15 | `count` (2-3), `ring_offset` (0.2-0.5) |
| twisted | 0.15 | `twist` (0.8-2.0), `surface_noise` (0.1-0.4) |

**wireframe_cube 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.25 | 默认参数 |
| irregular | 0.25 | `vertex_noise` (0.1-0.6) |
| morphing | 0.25 | `morph` (0.2-1.0) |
| deformed | 0.25 | `vertex_noise` (0.2-0.5), `morph` (0.1-0.5), `scale` (0.2-0.7) |

**plasma 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.20 | 默认参数 |
| warped | 0.20 | `self_warp` (0.2-0.8) |
| noisy | 0.20 | `noise_injection` (0.2-0.7) |
| turbulent | 0.20 | `self_warp` (0.1-0.4), `noise_injection` (0.1-0.4), `frequency` (0.08-0.2) |
| slow_morph | 0.20 | `frequency` (0.01-0.03), `speed` (0.1-0.5), `noise_injection` (0.3-0.6) |

**wave 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.25 | 默认参数 |
| warped | 0.25 | `self_warp` (0.2-0.7) |
| chaotic | 0.25 | `noise_injection` (0.3-0.8), `wave_count` (5-10) |
| minimal | 0.25 | `wave_count` (1-2), `amplitude` (1.5-3.0) |

**moire 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.25 | 默认参数 |
| distorted | 0.25 | `distortion` (0.2-0.7) |
| multi_center | 0.25 | `multi_center` (2-3) |
| dense | 0.25 | `freq_a` (12-20), `freq_b` (12-20), `distortion` (0.1-0.3) |

**chroma_spiral 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.20 | 默认参数 |
| warped | 0.20 | `distortion` (0.2-0.6) |
| multi | 0.20 | `multi_center` (2-4) |
| tight | 0.20 | `arms` (5-8), `tightness` (1.0-2.0) |
| loose | 0.20 | `arms` (1-2), `tightness` (0.1-0.3), `chroma_offset` (0.15-0.3) |

**mod_xor 变体：**

| 变体 | 权重 | 关键参数 |
|------|------|----------|
| classic | 0.25 | 默认参数 |
| distorted | 0.25 | `distortion` (0.2-0.6) |
| fine | 0.25 | `modulus` (4-8), `zoom` (0.5-0.8) |
| layered | 0.25 | `modulus` (16-64), `layers` (2-3) |

### 效果形变参数 — Deformation Parameters

部分效果支持额外的形变参数（由变体注入或直接设置）：

| 效果 | 形变参数 | 范围 |
|------|----------|------|
| `donut` | `surface_noise`, `asymmetry_x`, `asymmetry_y`, `twist`, `count`, `ring_offset` | 0.0-2.0 |
| `wireframe_cube` | `vertex_noise`, `morph` | 0.0-1.0 |
| `plasma` | `self_warp`, `noise_injection` | 0.0-1.0 |
| `wave` | `self_warp`, `noise_injection` | 0.0-1.0 |
| `moire` | `distortion`, `multi_center` (1-4) | 0.0-1.0 |
| `chroma_spiral` | `distortion`, `multi_center` (1-4) | 0.0-1.0 |
| `mod_xor` | `distortion` | 0.0-1.0 |

---

## 5. Background Fill — 第二渲染通道

`procedural/bg_fill.py`

在主 buffer 渲染完成后（PostFX 链之后），对 `bg=None` 的 cell 执行第二渲染通道填充背景色。复用系统的全部组件：effects、variants、transforms、PostFX、masks、color schemes。

### bg_fill 流程

1. 从 13 个候选 effect 中选择（排除重量级：game_of_life / sand_game / slime_dish / dyna）
2. （可选）用 TransformedEffect 包装 0~2 个 transform
3. 创建临时 buffer + 临时 Context（seed ^ 0xBF11 确保与前景不同）
4. 跑 effect.pre() + 逐像素 main() 填充临时 buffer
5. （可选）施加 0~1 个 PostFX
6. （可选）mask 空间调制
7. char_idx → 归一化 → color scheme 着色 → dim (~30%) → 与 fg 暗色混合 → cell.bg

### bg_fill_spec 结构

```python
{
    "effect": str,          # 背景 effect 名称
    "effect_params": dict,  # effect 参数
    "transforms": list,     # 变换链 [{"type": ..., ...}]
    "postfx": list,         # 后处理链 [{"type": ..., ...}]
    "mask": dict | None,    # 遮罩规格 {"type": ..., ...}
    "color_mode": str,      # "scheme" 或 "continuous"
    "color_scheme": str,    # 颜色方案名称
    "warmth": float,        # 色温
    "saturation": float,    # 饱和度
    "dim": float,           # 亮度衰减系数 (0.18~0.45)
}
```

### 组合空间

13 effect × ~5 variant × ~20 transform 组合 × 7 postfx × 6 mask × 8 color（7 named + continuous）≈ ~750,000 种离散背景纹理组合，加上连续参数。

---

## 6. Composition Modes（合成模式）

`procedural/compositor.py`

当文法选择叠加效果（overlay）时，需要决定两个效果的合成方式。系统支持五种合成模式：

### 模式总览

| 模式 | 实现类 | 说明 |
|------|--------|------|
| `blend` | `CompositeEffect` | 标准颜色混合（ADD/SCREEN/OVERLAY/MULTIPLY） |
| `masked_split` | `MaskedCompositeEffect` | 空间分割遮罩（horizontal/vertical/diagonal） |
| `radial_masked` | `MaskedCompositeEffect` | 径向遮罩（中心/边缘分区） |
| `noise_masked` | `MaskedCompositeEffect` | 噪声遮罩（有机斑块混合） |
| `sdf_masked` | `MaskedCompositeEffect` | SDF 几何遮罩（圆/方/环几何形状） |

### blend 模式

使用 `CompositeEffect`，通过 `BlendMode` 枚举选择混合公式：

| BlendMode | 公式 | 视觉效果 |
|-----------|------|----------|
| `ADD` | `min(255, c1 + c2)` | 叠亮（光效） |
| `MULTIPLY` | `c1 * c2 / 255` | 叠暗（阴影） |
| `SCREEN` | `255 - (255-c1)(255-c2)/255` | 明亮混合 |
| `OVERLAY` | 按通道条件混合 | 对比增强 |

`mix` 参数 (0.0-1.0) 控制 effect_b 的不透明度。

### masked_split 模式

使用 `MaskedCompositeEffect` + 分割类遮罩：

- `horizontal_split` — 上下分区（`mask_split` 控制分割位置）
- `vertical_split` — 左右分区
- `diagonal` — 对角分区（`mask_angle` 控制角度）

附加参数：`mask_split` (0.3-0.7), `mask_softness` (0.05-0.25)

### radial_masked 模式

使用 `MaskedCompositeEffect` + `radial` 遮罩：

- `mask_center_x`, `mask_center_y` (0.3-0.7) — 中心位置
- `mask_radius` (0.2-0.5) — 径向半径
- `mask_softness` (0.1-0.3) — 过渡柔和度
- `mask_invert` (30% 概率) — 反转内外

### noise_masked 模式

使用 `MaskedCompositeEffect` + `noise` 遮罩：

- `mask_noise_scale` (0.03-0.1) — 噪声缩放
- `mask_noise_octaves` (2-4) — FBM 层数
- `mask_threshold` (0.3-0.7) — 阈值
- `mask_softness` (0.1-0.25) — 过渡柔和度

产生有机的、不规则斑块状混合边界，视觉上类似岩石纹理或云层分界。

### sdf_masked 模式

使用 `MaskedCompositeEffect` + `sdf` 遮罩：

- `mask_sdf_shape` — 形状类型：`circle`（40%）, `box`（30%）, `ring`（30%）
- `mask_sdf_size` (0.15-0.45) — SDF 形状大小
- `mask_softness` (0.05-0.2) — 过渡柔和度
- `mask_sdf_thickness` (0.05-0.15) — 环形厚度（仅 ring 形状）
- `mask_invert` (30% 概率) — 反转内外

产生几何形状的空间遮罩，适合结构化、现代风格的合成效果。

---

## 7. Grammar Integration（文法集成）

`procedural/flexible/grammar.py`

`VisualGrammar` 类的产生式规则决定合成系统各层的概率启用和参数采样。所有概率受 `energy`、`structure`、`intensity` 三个情感派生参数影响。详见 [flexible.md](flexible.md) 文法系统全貌。

### 域变换概率 — `_choose_domain_transforms(energy, structure)`

| 变换类型 | 概率范围 | 影响因素 | 动画 |
|----------|----------|----------|------|
| 镜像对称 (mirror_x/y/quad/kaleidoscope) | 30-55% | `+ structure * 0.25` | — |
| 平铺 (tile) | 20-40% | `+ structure * 0.20` | — |
| 螺旋扭曲 (spiral_warp) | 15-35% | `+ energy * 0.20` | twist: linear (energy > 0.3) |
| 旋转 (rotate) | 25% | 固定概率 | angle: linear (energy > 0.2) |
| 缩放 (zoom) | 18-30% | `+ energy * 0.12` | factor: oscillate (50%) |
| 极坐标映射 (polar_remap) | 8-15% | `+ energy * 0.07` | — |

镜像类型内部子选择：mirror_x 30%, mirror_y 30%, mirror_quad 20%, kaleidoscope 20%。

多个变换可同时启用并链式应用。目标：60-80% 的渲染至少有 1 个变换。

**动画 kwargs 生成规则：** 当 energy 超过阈值时，Grammar 概率性地将固定参数替换为动画规格。动画速度与 energy 正相关（高能量情绪 → 更快旋转/缩放/扭曲）。

### 后处理链概率 — `_choose_postfx_chain(energy, structure, intensity)`

| PostFX 类型 | 概率范围 | 影响因素 | 动画参数 |
|-------------|----------|----------|----------|
| vignette | 35-55% | `+ intensity * 0.20` | `pulse_speed`, `pulse_amp` |
| scanlines | 22-35% | `+ energy * 0.13` | `scroll_speed` |
| threshold | 14-30% | `+ structure * 0.16` | — |
| edge_detect | 10-22% | `+ structure * 0.12` | — |
| invert | 8-16% | `+ energy * 0.08` | — |
| color_shift | 18-30% | `+ energy * 0.12` | `drift_speed` |
| pixelate | 9-19% | `+ (1-structure) * 0.10` | `pulse_speed`, `pulse_amp` |

每种 PostFX 独立投骰，互不排斥。**保底机制**：若链为空，自动选择一个温和效果（vignette/color_shift/scanlines）。

**动画参数注入：** Grammar 根据 energy 概率性地为 vignette、scanlines、color_shift、pixelate 注入动画参数。动画速度与 energy 正相关。

### 合成模式概率 — `_choose_composition_mode(energy, structure)`

仅当叠加效果存在时生效：

| 模式 | 概率权重 | 影响因素 |
|------|----------|----------|
| blend | 25% | 固定权重 |
| masked_split | 25-35% | `+ structure * 0.10` |
| radial_masked | 22-30% | `+ (1-structure) * 0.08` |
| noise_masked | 22-30% | `+ energy * 0.08` |
| sdf_masked | ~12% | 固定权重 |

**遮罩动画速度注入：** 当 energy > 0.25 时，Grammar 以 ~55% 概率为 `mask_anim_speed` 注入 0.3-2.0 范围的值。高能量情绪产生更动态的遮罩边界。

### 变体选择 — `_sample_variant_params(effect_name)`

1. 在 `VARIANT_REGISTRY[effect_name]` 中按 `weight` 加权随机选择一个变体
2. 对变体的每个参数范围 `(min, max)` 均匀采样：
   - 整数类型 → `randint(min, max)`
   - 浮点类型 → `uniform(min, max)`
3. 采样结果合并到效果参数字典（覆盖基础参数）

### 多样性抖动 — `_weighted_choice()` Diversity Jitter

所有加权随机选择在采样前对每个权重乘以 `uniform(0.5, 1.5)` 随机因子：
- 同一 seed 仍完全可重现（抖动使用 `self.rng`）
- 相邻 seed 不再总是选同一效果
- 高权重项仍更可能被选中，但差距缩小

### 叠加效果激活率

```
overlay_chance = 0.45 + energy * 0.35   → 45-80%
```

高能量情绪下叠加效果非常活跃。

### 背景填充规格 — `_choose_bg_fill_spec(energy, structure, warmth)`

| 维度 | 选项 | 概率影响 |
|------|------|----------|
| bg effect | 13 候选 (pop 主 effect) | energy/structure 加权 |
| transforms | 0-2 个 (mirror 40%, tile 30%, kaleidoscope 20%, spiral_warp 12%, polar_remap 10%, rotate 10%, zoom 8%) | — |
| postfx | 0-1 个 (40% 概率: vignette/color_shift/scanlines/threshold/invert/edge_detect/pixelate) | — |
| mask | 0-1 个 (35% 概率: radial/noise/diagonal/horizontal_split/vertical_split/sdf) | — |
| color_mode | 55% scheme / 45% continuous | — |
| dim | 0.22-0.38 + energy*0.05 | energy 越高越亮 |

### 颜色方案 — `_choose_color_scheme(warmth, energy)`

| warmth 范围 | 偏好方案 |
|-------------|----------|
| > 0.7 | fire (35%), heat (30%), plasma (20%), rainbow (15%) |
| 0.3-0.7 | plasma (28%), rainbow (25%), heat (20%), ocean (15%), cool (12%) |
| < 0.3 | cool (30%), ocean (28%), matrix (22%), plasma (15%), rainbow (5%) |

### 导演模式覆盖（Director Mode Overrides）

CLI 参数 `--transforms`、`--postfx`、`--composition`、`--mask`、`--variant` 可精确覆盖文法选择。`_apply_overrides()` 在文法生成 SceneSpec 后替换对应字段。当 `--composition` 为非 blend 模式但没有 overlay 时，自动创建一个叠加效果。

---

## 8. Pipeline Flow（管线流程）

`procedural/flexible/pipeline.py` — `FlexiblePipeline._build_effect()`

效果构建的完整流程：

```
1. 创建 bg_effect（从 EFFECT_REGISTRY 或 CPPNEffect）
        │
2. 叠加效果存在？
   ├── 否 → 单效果
   └── 是 → 选择合成方式
        ├── composition_mode == "blend"
        │   └── CompositeEffect(bg, overlay, BlendMode, mix)
        └── composition_mode != "blend" && mask_type 存在
            └── MaskedCompositeEffect(bg, overlay, mask, threshold, softness)
                │
3. domain_transforms 非空？
   ├── 否 → 跳过
   └── 是 → TransformedEffect(composite_or_single, transform_chain)
                │
4. postfx_chain → 写入 params["_postfx_chain"]
   └── Engine.render_frame() 中在 effect.post() 后执行
5. bg_fill_spec → params["_bg_fill_spec"]
   └── Engine.render_frame() 中在 PostFX 后执行 bg_fill(buffer, ...)
6. color_scheme → Engine(color_scheme=spec.color_scheme)
   └── 传给 bg_fill + buffer_to_image
```

**参数传递路径：**

```python
# Pipeline 将 postfx_chain 和 mask_params 注入 render_params
if spec.postfx_chain:
    render_params["_postfx_chain"] = spec.postfx_chain
if spec.mask_params:
    render_params.update(spec.mask_params)

# Engine 在 render_frame() 中读取并执行
postfx_chain = params.get("_postfx_chain", [])
```

遮罩参数通过 `ctx.params` 传递给 Mask 的 `pre()` 方法（如 `mask_split`, `mask_softness`, `mask_center_x` 等）。

---

## 9. Combinatorial Impact（组合影响）

### 合成前基线

基于 [flexible.md](flexible.md) 的估算，合成系统引入前的离散组合约为 ~3,000,000 种（17 效果 x 布局 x 梯度 x 装饰 x 混合模式 x 动画 x 参数变化）。

### 各层乘数

| 层 | 离散组合数 | 说明 |
|----|-----------|------|
| Structural Variants | 86 命名变体 | 17 个效果的预设参数配置 |
| PostFX Chain | 2^7 = 128 | 7 种效果独立开关 |
| Domain Transforms | 9 种类型 | 含连续参数的无限变化 |
| Blend Modes | 4 | ADD / SCREEN / OVERLAY / MULTIPLY |
| Spatial Masks | 6 种类型 | 含连续参数的无限变化 |
| Composition Modes | 5 | blend / masked_split / radial_masked / noise_masked / sdf_masked |

### 综合估算

```
17 基础效果
  x 86 结构变体（含连续参数采样）
  x 128 PostFX 开关组合
  x 9 域变换类型（含连续参数）
  x 5 合成模式（含 sdf_masked）
  x 6 空间遮罩类型（含连续参数）
  x 5 布局算法
  x 73 ASCII 梯度
  x 8 装饰风格
  x 13 bg_fill effect（含变体 + 连续参数）
  x ~20 bg_fill transform 组合（含 rotate/zoom）
  x 7 bg_fill postfx（含 invert/edge_detect/pixelate）
  x 6 bg_fill mask（含 horizontal_split/vertical_split/sdf）
  x 8 color scheme（7 named + continuous）
≈ 数千亿种离散组合
```

加上每层的连续参数采样（变体范围内均匀采样、遮罩位置/半径/柔和度、变换角度/因子/扭曲度、PostFX 强度、bg_fill dim 系数等），实际视觉变化空间是连续无限的。

**实际约束：** 并非所有组合都等概率出现。Grammar 的概率产生式规则根据情感参数（energy, structure, intensity）调制各层启用概率，确保视觉输出与情感语义一致。高 structure 倾向对称和网格，高 energy 倾向螺旋扭曲和色相偏移，高 intensity 倾向暗角和强对比。
