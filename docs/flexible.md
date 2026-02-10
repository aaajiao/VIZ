# Flexible Output System（柔性输出系统）

打破刚性的一一对应映射，实现连续、可插值、可组合的视觉生成。

```
旧系统: text → 离散类别 → 固定效果 → 固定参数 → 单一输出
新系统: text → VAD向量 → 连续参数空间 → 文法组合 → 噪声调制 → 千变万化
```

## 模块概览

| 模块 | 文件 | 职责 |
|------|------|------|
| Emotion | `procedural/flexible/emotion.py` | 文本 → VAD 连续情感向量 |
| ColorSpace | `procedural/flexible/color_space.py` | 连续颜色空间（取代固定调色板） |
| Modulator | `procedural/flexible/modulator.py` | 噪声调制器（参数随时间漂移） |
| Grammar | `procedural/flexible/grammar.py` | 随机文法（组合爆炸式的场景规格） |
| CPPN | `procedural/flexible/cppn.py` | 神经网络图案生成 |
| Pipeline | `procedural/flexible/pipeline.py` | 编排所有模块的主管线 |

---

## 1. EmotionVector — VAD 情感空间

`procedural/flexible/emotion.py`

### VAD 三维模型

| 维度 | 范围 | 含义 |
|------|------|------|
| Valence (效价) | [-1, +1] | 消极 → 积极 |
| Arousal (唤醒度) | [-1, +1] | 平静 → 兴奋 |
| Dominance (支配感) | [-1, +1] | 被动 → 控制 |

### 预定义锚点（VAD_ANCHORS）

系统预定义 25 种情绪：

```
joy         (+0.8, +0.5, +0.5)    fear        (-0.8, +0.8, -0.7)
euphoria    (+1.0, +0.9, +0.8)    panic       (-0.9, +1.0, -0.9)
calm        (+0.3, -0.7, +0.3)    anger       (-0.6, +0.8, +0.5)
love        (+0.85, +0.35, +0.25)    sadness     (-0.7, -0.3, -0.5)
bull        (+0.7, +0.6, +0.7)    bear        (-0.6, +0.5, -0.4)
neutral     ( 0.0,  0.0,  0.0)    ...
```

### text_to_emotion()

关键词匹配 → VAD 加权平均：

```python
ev = text_to_emotion("市场暴跌 恐慌蔓延")
# 内部: "暴跌" → (-0.8, +0.7, -0.5), "恐慌" → (-0.9, +0.9, -0.8)
# 结果: EmotionVector(-0.85, +0.80, -0.65)
```

支持中英文关键词词典（`_WORD_VAD`）。

### to_visual_params()

将 VAD 向量映射为 16 个连续视觉参数：

| 参数 | 映射关系 |
|------|----------|
| `warmth` | valence 越高越暖 |
| `saturation` | arousal 越高越饱和 |
| `brightness` | valence 偏正越亮 |
| `frequency` | arousal 越高频率越高 |
| `speed` | arousal 越高速度越快 |
| `complexity` | |arousal| 越大越复杂 |
| `density` | arousal 越高越密集 |
| `turbulence` | arousal 高 + valence 低时开启 |
| `contrast` | dominance 越高对比越强 |
| `energy` | 综合 arousal + |valence| |
| `structure` | dominance 映射 |
| `intensity` | magnitude 强度 |
| `float_amp` | arousal 反向（平静 → 大浮动） |
| `breath_amp` | arousal 正向 |
| `animation_speed` | arousal 正向 |
| `octaves` | complexity 映射 |

### 向量操作

```python
ev1.lerp(ev2, t=0.5)         # 线性插值
ev1.slerp(ev2, t=0.5)        # 球面插值
ev1.distance(ev2)             # 欧几里得距离
ev1.magnitude()               # 向量长度
blend_emotions([ev1, ev2], [0.7, 0.3])  # 加权混合
```

---

