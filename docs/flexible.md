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

系统预定义 20+ 种情绪：

```
joy         (+0.8, +0.5, +0.5)    fear        (-0.8, +0.8, -0.7)
euphoria    (+1.0, +0.9, +0.8)    panic       (-0.9, +1.0, -0.9)
calm        (+0.3, -0.7, +0.3)    anger       (-0.6, +0.8, +0.5)
love        (+0.9, +0.4, +0.3)    sadness     (-0.7, -0.3, -0.5)
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
    decoration_style: str       # corners/edges/scattered/minimal/none
    decoration_chars: str       # 装饰字符

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
| `_choose_decoration_style()` | corners, edges, scattered, minimal, none | structure |
| `_choose_particle_chars()` | 9 组字符集 | 均匀随机 |
| `_choose_text_elements()` | 8 组情绪词池（中英） | valence × arousal |
| `_choose_kaomoji_mood()` | 6 象限情绪 | valence × arousal |

### 组合空间

理论离散组合：7 bg × 5 overlay × 4 blend × 5 layout × 5 count × 3 text × 8 gradient × 4 post ≈ **235,200+** 种。加上连续参数（warmth, saturation, ...）→ 无限变体。

---

## 5. CPPNEffect — 神经网络图案

`procedural/flexible/cppn.py`

详见 [effects.md](effects.md) 中 CPPNEffect 章节。

---

## 6. FlexiblePipeline — 主管线

`procedural/flexible/pipeline.py`

编排所有模块的完整生成流程。

### 完整管线流程

```
输入（文本 / 情绪名 / VAD 向量）
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
        ├─────────────────┐
        ▼                 ▼
  _build_effect()    _build_sprites()
  (Effect 或          (Kaomoji + Text +
   CompositeEffect)    Decoration + Particle)
        │                 │
        ▼                 ▼
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

# 单帧
img = pipe.generate(
    text="市场暴跌",      # 或 emotion="panic" 或 emotion_vector=ev
    seed=42,
    title="PANIC",
    output_path="output.png",
)

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
4. **装饰精灵**：按 `decoration_style` 分布（corners/edges/scattered/minimal）
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
