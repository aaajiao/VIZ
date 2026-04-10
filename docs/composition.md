# Effect Composition System（效果合成系统）

> For AI agent usage examples, see `skills/viz-ascii-art/references/COMPOSITION.md`.

效果合成系统为视觉输出提供四层可组合的结构变换，将基础效果从有限集合扩展到无限连续的视觉空间。

The composition system provides four composable layers of structural transformation, expanding the base effect set from a finite collection into an infinite continuous visual space.

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

**Five-Layer Architecture:**

1. **Structural Variants** — 基础效果的命名参数预设，提供离散结构变化
2. **Composition** — 双效果混合（BlendMode）或空间遮罩合成（MaskedCompositeEffect）
3. **Domain Transforms** — UV 坐标变换链（镜像、平铺、万花筒等）
4. **PostFX Chain** — 缓冲区级后处理（暗角、扫描线、边缘检测等）
5. **Background Fill** — 第二渲染通道，填充 `bg=None` cell

每层独立概率启用，层间可自由组合。

---

## 1. Domain Transforms（域变换）

`procedural/transforms.py`

坐标变换函数将像素坐标归一化为 UV `[0,1]` 后做几何变换，再转回像素坐标传给内部效果的 `main()` 方法。变换按列表顺序依次链式应用。

### TRANSFORM_REGISTRY

| 名称 | 说明 | 参数 |
|------|------|------|
| `mirror_x` | 水平镜像对称 | 无 |
| `mirror_y` | 垂直镜像对称 | 无 |
| `mirror_quad` | 四象限对称 | 无 |
| `kaleidoscope` | N 折旋转对称 | `segments=6`, `cx=0.5`, `cy=0.5` |
| `tile` | 平铺重复 | `cols=2`, `rows=2` |
| `rotate` | 绕中心旋转 | `angle=0.0`, `cx=0.5`, `cy=0.5` |
| `zoom` | 中心缩放 | `factor=2.0`, `cx=0.5`, `cy=0.5` |
| `spiral_warp` | 螺旋域扭曲 | `twist=1.0`, `cx=0.5`, `cy=0.5` |
| `polar_remap` | 笛卡尔转极坐标 | `cx=0.5`, `cy=0.5` |

共 9 种变换，其中 6 种带连续参数。

### Animated Kwargs

变换参数支持时间驱动动画（GIF/视频模式）。普通标量值原样传递；动画规格 dict 在每帧根据 `ctx.time` 求值。

**三种动画模式：**

| 模式 | 公式 | 用途 |
|------|------|------|
| `linear` | `base + time * speed` | 持续旋转/平移 |
| `oscillate`（默认）| `base + amp * sin(time * speed * TAU)` | 呼吸/脉动 |
| `ping_pong` | `base + amp * triangle(time * speed)` | 来回运动 |

`_resolve_animated_kwargs(kwargs, time)` 保证 time=0.0（静态 PNG）时输出与传统方式完全一致。

---

## 2. Spatial Masks（空间遮罩）

`procedural/masks.py`

空间遮罩为双效果合成提供逐像素的混合权重。`char_idx` 值 0-9 编码混合权重（0 = effect_a, 9 = effect_b）。

### MASK_REGISTRY

| 名称 | 说明 | 专用参数 |
|------|------|----------|
| `horizontal_split` | 上下分割 | — |
| `vertical_split` | 左右分割 | — |
| `diagonal` | 对角分割 | `mask_angle` |
| `radial` | 径向渐变 | `mask_center_x`, `mask_center_y`, `mask_radius`, `mask_invert` |
| `noise` | 噪声有机斑块 | `mask_noise_scale`, `mask_noise_octaves`, `mask_threshold`, `mask_seed_offset` |
| `sdf` | SDF 几何形状 | `mask_sdf_shape`, `mask_sdf_size`, `mask_sdf_thickness`, `mask_invert` |

**通用参数：** `mask_split` (0.5), `mask_softness` (0.05-0.15), `mask_anim_speed` (0.0 = static).

### Mask Animation

当 `mask_anim_speed > 0` 且 `ctx.time > 0` 时：

| 遮罩 | 动画效果 |
|------|---------|
| `horizontal_split` / `vertical_split` | 分割线扫动 |
| `diagonal` | 对角线旋转 |
| `radial` | 径向边界脉动 |
| `noise` | 有机形态漂移 |
| `sdf` | 几何形状脉动 |

---

## 3. PostFX Chain（后处理特效链）

`procedural/postfx.py`

缓冲区级别的后处理效果，在 `effect.post()` 之后、`buffer_to_image()` 之前执行。操作 Cell 网格（不是像素图像）。