## 2. ContinuousColorSpace — 连续颜色空间

`procedural/flexible/color_space.py`

取代旧系统的 5 种固定调色板（heat/rainbow/cool/matrix/plasma），用 warmth/saturation/brightness 三个连续参数生成颜色。

### 色温曲线

warmth 到 HSV 色相的分段线性映射：

```
warmth: 0.0 ──→ 0.3 ──→ 0.5 ──→ 0.7 ──→ 1.0
hue:    0.60    0.50    0.30    0.15    0.00
        蓝      青蓝     绿      黄绿     红
```

### 核心方法

```python
cs = ContinuousColorSpace()

# 单色采样
color = cs.sample(value=0.5, warmth=0.7, saturation=0.8)
# → (r, g, b) 元组

# 完整调色板（7色）
palette = cs.generate_palette(warmth=0.3, saturation=0.9, brightness=0.8)
# → {bg, primary, secondary, accent, glow, outline, dim}
```

### 调色板结构

| 角色 | 生成逻辑 |
|------|----------|
| `bg` | 极暗 + 色温倾向（V=0.02-0.08） |
| `primary` | 高饱和高亮（V=0.7-1.0） |
| `secondary` | 色相偏移 +0.05，稍暗 |
| `accent` | 互补色方向偏移（或高亮白色） |
| `glow` | 主色的淡化版（低饱和高亮） |
| `outline` | 主色的暗化版（V=0.3） |
| `dim` | 极暗参考色（V=0.15） |

### interpolate_palettes()

在两个调色板之间逐通道线性插值，用于动画过渡。

---

## 3. NoiseModulator — 噪声调制器

`procedural/flexible/modulator.py`

让视觉参数随时间/空间平滑漂移，避免静态输出的机械感。

### NoiseModulator

```python
mod = NoiseModulator(seed=42, base=0.5, amplitude=0.2, frequency=0.3)
value = mod.sample(t=1.5)        # 一维时间采样
value = mod.sample_2d(x, y, t)   # 二维空间+时间（支持域扭曲）
```

- 底层：FBM 噪声（3-4 层）
- 域扭曲（Domain Warping）：噪声扭曲噪声坐标，产生有机变形
- 可选 min/max 截断

### ModulatedParams

```python
mp = ModulatedParams(seed=42)
mp.add("frequency", base=0.05, amplitude=0.02, speed=0.3)
mp.add("warmth", base=0.7, amplitude=0.1, speed=0.2)

params = mp.sample(t=1.5)
# → {"frequency": 0.053, "warmth": 0.68, ...}
```

- 批量管理多个调制参数
- 视频模式：`t` 随帧推进，参数自然漂移
- 静态模式：`t=0` 也有微妙变化

---

## 4. VisualGrammar — 随机文法

`procedural/flexible/grammar.py`

概率产生规则生成完整的 `SceneSpec`（场景规格），类似上下文无关文法。

### SceneSpec 字段

```python
@dataclass
class SceneSpec:
    # 效果层
    bg_effect: str              # 背景效果名（plasma/wave/...）
    bg_params: dict             # 背景参数
    overlay_effect: str | None  # 叠加效果（可选）
    overlay_params: dict        # 叠加参数
    overlay_blend: str          # 混合模式
    overlay_mix: float          # 混合比例

    # 布局
    layout_type: str            # random_scatter/grid_jitter/spiral/force_directed/preset
    kaomoji_count: int          # 颜文字数量（2-12）
    kaomoji_size_range: tuple   # 大小范围
    kaomoji_mood: str           # 情绪类别
    has_central_kaomoji: bool   # 是否有中心大颜文字
    central_size: int           # 中心大小

    # 装饰
    text_elements: list         # 氛围文字列表
    particle_chars: str         # 粒子字符集
    decoration_style: str       # corners/edges/scattered/minimal/none/frame/grid_lines/circuit
    decoration_chars: str       # 装饰字符 (含 box-drawing)

    # 动画
    animations: list            # 动画模板
    float_amp: float            # 浮动幅度
    breath_amp: float           # 呼吸幅度

    # 后处理
    gradient_name: str          # ASCII 字符梯度
    sharpen: bool               # 锐化
    contrast: float             # 对比度
    warmth: float               # 色温
    saturation: float           # 饱和度
    brightness: float           # 亮度

    # 域变换 (Domain transforms)
    domain_transforms: list[dict]   # 变换链 [{"type": "kaleidoscope", "segments": 6}, ...]
    postfx_chain: list[dict]        # 后处理链 [{"type": "vignette", "strength": 0.5}, ...]

    # 合成模式 (Composition mode)
    composition_mode: str           # "blend" / "masked_split" / "radial_masked" / "noise_masked"
    mask_type: str | None           # 遮罩类型 (horizontal_split/vertical_split/diagonal/radial/noise/sdf)
    mask_params: dict               # 遮罩参数
```

### 产生规则

每条规则根据情感参数（energy, structure, valence, arousal）做加权随机选择：

| 规则 | 选项 | 权重影响 |
|------|------|----------|
| `_choose_bg_effect()` | plasma, wave, flame, moire, noise_field, sdf_shapes, cppn | energy + structure |
| `_choose_overlay_effect()` | plasma, wave, noise_field, moire, cppn | energy，排除已选 bg |
| `_choose_blend_mode()` | ADD, SCREEN, OVERLAY, MULTIPLY | energy 偏向 |
| `_choose_layout()` | random_scatter, grid_jitter, spiral, force_directed, preset | structure 偏向 |
| `_choose_kaomoji_count()` | 2-12 | base=4 + energy*4 |
| `_choose_animations()` | floating, breathing, color_cycle | energy/arousal |
| `_choose_decoration_style()` | corners, edges, scattered, minimal, none, **frame, grid_lines, circuit** | structure |
| `_choose_decoration_chars()` | **60+ 组** (box 角/线/交叉/方块/点/经典) | **energy + warmth** |
| `_choose_gradient()` | **67 种** (classic, blocks, vbar, hbar, box_thin, circles, punctuation, math, ...) | **energy + structure** |
| `_choose_particle_chars()` | **25+ 组** (经典/几何/box 线段/方块/盲文) | **energy + warmth** |
| `_choose_text_elements()` | 8 组情绪词池（中英 + **semigraphic 符号**） | valence × arousal |
| `_choose_kaomoji_mood()` | 6 象限情绪 | valence × arousal |
| `_choose_domain_transforms()` | mirror_x/y/quad, kaleidoscope, tile, rotate, zoom, spiral_warp, **polar_remap** | structure + energy (概率提高至 30-55%) |
| `_choose_postfx_chain()` | vignette, scanlines, threshold, edge_detect, invert, color_shift, pixelate | energy + structure + intensity (概率提高, 保底 ≥1) |
| `_choose_composition_mode()` | blend, masked_split, radial_masked, noise_masked | energy + structure (blend 降至 25%) |

详见 [box_chars.md](box_chars.md) 获取完整的字符集和梯度参考。

### 变体系统集成（Variant Integration）

文法通过 `_sample_variant_params(effect_name)` 从 `VARIANT_REGISTRY`（`procedural/effects/variants.py`）采样结构变体参数。7 个效果共 32 个命名变体，每个变体定义参数范围预设（如 `surface_noise: (0.3, 0.8)`），文法按权重选择变体后在范围内均匀采样。

辅助方法 `_jitter(base, amount, lo, hi)` 在基础值附近添加高斯随机偏移（σ = amount × 0.6），用于所有连续参数的微调。

**多样性抖动**：`_weighted_choice()` 在每次采样前对权重乘以 `uniform(0.5, 1.5)` 因子，让相邻 seed 产生不同结果，同时保持单 seed 可重现。