### POSTFX_REGISTRY

| 名称 | 说明 | 参数 | 动画参数 |
|------|------|------|----------|
| `threshold` | 二值化 | `threshold=0.5` | — |
| `invert` | 反转 char_idx 和颜色 | 无 | — |
| `edge_detect` | Sobel 边缘检测 | 无 | — |
| `scanlines` | 水平扫描线 | `spacing=4`, `darkness=0.3` | `scroll_speed` |
| `vignette` | 暗角 | `strength=0.5` | `pulse_speed`, `pulse_amp` |
| `pixelate` | 像素化 | `block_size=4` | `pulse_speed`, `pulse_amp` |
| `color_shift` | 色相偏移 | `hue_shift=0.1` | `drift_speed` |

共 7 种后处理效果，其中 4 种支持时间动画。链内顺序有意义。每种效果独立概率启用（2^7 = 128 种开关组合）。

### v0.8.0 Filter Modes

Engine now supports output-level filter modes applied after upscale: `sharpen` (default), `blur`, `detail`, `none`. Configured via `--filter-mode` CLI flag or `filter_mode` JSON field.

---

## 4. Structural Variants（结构变体）

`procedural/effects/variants.py`

为基础效果提供命名参数预设。文法系统按权重选择变体，然后在范围内均匀采样具体参数值。共 17 个效果 x 86 个命名变体。

Run `viz capabilities --format json` for the complete variant listing with all parameter ranges.

### Deformation Parameters

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

### 组合空间

13 effect x ~5 variant x ~20 transform 组合 x 7 postfx x 6 mask x 8 color (7 named + continuous) = ~750,000 种离散背景纹理组合，加上连续参数。

---

## 6. Composition Modes（合成模式）

`procedural/compositor.py`

当文法选择叠加效果（overlay）时，系统支持五种合成模式：

| 模式 | 实现 | 说明 |
|------|------|------|
| `blend` | `CompositeEffect` | 标准颜色混合（ADD/SCREEN/OVERLAY/MULTIPLY） |
| `masked_split` | `MaskedCompositeEffect` | 空间分割遮罩 |
| `radial_masked` | `MaskedCompositeEffect` | 径向遮罩 |
| `noise_masked` | `MaskedCompositeEffect` | 噪声遮罩 |
| `sdf_masked` | `MaskedCompositeEffect` | SDF 几何遮罩 |

### BlendMode

| BlendMode | 公式 | 视觉效果 |
|-----------|------|----------|
| `ADD` | `min(255, c1 + c2)` | 叠亮 |
| `MULTIPLY` | `c1 * c2 / 255` | 叠暗 |
| `SCREEN` | `255 - (255-c1)(255-c2)/255` | 明亮混合 |
| `OVERLAY` | 按通道条件混合 | 对比增强 |

`mix` 参数 (0.0-1.0) 控制 effect_b 的不透明度。

---

## 7. Grammar Integration（文法集成）

`procedural/flexible/grammar.py`

v0.8.0 Grammar 采用近均匀随机生成。效果、变换、后处理、蒙版等离散选择全部接近等概率，情绪参数仅提供 ≤20% 的轻微偏移。

**v0.8.0 生成机制：**
- 效果选择：17 种效果近均匀随机（`_biased_choice`，情绪偏移 ≤20%）
- 域变换：随机 0-3 个，从 9 种中均匀选取
- PostFX 链：随机 0-3 个，从 7 种中均匀选取（允许空链）
- 叠加效果：`overlay_chance = 0.45 + energy * 0.35`，overlay_mix 范围 0.05-0.95
- 调色板：程序化生成，每个 seed 独特的 16 色调色板
- 后处理滤镜：sharpen / blur / detail / none 随机选择

---

## 8. Combinatorial Impact

### 综合估算

```
17 基础效果
  x 86 结构变体（含连续参数采样）
  x 128 PostFX 开关组合
  x 9 域变换类型（含连续参数）
  x 5 合成模式
  x 6 空间遮罩类型（含连续参数）
  x 5 布局算法
  x 73 ASCII 梯度
  x 8 装饰风格
  x 13 bg_fill effect（含变体 + 连续参数）
  x ~20 bg_fill transform 组合
  x 7 bg_fill postfx
  x 6 bg_fill mask
  x 程序化调色板（每 seed 独特 16 色）
≈ 连续无限的视觉空间
```

每个 seed 程序化生成独特调色板，加上所有层的连续参数采样，实际视觉变化空间是连续无限的。Grammar 使用近均匀随机选择，情绪仅提供方向性偏移。