**导演模式覆盖**：CLI 参数（`--transforms`、`--postfx`、`--composition`、`--mask`、`--variant`）可精确覆盖文法的自动选择。覆盖在 `_apply_overrides()` 中执行，完全替换文法选择的对应字段。

详见 [composition.md](composition.md#structural-variants) 获取完整变体目录。

### 组合空间

理论离散组合：17 bg × 32 variants × 7 overlay × 4 blend × 4 composition × 6 mask × 128 postfx × 9 transform × 5 layout × 20 gradient × 8 deco × 60 chars ≈ **数亿** 种。加上连续参数（warmth, saturation, deformation, ...）→ 无限变体。详见 [composition.md](composition.md#combinatorial-impact)。

---

## 5. CPPNEffect — 神经网络图案

`procedural/flexible/cppn.py`

详见 [effects.md](effects.md) 中 CPPNEffect 章节。

---

## 6. FlexiblePipeline — 主管线

`procedural/flexible/pipeline.py`

编排所有模块的完整生成流程。现在接受可选的 `content` 参数，支持 AI 传入结构化内容数据。

### 完整管线流程

```
输入（文本 / 情绪名 / VAD 向量 + 可选 content）
        │
        ▼
  text_to_emotion() / emotion_from_name()
        │
        ▼
  EmotionVector (VAD 连续空间)
        │
        ▼
  to_visual_params() → 16 参数字典
        │
        ▼
  NoiseModulator.modulate(t) → 漂移后参数
        │
        ▼
  VisualGrammar.generate() → SceneSpec
        │
        ▼
  grammar.place_content(spec, content, visual_params)
  ← 放置 headline / metrics / timestamp / ambient words
        │
        ├─────────────────┐
        ▼                 ▼
  _build_effect()    _build_sprites()
  (Effect 或          (Kaomoji + Text +
   Composite/Masked    Decoration + Particle +
   → TransformedEffect  Content Overlay)
   包装)
        ▼                 │
  ContinuousColorSpace.generate_palette()
        │
        ▼
  Engine.render_frame(effect, sprites, params)
        │
        ▼
  PIL Image / GIF
```

### 主要方法

```python
pipe = FlexiblePipeline(seed=42)

# 单帧（纯视觉）
img = pipe.generate(
    text="市场暴跌",      # 或 emotion="panic" 或 emotion_vector=ev
    seed=42,
    title="PANIC",
    output_path="output.png",
)

# 单帧 + 内容数据（AI 集成）
content = {
    'source': 'market',
    'headline': 'DOW +600',
    'metrics': ['BTC: $92k', 'ETH: $4.2k'],
    'timestamp': '2026-02-03 12:00',
    'vocabulary': get_vocabulary('market'),
}
img = pipe.generate(emotion="bull", content=content)

# 动画
pipe.generate_video(
    text="hope rising",
    duration=3.0,
    fps=15,
    output_path="output.gif",
)

# 多变体
imgs = pipe.generate_variants(text="neutral", count=5)
```

### _build_sprites() 精灵构建

1. **位置生成**：根据 `layout_type` 选择布局算法
2. **颜文字精灵**：遍历位置，按 `_mood_from_valence_arousal()` 分配情绪，添加动画
3. **中心颜文字**：可选大尺寸中心角色
4. **装饰精灵**：按 `decoration_style` 分布（corners/edges/scattered/minimal/**frame/grid_lines/circuit**），新增 box-drawing 边框、网格和电路板风格，详见 [box_chars.md](box_chars.md)
5. **粒子精灵**：随机散布字符，浮动动画
6. **氛围文字**：grammar 生成的 `text_elements` 渲染
7. **标题**：居中大字 + 光晕

### _mood_from_valence_arousal()

2D 查找表（6 效价段 × 3 唤醒段）：

| valence \ arousal | 高 (>0.3) | 中 | 低 (<-0.3) |
|---|---|---|---|
| >0.7 | euphoria, excitement | happy, proud | love, relaxed |
| 0.3~0.7 | excitement, proud | happy | relaxed |
| 0~0.3 | surprised, confused | neutral | bored, sleepy |
| -0.3~0 | anxiety, confused | disappointed | bored |
| -0.6~-0.3 | anger, anxiety | sad | lonely |
| <-0.6 | panic, fear | sad, lonely | lonely |

### 关键常量

- `internal_size`：160 × 160（低分辨率渲染）
- `output_size`：1080 × 1080（最终输出）
- `drift_amount`：0.2-0.3（参数漂移强度）

---

## 7. Content 数据结构

`lib/content.py`

AI 传入的结构化内容数据，所有字段可选。

```python
from lib.content import make_content, content_has_data

content = make_content({
    'source': 'market',           # 内容来源（market/art/news/mood）
    'headline': 'DOW +600',       # 主标题
    'metrics': ['BTC: $92k'],     # 指标列表
    'timestamp': '2026-02-03',    # 时间戳
    'body': 'Markets rally...',   # 正文
})

if content_has_data(content):
    # headline/metrics/body 中至少有一项非空
    pass
```

### Content 如何影响渲染

`VisualGrammar.place_content()` 将内容数据概率性地放置到 SceneSpec 中：

| 内容字段 | 放置策略 |
|----------|----------|
| `headline` | 5 种位置概率分布（中上、中央、底部、左上角、偏移中央） |
| `metrics` | 聚集或散布放置，右下偏多 |
| `timestamp` | 4 种角落/底部位置 |
| `vocabulary.ambient_words` | 随机散布到 `text_elements` 中 |

SceneSpec 新增字段：`content_headline`, `content_metrics`, `content_timestamp`, `content_body`, `content_source`。

---

## 8. Source Vocabulary — 来源词汇

`lib/vocabulary.py`

不同来源通过视觉词汇（粒子、颜文字、符号）区分身份，而非固定视觉模板。

```python
from lib.vocabulary import get_vocabulary

vocab = get_vocabulary('market')
# → {
#     'particles': '$¥€₿↑↓▲▼◆●',
#     'kaomoji_moods': {'positive': ['bull','euphoria'], 'negative': ['bear','panic'], 'neutral': ['neutral']},
#     'symbols': ['$', '¥', '€', '₿', '↑', '↓'],
#     'decoration_chars': '═║╔╗╚╝╠╣╦╩',
#     'ambient_words': {'positive': ['HODL','PUMP','APE IN'], 'negative': ['SELL','EXIT','REKT'], 'neutral': ['HOLD','WAIT']}
# }

# AI 可覆盖任意字段
vocab = get_vocabulary('market', overrides={'particles': '★☆●○'})
```

### 预定义来源

| 来源 | 粒子风格 | 颜文字偏好 | 氛围词 |
|------|---------|-----------|--------|
| `market` | 货币符号 + 箭头 | bull/bear/euphoria/panic | 金融术语 |
| `art` | 几何 + 星号 | love/thinking/proud | 艺术词汇 |
| `news` | 方块 + 箭头 | surprised/thinking/neutral | 新闻用语 |
| `mood` | 柔和 + 星点 | 全情绪分类 | 情感词汇 |

### Vocabulary 如何影响渲染

1. **粒子字符** → `SceneSpec.particle_chars`（覆盖文法默认选择）
2. **颜文字情绪** → `SceneSpec.kaomoji_mood`（优先于 VAD 推断的情绪）
3. **装饰字符** → `SceneSpec.decoration_chars`
4. **氛围词** → `SceneSpec.text_elements`（通过 `place_content()` 注入）

词汇是默认值而非强制模板——情绪系统、文法系统仍然驱动整体视觉风格，词汇只提供来源的"指纹"。
